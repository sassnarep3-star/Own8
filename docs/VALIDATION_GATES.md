# Validation Gates & Leaderboard Rules

Session `28cc78aa` · 2026-11-03. Every strategy must pass these gates to earn a reward tier.
Gates are computed in `scripts/analyze.py::apply_gates` and published per-strategy on the site.
Flagged irregularities and unverified items do **not** block publication or merge; they are
listed on the Flagged for Review page.

## The seven gates

| Gate | Name | Rule (market / parlay strategies) | Rule (player-prop origination) |
|---|---|---|---|
| **G1** | Data integrity | All Part-A validation checks pass: official NFL anchor 91/91 exact; independent line cross-check within documented tolerance (≥90% of spreads / ≥95% of totals within 0.5 pt, MAD ≤ 0.5); player-stats internal consistency ≥95% exact with median diff 0; schedule coverage 100%. | Same (shared data foundation). |
| **G2** | Out-of-sample | Walk-forward only; ≥100 holdout bets; thresholds/σ fit on 2006–2015 train, evaluated 2016+. | Walk-forward within season by construction (no future games used). |
| **G3** | Beats baseline | @open: mean holdout CLV > 0. @close/parlay: holdout ROI > 0. | Accuracy line RMSE beats best naive baseline (last game / position mean). |
| **G4** | Statistical significance | Holdout ROI bootstrap 95% CI lower bound > 0, **or** CLV z ≥ 2. | Skill bootstrap 95% CI lower bound > 0. |
| **G5** | Luck removed | @open: CLV z ≥ 2 (outcome-independent skill). @close/parlay: binomial win-rate p < 0.05 vs break-even-at-vig null. | OOS R² > 0 **and** skill CI > 0 **and** fair-line over-hit 95% CI covers 50%. |
| **G6** | Robustness | ≥60% of holdout seasons positive **and** drop-best-season edge still > 0. | 2021 robustness skill > 0. |
| **G7** | Correlation correctness | Parlays: joint probability estimated empirically with bootstrap CI and \|correlation lift\| > 1% (pricing must not assume independence). Single bets/props: n/a (auto-pass). | n/a (auto-pass). |

**Why these gates:** G1–G2 prevent garbage-in and overfitting; G3–G4 demand a real, significant
edge over a sensible baseline; G5 is the explicit *luck removal* requirement (skill must show
up in a metric that does not depend on short-run wins); G6 kills single-season flukes; G7 forces
correct dependence modeling for combos.

## Leaderboard score (transparent, 0–100)

Market / parlay strategies:
```
score = 100 × (0.35·CLV_component + 0.25·ROI_component + 0.25·gate_component + 0.15·robustness_component)
  CLV_component        = clamp(CLV_z / 3, 0, 1)            (0 if no CLV measured)
  ROI_component        = clamp(ROI_CI_low / 0.03, 0, 1)    (parlays: clamp(ROI/0.05)×(1 if CI_low>0 else 0.5))
  gate_component       = gates_passed / 7
  robustness_component = fraction of holdout seasons positive
```
Player-prop origination:
```
score = 100 × (0.35·skill_component + 0.25·fairness_component + 0.25·gate_component + 0.15·robustness_component)
  skill_component     = clamp(RMSE_skill_pct / 10, 0, 1)
  fairness_component  = 1 − clamp(|over_hit_rate − 0.5| / 0.1, 0, 1)
  gate_component      = gates_passed / 7
  robustness_component= 1 if 2021 skill > 0 else 0
```

## Reward tiers

| Tier | Requirement | Meaning |
|---|---|---|
| **Gold** | 7/7 gates **and** score ≥ 70 | Deployable, skill-verified edge. |
| **Silver** | ≥6/7 gates **and** score ≥ 50 | Strong skill signal; one gate (usually profit-consistency) unproven. |
| **Bronze** | ≥5/7 gates **and** score ≥ 35 | Partial signal; research candidate. |
| **Rejected** | otherwise | No demonstrated skill edge; do not bet. |

## Current leaderboard (computed 2026-11-03)

| Rank | ID | Strategy | Score | Gates | Tier |
|---|---|---|---|---|---|
| 1 | S2 | Model total value @ opening line | 63.9 | 6/7 | **Silver** |
| 2 | X3 | RB1 rushing yards — fair-line origination | 51.4 | 4/7 | Rejected |
| 3 | X1 | QB passing yards — fair-line origination | 39.5 | 4/7 | Rejected |
| 4 | X2 | WR1 receiving yards — fair-line origination | 29.8 | 3/7 | Rejected |
| 5 | S6 | Fade extreme longshots | 19.7 | 3/7 | Rejected |
| 6 | S5 | Value moneyline @ closing line | 18.8 | 4/7 | Rejected |
| 7 | S3 | Model spread value @ closing line | 15.2 | 3/7 | Rejected |
| 8 | S1 | Model spread value @ opening line | 13.2 | 3/7 | Rejected |
| 9 | P4 | Underdog covers + Under | 13.1 | 2/7 | Rejected |
| 10 | S4 | Model total value @ closing line | 12.2 | 3/7 | Rejected |
| 11 | P1 | Favorite covers + Over | 10.1 | 2/7 | Rejected |
| 12 | P2 | Favorite covers + Under | 10.1 | 2/7 | Rejected |
| 13 | P3 | Underdog covers + Over | 8.6 | 2/7 | Rejected |

**No strategy reached Gold.** The single Silver (S2) is the only strategy with a statistically
robust, luck-free skill signal (CLV +0.80 pts, z 5.68). This is the honest outcome of applying
strict gates to an efficient market — not a failure of the method, but the method working.
