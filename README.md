# Own8 — NFL Line Lab

Collect, organize, and analyze NFL data to **originate our own betting lines** (spreads,
totals, moneylines, player props), research signals for **single bets, parlays, and player-prop
combos**, **determine correlation values**, and run everything as a **leaderboard competition**
where each strategy must pass **validation gates that remove luck** and reward only selectively
skill-based edges.

**Live dashboard:** https://sassnarep3-star.github.io/Own8/ (GitHub Pages, deployed from `main`).

## What's here

| Path | Contents |
|---|---|
| `EXECUTIVE_SUMMARY.md` | Important details at a glance |
| `docs/STRATEGY_RESEARCH.md` | Signal design, correlation findings, luck-removal method |
| `docs/VALIDATION_GATES.md` | The 7 gates, leaderboard scoring, reward tiers |
| `docs/DATA_PROVENANCE.md` | Every dataset, publisher, SHA-256, verification tier |
| `docs/SOURCES.md` | Official NFL sources + research references (all linked) |
| `docs/REPO_REVIEW.md` | Line-by-line audit of the starting repository |
| `data/official_facts.json` | 21 facts verified verbatim from NFL sources |
| `data/results/*.json` | All DERIVED numbers (validation, correlations, strategies, leaderboard) |
| `scripts/fetch_data.py` | Reproducible primary-data acquisition (GitHub API) |
| `scripts/analyze.py` | Validation + correlations + walk-forward backtests + gates |
| `scripts/build_site.py` | Generates the static dashboard in `site/` |
| `scripts/check_links.py` | Fails the build on any broken internal link |
| `site/` | The dashboard (landing + category subpages + Flagged for Review) |
| `COORDINATION.md` | Shared multi-session task board |

## Headline result

The only strategy with a robust, luck-free skill signal is **S2 — model total value at the
opening line**: it beats the closing total by **~0.80 points** (holdout z ≈ 5.7), earning
**Silver**. No strategy reached Gold — naive models do not beat the efficient closing market
after vig, consistent with the peer-reviewed evidence. Player props are strongly correlated
(QB↔WR1 r ≈ 0.70), which is the key input for correct same-game-parlay pricing.

## Verification policy

- **OFFICIAL** values are quoted verbatim from NFL-owned sources, each row linked.
- **Market lines are not published by the NFL** → labeled **PRIMARY (non-NFL)**, cross-checked
  between two independent mirrors, and flagged. Never presented as official.
- Unconfirmable values are left **blank** and marked **UNVERIFIED**. Nothing is inferred or fabricated.
- Irregularities are published on the **Flagged for Review** page (non-blocking).

## Reproduce

```bash
pip install -r requirements.txt
python3 scripts/fetch_data.py     # download primary data + sha256 manifest (data/raw/, git-ignored)
python3 scripts/analyze.py        # recompute every DERIVED number -> data/results/
python3 scripts/build_site.py     # regenerate site/
python3 scripts/check_links.py    # verify no broken links
```

Raw data (`data/raw/`) is git-ignored; the verified results JSON and the site are committed.

## Disclaimer

Research and education only — **not betting advice**. Gamble responsibly and only where legal.
