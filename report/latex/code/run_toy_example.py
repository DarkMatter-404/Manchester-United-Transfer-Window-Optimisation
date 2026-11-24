"""Runnable example of the transfer model (eight invented players).
Keep transfer_model.py, players.csv and roles.csv in this folder."""
import os

from transfer_model import read_inputs, solve_transfer_model

G = ["DEF", "MID", "FWD"]
params = {
    "G": G,
    "k": {g: 1 for g in G},        # starters per role
    "l": {g: 1 for g in G},        # minimum players per role
    "u": {g: 1 for g in G},        # maximum players per role
    "omega": {g: 1.0 for g in G},  # equal role weights
    "mu": 0.0, "lam": 0.0,         # no depth or development reward
    "F0": 0,                       # no committed arrivals
    "W": 10,                       # wage allowance, GBP m per year
    "TB": 6, "TS": 6,              # arrival and sale limits
    "senior_cap": 25, "non_hg_cap": 17,   # registration limits
    "fee_cap": 100,                # highest fee for one player
}
data = read_inputs(os.path.dirname(os.path.abspath(__file__)))

for allowance in (40, 30):         # net allowance B, GBP million
    params["B"] = allowance
    sol = solve_transfer_model(data, params)
    print("Net allowance", allowance, "| status", sol["status"])
    if not sol["has_solution"]:
        continue
    # Spending and wages recomputed from the chosen players
    fees = sum(data["f"][p] for p in sol["bought"])
    receipts = sum(data["r"][p] for p in sol["sold"])
    wages = sum(data["w"][p] for p in sol["squad"])
    print("  objective", sol["objective"], "| gap", sol["gap"])
    print("  bought", sorted(sol["bought"]),
          "| sold", sorted(sol["sold"]))
    print("  starters", sorted(sol["starters"]))
    print("  fees", fees, "| receipts", receipts,
          "| net spend", fees - receipts, "| wages", wages)
