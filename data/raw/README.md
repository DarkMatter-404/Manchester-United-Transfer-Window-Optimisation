# Raw data

The pipeline reads eight tables of the public [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) project by dcaribou, released under the CC0-1.0 licence. The snapshot used in this project was downloaded on 16 November 2026 (file host last modified 5 September 2026). The dataset is updated over time, so a fresh download may differ from the snapshot used here.

The eight files (about 185 MB) are too large for the repository and are attached to the GitHub release **`data-v1`** of this repository. Put them in `data/raw/transfermarkt/` and check them against `SHA256SUMS.txt`:

```bash
gh release download data-v1 --dir data/raw/transfermarkt --pattern "*.csv.gz"
cd data/raw/transfermarkt && shasum -a 256 -c SHA256SUMS.txt 2>/dev/null   # the last line of the file is the download date
```

| File | Used for |
|---|---|
| `players.csv.gz` | Player profiles (birth date, stored position, citizenship) |
| `player_valuations.csv.gz` | Dated market values; the latest one on or before 31 May 2025 is used |
| `appearances.csv.gz` | League minutes, goals and assists by match |
| `game_lineups.csv.gz` | Starting line-ups and positions, used for role eligibility |
| `games.csv.gz` | Match results, used for team level and goals conceded |
| `clubs.csv.gz`, `competitions.csv.gz` | Club and league identifiers |
| `transfers.csv.gz` | Dated transfers, used for the two-year rule and club spells |

Every dated table is cut at 31 May 2025 when the model inputs are built. The same files also hold the 2025/26 records used only for the later evaluation. The processed inputs in `data/processed/` are already included, so the optimisation can be run without the raw files.
