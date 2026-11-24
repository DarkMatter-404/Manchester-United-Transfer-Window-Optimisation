"""Recompute every rule from the chosen players, without using the solver.

The functions here take the lists of sold, bought, squad, cover and starting
players and add up fees, wages and counts again with plain Python. The result
is compared with the limits and with the objective value reported by Gurobi.
"""


def check_solution(data, params, sol, tol=1e-6):
    """Return (totals, problems). An empty problems list means every rule holds."""
    E, C, K = data["E"], data["C"], data["K"]
    G = params["G"]
    q, a, d = data["q"], data["a"], data["d"]

    sold = sol["sold"]
    bought = sol["bought"]
    squad = sol["squad"]
    problems = []

    # Cover and starting roles arrive as (player, role) pairs.
    # A player must not appear in more than one pair of either list.
    cover = {}                    # player -> allocated role
    for (p, g) in sol["cover"]:
        if p in cover:
            problems.append("Player has more than one cover role: " + p)
        cover[p] = g
    starters = {}                 # player -> starting role
    for (p, g) in sol["starters"]:
        if p in starters:
            problems.append("Player starts in more than one role: " + p)
        starters[p] = g

    # Transactions must involve the right kind of player
    for p in sold:
        if p not in E:
            problems.append("Sold player is not an existing player: " + p)
    for p in bought:
        if p not in C:
            problems.append("Bought player is not a candidate: " + p)

    # The squad is: existing players not sold, bought candidates, fixed arrivals
    expected_squad = [p for p in E if p not in sold] + list(bought) + list(K)
    if sorted(expected_squad) != sorted(squad):
        problems.append("Squad does not match the transactions.")

    # Every squad player has exactly one eligible cover role, and nobody else has one
    if sorted(cover.keys()) != sorted(squad):
        problems.append("Cover roles are not given for exactly the squad players.")
    for p in cover:
        if (p, cover[p]) not in q:
            problems.append("Cover role is not an eligible role: " + p + " " + cover[p])

    # A starter must be in the squad and start in the allocated role
    for p in starters:
        if p not in squad:
            problems.append("Starter is not in the squad: " + p)
        elif cover.get(p) != starters[p]:
            problems.append("Starter does not start in the allocated role: " + p)

    # Count players by role
    cover_count = {g: 0 for g in G}
    for p in cover:
        cover_count[cover[p]] += 1
    start_count = {g: 0 for g in G}
    for p in starters:
        start_count[starters[p]] += 1

    for g in G:
        if start_count[g] != params["k"][g]:
            problems.append("Wrong number of starters in role " + g)
        if cover_count[g] < params["l"][g] or cover_count[g] > params["u"][g]:
            problems.append("Cover count outside its bounds in role " + g)

    # Registration counts
    senior = 0
    non_homegrown = 0
    for p in squad:
        if data["t"][p] == 1:
            senior += 1
            if data["h"][p] == 0:
                non_homegrown += 1
    if senior > params["senior_cap"]:
        problems.append("Too many players need a senior-list place.")
    if non_homegrown > params["non_hg_cap"]:
        problems.append("Too many non-homegrown senior-list players.")

    # Money: fees and receipts in GBP million, wages in GBP million per year
    purchase_fees = sum(data["f"][p] for p in bought)
    sale_receipts = sum(data["r"][p] for p in sold)
    net_spend = params["F0"] + purchase_fees - sale_receipts
    wages = sum(data["w"][p] for p in squad)
    if net_spend > params["B"] + tol:
        problems.append("Net transfer spending is above the allowance.")
    if wages > params["W"] + tol:
        problems.append("Annual wages are above the allowance.")

    # Transaction counts
    arrivals = len(K) + len(bought)
    if arrivals > params["TB"]:
        problems.append("Too many arrivals.")
    if len(sold) > params["TS"]:
        problems.append("Too many discretionary sales.")

    # Scenario restrictions
    for p in params.get("no_buy", []):
        if p in bought:
            problems.append("A blocked purchase was made: " + p)
    for p in params.get("no_sell", []):
        if p in sold:
            problems.append("A blocked sale was made: " + p)
    for p in params.get("must_buy", []):
        if p not in bought:
            problems.append("A required purchase was not made: " + p)
    for p in params.get("must_sell", []):
        if p not in sold:
            problems.append("A required sale was not made: " + p)
    for p, g in params.get("start_role_if_bought", {}).items():
        if p in bought and starters.get(p) != g:
            problems.append("A player bought to start in a stated role does not start there: " + p)

    # Objective: starters get the role weight, everyone else the depth weight
    starter_score = 0.0
    depth_score = 0.0
    for p in cover:
        g = cover[p]
        if p in starters:
            starter_score += params["omega"][g] * a[p] * q[p, g]
        else:
            depth_score += a[p] * q[p, g] + params["lam"] * d[p]
    objective = starter_score + params["mu"] * depth_score
    if abs(objective - sol["objective"]) > 1e-4:
        problems.append("Recomputed objective differs from the solver objective.")

    totals = {
        "purchase_fees": purchase_fees,
        "sale_receipts": sale_receipts,
        "fixed_net_fees": params["F0"],
        "net_spend": net_spend,
        "wages": wages,
        "arrivals": arrivals,
        "sales": len(sold),
        "squad_size": len(squad),
        "senior": senior,
        "non_homegrown": non_homegrown,
        "cover_count": cover_count,
        "start_count": start_count,
        "starter_score": starter_score,
        "depth_score": depth_score,
        "objective": objective,
    }
    return totals, problems


def print_solution(data, params, sol, totals):
    """Print a short plain-text summary of a solved plan."""
    name = data["name"]
    print("Status:", sol["status"], "| gap:", round(sol["gap"], 6),
          "| runtime (s):", round(sol["runtime"], 3))
    print("Objective (weighted score points):", round(totals["objective"], 3))
    print("Sold:  ", ", ".join(name[p] for p in sol["sold"]) or "nobody")
    print("Bought:", ", ".join(name[p] for p in sol["bought"]) or "nobody")
    starting_players = [p for (p, g) in sol["starters"]]
    for g in params["G"]:
        starting = [name[p] for (p, role) in sol["starters"] if role == g]
        depth = [name[p] for (p, role) in sol["cover"] if role == g and p not in starting_players]
        print(" ", g, "| starting:", ", ".join(starting), "| depth:", ", ".join(depth) or "-")
    print("Purchase fees:", round(totals["purchase_fees"], 2), "| sale receipts:", round(totals["sale_receipts"], 2),
          "| fixed net fees:", totals["fixed_net_fees"], "| net spend:", round(totals["net_spend"], 2),
          "of", params["B"], "(GBP million)")
    print("Wages:", round(totals["wages"], 2), "of", params["W"], "(GBP million per year)")
    print("Arrivals:", totals["arrivals"], "of", params["TB"],
          "| sales:", totals["sales"], "of", params["TS"],
          "| senior list:", totals["senior"], "of", params["senior_cap"],
          "| non-homegrown:", totals["non_homegrown"], "of", params["non_hg_cap"])
