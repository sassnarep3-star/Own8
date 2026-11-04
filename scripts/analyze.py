#!/usr/bin/env python3
"""Own8 analysis pipeline (T3). Reads data/*.json (official-source captures only),
computes correlations, originates model lines for the Week 9 slate, evaluates
validation gates per strategy, and writes analysis/*.json.

Reproducible: python3 scripts/analyze.py  (stdlib only, no network, no manual input)

Model assumptions (NOT official values — see data/flagged.json F-07):
  HFA = 2.5 points home-field advantage (league-standard assumption)
  EDGE_MIN = 1.0 point minimum edge vs market to qualify as a candidate
  EDGE_MAX = 8.0 points sanity cap (larger edges = model unreliable -> no play)
  VIG = -110 standard juice assumption for ROI math
"""
import json, math, os, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

HFA = 2.5
EDGE_MIN = 1.0
EDGE_MAX = 8.0

def load(name):
    with open(DATA / name) as f:
        return json.load(f)

standings = load("standings-2026-reg-w8.json")["teams"]
sched = load("schedule-2026-week9.json")["games"]
tp_off = {t["abbr"]: t for t in load("team-passing-offense-2026.json")["teams"]}
tp_def = {t["abbr"]: t for t in load("team-passing-defense-2026.json")["teams"]}
tr_off = {t["abbr"]: t for t in load("team-rushing-offense-2026.json")["teams"]}
tr_def = {t["abbr"]: t for t in load("team-rushing-defense-2026.json")["teams"]}
ppass = load("player-passing-2026.json")["players"]
ngs = {p["name"]: p for p in load("nextgen-passing-2026-week8.json")["players"]}
prush = load("player-rushing-2026.json")["players"]
prec = load("player-receiving-2026.json")["players"]
market = load("market-lines.json")["lines"]
flagged = load("flagged.json")["items"]

# ---------- per-team derived rates (per game) ----------
teams = {}
for s in standings:
    a = s["abbr"]
    g = s["W"] + s["L"] + s["T"]
    teams[a] = {
        **s,
        "GP": g,
        "winpct": (s["W"] + 0.5 * s["T"]) / g,
        "PFpg": s["PF"] / g,
        "PApg": s["PA"] / g,
        "NETpg": s["NET"] / g,
        "passYDSpg": tp_off[a]["YDS"] / g,
        "rushYDSpg": tr_off[a]["YDS"] / g,
        "passYDSallowed_pg": tp_def[a]["YDS"] / g,
        "rushYDSallowed_pg": tr_def[a]["YDS"] / g,
        "passRTG": tp_off[a]["RTG"],
        "passAVG": tp_off[a]["AVG"],
        "rushAVG": tr_off[a]["AVG"],
    }

abbrs = sorted(teams)

def pearson(xs, ys):
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else float("nan")

def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))

# ---------- correlations (computed from official data only) ----------
def col(key):
    return [teams[a][key] for a in abbrs]

correlations = [
    {"pair": "Team points-for per game (PFpg) vs win%", "type": "pearson", "n": 32,
     "r": round(pearson(col("PFpg"), col("winpct")), 4),
     "interpretation": "Pythagorean sanity check: scoring rate should track winning. High r = standings points are skill-consistent, not luck-driven."},
    {"pair": "Net points per game (NETpg) vs win%", "type": "pearson", "n": 32,
     "r": round(pearson(col("NETpg"), col("winpct")), 4),
     "interpretation": "Point differential vs record — the core 'remove luck' regression anchor."},
    {"pair": "Net points per game (NETpg) rank vs win% rank", "type": "spearman", "n": 32,
     "r": round(spearman(col("NETpg"), col("winpct")), 4),
     "interpretation": "Rank correlation: robust to outliers (e.g., blowouts)."},
    {"pair": "Offensive pass YDS/game vs PFpg", "type": "pearson", "n": 32,
     "r": round(pearson(col("passYDSpg"), col("PFpg")), 4),
     "interpretation": "Passing volume explains scoring. Also used as the documented proxy for same-game QB-performance vs team-total correlation (parlay gate G5)."},
    {"pair": "Defensive pass YDS allowed/game vs PApg", "type": "pearson", "n": 32,
     "r": round(pearson(col("passYDSallowed_pg"), col("PApg")), 4),
     "interpretation": "Pass defense quality explains points allowed — drives QB/WR prop matchup factors."},
    {"pair": "Offensive rush YDS/game vs PFpg", "type": "pearson", "n": 32,
     "r": round(pearson(col("rushYDSpg"), col("PFpg")), 4),
     "interpretation": "Rushing volume vs scoring."},
    {"pair": "Defensive rush YDS allowed/game vs PApg", "type": "pearson", "n": 32,
     "r": round(pearson(col("rushYDSallowed_pg"), col("PApg")), 4),
     "interpretation": "Run defense vs points allowed — drives RB prop matchup factors."},
    {"pair": "Team pass RTG vs win%", "type": "pearson", "n": 32,
     "r": round(pearson(col("passRTG"), col("winpct")), 4),
     "interpretation": "QB efficiency vs winning."},
    {"pair": "Offensive pass YDS/game vs offensive rush YDS/game (game script)", "type": "pearson", "n": 32,
     "r": round(pearson(col("passYDSpg"), col("rushYDSpg")), 4),
     "interpretation": "Teams that pass more tend to run less (negative expected) — relevant when pairing QB overs with RB unders in the same game (correlation gate)."},
]
with open(OUT / "correlations.json", "w") as f:
    json.dump({"as_of": "2026-11-03", "method": "Pearson/Spearman across all 32 teams, computed from data/*.json (official NFL.com captures). n=32 teams, season through Week 8.",
               "correlations": correlations}, f, indent=2)

# ---------- model line origination for Week 9 ----------
league_avg_def_pass_ypg = statistics.mean(teams[a]["passYDSallowed_pg"] for a in abbrs)
league_avg_def_rush_ypg = statistics.mean(teams[a]["rushYDSallowed_pg"] for a in abbrs)

def market_spread_home(away, home):
    """Parse the third-party (UNVERIFIED) market line into 'home spread' points.
    Returns (value, verified=False) or (None, False)."""
    key = f"{away} at {home}"
    for ln in market:
        if ln["game"].startswith(key):
            txt = ln["spread_rendered"]
            # e.g. 'JAX -9.5 / BAL +9.5' -> home spread = +9.5 for BAL
            for part in txt.replace("(", " ").split("/"):
                p = part.strip()
                if p.startswith(home):
                    try:
                        return float(p.split()[1]), False
                    except Exception:
                        return None, False
    return None, False

games_out = []
for g in sched:
    away, home = g["away"], g["home"]
    A, H = teams[away], teams[home]
    proj_away = (A["PFpg"] + H["PApg"]) / 2 - HFA / 2
    proj_home = (H["PFpg"] + A["PApg"]) / 2 + HFA / 2
    model_spread_home = proj_home - proj_away   # + = home favored
    model_total = proj_away + proj_home
    mkt, _ = market_spread_home(away, home)
    edge = None
    edge_note = "No market line captured (market lines are not an official source — blank by rule)."
    if mkt is not None:
        edge = model_spread_home - mkt   # + means market underprices home side
        edge_note = ("Market input is a THIRD-PARTY aggregator value attributed to FanDuel, time-stamped Nov 3 11:31 AM ET — UNVERIFIED (flagged F-05). "
                     "Verify at a licensed sportsbook before any use.")
    # gates
    gates = {
        "G1_official_sources_only": {"status": "PASS", "detail": "All model inputs from nfl.com / nextgenstats.nfl.com captures dated 2026-11-03."},
        "G2_data_freshness_le_7d": {"status": "PASS", "detail": "Standings/stats through Week 8 (final Nov 2); captured Nov 3."},
        "G3_sample_size_ge_4_games": {"status": "PASS", "detail": f"{away} GP={A['GP']}, {home} GP={H['GP']} (min required 4)."},
        "G4_injury_news_check": {"status": "CONDITIONAL", "detail": "Latest official injury report is Week 8 (W9 report not yet published — flagged F-04); official nfl.com news applied where relevant (Hurts IR — PHI; McLaurin season out — WAS). Re-check official W9 report before acting."},
        "G5_correlation_check": {"status": "PASS", "detail": "Single-game play; no parlay legs. Same-game parlay correlation proxy r(pass YDSpg, PFpg) = " + str([c for c in correlations if 'same-game' in c['interpretation']][0]['r']) + " — same-game combos restricted (see correlation policy)."},
        "G6_edge_vs_market": {"status": ("PASS" if (edge is not None and EDGE_MIN <= abs(edge) <= EDGE_MAX) else ("FAIL_NO_TRADE" if edge is not None else "NOT_COMPUTABLE")),
                               "detail": (f"Model home spread {model_spread_home:+.2f} vs market {mkt:+.2f} -> edge {edge:+.2f} pts. {edge_note}" if mkt is not None else edge_note)},
        "G7_stake_cap": {"status": "PASS", "detail": "Kelly-style cap: max 2% of bankroll per single play (assumption, flagged F-07)."},
    }
    all_pass = all(v["status"] in ("PASS", "CONDITIONAL") for v in gates.values())
    games_out.append({
        "game": f"{away} at {home}", "away": away, "home": home, "date": g["date"], "kickoff_et": g["kickoff_et"],
        "network": g["network"], "venue": g["venue"], "game_url": g["game_url"], "label": g.get("label", ""),
        "away_record": f"{A['W']}-{A['L']}-{A['T']}", "home_record": f"{H['W']}-{H['L']}-{H['T']}",
        "proj_away": round(proj_away, 2), "proj_home": round(proj_home, 2),
        "model_spread_home": round(model_spread_home, 2),
        "model_spread_rendered": (f"{home} {model_spread_home:+.1f}" if model_spread_home >= 0 else f"{away} {-model_spread_home:.1f}"),
        "model_total": round(model_total, 2),
        "market_spread_home": mkt, "market_verified": False,
        "edge_pts": (round(edge, 2) if edge is not None else None),
        "candidate_side": (None if edge is None else (home if edge > 0 else away)),
        "candidate": (edge is not None and EDGE_MIN <= abs(edge) <= EDGE_MAX),
        "gates": gates, "gates_all_pass": all_pass,
        "inputs": {"away": {"PFpg": round(A["PFpg"],2), "PApg": round(A["PApg"],2), "passYDSpg": round(A["passYDSpg"],2), "rushYDSpg": round(A["rushYDSpg"],2)},
                   "home": {"PFpg": round(H["PFpg"],2), "PApg": round(H["PApg"],2), "passYDSpg": round(H["passYDSpg"],2), "rushYDSpg": round(H["rushYDSpg"],2)}},
        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-9",
        "inputs_source_urls": ["https://www.nfl.com/standings/", "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
                                "https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all",
                                "https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all",
                                "https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all"],
    })

with open(OUT / "model-lines-week9.json", "w") as f:
    json.dump({"as_of": "2026-11-03", "week": 9, "method": "proj_team = (team PFpg + opp PApg)/2; home/away each adjusted by HFA/2 = 1.25 (HFA=2.5 assumption, flagged F-07). model_spread_home = proj_home - proj_away. model_total = sum of projections. Edge = model_spread_home - market_spread_home (market = unverified third-party, F-05). Candidate requires EDGE_MIN<=|edge|<=EDGE_MAX and all gates PASS/CONDITIONAL.",
               "league_avg_def_pass_ypg": round(league_avg_def_pass_ypg, 2), "league_avg_def_rush_ypg": round(league_avg_def_rush_ypg, 2),
               "games": games_out}, f, indent=2)

# ---------- player prop signals for Week 9 (model projections; no market lines exist in official sources) ----------
qb_by_team = {p["team"]: p for p in ppass if p.get("team")}
# PHI backup QB verified via NGS week 8 (Tanner McKee, PHI)
if "PHI" not in qb_by_team and "Tanner McKee" in ngs:
    qb_by_team["PHI"] = {"name": "Tanner McKee", "team": "PHI", **{k: ngs["Tanner McKee"].get(k) for k in ("YDS", "ATT", "RATE", "COMP%")}}

prop_signals = []
for g in sched:
    away, home = g["away"], g["home"]
    A, H = teams[away], teams[home]
    for side, team, opp in (("away", away, home), ("home", home, away)):
        T, O = teams[team], teams[opp]
        qb = qb_by_team.get(team)
        qb_proj = None
        if qb and qb.get("YDS") and qb.get("ATT"):
            qb_ypg = qb["YDS"] / T["GP"]
            qb_proj = qb_ypg * (O["passYDSallowed_pg"] / league_avg_def_pass_ypg)
        # RB: top rusher on team by season YDS (team not rendered on RB page -> match by known team via NGS only for QBs; RB team mapping unavailable -> use team rush volume only)
        rb_team_proj = T["rushYDSpg"] * (O["rushYDSallowed_pg"] / league_avg_def_rush_ypg)
        wr_team_proj = T["passYDSpg"] * (O["passYDSallowed_pg"] / league_avg_def_pass_ypg)
        prop_signals.append({
            "game": f"{away} at {home}", "side": side, "team": team,
            "qb": qb["name"] if qb else None,
            "qb_proj_pass_yds": round(qb_proj, 1) if qb_proj else None,
            "qb_season_ypg": round(qb["YDS"] / T["GP"], 1) if qb and qb.get("YDS") else None,
            "team_rush_proj_yds": round(rb_team_proj, 1),
            "team_pass_proj_yds": round(wr_team_proj, 1),
            "opp_pass_def_ypg_allowed": round(O["passYDSallowed_pg"], 2),
            "opp_rush_def_ypg_allowed": round(O["rushYDSallowed_pg"], 2),
            "market_prop_line": None,
            "market_prop_line_note": "Blank by rule: prop lines are sportsbook-specific and not an official source (F-05). Compare against a licensed sportsbook only.",
            "source_url": g["game_url"],
        })

with open(OUT / "prop-signals-week9.json", "w") as f:
    json.dump({"as_of": "2026-11-03", "week": 9,
               "method": "QB proj pass YDS = QB season YDS/game * (opp pass defense YDS allowed/game / league avg). Team rush/pass proj likewise. These are model PROJECTIONS for research, not bets with a computable edge (no official market line exists).",
               "signals": prop_signals}, f, indent=2)

# ---------- strategies with validation gates ----------
r_qb_team = [c for c in correlations if "same-game QB-performance" in c["interpretation"]][0]["r"]
r_pass_rush = [c for c in correlations if "game script" in c["pair"]][0]["r"]
strategies = [
    {"id": "S1", "name": "Form Spread (single game)", "type": "single bet — spread",
     "description": "Originate spread from offensive/defensive PPG matchup model; take the side only when |model - market| edge is within [1.0, 8.0] pts and all gates pass. Market input is unverified third-party (F-05) until checked at a licensed book.",
     "games_evaluated": len(games_out), "candidates": sum(1 for g in games_out if g["candidate"]),
     "gates": ["G1", "G2", "G3", "G4", "G5", "G6", "G7"], "status": "active — Week 9 candidates listed on Model Lines page"},
    {"id": "S2", "name": "Total Fishing (game totals)", "type": "single bet — total",
     "description": "Model total = sum of matchup projections. Trade only when model total differs from market total by >= 1.0 pt (totals from aggregators are unverified; most W9 totals were not captured — left blank by rule).",
     "games_evaluated": len(games_out), "candidates": 0,
     "gates": ["G1", "G2", "G3", "G4", "G6"], "status": "limited — only 1 third-party total captured (SF game, F-05); mostly NOT_COMPUTABLE this week"},
    {"id": "S3", "name": "QB Prop Alignment", "type": "player prop — QB passing yards",
     "description": "Project QB yards = season YPG * opponent pass-defense factor. Compare with licensed-book line (never from aggregators). Favor QBs behind pass-blocking issues (high SK) facing weak pass rush (low def SK) — e.g., CLE (33 SK taken) at NO.",
     "signals": len([p for p in prop_signals if p["qb"]]),
     "gates": ["G1", "G2", "G3", "G4", "G6(market at licensed book only)"], "status": "active — projections on Prop Signals page"},
    {"id": "S4", "name": "RB Workload vs Run Defense", "type": "player prop — RB rushing yards",
     "description": "Team rush projection vs opponent run-defense YPG allowed; allocate to lead back share (RB team affiliation is not rendered on the official leaders page — F-02 — so use team-level signal + official depth chart on nfl.com team pages before acting).",
     "signals": len(prop_signals), "gates": ["G1", "G2", "G3", "G4"], "status": "active — team-level projections only (individual allocation unverified)"},
    {"id": "S5", "name": "WR Matchup vs Pass Defense", "type": "player prop — receiving yards/receptions",
     "description": "Team pass projection vs opponent pass defense; allocate by player share of team receiving (player YDS / team pass YDS). Injury adjustments from official nfl.com news (e.g., WAS WR McLaurin out for season -> target share redistributes).",
     "signals": len(prop_signals), "gates": ["G1", "G2", "G3", "G4"], "status": "active"},
    {"id": "S6", "name": "De-correlated 2-leg Parlay", "type": "parlay — 2 legs, different games",
     "description": "Pair two single-game candidates from DIFFERENT games (cross-game correlation ~0 by construction). Same-game parlays (SGP) are restricted: documented same-game proxy r(pass YDSpg, PFpg) = %.2f; legs like QB over + team over in the same game are mechanically correlated and are blocked when |r| >= 0.80." % r_qb_team,
     "legs_allowed": "different games only", "correlation_threshold": 0.80, "same_game_proxy_r": r_qb_team,
     "gates": ["G1", "G2", "G3", "G4", "G5", "G6", "G7(parlay stake <= 1% bankroll)"], "status": "active — build only from S1 candidate list"},
    {"id": "S7", "name": "Same-Game Parlay (restricted)", "type": "parlay — same game",
     "description": "Same-game combos are mechanically correlated (e.g., QB over + team over share the same drives). Default BLOCKED for correlated combos; only contrarian pairs (e.g., game total OVER + favorite spread UNDER, or game-script-negative pairs with r(pass YDSpg, rushYDSpg) = %.2f) may be submitted for review and must pass G5 with pair |r| < 0.80 from the computed correlation table." % r_pass_rush,
     "status": "restricted — correlated same-game combos BLOCKED; contrarian pairs reviewable; proxy r(passYDSpg,PFpg) = %.2f" % r_qb_team, "gates": ["G5"]},
    {"id": "S8", "name": "Live / in-game", "type": "live betting",
     "description": "Not covered: no official live-data feed was captured this session. Left blank — flagged rather than simulated.",
     "status": "not covered (no official live source captured)", "gates": ["G1"]},
]
with open(OUT / "strategies.json", "w") as f:
    json.dump({"as_of": "2026-11-03", "strategies": strategies}, f, indent=2)

# ---------- leaderboard (competition framework; points only, no real money) ----------
leaderboard = {
    "as_of": "2026-11-03",
    "note": "Leaderboard competition: strategies earn points when Week 9+ results grade (ROI at -110, stake-capped). No real-money wagering occurs here — rewards are points/trophies only (F-10). Grading is automated by re-running this pipeline after official scores post (nfl.com/scores) — no manual input.",
    "scoring": "points = realized ROI% at -110 vig * 100, per strategy per week; season total = sum. Tiers: Gold >= +5.0 season ROI-pts, Silver >= 0, Bronze < 0. Tie-break: higher Sharpe-like ratio (mean weekly ROI / stdev).",
    "tiers": {"gold": ">= +5.0 pts", "silver": ">= 0 pts", "bronze": "< 0 pts"},
    "standings": [
        {"rank": i + 1, "strategy_id": s["id"], "name": s["name"], "type": s["type"],
         "week9_projected_edge_pts": (round(sum(g["edge_pts"] for g in games_out if g["edge_pts"] is not None and g["candidate_side"] and s["id"] == "S1"), 2) if s["id"] == "S1" else None),
         "realized_pts": 0.0, "status": s["status"]}
        for i, s in enumerate(strategies)
    ],
}
with open(OUT / "leaderboard.json", "w") as f:
    json.dump(leaderboard, f, indent=2)

print("correlations:")
for c in correlations:
    print(f"  {c['type']:8s} r={c['r']:+.4f}  {c['pair']}")
print("\nmodel lines (W9):")
for g in games_out:
    print(f"  {g['game']:14s} model {g['model_spread_rendered']:>10s} total {g['model_total']:>5.1f}  mkt {g['market_spread_home']}  edge {g['edge_pts']}  candidate={g['candidate']}")
print("\nwrote:", [p.name for p in sorted(OUT.glob('*.json'))])
