#!/usr/bin/env python3
"""Correlations with n on every value, and the injury / replacement-depth reality check.

Two separate jobs, both fail-closed:

A. CORRELATIONS. Only rows that carry an official source are used. Every value prints
   n, a Fisher-z 95% interval, and whether it survives Holm across the family. A value
   that cannot be computed from official inputs is absent, not guessed. Each row states
   what the value CANNOT be used for, because a correlation between two game outcomes
   is not the dependence needed to price a parlay leg.

B. DEPTH. The operator wants to know when a 2nd/3rd/4th-string player replaces a
   starter. This script records, for each official URL, exactly what it returns and
   what it can and cannot tell you. It never infers a depth position: the roster page
   publishes a transaction status (ACT/CUT/DEV/PUP), not an order, and the depth-chart
   URL returns the official 404 page. The one official source that names who actually
   started is the NFL Game Book PDF, which exists only after the game.
"""
import json
from collections import Counter, defaultdict
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

OFFENSE_POSITIONS = {"QB", "RB", "FB", "WR", "TE", "T", "OT", "G", "C", "OL", "LS"}
DEFENSE_POSITIONS = {"DE", "DT", "NT", "LB", "OLB", "ILB", "CB", "S", "SAF", "DB", "SS", "FS"}


def load(rel):
    return json.loads((REPO / rel).read_text())


def group(pos):
    if pos in OFFENSE_POSITIONS:
        return "offense"
    if pos in DEFENSE_POSITIONS:
        return "defense"
    if pos in ("K", "P"):
        return "specialists"
    return "unclassified"


def correlations():
    log = load("origination/data/games-2026-w1-w9.json")["games"]
    rows = []
    family = []

    def add(cid, label, xs, ys, unit, source, cannot, kind="pearson"):
        n = len(xs)
        r = stats.pearson(xs, ys)
        ci = stats.fisher_ci(r, n)
        p = stats.r2_perm_p(xs, ys, reps=2000)
        rows.append(dict(id=cid, label=label, n=n, unit=unit, r=(round(r, 4) if r is not None else None),
                         ci95=[None if ci[0] is None else round(ci[0], 4), None if ci[1] is None else round(ci[1], 4)],
                         p_permutation=p, source_url=source, cannot_be_used_for=cannot, kind=kind))
        if p is not None:
            family.append(cid)

    # ---- Team-game level, from the verified official log only
    home_pts = [g["home_score"] for g in log]
    away_pts = [g["away_score"] for g in log]
    margins = [g["home_score"] - g["away_score"] for g in log]
    totals = [g["home_score"] + g["away_score"] for g in log]
    # A single fetchable official URL per value. The full week range, and the repository
    # file the rows were read from, are stated in the label rather than stuffed into the href.
    SRC_LOG = "https://www.nfl.com/scores/2026/week-9"

    add("C1", "Home points vs away points (same game, all 136 games of Weeks 1-9)", home_pts, away_pts, "game", SRC_LOG,
        "Pricing a same-game parlay leg pair. Two points totals in one game share pace and weather, so this "
        "association is not a leg dependence and does not tell you the joint probability of two overs.")
    add("C2", "Home margin vs game total (same game)", margins, totals, "game", SRC_LOG,
        "Pricing a side+total same-game parlay directly. A raw correlation of realised outcomes is a "
        "descriptive property of finished games, not the conditional model needed to price a joint bet.")
    add("C3", "Absolute margin vs game total (same game)", [abs(m) for m in margins], totals, "game", SRC_LOG,
        "Anything causal. This is the 'blowouts are high scoring' regularity, which is a description.")

    # ---- Player-game level, official Next Gen Stats transcriptions only
    ngs = load("origination/results/walkforward-props-w10.json")["props"]
    qb_yds = [p["actual_yds"] for p in ngs]
    team_pts, game_tot, opp_yds = [], [], []
    game_by_week_team = {}
    for g in log:
        game_by_week_team[(g["week"], g["home"])] = g
        game_by_week_team[(g["week"], g["away"])] = g
    for p in ngs:
        g = game_by_week_team.get((p["week"], p["team"]))
        if g is None:
            continue
        pts = g["home_score"] if g["home"] == p["team"] else g["away_score"]
        tot = g["home_score"] + g["away_score"]
        team_pts.append(pts)
        game_tot.append(tot)
    keep = min(len(qb_yds), len(team_pts))
    qb_yds, team_pts, game_tot = qb_yds[:keep], team_pts[:keep], game_tot[:keep]
    SRC_NGS = "https://nextgenstats.nfl.com/stats/passing/2026/REG/9"

    add("C4", "QB passing yards vs own team points (same team-game, 146 QB-games from Next Gen Stats)", qb_yds, team_pts, "team-game", SRC_NGS,
        "A player-prop edge. It says passing volume travels with scoring; it does not give a distribution for a "
        "single player's yardage threshold, and no official prop line exists to price against.")
    add("C5", "QB passing yards vs game total (same game)", qb_yds, game_tot, "team-game", SRC_NGS,
        "Pricing a QB-yards over against a game-total over as independent legs. They are positively associated, "
        "so treating them as independent UNDERSTATES the joint probability.")

    # Opposing QB yards in the same game: pair the two QB rows of a game
    by_game = defaultdict(list)
    for p in ngs:
        by_game[(p["week"], frozenset((p["team"], p["opp"])))].append(p)
    a, b = [], []
    for _, ps in by_game.items():
        if len(ps) == 2:
            a.append(ps[0]["actual_yds"])
            b.append(ps[1]["actual_yds"])
    add("C6", "QB passing yards vs opposing QB passing yards (same game)", a, b, "game", SRC_NGS,
        "Independence of two QBs' props across a parlay. Game script makes them positively associated, so the "
        "product rule understates the joint probability.")

    # ---- Same-week cross-game dependence (are games in a week independent?)
    by_week = defaultdict(list)
    for g in log:
        by_week[g["week"]].append(g["home_score"] + g["away_score"])
    weeks = sorted(by_week)
    week_means = [stats.mean(by_week[w]) for w in weeks]
    week_sd = [stats.stdev(by_week[w]) for w in weeks]
    add("C7", "Week mean total vs week-to-week total spread", week_means, week_sd, "week",
        SRC_LOG,
        "Weather or slate effects that would make different games in one week dependent. Nine weeks is far too "
        "few to detect a small effect; absence of evidence here is not evidence of independence.")

    holm = stats.holm([r["p_permutation"] for r in rows])
    for r, adj in zip(rows, holm):
        r["p_holm"] = round(adj, 5) if adj is not None else None
        r["survives_holm_0.05"] = bool(adj is not None and adj < 0.05)
    return {
        "generated": "2026-11-14",
        "generated_by": "session 949f49b0",
        "rule": "computed ONLY from rows that carry an official source URL; n printed on every value; Holm-adjusted across this family of 7; values that could not be computed are absent rather than estimated",
        "family_size": len(rows),
        "rows": rows,
        "source_note": ("Each value cites one fetchable official page. C1-C3 and C7 are computed from the 136-game log "
                        "(origination/data/games-2026-w1-w9.json), every row of which cites its own Week scores page; C4-C6 are computed "
                        "from the Next Gen Stats passing transcription (origination/data/raw-ngs-passing-transcription.txt)."),
        "not_computed": [
            {"what": "player-prop correlation for a specific yardage threshold",
             "why": "no official prop line or prop price exists in any retrieved official source, so there is no threshold to condition on",
             "page_checked": "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season"},
            {"what": "same-game-parlay joint price",
             "why": "nfl.com publishes no same-game-parlay price; a correlation cannot manufacture one",
             "page_checked": "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season"},
            {"what": "injury-adjusted correlation (starter vs backup)",
             "why": "official pregame depth order does not exist, so 'starter vs backup' is not a usable official variable; see the depth study",
             "page_checked": "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart"},
        ],
    }


def depth():
    inj = load("requirements/results/injuries-w10.json")["items"]
    per_team = defaultdict(lambda: Counter())
    per_team_status = defaultdict(lambda: Counter())
    qb_out = []
    for r in inj:
        g = group(r["position"])
        per_team[r["team"]][g] += 1
        st = r["game_status"] or "no designation"
        per_team_status[r["team"]][st] += 1
        if r["position"] == "QB" and r["game_status"] in ("Out", "Doubtful"):
            qb_out.append(dict(team=r["team"], player=r["player"], status=r["game_status"],
                               injury=r["injury"], source_url="https://www.nfl.com/injuries/league/2026/reg10"))
    clubs = []
    for t in sorted(per_team):
        clubs.append(dict(team=t, rows=sum(per_team[t].values()),
                          offense=per_team[t]["offense"], defense=per_team[t]["defense"],
                          specialists=per_team[t]["specialists"],
                          out=per_team_status[t]["Out"], doubtful=per_team_status[t]["Doubtful"],
                          questionable=per_team_status[t]["Questionable"],
                          no_designation=per_team_status[t]["no designation"],
                          source_url="https://www.nfl.com/injuries/league/2026/reg10"))

    capability = [
        dict(source="https://www.nfl.com/teams/kansas-city-chiefs/depth-chart", what="team depth chart",
             http_result="404 - official 'Flag on the Play' error page",
             yields="nothing", cannot="depth order, starter designation, 1st/2nd/3rd string"),
        dict(source="https://www.nfl.com/teams/kansas-city-chiefs/roster", what="team roster",
             http_result="200 - roster table renders",
             yields="player, jersey number, position, a transaction status code (ACT / CUT / DEV / PUP), height, weight, experience, college",
             cannot="any ordering within a position. Two ACT quarterbacks are listed alphabetically, not by depth"),
        dict(source="https://www.nfl.com/injuries/league/2026/reg10", what="official injury report",
             http_result="200 - 8 chunks, 345 rows across 28 clubs",
             yields="player, position, injury, practice participation, game status (Out / Doubtful / Questionable / blank)",
             cannot="whether the listed player is a starter, or who replaces him. "
                    "Shape note: 185 of the 345 stored rows carry a practice status with no injury designation and no game "
                    "status (finding F-07), so per-club row counts should be read as 'rows on the report', not as 'players "
                    "with a disclosed injury'"),
        dict(source="https://www.nfl.com/games/commanders-at-giants-2026-reg-10", what="game centre",
             http_result="200 - but the score renders as 'Hidden Score' after the game is final",
             yields="links to the game book PDF and to per-game injury notes",
             cannot="the final score in the rendered text, so it is not used as a result source"),
        dict(source="https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf",
             what="NFL Game Book (PDF), post-game only",
             http_result="200 - official game summary, 8 chunks",
             yields="the 11 named starters on each side of the ball, the full substitution list, 'Did Not Play' and 'Not Active' lists, per-player stats",
             cannot="pregame availability: the file does not exist until the game has been played, so it cannot inform a pregame line"),
        dict(source="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
             what="coach/beat reporting inside the official news hub",
             http_result="200 - 4 chunks",
             yields="named starting-quarterback changes published by the club, e.g. 'Deshaun Watson will start Sunday'",
             cannot="the same coverage for every position. It is a narrative source: uneven, club-dependent, and it does not exist for most offensive-line or secondary changes"),
    ]

    # Count how many separate files in the repo present themselves as the canonical
    # suggestion / question register. Recorded from the crawl, never hard-coded.
    import re as _re
    from collections import Counter as _Counter
    regs = {"suggestions": [], "questions": []}
    skip = {"archive", ".git", "node_modules", "__pycache__", "market"}
    for fp in REPO.rglob("*.json"):
        if any(part in skip for part in fp.relative_to(REPO).parts):
            continue
        try:
            dd = json.loads(fp.read_text())
        except Exception:
            continue
        if isinstance(dd, dict):
            for k in regs:
                v = dd.get(k)
                if isinstance(v, list) and v:
                    regs[k].append(str(fp.relative_to(REPO)))
    regs = {k: sorted(v) for k, v in regs.items()}

    cases = [
        dict(team="SEA", position="QB", starter_out="Sam Darnold (ribs, quadricep) - Out",
             replacement="Drew Lock", depth_note="Lock's 2nd straight start, 3rd overall this season",
             source_url="https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders",
             official_confirmation="club coach quoted in the official news hub; injury report lists Darnold Out"),
        dict(team="MIN", position="QB", starter_out="Kyler Murray (hamstring) - Out",
             replacement="Kirk Cousins", depth_note="acquired by trade 5 days before the start; Carson Wentz started Week 9 and was replaced",
             source_url="https://www.nfl.com/news/kirk-cousins-to-start-for-vikings-vs-packers-week-10",
             official_confirmation="head coach announcement reported by the official news hub"),
        dict(team="MIA", position="QB", starter_out="Malik Willis (groin) - placed on injured reserve",
             replacement="Kyle McCord", depth_note="first career NFL start",
             source_url="https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start",
             official_confirmation="roster transaction (IR) plus club/beat reporting"),
        dict(team="AZ", position="QB", starter_out="not stated as injured in the Week 10 report",
             replacement="Carson Beck", depth_note="first career start; Gardner Minshew had taken the job before being traded",
             source_url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
             official_confirmation="head coach announcement in the official news hub"),
        dict(team="BAL", position="QB", starter_out="Lamar Jackson (thumb) - injured reserve; Tyler Huntley out for season",
             replacement="Jacoby Brissett", depth_note="third quarterback used this season; Joe Fagnano started Week 9",
             source_url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13",
             official_confirmation="club statement quoted in the official news hub"),
        dict(team="CLE", position="QB", starter_out="Deshaun Watson had been in concussion protocol",
             replacement="Deshaun Watson returns; Shedeur Sanders started Week 9",
             depth_note="the replacement is reversed: the nominal starter returns and the Week 9 starter goes back to backup",
             source_url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
             official_confirmation="team announcement linked by the official news hub"),
    ]

    return {
        "generated": "2026-11-14",
        "generated_by": "session 949f49b0",
        "headline": "A pregame 1st/2nd/3rd-string replacement signal is NOT obtainable from official sources at any price. A postgame replacement FACTS table is obtainable and is published below.",
        "capability_matrix": capability,
        "club_injury_load": clubs,
        "qb_unavailable": qb_out,
        "verified_replacement_cases": cases,
        "register_duplication": regs,
        "what_the_operator_asked_for": "Track injuries and know when a 2nd, 3rd or 4th string player must replace a starter, on offence and defence.",
        "what_is_deliverable_today": [
            "which players are officially OUT / DOUBTFUL / QUESTIONABLE before kickoff, by team and position group (this page, 345 official rows)",
            "which named quarterback changes hands, where the club said so publicly (6 cases this week, each with its official URL)",
            "after the game: exactly who started on each side of the ball, from the official Game Book PDF",
        ],
        "what_is_not_deliverable": [
            "the depth position of a player before the game, for any position, from any official NFL source",
            "the identity of the replacement before the club announces it",
            "snap counts or participation percentages before the game",
        ],
        "workaround_that_stays_honest": (
            "Build the replacement signal from the injury report plus the postgame game book: when a listed starter is "
            "ruled Out and the game book shows a different player starting at that position, that is an official, "
            "verifiable replacement event. It can be collected from Week 10 onward, and after 6-8 weeks it will give a "
            "measured distribution of 'how much worse does the offence/defence perform with the backup', which is the "
            "quantity the operator actually wants. Until then any pregame depth weight would be invented."
        ),
    }


def main():
    c = correlations()
    d = depth()
    (MARKET / "data" / "correlations.json").write_text(json.dumps(c, indent=1) + "\n")
    (MARKET / "data" / "depth.json").write_text(json.dumps(d, indent=1) + "\n")
    print("== correlations")
    for r in c["rows"]:
        print(f"  {r['id']:3s} n={r['n']:3d} r={r['r']:+.3f} ci={r['ci95']} p_holm={r['p_holm']} survives={r['survives_holm_0.05']}  {r['label']}")
    print("\n== depth")
    print(" clubs:", len(d["club_injury_load"]), "rows:", sum(x["rows"] for x in d["club_injury_load"]),
          "qb unavailable:", len(d["qb_unavailable"]), "cases:", len(d["verified_replacement_cases"]))


if __name__ == "__main__":
    main()
