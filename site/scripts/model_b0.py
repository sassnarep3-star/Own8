#!/usr/bin/env python3
"""Shadow baseline B0 (singles only): originate, grade, and check.

Method (identical to the frozen W10 method in requirements/results/week10-lines.json):
  H (home projected points) = (home PF/G + away PA/G) / 2
  A (away projected points) = (away PF/G + home PA/G) / 2
  margin = H - A (home minus away), total = H + A
  p_home = Phi(margin / sigma), sigma = 13.1768 (frozen B0 margin SD)
  No venue term. Munich gets none.

NOTE: the written method string in requirements/results/week10-lines.json reads
"away projection = (away PF/G + away PA/G)/2". The stored numbers reproduce only
with the symmetric form above; check_b0() below proves it on all 13 stored W10 games.

Inputs: nfl.com standings (site/data/standings-2026-11-17.json), repo log W1-W9
(origination/data/games-2026-w1-w9.json), nfl.com Week 10 finals
(site/data/week10-results.json), W10 market prices (market/data/raw/official-prices-w10.json).
Pure standard library. Deterministic (bootstrap seeded).
"""
import json, math, random, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SIGMA = 13.1768  # frozen B0 margin SD (requirements/results/week10-lines.json, sigma_margin)


def P(*parts):
    return os.path.join(ROOT, *parts)


def load(p):
    with open(P(p), encoding="utf-8") as f:
        return json.load(f)


def Phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def b0(home_pf_g, home_pa_g, away_pf_g, away_pa_g):
    H = (home_pf_g + away_pa_g) / 2.0
    A = (away_pf_g + home_pa_g) / 2.0
    m = H - A
    return dict(H=H, A=A, margin=m, total=H + A, p_home=Phi(m / SIGMA))


def implied(ml):
    ml = float(ml)
    return (-ml) / (-ml + 100.0) if ml < 0 else 100.0 / (ml + 100.0)


def devig_home(home_ml, away_ml):
    ph, pa = implied(home_ml), implied(away_ml)
    return ph / (ph + pa)


def pre_w10_totals():
    log = load("origination/data/games-2026-w1-w9.json")["games"]
    t = {}
    for g in log:
        for side, pts, opp in (("away", g["away_score"], g["home_score"]), ("home", g["home_score"], g["away_score"])):
            tm = g[side]
            r = t.setdefault(tm, dict(G=0, PF=0, PA=0))
            r["G"] += 1; r["PF"] += pts; r["PA"] += opp
    return t


def standings_totals():
    rows = load("site/data/standings-2026-11-17.json")["rows"]
    return {r["team"]: dict(G=r["G"], PF=r["PF"], PA=r["PA"]) for r in rows}


def check_b0(pre):
    """Reproduce the stored W10 B0 values from the W1-W9 log. Returns list of mismatches."""
    stored = load("requirements/results/week10-lines.json")["games"]
    bad = []
    for g in stored:
        a, h = g["away"], g["home"]
        if a not in pre or h not in pre:
            continue
        ha = pre[h]; aa = pre[a]
        r = b0(ha["PF"] / ha["G"], ha["PA"] / ha["G"], aa["PF"] / aa["G"], aa["PA"] / aa["G"])
        dm = abs(r["margin"] - g["fair_home_margin_B0"]); dt = abs(r["total"] - g["fair_total_B0"])
        dp = abs(r["p_home"] - g["p_home_win_normal"])
        if dm > 0.0006 or dt > 0.0006 or dp > 0.0006:
            bad.append(dict(game=f"{a}@{h}", margin=(round(r["margin"], 4), g["fair_home_margin_B0"]),
                            total=(round(r["total"], 4), g["fair_total_B0"]), p=(round(r["p_home"], 4), g["p_home_win_normal"])))
    return bad, len(stored)


def bootstrap_ci(diffs, reps=10000, seed=20261117):
    rnd = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(reps):
        s = [diffs[rnd.randrange(n)] for _ in range(n)]
        means.append(sum(s) / n)
    means.sort()
    return means[int(0.025 * reps)], means[int(0.975 * reps)]


def grade_w10(pre):
    stored = load("requirements/results/week10-lines.json")["games"]
    market = {(g["away"], g["home"]): g for g in load("market/data/raw/official-prices-w10.json")["games"]}
    finals = {(g["away"], g["home"]): g for g in load("site/data/week10-results.json")["finals"]}
    rows = []
    for g in stored:
        key = (g["away"], g["home"])
        if key not in finals:
            rows.append(dict(game=f"{key[0]}@{key[1]}", status="NOT GRADED (no verified final)"))
            continue
        f = finals[key]; m = market[key]
        actual_margin = f["home_score"] - f["away_score"]
        actual_total = f["home_score"] + f["away_score"]
        y = 1 if actual_margin > 0 else 0
        mkt_margin = -m["spread_home"]
        p_mkt = devig_home(m["home_ml"], m["away_ml"])
        rows.append(dict(
            game=f"{key[0]}@{key[1]}", status="GRADED", away=key[0], home=key[1],
            away_score=f["away_score"], home_score=f["home_score"],
            actual_margin=actual_margin, actual_total=actual_total,
            model_margin=round(g["fair_home_margin_B0"], 2), market_margin=mkt_margin,
            model_total=round(g["fair_total_B0"], 2), market_total=m["total"],
            model_p_home=round(g["p_home_win_normal"], 4), market_p_home=round(p_mkt, 4),
            home_won=y,
            err_model_margin=abs(g["fair_home_margin_B0"] - actual_margin),
            err_market_margin=abs(mkt_margin - actual_margin),
            err_model_total=abs(g["fair_total_B0"] - actual_total),
            err_market_total=abs(m["total"] - actual_total),
            brier_model=(g["p_home_win_normal"] - y) ** 2,
            brier_market=(p_mkt - y) ** 2,
            brier_coinflip=(0.5 - y) ** 2,
            diff_margin_model_minus_market=round(g["fair_home_margin_B0"] - mkt_margin, 2),
            source_final=f["game_url"], source_market=m["source_url"],
        ))
    graded = [r for r in rows if r["status"] == "GRADED"]
    n = len(graded)
    mae = lambda k: sum(r[k] for r in graded) / n
    bm = sum(r["brier_model"] for r in graded) / n
    bk = sum(r["brier_market"] for r in graded) / n
    bc = sum(r["brier_coinflip"] for r in graded) / n
    dm_diffs = [r["err_model_margin"] - r["err_market_margin"] for r in graded]
    dt_diffs = [r["err_model_total"] - r["err_market_total"] for r in graded]
    db_diffs = [r["brier_model"] - r["brier_market"] for r in graded]
    summary = dict(
        n_graded=n, n_pending=len(rows) - n,
        spread_mae_model=round(mae("err_model_margin"), 3), spread_mae_market=round(mae("err_market_margin"), 3),
        spread_mae_diff_ci95=[round(x, 3) for x in bootstrap_ci(dm_diffs)],
        total_mae_model=round(mae("err_model_total"), 3), total_mae_market=round(mae("err_market_total"), 3),
        total_mae_diff_ci95=[round(x, 3) for x in bootstrap_ci(dt_diffs)],
        ml_brier_model=round(bm, 4), ml_brier_market=round(bk, 4), ml_brier_coinflip_control=round(bc, 4),
        ml_brier_skill_vs_market=round(1 - bm / bk, 4),
        ml_brier_diff_ci95=[round(x, 4) for x in bootstrap_ci(db_diffs)],
        home_win_rate=round(sum(r["home_won"] for r in graded) / n, 4),
    )
    return rows, summary


def originate_w11(stand):
    sched = load("site/data/week11-schedule.json")["games"]
    out = []
    for g in sched:
        a, h = g["away"], g["home"]
        ta, th = stand[a], stand[h]
        r = b0(th["PF"] / th["G"], th["PA"] / th["G"], ta["PF"] / ta["G"], ta["PA"] / ta["G"])
        out.append(dict(game=f"{a}@{h}", away=a, home=h, kickoff=g["kickoff_et"], network=g["network"],
                        H_home=round(r["H"], 2), A_away=round(r["A"], 2),
                        fair_home_margin=round(r["margin"], 2), fair_handicap_home=round(-r["margin"], 2),
                        fair_total=round(r["total"], 2), p_home=round(r["p_home"], 4),
                        market_spread_home=None, market_total=None, market_ml_home=None,
                        difference_column="BLANK (no verified market capture for Week 11 in this session)",
                        source_schedule=g["source_url"]))
    return out


if __name__ == "__main__":
    pre = pre_w10_totals()
    bad, n = check_b0(pre)
    print(f"check_b0: reproduced {n - len(bad)}/{n} stored W10 B0 games (|diff| <= 0.0006)")
    for b in bad:
        print("  MISMATCH", b)
    rows, summ = grade_w10(pre)
    out_w10 = dict(
        method="B0 (see model_b0.py). Graded only against verified nfl.com finals and the nfl.com picks-article W10 prices.",
        pre_registered_in="requirements/results/week10-lines.json (originated_at 2026-11-14)",
        check_reproduction=dict(games_checked=n, mismatches=bad),
        summary=summ, rows=rows,
        caveat="n is 12 settled games. Confidence intervals are bootstrap intervals on 12 games and are NOT evidence of skill or of its absence.")
    with open(P("site/data/b0-w10-grading.json"), "w", encoding="utf-8") as f:
        json.dump(out_w10, f, indent=1)
    print(json.dumps(summ, indent=1))
    if "--originate-w11" in sys.argv:
        stand = standings_totals()
        w11 = originate_w11(stand)
        with open(P("site/data/b0-w11-lines.json"), "w", encoding="utf-8") as f:
            json.dump(dict(
                method="B0 frozen before Week 11 kickoff (Thu 2026-11-19 8:15 PM ET). Inputs: nfl.com standings read 2026-11-17 (PF/G, PA/G through Week 10 finals). MNF LAC@BAL excluded (not final on nfl.com as read).",
                sigma_margin=SIGMA, prereg_rule="Do not edit these numbers after commit; any change requires a new versioned file (B0 v2).",
                games=w11), f, indent=1)
        print(f"originated {len(w11)} Week 11 B0 lines")
