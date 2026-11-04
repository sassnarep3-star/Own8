# Strategy Catalog — bet shapes and their rules

All strategies run through the validation gates (`validation-gates.md`). Status as of 2026-11-03, Week 9 slate.

## Singles

- **S1 — Form Spread.** Model spread from the PPG matchup model vs market (unverified until checked at a licensed book). Candidate ⇔ 1.0 ≤ |edge| ≤ 8.0 and gates pass. Week 9 status (updated 2026-11-04): **0 verified candidates.** Earlier candidates CIN at ATL and NYG at PHI were demoted because G6 cannot pass on the unverified third-party market line (F-05, F-23). Market-based edges are withheld (unverified third-party line, F-05). Gates G4 for both games: PASS on the official Week 9 injury report (no injuries reported for CIN, ATL, NYG, PHI). Official news context: PHI starting backup QB Tanner McKee with Jalen Hurts on IR (nfl.com). Cap-exceeded no-trade games: JAX@BAL, NYJ@KC, LV@SF.
- **S2 — Totals.** Model total vs market total, same band. This week only one third-party total was captured (unverified) → effectively NOT_COMPUTABLE; blank, not estimated.

## Player props (model projections; compare only at a licensed sportsbook)

- **S3 — QB passing yards.** Projection = season YPG × opponent pass-defense factor (YDS allowed/game ÷ league avg), cross-checked with Next Gen Stats Week 8 (CPOE, xCOMP%, TT). Examples from the W9 slate: CLE's Deshaun Watson (season 225.8 YPG) at NO; NYJ's Geno Smith (239.1 YPG) at KC. OL quality via sacks (SK) taken vs defense SK: CLE took 33 sacks (most) — temper the over.
- **S4 — RB rushing yards.** Team rush projection vs opponent run-defense factor; individual allocation requires the official depth chart (player team affiliations are not rendered on the leaders page — F-02), so the site publishes team-level signals only.
- **S5 — WR receiving.** Team pass projection vs opponent pass defense × player share of team receiving; official injury adjustments (WAS: Terry McLaurin out for season → redistributed target share vs LA).

## Parlays

- **S6 — De-correlated 2-leg parlay:** two S1 candidates from **different games**; cross-game correlation ≈ 0; stake ≤ 1% bankroll.
- **S7 — Same-game parlay (restricted):** correlated combos blocked by default; contrarian pairs only, pair |r| < 0.80 per `correlation-policy.md`.

## Not covered

- **S8 — Live/in-game:** no official live feed captured; left blank (flagged) rather than simulated.

## Leaderboard

See `leaderboard-rules.md`. Points only — no real-money wagering (F-10).
