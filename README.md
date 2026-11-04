# Own8 — NFL Line-Origination Lab

Originate your own NFL lines from **official verified sources only**, run every strategy through explicit **validation gates**, enforce computed **correlation limits**, and compete on a **skill leaderboard** across single bets, parlays, and player-prop combos. Built to remove luck and keep selectively skill-based signals. No manual input: the pipeline is fully scripted.

- **Live site (GitHub Pages):** https://sassnarep3-star.github.io/Own8/
- **As of:** 2026-11-03 — 2026 NFL season, after Week 8, ahead of the Week 9 slate (Nov 5–9)
- **Archive:** the first session's site (9cf451e4) is preserved verbatim at `archive/session-9cf451e4-own8/` (linked from the dashboard nav).

## Verification rule

Every table row on the site carries a **source link to an official site** (nfl.com, nextgenstats.nfl.com, or — for the user's jurisdiction — kansspelautoriteit.nl). If a value cannot be confirmed from an official source, the cell is left **blank** and the item is published on the **⚑ Flagged for Review** page (`data/flagged.json`). Nothing is inferred or filled in.

## Site structure (repository root, served by GitHub Pages)

- `index.html` — dashboard landing (KPIs, W9 candidates, category cards)
- `pages/` — subpages by category: executive summary, standings (W8), Week 9 schedule, Week 8 scores, team stats, player stats + Next Gen Stats, injuries & news, model lines (W9), prop signals (W9), strategies, validation gates, correlations, leaderboard, methodology, sources, **flagged-for-review**, responsible gambling
- `assets/style.css` — shared styles · `.nojekyll` — static serving

## Data & analysis (repository root)

- `data/*.json` — this session's official-source captures (standings, W9 schedule, W8 scores, team offense/defense passing+rushing, player leaders, NGS W8, injuries, news), each row with its source URL; `sources.json` registry; `market-lines.json` (unverified third-party reference); `flagged.json` (F-01…F-13 register)
- `data/nfl-2026-*.csv`, `data/sources.md`, `data/strategies.md`, `data/correlations.md`, `compute_correlations.py` — first session's captures/docs (standings verified; player CSVs flagged unverified — F-12)
- `analysis/*.json` — computed outputs: correlations, W9 model lines + gates, prop signals, strategies, leaderboard, link-check, cross-session verification
- `research/*.md` — executive summary, methodology, validation gates, correlation policy, strategies, leaderboard rules, responsible gambling
- `scripts/analyze.py` — analysis pipeline · `scripts/build_site.py` — site generator · `scripts/check_links.py` — link checker · `scripts/verify_combined.py` — cross-session data re-verification

## Run it yourself

```bash
python3 scripts/verify_combined.py  # cross-session standings re-verification
python3 scripts/analyze.py           # recompute analysis from data/*.json
python3 scripts/build_site.py        # rebuild index.html + pages/
python3 scripts/check_links.py       # verify links; exits non-zero on broken links
```

## Highlights (2026-11-03)

- Week 9 model-line candidates after all gates: **CIN at ATL** and **NYG at PHI**; JAX–BAL, NYJ–KC, LV–SF rejected by the 8-point edge sanity cap (anti-luck filter).
- Correlations computed from all 32 teams: net points/game vs win% **r = +0.84**; same-game parlays blocked by default (proxy r = +0.67, threshold 0.80).
- Official news applied: Jalen Hurts (PHI) on IR — likely out for season; Terry McLaurin (WAS) out for season (both nfl.com news).
- Week 9 injury report not yet published on NFL.com (flagged F-04); latest official report is Week 8.
- Cross-session re-verification: 32/32 teams, 0 mismatches between the two sessions' standings captures; one column-labeling issue found and fixed (F-01/F-11).

## Coordination & deploy record

`COORDINATION.md` is the shared task board: session claims, PRs #1–#5 with merge commits, GitHub Pages deploy confirmation, conflict-resolution log, and irregularities.

## Responsible gambling

Research/analytics only — no real-money wagering occurs in this project; leaderboard rewards are points. In the Netherlands use only Ksa-licensed providers (verify: https://kansspelautoriteit.nl/kansspelwijzer); self-exclude via CRUKS: https://kansspelautoriteit.nl/uitsluitregister-cruks. 18+ (NL) / 21+ where required. US helpline: 1-800-GAMBLER (https://www.ncpgambling.org/). See `pages/responsible-gambling.html` / `research/responsible-gambling.md`.
