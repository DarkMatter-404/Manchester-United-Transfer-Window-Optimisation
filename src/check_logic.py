"""Focused checks of the input rules: club identity, spells, fees, wages and alternatives.

The first groups use small invented histories. The others read the processed
tables and a set of saved run results.

Run from the repository root, after run_scenarios.py:
    python src/check_logic.py --results results/corrections/2026-11-18/model
The script exits with an error code if any check fails.
"""

import csv
import os
import sys

from club_spells import club_families, order_moves, current_spell, in_club_by, two_year_status
from model_inputs import (PROCESSED, read_table, base_settings, base_params, band_wage, fee_multiplier,
                          candidate_terms, build_data)
from output_paths import input_folder

RESULTS = input_folder("--results")
SIGNED_SINCE = "2023-06-01"
failures = []


def check(label, condition, detail=""):
    if condition:
        print("PASS", label, "|", detail)
    else:
        failures.append(label)
        print("FAIL", label, "|", detail)


def move(date, from_id, from_name, to_id, to_name, fee):
    return {"date": date, "from_id": from_id, "from_name": from_name, "to_id": to_id, "to_name": to_name, "fee": fee}


def spell(history, family, senior):
    moves, ambiguous = order_moves(history)
    return current_spell(moves, family, senior)


#########1. Club identity: invented clubs with similar names############

names_of = {1: ["Real Sociedad"], 2: ["Real Unión"], 3: ["Real Sociedad B"], 4: ["Real Unión B"],
            10: ["Man City"], 11: ["Man City U21"], 12: ["Man Utd"], 13: ["Man Utd U21"],
            20: ["AC Milan"], 21: ["Milan U19"], 30: ["Athletic Bilbao"], 31: ["Bilbao Athletic"]}
rows, ambiguous = club_families(names_of, {1, 2, 10, 12, 20, 30}, {20: ["Milan"]}, {31: 30})
owner = {member: senior for (member, senior, basis) in rows}
check("Real Sociedad B belongs to Real Sociedad, Real Unión B to Real Unión", owner.get(3) == 1 and owner.get(4) == 2,
      str(owner))
check("Real Unión is not part of Real Sociedad", 2 not in owner)
check("Man City U21 and Man Utd U21 go to different clubs", owner.get(11) == 10 and owner.get(13) == 12)
check("a short name entered by hand links Milan U19 to AC Milan", owner.get(21) == 20)
check("a side entered by hand links Bilbao Athletic to Athletic Bilbao", owner.get(31) == 30)
check("no side is linked to two clubs", not ambiguous)

# Without the hand-entered short name, Milan U19 is not guessed
rows, ambiguous = club_families(names_of, {20}, {}, {})
check("Milan U19 is not linked to AC Milan by a guess", 21 not in [m for (m, s, b) in rows])

#########2. Start of the current spell: invented histories############

# Club 1 Rovers with youth side 11; club 2 Town; club 3 City with youth side 31
ROVERS = {1, 11}

history = [move("2020-01-30", 2, "Town", 1, "Rovers", 0), move("2020-06-30", 1, "Rovers", 2, "Town", 0),
           move("2022-07-01", 2, "Town", 3, "City", 5000000), move("2024-08-22", 3, "City", 1, "Rovers", 20000000)]
start, basis = spell(history, ROVERS, 1)
check("new signing after an earlier spell", start == "2024-08-22", str(start) + ", " + basis)

history = [move("2019-07-25", 2, "Town", 1, "Rovers", 30000000), move("2019-07-26", 1, "Rovers", 2, "Town", 0),
           move("2020-06-30", 2, "Town", 1, "Rovers", 0), move("2021-07-15", 1, "Rovers", 3, "City", 0),
           move("2022-06-30", 3, "City", 1, "Rovers", 0)]
start, basis = spell(history, ROVERS, 1)
check("return from loan keeps the original signing", start == "2019-07-25", str(start) + ", " + basis)

history = [move("2023-01-01", 2, "Town", 1, "Rovers", 0), move("2023-06-30", 1, "Rovers", 2, "Town", 0),
           move("2023-07-01", 2, "Town", 1, "Rovers", 50000000)]
start, basis = spell(history, ROVERS, 1)
check("loan made permanent dates from the loan", start == "2023-01-01", str(start) + ", " + basis)

history = [move("2015-07-01", 2, "Town", 11, "Rovers U17", None), move("2023-07-01", 11, "Rovers U19", 1, "Rovers", None)]
start, basis = spell(history, ROVERS, 1)
check("internal promotion dates from joining the youth side", start == "2015-07-01", str(start) + ", " + basis)

history = [move("2019-07-01", 2, "Town", 31, "City U18", 1300000), move("2024-07-13", 31, "City U21", 1, "Rovers", 17850000)]
start, basis = spell(history, ROVERS, 1)
check("signing from another club's youth side is an ordinary signing", start == "2024-07-13", str(start) + ", " + basis)

# The Aramburu pattern: youth side of Rovers, away for years, then back through another club
history = [move("2017-12-31", 11, "Rovers Y", 2, "Town", None), move("2022-07-20", 2, "Town", 3, "City", None),
           move("2023-08-01", 3, "City", 11, "Rovers B", None), move("2024-07-01", 11, "Rovers B", 1, "Rovers", None)]
start, basis = spell(history, ROVERS, 1)
check("return through another club starts a new spell", start == "2023-08-01", str(start) + ", " + basis)

# Same-day moves given in the wrong order: a signing and a loan back on one day
history = [move("2020-07-01", 3, "City", 2, "Town", 0),
           move("2022-08-16", 1, "Rovers", 2, "Town", 0), move("2022-08-16", 2, "Town", 1, "Rovers", 18000000),
           move("2023-06-30", 2, "Town", 1, "Rovers", 0)]
moves, ambiguous = order_moves(history)
check("same-day moves put in a chain", [m["to_id"] for m in moves] == [2, 1, 2, 1] and not ambiguous)
start, basis = current_spell(moves, ROVERS, 1)
check("signing and loan back on one day, then return", start == "2022-08-16", str(start) + ", " + basis)

# Two same-day moves that cannot form a chain are reported, not guessed
moves, ambiguous = order_moves([move("2021-01-01", 2, "Town", 1, "Rovers", 0), move("2021-01-01", 3, "City", 1, "Rovers", 0)])
check("same-day moves that do not chain are reported", ambiguous == ["2021-01-01"])

#########3. Undated academy players: evidence decides############


def info(joined="", basis="", by="", evidence="", flag=""):
    return {"joined_club_date": joined, "joined_basis": basis, "in_club_by_date": by,
            "in_club_by_evidence": evidence, "history_flag": flag}


history = [move("2019-07-01", 11, "Rovers U19", 1, "Rovers", None)]
by, evidence = in_club_by(order_moves(history)[0], ROVERS, None)
status, why = two_year_status(info("", "came through the club's youth system", by, evidence), None, SIGNED_SINCE)
check("undated academy player with a dated record before the threshold is eligible", status == "eligible", why)

history = [move("2024-07-01", 11, "Rovers U19", 1, "Rovers", None)]
by, evidence = in_club_by(order_moves(history)[0], ROVERS, "2024-08-20")
status, why = two_year_status(info("", "came through the club's youth system", by, evidence), None, SIGNED_SINCE)
check("undated academy player with records only after the threshold is not verified", status == "not verified", why)

status, why = two_year_status(info("", "no move into the club on record"), None, SIGNED_SINCE)
check("no record at all is not verified", status == "not verified", why)

status, why = two_year_status(info("2022-01-01", "signed for a fee", flag="same-day moves on 2022-01-01 could not be put in order"),
                              None, SIGNED_SINCE)
check("an unordered same-day history is not verified", status == "not verified", why)

status, why = two_year_status(info(""), {"joined_club_date": "2022-08-16", "basis": "club announcement"}, SIGNED_SINCE)
check("a documented joining date entered by hand is used", status == "eligible", why)

#########4. Named real cases############

players = {row["name"]: row for row in read_table(PROCESSED, "players_at_cutoff.csv")}
pool = {row["name"]: row for row in read_table(PROCESSED, "pool_players.csv")}
family = list(csv.DictReader(open(os.path.join(PROCESSED, "club_family.csv"), newline="")))
members = {int(r["member_club_id"]): int(r["senior_club_id"]) for r in family if r["senior_club_id"]}

for name, date in [("Raoul Bellanova", "2024-08-22"), ("Liam Delap", "2024-07-13"), ("Jon Aramburu", "2023-08-01")]:
    check(name + ": current spell starts " + date, players[name]["joined_club_date"] == date, players[name]["joined_basis"])
    check(name + " is not eligible under the two-year rule", pool[name]["two_year_status"] == "joined within two years",
          pool[name]["two_year_status"])

check("Real Unión (12405) is not part of Real Sociedad (681)", members.get(12405) != 681)
check("Real Sociedad B (9899) is part of Real Sociedad (681)", members.get(9899) == 681)
check("Man City U21 (9265) is not part of Ipswich Town (677)", members.get(9265) != 677)
check("Arsenal U21 (9249) is not part of Manchester United (985)", members.get(9249) != 985)
check("Milan U19 (10958) is part of AC Milan (5)", members.get(10958) == 5)
check("FC Bayern II (28) is part of Bayern Munich (27)", members.get(28) == 27)
check("Pavlovic: promotion from FC Bayern II is not a new signing",
      pool["Aleksandar Pavlovic"]["two_year_status"] == "eligible", pool["Aleksandar Pavlovic"]["two_year_evidence"])

base_data, base_info, base_over = build_data(base_settings(), base_params()["fee_cap"])
status_of = {row["player_id"]: row["two_year_status"] for row in read_table(PROCESSED, "pool_players.csv")}
not_eligible = [p for p in base_data["C"] if status_of[p] != "eligible"]
check("base candidates are all eligible under the two-year rule", not not_eligible, str(len(base_data["C"])) + " candidates")

#########5. Wages: held fixed except in wage and combined scenarios############

pool_by_id = {row["player_id"]: row for row in read_table(PROCESSED, "pool_players.csv")}
free_agents = [row["player_id"] for row in read_table(os.path.join(os.path.dirname(PROCESSED), "..", "docs"), "free_agents.csv")]


def base_wage(p):
    """Wage from the complete base fee rule, for any candidate, available in the base run or not."""
    row = pool_by_id[p]
    return band_wage(fee_multiplier(row, base_settings()) * float(row["value_gbp_m"]))


def scenario(changes):
    settings = base_settings()
    settings.update(changes)
    return build_data(settings, base_params()["fee_cap"])[0]


fee_and_club_scenarios = {
    "fee only 0.9": {"alpha": 0.9, "alpha_english_pl": 1.3},
    "fee only 1.5": {"alpha": 1.5, "alpha_english_pl": 1.5},
    "club rules removed": {"blocked_clubs": [], "club_multiplier": {}, "elite_clubs": []},
    "elite-club mark-up 2.0": {"elite_club_multiplier": 2.0},
}
for label, changes in fee_and_club_scenarios.items():
    data = scenario(changes)
    changed = [data["name"][p] for p in data["C"] if abs(data["w"][p] - base_wage(p)) > 1e-9]
    newly = [p for p in data["C"] if p not in base_data["C"]]
    check(label + ": no candidate wage changes", not changed,
          str(len(data["C"])) + " candidates, " + str(len(newly)) + " not available in the base run")

data = scenario({"alpha": 1.5, "alpha_english_pl": 1.5})
dearer = [p for p in data["C"] if p in base_data["C"] and data["f"][p] > base_data["f"][p] + 1e-9]
check("fee only 1.5: fees do rise", len(dearer) > 0, str(len(dearer)) + " candidates cost more")

for factor in (0.9, 1.1):
    data = scenario({"candidate_wage_factor": factor})
    fee_changed = [p for p in data["C"] if abs(data["f"][p] - base_data["f"][p]) > 1e-9]
    wage_wrong = [p for p in data["C"] if abs(data["w"][p] - factor * base_wage(p)) > 1e-9]
    check("candidate wages x" + str(factor) + ": fees unchanged, wages scaled", not fee_changed and not wage_wrong)

data = scenario({"alpha": 0.9, "alpha_english_pl": 1.3, "wage_follows_fee": True})
moved = [p for p in data["C"] if abs(data["w"][p] - base_wage(p)) > 1e-9]
check("combined fee-and-wage 0.9: wages are allowed to follow the fee", len(moved) > 0, str(len(moved)) + " wages move")

david = pool["Jonathan David"]["player_id"]
for label, changes in fee_and_club_scenarios.items():
    data = scenario(changes)
    check(label + ": free agent's fee is zero and wage unchanged",
          data["f"][david] == 0 and abs(data["w"][david] - base_data["w"][david]) < 1e-9)

#########6. A high-value free agent is not removed by the fee ceiling############

invented = {"player_id": "X1", "value_gbp_m": "90", "country": "France", "league": "FR1",
            "club_name": "Invented FC", "minutes_share_2024": "0.6", "club_rank_2024": "9"}
fee, wage = candidate_terms(invented, base_settings(), ["X1"])
check("free agent worth 90: payable fee is zero, so within the ceiling",
      fee == 0 and fee <= base_params()["fee_cap"], "fee " + str(fee))
check("free agent worth 90: wage still follows the value", abs(wage - band_wage(99)) < 1e-9, "wage " + str(wage))
fee, wage = candidate_terms(invented, base_settings(), [])
check("same player under contract: fee of 99 is above the ceiling", fee > base_params()["fee_cap"], "fee " + str(round(fee, 2)))

#########7. Direct alternatives start in the role of the original target############

with open(os.path.join(RESULTS, "direct_alternatives.csv"), newline="") as file:
    direct = list(csv.DictReader(file))
wrong = [row["need"] + " " + row["plan"] + " " + row["player"] for row in direct
         if row["role"] != "" and (row["role"] != row["need"] or row["starts"] != "yes")]
check("every direct alternative starts in the needed role", not wrong, str(len(direct)) + " rows; " + ", ".join(wrong))

print()
if failures:
    print("FAILED checks:", ", ".join(failures))
    sys.exit(1)
print("All focused checks passed.")
