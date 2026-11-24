# Data check (plan Step 3)

Carried out on 16 November 2026 in one working session. The aim was to find out, for every coefficient in the model, whether it can be observed from data dated on or before 31 May 2025 or has to be estimated by a stated rule. Sources are listed in [source_register.csv](source_register.csv). Table and column definitions are in [data_dictionary.md](data_dictionary.md).

Nothing in this file is a model result. Section 4 lists the proposals as they stood after the check. The team's rulings on four of them, given later the same day, are in `decisions.md` Section 3.

## 1. What was tested

| Source | Test | Outcome |
|---|---|---|
| Transfermarkt datasets (dcaribou), individual `csv.gz` tables | Downloaded eight tables; read with every dated table cut at 31 May 2025 | Works. This is the main source |
| Premier League squad lists, 7 February 2025 | Read United's senior list and under-21 list | Works. Gives the senior list, home-grown marks and the under-21 list |
| Premier League squad-list rules | Read the 25 and 17 limits and the under-21 birth-date rule | Works |
| ECB reference rates | Euro to pound rate for the last week of May 2025 | Works. 0.8412 GBP per EUR on 30 May 2025 |
| Understat through the `soccerdata` package | Read 2024/25 player season statistics for one league | **Failed.** The site returned an error page and the package could not parse it. Not pursued further: we do not work around a site's access behaviour |
| ClubElo API | Ratings on 31 May 2025 | **Failed.** HTTP 502 on every attempt this session. Can be retried |
| Capology (wage estimates) | Open United's 2024/25 salary page | **Failed.** HTTP 403 for automated access |
| Spotrac (wage estimates) | Open United's 2024/25 payroll page | **Failed.** HTTP 402 (payment required) |

## 2. What the main source covers

The Transfermarkt dataset has match-level player records (minutes, goals, assists, cards), match lineups with the position each starter played, match results, dated market valuations and dated transfers. It has no expected-goals, passing, defensive-action, goalkeeping, injury, wage or contract-history data.

Match-level player records exist for 14 European first-tier leagues in both 2023/24 and 2024/25: England, Spain, Italy, Germany, France, Netherlands, Portugal, Belgium, Türkiye, Russia, Ukraine, Greece, Scotland and Denmark. In the big five leagues every league match has a lineup (for example 380 of 380 in England, Spain and Italy).

`src/prepare_inputs.py` builds four tables from these files. Checks on its output:

- 6,761 players had league minutes in 2024/25 in the 14 leagues. Player ids are unique.
- The latest dates read were 31 May 2025 (matches) and 30 May 2025 (valuations). The script stops if a later row is read.
- Missing fields among the 6,761 players: date of birth 1, main position 2, valuation before the cutoff 282 (4%), preferred foot 81, height 77.

Players who could be candidates under the agreed age rule (age 26 or younger on 31 May 2025, not at United):

| League group | Any league minutes | At least 900 minutes | ...with a valuation | ...valued at £100m or less | ...also played in 2023/24 |
|---|---:|---:|---:|---:|---:|
| Big five (England, Spain, Italy, Germany, France) | 1,503 | 814 | 808 | 795 | 650 |
| Netherlands, Portugal, Belgium | 1,034 | 515 | 514 | 514 | 343 |
| Türkiye, Russia, Ukraine, Greece, Scotland, Denmark | 1,445 | 611 | 604 | 604 | 402 |

By main role, with at least 900 minutes:

| | GK | CB | WB | CM | AM | ST |
|---|---:|---:|---:|---:|---:|---:|
| Big five | 35 | 171 | 137 | 183 | 194 | 94 |
| All 14 leagues | 105 | 389 | 343 | 426 | 472 | 205 |

Effect of the minutes threshold on the pool size (big five / all 14 leagues): 450 minutes 1,007 / 2,523; 900 minutes 814 / 1,940; 1,350 minutes 598 / 1,359; 1,800 minutes 422 / 862.

Among the 1,940, 58 have a latest valuation older than 1 December 2024.

Positions: the lineup data record the position each starter actually played. In the big-five pool of 814, 562 players have at least five starts in one role only, 233 in two roles, and 19 in three or more. The stored "main position" can disagree with where a player was used. Patrick Dorgu is stored as a left winger but started 44 matches in wide-midfield or full-back positions and 14 in advanced positions. Role eligibility should therefore come from starts, not from the stored label.

## 3. How each coefficient can be obtained

| Coefficient | Evidence available | Gap | Fallback |
|---|---|---|---|
| Sets E, D, excluded loans | Feb 2025 squad list; United appearances to the cutoff; dated transfer rows; dated club statements | Contract dates are not in the data. Players with no appearances are invisible in match data | Build the roster by hand from the squad list and dated reports; record evidence for every player |
| Set K (fixed arrivals) | Dated reports | Needs a team ruling for one player (Section 5) | Run both treatments |
| Eligible roles H | Starts by position, both seasons | None in the 14 leagues | Main-position role if a player has too few starts |
| Quality q | Minutes share, goals and assists per 90, team goals conceded in the player's starts, club points per game, dated market value | No expected goals, passing, defensive or goalkeeping statistics | A simple composite from what exists (Section 4.3) |
| Availability a | Share of club matches in which a player was in the matchday squad | Cannot tell injury from non-selection or suspension | a = 1 in the base; use the squad share only to review finalists |
| Development d | Minutes and output relative to players of the same age and role | Not yet defined | d not used (λ = 0) |
| Purchase fee f | Latest valuation before the cutoff, in euros, converted at 0.8412 | A valuation is an estimate, not an agreed price | Multiplier scenarios |
| Sale receipt r | Same | Same | Discount scenarios |
| Wage w | None accessible | No wage source could be read | A stated estimation rule (Section 4.5) |
| Home-grown h | Squad list marks for United | Not in the data for candidates | Candidates treated as not home-grown unless shown otherwise; finalists checked by hand |
| Senior registration t | Date of birth | None | Born on or after 1 January 2004 means no senior place is needed in 2025/26 |
| W, l, u, ω, μ | Policy choices | Team decision | Section 4 |

## 4. Proposals awaiting approval

These are suggestions from the data check. None has been used in a model run.

**4.1 Candidate leagues.** Use the big five leagues in the base. The match data are complete there and the level of play is broadly comparable, which matters because we have no league-strength rating. Other leagues would be recorded as an exclusion by coverage, not as a judgement on those players. A wider pool is possible as a sensitivity run but would mix leagues of different strength without an adjustment.

**4.2 Minutes threshold.** At least 900 league minutes in 2024/25 (ten full matches) for a candidate. Per-90 rates on fewer minutes are unreliable. Existing United players are never removed by this rule.

**4.3 Quality score.** For each role, rank players against the others eligible for that role (percentile, 0 to 100) on a few components and take a weighted average:

- playing-time share (league minutes divided by the minutes the club played), both seasons, with 2024/25 weighted more;
- an output measure that suits the role: goals and assists per 90 for ST and AM; assists per 90 for WB and CM with a lower weight; team goals conceded per start for CB and GK, also with a low weight because it depends on the whole team;
- club points per game, as a rough indicator of the level the player played at;
- the dated market value, as a disclosed stand-in for what the statistics miss, with more weight in roles where statistics are thin (GK, CB).

The weights are a team choice. The score would be tested with and without the market-value component, because that component also drives the fee.

**4.4 Role eligibility.** A player is eligible for a role with at least five starts in it across the two seasons. A player with no such role gets the role of the stored main position.

**4.5 Wages.** No wage source can be read automatically. Two options: (a) the team enters estimated wages by hand for the United squad from a source viewed in a browser, with the source and date recorded; (b) every wage is estimated by one rule from the dated market value, for example fixed weekly amounts for value bands. Option (b) treats United players and candidates the same way and is the suggested base. Under (b), the wage allowance W could be set as the estimated wage total of the first-team pool at the cutoff, including the players leaving on expiring contracts, so that the squad's wage total may not grow. Players out on loan are outside both the allowance and the model.

**4.6 Fees and receipts.** Fee = α × value and receipt = β × value, with α in {1.0, 1.2, 1.5} and β in {0.7, 0.9, 1.0} as scenarios, and a base to be chosen.

**4.7 Team strength.** Use club points per game from the match data. ClubElo can replace it if the API comes back.

## 5. Roster evidence found so far

Collected for Step 4. Each line gives the date the information was public.

| Player | Status at the cutoff | Evidence |
|---|---|---|
| Christian Eriksen, Victor Lindelöf, Jonny Evans | Leaving at contract expiry (set D) | Club statement after the last league match on 25 May 2025, reported by [ESPN](https://africa.espn.com/football/story/_/id/45479270/man-united-release-victor-lindelof-christian-eriksen-jonny-evans) and [Fichajes, 26 May 2025](https://www.fichajes.net/en/news/manchester-united-makes-official-its-first-3-departures-20250526.html) |
| Tom Heaton | Contract ending June 2025; a new deal was announced only after the cutoff, so set D under the no-renewal rule | Earlier one-year extension reported [2 July 2024](https://www.beinsports.com/en-us/soccer/premier-league/articles/man-utd-back-up-goalkeeper-heaton-pens-one-year-contract-extension-2024-07-02); new deal reported [27 June 2025](https://prod.beinsports.com/en-au/football/premier-league/articles/heaton-handed-one-year-extension-at-united-2025-06-27) |
| Dermot Mee | On the February 2025 senior list; contract status not found | To verify |
| Marcus Rashford | On loan at Aston Villa (excluded) | [Aston Villa, 2 February 2025](https://avfc.co.uk/news/2025/february/02/villa-announce-marcus-rashford-loan-signing); transfer row dated 2 February 2025 |
| Antony, Tyrell Malacia, Jadon Sancho | On loan at Real Betis, PSV and Chelsea (excluded) | Transfer rows dated 25 January 2025, 4 February 2025 and 30 August 2024, and appearances for those clubs up to the cutoff. Club announcements still to be cited |
| Diego León | Arrival agreed before the cutoff (set K) | Agreement reported in December 2024 for a move in summer 2025, initial fee about $4m plus add-ons ([report](https://ca.sports.yahoo.com/news/fabrizio-romano-man-utd-reach-083500893.html)). Confirmed by the club in July 2025 at an initial £3.3m |
| Matheus Cunha | **Needs a team ruling.** Reports dated 27 and 28 May 2025 say United met the £62.5m release clause and Wolves gave permission for a medical ([Sky Sports](https://www.skysports.com/football/news/12040/13375623/matheus-cunha-transfer-brazilian-set-for-manchester-united-medical-after-wolves-62-5m-release-clause-terms-met), [RTÉ, 27 May 2025](https://www.rte.ie/sport/soccer/2025/0527/1515294-manchester-united-close-in-on-l62-5m-cunha-deal)). The club's own statement came on [1 June 2025](https://www.irishtimes.com/sport/soccer/2025/06/01/manchester-united-confirm-agreement-to-sign-matheus-cunha-from-wolves), one day after the cutoff | Fixed arrival or ordinary candidate |

## 6. Exposure to later information

The searches for roster evidence returned some news from after the cutoff, including later transfers of United players. No 2025/26 match or performance data were opened. Nothing from those results is used as a decision input. See `decisions.md` item 5.1.
