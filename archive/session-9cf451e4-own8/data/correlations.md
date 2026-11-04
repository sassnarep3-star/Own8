# Correlation Values — Computed from Official Data


Computed with Pearson correlation (r) from verified official NFL data:
- Team table: data/nfl-2026-standings.csv (source: https://www.nfl.com/standings/, 2026 REG, fetched 2026-11-03)
- Player tables: data/nfl-2026-{passing,rushing,receiving}.csv (source: https://nextgenstats.nfl.com/stats/..., 2026 REG, fetched 2026-11-03)

n/a = not computable (insufficient data or missing values).

## Team-level correlations (32 teams, 2026 REG)


| Variable A | Variable B | Teams | Pearson r | Interpretation | Source |
|---|---|---:|---|---|---|
| Wins | Points For | 32 | +0.584 | positive, moderate | https://www.nfl.com/standings/ |
| Wins | Points Against | 32 | -0.535 | negative, moderate | https://www.nfl.com/standings/ |
| Wins | Net Points | 32 | +0.808 | positive, strong | https://www.nfl.com/standings/ |
| Win % | Points For / Game | 32 | +0.618 | positive, moderate | https://www.nfl.com/standings/ |
| Win % | Points Against / Game | 32 | -0.581 | negative, moderate | https://www.nfl.com/standings/ |
| Points For | Points Against | 32 | +0.044 | positive, weak | https://www.nfl.com/standings/ |
| Win % | Home Win % | 32 | +0.881 | positive, strong | https://www.nfl.com/standings/ |
| Win % | Road Win % | 32 | +0.600 | positive, moderate | https://www.nfl.com/standings/ |
| Win % | Division Win % | 32 | +0.800 | positive, strong | https://www.nfl.com/standings/ |
| Win % | Conference Win % | 32 | +0.895 | positive, strong | https://www.nfl.com/standings/ |

## Player-level correlations (Next Gen Stats leaders tables)

| Variable A | Variable B | Players | Pearson r | Source |
|---|---|---:|---|---|
| Pass attempts vs Passing yards (QB) | 32 | +0.573 | positive, moderate | https://nextgenstats.nfl.com/stats/passing/2026/REG/1 |
| Pass attempts vs Passer rating (QB) | 32 | -0.179 | negative, weak | https://nextgenstats.nfl.com/stats/passing/2026/REG/1 |
| Rush attempts vs Rushing yards (RB) | 34 | +0.788 | positive, strong | https://nextgenstats.nfl.com/stats/rushing/2026/REG/1 |
| Targets vs Receiving yards (WR/TE) | 47 | +0.396 | positive, weak | https://nextgenstats.nfl.com/stats/receiving/2026/REG/1 |
| Receptions vs Receiving yards (WR/TE) | 47 | +0.510 | positive, moderate | https://nextgenstats.nfl.com/stats/receiving/2026/REG/1 |

## Notes

- Correlations are descriptive of the fetched snapshot only; they are not predictive signals.
- Player tables appear to contain partial/early-season totals relative to games played in the standings (see data/sources.md, UNVERIFIED items); player-level correlations are therefore flagged UNVERIFIED.
- Betting-market correlations (e.g., same-game parlay leg correlation) cannot be computed: odds are not published by official NFL sources and are left blank.
