#!/usr/bin/env python3
"""O1 — Build the official 2026 Weeks 1-8 game log and reconcile it against the official standings.

Inputs (verbatim transcriptions of official nfl.com pages, see headers in each file):
  data/raw-scores-transcription.txt     https://www.nfl.com/scores/2026/week-N  (N = 1..8)
  data/raw-standings-transcription.txt  https://www.nfl.com/standings/league/2026/REG
  data/raw-division-groups.txt          https://www.nfl.com/standings/division/2026/REG

Outputs:
  data/games-2026-w1-w8.json            one row per game, each with its official source links
  out/standings-reconciliation.json     per-team, per-column comparison (official vs recomputed from game log)
  out/o1-checks.json                    every automated check with pass/fail + irregularities

Fail-closed rule: a game row is marked verified only if ALL of its checks pass AND both teams reconcile
on every standings column. Any failing value would be blanked and flagged (never guessed).
"""
import calendar
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DATA, SLUG_TO_ABBR, ABBR_TO_SLUG, SCORES_URL, GAME_URL, STANDINGS_URL, DIVISION_URL,
                    TEAM_URL, read_rows, dump_json, rec, pct)

MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def nickname(abbr):
    return ABBR_TO_SLUG[abbr].split("-")[-1]


def parse_date(label):
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2})(st|nd|rd|th)", label)
    if not m:
        return None
    return dt.date(2026, MONTHS[m.group(1)], int(m.group(2)))


def main():
    checks, irregular = [], []

    def check(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        return ok

    # ---------- parse scores ----------
    games, byes = [], []
    for r in read_rows(os.path.join(DATA, "raw-scores-transcription.txt")):
        if r[0] == "BYE":
            byes.append({"week": int(r[1]), "team": r[2], "record_shown": r[3]})
            continue
        week, label, away, as_, home, hs, win_ind, slug = r
        g = {"week": int(week), "heading": label, "away": away, "home": home,
             "away_score": None if as_ == "HIDDEN" else int(as_),
             "home_score": None if hs == "HIDDEN" else int(hs),
             "winner_indicator": win_ind, "slug": slug}
        games.append(g)

    teams = set(SLUG_TO_ABBR.values())
    # ---------- per-game checks ----------
    for g in games:
        gid = f"W{g['week']} {g['away']}@{g['home']}"
        g["checks"] = []

        def gc(name, ok, detail=""):
            g["checks"].append({"check": name, "pass": bool(ok), "detail": detail})
            return ok
        gc("teams are valid nfl.com abbreviations", g["away"] in teams and g["home"] in teams)
        gc("scores present (not hidden)", g["away_score"] is not None and g["home_score"] is not None)
        exp_slug = f"{nickname(g['away'])}-at-{nickname(g['home'])}-2026-reg-{g['week']}"
        gc("game URL slug matches teams + week", g["slug"] == exp_slug, f"expected {exp_slug}")
        if g["away_score"] is not None:
            if g["away_score"] > g["home_score"]:
                exp_w = g["away"]
            elif g["home_score"] > g["away_score"]:
                exp_w = g["home"]
            else:
                exp_w = "NONE"
            gc("winner indicator agrees with scores", g["winner_indicator"] == exp_w,
               f"indicator={g['winner_indicator']} expected={exp_w}")
        d = parse_date(g["heading"])
        g["date"] = d.isoformat() if d else None
        g["weekday_from_date"] = WEEKDAYS[d.weekday()] if d else None
        named = [w for w in WEEKDAYS if w in g["heading"]]
        if named and d and named[0] != WEEKDAYS[d.weekday()]:
            irregular.append({"id": "O1-IR-date-label", "game": gid,
                              "detail": f"nfl.com heading '{g['heading']}' names {named[0]}, but {d.isoformat()} is a "
                                        f"{WEEKDAYS[d.weekday()]}. Recorded verbatim; date = heading month/day + season year 2026.",
                              "source": SCORES_URL.format(w=g['week'])})
        g["international"] = "International Game" in g["heading"]
        g["source_url"] = SCORES_URL.format(w=g["week"])
        g["game_url"] = GAME_URL.format(slug=g["slug"])
        if g["away_score"] is not None:
            g["home_margin"] = g["home_score"] - g["away_score"]
            g["total"] = g["home_score"] + g["away_score"]

    # ---------- weekly completeness ----------
    weeks = sorted({g["week"] for g in games})
    for w in weeks:
        wg = [g for g in games if g["week"] == w]
        wb = [b for b in byes if b["week"] == w]
        seen = [g["away"] for g in wg] + [g["home"] for g in wg] + [b["team"] for b in wb]
        check(f"W{w}: every one of 32 teams appears exactly once (games + byes)",
              len(seen) == 32 and set(seen) == teams, f"{len(wg)} games, {len(wb)} byes")

    # ---------- standings ----------
    st = {}
    for r in read_rows(os.path.join(DATA, "raw-standings-transcription.txt")):
        slug = r[0]
        a = SLUG_TO_ABBR[slug]
        st[a] = {"slug": slug, "W": int(r[1]), "L": int(r[2]), "T": int(r[3]), "PCT": r[4], "PF": int(r[5]),
                 "PA": int(r[6]), "NET": int(r[7]), "HOME": rec(r[8]), "ROAD": rec(r[9]), "DIV": rec(r[10]),
                 "DIV%": r[11], "CONF": rec(r[12]), "CONF%": r[13], "col14": rec(r[14]), "STRK": r[15],
                 "col16": rec(r[16])}
    check("standings: 32 distinct teams transcribed", len(st) == 32 and set(st) == teams)

    conf, div = {}, {}
    for r in read_rows(os.path.join(DATA, "raw-division-groups.txt")):
        for slug in r[2].split(","):
            a = SLUG_TO_ABBR[slug]
            conf[a] = r[0]
            div[a] = f"{r[0]}-{r[1]}"
    check("division groups: 8 groups x 4 = 32 teams", len(div) == 32 and len(set(div.values())) == 8)

    # bye-box records must equal current standings W-L-T (they are current records)
    for b in byes:
        s = st[b["team"]]
        check(f"bye box record W{b['week']} {b['team']} equals standings W-L-T",
              rec(b["record_shown"]) == (s["W"], s["L"], s["T"]), f"bye box {b['record_shown']}")

    # ---------- recompute from game log ----------
    def blank():
        return {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "HOME": [0, 0, 0], "ROAD": [0, 0, 0], "DIV": [0, 0, 0],
                "CONF": [0, 0, 0], "NONCONF": [0, 0, 0], "seq": []}
    calc = {t: blank() for t in teams}
    for g in sorted(games, key=lambda x: (x["week"], x["date"] or "")):
        if g["away_score"] is None:
            continue
        for side, opp, pf, pa, loc in ((g["away"], g["home"], g["away_score"], g["home_score"], "ROAD"),
                                        (g["home"], g["away"], g["home_score"], g["away_score"], "HOME")):
            c = calc[side]
            res = 0 if pf > pa else (1 if pf < pa else 2)  # index into W,L,T
            c[["W", "L", "T"][res]] += 1
            c["PF"] += pf
            c["PA"] += pa
            c[loc][res] += 1
            if div[side] == div[opp]:
                c["DIV"][res] += 1
            if conf[side] == conf[opp]:
                c["CONF"][res] += 1
            else:
                c["NONCONF"][res] += 1
            c["seq"].append("WLT"[res])

    def streak(seq):
        if not seq:
            return ""
        last, n = seq[-1], 0
        for x in reversed(seq):
            if x != last:
                break
            n += 1
        return f"{n}{last}"

    recon, team_ok = [], {}
    for t in sorted(teams):
        s, c = st[t], calc[t]
        last5 = c["seq"][-5:]
        l5 = (last5.count("W"), last5.count("L"), last5.count("T"))
        rows = [
            ("W", s["W"], c["W"]), ("L", s["L"], c["L"]), ("T", s["T"], c["T"]),
            ("PCT", s["PCT"], f"{pct(c['W'], c['L'], c['T']):.3f}"),
            ("PF", s["PF"], c["PF"]), ("PA", s["PA"], c["PA"]), ("NET", s["NET"], c["PF"] - c["PA"]),
            ("HOME", "-".join(map(str, s["HOME"])), "-".join(map(str, c["HOME"]))),
            ("ROAD", "-".join(map(str, s["ROAD"])), "-".join(map(str, c["ROAD"]))),
            ("DIV", "-".join(map(str, s["DIV"])), "-".join(map(str, c["DIV"]))),
            ("DIV%", s["DIV%"], f"{pct(*c['DIV']):.3f}"),
            ("CONF", "-".join(map(str, s["CONF"])), "-".join(map(str, c["CONF"]))),
            ("CONF%", s["CONF%"], f"{pct(*c['CONF']):.3f}"),
            ("STRK", s["STRK"], streak(c["seq"])),
            ("col14 (hypothesis: non-conference record)", "-".join(map(str, s["col14"])), "-".join(map(str, c["NONCONF"]))),
            ("col16 (hypothesis: last-5 record)", "-".join(map(str, s["col16"])), "-".join(map(str, l5))),
        ]
        cells = [{"column": k, "official": str(o), "recomputed": str(v), "match": str(o) == str(v)} for k, o, v in rows]
        ok = all(x["match"] for x in cells)
        team_ok[t] = ok
        recon.append({"team": t, "team_url": TEAM_URL.format(slug=ABBR_TO_SLUG[t]), "games_played": len(c["seq"]),
                      "all_match": ok, "cells": cells, "source_url": STANDINGS_URL})
    n_cells = sum(len(r["cells"]) for r in recon)
    n_match = sum(x["match"] for r in recon for x in r["cells"])
    check("standings reconciliation: every cell for all 32 teams matches the game log",
          n_cells == n_match, f"{n_match}/{n_cells} cells match")
    hyp14 = all(x["match"] for r in recon for x in r["cells"] if x["column"].startswith("col14"))
    hyp16 = all(x["match"] for r in recon for x in r["cells"] if x["column"].startswith("col16"))
    check("unlabeled col14 behaves as non-conference record for all 32 teams", hyp14)
    check("unlabeled col16 behaves as last-5 record for all 32 teams", hyp16)

    # ---------- finalize rows (fail-closed) ----------
    out_games = []
    for g in sorted(games, key=lambda x: (x["week"], x["date"] or "", x["away"])):
        row_ok = all(c["pass"] for c in g["checks"]) and team_ok[g["away"]] and team_ok[g["home"]]
        row = {k: g.get(k) for k in ("week", "date", "heading", "international", "away", "home", "away_score",
                                     "home_score", "home_margin", "total", "winner_indicator", "game_url",
                                     "source_url")}
        row["verified"] = row_ok
        row["verification"] = ("transcribed from source_url; winner indicator, URL slug and weekly completeness "
                               "checks pass; both teams reconcile on all 16 standings columns at " + STANDINGS_URL) \
            if row_ok else "UNVERIFIED — see checks"
        if not row_ok:
            row["away_score"] = row["home_score"] = row["home_margin"] = row["total"] = None
            irregular.append({"id": "O1-IR-row", "game": f"W{g['week']} {g['away']}@{g['home']}",
                              "detail": "row failed a check; scores blanked", "source": g["source_url"]})
        row["checks"] = g["checks"]
        out_games.append(row)

    dump_json({"dataset": "games-2026-w1-w8", "captured_by": "session 4bc92a5f", "captured_at_utc": "2026-11-04",
               "sources": [SCORES_URL.format(w=w) for w in weeks] + [STANDINGS_URL, DIVISION_URL],
               "notes": ["home/away exactly as nfl.com lists them ('AWAY at HOME' in the game URL); designated home team "
                         "for international games — standings HOME/ROAD reconcile under that convention.",
                         "date = month/day from the rendered section heading + season year 2026.",
                         "no market (betting) data in this file."],
               "byes": byes, "games": out_games}, "games-2026-w1-w8.json", base=DATA)
    dump_json({"source_url": STANDINGS_URL, "division_source_url": DIVISION_URL, "teams": recon,
               "cells_total": n_cells, "cells_matching": n_match}, "standings-reconciliation.json")
    summary = {"games": len(out_games), "verified_games": sum(r["verified"] for r in out_games),
               "checks_total": len(checks) + sum(len(g["checks"]) for g in games),
               "checks_failed": [c for c in checks if not c["pass"]] +
                                [dict(c, game=f"W{g['week']} {g['away']}@{g['home']}") for g in games for c in g["checks"] if not c["pass"]],
               "standings_cells": f"{n_match}/{n_cells}", "irregularities": irregular, "league_checks": checks}
    dump_json(summary, "o1-checks.json")
    print(f"games={summary['games']} verified={summary['verified_games']} checks={summary['checks_total']} "
          f"failed={len(summary['checks_failed'])} standings_cells={n_match}/{n_cells} irregularities={len(irregular)}")
    for c in summary["checks_failed"][:40]:
        print("FAIL:", c)
    for r in recon:
        for x in r["cells"]:
            if not x["match"]:
                print("MISMATCH", r["team"], x)
    return 0 if not summary["checks_failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
