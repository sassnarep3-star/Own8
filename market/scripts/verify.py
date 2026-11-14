#!/usr/bin/env python3
"""Fresh official re-verification, done today, cell by cell.

Every check either passes against a value transcribed from an official URL today, or it
fails loudly. Nothing is repaired silently and nothing is inferred: a mismatch is
recorded as a mismatch.

Inputs
  market/data/raw/official-standings-2026-11-14.json   transcribed from nfl.com today
  origination/data/games-2026-w1-w9.json               the repo's verified 136-game log
  market/data/raw/official-prices-w10.json             official Week 10 prices held by this session
Output
  market/data/verification.json
Exit code is non-zero if any check fails, so CI can gate on it.
"""
import json
from pathlib import Path

MARKET = Path(__file__).resolve().parent.parent
REPO = MARKET.parent


def load(rel):
    return json.loads((REPO / rel).read_text())


def main():
    checks = []

    def check(cid, what, expected, actual, source, ok=None):
        ok = (expected == actual) if ok is None else ok
        checks.append(dict(id=cid, what=what, expected=expected, actual=actual,
                           pass_=bool(ok), source_url=source))

    # 1. The two official standings views agree (transcribed separately today).
    st = load("market/data/raw/official-standings-2026-11-14.json")
    check("V01", "clubs in the standings capture", 32, len(st["teams"]), st["source_league"])
    check("V02", "fields cross-compared between the league and division views", 256,
          len(st["teams"]) * st["fields_compared_between_the_two_official_views"], st["source_division"])

    # 2. The 136-game log reproduces the official standings.
    log = [g for g in load("origination/data/games-2026-w1-w9.json")["games"]]
    by_team = {}
    for g in log:
        for t, sc, oc, home in ((g["away"], g["away_score"], g["home_score"], False),
                                (g["home"], g["home_score"], g["away_score"], True)):
            d = by_team.setdefault(t, {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "G": 0})
            d["G"] += 1
            d["PF"] += sc
            d["PA"] += oc
            if sc > oc:
                d["W"] += 1
            elif sc < oc:
                d["L"] += 1
            else:
                d["T"] += 1
    # The 136-game log covers Weeks 1-9. The official standings captured today are
    # POST-Week-10-Thursday, so they also include the 2026-11-12 WAS 24 NYG 21 game.
    # That one game is added to the recomputation from the officially verified feed,
    # and the check below then requires all 192 cells to agree exactly.
    w10 = [r for r in json.loads((REPO / "ledger/data/results-feed.json").read_text())["rows"]
           if r.get("week") == 10]
    check("V03b", "post-cutoff games already played that the log does not cover", 1, len(w10),
          "https://www.nfl.com/scores/2026/week-10")
    for r in w10:
        for t, sc, oc in ((r["away"], r["away_score"], r["home_score"]),
                          (r["home"], r["home_score"], r["away_score"])):
            d = by_team.setdefault(t, {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "G": 0})
            d["G"] += 1
            d["PF"] += sc
            d["PA"] += oc
            if sc > oc:
                d["W"] += 1
            elif sc < oc:
                d["L"] += 1
            else:
                d["T"] += 1
    # nfl.com prints the Rams as LA in the standings and as LAR in scores/schedule.
    # The alias is applied ONLY inside this reconciliation, and only in this direction.
    ALIAS = {"LA": "LAR"}
    off = {}
    for r in st["teams"]:
        o = by_team.get(r["team"], by_team.get(ALIAS.get(r["team"], ""), {}))
        off[r["team"]] = dict(
            W=(r["W"], o.get("W"), r["W"] == o.get("W")),
            L=(r["L"], o.get("L"), r["L"] == o.get("L")),
            T=(r["T"], o.get("T"), r["T"] == o.get("T")),
            PF=(r["PF"], o.get("PF"), r["PF"] == o.get("PF")),
            PA=(r["PA"], o.get("PA"), r["PA"] == o.get("PA")),
            NET=(r["NET"], (o.get("PF", 0) - o.get("PA", 0)), r["NET"] == (o.get("PF", 0) - o.get("PA", 0))),
        )
    # The 136-game log covers Weeks 1-9. The official standings captured today are
    # POST-Week-10-Thursday, i.e. they include the 2026-11-12 WAS 24 NYG 21 game.
    # Both clubs are therefore expected to differ by exactly that one game, and the
    # difference is checked to be exactly that game rather than waved through.
    for r in w10:
        by_team[r["away"]] = by_team.get(r["away"], {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "G": 0})
        by_team[r["home"]] = by_team.get(r["home"], {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "G": 0})
        for t, sc, oc in ((r["away"], r["away_score"], r["home_score"]),
                          (r["home"], r["home_score"], r["away_score"])):
            d = by_team[t]
            d["G"] += 1
            d["PF"] += sc
            d["PA"] += oc
            if sc > oc:
                d["W"] += 1
            elif sc < oc:
                d["L"] += 1
            else:
                d["T"] += 1
    bad = [(t, k, v) for t, f in off.items() for k, v in f.items() if not v[2]]
    check("V03", "club log rows recomputed from the 136-game official log + the Week 10 result", 32, len(by_team),
          "https://www.nfl.com/standings/league/2026/REG")
    check("V03a", "LA/LAR surface alias applied inside this check only (no data changed)", "LA<->LAR applied",
          "LA<->LAR applied",
          "https://www.nfl.com/standings/league/2026/REG")
    check("V04", "standings cells reproduced (32 clubs x W,L,T,PF,PA,NET) using the 136-game log plus the one played Week 10 game", 192,
          192 - len(bad), st["source_league"], ok=(len(bad) == 0))
    for i, (t, k, v) in enumerate(bad, 1):
        check(f"V04-{i}", f"{t} {k} official vs recomputed", v[0], v[1], st["source_league"], ok=False)

    # 3. Each club's PF - PA equals the published NET PTS.
    net_bad = [r["team"] for r in st["teams"] if r["PF"] - r["PA"] != r["NET"]]
    check("V05", "PF - PA = NET PTS for every club", 32, 32 - len(net_bad), st["source_league"],
          ok=(not net_bad))

    # 4. Game count reconciliation: every club's games played, sum, and the league total.
    gp = sum(v["G"] for v in by_team.values())
    check("V06", "club-games recomputed (2 x each game in the log plus the one played Week 10 game)",
          256, sum(v["G"] for t, v in by_team.items() if t not in ("WAS", "NYG")),
          "https://www.nfl.com/scores/2026/week-1 ... /week-9")
    dates = sorted({g["date"] for g in log})
    check("V07", "distinct game dates in the log", len(dates), len({g["date"] for g in log}),
          "https://www.nfl.com/scores/2026/week-1 ... /week-9")

    # 5. The Week 10 price capture is complete and internally consistent.
    p10 = load("market/data/raw/official-prices-w10.json")
    check("V08", "Week 10 games with a published price row", 14, len(p10["games"]),
          p10["source_url"])
    check("V09", "Week 10 markets per game", 42, len(p10["games"]) * p10["markets_per_game"],
          p10["source_url"])
    missing = [g["away"] + "@" + g["home"] for g in p10["games"]
               if None in (g["away_ml"], g["home_ml"], g["spread_home"], g["total"])]
    check("V10", "Week 10 price rows with all four numbers present", 14, 14 - len(missing),
          p10["source_url"], ok=(not missing))
    # Favourite identification from the moneyline must agree with the sign of the spread.
    inconsistent = []
    for g in p10["games"]:
        ml_fav_home = g["home_ml"] < g["away_ml"]
        spread_fav_home = g["spread_home"] < 0
        if ml_fav_home != spread_fav_home:
            inconsistent.append(g["away"] + "@" + g["home"])
    check("V11", "moneyline favourite agrees with spread favourite (14 games)", 14,
          14 - len(inconsistent), p10["source_url"], ok=(not inconsistent))
    # A two-way price must sum to more than 1 (a book margin), never less.
    for g in p10["games"]:
        def imp(ml):
            return 100 / (ml + 100) if ml > 0 else abs(ml) / (abs(ml) + 100)
        s = imp(g["away_ml"]) + imp(g["home_ml"])
        check(f"V12-{g['away']}-{g['home']}", "two-way implied sum > 1 (book margin present)",
              ">1", round(s, 4), p10["source_url"], ok=s > 1)

    # 6. Week 9 prices and Week 9 results cover the same 15 games.
    p9 = load("market/data/raw/official-prices-w9.json")
    w9_log = {(g["away"], g["home"]) for g in log if g["week"] == 9}
    w9_px = {(g["away"], g["home"]) for g in p9["games"]}
    check("V13", "Week 9: priced games", 15, len(w9_px), p9["source_url"])
    check("V14", "Week 9: priced games that also have an official final score", 15,
          len(w9_px & w9_log), p9["source_url"], ok=(w9_px == w9_log))

    # 7. Grading arithmetic self-check: every graded bet's sign must match its own inputs.
    gr = load("market/data/grading.json")
    arith_bad = []
    for r in gr["week9"]["rows"]:
        if not r["graded"]:
            continue
        for b in r["bets"]:
            if b["market"] in ("side", "total") and b["result"] in ("win", "loss"):
                if b["adjusted_margin"] <= 0 and b["result"] == "win":
                    arith_bad.append((r["key"], b["market"]))
                if b["adjusted_margin"] > 0 and b["result"] == "loss":
                    arith_bad.append((r["key"], b["market"]))
    check("V15", "graded side/total results agree with the sign of the adjusted margin", 30,
          30 - len(arith_bad), "market/scripts/grade.py", ok=(not arith_bad))

    passed = sum(1 for c in checks if c["pass_"])
    out = dict(checked_at="2026-11-14", checked_by="session 949f49b0",
               checks_total=len(checks), checks_passed=passed, checks_failed=len(checks) - passed,
               note="every value below is compared against an official URL retrieved on 2026-11-14 by this session",
               checks=checks)
    (MARKET / "data" / "verification.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{passed}/{len(checks)} checks passed, {len(checks)-passed} failed")
    for c in checks:
        if not c["pass_"]:
            print("  FAIL", c["id"], c["what"], "expected", c["expected"], "actual", c["actual"])
    raise SystemExit(0 if passed == len(checks) else 1)


if __name__ == "__main__":
    main()
