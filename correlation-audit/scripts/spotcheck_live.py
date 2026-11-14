#!/usr/bin/env python3
"""Live spot-check of the committed raw captures against the official pages (session 5b52ac15).

The OBSERVED values below were copied from the text returned by fetch_page on 2026-11-14:
  https://www.nfl.com/scores/2026/week-9            (chunk 0 + chunk 1; 15 games; team final scores)
  https://nextgenstats.nfl.com/stats/passing/2026/REG/8  (chunk 0; 27 passer rows)
Nothing here is inferred: a cell that was not observed is absent and reported as not compared.
Output: correlation-audit/data/live-spotcheck-2026-11-14.json
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GAMES = os.path.join(ROOT, "origination", "data", "games-2026-w1-w9.json")
NGS = os.path.join(ROOT, "origination", "data", "raw-ngs-passing-transcription.txt")
OUT = os.path.join(ROOT, "correlation-audit", "data", "live-spotcheck-2026-11-14.json")
SCORES_URL = "https://www.nfl.com/scores/2026/week-9"
NGS_URL = "https://nextgenstats.nfl.com/stats/passing/2026/REG/8"

# (away_abbr, away_score, home_abbr, home_score) as displayed on nfl.com scores/2026/week-9
OBSERVED_W9 = [
    ("JAX", 33, "BAL", 10), ("CIN", 34, "ATL", 17), ("DEN", 26, "CAR", 21), ("DAL", 27, "IND", 23),
    ("NYJ", 12, "KC", 35), ("DET", 19, "MIA", 9), ("CLE", 22, "NO", 23), ("NYG", 19, "PHI", 11),
    ("LAR", 20, "WAS", 13),
    ("HOU", 44, "LAC", 22), ("LV", 17, "SF", 38), ("GB", 45, "NE", 27), ("AZ", 3, "SEA", 17),
    ("TB", 24, "CHI", 27), ("BUF", 23, "MIN", 6),
]
# (player, team, ATT, YDS, TD, INT) as displayed in the NGS passing table, URL .../REG/8
OBSERVED_NGS_W8 = [
    ("Joe Burrow", "CIN", 48, 462, 5, 3), ("Deshaun Watson", "CLE", 39, 324, 0, 0),
    ("Patrick Mahomes", "KC", 41, 321, 3, 0), ("Cam Ward", "TEN", 40, 304, 2, 0),
    ("Geno Smith", "NYJ", 32, 290, 2, 1), ("Josh Allen", "BUF", 34, 289, 2, 1),
    ("Jordan Love", "GB", 41, 288, 3, 1), ("Justin Herbert", "LAC", 32, 257, 0, 2),
    ("Kirk Cousins", "LV", 26, 247, 3, 0), ("Caleb Williams", "CHI", 34, 247, 1, 0),
    ("Bo Nix", "DEN", 32, 222, 2, 0), ("Jayden Daniels", "WAS", 29, 217, 1, 0),
    ("Tanner McKee", "PHI", 34, 212, 0, 1), ("Malik Willis", "MIA", 32, 211, 2, 1),
    ("Kyler Murray", "MIN", 29, 210, 2, 1), ("Bryce Young", "CAR", 41, 209, 1, 1),
    ("Drake Maye", "NE", 20, 199, 2, 0), ("Dak Prescott", "DAL", 29, 195, 1, 0),
    ("Sam Darnold", "SEA", 34, 188, 2, 1), ("Gardner Minshew", "AZ", 23, 188, 3, 0),
    ("Jared Goff", "DET", 25, 176, 1, 1), ("Aaron Rodgers", "PIT", 25, 172, 0, 1),
    ("Matthew Stafford", "LAR", 25, 157, 1, 1), ("Daniel Jones", "IND", 28, 144, 1, 2),
    ("Michael Penix Jr.", "ATL", 24, 125, 0, 4), ("Jacoby Brissett", "AZ", 23, 119, 0, 1),
    ("Joe Fagnano", "BAL", 21, 91, 0, 1),
]


def main():
    games = json.load(open(GAMES, encoding="utf-8"))["games"]
    w9 = [g for g in games if g["week"] == 9]
    by = {(g["away"], g["home"]): g for g in w9}
    rows = []
    for a, asc, h, hsc in OBSERVED_W9:
        g = by.get((a, h))
        if g is None:
            rows.append({"check": f"W9 {a} at {h}", "official_page": f"{a} {asc}, {h} {hsc}", "game_log": None, "match": False, "source": SCORES_URL})
            continue
        ok = g["away_score"] == asc and g["home_score"] == hsc
        rows.append({"check": f"W9 {a} at {h}", "official_page": f"{a} {asc}, {h} {hsc}",
                     "game_log": f"{g['away']} {g['away_score']}, {g['home']} {g['home_score']}", "match": ok, "source": SCORES_URL})
    unmatched_log = [f"{g['away']}@{g['home']}" for g in w9 if (g['away'], g['home']) not in {(a, h) for a, _, h, _ in OBSERVED_W9}]

    ngs_w8 = []
    with open(NGS, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            w, name, team, att, yds, td, it = line.rstrip("\n").split("|")
            if int(w) == 8:
                ngs_w8.append((name, team, int(att), int(yds), int(td), int(it)))
    obs = set(OBSERVED_NGS_W8)
    ngs_rows = []
    for name, team, att, yds, td, it in ngs_w8:
        ok = (name, team, att, yds, td, it) in obs
        ngs_rows.append({"check": f"NGS W8 {name} {team}", "match": ok, "source": NGS_URL})
    rows_ngs_ok = sum(r["match"] for r in ngs_rows)

    out = {
        "as_of": "2026-11-14",
        "method": "Observed values transcribed from fetch_page output; compared programmatically with committed captures.",
        "nfl_scores_week9": {"source": SCORES_URL, "observed_games": len(OBSERVED_W9), "rows": rows,
                             "matched": sum(r["match"] for r in rows), "log_games_not_observed": unmatched_log},
        "ngs_week8": {"source": NGS_URL, "observed_rows": len(OBSERVED_NGS_W8), "committed_rows": len(ngs_w8),
                      "matched": rows_ngs_ok, "rows": ngs_rows,
                      "caveat": "The rendered table carries no explicit week label; week identity rests on the URL path and on the 27/27 agreement with the W8 capture."},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"nfl.com W9: {out['nfl_scores_week9']['matched']}/{len(OBSERVED_W9)} games match; log W9 games not observed: {unmatched_log}")
    print(f"NGS W8: {rows_ngs_ok}/{len(ngs_w8)} committed rows match observed ({len(OBSERVED_NGS_W8)} observed)")
    ok = out["nfl_scores_week9"]["matched"] == len(OBSERVED_W9) and rows_ngs_ok == len(ngs_w8) == len(OBSERVED_NGS_W8)
    return 0 if ok and not unmatched_log else 1


if __name__ == "__main__":
    sys.exit(main())
