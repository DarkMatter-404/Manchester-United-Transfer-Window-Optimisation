"""Additional runs for the report, made on 21 November 2026.

These runs were made after the freeze and after the 2025/26 outcomes had been
examined. They use the same inputs and the same model as the corrected runs of
18 November 2026 and do not change the recommendation. They answer four
questions raised in review:

  1. How does the objective change with the wage allowance? (the wage curve
     drawn beside the budget curve)
  2. What does one step more or less of each limit change? (arrivals and
     non-homegrown places; budget and wage steps come from 1 and the earlier runs)
  3. Why are the reserves Mason Mount and Rasmus Hojlund kept? (no depth reward,
     and forced sales of each)
  4. How much objective does the plan give up to protect the wage limit against
     candidates earning more than estimated? (a robust wage limit)

It also solves the linear relaxation of the base model, in which every binary
variable may take any value between 0 and 1, re-decides the plan when both
doubtful purchases (Hincapie and Ederson) fall through, and counts the reference
players whose playing time comes from two clubs in one season.

Run from the repository root:
    python src/extra_runs.py --out results/corrections/2026-11-21
"""

import copy
import csv
import datetime
import itertools
import json
import os
import subprocess
import sys

from gurobipy import gurobi, read, setParam

import run_scenarios as rs
import toy_model
from check_solution import check_solution
from model_inputs import base_settings, base_params, build_data, unavailable_candidates
from output_paths import output_folder
from transfer_model import read_inputs, solve_transfer_model

HERE = os.path.dirname(os.path.abspath(__file__))

MOUNT = "346483"      # Mason Mount, reserve attacking midfielder in the base plan
HOJLUND = "610442"    # Rasmus Hojlund, reserve striker in the base plan
HINCAPIE = "659813"   # Piero Hincapie, base purchase (CB)
EDERSON = "607854"    # Ederson, base purchase (CM)

WAGE_DEVIATION = 0.10   # a purchased player may earn up to 10% more than estimated
GAMMAS = range(0, 7)    # number of purchased players whose wage may be higher (at most six arrivals)


#########Robust wage limit############

def robust_wage_plan(data, params, gamma, deviation):
    """Best plan when up to gamma purchased players may each earn their estimated
    wage plus deviation[p] (GBP million per year).

    The protected wage limit is
        sum of wages of the squad + largest possible extra wages <= W,
    where the extra wages are those of the gamma purchases with the largest
    deviations. Written with linear-programming duality, a plan satisfies it if
    there is a number pi >= 0 with
        sum_p w_p x_p + gamma * pi + sum_{p in C} b_p * max(0, deviation_p - pi) <= W.
    For a fixed plan the left side is smallest at pi = 0 or at one of the
    deviations, so the robust model is solved by trying each of these values:
    candidate wages become w_p + max(0, deviation_p - pi), the allowance becomes
    W - gamma * pi, and the best of these ordinary runs is the robust plan.
    """
    best = None
    for pi in sorted(set([0.0] + [deviation[p] for p in data["C"]])):
        adjusted = copy.deepcopy(data)
        for p in data["C"]:
            adjusted["w"][p] = data["w"][p] + max(0.0, deviation[p] - pi)
        adjusted_params = dict(params)
        adjusted_params["W"] = params["W"] - gamma * pi
        sol = solve_transfer_model(adjusted, adjusted_params, model_name="robust_wages", find_iis=False)
        if sol["has_solution"] and (best is None or sol["objective"] > best[1]["objective"] + 1e-6):
            best = (pi, sol)
    return best


def worst_case_wages(data, sol, gamma, deviation):
    """Squad wages if the gamma purchases with the largest deviations all earn more."""
    extra = sorted((deviation[p] for p in sol["bought"]), reverse=True)[:gamma]
    return sum(data["w"][p] for p in sol["squad"]) + sum(extra)


def check_robust_method_on_toy():
    """Compare the method above with a search over every plan of the invented example."""
    data = read_inputs(toy_model.TOY_FOLDER)
    results = []
    for gamma in (0, 1, 2, 3):
        for W in (10, 11, 12):
            params = toy_model.toy_params()
            params["W"] = W
            deviation = {p: 0.2 * data["w"][p] for p in data["C"]}

            # Search: every set of sales and purchases that meets the protected wage limit
            best_search = None
            for n_sold in range(len(data["E"]) + 1):
                for sold in itertools.combinations(data["E"], n_sold):
                    for n_bought in range(len(data["C"]) + 1):
                        for bought in itertools.combinations(data["C"], n_bought):
                            squad = [p for p in data["E"] if p not in sold] + list(bought)
                            extra = sorted((deviation[p] for p in bought), reverse=True)[:gamma]
                            if sum(data["w"][p] for p in squad) + sum(extra) > W + 1e-9:
                                continue
                            fixed = dict(params)
                            fixed["must_buy"], fixed["must_sell"] = list(bought), list(sold)
                            fixed["no_buy"] = [p for p in data["C"] if p not in bought]
                            fixed["no_sell"] = [p for p in data["E"] if p not in sold]
                            value = toy_model.brute_force(data, fixed)
                            if value is not None and (best_search is None or value > best_search):
                                best_search = value

            robust = robust_wage_plan(data, params, gamma, deviation)
            best_method = robust[1]["objective"] if robust else None
            same = (best_search is None and best_method is None) or (
                best_search is not None and best_method is not None and abs(best_search - best_method) < 1e-6)
            results.append({"gamma": gamma, "W": W, "search": best_search, "method": best_method,
                            "passed": "yes" if same else "no"})
    return results


#########Linear relaxation############

def linear_relaxation(data, params, model_file):
    """Solve the integer model, save it to a file, then solve its linear relaxation.

    Gurobi writes the model to ResultFile after solving, so the model can be read
    back without changing the model code.
    """
    setParam("OutputFlag", 0)
    setParam("ResultFile", model_file)
    sol = solve_transfer_model(data, params, model_name="relaxation_check")
    setParam("ResultFile", "")

    integer = read(model_file)
    integer.Params.OutputFlag = 0
    integer.optimize()

    relaxed = integer.relax()
    relaxed.Params.OutputFlag = 0
    relaxed.optimize()
    fractional = [v.VarName for v in relaxed.getVars() if 1e-6 < v.X < 1 - 1e-6]

    rows = {}
    for name in ["net_spend", "wages", "arrivals", "sales", "senior_list", "non_homegrown"]:
        c = relaxed.getConstrByName(name)
        rows[name] = {"slack": round(c.Slack, 4), "dual_price": round(c.Pi, 4)}

    return {
        "integer_objective_from_model_code": round(sol["objective"], 4),
        "integer_objective_from_saved_model": round(integer.ObjVal, 4),
        "integer_nodes_explored": int(integer.NodeCount),
        "relaxation_objective": round(relaxed.ObjVal, 4),
        "relaxation_minus_integer": round(relaxed.ObjVal - integer.ObjVal, 4),
        "fractional_variables": len(fractional),
        "fractional_by_kind": {kind: len([v for v in fractional if v.startswith(kind + "[")])
                               for kind in ["sell", "buy", "squad", "cover", "start"]},
        "rows_of_relaxation": rows,
    }


#########Main############

if __name__ == "__main__":
    RESULTS = output_folder()
    rs.RESULTS = RESULTS
    log = []

    # Check the robust method on the invented example before using it
    toy_checks = check_robust_method_on_toy()
    failed = [c for c in toy_checks if c["passed"] != "yes"]
    print("Robust method against a full search of the example:", len(toy_checks), "cases,",
          len(failed), "failed")
    if failed:
        sys.exit("The robust method does not match the full search: " + str(failed))

    # Base run again, so the new runs can be compared with it
    base = rs.run("extra/base", "base", base_settings(), base_params())

    #########1 and 2: limits############

    scenarios = []
    for W in (141, 155, 162, 169, 176, 183):
        params = base_params()
        params["W"] = W
        scenarios.append(("extra/wage_allowance_" + str(W), "wage allowance", params))
    params = base_params()
    params["TB"] = 7
    scenarios.append(("extra/arrivals_7", "arrivals limit", params))
    for cap in (16, 18):
        params = base_params()
        params["non_hg_cap"] = cap
        scenarios.append(("extra/non_homegrown_" + str(cap), "non-homegrown limit", params))

    #########3: reserves############

    params = base_params()
    params["mu"] = 0.0
    scenarios.append(("extra/depth_weight_0", "depth weight", params))
    for p, label in ((MOUNT, "Mount"), (HOJLUND, "Hojlund")):
        params = base_params()
        params["must_sell"] = [p]
        scenarios.append(("extra/must_sell_" + label, "forced sale", params))

    # Both doubtful purchases fall through together; the whole plan is decided again
    params = base_params()
    params["no_buy"] = [HINCAPIE, EDERSON]
    scenarios.append(("extra/without_Hincapie_and_Ederson", "full plan: two signings blocked", params))

    for name, group, params in scenarios:
        rs.run(name, group, base_settings(), params)

    for entry in rs.run_log:
        if "objective" not in entry:
            continue
        plan = rs.plans[entry["run"]]
        entry["objective_on_base_scale"] = rs.score_on_base_scale(plan["settings"], plan["params"],
                                                                  plan["sol"]["bought"], plan["sol"]["sold"])
        entry["signings_shared_with_base"] = len([p for p in plan["sol"]["bought"] if p in base["bought"]])
        entry["sales_shared_with_base"] = len([p for p in plan["sol"]["sold"] if p in base["sold"]])

    columns = ["run", "group", "status", "gap", "bound", "runtime", "checks_passed", "objective",
               "objective_on_base_scale", "signings_shared_with_base", "sales_shared_with_base",
               "bought", "sold", "purchase_fees", "sale_receipts", "net_spend", "wages",
               "arrivals", "sales", "senior", "non_homegrown", "candidates"]
    with open(os.path.join(RESULTS, "extra_runs_summary.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for entry in rs.run_log:
            writer.writerow([entry.get(c, "") for c in columns])

    #########4: robust wage limit############

    settings, params = base_settings(), base_params()
    data, info, over_cap = build_data(settings, params["fee_cap"])
    params["no_buy"] = unavailable_candidates(data)
    deviation = {p: WAGE_DEVIATION * data["w"][p] for p in data["C"]}
    robust_rows = []
    for gamma in GAMMAS:
        pi, sol = robust_wage_plan(data, params, gamma, deviation)
        # Recompute the plan with the estimated wages, then the protected wage total
        totals, problems = check_solution(data, params, sol)
        worst = worst_case_wages(data, sol, gamma, deviation)
        if worst > params["W"] + 1e-6:
            problems.append("protected wage total above the allowance")
        name = "robust/gamma_" + str(gamma)
        rs.save_run(name, settings, params, data, info, sol, totals, over_cap)
        cover = dict(sol["cover"])
        robust_rows.append({
            "gamma": gamma, "pi": round(pi, 4), "status": sol["status"], "gap": round(sol["gap"], 6),
            "checks_passed": "yes" if not problems else "no", "objective": round(totals["objective"], 2),
            "change_from_base": round(totals["objective"] - rs.run_log[0]["objective"], 2),
            "bought": "; ".join(data["name"][p] + " (" + cover[p] + ")" for p in sol["bought"]),
            "sold": "; ".join(data["name"][p] for p in sol["sold"]),
            "net_spend": round(totals["net_spend"], 2), "wages": round(totals["wages"], 2),
            "protected_wages": round(worst, 2), "arrivals": totals["arrivals"], "sales": totals["sales"],
            "non_homegrown": totals["non_homegrown"],
            "signings_shared_with_base": len([p for p in sol["bought"] if p in base["bought"]]),
        })
        print(name, "| objective", robust_rows[-1]["objective"], "| checks", robust_rows[-1]["checks_passed"])
    with open(os.path.join(RESULTS, "robust_wages.csv"), "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(robust_rows[0].keys()))
        writer.writeheader()
        writer.writerows(robust_rows)

    #########5: linear relaxation############

    folder = os.path.join(RESULTS, "relaxation")
    os.makedirs(folder, exist_ok=True)
    relaxation = {"base": linear_relaxation(data, params, os.path.join(folder, "base_model.mps"))}
    # The same with the base plan's purchases and sales fixed: only roles and starters remain
    fixed = rs.fix_transactions(params, data, base["bought"], base["sold"])
    relaxation["transactions_fixed"] = linear_relaxation(data, fixed, os.path.join(folder, "fixed_model.mps"))
    with open(os.path.join(folder, "relaxation.json"), "w") as file:
        json.dump(relaxation, file, indent=1, sort_keys=True)
    for path in ("base_model.mps", "fixed_model.mps"):
        os.remove(os.path.join(folder, path))   # large and easy to rebuild

    #########6: players whose playing time comes from two clubs############

    # The playing-time component divides league minutes for all clubs by the main
    # club's league matches. This lists the reference players with a season at two
    # or more clubs, where that ratio can overstate the share. Nothing is rescored.
    pool = {r["player_id"]: r for r in rs.read_table(rs.PROCESSED, "pool_players.csv")}
    seasons = [r for r in rs.read_table(rs.PROCESSED, "player_seasons.csv")
               if r["player_id"] in pool and r["season"] in ("2023", "2024")]
    two_clubs = [r for r in seasons if int(r["clubs_in_season"]) >= 2]
    affected = sorted(set(r["player_id"] for r in two_clubs))
    base_entry = rs.plans["extra/base"]["sol"]
    with open(os.path.join(RESULTS, "playing_time_audit.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["player_id", "name", "status", "season", "clubs_in_season", "main_club",
                         "minutes_share", "in_base_plan"])
        for r in two_clubs:
            p = r["player_id"]
            if p in base_entry["bought"]:
                role = "bought"
            elif p in base_entry["sold"]:
                role = "sold"
            elif p in base_entry["squad"]:
                role = "kept"
            else:
                role = ""
            writer.writerow([p, pool[p]["name"], pool[p]["status"], r["season"], r["clubs_in_season"],
                             r["club_name"], r["minutes_share"], role])
    audit = {
        "reference_players": len(pool),
        "player_seasons": len(seasons),
        "player_seasons_at_two_or_more_clubs": len(two_clubs),
        "players_affected": len(affected),
        "affected_existing_players": [pool[p]["name"] for p in affected if pool[p]["status"] == "E"],
        "affected_base_purchases": [pool[p]["name"] for p in affected if p in base_entry["bought"]],
        "affected_base_sales": [pool[p]["name"] for p in affected if p in base_entry["sold"]],
    }
    print("Playing-time audit:", json.dumps(audit))

    #########Record of these runs############

    def git(*args):
        try:
            return subprocess.run(["git"] + list(args), cwd=HERE, capture_output=True, text=True).stdout.strip()
        except OSError:
            return ""

    manifest = {
        "written": datetime.datetime.now().isoformat(timespec="seconds"),
        "note": ("Additional analysis after the freeze and after the 2025/26 outcomes were examined. "
                 "Same inputs and model as the corrected runs of 18 November 2026; the recommendation is unchanged."),
        "code_commit": git("rev-parse", "HEAD"),
        "uncommitted_code_or_inputs": git("status", "--porcelain", "--", "../src", "../data", "../docs") != "",
        "command": "python src/extra_runs.py --out " + os.path.relpath(RESULTS, os.path.join(HERE, "..")),
        "python": sys.version.split()[0],
        "gurobi": ".".join(str(v) for v in gurobi.version()),
        "wage_deviation": WAGE_DEVIATION,
        "robust_method_toy_checks": toy_checks,
        "playing_time_audit": audit,
        "runs": [{k: e.get(k, "") for k in ["run", "group", "status", "gap", "checks_passed", "objective"]}
                 for e in rs.run_log],
    }
    with open(os.path.join(RESULTS, "extra_manifest.json"), "w") as file:
        json.dump(manifest, file, indent=1, sort_keys=True)

    print("Extra runs:", len(rs.run_log), "| with a failed check:",
          len([e for e in rs.run_log if e.get("checks_passed") == "no"]),
          "| robust runs with a failed check:", len([r for r in robust_rows if r["checks_passed"] != "yes"]))
    print("Relaxation:", json.dumps(relaxation, indent=1))
