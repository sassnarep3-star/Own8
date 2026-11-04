# Official Sources — Own8 NFL Lines Project

All data on this site was fetched from the following official, verified sources on 2026-11-03. No values were inferred or filled in. Any value that could not be confirmed from an official source is left blank and flagged as UNVERIFIED on the Flagged for Review page.

| # | Source | URL | Data retrieved | Use on site |
|---|--------|-----|----------------|-------------|
| 1 | NFL.com — Standings | https://www.nfl.com/standings/ | 2026 Regular Season standings, all 32 teams (W-L-T, PCT, PF, PA, net points, home/road/division/conference records, streak), fetched 2026-11-03 | Team standings tables; team-level correlation inputs |
| 2 | NFL Next Gen Stats — Passing Leaders | https://nextgenstats.nfl.com/stats/passing/2026/REG/1 | 2026 Regular Season passing leaders (attempts, yards, TDs, INTs, passer rating, completion %) | Quarterback context for player-prop strategy design |
| 3 | NFL Next Gen Stats — Rushing Leaders | https://nextgenstats.nfl.com/stats/rushing/2026/REG/1 | 2026 Regular Season rushing leaders (attempts, yards, avg, TDs, yards over expected) | Running-back context for player-prop strategy design |
| 4 | NFL Next Gen Stats — Receiving Leaders | https://nextgenstats.nfl.com/stats/receiving/2026/REG/1 | 2026 Regular Season receiving leaders (targets, receptions, catch %, yards, TDs, YAC/rec) | Wide receiver / tight end context for player-prop strategy design |
| 5 | NFL.com — Tie Breaking Procedure | http://www.nfl.com/standings/tiebreakingprocedures | Standings tie-break reference (linked from NFL.com standings page) | Methodology reference only |
| 6 | NFL Next Gen Stats — Glossary | https://nextgenstats.nfl.com/glossary | Next Gen Stat definitions | Methodology reference only |

## Items NOT available from official NFL sources (left blank, flagged UNVERIFIED)

- Betting odds, lines, spreads, totals, implied probabilities — NFL.com does not publish betting lines; these come from sportsbooks, which are not official NFL sources. Every odds-dependent field in strategy tables is blank until a verified odds source is added.
- Injury / player availability reports — not fetched in this session; every availability-dependent gate is blank/unverified.
- Historical game-by-game results beyond the current standings snapshot — not available from the official sources above; backtest win rates are blank/unverified.
- Correlation values requiring game-by-game data — approximated from season-aggregate standings and player stats where possible (see data/correlations.md); full game-level correlations are blank/unverified.

## Verification standard

Every table row on the site carries a source link. If a value cannot be confirmed from an official source, it is left blank and the row is flagged UNVERIFIED on the Flagged for Review page. Nothing is inferred.
