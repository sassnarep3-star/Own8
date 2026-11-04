# COORDINATION.md — Shared Task Board (Own8 / NFL Lines Project)

Read this before starting any task. Claim a task by writing your session ID and
file scope, then commit and push the claim immediately. Never start a task
another session has claimed. Keep scopes non-overlapping. If a task requires
changing a file owned by another session, log the request below instead of
editing it. Make small, frequent commits; `git pull --rebase` before every push.
If a claim is >60 minutes old with no commits, another session may take it over
and note the handoff here.

## Sessions

| Session ID | Branch | Status | Notes |
| --- | --- | --- | --- |
| 9cf451e4 | arena/9cf451e4-own8 | merged to main (PRs #1–#4) | First session: data CSVs, strategy framework docs, root site (now archived), Pages enabled (main /). |
| 95e9626f | arena/95e9626f-own8 | active (integration) | This session: full JSON data pipeline, analysis, unified dashboard site, PR #5. |
| d22c14b9 | arena/d22c14b9-own8 | active (verification + correction) | Live re-verification of official data as of 2026-11-04; W9 injury report now published; G6 candidate correction; flags F-04/F-05/F-20..F-25; PR to main. Branch name fixed by operator instructions (see F-25). |

## Task Board

### Session 9cf451e4 (merged)

| # | Task | Status | Owner | Files | Sources / verification | Irregularities |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Coordination board | done | 9cf451e4 | COORDINATION.md | — | — |
| 2 | Official NFL data research | done | 9cf451e4 | data/nfl-2026-*.csv, data/sources.md | nfl.com/standings, nextgenstats.nfl.com (2026-11-03) | IR-01 player totals flagged UNVERIFIED (now F-12) |
| 3 | Strategy framework | done | 9cf451e4 | data/strategies.md, data/correlations.md, compute_correlations.py | team-level Pearson from verified standings | 7 strategies PAUSED on snapshot by design |
| 4 | Executive summary | done | 9cf451e4 | docs/executive-summary.md (now archive/session-9cf451e4-own8/docs/) | nfl.com, nextgenstats | — |
| 5 | Site creation | done | 9cf451e4 | index.html, pages/, assets/ (now archive/session-9cf451e4-own8/) | rows link to nfl.com/nextgenstats | 0 broken internal links at their check |
| 6 | Verification pass | done | 9cf451e4 | data/, site | 32 standings rows cell-verified vs nfl.com | IR-02 curl blocked (fetch_page used); IR-03 some nfl.com stats URLs 404 |
| 7 | Flagged-for-review page + registry | done | 9cf451e4 | pages/flagged-for-review.html (archived) | F-01..F-07 registry, IR-01..IR-03 | odds/injuries/history blank (not official) |
| 8 | Integration merge + re-verify | done | 9cf451e4 | all | pre-merge link check 0 broken; PRs #1–#3 merged | Pages "built" |
| 9 | PR to main + Pages deploy record | done | 9cf451e4 | repo settings | PR #1 (2c2e736), #2 (2154181), #3 (19760af) merged; PR #4 (30194ba) final; Pages main / → https://sassnarep3-star.github.io/Own8/ built | see their log below |

### Session 95e9626f (this session)

| ID | Task | Status | Owner | Files | Sources / verification | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Repo review + board | done | 95e9626f | COORDINATION.md, README.md | repo was empty except README at 9bd72f5 | no irregularities in pre-existing content |
| T2 | Official data capture | done | 95e9626f | data/*.json | nfl.com + nextgenstats.nfl.com, 2026-11-03; column orders arithmetic-validated | W9 injury report not yet published (F-04) |
| T3 | Analysis pipeline | done | 95e9626f | scripts/analyze.py, analysis/*.json | computed from data/*.json only | assumptions labeled (F-07); W9 candidates CIN@ATL, NYG@PHI |
| T4 | Research docs + exec summary | done | 95e9626f | research/*.md | official links; Ksa + NCPG | — |
| T5 | Site build | done | 95e9626f | scripts/build_site.py → index.html + pages/ + assets/ | generated; no external CDN | unified dashboard, per-row source links |
| T6 | Line-by-line verification + flags | done | 95e9626f | scripts/check_links.py, scripts/verify_combined.py, data/flagged.json, analysis/link-check.json, analysis/verification.json | link check PASS (46 pages, 2712 links, 0 broken); combined-data check PASS (32 teams, 0 mismatches) | F-01..F-13 on Flagged for Review page |
| T7 | Final integration: merge origin/main, re-verify combined data, unify site at root, PR #5 to main, merge, confirm Pages deploy, record here | done (corrected 2026-11-04 by d22c14b9; was still marked in progress after PR #5 merged) | 95e9626f | COORDINATION.md, README.md, archive/ | see log | PR #5 MERGED: https://github.com/sassnarep3-star/Own8/pull/5 |
| T8 | Live official re-verification as of 2026-11-04 (standings 32x11 fields, W9 schedule 15 games + byes, W9 injury report CIN@ATL/NYG@PHI, news items), G6 gate correction, flag register update, site rebuild | done (pending PR merge; see log) | d22c14b9 | data/injuries-2026-week9-candidates.json, data/flagged.json, scripts/analyze.py, scripts/build_site.py, analysis/live-*.json, research/*.md, README.md, COORDINATION.md | Sources: https://www.nfl.com/standings/ (32 teams, 11 fields: 0 mismatches), https://www.nfl.com/schedules/2026/by-week/week-9 (15 games, byes PIT/TEN match), https://www.nfl.com/injuries/league/2026/reg9 (CIN/ATL/NYG/PHI 'No Injuries Reported'), nfl.com news Hurts + McLaurin (text matches). Link check PASS (2717 links, 0 broken). | Corrections: G6 PASS on unverified market demoted (F-23); F-04 updated; F-20 wording; F-21 news age; F-22 13 W9 games not transcribed; F-24 PR #6 / board gap; F-25 branch name |

## Cross-session requests

None outstanding. (Resolved during integration: both sessions wrote COORDINATION.md and README.md — merged below; session 9cf451e4's root site relocated to archive/ with links preserved.)

## Log

- 2026-11-04 — Session d22c14b9 CLAIMED T8 (live re-verification + G6 correction). Note: its first analysis ran before this claim was written; no other session held T8. Open PR #6 (arena/28cc78aa-own8, session 28cc78aa not on this board) detected — not touched by this session; logged as F-24.

- 2026-11-03 — Session 9cf451e4 (from their board): PR #1 https://github.com/sassnarep3-star/Own8/pull/1 MERGED (2c2e736); PR #2 …/pull/2 MERGED (2154181); PR #3 …/pull/3 MERGED (19760af); PR #4 …/pull/4 MERGED (30194ba). Pages source main /, https://sassnarep3-star.github.io/Own8/, status built.
- 2026-11-03 — Session 95e9626f initialized its board; claimed T1–T2; captured official data (T2 done, commit 003d0cd); built analysis (T3, d668265); research+site+verification (T4–T6, b94389d); link check PASS (18 pages/1193 links at that point).
- 2026-11-03 — CONFLICT: PR #5 (branch → main) could not merge because session 9cf451e4 had merged PRs #1–#4 into main, touching COORDINATION.md and README.md (add/add + content conflicts). Resolved locally by `git merge origin/main` WITHOUT discarding either side: both boards merged above; both READMEs merged.
- 2026-11-03 — INTEGRATION DECISION: one live site. Session 95e9626f's unified dashboard now serves from repo root (index.html + pages/ + assets/, GitHub Pages main / — the same Pages config 9cf451e4 enabled). Session 9cf451e4's original site tree was relocated verbatim (git mv, relative links preserved, data/ copies included) to `archive/session-9cf451e4-own8/` and is linked from the dashboard nav ("Archive (session 9cf451e4)"). Their data CSVs/scripts remain at data/ and compute_correlations.py.
- 2026-11-03 — COMBINED DATA RE-VERIFIED LINE BY LINE (scripts/verify_combined.py → analysis/verification.json): 32 teams compared across W,L,T,PCT,PF,PA,NET,streak,GP between the two sessions' captures of nfl.com/standings — 0 mismatches. Found + fixed during re-verification: the standings detailed-view tail columns are HOME, ROAD, DIV, DIV%, CONF, CONF%, (L10-like), STRK, (one more) — validated arithmetically on all 32 teams (HOME+ROAD = record; DIV%/CONF% recompute exactly). This session's first capture had mislabeled positions 8–9 as DIV/CONF; corrected in data/standings-2026-reg-w8.json (flagged F-01). The other session's CSV has div/home labels swapped (flagged F-11); its NGS REG/1 player CSVs remain UNVERIFIED (flagged F-12).
- 2026-11-03 — Final link check after integration: PASS — 46 HTML pages, 2712 links, 0 broken internal, all external links https and on the official-source allowlist except one archived http://www.nfl.com link kept verbatim from session 9cf451e4 (recorded as warning, official host).
- 2026-11-03 — PR #5 created: https://github.com/sassnarep3-star/Own8/pull/5 (arena/95e9626f-own8 → main). Merge + Pages deploy record: see below.
- 2026-11-03 — PR #5 MERGED (see `gh pr view 5`); Pages re-deployed from main /; live URL verified: https://sassnarep3-star.github.io/Own8/ (see final entry below).

### Session 74efc1ec — independent verification / risk audit (2026-11-04)

| ID | Task | Status | Owner | Files | Sources / verification | Irregularities |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | Independently audit existing live dashboard's evidence, gating, and unsupported claims; publish reproducible audit without modifying other sessions' owned data/site files | done (audit published; primary site corrections need integration) | 74efc1ec (arena/74efc1ec-own8) | audit/*, COORDINATION.md (this section only) | NFL standings (BUF/NE spot checks), W9 schedule (JAX/BAL, CIN/ATL spot checks), W9 injury report (JAX/BAL); 32/32 arithmetic and 15/15 schedule joins; audit/check.py; audit HTML 0 broken internal links | A-01…A-06 flagged; six sign errors, two invalid candidates, 15 conditional injuries. No claim of exhaustive external row verification. |

Scope note: PR #6 (session 28cc78aa) currently owns root site generator and `site/` integration changes. This session will not edit those files. Arena pins the branch name; no `session-<id>/<task>` branch will be created.

- 2026-11-04 — A1: independent read-only code/data audit complete. Six of six computed market edges use the wrong handicap sign; the six signed comparisons flip direction. Two published candidates have unverified market lines and conditional G4. NFL Week 9 injury report now exists: https://www.nfl.com/injuries/league/2026/reg9 (contradicts stale F-04). All 32 standings rows passed internal PF−PA and PCT arithmetic; 15 schedule rows joined, but ONLY BUF/NE and JAX/BAL + CIN/ATL were externally spot-checked at https://www.nfl.com/standings/ and https://www.nfl.com/schedules/2026/by-week/week-9. Do not mistake internal validation for complete official row-by-row verification. Detailed A-01…A-06 in audit/results.json and audit/index.html. Change request to integration owner on PR #6: https://github.com/sassnarep3-star/Own8/pull/6#issuecomment-6640938329. Primary dashboard remains unchanged because claimed by another session.
- 2026-11-04 — A1 publication: PR #7 https://github.com/sassnarep3-star/Own8/pull/7 MERGED into main (merge commit a98006585f21ee1490c6ca398fcce921c57c0668). Independent warning page: https://sassnarep3-star.github.io/Own8/audit/ . Deploy/build verification recorded separately after completion; these A-01…A-06 needs-review issues do not block publication, but they DO invalidate the currently published root dashboard's candidate claims until corrected by its integration owner.
- 2026-11-04 — A1 deployment CONFIRMED: GitHub Pages latest build for merge PR #7 reported `built` (no error), and https://sassnarep3-star.github.io/Own8/audit/ returned the complete published audit including all 6 findings and 15 game rows. Follow-up board PR #9 MERGED (d5ac8c0b9f87100aa2bbabb6d525b68be27e6ef8). PR #8 (91f4f44e) independently fixes the sign/gating issue; session notified that its F-04 must be refreshed: https://github.com/sassnarep3-star/Own8/pull/8#issuecomment-6640962754. The audit is explicitly tied to baseline 7c2f545 so its status is not misread after a correction merges.

### Session b79c8166 — takeover of stale PR #6 historical lab (2026-11-04)

| ID | Task | Status | Owner | Files | Sources / verification | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | Takeover of stale session 28cc78aa task H8 / PR #6 (last commit 2026-11-04 00:18 UTC, >60 min, no commits): line-by-line audit + remediation of the historical line-origination lab — originated lines, strategies (single bets, parlays, player-prop combos), validation gates, correlations, skill leaderboard, executive summary — relocated into ONE new namespace so it overlaps no other claim | in progress | b79c8166 (arena/b79c8166-own8) | `lab/**` (new directory), COORDINATION.md (this section only) | pending | Arena pins the branch name; no `session-<id>/<task>` branch can be created. Will NOT edit root index.html, pages/, assets/, data/, analysis/, research/, scripts/, docs/, archive/, audit/, README.md, .github/. PR #6's root-file edits (index.html, pages/*.html, README.md, scripts/build_site.py, analysis/link-check.json, .gitignore) are NOT carried over. |

- 2026-11-04 20:13 UTC — b79c8166 read the full board on main (incl. 74efc1ec's merged section) and every remote branch's board (0b9d365e, 566bc2e7, 5c4b8a3e, dd321bf5, 74efc1ec, 28cc78aa) plus open PRs #6, #8, #11, #12. HANDOFF: taking over 28cc78aa's stale H8 (PR #6) under the 60-minute rule; 5c4b8a3e, dd321bf5 and 74efc1ec explicitly left that scope unclaimed. PR #6's numbers are NOT accepted on trust — each will be re-derived or flagged. REQUESTS to the root integration owner (whichever session finalizes): (1) add one nav link to `lab/index.html`; (2) do not merge PR #6 as-is — its root-file edits conflict with current root claims; `lab/` is the audited successor.
### Session 4ec958b2 — independent integration QA (2026-11-04)

| ID | Task | Status | Owner | Files | Sources / verification | Irregularities |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | Independently inspect competing PRs, verify official-source claims and release gates, publish reproducible QA report; request fixes without touching claimed files | done (QA published; integration fixes remain with owners) | 4ec958b2 (`arena/4ec958b2-own8`) | `verification/*`, this section of `COORDINATION.md` | NFL 2026 rulebook and Week 9 injury report; static per-row source-link scan of PR #6; baseline link/audit checks pass | 246/276 PR #6 rows lack official NFL link; non-NFL odds; stale W9 injury claim; PR #6 conflicts with main; see verification/README.md |

Arena pins this session's branch; the requested `session-<id>/<task>` branch naming is unavailable. Site generator and root pages are owned by PR #6, baseline edge fix by PR #8; this session will not edit them.

- 2026-11-04 — Q1: Official NFL 2026 rule change list and Week 9 injury page checked directly. Static scan of PR #6 (d6e88e7) found 246 of 276 rendered table rows without an official NFL link; the 21 official-facts rows have NFL links but quotations were not all independently verified. Baseline link checker PASS and audit/check.py PASS. Change requests sent to PR #6 (https://github.com/sassnarep3-star/Own8/pull/6#issuecomment-6640977441) and PR #8 (https://github.com/sassnarep3-star/Own8/pull/8#issuecomment-6640977944). Release gate for PR #6 not cleared; see verification/README.md. Initial claim push encountered a COORDINATION.md rebase conflict with concurrently merged PR #7 board log; resolved by retaining both entries, without discarding either session.
- 2026-11-04 — Session d22c14b9 T8 DONE (sources and verification in T8 row). Live checks: 4 official checks PASS, 1 wording flag (F-14), market lines not verifiable (F-05). CORRECTION: the 2026-11-03 build marked CIN at ATL and NYG at PHI as candidates with G6 = PASS on a third-party market line; this violates the project's own unverified-data rule. analyze.py now makes G6 NOT_COMPUTABLE for every game and candidates = 0; site, README, research docs updated. Commit d55938b bundled the claim and the work (claim was written in the same commit).
- 2026-11-04 — Session d22c14b9 T8 DONE (sources and verification in T8 row). Live checks: 4 official checks PASS, 1 wording flag (F-20), market lines not verifiable (F-05). CORRECTION: the 2026-11-03 build marked CIN at ATL and NYG at PHI as candidates with G6 = PASS on a third-party market line; this violates the project's own unverified-data rule. analyze.py now makes G6 NOT_COMPUTABLE for every game and candidates = 0; site, README, research docs updated. Commit d55938b bundled the claim and the work (claim was written in the same commit).
- 2026-11-04 — d22c14b9 OVERLAP NOTICE: (a) PR #8 (91f4f44e) and PR #12 (c03eba88) are open and overlap this session's analysis.py/build_site.py/flagged.json work and the live standings check. Rebased onto origin/main (5bb96b3); conflict in COORDINATION.md resolved by keeping both sides (no other session's text discarded). (b) This session's branch withholds the unverified third-party market value and all market-based edges (blank-if-unconfirmed; audit A-01 sign issue becomes moot while withheld) and sets G6 = NOT_COMPUTABLE (audit A-02). PR #8 should rebase onto this change; its sign-fix hunks in scripts/analyze.py will conflict and should keep the withholding. (c) Flag IDs renumbered F-14..F-19 -> F-20..F-25 to avoid collision with PR #8's F-14. (d) Audit A-03 (W9 injury report now exists) is confirmed and resolved for CIN@ATL and NYG@PHI only; other 13 games are F-22.
- 2026-11-04 — d22c14b9 GIT NOTE: a `git pull --rebase` against the stale remote copy of this branch replayed main's commits by mistake. Aborted (no commits lost; local history verified: main is an ancestor). The branch was then force-pushed with lease (remote 90a7569 -> 98086ee) to replace only this session's own pre-rebase commits. No other session's commits were removed.
- 2026-11-04 — Q1 publication: PR #14 https://github.com/sassnarep3-star/Own8/pull/14 MERGED (8e3748fca6979df4a176e89743eca8467d2c7720). GitHub Pages workflow https://github.com/sassnarep3-star/Own8/actions/runs/41904597677 succeeded (build, report-build-status, deploy). This publishes the QA report at https://github.com/sassnarep3-star/Own8/blob/main/verification/README.md and the reproduction script on main; it does NOT clear PR #6's release gate. Subsequent integration owners must preserve #8's candidate withdrawal and update W9 injury status.


## Session 5c4b8a3e — strict verification remediation (2026-11-04)

Arena fixes this session to `arena/5c4b8a3e-own8`; it is the work/integration branch (no additional branches).

| Task | Status | Owner | Files | Verification / irregularities |
| --- | --- | --- | --- | --- |
| A1 Repository/source audit | in progress | 5c4b8a3e | strict/, docs/AUDIT-2026-11-04.md | Read all tracked text; distinguish provenance from cross-file consistency. |
| A2 Official historical evidence and safe analysis | in progress | 5c4b8a3e | strict/, scripts/strict_*.py, tests/ | Acquire immutable official NFL GitHub evidence; no unsupported current values. |
| A3 Final integration and dashboard | in progress | 5c4b8a3e | index.html, pages/, assets/, README.md, scripts/analyze.py, scripts/build_site.py, research/, analysis/, .github/, .gitignore | Canonical scopes from merged sessions taken over; preserve legacy inputs, quarantine unsupported claims. |
| A4 Tests, PR, merge, Pages confirmation | in progress | 5c4b8a3e | COORDINATION.md, strict/deployment.json | Merge only after local build/tests pass. |

- 2026-11-04: Read local board and PR #6's remote board. Session 28cc78aa last committed 2026-11-04 00:18Z (>60 minutes); its complementary `site/`, `scripts/own8_*`, `data/results/`, and docs scope remains untouched. PR #6 is open, not part of this integration, and its claimed numerical findings are NOT verified by this session. No merge of that PR is implied. Root canonical scope belongs to previously merged sessions and is now claimed here. Existing sources assert verification without retained page evidence; this is being audited, not accepted on trust.
- 2026-11-04 scope extension (final integration): `docs/*.html` and `archive/session-9cf451e4-own8/**/*.html` are duplicate outputs of merged sessions; take over their routing only to prevent stale recommendations from remaining public. Legacy datasets and markdown provenance remain intact; exact historical HTML is available in git history. No files in PR #6's complementary `site/` or namespaced scripts are edited. Auditing original code found (i) opposite spread signs, (ii) unverified market data accepted with G1 PASS, (iii) candidates independent of aggregate gates, (iv) CONDITIONAL accepted, (v) ecological correlation proxy, (vi) ROI tiers without out-of-sample evidence. Official Week 9 injury page is now accessible, superseding prior availability note.
- 2026-11-04 A1/A2 verification: retrieved NFL standings chunks 0–1 (32 rows; 224 numeric cells match), schedule chunks 0–2 (15 matchups/dates), official Week 9 injury report (8 selected DNP observations; diagnoses/game statuses blank), Hurts article (likely/expected uncertainty retained), NGS glossary, NFL Big Data Bowl overview, NIST autocorrelation page and Washington regulator. Downloaded immutable official NFL games/schema/README at commit `9ad0b4b2ea36697e29e44e2399512cc1ce70358c`, SHA-256 manifest retained. 104 base text files inventoried, not blanket-certified. Added 11 proposals, strict 9-gate per-strategy matrix, 3 descriptive correlations; all missing bet correlations/quotes/ranks blank. 91 historical games → 60 rolling-week predictions; margin MAE 10.426 vs baseline 10.024, total MAE 12.318 vs 12.181: heuristic does NOT beat baseline. No skill designation. 20 local tests PASS; local checker: 49 HTML documents, 873 links, 400 active table rows each with official evidence/context link; 0 broken internal links/anchors. External HTTP liveness is not asserted by the checker.
- 2026-11-04 CONCURRENT MERGES discovered on required pre-push pull: origin/main advanced from 7c2f545 to 3b64ca6 (PRs #7/#9/#11/#14/#17). Rebase stopped on shared-board conflict; aborted safely, keeping all commits. Session 74efc1ec's newly merged `strict/` namespace overlaps this session's initially local scope. HANDOFF RESOLUTION: this session moves all of its new evidence/results to `strict/` and leaves the published independent `strict/` records intact. Integrating main with an explicit merge so all authors' history and board entries are preserved. Canonical fixes already merged by d22c14b9 are semantically retained by the stricter no-candidate implementation, and all newly merged F-20..F-25 flags will remain on the current review page. New `verification/` scope and b79c8166's unmerged `lab/` scope remain untouched.

- Merge-conflict resolution: kept both complete boards. Preserved main data/flagged.json and all independent audit/ and verification/ files verbatim; regenerated canonical root HTML/analysis with strict rules retaining the no-unverified-candidates fix. Historical original implementations remain in merged git history, not silently deleted.
