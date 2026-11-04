# Strategy Research — NFL Line Origination & Signal Design

Session `28cc78aa` · 2026-11-03. All numbers below are **DERIVED** by `scripts/analyze.py`
from the primary datasets in `docs/DATA_PROVENANCE.md` (reproducible, seed 20261103).
Market data is **PRIMARY (non-NFL)** — the NFL does not publish betting lines — and is
flagged as such. Method references are in `docs/SOURCES.md` (R1–R4).

## 1. Objective & framing

Originate our own NFL lines (spreads, totals, moneylines, player props), compare them to
market lines, and keep only strategies that demonstrate **skill independent of luck**.
The project is run as a leaderboard competition: every strategy is scored and must pass
validation gates (`docs/VALIDATION_GATES.md`) to earn a reward tier.

Two structural facts shape everything:
- **Closing lines are highly efficient.** Moskowitz (2021, R4) finds mispricing in betting
  markets but returns too small to overcome transaction costs. Our backtests confirm this:
  naive models do not beat the closing spread/total after vig.
- **Skill is measured by line-beating, not by wins.** Closing-line value (CLV) — getting a
  better number than the eventual close — is outcome-independent and is the primary skill
  metric (R1, R4). A strategy can be +EV yet lose money short-run; CLV separates the two.

## 2. The ratings engine (line origination core)

A walk-forward, points-based team rating produces a model margin and total for every game:
- Each team carries a rolling log of its last 8 games (points for / against).
- Expected home points = (home offense avg + away defense avg) / 2; away symmetric.
- Model margin = exp_home − exp_away + home-field advantage (expanding mean of home margins).
- Model total = exp_home + exp_away.
- **No leakage:** ratings use only games strictly before the current game; at each season
  boundary ratings regress 25% toward the league mean (roster turnover).
- Moneyline probability = Φ(model_margin / σ), σ = std of (actual − model) margin fit on the
  2006–2015 training window only.

This is deliberately simple and transparent. It is a *baseline origination engine*, not a
claim of state-of-the-art prediction. Its market Brier score (0.2247) is **worse** than the
no-vig market (0.21105) over 2006–2025 — the market is the better forecaster, exactly as the
efficiency literature predicts.

## 3. Signal catalog & results (holdout unless noted)

| ID | Signal | Category | Key holdout result | Verdict |
|---|---|---|---|---|
| S1 | Model spread vs **opening** consensus, bet edge ≥ T | Single | CLV −0.02 pts (z −0.21); ROI −10.5% | Rejected — no spread edge |
| S2 | Model total vs **opening** consensus, bet edge ≥ T | Single | **CLV +0.80 pts (z 5.68, CI 0.53–1.09)**; ROI −6.9% | **Silver** — real line-beating skill, ROI unproven |
| S3 | Model spread vs **closing** line | Single | ROI −1.3% (CI −7.0–4.5%) | Rejected — close is efficient |
| S4 | Model total vs **closing** line | Single | ROI negative | Rejected |
| S5 | Value ML: model prob − no-vig market ≥ 5 pp | Single | ROI negative; model Brier worse than market | Rejected |
| S6 | Fade extreme longshots (dog implied ≤ 15%) | Single | ROI negative after vig | Rejected — bias exists but vig eats it |
| P1–P4 | Same-game cover+total 2-leg parlays @ +260 | Parlay | All ROI −8% to −16%; legs ~independent | Rejected — no correlation edge |
| X1–X3 | Player-prop fair-line origination (QB/WR/RB yards) | Player prop | QB +1.7% RMSE skill (CI −0.2–3.6); WR/RB ≤ 0 | Rejected as betting edge; useful as pricing input |

**Headline:** the only robust skill signal found is **S2 — the model beats the opening game
total by ~0.8 points on average** (highly significant, z≈5.7). That is a genuine, luck-free
signal. It does **not** yet convert to proven profit (holdout ROI negative, season consistency
50%), so it earns Silver, not Gold. This is the honest, defensible conclusion.

## 4. Correlation values (the core deliverable for prop combos)

Estimated from 2009–2017 player-game data (D3, n≈4,600 team-games) with 2,000-sample
bootstrap 95% CIs, and re-checked on 2021 (D4, n=544). Full table: `data/results/correlations.json`.

| Pair | r (2009–17) | 95% CI | 2021 check | Use |
|---|---|---|---|---|
| QB pass yds ↔ team WR1 rec yds | **0.695** | 0.68–0.71 | 0.671 | Strong + SGP leg pair |
| QB pass yds ↔ team WR2 rec yds | **0.756** | 0.74–0.77 | — | Even stronger (WR2 volume-dependent) |
| WR1 ↔ WR2 rec yds (same team) | **0.492** | 0.47–0.52 | 0.497 | Positive, NOT negative — both ride team pass volume |
| QB pass yds ↔ team points | 0.379 | 0.35–0.40 | 0.432 | QB yards + team over/ML |
| QB pass yds ↔ RB1 rush yds (same team) | **−0.178** | −0.20–−0.15 | — | Game-script tension (negative SGP pair) |
| RB1 rush yds ↔ team point margin | **0.334** | 0.31–0.36 | 0.361 | Game script: leaders run |
| Team points ↔ game total | 0.676 | 0.66–0.69 | — | Team over + game over |
| QB pass yds ↔ opposing QB pass yds | 0.172 | 0.12–0.22 | — | Shootout / pace effect |
| Closing spread ↔ closing total (market) | −0.020 | −0.05–0.01 | — | No market-level relation |
| Favorite covers ↔ over hits (binary φ) | −0.007 | −0.04–0.02 | — | Cover & total legs ~independent |

**Implications for parlay / prop-combo pricing**
- **Same-game player props are strongly correlated.** QB+WR1 yards r≈0.70 means an
  "independent-legs" parlay price badly misstates the joint probability. Price these with the
  empirical joint distribution (or a copula calibrated to r), not by multiplying legs.
- **WR1+WR2 is positively correlated (r≈0.49)**, contrary to the "target competition" intuition.
  Stacking two receivers on the same offense is less diversifying than it looks.
- **QB yards + own RB yards is negatively correlated (r≈−0.18)** — a rare negatively-correlated
  SGP pair that books may over-price.
- **Game-level cover+total legs are essentially independent (φ≈0)**, so standard 2-leg parlay
  pricing is roughly fair there; our P1–P4 backtests lose the vig, confirming no edge.

## 5. Player-prop line origination (X1–X3)

No historical *market* prop lines are publicly archived in any reachable primary source, so
props are evaluated as **line origination**, not ROI backtests (flagged). Dual estimator,
walk-forward within season (min 2 prior games):
- **Accuracy line** = expanding mean of prior games → RMSE vs naive baselines (last game,
  position mean).
- **Fair 50/50 line** = expanding median of prior games → over-hit rate should be ≈50%.

Results: QB expanding mean beats the position-mean baseline by **1.7% RMSE** (CI −0.2–3.6,
not significant); WR1 and RB1 naive estimators do **not** beat baselines. A rolling-4-median
variant was tested and rejected (worse RMSE than expanding mean at every position). The
over-hit rate at the fair line is 47.7–48.8% (slightly under 50% because yards are right-skewed
and the within-season median lags early-season usage). **Conclusion:** simple univariate prop
origination is not a standalone edge; its value is as the *input* to the correlation-aware
combo pricing in §4. Better prop lines need usage/role features (snap share, targets, game
script) — listed as future work, not fabricated.

## 6. Removing luck (method)

- **CLV as the skill metric** (§3): line-beating is independent of whether the bet wins.
- **Bootstrap CIs** (2,000 resamples) on every ROI, CLV, correlation, and skill estimate.
- **Binomial luck null:** win rate tested against the break-even probability *at the posted
  vig* (e.g., 52.38% at −110); p-value reported per strategy.
- **Out-of-sample protocol:** thresholds/σ chosen on 2006–2015 train; evaluated on 2016+ holdout.
- **Season robustness:** fraction of seasons with positive edge + drop-best-season edge.
- **Market calibration check:** no-vig moneyline deciles vs empirical win rate; market Brier
  0.21105 vs model 0.2247 → market better calibrated; favorite-longshot bias visible (longshots
  implied 16.2% → won 19.1%; big favorites implied 91.7% → won 95.1%) but too small to beat vig.

## 7. Market context (DERIVED, D1)

- **Key numbers:** margin 3 occurs in 14.5% of games, margin 7 in 8.9% (2006–2025) — buying
  on/off 3 and 7 has measurable value; originate lines aware of these atoms.
- **Scoring environment:** league avg total 45.8 (2024), 46.0 (2025); home margin ≈1.9–2.1 pts.
- **Ties exist** in the regular season (Rule 16-1-3(d), OFFICIAL F21) — moneyline pushes must be
  modeled, not ignored.

## 8. Future work (not fabricated, not counted as results)

Usage-based prop models (snap/target share, game script), EPA-based ratings, injury/lineup
adjustments, copula-based SGP pricing, and live line-shopping across books. These are the
natural next steps to convert the S2 CLV signal and the correlation structure into profit.
