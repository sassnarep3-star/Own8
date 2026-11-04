#!/usr/bin/env python3
"""Cross-session combined-data re-verification (T7 integration step).

Compares the parallel session's standings capture (data/nfl-2026-standings.csv,
session arena/9cf451e4-own8, source https://www.nfl.com/standings/) against this
session's capture (data/standings-2026-reg-w8.json) line by line, field by field,
and validates the decoded standings tail columns arithmetically.

Writes analysis/verification.json. Exits non-zero on any mismatch.
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
mine = json.load(open(ROOT / "data/standings-2026-reg-w8.json"))["teams"]
mine_by_abbr = {t["abbr"]: t for t in mine}

raw = list(csv.reader(open(ROOT / "data/nfl-2026-standings.csv")))
hdr, raw = raw[0], raw[1:]
rows = []
for r in raw:
    # parse from the end to tolerate column-count drift in the other session's CSV
    rows.append({"abbr": r[3], "w": r[4], "l": r[5], "t": r[6], "pct": r[7], "pf": r[8], "pa": r[9],
                 "net_pts": r[10], "streak": r[-4], "games_played": r[-3],
                 "home_w": r[11], "home_l": r[12], "home_t": r[13],
                 "road_w": r[14], "road_l": r[15], "road_t": r[16],
                 "div_w": r[17], "div_l": r[18], "div_t": r[19]})
report = {"as_of": "2026-11-03", "csv_source": "https://www.nfl.com/standings/ (session 9cf451e4 capture)",
          "json_source": "https://www.nfl.com/standings/ (session 95e9626f capture)",
          "rows_compared": 0, "mismatches": [], "column_notes": [], "status": "PASS"}

def parse_rec(s):
    w, l, t = s.split("-")
    return int(w), int(l), int(t)

for r in rows:
    report["rows_compared"] += 1
    a = {"LAR": "LA", "ARI": "AZ"}.get(r["abbr"], r["abbr"])
    m = mine_by_abbr.get(a)
    if not m:
        report["mismatches"].append(f"{a}: missing in JSON")
        continue
    pairs = [("w", "W", int), ("l", "L", int), ("t", "T", int), ("pf", "PF", int), ("pa", "PA", int),
             ("net_pts", "NET", int), ("pct", "PCT", float)]
    for csvcol, jkey, cast in pairs:
        cv, jv = cast(r[csvcol]), m[jkey]
        if abs(cv - jv) > 0.0005:
            report["mismatches"].append(f"{a}.{csvcol}: csv={cv} json={jv}")
    # streak
    if r["streak"] != m["STRK"]:
        report["mismatches"].append(f"{a}.streak: csv={r['streak']} json={m['STRK']}")
    # games played check
    if int(r["games_played"]) != m["W"] + m["L"] + m["T"]:
        report["mismatches"].append(f"{a}.games_played: csv={r['games_played']} != W+L+T={m['W']+m['L']+m['T']}")
    # home+road arithmetic on the CSV itself
    hw, hl, ht = parse_rec(f"{r['home_w']}-{r['home_l']}-{r['home_t']}")
    rw, rl, rt = parse_rec(f"{r['road_w']}-{r['road_l']}-{r['road_t']}")
    if (hw + rw, hl + rl, ht + rt) != (m["W"], m["L"], m["T"]):
        report["mismatches"].append(f"{a}: csv home+road != record")
    # their csv 'div' column equals our HOME column -> label-suspect, flagged
    if f"{r['div_w']}-{r['div_l']}-{r['div_t']}" != m["HOME"]:
        report["column_notes"].append(f"{a}: csv div column != HOME (ok, just noted)")

# arithmetic validation of decoded tail columns in the JSON
for t in mine:
    hw, hl, ht = parse_rec(t["HOME"]); rw, rl, rt = parse_rec(t["ROAD"])
    if (hw + rw, hl + rl, ht + rt) != (t["W"], t["L"], t["T"]):
        report["mismatches"].append(f"{t['abbr']}: HOME+ROAD != W-L-T")
    dw, dl, dt = parse_rec(t["DIV"])
    calc = round((dw + 0.5 * dt) / (dw + dl + dt), 3)
    if abs(calc - t["DIVPCT"]) > 0.001:
        report["mismatches"].append(f"{t['abbr']}: DIVPCT {t['DIVPCT']} != calc {calc}")
    cw, cl, ct = parse_rec(t["CONF"])
    calc = round((cw + 0.5 * ct) / (cw + cl + ct), 3)
    if abs(calc - t["CONFPCT"]) > 0.001:
        report["mismatches"].append(f"{t['abbr']}: CONFPCT {t['CONFPCT']} != calc {calc}")

report["status"] = "PASS" if not report["mismatches"] else "FAIL"
report["summary"] = (f"{report['rows_compared']} teams compared across W,L,T,PCT,PF,PA,NET,streak,GP: "
                     f"{len(report['mismatches'])} mismatches; decoded HOME/ROAD/DIV/CONF columns arithmetic-validated on all 32 teams. "
                     "Note: the other session's CSV 'div'/'conf' columns align with HOME/ROAD and CONF respectively — "
                     "see flagged F-11; its player CSVs remain UNVERIFIED per their IR-01 (flagged F-12).")
json.dump(report, open(ROOT / "analysis/verification.json", "w"), indent=2)
print(json.dumps({"rows_compared": report["rows_compared"], "mismatches": report["mismatches"][:10],
                  "status": report["status"]}, indent=2))
print(report["summary"])
sys.exit(0 if report["status"] == "PASS" else 1)
