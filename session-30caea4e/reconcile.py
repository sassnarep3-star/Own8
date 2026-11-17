"""Reconcile the repo results feed + official Week 10 Sunday finals against the official nfl.com standings.

Inputs (read-only): ../ledger/data/results-feed.json, ./official-w10-finals.json
Output: ./reconcile.json  (prints a summary; exit 1 on any mismatch)
A team's record is reproduced as sum over games. Exact match of W, L, T, PF, PA required.
Team codes follow the official page; the feed uses the same codes (AZ, LA, ...).
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
feed = json.loads((ROOT / "ledger/data/results-feed.json").read_text())["rows"]
off = json.loads((HERE / "official-w10-finals.json").read_text())

# Team-code aliases: the repo feed writes the Rams as LAR; the official standings page writes LA.
# Verified: nfl.com standings row "Los Angeles Rams" = LA; feed key 2026-W01-SF-LAR is the same club.
ALIAS = {"LAR": "LA"}
def norm(c): return ALIAS.get(c, c)

games = []
for r in feed:
    games.append({"src": "ledger/data/results-feed.json", "key": r["key"], "away": norm(r["away"]), "home": norm(r["home"]),
                  "away_score": r["away_score"], "home_score": r["home_score"], "game_url": r["game_url"]})
feed_keys = {g["key"] for g in games}
added = []
for f in off["finals"]:
    key = f"2026-W{f['week']:02d}-{f['away']}-{f['home']}"
    if key in feed_keys:
        continue  # already in the feed (Thursday WAS-NYG); checked below for equality
    games.append({"src": "official-w10-finals.json", "key": key, "away": norm(f["away"]), "home": norm(f["home"]),
                  "away_score": f["away_score"], "home_score": f["home_score"], "game_url": f["game_url"]})
    added.append(key)

# Check the already-in-feed Thursday game against the official capture
feed_by_key = {r["key"]: r for r in feed}
thu_checks = []
for f in off["finals"]:
    key = f"2026-W{f['week']:02d}-{f['away']}-{f['home']}"
    if key in feed_by_key:
        r = feed_by_key[key]
        thu_checks.append({"key": key, "feed": [r["away_score"], r["home_score"]],
                           "official": [f["away_score"], f["home_score"]],
                           "equal": (r["away_score"], r["home_score"]) == (f["away_score"], f["home_score"])})

rec = {}
for team in off["official_standings"]["rows"]:
    rec[team] = dict(W=0, L=0, T=0, PF=0, PA=0, games=0)
for g in games:
    a, h = g["away"], g["home"]
    for t in (a, h):
        if t not in rec:
            raise SystemExit(f"unknown team code {t} in {g['key']}")
    rec[a]["PF"] += g["away_score"]; rec[a]["PA"] += g["home_score"]
    rec[h]["PF"] += g["home_score"]; rec[h]["PA"] += g["away_score"]
    rec[a]["games"] += 1; rec[h]["games"] += 1
    if g["away_score"] > g["home_score"]:
        rec[a]["W"] += 1; rec[h]["L"] += 1
    elif g["away_score"] < g["home_score"]:
        rec[h]["W"] += 1; rec[a]["L"] += 1
    else:
        rec[a]["T"] += 1; rec[h]["T"] += 1

cells, mismatches, team_rows = 0, [], []
for team, (w, l, t, pf, pa) in off["official_standings"]["rows"].items():
    mine = rec[team]
    got = [mine["W"], mine["L"], mine["T"], mine["PF"], mine["PA"]]
    exp = [w, l, t, pf, pa]
    row_ok = True
    for name, gv, ev in zip(["W", "L", "T", "PF", "PA"], got, exp):
        cells += 1
        if gv != ev:
            row_ok = False
            mismatches.append({"team": team, "field": name, "computed": gv, "official": ev})
    team_rows.append({"team": team, "computed": got, "official": exp, "games_in_repo_plus_official": mine["games"], "match": row_ok})

summary = {
    "generated_utc": "2026-11-17",
    "inputs": {"results_feed_games": len(feed), "official_sunday_finals_added": added,
               "official_standings_source": off["official_standings"]["source"]},
    "games_used": len(games),
    "thursday_already_in_feed_check": thu_checks,
    "cells_checked": cells,
    "cells_mismatched": len(mismatches),
    "mismatches": mismatches,
    "teams": team_rows,
    "not_final_on_read": off["not_final_on_read"],
    "caveat": "Reconciles the record as printed on the official standings page read on 2026-11-17. The page shows the pre-Monday state for LAC and BAL (0-8 and 4-5), so the Monday game is excluded. Matching standings do not prove each game's score independently of the scores page, because both come from nfl.com.",
}
(HERE / "reconcile.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"games used={len(games)} added={len(added)} cells={cells} mismatched={len(mismatches)} thu_equal={all(c['equal'] for c in thu_checks)}")
for m in mismatches: print("MISMATCH", m)
sys.exit(1 if mismatches or not all(c['equal'] for c in thu_checks) else 0)
