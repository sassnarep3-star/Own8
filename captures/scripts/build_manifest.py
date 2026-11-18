#!/usr/bin/env python3
"""Writes captures/manifest.json: public metadata only (URLs, retrieval bounds, counts, SHA-256 of the
private row files). Row-level data is never copied into this file. Standard library only.
Run: python3 captures/scripts/build_manifest.py   then   python3 captures/scripts/check_captures.py
"""
import hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
META_FILES = [
    "captures/2026-11-18/injury-report-w11.meta.json",
    "captures/2026-11-18/gamebook-2026-w10-ne-at-det.meta.json",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


captures = []
for meta_rel in META_FILES:
    meta = load(meta_rel)
    rows_path = os.path.join(ROOT, meta["rows_file"])
    lines = [ln for ln in open(rows_path, encoding="utf-8").read().splitlines()[1:] if ln]
    team_col = meta["required_columns"].index("team")
    cap = {
        "id": meta["capture_id"],
        "source_url": meta["source_url"],
        "retrieval": meta["retrieval"],
        "retrieved_utc_upper_bound": meta["retrieved_utc_upper_bound"],
        "chunks_read": meta["chunks_read"],
        "chunks_total": meta["chunks_total"],
        "rows": meta["rows"],
        "clubs_with_rows": len({ln.split("\t")[team_col] for ln in lines}),
        "meta_file": meta_rel,
        "meta_sha256": sha256(os.path.join(ROOT, meta_rel)),
        "private_file": meta["rows_file"],
        "private_sha256": sha256(rows_path),
        "private_bytes": os.path.getsize(rows_path),
        "public": False,
        "public_fields": "counts, hashes and URLs only; row-level data stays in private-store/",
    }
    if "page_title_as_read" in meta:
        cap["page_title_as_read"] = meta["page_title_as_read"]
    if "games" in meta:
        cap["games"] = len(meta["games"])
        cap["clubs_no_injuries_reported"] = len(meta["teams_listed_no_injuries"])
    if "scope_note" in meta:
        cap["scope_note"] = meta["scope_note"]
    captures.append(cap)

probes = load("captures/2026-11-18/probes.json")
out = {
    "schema": "own8-capture-manifest/2",
    "note": "Each hash covers the file as written by the session. fetch_page returns text, not bytes, so a hash proves the file is unchanged since capture, not that it equals nfl.com's bytes.",
    "captures": captures,
    "probes": probes["probes"],
    "news_reported_roster_moves": probes["news_reported_roster_moves"],
    "probes_retrieved_utc_upper_bound": probes["retrieved_utc_upper_bound"],
}
with open(os.path.join(ROOT, "captures", "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote captures/manifest.json:", [c["id"] for c in captures])
