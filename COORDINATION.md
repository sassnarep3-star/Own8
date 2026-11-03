# COORDINATION — Shared Task Board

Repo: `sassnarep3-star/Own8` · Project: NFL line origination, strategy research, validation, and dashboard site.

## Session registry

| Session ID | Branch | Notes |
|---|---|---|
| `28cc78aa` | `arena/28cc78aa-own8` | Arena Agent Mode session (2026-11-03). Platform constraint: this session is pinned to branch `arena/28cc78aa-own8` and may not create/switch branches, so this branch serves as both its work branch and the integration branch. All claims below are owned by this session unless another session claims an unclaimed row. |

## Ground rules (all sessions)

1. Claim a task here (session ID + file scope), commit and push the claim **before** editing task files.
2. Never edit files inside another session's claimed scope — log a change request here instead.
3. `git pull --rebase` before every push. Small, frequent commits.
4. Verification rule: every data-table row must carry a link to an official/primary source. Values that cannot be confirmed from an official source are left **blank** and flagged `UNVERIFIED` on the Flagged for Review page. Derived statistics computed by this project from primary data are labeled `DERIVED` with methodology + data-provenance links, and their provenance caveats are listed on Flagged for Review.
5. Stale claims (>60 min, no commits) may be taken over; note the handoff in the log.
6. Shared outputs (site index/nav, combined data) are finalized only in the integration task after all other tasks are done.

## Task board

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| T1 | Repo review (line-by-line audit of existing repo contents) | in progress | 28cc78aa | `docs/REPO_REVIEW.md` |
| T2 | Official-source research: NFL rules, season structure, scoring environment, betting-relevant official facts | in progress | 28cc78aa | `data/official_facts.json`, `docs/SOURCES.md` |
| T3 | Primary data acquisition (play-by-play / schedules / player stats from public primary-data mirrors on GitHub) with provenance log | in progress | 28cc78aa | `data/raw/` (git-ignored), `data/processed/`, `scripts/fetch_data.py`, `docs/DATA_PROVENANCE.md` |
| T4 | Strategy research & catalog: singles, parlays, player-prop combos; signal definitions; validation gates; luck-vs-skill methodology | in progress | 28cc78aa | `docs/STRATEGY_RESEARCH.md`, `docs/VALIDATION_GATES.md`, `strategies/` |
| T5 | Quantitative analysis: correlation estimation, backtests with validation gates, leaderboard scoring | in progress | 28cc78aa | `scripts/analyze.py`, `data/processed/`, `data/results/` |
| T6 | Executive summary | in progress | 28cc78aa | `EXECUTIVE_SUMMARY.md` |
| T7 | Dashboard site (landing + category subpages, tables with per-row source links, Flagged for Review page) | in progress | 28cc78aa | `site/` |
| T8 | Final integration: re-verify combined data, build site, link check, PR to main, merge, GitHub Pages deploy confirmation | unclaimed (integration; will be claimed by 28cc78aa when T1–T7 done) | — | `site/index.html` (final), `.github/workflows/`, `COORDINATION.md` |

## Change requests

(none)

## Log

- 2026-11-03 · `28cc78aa`: Board created. Repo inspected: contains only `README.md` (6 bytes, `# Own8`), single commit `9bd72f5`. No other sessions present. T1–T7 claimed with non-overlapping scopes above; T8 reserved for final integration.
