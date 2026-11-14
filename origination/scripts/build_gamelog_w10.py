#!/usr/bin/env python3
"""W2 — Extend the official 2026 game log to Weeks 1-9 and reconcile it against the official standings
captured 2026-11-14 (which include the completed Week 10 Thursday game for WAS/NYG).

Inputs (verbatim transcriptions of official nfl.com pages, session e8155046, 2026-11-14):
  data/games-2026-w1-w8.json                    inherited verified log (session 4bc92a5f) — read, never rewritten
  data/raw-scores-w9-transcription.txt          https://www.nfl.com/scores/2026/week-9
  data/raw-schedule-w10-transcription.txt       https://www.nfl.com/schedules/2026/by-week/week-10 (slate + bye checks)
  data/raw-standings-2026-11-14.txt             https://www.nfl.com/standings/league/2026/REG
  data/raw-w10-postcutoff-transcription.txt     https://www.nfl.com/scores/2026/week-10 (WAS 24 NYG 21) — recon only
  data/raw-division-groups.txt                  inherited division grouping (structural, unchanged mid-season)
  data/raw-schedule-w9-transcription.txt        inherited W9 slate — independent cross-check of the W9 pairs/slugs

Outputs:
  data/games-2026-w1-w9.json                    one row per W1-W9 game, each with official source links
  results/standings-reconciliation-2026-11-14.json   per-team, per-column (official vs recomputed)
  results/w2-checks.json                        every automated check with pass/fail + irregularities

Fail-closed rules (identical spirit to O1): a game row is verified only if ALL of its checks pass AND both
teams reconcile on every standings column; any failing value is blanked and flagged, never guessed.
Standings reconciliation target = W1-W9 log + the single post-cutoff Thursday game (recorded in the
standings file header and raw-w10-postcutoff-transcription.txt); every other team is W1-W9 only.
"""
import calendar
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DATA, OUT, SLUG_TO_ABBR, ABBR_TO_SLUG, SCORES_URL, GAME_URL, STANDINGS_URL, DIVISION_URL,
                    TEAM_URL, read_rows, dump_json, rec, pct)  # noqa: E402

MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

STANDINGS_URL_1114 = STANDINGS_URL  # same URL, captured 2026-11-14 (file name records the date)
SCHEDULE_W10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
SCORES_W10_URL = "https://www.nfl.com/scores/2026/week-10"
SCORES_W9_URL = SCORES_URL.format(w=9)


def nickname(abbr):
    return ABBR_TO_SLUG[abbr].split("-")[-1]


def parse_date(label):
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2})(st|nd|rd|th)", label)
    if not m:
        return None
    return dt.date(2026, MONTHS[m.group(1)], int(m.group(2)))


def parse_scores_rows(path, week_expected):
    """Parse BYE + game rows from a scores transcription (same schema as O1)."""
    games, byes = [], []
    for r in read_rows(path):
        if r[0] == "BYE":
            byes.append({"week": int(r[1]), "team": r[2], "record_shown": r[3]})
            continue
        week, label, away, as_, home, hs, win_ind, slug = r
        g = {"week": int(week), "heading": label, "away": away, "home": home,
             "away_score": None if as_ == "HIDDEN" else int(as_),
             "home_score": None if hs == "HIDDEN" else int(hs),
             "winner_indicator": win_ind, "slug": slug}
        assert g["week"] == week_expected, g
        games.append(g)
    return games, byes


def run_game_checks(g, teams, irregular):
    """Per-game checks identical to O1 (fail-closed)."""
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
        irregular.append({"id": "W2-IR-date-label", "game": gid,
                          "detail": f"nfl.com heading '{g['heading']}' names {named[0]}, but {d.isoformat()} is a "
                                    f"{WEEKDAYS[d.weekday()]}. Recorded verbatim; date = heading month/day + season year 2026.",
                          "source": SCORES_W9_URL})
    g["international"] = "International Game" in g["heading"]
    g["source_url"] = SCORES_W9_URL
    g["game_url"] = GAME_URL.format(slug=g["slug"])
    if g["away_score"] is not None:
        g["home_margin"] = g["home_score"] - g["away_score"]
        g["total"] = g["home_score"] + g["away_score"]


def main():
    checks, irregular = [], []

    def check(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        return ok

    teams = set(SLUG_TO_ABBR.values())

    # ---------- inherited W1-W8 log (immutable) ----------
    with open(os.path.join(DATA, "games-2026-w1-w8.json"), encoding="utf-8") as f:
        inherited = json.load(f)
    base_games = inherited["games"]
    check("inherited W1-W8 log: 121 games, all verified", len(base_games) == 121 and all(g["verified"] for g in base_games),
          f"{len(base_games)} games")
    base_byes = inherited["byes"]

    # ---------- W9 scores ----------
    w9_games, w9_byes = parse_scores_rows(os.path.join(DATA, "raw-scores-w9-transcription.txt"), 9)
    check("W9: 15 games transcribed", len(w9_games) == 15, f"{len(w9_games)} games")
    check("W9: 2 bye boxes transcribed (PIT, TEN)", len(w9_byes) == 2 and {b['team'] for b in w9_byes} == {'PIT', 'TEN'},
          ",".join(b["team"] for b in w9_byes))
    for g in w9_games:
        run_game_checks(g, teams, irregular)

    # independent cross-check: W9 slate vs the Week 9 schedule transcription captured 2026-11-04 (session 4bc92a5f)
    sched_pairs = set()
    with open(os.path.join(DATA, "raw-schedule-w9-transcription.txt"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip() or line.startswith("BYE"):
                continue
            h, away, home, day, tm, net, slug = line.rstrip("\n").split("|")
            sched_pairs.add((away, home, slug))
    score_pairs = {(g["away"], g["home"], g["slug"]) for g in w9_games}
    check("W9 slate matches the independently captured W9 schedule page (pairs + slugs, 15/15)",
          sched_pairs == score_pairs, f"only_in_scores={sorted(score_pairs - sched_pairs)} only_in_schedule={sorted(sched_pairs - score_pairs)}")

    # ---------- weekly completeness for the combined log ----------
    all_games = [dict(g) for g in base_games] + w9_games
    all_byes = list(base_byes) + w9_byes
    weeks = sorted({g["week"] for g in all_games})
    check("combined log covers weeks 1-9 with no gap", weeks == list(range(1, 10)), str(weeks))
    for w in weeks:
        wg = [g for g in all_games if g["week"] == w]
        wb = [b for b in all_byes if b["week"] == w]
        seen = [g["away"] for g in wg] + [g["home"] for g in wg] + [b["team"] for b in wb]
        check(f"W{w}: every one of 32 teams appears exactly once (games + byes)",
              len(seen) == 32 and set(seen) == teams, f"{len(wg)} games, {len(wb)} byes")

    # ---------- post-cutoff game (standings recon only; NOT part of the log) ----------
    post = []
    for r in read_rows(os.path.join(DATA, "raw-w10-postcutoff-transcription.txt")):
        week, label, away, as_, home, hs, win_ind, slug = r
        post.append({"week": int(week), "heading": label, "away": away, "home": home,
                     "away_score": int(as_), "home_score": int(hs), "winner_indicator": win_ind, "slug": slug})
    check("post-cutoff: exactly 1 completed Week 10 game (WAS at NYG)",
          len(post) == 1 and post[0]["away"] == "WAS" and post[0]["home"] == "NYG"
          and post[0]["away_score"] == 24 and post[0]["home_score"] == 21,
          f"{post[0]['away']} {post[0]['away_score']}-{post[0]['home_score']} {post[0]['home']}" if post else "missing")
    for g in post:
        exp_slug = f"{nickname(g['away'])}-at-{nickname(g['home'])}-2026-reg-{g['week']}"
        check("post-cutoff game URL slug matches teams + week", g["slug"] == exp_slug, f"expected {exp_slug}")
        exp_w = g["away"] if g["away_score"] > g["home_score"] else g["home"]
        check("post-cutoff winner indicator agrees with scores", g["winner_indicator"] == exp_w,
              f"indicator={g['winner_indicator']} expected={exp_w}")

    # ---------- standings (2026-11-14 capture) ----------
    st = {}
    for r in read_rows(os.path.join(DATA, "raw-standings-2026-11-14.txt")):
        slug = r[0]
        a = SLUG_TO_ABBR[slug]
        st[a] = {"slug": slug, "W": int(r[1]), "L": int(r[2]), "T": int(r[3]), "PCT": r[4], "PF": int(r[5]),
                 "PA": int(r[6]), "NET": int(r[7]), "HOME": rec(r[8].replace(" ", "")), "ROAD": rec(r[9].replace(" ", "")),
                 "DIV": rec(r[10].replace(" ", "")), "DIV%": r[11], "CONF": rec(r[12].replace(" ", "")), "CONF%": r[13],
                 "col14": rec(r[14].replace(" ", "")), "STRK": r[15], "col16": rec(r[16].replace(" ", ""))}
    check("standings 2026-11-14: 32 distinct teams transcribed", len(st) == 32 and set(st) == teams, f"{len(st)} teams")

    # league arithmetic balance (independent check on the transcription itself)
    check("standings arithmetic: sum(PF) == sum(PA)",
          sum(s["PF"] for s in st.values()) == sum(s["PA"] for s in st.values()),
          f"PF={sum(s['PF'] for s in st.values())} PA={sum(s['PA'] for s in st.values())}")
    check("standings arithmetic: sum(W) == sum(L)",
          sum(s["W"] for s in st.values()) == sum(s["L"] for s in st.values()),
          f"W={sum(s['W'] for s in st.values())} L={sum(s['L'] for s in st.values())}")
    for a, s in st.items():
        gp = s["W"] + s["L"] + s["T"]
        if abs(pct(s["W"], s["L"], s["T"]) - float(s["PCT"])) > 0.00051:
            check(f"standings PCT arithmetic {a}", False, f"record {s['W']}-{s['L']}-{s['T']} vs PCT {s['PCT']}")
        if s["PF"] - s["PA"] != s["NET"]:
            check(f"standings NET arithmetic {a}", False, f"PF-PA={s['PF']-s['PA']} NET={s['NET']}")
    check("standings PCT and NET arithmetic hold for all 32 teams",
          all(abs(pct(s["W"], s["L"], s["T"]) - float(s["PCT"])) <= 0.00051 and s["PF"] - s["PA"] == s["NET"]
              for s in st.values()))

    # as-of verification: WAS/NYG must include the Thursday result; every other team must be W1-W9 only
    was, nyg = st["WAS"], st["NYG"]
    check("standings as-of: WAS row includes the Week 10 Thursday win (3-5-1, 9 gp)",
          (was["W"], was["L"], was["T"], was["STRK"]) == (3, 5, 1, "1W"), f"{was['W']}-{was['L']}-{was['T']} {was['STRK']}")
    check("standings as-of: NYG row includes the Week 10 Thursday loss (5-3-1, 9 gp, 1L)",
          (nyg["W"], nyg["L"], nyg["T"], nyg["STRK"]) == (5, 3, 1, "1L"), f"{nyg['W']}-{nyg['L']}-{nyg['T']} {nyg['STRK']}")

    # ---------- W10 slate file checks (data verification lives here; lines are model_w10's job) ----------
    w10_rows, w10_byes = [], []
    with open(os.path.join(DATA, "raw-schedule-w10-transcription.txt"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            if line.startswith("BYE"):
                _, team, record = line.rstrip("\n").split("|")
                w10_byes.append({"team": team, "record_shown": record})
                continue
            h, away, home, day, tm, net, slug = line.rstrip("\n").split("|")
            w10_rows.append({"heading": h, "away": away, "home": home, "day": day,
                             "time_as_rendered": tm, "network": net, "slug": slug})
    check("W10 slate: 14 games transcribed", len(w10_rows) == 14, f"{len(w10_rows)} games")
    check("W10 slate: 4 bye boxes (CHI, DEN, PHI, TB)", len(w10_byes) == 4 and {b['team'] for b in w10_byes} == {'CHI', 'DEN', 'PHI', 'TB'},
          ",".join(b["team"] for b in w10_byes))
    w10_seen = [r["away"] for r in w10_rows] + [r["home"] for r in w10_rows] + [b["team"] for b in w10_byes]
    check("W10 slate: every one of 32 teams appears exactly once (games + byes)",
          len(w10_seen) == 32 and set(w10_seen) == teams, f"{len(w10_seen)} appearances")
    for r in w10_rows:
        exp = f"{nickname(r['away'])}-at-{nickname(r['home'])}-2026-reg-10"
        check(f"W10 slug {r['away']}@{r['home']} matches teams + week", r["slug"] == exp, f"expected {exp}")
    for b in w10_byes:
        s = st[b["team"]]
        check(f"W10 bye box record {b['team']} equals standings W-L-T (as of 2026-11-14)",
              rec(b["record_shown"]) == (s["W"], s["L"], s["T"]),
              f"bye box {b['record_shown']} vs standings {s['W']}-{s['L']}-{s['T']}")
    for b in w9_byes:
        s = st[b["team"]]
        check(f"W9 bye box record {b['team']} equals standings W-L-T (as of 2026-11-14)",
              rec(b["record_shown"]) == (s["W"], s["L"], s["T"]),
              f"bye box {b['record_shown']} vs standings {s['W']}-{s['L']}-{s['T']}")
    # W10 slate vs W9 log: no team plays its W9 opponent pattern check is not meaningful; instead verify
    # every W10 game's away/home teams come from the 32 and the Thursday game is present and already final.
    thu = [r for r in w10_rows if r["slug"] == "commanders-at-giants-2026-reg-10"]
    check("W10 slate includes the completed Thursday game (excluded from lines by model_w10)",
          len(thu) == 1 and thu[0]["heading"] == "Thursday Night Football, November 12th",
          thu[0]["heading"] if thu else "missing")
    intl = [r for r in w10_rows if r["heading"].startswith("International Game")]
    check("W10 slate: exactly one international (neutral) game — NE at DET, Munich",
          len(intl) == 1 and intl[0]["away"] == "NE" and intl[0]["home"] == "DET",
          intl[0]["heading"] if intl else "missing")

    # ---------- division groups (inherited, structural) ----------
    conf, div = {}, {}
    for r in read_rows(os.path.join(DATA, "raw-division-groups.txt")):
        for slug in r[2].split(","):
            a = SLUG_TO_ABBR[slug]
            conf[a] = r[0]
            div[a] = f"{r[0]}-{r[1]}"
    check("division groups: 8 groups x 4 = 32 teams", len(div) == 32 and len(set(div.values())) == 8)

    # ---------- recompute from W1-W9 log + post-cutoff Thursday ----------
    def blank():
        return {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "HOME": [0, 0, 0], "ROAD": [0, 0, 0], "DIV": [0, 0, 0],
                "CONF": [0, 0, 0], "NONCONF": [0, 0, 0], "seq": []}
    calc = {t: blank() for t in teams}

    def accumulate(g, target):
        for side, opp, pf, pa, loc in ((g["away"], g["home"], g["away_score"], g["home_score"], "ROAD"),
                                        (g["home"], g["away"], g["home_score"], g["away_score"], "HOME")):
            c = target[side]
            res = 0 if pf > pa else (1 if pf < pa else 2)
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

    for g in sorted(all_games, key=lambda x: (x["week"], x.get("date") or "", x["away"])):
        if g.get("away_score") is None:
            continue
        accumulate(g, calc)
    # post-cutoff game appended ONLY to the standings-recon sequence (after W9), never into the published log
    for g in post:
        accumulate(g, calc)

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
                      "all_match": ok, "cells": cells, "source_url": STANDINGS_URL_1114,
                      "recon_scope": "W1-W9 log + W10 Thursday post-cutoff game" if t in ("WAS", "NYG") else "W1-W9 log"})
    n_cells = sum(len(r["cells"]) for r in recon)
    n_match = sum(x["match"] for r in recon for x in r["cells"])
    check("standings reconciliation: every cell for all 32 teams matches (512/512 required)",
          n_cells == n_match, f"{n_match}/{n_cells} cells match")
    hyp14 = all(x["match"] for r in recon for x in r["cells"] if x["column"].startswith("col14"))
    hyp16 = all(x["match"] for r in recon for x in r["cells"] if x["column"].startswith("col16"))
    check("unlabeled col14 behaves as non-conference record for all 32 teams", hyp14)
    check("unlabeled col16 behaves as last-5 record for all 32 teams", hyp16)

    # ---------- finalize W9 rows (fail-closed); W1-W8 rows carried verbatim ----------
    out_w9 = []
    for g in sorted(w9_games, key=lambda x: (x["week"], x["date"] or "", x["away"])):
        row_ok = all(c["pass"] for c in g["checks"]) and team_ok[g["away"]] and team_ok[g["home"]]
        row = {k: g.get(k) for k in ("week", "date", "heading", "international", "away", "home", "away_score",
                                     "home_score", "home_margin", "total", "winner_indicator", "game_url",
                                     "source_url")}
        row["verified"] = row_ok
        row["verification"] = ("transcribed from source_url on 2026-11-14; winner indicator, URL slug and weekly "
                               "completeness checks pass; both teams reconcile on all 16 standings columns at "
                               + STANDINGS_URL_1114 + " (captured 2026-11-14)") \
            if row_ok else "UNVERIFIED — see checks"
        if not row_ok:
            row["away_score"] = row["home_score"] = row["home_margin"] = row["total"] = None
            irregular.append({"id": "W2-IR-row", "game": f"W{g['week']} {g['away']}@{g['home']}",
                              "detail": "row failed a check; scores blanked", "source": g["source_url"]})
        row["checks"] = g["checks"]
        out_w9.append(row)

    out_base = []
    for g in base_games:
        row = dict(g)
        row_ok = row.get("verified") and team_ok[row["away"]] and team_ok[row["home"]]
        row["verified"] = bool(row_ok)
        row["verification"] = (f"inherited verified row (session 4bc92a5f capture of {row['source_url']}); both teams "
                               f"reconcile on all 16 standings columns at {STANDINGS_URL_1114} (captured 2026-11-14)"
                               if row_ok else "UNVERIFIED — team standings reconciliation failed on 2026-11-14 capture")
        if not row_ok:
            row["away_score"] = row["home_score"] = row["home_margin"] = row["total"] = None
            irregular.append({"id": "W2-IR-inherited-row", "game": f"W{row['week']} {row['away']}@{row['home']}",
                              "detail": "inherited row failed 2026-11-14 standings reconciliation; scores blanked",
                              "source": row["source_url"]})
        out_base.append(row)

    out_games = sorted(out_base + out_w9, key=lambda x: (x["week"], x["date"] or "", x["away"]))
    check("combined log: 136 games (121 W1-W8 + 15 W9)", len(out_games) == 136, f"{len(out_games)} games")
    check("combined log: every row verified (fail-closed)", all(g["verified"] for g in out_games),
          f"{sum(g['verified'] for g in out_games)}/{len(out_games)}")

    dump_json({"dataset": "games-2026-w1-w9", "captured_by": "session e8155046 (extends session 4bc92a5f's verified W1-W8 log)",
               "captured_at_utc": "2026-11-14",
               "sources": [SCORES_URL.format(w=w) for w in weeks] + [SCORES_W10_URL, STANDINGS_URL_1114, DIVISION_URL,
                                                                    SCHEDULE_W10_URL,
                                                                    "https://www.nfl.com/schedules/2026/by-week/week-9"],
               "notes": ["W1-W8 rows inherited verbatim from games-2026-w1-w8.json (session 4bc92a5f); W9 rows newly "
                         "transcribed 2026-11-14 by session e8155046.",
                         "standings reconciliation target = this log + the completed W10 Thursday game "
                         "(WAS 24 at NYG 21, raw-w10-postcutoff-transcription.txt); the Thursday game is NOT part of "
                         "this log and is excluded from Week 10 line origination.",
                         "home/away exactly as nfl.com lists them; designated home team for international games — "
                         "standings HOME/ROAD reconcile under that convention.",
                         "date = month/day from the rendered section heading + season year 2026.",
                         "no market (betting) data in this file."],
               "byes": all_byes, "games": out_games}, "games-2026-w1-w9.json", base=DATA)
    dump_json({"source_url": STANDINGS_URL_1114, "captured_at": "2026-11-14", "division_source_url": DIVISION_URL,
               "post_cutoff_game_source_url": SCORES_W10_URL, "teams": recon,
               "cells_total": n_cells, "cells_matching": n_match}, "standings-reconciliation-2026-11-14.json")
    summary = {"games": len(out_games), "verified_games": sum(g["verified"] for g in out_games),
               "checks_total": len(checks) + sum(len(g["checks"]) for g in w9_games),
               "checks_failed": [c for c in checks if not c["pass"]] +
                                [dict(c, game=f"W{g['week']} {g['away']}@{g['home']}") for g in w9_games for c in g["checks"] if not c["pass"]],
               "standings_cells": f"{n_match}/{n_cells}", "irregularities": irregular, "league_checks": checks}
    dump_json(summary, "w2-checks.json")
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
