# Evaluation on 2025/26 (corrected calculation)

Produced by `src/evaluate_results.py` from the frozen lists in `aman/results/freeze`, after checking every frozen file against the freeze manifest. Players are evaluated at the clubs they played for. No league position is inferred for a United squad that never existed.

## Group summaries

Means and counts are the summaries the evaluation plan named before outcomes were seen. Medians were added afterwards, as an extra description; they were not part of the plan. A player can belong to more than one group (for example a base signing that United also signed), so memberships can exceed distinct players.

| group | measure | memberships | distinct_players | valid_observations | mean | median_added_after_evaluation |
|---|---|---|---|---|---|---|
| base signing | share of main club's league minutes | 6 | 6 | 6 | 0.624 | 0.589 |
| base signing | change in market value, % | 6 | 6 | 6 | -7.717 | -13.35 |
| direct alternative | share of main club's league minutes | 18 | 18 | 16 | 0.556 | 0.516 |
| direct alternative | change in market value, % | 18 | 18 | 18 | 0.794 | -4.55 |
| actual United signing | share of main club's league minutes | 5 | 5 | 4 | 0.705 | 0.75 |
| actual United signing | change in market value, % | 5 | 5 | 5 | 88.7 | 25.0 |
| sold in the base plan | share of main club's league minutes | 3 | 3 | 3 | 0.729 | 0.757 |
| sold in the base plan | change in market value, % | 3 | 3 | 3 | -37.267 | -38.5 |
| all groups | share of main club's league minutes | 32 | 30 | 29 | 0.609 | 0.653 |
| all groups | change in market value, % | 32 | 30 | 32 | 9.366 | -4.55 |

Goals and assists are not averaged across groups, because they mean different things in different roles. They are shown per player below, at the player's main club.

## Players

| group | need | plan | player | main_club | share_of_main_club_league_minutes | season_league_minutes_all_clubs | role_measure | value_change_pct | note |
|---|---|---|---|---|---|---|---|---|---|
| base signing | WB | A | Ritsu Doan | Eintracht Frankfurt | 0.7775 | 2379 | goals+assists per 90 0.38 | -22.7 |  |
| direct alternative | WB | B | Rayan Aït-Nouri | Manchester City | 0.2854 | 976 | goals+assists per 90 0.18 | 14.3 |  |
| direct alternative | WB | C | Bafodé Diakité | AFC Bournemouth | 0.3728 | 1275 | goals+assists per 90 0.0 | 0.0 |  |
| direct alternative | WB | D | Weston McKennie | Juventus FC | 0.8307 | 2841 | goals+assists per 90 0.35 | 25.0 |  |
| base signing | AM | A | Bryan Mbeumo | Manchester United | 0.7675 | 2625 | goals+assists per 90 0.48 | 36.4 |  |
| direct alternative | AM | B | Rafael Leão | AC Milan | 0.5442 | 1861 | goals+assists per 90 0.58 | -33.3 |  |
| direct alternative | AM | C | Matheus Cunha | Manchester United | 0.7319 | 2503 | goals+assists per 90 0.5 | 25.0 |  |
| direct alternative | AM | D | Álex Baena | Atlético de Madrid | 0.4596 | 1572 | goals+assists per 90 0.29 | -20.0 |  |
| base signing | GK | A | Lucas Chevalier | Paris Saint-Germain | 0.5 | 1530 | conceded per start 0.76 | -16.7 |  |
| direct alternative | GK | B | Marcin Bulka |  |  |  |  | -40.0 | no league minutes in the covered leagues in 2025/26 |
| direct alternative | GK | C | Marco Carnesecchi | Atalanta BC | 0.9737 | 3330 | conceded per start 0.95 | 20.0 |  |
| direct alternative | GK | D | Joan García | FC Barcelona | 0.7895 | 2700 | conceded per start 0.7 | 125.0 |  |
| base signing | ST | A | Jonathan David | Juventus FC | 0.5216 | 1784 | goals+assists per 90 0.5 | -33.3 |  |
| direct alternative | ST | B | Jonathan Burkardt | Eintracht Frankfurt | 0.4379 | 1340 | goals+assists per 90 0.94 | -14.3 |  |
| direct alternative | ST | C | Dušan Vlahović | Juventus FC | 0.2836 | 970 | goals+assists per 90 0.74 | -22.2 |  |
| direct alternative | ST | D | Evann Guessand | Aston Villa | 0.1719 | 916 | goals+assists per 90 0.0 | 0.0 | played for 2 clubs; main-club columns use that club only |
| base signing | CM | A | Éderson | Atalanta BC | 0.6535 | 2235 | goals+assists per 90 0.12 | -10.0 |  |
| direct alternative | CM | B | Martín Zubimendi | Arsenal FC | 0.8778 | 3002 | goals+assists per 90 0.18 | 25.0 |  |
| direct alternative | CM | C | Enzo Millot |  |  |  |  | -28.6 | no league minutes in the covered leagues in 2025/26 |
| direct alternative | CM | D | Pablo Barrios | Atlético de Madrid | 0.4871 | 1666 | goals+assists per 90 0.11 | 10.0 |  |
| base signing | CB | A | Piero Hincapié | Arsenal FC | 0.524 | 1882 | conceded per start 1.0 | 0.0 | played for 2 clubs; main-club columns use that club only |
| direct alternative | CB | B | Levi Colwill | Chelsea FC | 0.0658 | 225 | conceded per start 1.5 | -9.1 |  |
| direct alternative | CB | C | Dani Vivian | Athletic Bilbao | 0.7494 | 2563 | conceded per start 1.68 | -50.0 |  |
| direct alternative | CB | D | Edmond Tapsoba | Bayer 04 Leverkusen | 0.8418 | 2576 | conceded per start 1.31 | -12.5 |  |
| sold in the base plan |  |  | Harry Maguire | Manchester United | 0.4839 | 1655 |  | -38.5 |  |
| sold in the base plan |  |  | Casemiro | Manchester United | 0.757 | 2589 |  | -40.0 |  |
| sold in the base plan |  |  | Luke Shaw | Manchester United | 0.9453 | 3233 |  | -33.3 |  |
| actual United signing |  |  | Matheus Cunha | Manchester United | 0.7319 | 2503 |  | 25.0 |  |
| actual United signing |  |  | Diego León |  |  |  |  | 0.0 | no league minutes in the covered leagues in 2025/26 |
| actual United signing |  |  | Bryan Mbeumo | Manchester United | 0.7675 | 2625 |  | 36.4 |  |
| actual United signing |  |  | Benjamin Sesko | Manchester United | 0.4787 | 1637 |  | 15.4 |  |
| actual United signing |  |  | Senne Lammens | Manchester United | 0.8421 | 3240 |  | 366.7 | played for 2 clubs; main-club columns use that club only |

## Players who played for more than one club

Each club's share uses that club's minutes and that club's league matches.

| player | club | league | league_minutes | club_league_matches | club_minutes_share | is_main_club |
|---|---|---|---|---|---|---|
| Evann Guessand | Aston Villa | GB1 | 588 | 38 | 0.1719 | yes |
| Evann Guessand | Crystal Palace | GB1 | 328 | 38 | 0.0959 | no |
| Senne Lammens | Manchester United | GB1 | 2880 | 38 | 0.8421 | yes |
| Senne Lammens | Royal Antwerp FC | BE1 | 360 | 30 | 0.1333 | no |
| Piero Hincapié | Arsenal FC | GB1 | 1792 | 38 | 0.524 | yes |
| Piero Hincapié | Bayer 04 Leverkusen | L1 | 90 | 34 | 0.0294 | no |

## Moves into United's organisation in the window

Every move into Manchester United or its own youth sides dated 2025-06-01 to 2025-09-01 in the transfer records, as reviewed in `docs/actual_united_arrivals_2025.csv`. Only permanent arrivals into the senior squad form the comparison group. The group was fixed from the transfer records, not from later performance.

| name | date | from_club | to_side | classification | in_comparison_group |
|---|---|---|---|---|---|
| Antony | 2025-06-30 | Real Betis | Man Utd | return from loan | no |
| Jadon Sancho | 2025-06-30 | Chelsea | Man Utd | return from loan | no |
| Marcus Rashford | 2025-06-30 | Aston Villa | Man Utd | return from loan | no |
| Tyrell Malacia | 2025-06-30 | PSV | Man Utd | return from loan | no |
| Bendito Mantato | 2025-07-01 | Man Utd U18 | Man Utd U21 | move between United's own sides | no |
| Chido Obi | 2025-07-01 | Man Utd U18 | Man Utd | move between United's own sides | no |
| Ethan Wheatley | 2025-07-01 | Man Utd U21 | Man Utd | move between United's own sides | no |
| Jacob Devaney | 2025-07-01 | Man Utd U18 | Man Utd U21 | move between United's own sides | no |
| James Scanlon | 2025-07-01 | Man Utd U18 | Man Utd U21 | move between United's own sides | no |
| Jaydan Kamason | 2025-07-01 | Man Utd U18 | Man Utd U21 | move between United's own sides | no |
| Matheus Cunha | 2025-07-01 | Wolves | Man Utd | permanent arrival into the senior squad | yes |
| Diego León | 2025-07-05 | Cerro Porteño | Man Utd | permanent arrival into the senior squad | yes |
| Enzo Kana-Biyik | 2025-07-10 | Le Havre U19 | Man Utd U21 | arrival into United's under-21 side | no |
| Bryan Mbeumo | 2025-07-21 | Brentford | Man Utd | permanent arrival into the senior squad | yes |
| Benjamin Sesko | 2025-08-09 | Leipzig | Man Utd | permanent arrival into the senior squad | yes |
| Senne Lammens | 2025-09-01 | Royal Antwerp | Man Utd | permanent arrival into the senior squad | yes |
