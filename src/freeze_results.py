"""Freeze the recommendations before any 2025/26 outcome is opened.

The freeze records which code and inputs produced the results, the preferred
plan, the alternatives, every candidate that was considered, and the measures
that will be used to evaluate them. It refuses to run while code or inputs
have uncommitted changes, so the recorded commit really contains them.

Because the study is retrospective, the freeze documents the procedure. It is
not a claim that the plan was made in 2025.

A freeze is made once. The script refuses to write into a folder that already
exists, so the freeze of 17 November 2026 in results/freeze cannot be
overwritten. Rerunning the analysis does not need a new freeze; a new freeze is
only for a new recommendation made before its outcomes are examined.

Run from the repository root, after run_scenarios.py and check_logic.py:
    python src/freeze_results.py --results <folder of a run> --out <new folder>
"""

import csv
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

from model_inputs import base_settings, base_params, build_data, read_table, PROCESSED

HERE = os.path.dirname(os.path.abspath(__file__))
AMAN = os.path.join(HERE, "..")


def argument(flag):
    if flag in sys.argv and sys.argv.index(flag) + 1 < len(sys.argv):
        return os.path.abspath(sys.argv[sys.argv.index(flag) + 1])
    sys.exit("Usage: python src/freeze_results.py --results <folder of a run> --out <new folder>")


RESULTS = argument("--results")
FREEZE = argument("--out")
if os.path.exists(FREEZE):
    sys.exit("A freeze already exists at " + FREEZE + ". A freeze is never overwritten; choose a new folder.")

# Measures fixed now, before outcomes are seen
EVALUATION_PLAN = """# Evaluation plan

Written at the freeze, before any 2025/26 match or valuation record was opened.

## Who is evaluated

1. The six signings of the base plan.
2. Every plan B, C and D player in `direct_alternatives.csv`, whether or not the model preferred them.
3. The three players the base plan sells.
4. For description only: the players Manchester United actually signed between 1 June and 1 September 2025, taken from the transfer records.

## Measures, 2025/26 season

For each player, from league matches in the covered leagues:

- League minutes, starts, and the share of the club's league minutes played.
- Goals plus assists per 90 minutes. For centre-backs and goalkeepers, goals the team conceded per match started.
- The club and league the player played for.
- Market value on the latest valuation dated on or before 12 June 2026, against the value at the cutoff.

## Rules

- A missing outcome is reported as missing with its reason. It is not treated as zero.
- Players are evaluated in the clubs and leagues they actually played in. No league position or points total is inferred for a United squad that never existed.
- The model, its settings and the score are not changed in the light of these outcomes. Any later change is a separate, exploratory analysis and is labelled as such.
- Groups are compared with simple averages and counts. No test of significance is claimed for groups this small.
"""


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=AMAN, capture_output=True, text=True).stdout.strip()


def file_hash(path):
    with open(path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


# The code and the inputs must be committed before they can be frozen
uncommitted = git("status", "--porcelain", "--", "src", "data/processed", "data/manual", "docs",
                  os.path.relpath(RESULTS, AMAN))
uncommitted = [line for line in uncommitted.split("\n") if line]
if uncommitted:
    print("Commit these before freezing:")
    for line in uncommitted:
        print(" ", line)
    sys.exit(1)

os.makedirs(FREEZE, exist_ok=True)

# The preferred plan, the alternatives and the review, copied as they stand
for name in ["direct_alternatives.csv", "full_plan_alternatives.csv", "shortlist_review.csv",
             "runs_summary.csv", "run_manifest.json"]:
    shutil.copy(os.path.join(RESULTS, name), os.path.join(FREEZE, name))
shutil.copy(os.path.join(RESULTS, "base", "squad.csv"), os.path.join(FREEZE, "preferred_plan.csv"))
shutil.copy(os.path.join(RESULTS, "base", "settings.json"), os.path.join(FREEZE, "preferred_plan_settings.json"))

# Every candidate the base case could have bought, not only the ones it chose
data, info, over_cap = build_data(base_settings(), base_params()["fee_cap"])
roles_of = {}
for (p, g) in data["H"]:
    roles_of.setdefault(p, []).append(g)
with open(os.path.join(FREEZE, "candidates_considered.csv"), "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["player_id", "name", "club_at_cutoff", "age", "roles", "fee_gbp_m", "wage_gbp_m"])
    for p in data["C"]:
        writer.writerow([p, data["name"][p], info[p]["club"], info[p]["age"], "/".join(roles_of[p]),
                         round(data["f"][p], 2), round(data["w"][p], 2)])

with open(os.path.join(FREEZE, "evaluation_plan.md"), "w") as file:
    file.write(EVALUATION_PLAN)

# Hashes of everything frozen and of the inputs behind it
frozen_files = {}
for name in sorted(os.listdir(FREEZE)):
    if name != "freeze_manifest.json":
        frozen_files[name] = file_hash(os.path.join(FREEZE, name))
with open(os.path.join(RESULTS, "run_manifest.json")) as file:
    run_manifest = json.load(file)

plan = read_table(FREEZE, "preferred_plan.csv")
manifest = {
    "frozen_at": datetime.datetime.now().isoformat(timespec="seconds"),
    "code_commit": git("rev-parse", "HEAD"),
    "note": "Retrospective study. The freeze documents the procedure; it is not a claim of a plan made in 2025.",
    "base_settings": base_settings(),
    "base_params": base_params(),
    "signings": [row["name"] + " (" + row["role"] + ")" for row in plan if row["action"] == "bought"],
    "sales": [row["name"] for row in plan if row["action"] == "sold"],
    "candidates_considered": len(data["C"]),
    "input_sha256": run_manifest["input_sha256"],
    "frozen_file_sha256": frozen_files,
}
with open(os.path.join(FREEZE, "freeze_manifest.json"), "w") as file:
    json.dump(manifest, file, indent=1, sort_keys=True)

print("Frozen at commit", manifest["code_commit"][:10])
print("Signings:", ", ".join(manifest["signings"]))
print("Sales:", ", ".join(manifest["sales"]))
print("Candidates considered:", manifest["candidates_considered"], "| files frozen:", len(frozen_files))
