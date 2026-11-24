"""Fill the result tables in the report from the saved output files.

The report marks each generated table like this:

    <!-- generated: budget -->
    ...table...
    <!-- end generated -->

This script replaces everything between the two markers with a table built
from the run and evaluation outputs, so no figure in those tables is typed
in by hand.

Run from the repository root:
    python src/fill_report_tables.py --model results/corrections/2026-11-18/model --evaluation results/corrections/2026-11-18/evaluation
"""

import csv
import os
import re

from output_paths import input_folder

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "..", "report", "report.md")
MODEL = input_folder("--model")
EVALUATION = input_folder("--evaluation")
ROLES = ["GK", "CB", "WB", "CM", "AM", "ST"]


def read_csv(path):
    with open(path, newline="") as file:
        return list(csv.DictReader(file))


def is_number(text):
    text = str(text).replace(",", "").replace("%", "").replace("+", "").replace("£", "").strip()
    try:
        float(text)
        return True
    except ValueError:
        return False


def table(rows, columns):
    """A markdown table; columns whose values are all numbers are right-aligned."""
    aligns = []
    for c in columns:
        values = [row.get(c, "") for row in rows if row.get(c, "") != ""]
        aligns.append("---:" if values and all(is_number(v) for v in values) else "---")
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(aligns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return "\n".join(lines)


def money(value):
    return "{:.1f}".format(float(value))


runs = {r["run"]: r for r in read_csv(os.path.join(MODEL, "runs_summary.csv"))}
base = runs["base"]
base_objective = float(base["objective"])


def difference(name):
    return "{:+.1f}".format(float(runs[name]["objective"]) - base_objective)


tables = {}

#########Base plan############

squad = read_csv(os.path.join(MODEL, "base", "squad.csv"))
summary = {r["item"]: r["value"] for r in read_csv(os.path.join(MODEL, "base", "summary.csv"))}
none = {r["item"]: r["value"] for r in read_csv(os.path.join(MODEL, "no_transfers", "summary.csv"))}
signings = ", ".join(r["name"] + " (" + r["role"] + ", "
                     + ("no fee" if float(r["fee_or_receipt_gbp_m"]) == 0 else "£" + money(r["fee_or_receipt_gbp_m"]) + "m") + ")"
                     for r in squad if r["action"] == "bought")
sales = ", ".join(r["name"] + " (£" + money(r["fee_or_receipt_gbp_m"]) + "m)" for r in squad if r["action"] == "sold")
lineup = "; ".join(g + ": " + ", ".join(r["name"] for r in squad if r["starter"] == "1" and r["role"] == g) for g in ROLES)
tables["base_plan"] = table([
    {"": "Objective", "No transfers": "{:,.1f}".format(float(none["objective"])), "Base plan": "{:,.1f}".format(float(summary["objective"]))},
    {"": "Signings", "No transfers": "none", "Base plan": signings},
    {"": "Sales (receipts)", "No transfers": "none", "Base plan": sales},
    {"": "Starting eleven", "No transfers": "", "Base plan": lineup},
    {"": "Net spend, £m", "No transfers": "0", "Base plan": money(summary["net_spend"]) + " of 250"},
    {"": "Wages, £m a year", "No transfers": money(none["wages"]), "Base plan": "{:.2f}".format(float(summary["wages"])) + " of 148"},
    {"": "Arrivals, sales", "No transfers": "0, 0", "Base plan": summary["arrivals"].split(".")[0] + " of 6, " + summary["sales"].split(".")[0] + " of 6"},
    {"": "Candidates available", "No transfers": "0", "Base plan": summary["candidates_available"]},
], ["", "No transfers", "Base plan"])

#########Budget against quality############

rows = [{"Net budget": "No transfers", "Objective": "{:,.1f}".format(float(runs["no_transfers"]["objective"])),
         "Gain over the step before": "", "Net spend": "0", "Wages": money(runs["no_transfers"]["wages"])}]
previous = float(runs["no_transfers"]["objective"])
for budget, name in [(0, "sensitivity/budget_0"), (50, "sensitivity/budget_50"), (100, "sensitivity/budget_100"),
                     (150, "sensitivity/budget_150"), (200, "sensitivity/budget_200"), (250, "base"),
                     (300, "sensitivity/budget_300")]:
    value = float(runs[name]["objective"])
    rows.append({"Net budget": "£" + str(budget) + "m" + (" (base)" if name == "base" else ""),
                 "Objective": "{:,.1f}".format(value), "Gain over the step before": "{:+.1f}".format(value - previous),
                 "Net spend": money(runs[name]["net_spend"]), "Wages": money(runs[name]["wages"])})
    previous = value
tables["budget"] = table(rows, ["Net budget", "Objective", "Gain over the step before", "Net spend", "Wages"])

#########What binds############

tables["limits"] = table([{"Change": label, "Objective": "{:,.1f}".format(float(runs[name]["objective"])),
                           "Difference from base": difference(name)} for label, name in [
    ("Four arrivals instead of six", "sensitivity/arrivals_4"),
    ("Five arrivals instead of six", "sensitivity/arrivals_5"),
    ("Wage allowance held at today's £133.4m", "sensitivity/wage_allowance_no_growth"),
    ("Wage allowance removed", "sensitivity/wage_allowance_removed"),
    ("Fee ceiling £100m instead of £75m", "sensitivity/fee_ceiling_100")]],
    ["Change", "Objective", "Difference from base"])

#########Sensitivity on the same scale############

rows = []
for label, name in [("Fees 0.9 × value, wages unchanged", "sensitivity/fee_only_0.9"),
                    ("Fees 1.5 × value, wages unchanged", "sensitivity/fee_only_1.5"),
                    ("Candidate wages 10% lower, fees unchanged", "sensitivity/candidate_wages_minus_10"),
                    ("Candidate wages 10% higher, fees unchanged", "sensitivity/candidate_wages_plus_10"),
                    ("Combined: fees 0.9 × and wage bands follow", "sensitivity/combined_fee_and_wage_0.9"),
                    ("Combined: fees 1.5 × and wage bands follow", "sensitivity/combined_fee_and_wage_1.5"),
                    ("Sale receipts 0.7 × value", "sensitivity/sale_receipt_0.7"),
                    ("Sale receipts 1.0 × value", "sensitivity/sale_receipt_1.0"),
                    ("Club rules removed, wages unchanged", "sensitivity/rivals_like_other_clubs"),
                    ("United's wages from the candidate bands", "sensitivity/united_wages_by_bands"),
                    ("Cunha fixed as an arrival at £62.5m", "sensitivity/cunha_fixed"),
                    ("Without the two-year rule", "sensitivity/without_two_year_rule")]:
    r = runs[name]
    rows.append({"Change": label, "Difference from base": difference(name), "Net spend": money(r["net_spend"]),
                 "Signings shared with base": r["signings_shared_with_base"] + " of 6"})
tables["sensitivity"] = table(rows, ["Change", "Difference from base", "Net spend", "Signings shared with base"])

#########Scoring choices, re-scored on the base scale############

rows = []
for label, name in [("Depth weight 0.2", "sensitivity/depth_weight_0.2"), ("Depth weight 0.4", "sensitivity/depth_weight_0.4"),
                    ("Role weights favouring weak roles", "sensitivity/weakness_weights"),
                    ("Score without market value", "sensitivity/quality_without_value")]:
    r = runs[name]
    rows.append({"Change": label, "On the base scale": "{:,.1f}".format(float(r["objective_on_base_scale"])),
                 "Signings shared with base": r["signings_shared_with_base"] + " of 6"})
tables["scoring"] = table(rows, ["Change", "On the base scale", "Signings shared with base"])

#########Direct alternatives############

direct = read_csv(os.path.join(MODEL, "direct_alternatives.csv"))
rows = []
for g in ROLES:
    row = {"Need": g}
    for r in direct:
        if r["need"] == g and r["likelihood"]:
            row["Plan " + r["plan"]] = r["player"] + " (" + r["likelihood"] + ")"
    rows.append(row)
tables["direct"] = table(rows, ["Need", "Plan A", "Plan B", "Plan C", "Plan D"])

#########Evaluation############

summary = read_csv(os.path.join(EVALUATION, "group_summary.csv"))
by = {}
for r in summary:
    by.setdefault(r["group"], {})[r["measure"]] = r
labels = [("base signing", "Base signings"), ("direct alternative", "Direct alternatives (B to D)"),
          ("actual United signing", "Players United actually signed"), ("sold in the base plan", "Players the base plan sells")]
rows = []
for key, label in labels:
    share = by[key]["share of main club's league minutes"]
    value = by[key]["change in market value, %"]
    rows.append({"Group": label, "Memberships": share["memberships"], "Valid (minutes)": share["valid_observations"],
                 "Mean share of main club's league minutes": "{:.2f}".format(float(share["mean"])),
                 "Mean change in market value": "{:+.1f}%".format(float(value["mean"])),
                 "Median share (added later)": "{:.2f}".format(float(share["median_added_after_evaluation"])),
                 "Median value change (added later)": "{:+.1f}%".format(float(value["median_added_after_evaluation"]))})
tables["evaluation"] = table(rows, ["Group", "Memberships", "Valid (minutes)", "Mean share of main club's league minutes",
                                    "Mean change in market value", "Median share (added later)",
                                    "Median value change (added later)"])

#########Write into the report############

with open(REPORT) as file:
    text = file.read()
for name, content in tables.items():
    pattern = re.compile(r"(<!-- generated: " + name + r" -->\n).*?(<!-- end generated -->)", re.S)
    if len(pattern.findall(text)) != 1:
        raise ValueError("Expected one marked block for table '" + name + "' in the report")
    text = pattern.sub(lambda m: m.group(1) + content + "\n" + m.group(2), text)
with open(REPORT, "w") as file:
    file.write(text)
print("Filled", len(tables), "tables in", os.path.relpath(REPORT))
