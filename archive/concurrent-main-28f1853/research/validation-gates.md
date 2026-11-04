# Validation Gates — every strategy must pass before it can appear as a candidate

| Gate | Rule | Data source | Week 9 status (as of 2026-11-03) |
| --- | --- | --- | --- |
| **G1 — Official sources only** | Every input row must link to an official source (nfl.com, nextgenstats.nfl.com, team sites, official regulator). Third-party values never enter a verified table. | `data/sources.json` | PASS — all inputs captured from official domains 2026-11-03 |
| **G2 — Freshness ≤ 7 days** | Standings/stats must be from the most recent completed week (≤ 7 days old). | nfl.com standings/scores timestamps | PASS — through Week 8 (final 2026-11-02) |
| **G3 — Sample size ≥ 4 games** | Both teams ≥ 4 games played (avoids tiny-sample noise). | nfl.com standings | PASS — all teams 7–8 GP |
| **G4 — Injury & news check** | Check the latest **published** official injury report + official nfl.com news; adjust (e.g., QB change, WR out). Re-check when the next report publishes. | https://www.nfl.com/injuries/ · nfl.com news | CONDITIONAL — W9 report not yet published (F-04); W8 report + Hurts/McLaurin news applied |
| **G5 — Correlation check** | Multi-leg bets: pair correlation must satisfy the correlation policy (see `correlation-policy.md`). Same-game correlated combos blocked by default. | `analysis/correlations.json` | PASS for singles; enforced for S6/S7 |
| **G6 — Edge vs market, sanity band** | Candidate requires `1.0 ≤ |model − market| ≤ 8.0` points. Market input, where used, is unverified third-party (F-05) and must be re-verified at a licensed sportsbook. No market line → NOT_COMPUTABLE (blank), never estimated. | `data/market-lines.json` (unverified) | Updated 2026-11-04: all 15 games NOT_COMPUTABLE (market input is unverified third-party, F-05); 0 candidates. Earlier build wrongly marked 2 candidates PASS (F-23). |
| **G7 — Stake cap** | ≤ 2% of bankroll per single, ≤ 1% per parlay (Kelly-style; assumption F-07). | framework | PASS (rule enforced in grading) |

A strategy that fails any gate is **not published as a candidate** — it is logged with the failing gate instead. "Needs review" items are published on the Flagged for Review page and block nothing.
