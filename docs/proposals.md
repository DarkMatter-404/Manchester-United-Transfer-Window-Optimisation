# Proposals awaiting approval

Written on 16 November 2026. These are the settings the model still needs before its first run on real players. Each one is a suggestion with its reason. None has been used in a model run, and no quality score has been computed yet. The point of approving them now is that the settings are fixed before anyone sees which players the model picks.

**Outcome, 16 November 2026.** Aman replied the same day. P1, P2, P3, P6 and P7 were approved as written. P4 was raised from 0.2 to 0.3. P5 keeps 1.1 × value in general and adds 1.3 × value for an English player at a Premier League club. P8 was replaced: Diego León is left out of the model. The rulings and the values used are in `decisions.md` items 3.8 and 3.9. The rest of this page is kept as the record of what was proposed.

## Summary

| # | Setting | Proposed base | Also tested |
|---|---|---|---|
| P1 | Annual wage cap W | £148m (today's squad total plus 10%) | £134.7m (no growth); no cap |
| P2 | Players per role, minimum to maximum | GK 2–3, CB 5–7, WB 4–5, CM 4–5, AM 4–6, ST 2–3 | One fewer or one more where the result is sensitive |
| P3 | Role weights ω | All equal to 1 | Weights that favour United's weakest roles |
| P4 | Depth weight μ | 0.2 | 0.1 and 0.3 |
| P5 | Purchase fee | 1.1 × market value | 0.9 × and 1.5 × |
| P6 | Sale receipt | 0.9 × market value | 0.7 × and 1.0 × |
| P7 | Quality score | Four components ranked within each role, weights below | Without the market-value component |
| P8 | Diego León | Wing-back, placeholder score at the 25th percentile of wing-backs | 10th and 50th percentile |

Already settled and not repeated here: £250m net budget, £100m fee ceiling, six arrivals, six sales, 3-4-2-1, the registration limits, the candidate pool (big five leagues, age 26 or under, 900 league minutes), role eligibility from five starts, candidate wage bands, neutral availability and no development bonus.

## P1. Wage cap W

**Proposal: W = £148m per year.**

The 24 existing players' wages add up to £133.38m a year, and the fixed arrival adds £1.30m, so the squad costs £134.68m before any decision. The proposal allows 10% above that.

Why not zero growth: four players are leaving on expiring contracts, and their wages are not in our table. A cap at exactly today's total would give the model no credit for the pay those four free up. Ten per cent (about £13.5m) is a stand-in for that room. It is a policy assumption, not a club figure.

Tested as well: £134.7m (the squad's wage total cannot grow at all) and no cap, which shows whether the wage limit changes the plan or only the transfer budget matters.

If the 2024/25 payroll table becomes available, the four leavers' actual wages can replace the 10% stand-in.

## P2. Players per role

**Proposal:**

| Role | Starters | Minimum | Maximum | United now (most likely role) |
|---|---:|---:|---:|---:|
| GK | 1 | 2 | 3 | 2 |
| CB | 3 | 5 | 7 | 6 |
| WB | 2 | 4 | 5 | 5 |
| CM | 2 | 4 | 5 | 4 |
| AM | 2 | 4 | 6 | 5 |
| ST | 1 | 2 | 3 | 3 |
| Total | 11 | 21 | 29 | 25 |

The minimum is about two players for every starting place, so each position has a replacement. The maximum stops the model from stacking one role. Each player is counted in one role only, so a versatile player cannot be double-counted as cover. The current 25 players (24 existing plus León) can be arranged to fit these bounds, so keeping everyone is a valid comparison case.

## P3. Role weights ω

**Proposal: every role has weight 1 in the base run.**

The objective adds up the quality of the eleven starters. A weak role already offers the largest gain from a new starter, so the model is drawn to weak roles without any extra weight. Adding weakness weights on top would count the same weakness twice.

Tested as well: a run where each role's weight is 1 plus its gap to the pool, to see whether the plan changes.

## P4. Depth weight μ

**Proposal: μ = 0.2.**

A squad player who does not start counts for one fifth of what a starter in the same role counts. This keeps the model from buying only eleven stars and filling the bench with anyone, but keeps starters clearly more important. With about 14 non-starters, total depth is worth roughly three starters.

Tested as well: 0.1 and 0.3.

## P5. Purchase fee

**Proposal: fee = 1.1 × the player's market value. A candidate whose fee comes out above £100m is unavailable in that run.**

Evidence from before the cutoff: for 459 transfers of players aged 26 or under into big-five clubs between June 2023 and May 2025 (fee and value both at least €5m), the fee divided by the market value at the time had a median of 1.12. A quarter of deals were below 0.88 and a quarter above 1.50. United's own ten purchases in that period had a median of 1.12.

Tested as well: 0.9 × (cheap market) and 1.5 × (expensive market, the upper quartile).

Not proposed for the base: an extra premium for buying from the other traditional top-six clubs. Their 35 sales in the data had a median ratio of 1.02, which does not support a premium. It can be run as a scenario if the team wants to show it.

Limits of this evidence: only completed deals are in the data, and a valuation can be updated after a move is rumoured.

## P6. Sale receipt

**Proposal: receipt = 0.9 × the player's market value.**

Evidence from before the cutoff: United's 13 sales with a fee between June 2023 and May 2025 had a median ratio of 0.97, but established first-team players mostly went for less than their value (ratios of 0.49, 0.60, 0.61, 0.71, 0.88, 0.95 and 0.97 for seven of them), while young academy players went for more. A discount of 10% is a middle course.

Tested as well: 0.7 × (buyers know United needs to sell) and 1.0 ×.

The model assumes a buyer exists at that price. A sale that might not happen is tested separately by blocking it and solving again.

## P7. Quality score

**Proposal: a score from 0 to 100 for each player in each eligible role, made of four components.**

| Component | What it measures | How it is computed |
|---|---|---|
| Playing time | How much the club relied on the player | League minutes divided by the minutes the club played |
| Output | What the player produced, suited to the role | ST and AM: goals plus assists per 90 minutes. WB and CM: the same. CB and GK: goals the team conceded per match the player started (fewer is better) |
| Team level | The standard of the team the player was in | The club's league points per match |
| Market value | What the statistics miss | Latest valuation before the cutoff |

Each component is turned into a percentile among all players in the pool who are eligible for that role (0 is the lowest, 100 the highest). The score is the weighted average of the four percentiles:

| Role | Playing time | Output | Team level | Market value |
|---|---:|---:|---:|---:|
| ST | 0.20 | 0.40 | 0.10 | 0.30 |
| AM | 0.20 | 0.40 | 0.10 | 0.30 |
| WB | 0.30 | 0.20 | 0.15 | 0.35 |
| CM | 0.30 | 0.15 | 0.15 | 0.40 |
| CB | 0.30 | 0.10 | 0.20 | 0.40 |
| GK | 0.30 | 0.10 | 0.20 | 0.40 |

Reasons for the weights: goals and assists say a lot about a striker and little about a centre-back, so output counts most for ST and AM. Goals conceded depend on the whole team, so that measure gets only 0.10. Where the statistics say little (CM, CB, GK), market value carries more of the score.

Other rules:

- **Two seasons.** 2024/25 counts 70% and 2023/24 counts 30%. A player with no 2023/24 record in the covered leagues is scored on 2024/25 alone.
- **Small samples.** A player with fewer than 900 weighted league minutes (or fewer than ten starts, for the goals-conceded measure) gets the middle value of 50 for output. This affects some of United's young players, not candidates.
- **A versatile player** has the same statistics in every role but is ranked against a different group in each, so the score differs by role.
- **Experience** is not a separate component. Two seasons of playing time and the team level already reflect it, and adding minutes again would count them twice.

Tested as well: the same score with the market-value component removed and the other weights scaled up. Market value also sets the fee, so this check shows how much the plan depends on it.

What this score cannot do: it has no expected goals, passing, defending or goalkeeping statistics. It is a coarse ranking, weakest for goalkeepers and defenders. United finished low in 2024/25, so its players score low on team level and, for defenders, on goals conceded. That may make the model keener to replace them than a fuller score would.

## P8. Diego León

**Proposal: role WB; quality at the 25th percentile of the wing-backs in the pool; wage £1.3m from the payroll table; no senior-list place needed.**

León is a fixed arrival, so the model must include this player, but there are no matches in the covered leagues to score. A low placeholder treats León as a depth player, which fits an 18-year-old joining from outside Europe. The fee (reported before the cutoff at about $4m, roughly £3.3m) is counted once as a fixed commitment in the budget.

Tested as well: the 10th and the 50th percentile.

## Planned runs once the settings are approved

One base run, then each of these on its own so that its effect can be read off:

1. No transfers at all (the comparison case).
2. Budget at £100m, £150m and £200m.
3. Purchase fee at 0.9 × and 1.5 ×; sale receipt at 0.7 × and 1.0 ×.
4. Wage cap at £134.7m and removed.
5. Depth weight at 0.1 and 0.3.
6. Quality score without market value.
7. Weakness-based role weights.
8. Cunha fixed as an arrival at £62.5m.
9. United's wages replaced by the candidate bands.
10. Each chosen signing blocked in turn, to find the next-best plan.
11. Each proposed sale blocked in turn.
