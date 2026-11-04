# Own8 — paper competition and settlement module

**Live subsite:** https://sassnarep3-star.github.io/Own8/competition/

**Executive brief:** [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)

**Executed-check record:** [VALIDATION.md](VALIDATION.md)

**Evidence checked:** 2026-11-04 UTC. **State: research only, no live selections.**

This is an isolated addition to Own8, not a competing root dashboard. Its scope is
`competition/**`. Other sessions own the root generators/data/navigation. Starting
repository audit: `7c2f5459350c8a94f13cd12d4315ba92b044275a`.

## What exists

- A clean 14-page category dashboard, including single bets, parlays, player-prop
  combos, validation gates, leaderboard, sources, source coverage and **Flagged
  for Review**. Tables are searchable/sortable; the site works without JavaScript.
- Selected-field official transcriptions: **32 standings rows, 15 Week 9 fixtures,
  14 Week 8 final results, 28 Week 9 JAX/BAL practice rows**. Every rendered row
  has an official reference. Unknown injury/game-status fields are null.
- **15 primary DraftKings game-line rows**, not aggregator quotes. The publisher
  is authoritative for what its own page displayed, **not** for NFL results,
  legality in Washington, current availability or true win probabilities.
- **15 untrained B0 reference spreads/totals** from checked scoring rates. The
  explicit benchmark sets home advantage to zero everywhere, including Madrid.
  These are derived project outputs, not official or validated fair prices.
  Win probabilities, betting edges and uncertainty intervals stay null.
- Three descriptive correlations from checked NFL fields. Four actual wager-leg
  correlations remain null. There is no default cross-game independence.
- **524 inherited root-data rows** audited for field coverage; unsupported values
  are null in the export. **104 starting files / all their text lines** are
  inventoried. This is **not** a claim of exhaustive external fact verification.
- A real, deliberately empty prediction ledger; zero ranked or rewarded
  strategies. Eight **proposed** hypotheses are catalog entries, not externally
  preregistered, skill-qualified strategies.

## Reproduce without user input

Python 3.10+ with standard library only; `zoneinfo` needs the system timezone
catalog (present in GitHub's Ubuntu/Python runners).

```sh
python3 -m unittest discover -s competition/tests -v
python3 competition/scripts/pipeline.py
python3 competition/scripts/build_site.py
python3 competition/scripts/check_site.py
```

No file outside `competition/` is modified by those commands. The pipeline reads
starting-commit objects with `git show`; CI must fetch enough Git history to
include that commit (`fetch-depth: 0` if using checkout in a new runner).
Outputs are deterministic for the committed snapshots. No frozen snapshot is
presented as a live refresh. Source raw HTML and exact page-fetch instants were
not retained; SHA-256 verifies the transcriptions' subsequent local integrity,
not the authenticity of upstream HTML.

## Core contracts

### Admission versus promotion

`ledger.admission` evaluates **eight ticket gates**: exact NFL fixture, external
pregame receipt, exact source-timed primary prices, final participation evidence,
joint model when applicable, prior model registration, explicit/atomic paper
exposure limits and reviewed operator rules. `CONDITIONAL` and unknown are **not
PASS**. Project policies: at most two legs, one research unit per ticket, ten
open units, 15-minute price-age and 24-hour participation-report limits.

A paper ticket passing admission would still not prove skill. Promotion uses nine
additional gates, including a declared 200-ticket/20-week screen, two frozen
holdouts, positive simultaneous lower net-ROI limit, Holm adjustment across all
variants, calibration and CLV support, portfolio checks and a fixed final look.
These are **project design choices**, not official standards or proof of power.
Week-block exchangeability is an assumption. Shared teams, serial dependence,
regime shifts and selection bias can invalidate uncertainty estimates.

**Luck cannot be eliminated.** Positive historical returns, CLV or a small
p-value never guarantee future profitability. No strategy in this module has
passed promotion.

### Publication and integrity

`GithubReceipts` obtains/reads a real GitHub issue-comment receipt through `gh`.
The server `created_at` must equal `updated_at`, and its body must contain the
exact payload hash. The timestamp must precede **every** kickoff and follow the
training cutoff. A local hash alone is not proof of publication time.

`publish_prediction` atomically checks existing open exposure under a file lock,
checks all admission gates and appends only qualified **paper** entries. A
rejected attempt may leave a rejected receipt but never a competitive prediction.

The append-only JSONL chain detects content/order changes; a saved checkpoint
also detects removed tails. Trusted external receipts/checkpoints and reviewed
source adapters remain necessary. Low-level append functions or arbitrary JSON
flags are **not** a verification service or a way to certify an entry.

### Settlement and corrections

- Signed handicap convention: selected-team final margin **plus** its signed
  handicap determines cover/push/loss. A fair home handicap is the negative of
  expected home margin.
- Actual American/decimal prices are explicit. No default `-110` is substituted.
- Win profit = stake × (decimal odds − 1); losing profit = −stake. Returned
  stake is not profit. No result, unknown result and zero statistic are distinct.
- Whole-ticket combined prices are required. A push, void, DNP, tie or repricing
  case is held without complete market-specific rules and exact revised odds.
- `settle_prediction` rechecks admission/receipt evidence, grades official final
  fields and appends idempotent correction revisions. `latest_settlements`
  prevents counting a correction as an extra winning/losing ticket.

### Real deployment boundary

The production ledger is genuinely empty. Exact price update/observation instants,
final game availability, complete operator settlement rules, calibrated joint
models and prospective strategy emitters are missing. The production report
**refuses** to promote a nonempty ledger until a reviewed receipt/outcome adapter
is installed. APIs are covered by **synthetic tests only**, not live betting or
an actual return backtest. Synthetic fixtures never enter production data/site
metrics.

No continuous refresh/scheduled grading workflow is enabled by this isolated
module, because other sessions own shared workflow/settings scopes. The
integration contract is in [automation/README.md](automation/README.md), and this
limitation is published as C-F11. There is no hidden promise of unattended live
picks, weekly grading or real-money wagering.

## Evidence and official references

The complete review scope for each source is in [data/sources.json](data/sources.json).

- NFL standings: https://www.nfl.com/standings/
- NFL fixtures: https://www.nfl.com/schedules/2026/by-week/week-9
- NFL final results: https://www.nfl.com/scores/2026/week-8
- NFL injury report: https://www.nfl.com/injuries/league/2026/reg9
- NFL NGS definitions: https://nextgenstats.nfl.com/glossary
- Primary price observation: https://sportsbook.draftkings.com/leagues/football/nfl
- Operator odds definitions: https://sportsbook.draftkings.com/help/how-to-bet-reading-odds
- Operator football guide: https://sportsbook.draftkings.com/help/how-to-bet/football-betting-guide
- Operator parlay guide: https://sportsbook.draftkings.com/help/how-to-bet-parlay
- Pearson method: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
- Uncertainty: https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm
- Bootstrap: https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm
- Time dependence: https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm
- Holm correction: https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html

## Review flags

All 16 current issues appear on [flagged.html](flagged.html) and in
[data/flags.json](data/flags.json). Important: missing quote-update timestamps;
NFL/operator LV–SF kickoff discrepancy; ambiguous prop ladders; practice ≠ game
status; complete rulebook unavailable; untrained baseline; no measured wager-leg
correlation; inherited verification overclaims; automation handoff; selected-field
transcription limits; wrong inherited Netherlands assumption; statistical-policy
caveats; an inconsistent fractional-odds guide example; and the inherited LAC CSV
row's surplus field/shifted tail labels.

## Research safety

No cash rewards, purchase, account funding, real-money wager, bookmaker
intermediation or location bypass exists here. Proposed rewards are symbolic
points only, and none have been awarded.

Washington official rules: https://wsgc.wa.gov/tribal-partnerships/sports-wagering/sports-wagering-requirements-and-rules

NCPG currently lists call/text **1-800-MY-RESET (1-800-697-3738)**:
https://www.ncpgambling.org/help-treatment/
