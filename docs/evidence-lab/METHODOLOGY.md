# Own8 verification package — methodology and requirement coverage

As of 2026-11-04. This package is separate from the existing root dashboard and historical lab; it does not certify their claims.

## 1. Evidence and verification levels

**Official source actually retrieved:** the NFL publisher's `nfl-football-ops/Big-Data-Bowl` GitHub repository, pinned at `9ad0b4b2ea36697e29e44e2399512cc1ce70358c`.

- [Official games file](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv)
- [Official schema](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md)
- [Official publisher README](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/README.md)

Authority basis: the publisher identifies the repository as the NFL Big Data Bowl data homepage, and GitHub repository metadata links to `ops.nfl.com/big-data-bowl`. Direct NFL website retrieval is unavailable under this session's network restrictions. This is not independent confirmation via that website.

`capture.py` obtains the immutable file metadata and Git blob through the GitHub API, verifies the Git blob hash and size, and stores original bytes and SHA-256. `analyze.py` checks hashes before using any values. It parses all 91 game rows and verifies unique game IDs, the stated season/week domain, nonnegative integer scores, and exact provenance. The schema describes this sample as 2017 Weeks 1–6. The displayed historical fact cells are direct source fields, not reconstructions.

Verification levels must not be conflated:

1. **Exact official capture:** immutable official file matches captured bytes. All displayed game facts in this package have this level.
2. **Internal consistency:** identifiers, arithmetic, chronology, link targets and cross-file agreement. This does not establish independent external truth.
3. **Derived research:** model estimates, errors and descriptive correlations. Reproducible, but not official facts or validated betting signals.
4. **Unverified:** unavailable current scores, odds, injuries, props, bet outcomes, legal eligibility or strategy skill. Leave factual cells blank; publish the gap.

No 2026 fact, historical bookmaker quote, or player-prop line was independently confirmed here. NFL game data is not a source for a sportsbook's executable odds. A future price feed must come directly from the price-setting operator and include timestamp, market identifier, rules and evidence. A source link by itself never grants verification.

## 2. Historical fair-line prototype

Purpose: exercise a leakage-safe origination path using a small official dataset, not recommend bets.

- Warm-up: 2017 Weeks 1–2 (31 games). Evaluate Weeks 3–6 (60 games).
- Before each evaluated week, use only games from strictly earlier weeks, even if a game earlier in the same week has already finished. This is conservative and reproducible.
- `L` = training mean points per team-game.
- `O_t` = (training points scored by team t + 4 × L) / (team t training games + 4).
- `D_t` = (training points allowed by team t + 4 × L) / (team t training games + 4).
- `H` = training mean (home score − away score).
- Predicted home points = (O_home + D_away)/2 + H/2.
- Predicted away points = (O_away + D_home)/2 − H/2.
- Predicted home margin = predicted home points − predicted away points.
- Fair home handicap = −predicted home margin.
- Predicted total = sum of the two point estimates.

The shrinkage weight of four pseudo-games is a declared research assumption, not an official fact and not a weight optimized on this sample. The model ignores schedule strength, injuries, personnel, weather and scoring distribution. It is a diagnostic baseline. Past scores do not imply calibrated cover probabilities. A mean prediction does not necessarily equal a market fair line at NFL key numbers.

Baseline comparator: prior-week league mean home margin and league mean total, without team-specific information. Report point MAE and RMSE, not ROI. This prototype performs worse than the league baseline on both MAE metrics in this sample; no tuning to reverse that result is performed. There is no untouched prospective confirmation set or independent season replication here.

A historical point estimate is allowed only in a clearly labeled **derived estimate** column; it must never populate an official-fact or officially confirmed market column.

## 3. Betting math and settlement conventions

These are mathematical definitions / project implementation choices, not NFL data facts.

- Decimal payout from American odds A: 1+A/100 if A≥100, or 1+100/|A| if A≤−100. Reject invalid and nonfinite inputs.
- Two-way proportional no-vig probabilities normalize reciprocal decimal prices. This assumes mutually exclusive exhaustive outcomes on the non-push sample. It is a model of removing margin, not a guarantee of true probability.
- Expected net return per unit staked = p_win × (decimal payout−1) − p_loss. Explicit p_push contributes zero return.
- Home cover margin = predicted home winning margin + signed home handicap. A predicted home margin of +7 versus home −3 produces +4 points of cover margin, **not** a 4% ROI or a measured win probability.
- Historical settlement uses official final scores and a specified spread or total. Pushes return PUSH, never LOSS or WIN.
- No wager settlement, reward payout or bankroll transaction is implemented. Unit-test odds and bets are synthetic.
- Book-specific overtime, void, injury and parlay-push rules must be verified before any real grading; no generic product or push rule is assumed for combos.

## 4. Correlation and joint probability

Two descriptive Pearson correlations are calculated across the 91 official games: home vs away points, and home margin vs game total. Undefined constant/insufficient samples return blank. The second pair shares score variables algebraically; association is not an edge.

Exploratory intervals use 2,000 whole-week bootstrap resamples with seed 3408. There are only six weekly clusters. These intervals are not strong inference and do not fully capture repeated-team dependence or season uncertainty. No strategy gate passes on them.

Player-prop, threshold-specific side/total and cross-game leg correlations remain blank. Requirements for later estimation:

1. Align legs on the same scenarios and pregame data cutoffs; preserve whole games and shared players/teams.
2. Define the actual prop or betting threshold and settlement convention. Pearson on raw yardage is not the same as correlation of over/under indicators.
3. Estimate joint tails, not just pairwise r. Pairwise correlations do not determine a multi-leg distribution.
4. Preserve repeated teams, same-week shocks, shared weather and market factors in block/cluster validation; different games are not automatically independent.
5. Obtain the actual offered combo price and rules, compare joint probability with break-even after margin and uncertainty, and validate out of sample.

The engine's small binary scenario estimator directly counts aligned joint wins and reports Fréchet bounds. It rejects missing outcomes, pushes and unaligned leg counts; a richer rules-aware model is required for those cases. Synthetic regression tests show why product-of-marginals can be wrong.

## 5. Skill validation and research competition

**Luck cannot be removed.** The objective is to reduce false discoveries and distinguish repeatable signal from noise, with uncertainty. No approved or winning strategy exists in this package.

Proposed rules (policy choices, not proven optimal thresholds):

- Register all tried variants, primary hypotheses, parameters, markets, selection frequency, costs, stake policy, train/validation/test splits and primary tests before evaluation.
- Preserve an untouched confirmation period. For final selection, test on data not used to develop any of the alternatives.
- Audit publication timestamps; lag injuries, transactions and features to what was actually available at lock time. Freeze exact prediction and quote records before kickoff in an append-only ledger.
- Require at least 1,000 held-out bets over at least three seasons; these are minimum safeguards, not power calculations or guarantees. Dependence reduces effective sample size; run power and minimum-detectable-effect analysis for the chosen design.
- Use valid week/season blocks or an appropriate dependency-aware inference procedure. Require a positive simultaneous lower bound on net ROI, and a clustered p-value at most 0.05 divided by the number of registered trials. Include failed and discarded trials in that family. Validate the inference method and account for adaptive searches.
- Require probability calibration and season robustness. Brier/log-loss comparisons need calibrated probabilities and a frozen market baseline, neither supplied by the point model here.
- Closing-line value is a useful secondary diagnostic, but not proof of profitable execution; define signed CLV consistently and timestamp both quotes.
- Never repeatedly inspect a fixed-sample p-value and stop when significant. Use a separately validated anytime-valid plan or new untouched confirmation data.
- Validate paired dependence and aggregate exposures, including singles that overlap by team/week.
- Lock stake caps and enforce observed holdout drawdown ≤20%; stress testing is required. Historical limits do not guarantee future drawdown limits.
- Every evidence, freshness, chronology, sample, skill, dependence, risk and settlement gate must literally be PASS. CONDITIONAL/UNKNOWN/missing fails closed.

Only after all gates pass: rank by multiplicity-adjusted lower net ROI bound; proposed non-cash reward points are 10,000 × that positive bound. Publish all tested variants and uncertainty. Ties use registered strategy ID. No current rank or reward is assigned. This is a contest design, not a funded competition.

## 6. Automation, operations and scope

`analyze.py`, `build.py` and `check.py` run without user input and reproduce this captured research package. `capture.py` intentionally refreshes immutable official evidence. None runs a scheduled current odds feed, wager execution, injury ingestion or prospective settlement daemon. No such capability is claimed.

Current-data deployment requirements remain flagged: official/licensed price access, archived timestamped raw responses, schema drift checks, final injury states, prospective locks, independent results and book rules, idempotent settlement with reversals, audit trails, alerts, and freshness-enforced publication. If unavailable, the system must publish HOLD, not fill values.

## 7. Repository review and parallel work

The root dashboard, legacy data and historical lab have independent owners. This session read the shared board, claimed only `evidence-lab/**`, and notified PR #6/#8 owners. No conflicting site/data edits were made. `repo-review.json` records inspected paths, hashes, exact line findings and the baseline revision; it is not an exhaustive external certification of every repo file.

Known legacy risks—handicap sign, conditional passes, unverified candidates, placeholder realized points, jurisdiction assumptions and claims of luck removal/automatic settlement—are published for review. Source links accompanying these findings define official data scope, not an assertion that the NFL verified our code audit.

## Requirement disposition

| Requirement | Disposition | Official context |
| --- | --- | --- |
| Executive summary | Published with explicit evidence scope and blockers | [Official games](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) |
| Clean categorized dashboard | Eight static pages, searchable tables, pinned official links on every data row | [Publisher README](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/README.md) |
| Official row verification | All 91 displayed historical fact rows match captured official file; source hashes checked; no claim of 91 independent gamebook checks | [Official games](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) |
| Originate lines | Prior-week-only historical point-forecast prototype; current lines unverified and blank | [Schema](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md) |
| Singles, parlays, props | Seven research hypotheses; all HOLD pending prices, outcomes and validation | [Schema](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md) |
| Correlation values | Two descriptive score pairs derived; unsupported bet-leg/prop values blank | [Official games](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv) |
| Selectively skill-based rewards | Fail-closed gate engine and proposed non-cash scoring; no demonstrated skill, rank or rewards | [Dataset scope](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md) |
| No manual input | This package builds/tests offline without prompts; live ingestion/settlement not implemented | [Publisher scope](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/README.md) |

These official context links do not endorse our custom policies, models or implementation.
