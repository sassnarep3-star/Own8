# Own8 — NFL Line-Origination Lab

Originate your own NFL lines from **official verified sources only**, run every strategy through explicit **validation gates**, enforce computed **correlation limits**, and compete on a **skill leaderboard** across single bets, parlays, and player-prop combos. Built to remove luck and keep selectively skill-based signals. No manual input: the pipeline is fully scripted.

- **Live site (GitHub Pages):** https://sassnarep3-star.github.io/Own8/
- **Complementary historical backtest lab:** https://sassnarep3-star.github.io/Own8/site/ (session 28cc78aa — 1999–2026 backtests, correlation library, gated leaderboard)
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

---

## Complementary historical backtest lab (session 28cc78aa)

A second, independent analysis adds **deep historical backtesting** alongside the 2026-snapshot
dashboard above. It is served at **https://sassnarep3-star.github.io/Own8/site/** by the same
root GitHub Pages, and is fully reproducible.

- **Data:** 7,548 games (1999–2026) + closing lines; 479,089 book-level opening/closing odds
  (2006–2021); 59,989 player-game stat rows (2009–2017); a 2021 robustness sample; and an
  **official NFL anchor** (`nfl-football-ops/Big-Data-Bowl`). Game results matched **91/91 exactly**
  vs the NFL's official published scores.
- **13 strategies** (singles, same-game parlays, player-prop combos) backtested walk-forward and
  scored on a **7-gate leaderboard** that removes luck (CLV, bootstrap CIs, binomial-at-vig null,
  season robustness). Headline: **S2 (model total value @ opening line)** is the only robust skill
  signal — **CLV +0.80 pts, z ≈ 5.7** → Silver. No strategy reached Gold (the closing market is efficient).
- **16 correlation estimates** with bootstrap 95% CIs + 2021 check: QB↔WR1 r = 0.695, WR1↔WR2 r = 0.492,
  QB↔own-RB r = −0.178, cover↔total φ ≈ 0 — the inputs for correct same-game-parlay pricing.
- **21 official NFL facts** quoted verbatim with source links; executive summary; provenance + gates docs.

Files (namespaced so the canonical root pipeline above is untouched):

- `EXECUTIVE_SUMMARY.md`, `docs/STRATEGY_RESEARCH.md`, `docs/VALIDATION_GATES.md`,
  `docs/DATA_PROVENANCE.md`, `docs/SOURCES.md`, `docs/REPO_REVIEW.md`, `data/official_facts.json`
- `data/results/*.json` — computed validation, correlations, strategies, leaderboard, market context
- `scripts/fetch_data.py`, `scripts/own8_analyze.py`, `scripts/own8_build_site.py`, `scripts/own8_check_links.py`
- `site/` — the 12-page complementary dashboard (per-row source links + Flagged for Review)

```bash
pip install -r requirements.txt
python3 scripts/fetch_data.py        # download primary data + sha256 manifest (data/raw/, git-ignored)
python3 scripts/own8_analyze.py      # recompute historical results -> data/results/
python3 scripts/own8_build_site.py   # regenerate site/
python3 scripts/own8_check_links.py  # verify no broken links
```

Market lines are **PRIMARY (non-NFL)** (the NFL does not publish betting lines): cross-checked
between two independent mirrors and flagged, never presented as official. Unconfirmable values
are left blank and marked UNVERIFIED. See `site/flagged.html`.

---

## Coordination & deploy record

`COORDINATION.md` is the shared task board: session claims (9cf451e4, 95e9626f, 28cc78aa),
PRs #1–#6 with merge commits, GitHub Pages deploy confirmation, conflict-resolution log, and irregularities.

## Responsible gambling

Research/analytics only — no real-money wagering occurs in this project; leaderboard rewards are points. In the Netherlands use only Ksa-licensed providers (verify: https://kansspelautoriteit.nl/kansspelwijzer); self-exclude via CRUKS: https://kansspelautoriteit.nl/uitsluitregister-cruks. 18+ (NL) / 21+ where required. US helpline: 1-800-GAMBLER (https://www.ncpgambling.org/). See `pages/responsible-gambling.html` / `research/responsible-gambling.md`.
