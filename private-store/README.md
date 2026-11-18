# private-store (row-level official captures)

Holds row-level player data from official nfl.com pages that the public site must not publish until the source terms have been read.

- `injury-report-2026-w11.tsv`: the 26 Week 11 club rows (team, player, position, injury column, practice status, game status), transcribed from https://www.nfl.com/injuries/league/2026/reg11 (retrieved before 2026-11-18T06:29:20Z).
- The Pages build excludes this folder (`_config.yml`). The site reads it only to compute counts; no player name is published.
- Integrity: `captures/scripts/check_captures.py` re-hashes this file against `captures/manifest.json`.

Limit: the repository is public, so this folder is not private from GitHub readers. Moving it needs an operator decision (flag F-31).
