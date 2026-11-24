"""Run the transfer model on the real player pool.

Each run builds the model inputs under one set of settings, solves the model,
recomputes every rule from the chosen players and saves the plan in
results/<run name>/ together with the settings that produced it.

The script then writes:
    results/runs_summary.csv            one line per run
    results/direct_alternatives.csv     plans A to D for each base signing
    results/full_plan_alternatives.csv  re-decided plans when a signing or sale is blocked
    results/shortlist_review.csv        ownership, commitment, contract and registration checks
    results/run_manifest.json           code version, input hashes and solver details
    results/RESULTS.md                  the same tables in readable form

All of these go to the folder named with --out. The original results in
results are never overwritten (see output_paths.py).

Run from the repository root, after score_players.py:
    python src/run_scenarios.py --out results/corrections/2026-11-18/model
"""

import csv
import datetime
import hashlib
import json
import os
import subprocess
import sys

from importlib import metadata

from gurobipy import GurobiError, gurobi

from transfer_model import solve_transfer_model
from check_solution import check_solution, print_solution
from output_paths import output_folder, is_correction
from model_inputs import (PROCESSED, MANUAL, DOCS, ROLES, read_table, base_settings, base_params,
                          build_data, unavailable_candidates, likelihood)

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = None   # set from --out when the script runs

run_log = []      # one entry per run
plans = {}        # run name -> what is needed to re-score or compare the plan later


def fix_transactions(params, data, bought, sold):
    """Limits that hold a plan's purchases and sales fixed while roles are re-decided."""
    fixed = dict(params)
    fixed["must_buy"] = list(bought)
    fixed["must_sell"] = list(sold)
    fixed["no_buy"] = [p for p in data["C"] if p not in bought]
    fixed["no_sell"] = [p for p in data["E"] if p not in sold]
    fixed["start_role_if_bought"] = {}
    return fixed


def score_on_base_scale(settings, params, bought, sold):
    """Objective of a plan's transactions under the base score and base weights.

    Runs that use another score or other weights have objectives on a different
    scale. Re-scoring every plan the same way makes them comparable.
    """
    common_settings = dict(settings)
    common_settings["quality"] = base_settings()["quality"]
    common_params = dict(params)
    common_params["omega"] = base_params()["omega"]
    common_params["mu"] = base_params()["mu"]
    data, info, over_cap = build_data(common_settings, common_params["fee_cap"])
    sol = solve_transfer_model(data, fix_transactions(common_params, data, bought, sold), model_name="rescore")
    return round(sol["objective"], 2) if sol["has_solution"] else ""


def save_run(name, settings, params, data, info, sol, totals, over_cap):
    """Write the plan, its totals and its settings to results/<name>/."""
    folder = os.path.join(RESULTS, *name.split("/"))
    os.makedirs(folder, exist_ok=True)
    cover = dict(sol["cover"])
    starters = dict(sol["starters"])

    with open(os.path.join(folder, "squad.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["player_id", "name", "club_at_cutoff", "age", "action", "role", "starter",
                         "quality_in_role", "wage_gbp_m", "fee_or_receipt_gbp_m"])
        for p in data["E"] + data["C"] + data["K"]:
            if p in data["K"]:
                action, money = "fixed arrival", ""
            elif p in sol["sold"]:
                action, money = "sold", round(data["r"][p], 2)
            elif p in sol["bought"]:
                action, money = "bought", round(data["f"][p], 2)
            elif p in data["E"]:
                action, money = "kept", ""
            else:
                continue
            g = cover.get(p, "")
            writer.writerow([p, data["name"][p], info[p]["club"], info[p]["age"], action, g,
                             1 if p in starters else 0,
                             round(data["q"][p, g], 2) if g else "",
                             round(data["w"][p], 2), money])

    with open(os.path.join(folder, "summary.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["item", "value"])
        writer.writerow(["status", sol["status"]])
        writer.writerow(["optimality_gap", round(sol["gap"], 6)])
        writer.writerow(["best_bound", round(sol["bound"], 3)])
        writer.writerow(["runtime_seconds", round(sol["runtime"], 3)])
        writer.writerow(["variables", sol["num_vars"]])
        writer.writerow(["constraints", sol["num_constrs"]])
        writer.writerow(["candidates_available", len(data["C"])])
        writer.writerow(["candidates_above_fee_ceiling", len(over_cap)])
        for key in ["objective", "starter_score", "depth_score", "purchase_fees", "sale_receipts",
                    "fixed_net_fees", "net_spend", "wages", "arrivals", "sales", "squad_size",
                    "senior", "non_homegrown"]:
            writer.writerow([key, round(totals[key], 3)])
        for g in params["G"]:
            writer.writerow(["players_" + g, totals["cover_count"][g]])

    # The complete settings and limits of this run
    with open(os.path.join(folder, "settings.json"), "w") as file:
        json.dump({"settings": settings, "params": params}, file, indent=1, sort_keys=True)


def run(name, group, settings, params, show=False):
    """Build, solve, check and save one run. Returns the solution or None."""
    data, info, over_cap = build_data(settings, params["fee_cap"])
    # Block candidates known to be unavailable, on top of any blocks set for this run
    params = dict(params)
    params["no_buy"] = list(params.get("no_buy", [])) + [p for p in unavailable_candidates(data)
                                                         if p not in params.get("no_buy", [])]
    entry = {"run": name, "group": group}
    run_log.append(entry)

    try:
        sol = solve_transfer_model(data, params, model_name=name.replace("/", "_"))
    except GurobiError as error:
        print(name, "| solver could not run this model:", error)
        entry["status"] = "NOT RUN"
        return None

    entry["status"] = sol["status"]
    entry["runtime"] = round(sol["runtime"], 3)
    if not sol["has_solution"]:
        print(name, "| no plan found:", sol["status"], "|", ", ".join(sol.get("iis", [])))
        return None

    # Recompute every rule from the chosen players
    totals, problems = check_solution(data, params, sol)
    if show:
        print("=====", name, "=====")
        print_solution(data, params, sol, totals)
        print()
    if problems:
        print(name, "| CHECK FAILED:", "; ".join(problems))
    save_run(name, settings, params, data, info, sol, totals, over_cap)

    cover = dict(sol["cover"])
    entry.update({
        "gap": round(sol["gap"], 6), "bound": round(sol["bound"], 2),
        "checks_passed": "yes" if not problems else "no",
        "objective": round(totals["objective"], 2), "starter_score": round(totals["starter_score"], 2),
        "bought": "; ".join(data["name"][p] + " (" + cover[p] + ")" for p in sol["bought"]),
        "sold": "; ".join(data["name"][p] for p in sol["sold"]),
        "purchase_fees": round(totals["purchase_fees"], 2), "sale_receipts": round(totals["sale_receipts"], 2),
        "net_spend": round(totals["net_spend"], 2), "wages": round(totals["wages"], 2),
        "arrivals": totals["arrivals"], "sales": totals["sales"],
        "senior": totals["senior"], "non_homegrown": totals["non_homegrown"],
        "candidates": len(data["C"]),
    })
    plans[name] = {"settings": settings, "params": params, "sol": sol, "data": data, "info": info}
    return sol


def weakness_weights(no_transfer_sol):
    """Role weights that favour the roles where United's current starters score lowest.

    Weight = 1 + (benchmark - United average) / 100, never below 1. The benchmark
    is the score that 90% of the pool's players in the role fall below.
    """
    scores = read_table(PROCESSED, "scores.csv")
    quality = {(row["player_id"], row["role"]): float(row["quality"]) for row in scores}
    weights = {}
    for g in ROLES:
        united = [quality[p, role] for (p, role) in no_transfer_sol["starters"] if role == g]
        ranked = sorted(float(row["quality"]) for row in scores if row["role"] == g)
        benchmark = ranked[int(0.9 * (len(ranked) - 1))]
        weights[g] = round(1.0 + max(0.0, benchmark - sum(united) / len(united)) / 100.0, 3)
    return weights


def changes_from_base(base, other, names):
    """Describe how another plan's transfers and starting roles differ from the base plan."""
    parts = []
    signings_in = [names[p] for p in other["bought"] if p not in base["bought"]]
    signings_out = [names[p] for p in base["bought"] if p not in other["bought"]]
    sales_in = [names[p] for p in other["sold"] if p not in base["sold"]]
    sales_out = [names[p] for p in base["sold"] if p not in other["sold"]]
    if signings_in:
        parts.append("signs instead: " + ", ".join(signings_in))
    if signings_out:
        parts.append("no longer signs: " + ", ".join(signings_out))
    if sales_in:
        parts.append("also sells: " + ", ".join(sales_in))
    if sales_out:
        parts.append("keeps: " + ", ".join(sales_out))
    base_start, other_start = dict(base["starters"]), dict(other["starters"])
    moved = [names[p] + " " + base_start[p] + " to " + other_start[p]
             for p in other_start if p in base_start and base_start[p] != other_start[p]]
    if moved:
        parts.append("starting role changes: " + ", ".join(moved))
    return "; ".join(parts) or "same transfers and starting roles"


def file_hash(path):
    with open(path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


def markdown_table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    RESULTS = output_folder()
    pool_rows = {row["player_id"]: row for row in read_table(PROCESSED, "pool_players.csv")}
    existing = [p for p, row in pool_rows.items() if row["status"] == "E"]

    #########Comparison case and base case############

    settings = base_settings()
    settings["candidates"] = False
    params = base_params()
    params["no_sell"] = existing
    no_transfers = run("no_transfers", "comparison", settings, params, show=True)

    base = run("base", "base", base_settings(), base_params(), show=True)
    base_data = plans["base"]["data"]
    base_info = plans["base"]["info"]
    names = dict(base_data["name"])

    #########One change at a time############

    scenarios = []    # (name, group, settings, params)

    # Net transfer allowance: the trade-off between spending and squad quality
    for budget in (0, 50, 100, 150, 200, 300):
        params = base_params()
        params["B"] = budget
        scenarios.append(("budget_" + str(budget), "budget", base_settings(), params))

    # Purchase fees only: wages stay as in the base case
    for alpha in (0.9, 1.5):
        settings = base_settings()
        settings["alpha"] = alpha
        settings["alpha_english_pl"] = max(alpha, settings["alpha_english_pl"])
        scenarios.append(("fee_only_" + str(alpha), "fee only", settings, base_params()))

    # Combined fee-and-wage scenarios: the wage band follows the scenario fee
    for alpha in (0.9, 1.5):
        settings = base_settings()
        settings["alpha"] = alpha
        settings["alpha_english_pl"] = max(alpha, settings["alpha_english_pl"])
        settings["wage_follows_fee"] = True
        scenarios.append(("combined_fee_and_wage_" + str(alpha), "combined fee and wage", settings, base_params()))

    # Candidate wages 10% lower and higher; fees and the wage allowance unchanged
    for factor, label in ((0.9, "minus_10"), (1.1, "plus_10")):
        settings = base_settings()
        settings["candidate_wage_factor"] = factor
        scenarios.append(("candidate_wages_" + label, "candidate wages", settings, base_params()))

    # Sale receipts
    for beta in (0.7, 1.0):
        settings = base_settings()
        settings["beta"] = beta
        scenarios.append(("sale_receipt_" + str(beta), "sale receipt", settings, base_params()))

    # Wage allowance: no growth on the current total, and no limit at all
    params = base_params()
    params["W"] = 133.38
    scenarios.append(("wage_allowance_no_growth", "wage allowance", base_settings(), params))
    params = base_params()
    params["W"] = 10000
    scenarios.append(("wage_allowance_removed", "wage allowance", base_settings(), params))

    # The earlier, higher ceiling on the fee for one player
    params = base_params()
    params["fee_cap"] = 100
    scenarios.append(("fee_ceiling_100", "fee ceiling", base_settings(), params))

    # Number of arrivals allowed
    for arrivals in (4, 5):
        params = base_params()
        params["TB"] = arrivals
        scenarios.append(("arrivals_" + str(arrivals), "arrivals limit", base_settings(), params))

    # Depth weight
    for mu in (0.2, 0.4):
        params = base_params()
        params["mu"] = mu
        scenarios.append(("depth_weight_" + str(mu), "depth weight", base_settings(), params))

    # Quality score without the market-value component
    settings = base_settings()
    settings["quality"] = "quality_no_value"
    scenarios.append(("quality_without_value", "scoring", settings, base_params()))

    # Role weights that favour United's weakest roles
    params = base_params()
    params["omega"] = weakness_weights(no_transfers)
    scenarios.append(("weakness_weights", "role weights", base_settings(), params))

    # Matheus Cunha treated as an arrival already agreed at GBP 62.5 million
    settings = base_settings()
    settings["fixed_arrivals"] = {"517894": 62.5}
    params = base_params()
    params["F0"] = 62.5
    scenarios.append(("cunha_fixed", "commitment", settings, params))

    # United's wages estimated by the candidate bands instead of the wage table
    settings = base_settings()
    settings["united_wages"] = "bands"
    scenarios.append(("united_wages_by_bands", "United wage estimate", settings, base_params()))

    # Rival and wealthy clubs treated like any other seller
    settings = base_settings()
    settings["blocked_clubs"] = []
    settings["club_multiplier"] = {}
    settings["elite_clubs"] = []
    scenarios.append(("rivals_like_other_clubs", "club rules", settings, base_params()))

    # Without the two-year rule. Scores are the same as in the base case,
    # because every run scores players against the same group.
    settings = base_settings()
    settings["two_year_rule"] = False
    scenarios.append(("without_two_year_rule", "two-year rule", settings, base_params()))

    for name, group, settings, params in scenarios:
        run("sensitivity/" + name, group, settings, params)

    #########Alternative full plans############

    # One signing or one sale is ruled out and the whole plan is decided again
    full_plans = []
    for p in base["bought"]:
        params = base_params()
        params["no_buy"] = [p]
        name = "full_plans/without_" + names[p].replace(" ", "_")
        sol = run(name, "full plan: signing blocked", base_settings(), params)
        full_plans.append({"blocked": "cannot sign " + names[p], "run": name,
                           "changes": changes_from_base(base, sol, plans[name]["data"]["name"])})
    for p in base["sold"]:
        params = base_params()
        params["no_sell"] = [p]
        name = "full_plans/cannot_sell_" + names[p].replace(" ", "_")
        sol = run(name, "full plan: sale blocked", base_settings(), params)
        full_plans.append({"blocked": "cannot sell " + names[p], "run": name,
                           "changes": changes_from_base(base, sol, plans[name]["data"]["name"])})

    #########Direct alternatives for each signing############

    # The other five purchases and the sales are held fixed. The replacement must be
    # able to play the role the original target starts in and must start in that role.
    # The rest of the lineup is not fixed: the model may still re-arrange other players.
    base_start = dict(base["starters"])
    base_cover = dict(base["cover"])
    base_objective = run_log[1]["objective"]
    direct = []

    for target in base["bought"]:
        need = base_cover[target]
        starts = target in base_start
        blocked = []
        choice = target
        for plan in ("A", "B", "C", "D"):
            if plan == "A":
                objective, role, started = base_objective, need, starts
            else:
                blocked.append(choice)
                params = base_params()
                params["must_buy"] = [q for q in base["bought"] if q != target]
                params["must_sell"] = list(base["sold"])
                params["no_sell"] = [q for q in existing if q not in base["sold"]]
                can_replace = [q for q in base_data["C"] if (q, need) in base_data["q"]
                               and q not in params["must_buy"] and q not in blocked]
                params["no_buy"] = [q for q in base_data["C"] if q not in can_replace and q not in params["must_buy"]]
                if starts:
                    params["start_role_if_bought"] = {q: need for q in can_replace}
                name = "direct/" + need + "_" + names[target].replace(" ", "_") + "_" + plan
                sol = run(name, "direct alternative", base_settings(), params)
                if sol is None:
                    break
                new = [q for q in sol["bought"] if q not in params["must_buy"]]
                if not new:
                    direct.append({"need": need, "plan": plan, "player": "no further signing fits"})
                    break
                choice = new[0]
                objective = run_log[-1]["objective"]
                role = dict(sol["cover"])[choice]
                started = choice in dict(sol["starters"])
            label, reason = likelihood(pool_rows[choice], base_settings(), base_data["f"][choice])
            direct.append({
                "need": need, "plan": plan, "player": names[choice], "club": base_info[choice]["club"],
                "age": base_info[choice]["age"], "role": role, "starts": "yes" if started else "no",
                "quality_in_role": round(base_data["q"][choice, role], 1),
                "fee_gbp_m": round(base_data["f"][choice], 1), "wage_gbp_m": round(base_data["w"][choice], 2),
                "likelihood": label, "reason": reason, "objective": objective,
                "change_from_base": round(objective - base_objective, 2),
            })

    #########Review of every shortlisted player############

    # The same four questions for every player in the lists above. What the data can
    # answer is filled in here; the rest comes from findings entered by hand, and is
    # "not verified" where nobody has looked.
    findings = {}
    for row in read_table(DOCS, "shortlist_checks.csv"):
        findings[row["player"], row["check"]] = row["finding"]
    free_agents = [row["player_id"] for row in read_table(DOCS, "free_agents.csv")]
    review = []
    for row in direct:
        if "club" not in row:
            continue
        p = [q for q in pool_rows if pool_rows[q]["name"] == row["player"]][0]
        info = pool_rows[p]
        if info["joined_club_date"] != "":
            ownership = "At the club since " + info["joined_club_date"] + " (" + info["two_year_evidence"] + ")"
        else:
            ownership = info["two_year_evidence"]
        review.append({
            "need": row["need"], "plan": row["plan"], "player": row["player"], "club_at_cutoff": row["club"],
            "ownership_and_spell": ownership,
            "commitment_before_cutoff": findings.get((row["player"], "commitment"), "Not verified"),
            "contract_or_free_status": findings.get((row["player"], "contract"),
                                                    "Documented free agent" if p in free_agents else "Not verified"),
            "senior_place_needed": "yes" if info["senior_reg"] == "1" else "no",
            "home_grown": findings.get((row["player"], "registration"), "Counted as not home-grown; not verified"),
        })
    review_columns = ["need", "plan", "player", "club_at_cutoff", "ownership_and_spell", "commitment_before_cutoff",
                      "contract_or_free_status", "senior_place_needed", "home_grown"]
    with open(os.path.join(RESULTS, "shortlist_review.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(review_columns)
        for row in review:
            writer.writerow([row[c] for c in review_columns])

    #########Every plan on the base scale, and its overlap with the base plan############

    for entry in run_log:
        if "objective" not in entry:
            continue
        plan = plans[entry["run"]]
        entry["objective_on_base_scale"] = score_on_base_scale(plan["settings"], plan["params"],
                                                               plan["sol"]["bought"], plan["sol"]["sold"])
        entry["signings_shared_with_base"] = len([p for p in plan["sol"]["bought"] if p in base["bought"]])
        entry["sales_shared_with_base"] = len([p for p in plan["sol"]["sold"] if p in base["sold"]])

    #########Write the summary files############

    columns = ["run", "group", "status", "gap", "bound", "runtime", "checks_passed", "objective",
               "objective_on_base_scale", "signings_shared_with_base", "sales_shared_with_base",
               "bought", "sold", "purchase_fees", "sale_receipts", "net_spend", "wages",
               "arrivals", "sales", "senior", "non_homegrown", "candidates"]
    with open(os.path.join(RESULTS, "runs_summary.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        for entry in run_log:
            writer.writerow([entry.get(c, "") for c in columns])

    direct_columns = ["need", "plan", "player", "club", "age", "role", "starts", "quality_in_role", "fee_gbp_m",
                      "wage_gbp_m", "likelihood", "reason", "objective", "change_from_base"]
    with open(os.path.join(RESULTS, "direct_alternatives.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(direct_columns)
        for row in direct:
            writer.writerow([row.get(c, "") for c in direct_columns])

    with open(os.path.join(RESULTS, "full_plan_alternatives.csv"), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["blocked", "run", "objective", "net_spend", "wages", "changes"])
        for row in full_plans:
            entry = [e for e in run_log if e["run"] == row["run"]][0]
            row.update({"objective": entry.get("objective", ""), "net_spend": entry.get("net_spend", ""),
                        "wages": entry.get("wages", "")})
            writer.writerow([row[c] for c in ["blocked", "run", "objective", "net_spend", "wages", "changes"]])

    # Code version, input files and solver details of this set of runs
    def git(*args):
        try:
            return subprocess.run(["git"] + list(args), cwd=HERE, capture_output=True, text=True).stdout.strip()
        except OSError:
            return ""

    inputs = {}
    for folder, label, files in [
            (PROCESSED, "data/processed", ["pool_players.csv", "pool_roles.csv", "scores.csv",
                                           "players_at_cutoff.csv", "player_seasons.csv",
                                           "player_role_starts.csv", "club_seasons.csv"]),
            (MANUAL, "data/manual", ["united_wages.csv", "united_wages_hand_entered.csv"]),
            (PROCESSED, "data/processed", ["club_family.csv"]),
            (DOCS, "docs", ["roster_reconciliation.csv", "unavailable_candidates.csv", "free_agents.csv",
                            "likelihood_notes.csv", "joining_date_overrides.csv", "shortlist_checks.csv",
                            "club_aliases.csv"])]:
        for name in files:
            inputs[label + "/" + name] = file_hash(os.path.join(folder, name))
    manifest = {
        "written": datetime.datetime.now().isoformat(timespec="seconds"),
        "code_commit": git("rev-parse", "HEAD"),
        "uncommitted_code_or_inputs": git("status", "--porcelain", "--", "../src", "../data", "../docs") != "",
        "output_folder": os.path.relpath(RESULTS, os.path.join(HERE, "..")),
        "post_freeze_correction": is_correction(RESULTS),
        "command": "python src/run_scenarios.py --out " + os.path.relpath(RESULTS, os.path.join(HERE, "..")),
        "python": sys.version.split()[0],
        "gurobi": ".".join(str(v) for v in gurobi.version()),
        "packages": {name: metadata.version(name) for name in ["gurobipy", "duckdb", "pdfplumber"]},
        "base_settings": base_settings(),
        "base_params": base_params(),
        "input_sha256": inputs,
        "runs": [{k: entry.get(k, "") for k in ["run", "group", "status", "gap", "bound", "runtime",
                                                 "checks_passed", "objective"]} for entry in run_log],
    }
    with open(os.path.join(RESULTS, "run_manifest.json"), "w") as file:
        json.dump(manifest, file, indent=1, sort_keys=True)

    # A readable page with the main tables
    main_runs = [e for e in run_log if not e["run"].startswith("direct/")]
    budget_rows = [e for e in run_log if e["group"] in ("budget", "base", "comparison")]
    budget_rows.sort(key=lambda e: -1 if e["group"] == "comparison" else plans[e["run"]]["params"]["B"])
    for e in budget_rows:
        e["budget"] = "no transfers" if e["group"] == "comparison" else plans[e["run"]]["params"]["B"]
    page = [
        "# Results of the last run", "",
        ("**Post-freeze correction run.** These results were produced after the 2025/26 outcomes had been "
         "examined, to correct errors found in review. They are not a recommendation frozen before outcomes "
         "were seen; the frozen recommendation is in `results/freeze/`." if is_correction(RESULTS) else ""), "",
        "Written by `src/run_scenarios.py`. Money is in GBP million, wages per year.", "",
        "`objective` is on each run's own scale. `objective_on_base_scale` re-scores the same purchases and "
        "sales with the base quality score and base weights, so that column can be compared across all runs.", "",
        "## Budget and quality", "",
        markdown_table(budget_rows, ["budget", "objective", "net_spend", "wages", "arrivals", "sales", "bought", "sold"]), "",
        "## All runs", "",
        markdown_table(main_runs, ["run", "group", "status", "checks_passed", "objective", "objective_on_base_scale",
                                   "signings_shared_with_base", "bought", "sold", "net_spend", "wages"]), "",
        "## Direct alternatives", "",
        "Plan A is the base signing. For B, C and D the other five purchases and all sales are held fixed, the "
        "earlier choices are ruled out, and the replacement must start in the same role. The rest of the lineup "
        "may still be re-arranged. Options in different rows are not guaranteed to be affordable together. "
        "Likelihood labels are judgement written as rules, not probabilities.", "",
        markdown_table(direct, direct_columns), "",
        "## Review of the shortlisted players", "",
        "The same checks for every player above. A later announcement does not prove that no earlier "
        "commitment existed, so the wording is limited to what the reviewed sources establish.", "",
        markdown_table(review, review_columns), "",
        "## Alternative full plans", "",
        "One signing or sale is ruled out and every transfer and role is decided again.", "",
        markdown_table(full_plans, ["blocked", "objective", "net_spend", "wages", "changes"]), ""]
    with open(os.path.join(RESULTS, "RESULTS.md"), "w") as file:
        file.write("\n".join(page))

    print("Runs:", len(run_log), "| with a failed check:",
          len([e for e in run_log if e.get("checks_passed") == "no"]),
          "| without a plan:", len([e for e in run_log if "objective" not in e]))
