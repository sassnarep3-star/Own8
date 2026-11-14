# Session 1052cf22 — final integration verification record (2026-11-14)

Scope: root integration/publication surface (see this session's section of `COORDINATION.md`).
This directory holds this session's own verification evidence only. The user-facing result is on
the live dashboard (<https://sassnarep3-star.github.io/Own8/>) in the **Operator requirement
coverage** table on the
[executive summary](https://sassnarep3-star.github.io/Own8/pages/executive-summary.html).

## Live official re-reads (2026-11-14)

| Check | Official source | Result |
| --- | --- | --- |
| Week 10 Thursday final (WAS 24 – NYG 21, Nov 12) | <https://www.nfl.com/scores/2026/week-10> | MATCH |
| League standings W/L/T/PCT/PF/PA/NET/STRK, 191 cells across 24 teams | <https://www.nfl.com/standings/league/2026/REG> | 0 mismatches |
| Week 10 slate (14 games, times, networks, 4 byes) | <https://www.nfl.com/schedules/2026/by-week/week-10> | MATCH |
| Scores-page team records (15 teams incl. ties) | <https://www.nfl.com/scores/2026/week-10> | 15/15 MATCH |

## Checker replay on the integrated tree

All PASS: root (`audit_repo`, `analyze`, `test_audit`, `tests/`, `build_site`, `check_links`
40 pages / 3,029 links / 2,185 rows / 0 errors, `audit_publication` 61 HTML / 1,233 URLs),
requirements CI replay (byte-identical regeneration), ledger (22 checks + 23 unit tests),
origination (15 pages, 0 failures), correlation-audit (8 tests), signals (115/115),
decision-review (7 pages). Machine record: [`verification.json`](verification.json).

## Operator requirement coverage — all eight features published

| # | Requirement | Where | Status |
| --- | --- | --- | --- |
| 1 | Price-snapshot store (open + close per originated market) | `ledger/price-store.html`, `market/pages/prices.html` | PUBLISHED — ledger 0/78 blank fail-closed (LF-01); market/ holds locked nfl.com picks-article lines (W9 15 rows, W10 14 rows); reconciliation open (SG-03) |
| 2 | Verified results feed | `ledger/results-feed.html` | VERIFIED — 137 official rows |
| 3 | Side → total → moneyline origination order | `ledger/price-store.html` | PUBLISHED — order recorded per market |
| 4 | Fair / market / difference columns | `ledger/lines.html` | PUBLISHED — market+difference blank with reason |
| 5 | Signal vs staking leaderboard split | `ledger/leaderboard-split.html` | PUBLISHED — staking cannot change rank |
| 6 | Replacement-depth tracking | `requirements/pages/availability.html`, `integration/injuries-w10.html`, `signals/availability.html` | BLOCKED at official-source level (depth charts 404); injury/depth tiers published; string depth never inferred |
| 7 | Official-only correlations with n published | `pages/correlations.html`, `origination/correlations.html`, `correlation-audit/index.html` | PUBLISHED — n beside every value; independent recompute 11/11 |
| 8 | Demotion gate (live → paper) | `ledger/demotion-gate.html` | PUBLISHED — D1–D8 + P1 pre-registered; 0 LIVE strategies |

## Parallel-session coordination

Session 053940d1 (final integration round 3) merged the `ledger/` + `decision-review/` root
navigation first (PR #52); this session kept their version and dropped its duplicate edits,
re-applying only unique deltas. Stale PR #39 was closed as superseded with disposition comments
from both sessions. Nothing of any other session was discarded.

## Irregularities

None found in this pass. The existing flagged registers (root `pages/flagged.html` including
the new **Parallel review registers** section, `origination/`, `ledger/`, `correlation-audit/`,
`signals/`, `requirements/`) remain published and non-blocking.

## Links for manual review

- Live dashboard: <https://sassnarep3-star.github.io/Own8/>
- Coverage table: <https://sassnarep3-star.github.io/Own8/pages/executive-summary.html>
- Decision ledger: <https://sassnarep3-star.github.io/Own8/ledger/index.html>
- Correlation audit: <https://sassnarep3-star.github.io/Own8/correlation-audit/index.html>
- Signal desk: <https://sassnarep3-star.github.io/Own8/signals/index.html>
- Requirements & decision review: <https://sassnarep3-star.github.io/Own8/requirements/index.html>
- Flagged for Review: <https://sassnarep3-star.github.io/Own8/pages/flagged.html>
