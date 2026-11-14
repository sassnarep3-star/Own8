# Own8 · NFL research lab

**Evidence before edge.** An official-source audit dashboard, transparent line-origination benchmark, and fail-closed strategy competition registry for singles, parlays and player-prop combinations.

**Live:** https://sassnarep3-star.github.io/Own8/  
**Requirements & decision review:** https://sassnarep3-star.github.io/Own8/requirements/index.html  
**Decision ledger (price store, results feed, fair/market/difference, demotion gate, signal-vs-staking):** https://sassnarep3-star.github.io/Own8/ledger/index.html  
**Decision review & readiness:** https://sassnarep3-star.github.io/Own8/decision-review/index.html  
**Executive brief:** https://sassnarep3-star.github.io/Own8/pages/executive-summary.html  
**Correlation audit (independent recomputation):** https://sassnarep3-star.github.io/Own8/correlation-audit/index.html  
**Signal desk (baselines, depth tiers, decision queue):** https://sassnarep3-star.github.io/Own8/signals/index.html  
**Flagged for Review:** https://sassnarep3-star.github.io/Own8/pages/flagged.html

## Executive summary · 2026-11-04 snapshot

> **Superseded for current numbers.** The section below describes the 04 Nov snapshot. For the current state of the data, the out-of-sample grading and the review queue, read [What changed on 2026-11-14](#what-changed-on-2026-11-14-session-f6e60a81) below and the [requirements section](https://sassnarep3-star.github.io/Own8/requirements/index.html).

- Independently rechecked **32 standings core rows / 256 fields** against NFL.com; **15 Week 9 schedule entries**, **12 complete Week 8 scores**, **28 JAX/BAL practice entries**, and **two NFL news bodies**. Exact coverage: `data/sources.json` and `data/audit-snapshot.json`. Two score rows remain blank because their full source text was not observed. No claim of exhaustive external verification of all inherited files.
- Originates **15 illustrative B0 scoring benchmarks** from audited points-for/against rates. All are **derived project calculations**, not official NFL lines, calibrated fair prices or recommendations. Home handicap = projected away score − projected home score. No fitted venue/roster adjustment; the Madrid game does not receive a home-field assumption.
- Computes three **descriptive team correlations**, not betting-leg dependence. All parlay/player-prop correlation values remain blank.
- Registers **eight research strategies**. **Zero eligible strategies, no established betting edge, no ranks or rewards.** Missing operator prices, chronological test evidence, final availability and aligned joint outcomes block promotion.
- Removes unsupported claims that luck can be eliminated, unverified odds can yield verified candidates, or conditional gates count as passes. Statistical uncertainty cannot be eliminated.
- Catalogs **471 inherited JSON/CSV entries**, withholding unverified values; records file-level review scope, source links and review flags. Every canonical table row has an official reference or explicitly labeled verification target.


## What changed on 2026-11-14 (session f6e60a81)

The repository was last refreshed on 2026-11-04, when the official game log stopped at Week 8. Two weeks of football had been played since and nothing had failed, so this session re-captured the official data and, for the first time, graded the model against results it had never seen.

- **Official capture refreshed.** 15 Week 9 scores, the completed Week 10 Thursday game, the 14-game Week 10 slate and all 345 Week 10 injury rows are transcribed from nfl.com with their exact URLs. The official game log now runs to **137 games**. Recomputing every club's W-L-T, PCT, PF, PA, NET, HOME and ROAD from that log matches the official standings on **352 of 352 cells**.
- **The Week 9 lines were graded out of sample.** The 15 fair lines originated on 04 Nov were scored against the results: spread MAE **10.65**, total MAE **10.81**, home covers **5 of 15**, moneyline Brier **0.190**. At n = 15 none of that is distinguishable from a coin flip, and the site says so.
- **Week 10 lines originated.** 13 fair numbers for the games not yet played, labelled UNVALIDATED, with no market price and no edge, because no official source publishes one.
- **New review layer.** `requirements/` publishes a requirement register (16 rows), an open-question register (22 rows), a suggestions section (16 proposals, every decision still open), an availability and deficiencies register, a luck decomposition, a verification log and a review register (15 flags). Every table row carries an official source link and `requirements/scripts/check_req.py` fails the build if one does not.
- **One hard limit, stated plainly.** The requirement to know when a 2nd, 3rd or 4th string player is replacing a starter is only half achievable. The nfl.com depth-chart URL returns **404**, the roster page publishes only a status code, and the only official page naming actual starters is the **NFL Game Book PDF**, which appears after the game.

Start here: [executive summary](https://sassnarep3-star.github.io/Own8/requirements/pages/executive-summary.html) · [suggestions for your decision](https://sassnarep3-star.github.io/Own8/requirements/pages/suggestions.html) · [open questions](https://sassnarep3-star.github.io/Own8/requirements/pages/questions.html) · [flagged for review](https://sassnarep3-star.github.io/Own8/requirements/pages/flagged.html)

### Reproduce the new work

```sh
python3 requirements/scripts/verify_capture.py      # capture checks, 352-cell reconciliation, W9 grading, W10 lines
python3 requirements/scripts/analyze_availability.py # availability register + luck decomposition
python3 requirements/scripts/build_checks.py         # merge every check family into one result file
python3 requirements/scripts/build_flags.py          # review register
python3 requirements/scripts/req_site.py             # the section pages
python3 requirements/scripts/check_req.py            # every row sourced, every link resolves
```

## Reproduce the inherited root dashboard (Python 3.11+, standard library only)

```sh
python3 scripts/audit_repo.py
python3 scripts/analyze.py
python3 -m unittest discover -s scripts -p 'test_audit.py' -v
python3 scripts/build_site.py
python3 scripts/check_links.py
```

`.github/workflows/audit.yml` runs these checks for pushes/PRs and daily, uploads an audited preview artifact. The existing legacy GitHub Pages main/root pipeline publishes the site; `_config.yml` excludes legacy archive/capture surfaces. It validates/rebuilds the **dated snapshot**; it does **not** implement unattended fresh official-data capture, sportsbook access, future settlement or a live odds feed. No user input was needed for this session. Unavailable inputs stay null; strategy eligibility fails closed. Build PASS is not evidence-gate PASS.

## Evidence boundary

`data/audit-snapshot.json` is the only numeric input to the canonical analysis. It is a structured audit transcription following official-page retrieval, **not raw HTTP capture**. Checked fields are bounded explicitly. Dynamic pages can change. `analysis/audit-inventory.json` lists all inherited entries; their labels are identifiers, not verified player/team facts. Local arithmetic and cross-capture agreement are not substitutes for official verification.

Official sources checked: [NFL standings](https://www.nfl.com/standings/), [schedule](https://www.nfl.com/schedules/2026/by-week/week-9), [scores](https://www.nfl.com/scores/2026/week-8), [injuries](https://www.nfl.com/injuries/league/2026/reg9), [NGS glossary](https://nextgenstats.nfl.com/glossary), [NIST association](https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm), [confidence intervals](https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm), [multiplicity](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm), [Washington resources](https://wsgc.wa.gov/responsible-gaming-self-exclusion). Registry contains news links and exact source scope. Statistical references do not endorse our model or proposed competition rules.

## Repository layout

- `index.html`, `pages/`, `assets/`: generated, responsive, searchable static dashboard; no CDN/dependencies.
- `data/audit-snapshot.json`, `sources.json`, `flagged.json`: audited extract, source coverage, review register.
- `scripts/audit_math.py`, `analyze.py`, `audit_repo.py`, `test_audit.py`, `check_links.py`, `build_site.py`: computation, bounded verification, regression tests and site generation.
- `analysis/`: derived outputs and software-check reports, not official NFL publications.
- `research/`: executive summary and proposed research/competition methods.
- `COORDINATION.md`: task ownership, handoffs, conflicts, PR and deployment record.
- `archive/`, old root data CSV/JSON/Markdown, `compute_correlations.py`: historical artifacts retained for audit, **not authoritative**. Excluded from publication by `_config.yml` in the legacy Pages build.
- `docs/*.html`: redirects to audited canonical pages.
- `audit/`: concurrent session 74efc1ec's independent baseline audit, preserved unchanged. Its findings refer to baseline commit 7c2f545, not the new canonical outputs.

## Responsible research

No real-money bets, stakes, cash rewards, automatic wagering or guarantees. Proposed rewards are paper points only and none are awarded. See [Washington State Gambling Commission resources](https://wsgc.wa.gov/responsible-gaming-self-exclusion). No personalized legal determination or unsupported jurisdiction assumption.
