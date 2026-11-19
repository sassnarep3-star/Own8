#!/usr/bin/env python3
"""Independent check of the public Week 11 delta and the second transcription (standard library only).

1. Recomputes the headline counts of captures/2026-11-19/delta-w11-r1-to-r2.json from the two private row
   files (joined on team and player) and requires them to match exactly.
2. Requires each private row file's SHA-256 to equal captures/manifest.json.
3. Requires the sorted-row SHA-256 of the primary file to equal captures/2026-11-19/verification-second-transcription.json.
4. Requires that no player name, designation or injury text from either read appears in any public capture file
   under captures/2026-11-19/ (the meta file is public; the private rows are not).
Exit 1 on any failure. Run: python3 captures/scripts/check_delta_independent.py
"""
import glob, hashlib, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
fails = []


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def rows(rel):
    lines = [ln.rstrip("\n") for ln in open(os.path.join(ROOT, rel), encoding="utf-8") if ln.strip()]
    header = lines[0].split("\t")
    return [dict(zip(header, ln.split("\t"))) for ln in lines[1:]]


def sha256_file(rel):
    return hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()


manifest = load("captures/manifest.json")
by_id = {c["id"]: c for c in manifest["captures"]}
early_meta = by_id["injury-report-2026-w11-r1"]
late_meta = by_id["injury-report-2026-w11-r2"]
early_rel = early_meta["private_file"]
late_rel = late_meta["private_file"]
early, late = rows(early_rel), rows(late_rel)
for cap, rel in ((early_meta, early_rel), (late_meta, late_rel)):
    if sha256_file(rel) != cap["private_sha256"]:
        fails.append(f"{cap['id']}: SHA-256 of {rel} differs from manifest")

e = {(r["team"], r["player"]): r for r in early}
l = {(r["team"], r["player"]): r for r in late}
both = [k for k in e if k in l]
calc = {
    "rows_in_both_reads": len(both),
    "rows_only_in_later_read": len([k for k in l if k not in e]),
    "rows_only_in_earlier_read": len([k for k in e if k not in l]),
    "practice_status_changed": sum(1 for k in both if e[k]["practice_status"] != l[k]["practice_status"]),
    "injury_text_changed_or_filled": sum(1 for k in both if e[k]["injuries"] != l[k]["injuries"]),
    "game_status_changed_or_filled": sum(1 for k in both if e[k]["game_status"] != l[k]["game_status"]),
}
delta_rel = "captures/2026-11-19/delta-w11-r1-to-r2.json"
delta = load(delta_rel)
for k, v in calc.items():
    if delta.get(k) != v:
        fails.append(f"delta {k}: published {delta.get(k)} != recomputed {v}")

ver = load("captures/2026-11-19/verification-second-transcription.json")
raw = [ln.rstrip("\n") for ln in open(os.path.join(ROOT, late_rel), encoding="utf-8") if ln.strip()]
lines = sorted(raw[1:])
sorted_hash = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
if sorted_hash != ver["sorted_rows_sha256"]:
    fails.append("primary rows do not match the recorded second transcription (sorted-row hash)")
if ver["primary_rows_file_sha256"] != late_meta["private_sha256"]:
    fails.append("verification record points at a different primary file hash")

secret = set()
for r in early + late:
    for f in ("player", "injuries"):  # vocabulary (practice and game status) is pinned in the meta, not player data
        v = r.get(f, "").strip()
        if len(v) >= 4 and v not in ("Out", "Questionable", "Doubtful"):
            secret.add(v)
for path in glob.glob(os.path.join(ROOT, "captures", "2026-11-19", "*.json")):
    text = open(path, encoding="utf-8").read()
    leaks = sorted(v for v in secret if v in text)
    if leaks:
        fails.append(f"{os.path.relpath(path, ROOT)} contains row-level text: {leaks[:3]}")

print("recomputed:", calc)
if fails:
    print("FAILURES:", len(fails))
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("OK: delta recomputes from the private reads, hashes match the manifest, second transcription matches row for row, no row-level text in public capture files")
