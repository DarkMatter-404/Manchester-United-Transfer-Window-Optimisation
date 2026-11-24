# Decision log

**The current value of every assumption is in [assumptions.md](assumptions.md).** This file is the dated history: it records how each value was reached, including values that were later replaced.

This file records the project's modelling choices. The agreed project rules were set in the team's project plan, which is not part of this public copy; they are listed here only so that fixed rules and open choices can be told apart. A change to an agreed rule needs an instruction from the team. Routine estimation choices are proposed here, dated, and tested.

Each entry is labelled **Agreed rule**, **Implementation choice**, **Provisional** (a placeholder that still needs a decision or data) or **Limitation**.

## 1. Agreed rules carried into the code

These are not open for tuning. The code takes them as parameters so the small test cases can use other values, but the real runs must use the values below.

| Rule | Value | Where it appears in the model |
|---|---|---|
| Net transfer allowance B | £250m | `net_spend` row |
| Highest fee for one discretionary purchase | £75m, lowered from £100m on 17 November 2026 (3.13) | Candidate filter; `check_inputs` rejects a candidate above `fee_cap` |
| Candidate age | ≤ 26 on 31 May 2025 | Candidate filter, not a model row |
| Candidate location | Employed by a European club | Candidate filter, not a model row |
| Arrivals T_B | ≤ 6, fixed arrivals included | `arrivals` row |
| Discretionary sales T_S | ≤ 6 | `sales` row |
| Formation | 3-4-2-1: k = (GK 1, CB 3, WB 2, CM 2, AM 2, ST 1) | `formation` rows |
| Senior registration | ≤ 25 senior-list players, ≤ 17 non-homegrown among them | `senior_list` and `non_homegrown` rows |
| Information cutoff | End of 31 May 2025 | Input preparation |
| Loans | No loan decisions; players out on loan at the cutoff are excluded | Roster reconciliation |
| Expiring contracts | No assumed renewal; zero proceeds | Roster reconciliation (set D) |

## 2. Implementation choices made on 16 November 2026

**2.1 One model function for the toy and the real runs. (Implementation choice)**
`src/transfer_model.py` holds the full formulation of plan Section 12. The toy checks call the same function with three roles and one starter per role. This avoids keeping two versions of the constraints that could drift apart.

**2.2 Registration limits and the fee ceiling are parameters. (Implementation choice)**
The formulation writes 25, 17 and 100 as numbers. The code reads them from `senior_cap`, `non_hg_cap` and `fee_cap` so that a three-player toy case can test the registration rows with small limits. Real runs use 25, 17 and 100.

**2.3 Scenario restrictions `no_buy` and `no_sell`. (Implementation choice)**
A run can list candidates that may not be bought (b_p = 0) and existing players who may not be sold (s_p = 0). These are the rows described in plan Section 12.9 for ranked alternatives and failed-sale checks. They are also used for the no-transfer comparison. They add restrictions only; they never create income or relax a limit.

**2.4 Cover and starting roles are reported as (player, role) pairs. (Implementation choice)**
The checker receives lists of pairs rather than one role per player, so a plan that gave one player two roles would be reported instead of being hidden by the data structure.

**2.5 Infeasible runs. (Implementation choice)**
If Gurobi reports that no plan satisfies the rules, the code does not read solution values. It asks Gurobi for an irreducible inconsistent subsystem and returns the names of the conflicting rows. A hard rule is not relaxed automatically.

**2.6 First settings for availability and development. (Agreed starting point, plan Section 12.6)**
λ = 0 (no development bonus) and a_p = 1 (neutral availability) until supported indicators exist. Neutral availability means injury effects are not quantified. It does not mean a player is known to be fit.

**2.7 Dated tables are cut when they are read. (Implementation choice)**
`src/prepare_inputs.py` reads every dated source table through a filter that keeps rows dated on or before 31 May 2025, and stops if a later row is found. The undated profile fields that describe a player today (current club, current value, contract end) are not used. Club at the cutoff is taken from the last league appearance, and value from the latest dated valuation.

**2.8 Currency. (Implementation choice)**
Euro values are converted at 0.8412 GBP per EUR, the ECB reference rate on 30 May 2025, the last rate published before the cutoff.

**2.9 Roles come from positions started. (Implementation choice, threshold still open)**
Lineup position labels are mapped to the six roles in `src/prepare_inputs.py`. Wide-midfield and full-back labels count as WB; wingers and second strikers count as AM, the two places behind the striker. The number of starts needed for eligibility is a proposal (see Section 3).

**2.10 Wide midfielders are wing-backs only in a back-three or back-five shape. (Implementation choice; corrected after the first base run)**
The first base run chose Álex Baena, a winger, as a starting wing-back. The cause was the role mapping in 2.9: the lineup label "Left Midfield" or "Right Midfield" was always counted as WB. That is right for a team in a 3-4-2-1, where those players are the wing-backs, but wrong for a 4-4-2, where they are wide attackers. All of Baena's nine such starts were in 4-4-2 shapes.

The rule now uses the team's formation in each match: the label counts as WB when the formation starts with three or five defenders, and as AM otherwise. In the big five leagues 81% of these starts were in back-three or back-five shapes. The change altered the eligible roles of 45 pool players (28 lost WB, 25 gained AM) and of no United player.

This correction was made after seeing a selection, which the procedure tries to avoid. It is recorded because it changes inputs. It was made on football grounds, to stop an unsuitable lineup, and not to favour or remove a particular player.

**2.11 Candidates shown by dated evidence to be unavailable are blocked. (Implementation choice, following the plan)**
`docs/unavailable_candidates.csv` lists candidates who could not have been signed at the cutoff, each with a dated source. They are blocked in every run. First entry: Jeremie Frimpong, whose move to Liverpool was announced on 30 May 2025. The check is made by hand on the players a run selects, so a player who was unavailable but never selected is not listed.

## 3. Team rulings of 16 November 2026

Given by Aman on 16 November 2026, before any real-player model run and before any quality score was computed.

**3.1 Matheus Cunha is an ordinary candidate in the base case. (Team ruling)**
Reports of 27 and 28 May 2025 said United had met the release clause, but the club's statement is dated 1 June 2025, after the cutoff. Cunha is therefore not a fixed arrival and is in the candidate pool with a fee estimated like any other candidate. A separate sensitivity run will fix Cunha as an arrival at the reported £62.5m.

**3.2 Candidates come from the big five leagues only. (Team ruling)**
England, Spain, Italy, Germany and France. Other leagues are excluded for lack of a league-strength adjustment, not as a judgement on their players. With the agreed age limit and a 900-minute threshold this gives 806 candidates (`docs/exclusions.csv`).

**3.3 United wages are entered by hand; candidate wages use a value-band rule. (Team ruling)**
United's wages go into `data/manual/united_wages.csv` with source and date. Candidate wages are estimated from bands of the estimated fee; the bands in 3.5 are a proposal and are not yet approved. Because the two groups are measured differently, a sensitivity run will apply the band rule to United's players as well.

**3.4 Market value is one component of the quality score. (Team ruling)**
The dated market value enters the score with more weight where statistics are thin (GK, CB). Results are also reported with that component removed, because value also drives the fee.

**3.5 Candidate wage bands. (Team ruling: approved by Aman on 16 November 2026, before any real-player run)**
Weekly gross wage by estimated purchase fee. These are assumptions, not observed pay. They apply to candidates only; United's players use the figures in `data/manual/united_wages.csv`.

| Estimated fee | Weekly wage | Per year |
|---|---:|---:|
| £70m or more | £250,000 | £13.0m |
| £50m to under £70m | £200,000 | £10.4m |
| £35m to under £50m | £150,000 | £7.8m |
| £20m to under £35m | £110,000 | £5.7m |
| £10m to under £20m | £75,000 | £3.9m |
| Under £10m | £45,000 | £2.3m |

**3.6 Players on loan at the cutoff are ignored completely. (Team ruling, 16 November 2026)**
Rashford, Antony, Malacia and Sancho were on loan away from United on 31 May 2025. They are outside the model: they cannot be sold, they bring no sale receipt into the transfer budget, they create no wage saving, and their wages are not counted in the wage allowance or anywhere else. Their wage obligations are not estimated or reserved. This replaces the earlier instruction in the plan to reserve those obligations.

Only loans in place on 31 May 2025 count. A player who was at United on that date and was loaned out later stays in the model, because a later loan is information from after the cutoff. This matters for the wage source in 3.7, whose "loaned out" list is for 2025/26 and names Onana, Højlund, Collyer and Amass; all four were at United at the cutoff and remain existing players.

**3.7 Source of United's wages. (Implementation choice, with a limitation)**
Aman supplied a browser printout of a public payroll table for the **2025/26** season (`data/manual/2025-26 Manchester United F.C. Payroll Table.pdf`, viewed 16 November 2026). `src/extract_united_wages.py` reads the annual salary of each player who is in the model and writes `data/manual/united_wages.csv`. The figures are the provider's estimates of gross annual base salary, not club-confirmed pay.

The table is from the season after the cutoff. A figure is used as the player's wage at the cutoff on the assumption that the contract terms did not change between 31 May 2025 and the 2025/26 listing. This has not been checked contract by contract. Known points:

- 24 of the 25 model players have a figure from the table. Alejandro Garnacho is not in it; Aman supplied the 2024/25 figure by hand on 16 November 2026 (gross base wage of £50,000 a week, £2.6m a year; source page not recorded). It is kept in `data/manual/united_wages_hand_entered.csv`.
- Diego León's figure is from the contract that began after the cutoff; the move was agreed before it.
- Wages shown for players United signed after the cutoff (Cunha, Mbeumo, Šeško, Lammens) are **not used**. Any of them who is a candidate gets a band wage like every other candidate.
- The printout also lists 2026 transactions. They are not used.

The 2024/25 version of the same table would be the better source, since it predates the cutoff and should include Garnacho. It should replace this one if it can be obtained.

**3.8 Settings approved on 16 November 2026. (Team rulings)**
Aman's replies to `proposals.md`, given before any real-player model run. The quality scores were computed only after this approval.

| Setting | Ruling | Value used |
|---|---|---|
| Wage allowance W | Approved as proposed | £148m per year |
| Players per role, minimum to maximum | Approved as proposed | GK 2–3, CB 5–7, WB 4–5, CM 4–5, AM 4–6, ST 2–3 |
| Role weights ω | Approved as proposed | 1 for every role |
| Depth weight μ | Changed: 0.2 was judged too low, because some non-starters are rotation players who play often | 0.3; tested at 0.2 and 0.4 |
| Purchase fee | Changed: 1.1 × value in general, higher for an English player at a Premier League club | 1.1 × value; 1.3 × value for an English player at a Premier League club |
| Sale receipt | Approved as proposed | 0.9 × value |
| Quality score | Approved as proposed | Components, weights and rules of proposals.md P7 |
| Diego León | Changed: leave the player out of the model | Not in the model (see 3.9) |

Two of these values were chosen by the assistant from Aman's direction. **Aman confirmed both on 16 November 2026**, before the base case was run:

- **Depth weight 0.3.** Aman asked for more than 0.2 without naming a number.
- **English player at a Premier League club, 1.3.** Aman asked for a higher multiplier without naming a number. In transfers between big-five clubs from June 2021 to May 2025 (players aged 26 or under, fee and value at least €5m), English players sold by Premier League clubs went for a median of 1.27 times their value (50 deals), against 1.06 for all other deals (493). In the last two seasons alone the figures were 1.26 and 1.09. The same data show non-English players sold by Premier League clubs at 1.22 (95 deals), so part of the premium belongs to the selling league, not to nationality. The ruling applies it to English players only.

The wage allowance was proposed as today's squad total plus 10%. With León left out, the existing players total £133.38m, so £148m is about 11% above it. The approved figure of £148m is kept.

**3.9 Diego León is left out of the model. (Team ruling, 16 November 2026)**
The plan treats an arrival agreed before the cutoff as fixed. Aman ruled that León should be ignored. The recorded reason is one that holds at the cutoff: an 18-year-old with no senior match in the covered leagues, signed for development, who falls outside the first-team pool in the same way as the wider academy. Aman also noted that León has not played since; that is information from after the cutoff and is not the basis of the ruling. Consequences: there is no fixed arrival, the reported fee of about £3.3m is not counted in the budget, León does not use one of the six arrivals, and the wage is not counted.

**3.10 Realism rulings after the first base run. (Team rulings, 16 November 2026)**
The first base plan was checked by hand and four questions were put to Aman. These rulings were made after seeing a provisional selection; they are feasibility assumptions about who can be bought, not changes to how players are scored.

| Question | Ruling | How it is applied |
|---|---|---|
| Players at Manchester City and Liverpool | Never sold to United | Left out of the candidates in every run |
| Players at Arsenal | Sold only at a very high mark-up | Fee = 2.0 × value |
| Players at Chelsea and Tottenham | A mark-up below Arsenal's but above other clubs | Fee = 1.5 × value |
| Players who joined their club in January 2025 | Treated like any other candidate | No rule added |
| Mason Greenwood | A return to United is not feasible | Blocked (`docs/unavailable_candidates.csv`) |
| A player documented as leaving without a fee | No fee; wage as for a bought player of the same value | Fee set to zero for players listed with a dated source in `docs/free_agents.csv`; first entry Jonathan David |

The Arsenal figure of 2.0 and the Chelsea and Tottenham figure of 1.5 were chosen by the assistant from Aman's wording. Aman confirmed them on 16 November 2026. Where more than one mark-up applies to a player, the highest is used; mark-ups are not multiplied together. The transfer data do not support or contradict these mark-ups: completed sales by these clubs had a median of 1.02 times value, but sales of leading players to a direct rival are rare, so the data say little about what such a deal would cost.

The free-agent rule covers only players checked by hand. A free agent the model never selects is not identified and keeps a value-based fee, which makes such players look dearer than they were.

**3.11 Further rulings after the second base run. (Team rulings, 16 November 2026)**
Made after seeing a base plan, as feasibility assumptions about who can be bought and at what price.

- **Two-year rule.** A candidate who joined their club on or after 1 June 2023 cannot be signed, because clubs rarely sell a player they signed recently. This replaces the earlier ruling that left January 2025 arrivals alone. The joining date is the first dated move into the club in the transfer records; a move up from the club's own youth or reserve side and a return from a loan are not counted as joining. The rule removes 463 of the 806 candidates and leaves 343 (`docs/exclusions.csv`).
- **Key players are not sold cheaply.** Aman agreed that leading players at Paris Saint-Germain and Barcelona would not be sold at 1.1 times value. Applied as a general rule: a candidate who played at least 70% of the league minutes of a club that finished in its league's top four costs 1.5 times value. The 70%, the top four and the 1.5 were chosen by the assistant; Aman confirmed them on 17 November 2026.
- **Contract length.** Aman asked for the fee to rise with the years left on a player's contract. **This is not applied.** The data hold each player's contract end only as it stands today, which reflects renewals and moves after the cutoff. A dataset snapshot dated 30 May 2025 exists in the source's version history, but its files could no longer be downloaded on 16 November 2026. The only contract information used is the dated evidence for documented free agents (3.10).
- **Order of approach and likelihood.** Two outputs are produced for each signing in the base plan (`results/approach_plan.csv`). Plan A is the base choice. Plans B, C and D are found by holding the rest of the plan fixed, blocking the earlier choices and solving again, considering only players who can play the same role. Each player also gets a label:

| Label | Rule |
|---|---|
| Likely | Leaving without a fee; or played under half of the club's league minutes; or the club finished 15th or lower |
| Doubtful | Plays for Arsenal, Chelsea or Tottenham; or a regular starter (70% of minutes) at a top-four club |
| Possible | Everyone else |

These labels are judgement written down as rules. They are not probabilities and were not estimated from past deals.

**3.12 Rulings of 17 November 2026. (Team rulings)**

- **Four clubs that have no need to sell.** The key-player rule in 3.11 uses league minutes, and it missed the players it was written for: Paris Saint-Germain and Bayern Munich rest their leading players in league matches, so none of their candidates reached 70% of league minutes (Achraf Hakimi did not). Aman asked for the same mark-up at Bayern Munich and Real Madrid. Applied as: every candidate at Paris Saint-Germain, Barcelona, Real Madrid or Bayern Munich costs 1.5 times value, whatever their minutes. The 70% rule still applies at other top-four clubs. Where several mark-ups apply, the highest is used.
- **Contract length is left out.** Confirmed by Aman: it would need contract dates as of the cutoff, and applying it to a few hand-checked players would treat them differently from the rest. The report should name this as a limitation.
- **A fee of £75m or more is labelled doubtful.** Aman's view is that United would be unlikely to pay that much for one player. This changes the likelihood label only. The hard ceiling stays at £100m, as agreed in the plan. For reference, United paid more than £75m for a player three times before the cutoff (2016, 2019 and 2022), so this is a view about the club's position in 2025, not a historical fact. A run with the ceiling lowered to £75m is included among the sensitivity runs.
- **Later information about Enzo Fernández.** While discussing the base plan, Aman mentioned a transfer of this player in 2026. That is after the cutoff. It has not been checked, is not an input, and may not be used to defend or change the selection; it belongs to the evaluation step only.

**3.13 Fee ceiling lowered to £75m, and hand checks. (Team ruling and implementation, 17 November 2026)**

- **Fee ceiling.** Aman ruled that the highest fee for one purchase is £75m, given the club's position in 2025. This changes an agreed rule and is recorded in the plan and the project overview. The run with the earlier £100m ceiling is kept as a sensitivity run; it scores 0.05 points more. The ruling was made after seeing that run.
- **Hand checks.** The six base signings and the borderline plan B to D players were checked against dated sources for a move already agreed before the cutoff, and Premier League players for home-grown marks. Findings are in `docs/hand_checks.csv`. One player was blocked: Giorgi Mamardashvili, whose transfer to Liverpool was confirmed on 27 August 2024. Martín Zubimendi was reported on 28 May 2025 to have agreed a move to Arsenal that was not announced by the cutoff; under the standard used for Cunha (an official announcement) the player stays available and is labelled doubtful by hand (`docs/likelihood_notes.csv`). No dated evidence was found either way for Éderson and Levi Colwill. The other plan B to D players were not searched one by one.
- **Home-grown status.** The base signings from Premier League clubs carry no home-grown mark on the squad lists of 7 February 2025, except that Levi Colwill was on an under-21 list, which carries no marks. All candidates stay counted as not home-grown. The base plan has 16 non-home-grown senior players against a limit of 17, so it holds either way.
- **Later information seen during the checks.** Establishing that a player was free at the cutoff meant finding when the player's later move was announced. Those later moves are recorded only to date the absence of an earlier deal. They are not inputs.

**3.14 Corrections from the review of 17 November 2026. (Approved by Aman)**
A review of the project found errors and unclear points. Aman approved the corrections below. None changes an approved rule; each changes how a rule is carried out or reported.

- **Two-year rule.** The earlier version dated a player's stay from the earliest move into the club, and ignored every move from a youth side. Both were wrong. Raoul Bellanova was treated as at Atalanta since a 2020 loan although the current spell began with a signing from Torino in August 2024; Liam Delap's signing by Ipswich from Manchester City's youth setup in July 2024 was ignored. `src/club_spells.py` now finds the start of the current spell and tells apart a new signing after an earlier spell, a loan made permanent, a return from loan, a move up from the club's own youth side and a signing from another club's youth side. A candidate whose spell cannot be dated and who has no match for the club before June 2023 is "not verified" and is not treated as eligible (8 players). One case is settled by a documented entry in `joining_date_overrides.csv` (Destiny Udogie). Result: 484 candidates are inside the two years (463 before), 314 are eligible (343 before).
- **One scoring reference.** Scores are percentiles within a group, so removing candidates used to change every score. All 806 candidates that pass the league, age, minutes and valuation filters are now scored together with the existing players, in every run. The two-year rule is applied when a run is built. A run without the rule can therefore be compared with the base case.
- **Fees and wages separated.** A candidate's wage used to follow the scenario fee, so a "fee" scenario also changed wages. The wage now comes from the fee the base rule gives and stays fixed in fee-only runs. Runs where the wage band follows the fee are kept and named "combined fee and wage". Two runs change candidate wages by 10% with fees fixed.
- **Free agents and the fee ceiling.** The ceiling is now applied to the fee actually payable. A documented free agent pays nothing and cannot be removed by the ceiling; the wage still follows the player's value.
- **Direct alternatives.** Plans B to D for each signing now hold the other five purchases and all sales fixed and require the replacement to start in the role the original target starts in. The earlier version only required eligibility, which let a striker alternative be used in attacking midfield. Only transactions are fixed; the rest of the lineup may still be re-arranged. Plans where everything is re-decided are reported separately with their changes listed.
- **Comparing plans across scoring choices.** Runs with another score or other weights are on a different scale. Every plan's purchases and sales are re-scored with the base score and base weights, and that figure is used for comparisons.
- **Review of the shortlist.** Every player in the A to D lists gets the same four checks (ownership and spell, commitment before the cutoff, contract or free status, registration), in `results/shortlist_review.csv`. Where nothing was reviewed the entry says "not verified". A later announcement is not treated as proof that no earlier commitment existed.
- **Saved with each run.** The complete settings and limits, and a manifest with the code version, input hashes and solver status, bound, gap and runtime.

**3.15 Freeze and evaluation. (Procedure, 17 November 2026)**
After the corrected runs were checked and committed, the recommendations were frozen in `results/freeze/`: code commit, input hashes, base settings, the preferred plan, the direct and full-plan alternatives, the shortlist review, all 281 candidates considered and the evaluation measures. The freeze was committed and pushed before the evaluation script was run. That script is the only code that reads records dated after the cutoff, and it reads the frozen lists, not the model. No input, setting or score was changed after the outcomes were seen. Any later change would be a separate exploratory analysis.

The team and the assistant already knew parts of what happened in 2025/26 before the freeze (5.1), so the freeze documents the procedure and does not make the study blind.

**3.16 Post-freeze corrections. (Approved by the team, 18 November 2026)**
A review of the frozen version (commit `d3c86de`) found errors in how some rules were carried out. They were corrected after the 2025/26 outcomes had been examined, so the corrected results are labelled as a post-freeze correction and kept in `results/corrections/2026-11-18/`. The freeze and the original evaluation are unchanged and their hashes were checked before and after. No rule, limit, weight or score changed. Full details are in that folder's `correction_log.md` and `before_after.md`.

- **Club identity.** Clubs are identified by id, with a reviewed list of clubs' own youth-side names (`club_aliases.csv`). This replaces matching on shared words in names, which had joined Real Unión to Real Sociedad and failed to recognise sides such as FC Bayern II. Seventeen candidates changed eligibility: Aramburu is out; fifteen academy players and Herzog are in. Eligible candidates rose from 314 to 329.
- **Undated academy players** are accepted only with a dated record in the club before 1 June 2023; seven remain not verified and excluded.
- **Repeatable inputs.** Same-day moves are put in order and unorderable days are flagged; ties have an explicit rule; two builds give identical files.
- **Wages** come from the complete base fee rule in every run except the combined fee-and-wage runs. The club-rules run had changed 25 candidates' wages; now none change.
- **Evaluation** is measured club by club; a player's summary uses the main club only. Means and counts are reported as planned; medians are labelled as added later. The window ends on 1 September 2025, and the comparison group comes from a reviewed list of moves into United.
- **Safeguards.** New runs write only to a folder named with `--out`, never into the original results; freezing refuses an existing folder; the evaluation checks the frozen files' hashes first.
- **Result.** All 56 runs return the same transfers, objective, spending and wages as before. The frozen recommendation and its alternatives are unchanged.

**3.17 Additional runs and report revision. (Approved by Aman, 21 November 2026)**
After a review of the report against the project guideline, Aman approved additional analysis and a shorter main text (about 15 to 17 pages). The runs were made after the 2025/26 outcomes had been examined, use the same inputs and model as the corrected runs of 18 November 2026, and are kept in `results/corrections/2026-11-21/`. No rule, limit, weight or score of the base case changed, and the recommendation is unchanged.
- Wage allowance at £141m, £155m, £162m, £169m, £176m and £183m, in steps of £7m, to draw the wage curve beside the budget curve.
- One step on each limit: arrivals 7 (with the existing 5), non-home-grown places 16 and 18, budget ±£50m and wages ±£7m.
- No depth reward (μ = 0) and forced sales of Mason Mount and Rasmus Højlund, to explain why the two reserves are kept.
- A protected wage limit in the sense of Bertsimas and Sim (2004): up to Γ purchased players may earn more than estimated. The deviation of 10% of the estimated wage is an assumption made for this analysis, chosen to match the existing ±10% wage runs; to be confirmed by the team. It was solved by trying each possible value of the dual variable with the unchanged model code, a method checked against a full search of the invented example.
- The linear relaxation of the base model and of the model with the base transactions fixed.
The stability measure in the report counts only the 17 sensitivity runs that change the plan, because the full plans block a purchase by design and ten runs repeat the base plan.
On 22 November 2026, after peer reviews of the report, Aman approved two further additions to the same folder: a run in which Hincapié and Éderson are both ruled out and the whole plan is decided again, and a count of the reference players whose playing time comes from two clubs in one season (nothing rescored). The report text was corrected where the reviews found errors (the description of the reserves, the claim about fractional values in the relaxation, the run count and the table order), and the statement on assistance was drafted for the team to confirm.

## 4. Choices still open

| Choice | Status on 16 November 2026 |
|---|---|
| Contract length in the fee | Left out by team ruling (3.12); to be named as a limitation |
| Left/right roles | Open; add only if the chosen lineups look unsuitable |
| Treatment of missing availability evidence | Neutral base agreed; review of finalists still to define |
| Dermot Mee's contract status at the cutoff | To verify |
| Loan status of any candidate the model selects | Not checked. A candidate on loan is shown at the loan club |

Settled since the last version of this table: wage estimates, wage allowance, players per role, candidate pool, role eligibility (five starts), quality score, role weights, depth weight, fee and sale multipliers, and León (3.2 to 3.9).

## 5. Limitations recorded so far

**5.1 This is a retrospective exercise. (Limitation)**
The work is being done in November 2026. The team, and the AI assistant used for coding support, already know some of what happened after 31 May 2025. The earlier team explainer lists United's actual summer 2025 signings and departures and parts of the 2025/26 season. That knowledge cannot be removed, so the safeguards are procedural: inputs are built only from data dated on or before the cutoff, scoring and filter rules are written down before selections are inspected, 2025/26 data stay in a separate folder until the freeze, and no parameter is adjusted because of how a player later performed. The report must state this limitation.

On 16 November 2026, web searches for dated roster evidence returned some news from after the cutoff, including later transfers of United players. The wage printout supplied the same day shows United's 2025/26 squad, the wages of players signed after the cutoff, and some 2026 transactions. No 2025/26 match or performance data were opened, and none of that later information is used as an input.

**5.2 Solver licence size. (Limitation, action needed)**
The Gurobi licence installed with `pip install gurobipy` is size-limited to 2,000 variables and 2,000 linear constraints. The model has |E| + |C| + |P| + 2|H| variables. With about 30 existing players and 1.5 eligible roles per player, that allows roughly 370 candidates. The agreed pool has 806 candidates and 24 existing players. The base case has 792 candidates after the fee ceiling and needs about 3,800 variables, so the size-limited licence is not enough. On 16 November 2026 Gurobi refused the base model for this reason. Later the same day Aman supplied an academic Web License Service licence file, which is kept in the home folder and not in this repository. With it the base case solves in under a second. This licence needs an internet connection at each run. If the candidate pool after the agreed filters is larger, the full run needs a free academic licence (requested from the Gurobi user portal on the university network or VPN). The candidate pool must not be cut down just to fit the licence without recording it as a disclosed exclusion.

**5.3 Performance statistics are limited. (Limitation)**
The only performance source that could be read has minutes, goals, assists, cards, positions started and match results. Expected-goals, passing, defensive-action and goalkeeping statistics are not available to the project. Any quality score will therefore be a coarse ranking, weakest for goalkeepers and defenders, and the report should say so.

**5.4 Wages are estimates. (Limitation)**
United's wages are a provider's estimates taken from a 2025/26 table (3.7). Candidate wages are assumed bands (3.5). The two groups are measured differently, so a sensitivity run will apply the bands to United's players as well.
