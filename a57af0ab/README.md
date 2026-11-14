# a57af0ab — Week 10 official injury data layer

Scope of this directory after the 2026-11-14 hand-off (see COORDINATION.md, session a57af0ab):

- `data/raw/injury-w10-transcription.txt` — row-by-row copy of the official nfl.com Week 10 (2026) injury report, one `ROW|` line per table row, `GAME|` lines per game. Source: https://www.nfl.com/injuries/league/2026/reg10 (8 chunks, fetched 2026-11-14). Schedule cross-check: https://www.nfl.com/schedules/2026/by-week/week-10.
- `parse_injuries.py` — builds `data/injuries-2026-w10.json` from the transcription (stdlib only; rejects malformed rows).
- `data/injuries-2026-w10.json` — 345 rows, 14 games, 28 teams, with per-team position-group counts. Starter and backup fields are not present: no official depth chart was found (https://www.nfl.com/teams/new-york-giants/depth-chart returns 404).
- `check_injuries.py` — data checks (counts, sources, allowed values, tallies). Run: `python3 a57af0ab/check_injuries.py`.

The HTML hub built from this data was NOT published here. The Week 10 injury hub is owned by session 101b20bc (`hub/**`). The page prepared in this session is kept in branch history (commit b91681c on arena/a57af0ab-own8).

Verification done: parser and check PASS; 67 overlapping rows in hub/data/injuries-w10.csv (session 101b20bc, chunks 0–1) were compared field by field with this file: 67/67 match, 0 mismatches. Single transcription otherwise (flag: no independent second pass over chunks 2–7).
