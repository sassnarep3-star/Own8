# Validation record — competition module

Checked 2026-11-04 UTC. This is a software / selected-field evidence record, **not
proof of betting skill or upstream response authenticity**.

## Completed checks

| Check | Executed result | Scope / qualification | Primary project source |
| --- | --- | --- | --- |
| Standard-library unit suite | **83 tests PASS** | Numeric/sign/price math; push/void/DNP handling; missing inputs; timestamp leakage; stale/edited receipts; all-PASS gating; exact combined payouts; hash/checkpoint tampering; official-score revisions; simultaneous publisher exposure; simultaneous grader idempotence; clustered statistics and Holm; actual selected-field snapshot. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/tests/test_competition.py) |
| Evidence pipeline | **PASS** | 32 standings, 15 fixtures, 14 finals, 15 primary game-price rows, 28 practice rows. Manifest hashes and selected-field arithmetic / identity checks only. Exact page fetch instants and raw upstream responses were not retained. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/data/sources.json) |
| Static site builder | **14 pages built** | Writes only competition/. Untrained B0 reference lines are labeled derived, not official or validated forecasts. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/scripts/build_site.py) |
| Local HTML / link / null checker | **PASS** | 347 local references; 876 data rows with relevant primary references; no missing internal targets/anchors; no malformed table dimensions; no fabricated empty performance or unqualified ranks/rewards. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/site-check.json) |
| Real Chromium browser | **42 page/viewport combinations PASS** | Chromium 153.0.8010.0 / Playwright 1.64.1. All 14 pages at 1440×1000, 390×844 and 320×740. No horizontal body overflow, page/console/request failures; keyboard/mobile menu, numeric sorting, filter clear/empty state, blank unknown performance and prop numbers. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/browser-check.json) |
| Source-coverage audit | **524 starting-data rows inventoried** | Selected fields only independently matched; every unsupported field value is null in the export. Row links on unverified records are review/context targets, not a verified badge. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/entry-audit.json) |
| Repository inventory | **104 starting tracked files inventoried** | Targeted code review + automated line/file inventory; **not exhaustive external verification of every line**. Baseline-specific findings are not presumed to apply to later parallel fixes. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/repository-audit.json) |
| Production competition | **Empty** | Zero genuine locked predictions, settlements, ranks or rewards. Synthetic tests never enter production metrics. No profit/skill claim. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/data/ledger.jsonl) |

Machine-readable check reports:
[site-check.json](results/site-check.json),
[browser-check.json](results/browser-check.json),
[evidence-check.json](results/evidence-check.json).

Local link validation does **not** recheck external HTTP liveness or certify
adjacent facts. Exact source review scopes are in [data/sources.json](data/sources.json).

## Issues found and fixed while testing

1. A malformed inherited LAC CSV record has a surplus field. The initial audit
   sorter raised a mixed `None`/string key error. The module now records an
   explicit parse anomaly without shifting columns or filling affected values.
   Shared source data was preserved read-only; finding C-F16 is published.
2. Replaced the misleading `registered_trials` output field with
   `trial_family_size`; a proposed catalog does not establish preregistration.
3. Settlement-rule evidence is supplied by the trusted reviewed adapter, never
   a ticket's self-certified PASS flag.
4. Added file-lock-protected atomic grader revision selection and publisher
   exposure accounting; parallel test calls cannot duplicate grades/overspend.
5. Real-browser testing caught mobile min-content overflow in the overview grid.
   Added min-width constraints and reran all pages at two phone sizes.
6. Minimal sandbox Chromium needed its packaged NSS libraries, and a
   single-process runtime could not survive multiple contexts. The isolated
   test harness uses packaged libraries, normal multi-process Chromium and
   does not disable same-origin web security. No browser binaries/dependencies are
   committed.
7. Markdown downloads can be transformed by Jekyll. A static
   `executive-summary.txt` download and a GitHub README link avoid broken
   `.md` routes in the live static site.

## Reproduce browser checks (optional)

Standard Python checks require no installed packages. The optional browser check
installs **test-only** packages under ignored competition/.cache/browser:

```sh
npm install --prefix competition/.cache/browser --no-package-lock --ignore-scripts \
  playwright-core@1.64.1 @sparticuz/chromium@153.0.0
# Run a static server bound to 0.0.0.0 on port 8816, serving competition/.
node competition/tests/browser_smoke.cjs
```

The server is already running in the Arena live preview during this session;
no user input is needed. `BROWSER_BASE_URL` can point the harness at another
**competition-root** static server. The browser check visits only our local
pages; it never contacts an operator or places a bet. Screenshots remain in
ignored competition/.cache/ rather than adding large generated files to Git.

## Requirements and explicit boundaries

| Requirement | Delivery | Unresolved / published limitation | Primary project source |
| --- | --- | --- | --- |
| Own lines | 15 transparent B0 research handicaps/totals | Untrained benchmark; no validated fair probabilities/edges (C-F07). | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/reference-lines.json) |
| Singles/parlays/props | Eight proposed hypotheses; all category pages; exact contract and settlement math | No prospective OOS tickets or qualified strategy (C-F01). | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/data/strategy-catalog.json) |
| Every strategy validated before promotion | Eight admission / nine promotion gates, all-PASS only | No empirical gate passes; minimum counts are policy, not proof of power. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/scripts/ledger.py) |
| Correlation discipline | Three descriptive coefficients; four unknown bet correlations blank | No independence assumption or measured joint wager sample (C-F09). | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/correlations.json) |
| Skill vs luck | Frozen receipts/holdouts, exact-price returns, week clusters and trial-family correction | Cannot remove luck; dependence and selection can invalidate coverage (C-F14). | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/scripts/evaluation.py) |
| Real leaderboard/rewards | Append-only empty production ledger; conditional symbolic-point protocol | No invented ranks/results; rewards remain blank. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/leaderboard.json) |
| Executive/source/repository review | Executive brief, source register, 524-row coverage and 104-file inventory | Review scope explicitly bounded; no blanket all-line certification (C-F10/C-F12). | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/README.md) |
| Clean Pages dashboard | 14 responsive source-linked pages; static assets and direct-route publishing | Root navigation/CI are integration-owner scope; request logged, not overwritten. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/index.html) |
| Unknown factual values blank | Null export cells and genuinely empty rendered cells with unverified labels | Raw legacy files remain preserved behind canonical publication exclusions. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/results/entry-audit.json) |
| Live automation | Tested receipt, grading and correction APIs; unattended snapshot builds | Complete refresh/registration/rules/outcome adapters and production emitter missing (C-F11). | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/automation/README.md) |
| Irregularities published | 16 flags, all source-linked | Non-blocking website flags still block unsupported strategy eligibility. | [Primary record](https://github.com/sassnarep3-star/Own8/blob/main/competition/data/flags.json) |

PR/merge/deployment outcome is recorded separately in the session's section of
COORDINATION.md and competition/DEPLOYMENT.md after release. No result is claimed
here before that operation completes.
