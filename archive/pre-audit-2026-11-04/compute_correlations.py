"""Compute correlation values from verified official NFL data files.

Inputs (all official, fetched 2026-11-03):
  data/nfl-2026-standings.csv   (nfl.com/standings)
  data/nfl-2026-passing.csv     (nextgenstats.nfl.com)
  data/nfl-2026-rushing.csv     (nextgenstats.nfl.com)
  data/nfl-2026-receiving.csv   (nextgenstats.nfl.com)

Output: data/correlations.md (append/compute block).
"""
import csv
import math
from collections import defaultdict


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fmt(v):
    return "n/a" if v is None else f"{v:+.3f}"


def main():
    standings = read_csv("data/nfl-2026-standings.csv")
    passing = read_csv("data/nfl-2026-passing.csv")
    rushing = read_csv("data/nfl-2026-rushing.csv")
    receiving = read_csv("data/nfl-2026-receiving.csv")

    # Team-level maps from standings (verified)
    teams = {r["abbr"]: r for r in standings}
    get = lambda r, c: float(r[c]) if r[c] not in ("", None) else None

    rows = []
    for abbr, r in teams.items():
        w = get(r, "w"); l = get(r, "l"); t = get(r, "t")
        gp = (w or 0) + (l or 0) + (t or 0)
        pct = get(r, "pct")
        pf = get(r, "pf"); pa = get(r, "pa"); net = get(r, "net_pts")
        pfpg = (pf / gp) if (pf is not None and gp) else None
        papg = (pa / gp) if (pa is not None and gp) else None
        conf_pct = get(r, "conf_w") / ((get(r, "conf_w") or 0) + (get(r, "conf_l") or 0)) if (get(r, "conf_w") is not None or get(r, "conf_l") is not None) else None
        rows.append({
            "abbr": abbr, "team": r["team"], "conf": r["conference"], "div": r["division"],
            "w": w, "l": l, "t": t, "gp": gp, "pct": pct, "pf": pf, "pa": pa, "net": net,
            "pfpg": pfpg, "papg": papg,
            "home_pct": (get(r, "home_w") / ((get(r, "home_w") or 0) + (get(r, "home_l") or 0))) if get(r, "home_w") is not None else None,
            "road_pct": (get(r, "road_w") / ((get(r, "road_w") or 0) + (get(r, "road_l") or 0))) if get(r, "road_w") is not None else None,
            "div_pct": (get(r, "div_w") / ((get(r, "div_w") or 0) + (get(r, "div_l") or 0))) if get(r, "div_w") is not None else None,
            "conf_pct": conf_pct,
        })

    def col(name):
        return [r[name] for r in rows]

    pairs = [
        ("Wins vs Points For", "w", "pf"),
        ("Wins vs Points Against", "w", "pa"),
        ("Wins vs Net Points", "w", "net"),
        ("Win% vs Points Per Game", "pct", "pfpg"),
        ("Win% vs Points Against Per Game", "pct", "papg"),
        ("Points For vs Points Against", "pf", "pa"),
        ("Win% vs Home Win%", "pct", "home_pct"),
        ("Win% vs Road Win%", "pct", "road_pct"),
        ("Win% vs Division Win%", "pct", "div_pct"),
        ("Win% vs Conference Win%", "pct", "conf_pct"),
    ]

    out = ["# Correlation Values — Computed from Official Data\n",
           "",
           "Computed with Pearson correlation (r) from verified official NFL data:",
           "- Team table: data/nfl-2026-standings.csv (source: https://www.nfl.com/standings/, 2026 REG, fetched 2026-11-03)",
           "- Player tables: data/nfl-2026-{passing,rushing,receiving}.csv (source: https://nextgenstats.nfl.com/stats/..., 2026 REG, fetched 2026-11-03)",
           "",
           "n/a = not computable (insufficient data or missing values).",
           "",
           "## Team-level correlations (32 teams, 2026 REG)\n",
           "",
           "| Variable A | Variable B | Teams | Pearson r | Interpretation | Source |",
           "|---|---|---:|---|---|---|",
    ]

    for label, a, b in pairs:
        xa, ya = [], []
        for r in rows:
            if r[a] is not None and r[b] is not None:
                xa.append(r[a]); ya.append(r[b])
        rval = pearson(xa, ya)
        interps = {
            "w": "Wins", "pct": "Win %", "pf": "Points For", "pa": "Points Against",
            "net": "Net Points", "pfpg": "Points For / Game", "papg": "Points Against / Game",
            "home_pct": "Home Win %", "road_pct": "Road Win %", "div_pct": "Division Win %",
            "conf_pct": "Conference Win %",
        }
        interp = "weak" if rval is None else (
            "strong" if abs(rval) >= 0.7 else "moderate" if abs(rval) >= 0.4 else "weak")
        direction = "positive" if (rval is not None and rval > 0) else ("negative" if rval is not None else "n/a")
        out.append(f"| {interps[a]} | {interps[b]} | {len(xa)} | {fmt(rval)} | {direction}, {interp} | https://www.nfl.com/standings/ |")

    out += [
        "",
        "## Player-level correlations (Next Gen Stats leaders tables)\n",
        "| Variable A | Variable B | Players | Pearson r | Source |",
        "|---|---|---:|---|---|",
    ]

    def pass_col(c): return [float(p[c]) for p in passing if p[c] not in ("", None)]
    def rush_col(c): return [float(p[c]) for p in rushing if p[c] not in ("", None)]
    def recv_col(c): return [float(p[c]) for p in receiving if p[c] not in ("", None)]

    player_pairs = [
        ("Pass attempts vs Passing yards (QB)", pass_col("attempts"), pass_col("passing_yards"), "https://nextgenstats.nfl.com/stats/passing/2026/REG/1"),
        ("Pass attempts vs Passer rating (QB)", pass_col("attempts"), pass_col("passer_rating"), "https://nextgenstats.nfl.com/stats/passing/2026/REG/1"),
        ("Rush attempts vs Rushing yards (RB)", rush_col("rush_attempts"), rush_col("rushing_yards"), "https://nextgenstats.nfl.com/stats/rushing/2026/REG/1"),
        ("Targets vs Receiving yards (WR/TE)", recv_col("targets"), recv_col("receiving_yards"), "https://nextgenstats.nfl.com/stats/receiving/2026/REG/1"),
        ("Receptions vs Receiving yards (WR/TE)", recv_col("receptions"), recv_col("receiving_yards"), "https://nextgenstats.nfl.com/stats/receiving/2026/REG/1"),
    ]
    for label, xs, ys, src in player_pairs:
        n = min(len(xs), len(ys))
        rval = pearson(xs[:n], ys[:n]) if n >= 2 else None
        interp = "strong" if rval is not None and abs(rval) >= 0.7 else ("moderate" if rval is not None and abs(rval) >= 0.4 else ("weak" if rval is not None else "n/a"))
        direction = "positive" if (rval is not None and rval > 0) else ("negative" if rval is not None else "n/a")
        out.append(f"| {label} | {n} | {fmt(rval)} | {direction}, {interp} | {src} |")

    out += [
        "",
        "## Notes\n",
        "- Correlations are descriptive of the fetched snapshot only; they are not predictive signals.",
        "- Player tables appear to contain partial/early-season totals relative to games played in the standings (see data/sources.md, UNVERIFIED items); player-level correlations are therefore flagged UNVERIFIED.",
        "- Betting-market correlations (e.g., same-game parlay leg correlation) cannot be computed: odds are not published by official NFL sources and are left blank.",
        "",
    ]
    with open("data/correlations.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    # Console summary
    for label, a, b in pairs:
        xa, ya = [], []
        for r in rows:
            if r[a] is not None and r[b] is not None:
                xa.append(r[a]); ya.append(r[b])
        print(f"{label}: n={len(xa)} r={fmt(pearson(xa, ya))}")
    for label, xs, ys, src in player_pairs:
        n = min(len(xs), len(ys))
        print(f"{label}: n={n} r={fmt(pearson(xs[:n], ys[:n]) if n >= 2 else None)}")


if __name__ == "__main__":
    main()
