#!/usr/bin/env python3
"""Originate our own numbers against the market: side first, then total, then moneyline.

SIGN CONVENTION (fixed here so every column is unambiguous)
  margin_home      : home_score - away_score. Negative means the home team lost.
  handicap_home    : points added to the home team. -3.0 means "home favoured by 3".
  For any game, handicap_home = -margin_home.

Origin order is enforced and printed: side is produced first, total second, moneyline
last, because the moneyline is derived from the side's margin distribution. That is the
operator's requirement, and it exposes the dependency: the side drives the moneyline,
never the reverse.

What this produces
  1. the market's own numbers, de-vigged where a price exists (Week 9 and Week 10);
  2. our own numbers, copied read-only from the origination results files;
  3. the difference between them, in one convention, on the same row;
  4. on Week 9 - the only week with BOTH an official price and an official result - a
     head-to-head accuracy table: which is closer to what actually happened, our number
     or the market's? That is the only honest test of "can we originate our own line";
  5. a blend weight, fitted and reported, with an explicit rule for when it may be adopted.
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
SIGMA_MARGIN = 12.60684074876305   # origination/results/w10-lines.json -> model.S1_sigma_loo
SIGMA_TOTAL = 13.715481424180531   # origination/results/w10-lines.json -> model.S2_sigma_total


def load(rel):
    return json.loads((REPO / rel).read_text())


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def inv_norm(p):
    lo, hi = -6.0, 6.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def prob_to_american(p):
    if p is None or p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return round(-100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def market_table(week):
    prices = load(f"market/data/raw/official-prices-w{week}.json")
    out = {}
    for g in prices["games"]:
        raw_a = stats.american_to_implied(g["away_ml"])
        raw_h = stats.american_to_implied(g["home_ml"])
        _, dev_h = stats.pair_devig(raw_a, raw_h)
        implied_handicap = -SIGMA_MARGIN * inv_norm(dev_h)
        out[(g["away"], g["home"])] = dict(
            raw_home=raw_h, raw_away=raw_a, devig_home=dev_h,
            overround=raw_a + raw_h - 1,
            implied_handicap_home=implied_handicap,
            published_handicap_home=g["spread_home"],
            published_total=g["total"],
            published_ml_home=g["home_ml"], published_ml_away=g["away_ml"],
            spread_minus_implied=round(g["spread_home"] - implied_handicap, 3),
            verbatim=g["verbatim"],
        )
    return out, prices["source_url"], prices["lock_statement"]


def three_column_rows(week, own_games, home_margin_key, total_key, p_key):
    mkt, url, lock = market_table(week)
    rows = []
    for g in own_games:
        m = mkt.get((g["away"], g["home"]))
        if m is None:
            continue
        own_margin = g[home_margin_key]
        own_handicap = -own_margin
        own_total = g[total_key]
        own_p = g[p_key]
        base = dict(week=week, away=g["away"], home=g["home"], game_url=g["game_url"],
                    price_source_url=url, lock=lock, verbatim=m["verbatim"],
                    book_overround=round(m["overround"], 4),
                    market_devig_p_home=round(m["devig_home"], 4))
        rows.append(dict(base, order=1, market="side",
                         own_fair_handicap_home=round(own_handicap, 3),
                         own_fair_home_margin=round(own_margin, 3),
                         market_published_handicap_home=m["published_handicap_home"],
                         market_implied_handicap_home=round(m["implied_handicap_home"], 3),
                         difference_vs_published=round(own_handicap - m["published_handicap_home"], 3),
                         difference_vs_devigged=round(own_handicap - m["implied_handicap_home"], 3),
                         columns_are_three_separate_columns=True))
        rows.append(dict(base, order=2, market="total",
                         own_fair_total=round(own_total, 3),
                         market_published_total=m["published_total"],
                         difference_vs_published=round(own_total - m["published_total"], 3),
                         note="the market prints a total but no total price; nothing independent of the printed total exists, so only one difference column is defined here"))
        rows.append(dict(base, order=3, market="moneyline",
                         own_p_home=round(own_p, 4),
                         own_ml_home=prob_to_american(own_p), own_ml_away=prob_to_american(1 - own_p),
                         market_published_ml_home=m["published_ml_home"],
                         market_published_ml_away=m["published_ml_away"],
                         difference_vs_raw_p_home=round(own_p - m["raw_home"], 4),
                         difference_vs_devigged_p_home=round(own_p - m["devig_home"], 4),
                         note="the moneyline is originated last, from the side's margin distribution"))
    return rows, url, lock, mkt


def week9_head_to_head():
    """Who is closer to the truth on Week 9 - our own number or the market's?

    Both are compared on the SAME 15 games against the official finals. Errors are
    absolute. A paired bootstrap on (our error - market error) says whether any
    apparent difference could be noise.
    """
    grading = load("market/data/grading.json")
    rows = [r for r in grading["week9"]["rows"] if r["graded"]]
    out = []
    side_diffs, total_diffs, ml_our, ml_mkt, ml_n = [], [], [], [], 0
    for r in rows:
        actual_margin = r["actual_home_margin"]
        actual_total = r["actual_total"]
        own_h = -r["fair_home_margin"]
        mkt_h = r["market_spread_home"]
        e_own = abs(own_h - (-actual_margin))
        e_mkt = abs(mkt_h - (-actual_margin))
        side_diffs.append(e_own - e_mkt)
        e_own_t = abs(r["fair_total"] - actual_total)
        e_mkt_t = abs(r["market_total"] - actual_total)
        total_diffs.append(e_own_t - e_mkt_t)
        y = 1.0 if actual_margin > 0 else 0.0
        raw_h = stats.american_to_implied(r["market_ml_home"])
        raw_a = stats.american_to_implied(r["market_ml_away"])
        _, dev_h = stats.pair_devig(raw_a, raw_h)
        ml_our.append(stats.brier(r["fair_p_home"], y))
        ml_mkt.append(stats.brier(dev_h, y))
        ml_n += 1
        out.append(dict(
            key=r["key"], away=r["away"], home=r["home"],
            actual_home_margin=actual_margin, actual_total=actual_total,
            own_handicap_home=round(own_h, 3), market_handicap_home=mkt_h,
            own_abs_error=round(e_own, 3), market_abs_error=round(e_mkt, 3),
            closer=("own" if e_own < e_mkt else ("market" if e_mkt < e_own else "tie")),
            own_total=round(r["fair_total"], 3), market_total=r["market_total"],
            own_total_abs_error=round(e_own_t, 3), market_total_abs_error=round(e_mkt_t, 3),
            own_p_home=r["fair_p_home"], market_devig_p_home=round(dev_h, 4),
            game_url=r["game_url"], price_source_url=r["price_source_url"],
            result_source_url=r["result_source_url"],
        ))
    summary = {
        "n": len(out),
        "side": {
            "own_mae": round(stats.mean([abs(-r["fair_home_margin"] - (-r["actual_home_margin"])) for r in rows]), 4),
            "market_mae": round(stats.mean([abs(r["market_spread_home"] - (-r["actual_home_margin"])) for r in rows]), 4),
            "mean_paired_diff_own_minus_market": round(stats.mean(side_diffs), 4),
            "paired_diff_ci95": [round(x, 4) for x in stats.bootstrap_ci(side_diffs)],
            "p_one_sided_own_better": stats.signflip_p(side_diffs),
            "games_own_closer": sum(1 for r in out if r["closer"] == "own"),
        },
        "total": {
            "own_mae": round(stats.mean([abs(r["fair_total"] - r["actual_total"]) for r in rows]), 4),
            "market_mae": round(stats.mean([abs(r["market_total"] - r["actual_total"]) for r in rows]), 4),
            "mean_paired_diff_own_minus_market": round(stats.mean(total_diffs), 4),
            "paired_diff_ci95": [round(x, 4) for x in stats.bootstrap_ci(total_diffs)],
            "p_one_sided_own_better": stats.signflip_p(total_diffs),
        },
        "moneyline": {
            "own_brier": round(stats.mean(ml_our), 6),
            "market_devig_brier": round(stats.mean(ml_mkt), 6),
            "mean_paired_diff_own_minus_market": round(stats.mean([a - b for a, b in zip(ml_our, ml_mkt)]), 6),
            "paired_diff_ci95": [round(x, 6) for x in stats.bootstrap_ci([a - b for a, b in zip(ml_our, ml_mkt)])],
            "p_one_sided_own_better": stats.signflip_p([a - b for a, b in zip(ml_our, ml_mkt)]),
        },
    }
    return out, summary


def blend_analysis():
    """Fit w in p = w*own + (1-w)*market on Week 9, scored by Brier. Reported, not adopted."""
    grading = load("market/data/grading.json")
    rows = [r for r in grading["week9"]["rows"] if r["graded"]]
    res = {"n": len(rows), "fitted_on": "Week 9 only", "by_strategy": {}}
    for label, field in (("S6", "fair_p_home"), ("S7", "fair_p_home_S7"), ("S8", "fair_p_home_S8")):
        usable = [r for r in rows if r.get(field) is not None]
        if not usable:
            continue
        curve = []
        best = None
        for i in range(21):
            w = i / 20
            bs = []
            for r in usable:
                raw_h = stats.american_to_implied(r["market_ml_home"])
                raw_a = stats.american_to_implied(r["market_ml_away"])
                _, dev_h = stats.pair_devig(raw_a, raw_h)
                p = w * r[field] + (1 - w) * dev_h
                y = 1.0 if r["actual_home_margin"] > 0 else 0.0
                bs.append(stats.brier(p, y))
            m = stats.mean(bs)
            curve.append({"w_own": round(w, 2), "brier": round(m, 6)})
            if best is None or m < best[1]:
                best = (round(w, 2), m)
        res["by_strategy"][label] = {"best_w_own": best[0], "best_brier": round(best[1], 6),
                                     "n": len(usable), "curve": curve}
    res["decision_rule"] = (
        "Do not adopt a non-zero weight until all four hold: (1) at least 60 priced games scored; "
        "(2) the weight is re-fitted walk-forward, i.e. fitted only on weeks before the week it scores; "
        "(3) the blended model's lower 95% bootstrap bound on per-bet skill is above 0; "
        "(4) that survives Holm across the whole strategy family. A weight fitted on 15 games is a "
        "description of 15 games."
    )
    return res


def main():
    own10 = load("origination/results/w10-lines.json")
    rows10, url10, lock10, _ = three_column_rows(
        10, own10["games"], "fair_home_margin_S1", "fair_total_S4", "p_home_S6")
    own9 = load("origination/results/w9-lines.json")
    rows9, url9, lock9, _ = three_column_rows(
        9, own9["games"], "fair_margin_home_S1", "fair_total_S4", "p_home_S6")
    h2h_rows, h2h = week9_head_to_head()
    blend = blend_analysis()
    order_ok = all(rows10[i * 3]["order"] == 1 and rows10[i * 3 + 1]["order"] == 2
                   and rows10[i * 3 + 2]["order"] == 3 for i in range(len(rows10) // 3))
    out = {
        "generated": "2026-11-14",
        "generated_by": "session 949f49b0",
        "convention": {
            "margin_home": "home_score - away_score",
            "handicap_home": "points added to the home team; -3.0 means home favoured by 3",
            "identity": "handicap_home = -margin_home",
        },
        "origin_order": ["side", "total", "moneyline"],
        "origin_order_verified": order_ok,
        "sigma_margin_used": SIGMA_MARGIN,
        "why_sigma_matters": (
            "the market-implied handicap is a translation of a probability through OUR normal model, so it is "
            "not a number the market publishes. The published handicap is the market's own number and sits "
            "beside it. When the two disagree, the model's sigma is wrong, not the market."),
        "week10": {"rows": rows10, "price_source_url": url10, "lock": lock10,
                   "status": "PROSPECTIVE - UNVALIDATED; the games had not been played at capture time, so no outcome and no ROI is attached"},
        "week9": {"rows": rows9, "price_source_url": url9, "lock": lock9,
                  "status": "GRADED - see week9_head_to_head"},
        "week9_head_to_head": {"rows": h2h_rows, "summary": h2h},
        "blend": blend,
    }
    (MARKET / "data" / "own-lines.json").write_text(json.dumps(out, indent=1) + "\n")

    print("rows W10", len(rows10), "order ok", order_ok, "| rows W9", len(rows9))
    print("\n== Week 9 head to head (identical 15 games, official finals)")
    for k, v in h2h.items():
        print(" ", k, json.dumps(v))
    print("\n== blend (fitted on the same 15 games)")
    for k, v in blend["by_strategy"].items():
        print(" ", k, "best w_own =", v["best_w_own"], "brier", v["best_brier"])


if __name__ == "__main__":
    main()
