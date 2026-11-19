#!/usr/bin/env python3
"""Converts the pipe-delimited transcription of the Week 11 injury report (all 7 chunks read on 2026-11-19)
into the TSV held in private-store/. Standard library only. Run from the repo root:
  python3 captures/2026-11-19/build_r2_tsv.py
"""
import collections, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PR = {"FP": "Full Participation in Practice", "LP": "Limited Participation in Practice", "DNP": "Did Not Participate In Practice"}
rows, game = [], None
with open(os.path.join(ROOT, "captures/2026-11-19/transcription-w11-r2.txt"), encoding="utf-8") as f:
    for ln in f:
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#NO INJURIES"):
            continue
        if ln.startswith("#GAME "):
            game = ln[6:]
            continue
        team, player, pos, inj, pr, gs = ln.split("|")
        rows.append([game, team, player, pos, inj, PR[pr], gs])
hdr = ["section_game", "team", "player", "position", "injuries", "practice_status", "game_status"]
with open(os.path.join(ROOT, "private-store/injury-report-2026-w11-r2.tsv"), "w", encoding="utf-8") as f:
    f.write("\t".join(hdr) + "\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
print("rows", len(rows), "clubs", len({r[1] for r in rows}), collections.Counter(r[6] for r in rows))
