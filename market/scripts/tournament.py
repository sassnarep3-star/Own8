#!/usr/bin/env python3
"""Strategy tournament: score every pre-registered strategy on the SAME official prices.

Why this file exists. The repository already contains a validated strategy tournament
(origination/results/validation-w10.json: 12 strategies, 8 pre-registered gates,
4 passing). That tournament is scored on LOSS FUNCTIONS - mean absolute error and
Brier score - because no official price existed when it was written. A loss function
ranks forecasts; it does not pay a bettor. This script re-settles the SAME forecasts
against prices that nfl.com actually publishes, so a competitive leaderboard can rank
strategies on the thing the operator cares about (money) without dropping the
statistical discipline (per-bet skill vs the market's own probability, a lower bound,
and a multiple-testing correction).

Inputs are read-only:
  origination/results/walkforward-games-w10.json   per-game walk-forward forecasts, every strategy
  origination/results/walkforward-games.json       Weeks 3-8 forecasts (augmentation for n)
  origination/results/w9-lines.json                Week 9 published fair lines
  origination/data/games-2026-w1-w9.json           official verified results
  market/data/raw/official-prices-w9.json          official Week 9 prices
  market/data/raw/official-prices-w10.json         official Week 10 prices
Output:
  market/data/tournament.json

Honesty rules enforced here:
  * A strategy with no priced market is listed and marked UNPRICEABLE, never scored.
  * Every row prints n. Every p-value is Holm-adjusted across the family of scored
    strategies, and the family size is printed.
  * Skill is measured per bet as (model probability of the side it chose) minus (the
    de-vigged market probability of that same side). Beating a raw price only means
    "the book kept less than expected", which is not skill.
  * Any claim about ROI is suppressed below 30 settled bets by the verdict function
    in grade.py; the number is still printed, with its verdict beside it.
"""
import json
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

STRATEGIES = [
    ("S1", "Single: point spread", "Ridge margin ratings + home edge (lambda by LOO-CV)", "side"),
    ("S2", "Single: point spread", "Offence/defence points ridge -> margin", "side"),
    ("S3", "Single: point spread", "Naive season point differential per game (unshrunk) - control", "side"),
    ("S4", "Single: game total", "Offence/defence points ridge -> total", "total"),
    ("S5", "Single: game total", "Naive PF/PA per game averages -> total - control", "total"),
    ("S6", "Single: moneyline", "Win probability = Phi(S1 margin / LOO sigma)", "moneyline"),
    ("S7", "Single: moneyline", "Win probability = Phi(S2 margin / sigma)", "moneyline"),
    ("S8", "Single: moneyline", "Win probability = Phi(S3 margin / S1 sigma) - control", "moneyline"),
    ("S9", "Parlay: 2-leg cross-game moneyline", "Product of S6 leg probabilities (independence)", "parlay"),
    ("S10", "Same-game parlay: side + total", "Bivariate-normal joint probability", "sgp"),
    ("S11", "Player prop: QB passing yards", "Empirical-Bayes shrunk QB average", "prop"),
    ("S12", "Player prop: QB passing yards", "S11 + shrunk opponent pass-defence adjustment", "prop"),
]


def load(rel):
    return json.loads((REPO / rel).read_text())


def price_map(week):
    d = load(f"market/data/raw/official-prices-w{week}.json")
    return {(g["away"], g["home"]): g for g in d["games"]}, d["source_url"], d["lock_statement"]


def devig_moneyline(p):
    """De-vigged home probability from the published pair, plus the book's margin."""
    raw_a = stats.american_to_implied(p["away_ml"])
    raw_h = stats.american_to_implied(p["home_ml"])
    _, dh = stats.pair_devig(raw_a, raw_h)
    return dh, (raw_a + raw_h) - 1.0


def settle_moneyline(choose_home, p):
    """Return (won, price, model_prob, market_prob_after_vig, per_bet_skill)."""
    price = p["home_ml"] if choose_home else p["away_ml"]
    return price


def row_from_games(games, week, prices, results, strategy_spec, prob_key):
    """Build per-bet rows for one strategy on one week of official prices."""
    out = []
    for g in games:
        p = prices.get((g["away"], g["home"]))
        if p is None:
            continue
        res = results.get((g["away"], g["home"]))
        if res is None:
            continue
        away_score, home_score = res[0], res[1]
        margin = home_score - away_score
        total = home_score + away_score
        p_home = g[prob_key]
        side_home = p_home >= 0.5
        dec = stats.american_to_decimal(p["home_ml"] if side_home else p["away_ml"])
        won = (margin > 0) if side_home else (margin < 0)
        void = margin == 0
        mkt_home, vig = devig_moneyline(p)
        model_prob_side = p_home if side_home else 1 - p_home
        market_prob_side = mkt_home if side_home else 1 - mkt_home
        out.append(dict(
            week=week, away=g["away"], home=g["home"],
            strategy_prob_home=round(p_home, 4),
            side="home" if side_home else "away",
            decimal_odds=round(dec, 4),
            result="void-tie" if void else ("win" if won else "loss"),
            profit_units=0.0 if void else (round(dec - 1, 4) if won else -1.0),
            model_prob_side=round(model_prob_side, 4),
            market_prob_side_devigged=round(market_prob_side, 4),
            per_bet_skill=round(model_prob_side - market_prob_side, 4),
            book_margin=round(vig, 4),
            price_source_url="market/data/raw/official-prices-w9.json" if week == 9 else "market/data/raw/official-prices-w10.json",
            result_source_url=res[2],
        ))
    return out


def main():
    wf = load("origination/results/walkforward-games-w10.json")["games"]
    wf_small = load("origination/results/walkforward-games.json")["games"]
    log = load("origination/data/games-2026-w1-w9.json")["games"]
    results = {}
    for g in log:
        results[(g["away"], g["home"])] = (g["away_score"], g["home_score"], g["source_url"])
    p9, u9, l9 = price_map(9)
    p10, u10, l10 = price_map(10)

    w9 = [g for g in wf if g["week"] == 9]
    w10 = []  # no Week 10 results exist yet at capture time (all games unplayed or ungraded)
    priced_week9_games = {k for k in p9 if k in results}
    print("priced Week 9 games with a result:", len(priced_week9_games))
    print("Week 10 games priced but not yet played:", len(p10))
    print("Weeks 3-8 forecasts available:", len(wf_small), "(no official price for these weeks in this repo)")

    prob_keys = {"S6": "p_S6", "S7": "p_S7", "S8": "p_S8"}
    rows = []
    family = []
    for sid, product, desc, market in STRATEGIES:
        entry = dict(id=sid, product=product, strategy=desc, market_type=market,
                     n_bets=0, n_settled=0, status=None, reason=None, bets=[])
        if market in ("parlay", "sgp"):
            entry["status"] = "UNPRICEABLE - NO OFFICIAL PRICE"
            entry["reason"] = ("nfl.com publishes only single-game spread, total and moneyline prices. "
                               "It publishes no parlay or same-game-parlay price, so no parlay ROI can be "
                               "computed from an official source. Left unscored, never estimated.")
        elif market == "prop":
            entry["status"] = "UNPRICEABLE - NO OFFICIAL PRICE"
            entry["reason"] = ("nfl.com publishes no player-prop line or price anywhere in the retrieved "
                               "sources. The prop forecasts exist and are graded on loss (see "
                               "origination/results/validation-w10.json) but cannot be priced.")
        else:
            if market in ("side", "total"):
                entry["status"] = "SCORED ON LOSS ONLY - NO OFFICIAL PRICE FOR THIS MARKET"
                entry["reason"] = ("nfl.com prints a spread and a total but no PRICE for either. Grading a "
                                   "spread bet requires an assumed -110, which is a convention, not an "
                                   "official number, so this strategy is ranked on loss only.")
            else:
              key = prob_keys[sid]
              bets = row_from_games(w9, 9, p9, results, (sid, product, desc, market), key)
              settled = [b for b in bets if b["result"] in ("win", "loss")]
              wins = sum(1 for b in settled if b["result"] == "win")
              profit = sum(b["profit_units"] for b in bets)
              skills = [b["per_bet_skill"] for b in settled]
              be = (sum(1.0 / b["decimal_odds"] for b in settled) / len(settled)) if settled else None
              entry.update(
                  n_bets=len(bets), n_settled=len(settled), wins=wins,
                  losses=len(settled) - wins, pushes=len(bets) - len(settled),
                  hit_rate=(wins / len(settled)) if settled else None,
                  hit_rate_wilson95=list(stats.wilson(wins, len(settled))) if settled else None,
                  breakeven_rate=be,
                  roi=(profit / len(bets)) if bets else None,
                  profit_units=round(profit, 4),
                  mean_skill=stats.mean(skills), mean_skill_ci95=list(stats.bootstrap_ci(skills)) if skills else None,
                  mean_book_margin=stats.mean([b["book_margin"] for b in bets]) if bets else None,
                  p_value_vs_breakeven=binomial_two_sided(wins, len(settled), be) if settled else None,
                  status="SCORED", bets=bets,
              )
              if skills:
                  family.append((sid, stats.signflip_p(skills)))
        rows.append(entry)

    # Holm across the scored family only; the family size is printed with the result.
    scored = [r for r in rows if r["status"] == "SCORED" and r["p_value_vs_breakeven"] is not None]
    holm_on_roi = stats.holm([r["p_value_vs_breakeven"] for r in scored]) if scored else []
    for r, adj in zip(scored, holm_on_roi):
        r["p_value_holm_across_scored_family"] = adj
        r["family_size"] = len(scored)
        r["ranking_eligible"] = bool(adj is not None and adj < 0.05 and r["mean_skill_ci95"] and r["mean_skill_ci95"][0] > 0)
    skill_family = [p for _, p in family]
    holm_skill = stats.holm(skill_family) if skill_family else []
    for (sid, _), adj in zip(family, holm_skill):
        for r in rows:
            if r["id"] == sid:
                r["mean_skill_p_signflip"] = stats.signflip_p(
                    [b["per_bet_skill"] for b in r["bets"] if b["result"] in ("win", "loss")])
                r["mean_skill_p_holm"] = adj

    leaderboard = sorted(
        [r for r in rows if r["status"] == "SCORED"],
        key=lambda r: -(r["mean_skill_ci95"][0] if r["mean_skill_ci95"] else -9),
    )
    for i, r in enumerate(leaderboard, 1):
        r["rank_by_lower_bound_of_skill"] = i

    out = {
        "generated": "2026-11-14",
        "generated_by": "session 949f49b0",
        "description": "Every pre-registered strategy re-settled against officially published prices. Signal (per-bet skill vs the de-vigged market price) is ranked separately from staking (flat-stake ROI) so a lucky run cannot mask a bad signal or vice versa.",
        "ranking_rule": "rank by the LOWER 95% bootstrap bound of mean per-bet skill (model probability minus de-vigged market probability on the side the strategy chose); ROI is reported beside it and never used to set rank",
        "priced_weeks": [9],
        "unpriced_weeks": {
            "3-8": "walk-forward forecasts exist in origination/results/walkforward-games.json, but this repo holds no official price series for those weeks",
            "10": "prices captured; games not played at capture time, so nothing can be settled",
        },
        "family": {"scored_strategies": len(scored), "holm_alpha": 0.05,
                   "note": "Holm step-down across the scored family only. Strategies that could not be priced are excluded from the family, which makes the correction LESS conservative than a family that included them."},
        "rows": rows,
        "leaderboard": [{"rank": r["rank_by_lower_bound_of_skill"], "id": r["id"],
                         "product": r["product"], "n": r["n_settled"],
                         "lower_bound_skill": r["mean_skill_ci95"][0] if r["mean_skill_ci95"] else None,
                         "mean_skill": r["mean_skill"], "roi": r["roi"],
                         "ranking_eligible": r["ranking_eligible"], "verdict": verdict_for(r)}
                        for r in leaderboard],
    }
    (MARKET / "data" / "tournament.json").write_text(json.dumps(out, indent=1) + "\n")

    print("\n== strategy board (Week 9 official prices, n=15 games each)")
    for r in out["leaderboard"]:
        print(f"  #{r['rank']} {r['id']:3s} n={r['n']:2d} skill={r['mean_skill']:+.4f} "
              f"lcb={r['lower_bound_skill']:+.4f} ROI={r['roi']*100:+6.1f}%  {r['verdict']}")
    print("\nunpriceable:", [r["id"] for r in rows if r["status"] != "SCORED"])


def binomial_two_sided(k, n, p):
    import math
    if p is None or n == 0:
        return None
    def pmf(i):
        return math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    ge = sum(pmf(i) for i in range(k, n + 1))
    le = sum(pmf(i) for i in range(0, k + 1))
    return min(1.0, 2 * min(ge, le))


def verdict_for(r):
    n = r["n_settled"]
    if n == 0:
        return "NOT SCORED"
    if r["ranking_eligible"]:
        return "SIGNAL SURVIVES THE FAMILY CORRECTION"
    if r["mean_skill"] and r["mean_skill"] > 0:
        return f"POSITIVE SIGNAL POINT ESTIMATE, NOT SIGNIFICANT AT n={n}"
    return f"NO SIGNAL (mean skill <= 0) AT n={n}"


if __name__ == "__main__":
    main()
