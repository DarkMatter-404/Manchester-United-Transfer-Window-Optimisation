# Results of the last run

**Post-freeze correction run.** These results were produced after the 2025/26 outcomes had been examined, to correct errors found in review. They are not a recommendation frozen before outcomes were seen; the frozen recommendation is in `aman/results/freeze/`.

Written by `src/run_scenarios.py`. Money is in GBP million, wages per year.

`objective` is on each run's own scale. `objective_on_base_scale` re-scores the same purchases and sales with the base quality score and base weights, so that column can be compared across all runs.

## Budget and quality

| budget | objective | net_spend | wages | arrivals | sales | bought | sold |
|---|---|---|---|---|---|---|---|
| no transfers | 876.47 | 0 | 133.38 | 0 | 0 |  |  |
| 0 | 1050.86 | -2.1 | 143.52 | 6 | 4 | Jonathan Burkardt (AM); Ritsu Doan (WB); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Alexsandro (CB) | Lisandro Martínez; Mason Mount; Rasmus Højlund; Leny Yoro |
| 50 | 1069.15 | 49.38 | 140.66 | 6 | 3 | Ritsu Doan (WB); Lucas Chevalier (GK); Bafodé Diakité (CB); Paul Nebel (AM); Jonathan David (ST); Alexsandro (CB) | Casemiro; Leny Yoro; Tyler Fredricson |
| 100 | 1086.56 | 95.9 | 146.9 | 6 | 3 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Alexsandro (CB) | Casemiro; Lisandro Martínez; Tyler Fredricson |
| 150 | 1096.02 | 143.68 | 147.94 | 6 | 3 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Dani Vivian (CB); Jonathan David (ST); Alexsandro (CB) | Harry Maguire; Casemiro; Tyler Fredricson |
| 200 | 1100.96 | 198.69 | 147.94 | 6 | 3 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw |
| 250 | 1100.96 | 198.69 | 147.94 | 6 | 3 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw |
| 300 | 1100.96 | 198.69 | 147.94 | 6 | 3 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw |

## All runs

| run | group | status | checks_passed | objective | objective_on_base_scale | signings_shared_with_base | bought | sold | net_spend | wages |
|---|---|---|---|---|---|---|---|---|---|---|
| no_transfers | comparison | OPTIMAL | yes | 876.47 | 876.47 | 0 |  |  | 0 | 133.38 |
| base | base | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 198.69 | 147.94 |
| sensitivity/budget_0 | budget | OPTIMAL | yes | 1050.86 | 1050.86 | 3 | Jonathan Burkardt (AM); Ritsu Doan (WB); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Alexsandro (CB) | Lisandro Martínez; Mason Mount; Rasmus Højlund; Leny Yoro | -2.1 | 143.52 |
| sensitivity/budget_50 | budget | OPTIMAL | yes | 1069.15 | 1069.15 | 3 | Ritsu Doan (WB); Lucas Chevalier (GK); Bafodé Diakité (CB); Paul Nebel (AM); Jonathan David (ST); Alexsandro (CB) | Casemiro; Leny Yoro; Tyler Fredricson | 49.38 | 140.66 |
| sensitivity/budget_100 | budget | OPTIMAL | yes | 1086.56 | 1086.56 | 4 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Alexsandro (CB) | Casemiro; Lisandro Martínez; Tyler Fredricson | 95.9 | 146.9 |
| sensitivity/budget_150 | budget | OPTIMAL | yes | 1096.02 | 1096.02 | 4 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Dani Vivian (CB); Jonathan David (ST); Alexsandro (CB) | Harry Maguire; Casemiro; Tyler Fredricson | 143.68 | 147.94 |
| sensitivity/budget_200 | budget | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 198.69 | 147.94 |
| sensitivity/budget_300 | budget | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 198.69 | 147.94 |
| sensitivity/fee_only_0.9 | fee only | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 180.69 | 147.94 |
| sensitivity/fee_only_1.5 | fee only | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 234.69 | 147.94 |
| sensitivity/combined_fee_and_wage_0.9 | combined fee and wage | OPTIMAL | yes | 1107.81 | 1107.81 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Levi Colwill (CB); Piero Hincapié (CB) | Harry Maguire; Casemiro; Tyler Fredricson | 193.81 | 147.94 |
| sensitivity/combined_fee_and_wage_1.5 | combined fee and wage | OPTIMAL | yes | 1093.46 | 1093.46 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Éderson (CM) | Harry Maguire; Casemiro; Luke Shaw | 203.15 | 147.94 |
| sensitivity/candidate_wages_minus_10 | candidate wages | OPTIMAL | yes | 1103.93 | 1103.93 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Éderson (CM) | Harry Maguire; Casemiro | 167.82 | 146.48 |
| sensitivity/candidate_wages_plus_10 | candidate wages | OPTIMAL | yes | 1093.46 | 1093.46 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Éderson (CM) | Harry Maguire; Casemiro; Luke Shaw | 158.73 | 147.84 |
| sensitivity/sale_receipt_0.7 | sale receipt | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 204.58 | 147.94 |
| sensitivity/sale_receipt_1.0 | sale receipt | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 195.75 | 147.94 |
| sensitivity/wage_allowance_no_growth | wage allowance | OPTIMAL | yes | 1075.98 | 1075.98 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Piero Hincapié (CB) | Matthijs de Ligt; Harry Maguire; Casemiro; Luke Shaw | 129.96 | 133.12 |
| sensitivity/wage_allowance_removed | wage allowance | OPTIMAL | yes | 1129.44 | 1129.44 | 5 | Rafael Leão (AM); Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Piero Hincapié (CB) | Tyler Fredricson | 229.23 | 182.52 |
| sensitivity/fee_ceiling_100 | fee ceiling | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 198.69 | 147.94 |
| sensitivity/arrivals_4 | arrivals limit | OPTIMAL | yes | 1041.92 | 1041.92 | 4 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST) | Casemiro | 91.44 | 144.82 |
| sensitivity/arrivals_5 | arrivals limit | OPTIMAL | yes | 1072.25 | 1072.25 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Piero Hincapié (CB) | Harry Maguire; Casemiro | 144.69 | 145.34 |
| sensitivity/depth_weight_0.2 | depth weight | OPTIMAL | yes | 1027.69 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 198.69 | 147.94 |
| sensitivity/depth_weight_0.4 | depth weight | OPTIMAL | yes | 1174.23 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 198.69 | 147.94 |
| sensitivity/quality_without_value | scoring | OPTIMAL | yes | 1040.5 | 1068.81 | 3 | Mahdi Camara (CM); Luca Ranieri (CB); Ritsu Doan (WB); Bryan Mbeumo (AM); Jonathan David (ST); Alexsandro (CB) | Casemiro; Ayden Heaven; Tyler Fredricson | 91.86 | 146.64 |
| sensitivity/weakness_weights | role weights | OPTIMAL | yes | 1205.85 | 1099.33 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Levi Colwill (CB); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 205.0 | 147.94 |
| sensitivity/cunha_fixed | commitment | OPTIMAL | yes | 1096.65 | 1096.65 | 5 | Ritsu Doan (WB); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 210.3 | 147.94 |
| sensitivity/united_wages_by_bands | United wage estimate | OPTIMAL | yes | 1080.48 | 1080.48 | 4 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Alexsandro (CB) | Lisandro Martínez; Leny Yoro; Tyler Fredricson | 61.83 | 147.94 |
| sensitivity/rivals_like_other_clubs | club rules | OPTIMAL | yes | 1100.96 | 1100.96 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 198.69 | 147.94 |
| sensitivity/without_two_year_rule | two-year rule | OPTIMAL | yes | 1112.74 | 1112.74 | 3 | Christian Pulisic (AM); Ritsu Doan (WB); Evan Ndicka (CB); Tijjani Reijnders (CM); Lucas Chevalier (GK); Jonathan David (ST) | Harry Maguire; Casemiro | 146.37 | 145.86 |
| full_plans/without_Ritsu_Doan | full plan: signing blocked | OPTIMAL | yes | 1097.51 | 1097.51 | 5 | Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Rayan Aït-Nouri (WB); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 210.72 | 147.94 |
| full_plans/without_Bryan_Mbeumo | full plan: signing blocked | OPTIMAL | yes | 1100.2 | 1100.2 | 5 | Rafael Leão (AM); Ritsu Doan (WB); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 217.2 | 147.94 |
| full_plans/without_Lucas_Chevalier | full plan: signing blocked | OPTIMAL | yes | 1095.67 | 1095.67 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Marcin Bulka (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 196.17 | 147.94 |
| full_plans/without_Jonathan_David | full plan: signing blocked | OPTIMAL | yes | 1093.08 | 1093.08 | 5 | Ritsu Doan (WB); Bryan Mbeumo (ST); Lucas Chevalier (GK); Álex Baena (AM); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 244.96 | 147.94 |
| full_plans/without_Éderson | full plan: signing blocked | OPTIMAL | yes | 1099.33 | 1099.33 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Levi Colwill (CB); Piero Hincapié (CB) | Harry Maguire; Casemiro; Luke Shaw | 205.0 | 147.94 |
| full_plans/without_Piero_Hincapié | full plan: signing blocked | OPTIMAL | yes | 1100.47 | 1100.47 | 5 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Levi Colwill (CB) | Harry Maguire; Casemiro; Luke Shaw | 205.0 | 147.94 |
| full_plans/cannot_sell_Harry_Maguire | full plan: sale blocked | OPTIMAL | yes | 1093.82 | 1093.82 | 4 | Jonathan Burkardt (AM); Ritsu Doan (WB); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Éderson (CM) | Casemiro; Luke Shaw; Tyler Fredricson | 147.8 | 147.16 |
| full_plans/cannot_sell_Casemiro | full plan: sale blocked | OPTIMAL | yes | 1080.81 | 1080.81 | 4 | Jonathan Burkardt (AM); Ritsu Doan (WB); Lucas Chevalier (GK); Bafodé Diakité (CB); Jonathan David (ST); Piero Hincapié (CB) | Harry Maguire; Mason Mount; Luke Shaw; Tyler Fredricson | 124.33 | 147.68 |
| full_plans/cannot_sell_Luke_Shaw | full plan: sale blocked | OPTIMAL | yes | 1097.93 | 1097.93 | 6 | Ritsu Doan (WB); Bryan Mbeumo (AM); Lucas Chevalier (GK); Jonathan David (ST); Éderson (CM); Piero Hincapié (CB) | Harry Maguire; Casemiro; Mason Mount | 186.58 | 147.94 |

## Direct alternatives

Plan A is the base signing. For B, C and D the other five purchases and all sales are held fixed, the earlier choices are ruled out, and the replacement must start in the same role. The rest of the lineup may still be re-arranged. Options in different rows are not guaranteed to be affordable together. Likelihood labels are judgement written as rules, not probabilities.

| need | plan | player | club | age | role | starts | quality_in_role | fee_gbp_m | wage_gbp_m | likelihood | reason | objective | change_from_base |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WB | A | Ritsu Doan | SC Freiburg | 26 | WB | yes | 81.2 | 20.4 | 5.72 | possible | regular player at a club outside the top four | 1100.96 | 0.0 |
| WB | B | Rayan Aït-Nouri | Wolverhampton Wanderers | 23 | WB | yes | 77.8 | 32.4 | 5.72 | likely | club finished 15th or lower | 1097.51 | -3.45 |
| WB | C | Bafodé Diakité | LOSC Lille | 24 | WB | yes | 77.2 | 23.1 | 5.72 | possible | regular player at a club outside the top four | 1097.01 | -3.95 |
| WB | D | Weston McKennie | Juventus FC | 26 | WB | yes | 75.4 | 22.2 | 5.72 | possible | at a top-four club but played under 70% of its league minutes | 1095.12 | -5.84 |
| AM | A | Bryan Mbeumo | Brentford FC | 25 | AM | yes | 88.3 | 50.9 | 10.4 | possible | regular player at a club outside the top four | 1100.96 | 0.0 |
| AM | B | Rafael Leão | AC Milan | 25 | AM | yes | 87.6 | 69.4 | 10.4 | possible | regular player at a club outside the top four | 1100.2 | -0.76 |
| AM | C | Matheus Cunha | Wolverhampton Wanderers | 26 | AM | yes | 84.0 | 55.5 | 10.4 | likely | club finished 15th or lower | 1096.65 | -4.31 |
| AM | D | Álex Baena | Villarreal CF | 23 | AM | yes | 83.1 | 46.3 | 7.8 | possible | regular player at a club outside the top four | 1095.76 | -5.2 |
| GK | A | Lucas Chevalier | LOSC Lille | 23 | GK | yes | 88.3 | 27.8 | 5.72 | possible | regular player at a club outside the top four | 1100.96 | 0.0 |
| GK | B | Marcin Bulka | OGC Nice | 25 | GK | yes | 83.0 | 25.2 | 5.72 | doubtful | regular starter at a top-four club | 1095.67 | -5.29 |
| GK | C | Marco Carnesecchi | Atalanta BC | 24 | GK | yes | 82.7 | 31.5 | 5.72 | doubtful | regular starter at a top-four club | 1095.42 | -5.54 |
| GK | D | Joan García | RCD Espanyol Barcelona | 24 | GK | yes | 72.8 | 18.5 | 3.9 | doubtful | reported on 26 May 2025 to have agreed terms in principle with Barcelona; not announced by the cutoff | 1085.5 | -15.46 |
| ST | A | Jonathan David | LOSC Lille | 25 | ST | yes | 86.1 | 0.0 | 7.8 | likely | leaving the club without a fee | 1100.96 | 0.0 |
| ST | B | Jonathan Burkardt | 1.FSV Mainz 05 | 24 | ST | yes | 75.8 | 32.4 | 5.72 | possible | regular player at a club outside the top four | 1090.74 | -10.22 |
| ST | C | Dušan Vlahović | Juventus FC | 25 | ST | yes | 75.0 | 41.6 | 7.8 | possible | at a top-four club but played under 70% of its league minutes | 1089.89 | -11.07 |
| ST | D | Evann Guessand | OGC Nice | 23 | ST | yes | 71.8 | 31.5 | 5.72 | doubtful | regular starter at a top-four club | 1086.71 | -14.25 |
| CM | A | Éderson | Atalanta BC | 25 | CM | yes | 86.5 | 63.1 | 10.4 | doubtful | regular starter at a top-four club | 1100.96 | 0.0 |
| CM | B | Martín Zubimendi | Real Sociedad | 26 | CM | yes | 79.4 | 55.5 | 10.4 | doubtful | reported on 28 May 2025 to have agreed a move to Arsenal; not announced by the cutoff | 1093.81 | -7.15 |
| CM | C | Enzo Millot | VfB Stuttgart | 22 | CM | yes | 77.4 | 32.4 | 5.72 | possible | regular player at a club outside the top four | 1091.89 | -9.07 |
| CM | D | Pablo Barrios | Atlético de Madrid | 21 | CM | yes | 76.5 | 46.3 | 7.8 | possible | at a top-four club but played under 70% of its league minutes | 1090.9 | -10.06 |
| CB | A | Piero Hincapié | Bayer 04 Leverkusen | 23 | CB | yes | 87.6 | 63.1 | 10.4 | doubtful | regular starter at a top-four club | 1100.96 | 0.0 |
| CB | B | Levi Colwill | Chelsea FC | 22 | CB | yes | 87.2 | 69.4 | 10.4 | doubtful | plays for a direct rival | 1100.47 | -0.49 |
| CB | C | Dani Vivian | Athletic Bilbao | 25 | CB | yes | 86.8 | 50.5 | 10.4 | doubtful | regular starter at a top-four club | 1100.13 | -0.83 |
| CB | D | Edmond Tapsoba | Bayer 04 Leverkusen | 26 | CB | yes | 85.7 | 50.5 | 10.4 | doubtful | regular starter at a top-four club | 1099.02 | -1.94 |

## Review of the shortlisted players

The same checks for every player above. A later announcement does not prove that no earlier commitment existed, so the wording is limited to what the reviewed sources establish.

| need | plan | player | club_at_cutoff | ownership_and_spell | commitment_before_cutoff | contract_or_free_status | senior_place_needed | home_grown |
|---|---|---|---|---|---|---|---|---|
| WB | A | Ritsu Doan | SC Freiburg | At the club since 2022-07-05 (signed for a fee) | No pre-cutoff commitment established from reviewed sources. A later move to Eintracht Frankfurt was announced on 7 Aug 2025 | Not verified | yes | Counted as not home-grown; not verified |
| WB | B | Rayan Aït-Nouri | Wolverhampton Wanderers | At the club since 2020-10-04 (arrived without a recorded fee (loan or free transfer)) | No pre-cutoff commitment established from reviewed sources. The earliest report found of a move to Manchester City is dated 5 Jun 2025 | Not verified | yes | No home-grown mark on Wolves' senior list of 7 Feb 2025 |
| WB | C | Bafodé Diakité | LOSC Lille | At the club since 2022-08-05 (signed for a fee) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| WB | D | Weston McKennie | Juventus FC | At the club since 2020-09-01 (arrived without a recorded fee (loan or free transfer)) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| AM | A | Bryan Mbeumo | Brentford FC | At the club since 2019-08-05 (signed for a fee) | No pre-cutoff commitment established from reviewed sources. Bids from United were reported from early June 2025 | Not verified | yes | No home-grown mark on Brentford's senior list of 7 Feb 2025 |
| AM | B | Rafael Leão | AC Milan | At the club since 2019-08-01 (signed for a fee) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| AM | C | Matheus Cunha | Wolverhampton Wanderers | At the club since 2023-01-01 (arrived without a recorded fee (loan or free transfer)) | United was reported on 27-28 May 2025 to have met the release clause; the club statement is dated 1 Jun 2025. By team ruling the player is an ordinary candidate | Not verified | yes | No home-grown mark on Wolves' senior list of 7 Feb 2025 |
| AM | D | Álex Baena | Villarreal CF | at the club before a loan; joining not on record; in the club by 2017-07-01 (move out of the club, for example on loan) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| GK | A | Lucas Chevalier | LOSC Lille | at the club before a loan; joining not on record; in the club by 2016-07-01 (move between the club's own sides) | No pre-cutoff commitment established from reviewed sources. A later move to Paris Saint-Germain was announced on 9 Aug 2025 | Not verified | yes | Counted as not home-grown; not verified |
| GK | B | Marcin Bulka | OGC Nice | At the club since 2021-08-05 (arrived without a recorded fee (loan or free transfer)) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| GK | C | Marco Carnesecchi | Atalanta BC | At the club since 2017-01-30 (joined the club's youth or reserve side from another club (for a fee)) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| GK | D | Joan García | RCD Espanyol Barcelona | At the club since 2016-07-01 (joined the club's youth or reserve side from another club (no recorded fee)) | Reported on 26 May 2025 to have agreed terms in principle with Barcelona; the release clause was paid on 13 Jun 2025. Kept available under the standard used for Cunha; labelled doubtful | Not verified | yes | Counted as not home-grown; not verified |
| ST | A | Jonathan David | LOSC Lille | At the club since 2020-08-11 (signed for a fee) | Not verified | Announced on 14 May 2025 that he would leave Lille without a fee when the contract ended on 30 June 2025 | yes | Counted as not home-grown; not verified |
| ST | B | Jonathan Burkardt | 1.FSV Mainz 05 | At the club since 2014-07-01 (joined the club's youth or reserve side from another club (no recorded fee)) | No pre-cutoff commitment established from reviewed sources. The earliest dated report found of an agreement with Eintracht Frankfurt is 9 Jun 2025 | Not verified | yes | Counted as not home-grown; not verified |
| ST | C | Dušan Vlahović | Juventus FC | At the club since 2022-01-28 (signed for a fee) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| ST | D | Evann Guessand | OGC Nice | At the club since 2016-07-01 (joined the club's youth or reserve side from another club (no recorded fee)) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| CM | A | Éderson | Atalanta BC | At the club since 2022-07-06 (signed for a fee) | Not verified: one search found nothing either way | Not verified | yes | Counted as not home-grown; not verified |
| CM | B | Martín Zubimendi | Real Sociedad | At the club since 2011-07-01 (joined the club's youth or reserve side from another club (no recorded fee)) | Reported on 28 May 2025 to have met Arsenal's terms with a medical to follow; not announced by the cutoff. Kept available under the standard used for Cunha; labelled doubtful | Not verified | yes | Counted as not home-grown; not verified |
| CM | C | Enzo Millot | VfB Stuttgart | At the club since 2021-08-14 (signed for a fee) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| CM | D | Pablo Barrios | Atlético de Madrid | At the club since 2017-07-01 (joined the club's youth or reserve side from another club (no recorded fee)) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| CB | A | Piero Hincapié | Bayer 04 Leverkusen | At the club since 2021-08-16 (signed for a fee) | No pre-cutoff commitment established from reviewed sources. Interest from other clubs was reported later in summer 2025 | Contract extended in December 2024 to 30 June 2029, as stated by the club | yes | Counted as not home-grown; not verified |
| CB | B | Levi Colwill | Chelsea FC | at the club before a loan; joining not on record; in the club by 2019-07-01 (move between the club's own sides) | Not verified: one search found nothing either way | Not verified | yes | On Chelsea's under-21 list of 7 Feb 2025, which carries no home-grown marks; counted as not home-grown |
| CB | C | Dani Vivian | Athletic Bilbao | At the club since 2017-07-01 (joined the club's youth or reserve side from another club (no recorded fee)) | Not verified | Not verified | yes | Counted as not home-grown; not verified |
| CB | D | Edmond Tapsoba | Bayer 04 Leverkusen | At the club since 2020-01-31 (signed for a fee) | Not verified | Not verified | yes | Counted as not home-grown; not verified |

## Alternative full plans

One signing or sale is ruled out and every transfer and role is decided again.

| blocked | objective | net_spend | wages | changes |
|---|---|---|---|---|
| cannot sign Ritsu Doan | 1097.51 | 210.72 | 147.94 | signs instead: Rayan Aït-Nouri; no longer signs: Ritsu Doan |
| cannot sign Bryan Mbeumo | 1100.2 | 217.2 | 147.94 | signs instead: Rafael Leão; no longer signs: Bryan Mbeumo |
| cannot sign Lucas Chevalier | 1095.67 | 196.17 | 147.94 | signs instead: Marcin Bulka; no longer signs: Lucas Chevalier |
| cannot sign Jonathan David | 1093.08 | 244.96 | 147.94 | signs instead: Álex Baena; no longer signs: Jonathan David; starting role changes: Bryan Mbeumo AM to ST |
| cannot sign Éderson | 1099.33 | 205.0 | 147.94 | signs instead: Levi Colwill; no longer signs: Éderson |
| cannot sign Piero Hincapié | 1100.47 | 205.0 | 147.94 | signs instead: Levi Colwill; no longer signs: Piero Hincapié |
| cannot sell Harry Maguire | 1093.82 | 147.8 | 147.16 | signs instead: Jonathan Burkardt, Bafodé Diakité; no longer signs: Bryan Mbeumo, Piero Hincapié; also sells: Tyler Fredricson; keeps: Harry Maguire |
| cannot sell Casemiro | 1080.81 | 124.33 | 147.68 | signs instead: Jonathan Burkardt, Bafodé Diakité; no longer signs: Bryan Mbeumo, Éderson; also sells: Mason Mount, Tyler Fredricson; keeps: Casemiro |
| cannot sell Luke Shaw | 1097.93 | 186.58 | 147.94 | also sells: Mason Mount; keeps: Luke Shaw |
