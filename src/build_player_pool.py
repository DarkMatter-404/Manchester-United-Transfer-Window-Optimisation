"""Build the player pool: existing players, candidates and fixed arrivals.

Existing players and fixed arrivals come from the hand-checked roster file.
Candidates are found by applying the agreed recruitment filters to the
decision-time tables. Eligible roles come from positions actually started.

Inputs:   data/processed/players_at_cutoff.csv, player_seasons.csv,
          player_role_starts.csv and docs/roster_reconciliation.csv
Outputs:  data/processed/pool_players.csv, pool_roles.csv,
          excluded_candidates.csv and docs/exclusions.csv

Run from the repository root, after prepare_inputs.py:
    python src/build_player_pool.py
"""

import csv
import os

from club_spells import two_year_status

HERE = os.path.dirname(os.path.abspath(__file__))
PROCESSED = os.path.join(HERE, "..", "data", "processed")
DOCS = os.path.join(HERE, "..", "docs")

# Recruitment filters for discretionary candidates
CANDIDATE_LEAGUES = ["GB1", "ES1", "IT1", "L1", "FR1"]   # England, Spain, Italy, Germany, France
MAX_AGE = 26               # completed years on 31 May 2025
MIN_MINUTES = 900          # league minutes in 2024/25
SIGNED_SINCE = "2023-06-01"    # a current spell that began on or after this date is "within two years"
UNDER_21_FROM = "2004-01-01"   # born on or after this date: no senior-list place needed in 2025/26

# A player is eligible for a role after this many starts in it over 2023/24 and 2024/25
MIN_ROLE_STARTS = 5


def read_table(path):
    with open(path, newline="") as file:
        return list(csv.DictReader(file))


def write_table(path, columns, rows):
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row[c] for c in columns])


#########Read the decision-time tables############

players = {row["player_id"]: row for row in read_table(os.path.join(PROCESSED, "players_at_cutoff.csv"))}

# League minutes in 2024/25, and the share of the club's minutes they represent
minutes_2024 = {}
minutes_share_2024 = {}
for row in read_table(os.path.join(PROCESSED, "player_seasons.csv")):
    if row["season"] == "2024":
        minutes_2024[row["player_id"]] = int(row["minutes"])
        minutes_share_2024[row["player_id"]] = float(row["minutes_share"])

# League position of every club in 2024/25, by points per match
club_rank = {}
by_league = {}
for row in read_table(os.path.join(PROCESSED, "club_seasons.csv")):
    if row["season"] == "2024":
        by_league.setdefault(row["league"], []).append((float(row["points"]) / float(row["matches"]), row["club_id"]))
for league in by_league:
    ordered = sorted(by_league[league], reverse=True)
    for position, (points_per_match, club_id) in enumerate(ordered):
        club_rank[club_id] = position + 1

# Starts by role over the two seasons
role_starts = {}
for row in read_table(os.path.join(PROCESSED, "player_role_starts.csv")):
    role_starts.setdefault(row["player_id"], {})[row["role"]] = int(row["starts_total"])

roster = read_table(os.path.join(DOCS, "roster_reconciliation.csv"))
# United's own players, whatever their status. A row marked C is a player at
# another club who is recorded there only to document a ruling.
united_ids = set(row["player_id"] for row in roster if row["model_set"] != "C")


# Joining dates entered by hand where the transfer records cannot settle a case
overrides = {row["player_id"]: row for row in read_table(os.path.join(DOCS, "joining_date_overrides.csv"))}


def eligible_roles(p):
    """Roles with enough starts; otherwise the role of the stored main position."""
    starts = role_starts.get(p, {})
    roles = [(g, n, "starts") for g, n in starts.items() if n >= MIN_ROLE_STARTS]
    if not roles and p in players and players[p]["main_role"]:
        g = players[p]["main_role"]
        roles = [(g, starts.get(g, 0), "main position")]
    return roles


pool = []          # one row per player in the model
pool_roles = []    # one row per eligible player-role pair
excluded = []      # big-five players of the right age who fail another filter
problems = []

#########Existing players and fixed arrivals############

for row in roster:
    if row["model_set"] not in ("E", "K"):
        continue
    p = row["player_id"]
    info = players.get(p)
    roles = eligible_roles(p)
    if info is None:
        # A fixed arrival from outside the covered leagues has no match data here
        problems.append(row["name"] + ": no match data in the covered leagues; role, value and score must be entered by hand")
    elif not roles:
        problems.append(row["name"] + ": no eligible role found")
    pool.append({
        "player_id": p,
        "name": row["name"],
        "status": row["model_set"],
        "date_of_birth": row["date_of_birth"],
        "age_at_cutoff": info["age_at_cutoff"] if info else "",
        "club_name": info["club_name"] if info else "",
        "country": info["country_of_citizenship"] if info else "",
        "league": info["league"] if info else "",
        "value_gbp_m": info["value_gbp_m"] if info else "",
        "value_date": info["value_date"] if info else "",
        "minutes_2024": minutes_2024.get(p, 0),
        "minutes_share_2024": minutes_share_2024.get(p, 0),
        "club_rank_2024": club_rank.get(info["club_id"], "") if info else "",
        "joined_club_date": info["joined_club_date"] if info else "",
        "two_year_status": "",
        "two_year_evidence": "",
        # The home-grown mark exists only for senior-list players. It is left at 0
        # for the others, which has no effect while they need no senior place.
        "homegrown": row["homegrown_mark"] if row["homegrown_mark"] != "" else 0,
        "senior_reg": row["senior_place_2025_26"],
        "roles": "/".join(sorted(g for g, n, basis in roles)),
    })
    for g, n, basis in roles:
        pool_roles.append({"player_id": p, "role": g, "starts_total": n, "basis": basis})

#########Candidates############

counts = {"with league minutes in the 14 covered leagues": 0, "already in the United roster file": 0,
          "outside the candidate leagues": 0, "older than the age limit or age unknown": 0,
          "below the minutes threshold": 0, "no valuation before the cutoff": 0, "no eligible role": 0,
          "candidates kept": 0,
          "of these: current spell began within two years of the cutoff": 0,
          "of these: start of current spell not verified": 0,
          "of these: eligible under the two-year rule": 0}

for p, info in players.items():
    counts["with league minutes in the 14 covered leagues"] += 1

    # United's own players, including those out on loan, are never candidates
    if p in united_ids or info["club_id"] == "985":
        counts["already in the United roster file"] += 1
        continue
    if info["league"] not in CANDIDATE_LEAGUES:
        counts["outside the candidate leagues"] += 1
        continue
    if info["age_at_cutoff"] == "" or float(info["age_at_cutoff"]) > MAX_AGE:
        counts["older than the age limit or age unknown"] += 1
        continue

    # From here on the player is in a candidate league and young enough;
    # anyone dropped is listed by name with the reason
    reason = None
    roles = eligible_roles(p)
    if minutes_2024.get(p, 0) < MIN_MINUTES:
        reason = "below the minutes threshold"
    elif info["value_gbp_m"] == "":
        reason = "no valuation before the cutoff"
    elif not roles:
        reason = "no eligible role"
    if reason is not None:
        counts[reason] += 1
        excluded.append({"player_id": p, "name": info["name"], "club_name": info["club_name"],
                         "league": info["league"], "age_at_cutoff": info["age_at_cutoff"],
                         "minutes_2024": minutes_2024.get(p, 0), "reason": reason})
        continue

    counts["candidates kept"] += 1
    # Every candidate stays in this file so that all runs score players against
    # the same group. The two-year rule is applied when a run is built.
    status, evidence = two_year_status(info, overrides.get(info["player_id"]), SIGNED_SINCE)
    if status == "joined within two years":
        counts["of these: current spell began within two years of the cutoff"] += 1
    elif status == "not verified":
        counts["of these: start of current spell not verified"] += 1
    else:
        counts["of these: eligible under the two-year rule"] += 1
    pool.append({
        "player_id": p,
        "name": info["name"],
        "status": "C",
        "date_of_birth": info["date_of_birth"],
        "age_at_cutoff": info["age_at_cutoff"],
        "club_name": info["club_name"],
        "country": info["country_of_citizenship"],
        "league": info["league"],
        "value_gbp_m": info["value_gbp_m"],
        "value_date": info["value_date"],
        "minutes_2024": minutes_2024[p],
        "minutes_share_2024": minutes_share_2024[p],
        "club_rank_2024": club_rank.get(info["club_id"], ""),
        "joined_club_date": info["joined_club_date"],
        "two_year_status": status,
        "two_year_evidence": evidence,
        # Home-grown status is not in the data; a candidate is treated as not
        # home-grown until checked by hand
        "homegrown": 0,
        "senior_reg": 0 if info["date_of_birth"] >= UNDER_21_FROM else 1,
        "roles": "/".join(sorted(g for g, n, basis in roles)),
    })
    for g, n, basis in roles:
        pool_roles.append({"player_id": p, "role": g, "starts_total": n, "basis": basis})

#########Checks############

ids = [row["player_id"] for row in pool]
if len(set(ids)) != len(ids):
    problems.append("A player appears twice in the pool.")
for row in pool:
    if row["status"] == "C":
        if float(row["age_at_cutoff"]) > MAX_AGE or row["league"] not in CANDIDATE_LEAGUES:
            problems.append("Candidate breaks a recruitment rule: " + row["name"])
        if row["roles"] == "":
            problems.append("Candidate has no role: " + row["name"])

#########Save and summarise############

write_table(os.path.join(PROCESSED, "pool_players.csv"),
            ["player_id", "name", "status", "date_of_birth", "age_at_cutoff", "club_name", "country", "league",
             "value_gbp_m", "value_date", "minutes_2024", "minutes_share_2024", "club_rank_2024",
             "joined_club_date", "two_year_status", "two_year_evidence", "homegrown", "senior_reg", "roles"], pool)
write_table(os.path.join(PROCESSED, "pool_roles.csv"),
            ["player_id", "role", "starts_total", "basis"], pool_roles)
write_table(os.path.join(PROCESSED, "excluded_candidates.csv"),
            ["player_id", "name", "club_name", "league", "age_at_cutoff", "minutes_2024", "reason"], excluded)

# Exclusion log: one line per filter, in the order the filters are applied
log = [{"step": i + 1, "filter": name, "players": n} for i, (name, n) in enumerate(counts.items())]
write_table(os.path.join(DOCS, "exclusions.csv"), ["step", "filter", "players"], log)

for name, n in counts.items():
    print(name + ":", n)
for status in ("E", "K", "C"):
    print("Pool, status", status + ":", len([row for row in pool if row["status"] == status]))
for g in ["GK", "CB", "WB", "CM", "AM", "ST"]:
    eligible = set(row["player_id"] for row in pool_roles if row["role"] == g)
    existing = [row for row in pool if row["status"] == "E" and row["player_id"] in eligible]
    candidates = [row for row in pool if row["status"] == "C" and row["player_id"] in eligible]
    print("Eligible for", g + ":", len(existing), "existing,", len(candidates), "candidates")
print("Eligible player-role pairs:", len(pool_roles))

if problems:
    print()
    print("To resolve:")
    for text in problems:
        print(" -", text)
