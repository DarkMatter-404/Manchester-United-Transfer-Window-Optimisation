"""Descriptive comparison of transfer fees with market values before the cutoff.

This is the exploratory calculation that informed the team's choice of a 1.3
fee multiplier for English players at Premier League clubs. It describes past
transfers; it does not estimate a causal premium for nationality, and its
output is not an input to the model.

Sample: transfers dated 1 June 2021 to 31 May 2025 between clubs whose
domestic league is one of the five candidate leagues, with a recorded fee and
a recorded market value of at least EUR 5 million each, for players aged 26 or
under on the transfer date. The market value is the one stored with the
transfer record. Rows with a missing fee, value or birth date drop out through
these filters. The club league and the citizenship are the source's stored
fields, which are not dated.

Run from the repository root:
    python src/fee_ratio_check.py
"""

import os

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw", "transfermarkt")
LEAGUES = ("GB1", "ES1", "IT1", "L1", "FR1")


def path(name):
    return os.path.join(RAW, name + ".csv.gz")


con = duckdb.connect()
rows = con.execute(f"""
    WITH clubs AS (
        SELECT club_id, domestic_competition_id AS league FROM read_csv_auto('{path("clubs")}')
    )
    SELECT t.transfer_date,
           t.transfer_fee / t.market_value_in_eur AS ratio,
           p.country_of_citizenship AS country,
           cf.league AS from_league,
           date_part('year', age(t.transfer_date, CAST(p.date_of_birth AS DATE))) AS age
    FROM read_csv_auto('{path("transfers")}') t
    JOIN read_csv_auto('{path("players")}') p USING (player_id)
    JOIN clubs cf ON cf.club_id = t.from_club_id
    JOIN clubs ct ON ct.club_id = t.to_club_id
    WHERE t.transfer_date BETWEEN DATE '2021-06-01' AND DATE '2025-05-31'
      AND t.transfer_fee >= 5000000 AND t.market_value_in_eur >= 5000000
      AND cf.league IN {LEAGUES} AND ct.league IN {LEAGUES}
""").fetchall()

# Players aged 26 or under on the transfer date
sample = [r for r in rows if r[4] is not None and r[4] <= 26]


def median(values):
    values = sorted(values)
    n = len(values)
    return values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2


def show(label, group):
    print("{:<62} n = {:>3} | median fee / value = {:.2f}".format(label, len(group), median([r[1] for r in group])))


english_pl = [r for r in sample if r[2] == "England" and r[3] == "GB1"]
show("English player sold by a Premier League club", english_pl)
show("Non-English player sold by a Premier League club", [r for r in sample if r[2] != "England" and r[3] == "GB1"])
show("Player sold by a club in the other four leagues", [r for r in sample if r[3] != "GB1"])
show("Every transfer except English players at Premier League clubs",
     [r for r in sample if not (r[2] == "England" and r[3] == "GB1")])
