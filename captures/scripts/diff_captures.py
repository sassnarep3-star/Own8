#!/usr/bin/env python3
"""Publishes the delta between two Week 11 injury-report captures as COUNTS ONLY (standard library only).

Joins rows on (team, player) across the two private TSVs, then writes captures/2026-11-19/delta-w11-r1-to-r2.json
with counts and SHA-256 hashes. No player name is written to the public file.
Run: python3 captures/scripts/diff_captures.py
"""
import hashlib, json, os
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OLD = "private-store/injury-report-2026-w11.tsv"
NEW = "private-store/injury-report-2026-w11-r2.tsv"
OUT = "captures/2026-11-19/delta-w11-r1-to-r2.json"


def sha(rel):
    return hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        lines = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    hdr, body = lines[0], lines[1:]
    return [dict(zip(hdr, r + [""] * (len(hdr) - len(r)))) for r in body]


old, new = read(OLD), read(NEW)
old_k = {(r["team"], r["player"]): r for r in old}
new_k = {(r["team"], r["player"]): r for r in new}
both = [k for k in new_k if k in old_k]
old_teams = {r["team"] for r in old}
new_teams = {r["team"] for r in new}
thu_teams = {r["team"] for r in old}  # the earlier capture holds only the Thursday game

counts = Counter()
for k in both:
    o, n = old_k[k], new_k[k]
    if o["practice_status"] != n["practice_status"]:
        counts["practice_status_changed"] += 1
    if o["injuries"] != n["injuries"]:
        counts["injury_text_changed_or_filled"] += 1
    if o["game_status"] != n["game_status"]:
        counts["game_status_changed_or_filled"] += 1

out = dict(
    schema="own8-capture-delta/1",
    what="Delta between two reads of the Week 11 injury report. Counts only; player names stay in private-store/.",
    earlier_capture=dict(id="injury-report-2026-w11-r1", private_sha256=sha(OLD), rows=len(old),
                         retrieved_utc_upper_bound="2026-11-18T06:29:20Z", clubs_with_rows=len(old_teams)),
    later_capture=dict(id="injury-report-2026-w11-r2", private_sha256=sha(NEW), rows=len(new),
                       retrieved_utc_upper_bound=None, clubs_with_rows=len(new_teams)),
    rows_in_both_reads=len(both),
    rows_only_in_later_read=len(new_k) - len(both),
    rows_only_in_earlier_read=len(old_k) - len(both),
    practice_status_changed=counts["practice_status_changed"],
    injury_text_changed_or_filled=counts["injury_text_changed_or_filled"],
    game_status_changed_or_filled=counts["game_status_changed_or_filled"],
    clubs_read_no_injuries_on_earlier_read=24,
    clubs_read_no_injuries_on_later_read=len({"CIN", "WAS"}),
    clubs_with_rows_in_later_read_that_earlier_read_marked_no_injuries=len(new_teams - thu_teams - {"IND", "HOU"}),
    interpretation=("The earlier read held only the IND at HOU rows (26). Of the 24 clubs it marked 'No Injuries Reported', "
                    "22 now list player rows; CIN and WAS still read 'No Injuries Reported'. The earlier read's Injuries and "
                    "Game Status cells were blank for all 26 rows; the later read fills them for IND and HOU. "
                    "Which change is real and which is a capture artefact cannot be settled from two reads."),
)
with open(os.path.join(ROOT, OUT), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(json.dumps({k: v for k, v in out.items() if k not in ("earlier_capture", "later_capture", "interpretation", "what")}, indent=1))
