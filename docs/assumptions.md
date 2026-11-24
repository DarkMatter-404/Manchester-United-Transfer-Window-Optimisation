# Current assumptions

This is the one table of what the model assumes **now**. It was last updated on 18 November 2026, after the post-freeze corrections, and matches `src/model_inputs.py`. When a value here differs from an older document, this page is right.

The history of how each value was reached, with dates and reasons, is in [decisions.md](decisions.md). [proposals.md](proposals.md) and Section 4 of [data_check.md](data_check.md) are earlier proposals kept as a record; they are not current instructions.

## Scope and limits

| Item | Current value | Kind |
|---|---|---|
| Club and window | Manchester United, summer 2025, permanent transfers only | Agreed rule |
| Information cutoff | End of 31 May 2025 for the historical match, transfer and valuation records. Not every input is dated to the cutoff: United's wages come from a later table and a few profile fields are undated (see the last section) | Agreed rule |
| Performance history | 2023/24 and 2024/25, up to the cutoff | Agreed rule |
| Net transfer allowance | £250m | Agreed rule |
| Highest fee for one purchase | £75m (lowered from £100m on 17 November 2026) | Team ruling |
| Arrivals | At most 6 | Agreed rule |
| Discretionary sales | At most 6 | Agreed rule |
| Annual wage allowance | £148m, for the players in the model. The base plan uses £147.94m; the £0.06m left is a margin on estimated wages, not evidence that the plan would be affordable in practice | Team ruling |
| Formation | 3-4-2-1: GK 1, CB 3, WB 2, CM 2, AM 2, ST 1 | Agreed rule |
| Players per role, minimum to maximum | GK 2–3, CB 5–7, WB 4–5, CM 4–5, AM 4–6, ST 2–3 | Team ruling |
| Senior registration | At most 25 senior-list players, at most 17 of them not home-grown | League rule |

## Who is in the model

| Item | Current value | Kind |
|---|---|---|
| Existing players | 24 players at United on the cutoff (`roster_reconciliation.csv`) | Evidence-based |
| Expiring contracts | Eriksen, Lindelöf, Evans and Heaton leave without a fee; no renewal assumed | Agreed rule |
| Players on loan at the cutoff | Rashford, Antony, Malacia and Sancho are ignored completely: no receipts, no wages, no savings | Team ruling |
| Diego León | Left out as a development signing; no fixed arrival in the base case | Team ruling |
| Matheus Cunha | An ordinary candidate; a run that fixes the arrival at £62.5m is a sensitivity run | Team ruling |
| Candidate leagues | England, Spain, Italy, Germany, France | Team ruling |
| Candidate age | 26 or younger on the cutoff | Agreed rule |
| Candidate minutes | At least 900 league minutes in 2024/25 | Team ruling |
| Two-year rule | A candidate whose current spell at the club began on or after 1 June 2023 cannot be signed. Clubs are identified by id, with their own youth and reserve sides from `data/processed/club_family.csv` and the reviewed names in `club_aliases.csv`. An unknown start date is accepted only if a dated record shows the player in the club before 1 June 2023; otherwise the case is not verified and not eligible (7 candidates). Method: `data_dictionary.md` Section 2 | Team ruling; method corrected 18 November 2026 |
| Clubs that never sell to United | Manchester City and Liverpool | Team ruling |
| Blocked by name | Jeremie Frimpong and Giorgi Mamardashvili (already signed elsewhere), Mason Greenwood (team ruling) | Evidence and ruling |

## Fees, receipts and wages

| Item | Current value | Kind |
|---|---|---|
| Market value | Latest valuation dated on or before the cutoff, converted at 0.8412 GBP per EUR | Observed estimate |
| Purchase fee | 1.1 × value | Team ruling, with pre-cutoff evidence |
| English player at a Premier League club | 1.3 × value | Team ruling, with pre-cutoff evidence |
| Arsenal | 2.0 × value | Team ruling |
| Chelsea, Tottenham | 1.5 × value | Team ruling |
| Paris Saint-Germain, Barcelona, Real Madrid, Bayern Munich | 1.5 × value for every player | Team ruling |
| Regular starter (70% of league minutes) at a top-four club | 1.5 × value | Team ruling |
| Several mark-ups at once | The highest one applies | Implementation choice |
| Documented free agent | No fee, checked before the fee ceiling; first entry Jonathan David | Team ruling |
| Contract length | Not used: contract dates as of the cutoff are not available | Limitation |
| Sale receipt | 0.9 × value | Team ruling |
| United wages | A provider's 2025/26 payroll table, used as an approximation of wages on the cutoff under an unchanged-contract assumption; Garnacho's 2024/25 figure entered by hand | Approximation |
| Candidate wages | Bands by the fee the base rule gives: £70m+ £250k a week, £50m+ £200k, £35m+ £150k, £20m+ £110k, £10m+ £75k, under £10m £45k | Team ruling |
| Wage and fee scenarios | A candidate's wage comes from the complete base fee rule (base multipliers and base club rules) in every run, so fee-only and club-price runs change no wage. Only runs named "combined fee and wage" let the wage follow the run's fee; runs named "candidate wages" scale wages with fees fixed | Implementation choice; corrected 18 November 2026 |

## Quality score and objective

| Item | Current value | Kind |
|---|---|---|
| What the score is | A role-based quality proxy from 0 to 100. It is not a scouting rating and not a prediction of league points | Description |
| Components | Playing time, output, team level, market value, each as a percentile among players eligible for the role. Playing time is a proxy: a season's league minutes for all clubs divided by the main club's matches, so for a player at two clubs it overstates the share at the main club. It is kept as frozen | Team ruling |
| Weights (playing time, output, team level, value) | ST and AM 0.20, 0.40, 0.10, 0.30; WB 0.30, 0.20, 0.15, 0.35; CM 0.30, 0.15, 0.15, 0.40; CB and GK 0.30, 0.10, 0.20, 0.40 | Team ruling |
| Output measure | Goals plus assists per 90 minutes; for CB and GK, goals the team conceded per start | Team ruling |
| Season weights | 2024/25 counts 70%, 2023/24 counts 30% | Team ruling |
| Small samples | Output set to 50 below 900 weighted minutes (or ten weighted starts for CB and GK) | Team ruling |
| Reference group for percentiles | All 806 candidates that pass the league, age, minutes and valuation filters, plus the 24 existing players. The same group is used in every run, including the run without the two-year rule | Implementation choice |
| Role eligibility | At least five starts in the role over the two seasons; otherwise the stored main position | Team ruling |
| Wide midfielders | Count as WB only when the team lined up with three or five at the back; otherwise AM | Implementation choice |
| Role weights | 1 for every role | Team ruling |
| Depth weight | 0.3 | Team ruling |
| Availability | 1 for every player. Injury risk is not quantified; this is not evidence that a player is fit | Limitation |
| Development | Not used. Development potential is not quantified | Limitation |

## Inputs that are not dated to the cutoff

The model's historical records are cut at 31 May 2025. These inputs are not, and are approximations or fallbacks:

| Input | What is used | Why it matters |
|---|---|---|
| United wages | A 2025/26 payroll table | Reflects the season after the cutoff; assumes contracts were unchanged |
| Stored main position | The source's current label | Used only as a fallback for players with fewer than five starts in any role |
| Preferred foot, height, citizenship | The source's current profile | Citizenship is used for the English mark-up |
| Registration rules page | Dated 2 July 2025 | Only standing rules are taken from it |

## Labels that are judgement

Likelihood labels (likely, possible, doubtful) follow written rules in `src/model_inputs.py`, with two labels set by hand from dated reports (`likelihood_notes.csv`). They are not probabilities and were not estimated from past deals.

## The evaluation

The 2025/26 evaluation uses records from after the cutoff and reads only the frozen lists. It is not a model input. It measures each club separately; a player's summary uses the club with the most league minutes. Means and counts are the summaries planned at the freeze; medians are shown as an extra description added after the evaluation. Higher later playing time for a player the plan sells is a risk indicator for that sale, not proof that the sale was wrong: the plan also counts the wages freed and the players bought.
