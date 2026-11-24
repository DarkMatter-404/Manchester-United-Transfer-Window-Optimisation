# Hand-supplied inputs

## Wage source

The wages come from a browser printout of a public third-party payroll table, saved on 16 November 2026. It lists an estimated gross annual salary for each United player in the **2025/26** season. The printout is not included in this public copy because it is a third-party page; the page address is in the `source_url` column of `united_wages.csv`.

`united_wages.csv` was written from that PDF by `src/extract_united_wages.py`, which therefore cannot be rerun from this copy. In the original project it was run from the repository root:

```
python src/extract_united_wages.py
```

| Column | Meaning |
|---|---|
| `player_id`, `name`, `model_set` | From `docs/roster_reconciliation.csv`. `E` is an existing player, `K` the fixed arrival |
| `annual_wage_gbp` | Annual salary in pounds as printed in the table |
| `weekly_wage_gbp` | Annual salary divided by 52 |
| `gross_or_net` | `gross` |
| `season_of_figure` | Season the table refers to |
| `source_url`, `viewed_on` | Page address and the date it was viewed |
| `note` | Anything that needs care |

The model uses wages in GBP million per year: `annual_wage_gbp / 1_000_000`.

## What to keep in mind

- The table is from the season after the 31 May 2025 cutoff. A figure stands in for the wage at the cutoff only if the player's contract did not change in between. See `docs/decisions.md` item 3.7.
- Only players in the model get a wage here. The four players on loan at the cutoff are left out on purpose (`docs/decisions.md` item 3.6).
- The table's "loaned out" list is for 2025/26. Onana, Højlund, Collyer and Amass are on it but were at United at the cutoff, so they stay in the model.
- Wages printed for players United signed after the cutoff are not used.
- An empty wage is not treated as zero.
- A player missing from the PDF can be given a figure in `united_wages_hand_entered.csv`, with its season and source. Alejandro Garnacho's 2024/25 wage is entered there; the page it came from was not recorded.
