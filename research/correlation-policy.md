# Correlation policy

Three descriptive statistics are calculated over 32 verified team season-to-date aggregates: points/game vs win fraction, net points/game vs win fraction, and rank net points/game vs rank win fraction (average tied ranks). Official inputs: https://www.nfl.com/standings/ . Values: `analysis/correlations.json`.

These teams share games and scoring outcomes. The observations are not independent game experiments. No IID interval or claim of causality/forward skill is made. Association does not imply causality: https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm .

Team aggregates cannot substitute for QB-over/receiver-over, team-total or cross-game cover indicators. All bet-leg correlations, observation counts and confidence intervals are blank. Missing dependence is not independence; low Pearson correlation would not establish independence either.

Future joint-event research must align game/player IDs, pregame timestamps, thresholds, pushes and selection criteria. Estimate event-specific dependence, validate the whole joint distribution prospectively, and report block-based uncertainty. Three-plus-leg payouts cannot be identified from pairwise correlations alone. All combinations remain blocked; no arbitrary correlation cutoff is used to certify safety or skill.
