# Own8 — NFL Lines Project

Originate, validate, and track NFL betting-line strategies (single bets, parlays, player-prop combos) as a leaderboard competition. Every strategy passes six validation gates before a signal is released; correlation between legs is measured and documented. No manual inputs. All data traced to official verified sources or left blank and flagged.

## Live site
GitHub Pages: https://sassnarep3-star.github.io/Own8/ (enabled after merge to main — see COORDINATION.md for the PR/deploy record)

## Site structure (static, repo root `site/`)
- `index.html` — Dashboard landing page
- `pages/executive-summary.html` — Executive summary
- `pages/single-bets.html` — Single-bet strategies
- `pages/parlays.html` — Parlay strategies
- `pages/player-props.html` — Player-prop combos
- `pages/validation-gates.html` — Six validation gates + per-strategy results
- `pages/correlations.html` — Pearson correlation values
- `pages/standings-data.html` — 32-team 2026 NFL regular-season standings (verified)
- `pages/flagged-for-review.html` — Unverified items + irregularities
- `pages/sources.html` — Official source register

## Data (repository root)
- `data/nfl-2026-standings.csv` — 32 teams, 2026 REG, source: https://www.nfl.com/standings/ (fetched 2026-11-03, verified cell-by-cell)
- `data/nfl-2026-passing.csv` — QBs, source: https://nextgenstats.nfl.com/stats/passing/2026/REG/1 (flagged UNVERIFIED — see IR-01)
- `data/nfl-2026-rushing.csv` — RBs, source: https://nextgenstats.nfl.com/stats/rushing/2026/REG/1 (flagged UNVERIFIED — see IR-01)
- `data/nfl-2026-receiving.csv` — WRs/TEs, source: https://nextgenstats.nfl.com/stats/receiving/2026/REG/1 (flagged UNVERIFIED — see IR-01)
- `data/correlations.md` + `compute_correlations.py` — Pearson r computation method and results
- `data/strategies.md` — Strategy definitions, rules, gate results
- `data/sources.md` — Full source register

## Verification standard
Every table row carries a source link to an official site. If a value cannot be confirmed from an official source, it is left blank and flagged UNVERIFIED on the Flagged for Review page. Nothing is inferred or filled in.

## Coordination
`COORDINATION.md` is the shared task board (claims, statuses, sources, irregularities, PR/deploy record).

## Disclaimer
Not gambling or financial advice. Analytical framework and verified public NFL data only. Betting lines/odds are not published by the NFL.
