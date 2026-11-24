# Data dictionary

Last updated 18 November 2026. Describes the files as the code writes them now.

Money is in GBP million for fees, receipts and values, and GBP million per year for wages. A weekly wage in pounds converts as `weekly_wage * 52 / 1_000_000`. Euro values are converted at 0.8412 GBP per EUR, the ECB reference rate on 30 May 2025. Seasons are named by their starting year: 2023 means 2023/24 and 2024 means 2024/25.

Each column is one of: an **observation** from the dated source records, a **calculation** from observations, an **estimate** (fees, receipts, United wages from a later table, candidate wage bands), or a **policy assumption** (limits, weights, mark-ups). The assumptions themselves are listed in `assumptions.md`.

## 1. Decision-time tables (`data/processed/`, written by `src/prepare_inputs.py`)

Built only from records dated on or before 31 May 2025. League means the domestic first-tier league.

### `players_at_cutoff.csv`: one row per player with league minutes in 2024/25 in the 14 covered leagues

| Column | Meaning | Kind |
|---|---|---|
| `player_id`, `name` | Source id and name | Observation |
| `date_of_birth`, `age_at_cutoff` | Birth date; completed years on 31 May 2025 | Observation, calculation |
| `main_position`, `main_role` | The source's stored main position and the role it maps to. **Not dated**: it is the current label, used only as a fallback for role eligibility | Observation, undated |
| `foot`, `height_in_cm`, `country_of_citizenship` | Stored profile fields; not dated. Citizenship is used for the English mark-up | Observation, undated |
| `club_id`, `club_name`, `league` | Club and league of the last league appearance in 2024/25. A player on loan is shown at the loan club | Calculation |
| `last_league_appearance` | Date of that appearance | Observation |
| `value_eur`, `value_date`, `value_gbp_m` | Latest market valuation on or before the cutoff, its date, and the value in GBP million | Estimate by the source |
| `joined_club_date` | Start of the current spell in the club's organisation, found from the dated transfer records (see Section 2). Empty if the records do not show it | Calculation |
| `joined_basis` | How the start was found: signed for a fee; arrived without a recorded fee; joined the club's youth or reserve side from another club; came through the club's youth system with entry not on record; at the club before a loan with joining not on record; or no move into the club on record | Calculation |
| `in_club_by_date`, `in_club_by_evidence` | Only when `joined_club_date` is empty: the earliest dated record placing the player in the club's organisation (a move between the club's own sides, a move out of the club, or a first match for the club) | Calculation |
| `first_club_appearance` | First match for the club's organisation in the source | Observation |
| `history_flag` | Set if moves on one day could not be put in a single chain for this club | Calculation |

### `player_seasons.csv`: one row per player and season

| Column | Meaning |
|---|---|
| `player_id`, `season` | Key |
| `league`, `club_id`, `club_name` | League and club where the player had most league minutes that season (ties go to the smaller club id) |
| `clubs_in_season` | Number of clubs with league minutes; the counts below are added across them |
| `minutes`, `appearances`, `starts` | League minutes, appearances and starts, all clubs |
| `goals`, `assists`, `yellow_cards`, `red_cards` | League totals, all clubs; goals include penalties |
| `club_matches` | League matches played by the main club up to the cutoff |
| `minutes_share` | `minutes / (90 * club_matches)`. **A proxy**: for a player at two clubs the numerator covers both clubs and the denominator only the main club, so it can exceed 1. This is the playing-time input of the frozen quality score and has not been changed |
| `club_points_per_game` | League points per match of the main club |
| `team_goals_for_in_starts`, `team_goals_against_in_starts` | Goals the player's team scored and conceded in the league matches the player started |

### `player_role_starts.csv`: one row per player and role started

| Column | Meaning |
|---|---|
| `player_id`, `role` | Key |
| `starts_2023`, `starts_2024`, `starts_total` | Starts in that role, all competitions in the source |

Lineup positions map to roles: Goalkeeper → GK; Centre-Back, Sweeper → CB; Left-Back, Right-Back → WB; Defensive Midfield, Central Midfield → CM; Attacking Midfield, Left Winger, Right Winger, Second Striker → AM; Centre-Forward → ST. **Left Midfield and Right Midfield depend on the team's formation in that match:** they count as WB when the formation starts with three or five defenders (for example 3-4-2-1 or 5-4-1) and as AM otherwise (for example 4-4-2). Generic labels (Attack, Midfield, Defender) are not counted.

### `club_seasons.csv`: one row per club, league and season

`club_id`, `club_name`, `league`, `season`, `matches`, `points`, `goals_for`, `goals_against`, up to the cutoff.

### `club_family.csv`: one row per youth or reserve side linked to a senior club

| Column | Meaning |
|---|---|
| `member_club_id`, `member_names` | The side's id and every name it is recorded under |
| `senior_club_id`, `senior_names` | The senior club it belongs to |
| `basis` | Either "name '…' is one of the senior club's names with a youth ending", or "entered by hand after review" |

A side whose name would fit two senior clubs is listed with an empty `senior_club_id` and is not linked. There were none.

## 2. How the start of a spell is found

Clubs are identified by id. A club organisation is the senior club plus the sides in `club_family.csv`. A side is linked if one of its names is exactly one of the senior club's recorded names followed by a youth or reserve ending (U17, U19, II, B, Youth, Castilla and similar), or if `docs/club_aliases.csv` lists it. Names are never matched by a shared prefix or substring, so Real Unión is not part of Real Sociedad.

The player's moves are sorted by date, and moves on the same day are put in the chain they form. The latest move into the organisation from outside is then traced back:
- through loan returns, to the move before the loan;
- through a loan made permanent within 62 days, to the start of the loan.

What remains is the start of the current spell. A move up from the club's own youth side is not a new arrival. A signing from another club's youth side is an ordinary signing. The two-year rule then reads:

| Situation | Status |
|---|---|
| Documented date in `joining_date_overrides.csv` | Eligible if before 1 June 2023 |
| Same-day moves that could not be ordered | Not verified |
| `joined_club_date` known | Eligible if before 1 June 2023, otherwise joined within two years |
| No start date, but `in_club_by_date` before 1 June 2023 | Eligible |
| Otherwise | Not verified, treated as not eligible |

## 3. Pool and score tables (`data/processed/`)

### `pool_players.csv` (from `src/build_player_pool.py`): one row per player in the scoring reference

24 existing players (`status` E) and 806 candidates (`status` C). Every candidate that passes the league, age, minutes and valuation filters is kept here, whatever the two-year rule says, so that every run scores players against the same group. The rule is applied when a run is built.

| Column | Meaning |
|---|---|
| `player_id`, `name`, `status`, `date_of_birth`, `age_at_cutoff`, `club_name`, `country`, `league` | Identity and club at the cutoff |
| `value_gbp_m`, `value_date` | Dated market value |
| `minutes_2024`, `minutes_share_2024`, `club_rank_2024` | League minutes in 2024/25, the playing-time proxy above, and the club's league position by points per match |
| `joined_club_date` | As in `players_at_cutoff.csv` |
| `two_year_status`, `two_year_evidence` | Eligible, joined within two years, or not verified, with the evidence used. Empty for existing players |
| `homegrown`, `senior_reg` | Registration flags (0/1). Candidates are counted as not home-grown unless checked |
| `roles` | Eligible roles |

### `pool_roles.csv`: one row per eligible player-role pair

`player_id`, `role`, `starts_total`, `basis` (`starts` when the five-start rule is met, `main position` when the stored position was used instead).

### `excluded_candidates.csv`

Big-five players aged 26 or under who fail the minutes, valuation or role filter, with the reason.

### `scores.csv` (from `src/score_players.py`): one row per eligible player-role pair

| Column | Meaning |
|---|---|
| `pct_playing_time`, `pct_output`, `pct_team_level`, `pct_value` | Percentile of each component among the players eligible for the role, 0 to 100 |
| `small_sample` | 1 if the output component was set to 50 because of too few minutes or starts |
| `quality` | The weighted average of the four percentiles; the quality proxy used in the base case |
| `quality_no_value` | The same without the market-value component |

## 4. Hand-entered tables (`docs/` and `data/manual/`)

| File | Contents |
|---|---|
| `docs/roster_reconciliation.csv` | United's players at the cutoff with their status and dated evidence |
| `docs/club_aliases.csv` | Reviewed short names of clubs' own youth sides (kind `short name`) and sides with no youth ending (kind `side`), each with a reason |
| `docs/joining_date_overrides.csv` | Joining dates the records cannot settle, with a source |
| `docs/unavailable_candidates.csv` | Candidates blocked by dated evidence or team ruling |
| `docs/free_agents.csv` | Candidates documented as leaving without a fee |
| `docs/likelihood_notes.csv` | Likelihood labels set by hand from dated reports |
| `docs/shortlist_checks.csv` | Findings used in the shortlist table at the freeze (unchanged since) |
| `docs/actual_united_arrivals_2025.csv` | Evaluation only: every move into United's organisation from 1 June to 1 September 2025, classified, with the comparison group marked |
| `data/manual/united_wages.csv` | United wages read from the 2025/26 payroll table (an approximation of wages at the cutoff) |
| `data/manual/united_wages_hand_entered.csv` | Wages entered by hand for players missing from that table |

## 5. Model inputs

`src/model_inputs.py` builds the dictionaries the model reads from the tables above: sets E and C, eligible pairs H, quality q, fees f, receipts r, wages w and the registration flags. The small invented cases in `data/toy/` use the same layout as files (`players.csv`, `roles.csv`); the real inputs are built in memory and are not written as separate files. Each run's settings are saved with its results.

## 6. Run outputs (folder named with `--out`)

| File | Contents |
|---|---|
| `<run>/squad.csv` | Every kept, bought or sold player: role, starter flag, quality in role, wage, fee or receipt |
| `<run>/summary.csv` | Solver status, gap, bound, runtime, model size, objective and its parts, spending, wages, counts |
| `<run>/settings.json` | Complete settings and limits of the run |
| `runs_summary.csv` | One line per run, including `objective_on_base_scale` (the run's transfers re-scored with the base score and weights) and the overlap with the base plan |
| `direct_alternatives.csv` | Plans A to D per signing: role, whether the player starts, quality, fee, wage, likelihood label and reason, objective and change from base |
| `full_plan_alternatives.csv` | Re-decided plans when a signing or sale is blocked, with the changes listed |
| `shortlist_review.csv` | Ownership, commitment, contract and registration fields for every shortlisted player |
| `run_manifest.json` | Code commit, whether code or inputs were uncommitted, output folder, command, package versions, input hashes, and status, gap, bound and runtime of every run |
| `RESULTS.md` | The main tables in readable form |

## 7. Evaluation outputs (folder named with `--out`)

| File | Contents |
|---|---|
| `player_outcomes.csv` | One row per group membership (`group`, `need`, `plan`, `player_id`). Main-club columns use only the club with the most league minutes (then most starts, then smaller club id): `main_club`, `main_club_league_minutes`, `main_club_league_matches`, `share_of_main_club_league_minutes`, starts, goals, assists, goals plus assists per 90, team goals conceded per start. Season totals across clubs are in `season_league_minutes_all_clubs`, `season_goals_all_clubs`, `season_assists_all_clubs`. Market value at the cutoff and latest on or before 12 June 2026. A missing outcome is left blank with a note, not set to zero |
| `player_club_outcomes.csv` | One row per player and club: minutes, that club's league matches, `club_minutes_share` (that club's minutes over 90 × that club's matches), starts, goals, assists, conceded in starts, main-club flag |
| `group_summary.csv` | Per group and measure: memberships, distinct players, valid observations, mean (as planned at the freeze) and median (added after the evaluation) |
| `EVALUATION.md` | The same in readable form, with the reviewed list of moves into United |

The original evaluation of 17 November 2026 in `results/evaluation/` used an earlier layout (`minutes_share` over all clubs against one club's matches) and is kept unchanged as a record.
