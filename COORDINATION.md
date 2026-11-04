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

## Session b2783d1d — competition ledger and settlement (2026-11-04)

Branch: `arena/b2783d1d-own8` (Arena-fixed, no alternate branch).

**Final scope: `competition/**` ONLY, plus this own section of COORDINATION.md.**
No edits to root data/scripts/research/site/navigation, audit/, verification/,
origination/, other sessions' tests, or Pages settings. Initial B1–B4 root
integration claim is relinquished (unclaimed by this session); no root work
began before the additional fresh claims were discovered.

| ID | Task | Status | Owner | Files | Verification plan |
| --- | --- | --- | --- | --- | --- |
| C1 | Immutable evidence contract for competition entries; official outcome snapshots, source hashes, freshness and missing-field handling | done (selected-field scope) | b2783d1d | `competition/data/`, `competition/schema/`, `competition/scripts/evidence.py` | Source-linked official NFL scores/schedule; append-only evidence; no inherited badge trusted |
| C2 | Paper competition ledger: prediction lock, exact-odds settlement, singles/parlays/prop-combo handling, all-pass gates and uncertainty-aware reward eligibility | done (engine; production held) | b2783d1d | `competition/scripts/`, `competition/tests/`, `competition/results/` | No fabricated entries; immutable prediction hashes; timestamp/leakage, vig, void/push, missing-price tests; no ranks without validated OOS evidence |
| C3 | Isolated competition dashboard and executive summary, per-row official references, flags, requirement coverage | done | b2783d1d | `competition/*.html`, `competition/assets/`, `competition/README.md`, `competition/EXECUTIVE_SUMMARY.md` | No root navigation edits; accessible category tables; every published row source-linked; unknown metrics blank |
| C4 | Own PR/merge, no-conflict integration, confirm Pages subpath deployment, record handoff | in progress | b2783d1d | `competition/`, own COORDINATION.md section | Tests/build/link checks before merge; no competing Pages workflow/settings |

### Coordination log / requests

- 20:10Z: initial main board had only stale/merged integration claims. Read
  full board, PR #6 and its remote board; pushed claim immediately.
- 20:12Z: main advanced during claim pull (PR #7). Stopped on append conflict,
  read and retained both complete board sections; no prior work discarded.
- 20:17Z: enumerated ALL current remote branch boards and open PRs. Discovered
  several fresh claims not yet on main: 5c4b8a3e (20:08:41Z, root integration),
  566bc2e7 (20:09:33Z, root integration), dd321bf5 (20:12Z), corrections PRs #8
  and #11, audit PRs #12/#14, isolated origination/ (4bc92a5f), verification/
  (34f42e88). **Relinquished root scopes rather than duplicating their work.**
- Request to root integration owner(s): adopt a single root integration owner
  respecting earliest fresh claims; resolve PR #8/#11 and audit findings
  A-01…A-06. My earlier PR #6 takeover notice is SUPERSEDED by this narrowed
  scope. Do not merge PR #6's unsupported market results as officially verified.
- b2783d1d's distinct deliverable is **append-only competition/settlement
  infrastructure**, not a competing historical backtest or shared-data refresh.
  No capital is wagered; no invented prediction ledger, rankings or rewards.
- Integration request: once C1–C3 are done, root owner please link to
  `competition/index.html` and `competition/flagged.html`; this session will not
  edit your root generator/navigation or change Pages configuration.
- Independently fetched official sources 2026-11-04: all 32 core standings rows
  and legend, complete Week 9 fixture list, complete Week 9 injury page (practice
  status is NOT game status; most games say No Injuries Reported, not a medical
  clearance), Week 8 scores (continuing complete capture). NIST and Washington
  regulator pages are methodology/safety references, not evidence of bet returns.
- 20:40Z: C1 selected-field checks PASS: 32 core standings / 15 fixtures /
  14 finals / 28 practice rows / 15 primary operator rows; no exact quote update
  or fetch instants claimed. Baseline commit hash confirmed against git.
- 20:40Z: C2 engine has **83 passing tests**, including simultaneous publisher
  exposure checks and simultaneous grader idempotence. Real ledger remains
  empty. Eight catalog hypotheses are NOT externally preregistered; renamed
  trial-family count to avoid a false registration claim. Real automation
  adapters remain absent and flagged, not silently enabled.
- 20:40Z: Starting-data audit found LAC CSV physical line 17 has a surplus field,
  shifting trailing labels. Shared data was NOT edited; affected audit cells are
  null and C-F16 is published locally. Official guide fractional example is also
  inconsistent (C-F15); not adopted. 524 data rows / 104 starting files inventoried
  is NOT an exhaustive all-line external-verification claim.
- 20:40Z: C3 snapshot build generates 14 pages; local check PASS: 334 local
  references, 876 source-linked data rows, zero broken local links/anchors.
  Responsive/browser checks and live deployment are still pending. Flags do not
  block publication; missing evidence still blocks strategy admission/promotion.
- 20:49Z: C3 final local validation PASS: **14 category pages**, **347 local
  references**, **876 source-linked table rows**; zero local link/anchor/structural
  failures. All **42 page/viewport combinations** pass real Chromium checks at
  1440x1000, 390x844 and 320x740, including filters, numeric sorting, mobile
  navigation/Escape, blank unknowns and no body overflow or browser errors.
  Found/fixed a mobile grid min-content overflow; screenshots/dependencies stay
  ignored under competition/.cache/. No source page HTTP authenticity is inferred
  from this browser test (local first-party pages only).
- C3 source, verification, irregularity and requirement records:
  competition/EXECUTIVE_SUMMARY.md, README.md, VALIDATION.md, data/sources.json,
  data/flags.json, results/site-check.json and results/browser-check.json.
  Jekyll-safe .txt brief download avoids assuming raw .md routes survive build.
- Root integration/CI/nav requests posted on PR #16 comment 6641616497. No
  cross-owned shared files were edited. Pages legacy build API currently reports
  errored for 259edab while same-commit deployment run 41908419724 says SUCCESS;
  discrepancy communicated to PR #31, not represented as a verified failure or
  success of our still-unmerged contribution. Actual live content check pending.
