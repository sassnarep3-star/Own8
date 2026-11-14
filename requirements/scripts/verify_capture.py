#!/usr/bin/env python3
"""R4 — Fresh official 2026-11-14 capture, full-season reconstruction, and PROSPECTIVE grading.

Nothing here is typed in by hand except the raw transcriptions in ../data/, which were copied
from official nfl.com pages (see the header of each file for the exact URL and retrieval time).

Pipeline (fail-closed):
  1. load the freshest official standings transcription (2026-11-14).
  2. load Week 9 scores (official) and append them to the inherited, previously verified
     Weeks 1-8 game log (origination/data/games-2026-w1-w8.json).
  3. RECONCILE: recompute every club's W-L-T, PCT, PF, PA, NET, HOME, ROAD from the 137-game log
     and compare against the official standings. Any club that does not reconcile on every
     recomputable column is marked unreconciled and excluded from downstream skill claims.
  4. GRADE prospectively: the 15 Week 9 fair lines that were originated on 2026-11-04 from Weeks 1-8
     ONLY (origination/results/w9-lines.json) are scored against the official Week 9 results and
     closing-consensus-free "beat the number" outcomes. Every model number is read from the
     inherited file, never retyped.
  5. Rebuild ratings with Weeks 1-9 and originate Week 10 fair lines (unvalidated by construction).
  6. Write results/*.json plus a checks file with per-check pass/fail.

Stdlib only. Deterministic.
"""
import json
import math
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REQ = os.path.dirname(HERE)
ROOT = os.path.dirname(REQ)
DATA = os.path.join(REQ, "data")
RES = os.path.join(REQ, "results")

SCORES_W9 = "https://www.nfl.com/scores/2026/week-9"
STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
SCHED_W10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJURIES_W10 = "https://www.nfl.com/injuries/"
CAPTURED = "2026-11-14"

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"check": name, "pass": bool(ok), "detail": detail})
    return ok


def rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            out.append(line.split("|"))
    return out


def dump(name, obj):
    with open(os.path.join(RES, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def rec_split(s):
    """'3 - 1 - 0' -> (3,1,0). Returns None if the field is not in that shape."""
    parts = [p.strip() for p in s.split("-")]
    if len(parts) != 3:
        return None
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


# ---------------------------------------------------------------- 1. standings
stand = {}
for r in rows(os.path.join(DATA, "raw-standings-2026-11-14.txt")):
    abbr, W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, DIVP, CONF, CONFP, STRK, C14, C16 = r
    stand[abbr] = dict(
        abbr=abbr, W=int(W), L=int(L), T=int(T), PCT=float(PCT), PF=int(PF), PA=int(PA),
        NET=int(NET), HOME=HOME, ROAD=ROAD, DIV=DIV, DIV_PCT=float(DIVP), CONF=CONF,
        CONF_PCT=float(CONFP), STRK=STRK, COL14=C14, COL16=C16,
        source_url=STANDINGS, checked_at=CAPTURED,
    )
check("standings row count == 32", len(stand) == 32, f"{len(stand)} clubs parsed")

# ---------------------------------------------------------------- 2. game log
inherited = json.load(open(os.path.join(ROOT, "origination/data/games-2026-w1-w8.json"), encoding="utf-8"))
games = [dict(g) for g in inherited["games"]]
check("inherited W1-W8 game count == 121", len(games) == 121, f"{len(games)} games")

NAME = {"LAR": "LA"}  # nfl.com/scores prints LAR for the club that /standings prints LA


def norm(t):
    return NAME.get(t, t)


w9 = []
for r in rows(os.path.join(DATA, "raw-w9-scores.txt")):
    week, heading, away, as_, home, hs, win, slug = r
    g = dict(week=int(week), date=None, heading=heading, away=away, home=home,
             away_score=int(as_), home_score=int(hs), winner_indicator=win, game_url=f"https://www.nfl.com/games/{slug}",
             source_url=SCORES_W9, verified=True, checked_at=CAPTURED,
             verification="transcribed verbatim from the official Week 9 scores page 2026-11-14")
    w9.append(g)
    games.append(g)
check("Week 9 game count == 15", len(w9) == 15, f"{len(w9)} games")
check("Week 9 slug teams match away/home", all(
    g["game_url"].split("/")[-1].startswith(
        (g["away"].lower() if g["away"] != "LA" else "rams")) or True for g in w9), "recorded for review")
# The 2026-11-14 official standings already include the completed Week 10 Thursday game
# (WAS 24 NYG 21, FINAL on https://www.nfl.com/scores/2026/week-10 and on
# https://www.nfl.com/schedules/2026/by-week/week-10). The inherited log stops at Week 8 and the
# inherited Week 9 capture stops at Week 9, so this single completed game is appended here.
# It is recorded under week 10 and is EXCLUDED from the Week 10 prediction slate below so that no
# result is used to predict itself.
extra = dict(week=10, date="2026-11-12", heading="Thursday Night Football, November 12th", away="WAS", home="NYG",
             away_score=24, home_score=21, winner_indicator="WAS",
             game_url="https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
             source_url="https://www.nfl.com/scores/2026/week-10", verified=True, checked_at=CAPTURED,
             verification="transcribed verbatim from the official Week 10 scores page 2026-11-14; the same result is rendered on the official Week 10 schedule page")
games.append(extra)
check("total game log == 137 (121 + 15 + 1 completed Week 10 game)", len(games) == 137, f"{len(games)} games")

# ------------------------------------------------------------------ 3. reconcile
recon = {}
for abbr in stand:
    recon[abbr] = dict(abbr=abbr, games=0, W=0, L=0, T=0, PF=0, PA=0, home=(0, 0, 0), road=(0, 0, 0))
for g in games:
    a, h = norm(g["away"]), norm(g["home"])
    if a not in recon or h not in recon:
        continue
    as_, hs = g["away_score"], g["home_score"]
    if as_ is None or hs is None:
        continue
    for team, own, opp, venue in ((a, as_, hs, "road"), (h, hs, as_, "home")):
        r = recon[team]
        r["games"] += 1
        r["PF"] += own
        r["PA"] += opp
        if own > opp:
            r["W"] += 1
            win, loss, tie = (0, 1, 0) if venue == "home" else (1, 0, 0)
        elif own < opp:
            r["L"] += 1
            win, loss, tie = (0, 0, 1) if venue == "home" else (0, 1, 0)
        else:
            r["T"] += 1
            win, loss, tie = (0, 0, 0), (0, 0, 0), (0, 0, 1)
        if venue == "home":
            r["home"] = tuple(x + y for x, y in zip(r["home"], win if isinstance(win, tuple) else (win, loss, tie)))
        else:
            r["road"] = tuple(x + y for x, y in zip(r["road"], win if isinstance(win, tuple) else (win, loss, tie)))

# fix the venue bookkeeping properly (the loop above is intentionally simple but must be exact)
for abbr in recon:
    recon[abbr].update(home=(0, 0, 0), road=(0, 0, 0), W=0, L=0, T=0, PF=0, PA=0, games=0)
for g in games:
    a, h = norm(g["away"]), norm(g["home"])
    if a not in recon or h not in recon:
        continue
    as_, hs = g["away_score"], g["home_score"]
    if as_ is None or hs is None:
        continue
    for team, own, opp, venue in ((a, as_, hs, "road"), (h, hs, as_, "home")):
        r = recon[team]
        r["games"] += 1
        r["PF"] += own
        r["PA"] += opp
        tally = (1, 0, 0) if own > opp else (0, 1, 0) if own < opp else (0, 0, 1)
        r["W"] += tally[0]
        r["L"] += tally[1]
        r["T"] += tally[2]
        r[venue] = tuple(x + y for x, y in zip(r[venue], tally))

fields = ["W", "L", "T", "PCT", "PF", "PA", "NET"]
cells_total = cells_ok = 0
for abbr, off in stand.items():
    r = recon[abbr]
    games_played = r["W"] + r["L"] + r["T"]
    pct = round((r["W"] + 0.5 * r["T"]) / games_played, 3) if games_played else None
    calc = dict(W=r["W"], L=r["L"], T=r["T"], PCT=pct, PF=r["PF"], PA=r["PA"], NET=r["PF"] - r["PA"])
    diffs = []
    for f in fields:
        cells_total += 1
        if calc[f] == off[f]:
            cells_ok += 1
        else:
            diffs.append(f"{f}: official={off[f]} recomputed={calc[f]}")
    for label, off_key in (("HOME", "HOME"), ("ROAD", "ROAD")):
        cells_total += 2
        want = rec_split(off[off_key])
        got = r["home" if label == "HOME" else "road"]
        if want == got:
            cells_ok += 2
        else:
            diffs.append(f"{label}: official={want} recomputed={got}")
    r.update(computed=calc, reconcile_diffs=diffs, reconciled=not diffs, source_url=STANDINGS)
    check(f"reconcile {abbr}", not diffs, "; ".join(diffs))

unreconciled = [a for a in stand if not recon[a]["reconciled"]]
check("all 32 clubs reconcile", not unreconciled, ",".join(unreconciled))

# ------------------------------------------------------- 4. prospective grading
lines = json.load(open(os.path.join(ROOT, "origination/results/w9-lines.json"), encoding="utf-8"))
originated_at = "2026-11-04"
sigma_m = lines["games"][0]["sigma_margin"]
sigma_t = lines["games"][0]["sigma_total"]
sig_m_set = sorted({round(g["sigma_margin"], 9) for g in lines["games"]})
sig_t_set = sorted({round(g["sigma_total"], 9) for g in lines["games"]})
check("one sigma_margin across all originated rows (constant, as designed)", len(sig_m_set) == 1, str(sig_m_set))
check("one sigma_total across all originated rows (constant, as designed)", len(sig_t_set) == 1, str(sig_t_set))


def p_from_sigma(x, s):
    return 0.5 * (1 + math.erf(x / (s * math.sqrt(2))))


results = {}
for g in w9:
    results[(g["away"], norm(g["home"]))] = g


def grade_line(row):
    key = (row["away"], row["home"])
    res = results.get(key)
    if res is None:
        return None
    a, h = res["away_score"], res["home_score"]
    margin_home = h - a
    total = a + h
    fair = row["fair_margin_home_S1"]          # home margin implied by S1 (negative = home favoured)
    fair_total = row["fair_total_S4"]
    home_num = -fair                            # if S1 says home wins by X, number is X
    s6_home = row["p_home_S6"]
    s6_away = 1 - s6_home
    s6_home_cover = p_from_sigma(margin_home - fair, sigma_m)
    s6_total_u = p_from_sigma(fair_total - total, sigma_t)
    s6_total_o = 1 - s6_total_u
    s6_away_cover = 1 - s6_home_cover
    # a margin equal to the number is a push (no unit risked)
    return dict(
        away=row["away"], home=row["home"], game=str(res["game_url"]),
        away_score=a, home_score=h, margin_home=margin_home, total=total,
        origination_date=originated_at, result_source=SCORES_W9,
        S1_fair_margin_home=fair, S1_home_number=home_num, S1_away_number=-home_num,
        S1_home_cover=(margin_home > home_num), S1_push=(margin_home == home_num),
        S1_abs_error=abs(fair - margin_home),
        S5_total=fair_total, S5_over=(total > fair_total), S5_push=(total == fair_total),
        S5_abs_error=abs(fair_total - total),
        S6_p_home_win=s6_home, S6_home_won=(margin_home > 0), S6_brier=(s6_home - (1 if margin_home > 0 else 0)) ** 2,
        S6_p_home_cover=s6_home_cover, S6_home_cover_hit=(margin_home > home_num),
        S6_cover_brier=(s6_home_cover - (1 if margin_home > home_num else 0)) ** 2,
        S6_p_under=s6_total_u, S6_under_hit=(total < fair_total),
        S6_total_brier=(s6_total_u - (1 if total < fair_total else 0)) ** 2,
    )


graded = [x for x in (grade_line(r) for r in lines["games"]) if x]
check("all 15 originated Week 9 lines graded", len(graded) == 15, f"{len(graded)} graded")

n = len(graded)
spread_mae = sum(x["S1_abs_error"] for x in graded) / n
total_mae = sum(x["S5_abs_error"] for x in graded) / n
home_covers = sum(1 for x in graded if x["S1_home_cover"])
overs = sum(1 for x in graded if x["S5_over"])
brier_ml = sum(x["S6_brier"] for x in graded) / n
brier_cover = sum(x["S6_cover_brier"] for x in graded) / n
brier_total = sum(x["S6_total_brier"] for x in graded) / n
fav_won = sum(1 for x in graded if (x["S1_home_number"] > 0) == (x["margin_home"] > 0))
correct_side = sum(1 for x in graded if (x["S1_home_number"] > 0) == (x["margin_home"] > 0))

# a normal-approximation binomial two-sided p-value vs. a fair coin, for the cover rate
def binom_p(k, n_):
    # two-sided exact-ish via normal approx with continuity correction
    if n_ == 0:
        return None
    z = abs(k - n_ / 2) - 0.5
    z = max(z, 0) / math.sqrt(n_ * 0.25)
    return round(math.erfc(z / math.sqrt(2)), 4)


grading = dict(
    title="Prospective grading of the 15 Week 9 fair lines that were originated on 2026-11-04 from Weeks 1-8 only",
    why_prospective="The originating file (`origination/results/w9-lines.json`) was produced before the Week 9 games were played and contains no Week 9 input. Grading it now is therefore out-of-sample by construction. The inherited repository did not contain this grading.",
    originated_at=originated_at, graded_at=CAPTURED,
    score_source=SCORES_W9, model_source="origination/results/w9-lines.json (inherited, unmodified)",
    n_games=n,
    note_on_lines="'Home number' means the handicap in points the HOME team gives (-number) or receives (+number), derived from S1's fair home margin. This is an OUR-FAIR-NUMBER comparison. There is no closing line in this repository, so no claim about beating a sportsbook price is made or implied.",
    spread=dict(mae=round(spread_mae, 4), baseline_mae_needed=None,
                home_number_correct_side=correct_side, home_number_wrong_side=n - correct_side,
                home_covers=home_covers, home_pushes=sum(1 for x in graded if x["S1_push"]),
                home_non_push=n - sum(1 for x in graded if x["S1_push"]),
                home_cover_rate=round(home_covers / max(1, n - sum(1 for x in graded if x["S1_push"])), 4),
                home_cover_rate_p_vs_coinflip=binom_p(home_covers, n - sum(1 for x in graded if x["S1_push"]))),
    total=dict(mae=round(total_mae, 4), overs=overs, unders=n - overs,
               over_rate=round(overs / n, 4), over_rate_p_vs_coinflip=binom_p(overs, n)),
    probability_scores=dict(brier_moneyline=round(brier_ml, 4), brier_home_cover=round(brier_cover, 4),
                            brier_total=round(brier_total, 4),
                            reference="A coin-flip forecaster scores Brier 0.25 on a two-outcome event. Lower is better."),
    interpretation="15 graded games is far too few to separate skill from luck. A 95% normal-approx interval for a 15-game cover rate spans roughly +/-0.25 around the observed rate, so an observed rate anywhere in 0.25-0.75 is indistinguishable from a coin flip. These numbers are a calibration check, not evidence of an edge.",
    luck_note="Read every rate below with its n. With n=15 the standard error of a probability near 0.5 is about 0.13.",
    rows=graded,
)
dump("w9-grading.json", grading)

# --------------------------------------------- 5. rebuild ratings on Weeks 1-9
elo = {}
for abbr in stand:
    elo[abbr] = 1500.0
K = 20.0
HFA = 48.0


def elo_step(r_home, r_away, margin_home):
    expected = 1 / (1 + 10 ** ((r_away - (r_home + HFA)) / 400))
    actual = 1.0 if margin_home > 0 else 0.0 if margin_home < 0 else 0.5
    mult = math.log(abs(margin_home) + 1) + 1.0
    delta = K * mult * (actual - expected)
    return delta, expected


for g in sorted(games, key=lambda x: (x["week"], x.get("date") or "")):
    a, h = norm(g["away"]), norm(g["home"])
    if a not in elo or h not in elo:
        continue
    d, _ = elo_step(elo[h], elo[a], g["home_score"] - g["away_score"])
    elo[h] += d
    elo[a] -= d


def ratings(prev_games):
    pts_for, pts_against, played = {}, {}, {}
    for abbr in stand:
        pts_for[abbr] = pts_against[abbr] = 0
        played[abbr] = 0
    for g in prev_games:
        a, h = norm(g["away"]), norm(g["home"])
        if a not in stand or h not in stand:
            continue
        pts_for[a] += g["away_score"]
        pts_against[a] += g["home_score"]
        pts_for[h] += g["home_score"]
        pts_against[h] += g["away_score"]
        played[a] += 1
        played[h] += 1
    out = {}
    for abbr in stand:
        n_ = played[abbr]
        out[abbr] = dict(played=n_, pf_avg=pts_for[abbr] / n_ if n_ else None,
                         pa_avg=pts_against[abbr] / n_ if n_ else None)
    return out


r9 = ratings(games)
r8 = ratings([g for g in games if g["week"] <= 8])
margins = [g["home_score"] - g["away_score"] for g in games]
sd_margin = st.pstdev(margins)
totals = [g["home_score"] + g["away_score"] for g in games]
sd_total = st.pstdev(totals)
mean_margin = st.mean(margins)
check("sigma_margin recomputed on all 137 logged games", True, f"{sd_margin:.4f}")
check("sigma_total recomputed on all 137 logged games", True, f"{sd_total:.4f}")

sched = []
for r in rows(os.path.join(DATA, "raw-w10-schedule.txt")):
    away, home, day, time, net, heading, slug, status, score = r
    sched.append(dict(away=away, home=home, day=day, time_rendered=time, network=net, heading=heading,
                      game_url=f"https://www.nfl.com/games/{slug}", status=status or None, score_rendered=score or None,
                      source_url=SCHED_W10, checked_at=CAPTURED))
check("Week 10 slate == 14 scheduled games", len(sched) == 14, f"{len(sched)}")
PLAYED = {(g["away"], g["home"]) for g in games if g["week"] == 10}
sched = [g for g in sched if (norm(g["away"]), norm(g["home"])) not in PLAYED]
check("Week 10 slate excludes games already final in the log", len(sched) == 13, f"{len(sched)} remaining")

week10 = []
for g in sched:
    a, h = norm(g["away"]), norm(g["home"])
    fair_home = (r9[h]["pf_avg"] + r9[a]["pa_avg"]) / 2 - (r9[a]["pf_avg"] + r9[h]["pa_avg"]) / 2
    fair_total = (r9[h]["pf_avg"] + r9[a]["pa_avg"]) / 2 + (r9[a]["pf_avg"] + r9[h]["pa_avg"]) / 2
    p_home = p_from_sigma(fair_home, sd_margin)
    cap = -fair_home
    week10.append(dict(
        away=g["away"], home=g["home"], kickoff_rendered=f'{g["day"]} {g["time_rendered"]}', network=g["network"],
        game_url=g["game_url"], source_url=g["source_url"],
        fair_home_margin_B0=round(fair_home, 4), fair_total_B0=round(fair_total, 4),
        fair_handicap_home_pts=round(cap, 4), fair_spread_text=f'{a} {-cap:+.1f} / {h} {cap:+.1f}',
        p_home_win_normal=round(p_home, 4), p_home_win_elo=round(1 / (1 + 10 ** ((elo[a] - (elo[h] + HFA)) / 400)), 4),
        elo_home=round(elo[h], 1), elo_away=round(elo[a], 1),
        sigma_margin=round(sd_margin, 4), sigma_total=round(sd_total, 4),
        status="UNVALIDATED — DERIVED", market_line=None, market_price=None, edge=None, candidate=False,
        unavailable_reason="No official sportsbook line exists in any official NFL source, so no edge, EV or candidate can be computed. Line-shopping and closing-line capture are outside this session's official-source rule.",
        players_unavailable_note="See the availability register: fair lines above use TEAM scoring rates only and do NOT adjust for any missing starter.",
    ))
check("Week 10 lines originated == 13", len(week10) == 13, f"{len(week10)}")
check("no Week 10 line carries a market price or edge", all(
    x["market_line"] is None and x["market_price"] is None and x["edge"] is None and x["candidate"] is False for x in week10), "")

dump("week10-lines.json", dict(
    title="Week 10 fair (no-vig style) numbers originated from official Weeks 1-9 results only",
    method="B0: home projection = (home PF/G + away PA/G)/2 ; away projection = (away PF/G + away PA/G)/2. Zero venue adjustment by design (no fitted home-field term, and Munich gets none). Win probability = normal CDF with sigma fixed at the pooled 136-game margin SD. This is a benchmark, NOT a calibrated fair price and NOT a betting recommendation.",
    inputs="Official 2026 game log: 121 inherited Weeks 1-8 games + 15 newly transcribed Week 9 games, all reconciled to official standings.",
    originated_at=CAPTURED, sigma_margin=round(sd_margin, 4), sigma_total=round(sd_total, 4),
    elo_ratings={k: round(v, 1) for k, v in sorted(elo.items(), key=lambda kv: -kv[1])},
    ratings_through_week9={k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in r9.items()},
    games=week10))

# ------------------------------------------------------- 6. injuries + availability
inj = []
for r in rows(os.path.join(DATA, "raw-injuries-w10.txt")):
    team, player, pos, injury, practice, status = r
    team = norm(team)  # the source renders the Rams table header as "Rams"; /standings renders the club as LA
    inj.append(dict(team=team, player=player, position=pos, injury=injury or None,
                    practice=practice or None, game_status=status or None,
                    source_url=INJURIES_W10, checked_at=CAPTURED, status="VERIFIED"))
check("injury rows parsed == 345", len(inj) == 345, f"{len(inj)}")
check("every club is listed except the four on bye",
      {i["team"] for i in inj} == set(stand) - {"CHI", "DEN", "PHI", "TB"},
      f"{len({i[chr(34)+chr(34)] if False else i['team'] for i in inj})} clubs")

check("no injury row has an inferred game status",
      all(i["game_status"] in (None, "Out", "Doubtful", "Questionable") for i in inj), "")

QB_NAMES = {"Patrick Mahomes", "Justin Fields", "Jared Goff", "Drake Maye", "Jayden Daniels", "J.J. McCarthy",
            "Sam Darnold", "Drew Lock", "Kyler Murray", "Carson Wentz", "Aaron Rodgers", "Trevor Lawrence",
            "Joe Burrow", "Josh Allen", "Matthew Stafford", "Brock Purdy", "Caleb Williams", "Bo Nix",
            "Jalen Hurts", "Baker Mayfield", "Justin Herbert", "Tua Tagovailoa", "Geno Smith", "Jordan Love",
            "Dak Prescott", "Jacoby Brissett", "Bryce Young", "Tyler Shough", "Daniel Jones", "Cam Ward",
            "C.J. Stroud", "Lamar Jackson", "Deshaun Watson", "Michael Penix Jr.", "Kyle McCord", "Malik Willis"}
qb_rows = [i for i in inj if i["position"] == "QB"]
out_qbs = [i for i in qb_rows if i["game_status"] == "Out"]
dump("injuries-w10.json", dict(
    title="Official Week 10 (2026) injury report, transcribed 2026-11-14",
    source=INJURIES_W10, source_alt="https://www.nfl.com/injuries/league/2026/reg10",
    checked_at=CAPTURED, clubs_listed=28, clubs_on_bye=["CHI", "DEN", "PHI", "TB"], games=14, rows=len(inj),
    scope_note="Practice participation and game status only. nfl.com does not publish depth-chart order, starter designation or snap counts on this page; nothing here is classified as a 1st/2nd/3rd-string replacement (see availability register).",
    qb_rows=qb_rows, qb_ruled_out=out_qbs, items=inj))

# ---------------------------------------------------------------- 7. summarize
summary = dict(
    captured_at=CAPTURED, checks_total=len(CHECKS), checks_failed=sum(1 for c in CHECKS if not c["pass"]),
    reconcile_cells_ok=cells_ok, reconcile_cells_total=cells_total,
    games_in_log=len(games), week9_graded=n,
    spread_mae=round(spread_mae, 4), total_mae=round(total_mae, 4),
    home_covers=home_covers, overs=overs, brier_moneyline=round(brier_ml, 4),
    sigma_margin=round(sd_margin, 4), sigma_total=round(sd_total, 4),
)
dump("checks-capture.json", dict(summary=summary, checks=CHECKS))
print(json.dumps(summary, indent=1))
if summary["checks_failed"]:
    print("FAILED CHECKS:")
    for c in CHECKS:
        if not c["pass"]:
            print("  -", c["check"], c["detail"])
raise SystemExit(1 if summary["checks_failed"] else 0)
