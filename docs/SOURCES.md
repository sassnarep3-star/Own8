# Sources Registry

Every factual claim published by this project links to one of the sources below.
Tier definitions: see `docs/DATA_PROVENANCE.md`. Verification date for all OFFICIAL
sources: **2026-11-03** (fetched and read directly by session `28cc78aa`).

## Official NFL sources (tier OFFICIAL)

| ID | Source | What it verifies | URL |
|---|---|---|---|
| O1 | 2026 NFL Official Playing Rules (rulebook PDF, media.nfl.com) | Scoring values (Rule 11-1-2), Try spots (11-3-1), game length (4-1-1), overtime procedures (16-1), field dimensions (1-1), 11 players (5-1-1), 2026 rule changes (cover) | https://media.nfl.com/content/dam/communications/Official%20Playing%20Rules/2026%20Official%20Playing%20Rules.pdf |
| O2 | 2026 NFL Rulebook — operations.nfl.com | Same rulebook, canonical web edition incl. 2026 rule-change table | https://operations.nfl.com/rules-officiating/2026-nfl-rulebook/ |
| O3 | Approved 2025 Playing Rules, Bylaws and Resolutions (NFL Football Communications, Apr 1 2025) | 2025 OT alignment (both teams possess, 10-min regular-season OT), dynamic kickoff made permanent, touchback to 35, roster cut to 53 with 2 return designations | https://media.nfl.com/football-information/2025/approved-2025-playing-rules--bylaws-and-resolutions |
| O4 | NFL.com — "NFL moves extra point to 15-yard line for 2015 season" (May 19 2015) | PAT kick from the 15 (33-yd attempt), 2-pt try from the 2, defense may score 2 on Try returns | https://www.nfl.com/news/nfl-moves-extra-point-to-15-yard-line-for-2015-season-0ap3000000493347 |
| O5 | NFL.com — "What you need to know about enhanced NFL schedule featuring 17 regular-season games per team" | 17-game regular season adopted for 2021 (owners' vote) | https://www.nfl.com/news/what-you-need-to-know-nfl-schedule-17-regular-season-games |
| O6 | NFL.com — "Collective Bargaining Agreement" (2020) | 14-team playoffs from 2020 (7 per conference); gameday active roster 48 | https://www.nfl.com/news/collective-bargaining-agreement |
| O7 | NFL Football Operations GitHub — Big Data Bowl (`nfl-football-ops/Big-Data-Bowl`) | Official 2017-season game results (91-game sample) used to verify D1 line by line | https://github.com/nfl-football-ops/Big-Data-Bowl/blob/master/Data/games.csv |
| O8 | 2025 NFL rules changes — operations.nfl.com | 2025 dynamic kickoff + overtime summaries | https://operations.nfl.com/the-rules/rules-changes/2025-rules-changes |

## Primary data mirrors (tier PRIMARY (non-NFL))

| ID | Source | Contents | URL |
|---|---|---|---|
| D1 | LeeSharpe/nfldata `games.csv` | 1999–2026 schedules/results + closing market lines | https://github.com/LeeSharpe/nfldata/blob/master/data/games.csv |
| D2 | mrcaseb/nfl-data `nfl_lines_odds.csv.gz` | Book-level opening/closing odds, 2006→ | https://github.com/mrcaseb/nfl-data/blob/master/data/nfl_lines_odds.csv.gz |
| D3 | ryurko/nflscrapR-data legacy game player stats | Player-game passing/receiving/rushing, 2009–2017 | https://github.com/ryurko/nflscrapR-data/tree/master/legacy_data/game_player_stats |
| D4 | fantasydatapros course data, 2021 weekly | 2021 weekly player stats (robustness sample) | https://github.com/fantasydatapros/LearnPythonWithFantasyFootball/tree/master/2022/09-Correlation%20Matrices/01-Weekly%20Fantasy%20Stats%20-%202021 |

## Research literature (strategy methodology; tier RESEARCH)

Used to design validation gates and luck-vs-skill methodology. These are peer-reviewed
or primary research publications, not NFL sources; they justify *method*, never fill
data values.

| ID | Reference | Relevance | URL |
|---|---|---|---|
| R1 | Levitt, S. (2004), "Why are gambling markets organised so differently from financial markets?", Economic Journal 114(495) | Bookmaker bias exploitation; market-efficiency framing | https://doi.org/10.1111/j.1468-0297.2004.00207.x |
| R2 | Štrumbelj, E. (2014), "On determining probability forecasts from betting odds", International Journal of Forecasting 30(4) | Removing vig; odds→probability conversion | https://doi.org/10.1016/j.ijforecast.2014.02.008 |
| R3 | Mauboussin, M. (2012), *The Success Equation: Untangling Skill and Luck in Business, Sports, and Investing*, Harvard Business Review Press, ISBN 9781422184233 | Skill/luck decomposition framework (paradox of skill) | https://books.google.com/books/about/The_Success_Equation.html?id=Qb4qSoJ6B40C |
| R4 | Moskowitz, T. (2021), "Asset Pricing and Sports Betting", Journal of Finance 76(6), 3153–3209 | Momentum/mispricing exists in betting markets but returns fail to overcome transaction costs — core motivation for CLV-based validation | https://doi.org/10.1111/jofi.13082 |
