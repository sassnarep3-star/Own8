#!/usr/bin/env python3
"""Drift alarm for official-capture files (standard library only).

For every capture listed in captures/manifest.json:
  * the private row file exists; its SHA-256 and byte count match the manifest (immutability);
  * the metadata file's SHA-256 matches the manifest;
  * the header equals the pinned column list (schema drift);
  * the row count equals the pinned count (row-count drift);
  * unit/status vocabularies match the pinned sets (vocabulary drift);
  * no required cell is blank;
  * injury-report captures only: every row's team is in a listed game, each listed game matches the
    stored schedule capture (site/data/week11-schedule.json), and each club has rows or the
    'No Injuries Reported' mark, never both.
Exit 1 with a message on any failure. Run: python3 captures/scripts/check_captures.py
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
fails = []


def fail(msg):
    fails.append(msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


manifest_path = os.path.join(ROOT, "captures", "manifest.json")
if not os.path.exists(manifest_path):
    print("FAILURE: captures/manifest.json missing; run captures/scripts/build_manifest.py")
    sys.exit(1)
manifest = load("captures/manifest.json")

for cap in manifest["captures"]:
    meta_rel = cap["meta_file"]
    meta = load(meta_rel)
    rows_rel = meta["rows_file"]
    rows_path = os.path.join(ROOT, rows_rel)
    if not os.path.exists(rows_path):
        fail(f"{cap['id']}: private row file missing: {rows_rel}")
        continue
    if sha256(rows_path) != cap["private_sha256"]:
        fail(f"{cap['id']}: SHA-256 of {rows_rel} differs from manifest (file changed after capture)")
    if os.path.getsize(rows_path) != cap["private_bytes"]:
        fail(f"{cap['id']}: byte count of {rows_rel} differs from manifest")
    if sha256(os.path.join(ROOT, meta_rel)) != cap["meta_sha256"]:
        fail(f"{cap['id']}: SHA-256 of {meta_rel} differs from manifest")

    with open(rows_path, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    header = lines[0].split("\t")
    if header != meta["required_columns"]:
        fail(f"{cap['id']}: header differs from pinned schema (schema drift): {header}")
    body = [ln.split("\t") for ln in lines[1:]]
    if any(len(r) != len(header) for r in body):
        fail(f"{cap['id']}: a row has the wrong number of tab-separated fields")
    if len(body) != meta["rows"]:
        fail(f"{cap['id']}: row count {len(body)} != pinned {meta['rows']} (row-count drift)")

    recs = [dict(zip(header, r)) for r in body if len(r) == len(header)]
    optional = {"injuries", "game_status"}  # the only columns that may legitimately be blank
    for rec in recs:
        for c in header:
            if c in optional:
                continue
            if not rec.get(c, "").strip():
                fail(f"{cap['id']}: blank required cell '{c}' for {rec.get('player')!r}")
        if "allowed_units" in meta and rec["unit"] not in meta["allowed_units"]:
            fail(f"{cap['id']}: unknown unit {rec['unit']!r}")
        if "allowed_practice_status" in meta:
            if rec["practice_status"] not in meta["allowed_practice_status"]:
                fail(f"{cap['id']}: unknown practice status {rec['practice_status']!r} ({rec['player']})")
            if rec["game_status"] not in meta["allowed_game_status"]:
                fail(f"{cap['id']}: unknown game status {rec['game_status']!r} ({rec['player']})")

    if "games" in meta:
        games = {(g["away"], g["home"]) for g in meta["games"]}
        game_teams = {t for g in meta["games"] for t in (g["away"], g["home"])}
        no_inj = set(meta["teams_listed_no_injuries"])
        row_teams = {rec["team"] for rec in recs}
        for rec in recs:
            if rec["team"] not in game_teams:
                fail(f"{cap['id']}: team {rec['team']} is not in any listed game")
        for t in game_teams:
            if t in row_teams and t in no_inj:
                fail(f"{cap['id']}: {t} has rows and is also marked 'No Injuries Reported'")
            if t not in row_teams and t not in no_inj:
                fail(f"{cap['id']}: {t} has no rows and no 'No Injuries Reported' mark")
        sched = load("site/data/week11-schedule.json")
        sched_pairs = {(g["away"], g["home"]) for g in sched["games"]}
        if sched_pairs != games:
            fail(f"{cap['id']}: game pairs differ from stored schedule capture: "
                 f"only in report {sorted(games - sched_pairs)}, only in schedule {sorted(sched_pairs - games)}")
        sched_teams = {t for p in sched_pairs for t in p}
        if len(sched_teams) != 26 or len(game_teams) != 26:
            fail(f"{cap['id']}: expected 26 clubs in 13 games, found {len(game_teams)} in report")

print(f"captures checked: {len(manifest['captures'])}; probes: {len(manifest.get('probes', []))}")
if fails:
    print("FAILURES:", len(fails))
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("OK: hashes match, schemas pinned, row counts match, injury games match the stored schedule capture")
