"""Turn the player pool, scores and wage table into inputs for the transfer model.

Two dictionaries describe a run:

    settings   how fees, wages and availability are derived from the data
    params     the limits and weights of the optimisation model

Money is in GBP million; wages are per year.
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROCESSED = os.path.join(HERE, "..", "data", "processed")
MANUAL = os.path.join(HERE, "..", "data", "manual")
DOCS = os.path.join(HERE, "..", "docs")

ROLES = ["GK", "CB", "WB", "CM", "AM", "ST"]

# Weekly gross wage of a new signing by estimated fee: (fee of at least, GBP million; weekly wage, GBP)
WAGE_BANDS = [(70, 250000), (50, 200000), (35, 150000), (20, 110000), (10, 75000), (0, 45000)]

# A key player: played at least this share of the club's league minutes in 2024/25
# for a club that finished at least this high in its league
KEY_PLAYER_MINUTES_SHARE = 0.70
KEY_PLAYER_CLUB_RANK = 4

# United is assumed unlikely to pay this much for one player
DOUBTFUL_FEE = 75


def read_table(folder, name):
    with open(os.path.join(folder, name), newline="") as file:
        return list(csv.DictReader(file))


def band_wage(fee):
    """Annual wage for a signing whose estimated fee is this much."""
    for floor, weekly in WAGE_BANDS:
        if fee >= floor:
            return weekly * 52 / 1000000.0


def base_settings():
    """How model inputs are built from the data in the base case."""
    return {
        "alpha": 1.1,               # purchase fee = alpha x market value
        "alpha_english_pl": 1.3,    # the same for an English player at a Premier League club
        # Clubs that are assumed never to sell to United
        "blocked_clubs": ["Manchester City", "Liverpool FC"],
        # Other rivals sell only at a mark-up over market value
        "club_multiplier": {"Arsenal FC": 2.0, "Chelsea FC": 1.5, "Tottenham Hotspur": 1.5},
        # A regular starter at a club that finished in its league's top four is not sold cheaply
        "key_player_multiplier": 1.5,
        # Clubs rich enough not to need a sale; the same mark-up applies to all their players
        "elite_clubs": ["Paris Saint-Germain", "FC Barcelona", "Real Madrid", "Bayern Munich"],
        "elite_club_multiplier": 1.5,
        "beta": 0.9,                # sale receipt = beta x market value
        "quality": "quality",       # score column: "quality" or "quality_no_value"
        "candidates": True,         # False leaves all candidates out (no purchases possible)
        "two_year_rule": True,      # leave out candidates whose current spell began within two years
        "united_wages": "table",    # "table" uses the wage table, "bands" uses the candidate bands
        "candidate_wage_factor": 1.0,   # scales every candidate's wage, for wage-uncertainty runs
        # False: a candidate's wage is set once, from the base fee rule, and does not move with
        # the fee scenario. True: the wage band follows the scenario fee (a combined scenario).
        "wage_follows_fee": False,
        "fixed_arrivals": {},       # player id -> committed fee, for a deal treated as already agreed
    }


def base_params():
    """Limits and weights of the base case."""
    return {
        "G": ROLES,
        "k": {"GK": 1, "CB": 3, "WB": 2, "CM": 2, "AM": 2, "ST": 1},   # starters in a 3-4-2-1
        "l": {"GK": 2, "CB": 5, "WB": 4, "CM": 4, "AM": 4, "ST": 2},   # minimum players per role
        "u": {"GK": 3, "CB": 7, "WB": 5, "CM": 5, "AM": 6, "ST": 3},   # maximum players per role
        "omega": {g: 1.0 for g in ROLES},   # equal role weights
        "mu": 0.3,          # a squad player who does not start counts 0.3 of a starter
        "lam": 0.0,         # no development bonus
        "B": 250,           # net transfer allowance
        "F0": 0,            # no fixed commitments in the base case
        "W": 148,           # annual wage allowance
        "TB": 6,            # arrivals
        "TS": 6,            # discretionary sales
        "senior_cap": 25,   # senior-list places
        "non_hg_cap": 17,   # non-home-grown senior-list places
        "fee_cap": 75,      # highest fee for one purchase
    }


def is_key_player(row):
    return (float(row["minutes_share_2024"]) >= KEY_PLAYER_MINUTES_SHARE
            and int(row["club_rank_2024"]) <= KEY_PLAYER_CLUB_RANK)


def fee_multiplier(row, settings):
    """Fee as a multiple of market value. The highest applicable mark-up is used."""
    english_pl = row["country"] == "England" and row["league"] == "GB1"
    multiplier = settings["alpha_english_pl"] if english_pl else settings["alpha"]
    multiplier = max(multiplier, settings["club_multiplier"].get(row["club_name"], 0))
    if is_key_player(row):
        multiplier = max(multiplier, settings["key_player_multiplier"])
    if row["club_name"] in settings["elite_clubs"]:
        multiplier = max(multiplier, settings["elite_club_multiplier"])
    return multiplier


def candidate_terms(row, settings, free_agents):
    """Return (payable fee, annual wage) for one candidate.

    The payable fee is what the model charges against the budget and compares
    with the fee ceiling. A documented free agent pays nothing.

    The wage does not depend on the fee scenario unless the run says so. It
    comes from the wage band of the fee the complete base rule would give
    (base multipliers and base club rules), so that neither a cheaper or dearer
    transfer market nor a change to the club rules also changes wages, and so
    that a free agent is still paid like a player of the same value. Only a run
    marked as a combined fee-and-wage scenario lets the wage follow its fee.
    """
    value = float(row["value_gbp_m"])
    scenario_fee = fee_multiplier(row, settings) * value
    payable_fee = 0.0 if row["player_id"] in free_agents else scenario_fee

    if settings["wage_follows_fee"]:
        wage_basis = scenario_fee
    else:
        wage_basis = fee_multiplier(row, base_settings()) * value
    wage = band_wage(wage_basis) * settings["candidate_wage_factor"]
    return payable_fee, wage


def build_data(settings, fee_cap):
    """Build the dictionaries the model reads.

    Also returns extra columns for output files and the names of candidates
    left out because their payable fee is above the ceiling.
    """
    pool = read_table(PROCESSED, "pool_players.csv")
    scores = read_table(PROCESSED, "scores.csv")
    wage_table = {row["player_id"]: float(row["annual_wage_gbp"]) / 1000000.0
                  for row in read_table(MANUAL, "united_wages.csv")}
    free_agents = [row["player_id"] for row in read_table(DOCS, "free_agents.csv")]

    data = {"E": [], "C": [], "K": [], "name": {}, "H": [], "q": {},
            "a": {}, "d": {}, "f": {}, "r": {}, "w": {}, "h": {}, "t": {}}
    info = {}
    over_cap = []

    for row in pool:
        p = row["player_id"]
        value = float(row["value_gbp_m"])     # dated on or before the cutoff

        if row["status"] == "E":
            data["E"].append(p)
            data["r"][p] = settings["beta"] * value
            if settings["united_wages"] == "table":
                data["w"][p] = wage_table[p]
            else:
                data["w"][p] = band_wage(base_settings()["alpha"] * value)
        elif p in settings["fixed_arrivals"]:
            # A deal treated as agreed before the cutoff: the player joins whatever else is decided.
            # The committed fee is counted through F0 in the run's limits.
            data["K"].append(p)
            data["w"][p] = band_wage(settings["fixed_arrivals"][p])
        elif row["status"] == "C":
            if not settings["candidates"]:
                continue
            if row["club_name"] in settings["blocked_clubs"]:
                continue
            # Two-year rule: only candidates whose current spell is known to be older are kept
            if settings["two_year_rule"] and row["two_year_status"] != "eligible":
                continue
            payable_fee, wage = candidate_terms(row, settings, free_agents)
            if payable_fee > fee_cap:
                over_cap.append(row["name"])
                continue
            data["C"].append(p)
            data["f"][p] = payable_fee
            data["w"][p] = wage
        else:
            continue

        data["name"][p] = row["name"]
        data["h"][p] = int(row["homegrown"])
        data["t"][p] = int(row["senior_reg"])
        data["a"][p] = 1.0     # availability is not quantified
        data["d"][p] = 0.0     # no development indicator
        info[p] = {"club": row["club_name"], "age": row["age_at_cutoff"], "value": value}

    for row in scores:
        p = row["player_id"]
        if p in data["name"]:
            data["H"].append((p, row["role"]))
            data["q"][p, row["role"]] = float(row[settings["quality"]])

    return data, info, over_cap


def unavailable_candidates(data):
    """Candidates that dated evidence or a team ruling says could not be signed."""
    listed = [row["player_id"] for row in read_table(DOCS, "unavailable_candidates.csv")]
    return [p for p in listed if p in data["C"]]


def likelihood(row, settings, fee):
    """A rough, judgement-based label for how likely a purchase is, with its reason.

    These labels are assumptions written down as rules. They are not estimated
    from past deals and are not probabilities.
    """
    for note in read_table(DOCS, "likelihood_notes.csv"):
        if note["player_id"] == row["player_id"]:
            return note["likelihood"], note["reason"]
    free_agents = [r["player_id"] for r in read_table(DOCS, "free_agents.csv")]
    if row["player_id"] in free_agents:
        return "likely", "leaving the club without a fee"
    if row["club_name"] in settings["club_multiplier"]:
        return "doubtful", "plays for a direct rival"
    if row["club_name"] in settings["elite_clubs"]:
        return "doubtful", "club has no need to sell"
    if is_key_player(row):
        return "doubtful", "regular starter at a top-four club"
    if fee >= DOUBTFUL_FEE:
        return "doubtful", "fee of GBP 75 million or more"
    if float(row["minutes_share_2024"]) < 0.5:
        return "likely", "played under half of the club's league minutes"
    if int(row["club_rank_2024"]) >= 15:
        return "likely", "club finished 15th or lower"
    if int(row["club_rank_2024"]) <= KEY_PLAYER_CLUB_RANK:
        return "possible", "at a top-four club but played under 70% of its league minutes"
    return "possible", "regular player at a club outside the top four"
