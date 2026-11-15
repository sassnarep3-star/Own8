#!/usr/bin/env python3
"""Session 08643438 — 2026-11-15 official re-verification reconciliation.

Recomputes W-L-T / PF / PA for all 32 clubs from the committed 137-game results feed
(ledger/data/results-feed.json) plus the eight Week 10 Sunday finals read live from
https://www.nfl.com/scores/2026/week-10 on 2026-11-15, and compares each cell with the
league standings transcribed from https://www.nfl.com/standings/league/2026/REG the
same day. Every mismatch is reported, never corrected by inference.

Run from the repository root:  python3 session-08643438/reconcile.py
Writes: session-08643438/verification.json
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parent.parent

FETCHED_AT = "2026-11-15T23:37Z"
SCORES_URL = "https://www.nfl.com/scores/2026/week-10"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
INJURIES_URL = "https://www.nfl.com/injuries/league/2026/reg10"

# Eight Week 10 games FINAL on the official scores page at FETCHED_AT (the live and
# upcoming games are excluded; see week10_state below). Verbatim from the page.
NEW_FINALS = [
    {"away": "NE", "home": "DET", "away_score": 10, "home_score": 35, "label": "International Game (Munich), Sunday Nov 15"},
    {"away": "KC", "home": "ATL", "away_score": 35, "home_score": 13, "label": "Sunday Nov 15"},
    {"away": "HOU", "home": "CLE", "away_score": 24, "home_score": 27, "label": "Sunday Nov 15"},
    {"away": "MIN", "home": "GB", "away_score": 30, "home_score": 10, "label": "Sunday Nov 15"},
    {"away": "MIA", "home": "IND", "away_score": 22, "home_score": 24, "label": "Sunday Nov 15"},
    {"away": "CAR", "home": "NO", "away_score": 20, "home_score": 17, "label": "Sunday Nov 15"},
    {"away": "BUF", "home": "NYJ", "away_score": 31, "home_score": 12, "label": "Sunday Nov 15"},
    {"away": "JAX", "home": "TEN", "away_score": 40, "home_score": 23, "label": "Sunday Nov 15"},
]

# League standings as rendered on STANDINGS_URL at FETCHED_AT (32 rows, core fields).
# Team codes use the repo's scores-page convention (LAR for the Rams; the standings page
# prints LA — the documented alias IR-c56-01, applied only here and recorded as a check).
STANDINGS_AS_READ = {
    "BUF": {"w": 8, "l": 1, "t": 0, "pf": 287, "pa": 199},
    "SF": {"w": 7, "l": 1, "t": 0, "pf": 235, "pa": 156},
    "CHI": {"w": 7, "l": 2, "t": 0, "pf": 241, "pa": 184},
    "DEN": {"w": 7, "l": 2, "t": 0, "pf": 198, "pa": 186},
    "DET": {"w": 7, "l": 2, "t": 0, "pf": 257, "pa": 199},
    "JAX": {"w": 7, "l": 2, "t": 0, "pf": 269, "pa": 144},
    "KC": {"w": 7, "l": 2, "t": 0, "pf": 237, "pa": 156},
    "MIN": {"w": 7, "l": 2, "t": 0, "pf": 176, "pa": 126},
    "CIN": {"w": 6, "l": 2, "t": 0, "pf": 240, "pa": 175},
    "PIT": {"w": 6, "l": 2, "t": 0, "pf": 180, "pa": 144},
    "NYG": {"w": 5, "l": 3, "t": 1, "pf": 203, "pa": 196},
    "CLE": {"w": 6, "l": 4, "t": 0, "pf": 188, "pa": 220},
    "GB": {"w": 6, "l": 4, "t": 0, "pf": 226, "pa": 221},
    "LAR": {"w": 5, "l": 4, "t": 0, "pf": 214, "pa": 181},
    "SEA": {"w": 5, "l": 4, "t": 0, "pf": 202, "pa": 162},
    "NE": {"w": 5, "l": 5, "t": 0, "pf": 221, "pa": 242},
    "BAL": {"w": 4, "l": 5, "t": 0, "pf": 189, "pa": 236},
    "CAR": {"w": 4, "l": 5, "t": 0, "pf": 219, "pa": 236},
    "DAL": {"w": 4, "l": 5, "t": 0, "pf": 246, "pa": 236},
    "LV": {"w": 4, "l": 5, "t": 0, "pf": 238, "pa": 268},
    "WAS": {"w": 3, "l": 5, "t": 1, "pf": 196, "pa": 223},
    "AZ": {"w": 3, "l": 6, "t": 0, "pf": 178, "pa": 255},
    "HOU": {"w": 3, "l": 6, "t": 0, "pf": 233, "pa": 219},
    "NO": {"w": 3, "l": 6, "t": 0, "pf": 202, "pa": 236},
    "TB": {"w": 3, "l": 6, "t": 0, "pf": 202, "pa": 178},
    "ATL": {"w": 3, "l": 7, "t": 0, "pf": 201, "pa": 258},
    "IND": {"w": 3, "l": 7, "t": 0, "pf": 208, "pa": 271},
    "PHI": {"w": 2, "l": 7, "t": 0, "pf": 148, "pa": 221},
    "NYJ": {"w": 2, "l": 8, "t": 0, "pf": 194, "pa": 254},
    "MIA": {"w": 1, "l": 8, "t": 0, "pf": 148, "pa": 224},
    "TEN": {"w": 1, "l": 8, "t": 0, "pf": 167, "pa": 239},
    "LAC": {"w": 0, "l": 8, "t": 0, "pf": 121, "pa": 219},
}


def main():
    feed = json.loads((R / "ledger/data/results-feed.json").read_text())
    agg = {}
    for team in STANDINGS_AS_READ:
        agg[team] = {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0}

    def play(away, home, as_, hs):
        for team, gf, ga in ((away, as_, hs), (home, hs, as_)):
            agg[team]["pf"] += gf
            agg[team]["pa"] += ga
            if gf > ga:
                agg[team]["w"] += 1
            elif gf < ga:
                agg[team]["l"] += 1
            else:
                agg[team]["t"] += 1

    for r in feed["rows"]:
        play(r["away"], r["home"], r["away_score"], r["home_score"])
    for g in NEW_FINALS:
        play(g["away"], g["home"], g["away_score"], g["home_score"])

    per_team, cells_ok, cells_total, mismatches = {}, 0, 0, []
    for team in sorted(STANDINGS_AS_READ):
        read = STANDINGS_AS_READ[team]
        comp = agg[team]
        row = {"team": team, "as_read": read, "recomputed": comp, "cells": {}}
        for f in ("w", "l", "t", "pf", "pa"):
            ok = read[f] == comp[f]
            row["cells"][f] = ok
            cells_total += 1
            cells_ok += ok
            if not ok:
                mismatches.append({"team": team, "field": f, "as_read": read[f], "recomputed": comp[f]})
        per_team[team] = row

    out = {
        "session": "08643438",
        "checked_at": FETCHED_AT,
        "sources": [
            {"url": SCORES_URL, "read": "Week 10 live/completed/upcoming split at read time (3 chunks)"},
            {"url": STANDINGS_URL, "read": "32 league standings rows, core fields (2 chunks)"},
            {"url": INJURIES_URL, "read": "Week 10 injury report shape probe (first 2 chunks)"},
        ],
        "method": ("137 committed feed rows (ledger/data/results-feed.json: Weeks 1-9 verified log + Week 10 Thursday) "
                   "plus the eight Week 10 Sunday finals transcribed above, recomputed per club, compared cell-by-cell "
                   "with the standings as read. Mismatches are reported, never corrected by inference. "
                   "Alias applied only inside this check and recorded: standings print LA, repo stores LAR."),
        "games_recomputed": len(feed["rows"]) + len(NEW_FINALS),
        "week10_state_at_read": {
            "final": ["WAS 24 @ NYG 21 (TNF, Nov 12 — already in the feed)"] +
                     ["%s %d @ %s %d" % (g["away"], g["away_score"], g["home"], g["home_score"]) for g in NEW_FINALS],
            "live_at_read": ["LAR 34 @ AZ 6 (Q4 12:15)", "SEA 21 @ LV 10 (Q4 07:00)", "SF 31 @ DAL 19 (Q3 06:59)"],
            "upcoming": ["PIT @ CIN (SNF, Nov 15 8:20 PM)", "LAC @ BAL (MNF, Nov 16 8:15 PM)"],
            "byes": ["CHI", "DEN", "PHI", "TB"],
            "note": ("Scores in the live list are as rendered at read time and are NOT results. "
                     "The W10 line set may only be graded after all 14 games settle."),
        },
        "reconciliation": {
            "cells_ok": cells_ok,
            "cells_total": cells_total,
            "mismatches": mismatches,
            "verdict": "PASS" if not mismatches and cells_total == 160 else "FAIL",
        },
        "per_team": per_team,
        "f07_shape_probe": {
            "question": "Are the 185 practice-only rows in requirements/results/injuries-w10.json a capture artifact or the real report shape?",
            "answer": "REAL REPORT SHAPE — not a capture artifact.",
            "evidence_rows": [
                {"player": "John Bates", "team": "WAS", "position": "TE", "injuries": "", "practice": "Full Participation in Practice", "game_status": ""},
                {"player": "Treylon Burks", "team": "WAS", "position": "WR", "injuries": "", "practice": "Did Not Participate In Practice", "game_status": ""},
                {"player": "Hunter Henry", "team": "NE", "position": "TE", "injuries": "", "practice": "Limited Participation in Practice", "game_status": ""},
                {"player": "Jared Goff", "team": "DET", "position": "QB", "injuries": "", "practice": "Full Participation in Practice", "game_status": ""},
            ],
            "source_url": INJURIES_URL,
            "consequence": ("The market F-07 caveat stands as worded: per-club row counts are rows on the report, "
                            "not players with a disclosed injury, and must not be read as an injury-burden ranking. "
                            "The requirements capture is faithful to the official page."),
        },
        "lions_designation_check": {
            "prior_request": ("VR-08/VR-12: Kerby Joseph, Cade Mays and D.J. Reed were captured with blank game-status "
                              "cells while an official article listed all three as Out."),
            "official_page_as_read_2026_11_15": [
                {"player": "Kerby Joseph", "team": "DET", "injuries": "Knee", "practice": "Did Not Participate In Practice", "game_status": "Out"},
                {"player": "Cade Mays", "team": "DET", "injuries": "Ankle", "practice": "Did Not Participate In Practice", "game_status": "Out"},
                {"player": "D.J. Reed", "team": "DET", "injuries": "Hip", "practice": "Did Not Participate In Practice", "game_status": "Out"},
            ],
            "source_url": INJURIES_URL,
            "conclusion": ("All three now read Out on the official page. The earlier blank cells are consistent with the "
                           "report being a daily, timestamped series (game designations land later in the week), not "
                           "necessarily a transcription error. Any backtest must snapshot the report as it was known."),
        },
    }
    path = R / "session-08643438/verification.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print("reconciliation:", out["reconciliation"]["verdict"],
          "%d/%d cells" % (cells_ok, cells_total))
    if mismatches:
        print(json.dumps(mismatches, indent=1))
    return 0 if not mismatches and cells_total == 160 else 1


if __name__ == "__main__":
    raise SystemExit(main())
