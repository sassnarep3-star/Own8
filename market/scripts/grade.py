#!/usr/bin/env python3
"""Grade the repository's own fair lines against officially published prices.

Inputs (read-only, never modified by this script):
  origination/results/w9-lines.json          model fair numbers for Week 9, generated 2026-11-04
  origination/results/w10-lines.json         model fair numbers for Week 10, generated 2026-11-14
  origination/data/games-2026-w1-w9.json     verified official game log (Weeks 1-9)
  market/data/raw/official-prices-w9.json    FanDuel prices as printed by nfl.com, Week 9
  market/data/raw/official-prices-w10.json   FanDuel prices as printed by nfl.com, Week 10
  requirements/data/raw-w9-scores.txt        independent Week 9 transcription (cross-check only)

Output: market/data/grading.json

Money model (stated, not hidden):
  * one unit staked per graded bet, flat; push returns the stake (0 profit);
  * a losing bet returns -1 unit; a winning bet returns (decimal odds - 1) units;
  * American -> decimal conversion is exact: +A gives 1 + A/100, -A gives 1 + 100/A;
  * the price used is the FanDuel number printed by nfl.com. It is ONE book at ONE
    recorded lock time. It is not the best available price and it is not the price
    anyone actually got.

What this cannot do, and says so in the output:
  * it cannot grade player props (no official prop prices exist in this repo, and no
    official source publishes prop lines at all);
  * it cannot evaluate a strategy as profitable on 15 or 13 bets. A coin-flip test and
    a Wilson interval are always printed next to the ROI.
"""
import json
import math
from pathlib import Path

try:
    from . import stats
except ImportError:  # run as a plain script: python3 market/scripts/x.py
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    import stats

MARKET = Path(__file__).resolve().parent.parent
REPO = MARKET.parent


def load(rel):
    return json.loads((REPO / rel).read_text())


def _first(d, keys, nd=4):
    for k in keys:
        if d.get(k) is not None:
            return round(d[k], nd)
    return None


def teams_key(away, home):
    return f"{away}@{home}"


def grade_side(fair_margin_home, price_spread_home, actual_margin_home):
    """Model side = home if its fair home margin > 0 else away.

    'at the market line' means the bet is settled against the printed spread, so a
    push is possible and is recorded as a push, not silently dropped.
    """
    side = "home" if fair_margin_home > 0 else "away"
    if side == "home":
        line, margin = price_spread_home, actual_margin_home
    else:
        line, margin = -price_spread_home, -actual_margin_home
    adjusted = margin + line
    if abs(adjusted) < 1e-9:
        return side, "push", adjusted
    return side, ("win" if adjusted > 0 else "loss"), adjusted


def grade_total(fair_total, price_total, actual_total):
    side = "over" if fair_total > price_total else ("under" if fair_total < price_total else None)
    if side is None:
        return None, "push", actual_total - price_total
    adjusted = (actual_total - price_total) * (1 if side == "over" else -1)
    if abs(adjusted) < 1e-9:
        return side, "push", adjusted
    return side, ("win" if adjusted > 0 else "loss"), adjusted


def grade_ml(fair_p_home, actual_margin_home):
    """Model side = the side with fair probability > 0.5 (a tie is a no-bet).

    Moneyline has no push in the NFL, so a tie game is recorded as a void/no-bet and
    excluded from the record rather than counted either way.
    """
    if fair_p_home == 0.5:
        return None, "no-bet", None
    side = "home" if fair_p_home > 0.5 else "away"
    if actual_margin_home == 0:
        return side, "void-tie", 0
    won = (actual_margin_home > 0) if side == "home" else (actual_margin_home < 0)
    return side, ("win" if won else "loss"), None


def pnl(units_result, decimal_odds):
    if units_result == "win":
        return decimal_odds - 1.0
    if units_result == "loss":
        return -1.0
    return 0.0


def summarise(bets, label):
    settled = [b for b in bets if b["result"] in ("win", "loss")]
    wins = sum(1 for b in settled if b["result"] == "win")
    pushes = sum(1 for b in bets if b["result"] == "push")
    profit = sum(b["profit_units"] for b in bets)
    staked = sum(1 for b in bets if b["result"] in ("win", "loss", "push"))
    roi = (profit / staked) if staked else None
    lo, hi = stats.wilson(wins, len(settled))
    # Coin-flip null: a bet at decimal d breaks even at p* = 1/d.
    priced = [b for b in settled if b.get("decimal_odds")]
    breakeven = (sum(1.0 / b["decimal_odds"] for b in priced) / len(priced)) if priced else None
    obs = wins / len(settled) if settled else None
    # Exact two-sided binomial test against the average break-even rate.
    p_val = binomial_ge(wins, len(settled), breakeven) if settled else None
    return {
        "label": label,
        "bets": len(bets),
        "settled": len(settled),
        "wins": wins,
        "losses": len(settled) - wins,
        "pushes": pushes,
        "void_or_nobet": sum(1 for b in bets if b["result"] in ("void-tie", "no-bet")),
        "hit_rate": obs,
        "hit_rate_wilson95": [lo, hi],
        "breakeven_rate_at_prices": breakeven,
        "profit_units": profit,
        "units_staked": staked,
        "roi": roi,
        "p_value_vs_breakeven": p_val,
        "verdict": verdict(obs, lo, breakeven, len(settled)),
    }


def binomial_ge(k, n, p):
    """Two-sided exact binomial test (doubling the smaller tail), p is the null rate."""
    if p is None or n == 0:
        return None
    def pmf(i):
        return math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    ge = sum(pmf(i) for i in range(k, n + 1))
    le = sum(pmf(i) for i in range(0, k + 1))
    return min(1.0, 2 * min(ge, le))


def verdict(obs, lo, breakeven, n):
    if obs is None or n == 0:
        return "NO BETS"
    if n < 30:
        base = f"UNDERPOWERED (n={n}, need >=30 settled bets before any ROI is interpretable)"
    else:
        base = f"n={n}"
    if obs > breakeven and lo is not None and lo > breakeven:
        return "EVIDENCE OF EDGE ABOVE BREAKEVEN - " + base
    if obs > breakeven:
        return "POINT ESTIMATE ABOVE BREAKEVEN, INTERVAL INCLUDES IT - NOT SKILL - " + base
    return "POINT ESTIMATE BELOW BREAKEVEN - NO EDGE - " + base


def build_week(week, lines_file, log, prices_file, results_key):
    lines = load(lines_file)
    prices = load(prices_file)
    price_by_game = {teams_key(g["away"], g["home"]): g for g in prices["games"]}
    score_by_game = {teams_key(g["away"], g["home"]): g for g in log["games"] if g["week"] == week}

    rows = []
    for g in lines["games"]:
        k = teams_key(g["away"], g["home"])
        p = price_by_game.get(k)
        s = score_by_game.get(k)
        row = {
            "key": f"2026-W{week:02d}-{g['away']}-{g['home']}",
            "week": week,
            "away": g["away"],
            "home": g["home"],
            "game_url": g["game_url"],
            "price_source_url": prices["source_url"],
            "price_lock": prices["lock_statement"],
            "fair_home_margin": _first(g, ("fair_margin_home_S1", "fair_home_margin_B0")),
            "fair_total": _first(g, ("fair_total_S4", "fair_total_B0")),
            "fair_p_home": _first(g, ("p_home_S6", "p_home_win_normal")),
            "fair_p_home_S7": _first(g, ("p_home_S7",)),
            "fair_p_home_S8": _first(g, ("p_home_S8",)),
            "market_spread_home": p["spread_home"] if p else None,
            "market_total": p["total"] if p else None,
            "market_ml_home": p["home_ml"] if p else None,
            "market_ml_away": p["away_ml"] if p else None,
            "actual_home_margin": s["home_score"] - s["away_score"] if s else None,
            "actual_total": s["home_score"] + s["away_score"] if s else None,
            "result_source_url": s["source_url"] if s else None,
            "graded": False,
            "reason_not_graded": None,
            "bets": [],
        }
        if p is None:
            row["reason_not_graded"] = "no officially published price row for this game"
        elif s is None:
            row["reason_not_graded"] = "game not yet final at capture time; no result to settle against"
        else:
            row["graded"] = True
            fair_margin = row["fair_home_margin"]
            fair_total = row["fair_total"]
            fair_p = row["fair_p_home"]
            actual_margin = row["actual_home_margin"]
            actual_total = row["actual_total"]

            # 1. Side (spread) at the published spread
            side, res, adj = grade_side(fair_margin, p["spread_home"], actual_margin)
            row["bets"].append(dict(
                market="side", model_side=side, line=p["spread_home"],
                fair_value=fair_margin, market_value=p["spread_home"],
                difference=round(fair_margin - p["spread_home"], 4),
                adjusted_margin=round(adj, 3), result=res,
                price_note="spread bets conventionally priced -110 both ways; the nfl.com page prints no spread price",
                decimal_odds=stats.american_to_decimal(-110), profit_units=pnl(res, stats.american_to_decimal(-110)),
            ))
            # 2. Total at the published total
            tside, tres, tadj = grade_total(fair_total, p["total"], actual_total)
            row["bets"].append(dict(
                market="total", model_side=tside, line=p["total"],
                fair_value=fair_total, market_value=p["total"],
                difference=round(fair_total - p["total"], 4),
                adjusted_margin=round(tadj, 3), result=tres,
                price_note="totals conventionally priced -110 both ways; the nfl.com page prints no total price",
                decimal_odds=stats.american_to_decimal(-110), profit_units=pnl(tres, stats.american_to_decimal(-110)),
            ))
            # 3. Moneyline at the published moneyline
            mside, mres, _ = grade_ml(fair_p, actual_margin)
            if mside is None:
                ml_price = None
            else:
                ml_price = p["home_ml"] if mside == "home" else p["away_ml"]
            dec = stats.american_to_decimal(ml_price) if ml_price is not None else None
            row["bets"].append(dict(
                market="moneyline", model_side=mside, line=None,
                fair_value=fair_p, market_value=stats.american_to_implied(p["home_ml"]),
                difference=round(fair_p - stats.american_to_implied(p["home_ml"]), 4) if p["home_ml"] else None,
                result=mres,
                price_note="published American moneyline used directly",
                decimal_odds=dec, profit_units=pnl(mres, dec) if dec else 0.0,
            ))
        rows.append(row)

    graded = [r for r in rows if r["graded"]]
    flat = [b for r in graded for b in r["bets"]]
    by_market = {}
    for m in ("side", "total", "moneyline"):
        by_market[m] = summarise([b for b in flat if b["market"] == m], f"Week {week} {m}")
    overall = summarise(flat, f"Week {week} all markets")
    return rows, by_market, overall


def main():
    log = load("origination/data/games-2026-w1-w9.json")
    w9_rows, w9_by, w9_all = build_week(9, "origination/results/w9-lines.json", log, "market/data/raw/official-prices-w9.json", "raw-w9-scores.txt")
    w10_rows, w10_by, w10_all = build_week(10, "origination/results/w10-lines.json", log, "market/data/raw/official-prices-w10.json", None)

    # Independent cross-check of the Week 9 scores against a second transcription.
    w9_txt = (REPO / "requirements/data/raw-w9-scores.txt").read_text().splitlines()
    cross = {"file": "requirements/data/raw-w9-scores.txt", "checked": [], "mismatches": []}
    # Format of that file: week | heading | away | away_score | home | home_score | winner | slug
    for line in w9_txt:
        parts = [x.strip() for x in line.split("|")]
        if len(parts) < 6 or line.startswith("#"):
            continue
        try:
            av, asc, hm, hsc = parts[2], int(parts[3]), parts[4], int(parts[5])
        except ValueError:
            continue
        hit = [r for r in w9_rows if r["away"] == av and r["home"] == hm]
        if hit:
            ok = hit[0]["actual_home_margin"] == hsc - asc
            (cross["checked"] if ok else cross["mismatches"]).append(f"{av} {asc} @ {hm} {hsc}")

    out = {
        "generated": "2026-11-14",
        "generated_by": "session 949f49b0",
        "description": "Fair line vs officially published FanDuel price vs difference, with settlement, flat-stake units and a stated verdict per line. The money model is documented in market/scripts/grade.py.",
        "money_model": {
            "stake": "1 unit per bet, flat, no compounding, no stake sizing",
            "side_and_total_price_assumption": "normally -110 both ways; nfl.com prints no spread or total price, so -110 is an ASSUMPTION recorded per bet, not an official number",
            "moneyline_price": "the American number printed by nfl.com, converted exactly",
            "push": "stake returned, 0 profit, counted as a bet",
            "tie_game_moneyline": "void, excluded from record",
        },
        "week9": {"rows": w9_rows, "by_market": w9_by, "overall": w9_all},
        "week10": {"rows": w10_rows, "by_market": w10_by, "overall": w10_all},
        "score_crosscheck": cross,
    }
    (MARKET / "data" / "grading.json").write_text(json.dumps(out, indent=1) + "\n")

    for wk, by, allr in (("W9", w9_by, w9_all), ("W10", w10_by, w10_all)):
        print(f"== {wk}")
        for k, v in list(by.items()) + [("ALL", allr)]:
            roi = "n/a" if v["roi"] is None else f"{v['roi']*100:+.1f}%"
            print(f"  {v['label']:22s} bets={v['bets']:2d} W-L-P={v['wins']}-{v['losses']}-{v['pushes']} "
                  f"hit={v['hit_rate']} breakeven={None if v['breakeven_rate_at_prices'] is None else round(v['breakeven_rate_at_prices'],3)} "
                  f"ROI={roi} units={v['profit_units']:+.2f} p={None if v['p_value_vs_breakeven'] is None else round(v['p_value_vs_breakeven'],3)}")
    print("cross-check:", len(cross["checked"]), "ok,", len(cross["mismatches"]), "mismatches")


if __name__ == "__main__":
    main()
