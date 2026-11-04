# Leaderboard Competition — rules

**Purpose:** rank strategies by skill, not luck. Rewards are **points and tier badges only** — this project does not place, facilitate, or intermediate real-money wagers (flagged F-10).

## Scoring

- When a week's games are final per **official scores** (https://www.nfl.com/scores/), each candidate bet grades at standard **−110** vig.
- Weekly points for a strategy = realized ROI% × 100 (stake-capped per G7).
- Season points = sum of weekly points. **Tiers:** Gold ≥ +5.0, Silver ≥ 0, Bronze < 0.
- Tie-break: higher Sharpe-like ratio = mean weekly ROI ÷ stdev of weekly ROI (rewards consistency — the anti-luck tie-break).

## Anti-luck design

- Bets only exist if they passed all validation gates (G1–G7) at origination.
- Edge sanity cap (|edge| ≤ 8) removes blowout-driven outliers.
- Stake caps (≤2% singles, ≤1% parlays) prevent variance domination.
- Same-game correlated parlays blocked by default (correlation policy).
- Standings anchor on net-points regression (r = +0.84 vs win%), not raw W-L.

## Automation

No manual input: after each week, re-capture official data, re-run `python3 scripts/analyze.py`, grade from official scores, update `analysis/leaderboard.json`, rebuild the site with `python3 scripts/build_site.py`, and verify links with `python3 scripts/check_links.py`.

## Current standings (2026-11-03, pre-Week-9)

All strategies at **0.0 realized points** (no games graded yet). Week 9 projections are shown on the Leaderboard page. First grading after the Week 9 slate completes (from Monday 2026-11-09 onward).
