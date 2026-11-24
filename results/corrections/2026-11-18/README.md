# Post-freeze correction of 18 November 2026

Start with `correction_log.md` (what was wrong and what changed) and `before_after.md` (the comparison, generated from the files).

| Path | Contents |
|---|---|
| `original_file_hashes.txt` | SHA-256 of the original freeze and evaluation files, recorded before any change |
| `model/` | All 56 runs with the corrected inputs; `model/run_manifest.json` has the code commit, input hashes, package versions and solver details |
| `evaluation/` | The corrected evaluation of the frozen recommendation: `player_outcomes.csv`, `player_club_outcomes.csv`, `group_summary.csv`, `EVALUATION.md`; `evaluation_manifest.json` has the code commit, input and raw-file hashes, package version and command |
| `shortlist_review_2026-11-18.csv` | Dated review of the six signings and the plan B in each role |
| `check_logs/` | Output of every check run for this correction |
| `before_after.md` | Original against corrected, by `src/compare_corrections.py` |

## Reproducing these outputs

From the repository root, with the raw files in `aman/data/raw/transfermarkt/` matching `aman/docs/raw_data_checksums.txt` and a Gurobi licence in the home folder. Tested with Python 3.12.11, gurobipy 14.0.0, duckdb 2.0.0 and pdfplumber 0.11.10. The code version is in `model/run_manifest.json` (`code_commit`).

```
C=aman/results/corrections/2026-11-18
aman/.venv/bin/python aman/src/toy_model.py
aman/.venv/bin/python aman/src/check_repeatability.py        # builds the inputs twice
aman/.venv/bin/python aman/src/run_scenarios.py --out $C/model
aman/.venv/bin/python aman/src/check_logic.py --results $C/model
aman/.venv/bin/python aman/src/evaluate_results.py --freeze aman/results/freeze --out $C/evaluation
aman/.venv/bin/python aman/src/check_evaluation.py --freeze aman/results/freeze --evaluation $C/evaluation
aman/.venv/bin/python aman/src/compare_corrections.py --corrections $C
```

No step writes into `aman/results/freeze/`, `aman/results/evaluation/` or the other original result folders, and no new freeze is made. Solver runtimes differ between machines; everything else should match.
