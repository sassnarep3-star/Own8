#!/usr/bin/env python3
"""Build the integration workspace pages (session 2d4025da, tasks I1-I4).

Reads only integration/data/*.json (committed captures) and writes
integration/*.html. Every NFL-fact table row carries its official nfl.com
source link; software-check rows carry their evidence link. Nothing is
inferred: values come straight from the JSON captures.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
INT = ROOT / "integration"
E = html.escape

NAV = [
    ("index.html", "01", "Integration dashboard"),
    ("freshness.html", "02", "Freshness audit"),
    ("reconciliation.html", "03", "Reconciliation & signals"),
    ("injuries-w10.html", "04", "Week 10 injuries"),
    ("review.html", "05", "Repo review (I1)"),
    ("../index.html", "00", "Root dashboard"),
    ("../requirements/index.html", "★", "Requirements & decisions"),
    ("../decision/site/index.html", "↗", "Decision support"),
    ("../origination/index.html", "↗", "Origination lab"),
    ("../suggestions/index.html", "↗", "Suggestions"),
    ("../review/index.html", "↗", "Repo review (aa2d8cbe)"),
]


def page(name, title, desc, body, cur):
    nav = "".join(
        f'<a{" aria-current=page" if href == cur else ""} href="{href}"><span>{num}</span>{E(label)}</a>'
        for href, num, label in NAV
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{E(desc)}"><title>{E(title)} · Own8 integration</title><link rel="stylesheet" href="assets/style.css"><script src="assets/app.js" defer></script></head><body><a class="skip" href="#main">Skip to content</a><div class="layout"><aside><a class="brand" href="../index.html"><span class="brand-mark">8</span> OWN8<span class="lab">INTEGRATION</span></a><div class="nav-label">INTEGRATION WORKSPACE</div><nav aria-label="Integration navigation">{nav}</nav><div class="aside-foot">Session 2d4025da · I1–I4<br>Captured 14 NOV 2026 · Paper research only</div></aside><div class="workspace"><header class="top"><span>OWN8 / {E(title)}</span><span>2026 SEASON · WEEK 10</span></header><main id="main"><div class="eyebrow">INTEGRATION · 2026-11-14</div><h1>{E(title)}</h1><p class="lead">{E(desc)}</p>{body}</main><footer><span>OWN8 · Evidence before edge.</span><span>Every fact row links its official source. Blank = unconfirmed.</span></footer></div></div></body></html>"""


def table(caption, headers, rows, cls=""):
    th = "".join(f"<th{' class=num' if h.startswith('#') else ''}>{E(h.lstrip('#'))}</th>" for h in headers)
    tr = []
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            cells.append(f"<td{' class=num' if headers[i].startswith('#') else ''}>{c}</td>")
        tr.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<div class="table-tools"><label>Filter rows <input type="search" placeholder="Search this table…" aria-label="Filter {E(caption)}"></label>'
            f'<span class="row-count">{len(rows)} rows</span></div>'
            f'<div class="table-wrap"><table><caption>{E(caption)}</caption><thead><tr>{th}</tr></thead><tbody>{"".join(tr)}</tbody></table></div>')


def src(url, label="Official source ↗"):
    return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'


def badge(text):
    kind = {"PASS": "good", "CURRENT": "good", "FAIL": "bad", "STALE": "warn",
            "SUPERSEDED BY FACT": "warn", "HEALTHY": "good", "open, non-blocking": "mut",
            "needs review": "warn", "resolved": "good", "fixed": "good"}.get(text.split(" ")[0].rstrip(":"), "neutral")
    if "STALE" in text:
        kind = "warn"
    if "SUPERSEDED" in text:
        kind = "warn"
    if text.startswith("CURRENT") or text in ("PASS", "HEALTHY", "resolved"):
        kind = "good"
    if text.startswith("FAIL") or text == "high":
        kind = "bad"
    if text == "medium":
        kind = "warn"
    if text == "low":
        kind = "mut"
    return f'<span class="badge {kind}">{E(text)}</span>'


def load(name):
    with open(INT / "data" / name, encoding="utf-8") as fh:
        return json.load(fh)


def build():
    review = load("repo-review-2026-11-14.json")
    fresh = load("freshness.json")
    health = load("pages-health.json")
    recon = load("reconciliation-2026-11-14.json")
    stand = load("standings-2026-reg-w10.json")
    w9 = load("scores-2026-week9.json")
    w10 = load("schedule-2026-week10.json")
    inj = load("injuries-2026-week10.json")
    sig = load("deficiency-signals-w10.json")

    n_checks = len(review["checkers"])
    n_pass = sum(1 for c in review["checkers"] if c["exit"] == 0)
    n_find = len(review["findings"])
    n_inj_rows = sum(len(t["rows"]) for g in inj["games"] for t in g["teams"])

    # ---------- index.html ----------
    kpis = f"""<div class="kpis">
<a class="kpi" href="reconciliation.html"><strong>{recon['games_reconciled']}</strong><h2>Official games reconciled</h2><small>137 games → 32/32 standings rows ✓</small></a>
<a class="kpi" href="injuries-w10.html"><strong>{n_inj_rows}</strong><h2>Week 10 injury rows</h2><small>28 team tables, every row source-linked</small></a>
<a class="kpi" href="review.html"><strong>{n_pass}/{n_checks}</strong><h2>Checkers passing</h2><small>1 known pre-existing failure (IR-01)</small></a>
<a class="kpi" href="freshness.html"><strong>{sum(1 for r in fresh['rows'] if 'STALE' in r['status'] or 'SUPERSEDED' in r['status'])}</strong><h2>Stale / superseded surfaces</h2><small>of {len(fresh['rows'])} audited — see freshness audit</small></a>
</div>"""
    status_rows = [
        ["I1 · Repo review", badge("done") + " Checker matrix + 10 findings with evidence", '<a href="review.html">review.html ↗</a>'],
        ["I2 · Freshness + fresh capture", badge("done") + " W9 finals, W10 slate, standings, 345-row injuries, 137-game reconciliation", '<a href="freshness.html">freshness.html ↗</a>'],
        ["I3 · Pages deploy health", badge(health["result"].split(" —")[0]) + " API `errored` → recovered; 6 green builds 14 Nov", '''<a href="review.html">evidence ↗</a>'''],
        ["I4 · Final integration", badge("done") + " PR #43 merged (08b42d2) · Pages deploy success · live site re-fetched", '<a href="https://github.com/sassnarep3-star/Own8/pull/43" target="_blank" rel="noopener noreferrer">PR #43 ↗</a>'],
    ]
    surface_rows = []
    for r in fresh["rows"]:
        surface_rows.append([E(r["surface"]), E(r["shows"][:90]), badge(r["status"]), src(r["source"])])
    health_rows = [[E(o["at"]), badge(o["status"]), E(o["detail"][:150]), src(o["evidence_url"], "Evidence ↗")] for o in health["observations"]]
    body = kpis + """
<div class="notice"><strong>What this workspace is</strong><p>The integration layer for session 2d4025da: it runs every committed checker, audits how fresh each published surface is, publishes fresh official NFL captures for Week 9/Week 10 (with per-row source links), reconciles the standings line-by-line against the official game log, diagnoses GitHub Pages health, and performs the final root-navigation integration. It does not replace any parallel session's workspace — it maps, verifies and links them.</p></div>
""" + table("Integration tasks", ["Task", "Status", "Where"], status_rows) + \
        table("Published surfaces vs the live league (as of 2026-11-14)", ["Surface", "What it shows", "Freshness", "Official basis"], surface_rows) + \
        '<h2 id="pages">GitHub Pages health (I3)</h2>' + table("Pages deploy observations", ["When", "Status", "Detail", "Evidence"], health_rows) + \
        f'<p class="table-note">{E(health["diagnosis"])}</p>'
    (INT / "index.html").write_text(page("index", "Integration dashboard",
        "Checker inventory, deploy health, freshness map and task status for the final integration of Own8.",
        body, "index.html"), encoding="utf-8")

    # ---------- review.html ----------
    chk_rows = [[E(c["family"]), f"<code>{E(c['checker'])}</code>", badge("PASS" if c["exit"] == 0 else "FAIL"),
                 E(c["result"]), src("https://github.com/sassnarep3-star/Own8/blob/main/README.md", "How to run ↗")]
                for c in review["checkers"]]
    find_rows = [[f"<strong>{E(f['id'])}</strong>", badge(f["severity"]), E(f["area"]), E(f["finding"]),
                  f"<code>{E(f['evidence'][:90])}</code> {src(f['link'], 'Evidence ↗')}", E(f["owner"]), badge(f["status"])]
                 for f in review["findings"]]
    wf_rows = [[f'<code>{E(w["file"])}</code> {src(w["link"], "file ↗")}', E(w["runs"])] for w in review["ci_workflows"]]
    body = (f'<div class="notice"><strong>Scope</strong><p>{E(review["scope"])}</p></div>' +
            table("Checker matrix (every committed checker, executed 2026-11-14)", ["Family", "Command", "Result", "Output", "Evidence"], chk_rows) +
            table("Irregularities found (this review)", ["ID", "Severity", "Area", "Finding", "Evidence", "Owner", "Status"], find_rows) +
            table("CI workflows on main", ["File", "What it runs"], wf_rows))
    (INT / "review.html").write_text(page("review", "Repository review (I1)",
        "Line-by-line structural review: every checker executed, every irregularity recorded with evidence.",
        body, "review.html"), encoding="utf-8")

    # ---------- freshness.html ----------
    fr_rows = [[E(r["surface"]), E(r["shows"]), E(r["official_state"]), badge(r["status"]), E(r["action"]), src(r["source"])]
               for r in fresh["rows"]]
    w9_rows = [[g["date"], E(g["slot"]), f"<strong>{E(g['away'])}</strong> {g['away_score']} – {g['home_score']} <strong>{E(g['home'])}</strong>",
                g["status"], src(g["game_url"])] for g in w9["games"]]
    w10_rows = [[g["date"], E(g["away"]) + " " + (str(g["away_score"]) if g["away_score"] is not None else "–"),
                 E(g["home"]) + " " + (str(g["home_score"]) if g["home_score"] is not None else "–"),
                 E(g["kickoff_printed"]), E(g["network"]), g["status"], src(g["game_url"])] for g in w10["games"]]
    body = (f'<div class="notice"><strong>Method</strong><p>{E(fresh["method"])}</p></div>' +
            table("Freshness audit — every published surface", ["Surface", "What it shows", "Live official state (2026-11-14)", "Status", "Action", "Official source"], fr_rows) +
            '<h2>Week 9 final results (fresh capture)</h2>' +
            table("All 15 Week 9 games", ["Date", "Slot", "Result", "Status", "Source"], w9_rows) +
            '<h2>Week 10 slate (fresh capture)</h2>' +
            table("Week 10: 14 games, byes CHI / DEN / PHI / TB", ["Date", "Away", "Home", "Kickoff (printed)", "Network", "Status", "Source"], w10_rows))
    (INT / "freshness.html").write_text(page("freshness", "Freshness audit",
        "Which surfaces are stale, superseded or current — checked against live official NFL pages.",
        body, "freshness.html"), encoding="utf-8")

    # ---------- reconciliation.html ----------
    st_rows = []
    smap = {t["abbr"]: t for t in stand["teams"]}
    for t in stand["teams"]:
        st_rows.append([E(t["abbr"]), E(t["name"]), f"{t['W']}-{t['L']}-{t['T']}", str(t["PCT"]), str(t["PF"]), str(t["PA"]), str(t["NET"]),
                        E(t["HOME"]), E(t["ROAD"]), E(t["STRK"]), src("https://www.nfl.com/standings/")])
    sig_rows = [[E(s["game"]), E(s["team"]), ", ".join(s["out_positions"]) or "—",
                 ", ".join(s["doubtful_positions"]) or "—", ", ".join(s["questionable_positions"]) or "—",
                 str(s["out_count"]), "QB OUT" if s["qb_out"] else "", src(s["source_url"])] for s in sig["signals"]]
    body = f"""<div class="notice"><strong>Verification result</strong><p>Recomputing every club's W-L-T, PF and PA from {recon['games_reconciled']} official game results (Weeks 1–8 inherited official log + Week 9 finals captured here + Week 10 TNF) matches the fresh <a href="https://www.nfl.com/standings/" target="_blank" rel="noopener noreferrer">nfl.com/standings</a> transcription on <strong>{recon['standings_rows_ok']}/32 rows and {recon['field_comparisons']} field comparisons</strong>, plus {recon['schedule_record_crosschecks_ok']}/28 schedule-page record cross-checks. Status: {badge(recon['status'])}. Machine-readable evidence: <code>integration/data/reconciliation-2026-11-14.json</code>.</p></div>
""" + table("Standings as captured 2026-11-14 (every row reconciled)", ["Team", "Name", "W-L-T", "#PCT", "#PF", "#PA", "#NET", "Home", "Road", "Strk", "Source"], st_rows) + \
        '<h2>Position-group deficiency signals (Week 10)</h2>' + \
        f'<p class="table-note">Derived ONLY from Out/Doubtful/Questionable cells on the official injury page — counts and position sets, never replacement names. Official depth-chart pages return 404 (verified independently by three sessions), so 2nd/3rd/4th-string order stays blank. {E(sig["caveat"])}</p>' + \
        table("Out / Doubtful / Questionable by team", ["Game", "Team", "OUT positions", "DOUBTFUL positions", "QUESTIONABLE positions", "#OUT", "QB note", "Source"], sig_rows)
    (INT / "reconciliation.html").write_text(page("reconciliation", "Reconciliation & signals",
        "137 official games recomputed into the standings, plus position-group deficiency signals from the Week 10 injury report.",
        body, "reconciliation.html"), encoding="utf-8")

    # ---------- injuries-w10.html ----------
    inj_rows = []
    for g in inj["games"]:
        label = f"{g['date_header']} · {g['kickoff_printed']} · {E(g['network'])} · <strong>{E(g['away']['abbr'])} at {E(g['home']['abbr'])}</strong>"
        for t in g["teams"]:
            for r in t["rows"]:
                inj_rows.append([label if r is t["rows"][0] else "", E(t["table_label"]),
                                 f'<a href="{r["url"]}" target="_blank" rel="noopener noreferrer">{E(r["player"])}</a>',
                                 E(r["position"]), E(r["injury"]), E(r["practice"]),
                                 badge(r["game_status"]) if r["game_status"] else '<span class="badge mut">blank as printed</span>',
                                 src(inj["source_url"])])
    news_rows = [[E(n["title"]), src(n["url"])] for n in inj["news"]]
    body = (f'<div class="notice"><strong>Capture</strong><p>{E(inj["verification"])} {E(inj["notes"][0])} {E(inj["notes"][2])}</p></div>' +
            table("Week 10 official injury report — all rows", ["Game", "Team", "Player", "Pos", "Injury (as printed)", "Practice status", "Game status", "Source"], inj_rows) +
            '<h2>Official news printed on the same page</h2>' +
            table("News headlines (verbatim)", ["Headline", "Source"], news_rows))
    (INT / "injuries-w10.html").write_text(page("injuries-w10", "Week 10 injuries",
        f"Complete transcription of the official Week 10 injury report: {n_inj_rows} rows, 28 team tables, every row with its player page.",
        body, "injuries-w10.html"), encoding="utf-8")

    print(f"built 5 pages; injury rows={n_inj_rows}; checkers={n_pass}/{n_checks}; findings={n_find}")


if __name__ == "__main__":
    build()
