# Own8 methodology

## Evidence and dates

Only audited `data/audit-snapshot.json` values enter the canonical engine. Retrieved on 2026-11-04 with the page-extraction tool; structured transcription, not retained raw HTTP. Verified fields are explicit; links alone do not certify a row. Other inherited rows are inventoried with numerical values blank. Date-only captures do not establish pre-kickoff availability for historical tests.

Official observations: https://www.nfl.com/standings/ and https://www.nfl.com/scores/2026/week-8 . Full source register: `data/sources.json`.

## B0 origination benchmark (project design, not official fair values)

- GP = W + L + T.
- Expected away score = (away PF/GP + home PA/GP) / 2.
- Expected home score = (home PF/GP + away PA/GP) / 2.
- Expected home margin = home score − away score.
- Home handicap = −expected home margin; expected total = sum of expected scores.
- No fitted home-field, opponent, pace or roster adjustment. Zero venue adjustment is a transparent design choice, not an estimated NFL parameter. B0 is blocked for use as a betting strategy.
- A mean margin does not identify a win probability, spread-cover probability, moneyline or prop threshold. No residual distribution was fitted; those values remain null.

## Pricing primitives (implemented/tested, no empirical input estimates)

American A ≥ +100 gives decimal d = 1 + A/100; A ≤ −100 gives d = 1 + 100/abs(A). Reject invalid prices. With p(win), p(push) and p(loss)=1−p(win)−p(push), EV per unit = p(win)(d−1)−p(loss). Never substitute a universal −110 quote.

For two binary events only, P(A and B) = pa pb + rho sqrt(pa(1−pa)pb(1−pb)); reject infeasible values outside [max(0,pa+pb−1), min(pa,pb)]. This is not a three-leg joint model. No actual bet-event estimates are supplied.

## Development protocol (proposed, not claimed completed)

Pre-register feature definitions, candidate variants, information cutoff, baseline, testing family and reward rule. Train on earlier seasons, tune only on rolling development folds, then lock settings before an untouched final season. Lag all player/team features by actual availability. Do not turn the current season snapshot into a historical backtest. Obtain official final results and operator-native timestamped lines, prices and settlement rules. Absent evidence blocks eligibility.

Evaluate proper scores (Brier and log loss), reliability/calibration, error by regime, abstention and stability. Compare paired losses against the frozen baseline with week/game-block uncertainty and multiplicity adjustment. Forecast scores, expected value, realized returns and CLV are different quantities; do not conflate them. No finite analysis guarantees future profit or removes chance.

Statistical context checked: [NIST association](https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm), [confidence intervals](https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm), [multiple comparisons](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm). These do not endorse our strategy designs.
