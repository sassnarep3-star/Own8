# Own8 · NFL research lab

**Evidence before edge.** An official-source audit dashboard, transparent line-origination benchmark, and fail-closed strategy competition registry for singles, parlays and player-prop combinations.

**Live:** https://sassnarep3-star.github.io/Own8/  
**Requirements & decision review:** https://sassnarep3-star.github.io/Own8/requirements/index.html  
**Decision ledger (price store, results feed, fair/market/difference, demotion gate, signal-vs-staking):** https://sassnarep3-star.github.io/Own8/ledger/index.html  
**Decision review & readiness:** https://sassnarep3-star.github.io/Own8/decision-review/index.html  
**Executive brief:** https://sassnarep3-star.github.io/Own8/pages/executive-summary.html  
**Correlation audit (independent recomputation):** https://sassnarep3-star.github.io/Own8/correlation-audit/index.html  
**Signal desk (baselines, depth tiers, decision queue):** https://sassnarep3-star.github.io/Own8/signals/index.html  
**Market reality (verified price rows, decision gate):** https://sassnarep3-star.github.io/Own8/market/index.html  
**Flagged for Review:** https://sassnarep3-star.github.io/Own8/pages/flagged.html

## Executive summary · 2026-11-04 snapshot

> **Superseded for current numbers.** The section below describes the 04 Nov snapshot. For the latest dated result capture, read [What changed on 2026-11-17](#what-changed-on-2026-11-17-session-c38420f6), then the [15 Nov price/freshness integration](#what-changed-on-2026-11-15-final-integration-round-5--session-08643438) and the [requirements section](https://sassnarep3-star.github.io/Own8/requirements/index.html).

- Independently rechecked **32 standings core rows / 256 fields** against NFL.com; **15 Week 9 schedule entries**, **12 complete Week 8 scores**, **28 JAX/BAL practice entries**, and **two NFL news bodies**. Exact coverage: `data/sources.json` and `data/audit-snapshot.json`. Two score rows remain blank because their full source text was not observed. No claim of exhaustive external verification of all inherited files.
- Originates **15 illustrative B0 scoring benchmarks** from audited points-for/against rates. All are **derived project calculations**, not official NFL lines, calibrated fair prices or recommendations. Home handicap = projected away score − projected home score. No fitted venue/roster adjustment; the Madrid game does not receive a home-field assumption.
- Computes three **descriptive team correlations**, not betting-leg dependence. All parlay/player-prop correlation values remain blank.
- Registers **eight research strategies**. **Zero eligible strategies, no established betting edge, no ranks or rewards.** Missing operator prices, chronological test evidence, final availability and aligned joint outcomes block promotion.
- Removes unsupported claims that luck can be eliminated, unverified odds can yield verified candidates, or conditional gates count as passes. Statistical uncertainty cannot be eliminated.
- Catalogs **471 inherited JSON/CSV entries**, withholding unverified values; records file-level review scope, source links and review flags. Every canonical table row has an official reference or explicitly labeled verification target.


## What changed on 2026-11-15 (final integration round 5 · session 08643438)

- **The repository's central price claim was wrong and is now corrected (SG-03 / F-01 / X3).** The decision ledger asserted "no official source publishes this market" on all 39 Week 10 markets. That was false: nfl.com publishes a FanDuel line for every game in its weekly picks article, locked 2 p.m. ET Thursday. The price store now records **87 verified snapshot values** (29 games × 3 markets, Weeks 9–10) with their nfl.com URLs and verbatim text, and publishes **fair line, market line and the difference as three separate columns** per market (differences cross-checked 39/39 against the independent market/ computation). Opening and closing values stay blank, fail-closed: no official source publishes a market-open or market-close number. See [ledger/price-store](https://sassnarep3-star.github.io/Own8/ledger/price-store.html) and flags LF-01/LF-11.
- **The landing page now carries a decision-readiness table**: one row per requirement (RQ-01..16), the gate that blocks it, and the specific number that would clear it — every number quoted from a pre-registered register (G3 sample sizes ≥ 80/40/100, G7 ECE ≤ 0.10, D6 p_Holm < 0.05, Q-04's 6–8 game-weeks of Game Books), blank and flagged where no pre-registered number exists.
- **Fresh official re-verification (2026-11-15):** standings recomputed from the 137-game feed plus the eight Week 10 Sunday finals match all 32 official rows — **160/160 cells PASS**. The F-07 injury-report question is resolved: the 185 practice-only rows are the *real* official report shape (verified against the live page), not a capture artifact. The three Lions game-status requests (VR-08/VR-12) are superseded — the official page now shows all three Out; the report is a daily timestamped series. Evidence: [session-08643438/verification.json](session-08643438/verification.json).
- **Historical freshness state (V-03, 2026-11-15):** eight Week 10 Sunday finals were not yet in the feed at that capture. This was superseded by the 2026-11-17 addendum below: 12 Sunday finals have been added; LAC at BAL remains unresolved.
- The stale desk flagged page was regenerated (C-01..C-05 restored), and the duplicated coordination-board collision notes collapsed to one.


## What changed on 2026-11-17 (session c38420f6)

A fresh official-source re-read found the Week 10 line snapshot had fallen behind game results. The pre-kickoff forecasts and their original model inputs were preserved; a separate dated results addendum was added.

- **Official results feed:** 12 Sunday Week 10 games were checked individually against both [NFL Week 10 scores](https://www.nfl.com/scores/2026/week-10) and each [NFL Game Center](https://www.nfl.com/games/patriots-at-lions-2026-reg-10). Each displayed a score and `Final`. They are now appended to the [ledger results feed](https://sassnarep3-star.github.io/Own8/ledger/results-feed.html), which contains **149 final rows** (136 in the verified W1–W9 log, one Week 10 Thursday final, 12 Week 10 Sunday finals). The historical 136-game pregame corpus is unchanged.
- **One result is intentionally blank:** as read on 2026-11-17, the [LAC at BAL score page](https://www.nfl.com/scores/2026/week-10), [Game Center](https://www.nfl.com/games/chargers-at-ravens-2026-reg-10) and [official standings](https://www.nfl.com/standings/league/2026/REG) did not establish a final score. The fixture is excluded from the result feed and diagnostic. No reason or score is inferred.
- **Exploratory, not leaderboard:** the frozen Week 10 forecast was compared with the 12 observed finals. S1/S2/S3 side MAE = 11.4746 / 12.0628 / 8.9643 points; S4/S5 total MAE = 9.8204 / 10.1829; the locked-Thursday market comparison was 11.2083 side MAE and 8.8333 total MAE; S6 home-win Brier = 0.1785 vs 0.1678 for the de-vigged locked market. `n=12`; there are no confidence intervals, multiplicity adjustment, cluster bound, bet settlements or ROI in this diagnostic. **No skill claim, strategy rank, reward, or promotion follows.** Full per-game inputs, errors and official links: [`session-c38420f6/`](session-c38420f6/index.html).
- **Freshness and provenance flags:** the other model/standings pages still reflect their dated pregame snapshot and are not current power ratings; no postgame re-fit or full 32-team standings reconciliation was performed. This fetch path also did not retain raw HTTP bodies or hashes, so the addendum is timestamped structured evidence, **not an immutable/hash-verified capture**. See root flags A17–A19.

## What changed on 2026-11-14 (session f6e60a81)

The repository was last refreshed on 2026-11-04, when the official game log stopped at Week 8. Two weeks of football had been played since and nothing had failed, so this session re-captured the official data and, for the first time, graded the model against results it had never seen.

- **Official capture refreshed.** 15 Week 9 scores, the completed Week 10 Thursday game, the 14-game Week 10 slate and all 345 Week 10 injury rows are transcribed from nfl.com with their exact URLs. The official game log now runs to **137 games**. Recomputing every club's W-L-T, PCT, PF, PA, NET, HOME and ROAD from that log matches the official standings on **352 of 352 cells**.
- **The Week 9 lines were graded out of sample.** The 15 fair lines originated on 04 Nov were scored against the results: spread MAE **10.65**, total MAE **10.81**, home covers **5 of 15**, moneyline Brier **0.190**. At n = 15 none of that is distinguishable from a coin flip, and the site says so.
- **Week 10 lines originated (historical 2026-11-14 state).** 13 forecast values were labelled UNVALIDATED. At that capture, the originated-line table had no market values. The price source claim was corrected in the 2026-11-15 integration: the NFL Week 10 picks article publishes locked FanDuel lines (not opening/closing numbers). Twelve game outcomes are now captured separately; one remains unresolved (see 2026-11-17 update).
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
