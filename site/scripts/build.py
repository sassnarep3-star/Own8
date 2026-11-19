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

FETCH = "2026-11-17"
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
    ("data-team-view.html", "Per-team injury view"),
    ("data-depth.html", "Depth & availability"),
    ("strategies.html", "Strategies"),
    ("correlations.html", "Correlations"),
    ("requirements.html", "Requirements"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("decision-guide.html", "Decision guide"),
    ("repo-review.html", "Repo review"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]
CATS = [
    ("Overview", ["index.html", "executive-summary.html"]),
    ("Data (official)", ["data-standings.html", "data-results.html", "data-schedule.html", "data-injuries.html", "data-team-view.html", "data-depth.html"]),
    ("Models & lines", ["data-lines.html", "strategies.html", "correlations.html"]),
    ("Decisions", ["requirements.html", "questions.html", "suggestions.html", "decision-guide.html"]),
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
<span class="stamp">Source dates vary · see Sources · paper research only</span></header>
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
 "R-01": "14 of 14 Week 10 finals (met); ROI still lacks prices/stakes",
 "R-03": "14 of 14 Week 10 finals (met)",
 "R-14": "6 to 8 game-weeks of postgame Game Books (repo README, RQ-12)",
 "R-18": "13 of 13 Week 11 venues required; 1 currently verified",
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
            return a(REPO + m, "Project evidence") + ' · <span class="flag">UNVERIFIED: official NFL source not linked</span>'
    return '<span class="flag">UNVERIFIED: no official source</span>'


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
        ("Standings re-check", "24 / 32 rows",
         "All 24 visible rows matched the stored snapshot on 19 Nov; 8 rows were not in the fetched chunk", OFF_STANDINGS),
        ("Week 10 results", f"{s['n_graded']} graded · {s['n_pending']} pending",
         "13 games graded; the remaining final was confirmed from the official Game Book and stored", OFF_SCORES),
        ("Week 11 fair lines", f"{len(w11['games'])} games · PRE-REGISTERED",
         "B0-v2 includes the verified Monday result; market and residual remain blank without a verified Week 11 price", REPO + "site/data/b0-w11-lines-v2.json"),
        ("Strategies on any leaderboard", "0",
         "No prospective strategy has qualified; backtest-only candidates remain off the leaderboard (F-01)", REPO + "ledger/data/strategy-registry.json"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="k">{E(k)}</div><div class="v">{E(v)}</div><div class="n">{E(n)}</div>'
        f'<div class="src">{a(u, "Source")}</div></div>' for k, v, n, u in cards)
    evidence = [
        ["Official standings", "The 19 Nov live page matched all 24 rows visible in the fetched chunk. Eight teams were not observed in that chunk; the stored standings snapshot still predates the verified Week 10 Monday final.", "PARTIAL RE-CHECK", OFF_STANDINGS],
        ["Week 10 test (13 settled games)",
         f"Spread MAE {num(s['spread_mae_model'],2)} (model) vs {num(s['spread_mae_market'],2)} (market); total MAE {num(s['total_mae_model'],2)} vs {num(s['total_mae_market'],2)}. Moneyline Brier {num(s['ml_brier_model'],3)} vs {num(s['ml_brier_market'],3)}. All paired 95% intervals include zero.",
         "NO EVIDENCE OF EDGE YET", OFF_SCORES],
        ["Strategy registry", "Backtest-only labels exist, but no strategy has qualified prospectively. F-01 records the registry/leaderboard policy conflict; no backtest rank is published.",
         "FLAGGED · NO LEADERBOARD", OFF_SCORES],
        ["Availability (depth, snaps, Game Books)", "Houston depth-chart route returned the official 404 page on 19 Nov. One page of a seven-page Game Book was captured for one game; no all-club depth or snap-count route is verified.",
         "BLOCKED", OFF_DEPTH],
        ["Injury report", "Repository capture: all 7 chunks on 19 Nov, 253 rows across 24 clubs, 16 game-designation cells on Thursday; earlier 18 Nov capture had 26 rows and a counts-only delta exists. The brief's 254-row count remains unreconciled (F-34).",
         "PARTIAL · ROW COUNT FLAGGED", OFF_INJ11],
        ["Correlations", "Published correlations are descriptive, include n and intervals, and link official NFL/Next Gen Stats inputs; they are not validated betting-leg dependence.", "DESCRIPTIVE ONLY", OFF_SCORES],
    ]
    ev_rows = [[E(a1), E(b1), badge(c1), a(d1, "Official source")] for a1, b1, c1, d1 in evidence]
    src_both = a(OFF_SCORES, "NFL results") + " · " + a(OFF_PICKS, "NFL published prices") + " · " + a(REPO + "site/data/b0-w10-grading.json", "paired grading")
    luck_rows = [
        ["Spread MAE (points; lower is better)", "13", num(s["spread_mae_model"], 2), num(s["spread_mae_market"], 2), num(s["spread_mae_model"] - s["spread_mae_market"], 2), f"{s['spread_mae_diff_ci95'][0]:+.2f} to {s['spread_mae_diff_ci95'][1]:+.2f}", "Includes zero" , src_both],
        ["Total MAE (points; lower is better)", "13", num(s["total_mae_model"], 2), num(s["total_mae_market"], 2), num(s["total_mae_model"] - s["total_mae_market"], 2), f"{s['total_mae_diff_ci95'][0]:+.2f} to {s['total_mae_diff_ci95'][1]:+.2f}", "Includes zero", src_both],
        ["Moneyline Brier (lower is better)", "13", num(s["ml_brier_model"], 4), num(s["ml_brier_market"], 4), num(s["ml_brier_model"] - s["ml_brier_market"], 4), f"{s['ml_brier_diff_ci95'][0]:+.4f} to {s['ml_brier_diff_ci95'][1]:+.4f}", "Includes zero", src_both],
    ]
    luck_panel = f'''<h2 id="luck-panel">Luck &amp; uncertainty panel</h2>
<p class="meta">A finite sample cannot have luck removed. This panel shows the observable model-minus-market outcomes and uncertainty on the 13 graded Week 10 games; every paired 95% interval includes zero. That is not evidence of an edge. The pre-registered single-game sample gate is 80, not 13 ({a(REPO + "origination/results/validation-w10.json", "gate register")}).</p>
{table(["Measure", "n games", "Model", "Market", "Difference (model − market)", "95% interval", "Interpretation", "Sources"], luck_rows, cls="dense")}
<p class="meta">This is a descriptive, small-sample audit, not a strategy ranking, ROI result, or guarantee. Interval method and reproducible values: {a(REPO + "site/data/b0-w10-grading.json", "stored grading")}; official outcomes and published locked prices are linked in each row.</p>'''
    dr_rows = [[E(r["id"]), E(r["requirement"]), badge(r["status"]), E(r["gap"] or "—"), E(clearing(r["id"], r["status"])), src_cell(r)] for r in reqs]
    summary_line = " · ".join(f"{k}: {v}" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))
    body = f"""
<section class="cards">{card_html}</section>
<h2>What the evidence says</h2>
{table(["Area", "Finding", "Status", "Source"], ev_rows, cls="findings")}
{luck_panel}
<h2>Decision readiness (one row per requirement)</h2>
<p class="meta">{E(summary_line)}. The gap column is the blocker. The last column is a number from the brief or the repo's own registers that would clear it; where none exists, the cell says so.</p>
{table(["ID", "Requirement", "Status", "Blocking gap", "Number that clears it", "Source"], dr_rows, cls="dense", filter_id="ready")}
<h2>Pages</h2>
<ul class="links">
<li>{a("executive-summary.html", "Executive summary")}: one-page brief.</li>
<li>{a("suggestions.html", "Suggestions")}: reviewable options, cost and risk; operator-only decisions are separated from safe paper-work.</li>
<li>{a("decision-guide.html", "Decision guide")}: current answer, known information, gaps, gates and evidence required for each decision.</li>
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
<p class="lead">Updated 19 Nov 2026, with source-specific limits. Week 10 results are settled in the feed, but the standings live re-check was partial and the Week 10 shadow-model sample is only 13 games. A forecasting edge is not established. The depth and availability layer cannot be built yet because no all-32 source route is verified.</p>
<h2>1. What is verified</h2>
<ul>
<li>The Week 10 official results feed contains 150 games: 136 from Weeks 1–9 plus all 14 Week 10 finals. The 19 Nov standings spot-check matched the 24 rows visible in the fetched chunk; the remaining eight were not observed in that chunk. The stored standings snapshot predates the Monday final and its full live reconciliation remains incomplete ({a(OFF_STANDINGS, "NFL standings")}; {a(REPO + "site/data/verification-2026-11-19.json", "dated check")}.)</li>
<li>All 14 Week 10 games are settled in the feed; Monday LAC@BAL (20–23) was confirmed against the official Game Book on 18 Nov. The 19 Nov scores-page spot-check matched nine visible finals; the remaining five stay supported by dated stored evidence, not this partial re-read.</li>
<li>Week 11 has 13 games and 6 byes. Thursday's Colts at Texans venue is Reliant Stadium, Houston ({a(OFF_SCHED, "schedule")}; {a(OFF_COLTS, "game centre")}). Venues for the other 12 games are not verified.</li>
<li>Lions designations: Kerby Joseph, Cade Mays and D.J. Reed are all Out on the Week 10 report ({a(OFF_INJ10, "injury report")}, F-15).</li>
<li>Week 11 injury report read twice (18 and 19 Nov). Between the reads, 22 clubs moved from "No Injuries Reported" to listed rows and 16 game designations were filled, all on the Thursday game (IND at HOU). Only change counts are published ({a(OFF_INJ11, "official report")}; <a href="data-injuries.html">Injuries</a>, F-34).</li>
</ul>
<h2>2. What the model does, and how it did</h2>
<ul>
<li>The shadow baseline (B0) uses team strength only: points for and against per game, no injuries, no depth, no venue. Its formula reproduces all 13 stored Week 10 values (F-02).</li>
<li>Week 10, {s['n_graded']} graded games ({s['n_pending']} pending): spread error {num(s['spread_mae_model'],2)} points (model) vs {num(s['spread_mae_market'],2)} (market). Total error {num(s['total_mae_model'],2)} vs {num(s['total_mae_market'],2)}; the market is better here. Moneyline Brier {num(s['ml_brier_model'],3)} vs {num(s['ml_brier_market'],3)} (market). Every model-minus-market interval includes zero. {s['n_graded']} games are not evidence in either direction.</li>
<li>Re-verified live on 2026-11-19 (session 29145302): the nfl.com standings, Week 10 scores and Week 11 schedule pages were re-read and match the stored captures on every observed row (24 standings rows, 9 Week 10 finals, 6 Week 11 games; see <a href="sources.html">Sources</a>). Unobserved rows were left as stored, not upgraded.</li>
<li>Week 11 has a frozen B0-v2 line set registered after the verified Monday final. It carries model probabilities and its inputs; verified market columns remain blank, so no residual or CLV is published. B0-v1 is retained as a separate earlier version.</li>
</ul>
<h2>3. Strategies and the leaderboard</h2>
<ul>
<li>The registry has 14 strategies. Four (S6, S1, S7, S2) pass the pre-registered gates on the W3 to W9 walk-forward backtest, which compares against naive baselines, not the market, and nothing has settled prospectively. Under your rule (no backtest numbers on the leaderboard) they are <b>not</b> ranked here. The conflict with the README's "zero eligible" is flagged (F-01); the ruling is S-02.</li>
<li>Parlays and prop combinations stay behind the joint-evidence gate. None can be ranked: there are no official joint or prop prices (M1 and M2 not scored).</li>
</ul>
<h2>4. What blocks the rest</h2>
<ul>
<li><b>Depth order.</b> The Houston depth-chart URL returned the NFL's 404 page on 19 Nov. No all-32 route is verified; one page of one Game Book is not a complete depth register (R-22, R-23).</li>
<li><b>Injury history.</b> The repository records two Week 11 reads; the second is a seven-chunk, 253-row transcription across 24 clubs, with 16 Thursday game-status cells. The brief's 254 count remains unreconciled and the large delta may reflect a capture artifact (F-34/F-37). No full Wed-to-kickoff series or outcome validation exists yet.</li>
<li><b>Price history.</b> The <a href="{OFF_PICKS}">official Week 10 picks article</a> publishes FanDuel lines locked Thursday at 2 p.m. ET; this is not an opening/closing series. The <a href="../ledger/price-store.html">price ledger</a> records 39 locked market rows and no opening/closing values. F-12's “12 of 14” refers to the 17 Nov freshness re-read (2 of 14 game rows re-read), not missing locked-price values.</li>
<li><b>Rights and storage.</b> NFL's terms page restricts systematic retrieval and copying absent express prior written consent. Project-specific permission is unresolved; <code>private-store/</code> is still inside the public Git repository (Q-10, F-31).</li>
</ul>
<h2>5. Requirement status</h2>
<p>{E(', '.join(f'{k}: {v}' for k, v in sorted(c.items(), key=lambda kv: -kv[1])))}. Full table: {a("requirements.html", "requirements")}.</p>
<h2>6. Your decisions</h2>
<p>Review the alternatives on {a("suggestions.html", "Suggestions")}. The {a("decision-guide.html", "decision guide")} separates safe paper-only steps from operator-only choices: licensed price/snap feeds, data rights, private storage/alerts, and any reward. No licensing, legal, spending or reward decision is made automatically.</p>
<h2>7. Irregularities</h2>
<p>{a("flagged.html", "Flagged for review")} lists open items including the strategy-registry conflict (F-01), the B0 method-text mismatch (F-02), the picks-article label inconsistency (F-03), injury-capture row-count conflict (F-05), unverified Week 10 market rows (F-12), and public-repository raw storage (F-31). F-23 is resolved by the separately frozen B0-v2; its market fields remain blank.</p>
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
<p class="ok-line"><b>Reconciliation (rebuilt on this build):</b> the 150-game official log reproduces 152 of 160 stored standings cells (W, L, T, PF, PA). Eight BAL/LAC cells differ because the standings snapshot predates the verified LAC 20–BAL 23 final. Script: <code>site/scripts/model_b0.py</code> (<code>reconcile()</code>).</p>
<p class="flag-line"><b>Freshness:</b> this table is the 17 Nov stored snapshot, not a new full transcription. The 19 Nov live check matched the first 24 visible rows; the remaining eight were not in the fetched chunk and remain unverified today. See {a(REPO + "site/data/verification-2026-11-19.json", "row-level check scope")}.</p>
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
<p class="meta">Stored feed: 14 Week 10 finals, each linked to an official game centre; Monday LAC@BAL (LAC 20, BAL 23) was confirmed against the Game Book on 18 Nov. The 19 Nov live scores-page re-read matched nine visible finals in chunk 0 of 2; the other five remain supported by earlier dated evidence, not by that partial re-read.</p>
<p class="flag-line"><b>F-04 resolved:</b> Monday LAC@BAL showed no score on nfl.com as read 2026-11-17 (recorded pending); confirmed FINAL on 2026-11-18 against the official Game Book: LAC 20, BAL 23 at M&T Bank Stadium. Included in the results feed and grading. Game centre: {a("https://www.nfl.com/games/chargers-at-ravens-2026-reg-10", "LAC at BAL")}.</p>
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
<p class="flag-line"><b>Scope:</b> {s['n_graded']} games graded; {s['n_pending']} pending. Only 2 of the 14 market rows were re-verified against the picks article in this capture set: Patriots at Lions and Chargers at Ravens. The other market cells remain marked <span class="flag">unverified</span> (F-12).</p>
{table(["Game", "Fair spread (home)", "Market spread (home)", "Difference (fair − market spread)", "Fair total", "Market total", "Difference (total)", "Fair P(home)", "Market P(home), de-vigged", "Final (away–home)", "Model error (pts)", "Market error (pts)", "Game", "Prices"], rows, cls="dense", filter_id="lines")}
<h2>Summary ({s['n_graded']} settled games)</h2>
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
    w11 = J("site/data/b0-w11-lines-v2.json")
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
<p class="meta">Stored source: nfl.com Week 11 schedule ({FETCH}; 3 pages read). The 19 Nov live re-check matched the first 6 games in chunk 0 of 3; 7 games were not observed in that re-check and retain their earlier dated source rows. 13 games; 6 teams on bye (ATL, CLE, GB, LAR, NE, SEA). Kickoffs as nfl.com renders them (ET).</p>
<p class="ok-line"><b>Dated announcements (nfl.com note on this page, read 17 Nov):</b> "In Week 16, two of the four designated matchups will be played on Saturday at 4:30 PM ET and 8:00 PM ET on NFL Network, with the remainder to be played either on Thursday night (8:15 PM ET), Sunday afternoon (1:00 PM ET and 4:25 PM ET), Sunday night (8:20 PM ET), or Monday night (8:15 PM ET). Specific dates and start times for the designated Week 16 matchups will be determined and announced at a later date during the season, no later than immediately after Week 14." Week 17 and Week 18 dates are likewise TBD on the page: Week 17 no later than immediately after Week 15; Week 18 after the conclusion of Week 17. No dated announcement has been located yet (R-19).</p>
<p class="flag-line"><b>Week 11 fair lines: B0-v2.</b> This version was pre-registered after the Week 10 Chargers–Ravens final was verified and uses the updated standings snapshot. Market and difference columns remain blank: no verified Week 11 market capture is stored. The earlier frozen B0-v1 is retained as a separate version.</p>
{table(["Day", "Kickoff (ET)", "Network", "Game (away at home)", "Venue", "Venue source", "Fair spread (home)", "Fair total", "Fair P(home)", "Market spread", "Difference", "Game"], rows, cls="dense", filter_id="sched")}
<p class="meta">Venue is verified only for Indianapolis at Houston (Reliant Stadium). The other 12 stay blank until each game centre is read (Q-16).</p>
"""
    page("data-schedule.html", "Schedule & venues", body, lead="Week 11 fixtures, provisional fair lines, and venues (only where the game centre has been read).")


DELTA_PUB = os.path.join(ROOT, "captures", "2026-11-19", "delta-w11-r1-to-r2.json")
MANIFEST_PUB = os.path.join(ROOT, "captures", "manifest.json")


def build_injuries():
    with open(DELTA_PUB, encoding="utf-8") as f:
        d = json.load(f)
    with open(MANIFEST_PUB, encoding="utf-8") as f:
        man = {c["id"]: c for c in json.load(f)["captures"]}
    e_bound = man["injury-report-2026-w11-r1"]["retrieved_utc_upper_bound"]
    l_bound = man["injury-report-2026-w11-r2"]["retrieved_utc_upper_bound"]
    reads = [
        ["Read 1 (Week 11 report, 3 of 3 chunks)", e_bound + " (upper bound)", "13 games; rows for 2 clubs (IND, HOU); 24 clubs 'No Injuries Reported'", str(d["earlier_capture"]["rows"]), a(OFF_INJ11, "Official report")],
        ["Read 2 (Week 11 report, 7 of 7 chunks)", l_bound + " (upper bound)", "13 games; rows for 24 clubs; 2 clubs 'No Injuries Reported' (CIN, WAS)", str(d["later_capture"]["rows"]), a(OFF_INJ11, "Official report")],
    ]
    changes = [
        ["Clubs that moved from 'No Injuries Reported' to listed rows", str(d["clubs_with_rows_in_later_read_that_earlier_read_marked_no_injuries"]), a(OFF_INJ11, "Official report")],
        ["Players on read 2 not on read 1", str(d["rows_only_in_later_read"]), a(OFF_INJ11, "Official report")],
        ["Players on read 1 not on read 2", str(d["rows_only_in_earlier_read"]), a(OFF_INJ11, "Official report")],
        ["Practice status changed (same player, same club)", str(d["practice_status_changed"]), a(OFF_INJ11, "Official report")],
        ["Injury text filled (blank on read 1)", str(d["injury_text_changed_or_filled"]), a(OFF_INJ11, "Official report")],
        ["Game designation filled (blank on read 1)", str(d["game_status_changed_or_filled"]), a(OFF_INJ11, "Official report")],
    ]
    lions = [
        ["Kerby Joseph", "Detroit Lions", "Out", a(OFF_INJ10, "Official report")],
        ["Cade Mays", "Detroit Lions", "Out", a(OFF_INJ10, "Official report")],
        ["D.J. Reed", "Detroit Lions", "Out", a(OFF_INJ10, "Official report")],
    ]
    body = f"""
<p class="meta">Official NFL injury report, Week 11. Two timestamped reads of the same URL. Only change counts are published here; player rows stay in <code>private-store/</code> (F-31).</p>
<p class="flag-line"><b>Read this first.</b> The 18 Nov read showed 24 clubs as 'No Injuries Reported'. The 19 Nov read lists rows for 24 of the 26 clubs. The 18 Nov statement is superseded (F-26) and is not a current status for any club. A clean read is not evidence of health.</p>
<h2>Reads (clock time is an upper bound; fetch_page returns no clock time)</h2>
{table(["Read", "Retrieved (UTC)", "Content", "Player rows", "Source"], reads)}
<h2>What changed between the two reads (counts only)</h2>
{table(["Change", "Count", "Source"], changes)}
<p class="meta">{E(d["interpretation"])}</p>
<p class="meta">Per-club view: <a href="data-team-view.html">per-team view</a>. Delta: <a href="https://github.com/sassnarep3-star/Own8/blob/main/captures/2026-11-19/delta-w11-r1-to-r2.json">captures/2026-11-19/delta-w11-r1-to-r2.json</a>; independent check: <a href="https://github.com/sassnarep3-star/Own8/blob/main/captures/scripts/check_delta_independent.py">captures/scripts/check_delta_independent.py</a>.</p>
<h2>Lions designations (Week 10 report, verified 17 Nov; not changed by the Week 11 reads)</h2>
{table(["Player", "Team", "Designation", "Source"], lions, filter_id="lions")}
<h2>Still missing</h2>
<ul>
<li><b>Friday 20 Nov and Saturday 21 Nov reads.</b> Two reads show a change between 18 and 19 Nov only (Q-07, F-35).</li>
<li><b>Practice trend (DNP to LP to FP).</b> Needs at least three reads on different days (R-09). Not yet measurable.</li>
<li><b>Daily capture from Wednesday to kickoff (R-08).</b> No scheduler captures nfl.com; each read is a manual fetch.</li>
<li><b>Week 10 pages 2 to 8 (F-05).</b> The Week 10 row count is still unreconciled.</li>
<li><b>Decision needed (F-36):</b> level view or delta view for the per-team page, and a definition of the net injury count.</li>
</ul>
"""
    page("data-injuries.html", "Injuries", body, lead="Two official reads of the Week 11 report, the change between them, and what is still missing.")


def build_depth():
    rows = [
        ["Route a: per-club official depth-chart page", "Houston Texans route returned the official 404 page when fetched 19 Nov; this does not establish other clubs' status", "0 of 32 verified", "BLOCKED", a(OFF_DEPTH, "NFL source")],
        ["Route b: official snap counts", "No all-32 official snap-count source is verified in this repository", "UNVERIFIED", "BLOCKED", '<span class="flag">UNVERIFIED: source not established</span>'],
        ["Licensed structured depth feed", "No license or authorized feed is recorded", "UNVERIFIED", "DECISION NEEDED", '<span class="flag">UNVERIFIED: source/rights not established</span>'],
        ["Official Game Books (actual game-day evidence)", "One page of a seven-page NE@DET Game Book was captured (lineups and Not Active list); no complete 32-club snap-share dataset", "1 partial game; not depth coverage", "PARTIAL", a("https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "NFL game centre") + " · " + a(REPO + "captures/manifest.json", "capture manifest")],
        ["Official transactions log", "No transaction log capture is recorded", "UNVERIFIED", "BLOCKED", '<span class="flag">UNVERIFIED: source not established</span>'],
    ]
    body = f"""
<p class="meta">Depth order is the input to every backup-replacement feature. Requirement R-23 needs one verified source route for all 32 clubs. No player is assigned a depth rank from jersey number, experience or salary; no image is transcribed by eye.</p>
<p class="flag-line"><b>Blocked:</b> backup-deficiency, offense/defense matchup matrix, replacement depth, per-team starters-out view, announced-starter field and stale-row flags. Shared/tied and empty slots must be preserved. One Game Book page is actual game-day evidence, not a pre-kickoff all-club depth chart or snap-count source.</p>
{table(["Source route", "What is verified", "Coverage", "Status", "Source / flag"], rows, filter_id="depth")}
"""
    page("data-depth.html", "Depth & availability", body, lead="The depth layer remains blocked. Source routes, proven coverage and the exact evidence needed to unblock it.")


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
                     a(OFF_SCORES, "NFL results") + " · " + a(REPO + "ledger/data/strategy-registry.json", "strategy record")])
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
        official_sources = a(OFF_SCORES, "NFL scores")
        if r["id"] in ("C5", "C6", "C7", "C8", "C9"):
            official_sources = a("https://nextgenstats.nfl.com/stats/passing", "NFL Next Gen Stats") + " · " + official_sources
        rows.append([E(r["id"]), E(r["pair"]), E(str(r["n"])), num(r["r"], 3),
                     f'{r["ci95"][0]:+.3f} to {r["ci95"][1]:+.3f}', f'{r["p_two_sided"]:.3f}',
                     "Yes (uncorrected)" if r["significant_5pct"] else "No", f'{r["p_holm"]:.3f}', holm,
                     E(r.get("scope", "")), official_sources + " · " + a(REPO + "origination/results/correlations.json", "calculation record")])
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
    ccfrows = []
    ccf = J("site/data/verification-ccf863a6-2026-11-19.json")
    for item in ccf["checks"]:
        ccfrows.append([E(item["id"]), E(item["observed"]), E(item["limit"]), E(item["use"]), a(item["url"], "Official page")])
    vrows = []
    for v in J("site/data/verification-2026-11-19.json")["checks"]:
        vrows.append([E(v["id"]), E(v["observed"]), E(v["stored"]), E(v["result"]), a(v["source_url"], "Open")])
    body = f"""
<p class="meta">Source dates and read limits are recorded per row. Most inherited pages were read 17 Nov; a limited re-check occurred 19 Nov. The 19 Nov injury page was read only for its first returned chunk, and the terms/depth/picks pages have separate scope notes below. These are page-fetch transcriptions, not raw HTTP captures.</p>
{table(["ID", "Source", "Kind", "Read", "Used for", "Link"], rows, cls="dense", filter_id="src")}
<h2>Focused official-source checks (19 Nov 2026; session ccf863a6)</h2>
<p class="meta">These records state exactly what the fetched page showed and what was not established. Full verification record: {a(REPO + "site/data/verification-ccf863a6-2026-11-19.json", "CCF-V01 to CCF-V04")}.</p>
{table(["ID", "Observed", "Limit", "Use", "Official source"], ccfrows, cls="dense", filter_id="ccf-checks")}
<h2>Live re-verification on 2026-11-19 (session 29145302)</h2>
<p class="meta">Three official pages were re-read live and compared to the stored captures. Only observed rows are recorded; unobserved rows were left as stored. Full record: <code>site/data/verification-2026-11-19.json</code>.</p>
{table(["ID", "Observed live", "Stored capture", "Result", "Link"], vrows, cls="dense", filter_id="v19")}
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
    reqdata = J("site/data/requirements.json")
    rows = req_rows()
    body = f"""
<p class="meta">Register baseline date: {E(reqdata.get('as_of', 'unknown'))}; selective status refresh: {E(reqdata.get('reviewed_at', 'not recorded'))}. Only the rows explicitly rechecked on 19 Nov are refreshed; other inherited statuses retain their earlier evidence dates. Items are grouped and duplicates merged. Status legend: DONE (built and checked), PARTIAL, BLOCKED (named missing input), NOT STARTED, NOT DONE (checked, not met), REJECTED (operator rejected), NOT POSSIBLE AS STATED, DECISION NEEDED, PENDING.</p>
{table(["ID", "Group", "Requirement (from the brief)", "Status", "What exists", "Gap or blocker", "Clearing number", "Source"], rows, cls="dense", filter_id="reqs")}
"""
    page("requirements.html", "Requirements", body, lead="The full operator brief as a tracked register. Nothing is marked done on the strength of a build passing alone.")


def build_questions():
    qdata = J("site/data/questions.json")
    qs = qdata["rows"]
    official = {
        "Q-01": [OFF_PICKS], "Q-02": [OFF_DEPTH], "Q-04": [OFF_INJ10, "https://www.nfl.com/games/patriots-at-lions-2026-reg-10"],
        "Q-05": [OFF_STANDINGS], "Q-06": [OFF_INJ10], "Q-07": [OFF_INJ11], "Q-08": [OFF_SCORES],
        "Q-09": [OFF_SCORES, OFF_PICKS], "Q-10": ["https://www.nfl.com/legal/terms/"],
        "Q-13": [OFF_SCHED], "Q-14": ["https://www.nfl.com/games/patriots-at-lions-2026-reg-10"],
        "Q-16": [OFF_SCHED],
        "Q-19": [OFF_SCORES], "Q-20": [OFF_STANDINGS],
    }
    rows = []
    for q in qs:
        links = official.get(q["id"], [])
        source_cell = " · ".join(a(u, "Official source") for u in links) if links else '<span class="flag">UNVERIFIED: no official source identified</span>'
        source_cell += " · " + a(REPO + "site/data/questions.json", "register record")
        rows.append([E(q["id"]), E(q["question"]), E(q["have"]), E(q["lack"]), E(q["how_to_answer"]), E(q["blocks"]), source_cell])
    body = f"""
<p class="meta">Register baseline date: {E(qdata.get('as_of', 'unknown'))}; selective refresh: {E(qdata.get('reviewed_at', 'not recorded'))}. Each row separates the current answer/evidence from missing information and a testable way to close the gap. Official-source links are included where identified; operator-only questions and unlocated sources remain explicitly UNVERIFIED. Source dates vary; check the Sources page.</p>
{table(["ID", "Question", "What we have / answer today", "What we lack", "How to answer", "Blocks", "Official source / evidence"], rows, cls="dense", filter_id="qs")}
"""
    page("questions.html", "Questions", body, lead="The questions and information that must be addressed before a decision can reasonably be made.")


def build_suggestions():
    sg = J("site/data/suggestions.json")
    source_map = {
        "S-01": [OFF_PICKS, "https://www.nfl.com/legal/terms/"], "S-02": [OFF_SCORES], "S-03": [OFF_DEPTH, "https://www.nfl.com/games/patriots-at-lions-2026-reg-10"],
        "S-04": [OFF_INJ11, "https://www.nfl.com/legal/terms/"], "S-05": ["https://www.nfl.com/legal/terms/"], "S-06": [OFF_STANDINGS],
        "S-07": [OFF_PICKS], "S-08": [OFF_INJ10],
    }
    parts = []
    for s in sg["rows"]:
        opts = "".join(f'<li><b>{E(o["label"])}.</b> {E(o["text"])}<br><span class="meta">Cost: {E(o["cost"])} · Risk: {E(o["risk"])}</span></li>' for o in s["options"])
        urls = source_map.get(s["id"], [])
        sources = " · ".join(a(u, "Official source") for u in urls) if urls else '<span class="flag">UNVERIFIED: operator/project policy; no official NFL source applies</span>'
        sources += " · " + a(REPO + "site/data/suggestions.json", "suggestion register")
        parts.append(f"""<section class="card wide"><div class="k">{E(s['id'])} · {E(s['requirement'])}</div>
<h3>{E(s['title'])}</h3><ul>{opts}</ul>
<p><b>Recommendation (not applied):</b> {E(s['recommendation'])}</p>
<p><b>Decision needed:</b> {E(s['decision'])}</p>
<p><b>Sources:</b> {sources}</p>
<p class="flag">Status: awaiting operator decision. No licensing, legal, spending or reward choice is made automatically.</p></section>""")
    body = f"""
<p class="lead">{E(sg['status'])}</p>
{''.join(parts)}
"""
    page("suggestions.html", "Suggestions", body, lead="Reviewable options with recommendations, cost, risk and sources. Operator-only decisions remain separate from safe paper-only work.")


def build_decision_guide():
    """A compact decision map built from the current official-source checks and frozen repo gates."""
    rows = [
        ["Q-01 · Results & line-quality", "We can grade the existing shadow model, but cannot claim a proven edge or ROI. The 19 Nov spot-check matched 9 visible Week 10 finals; other results remain tied to dated captures.", "Official Week 10 results are published. The project feed stores 150 results (136 W1–W9 + 14 W10) with source links; status and chronology must remain attached.", "A prospective sample, market-aligned prices/stakes and holdout evidence. A result feed alone is not ROI.", "Keep the singles-only model in shadow; lock forecast + probability + inputs before kickoff; grade only after an official final. No strategy rank/reward until pre-registered gates pass.", link_or_flag("https://www.nfl.com/scores/2026/week-10", "NFL scores") + " · " + a(REPO + "site/data/verification-2026-11-19.json", "19 Nov check")],
        ["Q-02 · Market-price policy", "A dated reference price exists for the NFL Week 10 picks article: FanDuel lines locked Thursday 2 p.m. ET. This is not an opening/closing history.", "The project price store has 87 Week 9–10 snapshots; opening and closing values are blank where not sourced.", "A lawful, retained open/close feed and an approved reuse policy are missing; no CLV claim can be made from one locked timestamp.", "Safe default: publish the existing locked-time snapshots as such and leave open/close/CLV blank. Do not automate additional systematic retrieval or acquire a paid feed until rights, terms and budget are approved.", link_or_flag("https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season", "NFL picks + locked lines") + " · " + a("https://www.nfl.com/legal/terms/", "NFL terms")],
        ["Q-03 · Injury surprise & availability", "The repository now contains a full 19 Nov Week 11 transcription across all 7 fetch chunks (253 player rows, 24 clubs) and a dated manifest; the earlier 18 Nov read had 26 rows. Sixteen game-designation cells appear for Thursday only.", "The brief says 254 rows; the transcribed 253-row count remains unreconciled. Two reads show large discrepancies that may be capture artifacts; they do not establish which changes were real. Friday read, multi-week archive, inactive evidence, Game Books and snap-count coverage are still missing.", "Reconcile 253 vs 254, preserve the current hashes and read timestamps, repeat capture Friday, then key-match and validate source deltas before outcome tests. Keep this outside the model pending multi-season calibration.", "Do not turn Questionable/Out levels into fixed penalties. Report observed deltas only with provenance and explicit capture-artifact caveats; require multi-week historical designation reliability, inactive/Game Book outcome joins and chronological ablations before modeling.", link_or_flag("https://www.nfl.com/injuries/league/2026/reg11", "NFL Week 11 injury report") + " · " + a(REPO + "captures/manifest.json", "capture manifest") + " · " + a(REPO + "captures/2026-11-19/delta-w11-r1-to-r2.json", "counts-only delta")],
        ["Q-04 · Starter and replacement depth", "The Houston Texans NFL depth-chart URL returned the official 404 page when rechecked 19 Nov. That says nothing about other clubs; an all-32 route is not verified.", "No player is assigned a starter/depth slot from jersey number, experience or salary. Game Books provide actual game-day evidence after the fact, not a full pre-kickoff depth register.", "A verified official or authorized source for all 32 clubs, grouped/shared/empty slots, dated roster events and snap counts. Coverage and definitions must be checked club by club.", "Keep the deficiency matrix blocked. Only proceed when the chosen source covers 32/32 clubs and preserves ties/empty slots; use verified play-time for role, never jersey order.", link_or_flag("https://www.nfl.com/teams/houston-texans/depth-chart", "NFL depth-chart probe") + " · " + a("https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "NFL game centre")],
        ["Q-05 · Skill, luck & leaderboard", "No evidence in the current record justifies promoting a strategy. A small realised win rate or ROI cannot separate skill from variance; luck is not eliminated, only bounded with proper scores and uncertainty.", "The repo pre-registers G3 sample thresholds: 80 singles, 40 independent parlay pairs, 100 player-games; other gates include paired uncertainty, multiplicity correction, calibration and stability.", "Prospective chronological holdouts and clean, comparable market baselines; strategy-registry conflicts are flagged and must be resolved before any leaderboard display.", "Singles first; rank only benchmark-relative proper-score skill with uncertainty after all preregistered gates pass. Keep backtest figures off the public leaderboard; split signal from staking. No real-money reward.", link_or_flag("https://www.nfl.com/scores/2026/week-10", "NFL results for settlement") + " · " + a(REPO + "ledger/data/strategy-registry.json", "pre-registration registry")],
        ["Q-06 · Parlays & player-prop combos", "Not decision-ready. Multiplying marginal probabilities does not supply a validated joint probability.", "The strategy rules explicitly hold combinations behind a joint-evidence gate; available game results do not by themselves validate operator-specific void/push settlement.", "Directly validated joint probabilities on chronological held-out outcomes, official/authorized prop prices and the operator's void/push rules.", "Do not rank parlays or prop combos until joint validation and settlement rules are both recorded; use distinct leaderboard divisions only after that gate.", link_or_flag("https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "NFL Game Book entry point") + " · " + a(REPO + "ledger/data/strategy-registry.json", "strategy gates")],
        ["Q-07 · Data rights, storage & alerts", "The NFL Terms page says use is individual, non-commercial and informational, and restricts systematic retrieval and copying absent express prior written consent. This is not a legal determination for this project.", "The repo has a `private-store/` directory but it is still in the public Git repository; excluding it from Pages does not make it private.", "Written rights/terms review, an actually private durable store, retention/access rules, alert owner and approved credentials.", "Keep raw row-level captures out of public deployment; do not treat Git as a secret store. Obtain operator/legal approval and provision private storage before automation or redistribution.", link_or_flag("https://www.nfl.com/legal/terms/", "NFL Terms and Conditions") + " · " + a(REPO + "private-store/", "repository storage path")],
    ]
    body = f"""
<p class="flag-line"><b>Decision rule:</b> facts below are limited to the linked official pages and dated project evidence. A source link is not permission to copy or redistribute its contents. Blank, unavailable, or unverified evidence is not guessed. Last focused official re-reads: 19 Nov 2026.</p>
<h2>What can be concluded now</h2>
{table(["Question / decision", "Answer today", "Verified information", "Missing information", "Gate and recommended next step", "Sources"], rows, cls="dense", filter_id="decision-guide")}
<h2>Safe path forward</h2>
<ol>
<li><b>Continue shadow singles only, in the requested order: side, then total, then moneyline.</b> Pre-register each model version and freeze probability, inputs, fair line, contemporaneous market line and residual before kickoff. Grade against official final results; do not call a line profitable or calibrated until the holdout gates clear.</li>
<li><b>Protect the evidence chain.</b> Keep raw-source values and derived analysis separate; label every capture with source, fetch time, hash, parser version and conflicts. Do not present a missing row as healthy or available.</li>
<li><b>Keep all strategies off reward rankings until qualification.</b> Use benchmark-relative Brier skill for probabilities and proper-score/error measures appropriate to numeric lines; publish n, uncertainty, multiplicity adjustment, calibration and the stake-independent signal result. Staking/ROI is a later escrow, never a substitute for signal skill.</li>
<li><b>Hold combination products behind a separate gate.</b> Require directly validated joint probabilities and explicit void/push settlement; no product of marginal probabilities as a substitute.</li>
<li><b>Do not claim “luck removed.”</b> Use pre-registration, chronological holdouts, controls, confidence bounds and multiplicity correction to limit false discoveries; residual uncertainty remains.</li>
</ol>
<h2>Choices that cannot safely be made automatically</h2>
<p>These are not data gaps that code can resolve: (1) whether to license an odds/snap-count feed and its budget/terms; (2) permission to systematically retrieve or republish NFL content; (3) approved private storage, retention and who receives alerts; and (4) whether any reward exists. Until approved, the conservative defaults are official published snapshots only, no open/close or CLV claim, paper research only, no raw-data publication and no reward. These defaults do not imply consent or legal clearance.</p>
<p>For the complete requirement-level gate list, see {a("index.html", "decision readiness table on the overview")}; for open questions and source targets, see {a("questions.html", "Questions")}; for alternatives and review, see {a("suggestions.html", "Suggestions")}. All unresolved items remain on {a("flagged.html", "Flagged for review")}.</p>
"""
    page("decision-guide.html", "Decision guide", body, lead="A plain-language answer to what the current evidence supports, what is still missing, and what must happen before a decision is defensible.")


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
    build_questions(); build_suggestions(); build_decision_guide(); build_repo_review(); build_sources(); build_flagged()
    build_readme()
    print("built", len(NAV), "pages")


if __name__ == "__main__":
    main()
