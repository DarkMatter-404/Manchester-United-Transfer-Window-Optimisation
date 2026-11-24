"""Evaluate the frozen recommendations on the 2025/26 season.

This is the only script that reads records dated after the cutoff. It reads
the frozen lists, never the model, and nothing it writes is an input to the
model. It follows the measures in <freeze>/evaluation_plan.md.

Before it reads anything it checks every frozen file against the hashes in
the freeze manifest, and stops if one has changed.

Playing time is measured club by club. A player who played for two clubs in
the season has one row for each club, and each club's share uses that club's
own minutes and matches. The one-line summary per player uses the club where
he or she played the most league minutes, labelled "main club".

Run from the repository root:
    python src/evaluate_results.py --freeze results/freeze --out results/corrections/2026-11-18/evaluation
"""

import csv
import datetime
import hashlib
import json
import os
import statistics
import subprocess
import sys
from importlib import metadata

import duckdb

from output_paths import input_folder, output_folder

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw", "transfermarkt")
DOCS = os.path.join(HERE, "..", "docs")

CUTOFF = "2025-05-31"
SEASON = 2025                       # the 2025/26 season, named by its starting year
WINDOW_START = "2025-06-01"         # the summer 2025 window, as written in the evaluation plan
WINDOW_END = "2025-09-01"
VALUE_UP_TO = "2026-06-12"          # last valuation date used
EUR_TO_GBP = 0.8412                 # the same rate as at the cutoff, so value changes are not currency changes
LEAGUES = ["GB1", "ES1", "IT1", "L1", "FR1", "NL1", "PO1", "BE1", "TR1", "RU1", "UKR1", "GR1", "SC1", "DK1"]
DEFENSIVE_ROLES = ["CB", "GK"]


def raw(table):
    return "read_csv_auto('" + os.path.join(RAW, table + ".csv.gz").replace("'", "''") + "')"


def read_table(folder, name):
    with open(os.path.join(folder, name), newline="") as file:
        return list(csv.DictReader(file))


def file_hash(path):
    with open(path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


def write_table(path, columns, rows):
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(c, "") for c in columns])


#########Check the freeze before using it############

FREEZE = input_folder("--freeze")
with open(os.path.join(FREEZE, "freeze_manifest.json")) as file:
    freeze_manifest = json.load(file)
changed = [name for name, expected in freeze_manifest["frozen_file_sha256"].items()
           if file_hash(os.path.join(FREEZE, name)) != expected]
if changed:
    sys.exit("Frozen files do not match the freeze manifest: " + ", ".join(changed))
print("All", len(freeze_manifest["frozen_file_sha256"]), "frozen files match the freeze manifest.")

OUT = output_folder()
con = duckdb.connect()
league_list = ", ".join("'" + code + "'" for code in LEAGUES)

#########Who is evaluated############

people = []     # (group, need, plan, player_id, name)
plan = read_table(FREEZE, "preferred_plan.csv")
ids = {row["name"]: row["player_id"] for row in read_table(FREEZE, "candidates_considered.csv")}
for row in plan:
    ids[row["name"]] = row["player_id"]

need_of = {}
for row in read_table(FREEZE, "direct_alternatives.csv"):
    if row["player"] not in ids:
        continue
    group = "base signing" if row["plan"] == "A" else "direct alternative"
    people.append((group, row["need"], row["plan"], ids[row["player"]], row["player"]))
    need_of[ids[row["player"]]] = row["need"]
for row in plan:
    if row["action"] == "sold":
        people.append(("sold in the base plan", "", "", row["player_id"], row["name"]))

# The players United actually signed: a reviewed list of every move into the
# club's organisation in the window. Every move in the records must be on it.
reviewed = read_table(DOCS, "actual_united_arrivals_2025.csv")
reviewed_keys = set((row["player_id"], row["date"]) for row in reviewed)
united_ids = [985] + [int(row["member_club_id"]) for row in
                      read_table(os.path.join(HERE, "..", "data", "processed"), "club_family.csv")
                      if row["senior_club_id"] == "985"]
window_moves = con.execute("""
    SELECT CAST(player_id AS VARCHAR), CAST(transfer_date AS VARCHAR), player_name
    FROM """ + raw("transfers") + """
    WHERE to_club_id IN (""" + ", ".join(str(i) for i in united_ids) + """)
      AND transfer_date BETWEEN DATE '""" + WINDOW_START + """' AND DATE '""" + WINDOW_END + """'
    ORDER BY 2, 1""").fetchall()
missing = [name for (pid, date, name) in window_moves if (pid, date) not in reviewed_keys]
if missing:
    sys.exit("Moves into United in the window that are not in actual_united_arrivals_2025.csv: " + ", ".join(missing))
for row in reviewed:
    if row["in_comparison_group"] == "yes":
        people.append(("actual United signing", "", "", row["player_id"], row["name"]))

#########Outcomes in 2025/26, club by club############

con.execute("CREATE TABLE who (player_id BIGINT)")
con.executemany("INSERT INTO who VALUES (?)", sorted(set((int(p[3]),) for p in people)))

# League matches of the season, one row per club and match
con.execute("""
CREATE TABLE club_matches AS
SELECT game_id, competition_id AS league, home_club_id AS club_id, away_club_goals AS goals_against
FROM """ + raw("games") + """ WHERE season = """ + str(SEASON) + """ AND competition_id IN (""" + league_list + """)
UNION ALL
SELECT game_id, competition_id AS league, away_club_id AS club_id, home_club_goals AS goals_against
FROM """ + raw("games") + """ WHERE season = """ + str(SEASON) + """ AND competition_id IN (""" + league_list + """)
""")

club_rows = con.execute("""
WITH played AS (
    SELECT a.player_id, a.player_club_id AS club_id, m.league,
           sum(a.minutes_played) AS played_minutes, sum(a.goals) AS goals, sum(a.assists) AS assists
    FROM """ + raw("appearances") + """ a
    JOIN club_matches m ON m.game_id = a.game_id AND m.club_id = a.player_club_id
    WHERE a.player_id IN (SELECT player_id FROM who)
    GROUP BY 1, 2, 3),
started AS (
    SELECT l.player_id, l.club_id, count(*) AS starts, sum(m.goals_against) AS conceded
    FROM """ + raw("game_lineups") + """ l
    JOIN club_matches m ON m.game_id = l.game_id AND m.club_id = l.club_id
    WHERE l.type = 'starting_lineup' AND l.player_id IN (SELECT player_id FROM who)
    GROUP BY 1, 2),
matches AS (SELECT club_id, league, count(*) AS club_matches FROM club_matches GROUP BY 1, 2)
SELECT p.player_id, p.club_id, c.name, p.league, p.played_minutes, t.club_matches,
       coalesce(s.starts, 0), p.goals, p.assists, s.conceded
FROM played p
JOIN matches t ON t.club_id = p.club_id AND t.league = p.league
LEFT JOIN started s ON s.player_id = p.player_id AND s.club_id = p.club_id
LEFT JOIN """ + raw("clubs") + """ c ON c.club_id = p.club_id
ORDER BY p.player_id, p.club_id""").fetchall()

clubs_of = {}
for (pid, club_id, club, league, played, matches, starts, goals, assists, conceded) in club_rows:
    clubs_of.setdefault(str(pid), []).append({
        "player_id": str(pid), "club_id": club_id, "club": club, "league": league,
        "league_minutes": int(played), "club_league_matches": int(matches),
        # This club's minutes over this club's league minutes
        "club_minutes_share": round(played / (90.0 * matches), 4),
        "starts": int(starts), "goals": int(goals), "assists": int(assists),
        "team_conceded_in_starts": int(conceded) if conceded is not None else "",
    })

# Main club: most league minutes; then most starts; then the smaller club id
main_club = {}
for pid, rows in clubs_of.items():
    ordered = sorted(rows, key=lambda r: (-r["league_minutes"], -r["starts"], r["club_id"]))
    main_club[pid] = ordered[0]
    for r in rows:
        r["is_main_club"] = "yes" if r is ordered[0] else "no"

values = {}
for (pid, before, after, after_date) in con.execute("""
    WITH before AS (
        SELECT player_id, first(market_value_in_eur ORDER BY date DESC) AS value FROM """ + raw("player_valuations") + """
        WHERE date <= DATE '""" + CUTOFF + """' GROUP BY 1),
    after AS (
        SELECT player_id, first(market_value_in_eur ORDER BY date DESC) AS value, max(date) AS value_date
        FROM """ + raw("player_valuations") + """
        WHERE date > DATE '""" + CUTOFF + """' AND date <= DATE '""" + VALUE_UP_TO + """' GROUP BY 1)
    SELECT w.player_id, b.value, a.value, CAST(a.value_date AS VARCHAR)
    FROM who w LEFT JOIN before b USING (player_id) LEFT JOIN after a USING (player_id)""").fetchall():
    values[str(pid)] = (before, after, after_date)

#########One row per group membership############

outcomes = []
for (group, need, plan_letter, pid, name) in people:
    row = {"group": group, "need": need, "plan": plan_letter, "player_id": pid, "player": name, "note": ""}
    rows = clubs_of.get(pid, [])
    if not rows:
        # Not zero: there is no league record in the covered leagues
        row["note"] = "no league minutes in the covered leagues in 2025/26"
    else:
        main = main_club[pid]
        row.update({
            "clubs_played_for": len(rows),
            "main_club": main["club"], "main_club_league": main["league"],
            "main_club_league_minutes": main["league_minutes"],
            "main_club_league_matches": main["club_league_matches"],
            "share_of_main_club_league_minutes": main["club_minutes_share"],
            "main_club_starts": main["starts"], "main_club_goals": main["goals"], "main_club_assists": main["assists"],
            "main_club_goals_assists_per_90": (round(90.0 * (main["goals"] + main["assists"]) / main["league_minutes"], 2)
                                               if main["league_minutes"] > 0 else ""),
            "main_club_team_conceded_per_start": (round(main["team_conceded_in_starts"] / main["starts"], 2)
                                                  if main["starts"] else ""),
            "season_league_minutes_all_clubs": sum(r["league_minutes"] for r in rows),
            "season_goals_all_clubs": sum(r["goals"] for r in rows),
            "season_assists_all_clubs": sum(r["assists"] for r in rows),
        })
        if len(rows) > 1:
            row["note"] = "played for " + str(len(rows)) + " clubs; main-club columns use that club only"
    before, after, after_date = values[pid]
    if before is not None:
        row["value_at_cutoff_gbp_m"] = round(before * EUR_TO_GBP / 1e6, 1)
    if after is not None:
        row["value_latest_gbp_m"] = round(after * EUR_TO_GBP / 1e6, 1)
        row["value_date"] = after_date
        if before:
            row["value_change_pct"] = round(100.0 * (after - before) / before, 1)
    else:
        row["note"] = (row["note"] + "; " if row["note"] else "") + "no valuation after the cutoff"
    outcomes.append(row)

outcome_columns = ["group", "need", "plan", "player_id", "player", "clubs_played_for", "main_club", "main_club_league",
                   "main_club_league_minutes", "main_club_league_matches", "share_of_main_club_league_minutes",
                   "main_club_starts", "main_club_goals", "main_club_assists", "main_club_goals_assists_per_90",
                   "main_club_team_conceded_per_start", "season_league_minutes_all_clubs", "season_goals_all_clubs",
                   "season_assists_all_clubs", "value_at_cutoff_gbp_m", "value_latest_gbp_m", "value_date",
                   "value_change_pct", "note"]
write_table(os.path.join(OUT, "player_outcomes.csv"), outcome_columns, outcomes)

club_columns = ["player_id", "player", "club_id", "club", "league", "league_minutes", "club_league_matches",
                "club_minutes_share", "starts", "goals", "assists", "team_conceded_in_starts", "is_main_club"]
names = {}
for (group, need, plan_letter, pid, name) in people:
    names[pid] = name
club_output = []
for pid in sorted(clubs_of, key=int):
    for r in clubs_of[pid]:
        r["player"] = names[pid]
        club_output.append(r)
write_table(os.path.join(OUT, "player_club_outcomes.csv"), club_columns, club_output)

#########Group summaries############

# The evaluation plan asks for averages and counts. Medians are shown as well,
# but were added after the outcomes had been seen.
MEASURES = [("share_of_main_club_league_minutes", "share of main club's league minutes"),
            ("value_change_pct", "change in market value, %")]
GROUPS = ["base signing", "direct alternative", "actual United signing", "sold in the base plan"]
summary = []
for group in GROUPS + ["all groups"]:
    members = [r for r in outcomes if group == "all groups" or r["group"] == group]
    for key, label in MEASURES:
        valid = [r[key] for r in members if r.get(key, "") != ""]
        summary.append({
            "group": group, "measure": label, "memberships": len(members),
            "distinct_players": len(set(r["player_id"] for r in members)),
            "valid_observations": len(valid),
            "mean": round(statistics.mean(valid), 3) if valid else "",
            "median_added_after_evaluation": round(statistics.median(valid), 3) if valid else "",
        })
summary_columns = ["group", "measure", "memberships", "distinct_players", "valid_observations", "mean",
                   "median_added_after_evaluation"]
write_table(os.path.join(OUT, "group_summary.csv"), summary_columns, summary)


#########A readable page############

def table(rows, columns, headers=None):
    lines = ["| " + " | ".join(headers or columns) + " |", "|" + "---|" * len(columns)]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return "\n".join(lines)


def role_measure(row):
    """The role-specific measure named in the evaluation plan, at the main club."""
    if row["need"] in DEFENSIVE_ROLES:
        value = row.get("main_club_team_conceded_per_start", "")
        return ("conceded per start " + str(value)) if value != "" else ""
    value = row.get("main_club_goals_assists_per_90", "")
    return ("goals+assists per 90 " + str(value)) if value != "" else ""


for row in outcomes:
    row["role_measure"] = role_measure(row) if row["need"] else ""
multi = [r for r in club_output if len(clubs_of[r["player_id"]]) > 1]
page = [
    "# Evaluation on 2025/26 (corrected calculation)", "",
    "Produced by `src/evaluate_results.py` from the frozen lists in `" + os.path.relpath(FREEZE, os.path.join(HERE, "..")) + "`, "
    "after checking every frozen file against the freeze manifest. Players are evaluated at the clubs they played for. "
    "No league position is inferred for a United squad that never existed.", "",
    "## Group summaries", "",
    "Means and counts are the summaries the evaluation plan named before outcomes were seen. Medians were added "
    "afterwards, as an extra description; they were not part of the plan. A player can belong to more than one group "
    "(for example a base signing that United also signed), so memberships can exceed distinct players.", "",
    table(summary, summary_columns), "",
    "Goals and assists are not averaged across groups, because they mean different things in different roles. "
    "They are shown per player below, at the player's main club.", "",
    "## Players", "",
    table(outcomes, ["group", "need", "plan", "player", "main_club", "share_of_main_club_league_minutes",
                     "season_league_minutes_all_clubs", "role_measure", "value_change_pct", "note"]), "",
    "## Players who played for more than one club", "",
    "Each club's share uses that club's minutes and that club's league matches.", "",
    table(multi, ["player", "club", "league", "league_minutes", "club_league_matches", "club_minutes_share",
                  "is_main_club"]), "",
    "## Moves into United's organisation in the window", "",
    "Every move into Manchester United or its own youth sides dated " + WINDOW_START + " to " + WINDOW_END + " in the "
    "transfer records, as reviewed in `docs/actual_united_arrivals_2025.csv`. Only permanent arrivals into the senior "
    "squad form the comparison group. The group was fixed from the transfer records, not from later performance.", "",
    table(reviewed, ["name", "date", "from_club", "to_side", "classification", "in_comparison_group"]), ""]
with open(os.path.join(OUT, "EVALUATION.md"), "w") as file:
    file.write("\n".join(page))

# Code version, inputs and command of this evaluation
def git(*args):
    return subprocess.run(["git"] + list(args), cwd=HERE, capture_output=True, text=True).stdout.strip()


inputs = {"docs/actual_united_arrivals_2025.csv": file_hash(os.path.join(DOCS, "actual_united_arrivals_2025.csv")),
          "data/processed/club_family.csv": file_hash(os.path.join(HERE, "..", "data", "processed", "club_family.csv"))}
for table_name in ["appearances", "games", "game_lineups", "player_valuations", "transfers", "clubs"]:
    inputs["data/raw/transfermarkt/" + table_name + ".csv.gz"] = file_hash(os.path.join(RAW, table_name + ".csv.gz"))
with open(os.path.join(OUT, "evaluation_manifest.json"), "w") as file:
    json.dump({
        "written": datetime.datetime.now().isoformat(timespec="seconds"),
        "code_commit": git("rev-parse", "HEAD"),
        "uncommitted_code_or_inputs": git("status", "--porcelain", "--", "../src", "../docs", "../data/processed") != "",
        "freeze_folder": os.path.relpath(FREEZE, os.path.join(HERE, "..")),
        "frozen_files_verified": len(freeze_manifest["frozen_file_sha256"]),
        "command": "python src/evaluate_results.py --freeze " + os.path.relpath(FREEZE, os.path.join(HERE, ".."))
                   + " --out " + os.path.relpath(OUT, os.path.join(HERE, "..")),
        "python": sys.version.split()[0],
        "packages": {"duckdb": metadata.version("duckdb")},
        "input_sha256": inputs,
        "season": SEASON, "window": [WINDOW_START, WINDOW_END], "value_up_to": VALUE_UP_TO,
    }, file, indent=1, sort_keys=True)

print("Group memberships:", len(outcomes), "| distinct players:", len(set(r["player_id"] for r in outcomes)),
      "| without league minutes:", len([r for r in outcomes if "main_club" not in r]),
      "| played for more than one club:", len(set(r["player_id"] for r in multi)))
for row in summary:
    print(row)
