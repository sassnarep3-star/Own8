#!/usr/bin/env python3
"""Builds the category site under site/ (static HTML, standard library only).

Inputs: site/data/*.json (verified captures and registers) and read-only repo artifacts
(ledger registry, correlations, B0 files). Output: site/*.html.
Run:  python3 site/scripts/build.py   then   python3 site/check.py
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(SITE, ".."))
sys.path.insert(0, HERE)
import model_b0  # noqa: E402  (reuses the frozen B0 functions and grading)
REC = model_b0.reconcile()

FETCH = "2026-11-18"
REPO = "https://github.com/sassnarep3-star/Own8/blob/main/"
E = html.escape


def J(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


def RJ(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


def a(href, text=None):
    return f'<a href="{E(href, quote=True)}">{E(text if text is not None else href)}</a>'


def link_or_flag(url, label="Source"):
    if url:
        return a(url, label)
    return '<span class="flag">UNVERIFIED: no official source</span>'


def table(headers, rows, cls="", filter_id=None):
    fid = f' data-filter="{filter_id}"' if filter_id else ""
    h = "".join(f"<th>{E(x)}</th>" for x in headers)
    body = []
    for r in rows:
        cells = "".join(f"<td>{c}</td>" for c in r)
        body.append(f"<tr>{cells}</tr>")
    filt = ""
    if filter_id:
        filt = (f'<input class="filter" type="search" placeholder="Filter rows…" '
                f'aria-label="Filter rows" data-target="{filter_id}">')
    return f'{filt}<div class="tw"><table class="{cls}" id="{filter_id or ""}"{fid}><thead><tr>{h}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("data-standings.html", "Standings"),
    ("data-results.html", "Results"),
    ("data-lines.html", "Lines vs market"),
    ("data-schedule.html", "Schedule & venues"),
    ("data-injuries.html", "Injuries"),
    ("data-depth.html", "Depth & availability"),
    ("strategies.html", "Strategies"),
    ("correlations.html", "Correlations"),
    ("requirements.html", "Requirements"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("repo-review.html", "Repo review"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]
CATS = [
    ("Overview", ["index.html", "executive-summary.html"]),
    ("Data (official)", ["data-standings.html", "data-results.html", "data-schedule.html", "data-injuries.html", "data-depth.html"]),
    ("Models & lines", ["data-lines.html", "strategies.html", "correlations.html"]),
    ("Decisions", ["requirements.html", "questions.html", "suggestions.html"]),
    ("Review", ["repo-review.html", "sources.html", "flagged.html"]),
]
TITLES = dict(NAV)


def page(name, title, body, lead=""):
    nav = []
    for cat, files in CATS:
        items = "".join(
            '<a href="%s"%s>%s</a>' % (f, (' aria-current="page"' if f == name else ""), E(TITLES[f])) for f in files)
        nav.append(f'<div class="cat"><div class="cat-h">{E(cat)}</div>{items}</div>')
    flagged_badge = ' <span class="badge">review</span>' if name == "flagged.html" else ""
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Own8 NFL research</title>
<link rel="stylesheet" href="assets/site.css">
</head><body>
<header class="top"><a class="brand" href="index.html">Own8 · NFL research</a>
<span class="stamp">Latest official sources re-read {FETCH} · older captures retain their own dates · paper research only</span></header>
<div class="wrap">
<aside class="side">{''.join(nav)}</aside>
<main>
<h1>{E(title)}{flagged_badge}</h1>
{f'<p class="lead">{lead}</p>' if lead else ''}
{body}
</main></div>
<footer>No real-money betting, stakes, or rewards. Paper research only. Model outputs are derived calculations, not official NFL data, and are labelled as such. Empty cells are unverified and are flagged. <a href="flagged.html">Flagged for review</a> lists every open item.</footer>
<script src="assets/site.js"></script>
</body></html>
"""
    with open(os.path.join(SITE, name), "w", encoding="utf-8") as f:
        f.write(doc)


def pct(x):
    return f"{100*x:.1f}%"


def num(x, d=2):
    if x is None:
        return "—"
    return f"{x:.{d}f}"


def badge(status):
    cls = {"DONE": "ok", "PARTIAL": "warn", "BLOCKED": "bad", "NOT STARTED": "bad", "NOT DONE": "bad",
           "REJECTED": "muted", "NOT POSSIBLE AS STATED": "muted", "DECISION NEEDED": "warn",
           "PENDING": "warn", "OPEN": "warn", "VERIFIED": "ok", "RESOLVED": "ok", "PASS": "ok"}
    key = status.split(" (")[0].split(" —")[0]
    c = "warn"
    for k, v in cls.items():
        if status.startswith(k):
            c = v
            key = k
            break
    return f'<span class="badge {c}">{E(status)}</span>'


# Clearing number per requirement: only numbers that exist in the brief or the repo's own
# registers. "—" means no pre-registered number exists (set one before use).



CLEAR = {
 "R-01": "14 of 14 Week 10 finals (13 now)",
 "R-03": "14 of 14 Week 10 finals (13 now)",
 "R-14": "6 to 8 game-weeks of postgame Game Books (repo README, RQ-12)",
 "R-18": "13 of 13 Week 11 venues from game centres (1 now)",
 "R-57": "G3 minimum sample sizes: 80 singles, 40 pairs, 100 player-games (validation-w10.json)",
 "R-79": "Merge done and Pages build reported as built",
}
NOCLEAR = "— (no pre-registered number in the repo)"


def clearing(rid, status):
    if rid in CLEAR:
        return CLEAR[rid]
    return "— (met)" if status == "DONE" else NOCLEAR


PATH_RE = re.compile(r"[\w.\-]+(?:/[\w.\-]+)+")


def src_cell(r):
    """Official source if the register has one; else the first repo path named in 'exists' that really exists."""
    if r["source"]:
        return a(r["source"], "Official source")
    for m in PATH_RE.findall(r["exists"] or ""):
        if os.path.exists(os.path.join(ROOT, m)):
            return a(REPO + m, "Repo artifact")
    return '<span class="flag">UNVERIFIED: no source</span>'


def req_rows():
    rows = []
    for r in J("site/data/requirements.json")["rows"]:
        rows.append([E(r["id"]), E(r["group"]), E(r["requirement"]), badge(r["status"]), E(r["exists"]),
                     E(r["gap"]), E(clearing(r["id"], r["status"])), src_cell(r)])
    return rows


def build_index():
    reqs = J("site/data/requirements.json")["rows"]
    from collections import Counter
    c = Counter(r["status"] for r in reqs)
    s = model_b0.load("site/data/b0-w10-grading.json")["summary"]
    w11 = J("site/data/b0-w11-lines-v2.json")
    cards = [
        ("Official standings reconciled", f"{REC['cells'] - len(REC['mismatches'])}/{REC['cells']} cells",
         f"The 136-game log plus {REC['games'] - 136} Week 10 finals reproduce each W, L, T, PF and PA", OFF_STANDINGS),
        ("Week 10 games graded", f"{s['n_graded']} graded · {s['n_pending']} pending",
         "All 14 Week 10 games are final; grading covers the 13 games in the pre-registered B0 line set", OFF_SCORES),
        ("Week 11 fair lines", f"{len(w11['games'])} games · B0 v2 · pre-kickoff",
         "Re-originated after LAC@BAL final; v1 is retained unchanged. Market columns remain blank.", REPO + "site/data/b0-w11-lines-v2.json"),
        ("Strategies on any leaderboard", "0",
         "Four backtest-gate passes are held off the leaderboard under the operator's rule (F-01)", REPO + "ledger/data/strategy-registry.json"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="k">{E(k)}</div><div class="v">{E(v)}</div><div class="n">{E(n)}</div>'
        f'<div class="src">{a(u, "Source")}</div></div>' for k, v, n, u in cards)
    evidence = [
        ["Official standings", f"32 teams. {REC['cells'] - len(REC['mismatches'])} of {REC['cells']} cells match the repo game log plus Week 10 finals.", "VERIFIED", OFF_STANDINGS],
        [f"Week 10 test ({s['n_graded']} settled games)",
         f"Spread error {num(s['spread_mae_model'],2)} (model) vs {num(s['spread_mae_market'],2)} (market). Moneyline Brier {num(s['ml_brier_model'],3)} vs {num(s['ml_brier_market'],3)}. The short-sample intervals include zero.",
         "NO EVIDENCE OF EDGE YET", REPO + "site/data/b0-w10-grading.json"],
        ["Strategy registry", "14 entries. Four are labelled PAPER-ELIGIBLE on a walk-forward backtest (W3 to W9) with no prospective settlement. The README says none are eligible.",
         "CONFLICT (F-01)", REPO + "ledger/data/strategy-registry.json"],
        ["Availability (depth, snaps, Game Books)", "No official depth source verified. The Houston depth-chart page returns 404 (17 Nov). No snap counts or Game Books captured.",
         "BLOCKED", OFF_DEPTH],
        ["Injury report", "Week 10 report: page 1 of 8 re-read; Lions designations verified. Earlier captures disagree on row counts. Week 11 report content is available at the official URL; no timestamped raw capture/hash was retained.",
         "PARTIAL", OFF_INJ10],
        ["Correlations", "Nine descriptive correlations with n and 95% intervals. Four survive Holm correction; C2 does not.", "DESCRIPTIVE ONLY (F-13)", REPO + "origination/results/correlations.json"],
    ]
    ev_rows = [[E(a1), E(b1), badge(c1), a(d1, "Source")] for a1, b1, c1, d1 in evidence]
    dr_rows = [[E(r["id"]), E(r["requirement"]), badge(r["status"]), E(r["gap"] or "—"), E(clearing(r["id"], r["status"])), src_cell(r)] for r in reqs]
    summary_line = " · ".join(f"{k}: {v}" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))
    body = f"""
<section class="cards">{card_html}</section>
<h2>What the evidence says</h2>
{table(["Area", "Finding", "Status", "Source"], ev_rows, cls="findings")}
<h2>Decision readiness (one row per requirement)</h2>
<p class="meta">{E(summary_line)}. The gap column is the blocker. The last column is a number from the brief or the repo's own registers that would clear it; where none exists, the cell says so.</p>
{table(["ID", "Requirement", "Status", "Blocking gap", "Number that clears it", "Source"], dr_rows, cls="dense", filter_id="ready")}
<h2>Pages</h2>
<ul class="links">
<li>{a("executive-summary.html", "Executive summary")}: one-page brief.</li>
<li>{a("suggestions.html", "Suggestions")}: 10 decisions with options, cost and risk. Nothing is implemented until you choose.</li>
<li>{a("questions.html", "Questions")}: what is known, what is missing, and how to answer each.</li>
<li>{a("flagged.html", "Flagged for review")}: every irregularity and unverified item, with source links.</li>
</ul>
"""
    page("index.html", "Overview", body, lead="An NFL line-origination research lab. Every number has a source; a blank or UNVERIFIED cell means not confirmed. Read the executive summary first.")


def build_exec():
    s = model_b0.load("site/data/b0-w10-grading.json")["summary"]
    reqs = J("site/data/requirements.json")["rows"]
    from collections import Counter
    c = Counter(r["status"] for r in reqs)
    body = f"""
<p class="lead">Status on {FETCH}. The official data we can read reconciles. A forecasting edge is not established. The depth and availability layer cannot be built yet, because no official depth-order source is verified.</p>
<h2>1. What is verified</h2>
<ul>
<li>The 32 official standings reconcile to the repo's 136-game log plus 13 Week 10 finals: {REC['cells'] - len(REC['mismatches'])} of {REC['cells']} cells match ({a(OFF_STANDINGS, "nfl.com standings")}).</li>
<li>13 of 14 Week 10 games are final on nfl.com as read. The Monday game (Chargers at Ravens) is not, so it is excluded and flagged (F-04).</li>
<li>Week 11 has 13 games and 6 byes. Thursday's Colts at Texans venue is Reliant Stadium, Houston ({a(OFF_SCHED, "schedule")}; {a(OFF_COLTS, "game centre")}). Venues for the other 12 games are not verified.</li>
<li>Lions designations: Kerby Joseph, Cade Mays and D.J. Reed are all Out on the Week 10 report ({a(OFF_INJ10, "injury report")}, F-15).</li>
</ul>
<h2>2. What the model does, and how it did</h2>
<ul>
<li>The shadow baseline (B0) uses team strength only: points for and against per game, no injuries, no depth, no venue. Its formula reproduces all 13 stored Week 10 values (F-02).</li>
<li>Week 10, 12 settled games: spread error {num(s['spread_mae_model'],2)} points (model) vs {num(s['spread_mae_market'],2)} (market). Total error {num(s['total_mae_model'],2)} vs {num(s['total_mae_market'],2)}; the market is better here. Moneyline Brier {num(s['ml_brier_model'],3)} vs {num(s['ml_brier_market'],3)} (market). Every model-minus-market interval includes zero. Twelve games are not evidence in either direction.</li>
<li>Week 11 fair lines were written in commit beca9d2 from the standings snapshot taken before Monday's game. They are <b>provisional</b>, have no market column, and will be re-originated once Monday is verified final (F-23).</li>
</ul>
<h2>3. Strategies and the leaderboard</h2>
<ul>
<li>The registry has 14 strategies. Four (S6, S1, S7, S2) pass the pre-registered gates on the W3 to W9 walk-forward backtest, which compares against naive baselines, not the market, and nothing has settled prospectively. Under your rule (no backtest numbers on the leaderboard) they are <b>not</b> ranked here. The conflict with the README's "zero eligible" is flagged (F-01); the ruling is S-02.</li>
<li>Parlays and prop combinations stay behind the joint-evidence gate. None can be ranked: there are no official joint or prop prices (M1 and M2 not scored).</li>
</ul>
<h2>4. What blocks the rest</h2>
<ul>
<li><b>Depth order.</b> The Houston depth-chart page returns 404 today. Without an official per-club depth source or official snap counts, no starter or backup can be identified (R-22, R-23).</li>
<li><b>Injury history.</b> Only page 1 of the Week 10 report was re-read, and earlier captures disagree on row counts. Designations cannot be treated as a time series until they are captured on a schedule (F-05).</li>
<li><b>Price history.</b> No official opening or closing series was found. The locked Thursday lines are the only price points, and 12 of the 14 Week 10 market rows are not re-verified (F-12, Q-01).</li>
<li><b>Rights.</b> Whether nfl.com-derived tables can be republished is unread (Q-10).</li>
</ul>
<h2>5. Requirement status</h2>
<p>{E(', '.join(f'{k}: {v}' for k, v in sorted(c.items(), key=lambda kv: -kv[1])))}. Full table: {a("requirements.html", "requirements")}.</p>
<h2>6. Your decisions</h2>
<p>Ten suggestions await a choice on {a("suggestions.html", "the suggestions page")}. The most urgent are the price-data policy (S-01), the leaderboard ruling (S-02), the depth source (S-03) and the snapshot store and alerts (S-04). Nothing has been implemented from them.</p>
<h2>7. Irregularities</h2>
<p>{a("flagged.html", "Flagged for review")} lists every open item, including the registry conflict (F-01), the method-text mismatch (F-02), the picks-article labels (F-03), the injury-count conflict (F-05) and the provisional Week 11 lines (F-23).</p>
"""
    page("executive-summary.html", "Executive summary", body)


def build_standings():
    d = J("site/data/standings-2026-11-17.json")
    rows = []
    for r in sorted(d["rows"], key=lambda x: (-x["PCT"], -x["NET"], x["team"])):
        rows.append([E(r["team"]), E(r["name"]), str(r["W"]), str(r["L"]), str(r["T"]), num(r["PCT"], 3),
                     str(r["PF"]), str(r["PA"]), f'{r["NET"]:+d}', a(d["source_url"], "nfl.com")])
    totW = sum(r["W"] for r in d["rows"]); totL = sum(r["L"] for r in d["rows"])
    totPF = sum(r["PF"] for r in d["rows"]); totPA = sum(r["PA"] for r in d["rows"])
    body = f"""
<p class="meta">Read {FETCH}. Sorted by win percentage, then net points. League totals: wins {totW}, losses {totL}, PF {totPF}, PA {totPA}. NET is PF minus PA.</p>
<p class="ok-line"><b>Reconciliation (rebuilt on this build):</b> the {REC['games'] - 13}-game official log plus {REC['games'] - (REC['games'] - 13)} Week 10 finals reproduce {REC['cells'] - len(REC['mismatches'])} of {REC['cells']} cells (W, L, T, PF, PA). Mismatches: {len(REC['mismatches'])}. Script: <code>site/scripts/model_b0.py</code> (<code>reconcile()</code>). The Monday game is excluded.</p>
{table(["Team", "Name", "W", "L", "T", "PCT", "PF", "PA", "NET", "Source"], rows, filter_id="standings")}
<p class="meta">Team codes follow nfl.com's scores text (AZ, LAR). Flag F-08 notes the mixed codes in older files.</p>
"""
    page("data-standings.html", "Standings", body, lead="The 32 official records as read on 17 Nov 2026, reconciled to the game log.")


def build_results():
    d = J("site/data/week10-results.json")
    rows = []
    for g in d["finals"]:
        rows.append([E(g["day"]), E(f'{g["away"]} at {g["home"]}'), str(g["away_score"]), str(g["home_score"]),
                     E(g["status"]), a(g["game_url"], "Game"), a(d["source_url"], "Scores")])
    for g in d["pending"]:
        rows.append([E(g["day"]), E(f'{g["away"]} at {g["home"]}'), "—", "—",
                     '<span class="badge warn">NOT FINAL as read</span>', a(g["game_url"], "Game"), a(d["source_url"], "Scores")])
    body = f"""
<p class="meta">Source: nfl.com Week 10 scores (3 pages read {FETCH}). Away team first. Week 10 has 14 games: 13 final and 1 not final as read. Commanders at Giants (Thursday, 24–21) is in the official log and standings. It is not in the Week 10 line set, and the repo does not record why.</p>
<p class="flag-line"><b>Open item F-04:</b> the Monday game (Chargers at Ravens) shows no final score on the scores, standings and picks pages as read. It is excluded from grading and from the Week 11 inputs until it is final on nfl.com.</p>
{table(["Day", "Game (away at home)", "Away", "Home", "Status", "Game centre", "Source"], rows, filter_id="results")}
"""
    page("data-results.html", "Results", body, lead="Week 10 final scores from nfl.com. Each row links to the official game page.")


def build_lines():
    g = model_b0.load("site/data/b0-w10-grading.json")
    s = g["summary"]
    stored = RJ("requirements/results/week10-lines.json")["games"]
    by = {r["game"]: r for r in g["rows"]}
    UNV = ' <span class="flag">unverified</span>'
    rows = []
    for st in stored:
        key = f'{st["away"]}@{st["home"]}'
        fh = st["fair_handicap_home_pts"]; ft = st["fair_total_B0"]; fp = st["p_home_win_normal"]
        r = by.get(key)
        if r and r["status"] == "GRADED":
            mh = -r["market_margin"]; mt = r["market_total"]; mp = r["market_p_home"]
            mk = "" if key == "NE@DET" else UNV
            rows.append([E(key), num(fh, 1), num(mh, 1) + mk, num(fh - mh, 2),
                         num(ft, 1), num(mt, 1) + mk, num(ft - mt, 2),
                         pct(fp), pct(mp) + mk,
                         f'{r["away_score"]}–{r["home_score"]}', num(r["err_model_margin"], 1), num(r["err_market_margin"], 1),
                         a(r["source_final"], "Game"), a(r["source_market"], "Prices")])
        else:
            rows.append([E(key), num(fh, 1), '<span class="flag">UNVERIFIED</span>', "—",
                         num(ft, 1), '<span class="flag">UNVERIFIED</span>', "—",
                         pct(fp), "—", "NOT GRADED", "—", "—",
                         a(st["game_url"], "Game"), a(OFF_PICKS, "Prices")])
    body = f"""
<p class="meta">Three columns per measure: <b>fair</b> (B0 baseline, from Weeks 1–9 results only, originated 14 Nov per the stored <code>originated_at</code> field), <b>market</b> (nfl.com picks article, FanDuel prices locked Thursday 12 Nov, 2 PM ET), and <b>difference</b> (fair minus market). Spread is points added to the home team; negative means home favoured. Margins are in home-team terms.</p>
<p class="flag-line"><b>Scope:</b> {s['n_graded']} games graded; 1 pending (Chargers at Ravens). Only 2 of the 14 market rows were re-verified against the picks article: Patriots at Lions (matches) and Chargers at Ravens (matches). The other 12 market cells are marked <span class="flag">unverified</span> (F-12).</p>
{table(["Game", "Fair spread (home)", "Market spread (home)", "Difference (fair − market spread)", "Fair total", "Market total", "Difference (total)", "Fair P(home)", "Market P(home), de-vigged", "Final (away–home)", "Model error (pts)", "Market error (pts)", "Game", "Prices"], rows, cls="dense", filter_id="lines")}
<h2>Summary (12 settled games)</h2>
{table(["Measure", "Model (B0)", "Market", "Difference (model − market)", "95% interval for the difference", "Reading", "Source"], [
 ["Spread error, mean absolute (points)", num(s['spread_mae_model'], 2), num(s['spread_mae_market'], 2), num(s['spread_mae_model'] - s['spread_mae_market'], 2), f"{s['spread_mae_diff_ci95'][0]:+.2f} to {s['spread_mae_diff_ci95'][1]:+.2f}", "Includes zero: no evidence either way", a(REPO + "site/data/b0-w10-grading.json", "Grading")],
 ["Total error, mean absolute (points)", num(s['total_mae_model'], 2), num(s['total_mae_market'], 2), num(s['total_mae_model'] - s['total_mae_market'], 2), f"{s['total_mae_diff_ci95'][0]:+.2f} to {s['total_mae_diff_ci95'][1]:+.2f}", "Includes zero; point estimate favours the market", a(REPO + "site/data/b0-w10-grading.json", "Grading")],
 ["Moneyline Brier (lower is better)", num(s['ml_brier_model'], 4), num(s['ml_brier_market'], 4), num(s['ml_brier_model'] - s['ml_brier_market'], 4), f"{s['ml_brier_diff_ci95'][0]:+.4f} to {s['ml_brier_diff_ci95'][1]:+.4f}", "Includes zero", a(REPO + "site/data/b0-w10-grading.json", "Grading")],
 ["Coin-flip control (p = 0.5, Brier 0.25)", num(s['ml_brier_coinflip_control'], 4), "—", "—", "—", "Model is better than the coin-flip control on this sample", a(REPO + "site/data/b0-w10-grading.json", "Grading")],
], cls="dense")}
<p class="meta">Bootstrap intervals: 10,000 resamples, seed 20261117 (model_b0.py). Twelve games cannot support a skill claim; the repo's own gate requires at least 80 singles games (G3).</p>
"""
    page("data-lines.html", "Lines vs market", body, lead="Week 10: fair line, market line and difference in separate columns, with the verified result beside them.")


def build_schedule():
    d = J("site/data/week11-schedule.json")
    w11 = J("site/data/b0-w11-lines.json")
    lk = {g["game"]: g for g in w11["games"]}
    rows = []
    for g in d["games"]:
        key = f'{g["away"]}@{g["home"]}'
        L = lk[key]
        venue = E(g["venue"]) if g.get("venue") else '<span class="flag">UNVERIFIED</span>'
        vsrc = a(g["venue_source"], "Game centre") if g.get("venue_source") else '<span class="flag">UNVERIFIED</span>'
        rows.append([E(g["day"]), E(g["kickoff_et"]), E(g["network"]), E(f'{g["away"]} at {g["home"]}'),
                     venue, vsrc, num(L["fair_handicap_home"], 1), num(L["fair_total"], 1), pct(L["p_home"]),
                     '<span class="flag">BLANK</span>', '<span class="flag">BLANK</span>', a(g["game_url"], "Game")])
    body = f"""
<p class="meta">Source: nfl.com Week 11 schedule ({FETCH}; 3 pages read). 13 games; 6 teams on bye (ATL, CLE, GB, LAR, NE, SEA). Kickoffs as nfl.com renders them (ET).</p>
<p class="ok-line"><b>Dated announcements (nfl.com note on this page, read 17 Nov):</b> "In Week 16, two of the four designated matchups will be played on Saturday at 4:30 PM ET and 8:00 PM ET on NFL Network, with the remainder to be played either on Thursday night (8:15 PM ET), Sunday afternoon (1:00 PM ET and 4:25 PM ET), Sunday night (8:20 PM ET), or Monday night (8:15 PM ET). Specific dates and start times for the designated Week 16 matchups will be determined and announced at a later date during the season, no later than immediately after Week 14." Week 17 and Week 18 dates are likewise TBD on the page: Week 17 no later than immediately after Week 15; Week 18 after the conclusion of Week 17. No dated announcement has been located yet (R-19).</p>
<p class="flag-line"><b>Provisional Week 11 fair lines</b> (B0). They were written in commit beca9d2 on 17 Nov from the pre-Monday standings snapshot, so they will be re-originated once Chargers at Ravens is verified final (F-23). Market and difference columns are blank: no verified Week 11 market was captured (F-11).</p>
{table(["Day", "Kickoff (ET)", "Network", "Game (away at home)", "Venue", "Venue source", "Fair spread (home)", "Fair total", "Fair P(home)", "Market spread", "Difference", "Game"], rows, cls="dense", filter_id="sched")}
<p class="meta">Venue is verified only for Indianapolis at Houston (Reliant Stadium). The other 12 stay blank until each game centre is read (Q-16).</p>
"""
    page("data-schedule.html", "Schedule & venues", body, lead="Week 11 fixtures, provisional fair lines, and venues (only where the game centre has been read).")


def build_injuries():
    rows = [
        ["Kerby Joseph", "Detroit Lions", "Out", a(OFF_INJ10, "Official report")],
        ["Cade Mays", "Detroit Lions", "Out", a(OFF_INJ10, "Official report")],
        ["D.J. Reed", "Detroit Lions", "Out", a(OFF_INJ10, "Official report")],
    ]
    cap = [
        ["Week 10 report, page 1 of 8", "Re-read 17 Nov", "Partial", a(OFF_INJ10, "Source")],
        ["Week 10 report, pages 2 to 8", "Not re-read", "Not captured", a(OFF_INJ10, "Source")],
        ["Week 11 report", "Not published: the reg11 URL serves Week 10 content", "Blocked", a(OFF_INJ11, "Source")],
        ["Earlier Week 10 captures in repo", "Row counts disagree (F-05)", "Unresolved", a(REPO + "integration/data/injuries-2026-week10.json", "Repo")],
    ]
    body = f"""
<p class="meta">Official NFL injury report, Week 10 (page 1 of 8 read {FETCH}). Only the designation below is confirmed; this table does not list injury types or practice status.</p>
<h2>Lions designations (verified on the Week 10 report)</h2>
{table(["Player", "Team", "Designation", "Source"], rows, filter_id="lions")}
<h2>Capture status</h2>
{table(["Capture", "State", "Result", "Source"], cap)}
<p class="flag-line"><b>Not done:</b> a time series of designations (R-07 to R-10) and daily capture from Wednesday to kickoff (R-08). The brief asks for injury surprises, never levels; that needs at least two timestamped reads per player.</p>
"""
    page("data-injuries.html", "Injuries", body, lead="What the official report says, what we re-read today, and what is still missing.")


def build_depth():
    rows = [
        ["Route a: per-club official depth-chart page", "Houston Texans page returns HTTP 404 (not found)", "0 of 32 clubs", "BLOCKED", a(OFF_DEPTH, "Source")],
        ["Route b: official snap counts", "No official source located or verified in this session", "0 of 32 clubs", "BLOCKED", '<span class="flag">UNVERIFIED</span>'],
        ["Licensed structured depth feed", "Requires operator authorisation (S-03)", "0 of 32 clubs", "DECISION NEEDED", '<span class="flag">UNVERIFIED</span>'],
        ["Official Game Books (actual starters)", "None captured. Published after kickoff; the repo estimates 6 to 8 game-weeks of postgame Game Books before a test is possible (README)", "0 of 32 clubs", "BLOCKED", a(REPO + "README.md", "Repo")],
        ["Official transactions log", "None captured", "0 of 32 clubs", "BLOCKED", '<span class="flag">UNVERIFIED</span>'],
    ]
    body = f"""
<p class="meta">Depth order is the input to every backup-replacement feature. The brief requires a verified route for all 32 clubs before any such feature is built (R-23). None is verified. Rules followed: no depth order from jersey number, experience or salary (rejected in the brief); no depth order read from images by eye.</p>
<p class="flag-line"><b>Blocked:</b> backup-deficiency (R-27), offence and defence matchup matrix (R-28), per-team view (R-29), announced-starter field (R-30), stale-row flags (R-31). The brief's examples (Ravens QB rows, Texans image, Packers jersey prefixes, Seattle shared slots, Washington empty slot) cannot be checked against an official page today (F-06, F-17, F-18).</p>
{table(["Source route", "What was checked (17 Nov)", "Clubs verified", "Status", "Source"], rows, filter_id="depth")}
"""
    page("data-depth.html", "Depth & availability", body, lead="The depth layer is blocked. These are the sources tested, what each returned, and what would unblock it.")


def build_strategies():
    reg = RJ("ledger/data/strategy-registry.json")
    rows = []
    for s in reg["strategies"]:
        gates = s.get("gates", {})
        passed = sum(1 for v in gates.values() if v is True)
        failed = [k for k, v in gates.items() if v is False]
        if s["status"] == "PAPER-ELIGIBLE":
            lb = '<span class="badge warn">NOT ON LEADERBOARD (F-01)</span>'
        else:
            lb = '<span class="badge muted">Not eligible</span>'
        rows.append([E(s["id"]), E(s["strategy"]), E(s.get("product", "")), E(s["status"]),
                     f"{passed} of {len(gates)}", E(", ".join(failed) or "—"),
                     E(str(s.get("n") if s.get("n") is not None else "—")), lb,
                     a(REPO + "ledger/data/strategy-registry.json", "Repo registry")])
    body = f"""
<p class="meta">Source: repo registry, generated 14 Nov (ledger/data/strategy-registry.json; read {FETCH}). The status column is the registry's own label. The leaderboard column is this site's decision under the operator's rule: backtest numbers are not shown in a ranking, and no skill figures are published here.</p>
<p class="flag-line"><b>Conflict F-01:</b> the root README says zero strategies are eligible; the registry labels four PAPER-ELIGIBLE. Those four pass the gates on a walk-forward backtest (W3 to W9) against naive baselines. They have not been compared with the market, and none has settled prospectively.</p>
{table(["ID", "Strategy", "Product", "Registry status", "Gates passed", "Gates failed", "n (backtest)", "Leaderboard", "Source"], rows, cls="dense", filter_id="strat")}
<h2>Rules in force (validation-w10.json, pre-registered)</h2>
<ul>
<li><b>G1</b> official data only; <b>G2</b> no leakage (predictions for week w use only weeks before w); <b>G3</b> sample size (80 games for singles, 40 independent pairs for parlays, 100 player-games for props).</li>
<li><b>G4</b> skill: paired bootstrap 95% interval of the loss difference against the baseline lies entirely below zero; <b>G5</b> Holm-adjusted permutation p below 0.05 across the family.</li>
<li><b>G6</b> stability: positive in both halves of the evaluation window; <b>G7</b> calibration: expected calibration error at most 0.10; <b>G8</b> no market data: the strategy can be priced and settled without sportsbook odds.</li>
<li>Ranking: by the lower bound of benchmark-relative skill, not by win rate or season-long ROI (the brief rejects ROI ranking).</li>
<li><b>Joint probabilities:</b> parlays and prop combinations are not ranked without a directly validated joint probability and the operator's void and push rules. Both are missing (M1 and M2 not scored).</li>
<li><b>Demotion:</b> a live strategy returns to paper when it fails its gates (ledger/data/demotion-rules.json). No strategy is live.</li>
</ul>
"""
    page("strategies.html", "Strategies", body, lead="Pre-registered strategies, the gates they face, and why none is on a leaderboard under the operator's rule.")


def build_correlations():
    c = RJ("origination/results/correlations.json")["correlations"]
    rows = []
    for r in c:
        holm = "Yes" if r["significant_after_holm"] else "No"
        rows.append([E(r["id"]), E(r["pair"]), E(str(r["n"])), num(r["r"], 3),
                     f'{r["ci95"][0]:+.3f} to {r["ci95"][1]:+.3f}', f'{r["p_two_sided"]:.3f}',
                     "Yes (uncorrected)" if r["significant_5pct"] else "No", f'{r["p_holm"]:.3f}', holm,
                     E(r.get("scope", "")), a(REPO + "origination/results/correlations.json", "Repo")])
    body = f"""
<p class="meta">Descriptive pair correlations from official nfl.com scores (and Next Gen Stats where stated), as computed in the repo (read {FETCH}). Each row shows n and a 95% interval. No officially published leg-level pairs exist, so betting-leg dependence is not estimated here.</p>
<p class="flag-line"><b>F-13:</b> C2 is significant at 5% before correction (p = 0.026). After Holm correction across the nine published tests, only C5, C6, C8 and C9 remain. The p-values and Holm values shown are the repo's own, as stored.</p>
{table(["ID", "Pair", "n", "r", "95% interval", "p (two-sided)", "Significant at 5% (uncorrected)", "p (Holm)", "Survives Holm", "Scope", "Source"], rows, cls="dense", filter_id="corr")}
"""
    page("correlations.html", "Correlations", body, lead="Nine correlations with their sample sizes. Only officially sourced inputs; leg-level dependence is blank.")


def build_sources():
    rows = []
    for s in J("site/data/sources.json")["rows"]:
        rows.append([E(s["id"]), E(s["label"]), E(s["kind"]), E(s["read"]), E(s["used_for"]), a(s["url"], "Open")])
    body = f"""
<p class="meta">Every source behind a value on this site. Official pages were read with the page-fetch tool on {FETCH}. A direct download from nfl.com failed from the sandbox with a TLS error, so each capture is the page text as the fetch tool returned it, not a raw HTTP capture.</p>
{table(["ID", "Source", "Kind", "Read", "Used for", "Link"], rows, cls="dense", filter_id="src")}
<h2>Method references (not re-read today)</h2>
<p>The repo README cites statistical references (NIST pages on confidence intervals and multiplicity). They were not re-read here, and citing them does not endorse the model.</p>
"""
    page("sources.html", "Sources", body, lead="Where each number came from, when it was read, and how it was checked.")


OFF_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
OFF_SCORES = "https://www.nfl.com/scores/2026/week-10"
OFF_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-11"
OFF_INJ10 = "https://www.nfl.com/injuries/league/2026/reg10"
OFF_INJ11 = "https://www.nfl.com/injuries/league/2026/reg11"
OFF_DEPTH = "https://www.nfl.com/teams/houston-texans/depth-chart"
OFF_PICKS = "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season"
OFF_COLTS = "https://www.nfl.com/games/colts-at-texans-2026-reg-11?tab=overview"











def build_requirements():
    rows = req_rows()
    body = f"""
<p class="meta">Every item from the operator brief, grouped and duplicates merged. Status legend: DONE (built and checked), PARTIAL, BLOCKED (named missing input), NOT STARTED, NOT DONE (checked, not met), REJECTED (operator rejected), NOT POSSIBLE AS STATED, DECISION NEEDED, PENDING.</p>
{table(["ID", "Group", "Requirement (from the brief)", "Status", "What exists", "Gap or blocker", "Clearing number", "Source"], rows, cls="dense", filter_id="reqs")}
"""
    page("requirements.html", "Requirements", body, lead="The full operator brief as a tracked register. Nothing is marked done on the strength of a build passing alone.")


def build_questions():
    qs = J("site/data/questions.json")["rows"]
    rows = [[E(q["id"]), E(q["question"]), E(q["have"]), E(q["lack"]), E(q["how_to_answer"]), E(q["blocks"]),
             a(REPO + "site/data/questions.json", "Register entry")] for q in qs]
    body = f"""
<p class="meta">What we have, what we lack, and how each question could be answered from an official source. Answers are needed before the matching decision can be made.</p>
{table(["ID", "Question", "What we have", "What we lack", "How to answer", "Blocks", "Source"], rows, cls="dense", filter_id="qs")}
"""
    page("questions.html", "Questions", body, lead="The questions and missing information that must be answered before a decision can reasonably be made.")


def build_suggestions():
    sg = J("site/data/suggestions.json")
    parts = []
    for s in sg["rows"]:
        opts = "".join(f'<li><b>{E(o["label"])}.</b> {E(o["text"])}<br><span class="meta">Cost: {E(o["cost"])} · Risk: {E(o["risk"])}</span></li>' for o in s["options"])
        parts.append(f"""<section class="card wide"><div class="k">{E(s['id'])} · {E(s['requirement'])}</div>
<h3>{E(s['title'])}</h3><ul>{opts}</ul>
<p><b>Recommendation (not applied):</b> {E(s['recommendation'])}</p>
<p><b>Decision needed:</b> {E(s['decision'])}</p>
<p class="flag">Status: awaiting your choice. Nothing has been implemented.</p></section>""")
    body = f"""
<p class="lead">{E(sg['status'])}</p>
{''.join(parts)}
"""
    page("suggestions.html", "Suggestions", body, lead="Options for you to choose from before anything changes. Each lists cost, risk and the decision it needs.")


def build_repo_review():
    rr = J("site/data/repo-review.json")["rows"]
    rows = []
    for r in rr:
        first = r["file"].split(";")[0].strip()
        if re.match(r"^[\w./-]+$", first) and os.path.exists(os.path.join(ROOT, first)):
            link = E(r["file"]) + " · " + a(REPO + first, "Repo")
        else:
            link = E(r["file"]) + " · " + a("flagged.html", "Flagged page")
        rows.append([E(r["id"]), E(r["item"]), E(r["finding"]), E(r["action"]), link, E(r["flag"])])
    body = f"""
<p class="meta">Irregularities found while reviewing the repo on {FETCH}. Scope: the files this session read, plus repo-wide checks (file counts, identifier searches, code usage, workflow files). About 600 non-archive files were not read line by line; that limit is stated (R-77).</p>
{table(["ID", "Item", "Finding", "Action", "File", "Flag"], rows, cls="dense", filter_id="rr")}
"""
    page("repo-review.html", "Repo review", body, lead="Irregularities in the repository, each with a file reference and a flag. None were fixed silently.")



def build_flagged():
    fl = J("site/data/flags.json")["rows"]
    rows = []
    for f in fl:
        link = a(f["link"], "Source") if f["link"] else '<span class="flag">UNVERIFIED: no source</span>'
        rows.append([E(f["id"]), E(f["title"]), E(f["detail"]), E(f["evidence"]), link, badge(f["status"])])
    body = f"""
<p class="lead">Irregularities and unverified items. None of them block the merge. Each has a source link for your review, and each is open until you decide.</p>
{table(["ID", "Title", "Detail", "Evidence", "Source", "Status"], rows, cls="dense", filter_id="flags")}
"""
    page("flagged.html", "Flagged for review", body, lead="Irregularities and unverified items, published for your review.")


def build_readme():
    txt = """# Own8 category site

Built by `python3 site/scripts/content.py` (registers) and `python3 site/scripts/build.py` (HTML). Checked by `python3 site/check.py`.

- Inputs: `site/data/*.json` (verified captures and registers) and read-only repo artifacts (`ledger/`, `origination/`, `requirements/`, `market/`).
- Model baseline B0 and its grading: `site/scripts/model_b0.py`. Week 11 fair lines frozen at commit beca9d2.
- Every table row has a source link. Values that cannot be confirmed are marked UNVERIFIED and left blank.
- Paper research only. No real-money betting, stakes or rewards.
"""
    with open(os.path.join(SITE, "README.md"), "w", encoding="utf-8") as f:
        f.write(txt)


CSS = """
:root{--ink:#18202a;--mut:#5a6572;--line:#dfe4ea;--bg:#f7f9fb;--ok:#0d7a3e;--warn:#9a5b00;--bad:#b3261e;--card:#fff;--acc:#1f5fbf}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--acc)}code{background:#eef2f6;padding:0 4px;border-radius:3px}
header.top{background:#12202f;color:#fff;padding:12px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
header.top a.brand{color:#fff;font-weight:700;text-decoration:none;font-size:17px}header.top .stamp{font-size:12px;opacity:.85}
.wrap{display:grid;grid-template-columns:230px 1fr;gap:0;min-height:80vh}
aside.side{background:#fff;border-right:1px solid var(--line);padding:14px 10px;position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto}
.cat{margin-bottom:10px}.cat-h{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);padding:4px 8px}
.cat a{display:block;padding:5px 8px;border-radius:6px;color:var(--ink);text-decoration:none}.cat a:hover{background:#eef2f6}
.cat a[aria-current=page]{background:#e3ecfb;font-weight:600}
main{padding:18px 26px;max-width:1200px}h1{font-size:24px;margin:4px 0 6px}h2{font-size:18px;margin:24px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}h3{font-size:16px;margin:6px 0}
.lead{font-size:15px;color:#2c3945;max-width:900px}.meta{color:var(--mut);font-size:13px;max-width:980px}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f1f4f8;position:sticky;top:0;font-weight:600}tr:last-child td{border-bottom:0}
table.dense td{max-width:340px}
.filter{margin:6px 0 8px;padding:7px 10px;border:1px solid var(--line);border-radius:6px;width:min(420px,100%);font:inherit}
.badge{display:inline-block;font-size:11.5px;padding:2px 7px;border-radius:999px;font-weight:600;white-space:nowrap;background:#eef2f6;color:var(--ink)}
.badge.ok{background:#e3f5ea;color:var(--ok)}.badge.warn{background:#fdf1dc;color:var(--warn)}.badge.bad{background:#fbe5e3;color:var(--bad)}.badge.muted{background:#eceff3;color:var(--mut)}
.flag{color:var(--bad);font-weight:600;font-size:12.5px}.flag-line{background:#fff7e6;border-left:4px solid #e0a100;padding:8px 12px;max-width:980px}
.ok-line{background:#eaf7ef;border-left:4px solid var(--ok);padding:8px 12px;max-width:980px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:12px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}.card.wide{margin:12px 0;max-width:980px}
.card .k{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}.card .v{font-size:22px;font-weight:700;margin:4px 0}.card .n{font-size:13px}.card .src{font-size:12px;margin-top:6px}
.badge{vertical-align:middle}
footer{color:var(--mut);font-size:12px;padding:16px 26px;border-top:1px solid var(--line);background:#fff}
@media(max-width:820px){.wrap{grid-template-columns:1fr}aside.side{position:static;max-height:none;display:flex;flex-wrap:wrap;gap:6px}.cat{margin:0}.cat-h{display:none}main{padding:14px}}
"""

JS = """
document.querySelectorAll('input.filter').forEach(function(inp){
  inp.addEventListener('input',function(){
    var t=document.getElementById(inp.dataset.target); if(!t) return;
    var q=inp.value.toLowerCase();
    Array.prototype.forEach.call(t.tBodies[0].rows,function(r){
      r.style.display = r.textContent.toLowerCase().indexOf(q)>-1 ? '' : 'none';
    });
  });
});
"""


def main():
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    with open(os.path.join(SITE, "assets", "site.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    with open(os.path.join(SITE, "assets", "site.js"), "w", encoding="utf-8") as f:
        f.write(JS)
    build_index(); build_exec(); build_standings(); build_results(); build_lines(); build_schedule()
    build_injuries(); build_depth(); build_strategies(); build_correlations(); build_requirements()
    build_questions(); build_suggestions(); build_repo_review(); build_sources(); build_flagged()
    build_readme()
    print("built", len(NAV), "pages")


if __name__ == "__main__":
    main()
