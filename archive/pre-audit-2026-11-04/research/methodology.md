# Methodology — how lines and signals are originated

**Principle:** collect → organize → analyze, using only official verified sources. No hallucinations: if a value cannot be confirmed from an official source, the cell is blank and the item is flagged (`data/flagged.json`).

## 1. Sources (official only)

- NFL.com: standings, schedules, scores, team stats, player stats, injury report, news — https://www.nfl.com/
- NFL Next Gen Stats (official NFL tracking data): https://nextgenstats.nfl.com/ (definitions: https://nextgenstats.nfl.com/glossary)
- Jurisdiction (user in the Netherlands): Kansspelautoriteit https://kansspelautoriteit.nl/ (licence check: https://kansspelautoriteit.nl/kansspelwijzer; CRUKS self-exclusion: https://kansspelautoriteit.nl/uitsluitregister-cruks)
- US responsible gambling: NCPG https://www.ncpgambling.org/ (1-800-GAMBLER)

Sportsbook lines are **not** official. They are dynamic, sportsbook-specific, and in this project are only ever recorded as unverified third-party captures (`data/market-lines.json`, flagged F-05).

## 2. Collection

Captured 2026-11-03 into `data/*.json`, each row carrying `source_url`. Column orders were validated arithmetically where possible (e.g., CMP/ATT = CMP%, YDS/ATT = AVG, 1ST/ATT = 1ST% on every row of the team stat tables; 1ST/REC = 1ST% on receiving; 40+ ≤ 20+ consistent with LNG on rushing). Where a label could not be verified from the capture (e.g., two trailing receiving columns), values are kept under neutral keys and flagged (F-03) instead of being mislabeled.

## 3. Analysis (`scripts/analyze.py`, stdlib only)

1. Per-team rates: PF/game, PA/game, net/game, pass/rush YDS per game, defensive YDS allowed per game, from `data/standings-2026-reg-w8.json` + team stat files.
2. Correlations across all 32 teams (Pearson and Spearman) → `analysis/correlations.json`.
3. Line origination for each Week 9 game:
   - `proj_away = (PFpg_away + PApg_home)/2 − HFA/2`
   - `proj_home = (PFpg_home + PApg_away)/2 + HFA/2`  (HFA = 2.5 is an **assumption**, flagged F-07)
   - `model_spread_home = proj_home − proj_away`; `model_total = proj_home + proj_away`
   - `edge = model_spread_home − market_spread_home` (only where a market line exists in the unverified capture)
   - candidate ⇔ `1.0 ≤ |edge| ≤ 8.0` **and** all gates PASS/CONDITIONAL → `analysis/model-lines-week9.json`
4. Player-prop projections: `QB proj = QB season YPG × (opp pass-def YDS allowed/game ÷ league avg)`; team rush/pass projections likewise → `analysis/prop-signals-week9.json`. Market prop lines are blank by rule (no official source).
5. Strategy definitions + gates → `analysis/strategies.json`; leaderboard → `analysis/leaderboard.json`.

## 4. Verification pass

`scripts/check_links.py` parses every generated HTML page and verifies (a) all internal links resolve to files that exist, (b) every external link uses https and is on the official-source allowlist or is explicitly marked as a flagged third-party link. Results are written to `analysis/link-check.json` and summarized on the site.

## 5. Weekly refresh (no manual input)

After each week's games: re-capture official pages → re-run `python3 scripts/analyze.py` → grade settled bets from official scores (nfl.com/scores) → update leaderboard → rebuild site (`python3 scripts/build_site.py`) → run link check. The whole loop is scripted.
