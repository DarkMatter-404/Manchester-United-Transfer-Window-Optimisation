"""Quality score (0 to 100) for every player in every eligible role.

Four components are computed for each player from records dated on or before
31 May 2025. Each component is turned into a percentile among the players
eligible for the same role, and the score is a weighted average of the four
percentiles. A second score leaves the market-value component out.

Inputs:   data/processed/pool_players.csv, pool_roles.csv, player_seasons.csv
Output:   data/processed/scores.csv

Run from the repository root, after build_player_pool.py:
    python src/score_players.py
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROCESSED = os.path.join(HERE, "..", "data", "processed")

# 2024/25 counts more than 2023/24
SEASON_WEIGHT = {"2024": 0.7, "2023": 0.3}

# Below these amounts the output component is not trusted and is set to 50
MIN_WEIGHTED_MINUTES = 900
MIN_WEIGHTED_STARTS = 10

# Weight of each component in each role; every row adds up to 1
WEIGHTS = {
    "ST": {"playing_time": 0.20, "output": 0.40, "team_level": 0.10, "value": 0.30},
    "AM": {"playing_time": 0.20, "output": 0.40, "team_level": 0.10, "value": 0.30},
    "WB": {"playing_time": 0.30, "output": 0.20, "team_level": 0.15, "value": 0.35},
    "CM": {"playing_time": 0.30, "output": 0.15, "team_level": 0.15, "value": 0.40},
    "CB": {"playing_time": 0.30, "output": 0.10, "team_level": 0.20, "value": 0.40},
    "GK": {"playing_time": 0.30, "output": 0.10, "team_level": 0.20, "value": 0.40},
}

# Output is goals conceded per start in these roles, goals plus assists per 90 in the others
DEFENSIVE_ROLES = ["CB", "GK"]


def read_table(name):
    with open(os.path.join(PROCESSED, name), newline="") as file:
        return list(csv.DictReader(file))


def percentiles(values):
    """Percentile of each player within a group. values maps player -> number.

    A player's percentile is the share of the group below them, counting
    half of the players tied with them, on a 0 to 100 scale.
    """
    result = {}
    n = len(values)
    for p in values:
        below = len([q for q in values if values[q] < values[p]])
        tied = len([q for q in values if values[q] == values[p]])
        result[p] = 100.0 * (below + 0.5 * tied) / n
    return result


#########Player statistics over the two seasons############

pool = read_table("pool_players.csv")
pool_roles = read_table("pool_roles.csv")
pool_ids = set(row["player_id"] for row in pool)

seasons = {}    # player -> list of season rows
for row in read_table("player_seasons.csv"):
    if row["player_id"] in pool_ids and row["season"] in SEASON_WEIGHT:
        seasons.setdefault(row["player_id"], []).append(row)

stats = {}
for row in pool:
    p = row["player_id"]
    rows = seasons.get(p, [])
    if not rows:
        raise ValueError("No season record for " + row["name"])

    # Season weights are rescaled when only one season is available
    total_weight = sum(SEASON_WEIGHT[r["season"]] for r in rows)
    weight = {r["season"]: SEASON_WEIGHT[r["season"]] / total_weight for r in rows}

    minutes = sum(weight[r["season"]] * float(r["minutes"]) for r in rows)
    goals_assists = sum(weight[r["season"]] * (float(r["goals"]) + float(r["assists"])) for r in rows)
    starts = sum(weight[r["season"]] * float(r["starts"]) for r in rows)
    conceded = sum(weight[r["season"]] * float(r["team_goals_against_in_starts"] or 0) for r in rows)

    stats[p] = {
        # Share of the club's league minutes the player played
        "playing_time": sum(weight[r["season"]] * float(r["minutes_share"]) for r in rows),
        # League points per match of the player's club
        "team_level": sum(weight[r["season"]] * float(r["club_points_per_game"]) for r in rows),
        # Latest market value before the cutoff, GBP million
        "value": float(row["value_gbp_m"]),
        "weighted_minutes": minutes,
        "weighted_starts": starts,
        "goals_assists_per_90": 90.0 * goals_assists / minutes if minutes > 0 else 0.0,
        "conceded_per_start": conceded / starts if starts > 0 else 0.0,
    }

#########Percentiles within each role and the score############

name = {row["player_id"]: row["name"] for row in pool}
status = {row["player_id"]: row["status"] for row in pool}
scores = []

for g in WEIGHTS:
    group = [row["player_id"] for row in pool_roles if row["role"] == g]

    pct = {}
    for component in ("playing_time", "team_level", "value"):
        pct[component] = percentiles({p: stats[p][component] for p in group})

    # Output: only players with enough minutes or starts are ranked
    if g in DEFENSIVE_ROLES:
        ranked = {p: -stats[p]["conceded_per_start"] for p in group
                  if stats[p]["weighted_starts"] >= MIN_WEIGHTED_STARTS}
    else:
        ranked = {p: stats[p]["goals_assists_per_90"] for p in group
                  if stats[p]["weighted_minutes"] >= MIN_WEIGHTED_MINUTES}
    pct["output"] = percentiles(ranked)

    w = WEIGHTS[g]
    for p in group:
        small_sample = p not in pct["output"]
        output = 50.0 if small_sample else pct["output"][p]
        quality = (w["playing_time"] * pct["playing_time"][p] + w["output"] * output
                   + w["team_level"] * pct["team_level"][p] + w["value"] * pct["value"][p])
        # Same score without market value; the other weights are scaled up to add to 1
        no_value = (w["playing_time"] * pct["playing_time"][p] + w["output"] * output
                    + w["team_level"] * pct["team_level"][p]) / (1.0 - w["value"])
        scores.append({
            "player_id": p, "name": name[p], "status": status[p], "role": g,
            "pct_playing_time": round(pct["playing_time"][p], 1),
            "pct_output": round(output, 1),
            "pct_team_level": round(pct["team_level"][p], 1),
            "pct_value": round(pct["value"][p], 1),
            "small_sample": 1 if small_sample else 0,
            "quality": round(quality, 2),
            "quality_no_value": round(no_value, 2),
        })

#########Save and summarise############

columns = ["player_id", "name", "status", "role", "pct_playing_time", "pct_output", "pct_team_level",
           "pct_value", "small_sample", "quality", "quality_no_value"]
with open(os.path.join(PROCESSED, "scores.csv"), "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(columns)
    for row in scores:
        writer.writerow([row[c] for c in columns])

print("Scored player-role pairs:", len(scores))
if len(scores) != len(pool_roles):
    raise ValueError("Some eligible player-role pairs were not scored.")
for g in WEIGHTS:
    group = [row for row in scores if row["role"] == g]
    values = sorted(row["quality"] for row in group)
    small = len([row for row in group if row["small_sample"] == 1])
    print(g, "| players", len(group), "| lowest", values[0], "| median", values[len(values) // 2],
          "| highest", values[-1], "| output set to 50 for", small)
