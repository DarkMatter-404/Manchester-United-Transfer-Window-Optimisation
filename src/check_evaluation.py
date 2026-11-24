"""Check the evaluation outputs against the raw match records, one club at a time.

Minutes and match counts are recomputed here in plain Python from the raw
rows, without reusing the evaluation script's queries, and compared with what
the evaluation wrote.

Run from the repository root, after evaluate_results.py:
    python src/check_evaluation.py --freeze results/freeze --evaluation results/corrections/2026-11-18/evaluation
The script exits with an error code if any check fails.
"""

import csv
import os
import sys

import duckdb

from output_paths import input_folder

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw", "transfermarkt")
DOCS = os.path.join(HERE, "..", "docs")
LEAGUES = ["GB1", "ES1", "IT1", "L1", "FR1", "NL1", "PO1", "BE1", "TR1", "RU1", "UKR1", "GR1", "SC1", "DK1"]
SEASON = 2025

FREEZE = input_folder("--freeze")
EVALUATION = input_folder("--evaluation")
failures = []


def check(label, condition, detail=""):
    if condition:
        print("PASS", label, "|", detail)
    else:
        failures.append(label)
        print("FAIL", label, "|", detail)


def read_table(folder, name):
    with open(os.path.join(folder, name), newline="") as file:
        return list(csv.DictReader(file))


outcomes = read_table(EVALUATION, "player_outcomes.csv")
club_rows = read_table(EVALUATION, "player_club_outcomes.csv")

#########Keys and identities############

keys = [(r["group"], r["player_id"]) for r in outcomes]
check("one row per group and player", len(keys) == len(set(keys)), str(len(keys)) + " rows")
club_keys = [(r["player_id"], r["club_id"]) for r in club_rows]
check("one row per player and club", len(club_keys) == len(set(club_keys)), str(len(club_keys)) + " rows")

known = set(r["player_id"] for r in read_table(FREEZE, "candidates_considered.csv"))
known |= set(r["player_id"] for r in read_table(FREEZE, "preferred_plan.csv"))
known |= set(r["player_id"] for r in read_table(DOCS, "actual_united_arrivals_2025.csv"))
unknown = [r["player"] for r in outcomes if r["player_id"] not in known]
check("every evaluated player id comes from the frozen lists or the reviewed arrivals", not unknown, ", ".join(unknown))

names_by_id = {}
for r in outcomes:
    names_by_id.setdefault(r["player_id"], set()).add(r["player"])
check("each player id has one name", all(len(v) == 1 for v in names_by_id.values()))

memberships = len(outcomes)
distinct = len(set(r["player_id"] for r in outcomes))
check("memberships and distinct players counted", memberships >= distinct, str(memberships) + " memberships, " + str(distinct) + " distinct players")

#########Recompute every club row from the raw records############

con = duckdb.connect()
league_list = ", ".join("'" + code + "'" for code in LEAGUES)
games = {}
for (game_id, league, home, away) in con.execute(
        "SELECT game_id, competition_id, home_club_id, away_club_id FROM read_csv_auto('"
        + os.path.join(RAW, "games.csv.gz") + "') WHERE season = " + str(SEASON)
        + " AND competition_id IN (" + league_list + ")").fetchall():
    games[game_id] = (league, home, away)

matches_of = {}
for (league, home, away) in games.values():
    matches_of[(home, league)] = matches_of.get((home, league), 0) + 1
    matches_of[(away, league)] = matches_of.get((away, league), 0) + 1

ids = sorted(set(int(r["player_id"]) for r in outcomes))
raw_minutes = {}
for (pid, game_id, club_id, played) in con.execute(
        "SELECT player_id, game_id, player_club_id, minutes_played FROM read_csv_auto('"
        + os.path.join(RAW, "appearances.csv.gz") + "') WHERE player_id IN (" + ", ".join(str(i) for i in ids) + ")").fetchall():
    if game_id in games and club_id in (games[game_id][1], games[game_id][2]):
        key = (str(pid), str(club_id), games[game_id][0])
        raw_minutes[key] = raw_minutes.get(key, 0) + played

wrong = []
for r in club_rows:
    key = (r["player_id"], r["club_id"], r["league"])
    minutes = raw_minutes.get(key, 0)
    matches = matches_of.get((int(r["club_id"]), r["league"]), 0)
    share = round(minutes / (90.0 * matches), 4) if matches else None
    if minutes != int(r["league_minutes"]) or matches != int(r["club_league_matches"]) or share != float(r["club_minutes_share"]):
        wrong.append(r["player"] + " at " + r["club"])
check("every club row: minutes, matches and share recomputed from raw rows", not wrong, str(len(club_rows)) + " rows; " + ", ".join(wrong))
missing_rows = [k for k in raw_minutes if k not in set((r["player_id"], r["club_id"], r["league"]) for r in club_rows)]
check("no raw league minutes left out of the club rows", not missing_rows, str(len(missing_rows)) + " left out")

#########Player summaries use the main club's own numerator and denominator############

clubs_of = {}
for r in club_rows:
    clubs_of.setdefault(r["player_id"], []).append(r)
problems = []
for r in outcomes:
    rows = clubs_of.get(r["player_id"], [])
    if not rows:
        if r["share_of_main_club_league_minutes"] != "" or "no league minutes" not in r["note"]:
            problems.append(r["player"] + ": missing outcome not left blank")
        continue
    main = [c for c in rows if c["is_main_club"] == "yes"]
    if len(main) != 1:
        problems.append(r["player"] + ": not exactly one main club")
        continue
    main = main[0]
    if int(main["league_minutes"]) != max(int(c["league_minutes"]) for c in rows):
        problems.append(r["player"] + ": main club is not the club with most minutes")
    if r["main_club"] != main["club"] or int(r["main_club_league_minutes"]) != int(main["league_minutes"]):
        problems.append(r["player"] + ": main-club columns do not match the main club row")
    if float(r["share_of_main_club_league_minutes"]) != float(main["club_minutes_share"]):
        problems.append(r["player"] + ": share does not equal the main club's own share")
    if int(r["season_league_minutes_all_clubs"]) != sum(int(c["league_minutes"]) for c in rows):
        problems.append(r["player"] + ": season total is not the sum over clubs")
check("player summaries: main club share, season totals and missing values", not problems, "; ".join(problems))

#########The three kinds of case are present and correct############

by_clubs = {}
for pid, rows in clubs_of.items():
    leagues = set(c["league"] for c in rows)
    kind = "one club" if len(rows) == 1 else ("two clubs, same league" if len(leagues) == 1 else "two clubs, different leagues")
    by_clubs.setdefault(kind, []).append(pid)
name_of = {r["player_id"]: r["player"] for r in outcomes}
for kind in ["one club", "two clubs, same league", "two clubs, different leagues"]:
    examples = by_clubs.get(kind, [])
    check("case present: " + kind, len(examples) > 0, ", ".join(sorted(name_of[p] for p in examples))[:120])

for pid in by_clubs.get("two clubs, same league", []) + by_clubs.get("two clubs, different leagues", []):
    rows = clubs_of[pid]
    main = [c for c in rows if c["is_main_club"] == "yes"][0]
    total = sum(int(c["league_minutes"]) for c in rows)
    old_style = round(total / (90.0 * int(main["club_league_matches"])), 4)
    print("     ", name_of[pid] + ":", ", ".join(c["club"] + " " + c["league_minutes"] + " min of " + c["club_league_matches"]
                                            + " matches" for c in rows),
          "| main-club share", main["club_minutes_share"], "| season total over main club's matches would be", old_style)

no_minutes = [r["player"] for r in outcomes if r["share_of_main_club_league_minutes"] == ""]
check("missing outcomes kept blank, not zero", all(r["share_of_main_club_league_minutes"] != "0" for r in outcomes),
      str(len(no_minutes)) + " without league minutes: " + ", ".join(no_minutes))

#########The comparison group follows the reviewed list and the planned window############

actual = [r for r in read_table(DOCS, "actual_united_arrivals_2025.csv") if r["in_comparison_group"] == "yes"]
evaluated = sorted(r["player_id"] for r in outcomes if r["group"] == "actual United signing")
check("actual-signing group is exactly the reviewed permanent arrivals", evaluated == sorted(r["player_id"] for r in actual),
      ", ".join(r["name"] for r in actual))
check("no comparison move after 1 September 2025", all(r["date"] <= "2025-09-01" for r in actual))

print()
if failures:
    print("FAILED checks:", ", ".join(failures))
    sys.exit(1)
print("All evaluation checks passed.")
