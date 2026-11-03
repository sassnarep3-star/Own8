# Coordination Board — Own8 NFL Lines Project

Session ID: `arena/9cf451e4-own8` (branch `arena/9cf451e4-own8`)

Rules: claim a task by writing your session ID + file scope, then commit and push immediately. Never start a task another session has claimed. Keep scopes non-overlapping. If a task needs a file owned by another session, log the request here instead of editing it. When finished, record sources, verification performed, and irregularities here, and mark the task done. Never mark verified without checking an official source; link that source. Flagged/unverified items do not block merge; they go on a "Flagged for Review" page.

| # | Task | Status | Owner | Files touched | Sources / verification | Irregularities |
|---|------|--------|-------|---------------|------------------------|----------------|
| 1 | Create coordination board | done | arena/9cf451e4-own8 | COORDINATION.md | — | — |
| 2 | Research official NFL data sources (standings, stats, schedules) | in progress | arena/9cf451e4-own8 | data/*.csv, data/sources.md | NFL.com (official) | nfl.com blocks direct fetch; using fetch_page/web_search |
| 3 | Develop strategy framework: single bets, parlays, player prop combos, validation gates, correlations | unclaimed | arena/9cf451e4-own8 | strategies/*.md | Official NFL stats where cited | — |
| 4 | Executive summary | unclaimed | arena/9cf451e4-own8 | docs/executive-summary.md | All site data | — |
| 5 | Site creation: landing page + category subpages, strategy tables with source links, unverified flags | unclaimed | arena/9cf451e4-own8 | site/*.html, site/assets/ | Each table row linked to official source | — |
| 6 | Verification pass: line-by-line check of every table row against official source | unclaimed | arena/9cf451e4-own8 | site/, data/ | Official NFL sources per row | — |
| 7 | Flagged for Review page + unverified-item registry | unclaimed | arena/9cf451e4-own8 | site/flagged-for-review.html | — | — |
| 8 | Integration: merge branches, re-verify combined data, confirm site builds with no broken links | unclaimed | arena/9cf451e4-own8 | all | — | — |
| 9 | PR from integration branch to main, merge, confirm GitHub Pages deploys, record PR link + result here | unclaimed | arena/9cf451e4-own8 | GitHub repo + Pages settings | — | — |
