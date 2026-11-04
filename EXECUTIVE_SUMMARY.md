# Executive Summary — Own8 NFL Line Origination & Strategy Competition

**Date:** 2026-11-03 · **Session:** `28cc78aa` · **Branch:** `arena/28cc78aa-own8`
**Live dashboard:** GitHub Pages (see `COORDINATION.md` for the deployed URL after merge).

## Mission

Collect, organize, and analyze NFL data to **originate our own betting lines** (spreads,
totals, moneylines, player props), research signals for singles / parlays / prop combos,
**determine correlation values**, and run the whole thing as a **leaderboard competition**
where each strategy must pass **validation gates** that **remove luck** and reward only
selectively skill-based edges. Every published value is verified line-by-line against an
official or named primary source, with a link on every table row.

## What was built

1. **Verified data foundation** — 7,548 games (1999–2026) with closing market lines; 479,089
   book-level opening/closing odds quotes (2006–2021); 59,989 player-game stat rows (2009–2017);
   a 2021 modern-era robustness sample; and an **official NFL anchor** (the NFL's own
   `nfl-football-ops` Big Data Bowl data). See `docs/DATA_PROVENANCE.md`.
2. **Line-by-line validation** — game results matched **91/91 exactly** against the NFL's
   official published scores; two independent odds mirrors agree within 0.5 pt on 93.4% of
   spreads / 98.5% of totals (MAD 0.18 / 0.15); player-stats internal consistency 96.9% exact.
3. **Line-origination engine** — a transparent walk-forward team-rating model (no leakage)
   producing spreads, totals, and moneyline probabilities, plus a dual-estimator player-prop
   line origination (accuracy line + fair 50/50 line).
4. **13 strategies** across single bets, same-game parlays, and player-prop combos, each
   backtested out-of-sample and scored on a 7-gate leaderboard.
5. **Correlation library** — 16 dependency estimates with bootstrap 95% CIs and a 2021
   robustness check, the core input for correct parlay/prop-combo pricing.
6. **Clean dashboard site** — landing page + category subpages, every row source-linked,
   plus a clearly labeled **Flagged for Review** page.

## Headline findings

- **One robust skill signal exists: the model beats the opening game total by ~0.80 points**
  (holdout 2016–2021, n=158, bootstrap CI 0.53–1.09, **z = 5.68**). Closing-line value is
  outcome-independent, so this is skill, not luck. It earns **Silver** — the only non-rejected
  strategy — because profit consistency (G6) is not yet proven (holdout ROI −6.9%).
- **No strategy reached Gold.** Naive models do not beat the efficient **closing** spread/total
  after vig, and the market's no-vig moneyline is better calibrated than our model
  (Brier 0.21105 vs 0.2247). This matches the peer-reviewed evidence (Moskowitz 2021) that
  betting-market edges are small relative to transaction costs.
- **Player props are strongly correlated** — the key to combo pricing:
  - QB pass yards ↔ WR1 receiving yards **r = 0.695** (2021 check 0.671).
  - QB pass yards ↔ WR2 receiving yards **r = 0.756**.
  - WR1 ↔ WR2 receiving yards **r = 0.492** (positive — stacking same-team receivers does not diversify).
  - QB pass yards ↔ own RB1 rush yards **r = −0.178** (game-script tension; a negatively correlated SGP pair).
  - RB1 rush yards ↔ team point margin **r = 0.334** (leaders run).
  - **Game-level cover ↔ total legs are ~independent (φ = −0.007)** — standard 2-leg parlay
    pricing is roughly fair there; all four cover+total parlay backtests lose the vig (−8% to −16%).
- **Key numbers confirmed:** margin 3 in 14.5% of games, margin 7 in 8.9% (2006–2025).
- **Simple prop origination is not a standalone edge** (QB +1.7% RMSE skill, CI crosses 0;
  WR/RB ≤ 0). Its value is as the input to correlation-aware combo pricing.

## Luck removal & validation

Every estimate carries a 2,000-sample bootstrap CI; win rates are tested against a binomial
null **at the posted vig**; thresholds are fit on a 2006–2015 train and judged on a 2016+
holdout; season-consistency and drop-best-season checks kill flukes; and CLV is the primary
skill metric because it does not depend on whether a bet wins. Seven gates (data integrity,
out-of-sample, beats-baseline, significance, luck-removed, robustness, correlation-correctness)
gate the reward tiers (Gold/Silver/Bronze/Rejected). Full rules: `docs/VALIDATION_GATES.md`.

## Verification & honesty policy

- **OFFICIAL** facts (rules, scoring, season structure) are quoted verbatim from NFL sources
  (nfl.com, operations.nfl.com, media.nfl.com, the official 2026 rulebook PDF, and the NFL's
  GitHub org). 21 official facts verified, each linked.
- **Market lines are not published by the NFL**, so they are labeled **PRIMARY (non-NFL)**,
  cross-checked between two independent mirrors, and flagged — never presented as official.
- Values that cannot be confirmed from an official source are left **blank** and flagged
  **UNVERIFIED**. Nothing is inferred or fabricated. Historical market prop lines do not exist
  in any reachable archive, so prop work is explicitly **line origination**, not a ROI backtest.

## Flagged for review (non-blocking)

- Market-line provenance (no official NFL source exists for betting lines).
- 6.6% of spread closes differ >0.5 pt between mirrors (concentrated 2006–2013; 25 games >1.5 pt).
- 3.1% of legacy player-stat team-games have passing/receiving yardage attribution quirks.
- Player-prop correlation era caveat (2009–2017 base, 2021 check) and missing market prop lines.
- The repo started empty; all work is new. Branch-policy note (pinned Arena branch).

## Bottom line

The competition did exactly what it should: it **found one genuine, luck-free skill signal**
(opening-total line-beating), **quantified the correlation structure** needed to price player
prop combos correctly, and **rejected twelve strategies** that could not prove an edge after
vig. The deliverable is a verified, reproducible, source-linked foundation and an honest
leaderboard — not a set of too-good-to-be-true picks. Next steps to convert the S2 signal and
correlations into profit: usage-based prop features, EPA ratings, injury/lineup adjustments,
and copula-based same-game-parlay pricing with line-shopping.
