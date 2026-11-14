#!/usr/bin/env python3
"""Build the Week 10 official injury + position-group deficiency tracker (session d6bada32).

Inputs : injury-depth/data/w10_transcription.tsv  (hand transcription of the official NFL.com
         Week 10 injury report, 8 chunks read 2026-11-14; only rows with an injury entry, a
         non-"Full Participation" practice status, or a game status are kept)
Outputs: injury-depth/data/w10-rows.json, injury-depth/data/w10-team-summary.json,
         injury-depth/index.html
Stdlib only.  Run:  python3 injury-depth/build.py
"""
import csv, html, json, os, re
from collections import defaultdict, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "data", "w10_transcription.tsv")
REPORT_URL = "https://www.nfl.com/injuries/league/2026/reg10"
REPORT_INDEX_URL = "https://www.nfl.com/injuries/"
SCORES_W10 = "https://www.nfl.com/scores/2026/week-10"
SCORES_W9 = "https://www.nfl.com/scores/2026/week-9"
PLAYER_BASE = "https://www.nfl.com/players/"
CAPTURED = "2026-11-14 (UTC, read between 00:50 and 01:15)"

# Games in the order they appear on the report. Away team is listed first (nfl.com convention,
# confirmed by game slugs such as commanders-at-giants-2026-reg-10 on the Week 10 scores page).
GAMES = OrderedDict([
    ("G01", dict(away="WAS", home="NYG", when="Thu Nov 12, 8:15 PM EST", net="Prime Video",
                 status="Final on nfl.com scores page: WAS 24, NYG 21", status_url=SCORES_W10)),
    ("G02", dict(away="NE", home="DET", when="Sun Nov 15, 9:30 AM EST", net="FOX, FOX Deportes",
                 status="Not yet played at capture (kickoff Sun Nov 15)", status_url=SCORES_W10)),
    ("G03", dict(away="KC", home="ATL", when="Sun Nov 15, 1:00 PM EST", net="CBS",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G04", dict(away="MIN", home="GB", when="Sun Nov 15, 1:00 PM EST", net="FOX",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G05", dict(away="JAX", home="TEN", when="Sun Nov 15, 1:00 PM EST", net="FOX",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G06", dict(away="BUF", home="NYJ", when="Sun Nov 15, 1:00 PM EST", net="CBS",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G07", dict(away="MIA", home="IND", when="Sun Nov 15, 1:00 PM EST", net="CBS",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G08", dict(away="CAR", home="NO", when="Sun Nov 15, 1:00 PM EST", net="FOX",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G09", dict(away="HOU", home="CLE", when="Sun Nov 15, 1:00 PM EST", net="FOX",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G10", dict(away="LAR", home="ARI", when="Sun Nov 15, 4:05 PM EST", net="CBS",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G11", dict(away="SEA", home="LV", when="Sun Nov 15, 4:05 PM EST", net="CBS",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G12", dict(away="SF", home="DAL", when="Sun Nov 15, 4:25 PM EST", net="FOX, FOX Deportes",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G13", dict(away="PIT", home="CIN", when="Sun Nov 15, 8:20 PM EST", net="NBC, Universo",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
    ("G14", dict(away="LAC", home="BAL", when="Mon Nov 16, 8:15 PM EST", net="ESPN, ABC, ESPN2, ESPN Deportes",
                 status="Not yet played at capture (kickoff Sun Nov 15 or Mon Nov 16)", status_url=SCORES_W10)),
])

# Position groups for the deficiency tracker (position codes exactly as printed on the report).
GROUP_OF = {"QB": "QB", "RB": "RB/FB", "FB": "RB/FB", "WR": "WR", "TE": "TE",
            "T": "OL", "G": "OL", "C": "OL", "DE": "DL", "DT": "DL", "LB": "LB",
            "CB": "CB", "S": "S", "K": "ST", "P": "ST", "LS": "ST"}
GROUP_ORDER = ["QB", "RB/FB", "WR", "TE", "OL", "DL", "LB", "CB", "S", "ST"]

ALLOWED_FIELDS = 8
rows = []
errors = []
with open(TSV, encoding="utf-8") as fh:
    reader = csv.reader((ln for ln in fh if not ln.startswith("#")), delimiter="\t")
    for n, rec in enumerate(reader, start=1):
        if not rec:
            continue
        if len(rec) != ALLOWED_FIELDS:
            errors.append(f"line {n}: expected {ALLOWED_FIELDS} fields, got {len(rec)}")
            continue
        gid, team, player, pos, injury, practice, gstatus, slug = [x.strip() for x in rec]
        if gid not in GAMES:
            errors.append(f"line {n}: unknown game {gid}")
        if team not in (GAMES[gid]["away"], GAMES[gid]["home"]):
            errors.append(f"line {n}: team {team} not in {gid}")
        if pos not in GROUP_OF:
            errors.append(f"line {n}: unknown position {pos}")
        if not slug or " " in slug:
            errors.append(f"line {n}: bad slug {slug!r}")
        if gstatus not in ("", "Out", "Doubtful", "Questionable"):
            errors.append(f"line {n}: bad game status {gstatus!r}")
        if practice and practice not in ("Full Participation in Practice", "Limited Participation in Practice",
                                         "Did Not Participate In Practice"):
            errors.append(f"line {n}: bad practice status {practice!r}")
        if not (injury or gstatus or practice != "Full Participation in Practice"):
            errors.append(f"line {n}: row has no injury/status and full practice - should not be transcribed")
        rows.append(OrderedDict([
            ("row_id", f"W10-{len(rows)+1:03d}"),
            ("game_id", gid), ("game", f"{GAMES[gid]['away']} at {GAMES[gid]['home']}"),
            ("team", team), ("player", player), ("position", pos),
            ("position_group", GROUP_OF.get(pos, "")),
            ("injuries_as_listed", injury), ("practice_status", practice), ("game_status", gstatus),
            ("player_url", PLAYER_BASE + slug + "/"),
            ("report_url", REPORT_URL),
            ("replacement_2nd_3rd_string", None),   # blank by design: no official depth chart reachable
            ("replacement_status", "UNVERIFIED - no official depth-chart source"),
        ]))

# Validation: duplicates and every game has both teams represented or is a documented gap.
seen = set()
for r in rows:
    key = (r["team"], r["player"])
    if key in seen:
        errors.append(f"duplicate row {key}")
    seen.add(key)
if errors:
    raise SystemExit("VALIDATION FAILED:\n" + "\n".join(errors))

# Team summary and deficiency view (official listing only).
team_games = {}
for gid, g in GAMES.items():
    team_games[g["away"]] = (gid, g["away"], g["home"])
    team_games[g["home"]] = (gid, g["away"], g["home"])

summary = OrderedDict()
for t in sorted(team_games):
    gid, a, h = team_games[t]
    trs = [r for r in rows if r["team"] == t]
    out = sum(1 for r in trs if r["game_status"] == "Out")
    doubt = sum(1 for r in trs if r["game_status"] == "Doubtful")
    quest = sum(1 for r in trs if r["game_status"] == "Questionable")
    dnp = sum(1 for r in trs if r["practice_status"].startswith("Did Not"))
    groups = OrderedDict((grp, []) for grp in GROUP_ORDER)
    for r in trs:
        if r["game_status"] in ("Out", "Doubtful"):
            groups[r["position_group"]].append(f"{r['player']} ({r['position']}, {r['game_status']})")
    summary[t] = OrderedDict([
        ("team", t), ("game_id", gid), ("game", f"{a} at {h}"), ("listed_rows", len(trs)),
        ("out", out), ("doubtful", doubt), ("questionable", quest), ("did_not_practice", dnp),
        ("out_or_doubtful_by_group", {k: v for k, v in groups.items() if v}),
        ("starter_backup_replacements", None),
        ("replacement_status", "UNVERIFIED - no official depth-chart source"),
        ("source_url", REPORT_URL),
    ])

os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
with open(os.path.join(HERE, "data", "w10-rows.json"), "w", encoding="utf-8") as fh:
    json.dump({"dataset": "nfl-injury-report-2026-week10-transcribed-subset", "captured": CAPTURED,
               "source_url": REPORT_URL, "source_index": REPORT_INDEX_URL,
               "scope": "Rows with an injury entry, a non-Full practice status, or a game status. "
                        "Full-participation players with no injury/status are omitted by design.",
               "row_count": len(rows), "rows": rows}, fh, indent=2, ensure_ascii=False)
with open(os.path.join(HERE, "data", "w10-team-summary.json"), "w", encoding="utf-8") as fh:
    json.dump({"dataset": "w10-position-group-exposure", "captured": CAPTURED, "source_url": REPORT_URL,
               "method": "Counts of Out / Doubtful / Questionable by team, from the official report. "
                         "Starter-vs-backup replacement is NOT computed: no official depth chart was reachable.",
               "teams": list(summary.values())}, fh, indent=2, ensure_ascii=False)

# ---------- HTML ----------
def esc(s):
    return html.escape("" if s is None else str(s), quote=True)

def badge(text, kind):
    return f'<span class="badge b-{kind}">{esc(text)}</span>'

status_kind = {"Out": "bad", "Doubtful": "warn", "Questionable": "info", "": "ok"}
total_out = sum(1 for r in rows if r["game_status"] == "Out")
total_doubt = sum(1 for r in rows if r["game_status"] == "Doubtful")
total_q = sum(1 for r in rows if r["game_status"] == "Questionable")
total_dnp = sum(1 for r in rows if r["practice_status"].startswith("Did Not"))
n_games = len(GAMES)

team_rows_html = []
for t, s in summary.items():
    grp_txt = "; ".join(f"{k}: {len(v)}" for k, v in s["out_or_doubtful_by_group"].items()) or "none"
    team_rows_html.append(
        "<tr>"
        f"<td>{esc(t)}</td><td>{esc(s['game'])}</td><td>{s['out']}</td><td>{s['doubtful']}</td>"
        f"<td>{s['questionable']}</td><td>{s['did_not_practice']}</td>"
        f"<td>{esc(grp_txt)}</td>"
        '<td class="unverified" title="Replacement order not verifiable from official sources">'
        f'{badge("UNVERIFIED", "flag")}</td>'
        f'<td><a href="{REPORT_URL}">NFL.com Week 10 injury report</a></td>'
        "</tr>")

game_rows_html = []
for gid, g in GAMES.items():
    n_rows = sum(1 for r in rows if r["game_id"] == gid)
    game_rows_html.append(
        "<tr>"
        f"<td>{esc(gid)}</td><td>{esc(g['away'])} at {esc(g['home'])}</td><td>{esc(g['when'])}</td>"
        f"<td>{esc(g['net'])}</td><td>{n_rows}</td><td>{esc(g['status'])}</td>"
        f'<td><a href="{g["status_url"]}">NFL.com scores (Week 10)</a></td></tr>')

detail_html = []
for r in rows:
    gs = r["game_status"]
    gbadge = badge(gs, status_kind.get(gs, "info")) if gs else ""
    pr = r["practice_status"]
    detail_html.append(
        "<tr>"
        f"<td>{esc(r['game'])}</td><td>{esc(r['team'])}</td>"
        f'<td><a href="{esc(r["player_url"])}">{esc(r["player"])}</a></td>'
        f"<td>{esc(r['position'])}</td><td>{esc(r['position_group'])}</td>"
        f"<td>{esc(r['injuries_as_listed'])}</td><td>{esc(pr)}</td><td>{gbadge}</td>"
        '<td class="unverified">' + badge("UNVERIFIED", "flag") + "</td>"
        f'<td><a href="{REPORT_URL}">report</a></td></tr>')

NAV = [("Hub", "../advisory/index.html"), ("Suggestions", "../advisory/suggestions.html"),
       ("Questions & gaps", "../advisory/questions.html"), ("Flagged for Review", "../advisory/flagged.html"),
       ("Sources", "../advisory/sources.html"), ("Week 10 injuries", "index.html")]

def nav_html(active):
    items = []
    for label, href in NAV:
        cur = ' aria-current="page"' if label == active else ""
        items.append(f'<a href="{href}"{cur}>{esc(label)}</a>')
    return "<nav>" + "".join(items) + "</nav>"

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Week 10 injury report &amp; position-group exposure · NFL Own8</title>
<meta name="description" content="Official NFL.com Week 10 injury report, transcribed row by row, with position-group exposure. Starter/backup replacement is flagged unverified.">
<link rel="stylesheet" href="../advisory/assets/style.css">
</head><body>
<header class="top"><div class="brand">NFL Own8 · Week 10 injuries</div>__NAV__</header>
<main>
<h1>Week 10 official injury report — position-group exposure</h1>
<p class="lede">Transcribed row by row from the official <a href="__REPORT_URL__">NFL.com Week 10 injury report</a>
(8 page chunks read on __CAPTURED__). Scope: every listed player with an injury entry, a non-full practice status,
or a game status. Starter-vs-backup replacement is <b>not</b> shown: no official depth-chart source was reachable
(see <a href="../advisory/questions.html#Q-02">Q-02</a>). Blank replacement cells are flagged <span class="badge b-flag">UNVERIFIED</span>.</p>

<div class="notice warn"><b>Timing.</b> Thursday Nov 12 (WAS at NYG) is already final on the
<a href="__SCORES__">NFL.com Week 10 scores page</a>, but its rows below are the pre-game report.
Sunday and Monday statuses are the report as captured; later changes are not reflected.</div>

<div class="cards">
  <div class="card"><div class="num">__NGAMES__</div><div class="lbl">games on the report</div></div>
  <div class="card"><div class="num">__NROWS__</div><div class="lbl">rows transcribed</div></div>
  <div class="card"><div class="num">__NOUT__</div><div class="lbl">listed Out</div></div>
  <div class="card"><div class="num">__NDOUBT__</div><div class="lbl">listed Doubtful</div></div>
  <div class="card"><div class="num">__NQ__</div><div class="lbl">listed Questionable</div></div>
  <div class="card"><div class="num">__NDNP__</div><div class="lbl">Did Not Participate (practice)</div></div>
</div>

<h2>Games</h2>
<div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Matchup (away at home)</th><th>Kickoff (as printed)</th><th>Network (as printed)</th><th>Rows</th><th>Game status</th><th>Source</th></tr></thead>
<tbody>__GAMES__</tbody></table></div>

<h2>Position-group exposure by team</h2>
<p class="small">Counts come from the official listing only. "Out or Doubtful by group" shows which position groups have a player listed Out or Doubtful. It does <b>not</b> say who replaces them.</p>
<div class="table-wrap"><table>
<thead><tr><th>Team</th><th>Game</th><th>Out</th><th>Doubtful</th><th>Questionable</th><th>Did Not Practice</th><th>Out or Doubtful by group</th><th>2nd/3rd-string replacement</th><th>Source</th></tr></thead>
<tbody>__TEAMS__</tbody></table></div>

<h2>All transcribed rows</h2>
<div class="tools">
  <input id="q" type="search" placeholder="Search player, team, injury…" aria-label="Search rows">
  <select id="g" aria-label="Filter by game"><option value="">All games</option>__GAMEOPTS__</select>
  <select id="s" aria-label="Filter by game status"><option value="">Any game status</option><option>Out</option><option>Doubtful</option><option>Questionable</option><option value="-">No game status</option></select>
</div>
<div class="table-wrap"><table id="rows">
<thead><tr><th>Game</th><th>Team</th><th>Player (nfl.com)</th><th>Pos</th><th>Group</th><th>Injury (as listed)</th><th>Practice</th><th>Game status</th><th>2nd/3rd-string replacement</th><th>Source</th></tr></thead>
<tbody>__DETAIL__</tbody></table></div>
<p class="small" id="count"></p>

<h2>What this page does not show</h2>
<ul class="plain">
<li>Starter vs. backup order for any position (no official depth chart reachable; <a href="../advisory/questions.html#Q-02">Q-02</a>).</li>
<li>Players who are not on the report (healthy players, and players placed on injured reserve who are no longer listed).</li>
<li>Week 10 inactives (published by the NFL shortly before each kickoff; not yet captured).</li>
</ul>
<p class="small">Verification: every row's player link and the report link were copied from the captured page.
Build validation (build.py) checks format, team membership, position codes and duplicates. Transcription was a single pass;
an independent second-pass comparison against the live page has NOT been done (flag <a href="../advisory/flagged.html#F-14">F-14</a>).
Re-capture before using any row for a decision.
Data: <a href="data/w10-rows.json">w10-rows.json</a> · <a href="data/w10-team-summary.json">w10-team-summary.json</a> ·
<a href="data/w10_transcription.tsv">transcription (TSV)</a> · <a href="https://github.com/sassnarep3-star/Own8/blob/main/injury-depth/build.py">build.py</a></p>
</main>
<footer>Independent analysis page. Not betting advice. Gambling in Singapore: see <a href="../advisory/flagged.html#F-01">F-01</a>.</footer>
<script>
(function(){
  var q=document.getElementById('q'),g=document.getElementById('g'),s=document.getElementById('s');
  var rows=document.querySelectorAll('#rows tbody tr'),count=document.getElementById('count');
  function apply(){
    var t=(q.value||'').toLowerCase(),gv=g.value,sv=s.value,shown=0;
    rows.forEach(function(r){
      var cells=r.children, txt=r.textContent.toLowerCase();
      var gs=(cells[7]?cells[7].textContent.trim():'');
      var ok=(!t||txt.indexOf(t)>-1)&&(!gv||r.getAttribute('data-game')===gv)&&(!sv||(sv==='-'?gs==='':gs===sv));
      r.style.display=ok?'':'none'; if(ok)shown++;
    });
    count.textContent='Showing '+shown+' of '+rows.length+' rows.';
  }
  [q,g,s].forEach(function(el){el.addEventListener('input',apply);el.addEventListener('change',apply);});
  apply();
})();
</script>
</body></html>
"""

game_opts = "".join(f'<option value="{esc(gid)}">{esc(gid)} · {esc(g["away"])} at {esc(g["home"])}</option>' for gid, g in GAMES.items())
detail_rows_tagged = []
for r, tr in zip(rows, detail_html):
    detail_rows_tagged.append(tr.replace("<tr>", f'<tr data-game="{esc(r["game_id"])}">', 1))

page = (PAGE.replace("__NAV__", nav_html("Week 10 injuries"))
        .replace("__REPORT_URL__", REPORT_URL).replace("__SCORES__", SCORES_W10).replace("__CAPTURED__", esc(CAPTURED))
        .replace("__NGAMES__", str(n_games)).replace("__NROWS__", str(len(rows)))
        .replace("__NOUT__", str(total_out)).replace("__NDOUBT__", str(total_doubt))
        .replace("__NQ__", str(total_q)).replace("__NDNP__", str(total_dnp))
        .replace("__GAMES__", "".join(game_rows_html)).replace("__TEAMS__", "".join(team_rows_html))
        .replace("__DETAIL__", "".join(detail_rows_tagged)).replace("__GAMEOPTS__", game_opts))
with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(page)

print(f"games={n_games} rows={len(rows)} out={total_out} doubtful={total_doubt} questionable={total_q} dnp={total_dnp}")
print("validation: PASS")
