# Strict evidence audit · 2026-11-04

## Scope, not blanket certification

Read and inventoried all 104 base tracked text files, recording line counts and SHA-256 in `strict/repository-inventory.json`. Inspected original analysis and generation code for source use, missing values, sign conventions, gate aggregation, correlation units and leaderboard claims. The inventory is not a statement that every inherited factual assertion was independently verified. Legacy captures not explicitly rechecked remain unverified. Later concurrent additions are preserved with their owners' scope statements, not certified by this session.

## Official evidence actually checked

- [NFL standings](https://www.nfl.com/standings/): both fetched chunks; 32 team names plus W,L,T,PCT,PF,PA,NET. 224 numerical fields match legacy JSON. HOME/ROAD/DIV/CONF columns not re-certified.
- [NFL Week 9 schedule](https://www.nfl.com/schedules/2026/by-week/week-9): all three chunks; 15 matchups/dates and Madrid label. Kickoff timezone and venue fields omitted.
- [NFL Week 9 injuries](https://www.nfl.com/injuries/league/2026/reg9): selected eight DNP observations in JAX/BAL; blank diagnoses/statuses preserved. Not a complete team/league capture.
- [Hurts article](https://www.nfl.com/news/eagles-qb-jalen-hurts-out-2026-season-blood-clots): likely/expected wording preserved; no quantitative injury adjustment inferred.
- [NGS glossary](https://nextgenstats.nfl.com/glossary): metric definitions; not a full player-game dataset.
- [NFL Big Data Bowl](https://operations.nfl.com/programs-initiatives/innovation/big-data-bowl): competition context, not betting skill evidence.
- [NFL repository games](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv), [schema](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/schema.md), [README](https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/README.md): downloaded via GitHub API, pinned, SHA-256 verified. 91 unique games; six 2017 weeks only. Game identifiers, week/season and scores checked row by row for expected types, uniqueness and range. SHA verification establishes reproduction against the official bytes, not a second independent score feed.
- [NIST autocorrelation](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm): randomness/dependence cautions; no endorsement of Own8 thresholds or specific methods.
- [Washington regulator](https://wsgc.wa.gov/tribal-partnerships/sports-wagering): resource verified, not legal eligibility.

Selected web observations are transcriptions, not full raw HTML archives. Their retrieval dates and scope are retained in `strict/evidence/`. No inferred missing values or bookmaker quotes.

## Findings

A01–A17 are published in `strict/flags.json` and the Flagged for Review page. The prior engine admitted unverified prices, used the opposite home-spread convention, accepted conditional gates, and exposed candidates independent of aggregate validation. It also used ecological team correlations as bet-leg proxies and offered unsupported skill/automatic grading claims. New engine fails closed, separates mean margin from handicap proxy, never treats a mean as a calibrated median, and leaves all current fair/market/return metrics null.

All inherited review rows remain visible as historical claims, explicitly not recertified. Concurrent main fixes withholding market lines and the independent `audit/` and `verification/` outputs are preserved. Root/duplicate HTML is untouched after the scope handoff; old source snapshots are available in Git history. PR #6 findings are not imported or endorsed.

## Actual research outcome

60 rolling-week development predictions: margin MAE 10.426 versus 10.024 baseline; total MAE 12.318 versus 12.181. No predictive improvement. Four week clusters/one partial season; seeded 4,000-resample intervals are illustrative. No claims of bet return, calibrated probabilities, multi-season skill or operational readiness. A real validation exercise needs longer official history, primary quotes/rules, matched player panels and locked forward outcomes.

## Reproduction and release

Namespaced commands in strict/README.md run standard-library-only build, unit tests and local links/row-source checks. Independent baseline `audit/check.py` intentionally expects the old schema; it is preserved historical evidence, not a current release test. Local source-link checking is not external liveness verification. GitHub check, merge and Pages records are logged in COORDINATION.md and `strict/deployment.json` when actually observed.

## Final scope handoff
Fresh PR #19 exposed a simultaneous canonical claim. To avoid ongoing overlap, this session yielded root files to dd321bf5, restored all root shared files exactly from main and publishes only strict/site plus namespaced evidence/code/tests. The new dashboard remains independently accessible. Shared raw captures, audit/, verification/ and other pending namespaces are preserved.
