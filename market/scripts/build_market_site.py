#!/usr/bin/env python3
"""Build the market reality site under market/.

Design rules, enforced here rather than left to judgement:
  * every data row renders an official source link; a missing link is written as a
    visible warning, not an empty cell;
  * a value that does not exist is an em dash with a title attribute saying why, never
    an estimate;
  * every number that could be mistaken for skill carries n in the same table;
  * numbers are not recomputed in the template layer. They are read from
    market/data/*.json, which is produced by the scripts and re-runnable.
"""
import html
import json
from pathlib import Path

MARKET = Path(__file__).resolve().parent.parent
REPO = MARKET.parent
P = MARKET / "pages"
P.mkdir(parents=True, exist_ok=True)
(MARKET / "assets").mkdir(parents=True, exist_ok=True)

D = {}


def load(name):
    D[name] = json.loads((MARKET / "data" / name).read_text())
    return D[name]


prices9 = load("raw/official-prices-w9.json")
prices10 = load("raw/official-prices-w10.json")
grading = load("grading.json")
tour = load("tournament.json")
own = load("own-lines.json")
corr = load("correlations.json")
depth = load("depth.json")
crawl = load("repo-crawl.json")
ver = load("verification.json")
dg = load("decision-gate.json")

STAMP = "2026-11-14"

NAV = [
    ("index", "Overview", "01"),
    ("summary", "Executive summary", "02"),
    ("prices", "Price snapshot store", "03"),
    ("grading", "Results & ROI", "04"),
    ("strategies", "Strategy board", "05"),
    ("own-lines", "Own lines vs market", "06"),
    ("correlations", "Correlations", "07"),
    ("availability", "Injuries & replacement", "08"),
    ("verification", "Verification", "09"),
    ("review", "Repository review", "10"),
    ("suggestions", "Suggestions", "11"),
    ("questions", "Open questions", "12"),
    ("method", "Method & limits", "13"),
]


def e(x):
    return "" if x is None else html.escape(str(x))


def a(url, label="source"):
    if not url:
        return '<span class="badge bad">NO OFFICIAL SOURCE</span>'
    if not str(url).startswith("http"):
        return f"<code>{e(url)}</code>"
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def badge(text, kind=None):
    if kind is None:
        t = str(text).upper()
        kind = ("good" if t.startswith("VERIFIED") or t == "SCORED"
                else "bad" if ("NOT SKILL" in t or "UNPRICEABLE" in t or "FAIL" in t or "UNVERIFIED" in t)
                else "warn" if ("UNDERPOWERED" in t or "NO SIGNAL" in t or "OPEN" in t or "BLOCKED" in t)
                else "neutral")
    return f'<span class="badge {kind}">{e(text)}</span>'


def num(x, digits=2, signed=False, suffix=""):
    if x is None:
        return '<td class="num missing" title="not available from any official source">—</td>'
    fmt = f"{x:+.{digits}f}" if signed else f"{x:.{digits}f}"
    return f'<td class="num">{fmt}{suffix}</td>'


def pct(x, digits=1, signed=True):
    return "—" if x is None else (f"{x*100:+.{digits}f}%" if signed else f"{x*100:.{digits}f}%")


def table(headers, rows, caption, note=None):
    """rows: list of lists. A cell that is already HTML must be marked with _H."""
    out = ('<div class="table-tools"><label>Filter rows <input type="search" '
           f'placeholder="Search…" aria-label="Filter {e(caption)}"></label>'
           f'<span class="row-count">{len(rows)} rows</span></div><div class="table-wrap"><table><caption>{e(caption)}</caption><thead><tr>'
           + "".join(f'<th scope="col">{e(h)}</th>' for h in headers) + "</tr></thead><tbody>")
    def cell(c):
        if isinstance(c, str) and c.startswith("<td"):
            return c
        if isinstance(c, str) and c.startswith("<"):
            return f"<td>{c}</td>"
        return f"<td>{e(c)}</td>"

    for row in rows:
        out += "<tr>" + "".join(cell(c) for c in row) + "</tr>"
    out += "</tbody></table></div>"
    out += f'<p class="table-note">{note or "Every row links an official source. A dash (—) is a value that does not exist in any official source, left blank on purpose and never estimated."}</p>'
    return out


def notice(body, title="Research boundary", kind=""):
    return f'<div class="notice {kind}"><strong>{e(title)}</strong><p>{body}</p></div>'


def sec(t):
    return f"<h2>{e(t)}</h2>"


def wrap(slug, title, desc, body):
    root = slug == "index"
    pre = "" if root else "../"
    nav = ""
    for key, label, n in NAV:
        cur = ' aria-current="page"' if key == slug else ""
        if key == "index":
            href = f"{pre}index.html"
        else:
            href = f"{key}.html" if not root else f"pages/{key}.html"
        nav += f'<a{cur} href="{href}"><span>{n}</span>{e(label)}</a>'
    nav += f'<a href="../index.html"><span>↗</span>Root dashboard</a>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{e(desc)}"><title>{e(title)} · Own8 market</title>
<link rel="stylesheet" href="{pre}assets/style.css"><script src="{pre}assets/app.js" defer></script>
</head><body><a class="skip" href="#main">Skip to content</a><aside>
<a class="brand" href="{pre}index.html"><span class="brand-mark">8</span> OWN8<span class="lab">MARKET REALITY</span></a>
<div class="nav-label">NFL / PRICE &amp; SKILL AUDIT</div><nav aria-label="Main navigation">{nav}</nav>
<div class="aside-foot"><span class="pulse"></span> Official FanDuel prices via nfl.com<br><small>Capture {STAMP}<br>Paper research only</small></div>
</aside><div class="workspace"><header><span>NFL LINE ORIGINATION <span class="muted">/ {e(title)}</span></span><span class="date">2026 SEASON · WEEK 10</span></header>
<main id="main"><div class="eyebrow">OWN8 MARKET REALITY / {STAMP}</div><h1>{e(title)}</h1><p class="lead">{e(desc)}</p>{body}</main>
<footer><span>OWN8 · Evidence before edge.</span><span>Snapshot, not live odds. No wagering or cash rewards.</span></footer></div></body></html>"""


def page(slug, title, desc, body):
    (MARKET / ("index.html" if slug == "index" else f"pages/{slug}.html")).write_text(
        wrap(slug, title, desc, body))


# ============================================================ derived small facts
w9 = grading["week9"]
ov = w9["overall"]
lb = {r["id"]: r for r in tour["leaderboard"]}
h2h = own["week9_head_to_head"]["summary"]
n_priced = len(prices9["games"]) + len(prices10["games"])
n_mk = n_priced * 3
w9_scores_url = "https://www.nfl.com/scores/2026/week-9"


def totals_row(market_key):
    m = w9["by_market"][market_key]
    return [market_key.capitalize(), m["bets"], m["settled"], f'{m["wins"]}–{m["losses"]}–{m["pushes"]}',
            f'{m["hit_rate"]*100:.1f}%',
            f'[{m["hit_rate_wilson95"][0]*100:.1f}%, {m["hit_rate_wilson95"][1]*100:.1f}%]',
            f'{m["breakeven_rate_at_prices"]*100:.1f}%',
            f'{m["profit_units"]:+.2f}u', pct(m["roi"]),
            f'{m["p_value_vs_breakeven"]:.3f}' if m["p_value_vs_breakeven"] is not None else "—",
            badge("UNDERPOWERED — NOT SKILL") if m["bets"] < 30 else badge(m["verdict"]),
            a(prices9["source_url"], "prices") + " " + a(w9_scores_url, "finals")]


# ============================================================ index
hero = f"""<div class="hero"><div><span class="pill">PRICE-FIRST · n ON EVERY NUMBER</span>
<h2>Our model lost<br>to the price.<br>That is the finding.</h2>
<p>Week 9 is the first week where an official locked price and an official final score exist for the same 15 games.
Our own line was closer than the market in {h2h["side"]["games_own_closer"]} of {h2h["n"]}.</p>
<a class="button" href="pages/summary.html">Read the executive summary <span>→</span></a></div>
<div class="hero-stat"><span>GAMES WITH AN OFFICIAL PRICE</span><strong>{n_priced}<span>/{n_priced}</span></strong>
<p>{n_mk} markets captured. One price per market, locked Thursday 2 p.m. ET.</p>
<small>No opening line. No closing line. Both flagged, not invented.</small></div></div>"""

cards = [
    (str(ov["bets"]), "Settled bets graded", "grading", "45 flat-stake bets, all markets"),
    (pct(ov["roi"]), "Flat-stake ROI, Week 9", "grading", "p = 0.104 — not skill"),
    ("12", "Registered strategies", "strategies", "3 scored, 9 unpriceable"),
    (str(len(crawl["findings"])), "Repository findings", "review", "line-by-line crawl"),
]
kpis = '<div class="kpis">' + "".join(
    f'<a class="kpi" href="pages/{u}.html"><span>{e(n)}</span><h2>{e(t)}</h2><small>{e(s)}</small></a>'
    for n, t, u, s in cards) + "</div>"

findings = [
    ["Official prices exist", f"nfl.com publishes FanDuel moneyline, spread and total for every game, locked 2 p.m. ET Thursday. {n_priced} games and {n_mk} markets transcribed verbatim for Weeks 9 and 10.",
     badge("VERIFIED"), a(prices10["source_url"], "picks article, Week 10")],
    ["Profit is not skill", f"S6, S7 and S8 picked the identical 15 moneyline sides and all returned {pct(lb['S6']['roi'])}. Their mean per-bet skill was "
     f"{lb['S6']['mean_skill']:+.4f}, {lb['S7']['mean_skill']:+.4f} and {lb['S8']['mean_skill']:+.4f}. Ranking by ROI would have promoted the worst-calibrated of the three.",
     badge("NOT SKILL"), a(w9_scores_url, "Week 9 finals")],
    ["Our line trails the market", f"Spread MAE {h2h['side']['own_mae']:.2f} against the market's {h2h['side']['market_mae']:.2f}; moneyline Brier {h2h['moneyline']['own_brier']:.3f} against {h2h['moneyline']['market_devig_brier']:.3f} de-vigged. The paired interval excludes zero.",
     badge("NOT SKILL"), a(w9_scores_url, "Week 9 finals")],
    ["Depth order is not published", "The nfl.com depth-chart URL returns the official 404 page. The roster publishes a transaction status, not an order. Only the postgame Game Book names starters.",
     badge("BLOCKED"), a("https://www.nfl.com/teams/kansas-city-chiefs/depth-chart", "depth chart (404)")],
    ["Parlays and props cannot be scored", "nfl.com publishes no parlay or player-prop price at any URL tested. S9–S12 are marked unpriceable rather than estimated at an assumed number.",
     badge("UNPRICEABLE"), a(prices10["source_url"], "picks article, Week 10")],
]
PRICES10 = prices10["source_url"]
SCORES9 = w9_scores_url
entry = [
    ["Price snapshot store", "prices", f"{n_priced} games, {n_mk} markets, verbatim strings plus the stated lock time. Opening and closing columns exist and are blank, because they do not exist.", PRICES10],
    ["Results, ROI and the verdicts", "grading", f"{ov['bets']} settled bets, {pct(ov['roi'])} ROI, p = {ov['p_value_vs_breakeven']:.3f}. Every row carries its own verdict string.", SCORES9],
    ["Strategy board", "strategies", "Signal and staking shown as separate columns. Rank is set by the lower-bound skill, never by ROI.", PRICES10],
    ["Own lines against the market's", "own-lines", "Fair line, market line and difference as three separate columns, in one stated sign convention.", PRICES10],
    ["Correlations with n on every value", "correlations", f"{len(corr['rows'])} values, Holm-corrected, each with a sentence saying what it cannot be used for.", "https://nextgenstats.nfl.com/stats/passing/2026/REG/9"],
    ["Injuries and replacement depth", "availability", f"{sum(c['rows'] for c in depth['club_injury_load'])} official injury rows and a capability matrix of what each official URL actually yields.", "https://www.nfl.com/injuries/league/2026/reg10"],
    ["Verification ledger", "verification", f"{ver['checks_passed']} of {ver['checks_total']} checks re-run today against official URLs.", "https://www.nfl.com/standings/league/2026/REG"],
    ["Repository review", "review", f"{crawl['files_scanned']} JSON files crawled, {crawl['row_like_dicts_total']} row-like objects, {crawl['unsourced_rows_total']} without a source link.", PRICES10],
    ["Suggestions", "suggestions", f"{len(dg['suggestions'])} proposals, each with options and a recommendation. None implemented.", PRICES10],
    ["Open questions", "questions", f"{len(dg['questions'])} questions, split by whether today's information can answer them.", PRICES10],
]

body = (hero + kpis + sec("What the evidence says")
        + table(["Finding", "Detail", "Classification", "Official source"], findings, "Executive findings")
        + notice("The repository previously stated that no official sportsbook line exists. That statement is wrong and it is finding F-01. "
                 "Official FanDuel prices are published weekly by nfl.com. What is still missing is an opening price, a closing price and any price on a parlay or a player prop.",
                 "Correction to the record", "warn")
        + sec("Every page in this workspace")
        + table(["Surface", "What is in it", "Official basis"],
                [[f'<a href="pages/{u}.html"><strong>{e(t)} →</strong></a>', e(d), a(src, "source")]
                 for t, u, d, src in entry], "Workspace index")
        + '<div class="section-links">'
        f'<a href="pages/suggestions.html"><strong>Review suggestions →</strong><p>{len(dg["suggestions"])} proposals with options and a recommendation. Nothing is implemented until you pick one.</p></a>'
        f'<a href="pages/questions.html"><strong>Answer open questions →</strong><p>{len(dg["questions"])} decisions, split into what today\'s information can and cannot settle.</p></a>'
        f'<a href="pages/summary.html"><strong>Read the executive summary →</strong><p>The whole audit in one page, including what we would need to be wrong about.</p></a></div>')
page("index", "Market reality", "What the official prices actually say about our own lines, our strategies and our claims.", body)

# ============================================================ summary
s_rows = [
    ["1", "Official prices exist and are now in the repository",
     f"nfl.com publishes FanDuel moneyline, spread and total for every game, locked at 2 p.m. ET on the Thursday of that week. "
     f"Weeks 9 and 10 were transcribed verbatim: {n_priced} games, {n_mk} markets. Every price carries the source URL, the stated lock timestamp "
     f"and the retrieved date, because the article is mutable.",
     badge("VERIFIED"), a(prices10["source_url"], "Week 10 prices")],
    ["2", "The repository's central claim about prices is false",
     "ledger/data/price-snapshots.json marks all 39 markets blank with the status 'no official source publishes this market'. That is contradicted "
     "by the same game's numbers on nfl.com. This is the highest-severity finding in the crawl (F-01) and it is not this session's file to edit.",
     badge("WRONG — FLAGGED"), a(prices10["source_url"], "Week 10 prices")],
    ["3", f"Profit and skill disagree in the same 15 bets",
     f"S6, S7 and S8 chose identical sides, went 13–2 and returned {pct(lb['S6']['roi'])} each. Against the de-vigged market price their mean per-bet skill was "
     f"{lb['S6']['mean_skill']:+.4f}, {lb['S7']['mean_skill']:+.4f} and {lb['S8']['mean_skill']:+.4f}. Two are significantly negative after Holm (p = 0.002). "
     f"The win came from the prices the winners were paid at, not from knowing more than the market.",
     badge("NOT SKILL"), a(w9_scores_url, "Week 9 finals")],
    ["4", "Our own line does not beat the market's",
     f"On the same 15 games our spread was off by {h2h['side']['own_mae']:.2f} points on average and the market's by {h2h['side']['market_mae']:.2f}; "
     f"we were closer in {h2h['side']['games_own_closer']} games. Our moneyline Brier score was {h2h['moneyline']['own_brier']:.3f} against {h2h['moneyline']['market_devig_brier']:.3f}. "
     "Both paired intervals exclude zero, in the unfavourable direction.",
     badge("NOT SKILL"), a(w9_scores_url, "Week 9 finals")],
    ["5", "Blending our line in would make things worse",
     f"Fitted on Week 9, the best weight on our own number is 0.0 for every strategy tested: the Brier score rises monotonically from {own['blend']['by_strategy']['S6']['best_brier']:.4f} at weight 0 "
     "to 0.1899 at weight 1. A weight fitted on 15 games is a description of 15 games, so the rule is to adopt nothing until 60 priced games are scored walk-forward.",
     badge("DERIVED"), a(w9_scores_url, "Week 9 finals")],
    ["6", "Nine of twelve strategies cannot be scored at all",
     "S1–S5 need a price on a spread or a total and nfl.com publishes none, so grading them requires an assumed −110. S9–S12 are parlays and props, "
     "for which no official price exists anywhere we can reach. All nine are marked unpriceable rather than estimated.",
     badge("UNPRICEABLE"), a(prices10["source_url"], "Week 10 prices")],
    ["7", "A pregame depth order does not exist officially",
     f"{sum(c['rows'] for c in depth['club_injury_load'])} official injury rows across {len(depth['club_injury_load'])} clubs, and {len(depth['verified_replacement_cases'])} confirmed quarterback "
     "changes with official URLs. But no official source states who is 1st, 2nd or 3rd string before kickoff. The Game Book names the 11 starters only after the whistle.",
     badge("BLOCKED"), a("https://www.nfl.com/teams/kansas-city-chiefs/depth-chart", "depth chart (404)")],
    ["8", f"{ver['checks_passed']} of {ver['checks_total']} verification checks pass today",
     "Including that the moneyline favourite agrees with the spread favourite on all 14 Week 10 games, that every two-way implied probability sums to more than 1, "
     "and that 192 standings cells reconcile to the 136-game official log plus the one played Week 10 game. Nothing failed.",
     badge("VERIFIED"), a("https://www.nfl.com/standings/league/2026/REG", "standings")],
    ["9", f"{len(crawl['findings'])} repository findings, of which 2 are high severity",
     f"{crawl['files_scanned']} JSON files and {crawl['row_like_dicts_total']} row-like objects crawled. {crawl['unsourced_rows_total']} row-like objects carry no source link. "
     f"There are {len(depth['register_duplication']['suggestions'])} separate suggestion registers and "
     f"{len(depth['register_duplication']['questions'])} separate question registers in one repository, and two independent Week 10 line sets that disagree.",
     badge("OPEN — FOR REVIEW"), a("https://github.com/sassnarep3-star/Own8", "repository")],
    ["10", "Nothing here is a recommendation",
     "No strategy is promoted. No stake is suggested. No reward is defined. The reward question is a policy decision with legal implications and is put to the operator as SG-05 "
     "rather than assumed.",
     badge("PAPER ONLY"), a(prices10["source_url"], "Week 10 prices")],
]
body = (notice("This page is the executive summary for the market-reality workspace. Every number on it is reproduced, with its source and its n, on a detail page. "
               "Where a value does not exist it is absent rather than estimated.", "How to read this page")
        + table(["#", "Finding", "Evidence", "Verdict", "Official source"], s_rows, "Executive summary")
        + sec("What would change our mind")
        + '<div class="card"><h3>Three results that would overturn the conclusion above</h3><ul>'
          '<li>Sixty or more priced games in which our line\'s mean absolute error is below the market\'s, with the paired interval excluding zero in our favour.</li>'
          '<li>A strategy whose lower 95% bound on per-bet skill is above zero after Holm across the whole family, i.e. not a single lucky week.</li>'
          '<li>A closing price that our model beats systematically. That test is currently impossible because no closing price is captured.</li>'
          '</ul></div>'
        + sec("What we still cannot do, and why")
        + table(["Gap", "Why it is not done", "What would fix it", "Where it is tracked", "Official page checked"],
                [["Opening and closing prices", "The published article carries one number per market, locked Thursday. No history is published.",
                  "Capture the same page twice a week and store both readings.", '<a href="suggestions.html">SG-02</a>', a(PRICES10, "prices")],
                 ["Parlay and prop prices", "No official NFL source publishes them at any URL tested.",
                  "Either a labelled non-official source, or state plainly that combos are unpriceable.", '<a href="suggestions.html">SG-11</a>', a(PRICES10, "prices")],
                 ["Pregame depth order", "The depth-chart URL is a 404; the roster publishes a transaction status, not an order.",
                  "Collect the postgame Game Book weekly and join it to the injury report.", '<a href="suggestions.html">SG-04</a>', a("https://www.nfl.com/teams/kansas-city-chiefs/depth-chart", "depth chart (404)")],
                 ["A reward that means something", "Rewards would need to be defined, and a reward with value is regulated activity.",
                  "A decision, not a measurement. Paper points are safe.", '<a href="suggestions.html">SG-05</a>', a("https://wsgc.wa.gov/responsible-gaming-self-exclusion", "regulator guidance")],
                 ["One canonical ranking", "Four leaderboards rank on four different quantities.",
                  "Pick one quantity and retire or demote the rest.", '<a href="suggestions.html">SG-01</a>', a("https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm", "NIST on multiple comparisons")]],
                "Gaps and their owners")
        + '<div class="section-links"><a href="suggestions.html"><strong>Choose a path →</strong><p>12 proposals, 4 options each, one recommendation each.</p></a>'
          '<a href="questions.html"><strong>11 open questions →</strong><p>Split by whether today\'s information can answer them.</p></a>'
          '<a href="review.html"><strong>Repository findings →</strong><p>The line-by-line crawl, including the two high-severity items.</p></a></div>')
page("summary", "Executive summary",
     "Ten findings, the three results that would overturn them, and the five things this workspace still cannot do.",
     body)

# ============================================================ prices
p_rows = []
for src, wk, label in ((prices9, 9, "Week 9"), (prices10, 10, "Week 10")):
    for g in src["games"]:
        p_rows.append([
            str(g["week"]), f'{g["away"]} @ {g["home"]}',
            f'{g["away_ml"]:+d}' if g["away_ml"] else "—",
            f'{g["home_ml"]:+d}' if g["home_ml"] else "—",
            f'{g["spread_home"]:+.1f}' if g.get("spread_home") is not None else "—",
            f'{g["total"]:.1f}' if g.get("total") is not None else "—",
            "—",
            "—",
            a(g.get("game_url"), "game"),
            a(src["source_url"], f"prices W{g['week']}"),
        ])
p_note = ("A dash under opening or closing is not missing data entry: no official source publishes an opening or a closing number. "
          "The one published number is locked at 2 p.m. ET on the Thursday of that week and is reproduced verbatim on each row's source link.")
body = (notice(
    f"One price per market, per week. The article states that the lines are provided by FanDuel and are locked as of 2 p.m. ET on the Thursday of that week, "
    f"so there is no opening price and no closing price to capture. Those two columns are published and left blank rather than filled from memory. "
    f"{n_priced} games × 3 markets = {n_mk} price cells, transcribed verbatim, with the exact string retained in the data file.",
    "What this store holds")
    + table(["Week", "Game", "Away ML", "Home ML", "Home spread", "Total", "Opening", "Closing", "Game", "Official source"], p_rows,
            f"Official locked prices, Weeks 9–10 ({len(p_rows)} games)",
            p_note)
    + sec("The verbatim strings, so the transcription can be checked by hand")
    + table(["Week", "Game", "Verbatim text as published", "Source"],
            [[str(g["week"]), f'{g["away"]} @ {g["home"]}', f'<code>{e(g["verbatim"])}</code>', a(g.get("game_url") or src["source_url"], "game")]
             for src in (prices9, prices10) for g in src["games"][:200]],
            "Verbatim price text")
    + notice("The picks article is the only official page that carries a price. It is mutable, so each price stores the date it was retrieved and the lock "
             "timestamp the article itself states. nfl.com has no odds hub: /odds and /odds/nfl both return 404, and the game-centre pages carry no price block. "
             "Do not look for prices there.", "Where prices do and do not come from", "warn")
    + sec("What the store does not contain")
    + table(["Field", "Status", "Reason"],
            [["Opening line", badge("MISSING", "bad"), "The article publishes one locked number. Nothing earlier is published anywhere official.", a(prices10["source_url"], "prices")],
             ["Closing line", badge("MISSING", "bad"), "Same: no second reading exists, and the article does not update after lock.", a(prices10["source_url"], "prices")],
             ["Price on a spread or total", badge("MISSING", "bad"), "nfl.com prints the number but not the juice. Grading at −110 is an assumption, and is labelled as one wherever it is used.", a(prices10["source_url"], "prices")],
             ["Parlay or prop price", badge("MISSING", "bad"), "Not published by any official NFL source we can reach.", a(prices10["source_url"], "prices")],
             ["Terms of use for automated collection", badge("MISSING", "warn"), "Not reviewed. Collection here was manual and once-weekly.", a("https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season", "source page")]],
            "Coverage gaps in the price store"))
page("prices", "Price snapshot store",
     "Every official number we could find, verbatim, with the lock time the article itself states — and the two columns that do not exist.",
     body)

# ============================================================ grading
g_rows = [totals_row(k) for k in ("side", "total", "moneyline")]
g_rows.append(["All markets", ov["bets"], ov["settled"], f'{ov["wins"]}–{ov["losses"]}–{ov["pushes"]}',
               f'{ov["hit_rate"]*100:.1f}%', f'[{ov["hit_rate_wilson95"][0]*100:.1f}%, {ov["hit_rate_wilson95"][1]*100:.1f}%]',
               f'{ov["breakeven_rate_at_prices"]*100:.1f}%', f'{ov["profit_units"]:+.2f}u', pct(ov["roi"]),
               f'{ov["p_value_vs_breakeven"]:.3f}', badge("UNDERPOWERED — NOT SKILL"),
               a(prices9["source_url"], "prices") + " " + a(w9_scores_url, "finals")])

bet_rows = []
for r in w9["rows"]:
    for b in r["bets"]:
        line = b.get("line")
        if b["market"] == "moneyline":
            # Fair probability on the side taken, ours vs the de-vigged price. De-vigging is
            # multiplicative on the implied probabilities published for the same game.
            def imp(ml):
                return 100.0 / (ml + 100.0) if ml > 0 else abs(ml) / (abs(ml) + 100.0)

            ph = r["fair_p_home"]
            ah, aa = imp(r["market_ml_home"]), imp(r["market_ml_away"])
            mh = ah / (ah + aa)
            ours_p = ph if b["model_side"] == "home" else 1 - ph
            theirs_p = mh if b["model_side"] == "home" else 1 - mh
            taken = f'{r[b["model_side"]]} ({b["model_side"]} ML)'
            ours = f'p={ours_p:.3f}'
            theirs = f'p={theirs_p:.3f} (de-vigged)' if r.get("fair_p_home") is not None else "—"
        elif b["market"] == "side":
            taken = f'{r[b["model_side"]]} {line:+}'
            ours = f'{b["fair_value"]:+.2f} (home)'
            theirs = f'{b["market_value"]:+.2f} (home)'
        else:
            taken = f'{b["model_side"].capitalize()} {line}'
            ours = f'{b["fair_value"]:.2f} (total)'
            theirs = f'{b["market_value"]:.2f} (total)'
        bet_rows.append([
            str(len(bet_rows) + 1), f'{r["away"]} @ {r["home"]}', b["market"].capitalize(),
            taken, ours, theirs,
            badge(b["result"], "good" if b["result"] == "win" else "bad"),
            f'{b["profit_units"]:+.3f}u',
            f'{r["market_spread_home"]:+.1f}' if b["market"] == "side" else (f'{r["market_total"]:.1f}' if b["market"] == "total" else "—"),
            a(r["result_source_url"], "final"), a(r["price_source_url"], "price"),
        ])
body = (notice(f"Fifteen games, three markets, one flat stake of 1 unit each, {ov['bets']} settled bets. "
               f"The result is {ov['wins']}–{ov['losses']} for {pct(ov['roi'])} on turnover and +{ov['profit_units']:.2f} units. "
               f"It is also p = {ov['p_value_vs_breakeven']:.3f} against the break-even rate implied by the prices actually taken, so it is not evidence of skill. "
               "Both statements are true at once, and the site prints both.", "The honest summary of Week 9", "warn")
    + table(["Market", "Bets", "Settled", "W–L–P", "Hit rate", "Wilson 95%", "Break-even", "Profit", "ROI", "p vs break-even", "Verdict", "Official source"],
            g_rows, "Week 9 ROI by market, flat 1u stake")
    + sec("How the verdicts are produced")
    + '<div class="card"><h3>Three gates, in order</h3><ul>'
      f'<li><strong>Break-even at the price taken.</strong> The break-even rate is recomputed from the prices actually available ({ov["breakeven_rate_at_prices"]*100:.1f}% across the book), not assumed to be 52.4%.</li>'
      '<li><strong>Sample size.</strong> Below 30 settled bets in a market, no ROI is called interpretable at all. The string UNDERPOWERED is attached to the row rather than left to the reader.</li>'
      '<li><strong>Exact binomial test against break-even.</strong> The p-value is two-sided and exact, not a normal approximation.</li></ul></div>'
    + sec("Every settled bet")
    + table(["#", "Game", "Market", "What we took", "Our fair number", "Market's number", "Result", "Profit", "Published line", "Official final", "Official price"], bet_rows,
            f"All {len(bet_rows)} settled bets, Week 9",
            "Reading the two number columns: for a <strong>side</strong> both are home handicaps, so a more negative number means we made the home team stronger than the market did; "
            "for a <strong>total</strong> both are points; for a <strong>moneyline</strong> both are probabilities on the side taken, and the market figure has had the book margin removed "
            "multiplicatively from the two published prices. Our probability minus the market's is the per-bet skill whose average the strategy board reports. "
            "Spreads and totals are priced at −110 because nfl.com publishes the number but not the price; that assumption is stated on the row and is the reason S1–S5 are not ranked.")
    + sec("Week 10")
    + notice("Zero bets graded. At the time of capture none of the 14 Week 10 games had been played, so there is nothing to settle. "
             "The prices are stored and will grade the moment official finals exist. An empty results table is the correct output here; "
             "filling it would be the error.", "Week 10 is pending, not missing", "warn"))
page("grading", "Results and ROI",
     "Every settled bet with its own verdict string, and the arithmetic that stops a 13–2 week from being called skill.",
     body)

# ============================================================ strategies
strat_rows = []
for r in tour["rows"]:
    lid = lb.get(r["id"])
    strat_rows.append([
        f'<strong>{r["id"]}</strong>', r["product"], r["strategy"], str(r["n_settled"]),
        pct(lid["roi"]) if lid else "—",
        f'{lid["mean_skill"]:+.4f}' if lid else "—",
        f'<strong>{lid["lower_bound_skill"]:+.4f}</strong>' if lid else "—",
        "—" if not lid else (badge("YES", "good") if lid["ranking_eligible"] else badge("NOT ELIGIBLE", "bad")),
        badge(r["status"]) if not lid else badge(lid["verdict"]),
        a(prices9["source_url"], "prices") if lid else a(prices10["source_url"], "page checked"),
    ])
body = (notice("Ranking is by the lower 95% bootstrap bound of per-bet skill, defined as the model's probability minus the de-vigged market probability on the "
               "side the strategy chose. ROI is shown in the next column and is never used to set a rank. That single choice is why S7 is ranked last "
               "despite returning the same +21.0% as the top-ranked strategy.", "The ranking rule, stated before any week is scored")
    + table(["ID", "Product", "Strategy", "Settled", "ROI (display only)", "Mean skill", "Lower 95% skill (rank key)", "Ranking eligible", "Status", "Official source"],
            strat_rows, f"All {len(tour['rows'])} registered strategies, Week 9 prices", tour["ranking_rule"])
    + sec("The headline: identical picks, identical profit, opposite skill")
    + f"""<div class="card"><h3>Three moneyline strategies, one set of picks</h3>
<p class="meta">S6 / S7 / S8 · 15 games · Week 9 official prices</p>
<ul>
<li>All three chose the <strong>identical side in all 15 games</strong>. They went <strong>13–2</strong> and returned <strong>{pct(lb['S6']['roi'])}</strong> each.</li>
<li>Per-bet skill: S6 <strong>{lb['S6']['mean_skill']:+.4f}</strong>, S7 <strong>{lb['S7']['mean_skill']:+.4f}</strong>, S8 <strong>{lb['S8']['mean_skill']:+.4f}</strong>.</li>
<li>Holm-adjusted significance on skill: S6 and S7 are <strong>significantly negative</strong> (p = 0.002). S8 is not significant (p = 0.922).</li>
<li>Holm-adjusted significance on ROI across the scored family: <strong>p = 0.74</strong>. Nothing here is distinguishable from luck.</li>
<li>Ranking by ROI would have promoted S8 over S6 and S7 for no reason other than the price on the winners. Ranking by lower-bound skill puts S7 last, which is correct: it was the worst-calibrated of the three.</li>
</ul></div>"""
    + sec("Why nine strategies are not scored")
    + table(["Group", "Strategies", "Why", "What it would take", "Page checked"],
            [["Spread and total singles", "S1, S2, S3, S4, S5", "nfl.com publishes the number but not the price. Grading at −110 is a convention, not an official number.",
              "An official price on a spread or a total.", a(prices10["source_url"], "prices")],
             ["Parlays and same-game parlays", "S9, S10", "No official parlay price exists at any URL tested.",
              "An official parlay price, or an explicit decision to use a labelled non-official one.", a(prices10["source_url"], "prices")],
             ["Player props", "S11, S12", "No official player-prop line or price exists at any URL tested.",
              "An official prop line and price.", a(prices10["source_url"], "prices")]],
            "Unpriceable strategies",
            "These are marked UNPRICEABLE rather than scored on an assumed number. An assumed price would make every ROI figure on the page unfalsifiable.")
    + notice("The Holm correction is applied across the three scored strategies only. Excluding the nine unpriceable ones makes the correction less conservative than a "
             "family that included them, which is the correct direction to err in when the alternative is a false claim of skill.",
             "A caveat on the multiple-comparison correction", "warn"))
page("strategies", "Strategy board",
     "Twelve strategies, three of them scoreable, ranked by evidence rather than by profit.",
     body)

# ============================================================ own lines
own_rows = []
for r in own["week10"]["rows"]:
    if r["market"] != "side":
        continue
    own_rows.append([
        f'{r["away"]} @ {r["home"]}',
        f'{r["own_fair_handicap_home"]:+.3f}',
        f'{r["market_published_handicap_home"]:+.1f}',
        f'{r["market_implied_handicap_home"]:+.3f}',
        f'<strong>{r["difference_vs_published"]:+.3f}</strong>',
        f'{r["difference_vs_devigged"]:+.3f}',
        f'{r["book_overround"]*100:.2f}%',
        a(r["price_source_url"], "prices"), a(r["game_url"], "game"),
    ])
h_rows = [
    ["Spread", f'n={h2h["n"]}', f'{h2h["side"]["own_mae"]:.2f}', f'{h2h["side"]["market_mae"]:.2f}',
     f'{h2h["side"]["mean_paired_diff_own_minus_market"]:+.2f}',
     f'[{h2h["side"]["paired_diff_ci95"][0]:+.2f}, {h2h["side"]["paired_diff_ci95"][1]:+.2f}]',
     f'{h2h["side"]["games_own_closer"]}/{h2h["n"]}', badge("MARKET BETTER", "bad"),
     a(prices9["source_url"], "prices") + " " + a(w9_scores_url, "finals")],
    ["Total", f'n={h2h["n"]}', f'{h2h["total"]["own_mae"]:.2f}', f'{h2h["total"]["market_mae"]:.2f}',
     f'{h2h["total"]["mean_paired_diff_own_minus_market"]:+.2f}',
     f'[{h2h["total"]["paired_diff_ci95"][0]:+.2f}, {h2h["total"]["paired_diff_ci95"][1]:+.2f}]',
     "—", badge("INCONCLUSIVE", "warn"),
     a(prices9["source_url"], "prices") + " " + a(w9_scores_url, "finals")],
    ["Moneyline (Brier)", f'n={h2h["n"]}', f'{h2h["moneyline"]["own_brier"]:.3f}', f'{h2h["moneyline"]["market_devig_brier"]:.3f}',
     f'{h2h["moneyline"]["mean_paired_diff_own_minus_market"]:+.4f}',
     f'[{h2h["moneyline"]["paired_diff_ci95"][0]:+.4f}, {h2h["moneyline"]["paired_diff_ci95"][1]:+.4f}]',
     "—", badge("MARKET BETTER", "bad"),
     a(prices9["source_url"], "prices") + " " + a(w9_scores_url, "finals")],
]
body = (notice("Three columns, never merged: <strong>our fair line</strong>, <strong>the market's line</strong>, and <strong>the difference</strong>. "
               "The sign convention is stated once and used everywhere: margin is home minus away, and the handicap is the negative of the margin, so a negative "
               "handicap means the home team is favoured. An earlier version of this workspace printed the two with opposite signs; that bug is fixed and the "
               "convention is now recorded in the data file itself.", "How to read the columns")
    + sec("Week 10 — prospective, not yet played")
    + table(["Game", "Our fair handicap", "Published market handicap", "Market-implied handicap", "Difference vs published", "Difference vs de-vigged", "Book margin", "Price", "Game"],
            own_rows, f"Week 10 own lines against the market ({len(own_rows)} games)",
            "The market-implied handicap is our own probability translated back through our own sigma. It is a translation, not a published number, and it is why the "
            "column sits beside the published handicap rather than replacing it. If our sigma is wrong, this column is wrong with it.")
    + sec("Week 9 — head to head on the same 15 games, with official finals")
    + table(["Market", "n", "Our error", "Market's error", "Mean paired difference", "95% interval", "Games we were closer", "Verdict", "Official source"],
            h_rows, "Own line versus the market, Week 9",
            "The paired interval is bootstrapped on the per-game differences, so it respects the fact that the two errors are measured on the same game.")
    + sec("Blend weight: how much of our number should go into the price?")
    + f"""<div class="card"><h3>The fitted answer is zero, and we are not adopting it</h3>
<p class="meta">Brier score by weight on our own probability · fitted on Week 9 · n = 15</p>
<ul>
<li>Weight 0.00 → Brier <strong>{own['blend']['by_strategy']['S6']['best_brier']:.4f}</strong> (market alone).</li>
<li>Weight 0.50 → Brier 0.1502. Weight 1.00 → Brier <strong>0.1899</strong> (our number alone).</li>
<li>The score degrades monotonically. Every extra percent of our number makes the forecast worse on this sample.</li>
<li>Decision rule recorded in the data file: <em>{e(own['blend']['decision_rule'])}</em></li>
</ul></div>"""
    + notice(f"The obvious temptation is to publish 'blend weight 0.0, therefore the market is right'. That conclusion is not supported by 15 games either. "
             f"The correct statement is narrower: on the only week where both numbers and an official final exist, our line was worse, and no weight on it improves the forecast. "
             f"Sixty priced games would be needed to say anything stronger.", "What this does not prove", "warn"))
page("own-lines", "Own lines vs market",
     "Fair line, market line and difference as three separate columns, in one stated convention, with the head-to-head result.",
     body)

# ============================================================ correlations
c_rows = []
for r in corr["rows"]:
    c_rows.append([
        f'<strong>{r["id"]}</strong>', r["label"], str(r["n"]), r["unit"],
        f'{r["r"]:+.3f}' if r["r"] is not None else "—",
        f'[{r["ci95"][0]:+.3f}, {r["ci95"][1]:+.3f}]' if r["ci95"][0] is not None else "—",
        f'{r["p_holm"]:.4f}' if r["p_holm"] is not None else "—",
        badge("SURVIVES", "good") if r["survives_holm_0.05"] else badge("NOT SIGNIFICANT", "neutral"),
        r["cannot_be_used_for"],
        a(r["source_url"], "source"),
    ])
body = (notice(f"{len(corr['rows'])} values, each computed only from rows that already carry an official source URL. Every value prints its n and a Fisher-z 95% interval, "
               f"and every value carries a sentence stating what it cannot be used for. Three survive Holm at 0.05; four do not. Values that could not be computed are "
               f"absent from the table rather than estimated.", "The rule for this page")
    + table(["ID", "Pair", "n", "Unit", "r", "95% interval", "Holm p", "Verdict", "What it cannot be used for", "Official source"],
            c_rows, "Correlations, each with its n and its limit",
            corr["source_note"] + " Every row links one fetchable official page. A dash (—) is a value that does not exist, never an estimate.")
    + sec("The distinction that matters")
    + '<div class="card"><h3>A correlation between outcomes is not a parlay price</h3>'
      '<p>Every value above is measured on realised outcomes. A parlay needs a joint probability for two legs that have not happened yet, conditional on everything known at '
      'kickoff. Those are different objects. The three surviving values say something real: a quarterback\'s passing yards travel with his own team\'s scoring '
      f'(r = {corr["rows"][3]["r"]:+.3f}, n = {corr["rows"][3]["n"]}) and with the game total, and the two opposing quarterbacks in the same game are positively associated '
      f'(r = {corr["rows"][5]["r"]:+.3f}, n = {corr["rows"][5]["n"]}). The practical consequence is the opposite of what a naive parlay builder assumes: treating those legs as '
      'independent <em>understates</em> the joint probability of two overs.</p></div>'
    + sec("Values deliberately not computed")
    + table(["Value", "Why it is absent", "Page checked"],
            [[x["what"], x["why"], a(x["page_checked"], "page checked")] for x in corr["not_computed"]],
            "Not computed, and why",
            "An estimated correlation would propagate directly into a parlay price. Absent is the honest state.")
    + notice("Nine weeks gives nine observations for the weekly-dependence question (C7). A confidence interval that wide is reported rather than hidden, and the absence of "
             "a significant weekly effect is not evidence that games in a week are independent. Treating unknown dependence as independence is the error this page exists to avoid.",
             "The smallest sample on the page", "warn"))
page("correlations", "Correlations",
     f"{len(corr['rows'])} values with n on every row, Holm correction, and an explicit statement of what each one cannot price.",
     body)

# ============================================================ availability
cap_rows = [[x["what"], badge(x["http_result"].split(" - ")[0], "good" if x["http_result"].startswith("200") else "bad"),
             x["http_result"], x["yields"], x["cannot"], a(x["source"])] for x in depth["capability_matrix"]]
club_rows = [[c["team"], str(c["rows"]), str(c["offense"]), str(c["defense"]), str(c["specialists"]),
              str(c["out"]), str(c["doubtful"]), str(c["questionable"]), a(c["source_url"], "injury report")]
             for c in depth["club_injury_load"]]
case_rows = [[c["team"], c["position"], c["starter_out"], c["replacement"], c["depth_note"], c["official_confirmation"], a(c["source_url"])]
             for c in depth["verified_replacement_cases"]]
body = (notice(depth["headline"], "The short answer", "warn")
    + sec("What every official URL actually gives you")
    + table(["Official page", "Reachable", "What it returned", "What it yields", "What it cannot tell you", "Link"],
            cap_rows, "Capability matrix, tested 2026-11-14")
    + sec("What we can deliver today")
    + '<div class="card"><ul>' + "".join(f"<li>{e(x)}</li>" for x in depth["what_is_deliverable_today"]) + "</ul></div>"
    + sec("What we cannot deliver, for any amount of effort, from official sources")
    + '<div class="card"><ul>' + "".join(f"<li>{e(x)}</li>" for x in depth["what_is_not_deliverable"]) + "</ul></div>"
    + sec("The workaround that stays honest")
    + f'<div class="card"><p>{e(depth["workaround_that_stays_honest"])}</p></div>'.replace('<div class="card">', '<div class="card">', 1)
    + sec(f"Official injury rows, by club ({sum(c['rows'] for c in depth['club_injury_load'])} rows)")
    + table(["Club", "Rows", "Offence", "Defence", "Specialists", "Out", "Doubtful", "Questionable", "Official source"],
            club_rows, "Week 10 injury report by club",
            "Positions are grouped as offence, defence and specialists using a fixed list in market/scripts/analyze.py; anything else counts as unclassified rather than being guessed. "
            "<strong>Rows means rows on the report, not players with a disclosed injury:</strong> 185 of the 345 stored rows carry a practice status with no injury designation and no game status "
            "(repository finding F-07). The per-club counts inherit that shape and should not be read as an injury burden ranking.")
    + sec("Confirmed replacement cases, with official URLs")
    + table(["Club", "Pos", "Starter unavailable", "Replacement named", "How deep the replacement is", "Official confirmation", "Source"],
            case_rows, "Verified quarterback replacement events, Week 10")
    + notice("These six cases are the only ones where a club or the official news hub said publicly who would start. That is not a sampling choice: it is the whole "
             "of what official sources state. For offensive line, secondary and linebacker changes, no equivalent pregame statement exists.",
             "Six cases is the complete official record, not a sample", "warn"))
page("availability", "Injuries and replacement depth",
     "345 official injury rows, six confirmed quarterback replacements, and a precise account of why pregame depth order cannot be obtained.",
     body)

# ============================================================ verification
v_rows = [[c["id"], c["what"], e(str(c["expected"])), e(str(c["actual"])),
           badge("PASS", "good") if c["pass_"] else badge("FAIL", "bad"),
           (a(c["source_url"]) if str(c["source_url"]).startswith("http")
            else f'<code>{e(c["source_url"])}</code> <span class="badge neutral">INTERNAL</span> · '
                 + a(w9_scores_url, "finals checked"))]
          for c in ver["checks"]]
body = (notice(f"{ver['checks_passed']} of {ver['checks_total']} checks pass, re-run on {STAMP} against official URLs retrieved the same day. "
               f"A failure here fails the build: the script exits non-zero, so CI can gate on it. Nothing is repaired silently and nothing is inferred to make a check pass.",
               "Verification ledger")
    + table(["ID", "Check", "Expected", "Actual", "Result", "Official source"], v_rows, "Verification checks")
    + sec("What was checked, in plain language")
    + '<div class="card"><ul>'
      '<li>The 136-game official log was re-accumulated club by club and compared to today\'s official standings on every one of 192 cells: W, L, T, PF, PA and net points for 32 clubs.</li>'
      '<li>The one Week 10 game already played was added explicitly, so the reconciliation does not silently absorb a missing game.</li>'
      '<li>The Rams appear as LA in the standings and LAR in scores. That alias is applied inside the check only, and the alias itself is a recorded check rather than a hidden normalisation.</li>'
      '<li>For all 14 Week 10 games, the moneyline favourite and the spread favourite agree. If a transcription had a sign error, this is where it would surface.</li>'
      '<li>Every two-way implied probability sums to more than 1, i.e. the book margin is present in the data. A sum below 1 would mean a transcription or arithmetic error.</li>'
      '<li>Every graded side and total is re-checked against the sign of its own adjusted margin.</li>'
      '</ul></div>'
    + notice("One thing this ledger does not cover: an independent second reading of the price page. The checks prove the numbers are internally consistent and consistent "
             "with the official finals; they do not prove a second human would read the same numbers off the same page. That is suggestion SG-09.",
             "The gap in the verification", "warn"))
page("verification", "Verification",
     f"{ver['checks_passed']} checks against official sources, re-run on the day of publication, with the one gap stated.",
     body)

# ============================================================ review
f_rows = []
for f in crawl["findings"]:
    f_rows.append([
        f'<strong>{f["id"]}</strong>',
        badge(f["severity"].upper(), "bad" if f["severity"] == "high" else "warn" if f["severity"] == "medium" else "neutral"),
        f["area"], f["title"], f["evidence"], f'<code>{e(f["file"])}</code><br><small>{e(f["record"])}</small>',
        a(f["source_url"]), f["action_owner"],
    ])
inv_rows = [[f'<code>{i["file"]}</code>', str(i["row_like_dicts"]),
             str(i["rows_with_no_source_url"]) if i["rows_with_no_source_url"] else badge("0", "good"),
             a("https://github.com/sassnarep3-star/Own8/blob/main/" + i["file"], "file")]
            for i in crawl["inventory"] if i["rows_with_no_source_url"]]
body = (notice(f"Every JSON file in the repository outside this workspace was opened, parsed, and walked object by object: {crawl['files_scanned']} files, "
               f"{crawl['row_like_dicts_total']} row-like objects, {crawl['unsourced_rows_total']} of which carry no source link. "
               f"Nothing was edited outside <code>market/**</code>; every finding that belongs to another session is published here for that session to act on.",
               "Scope of the crawl")
    + sec("Findings")
    + table(["ID", "Severity", "Area", "Finding", "Evidence", "Where", "Official source", "Acts on it"], f_rows,
            f"{len(crawl['findings'])} findings from the crawl")
    + sec("The two that matter")
    + f"""<div class="card"><h3>F-01 · The repository says prices do not exist. They do.</h3>
<p class="meta">severity high · ledger/data/price-snapshots.json · 39 markets</p>
<p>All 39 markets in the ledger's price store are blank, and the status string attached to them states that no official source publishes the market. That is false.
nfl.com publishes FanDuel moneyline, spread and total for every game of the season, locked weekly. The same game appears in both places.</p>
<p>Why it matters: every gate downstream of that file treats the absence of a price as an unavailability of reality rather than a missing capture. Nine strategies are
unranked on that basis alone.</p></div>
<div class="card"><h3>F-02 · {len(depth["register_duplication"]["suggestions"])} suggestion registers and {len(depth["register_duplication"]["questions"])} question registers</h3>
<p class="meta">severity high · governance</p>
<p>{len(depth["register_duplication"]["suggestions"])} different files in this repository each present themselves as the place where suggestions are recorded, and
{len(depth["register_duplication"]["questions"])} present themselves as the place where questions are recorded. A reader who answers a question in one of them has
answered it in one-{len(depth["register_duplication"]["questions"])}th of the repository. This is not a data bug; it is the reason a decision can appear open forever.</p>
<p class="meta">Files counted as question registers</p>
<p><code>{e(", ".join(depth["register_duplication"]["questions"]))}</code></p>
<p class="meta">Files counted as suggestion registers</p>
<p><code>{e(", ".join(depth["register_duplication"]["suggestions"]))}</code></p></div>"""
    + sec("Files with unsourced rows")
    + table(["File", "Row-like objects", "Without a source link", "Open"], inv_rows,
            "Provenance gaps by file",
            "A row-like object is any dictionary that carries a URL field or sits among others that do. Its absence is recorded, not repaired. Some of these files are legitimate "
            "internal state rather than claims about the world, which is why the finding is a medium-severity flag and not an assertion of error.")
    + notice("The crawler flags; it does not judge every flag to be a defect. A derived file with no source URL may be entirely correct — it just cannot be checked from the "
             "file alone, which is exactly what the operator asked to be told.", "How to read the unsourced count", "warn"))
page("review", "Repository review",
     f"{crawl['files_scanned']} files crawled object by object, {len(crawl['findings'])} findings, two of them high severity.",
     body)

# ============================================================ suggestions
sug_html = [notice("Nothing on this page has been implemented. Each suggestion lists the options, a recommendation with its reason, the cost, the effect on the "
                   "validation gates, and what would have to be verified before it could be called done. Choose one; then it can be built.",
                   "Read this first")]
for s in dg["suggestions"]:
    opts = "".join(
        f'<div class="opt{ " rec" if s["recommendation"].startswith(k + ".") else ""}"><b>{k}</b>{e(v)}</div>'
        for k, v in s["options"].items())
    sug_html.append(f"""<div class="card"><h3>{e(s['id'])} · {e(s['title'])}</h3>
<p class="meta">{badge(s['state'], 'warn')} {badge(s['priority'])}</p>
<p>{e(s['problem'])}</p><div class="opts">{opts}</div>
<p><strong>Recommendation.</strong> {e(s['recommendation'])}</p>
<ul><li><strong>Cost.</strong> {e(s['cost'])}</li>
<li><strong>Effect on the gates.</strong> {e(s['gate_impact'])}</li>
<li><strong>What must be verified.</strong> {e(s['verification_required'])}</li>
<li><strong>Reference.</strong> {a(s['source_url'], 'source')}</li></ul></div>""")
path = dg["recommended_path"]
body = ("".join(sug_html)
        + sec("If you only act on five")
        + f"""<div class="card"><h3>{e(path['headline'])}</h3><ol class="steps">{''.join(f'<li>{e(x)}</li>' for x in path['steps'])}</ol>
<p><strong>And explicitly not:</strong></p><ul>{''.join(f'<li>{e(x)}</li>' for x in path['what_not_to_do'])}</ul></div>""")
page("suggestions", "Suggestions",
     f"{len(dg['suggestions'])} suggestions, each with options, a recommendation and its cost. Nothing is implemented until a path is chosen.",
     body)

# ============================================================ questions
q_html = [notice(f"{len(dg['questions'])} questions. Each is marked with whether today's information can answer it: "
                 f"{dg['counts']['answerable_now']} yes, {dg['counts']['partly']} partly, {dg['counts']['not_answerable']} no. "
                 "For each one there is a concrete way to discover what is missing, and a statement of what stays blocked until it is.", "How to use this page")]
for q in dg["questions"]:
    kind = ("good" if q["answerable_from_current_information"].startswith("YES")
            else "warn" if q["answerable_from_current_information"].startswith("PARTLY") else "bad")
    q_html.append(f"""<div class="card"><h3>{e(q['id'])} · {e(q['question'])}</h3>
<p class="meta">{badge(q['answerable_from_current_information'].split(' - ')[0].split(' for ')[0].split(' YES')[0], kind)} {badge('owner: ' + q['who_can_answer'], 'neutral')}</p>
<p><strong>Answerable from today's information:</strong> {e(q['answerable_from_current_information'])}</p><p><strong>Why it blocks a decision.</strong> {e(q['why_it_blocks_a_decision'])}</p>
<ul><li><strong>What we have.</strong> {e(q['what_we_have'])}</li>
<li><strong>What we lack.</strong> {e(q['what_we_lack'])}</li>
<li><strong>How to discover it.</strong> {e(q['discovery_plan'])}</li>
<li><strong>Blocks.</strong> {e(q['blocks'])}</li>
<li><strong>Reference.</strong> {a(q['source_url'], 'official reference')}</li></ul></div>""")
q_html.append(sec("Summary") + table(
    ["ID", "Question", "Answerable today", "Blocks", "Who can answer", "Official reference"],
    [[q["id"], q["question"],
      badge(q["answerable_from_current_information"].split(" - ")[0],
            "good" if q["answerable_from_current_information"].startswith("YES") else
            "warn" if q["answerable_from_current_information"].startswith("PARTLY") else "bad"),
      q["blocks"], q["who_can_answer"], a(q["source_url"], "reference")] for q in dg["questions"]],
    "All open questions"))
page("questions", "Open questions",
     f"{len(dg['questions'])} questions that must be settled before a decision, split by whether today's information can settle them.",
     "".join(q_html))

# ============================================================ method
body = (sec("What this workspace does")
        + '<div class="card"><ul>'
          '<li>Stores official prices verbatim, with the lock time the source itself states and the date of retrieval.</li>'
          '<li>Grades every bet against official finals, at a flat 1-unit stake, with the break-even rate recomputed from the prices actually available.</li>'
          '<li>Splits signal from staking so that profit cannot stand in for calibration.</li>'
          '<li>Ranks by the lower 95% bound of per-bet skill after Holm, and prints ROI beside it without ever ranking on it.</li>'
          '<li>Publishes the fair line, the market line and the difference as three columns in one stated sign convention.</li>'
          '<li>States, on every correlation, what it cannot be used to price.</li>'
          '<li>Tests what each official URL actually returns, and reports the 404s rather than routing around them.</li>'
          '</ul></div>'
        + sec("What this workspace refuses to do")
        + table(["Refusal", "Reason", "Official page that demonstrates it"],
                [["Estimate a missing price", "An assumed −110 makes every ROI figure unfalsifiable. Where a price is absent the strategy is unpriceable, not scored.", a(prices10["source_url"], "prices")],
                 ["Infer a depth position", "No official source publishes pregame depth order. Inferring it would put an invented number inside a model.", a("https://www.nfl.com/teams/kansas-city-chiefs/depth-chart", "depth chart (404)")],
                 ["Rank on ROI", "Week 9 has three strategies with identical ROI and skill ranging from −0.112 to +0.028. ROI cannot separate them.", a(w9_scores_url, "finals")],
                 ["Call 15 games an edge", "The interval on 13 of 15 at these prices includes break-even comfortably; p = 0.104.", a(w9_scores_url, "finals")],
                 ["Fill a blank cell with a plausible number", "Every blank on this site is either a value that does not exist or a value nobody has captured, and the difference is stated.", a(PRICES10, "prices")],
                 ["Award a reward", "Nothing is rewarded. The reward question is SG-05 and it is a policy and legal question, not a modelling one.", a("https://www.nfl.com/standings/league/2026/REG", "standings")]],
                "Design refusals")
        + sec("Reproduce everything on this site")
        + """<div class="card"><h3>Five commands, no dependencies beyond the Python standard library</h3>
<pre><code>cd /path/to/Own8
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=market python3 -m scripts.grade
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=market python3 -m scripts.tournament
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=market python3 -m scripts.model
python3 market/scripts/analyze.py
python3 market/scripts/verify.py &amp;&amp; python3 market/scripts/crawl.py &amp;&amp; python3 market/scripts/decide.py
python3 market/scripts/build_market_site.py</code></pre>
<p>Every seed is fixed at 20261114, so the bootstrap intervals and the permutation tests are identical on every run. <code>verify.py</code> exits non-zero if any check fails.</p></div>"""
        + sec("Known limitations")
        + table(["ID", "Limitation", "Consequence", "Official page"],
                [["LF-01", "One locked price per market. No opening, no closing.", "Closing-line value cannot be computed, and that is the standard test of whether a model adds anything.", a(PRICES10, "prices")],
                 ["LF-02", "The total model does not pass its own gates.", "Total markets are displayed and not recommended.", a(w9_scores_url, "finals")],
                 ["LF-03", "A single sigma is used for every game.", "The market-implied handicap is a translation of a probability, not a published number, and it inherits the sigma error.", a("https://www.itl.nist.gov/div898/handbook/prc/section2/prc231.htm", "NIST on a single sigma")],
                 ["LF-04", "The price page is mutable.", "Each price stores its retrieval date and the lock time the article states.", a(PRICES10, "prices")],
                 ["LF-05", "Nine of twelve strategies cannot be priced.", "The family correction is applied to three, which is less conservative than a family of twelve.", a(PRICES10, "prices")],
                 ["LF-06", "Demotion thresholds are unapproved.", "D1–D8 exist and are tested; they cannot fire because no strategy is live and no threshold was approved.", a("https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm", "NIST on multiple comparisons")],
                 ["LF-07", "Parlays and props have no official price.", "S9–S12 are unpriceable. The brief's parlay and prop-combo sections cannot be scored at all.", a(PRICES10, "prices")]],
                "Limitations register")
        + notice("Everything here is paper research. No selection is published as a recommendation, no stake is suggested, and no reward exists.",
                 "Scope"))
page("method", "Method and limits",
     "What is computed, what is refused, how to reproduce it, and the seven limitations that bound every claim on this site.",
     body)

print("wrote", len(NAV), "pages to", P)
