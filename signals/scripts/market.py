#!/usr/bin/env python3
"""
SB3 — market-relative skill: what price would erase the signal?

The repository has repeatedly been asked to publish "the model line, the market line and the
difference". The honest version of that request is this file, because no official NFL source
publishes a market line (probes P5, P6, P12). So instead of inventing one, we compute the
MARKET LINE THAT WOULD MAKE THE SIGNAL WORTH ZERO. That number is a property of the model, not
of any book, and it can be computed exactly from official results.

Three things are produced:

  1. fair_line_vs_market_breakeven
     For each Week 11 game we originate a fair spread and total from the verified W1-W10 game log.
     We then state the break-even market number: the number at which a bet on our own fair line
     wins exactly often enough to pay the assumed price. Everything between the fair number and
     that market number is the cushion the model needs. If the market is inside the cushion, no
     bet exists even if the model is right.

  2. closing_line_that_erases_skill
     For each spread rule, the average absolute closing error that a market would need to have
     for the rule's measured hit rate to be worth exactly zero at the assumed price. If the market
     is at least that good, the edge is gone by definition.

  3. vig_arithmetic
     Why a 60% spread forecast is worth nothing at -110, with the exact numbers. This is the
     single most important table for a staking decision in this repository.

No price is used. The -110 is an assumption, restated in every row. Nothing here is a quote.

Run: python3 signals/scripts/market.py
"""
import json, math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
OUT = R / "signals" / "data"

GAMES = json.loads((R / "origination/data/games-2026-w1-w9.json").read_text())["games"]
PRED = json.loads((R / "origination/results/walkforward-games-w10.json").read_text())["games"]
LADDER = json.loads((OUT / "baseline-ladder.json").read_text())

ASSUMED_PRICE = -110
DECIMAL = 1 + 100 / 110
BREAKEVEN = 1 / DECIMAL

# Week 11 slate, transcribed from https://www.nfl.com/schedules/2026/by-week/week-11 on 2026-11-14.
# Neutral site only where the page prints a Mexico City badge (MIN at SF).
SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
W11 = [
    ("IND", "HOU", "Nov 19", "PRIME", False, "https://www.nfl.com/games/colts-at-texans-2026-reg-11"),
    ("MIA", "BUF", "Nov 22", "CBS", False, "https://www.nfl.com/games/dolphins-at-bills-2026-reg-11"),
    ("BAL", "CAR", "Nov 22", "FOX", False, "https://www.nfl.com/games/ravens-at-panthers-2026-reg-11"),
    ("NO", "CHI", "Nov 22", "FOX", False, "https://www.nfl.com/games/saints-at-bears-2026-reg-11"),
    ("TEN", "DAL", "Nov 22", "FOX", False, "https://www.nfl.com/games/titans-at-cowboys-2026-reg-11"),
    ("TB", "DET", "Nov 22", "FOX", False, "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"),
    ("AZ", "KC", "Nov 22", "CBS", False, "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11"),
    ("PIT", "PHI", "Nov 22", "CBS", False, "https://www.nfl.com/games/steelers-at-eagles-2026-reg-11"),
    ("NYJ", "LAC", "Nov 22", "FOX", False, "https://www.nfl.com/games/jets-at-chargers-2026-reg-11"),
    ("JAX", "NYG", "Nov 22", "CBS", False, "https://www.nfl.com/games/jaguars-at-giants-2026-reg-11"),
    ("LV", "DEN", "Nov 22", "CBS", False, "https://www.nfl.com/games/raiders-at-broncos-2026-reg-11"),
    ("MIN", "SF", "Nov 22", "NBC", True, "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"),
    ("CIN", "WAS", "Nov 23", "ESPN", False, "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11"),
]
# WAS at NYG played 2026-11-12, final 24-21 (probe P11). It is in the game log and is NOT re-originated.
PLAYED_W11 = []


def mean(x):
    return sum(x) / len(x)


def sd(x):
    m = mean(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


def phi_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# ---------------------------------------------------------------- ratings from official results only
def build(games, teams):
    """Ridge-free, transparent ratings: shrunk points-for/against per game with the league mean.

    Deliberately simple and fully auditable: every rating is a sum over official final scores.
    """
    pf, pa, gp = {}, {}, {}
    for g in games:
        for t, f, a_ in ((g["home"], g["home_score"], g["away_score"]),
                         (g["away"], g["away_score"], g["home_score"])):
            pf[t] = pf.get(t, 0) + f
            pa[t] = pa.get(t, 0) + a_
            gp[t] = gp.get(t, 0) + 1
    league_ppg = sum(pf.values()) / sum(gp.values())
    # empirical-Bayes style shrink toward the league mean, k = 3 games of prior weight
    k = 3.0
    off = {t: (pf[t] + k * league_ppg) / (gp[t] + k) for t in pf}
    deff = {t: (pa[t] + k * league_ppg) / (gp[t] + k) for t in pa}
    hfa = mean([g["home_margin"] for g in games if not g["international"]])
    resid_m = [g["home_margin"] - ((off[g["home"]] - deff[g["home"]]) - (off[g["away"]] - deff[g["away"]])
                                   + (0 if g["international"] else hfa)) for g in games]
    resid_t = [g["total"] - (off[g["home"]] + deff[g["away"]] + off[g["away"]] + deff[g["home"]]) / 2
               for g in games]
    return {
        "league_ppg": league_ppg, "hfa": hfa, "k": k,
        "off": off, "def": deff, "games": gp,
        "sigma_margin": sd(resid_m), "sigma_total": sd(resid_t),
        "resid_m": resid_m, "resid_t": resid_t,
    }


def originate(model, away, home, neutral):
    m = (model["off"][home] - model["def"][home]) - (model["off"][away] - model["def"][away])
    if not neutral:
        m += model["hfa"]
    t = (model["off"][home] + model["def"][away] + model["off"][away] + model["def"][home]) / 2
    p_home = phi_cdf(m / model["sigma_margin"])
    return m, t, p_home


def american(p):
    """Fair (no-vig) American price for a probability. Published as a derived fair number only."""
    p = min(max(p, 1e-6), 1 - 1e-6)
    if p >= 0.5:
        return round(-100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def main():
    model = build(GAMES, sorted({g["home"] for g in GAMES} | {g["away"] for g in GAMES}))

    # ---------------- 1. Week 11 fair lines and the break-even market distance
    # IMPORTANT CONCEPT, stated because it is easy to get wrong: the probability that the HOME TEAM
    # WINS is not the probability that a bet COVERS. A bet placed at our own fair number covers with
    # probability 1/2. It reaches the break-even probability only when the market number sits a
    # certain distance away from our fair number. That distance is z(breakeven) * sigma, and it does
    # not depend on the game at all — only on the assumed price and the league's scoring spread.
    lo, hi = -6.0, 6.0
    for _ in range(300):
        mid = (lo + hi) / 2
        if phi_cdf(mid) < BREAKEVEN:
            lo = mid
        else:
            hi = mid
    z_be = (lo + hi) / 2

    lines = []
    for away, home, day, net, neutral, url in W11:
        m, t, p = originate(model, away, home, neutral)
        cushion = z_be * model["sigma_margin"]
        cushion_total = z_be * model["sigma_total"]
        spread_text = (f"{home} -{abs(m):.1f}" if m < 0 else f"{away} -{m:.1f}") if m != 0 else "pick'em"
        lines.append({
            "game": f"{away} at {home}",
            "away": away, "home": home,
            "day_rendered": day, "network": net, "neutral_site": neutral,
            "originated_at": "2026-11-14",
            "fair_spread_home": round(m, 4),
            "fair_spread_text": spread_text,
            "fair_total": round(t, 4),
            "fair_ml_home": american(p),
            "fair_ml_away": american(1 - p),
            "model_win_prob_home": round(p, 6),
            "sigma_margin_used": round(model["sigma_margin"], 4),
            "market_spread": None,
            "market_total": None,
            "market_price": None,
            "difference_fair_minus_market": None,
            "breakeven_market_distance_spread_points": round(cushion, 4),
            "breakeven_market_distance_total_points": round(cushion_total, 4),
            "what_the_distance_means": (
                f"A -110 bet only breaks even once our fair number is at least {cushion:.2f} points "
                f"better (for a side) or {cushion_total:.2f} points better (for a total) than the "
                f"number actually available. This distance is the same for every game: it is a "
                f"property of the price and the league's scoring spread, not of this matchup. It is "
                f"not a profit target and it is not evidence of an edge."),
            "status": "UNVALIDATED — no market comparison exists, so no edge is claimed",
            "unavailable_reason": "No official NFL source publishes a spread, total or price "
                                  "(probes P5, P6, P12). The market and difference columns are blank "
                                  "by policy, not by omission.",
            "source_url": SCHED_URL,
            "game_url": url,
        })

    # ---------------- 2. the line advantage each measured hit rate implies
    # A bet wins with probability Phi(advantage / sigma), where sigma is the SD of the outcome
    # around a true line. Inverting that gives the average line advantage a rule must actually have
    # to produce the hit rate it produced. That advantage is then compared with the model's own
    # measured error, which bounds how much of the hit rate can be real.
    def z_of(prob):
        lo, hi = -6.0, 6.0
        for _ in range(300):
            mid = (lo + hi) / 2
            if phi_cdf(mid) < prob:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    own_mae = {a["id"]: a["value"] for a in LADDER["ladder"] if a["kind"] in ("spread", "total")}
    erase = []
    for arm in LADDER["ladder"]:
        b = arm["betting"]
        if not b["n_bets"] or b["hit_rate"] is None or arm["kind"] == "moneyline":
            continue
        hr = b["hit_rate"]
        sigma = model["sigma_margin"] if arm["kind"] == "spread" else model["sigma_total"]
        implied_adv = z_of(hr) * sigma if hr > 0.5 else 0.0
        model_err = own_mae.get(arm["id"])
        erase.append({
            "arm": arm["id"], "label": arm["label"], "kind": arm["kind"],
            "measured_hit_rate": hr, "n_bets": b["n_bets"],
            "measured_hit_rate_ci95": b["hit_rate_ci95"],
            "measured_roi_at_assumed_price": b["roi_per_unit_assumed_price"],
            "implied_line_advantage_points": round(implied_adv, 4),
            "models_own_mean_absolute_error_points": model_err,
            "market_error_that_would_be_required_points":
                round(model_err + implied_adv, 4) if model_err is not None else None,
            "interpretation": (
                f"To win {hr * 100:.2f}% of these bets at -110, this rule's number must have been "
                f"on average {implied_adv:.2f} points closer to the truth than the number it was "
                f"bet against. Since the rule's own mean absolute error is {model_err:.2f} points, "
                f"the opposing number would have had to be about "
                f"{(model_err + implied_adv):.2f} points off. The market's real accuracy is NOT "
                f"published in any official source, so this is the target the operator must obtain "
                f"a price series to test — not a comparison and not a claim."
                if model_err is not None else
                "Not applicable."),
            "uses_future_games": arm.get("uses_future_games", False),
        })

    # ---------------- 3. vig arithmetic — the decisive table
    vig = []
    for hr in (0.50, 0.52, 0.524, 0.55, 0.575, 0.588, 0.60, 0.6214):
        for price in (-110, -105, 100, 110):
            dec = 1 + (100 / abs(price) if price < 0 else price / 100)
            be = 1 / dec
            pnl = hr * (dec - 1) - (1 - hr)
            vig.append({
                "hit_rate": hr,
                "assumed_price": price,
                "decimal": round(dec, 6),
                "breakeven_hit_rate": round(be, 6),
                "roi_per_unit": round(pnl, 6),
                "survives": hr > be,
            })

    # book margin the operator must beat, stated explicitly
    two_way = (1 / DECIMAL) * 2
    book = {
        "assumed_price": ASSUMED_PRICE,
        "decimal": round(DECIMAL, 6),
        "breakeven_hit_rate": round(BREAKEVEN, 6),
        "two_way_overround_at_minus_110": round(two_way, 6),
        "book_hold_pct_at_minus_110": round((two_way - 1) * 100, 4),
        "consequence": (
            "A forecast must clear " + f"{BREAKEVEN * 100:.3f}% just to break even at an assumed "
            "-110. The repository's best measured spread hit rate (S1, 59.62% on 104 bets) has a "
            "95% interval whose lower bound is "
            + f"{next(a for a in LADDER['ladder'] if a['id'] == 'S1')['betting']['hit_rate_ci95'][0] * 100:.2f}%"
            + ". See market_verdict."),
    }

    s1 = next(a for a in LADDER["ladder"] if a["id"] == "S1")["betting"]

    # Which arms have a hit-rate interval whose LOWER BOUND clears the break-even rate? This is the
    # only defensible promotion test available without a price, and it is computed rather than
    # asserted, because the answer is not what a first draft of this file assumed.
    clears = []
    for a in LADDER["ladder"]:
        b = a["betting"]
        lo = b["hit_rate_ci95"][0]
        if lo is None:
            continue
        clears.append({
            "arm": a["id"], "label": a["label"], "kind": a["kind"],
            "n_bets": b["n_bets"], "hit_rate": b["hit_rate"], "ci_low": lo,
            "breakeven": round(BREAKEVEN, 6),
            "gap_points": round((lo - BREAKEVEN) * 100, 4),
            "clears": lo > BREAKEVEN,
            "uses_future_games": a.get("uses_future_games", False),
            "is_a_registered_strategy": a["id"].startswith("S"),
        })
    winners = [c for c in clears if c["clears"]]

    verdict = {
        "best_signal_arm": "S1",
        "hit_rate": s1["hit_rate"],
        "ci95": s1["hit_rate_ci95"],
        "breakeven": round(BREAKEVEN, 6),
        "ci_low_clears_breakeven": s1["hit_rate_ci95"][0] > BREAKEVEN,
        "gap_ci_low_to_breakeven_points": round((s1["hit_rate_ci95"][0] - BREAKEVEN) * 100, 4),
        "arms_whose_interval_clears_breakeven": [c["arm"] for c in winners],
        "count_of_arms_clearing": len(winners),
        "verdict": (
            "NO ARM IS PROMOTED. " + str(len(winners)) + " of the " + str(len(clears)) + " arms that placed any bet have a "
            "hit-rate interval whose lower bound clears the " + f"{BREAKEVEN * 100:.2f}%" + " break-even "
            "rate: " + ", ".join(f"{c['arm']} ({c['hit_rate'] * 100:.2f}%, low bound {c['ci_low'] * 100:.2f}%)"
                                 for c in winners) + ". Neither is promotable. "
            + " ".join(
                f"{c['arm']} is {'a naive rule that is not a registered strategy' if not c['is_a_registered_strategy'] else 'a registered strategy'}"
                f" whose interval clears by only {c['gap_points']:.2f} percentage points, out of "
                f"{len(clears)} arms tested (B01 is excluded because it placed none); at that margin a "
                f"family correction removes it."
                for c in winners)
            + " The point is not that these are bad numbers. It is that a 0.1-to-1.0 point margin over "
              "break-even, on about 100 bets, selected from nineteen arms, is indistinguishable from luck, and "
              "the repository would be manufacturing a signal by promoting it. What promotion requires "
              "is a price and an out-of-sample season, not a slightly higher hit rate."),
    }

    out = {
        "generated": "2026-11-14",
        "session": "8ef7f6bb",
        "title": "Market-relative skill — what closing number would erase each signal",
        "no_market_data_statement": (
            "No spread, total or price is imported from any source. Every 'market' figure in this "
            "file is either (a) blank because no official source publishes it, or (b) a "
            "breakeven threshold derived from the model's own error distribution and the assumed "
            "price. There is no market comparison anywhere in this repository, and this file does "
            "not create one."),
        "assumed_price": ASSUMED_PRICE,
        "assumed_price_is_a_quote": False,
        "model": {
            "method": "shrunk points-for/against per game (k=3 prior games at the league mean), "
                      "plus the league home edge measured from non-international games",
            "train_rows": len(GAMES),
            "sigma_margin": round(model["sigma_margin"], 4),
            "sigma_total": round(model["sigma_total"], 4),
            "league_ppg": round(model["league_ppg"], 4),
            "home_edge": round(model["hfa"], 4),
            "source_url": "https://www.nfl.com/scores/2026/week-1 ... /week-10",
        },
        "week11_fair_lines": lines,
        "line_advantage_implied_by_hit_rate": erase,
        "vig_arithmetic": vig,
        "book_arithmetic": book,
        "market_verdict": verdict,
        "interval_vs_breakeven": clears,
        "caveats": [
            "The Week 11 numbers are originated before those games are played. They are "
            "predictions, not results, and they carry no market comparison.",
            "Sigma is a single league-wide constant. Prior sessions flagged the same choice "
            "(LF-03); it is inherited, not re-litigated here.",
            "The break-even cushion assumes our error is unbiased and independent of the market's. "
            "If the model is systematically biased, the cushion is optimistic. There is no way to "
            "test that without a price series.",
            "Nothing in this file authorises a stake. It prices the hurdle, and states that the "
            "hurdle has not been cleared on evidence.",
        ],
    }
    (OUT / "market-relative.json").write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT / "market-relative.json")
    for ln in lines:
        print(f"  {ln['game']:12s} fair {ln['fair_spread_text']:14s} total {ln['fair_total']:6.2f} "
              f"distance {ln['breakeven_market_distance_spread_points']:5.2f} pts")
    print("S1 verdict:", verdict["verdict"][:90])


if __name__ == "__main__":
    main()
