"""Small illustrative checks of the transfer model.

All players and numbers are invented. Each check solves a tiny instance with
Gurobi and compares the answer with (1) a result worked out by hand,
(2) a brute-force search over every possible plan and (3) totals recomputed
from the chosen players.

Run from the repository root:
    python src/toy_model.py
The script exits with an error code if any check fails.
"""

import copy
import itertools
import os
import sys

from transfer_model import read_inputs, solve_transfer_model
from check_solution import check_solution, print_solution

TOY_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "toy")


def toy_params():
    """Basic toy settings: one starter per role and no extra depth."""
    G = ["DEF", "MID", "FWD"]
    return {
        "G": G,
        "k": {g: 1 for g in G},        # starters per role
        "l": {g: 1 for g in G},        # minimum players per role
        "u": {g: 1 for g in G},        # maximum players per role
        "omega": {g: 1.0 for g in G},  # equal role weights
        "mu": 0.0,                     # no depth reward
        "lam": 0.0,                    # no development bonus
        "B": 40,                       # net transfer allowance, GBP million
        "F0": 0,                       # no fixed commitments
        "W": 10,                       # wage allowance, GBP million per year
        "TB": 6,                       # arrivals limit, not binding here
        "TS": 6,                       # sales limit, not binding here
        "senior_cap": 25,              # not binding with three players
        "non_hg_cap": 17,              # not binding with three players
        "fee_cap": 100,                # highest allowed fee for one candidate
    }


def add_player(data, p, status, roles, wage, fee=None, receipt=None,
               homegrown=0, senior_reg=1):
    """Add one invented player to a copy of the toy data."""
    data[status].append(p)
    data["name"][p] = p
    data["w"][p] = wage
    data["h"][p] = homegrown
    data["t"][p] = senior_reg
    data["a"][p] = 1.0
    data["d"][p] = 0.0
    if status == "C":
        data["f"][p] = fee
    if status == "E":
        data["r"][p] = receipt
    for g in roles:
        data["H"].append((p, g))
        data["q"][p, g] = roles[g]


def brute_force(data, params):
    """Try every combination of sales, purchases, cover roles and starters.

    Returns the best objective value, or None if no plan satisfies the rules.
    Only suitable for a handful of players.
    """
    E, C, K = data["E"], data["C"], data["K"]
    G = params["G"]
    q, a, d = data["q"], data["a"], data["d"]
    roles_of = {p: [g for (pp, g) in data["H"] if pp == p] for p in E + C + K}
    can_sell = [p for p in E if p not in params.get("no_sell", [])]
    can_buy = [p for p in C if p not in params.get("no_buy", [])]
    must_buy = params.get("must_buy", [])
    must_sell = params.get("must_sell", [])

    best = None
    for n_sold in range(len(can_sell) + 1):
        for sold in itertools.combinations(can_sell, n_sold):
            for n_bought in range(len(can_buy) + 1):
                for bought in itertools.combinations(can_buy, n_bought):
                    # Purchases and sales taken as given must be part of the plan
                    if [p for p in must_buy if p not in bought] or [p for p in must_sell if p not in sold]:
                        continue
                    squad = [p for p in E if p not in sold] + list(bought) + list(K)

                    # Transaction counts
                    if len(K) + len(bought) > params["TB"] or len(sold) > params["TS"]:
                        continue
                    # Net spending and wages
                    net = params["F0"] + sum(data["f"][p] for p in bought) - sum(data["r"][p] for p in sold)
                    if net > params["B"] + 1e-9:
                        continue
                    if sum(data["w"][p] for p in squad) > params["W"] + 1e-9:
                        continue
                    # Registration
                    senior = [p for p in squad if data["t"][p] == 1]
                    if len(senior) > params["senior_cap"]:
                        continue
                    if len([p for p in senior if data["h"][p] == 0]) > params["non_hg_cap"]:
                        continue

                    # Give every squad player one cover role, in every possible way
                    for roles in itertools.product(*[roles_of[p] for p in squad]):
                        value = 0.0
                        feasible = True
                        for g in G:
                            group = [p for p, role in zip(squad, roles) if role == g]
                            if len(group) < params["l"][g] or len(group) > params["u"][g]:
                                feasible = False
                                break
                            # Best choice of starters among the players allocated to this role
                            best_group = None
                            for starting in itertools.combinations(group, params["k"][g]):
                                # A candidate bought only to start in this role must be among the starters
                                missing = [p for p, role in params.get("start_role_if_bought", {}).items()
                                           if p in bought and ((role == g and p not in starting)
                                                               or (role != g and p in group))]
                                if missing:
                                    continue
                                score = 0.0
                                for p in group:
                                    if p in starting:
                                        score += params["omega"][g] * a[p] * q[p, g]
                                    else:
                                        score += params["mu"] * (a[p] * q[p, g] + params["lam"] * d[p])
                                if best_group is None or score > best_group:
                                    best_group = score
                            if best_group is None:
                                feasible = False
                                break
                            value += best_group
                        if feasible and (best is None or value > best):
                            best = value
    return best


def print_lineup_table(data, params, allowances):
    """List all 18 one-per-role lineups of the basic toy with their totals."""
    defenders = ["A", "D1", "D2"]
    midfielders = ["B", "M1"]
    forwards = ["C", "F1", "F2"]
    rows = []
    for lineup in itertools.product(defenders, midfielders, forwards):
        bought = [p for p in lineup if p in data["C"]]
        sold = [p for p in data["E"] if p not in lineup]
        score = sum(data["q"][p, g] for p, g in zip(lineup, params["G"]))
        net = sum(data["f"][p] for p in bought) - sum(data["r"][p] for p in sold)
        wages = sum(data["w"][p] for p in lineup)
        rows.append((score, lineup, net, wages))
    rows.sort(reverse=True)

    print("All 18 lineups (score, net spend in GBP million, wages in GBP million per year)")
    header = "  lineup         score  net  wages"
    for B in allowances:
        header += "  allowed at " + str(B)
    print(header)
    for score, lineup, net, wages in rows:
        line = "  " + "-".join(lineup).ljust(13) + str(int(score)).rjust(7) + str(int(net)).rjust(5) + str(int(wages)).rjust(7)
        for B in allowances:
            allowed = net <= B and wages <= params["W"]
            line += ("yes" if allowed else "no").rjust(15)
        print(line)
    print()


#########Checks###############

failures = []


def run_check(label, data, params, expected=None, show=False):
    """Solve one case and compare it with the brute-force search and expected values.

    expected may contain objective, sold, bought, starters, net_spend and wages.
    Use expected={"feasible": False} for a case that should have no valid plan.
    """
    sol = solve_transfer_model(data, params, model_name=label)
    best = brute_force(data, params)
    notes = []

    if expected is not None and expected.get("feasible") is False:
        # The case should have no valid plan at all
        if sol["has_solution"] or sol["status"] != "INFEASIBLE":
            notes.append("expected INFEASIBLE, got " + sol["status"])
        if best is not None:
            notes.append("brute force found a valid plan")
        detail = "status " + sol["status"] + ", conflicting rules: " + ", ".join(sol.get("iis", []))
    elif not sol["has_solution"]:
        notes.append("no solution, status " + sol["status"])
        detail = ""
    else:
        totals, problems = check_solution(data, params, sol)
        notes += problems
        if sol["status"] != "OPTIMAL":
            notes.append("status is " + sol["status"])
        if best is None or abs(best - sol["objective"]) > 1e-6:
            notes.append("brute force gives " + str(best) + ", solver gives " + str(sol["objective"]))
        if expected is not None:
            if "objective" in expected and abs(expected["objective"] - sol["objective"]) > 1e-6:
                notes.append("objective " + str(sol["objective"]) + " is not " + str(expected["objective"]))
            for key in ("sold", "bought"):
                if key in expected and sorted(expected[key]) != sorted(sol[key]):
                    notes.append(key + " " + str(sorted(sol[key])) + " is not " + str(sorted(expected[key])))
            if "starters" in expected and sorted(expected["starters"].items()) != sorted(sol["starters"]):
                notes.append("starters " + str(sol["starters"]) + " are not " + str(expected["starters"]))
            for key in ("net_spend", "wages", "purchase_fees", "sale_receipts"):
                if key in expected and abs(expected[key] - totals[key]) > 1e-6:
                    notes.append(key + " " + str(totals[key]) + " is not " + str(expected[key]))
        detail = ("objective " + str(round(sol["objective"], 3))
                  + ", starters " + "-".join(p for (p, g) in sol["starters"])
                  + ", net " + str(totals["net_spend"]) + ", wages " + str(totals["wages"]))
        if show:
            print_solution(data, params, sol, totals)

    if notes:
        failures.append(label)
        print("FAIL", label, "|", "; ".join(notes))
    else:
        print("PASS", label, "|", detail)
    return sol


base = read_inputs(TOY_FOLDER)
print_lineup_table(base, toy_params(), [40, 30])

# 1. Net allowance 40: buy D2 and F1, sell A and C
params = toy_params()
run_check("allowance_40", base, params,
          {"objective": 234, "sold": ["A", "C"], "bought": ["D2", "F1"],
           "starters": {"D2": "DEF", "B": "MID", "F1": "FWD"},
           "purchase_fees": 75, "sale_receipts": 35, "net_spend": 40, "wages": 10}, show=True)
print()

# 2. Net allowance 30: sell all three, buy D2, M1 and F2
params = toy_params()
params["B"] = 30
run_check("allowance_30", base, params,
          {"objective": 230, "sold": ["A", "B", "C"], "bought": ["D2", "M1", "F2"],
           "starters": {"D2": "DEF", "M1": "MID", "F2": "FWD"},
           "purchase_fees": 95, "sale_receipts": 65, "net_spend": 30, "wages": 10})

# 3. No transfers at all: the original three stay (a comparison, not an optimum)
params = toy_params()
params["no_buy"] = list(base["C"])
params["no_sell"] = list(base["E"])
run_check("keep_original_three", base, params,
          {"objective": 205, "sold": [], "bought": [], "net_spend": 0, "wages": 7})

# 4. A failed sale: A cannot be sold, so the plan at allowance 40 has to change.
#    Keeping A and buying F1 would cost 45 net, so the receipt for A is not spent.
params = toy_params()
params["no_sell"] = ["A"]
run_check("sale_of_A_fails", base, params,
          {"objective": 226, "sold": ["B", "C"], "bought": ["M1", "F2"],
           "starters": {"A": "DEF", "M1": "MID", "F2": "FWD"}, "net_spend": 35, "wages": 10})

# 5. Fixed arrival K1 (a forward, committed fee 20) must be in the squad.
#    With one place per role, existing forward C has to be sold.
data_k = copy.deepcopy(base)
add_player(data_k, "K1", "K", {"FWD": 70}, wage=2)
params = toy_params()
params["F0"] = 20   # committed fee for K1, GBP million
run_check("fixed_arrival", data_k, params,
          {"objective": 226, "sold": ["A", "B", "C"], "bought": ["D2", "M1"],
           "starters": {"D2": "DEF", "M1": "MID", "K1": "FWD"},
           "purchase_fees": 70, "sale_receipts": 65, "net_spend": 25, "wages": 9})

# 6. The fixed arrival uses one of the allowed arrivals: with a limit of two,
#    only one more player can be bought.
params = toy_params()
params["F0"] = 20
params["TB"] = 2
run_check("fixed_arrival_counts_as_arrival", data_k, params,
          {"objective": 225, "sold": ["A", "C"], "bought": ["D1"], "net_spend": 30, "wages": 9})

# 7. Versatile candidate V can play DEF (78) or MID (80), fee 30, wage 3.
#    Using V in both roles at once would score 243; that must not happen.
data_v = copy.deepcopy(base)
add_player(data_v, "V", "C", {"DEF": 78, "MID": 80}, wage=3, fee=30)
params = toy_params()
run_check("versatile_one_role", data_v, params,
          {"objective": 239, "sold": ["A", "B", "C"], "bought": ["D2", "F1", "V"],
           "starters": {"D2": "DEF", "V": "MID", "F1": "FWD"}, "net_spend": 40, "wages": 10})

# 8. One versatile player cannot provide cover in two roles. Keep A, B, C and
#    allow only V to be bought, then ask for two DEF and two MID: four players
#    cannot fill five places.
params = toy_params()
params["no_buy"] = ["D1", "D2", "M1", "F1", "F2"]
params["l"] = {"DEF": 2, "MID": 2, "FWD": 1}
params["u"] = {"DEF": 2, "MID": 2, "FWD": 1}
params["W"] = 100
params["B"] = 100
run_check("versatile_not_counted_twice", data_v, params, {"feasible": False})

# 9. Registration: at most one non-homegrown senior-list player.
#    B and M1 are both non-homegrown, so DEF must be A and FWD must be C or F2
#    (F2 is exempt from the senior list).
params = toy_params()
params["non_hg_cap"] = 1
run_check("non_homegrown_limit", base, params,
          {"objective": 226, "sold": ["B", "C"], "bought": ["M1", "F2"],
           "starters": {"A": "DEF", "M1": "MID", "F2": "FWD"}, "net_spend": 35, "wages": 10})

# 10. Registration: only two senior-list places for three roles, so the exempt
#     player F2 must be chosen.
params = toy_params()
params["senior_cap"] = 2
run_check("senior_list_limit", base, params,
          {"objective": 230, "bought": ["D2", "M1", "F2"], "net_spend": 30, "wages": 10})

# 11. Depth: up to two players per role and a small depth reward.
#     Checked against the brute-force search only.
params = toy_params()
params["u"] = {g: 2 for g in params["G"]}
params["mu"] = 0.1
params["W"] = 14
run_check("depth_reward", base, params, show=True)
print()

# 12. Depth together with the versatile player and the fixed arrival
data_kv = copy.deepcopy(data_k)
add_player(data_kv, "V", "C", {"DEF": 78, "MID": 80}, wage=3, fee=30)
params = toy_params()
params["F0"] = 20
params["u"] = {g: 2 for g in params["G"]}
params["mu"] = 0.1
params["W"] = 16
params["B"] = 60
run_check("depth_versatile_fixed", data_kv, params)

# 13. Wage allowance too low for any squad: the cheapest three players cost 7
params = toy_params()
params["W"] = 6
run_check("wage_allowance_too_low", base, params, {"feasible": False})

# 15. Part of a plan held fixed: D1 must be bought and B must be sold.
#     With D1 (45) bought and A (20) and B (30) sold, M1 (55) and one forward fit:
#     D1-M1-C costs 50 net with wages 11, D1-M1-F2 costs 60. Neither is allowed at
#     allowance 40 and wages 10, so the case has no valid plan.
params = toy_params()
params["must_buy"] = ["D1"]
params["must_sell"] = ["B"]
run_check("required_purchase_and_sale_infeasible", base, params, {"feasible": False})
#     With allowance 60 and wages 12 the best plan is D1-M1-F2 (236).
params = toy_params()
params["must_buy"] = ["D1"]
params["must_sell"] = ["B"]
params["B"] = 60
params["W"] = 12
run_check("required_purchase_and_sale", base, params,
          {"objective": 236, "sold": ["A", "B", "C"], "bought": ["D1", "M1", "F2"], "net_spend": 60, "wages": 12})

# 16. A candidate bought only to start in a stated role. V can play DEF (78) or
#     MID (80). With allowance 55 and wages 11 the best plan uses V in MID:
#     D2-V-F1 scores 239. If V may be bought only as a DEF starter, the best
#     plan is V-B-F1: 78 + 75 + 85 = 238, net 30 + 60 - 20 - 15 = 55, wages 11.
params = toy_params()
params["B"] = 55
params["W"] = 11
run_check("versatile_free_choice_of_role", data_v, params,
          {"objective": 239, "starters": {"D2": "DEF", "V": "MID", "F1": "FWD"}})
params = toy_params()
params["B"] = 55
params["W"] = 11
params["start_role_if_bought"] = {"V": "DEF"}
run_check("bought_only_to_start_in_role", data_v, params,
          {"objective": 238, "sold": ["A", "C"], "bought": ["F1", "V"],
           "starters": {"V": "DEF", "B": "MID", "F1": "FWD"}, "net_spend": 55, "wages": 11})

# 14. The independent checker must reject plans that break the rules.
#     First plan: V covers and starts in two roles at once (score 243).
params = toy_params()
bad_plan = {"objective": 243, "sold": ["A", "B", "C"], "bought": ["F1", "V"], "squad": ["F1", "V"],
            "cover": [("V", "DEF"), ("V", "MID"), ("F1", "FWD")],
            "starters": [("V", "DEF"), ("V", "MID"), ("F1", "FWD")]}
totals, problems = check_solution(data_v, params, bad_plan)
found_two_roles = ("Player has more than one cover role: V" in problems
                   and "Player starts in more than one role: V" in problems)
#     Second plan: D1, B and F1 cost 70 net and 12 in wages, above both allowances.
bad_plan = {"objective": 240, "sold": ["A", "C"], "bought": ["D1", "F1"], "squad": ["B", "D1", "F1"],
            "cover": [("B", "MID"), ("D1", "DEF"), ("F1", "FWD")],
            "starters": [("B", "MID"), ("D1", "DEF"), ("F1", "FWD")]}
totals, problems = check_solution(base, params, bad_plan)
found_overspend = ("Net transfer spending is above the allowance." in problems
                   and "Annual wages are above the allowance." in problems)
if found_two_roles and found_overspend:
    print("PASS checker_rejects_bad_plans | two roles for one player and overspending are both reported")
else:
    failures.append("checker_rejects_bad_plans")
    print("FAIL checker_rejects_bad_plans")

print()
if failures:
    print("FAILED checks:", ", ".join(failures))
    sys.exit(1)
print("All toy checks passed.")
