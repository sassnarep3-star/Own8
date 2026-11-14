#!/usr/bin/env python3
"""Own8 integration verifier (session 2d4025da, task I2).

Recomputes per-team W-L-T, PF, PA, NET and PCT from official game results:
  - Weeks 1-8: origination/data/games-2026-w1-w8.json (session 4bc92a5f,
    transcribed from nfl.com/scores/2026/week-N and reconciled vs standings)
  - Week 9:    integration/data/scores-2026-week9.json (this session,
    transcribed from nfl.com/scores/2026/week-9)
  - Week 10 TNF: WAS at NYG from integration/data/schedule-2026-week10.json
    (transcribed from nfl.com/schedules/2026/by-week/week-10)
and compares them cell-by-cell against integration/data/standings-2026-reg-w10.json
(transcribed from nfl.com/standings/).

Also checks:
  - PCT and NET arithmetic on every standings row
  - HOME+ROAD = W-L-T on every standings row
  - schedule-page records vs standings records (32 cross-checks)
  - injury-report structure (28 team tables, every row has an nfl.com player URL)
  - per-team Out/Doubtful/Questionable counts (pure arithmetic on transcribed rows)

Fail-closed: any mismatch is recorded; nothing is inferred or repaired.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "integration" / "data"


def load(rel):
    with open(ROOT / rel, encoding="utf-8") as fh:
        return json.load(fh)


def split_rec(s):
    w, l, t = (int(x) for x in s.split("-"))
    return w, l, t


def main():
    errors = []
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            errors.append(f"{name}: {detail}")

    base = load("origination/data/games-2026-w1-w8.json")
    w9 = load("integration/data/scores-2026-week9.json")
    w10 = load("integration/data/schedule-2026-week10.json")
    stand = load("integration/data/standings-2026-reg-w10.json")
    inj = load("integration/data/injuries-2026-week10.json")

    # --- accumulate results --------------------------------------------
    res = {}  # abbr -> [w, l, t, pf, pa]

    def add(away, home, as_, hs):
        for team, pf, pa in ((away, as_, hs), (home, hs, as_)):
            r = res.setdefault(team, [0, 0, 0, 0, 0])
            r[3] += pf
            r[4] += pa
            if pf > pa:
                r[0] += 1
            elif pf < pa:
                r[1] += 1
            else:
                r[2] += 1

    # nfl.com prints LAR in some scores renderings and LA in others (both
    # observed on official pages; prior sessions logged the same quirk).
    # Normalize to the standings-page abbreviation (LA) for reconciliation only.
    ABBR = {"LAR": "LA"}

    n_reg = 0
    for g in base["games"]:
        check(f"W1-8 game has both scores ({g['away']}@{g['home']} w{g['week']})",
              g["away_score"] is not None and g["home_score"] is not None)
        add(ABBR.get(g["away"], g["away"]), ABBR.get(g["home"], g["home"]),
            g["away_score"], g["home_score"])
        n_reg += 1
    for g in w9["games"]:
        check(f"W9 final status ({g['away']}@{g['home']})", g["status"] == "Final")
        add(g["away"], g["home"], g["away_score"], g["home_score"])
        n_reg += 1
    tnfs = [g for g in w10["games"] if g["status"] == "Final"]
    check("exactly one W10 final at capture", len(tnfs) == 1, f"found {len(tnfs)}")
    for g in tnfs:
        add(g["away"], g["home"], g["away_score"], g["home_score"])
        n_reg += 1

    check("total games reconciled = 121 + 15 + 1", n_reg == 137, f"got {n_reg}")
    check("all 32 teams appear in results", len(res) == 32, f"got {len(res)}")

    # --- compare against standings -------------------------------------
    per_field = 0
    rows_ok = 0
    for t in stand["teams"]:
        ab = t["abbr"]
        r = res.get(ab)
        if r is None:
            errors.append(f"standings team {ab} missing from game results")
            continue
        w, l, ttl, pf, pa = r
        row_ok = True
        for field, recomputed in (("W", w), ("L", l), ("T", ttl), ("PF", pf), ("PA", pa)):
            per_field += 1
            if t[field] != recomputed:
                row_ok = False
                errors.append(f"{ab}.{field}: standings={t[field]} recomputed={recomputed}")
        # arithmetic on the transcribed row itself
        per_field += 2
        if t["NET"] != t["PF"] - t["PA"]:
            row_ok = False
            errors.append(f"{ab}.NET arithmetic: {t['NET']} != {t['PF']}-{t['PA']}")
        games_played = t["W"] + t["L"] + t["T"]
        pct = round((t["W"] + 0.5 * t["T"]) / games_played, 3) if games_played else 0.0
        if abs(t["PCT"] - pct) > 0.001:
            row_ok = False
            errors.append(f"{ab}.PCT arithmetic: {t['PCT']} != {pct}")
        # HOME + ROAD = W-L-T
        per_field += 1
        hw, hl, ht = split_rec(t["HOME"])
        rw, rl, rt = split_rec(t["ROAD"])
        if (hw + rw, hl + rl, ht + rt) != (t["W"], t["L"], t["T"]):
            row_ok = False
            errors.append(f"{ab}.HOME+ROAD != W-L-T")
        if row_ok:
            rows_ok += 1

    check("standings rows fully reconciled (6 fields + 3 arithmetic each)",
          rows_ok == 32, f"{rows_ok}/32 rows ok; {len(errors)} field errors")

    # --- schedule records vs standings ---------------------------------
    sched_ok = 0
    smap = {t["abbr"]: t for t in stand["teams"]}
    for g in w10["games"]:
        for side, rec in (("away", g["away_record"]), ("home", g["home_record"])):
            ab = g[side]
            if ab not in smap:
                errors.append(f"schedule team {ab} not in standings")
                continue
            t = smap[ab]
            mine = f"{t['W']}-{t['L']}-{t['T']}"
            alt = f"{t['W']}-{t['L']}-{t['T']}" if t["T"] else f"{t['W']}-{t['L']}"
            if rec in (mine, alt):
                sched_ok += 1
            else:
                errors.append(f"{ab}: schedule page record {rec} != standings {mine}")
    check("schedule-page records match standings (28 team slots)",
          sched_ok == 28, f"{sched_ok}/28")

    # --- injury report structure ---------------------------------------
    tables = sum(len(g["teams"]) for g in inj["games"])
    rows = [r for g in inj["games"] for t in g["teams"] for r in t["rows"]]
    url_ok = all(r["url"].startswith("https://www.nfl.com/players/") for r in rows)
    check("14 games / 28 team tables", len(inj["games"]) == 14 and tables == 28,
          f"{len(inj['games'])} games, {tables} tables")
    check("every injury row carries an official player URL", url_ok,
          f"{len(rows)} rows")
    allowed = {"", "Out", "Doubtful", "Questionable"}
    bad_status = [r for r in rows if r["game_status"] not in allowed]
    check("game statuses only from the official set (or blank as printed)",
          not bad_status, f"{len(bad_status)} unexpected")

    # --- derived position-deficiency signals (arithmetic only) ---------
    signals = []
    for g in inj["games"]:
        for side in ("away", "home"):
            ab = g[side]["abbr"]
            team_tbl = next(t for t in g["teams"] if t["abbr"] == ab)
            out_pos = sorted({r["position"] for r in team_tbl["rows"] if r["game_status"] == "Out"})
            dq_pos = sorted({r["position"] for r in team_tbl["rows"] if r["game_status"] == "Doubtful"})
            q_pos = sorted({r["position"] for r in team_tbl["rows"] if r["game_status"] == "Questionable"})
            signals.append({
                "team": ab,
                "opponent": g[side == "away" and "home" or "away"],
                "game": f"{g['away']['abbr']} at {g['home']['abbr']}",
                "out_positions": out_pos,
                "doubtful_positions": dq_pos,
                "questionable_positions": q_pos,
                "out_count": sum(1 for r in team_tbl["rows"] if r["game_status"] == "Out"),
                "qb_out": any(r["position"] == "QB" and r["game_status"] == "Out" for r in team_tbl["rows"]),
                "source_url": inj["source_url"],
                "derivation": "Counts and position sets computed ONLY from transcribed game_status cells; no replacement player is named (depth-chart string order is not published on this page)."
            })
    with open(OUT / "deficiency-signals-w10.json", "w", encoding="utf-8") as fh:
        json.dump({"dataset": "own8-integration-deficiency-signals-w10",
                   "generated_by": "integration/scripts/verify_fresh.py",
                   "as_of": "2026-11-14",
                   "source_url": inj["source_url"],
                   "caveat": "Position-level OUT/DOUBTFUL/QUESTIONABLE counts only. Who replaces an out starter (2nd/3rd/4th string order) is NOT published on the official injury page and is therefore left blank — see decision-support session e00061c1 task V5 (depth-chart availability).",
                   "signals": signals}, fh, indent=1)

    out = {
        "dataset": "own8-integration-reconciliation-2026-11-14",
        "generated_by": "integration/scripts/verify_fresh.py",
        "sources": [
            "https://www.nfl.com/scores/2026/week-1 (via origination log, W1-8)",
            "https://www.nfl.com/scores/2026/week-9",
            "https://www.nfl.com/schedules/2026/by-week/week-10",
            "https://www.nfl.com/standings/",
            "https://www.nfl.com/injuries/league/2026/reg10"
        ],
        "games_reconciled": n_reg,
        "standings_rows_ok": rows_ok,
        "standings_rows_total": 32,
        "field_comparisons": per_field,
        "schedule_record_crosschecks_ok": sched_ok,
        "injury_tables": tables,
        "injury_rows": len(rows),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "checks": checks,
    }
    with open(OUT / "reconciliation-2026-11-14.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: out[k] for k in ("status", "games_reconciled", "standings_rows_ok",
                                         "field_comparisons", "schedule_record_crosschecks_ok",
                                         "injury_tables", "injury_rows")}, indent=1))
    if errors:
        print("ERRORS:", *errors[:20], sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
