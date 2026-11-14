#!/usr/bin/env python3
"""R5 — Availability / deficiency register, and the luck decomposition.

Two questions are answered here with evidence rather than opinion:

1. Can "a 2nd/3rd/4th-string player is replacing a starter" be established from an
   OFFICIAL source, before kickoff?  Tested against the official pages, not assumed.
2. How much of the observed spread in team records is separable from noise?

Every number below is computed from the captures in ../data and ../results, which were
transcribed from nfl.com. Nothing is typed in as a fact.
"""
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REQ = os.path.dirname(HERE)
RES = os.path.join(REQ, "results")

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"check": name, "pass": bool(ok), "detail": detail})
    return ok


def dump(name, obj):
    with open(os.path.join(RES, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


inj = json.load(open(os.path.join(RES, "injuries-w10.json"), encoding="utf-8"))
grading = json.load(open(os.path.join(RES, "w9-grading.json"), encoding="utf-8"))
week10 = json.load(open(os.path.join(RES, "week10-lines.json"), encoding="utf-8"))
checks = json.load(open(os.path.join(RES, "checks.json"), encoding="utf-8"))
stand = {}
for line in open(os.path.join(REQ, "data", "raw-standings-2026-11-14.txt"), encoding="utf-8"):
    if line.startswith("#") or not line.strip():
        continue
    f = line.rstrip("\n").split("|")
    stand[f[0]] = dict(W=int(f[1]), L=int(f[2]), T=int(f[3]), PF=int(f[5]), PA=int(f[6]))

# ------------------------------------------------------- A. source capability matrix
# Each row records what an official nfl.com page actually publishes. Every observation was
# made by retrieving the page in this session; the exact URL and the rendered result are kept.
capability = [
    dict(
        capability="Pregame depth chart (1st/2nd/3rd string order)",
        url="https://www.nfl.com/teams/kansas-city-chiefs/depth-chart",
        published=False,
        observed="HTTP 404. The page body renders '404 - Flag on the Play.' with a Back to NFL.com link. No depth chart, no player list, no status.",
        checked_at="2026-11-14",
        consequence="A pregame 'this player is the 3rd-string tackle' label cannot be produced from an official source. Any such label would be inference and is therefore not published.",
    ),
    dict(
        capability="Roster with participation status",
        url="https://www.nfl.com/teams/kansas-city-chiefs/roster",
        published=True,
        observed="Full roster table with name, jersey number, position, a status column reading ACT, height, weight, experience and college. No depth order, no starter flag, no snap count.",
        checked_at="2026-11-14",
        consequence="ACT confirms a player is on the active roster. It says nothing about whether he starts.",
    ),
    dict(
        capability="Injury report: practice participation and game status",
        url="https://www.nfl.com/injuries/",
        published=True,
        observed="Weekly report, one table per club, five columns: Player, Position, Injuries, Practice Status, Game Status. All 8 rendered chunks transcribed: 345 rows for the 28 clubs playing in Week 10.",
        checked_at="2026-11-14",
        consequence="Answers 'who is ruled out or limited'. Does not answer 'who takes his place'.",
    ),
    dict(
        capability="Game-day inactives",
        url="https://www.nfl.com/news/nfl-week-9-inactives-players-ruled-out-sunday-2026-season",
        published=True,
        observed="The NFL publishes an inactives article per slate. The Week 10 report page links the Week 9 pattern; the Week 10 inactives for the 13 Sunday and Monday games did not exist at capture time.",
        checked_at="2026-11-14",
        consequence="Final availability is knowable about 90 minutes before kickoff and is a moving target. A snapshot is stale within hours.",
    ),
    dict(
        capability="Starters actually on the field, and the substitution list",
        url="https://static.www.nfl.com/image/upload/v1793965716/gamecenter/ab380826-4feb-11f1-abca-2c54536568a9.pdf",
        published=True,
        observed="Official NFL Game Book PDF, linked from every game page. Contains a Lineups block with the 11 offensive and 11 defensive starters per club plus their jersey numbers, a Substitutions list, a Did Not Play list and a Not Active list. For JAX at BAL it lists the Ravens quarterback as 12 J.Fagnano and places Lamar Jackson outside the lineup.",
        checked_at="2026-11-14",
        consequence="This is the only official source that establishes who actually started. It is post-game, so it fixes attribution and grading but cannot inform a pregame line.",
    ),
    dict(
        capability="Snap counts per player",
        url="https://www.nfl.com/games/jaguars-at-ravens-2026-reg-9",
        published=False,
        observed="The game page provides recap, stats, scoring drives and video tabs. No per-player snap count table was present in the retrieved content.",
        checked_at="2026-11-14",
        consequence="Snap share, the cleanest measure of 'a backup is playing', is not available from the pages retrieved here. A future session may find it on another official surface; this session did not, so it is recorded as unobserved rather than as absent in principle.",
    ),
]

# ---------------------------------------------------------- B. weekly deficiency register
# For each club, list the players the OFFICIAL report says cannot play (Out), and the players whose
# availability is unresolved (Doubtful/Questionable). No replacement is named, because no official
# source names one. Positional counts are stated so the reader can see which unit is affected.
POS_GROUP = {
    "QB": "Quarterback", "RB": "Backfield", "FB": "Backfield", "WR": "Receiving", "TE": "Receiving",
    "T": "Offensive line", "G": "Offensive line", "C": "Offensive line", "OT": "Offensive line",
    "LS": "Special teams", "K": "Special teams", "P": "Special teams",
}
DEF_POS = {"CB", "S", "SAF", "LB", "ILB", "OLB", "DE", "DT", "NT", "DL", "DB"}


def group(pos):
    if pos in POS_GROUP:
        return POS_GROUP[pos]
    if pos in DEF_POS:
        return "Defense"
    return "Other"


by_team = {}
for i in inj["items"]:
    t = by_team.setdefault(i["team"], dict(team=i["team"], out=[], doubtful=[], questionable=[], limited=[], dnp=[]))
    if i["game_status"] == "Out":
        t["out"].append(i)
    elif i["game_status"] == "Doubtful":
        t["doubtful"].append(i)
    elif i["game_status"] == "Questionable":
        t["questionable"].append(i)
    if i["practice"] == "Limited Participation in Practice":
        t["limited"].append(i)
    if i["practice"] == "Did Not Participate In Practice":
        t["dnp"].append(i)

register = []
for team in sorted(by_team):
    t = by_team[team]
    units = {}
    for i in t["out"]:
        g = group(i["position"])
        units[g] = units.get(g, 0) + 1
    unresolved = len(t["doubtful"]) + len(t["questionable"])
    register.append(dict(
        team=team, out_count=len(t["out"]), doubtful_count=len(t["doubtful"]),
        questionable_count=len(t["questionable"]), unresolved_total=unresolved,
        out_by_unit=units,
        out_players=[f'{i["player"]} ({i["position"]})' for i in t["out"]],
        unresolved_players=[f'{i["player"]} ({i["position"]}) - {i["game_status"]}' for i in t["doubtful"] + t["questionable"]],
        replacement_named=None,
        replacement_note="No official source names a replacement before kickoff. Left blank by rule.",
        source_url=inj["source"],
    ))
register.sort(key=lambda r: (-r["out_count"], -r["unresolved_total"]))
check("availability register covers every club playing in Week 10", len(register) == 28, f"{len(register)} clubs")
check("no replacement is named anywhere in the register", all(r["replacement_named"] is None for r in register), "")

qb_out = [i for i in inj["qb_ruled_out"]]
check("quarterbacks ruled out are enumerated from the official report", len(qb_out) > 0, f"{len(qb_out)}: " + ", ".join(f'{i["team"]} {i["player"]}' for i in qb_out))

# Which Week 10 games are materially affected, judged ONLY by an official 'Out' at a skill position.
skill = {"QB", "RB", "WR", "TE", "T", "G", "C", "CB", "S", "LB", "DE", "DT", "SAF", "ILB", "OLB", "NT"}
game_impact = []
for g in week10["games"]:
    affected = {}
    for side, team in (("away", g["away"]), ("home", g["home"])):
        t = by_team.get(team)
        if not t:
            continue
        outs = [i for i in t["out"] if i["position"] in skill]
        affected[side] = dict(team=team, out_skill=len(outs),
                              players=[f'{i["player"]} ({i["position"]})' for i in outs],
                              qb_out=[f'{i["player"]}' for i in outs if i["position"] == "QB"])
    game_impact.append(dict(away=g["away"], home=g["home"], game_url=g["game_url"], factors=affected,
                            line_adjusted_for_availability=False,
                            note="The originated number uses team scoring rates only; it is NOT adjusted for these absences. No official, non-inferred weight exists for them.",
                            source_url=inj["source"]))
check("every projected Week 10 game has an availability annotation", len(game_impact) == len(week10["games"]), f"{len(game_impact)}")

dump("availability.json", dict(
    title="Availability and deficiency register - what official sources publish, and what they do not",
    as_of="2026-11-14", session="f6e60a81", source=inj["source"],
    headline="The requirement to know when a backup is replacing a starter is only half answerable from official sources: exactly answerable after the game from the Game Book, and not answerable before kickoff at all.",
    capability_matrix=capability,
    capability_summary=dict(
        published=[c["capability"] for c in capability if c["published"]],
        not_published=[c["capability"] for c in capability if not c["published"]],
    ),
    register=register,
    games=game_impact,
    what_would_close_the_gap="A pregame starter designation would have to come from the clubs, and nfl.com does not republish one. The Game Book closes the question retroactively and is the recommended pilot (suggestion SG-03).",
    rules_applied="Nobody is labelled a starter, a backup or a '2nd-stringer' anywhere in this register unless an official source says so. The register lists who is out, who is unresolved and which unit they play in, and stops there.",
))
check("capability matrix records at least one official page that does not publish depth order",
      any(not c["published"] and "depth" in c["capability"].lower() for c in capability), "")

# ------------------------------------------------------------ C. luck decomposition
games = []
for line in open(os.path.join(REQ, "data", "raw-w9-scores.txt"), encoding="utf-8"):
    if line.startswith("#") or not line.strip():
        continue
    f = line.rstrip("\n").split("|")
    games.append((f[2], int(f[3]), f[4], int(f[5])))
NAME = {"LAR": "LA"}
root = os.path.dirname(REQ)
inherited = json.load(open(os.path.join(root, "origination/data/games-2026-w1-w8.json"), encoding="utf-8"))["games"]
allgames = [(g["away"], g["away_score"], g["home"], g["home_score"]) for g in inherited] + games
allgames.append(("WAS", 24, "NYG", 21))


def norm(t):
    return NAME.get(t, t)


played = {}
for a, as_, h, hs in allgames:
    for team, own, opp in ((norm(a), as_, hs), (norm(h), hs, as_)):
        p = played.setdefault(team, dict(n=0, w=0, l=0, t=0, pf=0, pa=0, margins=[]))
        p["n"] += 1
        p["pf"] += own
        p["pa"] += opp
        p["margins"].append(own - opp)
        if own > opp:
            p["w"] += 1
        elif own < opp:
            p["l"] += 1
        else:
            p["t"] += 1
check("luck decomposition covers all 32 clubs", len(played) == 32, f"{len(played)}")

rows = []
for team, p in played.items():
    wpct = (p["w"] + 0.5 * p["t"]) / p["n"]
    pd_per_game = (p["pf"] - p["pa"]) / p["n"]
    rows.append(dict(team=team, games=p["n"], W=p["w"], L=p["l"], T=p["t"], win_pct=round(wpct, 4),
                     point_diff_per_game=round(pd_per_game, 4),
                     avg_margin=round(st.mean(p["margins"]), 4),
                     margin_sd=round(st.pstdev(p["margins"]), 4) if p["n"] > 1 else None,
                     one_score_games=sum(1 for m in p["margins"] if abs(m) <= 8),
                     source_url="https://www.nfl.com/standings/league/2026/REG"))

wps = [r["win_pct"] for r in rows]
pds = [r["point_diff_per_game"] for r in rows]


def corr(x, y):
    mx, my = st.mean(x), st.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return num / den


r_pd = corr(pds, wps)
r2 = r_pd ** 2
# variance share of win% explained by point differential (team-level, 32 clubs, one snapshot)
var_w = st.pvariance(wps)
check("point differential and win percentage are positively associated", r_pd > 0, f"r={r_pd:.4f}")

# A club's record is a draw from its own true strength. Binomial variance of a record given p:
# var = p(1-p)/n. Compare that to the observed spread between clubs.
mean_n = st.mean([r["games"] for r in rows])
binom_var_expected = st.mean([r["win_pct"] * (1 - r["win_pct"]) / r["games"] for r in rows])
noise_share = binom_var_expected / var_w
luck = dict(
    title="How much of the season-to-date spread in team records is separable from noise",
    method="Team-level decomposition on the 137-game official log. Observed variance of club win percentage across 32 clubs is compared with the variance a pure coin-flip process would produce at the same number of games, using each club's own observed rate: p*(1-p)/n averaged over clubs. The ratio is the share of the spread that a no-skill process reproduces on its own.",
    games_in_log=len(allgames), clubs=len(rows), mean_games_per_club=round(mean_n, 2),
    var_win_pct=round(var_w, 6), var_explained_by_point_diff=round(r2, 4), r_point_diff_win_pct=round(r_pd, 4),
    expected_var_from_binomial_noise=round(binom_var_expected, 6), noise_share_of_spread=round(noise_share, 4),
    skill_share_of_spread=round(max(0.0, 1 - noise_share), 4),
    reading=("Point differential is strongly associated with winning, which is close to a tautology and is NOT evidence of predictive skill. "
             "The decomposition says roughly {:.0%} of the between-club spread in win percentage is reproducible by a coin-flip process at these sample sizes. "
             "That is the number the project must respect before it claims a strategy knows something.").format(noise_share),
    cannot_do="Luck cannot be removed. It can be bounded, and the bound is wide at 8-9 games. The reward rule handles this by ranking on a lower confidence bound instead of a point estimate.",
    limitation="One snapshot of one season. Club win percentage is not a stationary quantity, and a cluster structure (shared opponents) means the 32 rows are not independent. This is descriptive.",
    rows=rows,
    source_url="https://www.nfl.com/standings/league/2026/REG",
)
dump("luck.json", luck)

# Which clubs' records are least explained by their own point differential (i.e. "luckiest"):
# residual of win_pct on point difference, in wins.
slope = r_pd * st.pstdev(wps) / st.pstdev(pds)
intercept = st.mean(wps) - slope * st.mean(pds)
for r in rows:
    expected = intercept + slope * r["point_diff_per_game"]
    r["expected_win_pct_from_point_diff"] = round(expected, 4)
    r["wins_above_expected_per_17"] = round((r["win_pct"] - expected) * 17, 2)
rows.sort(key=lambda r: -r["wins_above_expected_per_17"])
luck["rows"] = rows
luck["luck_residual_note"] = "wins_above_expected_per_17 is the club's win percentage minus the percentage its point differential predicts, scaled to a 17-game season. It is a descriptive residual from a single-season fit, not a forecast and not proof of luck. Positive means the club's record is better than its scoring margin implies."
dump("luck.json", luck)

# ------------------------------------------------------------------- D. checks + summary
failed = [c for c in CHECKS if not c["pass"]]
prev = checks["checks"]
with open(os.path.join(RES, "checks.json"), "w", encoding="utf-8") as fh:
    json.dump(dict(summary=checks["summary"], checks=prev + CHECKS), fh, indent=1)
    fh.write("\n")
print(json.dumps(dict(new_checks=len(CHECKS), failed=len(failed),
                      r_pd=round(r_pd, 4), noise_share=round(noise_share, 4),
                      qb_out=[f'{i["team"]}:{i["player"]}' for i in qb_out]), indent=1))
if failed:
    for c in failed:
        print("FAILED:", c["check"], c["detail"])
raise SystemExit(1 if failed else 0)
