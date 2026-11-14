"""Build the a57af0ab review hub (static HTML) from JSON data. Stdlib only.

Inputs : a57af0ab/data/injuries-2026-w10.json  (written by parse_injuries.py)
         a57af0ab/data/content.json            (questions, suggestions, repo review, flags)
Outputs: a57af0ab/index.html and subpages, a57af0ab/assets/*
"""
import html
import json
import pathlib
import collections

HERE = pathlib.Path(__file__).resolve().parent
INJ = json.loads((HERE / "data" / "injuries-2026-w10.json").read_text(encoding="utf-8"))
CON = json.loads((HERE / "data" / "content.json").read_text(encoding="utf-8"))
E = html.escape

NAV = [
    ("index.html", "Home"),
    ("executive-summary.html", "Executive summary"),
    ("injuries.html", "Week 10 injuries"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "Flagged for Review"),
]


def link(url, label=None, cls=""):
    lab = label or url
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{E(url, quote=True)}" target="_blank" rel="noopener noreferrer">{E(lab)}</a>'


def layout(title, body, active):
    parts = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        parts.append('<a href="' + href + '"' + cur + '>' + E(label) + '</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} · NFL Review Hub</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="brand"><a href="index.html">NFL Review Hub</a> <span class="pill">Data as of {E(CON['as_of'])}</span></div>
    <nav>{nav}</nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap foot">
  <p>Official sources only. A blank cell means the value could not be confirmed from an official source and is flagged. Nothing here is a betting recommendation.
  Repo: {link("https://github.com/sassnarep3-star/Own8", "sassnarep3-star/Own8")} · Coordination board: {link("https://github.com/sassnarep3-star/Own8/blob/main/COORDINATION.md", "COORDINATION.md")}</p>
</footer>
<script src="assets/app.js"></script>
</body>
</html>
"""


def table(headers, rows, cls="data", filter_id=None):
    head = "".join(f"<th>{E(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    fid = f' data-filter="{filter_id}"' if filter_id else ""
    return f'<div class="tablewrap"><table class="{cls}"{fid}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def cell_text(v):
    return E(v) if v else '<span class="blank">blank · unverified</span>'


# ---------- derived numbers (computed from the transcription, not typed) ----------
rows = INJ["rows"]
status_counts = collections.Counter(r["game_status"] or "" for r in rows)
practice_counts = collections.Counter(r["practice_status"] for r in rows)
flag_counts = collections.Counter(f for r in rows for f in r["flags"])
teams = INJ["teams"]
team_rows = []
for t in teams:
    out = sum(t["groups"][g]["out"] for g in t["groups"])
    doubt = sum(t["groups"][g]["doubtful"] for g in t["groups"])
    quest = sum(t["groups"][g]["questionable"] for g in t["groups"])
    dnp = sum(t["groups"][g]["dnp"] for g in t["groups"])
    team_rows.append({**t, "out": out, "doubtful": doubt, "questionable": quest, "dnp": dnp,
                      "absent": out + doubt})
ranked = sorted(team_rows, key=lambda t: (-t["absent"], -t["out"], t["team"]))
flagged_teams = [t for t in team_rows if t["position_group_flags"]]
total_out = status_counts["Out"]
total_doubt = status_counts["Doubtful"]
total_quest = status_counts["Questionable"]
total_blank = status_counts[""]
n_games = len(INJ["games"])
n_rows = len(rows)
n_teams = len(teams)
byes = ", ".join(INJ["teams_on_bye_per_schedule"])
assert (n_games, n_teams, n_rows) == (14, 28, 345), (n_games, n_teams, n_rows)
assert (total_out, total_doubt, total_quest, total_blank) == (66, 10, 84, 185)
rep = INJ["source_report"]
sched = INJ["source_schedule"]

PAGES = {}

# ---------- landing ----------
cards = [
    ("executive-summary.html", "Executive summary", "What the verified data shows, what is missing, and what needs a decision."),
    ("injuries.html", "Week 10 injury tracker", f"{n_rows} official report rows across {n_games} games. Position-group counts per team. Starter and backup status left blank until verified."),
    ("questions.html", "Questions & information gaps", f"{len(CON['questions'])} questions: what we have, what is missing, and how to find it. Plus {len(CON['decisions'])} decisions for you."),
    ("suggestions.html", "Suggestions (choose a path)", f"{len(CON['suggestions'])} proposed changes. Nothing is implemented until you pick one."),
    ("repo-review.html", "Repo review", f"{len(CON['repo_review'])} checked items: irregularities, stale data, non-official sources, and clean checks."),
    ("flagged.html", "Flagged for Review", f"{len(CON['flagged'])} items with source links. They do not block publication."),
]
card_html = "".join(
    f'<a class="card" href="{href}"><h3>{E(t)}</h3><p>{E(d)}</p><span class="go">Open →</span></a>'
    for href, t, d in cards
)
other = [
    ("origination/index.html", "Line origination (walk-forward ratings, validation gates)"),
    ("strict/site/index.html", "Strict evidence site (strategies blocked pending validation)"),
    ("desk/index.html", "Independent NFL desk (blocked strategies, official-source checks)"),
    ("evidence-lab/README.md", "Evidence lab (official Big Data Bowl sources, no eligible strategy)"),
    ("verification/README.md", "Verification QA report"),
    ("audit/index.html", "Audit of the earlier live dashboard"),
]
other_html = "".join(f'<li>{link("https://github.com/sassnarep3-star/Own8/blob/main/" + p, p)} — {E(d)}</li>' for p, d in other)
body = f"""
<section class="hero">
  <h1>NFL review hub</h1>
  <p class="lede">A plain-language dashboard for the NFL project. It collects the official facts, shows what is missing, and lists the choices that come next. Every table row links to an official source. Where a value cannot be confirmed, the cell is blank and the item is flagged.</p>
  <div class="kpis">
    <div><b>{n_games}</b><span>games on the Week 10 report</span></div>
    <div><b>{total_out}</b><span>players listed Out</span></div>
    <div><b>{total_doubt}</b><span>listed Doubtful</span></div>
    <div><b>{total_quest}</b><span>listed Questionable</span></div>
    <div><b>0</b><span>starter / backup labels verified</span></div>
  </div>
</section>
<section class="cards">{card_html}</section>
<section>
  <h2>Other work in this repo (linked, not re-run here)</h2>
  <p>These areas belong to other sessions. This hub links to them and does not change them.</p>
  <ul class="plain">{other_html}</ul>
</section>
"""
PAGES["index.html"] = layout("Home", body, "index.html")

# ---------- executive summary ----------
kpi_rows = [
    [E("Official games on Week 10 injury report"), E(str(n_games)), link(rep)],
    [E("Teams on the report (byes per schedule: " + byes + ")"), E(str(n_teams)), link(sched)],
    [E("Report rows transcribed"), E(str(n_rows)), link(rep)],
    [E("Rows listed Out"), E(str(total_out)), link(rep)],
    [E("Rows listed Doubtful"), E(str(total_doubt)), link(rep)],
    [E("Rows listed Questionable"), E(str(total_quest)), link(rep)],
    [E("Rows with Did Not Participate in Practice"), E(str(practice_counts["Did Not Participate In Practice"])), link(rep)],
    [E("Rows with a blank game status on the report"), E(str(total_blank)), link(rep)],
    [E("Starter / backup labels verified"), '<span class="blank">0 · blank · unverified</span>', link("https://www.nfl.com/teams/new-york-giants/depth-chart", "Giants depth-chart URL (404)")],
    [E("Verified betting lines"), '<span class="blank">0 · blank · unverified</span>', link("https://www.nfl.com/", "nfl.com (no line source)")],
]
top_rows = [
    [E(t["team"]), E(str(t["out"])), E(str(t["doubtful"])), E(str(t["questionable"])), E(str(t["dnp"])),
     link(rep, "report")]
    for t in ranked[:8]
]
flag_rows = [
    [E(t["team"]), E("; ".join(t["position_group_flags"])), link(rep, "report")]
    for t in flagged_teams
]
ex_body = f"""
<h1>Executive summary</h1>
<p class="meta">{E(CON['as_of_note'])}</p>

<section class="callout">
<h2>Bottom line</h2>
<ul>
<li><b>The Week 10 injury picture is captured from the official report.</b> {n_rows} rows, {n_games} games, {n_teams} teams. Thursday's game (Commanders 24, Giants 21) is final on the official schedule; the other 13 games are still to be played.</li>
<li><b>Starter and backup exposure cannot be verified yet.</b> No official depth chart was found. The tracker shows counts by position group instead and leaves starter and backup labels blank.</li>
<li><b>The repo's standings are stale.</b> The root file is one completed week behind the official Week 10 schedule page for all 8 teams checked (Repo review R04).</li>
<li><b>No strategy can be promoted from this hub.</b> Market prices are not verified, bet-leg correlations are not computed, and the other namespaces record no strategy as passing its gates.</li>
<li><b>Decisions needed before more work:</b> market-data source (D1), scope (D2), refresh cadence (D3), and how to treat 'Not injury related' rows (D4). See Suggestions and Questions.</li>
</ul>
</section>

<h2>Key figures (each links to its source)</h2>
{table(["Metric", "Value", "Source"], kpi_rows)}

<h2>Teams with the most players listed Out or Doubtful</h2>
<p>Ranked by Out plus Doubtful, as printed on the report. This is a count, not a judgement of depth. Starter status is unknown.</p>
{table(["Team", "Out", "Doubtful", "Questionable", "Did not practice", "Source"], top_rows)}

<h2>Position groups with two or more Out or Doubtful</h2>
<p>Group labels are this project's own (see the injury tracker). Each flag means two or more listed players, not a confirmed starter loss.</p>
{table(["Team", "Flag (starter status unverified)", "Source"], flag_rows) if flag_rows else "<p>None.</p>"}

<h2>What this session did not do</h2>
<ul>
<li>It did not re-run line origination, correlation, or strategy validation. Those are in other namespaces (linked on the home page).</li>
<li>It did not fetch Week 9 scores or refresh the repo's standings.</li>
<li>It did not verify starters, backups, snap counts, or any betting line.</li>
<li>It did not set up any automatic or scheduled capture.</li>
</ul>
<p>Method: the injury rows were copied once from the official page text, checked for structure, team and game membership, and per-game counts by script. A second independent transcription has not been done (flag X-04).</p>
"""
PAGES["executive-summary.html"] = layout("Executive summary", ex_body, "executive-summary.html")

# ---------- injuries ----------
game_rows = []
for g in INJ["games"]:
    game_rows.append([
        E(g["game_slug"].replace("-", " ")),
        E(g["day_time_as_printed"]),
        E(g["network_as_printed"]),
        E(f'{g["first_listed_team"]} / {g["second_listed_team"]}'),
        E(str(g["rows"])),
        link(g["game_page_url"], "game"),
    ])
team_table_rows = []
for t in ranked:
    flags = "; ".join(t["position_group_flags"]) or ""
    team_table_rows.append([
        E(t["team"]), E(str(t["rows"])), E(str(t["out"])), E(str(t["doubtful"])), E(str(t["questionable"])),
        E(str(t["dnp"])), E(flags) if flags else '<span class="muted">none</span>',
        '<span class="blank">blank · unverified</span>', link(rep, "report"),
    ])
row_rows = []
for r in rows:
    flags = ", ".join(r["flags"]) if r["flags"] else ""
    row_rows.append([
        E(r["id"]), E(r["team"]), E(r["player"]), E(r["position"]), E(r["position_group"]),
        E(r["injuries"]) if r["injuries"] else '<span class="muted">none listed</span>',
        E(r["practice_status"]) if r["practice_status"] else '<span class="blank">blank</span>',
        E(r["game_status"]) if r["game_status"] else '<span class="blank">blank on report</span>',
        E(flags) if flags else '',
        link(r["source_urls"][0], "report") + " · " + link(r["source_urls"][1], "game"),
    ])
inj_body = f"""
<h1>Week 10 injury tracker (2026)</h1>
<p class="meta">Source: {link(rep, "official NFL Week 10 injury report")} · schedule: {link(sched, "official Week 10 schedule")} · captured {E(INJ['captured_utc_date'])}</p>
<div class="notice"><b>Starter and backup status: blank.</b> {E(INJ['starter_backup_status'])} Position-group counts are shown instead. Report publish time: {E(INJ['report_publish_time'])}.</div>

<h2>Games on the report ({n_games})</h2>
<p>Team order follows the official report, which matches the away team in each 'X at Y' schedule slug. Byes: {E(byes)}.</p>
{table(["Game (slug)", "Day and time (as printed)", "Network (as printed)", "Teams (as listed)", "Rows", "Source"], game_rows)}

<h2>Teams ({n_teams}): counts by status and position-group flags</h2>
<p>Out, Doubtful and Questionable are counted from the game-status column. 'Did not practice' counts the practice-status column. A flag means two or more Out or Doubtful players in one group.</p>
<div class="filterbar"><input type="search" placeholder="Filter teams…" data-target="teams-table" aria-label="Filter teams"></div>
{table(["Team", "Rows", "Out", "Doubtful", "Questionable", "Did not practice", "Group flags (starter status unverified)", "Starter / backup", "Source"], team_table_rows, filter_id="teams-table")}

<h2>All report rows ({n_rows})</h2>
<p>Each row is copied from the report. Blank cells stay blank. Flags are added by this project and are explained on the Flagged for Review page.</p>
<div class="filterbar"><input type="search" placeholder="Filter by team, player, injury, status…" data-target="rows-table" aria-label="Filter rows"></div>
{table(["ID", "Team", "Player", "Pos", "Group", "Injury (as printed)", "Practice status", "Game status", "Flags", "Source"], row_rows, filter_id="rows-table")}
"""
PAGES["injuries.html"] = layout("Week 10 injuries", inj_body, "injuries.html")

# ---------- questions ----------
q_rows = []
for q in CON["questions"]:
    srcs = "<br>".join(link(l["url"], l["label"]) for l in q["links"])
    q_rows.append([
        E(q["id"]), E(q["question"]), E(q["status"]), E(q["have"]), E(q["missing"]), E(q["discover"]), srcs,
    ])
d_rows = [[E(d["id"]), E(d["question"]), "<br>".join(link(l["url"], l["label"]) for l in d["links"])] for d in CON["decisions"]]
q_body = f"""
<h1>Questions and information gaps</h1>
<p class="meta">Each row says what we have, what is missing, and how to find it. Status words: MISSING, PARTLY ANSWERED, STALE, DECISION NEEDED, or ANSWERED BY OTHER NAMESPACES.</p>
<div class="filterbar"><input type="search" placeholder="Filter questions…" data-target="q-table" aria-label="Filter questions"></div>
{table(["ID", "Question", "Status", "What we have", "What is missing", "How to find it", "Official sources"], q_rows, filter_id="q-table")}
<h2>Decisions only you can make</h2>
<p>These decisions control what the project may do next. Nothing is implemented until you choose.</p>
{table(["ID", "Decision", "Reference"], d_rows)}
"""
PAGES["questions.html"] = layout("Questions", q_body, "questions.html")

# ---------- suggestions ----------
s_rows = []
for s in CON["suggestions"]:
    srcs = "<br>".join(link(l["url"], l["label"]) for l in s["links"])
    s_rows.append([E(s["id"]), E(s["suggestion"]), E(s["addresses"]), E(s["effort"]), E(s["decision"]), srcs])
s_body = f"""
<h1>Suggestions: choose a path</h1>
<div class="notice"><b>Nothing here has been implemented.</b> Each suggestion lists the gap it addresses and a reference. Choose by ID. Efforts are rough estimates from this session, not measured costs.</div>
<div class="filterbar"><input type="search" placeholder="Filter suggestions…" data-target="s-table" aria-label="Filter suggestions"></div>
{table(["ID", "Suggestion", "Addresses", "Effort (estimate)", "Decision", "Reference"], s_rows, filter_id="s-table")}
"""
PAGES["suggestions.html"] = layout("Suggestions", s_body, "suggestions.html")

# ---------- repo review ----------
r_rows = [[E(r["id"]), E(r["area"]), E(r["irregularity"]), E(r["severity"]), E(r["status"]), link(r["evidence"], "evidence")] for r in CON["repo_review"]]
r_body = f"""
<h1>Repo review</h1>
<p class="meta">Checked against the git tree on branch <code>arena/a57af0ab-own8</code> and the default branch. Repo facts are checked with git, not with outside sites. NFL facts are linked to nfl.com.</p>
<div class="filterbar"><input type="search" placeholder="Filter repo items…" data-target="r-table" aria-label="Filter repo items"></div>
{table(["ID", "Area", "Irregularity", "Severity", "Status", "Evidence"], r_rows, filter_id="r-table")}
"""
PAGES["repo-review.html"] = layout("Repo review", r_body, "repo-review.html")

# ---------- flagged ----------
f_rows = [[E(f["id"]), E(f["severity"]), E(f["item"]), link(f["source"], "source"), E(f["status"])] for f in CON["flagged"]]
fl_body = f"""
<h1>Flagged for Review</h1>
<p class="meta">Items that need a human check. They do not block publication. Each one links to its source.</p>
{table(["ID", "Severity", "Item", "Source", "Status"], f_rows)}
"""
PAGES["flagged.html"] = layout("Flagged for Review", fl_body, "flagged.html")

for name, content in PAGES.items():
    (HERE / name).write_text(content, encoding="utf-8")
print("built", ", ".join(PAGES))
