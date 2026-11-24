"""Build decision-time player tables from the raw Transfermarkt files.

Every dated table is cut at the information cutoff when it is read, so no
match, valuation or transfer after 31 May 2025 can enter the outputs.
The current-snapshot fields in the raw players table (current club, current
market value, contract end) are not used.

Inputs (not committed):  data/raw/transfermarkt/*.csv.gz
Outputs (small tables):  data/processed/

Run from the repository root:
    python src/prepare_inputs.py
"""

import csv
import os

import duckdb

from club_spells import club_families, order_moves, current_spell, in_club_by

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw", "transfermarkt")
OUT = os.path.join(HERE, "..", "data", "processed")
DOCS = os.path.join(HERE, "..", "docs")

CUTOFF = "2025-05-31"          # last day of permitted information
SEASONS = (2023, 2024)         # 2023/24 and 2024/25, named by starting year
EUR_TO_GBP = 0.8412            # ECB reference rate on 30 May 2025, GBP per EUR
MAN_UNITED = 985               # club id in the source data

# European first-tier leagues that have match-level player data in both seasons
LEAGUES = ["GB1", "ES1", "IT1", "L1", "FR1", "NL1", "PO1", "BE1",
           "TR1", "RU1", "UKR1", "GR1", "SC1", "DK1"]

# Position labels used in match lineups, mapped to the six roles of a 3-4-2-1.
# Full-backs count as wing-backs; wingers and second strikers are the two
# places behind the striker. The wide-midfield labels are handled separately
# below, because their meaning depends on the team's shape.
ROLE_OF_POSITION = {
    "Goalkeeper": "GK",
    "Centre-Back": "CB", "Sweeper": "CB",
    "Left-Back": "WB", "Right-Back": "WB",
    "Defensive Midfield": "CM", "Central Midfield": "CM",
    "Attacking Midfield": "AM", "Left Winger": "AM", "Right Winger": "AM", "Second Striker": "AM",
    "Centre-Forward": "ST",
}


def raw(table):
    """SQL fragment that reads one raw file."""
    path = os.path.join(RAW, table + ".csv.gz").replace("'", "''")
    return "read_csv_auto('" + path + "')"


os.makedirs(OUT, exist_ok=True)
con = duckdb.connect()

#########Decision-time views############

# Only rows dated on or before the cutoff are visible from here on
con.execute("CREATE VIEW games AS SELECT * FROM " + raw("games") + " WHERE date <= DATE '" + CUTOFF + "'")
con.execute("CREATE VIEW appearances AS SELECT * FROM " + raw("appearances") + " WHERE date <= DATE '" + CUTOFF + "'")
con.execute("CREATE VIEW lineups AS SELECT * FROM " + raw("game_lineups") + " WHERE date <= DATE '" + CUTOFF + "'")
con.execute("CREATE VIEW valuations AS SELECT * FROM " + raw("player_valuations") + " WHERE date <= DATE '" + CUTOFF + "'")
con.execute("CREATE VIEW transfers AS SELECT * FROM " + raw("transfers") + " WHERE transfer_date <= DATE '" + CUTOFF + "'")

# Undated reference tables: only stable fields are taken from them
con.execute("CREATE VIEW players AS SELECT player_id, name, CAST(date_of_birth AS DATE) AS date_of_birth, "
            "sub_position, foot, height_in_cm, country_of_citizenship FROM " + raw("players"))
con.execute("CREATE VIEW clubs AS SELECT club_id, name FROM " + raw("clubs"))

con.execute("CREATE TABLE role_map (position VARCHAR, role VARCHAR)")
con.executemany("INSERT INTO role_map VALUES (?, ?)", list(ROLE_OF_POSITION.items()))

league_list = ", ".join("'" + code + "'" for code in LEAGUES)
season_list = ", ".join(str(year) for year in SEASONS)

# League matches of the two seasons, one row per club and match
con.execute("""
CREATE TABLE club_matches AS
SELECT game_id, season, competition_id AS league, date, home_club_id AS club_id,
       home_club_goals AS goals_for, away_club_goals AS goals_against
FROM games WHERE competition_id IN (""" + league_list + """) AND season IN (""" + season_list + """)
UNION ALL
SELECT game_id, season, competition_id AS league, date, away_club_id AS club_id,
       away_club_goals AS goals_for, home_club_goals AS goals_against
FROM games WHERE competition_id IN (""" + league_list + """) AND season IN (""" + season_list + """)
""")

#########Table 1: club results by season############

# Points per game is a simple measure of how strong a club was within its league
con.execute("""
CREATE TABLE club_seasons AS
SELECT m.club_id, c.name AS club_name, m.league, m.season,
       count(*) AS matches,
       sum(CASE WHEN goals_for > goals_against THEN 3 WHEN goals_for = goals_against THEN 1 ELSE 0 END) AS points,
       sum(goals_for) AS goals_for, sum(goals_against) AS goals_against
FROM club_matches m LEFT JOIN clubs c USING (club_id)
GROUP BY 1, 2, 3, 4
ORDER BY 3, 4, 1
""")

#########Table 2: player league statistics by season############

# Minutes, goals and assists in league matches, by player, season and club
con.execute("""
CREATE TABLE player_club_seasons AS
SELECT a.player_id, m.season, m.league, a.player_club_id AS club_id,
       sum(a.minutes_played) AS minutes, count(*) AS appearances,
       sum(a.goals) AS goals, sum(a.assists) AS assists,
       sum(a.yellow_cards) AS yellow_cards, sum(a.red_cards) AS red_cards,
       max(a.date) AS last_appearance
FROM appearances a
JOIN club_matches m ON m.game_id = a.game_id AND m.club_id = a.player_club_id
GROUP BY 1, 2, 3, 4
""")

# League starts, with the goals the team scored and conceded in those matches
con.execute("""
CREATE TABLE player_starts AS
SELECT l.player_id, m.season, count(*) AS starts,
       sum(m.goals_for) AS team_goals_for_in_starts,
       sum(m.goals_against) AS team_goals_against_in_starts
FROM lineups l
JOIN club_matches m ON m.game_id = l.game_id AND m.club_id = l.club_id
WHERE l.type = 'starting_lineup'
GROUP BY 1, 2
""")

# One row per player and season. A player who changed club mid-season has the
# minutes of both clubs added; the club with more minutes is shown as the main club.
con.execute("""
CREATE TABLE player_seasons AS
WITH totals AS (
    SELECT player_id, season,
           -- Main club: most minutes; a tie goes to the smaller club id
           first(club_id ORDER BY minutes DESC, club_id) AS main_club_id,
           first(league ORDER BY minutes DESC, club_id) AS main_league,
           count(*) AS clubs_in_season,
           sum(minutes) AS minutes, sum(appearances) AS appearances,
           sum(goals) AS goals, sum(assists) AS assists,
           sum(yellow_cards) AS yellow_cards, sum(red_cards) AS red_cards
    FROM player_club_seasons GROUP BY 1, 2)
SELECT t.player_id, t.season, t.main_league AS league, t.main_club_id AS club_id, cs.club_name,
       t.clubs_in_season, t.minutes, t.appearances, coalesce(s.starts, 0) AS starts,
       t.goals, t.assists, t.yellow_cards, t.red_cards,
       cs.matches AS club_matches,
       round(t.minutes / (90.0 * cs.matches), 4) AS minutes_share,
       round(cs.points * 1.0 / cs.matches, 4) AS club_points_per_game,
       s.team_goals_for_in_starts, s.team_goals_against_in_starts
FROM totals t
LEFT JOIN player_starts s USING (player_id, season)
LEFT JOIN club_seasons cs ON cs.club_id = t.main_club_id AND cs.season = t.season AND cs.league = t.main_league
ORDER BY t.player_id, t.season
""")

#########Table 3: positions actually started############

# Number of starts in each role, all competitions in the source, both seasons.
# This is the evidence for which roles a player may be given in the model.
#
# A starter labelled Left or Right Midfield is a wing-back when the team lines
# up with three or five at the back (for example 3-4-2-1 or 5-4-1). In a
# back-four shape such as 4-4-2 the same label is a wide attacking player,
# so it counts towards AM instead.
con.execute("""
CREATE TABLE player_role_starts AS
WITH starts AS (
    SELECT l.player_id, g.season, l.position,
           CASE WHEN l.club_id = g.home_club_id THEN g.home_club_formation
                ELSE g.away_club_formation END AS formation
    FROM lineups l
    JOIN games g USING (game_id)
    WHERE l.type = 'starting_lineup' AND g.season IN (""" + season_list + """)
      AND l.player_id IN (SELECT player_id FROM player_seasons)),
with_role AS (
    SELECT s.player_id, s.season,
           CASE WHEN s.position IN ('Left Midfield', 'Right Midfield') THEN
                    CASE WHEN s.formation LIKE '3-%' OR s.formation LIKE '5-%' THEN 'WB' ELSE 'AM' END
                ELSE r.role END AS role
    FROM starts s LEFT JOIN role_map r ON r.position = s.position)
SELECT player_id, role,
       sum(CASE WHEN season = 2023 THEN 1 ELSE 0 END) AS starts_2023,
       sum(CASE WHEN season = 2024 THEN 1 ELSE 0 END) AS starts_2024,
       count(*) AS starts_total
FROM with_role
WHERE role IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2
""")

#########Table 4: one row per player at the cutoff############

# Club at the cutoff = club of the last league appearance in 2024/25.
# Value = latest valuation dated on or before the cutoff, converted to GBP million.
# Age is counted in completed years on the cutoff date.
con.execute("""
CREATE TABLE players_at_cutoff AS
WITH last_club AS (
    SELECT player_id, first(club_id ORDER BY last_appearance DESC, club_id) AS club_id,
           first(league ORDER BY last_appearance DESC, club_id) AS league, max(last_appearance) AS last_league_appearance
    FROM player_club_seasons WHERE season = 2024 GROUP BY 1),
value AS (
    SELECT player_id, first(market_value_in_eur ORDER BY date DESC, market_value_in_eur DESC) AS value_eur,
           max(date) AS value_date
    FROM valuations GROUP BY 1)
SELECT p.player_id, p.name, p.date_of_birth,
       date_part('year', age(DATE '""" + CUTOFF + """', p.date_of_birth)) AS age_at_cutoff,
       p.sub_position AS main_position, r.role AS main_role,
       p.foot, p.height_in_cm, p.country_of_citizenship,
       lc.club_id, c.name AS club_name, lc.league, lc.last_league_appearance,
       v.value_eur, v.value_date,
       round(v.value_eur * """ + str(EUR_TO_GBP) + """ / 1000000.0, 3) AS value_gbp_m
FROM last_club lc
JOIN players p USING (player_id)
LEFT JOIN (SELECT * FROM role_map UNION ALL
           SELECT * FROM (VALUES ('Left Midfield', 'WB'), ('Right Midfield', 'WB'))) r ON r.position = p.sub_position
LEFT JOIN clubs c ON c.club_id = lc.club_id
LEFT JOIN value v USING (player_id)
ORDER BY p.player_id
""")

#########Start of each player's current spell at the club############

# All dated moves of the players in the table. Same-day moves are put in order later.
moves_of = {}
rows = con.execute("""
    SELECT t.player_id, t.transfer_date, t.from_club_id, t.from_club_name, t.to_club_id, t.to_club_name, t.transfer_fee
    FROM transfers t WHERE t.player_id IN (SELECT player_id FROM players_at_cutoff)
    ORDER BY t.player_id, t.transfer_date, t.from_club_id, t.to_club_id""").fetchall()
for (player_id, date, from_id, from_name, to_id, to_name, fee) in rows:
    moves_of.setdefault(player_id, []).append(
        {"date": str(date), "from_id": from_id, "from_name": from_name, "to_id": to_id, "to_name": to_name, "fee": fee})

# Every name each club is recorded under, in the transfer records and the club table
names_of = {}
for (club_id, name) in con.execute("""
        SELECT from_club_id, from_club_name FROM transfers UNION SELECT to_club_id, to_club_name FROM transfers
        UNION SELECT club_id, name FROM clubs ORDER BY 1, 2""").fetchall():
    if club_id is not None and name is not None:
        names_of.setdefault(club_id, []).append(name)

# Short names and sides entered by hand after review (docs/club_aliases.csv)
extra_aliases = {}
extra_sides = {}
with open(os.path.join(DOCS, "club_aliases.csv"), newline="") as file:
    for row in csv.DictReader(file):
        if row["kind"] == "short name":
            extra_aliases.setdefault(int(row["senior_club_id"]), []).append(row["value"])
        elif row["kind"] == "side":
            extra_sides[int(row["value"])] = int(row["senior_club_id"])
        else:
            raise ValueError("Unknown kind in club_aliases.csv: " + row["kind"])

# Youth and reserve sides of each club a player is at on the cutoff
senior_ids = set(row[0] for row in con.execute("SELECT DISTINCT club_id FROM players_at_cutoff").fetchall())
family_rows, ambiguous = club_families(names_of, senior_ids, extra_aliases, extra_sides)
family = {club: {club} for club in senior_ids}
for (member, senior, basis) in family_rows:
    family[senior].add(member)
with open(os.path.join(OUT, "club_family.csv"), "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["member_club_id", "member_names", "senior_club_id", "senior_names", "basis"])
    for (member, senior, basis) in family_rows:
        writer.writerow([member, " | ".join(names_of[member]), senior, " | ".join(names_of[senior]), basis])
    for (member, owners) in ambiguous:
        writer.writerow([member, " | ".join(names_of[member]), "", " | ".join(str(o) for o in owners),
                         "not assigned: the name fits more than one senior club"])

# First match for the club organisation, as dated evidence of being there
con.execute("CREATE TABLE family_ids (senior_club_id BIGINT, club_id BIGINT)")
con.executemany("INSERT INTO family_ids VALUES (?, ?)", [(s, c) for s in family for c in sorted(family[s])])
first_match = dict(con.execute("""
    SELECT p.player_id, CAST(min(a.date) AS VARCHAR)
    FROM players_at_cutoff p
    JOIN family_ids f ON f.senior_club_id = p.club_id
    JOIN appearances a ON a.player_id = p.player_id AND a.player_club_id = f.club_id
    GROUP BY 1""").fetchall())

con.execute("""CREATE TABLE spells (player_id BIGINT, joined_club_date VARCHAR, joined_basis VARCHAR,
               in_club_by_date VARCHAR, in_club_by_evidence VARCHAR, first_club_appearance VARCHAR, history_flag VARCHAR)""")
spell_rows = []
for (player_id, club_id) in con.execute("SELECT player_id, club_id FROM players_at_cutoff ORDER BY player_id").fetchall():
    moves, ambiguous_dates = order_moves(moves_of.get(player_id, []))
    ids = family[club_id]
    start, basis = current_spell(moves, ids, club_id)
    # Dated evidence of being in the club is needed only when the start of the spell is not on record
    by_date, evidence = (None, "") if start else in_club_by(moves, ids, first_match.get(player_id))
    # Flag a day whose moves could not be put in order if it involves this club
    flag = ""
    for date in ambiguous_dates:
        if any(m["date"] == date and (m["from_id"] in ids or m["to_id"] in ids) for m in moves):
            flag = "same-day moves on " + date + " could not be put in order"
    spell_rows.append((player_id, start, basis, by_date, evidence, first_match.get(player_id), flag))
con.executemany("INSERT INTO spells VALUES (?, ?, ?, ?, ?, ?, ?)", spell_rows)

con.execute("""
CREATE TABLE players_out AS
SELECT p.*, s.joined_club_date, s.joined_basis, s.in_club_by_date, s.in_club_by_evidence,
       s.first_club_appearance, s.history_flag
FROM players_at_cutoff p LEFT JOIN spells s USING (player_id)
ORDER BY p.player_id""")
con.execute("DROP TABLE players_at_cutoff")
con.execute("ALTER TABLE players_out RENAME TO players_at_cutoff")
print("Club organisations:", len(family), "| youth and reserve sides assigned:", len(family_rows),
      "| not assigned because ambiguous:", len(ambiguous))

#########Save and summarise############

for table in ["club_seasons", "player_seasons", "player_role_starts", "players_at_cutoff"]:
    path = os.path.join(OUT, table + ".csv")
    con.execute("COPY " + table + " TO '" + path.replace("'", "''") + "' (HEADER, DELIMITER ',')")
    rows = con.execute("SELECT count(*) FROM " + table).fetchone()[0]
    print("Wrote", table + ".csv", "with", rows, "rows")

# Confirm that nothing after the cutoff was read
for table in ["games", "appearances", "lineups", "valuations"]:
    latest = con.execute("SELECT max(date) FROM " + table).fetchone()[0]
    print("Latest date used from", table + ":", latest)
    if str(latest) > CUTOFF:
        raise ValueError("A row after the cutoff was read from " + table)
