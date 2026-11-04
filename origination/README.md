# origination/ — official 2026 game log, line origination v2, skill-vs-luck lab

Owner: session **4bc92a5f** (branch `arena/4bc92a5f-own8`). Live: https://sassnarep3-star.github.io/Own8/origination/

Everything here is built **only from official NFL pages**: nfl.com scores, standings, division standings and the Week 9
schedule, plus Next Gen Stats weekly passing. **No sportsbook data is used.** Values that could not be confirmed are left
blank and listed in `results/flagged.json` / `flagged.html`. Nothing is inferred or filled in.

## Reproduce (Python 3 standard library only)

```
python3 origination/scripts/build_gamelog.py   # O1: transcriptions -> data/games-2026-w1-w8.json + standings reconciliation
python3 origination/scripts/model.py           # O2-O4: walk-forward models, gated leaderboard, correlations, luck, W9 lines
python3 origination/scripts/build_pages.py     # O5: origination/*.html + results/flagged.json
python3 origination/scripts/check_links.py     # O5: internal links + official source link on every data-table row
```

## Layout

| Path | Contents |
| --- | --- |
| `data/raw-scores-transcription.txt` | Verbatim nfl.com scores, Weeks 1–8 (121 games + bye boxes) |
| `data/raw-standings-transcription.txt` | Verbatim nfl.com league standings (32 rows × 16 columns) |
| `data/raw-division-groups.txt` | Division tables as grouped on nfl.com |
| `data/raw-schedule-w9-transcription.txt` | Verbatim nfl.com Week 9 schedule (15 games + 2 byes) |
| `data/raw-ngs-passing-transcription.txt` | Next Gen Stats weekly passing (ATT/YDS/TD/INT), Weeks 1, 3–8 (Week 2 page never rendered → blank) |
| `data/games-2026-w1-w8.json` | Verified game log; each row has the scores-page and game-page link |
| `results/*.json` | Reconciliation, checks, walk-forward predictions, leaderboard, correlations, luck, W9 lines, flags |
| `scripts/` | Build, model, statistics, page and link-check scripts |
| `*.html`, `assets/style.css` | Standalone dashboard (summary + 10 subpages) |

## Headline results (see `index.html`)

* **121/121** official games verified. **512/512** standings cells recompute exactly from the game log.
* **0 of 12** pre-registered strategies pass all 8 gates, so no medals are awarded. The best is S1 ridge margin ratings, which
  improves spread error by 1.7% versus the baseline (Holm-adjusted p = 0.32): not proven skill.
* About **60%** of the variance in team win% after 7–8 games is binomial luck.
* Combo correlations that survive Holm: QB passing yards ↔ game total r = +0.44; opposing QBs' yards r = +0.50;
  QB yards ↔ own points r = +0.40; QB attempts ↔ own margin r = −0.20. Different games in the same week are independent (ICC ≈ 0).
* Week 9 fair lines (spread, total, moneyline) are published as **unvalidated** estimates. They do not account for injuries or QB changes.
