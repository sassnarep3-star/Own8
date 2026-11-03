# COORDINATION.md — Shared Task Board (Own8 / NFL Lines Project)

This file is the shared task board for all agent sessions working on this repo.
Read it before starting any task. Claim a task by writing your session ID and
file scope in its row, then commit and push that claim immediately. Never start
a task another session has claimed. Keep scopes non-overlapping. If a task
requires changing a file owned by another session, log the request in the
"Cross-session requests" section instead of editing it. Make small, frequent
commits and run `git pull --rebase` before every push. If a claim is more than
60 minutes old with no commits, another session may take it over and note the
handoff here.

## Sessions

| Session ID | Branch | Status | Notes |
| --- | --- | --- | --- |
| 95e9626f | arena/95e9626f-own8 | active | Only session active at kickoff (2026-11-03). Claimed all tasks below; no other sessions observed. |

## Task Board

| ID | Task | Status | Owner session | Files touched | Sources / verification | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Repo review + create COORDINATION.md | done | 95e9626f | COORDINATION.md, README.md | n/a (repo was empty except README) | Repo contained only `README.md` ("# Own8") at commit 9bd72f5. No irregularities in existing content. |
| T2 | Collect official NFL data (standings, W9 schedule, W8 scores, team stats, player stats, Next Gen Stats, injuries, news) into `data/*.json`, every row with an official source link | done | 95e9626f | data/*.json | nfl.com, nextgenstats.nfl.com (official NFL domains), captured 2026-11-03; column orders validated arithmetically (CMP/ATT=CMP%, YDS/ATT=AVG, 1ST/ATT=1ST%) | Week 9 injury report not yet published on nfl.com (latest is Week 8, /injuries/league/2026/reg8) — flagged F-04, not blocking. |
| T3 | Analysis: correlations + model line origination for Week 9 + strategy cards with validation gates + leaderboard (computed, reproducible) | done | 95e9626f | scripts/analyze.py, analysis/*.json | Computed from data/*.json only (32 teams); rerun via `python3 scripts/analyze.py` | Model assumptions (HFA 2.5, -110, stake caps, edge band 1.0–8.0) labeled as assumptions — F-07. W9 candidates: CIN@ATL, NYG@PHI; JAX@BAL / NYJ@KC / LV@SF rejected by 8-pt sanity cap. |
| T4 | Research docs: executive summary, methodology, strategies, validation gates, correlation policy, leaderboard rules, responsible gambling | done | 95e9626f | research/*.md | Official links; Kansspelautoriteit (NL regulator) + NCPG for jurisdiction | Executive summary outlines goals, data, model, gates, correlation, leaderboard, flags. |
| T5 | Build GitHub Pages static site (dashboard landing + category subpages + tables + flagged page) | done | 95e9626f | docs/**, scripts/build_site.py | Generated from data/analysis/research; no external CDN (works offline); 18 pages | Clean dashboard UI, sidebar nav, cards, tables with per-row source links. |
| T6 | Line-by-line verification pass + flagged/unverified register | done | 95e9626f | data/flagged.json, docs/flagged.html, scripts/check_links.py, analysis/link-check.json | Link check: 18 pages, 1193 links, 0 broken internal, all external https + official allowlist — PASS. 10 flagged items F-01..F-10 published on Flagged for Review page | Third-party aggregator discrepancies (records, odds) recorded in data/market-lines.json as unverified (F-05/F-06), never in verified tables. Unverifiable cells left blank. |
| T7 | Final integration: PR to main, merge, enable/verify GitHub Pages deploy, record PR link + result here | in progress | 95e9626f | COORDINATION.md | gh CLI; Pages API | Do not merge a broken site; link checker PASS required first (done). |

## Cross-session requests

None.

## Log

- 2026-11-03 — Session 95e9626f initialized board, claimed T1 (done) and T2 (in progress). Repo reviewed line by line: only `README.md` with `# Own8` at 9bd72f5; `git status` clean; remote origin = github.com/sassnarep3-star/Own8. No irregularities found in existing repo content.
- 2026-11-03 — T2 data captured from official sources (nfl.com standings/schedules/scores/stats/injuries, nextgenstats.nfl.com). All captures timestamped 2026-11-03 UTC. Third-party aggregator values (nflschedules.com, ESPN scoreboard) observed but NOT used as sources; discrepancies logged to flagged register (T6).
