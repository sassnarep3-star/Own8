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
| T7 | Final integration: merge origin/main, re-verify combined data, unify site at root, PR #5 to main, merge, confirm Pages deploy, record here | in progress | 95e9626f | COORDINATION.md, README.md, archive/ | see log | PR #5: https://github.com/sassnarep3-star/Own8/pull/5 |

## Cross-session requests

None outstanding. (Resolved during integration: both sessions wrote COORDINATION.md and README.md — merged below; session 9cf451e4's root site relocated to archive/ with links preserved.)

## Log

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

### Session 34f42e88 — fail-closed validation and evidence portal (2026-11-04)

| ID | Task | Status | Owner | Files | Sources / verification | Irregularities |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | Official-source evidence capture; fail-closed betting math, skill gates and tests; isolated verification dashboard and executive summary; own PR and Pages deployment | in progress | 34f42e88 / arena/34f42e88-own8 | verification/**; COORDINATION.md (this section and own log only) | Sources to be captured from official NFL GitHub repository; local repo review; immutable hashes and explicit scope | Existing root/site/ owned by active PRs #6 and #8; no edits to those files. No exhaustive official verification claimed. |

- 2026-11-04 — 34f42e88 claim: isolated `verification/` scope avoids active owners of scripts/analyze.py, root dashboard, and historical lab. Arena branch is pinned; work remains on arena/34f42e88-own8 rather than creating a session branch. Integration request: root/historical integration owners should add a link to `/verification/`; this session will not edit their files. Source links alone do not prove verification. Existing audit A-01…A-06 remains applicable until owners demonstrate fixes.

- 2026-11-04 — 34f42e88 synchronization: initial pull exposed shallow-history add/add conflicts; aborted that rebase, fetched full history, and rebased claim onto current main. Preserved all upstream audit files and both coordination-log additions; no other session work discarded. Initial session remote did not yet exist, so first pre-push pull used origin/main.
