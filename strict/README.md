# Own8 · NFL Research Lab

**Evidence first. No unsupported picks. No claim that luck can be eliminated.**

- **Live dashboard:** https://sassnarep3-star.github.io/Own8/strict/site/
- **Executive summary:** https://sassnarep3-star.github.io/Own8/strict/site/pages/executive-summary.html
- **Flagged for Review:** https://sassnarep3-star.github.io/Own8/strict/site/pages/flagged.html
- **Evidence snapshot:** November 4, 2026. This is not a live odds or injury feed.

## Executive findings

- Re-observed **32 team names and 224 numerical standings cells** on the [official NFL standings](https://www.nfl.com/standings/); all selected numerical fields match the prior capture. Other columns are not re-certified.
- Checked **15 Week 9 matchups and dates** against the [official schedule](https://www.nfl.com/schedules/2026/by-week/week-9). CIN at ATL is labeled Madrid. Unconfirmed kickoff/venue fields are omitted.
- The [official Week 9 injury page](https://www.nfl.com/injuries/league/2026/reg9) is accessible. Eight selected JAX/BAL DNP observations are retained, not a full injury report. Blank injury diagnoses and game statuses stay blank; DNP does not mean out.
- Acquired **91 historical games** from the [NFL's own Big Data Bowl repository](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv), pinned to an immutable commit with SHA-256 checks.
- A small rolling-week benchmark generated **60 predictions**. Margin MAE was **10.426** points versus **10.024** baseline; total MAE **12.318** versus **12.181**. This heuristic did **not** beat its simple baseline. It is a retrospective development experiment, not a betting backtest or proof of skill.
- Three descriptive correlations are computed. Bet-leg correlations are **blank**: team-level associations do not price threshold bets or joint tails.
- **11 proposed strategies** cover singles, parlays, same-game combinations and player props. **Zero qualify.** No ranks, ROI, CLV, skill scores or reward points are fabricated. Rewards are proposed non-cash recognition, not funded prizes.

## Verification standard

Observed official facts, derived analysis, Own8 policies and unverified values are explicitly separated. Every active table row links to an official **evidence or context** page. A context link is not verification of a strategy, a code finding or a numerical edge. Missing official inputs are JSON `null` and blank table cells. Calculated historical estimates are clearly labeled derived, never passed off as official NFL model values.

The earlier engine's unsupported candidates, spread-sign comparison, conditional gate pass-through, correlation proxy and unsupported grading claims are superseded. All current fair lines, market quotes, edges and betting candidates are withheld. See `strict/flags.json` and the review page. Chance remains; testing can reduce false discoveries, not remove luck.

## Reproduce without manual input

Python 3.11+; standard library only; no API keys or paid credentials:

```bash
python3 scripts/strict_build_site.py
python3 -m unittest discover -s tests -v
python3 scripts/strict_check.py
```

`strict_build_site.py` computes deterministic evidence-based analysis and builds 18 dashboard pages, plus compatibility redirects. GitHub Actions repeats build/tests/link checks on pushes and PRs; GitHub Pages deploys committed static files from `main /`. There is **no** scheduled data refresh, authenticated odds acquisition, automatic outcome-grading daemon or wagering service. No missing data is invented to simulate one.

## Organization

- `strict/evidence/`: official historical files + immutable SHA-256 manifest; selected web observations with dates and scope.
- `strict/results.json`: descriptive correlations, historical predictions/metrics, proposal register and per-strategy gate matrix.
- `strict/flags.json`: current strict-audit findings; inherited flags remain in `data/flagged.json` and on the review page.
- `strict/repository-inventory.json`: 104 base tracked-text files, line counts and digests. Inventory is **not factual certification**.
- `scripts/strict_*.py`, `tests/`: reproducible engine, site builder and tests.
- `strict/site/pages/`, `strict/site/assets/`, `strict/site/index.html`: local-asset responsive/searchable/sortable static dashboard.
- `analysis/`: independent legacy/canonical outputs, untouched by this contribution; not consumed by the strict engine.
- `data/`: retained legacy captures, not blanket re-certified. Player-leader subsets and third-party market data are excluded from the strict engine.
- `audit/`: **independent session 74efc1ec's preserved baseline audit** of commit `7c2f545`. Its `check.py` expects that historical schema; do not run it against the redesigned schema. It is not the current build/test entrypoint.
- `verification/`: preserved independent PR #6 QA. The unmerged `site/` lab is not part of this release; the separate `lab/` scope is not edited by this session.
- Root `docs/`, `pages/`, `archive/` and `assets/`: untouched by this final namespaced release; legacy claims remain subject to the root integration owner’s audit.
- `COORDINATION.md`: all session histories, claims, conflict resolutions and deployment records.

## Safety and limitations

Research only. No real-money wagers, cash awards, accounts or bankroll inputs. [Washington's official regulator](https://wsgc.wa.gov/tribal-partnerships/sports-wagering) provides current local resources; this project does not determine legal eligibility. Statistical-method and reward thresholds are project proposals, not official NFL/NIST policies. External links are dated retrievals; the checker tests paths/anchors/source-link scope, not ongoing HTTP liveness.

## Coordination handoff
Canonical root/site scripts belong to dd321bf5 (PR #19). This contribution publishes only `strict/site/`, `strict/` evidence/results, namespaced scripts/tests, and this session’s board additions. It does not overwrite the canonical root or independent audits. Links to legacy raw files are provenance, not verification.
