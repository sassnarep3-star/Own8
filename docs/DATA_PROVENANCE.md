# Data Provenance & Verification Log

Session `28cc78aa` · 2026-11-03. Every dataset used by this project is listed here with its
publisher, exact fetch location, SHA-256 (in `data/raw/manifest.json` after running
`scripts/fetch_data.py`), and verification status.

**Verification tiers used throughout this project**

| Tier | Meaning |
|---|---|
| `OFFICIAL` | Value confirmed against an NFL-owned source (nfl.com, operations.nfl.com, media.nfl.com, static.www.nfl.com, or the NFL's own GitHub org `nfl-football-ops`). |
| `DERIVED` | Statistic computed by this project's scripts from a named primary dataset. Reproducible via `scripts/analyze.py`. The underlying dataset's own tier applies to the inputs. |
| `PRIMARY (non-NFL)` | Value taken from a widely-used public primary-data mirror that is **not** NFL-owned. Flagged on the Flagged for Review page because no NFL-official source publishes it. |
| `UNVERIFIED` | Could not be confirmed from an official source → value left blank in tables and flagged. |

## Datasets

### D1 — `games.csv` (schedules, results, closing market lines)
- Publisher: Lee Sharpe / nflverse (`LeeSharpe/nfldata` on GitHub).
- Fetch: GitHub contents API → `data/games.csv` (2,188,275 bytes at fetch time).
- Coverage: 7,548 games, seasons 1999–2026 (2026 in progress: 272 scheduled, results filled through the current week).
- Fields used: `season, game_type, week, gameday, home_team, away_team, home_score, away_score, result, total, overtime, spread_line, total_line, home_moneyline, away_moneyline, home_spread_odds, away_spread_odds, over_odds, under_odds`.
- Tier: scores `PRIMARY (non-NFL)` cross-validated against OFFICIAL anchor D5 (91/91 games of the 2017 BDB sample — see `data/results/validation.json`); market lines `PRIMARY (non-NFL)` cross-checked against independent mirror D2. The NFL does not publish betting lines, so no official source exists for them; they are flagged as such, never presented as official.
- Source links: [repo](https://github.com/LeeSharpe/nfldata) · [file](https://github.com/LeeSharpe/nfldata/blob/master/data/games.csv)

### D2 — `nfl_lines_odds.csv.gz` (book-level opening & closing odds)
- Publisher: Sebastian Carl / nflverse (`mrcaseb/nfl-data` on GitHub).
- Fetch: GitHub contents API → `data/nfl_lines_odds.csv.gz` (2,596,471 bytes).
- Coverage: 479,089 book-level quotes (moneyline / spread / total) with `opening_lines` and closing `lines`, multiple books, from 2006 on.
- Tier: `PRIMARY (non-NFL)`. Used to cross-check D1 closing lines and to measure open→close line movement (CLV).
- Source links: [repo](https://github.com/mrcaseb/nfl-data) · [file](https://github.com/mrcaseb/nfl-data/blob/master/data/nfl_lines_odds.csv.gz)

### D3 — `game_passing_df.csv`, `game_receiving_df.csv`, `game_rushing_df.csv` (player-game stats)
- Publisher: Ryurko / nflscrapR (`ryurko/nflscrapR-data`, legacy data aggregated from NFL play-by-play).
- Fetch: GitHub contents API (7.5 MB / 37.2 MB / 5.6 MB).
- Coverage: player-game rows, GameIDs 2009091000–2017123115 (2009–2017 seasons).
- Tier: `PRIMARY (non-NFL)`; internal consistency checked (team passing yards vs team receiving yards per game, team points vs games.csv) — see `data/results/validation.json`.
- Source links: [repo](https://github.com/ryurko/nflscrapR-data) · [directory](https://github.com/ryurko/nflscrapR-data/tree/master/legacy_data/game_player_stats)

### D4 — `fdp2021/{1..18}.csv` (2021 weekly player fantasy stats, modern-era robustness sample)
- Publisher: Fantasy Data Pros (course datasets, `fantasydatapros/LearnPythonWithFantasyFootball`).
- Fetch: GitHub contents API, 18 weekly files, ~400 players/week with PassingYds/RushingYds/ReceivingYds/etc.
- Tier: `PRIMARY (non-NFL)`. Used only as a modern-era robustness check on correlations estimated from D3.
- Source links: [repo](https://github.com/fantasydatapros/LearnPythonWithFantasyFootball) · [directory](https://github.com/fantasydatapros/LearnPythonWithFantasyFootball/tree/master/2022/09-Correlation%20Matrices/01-Weekly%20Fantasy%20Stats%20-%202021)

### D5 — `bdb_official/games.csv`, `plays.csv`, `players.csv` (OFFICIAL NFL anchor)
- Publisher: **National Football League** — the NFL Football Operations GitHub organization (`nfl-football-ops`), Big Data Bowl repository (2019 competition, 2017-season sample of 91 games).
- Fetch: GitHub contents API.
- Tier: `OFFICIAL` — this is the NFL's own published data. Used to verify D1 game results line by line (91 games: date, home/away teams, final scores).
- Source links: [org](https://github.com/nfl-football-ops) · [repo](https://github.com/nfl-football-ops/Big-Data-Bowl) · [games.csv](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/master/Data/games.csv)

## Known gaps (flagged, not filled)

| Gap | Consequence | Disposition |
|---|---|---|
| No official NFL source publishes betting lines or prop lines | Market-line values cannot carry an `OFFICIAL` tier | All market values labeled `PRIMARY (non-NFL)`; flagged for review. |
| Historical player-prop lines are not publicly archived in any reachable primary source | Prop strategies are evaluated as **line origination** (model fairness/calibration), not as backtests against market prop lines | Explicitly labeled; no fabricated prop lines. |
| D3 covers 2009–2017 only | Correlations may differ in the modern passing environment | D4 (2021) used as robustness check; era caveat flagged. |
| 2026 season incomplete at analysis time | 2026 excluded from all backtests | Backtests use completed seasons only. |

## Reproducibility

```bash
python3 scripts/fetch_data.py   # re-download all raw data + sha256 manifest
python3 scripts/analyze.py      # recompute every DERIVED number in data/results/
python3 scripts/build_site.py   # regenerate the dashboard from data/results/
```
