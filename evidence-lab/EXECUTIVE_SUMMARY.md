# Executive summary — Own8 NFL Evidence Lab

**As of 2026-11-04 · Research only · No actionable wagers or demonstrated winning strategies**

## Decision

Publish the source-linked research site and validation framework. **Do not publish current bet recommendations, a skill ranking, or rewards.** Required official prices, matched bet outcomes, prospective prediction locks and multi-season validation are absent. No statistical method removes luck or guarantees NFL betting profit.

## What is established

- **91 historical game rows** were captured directly from the NFL publisher's GitHub repository, pinned to an immutable revision. Original bytes match both Git blob hashes and SHA-256. The official schema identifies this as **2017 Weeks 1–6**, not current-season data. [Official game data](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) · [Official schema](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md)
- **60 historical point forecasts** were derived using prior weeks only: Weeks 1–2 warm-up, Weeks 3–6 evaluation. Predictions and training IDs are reproducible. This is a simple prototype, not a validated current fair-line service. [Official inputs](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) · [Local calculations](results.json)
- **The prototype does not beat its simple baseline on MAE.** Home-margin MAE is **10.43 points** vs **10.02** for the prior-week league baseline; total MAE is **12.32** vs **12.18**. These are derived forecast errors, not betting returns. No weight was tuned to hide the negative result. [Official inputs](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) · [Method](METHODOLOGY.md)
- Two **descriptive score correlations** are derived: home/away points **r=0.067**; home margin/game total **r=0.233**. Neither is a prop or parlay-leg estimate. Exploratory week-cluster intervals have only six clusters and are not strong evidence. Matched prop and betting-leg correlations remain blank. [Official inputs](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv)

## Strategy and competition design

Seven registered ideas cover spread, total, moneyline, cross-game parlays, same-game combinations, single props and QB/receiver combos. All remain **HOLD**. These are research proposals; only the historical spread/total point model is implemented.

Eight required gates cover evidence, freshness, chronology, sample, skill, dependence, risk and settlement. **CONDITIONAL is not PASS.** One missing gate blocks eligibility, rank and reward. Proposed thresholds are explicitly policy choices—not official NFL requirements or validated optimal settings.

Proposed non-cash reward scoring ranks only eligible strategies by a positive multiplicity-adjusted lower ROI bound, with calibration, season robustness, costs and dependence checks. There is no funded contest, bankroll transaction or automatic reward payout. [Official dataset scope](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md) · [Project policy](METHODOLOGY.md)

## Material findings and limitations

1. The existing baseline repository audit found a reversed spread sign, conditional gate passes, unverified candidates and placeholder leaderboard results. Active owners are handling their files. This package does not certify their eventual fixes; review the [baseline audit](../audit/index.html) and shared [coordination board](https://github.com/sassnarep3-star/Own8/blob/main/COORDINATION.md).
2. A source URL is not proof of a verified value. All historical fact cells in this package map to the exact official captured file; other repository datasets were not externally re-verified here. Matching two internal snapshots is not external verification.
3. Current odds, current injuries, prop thresholds, book rules, expected betting returns, ranks and rewards remain blank when unconfirmed. Descriptive score r is not a valid substitute for matched bet-leg r.
4. Local builds and tests run without prompts. There is no scheduled current-data feed, prospective prediction lock, official-price ingestion or live settlement service. Do not mistake a static rebuild for live automation.
5. Network restrictions allow GitHub, not direct NFL website checks. Official publisher README/schema and immutable GitHub API blobs were retrieved. No claim of exhaustive current official verification is made.
6. Existing jurisdiction-specific repository copy is not certified. This research package places no wagers and offers no legal advice.

All limitations are published on [Flagged for Review](flagged.html), including official context links. They do not block publishing an honest research site, but they block bet recommendations and skill claims.

## Deliverables

- Eight-page, searchable, responsive static evidence dashboard under `evidence-lab/`.
- Exact official source captures, immutable source registry, file hashes and per-row provenance.
- Dependency-free betting math, push-aware settlement primitives, paired-outcome joint estimator, chronological prototype, and strict gate/reward suppression.
- Regression suite and read-only link/evidence/repository checks, with machine-readable results.
- Reproducible method and proposed competition contract; no guessed missing values.

See [checks.json](checks.json) for the exact latest test count, source-row checks and internal link results. Deployment and PR outcomes are recorded in the coordination board after they actually complete.
