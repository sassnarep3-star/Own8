# Own8 executive summary — proof before points

**Checked 4 November 2026 UTC · Research only · No live selections**

## Decision

The NFL paper-competition and settlement module is ready for evidence review and
software testing, **not for claims of demonstrated betting skill**. No locked
forecast, settled ticket, skill-qualified strategy, rank or reward exists. The
leaderboard leaves unavailable performance cells blank instead of inventing zero
returns. A statistical process can reduce false discoveries; it cannot remove
luck or guarantee future profitability.

## Important findings

| Topic | Result / qualification | Official reference |
| --- | --- | --- |
| League evidence | 32 core standings rows, 15 Week 9 fixtures and 14 final Week 8 results checked against selected official fields. Not every inherited column is verified. | [NFL standings](https://www.nfl.com/standings/), [schedule](https://www.nfl.com/schedules/2026/by-week/week-9), [scores](https://www.nfl.com/scores/2026/week-8) |
| Own reference lines | 15 B0 spreads/totals computed from checked scoring rates. Home advantage is zero by declared benchmark design, including Madrid. These are **untrained project outputs**, not official or validated fair prices; probabilities and edges are blank. | [NFL standings](https://www.nfl.com/standings/), [NFL schedule](https://www.nfl.com/schedules/2026/by-week/week-9) |
| Primary market evidence | 15 spread/total/moneyline rows observed directly on DraftKings' page, not a third-party aggregator. Individual quote-update instants and exact retrieval times are unconfirmed: snapshot only, freshness HOLD. | [Primary operator page](https://sportsbook.draftkings.com/leagues/football/nfl) |
| Source disagreement | NFL lists LV at SF at 4:25 PM EST; operator renders 4:05 PM. NFL governs the fixture lock. No operator time is substituted. | [NFL schedule](https://www.nfl.com/schedules/2026/by-week/week-9), [NFL injuries](https://www.nfl.com/injuries/league/2026/reg9), [operator](https://sportsbook.draftkings.com/leagues/football/nfl) |
| Availability | 28 JAX/BAL practice rows transcribed; injury and game-status cells are blank. Other playing teams render “No Injuries Reported,” not confirmed healthy starters. | [NFL Week 9 report](https://www.nfl.com/injuries/league/2026/reg9) |
| Prop combos | Eight selected prop-page names/event groups checked; numerical ladder/price pairing ambiguous. Lines, prices and combo correlations remain blank. | [Primary prop page](https://sportsbook.draftkings.com/leagues/football/nfl?category=games&subcategory=player-props&nav_1=pass-yards) |
| Correlations | Three descriptive coefficients computed from checked scoring/standings fields. Four true wager-outcome correlations remain blank. Different games do not establish independence. | [NFL scores](https://www.nfl.com/scores/2026/week-8), [SciPy Pearson documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html), [NIST dependence](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm) |
| Settlement | Exact prices and full contract rules are required; pushes, voids, DNP, ties and SGP repricing are held rather than guessed. Introductory operator guides do not establish a complete current rulebook. | [Operator market guide](https://sportsbook.draftkings.com/help/how-to-bet/football-betting-guide), [parlay guide](https://sportsbook.draftkings.com/help/how-to-bet-parlay) |
| Skill competition | Eight proposed hypotheses across singles, parlays and props; none is prospectively registered or validated. All eight admission and nine promotion gates must pass at their respective stages. | [NIST uncertainty](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm), [Holm documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html) |
| Rewards | Proposed top-three 100 / 60 / 30 symbolic points only, after complete validation. Ranking objective is a simultaneous lower net-ROI limit, not raw win rate or a lucky week. These are project policies, not official recommendations; no points awarded. | [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm), [Holm documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html) |

## Skill validation design — explicitly project policy

1. Freeze model versions, the complete variant family, training cutoffs and two
   non-overlapping holdouts **before** outcomes. Publish prediction hashes using
   externally timestamped, unedited GitHub receipts before every kickoff.
2. Require exact source-timed primary prices, final participation evidence,
   market-specific settlement rules and exact combined quotes. No default vig,
   cross-game independence or assumed player rates.
3. Grade official final outcomes; append corrections without rewriting forecasts
   or double-counting settlement revisions.
4. Screen at least 200 settled tickets over 20 NFL season-week clusters; require
   positive returns in two frozen holdouts, positive simultaneous lower net-ROI
   limit and Holm-adjusted null rejection across **all** tested variants.
5. Require calibration improvement against a contemporaneous normalized market
   benchmark, matched CLV support and overlapping-exposure checks. CLV alone is
   not proof of profitability.
6. Make a single frozen final evaluation. The current protocol proposes
   2027-03-01; this date is not an official NFL requirement. No repeated
   significance peeking. Resampling assumes exchangeable week clusters; serial
   dependence and regime change can invalidate coverage. Minimum sample counts
   alone do not prove adequate power.

Method references: [NIST confidence limits](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm),
[NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm),
[NIST time dependence](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm),
[statsmodels multiple-testing documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).
These support the statistical background, not a claim that this specific
competition design is endorsed or proven.

## Repository review and limitations

The module inventories **104 files and 524 root-data rows at starting commit
7c2f545**. It performs targeted code review and selected-field official checks,
not exhaustive external verification of every inherited line. Unsupported cells
are null in the audit export. The inherited Chargers CSV row has an extra field
that shifts trailing labels; only independently matched core fields are kept.

Original root code also contained a spread-sign error, permissive conditional
and unverified-price gates, and fabricated zero leaderboard points. Other active
sessions own root remediation; this module does not overwrite their files or
presume that a later fix remains defective. Baseline-specific code links and all
16 irregularities appear on **Flagged for Review**.

The site builds/tests unattended from checked snapshots. Receipt, grading and
correction APIs are tested with **synthetic fixtures only**, never mixed with
production sports evidence. No continuous refresh schedule, complete rulebook
adapter or production strategy emitter is enabled here. Nonempty production
ledgers cannot be promoted until independent receipt/outcome verification is
integrated. This is disclosed as an operational limitation, not represented as a
live automated betting system.

## Deliverables and safety

- Category dashboard: https://sassnarep3-star.github.io/Own8/competition/
- Review flags: https://sassnarep3-star.github.io/Own8/competition/flagged.html
- Reproduction and evidence scope: [README.md](README.md), [source register](data/sources.json).

No real-money wagering, purchase, deposits or cash rewards occur. Washington's
regulator describes limited tribal-facility sports wagering and on-premises
mobile requirements; a visible web price is not legal availability at a user's
location. [Official Washington rules](https://wsgc.wa.gov/tribal-partnerships/sports-wagering/sports-wagering-requirements-and-rules).

The current NCPG help page lists call/text **1-800-MY-RESET (1-800-697-3738)**:
https://www.ncpgambling.org/help-treatment/.
