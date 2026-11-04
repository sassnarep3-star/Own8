# Executive Summary — Own8 NFL Lines Project

**Project:** Originate, validate, and track NFL betting-line strategies (single bets, parlays, player-prop combos)
as a leaderboard competition. **Data snapshot:** 2026 NFL Regular Season, fetched 2026-11-03.
**Sources:** NFL.com (official standings) and NFL Next Gen Stats (official player stats).
**Bottom line:** No strategy passes all validation gates on this snapshot → **no live signals issued**.
The framework is built; gating keeps luck out by design.

----------------------------------------------------------------------
1. OBJECTIVE
----------------------------------------------------------------------
Build a fully automated, source-verified NFL line-origination system. Strategies are originated
in-house, ranked on a leaderboard, and released only when they pass every validation gate.
Correlation between legs is measured and documented. Luck is removed by requiring verified skill
inputs (data completeness, sample size, correlation limits, edge vs implied line, backtest,
availability) before any signal.

----------------------------------------------------------------------
2. DATA (ALL FROM OFFICIAL VERIFIED SOURCES)
----------------------------------------------------------------------

Team standings — 32 teams, 2026 REG (source: https://www.nfl.com/standings/):
  Leaders by win%: BUF 6-1 (.857), MIN 6-1 (.857), SF 6-1 (.857), PIT 6-2 (.750), CHI 6-2 (.750)
  Best point differential: JAX +85, SF +58, CHI +54, CIN +48, BUF +52
  Worst point differential: LAC -76, PHI -65, IND -61, ARI -63, MIA -64

Player stats — Next Gen Stats 2026 REG (source: https://nextgenstats.nfl.com/stats/...):
  Passing leaders (yards): T. Shough (NO) 410, J. Love (GB) 387, B. Young (CAR) 361, J. Allen (BUF) 334
  Rushing leaders (yards): K. Walker III (KC) 173, J. Gibbs (DET) 156, D. Henry (BAL) 144
  Receiving leaders (yards): C. Olave (NO) 182, Z. Flowers (BAL) 150, C. Watson (GB) 147

⚠️ IRREGULARITY: Player-stat totals appear low relative to games played in the standings
(e.g., P. Mahomes 27 attempts, 184 yards although KC shows 7 games played). Possible partial data or
a week-filter default on the Next Gen Stats pages. Player inputs are flagged UNVERIFIED until
re-checked. See site/flagged-for-review.html and data/sources.md.

Not available from official NFL sources (left blank, flagged UNVERIFIED):
  Betting odds/lines/spreads/totals/implied probability (sportsbook data, not NFL)
  Injury/availability reports
  Historical game-by-game results for backtesting

----------------------------------------------------------------------
3. STRATEGIES ORIGINATED (7)
----------------------------------------------------------------------

Single bets (3): SB-01 Net-Differential Road Value; SB-02 Balanced-Game Total Under;
                 SB-03 Home Favorite Efficiency Edge
Parlays (2):         P-01 Division Favorite Moneyline 2-Leg Parlay; P-02 Same-Game Winner + Total
Player-prop combos (2): PP-01 QB Passing Over + Same-Team WR1 Over; PP-02 Opposing RB Rushing Split

Gate results (snapshot 2026-11-03): all 7 PAUSED.
  - PASS on data inputs where official data exists (team standings).
  - BLOCKED on odds/edge/backtest/availability — not published by official NFL sources.
  - P-02 blocked by correlation gate (same-game winner/total rho unknown).

Leaderboard: no live signals. PAUSED strategies are re-evaluated weekly as official data is refreshed.

----------------------------------------------------------------------
4. CORRELATION VALUES (computed from verified data, Pearson r)
----------------------------------------------------------------------

Team-level (32 teams, nfl.com/standings):
  Win% vs Conference Win%    r = +0.895  (strong positive)
  Win% vs Home Win%          r = +0.881  (strong positive)
  Wins vs Net Points         r = +0.808  (strong positive)
  Win% vs Division Win%      r = +0.800  (strong positive)
  Win% vs Points Per Game    r = +0.618  (moderate positive)
  Wins vs Points For         r = +0.584  (moderate positive)
  Wins vs Points Against     r = -0.535  (moderate negative)
  Win% vs Road Win%          r = +0.600  (moderate positive)
  Wins vs Net Points... (see full table: data/correlations.md)
  Points For vs Points Against r = +0.044 (negligible — scoring volume of both sides is unrelated)

Player-level (Next Gen Stats leader tables — FLAGGED UNVERIFIED):
  Rush attempts vs Rushing yards r = +0.788
  Pass attempts vs Passing yards r = +0.573
  Receptions vs Receiving yards  r = +0.510
  Pass attempts vs Passer rating r = -0.179

----------------------------------------------------------------------
5. LEADERBOARD & REWARDS (FRAMEWORK)
----------------------------------------------------------------------
Strategies are ranked by: gate-pass rate, documented correlation control, and verified-edge
consistency. Rewards for top-performing strategies are defined as allocation priority on the
weekly signal list — only strategies passing all six gates are eligible. No rewards are paid
out on unverified performance.

----------------------------------------------------------------------
6. LIMITATIONS & NEXT STEPS
----------------------------------------------------------------------
- Add verified odds source (sportsbook) to clear V4 (edge vs implied line).
- Add official injury report to clear V6 (availability).
- Add historical game-by-game data to clear V2/V5 (sample size, backtest).
- Re-fetch standings and player stats weekly (NFL.com, Next Gen Stats).
- Re-run correlation computation on refreshed data; update data/correlations.md.

----------------------------------------------------------------------
7. SOURCE LINKS
----------------------------------------------------------------------
https://www.nfl.com/standings/                      (team standings)
https://nextgenstats.nfl.com/stats/passing/2026/REG/1
https://nextgenstats.nfl.com/stats/rushing/2026/REG/1
https://nextgenstats.nfl.com/stats/receiving/2026/REG/1
http://www.nfl.com/standings/tiebreakingprocedures
https://nextgenstats.nfl.com/glossary

Full source register: data/sources.md.
