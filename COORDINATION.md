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

## Session 5c4b8a3e — strict verification remediation (2026-11-04)

Arena fixes this session to `arena/5c4b8a3e-own8`; it is the work/integration branch (no additional branches).

| Task | Status | Owner | Files | Verification / irregularities |
| --- | --- | --- | --- | --- |
| A1 Repository/source audit | in progress | 5c4b8a3e | audit/, docs/AUDIT-2026-11-04.md | Read all tracked text; distinguish provenance from cross-file consistency. |
| A2 Official historical evidence and safe analysis | in progress | 5c4b8a3e | audit/, scripts/strict_*.py, tests/ | Acquire immutable official NFL GitHub evidence; no unsupported current values. |
| A3 Final integration and dashboard | in progress | 5c4b8a3e | index.html, pages/, assets/, README.md, scripts/analyze.py, scripts/build_site.py, research/, analysis/, .github/, .gitignore | Canonical scopes from merged sessions taken over; preserve legacy inputs, quarantine unsupported claims. |
| A4 Tests, PR, merge, Pages confirmation | in progress | 5c4b8a3e | COORDINATION.md, audit/deployment.json | Merge only after local build/tests pass. |

- 2026-11-04: Read local board and PR #6's remote board. Session 28cc78aa last committed 2026-11-04 00:18Z (>60 minutes); its complementary `site/`, `scripts/own8_*`, `data/results/`, and docs scope remains untouched. PR #6 is open, not part of this integration, and its claimed numerical findings are NOT verified by this session. No merge of that PR is implied. Root canonical scope belongs to previously merged sessions and is now claimed here. Existing sources assert verification without retained page evidence; this is being audited, not accepted on trust.
- 2026-11-04 scope extension (final integration): `docs/*.html` and `archive/session-9cf451e4-own8/**/*.html` are duplicate outputs of merged sessions; take over their routing only to prevent stale recommendations from remaining public. Legacy datasets and markdown provenance remain intact; exact historical HTML is available in git history. No files in PR #6's complementary `site/` or namespaced scripts are edited. Auditing original code found (i) opposite spread signs, (ii) unverified market data accepted with G1 PASS, (iii) candidates independent of aggregate gates, (iv) CONDITIONAL accepted, (v) ecological correlation proxy, (vi) ROI tiers without out-of-sample evidence. Official Week 9 injury page is now accessible, superseding prior availability note.
- 2026-11-04 A1/A2 verification: retrieved NFL standings chunks 0–1 (32 rows; 224 numeric cells match), schedule chunks 0–2 (15 matchups/dates), official Week 9 injury report (8 selected DNP observations; diagnoses/game statuses blank), Hurts article (likely/expected uncertainty retained), NGS glossary, NFL Big Data Bowl overview, NIST autocorrelation page and Washington regulator. Downloaded immutable official NFL games/schema/README at commit `9ad0b4b2ea36697e29e44e2399512cc1ce70358c`, SHA-256 manifest retained. 104 base text files inventoried, not blanket-certified. Added 11 proposals, strict 9-gate per-strategy matrix, 3 descriptive correlations; all missing bet correlations/quotes/ranks blank. 91 historical games → 60 rolling-week predictions; margin MAE 10.426 vs baseline 10.024, total MAE 12.318 vs 12.181: heuristic does NOT beat baseline. No skill designation. 20 local tests PASS; local checker: 49 HTML documents, 873 links, 400 active table rows each with official evidence/context link; 0 broken internal links/anchors. External HTTP liveness is not asserted by the checker.
