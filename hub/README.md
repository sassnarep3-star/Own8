# hub/ — NFL 2026 dashboard (session 101b20bc)

Static, dependency-free dashboard. Open `hub/index.html` locally, or on GitHub Pages at `/Own8/hub/`.

## Rebuild and check

```sh
python3 hub/scripts/build_hub.py   # regenerates hub/index.html and hub/pages/*.html
python3 hub/scripts/check_hub.py   # links, source-link-per-row rule, standings arithmetic, injury rows
```

Standard library only (Python 3.11+).

## Inputs

| File | What | Source |
| --- | --- | --- |
| `data/standings-official.csv` | 32 official standings rows, 2026-11-14 | https://www.nfl.com/standings/ |
| `data/injuries-w10.csv` | Week 10 injury rows (blocks A-D complete, E partial) | https://www.nfl.com/injuries/league/2026/reg10 |
| `data/content.json` | Repo review, questions, suggestions, flags, source register | See each row's links |
| `../origination/results/*.json` | Lines, strategies, correlations (read only, republished) | Earlier session; see `origination/README.md` |

## Rules

- Every table row links to a source (checked by `check_hub.py`).
- Values not confirmed from an official source are left blank and flagged.
- Suggestions are options only. Nothing on the Suggestions page is implemented until you choose an option.
- No rewards, betting recommendations or legal opinions.
