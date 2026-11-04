# Executive Summary — Own8 NFL Line-Origination Project

**As of:** 2026-11-03 (NFL 2026 regular season, after Week 8, ahead of Week 9 which begins Thursday 2026-11-05)
**Prepared by:** automated agent session `95e9626f`, branch `arena/95e9626f-own8`
**Verification rule used throughout:** every value in this project comes from an official source (NFL.com, Next Gen Stats, or — for your jurisdiction — the Dutch regulator Kansspelautoriteit). If a value cannot be confirmed from an official source it is left **blank** and listed on the **Flagged for Review** page. Nothing is inferred or filled in.

## 1. Goal

Originate our own NFL betting lines from first principles, run them as a **leaderboard competition** that rewards top-performing strategies, and cover three bet shapes: **single bets, parlays, and player-prop combos**. Every strategy must pass explicit **validation gates**, correlation values are computed and enforced, and the framework is designed to **remove luck and keep only selectively skill-based signals**.

## 2. Data foundation (all official, captured 2026-11-03)

| Dataset | Official source |
| --- | --- |
| 2026 standings through Week 8 (all 32 teams: W-L-T, PCT, PF, PA, net, streak) | https://www.nfl.com/standings/ |
| Week 9 schedule (15 games, times, networks, venues, byes PIT/TEN) | https://www.nfl.com/schedules/2026/by-week/week-9 |
| Week 8 final scores (14 games) | https://www.nfl.com/scores/2026/week-8 |
| Team offense passing & rushing, team defense passing & rushing (season) | https://www.nfl.com/stats/team-stats/ |
| Player leaders: passing, rushing, receiving, interceptions (top 25 each) | https://www.nfl.com/stats/player-stats/ |
| Next Gen Stats QB passing, Week 8 (TT, CPOE, xCOMP%, AGG%, …) | https://nextgenstats.nfl.com/stats/passing/2026/REG/8 (+ glossary: https://nextgenstats.nfl.com/glossary) |
| Latest published official injury report (Week 8; Week 9 report not yet published — flagged F-04) | https://www.nfl.com/injuries/league/2026/reg8 |
| Official news: Terry McLaurin (WAS) out for season; Jalen Hurts (PHI) on IR, likely out for season | https://www.nfl.com/news/commanders-wr-terry-mclaurin-out-rest-of-season-torn-patellar-tendon · https://www.nfl.com/news/eagles-qb-jalen-hurts-out-2026-season-blood-clots |

Full machine-readable captures with per-row source links: `data/*.json`. Source registry: `data/sources.json`.

## 3. Market context (important)

The NFL does **not** publish betting lines. Any spread/total you see on a website is a **sportsbook's** number and moves constantly. The few lines visible on third-party aggregators on 2026-11-03 (attributed to FanDuel) are recorded as **unverified** in `data/market-lines.json` and flagged (F-05). In the Netherlands you may only use providers licensed by the **Kansspelautoriteit** — check https://kansspelautoriteit.nl/kansspelwijzer before using any book. Our own lines below are **model outputs computed from official stats**, not official NFL values.

## 4. Line origination model (transparent, reproducible)

`scripts/analyze.py` (stdlib only, no manual input) computes, per Week 9 game:

- `proj_team = (team PF/game + opponent PA/game) / 2`, with a home-field assumption of **2.5 pts** (flagged F-07 — an assumption, not an official value)
- **model spread** = proj_home − proj_away; **model total** = sum of projections
- **edge** = model spread − market spread, only where a market line was captured (unverified); a play is a *candidate* only when `1.0 ≤ |edge| ≤ 8.0` points (the 8.0 cap rejects model blow-ups)

Week 9 output (see Model Lines page), updated 2026-11-04: **0 verified candidates**. An earlier build listed CIN at ATL and NYG at PHI as candidates, but that was a gate error: G6 (edge vs market) passed on a third-party market value that the project's own rules classify as unverified (F-05, corrected under F-17). Model spreads and edges are now shown for reference only, and G6 is NOT_COMPUTABLE for all games. The official Week 9 injury report is now published; CIN, ATL, NYG and PHI are all listed as "No Injuries Reported".

## 5. Validation gates (every strategy must pass)

G1 official sources only · G2 data freshness ≤ 7 days · G3 sample ≥ 4 games · G4 injury/news check against the latest official report · G5 correlation check for any multi-leg bet · G6 edge vs market within sanity band · G7 stake cap (≤ 2% bankroll singles, ≤ 1% parlays — Kelly-style, assumption F-07). Week 9 status: G1–G3 PASS for all 15 games; G4 CONDITIONAL everywhere (Week 9 injury report not yet published — must be re-checked at https://www.nfl.com/injuries/ before acting); G6 computable for 6 games (unverified market input), NOT_COMPUTABLE for 9 (blank by rule).

## 6. Correlation discipline

Computed from the 32-team official data (`analysis/correlations.json`), e.g. net points/game vs win% **r = +0.84** (skill anchor), pass YDS/game vs PF/game **r = +0.67** (same-game QB↔team-total proxy), pass vs rush YDS/game **r = −0.32** (game script). Parlays (S6) are built only from **different games** (cross-game correlation ≈ 0); same-game parlays (S7) are **blocked by default** for correlated combos (QB over + team over) and only contrarian pairs may be reviewed when pair |r| < 0.80.

## 7. Bet shapes covered

- **Singles:** S1 Form Spread, S2 Totals (limited this week — only one third-party total captured, unverified)
- **Player props:** S3 QB passing (matchup factor + Next Gen CPOE), S4 RB rushing vs run defense, S5 WR receiving vs pass defense with official injury adjustments (McLaurin/Hurts)
- **Parlays:** S6 de-correlated 2-leg (different games), S7 same-game restricted
- **Live betting:** S8 not covered — no official live feed captured; left blank rather than simulated

## 8. Leaderboard competition

Strategies earn points when official scores post (ROI at −110 vig, stake-capped), graded automatically by re-running the pipeline — no manual input. Tiers: **Gold ≥ +5.0 pts, Silver ≥ 0, Bronze < 0**, tie-break by Sharpe-like ratio. Rewards are **points/trophies only** — this project places no real-money wagers (F-10). Current standings (all 0.0 realized points; Week 9 projections on the Leaderboard page).

## 9. Removing luck

- Anchoring on **net points per game** (r = 0.84 vs win%) instead of raw W-L
- Sanity-capped edges (|edge| ≤ 8) so blowout-driven model outliers don't masquerade as skill
- Regression-style matchup projections (offense vs defense) rather than narrative
- Turnover-luck metrics are **not** applied (fumble data not in captured categories — flagged F-09, so nobody assumes they were)
- Every input re-verified weekly against official sources; stale data fails G2

## 10. Flagged for review (does not block; see site page)

F-01 standings tail columns omitted (labels unverifiable) · F-02 player team affiliations not rendered on leader pages (null + player-page links) · F-03 two unlabeled receiving tail columns kept as raw keys · F-04 Week 9 injury report not yet published · F-05 market lines are unverified third-party · F-06 third-party record discrepancies discarded in favor of NFL.com · F-07 model assumptions (HFA 2.5, −110, stake caps) labeled as assumptions · F-08 top-25 pagination · F-09 no fumble-based luck metric · F-10 no real-money wagering; 18+ NL / 21+ where required; CRUKS self-exclusion https://kansspelautoriteit.nl/uitsluitregister-cruks; US helpline 1-800-GAMBLER https://www.ncpgambling.org/.

## 11. Repo & site

This repository hosts the data, analysis, research and the live GitHub Pages dashboard (`docs/`). Landing page + subpages by category: Standings, Week 9 Schedule, Week 8 Scores, Team Stats, Player Stats, Injuries & News, Model Lines, Prop Signals, Strategies, Validation Gates, Correlations, Leaderboard, Sources, Flagged for Review, Methodology, Executive Summary. Every table row carries its official source link. Build: `python3 scripts/build_site.py`; link check: `python3 scripts/check_links.py`.
