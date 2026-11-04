#!/usr/bin/env python3
"""O2/O3/O4 — Originate NFL lines from the verified official 2026 game log, validate them walk-forward,
rank strategies on a luck-resistant leaderboard, measure correlations for parlays / same-game parlays /
player-prop combos, decompose team records into skill vs luck, and publish Week 9 fair lines.

No sportsbook / market data is used anywhere: every input row comes from an official NFL source
(nfl.com scores, standings, schedule; Next Gen Stats). Strategies that would need market prices are
listed but cannot pass gate G8 and are never scored.

Pre-registered gates (fixed in code before any result was seen; identical for every strategy):
  G1 official data   every training/evaluation row is a verified official row (build_gamelog.py fail-closed)
  G2 no leakage      predictions for week w use only games from weeks < w (asserted at run time)
  G3 sample size     >= 80 games (singles) | >= 40 independent pairs (parlays) | >= 100 player-games (props)
  G4 skill           paired bootstrap 95% CI of mean(loss_model - loss_baseline) lies entirely below 0
  G5 multiplicity    Holm-adjusted one-sided sign-flip permutation p < 0.05 across the whole family
  G6 stability       mean loss improvement is positive in BOTH halves of the evaluation window
  G7 calibration     probability products only: expected calibration error (5 bins) <= 0.10
  G8 no market data  strategy can be priced and settled without sportsbook odds
Ranking ("leaderboard"): strategies passing ALL gates are ranked by the LOWER 95% bound of their skill score
(% loss reduction vs baseline), so a lucky point estimate cannot buy a medal.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats as S  # noqa: E402
from common import DATA, GAME_URL, SCORES_URL, dump_json  # noqa: E402

GRID = [0.5, 1, 2, 3, 5, 8, 12, 20, 30, 50, 80]
EVAL_WEEKS = [3, 4, 5, 6, 7, 8]
PROP_EVAL_WEEKS = [4, 5, 6, 7, 8]
NGS_URL = "https://nextgenstats.nfl.com/stats/passing/2026/REG/{w}"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-9"
GAMELOG = "origination/data/games-2026-w1-w8.json"


# ============================================================== data
def load_games():
    with open(os.path.join(DATA, "games-2026-w1-w8.json"), encoding="utf-8") as f:
        d = json.load(f)
    games = [g for g in d["games"] if g["verified"]]
    assert len(games) == len(d["games"]) == 121, "G1: unverified rows present"
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    assert len(teams) == 32
    return games, teams


def load_schedule():
    rows = []
    with open(os.path.join(DATA, "raw-schedule-w9-transcription.txt"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip() or line.startswith("BYE"):
                continue
            h, away, home, day, tm, net, slug = line.rstrip("\n").split("|")
            rows.append({"heading": h, "away": away, "home": home, "day": day, "time_as_rendered": tm,
                         "network": net, "neutral": h.startswith("International Game"),
                         "game_url": GAME_URL.format(slug=slug), "source_url": SCHEDULE_URL})
    assert len(rows) == 15
    return rows


def load_ngs():
    rows = []
    with open(os.path.join(DATA, "raw-ngs-passing-transcription.txt"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            w, name, team, att, yds, td, it = line.rstrip("\n").split("|")
            rows.append({"week": int(w), "player": name, "team": team, "att": int(att), "yds": int(yds),
                         "td": int(td), "int": int(it), "source_url": NGS_URL.format(w=w)})
    return rows


def outcome(g):
    m = g["home_score"] - g["away_score"]
    return m, g["home_score"] + g["away_score"], (1.0 if m > 0 else 0.0 if m < 0 else 0.5)


# ============================================================== models
class Baseline:
    """Knows nothing about teams: league home edge, league average total, league margin spread."""

    def fit(self, games, teams):
        nn = [outcome(g)[0] for g in games if not g["international"]]
        self.hfa = S.mean(nn)
        self.tot = S.mean([outcome(g)[1] for g in games])
        self.sigma = S.sd([outcome(g)[0] for g in games])
        return self

    def margin(self, h, a, neutral):
        return 0.0 if neutral else self.hfa

    def total(self, h, a, neutral):
        return self.tot


class MarginRidge:
    """S1: ridge-regularised margin ratings (Massey/SRS family) + home edge; lambda by exact LOO-CV."""

    def fit(self, games, teams):
        self.idx = {t: i for i, t in enumerate(teams)}
        p = len(teams) + 1
        X, y = [], []
        for g in games:
            x = [0.0] * p
            x[self.idx[g["home"]]], x[self.idx[g["away"]]] = 1.0, -1.0
            x[-1] = 0.0 if g["international"] else 1.0
            X.append(x)
            y.append(outcome(g)[0])
        best = S.loocv_ridge(X, y, [True] * len(teams) + [False], GRID)
        self.beta, self.lam, self.p_eff = best["beta"], best["lam"], best["p_eff"]
        self.sigma = math.sqrt(best["loo_mse"])  # out-of-sample (LOO) margin error -> win-prob scale
        self.hfa = self.beta[-1]
        self.tau = self.sigma / math.sqrt(self.lam)  # implied prior SD of team strength
        return self

    def rating(self, t):
        return self.beta[self.idx[t]]

    def margin(self, h, a, neutral):
        return self.rating(h) - self.rating(a) + (0.0 if neutral else self.hfa)


class PointsRidge:
    """S2/S4: offence/defence points model  pts = mu + off_team + def_opp +/- s/2 (home/away; 0 if neutral)."""

    def fit(self, games, teams):
        n = len(teams)
        self.n, self.idx = n, {t: i for i, t in enumerate(teams)}
        p = 2 + 2 * n
        X, y = [], []
        for g in games:
            loc = 0.0 if g["international"] else 0.5
            for team, opp, pts, sgn in ((g["home"], g["away"], g["home_score"], 1), (g["away"], g["home"], g["away_score"], -1)):
                x = [0.0] * p
                x[0], x[1] = 1.0, sgn * loc
                x[2 + self.idx[team]] = 1.0
                x[2 + n + self.idx[opp]] = 1.0
                X.append(x)
                y.append(pts)
        best = S.loocv_ridge(X, y, [False, False] + [True] * (2 * n), GRID)
        self.beta, self.lam, self.p_eff = best["beta"], best["lam"], best["p_eff"]
        infl = len(y) / max(len(y) - self.p_eff, 1.0)
        em, et = [], []
        for g in games:
            m, t, _ = outcome(g)
            em.append(m - self.margin(g["home"], g["away"], g["international"]))
            et.append(t - self.total(g["home"], g["away"], g["international"]))
        self.sigma_m = math.sqrt(S.mean([e * e for e in em]) * infl)
        self.sigma_t = math.sqrt(S.mean([e * e for e in et]) * infl)
        return self

    def off(self, t):
        return self.beta[2 + self.idx[t]]

    def dfn(self, t):
        return self.beta[2 + self.n + self.idx[t]]

    def pts(self, team, opp, loc):
        return self.beta[0] + self.off(team) + self.dfn(opp) + self.beta[1] * loc

    def margin(self, h, a, neutral):
        loc = 0.0 if neutral else 0.5
        return self.pts(h, a, loc) - self.pts(a, h, -loc)

    def total(self, h, a, neutral):
        loc = 0.0 if neutral else 0.5
        return self.pts(h, a, loc) + self.pts(a, h, -loc)


class TeamAverages:
    """S3/S5: naive unshrunk season averages (point differential per game; PF/PA per game)."""

    def fit(self, games, teams):
        acc = {t: [0, 0, 0] for t in teams}
        for g in games:
            for t, pf, pa in ((g["home"], g["home_score"], g["away_score"]), (g["away"], g["away_score"], g["home_score"])):
                acc[t][0] += pf
                acc[t][1] += pa
                acc[t][2] += 1
        self.pfg = {t: a[0] / a[2] for t, a in acc.items()}
        self.pag = {t: a[1] / a[2] for t, a in acc.items()}
        self.hfa = S.mean([outcome(g)[0] for g in games if not g["international"]])
        return self

    def margin(self, h, a, neutral):
        return (self.pfg[h] - self.pag[h]) - (self.pfg[a] - self.pag[a]) + (0.0 if neutral else self.hfa)

    def total(self, h, a, neutral):
        return ((self.pfg[h] + self.pag[a]) + (self.pfg[a] + self.pag[h])) / 2.0


def p_home(margin, sigma):
    return min(max(S.phi_cdf(margin / sigma), 0.001), 0.999)


# ============================================================== walk-forward
def walk_forward(games, teams):
    preds = []
    for w in EVAL_WEEKS:
        train = [g for g in games if g["week"] < w]
        test = [g for g in games if g["week"] == w]
        assert train and all(g["week"] < w for g in train), "G2 leakage"
        B = Baseline().fit(train, teams)
        M = MarginRidge().fit(train, teams)
        P = PointsRidge().fit(train, teams)
        A = TeamAverages().fit(train, teams)
        # in-sample residual correlation (margin vs total) available before week w, for SGP pricing
        rm = [outcome(g)[0] - M.margin(g["home"], g["away"], g["international"]) for g in train]
        rt = [outcome(g)[1] - P.total(g["home"], g["away"], g["international"]) for g in train]
        rho_train = max(min(S.pearson(rm, rt), 0.9), -0.9)
        for g in test:
            h, a, nt = g["home"], g["away"], g["international"]
            m, t, yw = outcome(g)
            r = {"week": w, "date": g["date"], "away": a, "home": h, "neutral": nt, "game_url": g["game_url"],
                 "source_url": g["source_url"], "actual_margin": m, "actual_total": t, "home_result": yw,
                 "train_games": len(train), "lambda_S1": M.lam, "lambda_S2": P.lam, "sigma_S1": round(M.sigma, 2),
                 "rho_train": round(rho_train, 3),
                 "m_B": B.margin(h, a, nt), "m_S1": M.margin(h, a, nt), "m_S2": P.margin(h, a, nt), "m_S3": A.margin(h, a, nt),
                 "t_B": B.total(h, a, nt), "t_S4": P.total(h, a, nt), "t_S5": A.total(h, a, nt)}
            r["p_B"] = p_home(r["m_B"], B.sigma)
            r["p_S6"] = p_home(r["m_S1"], M.sigma)
            r["p_S7"] = p_home(r["m_S2"], P.sigma_m)
            r["p_S8"] = p_home(r["m_S3"], M.sigma)
            preds.append(r)
    return preds


def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


# ============================================================== props (Next Gen Stats QB passing yards)
def ngs_join(ngs, games):
    by_wt = {}
    for g in games:
        by_wt[(g["week"], g["home"])] = (g, "home")
        by_wt[(g["week"], g["away"])] = (g, "away")
    per_team_week = {}
    for r in ngs:
        per_team_week[(r["week"], r["team"])] = per_team_week.get((r["week"], r["team"]), 0) + 1
    out = []
    for r in ngs:
        g, side = by_wt[(r["week"], r["team"])]  # KeyError would mean a QB listed for a team on bye -> data error
        opp = g["away"] if side == "home" else g["home"]
        tp = g["home_score"] if side == "home" else g["away_score"]
        op = g["away_score"] if side == "home" else g["home_score"]
        out.append(dict(r, opp=opp, side=side, team_pts=tp, opp_pts=op, total=tp + op, team_margin=tp - op,
                        single_qb=per_team_week[(r["week"], r["team"])] == 1, game_url=g["game_url"]))
    return out


def shrink_k(groups):
    """Method-of-moments random-effects shrinkage constant k = sigma_within^2 / tau^2 (inf if tau^2 <= 0)."""
    multi = [g for g in groups.values() if len(g) >= 2]
    if not multi:
        return float("inf"), float("nan"), float("nan")
    sw2 = sum(sum((x - S.mean(g)) ** 2 for x in g) for g in multi) / sum(len(g) - 1 for g in multi)
    means = [S.mean(g) for g in groups.values()]
    gm = S.mean(means)
    var_means = sum((m - gm) ** 2 for m in means) / (len(means) - 1)
    tau2 = var_means - S.mean([sw2 / len(g) for g in groups.values()])
    return (sw2 / tau2 if tau2 > 0 else float("inf")), sw2, tau2


def prop_models(train):
    mu = S.mean([r["yds"] for r in train])
    byq, byd = {}, {}
    for r in train:
        byq.setdefault(r["player"], []).append(r["yds"])
        byd.setdefault(r["opp"], []).append(r["yds"])
    kq, _, _ = shrink_k(byq)
    kd, _, _ = shrink_k(byd)

    def shr(vals, k):
        if not vals or math.isinf(k):
            return mu
        return (sum(vals) + k * mu) / (len(vals) + k)

    def s11(player):
        return shr(byq.get(player, []), kq)

    def s12(player, opp):
        return s11(player) + (shr(byd.get(opp, []), kd) - mu)
    return mu, s11, s12, kq, kd


def walk_forward_props(joined):
    out = []
    for w in PROP_EVAL_WEEKS:
        train = [r for r in joined if r["week"] < w]
        assert all(r["week"] < w for r in train), "G2 leakage (props)"
        mu, s11, s12, kq, kd = prop_models(train)
        for r in joined:
            if r["week"] != w:
                continue
            out.append({"week": w, "player": r["player"], "team": r["team"], "opp": r["opp"], "actual_yds": r["yds"],
                        "pred_P0": mu, "pred_S11": s11(r["player"]), "pred_S12": s12(r["player"], r["opp"]),
                        "k_qb": None if math.isinf(kq) else round(kq, 2), "k_def": None if math.isinf(kd) else round(kd, 2),
                        "source_url": r["source_url"], "game_url": r["game_url"]})
    return out


# ============================================================== evaluation
def evaluate(sid, product, desc, lm, lb, halves, n_min, extra=None, cal=None):
    d = [a - b for a, b in zip(lm, lb)]
    n = len(d)
    md = S.mean(d)
    lo, hi = S.bootstrap_ci(d)
    p = S.signflip_p(d)
    base = S.mean(lb)
    h1 = S.mean([x for x, hf in zip(d, halves) if hf == 1])
    h2 = S.mean([x for x, hf in zip(d, halves) if hf == 2])
    row = {"id": sid, "product": product, "strategy": desc, "n": n, "loss_model": S.mean(lm), "loss_baseline": base,
           "mean_diff": md, "ci95": [lo, hi], "skill_pct": -md / base * 100, "skill_pct_lcb": -hi / base * 100,
           "p_one_sided": p, "half1_diff": h1, "half2_diff": h2,
           "gates": {"G1": True, "G2": True, "G3": n >= n_min, "G4": hi < 0, "G6": h1 < 0 and h2 < 0, "G8": True}}
    if cal is not None:
        e, table = S.ece(*cal)
        row["ece"], row["calibration_table"] = e, table
        row["gates"]["G7"] = e <= 0.10
    else:
        row["gates"]["G7"] = None  # not applicable
    if extra:
        row.update(extra)
    return row


def run():
    games, teams = load_games()
    preds = walk_forward(games, teams)
    half = [1 if r["week"] <= 5 else 2 for r in preds]
    ae = lambda key, y="actual_margin": [abs(r[y] - r[key]) for r in preds]  # noqa: E731
    lb_m, lb_t = ae("m_B"), ae("t_B", "actual_total")
    y = [r["home_result"] for r in preds]
    board = []
    for sid, key, desc in (("S1", "m_S1", "Ridge margin ratings + home edge (lambda by LOO-CV)"),
                           ("S2", "m_S2", "Offence/defence points ridge -> margin"),
                           ("S3", "m_S3", "Naive season point differential per game (unshrunk)")):
        board.append(evaluate(sid, "Single: point spread (margin, abs error)", desc, ae(key), lb_m, half, 80,
                              extra={"rmse_model": math.sqrt(S.mean([e * e for e in ae(key)])),
                                     "rmse_baseline": math.sqrt(S.mean([e * e for e in lb_m]))}))
    for sid, key, desc in (("S4", "t_S4", "Offence/defence points ridge -> total"),
                           ("S5", "t_S5", "Naive PF/PA per game averages -> total")):
        board.append(evaluate(sid, "Single: game total (abs error)", desc, ae(key, "actual_total"), lb_t, half, 80))
    bB = [brier(r["p_B"], yy) for r, yy in zip(preds, y)]
    for sid, key, desc in (("S6", "p_S6", "Win probability = Phi(S1 margin / LOO sigma)"),
                           ("S7", "p_S7", "Win probability = Phi(S2 margin / sigma)"),
                           ("S8", "p_S8", "Win probability = Phi(S3 margin / S1 sigma)")):
        bm = [brier(r[key], yy) for r, yy in zip(preds, y)]
        board.append(evaluate(sid, "Single: moneyline (Brier score)", desc, bm, bB, half, 80,
                              extra={"logloss_model": S.mean([logloss(r[key], yy) for r, yy in zip(preds, y)]),
                                     "logloss_baseline": S.mean([logloss(r["p_B"], yy) for r, yy in zip(preds, y)]),
                                     "straight_up_hit_rate": S.mean([1.0 if (r[key] > .5) == (yy == 1) else 0.0 for r, yy in zip(preds, y) if yy != .5])},
                              cal=([r[key] for r in preds], y)))
    # ---- S9: 2-leg cross-game parlays on disjoint same-week pairs (model-favoured side in each game)
    pairs = []
    for w in EVAL_WEEKS:
        wk = [r for r in preds if r["week"] == w and r["home_result"] != 0.5]
        for i in range(0, len(wk) - 1, 2):
            pairs.append((wk[i], wk[i + 1]))
    pm, pb, ph, events = [], [], [], []
    for g1, g2 in pairs:
        q, qb, z = 1.0, 1.0, 1.0
        for g in (g1, g2):
            home_side = g["p_S6"] >= 0.5
            q *= g["p_S6"] if home_side else 1 - g["p_S6"]
            qb *= g["p_B"] if home_side else 1 - g["p_B"]
            z *= g["home_result"] if home_side else 1 - g["home_result"]
        pm.append(brier(q, z))
        pb.append(brier(qb, z))
        ph.append(1 if g1["week"] <= 5 else 2)
        events.append(z)
    board.append(evaluate("S9", "Parlay: 2-leg cross-game moneyline (Brier on joint event)",
                          "Product of S6 leg probabilities (independence across games)", pm, pb, ph, 40,
                          extra={"parlay_hit_rate": S.mean(events)}))
    # ---- S10: same-game parlay  home covers S1 line AND game goes over S4 total; correlation-adjusted vs independent
    sm, sb, sev = [], [], []
    for r in preds:
        z = 1.0 if (r["actual_margin"] > r["m_S1"] and r["actual_total"] > r["t_S4"]) else 0.0
        q = 0.25 + math.asin(r["rho_train"]) / (2 * math.pi)
        sm.append(brier(q, z))
        sb.append(brier(0.25, z))
        sev.append(z)
    board.append(evaluate("S10", "Same-game parlay: side + total (Brier on joint event)",
                          "Bivariate-normal joint probability using margin/total residual correlation from prior weeks",
                          sm, sb, half, 80, extra={"sgp_hit_rate": S.mean(sev)}))
    # ---- S11/S12: QB passing-yards props (Next Gen Stats)
    ngs = ngs_join(load_ngs(), games)
    pp = walk_forward_props(ngs)
    phalf = [1 if r["week"] <= 5 else 2 for r in pp]
    lp0 = [abs(r["actual_yds"] - r["pred_P0"]) for r in pp]
    for sid, key, desc in (("S11", "pred_S11", "QB passing yards: empirical-Bayes shrunk QB average"),
                           ("S12", "pred_S12", "S11 + shrunk opponent pass-defence adjustment")):
        board.append(evaluate(sid, "Player prop: QB passing yards (abs error)", desc,
                              [abs(r["actual_yds"] - r[key]) for r in pp], lp0, phalf, 100))
    # ---- multiplicity + verdicts + ranking
    adj = S.holm([b["p_one_sided"] for b in board])
    qv = S.bh([b["p_one_sided"] for b in board])
    for b, a, q in zip(board, adj, qv):
        b["p_holm"], b["q_bh"] = a, q
        b["gates"]["G5"] = a < 0.05
        failed = [k for k, v in sorted(b["gates"].items()) if v is False]
        b["verdict"] = "PASS" if not failed else "FAIL " + ",".join(failed)
    passing = sorted([b for b in board if b["verdict"] == "PASS"], key=lambda b: -b["skill_pct_lcb"])
    medals = ["Gold", "Silver", "Bronze"]
    for i, b in enumerate(passing):
        b["rank"], b["medal"] = i + 1, (medals[i] if i < 3 else "")
    for b in board:
        b.setdefault("rank", None)
        b.setdefault("medal", "")
    board.sort(key=lambda b: (b["rank"] is None, b["rank"] or 0, -b["skill_pct_lcb"]))
    not_scored = [
        {"id": "M1", "product": "Single / parlay vs sportsbook prices",
         "strategy": "Bet when originated line differs from the market line by a threshold",
         "verdict": "NOT SCORED — fails G8: no official source publishes sportsbook prices; a licensed odds feed is required",
         "gates": {"G8": False}},
        {"id": "M2", "product": "Player-prop combos vs sportsbook prop lines",
         "strategy": "Correlated prop combos priced against book prop lines",
         "verdict": "NOT SCORED — fails G8 (no official prop prices); correlations are still measured below",
         "gates": {"G8": False}},
    ]
    return games, teams, preds, board, not_scored, ngs, pp


# ============================================================== correlations (O3)
def corr_row(cid, label, x, y, scope, source, interpretation):
    r = S.pearson(x, y)
    lo, hi = S.fisher_ci(r, len(x))
    return {"id": cid, "pair": label, "n": len(x), "r": r, "ci95": [lo, hi], "p_two_sided": S.fisher_p(r, len(x)),
            "significant_5pct": S.fisher_p(r, len(x)) < 0.05, "scope": scope, "source": source,
            "use": interpretation}


def correlations(games, preds, ngs):
    src_games = "nfl.com scores W1-W8 (" + GAMELOG + ")"
    out = []
    hp = [g["home_score"] for g in games]
    ap = [g["away_score"] for g in games]
    out.append(corr_row("C1", "Home points vs away points (same game)", hp, ap, "121 games W1-W8", src_games,
                        "Team-total combos: if ~0, team totals can be priced independently"))
    em = [r["actual_margin"] - r["m_S1"] for r in preds]
    et = [r["actual_total"] - r["t_S4"] for r in preds]
    out.append(corr_row("C2", "Home margin residual vs total residual (walk-forward)", em, et, "89 games W3-W8", src_games,
                        "Same-game parlay 'home side + over': joint prob = 1/4 + asin(r)/(2*pi)"))
    fav = [(e if r["m_S1"] >= 0 else -e) for r, e in zip(preds, em)]
    out.append(corr_row("C3", "Favourite margin residual vs total residual (walk-forward)", fav, et, "89 games W3-W8", src_games,
                        "Same-game parlay 'favourite covers + over'"))
    absm = [abs(r["m_S1"]) for r in preds]
    out.append(corr_row("C4", "Size of predicted spread vs total residual", absm, et, "89 games W3-W8", src_games,
                        "Do lopsided matchups go over/under the originated total?"))
    one = [r for r in ngs if r["single_qb"]]
    src_ngs = "Next Gen Stats weekly passing W1,W3-W8 + nfl.com scores"
    yds = [r["yds"] for r in one]
    out.append(corr_row("C5", "QB passing yards vs own team points", yds, [r["team_pts"] for r in one], f"{len(one)} QB-games", src_ngs,
                        "QB yards over + team total over combo"))
    out.append(corr_row("C6", "QB passing yards vs game total", yds, [r["total"] for r in one], f"{len(one)} QB-games", src_ngs,
                        "QB yards over + game over combo"))
    out.append(corr_row("C7", "QB passing yards vs own team margin", yds, [r["team_margin"] for r in one], f"{len(one)} QB-games", src_ngs,
                        "QB yards over + own side combo (game script)"))
    out.append(corr_row("C8", "QB pass attempts vs own team margin", [r["att"] for r in one], [r["team_margin"] for r in one],
                        f"{len(one)} QB-games", src_ngs, "Trailing teams throw more -> attempts props vs side"))
    pair = {}
    for r in one:
        pair.setdefault((r["week"], r["game_url"]), []).append(r)
    both = [v for v in pair.values() if len(v) == 2]
    out.append(corr_row("C9", "Opposing QBs' passing yards (same game)", [v[0]["yds"] for v in both], [v[1]["yds"] for v in both],
                        f"{len(both)} games", src_ngs, "Shoot-out combos: QB A over + QB B over"))
    # cross-game dependence within a week (intra-class correlation by week)
    tot_groups = [[e for r, e in zip(preds, et) if r["week"] == w] for w in EVAL_WEEKS]
    win_groups = [[r["home_result"] - r["p_S6"] for r in preds if r["week"] == w] for w in EVAL_WEEKS]
    icc = [{"id": "C10", "pair": "Total residuals of different games in the same week (ICC)", "n": len(preds),
            "icc": S.icc_oneway(tot_groups), "scope": "6 weeks x 14-16 games", "source": src_games,
            "use": "Cross-game 'over' parlays: ICC ~ 0 means weekly totals move independently"},
           {"id": "C11", "pair": "Win-probability residuals of different games in the same week (ICC)", "n": len(preds),
            "icc": S.icc_oneway(win_groups), "scope": "6 weeks x 14-16 games", "source": src_games,
            "use": "Cross-game moneyline parlays: ICC ~ 0 supports multiplying leg probabilities"}]
    adj = S.holm([c["p_two_sided"] for c in out])
    for c, a in zip(out, adj):
        c["p_holm"] = a
        c["significant_after_holm"] = a < 0.05
    return out, icc


def combo_prices(corr):
    """Fair joint probability that BOTH legs go over their own medians, bivariate normal with measured r.
    Only correlations that survive Holm are used for pricing; others are priced as independent (r = 0)."""
    rows = []
    for c in corr:
        r_use = c["r"] if c["significant_after_holm"] else 0.0
        q = 0.25 + math.asin(r_use) / (2 * math.pi)
        rows.append({"id": c["id"], "combo": c["pair"], "r_measured": c["r"], "r_used": r_use,
                     "joint_prob_both_over": q, "fair_odds": S.american(q), "independent_prob": 0.25,
                     "independent_odds": S.american(0.25),
                     "note": "priced with measured r (survives Holm)" if c["significant_after_holm"] else
                             "r not significant after Holm -> priced as independent"})
    return rows


# ============================================================== skill vs luck (team records)
def luck(games, teams, full_model):
    rec = {t: {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "close": [0, 0, 0], "other": [0, 0, 0]} for t in teams}
    for g in games:
        m = g["home_score"] - g["away_score"]
        for t, pf, pa in ((g["home"], g["home_score"], g["away_score"]), (g["away"], g["away_score"], g["home_score"])):
            r = rec[t]
            r["PF"] += pf
            r["PA"] += pa
            res = 0 if pf > pa else 1 if pf < pa else 2
            r["WLT"[res]] += 1
            (r["close"] if abs(m) <= 8 else r["other"])[res] += 1
    wp = {t: (r["W"] + .5 * r["T"]) / (r["W"] + r["L"] + r["T"]) for t, r in rec.items()}
    # Pythagorean exponent fitted on these 32 teams (no external constant)
    best_k, best_sse = None, None
    for i in range(100, 501):
        k = i / 100
        sse = sum((wp[t] - r["PF"] ** k / (r["PF"] ** k + r["PA"] ** k)) ** 2 for t, r in rec.items())
        if best_sse is None or sse < best_sse:
            best_k, best_sse = k, sse
    rows = []
    for t, r in rec.items():
        gp = r["W"] + r["L"] + r["T"]
        py = r["PF"] ** best_k / (r["PF"] ** best_k + r["PA"] ** best_k)
        rows.append({"team": t, "record": f"{r['W']}-{r['L']}-{r['T']}", "games": gp, "win_pct": wp[t], "PF": r["PF"], "PA": r["PA"],
                     "pythag_win_pct": py, "expected_wins": py * gp, "luck_wins": (r["W"] + .5 * r["T"]) - py * gp,
                     "one_score_record": "-".join(map(str, r["close"])), "other_record": "-".join(map(str, r["other"])),
                     "rating_S1": full_model.rating(t)})
    rows.sort(key=lambda x: -x["luck_wins"])
    n_bar = S.mean([x["games"] for x in rows])
    var_obs = S.sd([x["win_pct"] for x in rows]) ** 2
    var_luck = S.mean([0.25 / x["games"] for x in rows])
    close_games = sum(1 for g in games if abs(g["home_score"] - g["away_score"]) <= 8)
    summary = {"teams": 32, "avg_games": n_bar, "var_observed_win_pct": var_obs, "var_luck_binomial": var_luck,
               "luck_share_of_variance": var_luck / var_obs if var_obs else None,
               "true_talent_sd_win_pct": math.sqrt(max(var_obs - var_luck, 0.0)),
               "pythag_exponent_fitted": best_k, "one_score_games": close_games, "games": len(games),
               "r_pythag_vs_actual": S.pearson([x["pythag_win_pct"] for x in rows], [x["win_pct"] for x in rows]),
               "method": "var(luck) = mean(0.25/games) (binomial, p=.5); luck share = var(luck)/var(observed win%). "
                         "Pythagorean exponent fitted to these 32 teams by least squares on k in [1,5]. One-score = margin <= 8."}
    return rows, summary


# ============================================================== Week 9 fair lines
def w9_lines(games, teams, board, ngs):
    sched = load_schedule()
    M = MarginRidge().fit(games, teams)
    P = PointsRidge().fit(games, teams)
    A = TeamAverages().fit(games, teams)
    B = Baseline().fit(games, teams)
    status = {b["id"]: b["verdict"] for b in board}
    rows = []
    for s in sched:
        h, a, nt = s["home"], s["away"], s["neutral"]
        m1, m2 = M.margin(h, a, nt), P.margin(h, a, nt)
        tot = P.total(h, a, nt)
        p = p_home(m1, M.sigma)
        fav, spread = (h, -m1) if m1 >= 0 else (a, m1)
        rows.append({"away": a, "home": h, "neutral_site": nt, "heading": s["heading"], "day": s["day"],
                     "time_as_rendered": s["time_as_rendered"], "network": s["network"],
                     "fair_margin_home_S1": m1, "fair_margin_home_S2": m2, "fair_margin_home_S3": A.margin(h, a, nt),
                     "fair_spread_text": f"{fav} {spread:+.1f}", "fair_total_S4": tot, "fair_total_S5": A.total(h, a, nt),
                     "p_home_S6": p, "fair_ml_home": S.american(p), "fair_ml_away": S.american(1 - p),
                     "sigma_margin": M.sigma, "sigma_total": P.sigma_t,
                     "home_pts_S4": P.pts(h, a, 0.0 if nt else 0.5), "away_pts_S4": P.pts(a, h, 0.0 if nt else -0.5),
                     "game_url": s["game_url"], "source_url": s["source_url"]})
    # props: QB passing yards, conditional on the QB with the team's most recent NGS row starting
    mu, s11, s12, kq, kd = prop_models(ngs)
    latest = {}
    for r in ngs:
        cur = latest.get(r["team"])
        if cur is None or (r["week"], r["att"]) > (cur["week"], cur["att"]):
            latest[r["team"]] = r
    resid = [r["yds"] - s11(r["player"]) for r in ngs]
    props = []
    for s in sched:
        for team, opp in ((s["away"], s["home"]), (s["home"], s["away"])):
            q = latest.get(team)
            if not q:
                continue
            props.append({"team": team, "opp": opp, "qb_conditional": q["player"], "qb_last_seen_week": q["week"],
                          "fair_pass_yds_S11": s11(q["player"]), "fair_pass_yds_S12": s12(q["player"], opp),
                          "condition": f"Conditional on {q['player']} starting — starters are not confirmed by an official source here (check https://www.nfl.com/injuries/league/2026/reg9).",
                          "source_url": q["source_url"], "game_url": s["game_url"]})
    model = {"S1_lambda": M.lam, "S1_hfa": M.hfa, "S1_sigma_loo": M.sigma, "S1_tau": M.tau, "S1_p_eff": M.p_eff,
             "S2_lambda": P.lam, "S2_mu": P.beta[0], "S2_home_edge": P.beta[1], "S2_sigma_margin": P.sigma_m,
             "S2_sigma_total": P.sigma_t, "baseline_hfa": B.hfa, "baseline_total": B.tot, "props_mu": mu,
             "props_k_qb": None if math.isinf(kq) else kq, "props_k_def": None if math.isinf(kd) else kd,
             "validation_status": {k: status[k] for k in ("S1", "S4", "S6", "S11", "S12")},
             "ratings": sorted([{"team": t, "rating_S1": M.rating(t), "off_S2": P.off(t), "def_S2_points_allowed_above_avg": P.dfn(t)} for t in teams],
                               key=lambda x: -x["rating_S1"])}
    return rows, props, model


def main():
    games, teams, preds, board, not_scored, ngs, pp = run()
    corr, icc = correlations(games, preds, ngs)
    full = MarginRidge().fit(games, teams)
    luck_rows, luck_sum = luck(games, teams, full)
    lines, props, model = w9_lines(games, teams, board, ngs)
    dump_json({"description": "Walk-forward predictions (each made only from earlier weeks) for every W3-W8 game",
               "data": GAMELOG, "games": preds}, "walkforward-games.json")
    dump_json({"description": "Walk-forward QB passing-yards predictions W4-W8", "props": pp}, "walkforward-props.json")
    dump_json({"gates_doc": __doc__, "family_size": len(board), "seed": S.SEED, "bootstrap_reps": 10000,
               "permutation_reps": 10000, "strategies": board, "not_scored": not_scored}, "leaderboard.json")
    dump_json({"correlations": corr, "cross_game_dependence": icc, "combo_pricing": combo_prices(corr),
               "method": "Pearson r, Fisher-z 95% CI and two-sided p; Holm across C1-C9. Joint probability at the medians "
                         "of two legs = 1/4 + asin(r)/(2*pi) (bivariate normal)."}, "correlations.json")
    dump_json({"summary": luck_sum, "teams": luck_rows}, "luck.json")
    dump_json({"description": "Week 9 fair (no-vig) lines originated only from official W1-W8 results; no market input.",
               "games": lines, "qb_props_conditional": props, "model": model}, "w9-lines.json")
    print("LEADERBOARD")
    for b in board:
        print(f"{b['id']:>4} {b['verdict']:<22} skill={b['skill_pct']:6.2f}% lcb={b['skill_pct_lcb']:7.2f}% "
              f"p={b['p_one_sided']:.4f} holm={b['p_holm']:.4f} n={b['n']} h1={b['half1_diff']:.3f} h2={b['half2_diff']:.3f} "
              f"model={b['loss_model']:.3f} base={b['loss_baseline']:.3f}" + (f" ece={b['ece']:.3f}" if 'ece' in b else ""))
    print("CORR")
    for c in corr:
        print(f"{c['id']:>4} r={c['r']:+.3f} [{c['ci95'][0]:+.2f},{c['ci95'][1]:+.2f}] p={c['p_two_sided']:.4f} holm={c['p_holm']:.4f} n={c['n']} {c['pair']}")
    for c in icc:
        print(f"{c['id']:>4} icc={c['icc']:+.3f} {c['pair']}")
    print("LUCK", json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in luck_sum.items() if k != 'method'}))
    print("W9")
    for r in lines:
        print(f"{r['away']:>3}@{r['home']:<3} {r['fair_spread_text']:>10} total={r['fair_total_S4']:.1f} pH={r['p_home_S6']:.3f} "
              f"ML {r['fair_ml_away']}/{r['fair_ml_home']} S2={r['fair_margin_home_S2']:+.1f} S3={r['fair_margin_home_S3']:+.1f}")
    print("MODEL", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in model.items() if k not in ("ratings", "validation_status")})


if __name__ == "__main__":
    main()
