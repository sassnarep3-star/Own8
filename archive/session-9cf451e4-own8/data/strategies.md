# Strategy Framework — Own8 NFL Lines

Originated NFL betting-line strategies: single bets, 2-3 leg parlays, and player-prop combos.
Every strategy must pass ALL validation gates before a signal is released. No signal is released
on luck alone: gates are skill-based (data completeness, sample size, correlation limits, edge vs
implied line, backtest, availability). Strategies that fail any gate are marked PAUSED with the
reason recorded. Odds-dependent values (implied probability, edge, line) are blank/UNVERIFIED
because NFL.com does not publish betting lines (see data/sources.md).

Sources: nfl.com/standings (2026 REG); nextgenstats.nfl.com (2026 REG passing/rushing/receiving).
Fetched 2026-11-03.

----------------------------------------------------------------------
VALIDATION GATES (applied to every strategy, every week)
----------------------------------------------------------------------

V1 Official-data completeness — every strategy input traced to an official source link.
V2 Sample size — minimum N observations computed from verified data (season-aggregate used as proxy;
      game-by-game history unavailable → blank/UNVERIFIED).
V3 Correlation limit — for multi-leg strategies, |Pearson r| between legs must be <= 0.45 unless the
      correlation is explicitly documented and sized down. Same-game legs require documented correlation.
V4 Edge vs implied line — modeled probability minus implied probability from line; REQUIRES sportsbook
      odds (not an official NFL source) → blank/UNVERIFIED → gate cannot pass.
V5 Backtest pass rate — historical win rate of the strategy; historical game-by-game results not
      available from official sources → blank/UNVERIFIED → gate cannot pass.
V6 Availability/injury check — all key players active per official injury report; not fetched in this
      session → blank/UNVERIFIED → gate cannot pass.

GATE RESULT: PASS = all six gates green. PAUSED = one or more gates blank/failed. No PAUSED strategy
issues a signal.

----------------------------------------------------------------------
CATEGORY A — SINGLE BETS
----------------------------------------------------------------------

SB-01 | Net-Differential Road Value (division game)
Type: Single bet — moneyline, road team
Rule: In a division matchup, back the road team when road team net points > home team net points + 10
      and road team win% >= 0.500.
Inputs (verified): net points, win% from nfl.com/standings (2026 REG).
Correlation: n/a (single leg).
Current qualified candidates from verified standings (road team net > home net + 10 and road >= .500):
  None identified from this snapshot — road favorites with a +10 net edge over the home team do not
  appear in division games on this standings snapshot. (Re-check weekly as games are added.)
Gate status: V1 PASS (verified data) | V2 blank | V3 n/a | V4 blank (odds) | V5 blank | V6 blank
Result: PAUSED — odds, backtest, and availability inputs unavailable from official sources.

SB-02 | Balanced-Game Total Under (conference game)
Type: Single bet — game total (under)
Rule: Conference matchup where combined PF+PA per game of both teams is in the bottom third of the
      league and neither team ranks in top 10 for points per game.
Inputs (verified): PF, PA, games played from nfl.com/standings.
Correlation: n/a (single leg).
Current qualified candidates: blank — per-game totals require odds-based total lines (not published by
      NFL.com); team scoring averages are computed below but no total line exists to compare against.
Gate status: V1 PASS (team scoring inputs) | V2 blank | V3 n/a | V4 blank (total line/odds) | V5 blank | V6 blank
Result: PAUSED — total line unavailable from official sources.

SB-03 | Home Favorite Efficiency Edge
Type: Single bet — moneyline, home team
Rule: Home team with win% >= 0.650 and home win% > road win% of opponent by 0.200+.
Inputs (verified): win%, home/road splits from nfl.com/standings.
Current qualified candidates: NYG (0.643, just below 0.650 threshold — does not qualify); no team meets
      all conditions on this snapshot.
Gate status: V1 PASS | V2 blank | V3 n/a | V4 blank (odds) | V5 blank | V6 blank
Result: PAUSED.

----------------------------------------------------------------------
CATEGORY B — PARLAYS (2–3 legs, different games unless correlation documented)
----------------------------------------------------------------------

P-01 | Division Favorite Moneyline 2-Leg Parlay
Type: Parlay — 2 moneyline favorites in division games, different games (no same-game legs)
Rule: Both legs: home division favorite with win% >= 0.600 and net points > 0.
Inputs (verified): win%, net points from nfl.com/standings.
Leg correlation: different games → cross-game outcome correlation treated as ~0 (documented assumption;
      not computed from game-level data → blank/UNVERIFIED).
Current qualified legs (snapshot): BUF (6-1, +52), PIT (6-2, +36), MIN (6-1, +47), CHI (6-2, +54),
      SF (6-1, +58) as home teams with win% >= 0.600 and net > 0 — home/away schedule not available
      from official source → home status blank/UNVERIFIED.
Gate status: V1 partial (standings data verified; home/away schedule blank) | V2 blank | V3 documented
      assumption (uncertified) | V4 blank (odds) | V5 blank | V6 blank
Result: PAUSED — schedule/odds/backtest/availability inputs unavailable from official sources.

P-02 | Same-Game Winner + Total (blocked by correlation gate)
Type: Same-game parlay — winner + over/under total
Rule: Not released. Same-game winner and total are positively correlated; correlation coefficient
      requires game-by-game scoring data, unavailable from official sources → |rho| unknown.
Gate status: V3 FAIL (|rho| unknown, exceeds documentation threshold) → blocked.
Result: PAUSED indefinitely until game-level data and correlation are verified.

----------------------------------------------------------------------
CATEGORY C — PLAYER PROP COMBOS
----------------------------------------------------------------------

PP-01 | QB Passing Yards Over + Same-Team WR1 Receiving Yards Over
Type: Player-prop combo, 2 legs, same team, different statistical categories
Rule: QB pass-yards over AND team's leading WR receiving-yards over. Positive correlation expected
      (passing volume benefits both) → documented, size down.
Inputs (verified context): NGS passing/rushing/receiving leaders (2026 REG) — flagged UNVERIFIED
      (totals appear low vs. games played; see data/sources.md).
Prop lines (over/under numbers): NOT published by NFL.com → blank/UNVERIFIED.
Leg correlation: positive (pass attempts correlate with receiving volume, r = +0.510 receptions vs
      receiving yards computed from verified NGS table) → within documentation rule if sized down;
      exact same-game leg rho not computed → blank/UNVERIFIED.
Gate status: V1 partial | V2 blank | V3 documented positive correlation (exact rho blank) |
      V4 blank (prop lines) | V5 blank | V6 blank (player availability)
Result: PAUSED — prop lines and availability unavailable from official sources.

PP-02 | Opposing RB Rushing Yards Split (game-script combo)
Type: Player-prop combo, 2 legs, opposing teams
Rule: Favorite's RB rushing yards UNDER + underdog's RB rushing yards OVER (expected negative
      correlation via game script).
Correlation: expected negative; game-level rushing correlation not computable from season aggregates
      → blank/UNVERIFIED.
Gate status: V3 blank (rho unknown) | V4 blank | V5 blank | V6 blank
Result: PAUSED.

----------------------------------------------------------------------
CURRENT LEADERBOARD (validation-gate results, snapshot 2026-11-03)
----------------------------------------------------------------------

| Strategy | Type | V1 Data | V2 Sample | V3 Correlation | V4 Edge | V5 Backtest | V6 Availability | Result |
|---|---|---|---|---|---|---|---|---|
| SB-01 Net-Differential Road Value | Single | PASS | blank | n/a | blank | blank | blank | PAUSED |
| SB-02 Balanced-Game Total Under | Single | PASS | blank | n/a | blank | blank | blank | PAUSED |
| SB-03 Home Favorite Efficiency Edge | Single | PASS | blank | n/a | blank | blank | blank | PAUSED |
| P-01 Division Favorite ML Parlay | Parlay | partial | blank | documented | blank | blank | blank | PAUSED |
| P-02 Same-Game Winner + Total | Same-game parlay | blank | blank | FAIL (unknown) | blank | blank | blank | PAUSED (blocked) |
| PP-01 QB Over + WR1 Over | Prop combo | partial | blank | documented | blank | blank | blank | PAUSED |
| PP-02 Opposing RB Split | Prop combo | blank | blank | blank | blank | blank | blank | PAUSED |

No strategy passes all six gates on this snapshot → NO LIVE SIGNALS ISSUED.
This is by design: skill-based selectivity means staying out when gates cannot be verified.

----------------------------------------------------------------------
CORRELATION VALUES USED
----------------------------------------------------------------------
See data/correlations.md. Team-level values (32 teams, 2026 REG standings):
  Wins vs Net Points r=+0.808 (strong positive)
  Win% vs Conference Win% r=+0.895 (strong positive)
  Win% vs Home Win% r=+0.881 (strong positive)
  Wins vs Points For r=+0.584 (moderate positive)
  Points For vs Points Against r=+0.044 (negligible)
Player-level (NGS leader tables, flagged UNVERIFIED — see data/sources.md):
  Rush attempts vs Rushing yards r=+0.788 (strong positive)
  Receptions vs Receiving yards r=+0.510 (moderate positive)
  Pass attempts vs Passing yards r=+0.573 (moderate positive)
