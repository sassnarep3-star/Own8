#!/usr/bin/env python3
"""Independent recomputation of the published correlations (C1-C11).

Session 5b52ac15. Stdlib only. Reads ONLY committed raw official captures and the
walk-forward output rows; never imports the originating model code.

Inputs (all repository paths, relative to the repo root):
  origination/data/games-2026-w1-w9.json          136 official nfl.com game rows (W1-W9)
  origination/data/raw-ngs-passing-transcription.txt  Next Gen Stats weekly passing rows (W1,W3-W8)
  origination/results/walkforward-games-w10.json  104 walk-forward rows (W3-W9) with model fields

Method (documented in method.txt of this folder, same as the published method line):
  Pearson r; Fisher-z 95% CI (z=1.959964); two-sided p from the Fisher-z normal approximation;
  Holm step-down across C1-C9; ICC(1) one-way ANOVA for C10/C11.

Outputs:
  correlation-audit/data/recomputed.json   per-ID recomputed values + comparison to published
  correlation-audit/data/input-checks.json  input integrity checks (counts, joins, arithmetic)
Exit code 1 if any recomputed value differs from the published value beyond tolerance.
"""
import json, math, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GAMES = os.path.join(ROOT, "origination", "data", "games-2026-w1-w9.json")
NGS = os.path.join(ROOT, "origination", "data", "raw-ngs-passing-transcription.txt")
WF = os.path.join(ROOT, "origination", "results", "walkforward-games-w10.json")
PUB = os.path.join(ROOT, "origination", "results", "correlations-w10.json")
OUT = os.path.join(ROOT, "correlation-audit", "data")
TOL = 1e-9
Z = 1.959964

NGS_URL = "https://nextgenstats.nfl.com/stats/passing/2026/REG/{w}"


def mean(a):
    return sum(a) / len(a)


def pearson(x, y):
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("need equal-length samples, n>=3")
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy)


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def fisher_ci(r, n):
    f, se = math.atanh(r), 1.0 / math.sqrt(n - 3)
    return math.tanh(f - Z * se), math.tanh(f + Z * se)


def fisher_p(r, n):
    return 2.0 * (1.0 - norm_cdf(abs(math.atanh(r)) * math.sqrt(n - 3)))


def holm(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj


def icc1(groups):
    groups = [g for g in groups if len(g) >= 2]
    k = len(groups)
    if k < 2:
        return float("nan")
    N = sum(len(g) for g in groups)
    grand = sum(sum(g) for g in groups) / N
    ssb = sum(len(g) * (mean(g) - grand) ** 2 for g in groups)
    ssw = sum(sum((x - mean(g)) ** 2 for x in g) for g in groups)
    msb = ssb / (k - 1)
    msw = ssw / (N - k)
    n0 = (N - sum(len(g) ** 2 for g in groups) / N) / (k - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw)


def load_games():
    with open(GAMES, encoding="utf-8") as f:
        return json.load(f)["games"]


def load_ngs():
    rows = []
    with open(NGS, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            w, name, team, att, yds, td, it = line.rstrip("\n").split("|")
            rows.append({"week": int(w), "player": name, "team": team, "att": int(att), "yds": int(yds)})
    return rows


def main():
    games = load_games()
    ngs_raw = load_ngs()
    wf = json.load(open(WF, encoding="utf-8"))["games"]
    pub = json.load(open(PUB, encoding="utf-8"))
    pub_by = {c["id"]: c for c in pub["correlations"]}
    pub_icc = {c["id"]: c for c in pub["cross_game_dependence"]}

    checks = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    # ---- input integrity -------------------------------------------------
    chk("games file has 136 rows (W1-W9)", len(games) == 136, f"rows={len(games)}")
    chk("every game row has integer scores",
        all(isinstance(g["home_score"], int) and isinstance(g["away_score"], int) for g in games))
    chk("every game row is marked verified", all(g.get("verified") is True for g in games))
    chk("every game row links an nfl.com game URL", all(str(g.get("game_url", "")).startswith("https://www.nfl.com/") for g in games))
    chk("every game row links an nfl.com scores URL", all(str(g.get("source_url", "")).startswith("https://www.nfl.com/") for g in games))

    by_wt = {}
    for g in games:
        by_wt[(g["week"], g["home"])] = (g, "home")
        by_wt[(g["week"], g["away"])] = (g, "away")

    # walk-forward outcomes must equal the official game row they claim to be
    wf_mismatch = []
    for r in wf:
        gs = [g for g in games if g["week"] == r["week"] and g["home"] == r["home"] and g["away"] == r["away"]]
        if len(gs) != 1:
            wf_mismatch.append((r["week"], r["away"], r["home"], "no unique official game"))
            continue
        g = gs[0]
        if (g["home_score"] - g["away_score"]) != r["actual_margin"] or (g["home_score"] + g["away_score"]) != r["actual_total"]:
            wf_mismatch.append((r["week"], r["away"], r["home"], "margin/total differs from official row"))
    chk("walk-forward outcomes equal official game rows (margin and total)", not wf_mismatch,
        f"rows={len(wf)} mismatches={len(wf_mismatch)} {wf_mismatch[:3]}")
    chk("walk-forward rows cover W3-W9 (104 games)", len(wf) == 104 and sorted({r['week'] for r in wf}) == [3, 4, 5, 6, 7, 8, 9], f"rows={len(wf)}")

    # NGS join: every NGS row must map to a game in which that team played
    join_fail = []
    joined = []
    for r in ngs_raw:
        key = (r["week"], r["team"])
        if key not in by_wt:
            join_fail.append(key)
            continue
        g, side = by_wt[key]
        tp = g["home_score"] if side == "home" else g["away_score"]
        op = g["away_score"] if side == "home" else g["home_score"]
        joined.append(dict(r, side=side, team_pts=tp, opp_pts=op, total=tp + op, team_margin=tp - op, game_url=g["game_url"]))
    chk("every NGS passing row joins to an official game the team played", not join_fail, f"fail={join_fail[:5]}")
    chk("NGS rows read", len(ngs_raw) == 210, f"rows={len(ngs_raw)}")
    weeks_ngs = sorted({r["week"] for r in ngs_raw})
    chk("NGS weeks captured are W1,W3-W8 (W2 not captured, W9 not captured)", weeks_ngs == [1, 3, 4, 5, 6, 7, 8], f"weeks={weeks_ngs}")

    per_tw = {}
    for r in joined:
        per_tw[(r["week"], r["team"])] = per_tw.get((r["week"], r["team"]), 0) + 1
    one = [r for r in joined if per_tw[(r["week"], r["team"])] == 1]
    chk("single-QB team-games used for C5-C9 = 204", len(one) == 204, f"n={len(one)}")

    # ---- correlations -----------------------------------------------------
    res = {}
    hp = [g["home_score"] for g in games]
    ap = [g["away_score"] for g in games]
    res["C1"] = dict(n=len(hp), r=pearson(hp, ap))

    em = [r["actual_margin"] - r["m_S1"] for r in wf]
    et = [r["actual_total"] - r["t_S4"] for r in wf]
    res["C2"] = dict(n=len(wf), r=pearson(em, et))
    fav = [(e if r["m_S1"] >= 0 else -e) for r, e in zip(wf, em)]
    res["C3"] = dict(n=len(wf), r=pearson(fav, et))
    res["C4"] = dict(n=len(wf), r=pearson([abs(r["m_S1"]) for r in wf], et))

    yds = [r["yds"] for r in one]
    res["C5"] = dict(n=len(one), r=pearson(yds, [r["team_pts"] for r in one]))
    res["C6"] = dict(n=len(one), r=pearson(yds, [r["total"] for r in one]))
    res["C7"] = dict(n=len(one), r=pearson(yds, [r["team_margin"] for r in one]))
    res["C8"] = dict(n=len(one), r=pearson([r["att"] for r in one], [r["team_margin"] for r in one]))
    pairs = {}
    for r in one:
        pairs.setdefault(r["game_url"], []).append(r)
    both = [v for v in pairs.values() if len(v) == 2]
    res["C9"] = dict(n=len(both), r=pearson([v[0]["yds"] for v in both], [v[1]["yds"] for v in both]))

    weeks_wf = sorted({r["week"] for r in wf})
    res["C10"] = dict(n=len(wf), icc=icc1([[e for r, e in zip(wf, et) if r["week"] == w] for w in weeks_wf]))
    win_resid = [r["home_result"] - r["p_S6"] for r in wf]
    res["C11"] = dict(n=len(wf), icc=icc1([[x for r, x in zip(wf, win_resid) if r["week"] == w] for w in weeks_wf]))

    ids9 = [f"C{i}" for i in range(1, 10)]
    for cid in ids9:
        r_ = res[cid]["r"]
        n_ = res[cid]["n"]
        res[cid]["ci95"] = list(fisher_ci(r_, n_))
        res[cid]["p_two_sided"] = fisher_p(r_, n_)
    adj = holm([res[c]["p_two_sided"] for c in ids9])
    for c, a in zip(ids9, adj):
        res[c]["p_holm"] = a
        res[c]["significant_after_holm"] = a < 0.05

    # Official-only family: Holm across the six tests whose inputs are official captures (C1, C5-C9).
    # C2-C4 use walk-forward model residuals and are withheld from the official register.
    official_ids = ["C1", "C5", "C6", "C7", "C8", "C9"]
    adj_off = holm([res[c]["p_two_sided"] for c in official_ids])
    holm_official = {c: a for c, a in zip(official_ids, adj_off)}

    # ---- compare with published ------------------------------------------
    rows = []
    any_fail = False
    for cid in [f"C{i}" for i in range(1, 12)]:
        rc = res[cid]
        if cid in pub_by:
            p = pub_by[cid]
            kind = "r"
            pub_val = p["r"]
            rec_val = rc["r"]
            pub_n = p["n"]
            pub_p = p.get("p_holm")
            pub_ci = p.get("ci95")
        else:
            p = pub_icc[cid]
            kind = "icc"
            pub_val = p["icc"]
            rec_val = rc["icc"]
            pub_n = p["n"]
            pub_p = None
            pub_ci = None
        ok_val = abs(pub_val - rec_val) <= 1e-6
        ok_n = pub_n == rc["n"]
        ok_p = True
        if pub_p is not None:
            ok_p = abs(pub_p - rc["p_holm"]) <= 1e-6
        ok_ci = True
        if pub_ci is not None:
            ok_ci = all(abs(a - b) <= 1e-6 for a, b in zip(pub_ci, rc["ci95"]))
        status = "MATCH" if (ok_val and ok_n and ok_p and ok_ci) else "MISMATCH"
        if status != "MATCH":
            any_fail = True
        rows.append({
            "id": cid, "pair": p["pair"], "kind": kind,
            "published": {"value": pub_val, "n": pub_n, "p_holm": pub_p, "ci95": pub_ci, "source": p.get("source"), "scope": p.get("scope")},
            "recomputed": {"value": rec_val, "n": rc["n"], "p_holm": rc.get("p_holm"), "ci95": rc.get("ci95")},
            "status": status,
        })

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "recomputed.json"), "w", encoding="utf-8") as f:
        json.dump({"method": "stdlib recomputation; see scripts/recompute_correlations.py", "rows": rows,
                   "tolerance_abs": 1e-6,
                   "holm_official_family": {"family": official_ids, "p_holm": holm_official},
                   "p_two_sided": {c: res[c]["p_two_sided"] for c in ids9}},
                  f, indent=1)
    with open(os.path.join(OUT, "input-checks.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "pass": sum(c["pass"] for c in checks), "total": len(checks),
                   "walk_forward_mismatches": wf_mismatch}, f, indent=1)
    n_pass = sum(c["pass"] for c in checks)
    print(f"input checks {n_pass}/{len(checks)} pass")
    for r in rows:
        print(f"{r['id']:>4} {r['status']:<8} n={r['recomputed']['n']:<4} r/icc={r['recomputed']['value']:+.6f} (published {r['published']['value']:+.6f})")
    return 1 if (any_fail or n_pass != len(checks)) else 0


if __name__ == "__main__":
    sys.exit(main())
