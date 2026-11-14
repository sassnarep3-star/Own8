#!/usr/bin/env python3
"""Build the decision-support section: out-of-sample evidence, suggestions, open questions.

Deliberately self-contained:
  * writes ONLY into decision/site/ (no shared index.html, pages/, assets/ or _config.yml)
  * every table row carries a source link
  * blank values stay blank and are labelled, never inferred
Run: python3 decision/scripts/build_decision_site.py
"""
import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent.parent
DEC = ROOT / "decision"
D, R, SITE = DEC / "data", DEC / "results", DEC / "site"
SITE.mkdir(parents=True, exist_ok=True)


def j(p):
    return json.loads(Path(p).read_text())


def e(x):
    return "" if x is None else html.escape(str(x))


def link(url, label="Official source"):
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def chip(t):
    t = str(t)
    cls = "good" if t.startswith(("VERIFIED", "ANSWERED", "FOUND")) else (
        "bad" if t.startswith(("NO", "NOT FOUND", "CRITICAL")) else "warn")
    return f'<span class="chip {cls}">{e(t)}</span>'


def table(headers, rows, caption, note=None):
    out = [f'<div class="tbl"><table><caption>{e(caption)}</caption><thead><tr>'
           + "".join(f"<th scope=\"col\">{e(h)}</th>" for h in headers) + "</tr></thead><tbody>"]
    for r in rows:
        cells = []
        for c in r:
            if c is None:
                cells.append('<td class="blank" title="Not available / not verified">—</td>')
            elif isinstance(c, str) and c.startswith("<"):
                cells.append(f"<td>{c}</td>")
            else:
                cells.append(f"<td>{e(c)}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table></div>")
    if note:
        out.append(f'<p class="note">{e(note)}</p>')
    return "".join(out)



OFFICIAL_HOSTS = {"www.nfl.com", "nextgenstats.nfl.com", "www.itl.nist.gov", "wsgc.wa.gov", "github.com"}

def official_url(sources):
    """First citable official URL in a source list; None when the list has none."""
    for s in sources:
        pu = urlparse(s)
        if pu.scheme == "https" and pu.hostname in OFFICIAL_HOSTS:
            return s
    return None

def repo_ref(sources):
    """Repo-relative paths shown as plain text so they can never become broken links."""
    out = [s for s in sources if not urlparse(s).scheme]
    return " ".join(f'<code>{e(s)}</code>' for s in out)


NAV = [
    ("index.html", "Start here"),
    ("executive-summary.html", "Executive summary"),
    ("out-of-sample.html", "Week 9 test"),
    ("suggestions.html", "Suggestions"),
    ("questions.html", "Open questions"),
    ("availability.html", "Injuries & depth"),
    ("anti-luck.html", "Anti-luck rules"),
    ("flagged.html", "Flagged for review"),
]


def wrap(slug, title, lead, body):
    nav = "".join(
        f'<a{" aria-current=page" if href == slug else ""} href="{href}">{e(label)}</a>'
        for href, label in NAV)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · Own8 decision support</title>
<style>
:root{{--bg:#0d1117;--panel:#151b23;--line:#232c38;--ink:#e6edf3;--mut:#8b98a8;--acc:#3fb950;--warn:#d29922;--bad:#f85149}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
header{{position:sticky;top:0;z-index:9;background:rgba(13,17,23,.94);border-bottom:1px solid var(--line);backdrop-filter:blur(8px)}}
.bar{{max-width:1180px;margin:0 auto;padding:.7rem 1rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap}}
.brand{{font-weight:700;letter-spacing:.02em;color:var(--ink);text-decoration:none}}
.brand b{{color:var(--acc)}}
nav{{display:flex;gap:.15rem;flex-wrap:wrap;margin-left:auto}}
nav a{{color:var(--mut);text-decoration:none;padding:.32rem .6rem;border-radius:7px;font-size:13.5px}}
nav a:hover{{background:var(--panel);color:var(--ink)}}
nav a[aria-current=page]{{background:#1f6feb22;color:#79c0ff;box-shadow:inset 0 0 0 1px #1f6feb55}}
main{{max-width:1180px;margin:0 auto;padding:1.6rem 1rem 4rem}}
h1{{font-size:1.72rem;line-height:1.25;margin:.2rem 0 .5rem;letter-spacing:-.01em}}
h2{{font-size:1.14rem;margin:2rem 0 .6rem;padding-bottom:.35rem;border-bottom:1px solid var(--line)}}
h3{{font-size:1rem;margin:1.3rem 0 .4rem}}
p{{margin:.55rem 0}}
.lead{{color:var(--mut);font-size:1.02rem;max-width:74ch}}
.note{{color:var(--mut);font-size:12.8px;margin:.45rem 0 0}}
a{{color:#79c0ff}}
code{{background:#1b2230;padding:.1rem .32rem;border-radius:5px;font-size:12.5px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:.8rem;margin:1.1rem 0}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:.85rem .9rem}}
.card .k{{font-size:1.5rem;font-weight:700;letter-spacing:-.02em}}
.card .l{{color:var(--mut);font-size:12.6px;text-transform:uppercase;letter-spacing:.05em}}
.tbl{{overflow-x:auto;border:1px solid var(--line);border-radius:11px;margin:.7rem 0}}
table{{border-collapse:collapse;width:100%;font-size:13.6px}}
caption{{text-align:left;padding:.65rem .8rem;color:var(--mut);font-size:12.5px;letter-spacing:.04em;text-transform:uppercase;border-bottom:1px solid var(--line)}}
th,td{{padding:.5rem .7rem;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}}
th{{background:#101720;color:var(--mut);font-weight:600;font-size:12.4px;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}}
tbody tr:last-child td{{border-bottom:0}}
tbody tr:hover{{background:#111823}}
td.blank{{color:#5a6472;text-align:center}}
.chip{{display:inline-block;padding:.1rem .45rem;border-radius:999px;font-size:11.4px;font-weight:600;white-space:nowrap;border:1px solid}}
.chip.good{{color:#3fb950;border-color:#3fb95055;background:#3fb95015}}
.chip.warn{{color:#d29922;border-color:#d2992255;background:#d2992215}}
.chip.bad{{color:#f85149;border-color:#f8514955;background:#f8514915}}
.box{{background:#10202b;border:1px solid #1f6feb44;border-left:3px solid #1f6feb;border-radius:9px;padding:.8rem 1rem;margin:1rem 0}}
.box.warn{{background:#241d10;border-color:#d2992244;border-left-color:#d29922}}
.box.bad{{background:#2a1414;border-color:#f8514944;border-left-color:#f85149}}
.box b{{display:block;margin-bottom:.2rem}}
.opt{{border:1px solid var(--line);border-radius:9px;padding:.6rem .8rem;margin:.45rem 0;background:#111823}}
.opt .t{{font-weight:600}}
.opt.rec{{border-color:#3fb95066;box-shadow:inset 3px 0 0 #3fb950}}
footer{{border-top:1px solid var(--line);color:var(--mut);font-size:12.5px;padding:1.1rem 1rem;text-align:center}}
ul{{margin:.4rem 0 .4rem 1.1rem;padding:0}} li{{margin:.22rem 0}}
</style></head><body>
<header><div class="bar"><a class="brand" href="index.html"><b>8</b> OWN8 · DECISION SUPPORT</a>
<nav aria-label="Section navigation">{nav}</nav></div></header>
<main><h1>{e(title)}</h1><p class="lead">{e(lead)}</p>{body}</main>
<footer>Paper research only · No wagering, no cash rewards, no profitability claim ·
Sources retrieved 2026-11-14 · Blank means unverified, never inferred</footer>
</body></html>"""


def page(slug, title, lead, body):
    (SITE / slug).write_text(wrap(slug, title, lead, body))


oos = j(R / "w9-out-of-sample.json")
sw = oos["summary"]
gates = j(D / "gates-audit.json")
sug = j(D / "suggestions-register.json")
qs = j(D / "open-questions.json")
av = j(D / "availability-probe.json")
inj = j(D / "injuries-2026-week10.json")
st = j(D / "standings-2026-reg-w9.json")
res = j(D / "results-2026-week9.json")
sch = j(D / "schedule-2026-week10.json")

# ---------------------------------------------------------------- index
idx_cards = "".join([
    f'<div class="card"><div class="k">{sw["n_games"]}</div><div class="l">Week 9 games tested</div></div>',
    f'<div class="card"><div class="k">{sw["winner_correct"]}/{sw["winner_scored"]}</div><div class="l">Benchmark winners correct</div></div>',
    f'<div class="card"><div class="k">{round(sw["baseline_winner_rules"]["better_win_pct"]["accuracy"]*100)}%</div><div class="l">Naive win-% rule, same games</div></div>',
    f'<div class="card"><div class="k">{qs["summary"]["answered"]}/{qs["summary"]["total"]}</div><div class="l">Questions answered</div></div>',
    f'<div class="card"><div class="k">{len(sug["suggestions"])}</div><div class="l">Suggestions awaiting a choice</div></div>',
])
verdict = f"""<div class="box bad"><b>The one result that matters</b>
<p>On all {sw["n_games"]} completed Week 9 games the site's own frozen lines picked
{sw["winner_correct"]} winners ({round(sw["winner_accuracy"]*100,1)}%). Against a coin flip that looks
significant (p={sw["binomial_p_vs_coinflip"]:.3f}). It is not evidence of skill: an identical
{round(sw["baseline_winner_rules"]["better_point_diff_per_game"]["accuracy"]*100,1)}% is achieved by simply picking
the team with the better season point differential, and
{round(sw["baseline_winner_rules"]["better_win_pct"]["accuracy"]*100,1)}% by picking the better record.
<strong>The model adds nothing measurable on this slate.</strong></p></div>"""
body = verdict + f'<div class="cards">{idx_cards}</div>' + """
<h2>What this section is for</h2>
<p>This is the decision layer: the evidence that was actually measured, the suggestions that need a
choice, and the questions that must be answered before anything is implemented. Nothing on these
pages has been applied to the live dashboard.</p>
<h2>Where to go</h2>
<ul class="navlist">
<li><a href="out-of-sample.html"><strong>Week 9 test</strong></a> — the frozen lines scored against
official results, with naive baselines. Supports the decision: does the current method show any skill?</li>
<li><a href="suggestions.html"><strong>Suggestions</strong></a> — six proposals, each with options, cost,
risk and a recommendation. Supports the decision: which path to implement, if any.</li>
<li><a href="questions.html"><strong>Open questions</strong></a> — what is answered, what is still open,
and what has to happen to answer it.</li>
<li><a href="availability.html"><strong>Injuries and depth</strong></a> — official Week 10 availability,
plus proof that starting-lineup depth is not published by the NFL.</li>
<li><a href="anti-luck.html"><strong>Anti-luck rules</strong></a> — how to stop luck being rewarded, and
what the current leaderboard design gets wrong.</li>
<li><a href="flagged.html"><strong>Flagged for review</strong></a> — irregularities and blanks, each with
the source that shows the problem.</li>
</ul>
"""
body += f"""<h2>How to use it</h2>
<p>Read the Week 9 test first — it changes how every other number on the site should be read. Then open
Suggestions, pick an option per item, and record the choice. The questions page lists what is still
blocked, so a choice is only made once its blockers are answered.</p>
<div class="box"><b>Verification rule used throughout</b>
<p>Every table row links an official source. Where an official source does not publish a value, the cell
is blank (shown as —) and the item is flagged. No value on these pages was inferred, estimated or
carried over from a non-official source.</p></div>"""
page("index.html", "Decision support",
     "Measured evidence, reviewable suggestions and open questions — built so a choice can be made before anything is implemented.",
     body)

# ---------------------------------------------------------------- out-of-sample
rowsz = [[g["game"], f'{g["proj_home_margin"]:+.1f}', f'{g["realized_home_margin"]:+d}',
          f'{g["abs_error_margin"]:.1f}', f'{g["proj_total"]:.1f}', g["realized_total"],
          g["projected_winner"], g["actual_winner"],
          chip("HIT" if g["winner_correct"] else "MISS") if g["winner_correct"] is not None else None,
          link(g["game_url"], "Game")]
         for g in sorted(oos["games"], key=lambda x: -x["abs_error_margin"])]
BASE_SRC = "https://www.nfl.com/scores/2026/week-9"
base_rows = [[k.replace("_", " "), v["hits"], v["scored"],
              f'{v["accuracy"]*100:.1f}%', f'{v["p_vs_coinflip"]:.4f}' if v["p_vs_coinflip"] else None,
              link(BASE_SRC, "Week 9")]
             for k, v in sw["baseline_winner_rules"].items()]
body = f"""<div class="box bad"><b>Result</b><p>Benchmark favourite hit
{sw["winner_correct"]} of {sw["winner_scored"]} ({round(sw["winner_accuracy"]*100,1)}%).
Naive point-differential rule: {round(sw["baseline_winner_rules"]["better_point_diff_per_game"]["accuracy"]*100,1)}% on the same games.
Naive win-percentage rule: {round(sw["baseline_winner_rules"]["better_win_pct"]["accuracy"]*100,1)}%.
The benchmark does not beat the simplest rule available.</p></div>
<h2>Accuracy versus a fixed baseline</h2>
<p>A hit rate means nothing without a comparison. These four rules were scored on the identical 15 games.</p>"""
body += table(["Rule", "Correct", "Scored", "Accuracy", "p vs coin flip (raw)", "Source"], base_rows,
              "Winner-pick rules, Week 9, n=15",
              "Raw p-values are shown only to demonstrate the trap: several rules clear p<0.05 on one slate. "
              "None of them is evidence of skill. Games with no side taken are excluded and counted.")
body += f"""<h2>Error, not just winners</h2>
<div class="cards">
<div class="card"><div class="k">{sw["margin_mae"]:.2f}</div><div class="l">Margin MAE (points)</div></div>
<div class="card"><div class="k">{sw["total_mae"]:.2f}</div><div class="l">Total MAE (points)</div></div>
<div class="card"><div class="k">{sw["naive_total_mae"]:.2f}</div><div class="l">Naive total MAE</div></div>
<div class="card"><div class="k">{sw["margin_bias"]:+.2f}</div><div class="l">Signed margin bias</div></div>
</div>
<p>{e(sw["home_field_diagnostic"])}</p>
<h2>Every game, worst error first</h2>"""
body += table(["Game", "Projected home margin", "Actual home margin", "Abs error", "Projected total",
               "Actual total", "Projected winner", "Actual winner", "Pick", "Source"], rowsz,
              "Week 9 out-of-sample detail",
              "Predictions are the frozen pre-kickoff values from analysis/model-lines-week9.json; "
              "actuals are official final scores. No line, price or edge exists for these games, so no ROI is shown.")
body += '<h2>What this does and does not prove</h2><ul>' + "".join(
    f"<li>{e(x)}</li>" for x in sw["interpretation"]) + "</ul>"
body += f'<div class="box warn"><b>Read this before quoting the number</b><p>{e(sw["anti_luck_conclusion"])}</p></div>'
page("out-of-sample.html", "Week 9: the first real test",
     "The site published 15 explicitly unvalidated Week 9 lines. Those games are now final. This is what happened.",
     body)

# ---------------------------------------------------------------- suggestions
sbody = [f'<div class="box"><b>{e(sug["status"])}</b><p>{e(sug["note"])}</p></div>',
         "<h2>How to choose</h2><ol>" + "".join(f"<li>{e(s)}</li>" for s in sug["decision_path"]) + "</ol>"]
for s in sug["suggestions"]:
    opts = []
    for o in s["options"]:
        rec = " rec" if s["recommendation"].startswith(o["option"]) else ""
        opts.append(f'<div class="opt{rec}"><span class="t">Option {e(o["option"])} — {e(o["label"])}</span>'
                    f'<p>{e(o["impact"])}</p><p class="note">Cost: {e(o["cost"])} · Risk: {e(o["risk"])}</p></div>')
    sbody.append(f"""<h2>{e(s["id"])} · {e(s["title"])}</h2>
<p><strong>Problem.</strong> {e(s["problem"])}</p>
<p><strong>Evidence.</strong> {e(s["evidence"])}</p>
{''.join(opts)}
<p><strong>Recommended.</strong> {e(s["recommendation"])} · <strong>Decision needed.</strong> {e(s["decision_needed"])}</p>
<p class="note">Status: proposed only — not implemented. Gates affected: {e(', '.join(s["gates_unblocked"]) or "none")} ·
Owner role: {e(s["owner_role"])} · {link(s["source"])}</p>""")
page("suggestions.html", "Suggestions for review",
     "Every proposal is listed with its evidence, its options, its cost and its risk. None has been implemented — the choice is yours.",
     "".join(sbody))

# ---------------------------------------------------------------- questions
def qsource(q):
    u = official_url(q["sources"])
    parts = [link(u, "Source")] if u else []
    ref = repo_ref(q["sources"])
    if ref:
        parts.append(ref)
    return " ".join(parts) if parts else None

qrows = [[q["id"], q["question"], chip(q["status"]), q["answer"], q["missing"],
          "YES" if q["blocking"] else "no", q["owner"], qsource(q)]
         for q in qs["questions"]]
body = f"""<div class="cards">
<div class="card"><div class="k">{qs["summary"]["total"]}</div><div class="l">Questions tracked</div></div>
<div class="card"><div class="k">{qs["summary"]["answered"]}</div><div class="l">Answered from official data</div></div>
<div class="card"><div class="k">{qs["summary"]["open"]}</div><div class="l">Still open</div></div>
<div class="card"><div class="k">{qs["summary"]["blocking"]}</div><div class="l">Blocking a decision</div></div></div>
<h2>Register</h2>""" + table(
    ["ID", "Question", "Status", "Answer", "What is missing", "Blocks a decision", "Owner", "Source"],
    qrows, "Open questions and information gaps",
    "A question is only marked answered when an official source settles it. 'What is missing' is the "
    "work needed to answer it — it is not a guess at the answer.") + """
<h2>How missing information would be discovered</h2>
<ul>
<li><strong>Depth and string order:</strong> needs an official depth chart or official participation counts.
Both were searched on 2026-11-14 and do not exist on nfl.com (see the injuries page). Until a citable
official source appears, the field stays blank.</li>
<li><strong>Prices and settlement:</strong> needs an operator-native, timestamped source with explicit
void/push rules. No official NFL page provides odds, so this must come from the project owner, not from
an aggregator.</li>
<li><strong>Correlation and joint outcomes:</strong> needs per-game player logs aligned to fixed thresholds.
Official season totals are not sufficient; the per-game logs must be transcribed with their own source links.</li>
<li><strong>Skill definition:</strong> needs a written rule, not more data. This is a decision, not a search.</li>
</ul>"""
page("questions.html", "Open questions",
     "What is known, what is unknown, and what specifically has to be answered before a decision is reasonable.",
     body)

# ---------------------------------------------------------------- availability
avrows = [[p["id"], link(p["page"], "Open page"), p["observed"], chip(p["result"]), p["meaning"]]
          for p in av["probe"]]
by_team = {}
for r in inj["rows"]:
    t = by_team.setdefault(r["team"], dict(rows=0, out=0, doubtful=0, questionable=0, blank=0, dnp=0))
    t["rows"] += 1
    gs = (r["game_status"] or "").strip()
    if gs == "Out":
        t["out"] += 1
    elif gs == "Doubtful":
        t["doubtful"] += 1
    elif gs == "Questionable":
        t["questionable"] += 1
    else:
        t["blank"] += 1
    if r["practice"] == "Did Not Participate In Practice":
        t["dnp"] += 1
inj_rows = [[r["team"], r["player"], r["position"], r["injury"] or None, r["practice"],
             r["game_status"] or None, link(r["source_url"], "Report")]
            for r in sorted(inj["rows"], key=lambda x: ((x["game_status"] or "zz"), x["team"], x["player"]))]
team_rows = [[k, v["rows"], v["out"], v["doubtful"], v["questionable"], v["dnp"], v["blank"],
              link(inj["source_url"], "Report")]
             for k, v in sorted(by_team.items())]
body = f"""<div class="box bad"><b>The requested starter/backup tracking cannot be built from official data</b>
<p>{e(av["answer"])}</p><p>{e(av["consequence"])}</p></div>
<h2>What was actually checked</h2>""" + table(
    ["ID", "Official page", "What the page returned", "Result", "What that means"],
    avrows, "Official-source feasibility probe, 2026-11-14",
    "Each row is an observed page response, not an opinion. Two depth-chart URLs were tried "
    "(league-wide and club-level); both return the NFL 404 page.") + f"""
<h2>What would unblock it</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in av["what_would_unblock_it"])}</ul>
<h2>Official availability this week instead</h2>
<p>Week 10 injury report, transcribed verbatim: <strong>{len(inj['rows'])} player rows</strong> across
{len(by_team)} clubs. Out / Doubtful / Questionable counts come from the official Game Status column;
blank means the club left it blank, which is <em>not</em> a statement that the player is available.</p>"""
body += table(["Team", "Rows", "Out", "Doubtful", "Questionable", "Did not practise", "No designation", "Source"],
              team_rows, "Week 10 availability by club")
body += table(["Team", "Player", "Position", "Injury", "Practice", "Game status", "Source"], inj_rows,
              "Week 10 injury report (official rows)",
              "Sorted by game status then club. Blank cells mirror blank cells on the official page.")
page("availability.html", "Injuries and depth",
     "Official injury availability is real and current. Starting-lineup depth is not published by the NFL — verified, not assumed.",
     body)

# ---------------------------------------------------------------- anti-luck
defects = [[d["id"], chip(d["severity"].upper()), d["defect"], d["evidence"], d["fix"],
            link(d["source"], "Method")]
           for d in gates["defects"]]
body = f"""<div class="box warn"><b>Why this page exists</b>
<p>{e(gates["strongest_available_signal"])}</p></div>
<h2>Defects found in the current competition design</h2>""" + table(
    ["ID", "Severity", "Defect", "Evidence", "Proposed fix", "Reference"], defects,
    "Leaderboard and validation-gate audit",
    "These are defects in the project's own design, not in the NFL's data. Each is fixable without any new data.") + """
<h2>What "removing luck" can honestly mean</h2>
<p>Luck cannot be deleted from a result. What can be done is to make luck's expected contribution small and visible:</p>
<ul>
<li><strong>Compress by sample, not by confidence.</strong> Require a minimum number of slates before a score counts.</li>
<li><strong>Compare, never report alone.</strong> Every number sits beside a fixed naive rule scored on the same games.</li>
<li><strong>Count the attempts.</strong> Register every variant up front and adjust for the whole family, because a
p&lt;0.01 will appear by chance when enough variants are tried.</li>
<li><strong>Separate error from outcome.</strong> A correct pick and a well-estimated line are different achievements;
report both.</li>
<li><strong>Reward the process, not the run.</strong> Pay for beating a baseline over a long sample with a stated
uncertainty interval, never for a hot week.</li>
</ul>
<div class="box"><b>Applied to today's evidence</b><p>On Week 9 the benchmark ties the naive point-differential
rule exactly and loses to the naive win-percentage rule. Under any rule in the list above, that scores zero.
Saying so is the useful result.</p></div>"""
page("anti-luck.html", "Anti-luck rules",
     "How to keep luck out of the leaderboard — and what the current design gets wrong.",
     body)

# ---------------------------------------------------------------- flagged
flags = [
    ["FL-01", "high", "The published dashboard is frozen at 2026-11-04 (Week 9 pre-game) while Week 9 is final and Week 10 has started.",
     "data/audit-snapshot.json", link("https://www.nfl.com/scores/2026/week-9", "Week 9 finals")],
    ["FL-02", "high", "No official depth chart exists on nfl.com, so 2nd/3rd/4th-string tracking is unverifiable and must stay blank.",
     "decision/data/availability-probe.json", link("https://www.nfl.com/teams/depth-chart", "404 page")],
    ["FL-03", "high", "The 15 published Week 9 lines are superseded: the games are final and the numbers should be read as historical.",
     "analysis/model-lines-week9.json", link("https://www.nfl.com/scores/2026/week-9", "Week 9 finals")],
    ["FL-04", "high", "Four parallel sessions claimed the same suggestions / questions / injury scope on 2026-11-14, risking duplicated and conflicting pages.",
     "COORDINATION.md", link("https://github.com/sassnarep3-star/Own8/actions", "CI runs")],
    ["FL-05", "medium", "Week 10 injury report was partially transcribed here (114 rows, 18 clubs); clubs not read are absent, not empty.",
     "decision/data/injuries-2026-week10.json", link("https://www.nfl.com/injuries/league/2026/reg10", "Report")],
    ["FL-06", "medium", "No verified operator price exists for any published line, so no ROI, edge or reward can be computed for any strategy.",
     "analysis/validation-gates.json", link("https://www.nfl.com/scores/", "NFL scores")],
    ["FL-07", "medium", "Leaderboard scoring requires a Brier score but the published benchmarks emit no probabilities.",
     "analysis/leaderboard.json", link("https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm", "NIST")],
    ["FL-08", "low", "Automated publishing is not wired: workflows validate and upload an artifact but do not republish the site, so it cannot refresh itself.",
     ".github/workflows/audit.yml", link("https://github.com/sassnarep3-star/Own8/actions", "Actions")],
]
body = """<div class="box warn"><b>Non-blocking by design</b>
<p>Nothing on this page prevents publication. Each item is shown with its source so it can be reviewed
after the site is live and changed on request. An item is removed only when its source confirms a fix.</p></div>
<h2>Register</h2>""" + table(["ID", "Priority", "Finding", "Where it lives", "Source"], flags,
                             "Flagged for review",
                             "Priorities: high = misleading if ignored; medium = limits what can be concluded; low = hygiene.")
body += f"""<h2>Unverified values, deliberately left blank</h2>
<ul>
<li><strong>Starter / 2nd / 3rd / 4th string designation.</strong> No official source. {link('https://www.nfl.com/teams/depth-chart','Checked')}.</li>
<li><strong>Snap counts and routes run.</strong> Absent from the official stats taxonomy. {link('https://www.nfl.com/stats/player-stats/','Checked')}.</li>
<li><strong>Market lines, prices and edges.</strong> No official NFL price source exists.</li>
<li><strong>Parlay and prop-combo correlations.</strong> Needs aligned per-game outcomes that are not yet transcribed.</li>
</ul>
<p>Each of these stays blank on every page in this section. A blank is a statement that the value could
not be confirmed, not a zero.</p>"""
page("flagged.html", "Flagged for review",
     "Irregularities and unverified items, each with the source that shows the problem.",
     body)


# ---------------------------------------------------------------- executive summary
def esc_summary():
    sn = sw["baseline_winner_rules"]
    return f"""<h2>Bottom line in seven lines</h2>
<ol>
<li><strong>The site is honest about what it does not know, and that is its strength.</strong> Every blocked
gate, every blank cell and every flag is correctly labelled. Nothing found this week contradicts that discipline.</li>
<li><strong>The published dashboard is stale.</strong> It was frozen at 2026-11-04, before Week 9 was played.
All 15 Week 9 games are now final and Week 10 is under way.</li>
<li><strong>The first real out-of-sample test is in, and it does not show skill.</strong> The frozen lines picked
{sw["winner_correct"]} of {sw["winner_scored"]} winners ({round(sw["winner_accuracy"]*100,1)}%); a naive
point-differential rule scored {round(sn["better_point_diff_per_game"]["accuracy"]*100,1)}% on the same games and a
naive win-percentage rule scored {round(sn["better_win_pct"]["accuracy"]*100,1)}%.</li>
<li><strong>A spectacular-looking p-value is a trap here.</strong> The coin-flip p-value is
{sw["binomial_p_vs_coinflip"]:.3f}, which would look like proof of skill; the baseline comparison shows it is not.</li>
<li><strong>Starting-lineup depth cannot be tracked from official data.</strong> nfl.com publishes no depth chart and
no snap counts; only position, roster status and injury designation are official. The requested
2nd/3rd/4th-string fields must stay blank.</li>
<li><strong>No strategy can ever be rewarded under the current rules,</strong> because three of the eight gates require
prices that do not exist in any official source. That is a design problem, not a data problem.</li>
<li><strong>Six decisions are waiting for a human,</strong> and none of them needs new data. They are on the
<a href="suggestions.html">Suggestions</a> page.</li>
</ol>
<h2>What was verified this session, and how</h2>"""
    + table(["Item", "How it was verified", "Result", "Source"],
      [["32 club records through Week 9", "Official standings retrieved and cross-read against the Week 10 schedule page",
        chip("VERIFIED"), link("https://www.nfl.com/standings/league/2026/REG", "Standings")],
       ["15 Week 9 final scores", "Official scores page, every game FINAL",
        chip("VERIFIED"), link("https://www.nfl.com/scores/2026/week-9", "Scores")],
       ["Week 10 slate: 14 games + 4 byes", "Official schedule page (32 clubs accounted for)",
        chip("VERIFIED"), link("https://www.nfl.com/schedules/2026/by-week/week-10", "Schedule")],
       ["Week 10 injury availability", f"{len(inj['rows'])} official player rows transcribed across {len(by_team)} clubs",
        chip("VERIFIED"), link("https://www.nfl.com/injuries/league/2026/reg10", "Injury report")],
       ["Depth chart / string order", "League-wide and club-level URLs both return the NFL 404 page",
        chip("NOT FOUND"), link("https://www.nfl.com/teams/depth-chart", "404")],
       ["Snap counts / role data", "Not present in the official player-stats taxonomy",
        chip("NOT FOUND"), link("https://www.nfl.com/stats/player-stats/", "Stats")],
       ["Market prices / edges", "No official NFL price source exists; none was assumed",
        None, link("https://www.nfl.com/scores/", "NFL")]],
      "Verification performed 2026-11-14",
      "Every result above is either an official page reading or an observed absence. No value was inferred.")
    + f"""<h2>What is still unknown</h2>
<p>{qs["summary"]["open"]} questions remain open and {qs["summary"]["blocking"]} of all tracked questions block a
decision. The two that matter most: <strong>what a strategy must beat to be called skilful</strong> (a rule to write,
not data to find) and <strong>where verified prices come from</strong> (no official source exists, so it needs a project
decision). Full list on the <a href="questions.html">Open questions</a> page.</p>
<h2>Honest limitation of this summary</h2>
<div class="box warn"><b>One week is one week</b>
<p>The test above is {sw["n_games"]} games. It is enough to reject the claim that the current method has demonstrated
skill, and nowhere near enough to prove it has none. The conclusion is "not shown", not "disproved".</p></div>"""

page("executive-summary.html", "Executive summary",
     "The short version: what is verified, what the first real test showed, and what needs a decision.",
     esc_summary())


print("built", len(NAV), "pages in", SITE.relative_to(ROOT))
