"""Build the model inputs twice from the same raw files and compare the results.

The input steps are run twice in a row. Every file they write must be
byte-for-byte the same both times. The quality scores and eligible roles are
also compared with the versions recorded at the freeze, because the
corrections are not allowed to change the scoring reference.

Run from the repository root:
    python src/check_repeatability.py
The script exits with an error code if any check fails.
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AMAN = os.path.join(HERE, "..")
PROCESSED = os.path.join(AMAN, "data", "processed")
MANUAL = os.path.join(AMAN, "data", "manual")
FREEZE_MANIFEST = os.path.join(AMAN, "results", "freeze", "freeze_manifest.json")

STEPS = ["prepare_inputs.py", "extract_united_wages.py", "build_player_pool.py", "score_players.py"]
OUTPUTS = [os.path.join(PROCESSED, name) for name in
           ["club_seasons.csv", "player_seasons.csv", "player_role_starts.csv", "players_at_cutoff.csv",
            "club_family.csv", "pool_players.csv", "pool_roles.csv", "excluded_candidates.csv", "scores.csv"]]
OUTPUTS.append(os.path.join(MANUAL, "united_wages.csv"))
OUTPUTS.append(os.path.join(AMAN, "docs", "exclusions.csv"))


def file_hash(path):
    with open(path, "rb") as file:
        return hashlib.sha256(file.read()).hexdigest()


def build():
    for step in STEPS:
        result = subprocess.run([sys.executable, os.path.join(HERE, step)], capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout, result.stderr)
            sys.exit("Step failed: " + step)
    return {os.path.relpath(path, AMAN): file_hash(path) for path in OUTPUTS}


failures = []
first = build()
second = build()
for name in first:
    same = first[name] == second[name]
    print("PASS" if same else "FAIL", "same output in two builds |", name, first[name][:16])
    if not same:
        failures.append(name)

# The scoring reference must be the one recorded at the freeze
with open(FREEZE_MANIFEST) as file:
    frozen_inputs = json.load(file)["input_sha256"]
for name in ["data/processed/scores.csv", "data/processed/pool_roles.csv"]:
    same = second[name] == frozen_inputs[name]
    print("PASS" if same else "FAIL", "identical to the version recorded at the freeze |", name)
    if not same:
        failures.append(name + " differs from the freeze")

print()
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("Input builds are repeatable and the scoring reference is unchanged.")
