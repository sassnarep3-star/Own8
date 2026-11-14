#!/usr/bin/env python3
"""Build the NFL hub static site (hub/index.html + hub/pages/*.html).

Inputs (read-only):
  hub/data/standings-official.csv   official nfl.com standings (transcribed, see sources)
  hub/data/injuries-w10.csv         official nfl.com Week 10 injury report rows (partial)
  hub/data/content.json             review, questions, suggestions, flags, sources
  origination/results/*.json        earlier session outputs, re-published unchanged
  origination/data/games-2026-w1-w8.json  repo game log (used only for reconciliation)

Standard library only.  Run from anywhere:  python3 hub/scripts/build_hub.py
"""
import csv
import html
import json
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent
ROOT = HUB.parent
DATA = HUB / "data"
PAGES = HUB / "pages"
ORIG = ROOT / "origination"

TODAY = "2026-11-14"
REPO_BLOB = "https://github.com/sassnarep3-star/Own8/blob/arena/101b20bc-own8/"
STANDINGS_URL = "https://www.nfl.com/standings/"
INJURY_URL = "https://www.nfl.com/injuries/league/2026/reg10"
FINAL_JAX_BAL = {  # only game whose official final was checked (source S3)
    "JAX@BAL": (33, 10, "https://www.nfl.com/games/jaguars-at-ravens-2026-reg-9"),
}

NAV = [
    ("index.html", "Dashboard"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/standings.html", "Standings"),
    ("pages/injuries.html", "Injuries and depth"),
    ("pages/lines.html", "Lines"),
    ("pages/strategies.html", "Strategies"),
    ("pages/correlations.html", "Correlations"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/questions.html", "Questions"),
    ("pages/repo-review.html", "Repo review"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/sources.html", "Sources"),
]


def esc(v):
    return html.escape("" if v is None else str(v))


def link(url, text=None):
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener">{esc(text or url)}</a>'


def links(urls):
    return "<br>".join(link(u) for u in urls) if urls else '<span class="unv">none</span>'


def table(headers, rows, cls=""):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    return f'<div class="tw"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def page(path_rel, title, body, active):
    depth = path_rel.count("/")
    prefix = "../" * depth
    nav = "".join(
        f'<a href="{prefix}{href}"{" class=on" if href == active else ""}>{esc(label)}</a>'
        for href, label in NAV
    )
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NFL hub</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<header class="top"><div class="brand"><a href="{prefix}index.html">NFL hub</a><span>2026 season · data as of {TODAY}</span></div>
<nav>{nav}</nav></header>
<main>
<h1>{esc(title)}</h1>
{body}
</main>
<footer>Derived values are project calculations, not official NFL data, betting advice or a recommendation. Blank cells are unverified and flagged. No rewards are awarded. Responsible gaming: <a href="https://ask.gov.sg/mha/questions/cmqu6lgkk008f4401iyk6rjzx">Singapore MHA gambling information</a>.</footer>
</body></html>
"""
    out = HUB / path_rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_doc, encoding="utf-8")


def load_content():
    return json.loads((DATA / "content.json").read_text(encoding="utf-8"))


def load_standings():
    with open(DATA / "standings-official.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_injuries():
    with open(DATA / "injuries-w10.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def repo_w1_w8():
    games = json.loads((ORIG / "data" / "games-2026-w1-w8.json").read_text(encoding="utf-8"))["games"]
    log = {}

    def add(team, pf, pa):
        d = log.setdefault(team, dict(w=0, l=0, t=0, pf=0, pa=0, gp=0))
        d["pf"] += pf
        d["pa"] += pa
        d["gp"] += 1
        if pf > pa:
            d["w"] += 1
        elif pf < pa:
            d["l"] += 1
        else:
            d["t"] += 1

    for g in games:
        add(g["away"], g["away_score"], g["home_score"])
        add(g["home"], g["home_score"], g["away_score"])
    if "LAR" in log and "LA" not in log:  # repo uses LAR; nfl.com standings use LA
        log["LA"] = log.pop("LAR")
    return log, len(games), max(g["week"] for g in games)


def build_standings(rows, log):
    body_rows = []
    totals = dict(w=0, l=0, t=0, pf=0, pa=0)
    for r in rows:
        w, l, t = int(r["w"]), int(r["l"]), int(r["t"])
        pf, pa = int(r["pf"]), int(r["pa"])
        for k, v in (("w", w), ("l", l), ("t", t), ("pf", pf), ("pa", pa)):
            totals[k] += v
        lg = log.get(r["abbr"], dict(w=0, l=0, t=0, gp=0))
        since = (w - lg["w"]) + (l - lg["l"]) + (t - lg["t"])
        body_rows.append([
            esc(r["conf"]), esc(r["team"]), esc(r["abbr"]),
            f"{w}-{l}-{t}", str(pf), str(pa), esc(r["net"]),
            esc(r["home"]), esc(r["road"]), esc(r["div"]), esc(r["conf_rec"]), esc(r["strk"]),
            f"{lg['w']}-{lg['l']}-{lg['t']}", str(since),
            link(STANDINGS_URL, "nfl.com/standings"),
        ])
    checks = (
        f"League totals: W {totals['w']} / L {totals['l']} / T {totals['t']}; "
        f"PF {totals['pf']} / PA {totals['pa']}. "
        + ("PASS: wins = losses and PF = PA." if totals["w"] == totals["l"] and totals["pf"] == totals["pa"] else "FAIL: totals do not balance.")
    )
    return body_rows, checks


def build_injuries(rows):
    out = []
    for r in rows:
        note = r["coverage_note"] or ""
        out.append([
            esc(r["block"]), esc(r["kickoff_et"]), esc(r["network"]), esc(r["team"]),
            esc(r["player"]), esc(r["position"]), esc(r["injury"]),
            esc(r["practice_status"]), esc(r["game_status"]) or '<span class="unv">blank</span>',
            esc(note), link(INJURY_URL, "nfl.com injury report"),
        ])
    return out


def main():
    content = load_content()
    standings = load_standings()
    injuries = load_injuries()
    log, n_games, max_week = repo_w1_w8()
    w9 = json.loads((ORIG / "results" / "w9-lines.json").read_text(encoding="utf-8"))
    lb = json.loads((ORIG / "results" / "leaderboard.json").read_text(encoding="utf-8"))
    corr = json.loads((ORIG / "results" / "correlations.json").read_text(encoding="utf-8"))

    st_rows, st_check = build_standings(standings, log)
    inj_rows = build_injuries(injuries)
    n_pass = sum(1 for s in lb["strategies"] if s.get("medal") or s.get("verdict", "").upper().startswith("PASS"))
    n_strat = len(lb["strategies"])
    n_w9 = len(w9["games"])
    n_inj_games = len({(r["block"]) for r in injuries})
    n_inj_full = len({r["block"] for r in injuries if r["block"] != "E"})
    since_w8_teams = sum(1 for s in standings if (int(s["w"]) + int(s["l"]) + int(s["t"])) - log.get(s["abbr"], {"gp": 0})["gp"] > 0)

    # ---------- Landing ----------
    cards = [
        (f"{n_games}", "official games in repo log", f"Weeks 1-{max_week} only"),
        (f"{len(standings)}/32", "standings rows captured", f"nfl.com standings as of {TODAY}"),
        (f"{since_w8_teams}", "teams with games after Week 8", "official standings vs repo log"),
        (f"{n_pass}/{n_strat}", "strategies passing all gates", "no rewards or medals"),
        (f"{len(injuries)}", "Week 10 injury rows transcribed", "blocks A-D complete, E partial"),
        (f"{len(content['flags'])}", "items flagged for review", "see Flagged for review"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="big">{esc(a)}</div><div class="lbl">{esc(b)}</div><div class="sub">{esc(c)}</div></div>'
        for a, b, c in cards
    )
    tiles = [
        ("pages/executive-summary.html", "Executive summary", "What matters, in one page"),
        ("pages/standings.html", "Standings", "All 32 official rows, reconciled to the repo log"),
        ("pages/injuries.html", "Injuries and depth", "Week 10 official injury rows, backup gaps"),
        ("pages/lines.html", "Lines", "Week 9 fair lines (already played)"),
        ("pages/strategies.html", "Strategies", "12 strategies, gates G1-G8, leaderboard"),
        ("pages/correlations.html", "Correlations", "Measured dependence and combo pricing"),
        ("pages/suggestions.html", "Suggestions", "Options for you to choose. Nothing implemented"),
        ("pages/questions.html", "Questions", "What is known, unknown and how to find it"),
        ("pages/repo-review.html", "Repo review", "Irregularities with source links"),
        ("pages/flagged.html", "Flagged for review", "Every flag, with links to check"),
        ("pages/sources.html", "Sources", "Official pages used and their limits"),
    ]
    tile_html = "".join(
        f'<a class="tile" href="{href}"><b>{esc(t)}</b><span>{esc(d)}</span></a>' for href, t, d in tiles
    )
    index_body = f"""
<p class="lead">A plain dashboard for the 2026 NFL research project. Every table row links to an official page or to the repo file it came from. Values that could not be confirmed are left blank and flagged. Nothing here is a betting recommendation.</p>
<div class="cards">{card_html}</div>
<h2>Start here</h2>
<div class="tiles">{tile_html}</div>
<h2>Current status</h2>
<ul>
<li><b>Data is stale.</b> The repo's official game log stops at Week 8. nfl.com shows more games since then (see Standings).</li>
<li><b>No strategy passes validation.</b> Zero strategies have earned a medal or any reward.</li>
<li><b>Injury coverage is partial.</b> Four Week 10 game blocks are transcribed; one more is partial; the rest are not yet captured.</li>
<li><b>Depth charts are not tracked.</b> No verified source for second- and third-string players exists yet.</li>
</ul>
"""
    page("index.html", "NFL hub · 2026 dashboard", index_body, "index.html")

    # ---------- Executive summary ----------
    exec_body = f"""
<p class="lead">Summary as of {TODAY}. Each statement points to a page with its source.</p>
<h2>1. The official picture is newer than the repo</h2>
<ul>
<li>The official standings pass arithmetic checks: league wins equal losses and points for equal points against (see <a href="standings.html">Standings</a>).</li>
<li>Repo game log: <b>{n_games} games</b>, Weeks 1-{max_week}. Official standings show <b>{since_w8_teams} of 32 teams</b> have a game since Week 8. Week 9 has 15 games, and PIT and TEN had byes.</li>
<li>Week 9 fair lines (<a href="lines.html">Lines</a>) price games that are already final. One checked result: JAX 33 - BAL 10 on Nov 5.</li>
</ul>
<h2>2. Strategy validation</h2>
<ul>
<li><b>{n_pass} of {n_strat}</b> strategies pass all validation gates. No medals, ranks or rewards. The two highest single-bet scores (S6 moneyline, S1 spread) are about 1.7% better than baseline, and their 95% intervals include zero.</li>
<li>Sportsbook-priced strategies cannot be validated: no official source publishes betting lines (see <a href="questions.html">Questions</a> Q-08).</li>
</ul>
<h2>3. Correlations</h2>
<ul>
<li>Same-game team points: r = 0.10, not significant after multiplicity control. Cross-game total residuals in the same week: ICC about -0.04 (no weekly shared effect). Measured correlations are in <a href="correlations.html">Correlations</a>.</li>
</ul>
<h2>4. Injuries and depth</h2>
<ul>
<li>Week 10 official injury report: block A-D complete (four games); block E (JAX at TEN) partial. The remaining games are not yet captured.</li>
<li>No second- or third-string depth data exists. Replacement analysis cannot be run yet. See <a href="suggestions.html">Suggestions</a> SG-03.</li>
</ul>
<h2>5. Decisions needed from you</h2>
<ul>
<li>Ten suggestions are listed on <a href="suggestions.html">Suggestions</a> with options. Nothing has been implemented.</li>
<li>Singapore law: the MHA page says all gambling is prohibited unless licensed; Singapore Pools is the only licensed remote operator (<a href="questions.html">Q-09</a>). This is not a legal opinion.</li>
</ul>
<h2>6. Irregularities</h2>
<ul>
<li>Third-party odds are tracked in Git (R-03). Compiled Python files are tracked (R-04). Nine parallel sites exist (R-05). Full list: <a href="repo-review.html">Repo review</a>.</li>
</ul>
"""
    page("pages/executive-summary.html", "Executive summary", exec_body, "pages/executive-summary.html")

    # ---------- Standings ----------
    st_body = f"""
<p class="lead">Official 2026 standings, captured {TODAY}. The last two columns compare each team with the repo's Week 1-{max_week} game log. A value of 0 in the last column means no game since Week {max_week}.</p>
<p class="note"><b>Reconciliation:</b> {esc(st_check)}</p>
{table(["Conf","Team","Abbr","W-L-T","PF","PA","Net","Home","Road","Div","Conf rec","Streak","Repo W-L-T (W1-8)","Games since W8","Source"], st_body_rows(st_rows))}
"""
    page("pages/standings.html", "Standings", st_body, "pages/standings.html")

    # ---------- Injuries ----------
    inj_body = f"""
<p class="lead">Week 10 official injury report. Transcribed from nfl.com chunks 0-1 of 8. Only rows with an injury, practice or game status are listed.</p>
<div class="box"><b>Coverage:</b> blocks A-D complete ({n_inj_full} blocks listed as complete). Block E (JAX at TEN) is partial, and the rest are not yet captured. This is {len(injuries)} rows, not the full report.</div>
<h2>Injury rows</h2>
{table(["Block","Kickoff (ET)","Network","Team","Player","Pos","Injury","Practice","Game status","Note","Source"], inj_rows)}
<h2>Backups and depth: what is missing</h2>
<div class="tw"><table><thead><tr><th>Need</th><th>Status</th><th>Source checked</th></tr></thead><tbody>
<tr><td>2nd- and 3rd-string replacements per position</td><td>Not tracked. No verified official depth-chart source.</td><td>{link("https://www.nfl.com/teams/buffalo-bills/roster", "nfl.com roster (status only)")}</td></tr>
<tr><td>Game-day inactive lists</td><td>Not captured.</td><td>{link("https://www.nfl.com/schedules/2026/by-week/week-10", "nfl.com Week 10 schedule (game pages)")} <span class="unv">inactives not verified</span></td></tr>
<tr><td>Starting QB per game</td><td>Not confirmed for any game.</td><td>{link(INJURY_URL, "injury report (status only)")}</td></tr>
</tbody></table></div>
"""
    page("pages/injuries.html", "Injuries and depth", inj_body, "pages/injuries.html")

    # ---------- Lines ----------
    line_rows = []
    for g in w9["games"]:
        key = f"{g['away']}@{g['home']}"
        final = FINAL_JAX_BAL.get(key)
        if final:
            res = f"{g['away']} {final[0]} - {g['home']} {final[1]} (Final)"
            res_link = link(final[2], "nfl.com game page")
        else:
            res = '<span class="unv">Unverified: final not captured</span>'
            res_link = link(g["game_url"], "nfl.com game page (not checked)")
        line_rows.append([
            esc(f"{g['away']} at {g['home']}"),
            esc(g["day"] + ", " + g["time_as_rendered"]),
            esc(g["fair_spread_text"]),
            f"{g['fair_total_S4']:.1f}",
            f"{g['p_home_S6']*100:.1f}%",
            f"{g['fair_ml_home']:+d} / {g['fair_ml_away']:+d}",
            res, res_link,
        ])
    lines_body = f"""
<p class="lead">{n_w9} Week 9 fair lines originated from official W1-W8 data by the earlier session. They are <b>historical</b> now: the games have been played. They are not forecasts.</p>
<div class="box"><b>Model notes (from origination):</b> {esc(w9['description'])}</div>
{table(["Game (away at home)","Kickoff (as rendered)","Fair spread (model)","Fair total (S4)","Home win prob (S6)","Fair moneyline H / A","Result","Source"], line_rows)}
<p class="note">Original file: <a href="{REPO_BLOB}origination/results/w9-lines.json">origination/results/w9-lines.json</a></p>
"""
    page("pages/lines.html", "Lines (Week 9, already played)", lines_body, "pages/lines.html")

    # ---------- Strategies ----------
    gate_rows = []
    for s in lb["strategies"]:
        g = s.get("gates", {})
        passed = sum(1 for v in g.values() if v is True)
        applicable = sum(1 for v in g.values() if v is not None)
        failed = [k for k, v in sorted(g.items()) if v is False]
        ci = s.get("ci95") or [None, None]
        gate_rows.append([
            esc(s["id"]), esc(s["product"]), esc(s["strategy"]), str(s.get("n", "")),
            f"{s['skill_pct']:.2f}", f"{s['skill_pct_lcb']:.2f}", f"{s['p_one_sided']:.3f}",
            f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci[0] is not None else "",
            f"{passed}/{applicable}", esc(", ".join(failed) or "none"),
            esc(s.get("verdict", "") or "BLOCKED"),
            links([f"{REPO_BLOB}origination/results/leaderboard.json", "https://www.nfl.com/scores/2026/week-8"]),
        ])
    for ns in lb["not_scored"]:
        gate_rows.append([
            esc(ns["id"]), esc(ns["product"]), esc(ns["strategy"]), "", "", "", "", "",
            "", esc("G8 (no market data)"), esc(ns.get("verdict", "NOT SCORED")),
            links([f"{REPO_BLOB}origination/results/leaderboard.json"]),
        ])
    strat_body = f"""
<p class="lead">{n_strat} strategies and {len(lb['not_scored'])} market-based ideas were pre-registered in the earlier session. A strategy must pass <b>all</b> gates G1-G8 to rank. Gate definitions and the leaderboard file are in <a href="{REPO_BLOB}origination/results/leaderboard.json">origination/results/leaderboard.json</a>.</p>
<div class="box"><b>Result:</b> {n_pass} of {n_strat} strategies pass all gates. No leaderboard ranks, no medals and no rewards are awarded. The skill score is percent loss reduction versus a naive baseline; the lower bound is the 95% bootstrap bound.</div>
{table(["ID","Product","Strategy","n","Skill %","Skill lower bound %","One-sided p","95% CI (mean loss diff)","Gates passed","Failed gates","Verdict","Source"], gate_rows)}
<p class="note">Gate definitions: G1 official data; G2 no leakage; G3 sample size; G4 paired bootstrap CI below zero; G5 Holm-adjusted permutation p &lt; 0.05; G6 both halves positive; G7 calibration; G8 no market data.</p>
"""
    page("pages/strategies.html", "Strategies and validation gates", strat_body, "pages/strategies.html")

    # ---------- Correlations ----------
    c_rows = []
    for c in corr["correlations"]:
        c_rows.append([
            esc(c["id"]), esc(c["pair"]), str(c.get("n", "")),
            f"{c['r']:+.3f}", f"[{c['ci95'][0]:+.2f}, {c['ci95'][1]:+.2f}]" if c.get("ci95") else "",
            f"{c['p_two_sided']:.3f}" if c.get("p_two_sided") is not None else "",
            f"{c['p_holm']:.3f}" if c.get("p_holm") is not None else "",
            "yes" if c.get("significant_after_holm") else "no",
            esc(c.get("scope", "")),
            links([f"https://www.nfl.com/scores/2026/week-{w}" for w in range(1, 9)]),
        ])
    icc_rows = []
    for c in corr["cross_game_dependence"]:
        icc_rows.append([
            esc(c["id"]), esc(c["pair"]), str(c.get("n", "")), f"{c['icc']:+.3f}", esc(c.get("scope", "")),
            esc(c.get("use", "")), links([f"https://www.nfl.com/scores/2026/week-{w}" for w in range(1, 9)]),
        ])
    combo_rows = []
    for c in corr["combo_pricing"]:
        combo_rows.append([
            esc(c["id"]), esc(c["combo"]), f"{c['r_measured']:+.3f}", f"{c['r_used']:+.3f}",
            f"{c['joint_prob_both_over']:.3f}" if c.get("joint_prob_both_over") is not None else "",
            str(c.get("fair_odds", "")), esc(c.get("note", "")),
            links([f"https://www.nfl.com/scores/2026/week-{w}" for w in range(1, 9)]),
        ])
    corr_body = f"""
<p class="lead">Correlations measured on the repo's official W1-W8 game log (121 games). The earlier session computed them; this page republishes the values unchanged. Statistical associations only, not evidence of an edge.</p>
<h2>Same-game and season correlations</h2>
{table(["ID","Pair","n","r","95% CI","p (two-sided)","p (Holm)","Survives Holm?","Scope","Source (weekly official scores pages)"], c_rows)}
<h2>Cross-game dependence (ICC)</h2>
{table(["ID","Pair","n","ICC","Scope","Use","Source"], icc_rows)}
<h2>Combo pricing (product of probabilities)</h2>
{table(["ID","Combo","r measured","r used","Joint prob","Fair odds (+)","Note","Source"], combo_rows)}
"""
    page("pages/correlations.html", "Correlations", corr_body, "pages/correlations.html")

    # ---------- Suggestions ----------
    sug_rows = []
    for s in content["suggestions"]:
        opts = "<br>".join(esc(o) for o in s["options"])
        sug_rows.append([
            esc(s["id"]), f"<b>{esc(s['title'])}</b><br><span class='sub'>{esc(s['why'])}</span>",
            opts, esc(s["needs"]), esc(s["effort"]), links(s["sources"]),
            f'<span class="pend">{esc(s["status"])}</span>',
            '<span class="unv">your choice</span>',
        ])
    sug_body = f"""
<p class="lead">Decision board. These are options for you to choose from. <b>Nothing listed here has been implemented.</b> Choose an option by ID (for example, "SG-01 option A") and the next session will carry it out.</p>
{table(["ID","Suggestion","Options","Needs","Effort","Sources","Status","Decision"], sug_rows)}
"""
    page("pages/suggestions.html", "Suggestions (awaiting your decision)", sug_body, "pages/suggestions.html")

    # ---------- Questions ----------
    q_rows = []
    for q in content["questions"]:
        q_rows.append([
            esc(q["id"]), f"<b>{esc(q['question'])}</b>", esc(q["status"]), esc(q["answer"]),
            esc(q["needed"]), esc(q["where"]), links(q["links"]),
        ])
    q_body = f"""
<p class="lead">What is known, what is not, and where to look. Status is set by checking the cited source, not by assumption.</p>
{table(["ID","Question","Status","Current answer","Information still needed","Where to look","Source"], q_rows)}
"""
    page("pages/questions.html", "Questions and information gaps", q_body, "pages/questions.html")

    # ---------- Repo review ----------
    r_rows = []
    for r in content["review"]:
        r_rows.append([esc(r["id"]), esc(r["severity"]), f"<b>{esc(r['item'])}</b>", esc(r["detail"]), links(r["links"])])
    rv_body = f"""
<p class="lead">Repository review of Own8 as of this session. Each finding names the file and the official or repo source. Read-only: no other session's files were changed.</p>
{table(["ID","Severity","Finding","Detail","Links"], r_rows)}
"""
    page("pages/repo-review.html", "Repo review and irregularities", rv_body, "pages/repo-review.html")

    # ---------- Flagged ----------
    f_rows = []
    for f_ in content["flags"]:
        f_rows.append([esc(f_["id"]), esc(f_["area"]), esc(f_["item"]), f'<span class="pend">{esc(f_["status"])}</span>', links(f_["links"])])
    flag_body = f"""
<p class="lead">Items for you to review after the site is live. None of these block publication. Unverified values are blank everywhere else on the site.</p>
{table(["ID","Area","Item","Status","Source links"], f_rows)}
<h2>Blank or unverified values</h2>
<ul>
<li>Final scores for 14 of 15 Week 9 games (Lines page).</li>
<li>Week 10 game results and winners (not captured).</li>
<li>Week 10 injury rows for block E after the fetched chunk, and blocks F onward (not captured).</li>
<li>Second- and third-string depth order (no verified source).</li>
<li>Week 2 Next Gen Stats passing rows (page did not render).</li>
<li>Any sportsbook price (no official source).</li>
</ul>
"""
    page("pages/flagged.html", "Flagged for review", flag_body, "pages/flagged.html")

    # ---------- Sources ----------
    s_rows = []
    for s in content["sources"]:
        s_rows.append([esc(s["id"]), link(s["url"]), esc(s["supports"]), esc(s["method"]), esc(s["limits"])])
    src_body = f"""
<p class="lead">Every source used on this site. Sources marked "not re-fetched" were cited by earlier sessions and were not re-checked here.</p>
{table(["ID","Link","What it supports","How it was used","Limits"], s_rows)}
"""
    page("pages/sources.html", "Sources", src_body, "pages/sources.html")

    print("built", len(list(HUB.rglob('*.html'))), "html pages")


def st_body_rows(rows):
    return rows


if __name__ == "__main__":
    main()
