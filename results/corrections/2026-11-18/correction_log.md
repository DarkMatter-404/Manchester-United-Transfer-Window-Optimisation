# Correction log, 18 November 2026

This folder holds a **post-freeze correction** of the project. The recommendations were frozen on 17 November 2026 (`aman/results/freeze/`) and evaluated the same day (`aman/results/evaluation/`). A review of that version (commit `d3c86de`) found errors. The team approved the corrections below on 18 November 2026.

The original freeze and evaluation files were checked against their recorded hashes before any change and again afterwards; none was modified (`original_file_hashes.txt`, `before_after.md` Section 1). The corrected runs here were made after the 2025/26 outcomes had been examined. They are a correction of how the agreed rules were carried out, not a new recommendation frozen before outcomes were seen. No rule, weight, limit or score was changed, and nothing was adjusted to favour players who did well in 2025/26.

All figures below are taken from `before_after.md`, which is generated from the files.

## A. Club identity in the two-year rule

**Issue.** The code decided whether a youth or reserve side belonged to a club by comparing names: any shared substring, or the same first four letters of the first word, counted. Unrelated clubs could be joined. Jon Aramburu was treated as being at Real Sociedad since 20 July 2022, the date he joined Real Unión, because both names begin with "Real". In the other direction, a club's own youth side with a shortened name ("FC Bayern II", "RM Castilla", "Celta Vigo B") was not recognised, so a promotion from it was read as a new signing.

**Correction.** Clubs are identified by id. A side belongs to a senior club only if its name is exactly one of the senior club's recorded names followed by a youth or reserve ending, or if it is listed in the reviewed table `docs/club_aliases.csv` (42 entries, each with a reason). The resulting table of sides is written to `data/processed/club_family.csv`. The start of a spell is then worked out within that club organisation. The existing distinctions are kept: a new signing after an earlier spell, a loan return, a loan made permanent, a move up from the club's own youth side, and a signing from another club's youth side.

**Evidence.** Aramburu's transfer records show Real Unión to Real Sociedad B on 1 August 2023, confirmed by Real Unión's announcement on that date: <https://realunionclub.com/jon-mikel-aramburu-no-continuara-en-el-real-union/>. The alias table was built by listing every move into a pool player's club from a side the exact rule did not link, and checking each name by hand.

**Effect.** 17 candidates changed status. Aramburu is now excluded. Fifteen academy players are now eligible, because their promotion from a short-named youth side is no longer read as a recent signing. Juanma Herzog is eligible on dated evidence. Overall, eligible candidates rose from 314 to 329.

## B. Repeatable input builds

**Issue.** A club's short name was taken from an unordered `SELECT DISTINCT`, so rebuilding the inputs could pick a different alias. Moves on the same day were in no fixed order. In the review's rebuild, 12 players' joining fields and two pool rows changed.

**Correction.** Aliases are no longer used in that way; all of a club's recorded names are read in a fixed order. Same-day moves are put into the chain they form (each move starts where the previous one ended). A day whose moves cannot be put in a single chain is flagged, and the player is "not verified" rather than guessed. Choices that could tie (main club, club at the cutoff, latest valuation) now have an explicit tie-break. There were no such ties in the data.

**Effect.** `src/check_repeatability.py` builds the inputs twice; all 11 output files are byte-for-byte identical (`check_logs/check_repeatability.txt`). One player in the data has a same-day pair that cannot be ordered (Fer López); he is not a candidate.

## C. Undated academy players

**Issue.** A candidate who came through a club's youth system with no recorded entry date was accepted automatically. That is broader than the written rule that an unknown spell is not eligible.

**Correction.** The exact entry date is not needed if a dated record shows the player in the club's organisation before 1 June 2023. Such a record can be a move between the club's own sides, a move out of the club (for example on loan), or a match for the club. Without such a record the case is "not verified" and excluded. Destiny Udogie's documented joining date (`docs/joining_date_overrides.csv`) agrees with the records now that same-day moves are ordered.

**Effect.** 7 candidates remain not verified, all valued between £0.25m and £4.2m. Three have records at a different club, which suggests an unrecorded loan; four have no transfer record. They stay excluded.

## D. Wages in club-price scenarios

**Issue.** Fee-only runs held wages fixed, but the wage reference still used the run's own club lists. Removing the club rules also lowered 25 candidates' wages.

**Correction.** A candidate's wage always comes from the complete base fee rule, for every run except those named "combined fee and wage". This also applies to candidates who are available only in a scenario.

**Effect.** Checks confirm that no wage changes in the fee-only runs or in two club-price runs, including 13 candidates who become available only when the club rules are removed (`check_logs/check_logic.txt`). The club-rules run chooses the same plan as before.

## E. Evaluation of players who changed clubs

**Issue.** The evaluator added a player's league minutes for all clubs and divided by the matches of the club where the player played most. It labelled the row with that club.

**Correction.** Outcomes are kept player by player and club by club (`evaluation/player_club_outcomes.csv`). Each club's share uses that club's minutes and that club's league matches. The one-line summary per player uses only the main club: the club with the most league minutes, then most starts, then the smaller club id. Season totals across clubs are in separately named columns. Player ids are in every output.

**Effect.** Three shares changed (computed from the source files): Hincapié 55.0% → 52.4% (Arsenal), Guessand 26.8% → 17.2% (Aston Villa), and Lammens 94.7% → 84.2% (United). `src/check_evaluation.py` recomputes every club row from the raw match records; all 14 checks pass.

The pre-cutoff playing-time input to the quality score uses a similar proxy: a player's league minutes for all clubs in a season divided by the matches of the main club. It is described as such in `docs/assumptions.md`. It was not changed, because the frozen scores must stay as they were. Changing it would be a separate, labelled analysis.

## F. Evaluation summaries

**Issue.** The frozen evaluation plan names averages and counts. The report showed medians instead, chosen after the outcomes were known. Goals plus assists were averaged across mixed roles. Two players appear in two groups each, so 32 memberships cover 30 players; this was not stated. The code used 2 September 2025 as the end of the window, against 1 September in the plan. It also defined actual signings as moves with a positive fee.

**Correction.** Means and counts are reported first, with valid-observation counts and distinct-player counts. Medians appear next to them, labelled as added after the evaluation. Goals plus assists are shown per player, not averaged across roles. The window ends on 1 September 2025. The comparison group comes from a reviewed list of all 16 moves into United's organisation in the window (`docs/actual_united_arrivals_2025.csv`), classed as loan returns, moves between United's own sides, an arrival into the under-21 side, and permanent arrivals into the senior squad. Only the last class forms the group; the evaluator stops if any move in the records is missing from the list.

**Effect.** The comparison group is unchanged: Cunha, León, Mbeumo, Šeško and Lammens. The source lists the five arrivals with fees and describes no loan, but uses the word "permanent" only implicitly (a five-year deal for Lammens).

## G. Safeguards for the freeze

**Issue.** The freeze script could overwrite the existing freeze. The evaluator checked only that a manifest existed. The run instructions presented freezing as part of a normal rerun.

**Correction.** `src/output_paths.py`: runs and evaluations write only to a folder given with `--out`, which may not be inside the original results except under `results/corrections/`. `freeze_results.py` refuses any folder that already exists. `evaluate_results.py` checks every frozen file against the freeze manifest and stops on a mismatch; this was tested on an altered copy. The README separates rerunning the analysis from making a new freeze.

## H. Bounded shortlist review

The six frozen signings and the plan B player in each role were reviewed for ownership and current spell, commitments before the cutoff, contract or free status, and registration (`shortlist_review_2026-11-18.csv`). Remaining gaps:
- Commitment status is not verified for 4 of the 12 (Éderson, David, Colwill, Leão).
- Contract status is not verified for 1 (Bulka).
- Where a later move was found, the finding reads "no pre-cutoff commitment established from the sources reviewed"; a later announcement does not prove that nothing was agreed earlier.
- Two contract findings rest on reports written after the cutoff (Doan, Éderson) and are labelled so.

The frozen shortlist review is unchanged; the other 12 shortlisted players keep its labels. The corrected run's own shortlist table differs from the original only in the column that repeats the spell evidence; all 24 shortlisted players remain eligible.

## I. Did the recommendation change?

No. All 56 runs return the same transfers, objective, spending and wages as the original runs, although 15 more candidates are available in each. The base plan, the starting eleven, the direct alternatives and the alternative full plans are identical (`before_after.md` Sections 4 and 5).

## Later information seen during this correction

Searches for contract and commitment evidence returned reports from after the cutoff, including later transfers of shortlisted players and a report of a failed move to United in 2026. They were used only to date the absence of an earlier agreement or to read a contract term in force before the cutoff. None is a model input.
