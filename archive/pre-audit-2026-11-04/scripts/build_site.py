#!/usr/bin/env python3
"""Own8 site builder (T5). Generates the static GitHub Pages site in docs/ from
data/*.json, analysis/*.json and research/*.md. Stdlib only, no network, no manual input.

Run: python3 scripts/build_site.py
"""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AN = ROOT / "analysis"
RES = ROOT / "research"
PAGES = ROOT / "pages"
ASSETS = ROOT / "assets"
for _d in (PAGES, ASSETS):
    _d.mkdir(parents=True, exist_ok=True)
(ROOT / ".nojekyll").write_text("")

def load(p):
    with open(p) as f:
        return json.load(f)

sources = load(DATA / "sources.json")["sources"]
src = {s["id"]: s for s in sources}
standings = load(DATA / "standings-2026-reg-w8.json")
sched = load(DATA / "schedule-2026-week9.json")
scores = load(DATA / "scores-2026-week8.json")
tp_off = load(DATA / "team-passing-offense-2026.json")
tr_off = load(DATA / "team-rushing-offense-2026.json")
tp_def = load(DATA / "team-passing-defense-2026.json")
tr_def = load(DATA / "team-rushing-defense-2026.json")
ppass = load(DATA / "player-passing-2026.json")
prush = load(DATA / "player-rushing-2026.json")
prec = load(DATA / "player-receiving-2026.json")
pint = load(DATA / "player-interceptions-2026.json")
ngs = load(DATA / "nextgen-passing-2026-week8.json")
inj = load(DATA / "injuries-2026-week8.json")
news = load(DATA / "news-items.json")
market = load(DATA / "market-lines.json")
flagged = load(DATA / "flagged.json")["items"]
corr = load(AN / "correlations.json")
lines = load(AN / "model-lines-week9.json")
props = load(AN / "prop-signals-week9.json")
strats = load(AN / "strategies.json")["strategies"]
board = load(AN / "leaderboard.json")

TEAM_URL = {
    "BUF": "buffalo-bills", "NE": "new-england-patriots", "NYJ": "new-york-jets", "MIA": "miami-dolphins",
    "PIT": "pittsburgh-steelers", "CIN": "cincinnati-bengals", "CLE": "cleveland-browns", "BAL": "baltimore-ravens",
    "JAX": "jacksonville-jaguars", "HOU": "houston-texans", "IND": "indianapolis-colts", "TEN": "tennessee-titans",
    "DEN": "denver-broncos", "KC": "kansas-city-chiefs", "LV": "las-vegas-raiders", "LAC": "los-angeles-chargers",
    "NYG": "new-york-giants", "DAL": "dallas-cowboys", "WAS": "washington-commanders", "PHI": "philadelphia-eagles",
    "MIN": "minnesota-vikings", "CHI": "chicago-bears", "DET": "detroit-lions", "GB": "green-bay-packers",
    "CAR": "carolina-panthers", "TB": "tampa-bay-buccaneers", "ATL": "atlanta-falcons", "NO": "new-orleans-saints",
    "SF": "san-francisco-49ers", "SEA": "seattle-seahawks", "LA": "los-angeles-rams", "AZ": "arizona-cardinals",
}
def team_link(a):
    return f'https://www.nfl.com/teams/{TEAM_URL[a]}/'

def esc(x):
    return html.escape("" if x is None else str(x))

def link(url, label=None):
    if not url:
        return '<span class="unverified">— (unverified/blank)</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label or url)}</a>'

def badge(status):
    s = esc(status)
    cls = {"PASS": "pass", "CONDITIONAL": "cond", "FAIL": "fail", "NOT_COMPUTABLE": "na", "PENDING": "cond"}.get(status.upper(), "na")
    return f'<span class="badge {cls}">{s}</span>'

def table(headers, rows, cls="data"):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = "".join(f"<td>{c}</td>" if isinstance(c, str) and c.startswith("<") else f"<td>{esc(c)}</td>" for c in r)
        trs.append(f"<tr>{tds}</tr>")
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'

def srclink(url, label="source"):
    return link(url, label)

NAV = [
    ("index.html", "Dashboard", False),
    ("executive-summary.html", "Executive Summary", False),
    ("standings.html", "Standings (W8)", False),
    ("schedule.html", "Week 9 Schedule", False),
    ("scores.html", "Week 8 Scores", False),
    ("team-stats.html", "Team Stats", False),
    ("player-stats.html", "Player Stats & NGS", False),
    ("injuries.html", "Injuries & News", False),
    ("model-lines.html", "Model Lines (W9)", False),
    ("prop-signals.html", "Prop Signals (W9)", False),
    ("strategies.html", "Strategies", False),
    ("validation-gates.html", "Validation Gates", False),
    ("correlations.html", "Correlations", False),
    ("leaderboard.html", "Leaderboard", False),
    ("methodology.html", "Methodology", False),
    ("sources.html", "Sources", False),
    ("flagged.html", "⚑ Flagged for Review", False),
    ("responsible-gambling.html", "Responsible Gambling", False),
    ("archive/session-9cf451e4-own8/index.html", "Archive (session 9cf451e4)", True),
]

def page(title, body, active, sub=False):
    prefix = "" if sub else "pages/"
    aprefix = "../" if sub else ""
    def navhref(href, ispath):
        if sub:
            if href == "index.html":
                return "../index.html"
            return ("../" + href) if ispath else href
        return href if href == "index.html" else (("" if ispath else "pages/") + href)
    nav = "".join(
        f'<a href="{navhref(href, ispath)}" class="{"active" if href == active else ""}">{esc(label)}</a>'
        for href, label, ispath in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Own8 NFL Lines</title>
<link rel="stylesheet" href="{aprefix}assets/style.css">
</head>
<body>
<div class="layout">
<aside class="sidebar">
  <div class="brand">🏈 Own8 <span>NFL Line Lab</span></div>
  <nav>{nav}</nav>
  <div class="sidefoot">Data as of 2026-11-03 · official sources only · <a href="{prefix}flagged.html">Flagged for Review</a></div>
</aside>
<main class="main">
<header class="topbar"><h1>{esc(title)}</h1><span class="asof">as of 2026-11-03 · 2026 NFL season, Week 9 slate</span></header>
<div class="content">
{body}
</div>
<footer class="footer">Own8 — research/analytics competition framework. Not gambling advice; no real-money wagering occurs here. Every table row links to its official source; unverifiable values are blank and <a href="{prefix}flagged.html">flagged</a>. 18+ (NL) / 21+ where required — <a href="{prefix}responsible-gambling.html">responsible gambling</a>.</footer>
</main>
</div>
</body>
</html>"""

# ---------------- minimal markdown renderer ----------------
def md(text):
    out, in_list, in_table = [], False, False
    tbl_rows = []
    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>"); in_list = False
    def flush_table():
        nonlocal in_table, tbl_rows
        if in_table:
            rows = tbl_rows; tbl_rows = []
            head = rows[0]; body = rows[1:]
            out.append("<table class='data'><thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table>")
            in_table = False
    for line in text.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            tbl_rows.append(cells); in_table = True
            continue
        flush_table()
        if s.startswith("# "): flush_list(); out.append(f"<h2>{render_inline(s[2:])}</h2>")
        elif s.startswith("## "): flush_list(); out.append(f"<h3>{render_inline(s[3:])}</h3>")
        elif s.startswith("### "): flush_list(); out.append(f"<h4>{render_inline(s[4:])}</h4>")
        elif s.startswith("- "):
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{render_inline(s[2:])}</li>")
        elif s.strip():
            flush_list(); out.append(f"<p>{render_inline(s)}</p>")
        else:
            flush_list()
    flush_list(); flush_table()
    return "\n".join(out)

def render_inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s

def md_page(name, title, active, intro=""):
    text = (RES / name).read_text()
    body = (f"<p class='muted'>{esc(intro)}</p>" if intro else "") + md(text)
    write(active, page(title, body, active, sub=True))

def write(fname, content):
    if fname == "index.html":
        content = re.sub(r'href="([a-z0-9-]+\.html)"', r'href="pages/\1"', content)
        content = content.replace('href="pages/index.html"', 'href="index.html"')
        content = content.replace('href="pages/archive/', 'href="archive/')
        (ROOT / fname).write_text(content)
    else:
        (PAGES / fname).write_text(content)
    print("wrote", fname)

# ---------------- CSS ----------------
(ASSETS / "style.css").write_text("""
:root{--bg:#f4f6fa;--panel:#ffffff;--ink:#16202e;--muted:#5b6b7f;--line:#e3e8f0;--accent:#0b5fff;--accent2:#0a3d91;--pass:#0e8a4d;--cond:#b26a00;--fail:#c22f2f;--na:#6b7686;--flag:#c22f2f;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.5}
.layout{display:flex;min-height:100vh}
.sidebar{width:230px;background:#0e1b2e;color:#dbe4f0;display:flex;flex-direction:column;position:sticky;top:0;height:100vh;flex-shrink:0}
.brand{padding:18px 18px 12px;font-size:20px;font-weight:800;color:#fff}
.brand span{display:block;font-size:11px;font-weight:600;color:#8fa3c0;letter-spacing:.08em;text-transform:uppercase}
.sidebar nav{display:flex;flex-direction:column;padding:8px}
.sidebar nav a{color:#c6d3e6;text-decoration:none;padding:8px 12px;border-radius:8px;font-size:13.5px}
.sidebar nav a:hover{background:#1a2c47}
.sidebar nav a.active{background:var(--accent);color:#fff;font-weight:700}
.sidefoot{margin-top:auto;padding:14px;font-size:11px;color:#8fa3c0}
.sidefoot a{color:#9db8e8}
.main{flex:1;min-width:0;display:flex;flex-direction:column}
.topbar{display:flex;align-items:baseline;gap:14px;background:var(--panel);border-bottom:1px solid var(--line);padding:16px 26px;position:sticky;top:0;z-index:5}
.topbar h1{font-size:20px;margin:0}
.asof{color:var(--muted);font-size:12.5px}
.content{padding:22px 26px;max-width:1250px}
.footer{padding:16px 26px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);background:var(--panel)}
.footer a{color:var(--accent)}
h2{margin:26px 0 10px;font-size:18px;border-bottom:2px solid var(--line);padding-bottom:6px}
h3{margin:20px 0 8px;font-size:15.5px}
h4{margin:14px 0 6px;font-size:14px}
p{margin:8px 0}
a{color:var(--accent)}
.muted{color:var(--muted);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px;margin:14px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;text-decoration:none;color:var(--ink);transition:box-shadow .15s}
.card:hover{box-shadow:0 4px 14px rgba(20,40,80,.12)}
.card .kpi{font-size:26px;font-weight:800;color:var(--accent2)}
.card .lbl{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px;margin:14px 0}
table.data{border-collapse:collapse;width:100%;font-size:13px;background:var(--panel);margin:10px 0}
table.data th{background:#0e1b2e;color:#eaf0fa;text-align:left;padding:8px 10px;position:sticky;top:0;font-size:12px;white-space:nowrap}
table.data td{border-bottom:1px solid var(--line);padding:7px 10px;vertical-align:top}
table.data tr:hover td{background:#f0f5ff}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700;color:#fff}
.badge.pass{background:var(--pass)} .badge.cond{background:var(--cond)} .badge.fail{background:var(--fail)} .badge.na{background:var(--na)}
.unverified{color:var(--flag);font-size:12px}
.tag{display:inline-block;background:#e8eefc;color:var(--accent2);border-radius:6px;padding:1px 7px;font-size:11px;font-weight:700;margin-right:4px}
.cand{background:#e7f6ee !important}
code{background:#eef2f8;padding:1px 5px;border-radius:5px;font-size:12.5px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:900px){.sidebar{width:64px}.sidebar nav a,.brand span,.sidefoot{display:none}.brand{font-size:16px}.grid2{grid-template-columns:1fr}}
""")

# ---------------- index ----------------
cands = [g for g in lines["games"] if g["candidate"]]
n_src = len(sources)
body = f"""
<p class="muted">Originate our own NFL lines from official data, run strategies through validation gates, and compete on a skill leaderboard. No manual input — the pipeline (<code>scripts/analyze.py</code> → <code>scripts/build_site.py</code>) rebuilds everything from official sources.</p>
<div class="cards">
  <div class="card"><div class="kpi">2026 W9</div><div class="lbl">Slate (Nov 5–9)</div></div>
  <div class="card"><div class="kpi">{len(lines['games'])}</div><div class="lbl">Games modeled</div></div>
  <div class="card"><div class="kpi">{len(standings['teams'])}</div><div class="lbl">Teams (standings W8)</div></div>
  <div class="card"><div class="kpi">{n_src}</div><div class="lbl">Official sources</div></div>
  <div class="card"><div class="kpi">{len(cands)}</div><div class="lbl">W9 candidates (gates passed)</div></div>
  <div class="card"><div class="kpi">{len(flagged)}</div><div class="lbl"><a href="flagged.html" style="color:inherit">Flagged items</a></div></div>
</div>
<div class="panel"><h3 style="margin-top:0">Week 9 candidates (model vs unverified market — see Model Lines)</h3>
{table(["Game","Kickoff (ET)","Model spread","Model total","Market (unverified)","Edge (pts)","Candidate side","Source"],
 [[f"{g['away']} at {g['home']}", f"{g['date']} {g['kickoff_et']}", g['model_spread_rendered'], g['model_total'],
   (f"<span>{g['home']} {g['market_spread_home']:+.1f}</span> <span class='unverified'>(unverified, F-05)</span>" if g['market_spread_home'] is not None else '<span class="unverified">blank — no official market line</span>'),
   (g['edge_pts'] if g['edge_pts'] is not None else '<span class="unverified">—</span>'),
   (f"<strong>{g['candidate_side']}</strong>" if g['candidate'] else "no trade"),
   link(g['game_url'], "nfl.com game page")] for g in cands]) or '<p class="muted">None this week.</p>'}
</div>
<div class="panel"><h3 style="margin-top:0">Browse by category</h3>
<div class="cards">
  <a class="card" href="executive-summary.html"><div class="lbl">Start here</div><strong>Executive Summary</strong></a>
  <a class="card" href="standings.html"><div class="lbl">Data</div><strong>Standings · Schedule · Scores</strong></a>
  <a class="card" href="team-stats.html"><div class="lbl">Data</div><strong>Team & Player Stats</strong></a>
  <a class="card" href="model-lines.html"><div class="lbl">Lines</div><strong>Model Lines W9 + Prop Signals</strong></a>
  <a class="card" href="strategies.html"><div class="lbl">System</div><strong>Strategies · Gates · Correlations</strong></a>
  <a class="card" href="leaderboard.html"><div class="lbl">Competition</div><strong>Leaderboard</strong></a>
  <a class="card" href="sources.html"><div class="lbl">Trust</div><strong>Sources · <span style="color:var(--flag)">Flagged for Review</span></strong></a>
</div></div>
<div class="panel"><h3 style="margin-top:0">Reading the numbers</h3>
<ul>
<li>Every table row carries a <strong>source link to an official site</strong> (nfl.com / nextgenstats.nfl.com / kansspelautoriteit.nl).</li>
<li>Values that could not be confirmed from an official source are <strong>blank</strong> and listed on <a href="flagged.html">Flagged for Review</a> — never inferred.</li>
<li>Model lines are <strong>computed from official stats</strong>; assumptions (home field 2.5, −110 vig, stake caps) are labeled as assumptions (F-07).</li>
<li>Market spreads/totals are sportsbook numbers, not official — captured ones are third-party and unverified (F-05). Verify at a licensed book; in NL check <a href="https://kansspelautoriteit.nl/kansspelwijzer" target="_blank" rel="noopener">Kansspelwijzer</a>.</li>
</ul></div>
"""
write("index.html", page("Dashboard", body, "index.html", sub=False))

# ---------------- standings ----------------
rows = []
for conf in ("AFC", "NFC"):
    for div in ("East", "North", "South", "West"):
        grp = [t for t in standings["teams"] if t["conf"] == conf and t["div"] == div]
        if not grp:
            continue
        rows.append([f"<strong>{conf} {div}</strong>", "", "", "", "", "", "", "", "", "", "", "", ""])
        for t in grp:
            rows.append([link(team_link(t["abbr"]), f"{t['name']} ({t['abbr']})"), t["W"], t["L"], t["T"], t["PCT"], t["PF"], t["PA"], t["NET"], t["HOME"], t["ROAD"], t["DIV"], t["DIVPCT"], t["CONF"], t["CONFPCT"], t["STRK"], srclink(standings["source_url"])])
body = f"""<p class="muted">{esc(standings['as_of'])} · {esc(standings['columns_note'])} Dataset source: {link(standings['source_url'],'NFL.com Standings')}. Tie-breaking procedure: {link('https://www.nfl.com/standings/tiebreakingprocedures','NFL.com')}</p>
<div class="wrap">{table(["Team","W","L","T","PCT","PF","PA","NET","HOME","ROAD","DIV","DIV%","CONF","CONF%","STRK","Source"], rows)}</div>"""
write("standings.html", page("Standings — 2026 through Week 8", body, "standings.html", sub=True))

# ---------------- schedule ----------------
rows = [[f"{g['away']} at {g['home']}", g["label"] or "—", g["date"], g["day"], g["kickoff_et"], g["network"], g["venue"], link(g["game_url"], "nfl.com game page"), srclink(sched["source_url"])] for g in sched["games"]]
byes = ", ".join(f"{b['abbr']} ({b['record']})" for b in sched["byes"])
body = f"""<p class="muted">{esc(sched['as_of'])} · {esc(sched['times_note'])} Byes: {esc(byes)}. Dataset source: {link(sched['source_url'],'NFL.com Week 9 schedule')}</p>
<div class="wrap">{table(["Matchup","Note","Date","Day","Kickoff (ET)","TV","Venue","Game page","Source"], rows)}</div>"""
write("schedule.html", page("Week 9 Schedule — 2026", body, "schedule.html", sub=True))

# ---------------- scores ----------------
rows = [[f"{g['away']} {g['away_score']} at {g['home']} {g['home_score']}", g["winner"], g["status"], g["date"], g["day"], link(g["game_url"], "nfl.com game page"), srclink(scores["source_url"])] for g in scores["games"]]
byes = ", ".join(f"{b['abbr']} ({b['record']})" for b in scores["byes"])
body = f"""<p class="muted">{esc(scores['as_of'])} · Byes: {esc(byes)}. Dataset source: {link(scores['source_url'],'NFL.com Week 8 scores')}</p>
<div class="wrap">{table(["Final score","Winner","Status","Date","Day","Game page","Source"], rows)}</div>"""
write("scores.html", page("Week 8 Scores — 2026", body, "scores.html", sub=True))

# ---------------- team stats ----------------
def team_table(ds, cols, show):
    rows = [[link(team_link(t["abbr"]), t["abbr"])] + [t.get(c, "") for c in show] + [srclink(ds["source_url"])] for t in ds["teams"]]
    return f"<h3>{esc(ds['dataset'])}</h3><p class='muted'>{esc(ds['columns_note'])}</p><div class='wrap'>{table(['Team'] + show + ['Source'], rows)}</div>"
body = f"""<p class="muted">Season totals through Week 8, as of {esc(tp_off['as_of'])}. Each table's rows link to the official NFL.com stats page (and the team's official page).</p>
{team_table(tp_off, tp_off['columns'], tp_off['columns'])}
{team_table(tr_off, tr_off['columns'], tr_off['columns'])}
{team_table(tp_def, tp_def['columns'], tp_def['columns'])}
{team_table(tr_def, tr_def['columns'], tr_def['columns'])}"""
write("team-stats.html", page("Team Stats — 2026 season", body, "team-stats.html", sub=True))

# ---------------- player stats ----------------
def player_table(ds, show, extra=None):
    rows = []
    for p in ds["players"]:
        row = [link(p["player_url"], p["name"])]
        if extra:
            row.append(esc(p.get("team") or ""))
        row += [p.get(c, "") for c in show]
        row.append(srclink(ds["source_url"]))
        rows.append(row)
    hdr = ["Player"] + (["Team"] if extra else []) + show + ["Source"]
    return f"<h3>{esc(ds['dataset'])}</h3><p class='muted'>{esc(ds['columns_note'])}</p><div class='wrap'>{table(hdr, rows)}</div>"
ngs_rows = [[link(f"https://www.nfl.com/players/{p['name'].lower().replace(' ', '-').replace('.', '').replace(chr(39), '')}/", p["name"]), p["team"], p["TT"], p["CAY"], p["IAY"], p["AYD"], p["AGG%"], p["LCAD"], p["AYTS"], p["ATT"], p["YDS"], p["TD"], p["INT"], p["RATE"], p["COMP%"], p["xCOMP%"], p["CPOE"], srclink(ngs["source_url"])] for p in ngs["players"]]
body = f"""<p class="muted">Season through Week 8 (top 25 rows per category as rendered; NFL.com paginates — flagged F-08). QB team column verified via the Next Gen Stats table, which renders TEAM; blank cells mean "not verified in capture" (F-02) — the player's official page (link in each row) is the source.</p>
{player_table(ppass, ppass['columns'], extra=True)}
{player_table(prush, prush['columns'])}
{player_table(prec, ['REC','YDS','TD','20+','40+','LNG','1ST','1ST%','FUM'])}
{player_table(pint, pint['columns'])}
<h3>{esc(ngs['dataset'])}</h3><p class="muted">{esc(ngs['columns_note'])} Glossary: {link('https://nextgenstats.nfl.com/glossary','Next Gen Stats glossary')}</p>
<div class="wrap">{table(["Player","Team","TT","CAY","IAY","AYD","AGG%","LCAD","AYTS","ATT","YDS","TD","INT","RATE","COMP%","xCOMP%","CPOE (+/-)","Source"], ngs_rows)}</div>"""
write("player-stats.html", page("Player Stats & Next Gen Stats — 2026", body, "player-stats.html", sub=True))

# ---------------- injuries & news ----------------
rows = [[r["game"], r["team"], link(r["player_url"], r["player"]), r["pos"], r["injuries"], r["practice"], badge("PASS" if r["game_status"] == "" else ("FAIL" if r["game_status"] == "Out" else "CONDITIONAL")) + " " + esc(r["game_status"]), srclink(inj["source_url"])] for r in inj["rows"]]
news_html = "".join(f"<li><a href='{esc(n['source_url'])}' target='_blank' rel='noopener'><strong>{esc(n['headline'])}</strong></a> ({esc(n['date'])}) — {esc(n['summary'])} <em>Affects: {esc(n['affects'])}</em></li>" for n in news["items"])
body = f"""<div class="panel"><span class="badge cond">F-04</span> <strong>Week 9 injury report not yet published on NFL.com as of 2026-11-03</strong> (<code>/injuries/league/2026/reg9</code> redirects to Week 8). The latest published official report is Week 8, shown below (players with Out/Questionable status in the captured portion). Re-check {link('https://www.nfl.com/injuries/','NFL.com injury report')} before acting on any Week 9 selection.</div>
<h3>Official news affecting Week 9</h3><ul>{news_html}</ul>
<h3>Latest official injury report — Week 8 (partial capture)</h3>
<p class="muted">{esc(inj['note'])}</p>
<div class="wrap">{table(["Game","Team","Player","Pos","Injuries","Practice status","Game status","Source"], rows)}</div>"""
write("injuries.html", page("Injuries & News", body, "injuries.html", sub=True))

# ---------------- model lines ----------------
rows = []
for g in lines["games"]:
    gates = " ".join(f"{k.split('_')[0]}:{badge(v['status'])}" for k, v in g["gates"].items())
    rows.append([
        f"{g['away']} at {g['home']}", f"{g['date']} {g['kickoff_et']}", f"{g['away_record']} / {g['home_record']}",
        g["proj_away"], g["proj_home"], f"<strong>{g['model_spread_rendered']}</strong>", g["model_total"],
        (f"<span>{g['home']} {g['market_spread_home']:+.1f}</span> <span class='unverified'>(unverified, F-05)</span>" if g["market_spread_home"] is not None else '<span class="unverified">blank</span>'),
        (g["edge_pts"] if g["edge_pts"] is not None else '<span class="unverified">—</span>'),
        (f"<strong>{g['candidate_side']}</strong>" if g["candidate"] else "no trade"),
        gates, link(g["game_url"], "game page"),
    ])
body = f"""<p class="muted">Method: {esc(lines['method'])}</p>
<div class="panel"><strong>Legend:</strong> {badge('PASS')} gate passed · {badge('CONDITIONAL')} passed with note (e.g., W9 injury report pending, F-04) · {badge('FAIL')}/{badge('NOT_COMPUTABLE')} gate not met — no trade. Market column: third-party aggregator values attributed to FanDuel, time-stamped 2026-11-03 11:31 AM ET — <strong>unverified</strong> (F-05); verify at a licensed sportsbook (NL: <a href="https://kansspelautoriteit.nl/kansspelwijzer" target="_blank" rel="noopener">Kansspelwijzer</a>). League avg pass YDS allowed/game: {lines['league_avg_def_pass_ypg']} · rush: {lines['league_avg_def_rush_ypg']} (computed from official data).</div>
<div class="wrap">{table(["Game","Kickoff (ET)","Records (away/home)","Proj away","Proj home","Model spread","Model total","Market spread (home)","Edge (pts)","Candidate","Gates G1–G7","Source"], rows)}</div>
<h3>Gate details</h3>
<div class="wrap">{table(["Game","Gate","Status","Detail"],
 [[f"{g['away']} at {g['home']}", k, badge(v['status']), esc(v['detail'])] for g in lines["games"] for k, v in g["gates"].items()])}</div>"""
write("model-lines.html", page("Model Lines — Week 9 (originated from official data)", body, "model-lines.html", sub=True))

# ---------------- prop signals ----------------
rows = [[p["game"], p["side"], p["team"], (esc(p["qb"]) if p["qb"] else '<span class="unverified">—</span>'),
         (p["qb_season_ypg"] if p["qb_season_ypg"] is not None else '<span class="unverified">—</span>'),
         (p["qb_proj_pass_yds"] if p["qb_proj_pass_yds"] is not None else '<span class="unverified">—</span>'),
         p["team_rush_proj_yds"], p["team_pass_proj_yds"], p["opp_pass_def_ypg_allowed"], p["opp_rush_def_ypg_allowed"],
         '<span class="unverified">blank — no official market line (F-05)</span>', link(p["source_url"], "game page")] for p in props["signals"]]
body = f"""<p class="muted">Method: {esc(props['method'])}</p>
<div class="wrap">{table(["Game","Side","Team","QB","QB season YPG","QB proj pass YDS","Team rush proj YDS","Team pass proj YDS","Opp pass def YPG allowed","Opp rush def YPG allowed","Market prop line","Source"], rows)}</div>
<p class="muted">Individual RB/WR allocation requires the official depth chart (player team affiliations are not rendered on the leaders page — F-02), so only team-level projections are published. Prop market lines are blank by rule: they are sportsbook-specific and not an official source.</p>"""
write("prop-signals.html", page("Player Prop Signals — Week 9", body, "prop-signals.html", sub=True))

# ---------------- strategies ----------------
cards = []
for s in strats:
    gates = " ".join(f'<span class="tag">{esc(g)}</span>' for g in s.get("gates", []))
    extra = ""
    if "candidates" in s: extra += f"<p><strong>{s['candidates']}</strong> of {s['games_evaluated']} games are candidates this week.</p>"
    if "signals" in s: extra += f"<p><strong>{s['signals']}</strong> signals computed.</p>"
    if "same_game_proxy_r" in s: extra += f"<p>Same-game proxy r(passYDSpg, PFpg) = <strong>{s['same_game_proxy_r']}</strong>; threshold {s['correlation_threshold']}.</p>"
    cards.append(f"""<div class="panel"><h3 style="margin-top:0">{esc(s['id'])} — {esc(s['name'])} <span class="tag">{esc(s['type'])}</span></h3>
    <p>{esc(s['description'])}</p>{extra}<p class="muted">Status: {esc(s['status'])} · Gates: {gates}</p></div>""")
body = f"""<p class="muted">Bet shapes: singles, player props, parlays. Every strategy must pass the <a href="validation-gates.html">validation gates</a>; multi-leg bets must satisfy the <a href="correlations.html">correlation policy</a>. As of 2026-11-03.</p>
{''.join(cards)}"""
write("strategies.html", page("Strategy Catalog", body, "strategies.html", sub=True))

# ---------------- correlations ----------------
rows = [[c["pair"], c["type"], c["n"], f"{c['r']:+.4f}", esc(c["interpretation"]), link("https://www.nfl.com/stats/team-stats/", "nfl.com team stats"), link("https://www.nfl.com/standings/", "nfl.com standings")] for c in corr["correlations"]]
body = f"""<p class="muted">{esc(corr['method'])}</p>
<div class="wrap">{table(["Pair","Statistic","n","r","Interpretation","Source 1","Source 2"], rows)}</div>
<h3>Enforcement rules</h3>
""" + md((RES / "correlation-policy.md").read_text().split("## Computed values", 1)[1].replace("## Rules", "", 1)) if False else f"""<p class="muted">{esc(corr['method'])}</p>
<div class="wrap">{table(["Pair","Statistic","n","r","Interpretation","Source 1","Source 2"], rows)}</div>
<h3>Enforcement rules</h3>
{md((RES / 'correlation-policy.md').read_text().split('## Rules', 1)[1])}"""
write("correlations.html", page("Correlation Analysis (computed from official data)", body, "correlations.html", sub=True))

# ---------------- leaderboard ----------------
rows = [[b["rank"], b["strategy_id"], esc(b["name"]), esc(b["type"]),
         (b["week9_projected_edge_pts"] if b["week9_projected_edge_pts"] is not None else '<span class="unverified">—</span>'),
         b["realized_pts"], esc(b["status"]), link("leaderboard.html", "this page")] for b in board["standings"]]
body = f"""<p class="muted">{esc(board['note'])}</p>
<p><strong>Scoring:</strong> {esc(board['scoring'])}</p>
<p><strong>Tiers:</strong> 🥇 Gold {esc(board['tiers']['gold'])} · 🥈 Silver {esc(board['tiers']['silver'])} · 🥉 Bronze {esc(board['tiers']['bronze'])}</p>
<div class="wrap">{table(["Rank","ID","Strategy","Type","W9 projected edge (pts)","Realized pts","Status","Source"], rows)}</div>
<h3>Full rules</h3>
{md((RES / 'leaderboard-rules.md').read_text())}"""
write("leaderboard.html", page("Leaderboard Competition", body, "leaderboard.html", sub=True))

# ---------------- sources ----------------
rows = [[s["id"], esc(s["label"]), link(s["url"], s["url"]), badge("PASS") + " official" if s["official"] else badge("CONDITIONAL"), esc(s["used_for"])] for s in sources]
body = f"""<p class="muted">{esc('Captured 2026-11-03 by session 95e9626f. Only official NFL / official regulator domains are used as sources for verified values. Third-party aggregator values are recorded only in data/market-lines.json and flagged (F-05), never as verified sources.')}</p>
<div class="wrap">{table(["ID","Source","Link","Status","Used for"], rows)}</div>"""
write("sources.html", page("Source Registry (official sources)", body, "sources.html", sub=True))

# ---------------- flagged ----------------
rows = [[f["id"], badge("FAIL") if f["severity"] == "high" else (badge("CONDITIONAL") if f["severity"] == "medium" else badge("PASS")), esc(f["severity"]), esc(f["item"]), link(f["source_url"], f["source_url"]) if f["source_url"] else '<span class="unverified">— no external source (internal assumption)</span>'] for f in flagged]
body = f"""<p class="muted">{esc(flagged and load(DATA / 'flagged.json')['note'])}</p>
<div class="panel" style="border-left:4px solid var(--flag)"><strong>These items do not block the site or any strategy.</strong> They are published here so they can be reviewed after the site is live. Rule: if a value cannot be confirmed from an official source, it is left blank and flagged — never inferred or filled in.</div>
<div class="wrap">{table(["ID","Severity badge","Severity","Item","Source link"], rows)}</div>"""
write("flagged.html", page("⚑ Flagged for Review (unverified / irregularities)", body, "flagged.html", sub=True))

# ---------------- markdown pages ----------------
md_page("executive-summary.md", "Executive Summary", "executive-summary.html")
md_page("methodology.md", "Methodology", "methodology.html")
md_page("validation-gates.md", "Validation Gates", "validation-gates.html")
md_page("responsible-gambling.md", "Responsible Gambling & Legal Notes", "responsible-gambling.html")

print("site build complete -> repo root + pages/")
