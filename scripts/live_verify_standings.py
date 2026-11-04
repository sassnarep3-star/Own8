#!/usr/bin/env python3
"""Session c03eba88: live re-verification of data/standings-2026-reg-w8.json
against the official source https://www.nfl.com/standings/ fetched on 2026-11-04
(transcribed verbatim from fetch_page chunks into /tmp/live_standings_2026-11-04.md
because direct curl is blocked in this sandbox — same workaround as IR-02).

Compares all 32 teams field by field (W,L,T,PCT,PF,PA,NET,HOME,ROAD,DIV,DIVPCT,
CONF,CONFPCT,STRK) and re-runs the arithmetic checks. Writes
analysis/live-verify-standings-2026-11-04.json. Exits non-zero on any mismatch.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = Path("/tmp/live_standings_2026-11-04.md")

live = {}
for line in LIVE.read_text().splitlines():
    if line.startswith("#") or not line.strip():
        continue
    c = [x.strip() for x in line.split("|")]
    live[c[0]] = {
        "W": int(c[1]), "L": int(c[2]), "T": int(c[3]), "PCT": float(c[4]),
        "PF": int(c[5]), "PA": int(c[6]), "NET": int(c[7]),
        "HOME": c[8].replace(" ", ""), "ROAD": c[9].replace(" ", ""),
        "DIV": c[10].replace(" ", ""), "DIVPCT": float(c[11]),
        "CONF": c[12].replace(" ", ""), "CONFPCT": float(c[13]),
        "STRK": c[15],
    }

cap = json.load(open(ROOT / "data/standings-2026-reg-w8.json"))["teams"]
report = {
    "verified_at": "2026-11-04",
    "live_source": "https://www.nfl.com/standings/ (fetched 2026-11-04 UTC via fetch_page; curl blocked in sandbox)",
    "captured_file": "data/standings-2026-reg-w8.json (captured 2026-11-03)",
    "teams_compared": 0, "mismatches": [], "arith": [], "status": "PASS",
}

fields = ["W", "L", "T", "PCT", "PF", "PA", "NET", "HOME", "ROAD", "DIV", "DIVPCT", "CONF", "CONFPCT", "STRK"]
for t in cap:
    a = t["abbr"]
    report["teams_compared"] += 1
    lv = live.get(a)
    if lv is None:
        report["mismatches"].append(f"{a}: missing from live fetch")
        continue
    for f in fields:
        cv, lv_v = t[f], lv[f]
        if isinstance(cv, float):
            ok = abs(cv - lv_v) <= 0.0005
        else:
            ok = cv == lv_v
        if not ok:
            report["mismatches"].append(f"{a}.{f}: captured={cv} live={lv_v}")
    # arithmetic checks on live values
    hw, hl, ht = map(int, lv["HOME"].split("-"))
    rw, rl, rt = map(int, lv["ROAD"].split("-"))
    if (hw + rw, hl + rl, ht + rt) != (lv["W"], lv["L"], lv["T"]):
        report["arith"].append(f"{a}: HOME+ROAD != record")
    # NFL win% counts ties as half a win: (W + T/2) / GP
    dw, dl, dt = map(int, lv["DIV"].split("-"))
    exp = round((dw + dt / 2) / (dw + dl + dt), 3) if (dw + dl + dt) else 0.0
    if abs(exp - lv["DIVPCT"]) > 0.0005:
        report["arith"].append(f"{a}: DIV% mismatch {exp} vs {lv['DIVPCT']}")
    cw, cl, ct = map(int, lv["CONF"].split("-"))
    exp = round((cw + ct / 2) / (cw + cl + ct), 3) if (cw + cl + ct) else 0.0
    if abs(exp - lv["CONFPCT"]) > 0.0005:
        report["arith"].append(f"{a}: CONF% mismatch {exp} vs {lv['CONFPCT']}")
    # overall PCT check with tie adjustment
    exp_pct = round((lv["W"] + lv["T"] / 2) / (lv["W"] + lv["L"] + lv["T"]), 3) if (lv["W"] + lv["L"] + lv["T"]) else 0.0
    if abs(exp_pct - lv["PCT"]) > 0.0005:
        report["arith"].append(f"{a}: PCT mismatch {exp_pct} vs {lv['PCT']}")
    if lv["PF"] - lv["PA"] != lv["NET"]:
        report["arith"].append(f"{a}: PF-PA != NET")

if len(live) != 32:
    report["mismatches"].append(f"live fetch has {len(live)} teams, expected 32")
if report["mismatches"] or report["arith"]:
    report["status"] = "FAIL"

out = ROOT / "analysis/live-verify-standings-2026-11-04.json"
out.write_text(json.dumps(report, indent=1))
print(json.dumps({k: (v if k not in ("mismatches", "arith") else v) for k, v in report.items()}, indent=1)[:2000])
print(f"\n{report['teams_compared']} teams compared vs live nfl.com/standings on 2026-11-04: "
      f"{len(report['mismatches'])} mismatches, {len(report['arith'])} arithmetic failures -> {report['status']}")
sys.exit(0 if report["status"] == "PASS" else 1)
