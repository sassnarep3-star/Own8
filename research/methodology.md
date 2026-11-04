# NFL line origination: research protocol

As of 2026-11-04. This is an executable research scaffold and verified snapshot, not a validated betting system. No wagering, account connection, deposits, paid competition or cash prizes are implemented. Official data publishers do not endorse this protocol.

## Evidence and publication rules

1. A URL is a review target, not proof of a value. Independently retrieved selected fields appear under `data/verified/`, with checked date, field scope and transcribed excerpts. These excerpts are not raw HTML or complete historical archives.
2. Legacy files remain in Git for provenance. Their numeric values are withheld from current tables unless independently rechecked. The baseline inventory records SHA-256, line counts and each structured row. Matching two captures only checks consistency, not truth.
3. Observed values, project calculations, research hypotheses and unverified fields are separate. Null means unavailable/unverified, never zero. No imputed statistic, price, rank, affiliation or injury adjustment is published as fact.
4. Snapshot date is not a pregame information timestamp. No historical backtest may use these observations for a game that already occurred. A later injury article cannot be backdated.
5. Every displayed table row links to an official reference. For a proposed method, that reference supports the data definition or general statistical principle only, not the method's effectiveness or chosen thresholds.

## Signals to investigate (hypotheses, not findings of edge)

- **S1 / spread:** opponent-adjusted, regularized scoring margin; model home margin first, then negate for the fair home handicap. Fit team offense/defense and home effect only inside chronological training folds. Compare against zero-margin and market baselines.
- **S2 / total:** a joint score distribution with pace, drive efficiency and score-state features. Test tail calibration and integer pushes. A mean total alone is not a distribution or betting probability.
- **S3 / QB passing:** volume model (dropbacks × attempt share) and efficiency model (yards/attempt). CPOE and intended air yards are possible features, not direct extra yards. NFL's time-to-throw excludes sacks; do not substitute it for all dropback timing.
- **S4 / RB rushing:** carries × yards/carry, with role, participation and opponent adjustment. Model role uncertainty. Team rushing totals do not identify a player's workload. No individual allocation is inferred here.
- **S5 / receiving:** team attempts × target share × catch probability × yards/catch, with coherent shared targets across receivers. Compare actual YAC with xYAC as a regression hypothesis. Do not assume residuals are all luck.
- **S6 / different-game parlay:** evaluate the actual quoted combined decimal payout against calibrated joint win probability. Different games are not automatically independent: shared teams, model errors, weather regimes and weekly selection rules can induce dependence.
- **S7 / same-game prop combos:** jointly simulate coherent attempts, completions, targets, yards and game script. QB yards and receiver yards must reconcile. Opposing overs/unders and negative correlations can also create invalid joints; neither sign is a shortcut to value.
- **S8 / regression/ablation:** test whether shrinking efficiency extremes and adding verified turnover/context variables improves forward performance. No arbitrary turnover adjustment is implemented without game-level data and evidence.

Official feature definitions: https://nextgenstats.nfl.com/glossary

## Current transparent baseline (calculation, not trained model)

For team i, games g = W + L + T and strength s = NET / (g + 8). The eight prior games are a project-chosen shrinkage hyperparameter toward zero, not an official estimate. Predicted home margin = s_home − s_away + H. Fair home handicap = −predicted margin. H is set to zero for all games because a fitted home advantage is unavailable; verified neutral games override any future nonzero H. CIN–ATL is listed as an international game in Madrid by the NFL.

The illustrative total is [(away PF/g + home PA/g) + (home PF/g + away PA/g)] / 2. This is an untrained scoring-average baseline, not an actionable fair total. It ignores opponent strength, player availability, pace and uncertainty. It is displayed only in the explicitly marked Research Lines table. No fair probabilities, EV, recommendation or stake is inferred from it.

All baseline inputs are from the independently checked standings snapshot. Source: https://www.nfl.com/standings/ and schedule https://www.nfl.com/schedules/2026/by-week/week-9

## Price conventions and payout

Decimal odds d return d times stake on a win, including stake. Unit net win is d−1, loss −1, push/void 0. American odds +a convert to 1+a/100; −a to 1+100/a. Quotes must include operator, market/side/threshold, exact timestamp/time zone, maximum availability if known, rules and full mutually exclusive outcome prices. Never assume −110.

For a complete mutually exclusive market, proportional de-vig probability is (1/d_i)/sum_j(1/d_j). This is a project modeling convention, not the true win probability. Cover expected value = P(win)(d−1) − P(loss); pushes return stake. Predicted cover margin = predicted home margin + quoted home handicap. A difference in points is not EV without a calibrated margin distribution.

For a combo, use the operator's actual combo quote, not the product of leg prices. Settlement with void/push legs must follow that operator's rules. The single-leg settlement helper does not pretend to implement every sportsbook's parlay rules. No verified operator quotes/rules are present, so all price-dependent outputs remain blank.

## Correlation and joint distributions

Pearson r = sum[(x−mean x)(y−mean y)] / sqrt(sum[(x−mean x)^2]sum[(y−mean y)^2]). Pair by stable game/player ID and the same timestamp/fold; reject unequal vectors, undefined constant series and missing/nonfinite values. Do not independently drop values from each vector and then truncate to equal length.

Descriptive cross-team snapshot correlations have n=32 teams, not independent games. Teams play each other. These associations are not bet-leg correlations, evidence of causation, proof of skill or forecasts. Ordinary independent-row confidence intervals are not reported for them. NIST cautions that association does not prove causation: https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm

For betting, estimate residual correlations after pregame context adjustment on held-out game-level observations. Also estimate threshold-specific binary hit correlation. For two Bernoulli legs with hit probabilities p,q and feasible rho, P(both) = pq + rho sqrt[p(1−p)q(1−q)]. Enforce max(0,p+q−1) ≤ P(both) ≤ min(p,q). The tested helper rejects infeasible inputs. Pairwise correlations do not identify the full distribution for three or more legs; require a coherent joint simulator, valid covariance matrix and out-of-sample joint calibration. All real bet-leg correlation and combo probability values remain blank here.

## Validation gates (project policy, not league rules)

All eleven gates must explicitly equal PASS. Missing, CONDITIONAL, stale, unverified and not-applicable strings do not pass. For a single, joint_distribution may PASS only after documenting that it has no multi-leg exposure. All current strategies are BLOCKED; publishing review findings does not block the website, but missing evidence does block model eligibility.

- **Provenance:** official source evidence for each feature and result; separately a direct operator quote for any price. Stable IDs, selected-field schema, source time, retrieval time and checksums. Reject schema drift and duplicate games.
- **As-of:** timezone-aware feature_time ≤ prediction_time < kickoff. Rolling training uses only earlier weeks. Pregame context must be refreshed within 24 hours and executable quote within 15 minutes of origination (proposed freshness policy; not implemented as a live collector).
- **Availability:** current official injury/inactive/roster information and confirmed roles before origination. No conditional injury pass. Missing impact estimates stop the strategy, not an invented numeric adjustment.
- **History:** at least three complete seasons of event-level training data and a separate complete untouched season for evaluation (policy floor, not a power guarantee). All legs in the same game remain in one fold.
- **Holdout:** nested expanding-window development, embargo adjacent information where needed, hyperparameters chosen on training/validation only, final season held out. Record baselines, all ablations and both successful and failed variants. Prospective shadow trial follows.
- **Calibration:** for binary events, Brier and log loss against a preregistered baseline; margin/total MAE or CRPS and reliability plots; player count/tail diagnostics; joint calibration for combos. Explicit push probabilities. Require positive lower 95% game-cluster bootstrap bound on baseline Brier improvement and net quoted-price EV before promotion. Thresholds and bootstrap choices must be frozen beforehand.
- **Multiple testing:** register every strategy/variant. Apply Holm family-wise correction at alpha 0.05 to prespecified tests, not only winning variants. No adaptive retuning of the untouched holdout. Market regimes and correlated experiments limit conclusions.
- **Price:** executable timestamped direct-operator prices and settlement terms, including both sides where needed for de-vig. Require positive lower uncertainty bound on net EV after documented costs. Closing-line value is a diagnostic, not proof of realized profit.
- **Joint distribution:** coherent, feasible and held-out calibrated probability for every multi-leg selection. No automatic independence and no universal absolute-correlation cutoff. Account for shared exposure across strategies.
- **Risk:** points-only flat one-unit stake per entry, maximum one aggregate unit per game and five per week across the competition (chosen project caps). Shared-game exposure must be deduplicated; no real-money bankroll management. Stress drawdown and limits before promotion.
- **Preregistration:** immutable prediction/model/data/quote hashes, thresholds, stake, rules version and prediction timestamp recorded before kickoff. No retrospective entry edits; corrections are append-only.

No claim is made that the full statistical trial or continuous official-data ingestion is implemented. Tested primitives cover strict eligibility, signs, prices, binary joint feasibility, chronological splitting, Brier scores, game-block bootstrap and Holm correction. No genuine forecast ledger exists yet.

## Skill leaderboard and rewards (proposed competition rules)

Do not rank an ungraded strategy, substitute zero for unknown return, award points on projection, or compare unequal betting opportunities as if identical. Keep all registered variants in the registry, including failures. Same entry universe and fixed flat stakes prevent leverage from deciding the winner. The competition has no entry fee or cash/value prize; badges are proposed non-monetary recognition only, contingent on evidence.

After the frozen holdout and a prospective shadow season, qualify only if every gate passes, at least 200 distinct settled game clusters and 12 weeks of observations are present, the paired Brier improvement lower 95% game-block bootstrap bound exceeds zero, net EV bound exceeds zero, and the Holm-adjusted prespecified test passes. These are design minima, not sufficient statistical power or a guarantee of future success. No such dataset exists here.

Rank eligible strategies by lower confidence bound of paired baseline Brier improvement (positive = better), then lower confidence bound of quoted-price unit ROI, then smaller game-cluster drawdown; ties remain shared. Gold/Silver/Bronze badges go to the first three qualified ranks only. Report Brier, log loss, calibration, unit ROI, drawdown, observed game/week counts, confidence bounds and all attempted variants side by side. Do not sum weekly ROI percentages. Total ROI = net settled profit / total risked stakes, with push/void treatment separately disclosed under preregistered operator terms. Bootstrap whole games with all their legs together, use week-block sensitivity checks, and separate estimation uncertainty from irreducible outcome variation.

Results and ranks remain blank. Randomness cannot be removed from football. These procedures can reduce overfitting and quantify uncertainty; they cannot guarantee that any strategy is exclusively skill-based or profitable.

## Automation boundaries

`python3 scripts/audit.py`, `python3 scripts/analyze.py`, `python3 scripts/build_site.py`, `python3 scripts/check_links.py` and the unit tests run unattended on fixed verified inputs. GitHub Actions rebuilds/tests the isolated static artifact. Both direct and scoped-workflow-token attempts to change publishing mode were denied. The working legacy main/root Pages build is retained with Jekyll exclusions; CI/preview checks an isolated artifact including the complementary strict workspace. No successful custom deployment is claimed. It does not scrape authenticated sources, buy datasets, refresh sportsbook quotes, place wagers or continuously grade a live contest. The source allowlist is not an external uptime check. Stale snapshots stay dated and do not silently become current.

## Safety and jurisdiction

Research only. Do not infer legality from approximate location. The Washington State Gambling Commission describes a limited tribal-casino sports-wagering framework and on-premises mobile geofencing: https://www.wsgc.wa.gov/tribal-partnerships/sports-wagering/sports-wagering-requirements-and-rules . Consult the regulator's current rules rather than assume remote mobile wagering is allowed. Help/self-exclusion information: https://www.wsgc.wa.gov/responsible-gaming-self-exclusion . No automated wagering or cash-reward competition is provided.
