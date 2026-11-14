"""Data-layer checks for the Week 10 official injury transcription. Stdlib only. Exit 1 on failure.

Checks: JSON counts (14 games, 28 teams, 345 rows); transcription ROW count equals JSON rows;
every row has nfl.com source URLs; positions and game statuses are from the allowed sets;
per-game row counts equal the transcription's per-game counts; 'Out' and 'Doubtful' tallies match.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
inj = json.loads((HERE / "data" / "injuries-2026-w10.json").read_text(encoding="utf-8"))
raw = (HERE / "data" / "raw" / "injury-w10-transcription.txt").read_text(encoding="utf-8").splitlines()
fail = []
if (len(inj["games"]), len(inj["teams"]), len(inj["rows"])) != (14, 28, 345):
    fail.append("counts changed from 14/28/345")
raw_rows = [l for l in raw if l.startswith("ROW|")]
if len(raw_rows) != len(inj["rows"]):
    fail.append(f"transcription ROW lines {len(raw_rows)} != JSON rows {len(inj['rows'])}")
game_rows = {}
for r in inj["rows"]:
    game_rows[r["game_slug"]] = game_rows.get(r["game_slug"], 0) + 1
    if not all(u.startswith("https://www.nfl.com/") for u in r["source_urls"]):
        fail.append(f"{r['id']}: non-nfl.com source")
    if r["position"] not in {"QB", "RB", "FB", "WR", "TE", "T", "G", "C", "DE", "DT", "LB", "CB", "S", "K", "P", "LS"}:
        fail.append(f"{r['id']}: unknown position {r['position']!r}")
    if r["game_status"] not in {"", "Out", "Doubtful", "Questionable"}:
        fail.append(f"{r['id']}: unknown game status {r['game_status']!r}")
for g in inj["games"]:
    if game_rows.get(g["game_slug"]) != g["rows"]:
        fail.append(f"{g['game_slug']}: game row count mismatch")
statuses = [r["game_status"] for r in inj["rows"]]
tally = {s: statuses.count(s) for s in ("Out", "Doubtful", "Questionable", "")}
if tally != {"Out": 66, "Doubtful": 10, "Questionable": 84, "": 185}:
    fail.append(f"status tallies changed: {tally}")
if fail:
    print("FAIL"); [print(" -", f) for f in fail]; sys.exit(1)
print(f"PASS: {len(inj['rows'])} rows, {len(inj['games'])} games, {len(inj['teams'])} teams; statuses {tally}")
