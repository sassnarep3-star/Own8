# Correlation Policy — how correlation values are determined and enforced

## Computed values (from official data, 32 teams, season through Week 8 — `analysis/correlations.json`)

| Pair | Type | r |
| --- | --- | --- |
| Net points/game vs win% | Pearson | +0.84 |
| Net points/game rank vs win% rank | Spearman | +0.85 |
| Points-for/game vs win% | Pearson | +0.62 |
| Offensive pass YDS/game vs points-for/game | Pearson | +0.67 |
| Defensive pass YDS allowed/game vs points-against/game | Pearson | +0.37 |
| Offensive rush YDS/game vs points-for/game | Pearson | +0.18 |
| Defensive rush YDS allowed/game vs points-against/game | Pearson | +0.60 |
| Team pass rating vs win% | Pearson | +0.58 |
| Offensive pass YDS/game vs offensive rush YDS/game (game script) | Pearson | −0.32 |

## Rules

1. **Parlays across different games (strategy S6):** cross-game correlation is treated as ≈ 0 by construction — legs must come from different games; max 2 legs this season phase.
2. **Same-game parlays (strategy S7):** mechanically correlated combos (QB over + team total over; RB over + team total over; favorite spread + over) are **blocked by default**. Only contrarian pairs may be submitted for review, and only if the pair's |r| < **0.80** using the computed table above (proxy for same-game QB↔team-total: r = +0.67; game-script pass↔rush: r = −0.32).
3. **Prop combos (player props):** a player prop combined with his own team's game bet in the same game is treated as correlated (default blocked); a player prop in game A combined with a prop in game B is allowed (cross-game).
4. **Correlation values are recomputed weekly** from the latest official data; the threshold 0.80 is a framework parameter (assumption, flagged F-07), not a measured constant.
5. Correlations are computed, never asserted: `python3 scripts/analyze.py` regenerates `analysis/correlations.json` from `data/*.json`.
