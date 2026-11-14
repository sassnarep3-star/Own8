#!/usr/bin/env python3
"""
SB2 — baseline ladder + luck decomposition.

Reads ONLY committed, already-verified artifacts:
  origination/data/games-2026-w1-w9.json      (136 official final scores)
  origination/results/walkforward-games-w10.json (walk-forward predictions, weeks 3-9)

and answers three questions the repository has never answered in one place:

  1. Skill against what?  Every strategy is scored against FIVE do-nothing rules on exactly
     the same games, not against one hand-picked benchmark.

  2. Would it have paid?  Each strategy's picks are staked flat at an EXPLICITLY ASSUMED
     -110 price (decimal 1.90909...). No market quote is used or claimed. The assumed price is
     an assumption and is labelled as one everywhere it appears. This turns a loss metric
     into the only thing that matters for a staking decision: hit rate vs the break-even rate.

  3. Is the result distinguishable from luck?  For every hit rate we publish the exact binomial
     probability that a coin-flipper does at least as well, and the sample size that would be
     needed to tell a real edge of that size from noise at 80% power.

Nothing here is fitted, tuned or selected. Every number is a closed-form function of the
committed inputs. Run:  python3 signals/scripts/ladder.py
"""
import json, math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
OUT = R / "signals" / "data"

GAMES = json.loads((R / "origination/data/games-2026-w1-w9.json").read_text())
PRED = json.loads((R / "origination/results/walkforward-games-w10.json").read_text())
W10 = json.loads((R / "origination/results/w10-lines.json").read_text())

GAMES_URL = "https://www.nfl.com/scores/2026/week-{w}"
ASSUMED_PRICE = -110
DECIMAL = 1 + 100 / 110          # 1.909090..., what -110 pays on a win
BREAKEVEN = 1 / DECIMAL          # 0.523809..., hit rate needed to break even at -110
PUSH_NOTE = "pushes are excluded from the denominator and returned, not counted as wins"


# ---------------------------------------------------------------- small statistics
def mean(x):
    return sum(x) / len(x) if x else float("nan")


def sd(x):
    m = mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1)) if len(x) > 1 else float("nan")


def wilson(wins, n, z=1.959963984540054):
    """95% Wilson score interval for a proportion. Better than normal approx at small n."""
    if n == 0:
        return [None, None]
    p = wins / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 6), round(min(1.0, c + h), 6)]


def binom_p_at_least(wins, n, p0=0.5):
    """P(X >= wins) under n fair coin flips. Exact, one-sided."""
    if n == 0:
        return None
    return float(sum(math.comb(n, k) * p0 ** k * (1 - p0) ** (n - k) for k in range(wins, n + 1)))


def n_for_power(p1, p0=0.5, power=0.80, alpha=0.05):
    """
    Games needed to detect a true win rate p1 against p0 at the given power, one-sided.
    Standard normal approximation; published as a planning figure, not a proof.
    """
    if p1 <= p0:
        return None
    z_a = 1.6448536269514722                 # one-sided 0.05
    z_b = 0.8416212335729143                 # 80% power
    pbar = (p0 + p1) / 2
    num = (z_a * math.sqrt(2 * pbar * (1 - pbar)) + z_b * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
    return int(math.ceil(num / (p1 - p0) ** 2))


# ---------------------------------------------------------------- staking at an assumed price
def stake(picks, labels, url_by_game, day=None):
    """
    picks: list of +1 (won), -1 (lost), 0 (push/void). Flat 1-unit stake, assumed -110.
    Flat staking means each game is an independent single bet, so same-week bets are only
    correlated with each other, not with themselves. The DAY-level record is therefore
    published as well: a slate that is 9-for-13 still has to survive a bad Sunday.
    """
    bets = [(p, l, u, d) for p, l, u, d in zip(picks, labels, url_by_game, day or [None] * len(picks)) if p != 0]
    n = len(bets)
    wins = sum(1 for p, _, _, _ in bets if p > 0)
    losses = n - wins
    pushes = len(picks) - n
    pnl = wins * (DECIMAL - 1) - losses
    by_day = {}
    for p, _, _, d in bets:
        d = d or "unknown"
        w, l = by_day.get(d, (0, 0))
        by_day[d] = (w + (1 if p > 0 else 0), l + (1 if p < 0 else 0))
    return {
        "n_bets": n,
        "pushes": pushes,
        "wins": wins,
        "losses": losses,
        "hit_rate": round(wins / n, 6) if n else None,
        "hit_rate_ci95": wilson(wins, n),
        "assumed_price": ASSUMED_PRICE,
        "breakeven_hit_rate": round(BREAKEVEN, 6),
        "roi_per_unit_assumed_price": round(pnl / n, 6) if n else None,
        "net_units_assumed_price": round(pnl, 4),
        "beats_breakeven_point": (wins / n > BREAKEVEN) if n else None,
        "beats_breakeven_ci_low": (wilson(wins, n)[0] > BREAKEVEN) if n else None,
        "p_value_vs_coin": round(binom_p_at_least(wins, n), 6) if n else None,
        "by_game_day": {d: {"wins": w, "losses": l,
                            "hit_rate": round(w / (w + l), 4) if w + l else None}
                        for d, (w, l) in sorted(by_day.items())},
        "worst_day_hit_rate": min([w / (w + l) for w, l in by_day.values() if w + l] or [None])
        if by_day else None,
    }


def abs_errors(preds, key, target):
    return [abs(r[target] - r[key]) for r in preds]


def ladder_row(sid, label, kind, preds, key, note, leakage=False, url_key="source_url"):
    """One arm of the ladder: accuracy metric + what it would have paid."""
    urls = [r.get(url_key) or r.get("source_url") for r in preds]
    days = [r.get("date") for r in preds]
    row = {"id": sid, "label": label, "kind": kind, "n": len(preds), "note": note,
           "uses_future_games": leakage,
           "eligible_as_a_rule": not leakage}
    if kind == "spread":
        ae = abs_errors(preds, key, "actual_margin")
        row["metric"] = "mean absolute error, home margin (points)"
        row["value"] = round(mean(ae), 4)
        row["rmse"] = round(math.sqrt(mean([e * e for e in ae])), 4)
        # pick the side the rule favours; a rule that predicts exactly 0 has no side -> no bet
        picks, labels, use = [], [], []
        for r, u in zip(preds, urls):
            m = r[key]
            if m == 0:
                continue
            home = m > 0
            margin_edge = (r["actual_margin"] - m) * (1 if home else -1)
            picks.append(1 if margin_edge > 0 else (-1 if margin_edge < 0 else 0))
            labels.append("home" if home else "away")
            use.append(u)
        row["betting"] = stake(picks, labels, use, days[:len(use)])
    elif kind == "total":
        ae = abs_errors(preds, key, "actual_total")
        row["metric"] = "mean absolute error, game total (points)"
        row["value"] = round(mean(ae), 4)
        row["rmse"] = round(math.sqrt(mean([e * e for e in ae])), 4)
        picks, labels, use = [], [], []
        for r, u in zip(preds, urls):
            t = r[key]
            d = r["actual_total"] - t
            picks.append(1 if d > 0 else (-1 if d < 0 else 0))
            labels.append("over")
            use.append(u)
        row["betting"] = stake(picks, labels, use, days[:len(use)])
    elif kind == "moneyline":
        # Brier against the realised home-win indicator; ties excluded from betting
        ys = [r["home_result"] for r in preds]
        row["metric"] = "Brier score, home win probability"
        row["value"] = round(mean([(r[key] - y) ** 2 for r, y in zip(preds, ys)]), 6)
        row["log_loss"] = round(mean([-(y * math.log(r[key]) + (1 - y) * math.log(1 - r[key]))
                                      for r, y in zip(preds, ys)]), 6)
        picks, labels, use = [], [], []
        for r, y, u in zip(preds, ys, urls):
            if y == 0.5:
                continue
            home = r[key] >= 0.5
            won = (y == 1) == home
            picks.append(1 if won else -1)
            labels.append("home" if home else "away")
            use.append(u)
        row["betting"] = stake(picks, labels, use, days[:len(use)])
        bet = row["betting"]
        row["betting"]["profit_requires_breakeven"] = (
            "at an assumed -110 the rule must win %.4f%% of these %d bets"
            % (BREAKEVEN * 100, bet["n_bets"]))
    return row


def main():
    preds = PRED["games"]
    games = GAMES["games"]
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------------- naive baselines, reconstructed walk-forward where they are not stored
    # B01 pick'em: margin 0 every game, total = league mean of everything played so far.
    # B02 league mean + home edge: these ARE origination's m_B / t_B / p_B.
    # B03 recent form: last 5 games per club before the week.
    # B04 always-home: bet the home side on every game, no magnitude.
    # B05 full-season oracle (DELIBERATE LEAKAGE): uses the whole season mean. Published only to
    #     show what leakage is worth; it is not a candidate rule.
    by_week = {}
    for g in games:
        by_week.setdefault(g["week"], []).append(g)

    def upto(w):
        return [g for g in games if g["week"] < w]

    def team_form(hist, team, n=5):
        rows = [g for g in hist if g["away"] == team or g["home"] == team][-n:]
        if not rows:
            return None
        pts, opp = [], []
        for g in rows:
            if g["home"] == team:
                pts.append(g["home_score"]); opp.append(g["away_score"])
            else:
                pts.append(g["away_score"]); opp.append(g["home_score"])
        return mean(pts), mean(opp), pts

    full = upto(12)                                        # every game in the file
    season_pf = {}
    season_pa = {}
    for g in full:
        for t, pf, pa in ((g["home"], g["home_score"], g["away_score"]),
                          (g["away"], g["away_score"], g["home_score"])):
            season_pf[t] = season_pf.get(t, 0) + pf
            season_pa[t] = season_pa.get(t, 0) + pa
    season_games = {}
    for g in full:
        season_games[g["home"]] = season_games.get(g["home"], 0) + 1
        season_games[g["away"]] = season_games.get(g["away"], 0) + 1
    oracle_margin = {}
    for t in season_pf:
        oracle_margin[t] = (season_pf[t] - season_pa[t]) / season_games[t]

    aug = []
    for r in preds:
        w = r["week"]
        hist = upto(w)
        non_neutral = [g["home_margin"] for g in hist if not g["international"]]
        hfa = mean(non_neutral) if non_neutral else 0.0
        league_total = mean([g["total"] for g in hist]) if hist else mean([g["total"] for g in games])
        fh, fa, _ = team_form(hist, r["home"]) or (league_total / 2, league_total / 2, [])
        ah, aa, _ = team_form(hist, r["away"]) or (league_total / 2, league_total / 2, [])
        recent_margin = ((fh + aa) / 2 - (fa + ah) / 2) + (0.0 if r["neutral"] else hfa)
        recent_total = ((fh + ah) / 2 + (fa + aa) / 2)
        aug.append(dict(r,
                        m_pickem=0.0,
                        t_pickem=league_total,
                        p_pickem=0.5,
                        m_recent=recent_margin,
                        t_recent=recent_total,
                        p_recent=min(max(0.5 + recent_margin / (2 * 13.86), 0.001), 0.999),
                        m_oracle=oracle_margin[r["home"]] - oracle_margin[r["away"]]
                                  + (0.0 if r["neutral"] else hfa),
                        m_alwayshome=1.0))
    preds_a = aug

    rows = []
    # spreads
    rows.append(ladder_row("B01", "Pick'em — every game predicted level, no team knowledge",
                           "spread", preds_a, "m_pickem",
                           "The floor. Any rule that cannot beat this has learned nothing."))
    rows.append(ladder_row("B02", "League mean + home edge — the repository's existing baseline",
                           "spread", preds_a, "m_B",
                           "Everything already published in origination/ is measured against this arm."))
    rows.append(ladder_row("B03", "Recent form — last 5 games, points for/against + home edge",
                           "spread", preds_a, "m_recent",
                           "Walk-forward, no leakage. Tests whether recency adds anything over B02."))
    rows.append(ladder_row("B04", "Always bet the home side (no magnitude)", "spread", preds_a,
                           "m_alwayshome",
                           "Pure side rule. Measures the home-field advantage as a betting rule."))
    rows.append(ladder_row("B05", "Full-season averages — DELIBERATE LEAKAGE, not a candidate",
                           "spread", preds_a, "m_oracle",
                           "Uses games the forecaster could not have seen. Published only as the "
                           "ceiling that leakage buys; never eligible, never promoted.", leakage=True))
    # totals
    rows.append(ladder_row("B06", "Pick'em total — league mean of every game already played",
                           "total", preds_a, "t_pickem",
                           "The floor for totals. A total rule must beat the running league average."))
    rows.append(ladder_row("B07", "League mean total — the repository's existing baseline",
                           "total", preds_a, "t_B",
                           "The existing originator's total benchmark."))
    rows.append(ladder_row("B08", "Recent form total — last 5 games, points for/against",
                           "total", preds_a, "t_recent", "Tests recency for totals."))
    # moneyline
    rows.append(ladder_row("B09", "Coin flip — 0.50 on every game", "moneyline", preds_a, "p_pickem",
                           "The floor for probabilities. Brier of a constant 0.5 is 0.25 by construction."))
    rows.append(ladder_row("B10", "League mean + home edge — existing baseline", "moneyline", preds_a,
                           "p_B", "The existing originator's probability benchmark."))
    rows.append(ladder_row("B11", "Recent form — last 5 games", "moneyline", preds_a, "p_recent",
                           "Recency as a probability rule."))

    # ---------------- the registered strategies, on the same ladder
    strat = []
    for sid, key, kind, label in (
            ("S1", "m_S1", "spread", "Ridge margin ratings + home edge (LOO-CV lambda)"),
            ("S2", "m_S2", "spread", "Offence/defence points ridge -> margin"),
            ("S3", "m_S3", "spread", "Naive season point differential per game (unshrunk)"),
            ("S4", "t_S4", "total", "Offence/defence points ridge -> total"),
            ("S5", "t_S5", "total", "Naive PF/PA per game averages -> total"),
            ("S6", "p_S6", "moneyline", "Win probability = Phi(S1 margin / LOO sigma)"),
            ("S7", "p_S7", "moneyline", "Win probability = Phi(S2 margin / LOO sigma)"),
            ("S8", "p_S8", "moneyline", "Win probability = Phi(S3 margin / S1 sigma)")):
        strat.append(ladder_row(sid, label, kind, preds_a, key,
                                "Registered strategy, scored on exactly the games above."))

    # ---------------- luck decomposition: how much of each result is noise
    def luck(rows_in):
        out = []
        for r in rows_in:
            b = r["betting"]
            if not b["n_bets"]:
                continue
            hr = b["hit_rate"]
            out.append({
                "id": r["id"], "label": r["label"], "kind": r["kind"],
                "n_bets": b["n_bets"],
                "hit_rate": hr,
                "hit_rate_ci95": b["hit_rate_ci95"],
                "coin_flip_p_value": b["p_value_vs_coin"],
                "beats_coin_at_5pct": (b["p_value_vs_coin"] is not None and b["p_value_vs_coin"] < 0.05),
                "edge_over_breakeven_points": round((hr - BREAKEVEN) * 100, 4),
                "edge_over_coin_points": round((hr - 0.5) * 100, 4),
                "games_needed_to_confirm_this_edge": n_for_power(hr),
                "sd_of_hit_rate_if_coin": round(math.sqrt(0.25 / b["n_bets"]), 6),
                "one_sd_window": [round(0.5 - math.sqrt(0.25 / b["n_bets"]), 6),
                                  round(0.5 + math.sqrt(0.25 / b["n_bets"]), 6)],
            })
        return out

    all_rows = rows + strat
    luck_rows = luck(all_rows)

    # ---------------- head-to-head: does the best strategy actually beat each naive rule?
    def find(sid):
        return next(r for r in all_rows if r["id"] == sid)

    h2h = []
    for sid in ("S1", "S2", "S3"):
        s = find(sid)
        for arm in ("B01", "B02", "B03", "B04"):
            b = find(arm)
            h2h.append({
                "kind": "spread", "strategy": sid, "vs": arm,
                "mae_strategy": s["value"], "mae_baseline": b["value"],
                "mae_improvement_points": round(b["value"] - s["value"], 4),
                "strategy_beats_arm": s["value"] < b["value"],
            })
    for sid in ("S4", "S5"):
        s = find(sid)
        for arm in ("B06", "B07", "B08"):
            b = find(arm)
            h2h.append({
                "kind": "total", "strategy": sid, "vs": arm,
                "mae_strategy": s["value"], "mae_baseline": b["value"],
                "mae_improvement_points": round(b["value"] - s["value"], 4),
                "strategy_beats_arm": s["value"] < b["value"],
            })
    for sid in ("S6", "S7", "S8"):
        s = find(sid)
        for arm in ("B09", "B10", "B11"):
            b = find(arm)
            h2h.append({
                "kind": "moneyline", "strategy": sid, "vs": arm,
                "brier_strategy": s["value"], "brier_baseline": b["value"],
                "brier_improvement": round(b["value"] - s["value"], 6),
                "strategy_beats_arm": s["value"] < b["value"],
            })

    # ---------------- summary the reader can act on
    best_spread = min((r for r in all_rows if r["kind"] == "spread" and r["id"] != "B05"),
                      key=lambda r: r["value"])
    profitable = [r["id"] for r in all_rows
                  if r.get("betting") and r["betting"].get("roi_per_unit_assumed_price") is not None
                  and r["betting"]["roi_per_unit_assumed_price"] > 0
                  and r.get("id") != "B05"]
    confirmed = [r["id"] for r in luck_rows if r["beats_coin_at_5pct"]]

    out = {
        "generated": "2026-11-14",
        "session": "8ef7f6bb",
        "title": "Baseline ladder — skill measured against do-nothing rules, and what luck could explain",
        "inputs": {
            "scores": "origination/data/games-2026-w1-w9.json (136 verified official rows)",
            "predictions": "origination/results/walkforward-games-w10.json (weeks 3-9, walk-forward)",
            "scores_source": GAMES_URL.format(w="1") + " ... week-9",
            "evaluation_weeks": PRED.get("description", "") and [3, 4, 5, 6, 7, 8, 9],
        },
        "assumed_price_block": {
            "assumed_price": ASSUMED_PRICE,
            "decimal_equivalent": round(DECIMAL, 6),
            "breakeven_hit_rate": round(BREAKEVEN, 6),
            "is_this_a_market_quote": False,
            "why_assumed": "No official NFL source publishes a price for any market (probe P5/P6/P12). "
                           "A standard -110 is therefore imposed as a stated assumption so that hit "
                           "rate can be compared with the rate required to break even. It is not a "
                           "quote, not a recommendation, and not evidence about any real sportsbook.",
            "push_note": PUSH_NOTE,
        },
        "ladder": all_rows,
        "luck_decomposition": luck_rows,
        "head_to_head": h2h,
        "findings": {
            "best_spread_rule": best_spread["id"],
            "best_spread_rule_label": best_spread["label"],
            "best_spread_mae": best_spread["value"],
            "leakage_ceiling_mae": find("B05")["value"],
            "leakage_is_worth_points": round(find("B05")["value"] - best_spread["value"], 4),
            "arms_profitable_at_assumed_price": profitable,
            "arms_whose_hit_rate_beats_coin_at_5pct": confirmed,
            "how_to_read": "An arm is not a signal because its ROI is positive. It is a signal only "
                           "if its hit-rate confidence interval clears the break-even rate. At these "
                           "sample sizes almost nothing can clear it, and that is the finding.",
        },
        "caveats": [
            "Every strategy here was selected from a family of 12 after the fact; a family-wise "
            "correction is required before any of it can be called a discovery (origination gate G5).",
            "The assumed -110 ignores pushes correctly at the bet level but ignores vig on pushes, "
            "line movement, limits and availability. It is a hurdle, not a simulation of a book.",
            "Week 10 finals did not exist at capture time (probe P11), so none of this is graded "
            "on the current slate.",
            "B05 uses future games on purpose. It is published as a leakage ceiling and is excluded "
            "from every 'best rule' and 'profitable' computation.",
        ],
    }
    (OUT / "baseline-ladder.json").write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT / "baseline-ladder.json")
    print("best legit spread rule:", best_spread["id"], best_spread["value"], "MAE")
    print("leakage ceiling:", find("B05")["value"], "MAE")
    for r in all_rows:
        b = r["betting"]
        print(f"  {r['id']:4s} {r['kind']:10s} n={b['n_bets']:3d} "
              f"hit={(b['hit_rate'] if b['hit_rate'] is not None else float('nan')):.4f} "
              f"roi={(b['roi_per_unit_assumed_price'] if b['roi_per_unit_assumed_price'] is not None else float('nan')):+.4f} "
              f"p_vs_coin={b['p_value_vs_coin']}")


if __name__ == "__main__":
    main()
