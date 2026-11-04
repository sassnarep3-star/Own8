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
| 95e9626f | arena/95e9626f-own8 | merged to main (PR #5) | Full JSON data pipeline, 2026-snapshot analysis, unified root dashboard. |
| 28cc78aa | arena/28cc78aa-own8 | integration (PR #6) | This session: deep historical line-origination lab (1999–2026), 13 gated strategies, correlation library, complementary dashboard at `site/`. |

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

### Session 95e9626f (merged)

| ID | Task | Status | Owner | Files | Sources / verification | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Repo review + board | done | 95e9626f | COORDINATION.md, README.md | repo was empty except README at 9bd72f5 | no irregularities in pre-existing content |
| T2 | Official data capture | done | 95e9626f | data/*.json | nfl.com + nextgenstats.nfl.com, 2026-11-03; column orders arithmetic-validated | W9 injury report not yet published (F-04) |
| T3 | Analysis pipeline | done | 95e9626f | scripts/analyze.py, analysis/*.json | computed from data/*.json only | assumptions labeled (F-07); W9 candidates CIN@ATL, NYG@PHI |
| T4 | Research docs + exec summary | done | 95e9626f | research/*.md | official links; Ksa + NCPG | — |
| T5 | Site build | done | 95e9626f | scripts/build_site.py → index.html + pages/ + assets/ | generated; no external CDN | unified dashboard, per-row source links |
| T6 | Line-by-line verification + flags | done | 95e9626f | scripts/check_links.py, scripts/verify_combined.py, data/flagged.json, analysis/link-check.json, analysis/verification.json | link check PASS (46 pages, 2712 links, 0 broken); combined-data check PASS (32 teams, 0 mismatches) | F-01..F-13 on Flagged for Review page |
| T7 | Final integration | done | 95e9626f | COORDINATION.md, README.md, archive/ | PR #5 merged; Pages re-deployed from main / | https://github.com/sassnarep3-star/Own8/pull/5 |

### Session 28cc78aa (this session — historical line-origination lab)

| ID | Task | Status | Owner | Files | Sources / verification | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | Repo review | done | 28cc78aa | docs/REPO_REVIEW.md | 1 pre-existing file read in full; git history inspected | repo empty at base 9bd72f5 |
| H2 | Official-source research | done | 28cc78aa | data/official_facts.json, docs/SOURCES.md | 21 facts quoted verbatim from NFL sources (rulebook PDF, media.nfl.com, nfl.com); research refs R1–R4 verified | Moskowitz corrected to 2021 |
| H3 | Primary data acquisition | done | 28cc78aa | scripts/fetch_data.py, data/raw/ (git-ignored), docs/DATA_PROVENANCE.md | 26 files via GitHub API + SHA-256 manifest; official anchor nfl-football-ops/Big-Data-Bowl | market lines PRIMARY (non-NFL), flagged |
| H4 | Strategy research + gates | done | 28cc78aa | docs/STRATEGY_RESEARCH.md, docs/VALIDATION_GATES.md | methodology from R1–R4 | 7 gates, 4 reward tiers |
| H5 | Quantitative analysis | done | 28cc78aa | scripts/own8_analyze.py, data/results/, data/processed/ | official scores 91/91 exact; odds cross-check 93.4%/98.5%; 16 correlations + 2021 check; 13 strategies | fixed spread-sign + prop-leakage bugs caught by gates |
| H6 | Executive summary | done | 28cc78aa | EXECUTIVE_SUMMARY.md | from computed results | S2 Silver (CLV +0.80, z 5.68); no Gold |
| H7 | Dashboard site | done | 28cc78aa | site/, scripts/own8_build_site.py, scripts/own8_check_links.py | 12 pages, per-row source links, Flagged for Review; link check 0 broken | served at /Own8/site/ via root Pages |
| H8 | Final integration | in progress | 28cc78aa | COORDINATION.md, README.md, scripts/own8_*.py | merged origin/main without discarding others; PR #6 | see log |

## Cross-session requests

- 28cc78aa → all: my historical lab is added as a **complementary section** at `site/`
  (served at https://sassnarep3-star.github.io/Own8/site/ by the existing root Pages).
  The unified root dashboard (session 95e9626f) remains the primary landing page. My scripts
  are namespaced `scripts/own8_*.py` so the canonical `scripts/{analyze,build_site,check_links}.py`
  (session 95e9626f) are untouched. No competing Pages workflow was added (my `pages.yml` removed).
- Resolved earlier (95e9626f): both 9cf451e4 and 95e9626f wrote COORDINATION.md and README.md —
  merged; 9cf451e4's root site relocated to archive/ with links preserved.

## Log

- 2026-11-03 — Session 9cf451e4 (from their board): PR #1 https://github.com/sassnarep3-star/Own8/pull/1 MERGED (2c2e736); PR #2 …/pull/2 MERGED (2154181); PR #3 …/pull/3 MERGED (19760af); PR #4 …/pull/4 MERGED (30194ba). Pages source main /, https://sassnarep3-star.github.io/Own8/, status built.
- 2026-11-03 — Session 95e9626f initialized its board; claimed T1–T2; captured official data (T2 done, commit 003d0cd); built analysis (T3, d668265); research+site+verification (T4–T6, b94389d); link check PASS (18 pages/1193 links at that point).
- 2026-11-03 — CONFLICT (95e9626f): PR #5 could not merge because 9cf451e4 had merged PRs #1–#4. Resolved locally WITHOUT discarding either side; both boards merged; 9cf451e4's site archived.
- 2026-11-03 — INTEGRATION DECISION (95e9626f): one live site at repo root (index.html + pages/ + assets/, Pages main /). 9cf451e4's tree relocated verbatim to archive/session-9cf451e4-own8/. Combined standings re-verified line by line (32 teams, 0 mismatches); F-01/F-11/F-12 flagged. Final link check PASS (46 pages, 2712 links, 0 broken). PR #5 MERGED; Pages re-deployed; live URL verified.
- 2026-11-03 — Session 28cc78aa: board created at base 9bd72f5 (unaware of parallel sessions, which had not yet merged into this branch's history). Claimed H1–H7; verified 21 official facts; acquired 26 primary-data files; built validation + correlations + 13 gated strategies; built 12-page dashboard. Gates caught and fixed a spread sign-convention bug (impossible 70% ROI) and a prop-baseline merge fan-out leakage. Full pipeline re-run reproduces committed outputs exactly.
- 2026-11-03 — CONFLICT (28cc78aa): PR #6 (arena/28cc78aa-own8 → main) could not merge because sessions 9cf451e4 and 95e9626f had merged PRs #1–#5 into main, with add/add conflicts on COORDINATION.md, README.md, and scripts/{analyze,build_site,check_links}.py. Resolved by `git merge origin/main` WITHOUT discarding any session's work: their canonical scripts kept; my scripts namespaced to scripts/own8_*.py; both prior boards preserved above and my H1–H8 board added; READMEs merged; my competing .github/workflows/pages.yml removed so the existing root legacy Pages (main /) continues to serve the unified dashboard AND my complementary site/ at /Own8/site/.
- 2026-11-03 — INTEGRATION DECISION (28cc78aa): the root dashboard (95e9626f) stays the primary live site; my historical lab is a complementary section linked from the merged README and root landing page. No data from any session was overwritten. Re-verification: my link check 0 broken; root site link check re-run after merge (see PR #6).
- 2026-11-03 — PR #6: https://github.com/sassnarep3-star/Own8/pull/6 (arena/28cc78aa-own8 → main). Merge + Pages deploy confirmation: see final entry below.
