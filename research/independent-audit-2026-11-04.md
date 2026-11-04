# Independent audit — 4 November 2026

## Executive summary

**Status: not validated; do not use the existing candidate picks or rankings for wagering.** The repository contains useful historical captures and a static dashboard, but its automated verification compares two local copies, not each cell with the NFL. The present audit is a targeted review, not a line-by-line verification of the whole repository. No strategy has demonstrated out-of-sample skill. Randomness cannot be eliminated from NFL outcomes; repeated prospective trials and uncertainty intervals can reduce the risk of mistaking luck for skill.

## Checks against official sources

| Item | Finding | Official source |
| --- | --- | --- |
| Buffalo and New England standings | The W-L-T, PCT, PF, PA and NET in the local Week 8 JSON match the official page at review time. Other rows were not independently checked in this audit. | [NFL standings](https://www.nfl.com/standings/) |
| CIN at ATL | NFL identifies this Week 9 game as played in Madrid at Bernabéu. The model nevertheless applies its ordinary home-field adjustment. No neutral-site estimate is verified. | [NFL game center](https://www.nfl.com/games/bengals-at-falcons-2026-reg-9) |
| Rams at Washington venue | The JSON says FedEx Field; NFL's game center says Northwest Stadium. The JSON value is incorrect. | [NFL game center](https://www.nfl.com/games/rams-at-commanders-2026-reg-9) |
| Week 9 injuries | The report now exists, including practice participation for Jacksonville and Baltimore. Blank game status is not evidence that a player will play. The site's assertion that the report has not been published is stale. | [NFL injury report](https://www.nfl.com/injuries/league/2026/reg9) |
| Jalen Hurts | NFL reports that he is expected to miss the remainder of the 2026 season and cites the team's statement. This does not establish the numerical effect on a model. | [NFL news](https://www.nfl.com/news/eagles-qb-jalen-hurts-out-2026-season-blood-clots) |
| Support | NCPG lists 1-800-MY-RESET for calls and texts. | [NCPG](https://www.ncpgambling.org/help-treatment/) |

## Critical irregularities requiring review

| ID | Finding | Evidence / official context |
| --- | --- | --- |
| A-01 | `model_spread_home` is home score minus away score, but a conventional home handicap is the opposite sign. The script subtracts the handicap instead of adding it; a +3 projected home margin and a -3 home handicap should give zero difference, not six. The displayed spread also labels a favored team with a plus sign. The existing candidate list is invalid. | [NFL schedule (game context)](https://www.nfl.com/schedules/2026/by-week/week-9); `scripts/analyze.py` |
| A-02 | Unverified third-party spreads enter `edge_pts`, and `G6` can pass despite `market_verified` being false. Conditional injury gates count as passing. Stake and freshness gates are hard-coded and do not verify actual stakes or current timestamps. | [NFL injuries](https://www.nfl.com/injuries/league/2026/reg9); `scripts/analyze.py` |
| A-03 | Cross-sectional team-season correlations cannot establish correlations between bet outcomes or player prop legs. Different games are not independent by construction. There is no empirical joint-outcome sample, correlation confidence interval, or tested same-game joint pricing. | [NFL team statistics](https://www.nfl.com/stats/team-stats/); `scripts/analyze.py` |
| A-04 | The leaderboard assigns ranks in source-code order, and zero realized points before any grading; no score ingestion or settlement logic is present in the analysis script. The claimed automated competition and grading are not implemented. | [NFL scores](https://www.nfl.com/scores/2026/week-8); `scripts/analyze.py` |
| A-05 | `verify_combined.py` checks local capture against local capture and checks arithmetic. Agreement is not independent official-source verification, and cannot establish source provenance or correct labels. Site link checker tests local existence and host names, not external HTTP availability or table-cell correctness. | [NFL standings](https://www.nfl.com/standings/); `scripts/verify_combined.py`, `scripts/check_links.py` |
| A-06 | Player association is built with a dictionary keyed by team; multiple QBs on one team overwrite one another in input order. No starting-QB confirmation or availability gate is applied. | [NFL player stats](https://www.nfl.com/stats/player-stats/); `scripts/analyze.py` |
| A-07 | The site and documentation claim no manual input, weekly recomputation, elimination of luck, and full line-by-line verification. Static captured inputs are not automatically refreshed; these claims are unsupported. | [NFL standings](https://www.nfl.com/standings/); `README.md`, `research/` |
| A-08 | The local schedule and injury snapshot have a wrong venue and stale injury claim respectively; the rest of the data is not certified by this audit. Historic source links may change and are not archived evidence. | [NFL game center](https://www.nfl.com/games/rams-at-commanders-2026-reg-9), [NFL injury report](https://www.nfl.com/injuries/league/2026/reg9) |

## Proposed validation gates (design, not completed or passed)

1. Timestamp and retain official input snapshots, per-cell source provenance, and independent checks; leave unverified input values blank. Lock all forecasts and prices before kickoff.
2. Use an explicit home-margin convention; handicap = negative projected home margin. Treat neutral sites separately and validate any venue adjustment out of sample. Require verified participant availability.
3. Capture timestamped directly sourced sportsbook prices and settlement rules where lawful; absent these, leave edges and wagering recommendations blank. Model projections are estimates, not official values.
4. Evaluate spread/total forecasts using chronological, rolling-origin splits without leakage; retain a final untouched test period. Compare against prespecified baselines and report calibration, log loss or Brier score, sample counts and uncertainty intervals. Avoid declaring skill from a short or selectively chosen sample.
5. For parlay and prop combinations, estimate dependence from matched historical **leg outcomes**, accounting for pushes, voids and shared games; require adequate sample sizes and uncertainty bounds. Until then, block all combinations rather than asserting independence or substituting team-level correlations.
6. For a leaderboard, preregister strategies, freeze submissions, settle from authoritative results and verified rules, report sample sizes and uncertainty, account for multiple comparisons, and award only after minimum sample and holdout requirements. No actual rankings or rewards exist yet.

## Delivery limitation

Prior dashboard and generated artifacts remain historical and contain known errors. They should not be presented as validated or deployed unchanged. Further source-by-source verification, implementation, independent tests and a complete rebuild are required before a safe integration or Pages deployment. This report does not assert that every source URL was live-tested or every repository row audited.
