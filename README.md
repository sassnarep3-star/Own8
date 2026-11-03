# Own8 — NFL Line-Origination Lab

Originate your own NFL lines from **official verified sources only**, run every strategy through explicit **validation gates**, enforce computed **correlation limits**, and compete on a **skill leaderboard** across single bets, parlays, and player-prop combos. Built to remove luck and keep selectively skill-based signals. No manual input: the pipeline is fully scripted.

- **Live site (GitHub Pages):** https://sassnarep3-star.github.io/Own8/ (dashboard with all entries, tables, analysis, and the Flagged for Review page)
- **As of:** 2026-11-03 — 2026 NFL season, after Week 8, ahead of the Week 9 slate (Nov 5–9)

## Verification rule

Every table row on the site carries a **source link to an official site** (nfl.com, nextgenstats.nfl.com, or — for the user's jurisdiction — kansspelautoriteit.nl). If a value cannot be confirmed from an official source, the cell is left **blank** and the item is published on the **⚑ Flagged for Review** page (`data/flagged.json`). Nothing is inferred or filled in.

## Repo layout

| Path | Contents |
| --- | --- |
| `COORDINATION.md` | Shared multi-session task board (claims, statuses, log, PR record) |
| `data/*.json` | Official-source data captures (standings, W9 schedule, W8 scores, team/player stats, Next Gen Stats, injuries, news) — each row with its source URL; plus `sources.json` (registry), `market-lines.json` (unverified third-party reference), `flagged.json` (flagged/unverified register) |
| `analysis/*.json` | Computed outputs: correlations, Week 9 model lines + gates, prop signals, strategies, leaderboard, link-check |
| `research/*.md` | Executive summary, methodology, validation gates, correlation policy, strategies, leaderboard rules, responsible gambling |
| `scripts/analyze.py` | Analysis pipeline (stdlib only): correlations + line origination + gates + leaderboard |
| `scripts/build_site.py` | Generates the static site in `docs/` |
| `scripts/check_links.py` | Verifies no broken internal links and https/allowlisted external links → `analysis/link-check.json` |
| `docs/` | The GitHub Pages site (served from `/docs`) |

## Run it yourself

```bash
python3 scripts/analyze.py      # recompute analysis from data/*.json
python3 scripts/build_site.py   # rebuild docs/
python3 scripts/check_links.py  # verify links; exits non-zero on broken links
```

## Highlights (2026-11-03)

- Week 9 model-line candidates after all gates: **CIN at ATL** and **NYG at PHI**; JAX–BAL, NYJ–KC, LV–SF rejected by the 8-point edge sanity cap (anti-luck filter).
- Correlations computed from all 32 teams: net points/game vs win% **r = +0.84**; same-game parlays blocked by default (proxy r = +0.67, threshold 0.80).
- Official news applied: Jalen Hurts (PHI) on IR — likely out for season; Terry McLaurin (WAS) out for season (both nfl.com news).
- Week 9 injury report not yet published on NFL.com (flagged F-04); latest official report is Week 8.

## Responsible gambling

Research/analytics only — no real-money wagering occurs in this project; leaderboard rewards are points. In the Netherlands use only Ksa-licensed providers (verify: https://kansspelautoriteit.nl/kansspelwijzer); self-exclude via CRUKS: https://kansspelautoriteit.nl/uitsluitregister-cruks. 18+ (NL) / 21+ where required. US helpline: 1-800-GAMBLER (https://www.ncpgambling.org/). See `research/responsible-gambling.md`.
