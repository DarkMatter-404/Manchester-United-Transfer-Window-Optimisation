"""Transfer-window model for one club and one window.

The model chooses permanent sales and purchases, the final squad, one cover
role for every squad player and a starting eleven.

Units
    fees and sale receipts   GBP million, whole transaction amounts
    wages                    GBP million per year
    quality, development     score points on a 0-100 scale
    availability             a number between 0 and 1
"""

import csv
import os

from gurobipy import *


STATUS_NAMES = {
    GRB.OPTIMAL: "OPTIMAL",
    GRB.INFEASIBLE: "INFEASIBLE",
    GRB.INF_OR_UNBD: "INF_OR_UNBD",
    GRB.UNBOUNDED: "UNBOUNDED",
    GRB.TIME_LIMIT: "TIME_LIMIT",
    GRB.INTERRUPTED: "INTERRUPTED",
    GRB.SUBOPTIMAL: "SUBOPTIMAL",
}


def read_inputs(folder):
    """Read players.csv and roles.csv from a folder into plain dictionaries."""
    data = {
        "E": [], "C": [], "K": [],   # existing players, candidates, fixed arrivals
        "name": {},
        "H": [], "q": {},            # eligible (player, role) pairs and their quality
        "a": {}, "d": {},            # availability and development indicator
        "f": {}, "r": {}, "w": {},   # purchase fee, sale receipt, annual wage
        "h": {}, "t": {},            # homegrown flag, senior-registration flag
    }

    with open(os.path.join(folder, "players.csv"), newline="") as file:
        for row in csv.DictReader(file):
            p = row["player_id"]
            status = row["status"]
            if status not in ("E", "C", "K"):
                raise ValueError("Unknown status for player " + p + ": " + status)
            data[status].append(p)
            data["name"][p] = row["name"]
            data["w"][p] = float(row["wage"])
            data["h"][p] = int(row["homegrown"])
            data["t"][p] = int(row["senior_reg"])
            data["a"][p] = float(row["availability"])
            data["d"][p] = float(row["development"])
            # A purchase fee applies to candidates, a sale receipt to existing players
            if status == "C":
                data["f"][p] = float(row["fee"])
            if status == "E":
                data["r"][p] = float(row["receipt"])

    with open(os.path.join(folder, "roles.csv"), newline="") as file:
        for row in csv.DictReader(file):
            pair = (row["player_id"], row["role"])
            data["H"].append(pair)
            data["q"][pair] = float(row["quality"])

    return data


def check_inputs(data, params):
    """Return a list of input problems. An empty list means the inputs are usable."""
    problems = []
    E, C, K = data["E"], data["C"], data["K"]
    P = E + C + K
    G = params["G"]

    # The three player sets must not overlap
    if len(set(P)) != len(P):
        problems.append("A player appears more than once across E, C and K.")

    # Every eligible pair must refer to a known player and a known role
    has_role = {p: False for p in P}
    for (p, g) in data["H"]:
        if p not in has_role:
            problems.append("Role listed for an unknown player: " + str(p))
        elif g not in G:
            problems.append("Unknown role " + str(g) + " for player " + str(p))
        else:
            has_role[p] = True
    if len(set(data["H"])) != len(data["H"]):
        problems.append("A (player, role) pair is listed more than once.")

    # A player without a role cannot be placed in the squad
    for p in P:
        if not has_role[p]:
            problems.append("Player has no eligible role: " + str(p))

    # Money and flags
    for p in C:
        if data["f"][p] < 0 or data["f"][p] > params["fee_cap"]:
            problems.append("Candidate fee outside 0 to fee cap: " + str(p))
    for p in E:
        if data["r"][p] < 0:
            problems.append("Negative sale receipt: " + str(p))
    for p in P:
        if data["w"][p] < 0:
            problems.append("Negative wage: " + str(p))
        if data["a"][p] < 0 or data["a"][p] > 1:
            problems.append("Availability outside 0 to 1: " + str(p))
        if data["h"][p] not in (0, 1) or data["t"][p] not in (0, 1):
            problems.append("Registration flags must be 0 or 1: " + str(p))

    # Cover must be at least the number of starters in each role
    for g in G:
        if not (params["k"][g] <= params["l"][g] <= params["u"][g]):
            problems.append("Need starters <= minimum cover <= maximum cover for role " + g)

    # Scenario restrictions must name real players
    for p in params.get("no_buy", []):
        if p not in C:
            problems.append("Blocked purchase is not a candidate: " + str(p))
    for p in params.get("no_sell", []):
        if p not in E:
            problems.append("Blocked sale is not an existing player: " + str(p))
    for p in params.get("must_buy", []):
        if p not in C:
            problems.append("Required purchase is not a candidate: " + str(p))
    for p in params.get("must_sell", []):
        if p not in E:
            problems.append("Required sale is not an existing player: " + str(p))
    for p, g in params.get("start_role_if_bought", {}).items():
        if p not in C or (p, g) not in data["q"]:
            problems.append("Starting-role condition names a candidate who cannot play that role: " + str(p))

    return problems


def solve_transfer_model(data, params, model_name="transfer_model",
                         show_log=False, time_limit=None, find_iis=True):
    """Build and solve the model. Returns a dictionary describing the outcome."""
    problems = check_inputs(data, params)
    if problems:
        raise ValueError("Input problems:\n" + "\n".join(problems))

    #########Parameters Set-up############

    E = data["E"]             # existing players who can be kept or sold
    C = data["C"]             # candidates who can be bought
    K = data["K"]             # arrivals already committed before the cutoff
    P = E + C + K
    H = data["H"]             # eligible (player, role) pairs
    q = data["q"]             # quality of player p in role g
    a = data["a"]             # availability adjustment
    d = data["d"]             # development indicator
    f = data["f"]             # purchase fee, GBP million
    r = data["r"]             # sale receipt, GBP million
    w = data["w"]             # annual wage, GBP million per year
    h = data["h"]             # 1 if homegrown
    t = data["t"]             # 1 if the player needs a senior-list place

    G = params["G"]           # roles
    k = params["k"]           # starters needed in each role
    l = params["l"]           # minimum players allocated to each role
    u = params["u"]           # maximum players allocated to each role
    omega = params["omega"]   # priority weight of each role
    mu = params["mu"]         # weight on depth relative to starters
    lam = params["lam"]       # weight on development inside the depth term
    B = params["B"]           # net transfer allowance, GBP million
    F0 = params["F0"]         # net fees of fixed commitments, GBP million
    W = params["W"]           # annual wage allowance, GBP million per year
    TB = params["TB"]         # maximum arrivals, fixed arrivals included
    TS = params["TS"]         # maximum discretionary sales
    senior_cap = params["senior_cap"]     # senior-list places
    non_hg_cap = params["non_hg_cap"]     # non-homegrown senior-list places
    no_buy = params.get("no_buy", [])     # candidates unavailable in this run
    no_sell = params.get("no_sell", [])   # existing players who cannot be sold in this run
    must_buy = params.get("must_buy", [])     # purchases taken as given in this run
    must_sell = params.get("must_sell", [])   # sales taken as given in this run
    start_role_if_bought = params.get("start_role_if_bought", {})   # candidate -> role to start in if bought

    # Eligible roles of each player and eligible players of each role
    roles_of = {p: [] for p in P}
    players_of = {g: [] for g in G}
    for (p, g) in H:
        roles_of[p].append(g)
        players_of[g].append(p)

    #########Model Set-up###############

    m = Model(model_name)
    m.Params.OutputFlag = 1 if show_log else 0
    if time_limit is not None:
        m.Params.TimeLimit = time_limit

    # Create transfer variables
    s = m.addVars(E, vtype=GRB.BINARY, name="sell")
    b = m.addVars(C, vtype=GRB.BINARY, name="buy")

    # Create squad, cover-role and starting-role variables
    x = m.addVars(P, vtype=GRB.BINARY, name="squad")
    z = m.addVars(H, vtype=GRB.BINARY, name="cover")
    y = m.addVars(H, vtype=GRB.BINARY, name="start")

    # Set objective: weighted starter quality plus a smaller reward for depth.
    # z - y equals 1 only for a squad player who is not starting, so each
    # player is counted once, either as a starter or as depth.
    starter_score = quicksum(omega[g] * a[p] * q[p, g] * y[p, g] for (p, g) in H)
    depth_score = quicksum((a[p] * q[p, g] + lam * d[p]) * (z[p, g] - y[p, g]) for (p, g) in H)
    m.setObjective(starter_score + mu * depth_score, GRB.MAXIMIZE)

    # Squad membership follows the transactions
    m.addConstrs((x[p] == 1 - s[p] for p in E), name="link_existing")
    m.addConstrs((x[p] == b[p] for p in C), name="link_candidate")
    m.addConstrs((x[p] == 1 for p in K), name="link_fixed")

    # Each squad player is allocated to exactly one eligible role
    m.addConstrs((quicksum(z[p, g] for g in roles_of[p]) == x[p] for p in P), name="one_cover_role")

    # A player can start only in the allocated role
    m.addConstrs((y[p, g] <= z[p, g] for (p, g) in H), name="start_in_cover_role")

    # Fill every starting place in the formation
    m.addConstrs((quicksum(y[p, g] for p in players_of[g]) == k[g] for g in G), name="formation")

    # Positional cover, starters included
    m.addConstrs((quicksum(z[p, g] for p in players_of[g]) >= l[g] for g in G), name="cover_min")
    m.addConstrs((quicksum(z[p, g] for p in players_of[g]) <= u[g] for g in G), name="cover_max")

    # Senior registration limits
    m.addConstr(quicksum(t[p] * x[p] for p in P) <= senior_cap, name="senior_list")
    m.addConstr(quicksum(t[p] * (1 - h[p]) * x[p] for p in P) <= non_hg_cap, name="non_homegrown")

    # Net transfer spending: fixed commitments plus purchases minus sale receipts
    m.addConstr(F0 + quicksum(f[p] * b[p] for p in C) - quicksum(r[p] * s[p] for p in E) <= B,
                name="net_spend")

    # Annual wages of the final squad
    m.addConstr(quicksum(w[p] * x[p] for p in P) <= W, name="wages")

    # Number of arrivals (fixed arrivals count) and of discretionary sales
    m.addConstr(len(K) + quicksum(b[p] for p in C) <= TB, name="arrivals")
    m.addConstr(quicksum(s[p] for p in E) <= TS, name="sales")

    # Scenario restrictions: a blocked purchase or a sale that cannot happen
    m.addConstrs((b[p] == 0 for p in no_buy), name="no_buy")
    m.addConstrs((s[p] == 0 for p in no_sell), name="no_sell")

    # Scenario restrictions: part of a plan held fixed while the rest is re-decided
    m.addConstrs((b[p] == 1 for p in must_buy), name="must_buy")
    m.addConstrs((s[p] == 1 for p in must_sell), name="must_sell")

    # Scenario restriction: a listed candidate may be bought only to start in the stated role
    m.addConstrs((b[p] <= y[p, g] for p, g in start_role_if_bought.items()), name="start_role_if_bought")

    # Solve the model
    m.optimize()
    if m.Status == GRB.INF_OR_UNBD:
        # All variables are binary, so the model cannot be unbounded.
        # Solve again with this setting to get a definite status.
        m.Params.DualReductions = 0
        m.optimize()

    # Collect the outcome. Solution values are read only when a solution exists.
    sol = {
        "status": STATUS_NAMES.get(m.Status, str(m.Status)),
        "has_solution": m.SolCount > 0,
        "runtime": m.Runtime,
        "num_vars": m.NumVars,
        "num_constrs": m.NumConstrs,
    }

    if m.SolCount > 0:
        sol["objective"] = m.ObjVal
        sol["bound"] = m.ObjBound
        sol["gap"] = m.MIPGap
        sol["sold"] = [p for p in E if s[p].X > 0.5]
        sol["bought"] = [p for p in C if b[p].X > 0.5]
        sol["squad"] = [p for p in P if x[p].X > 0.5]
        # Lists of (player, role) pairs, so a repeated player would be visible
        sol["cover"] = [(p, g) for (p, g) in H if z[p, g].X > 0.5]
        sol["starters"] = [(p, g) for (p, g) in H if y[p, g].X > 0.5]
    elif m.Status == GRB.INFEASIBLE and find_iis:
        # List a small set of rules that cannot all hold together
        m.computeIIS()
        sol["iis"] = [c.ConstrName for c in m.getConstrs() if c.IISConstr]

    return sol
