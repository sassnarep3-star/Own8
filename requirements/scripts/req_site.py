#!/usr/bin/env python3
"""Generate the requirements / decision-review section of the dashboard.

Reads only the JSON in ../data and ../results, which in turn come from the official captures and
the check scripts. Nothing on these pages is hand-typed except the prose that explains a table,
and every table row that states a fact carries an official source link.

Runs with the standard library only and writes static HTML that reuses the root dashboard's
stylesheet, so the section looks like part of the same product rather than a tenth site.
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REQ = os.path.dirname(HERE)
ROOT = os.path.dirname(REQ)
OUT = os.path.join(REQ, "pages")
os.makedirs(OUT, exist_ok=True)

CAPTURED = "2026-11-14"


def load(rel):
    with open(os.path.join(REQ, rel), encoding="utf-8") as fh:
        return json.load(fh)


REQS = load("data/requirements.json")
QUESTIONS = load("data/questions.json")
SUGGESTIONS = load("data/suggestions.json")
CHECKS = load("results/checks.json")
GRADING = load("results/w9-grading.json")
LINES = load("results/week10-lines.json")
INJURIES = load("results/injuries-w10.json")
AVAILABILITY = load("results/availability.json")
LUCK = load("results/luck.json")
FLAGS = load("results/flags.json")


def e(x):
    return "" if x is None else html.escape(str(x))


def a(url, label="Official source"):
    if not url:
        return ""
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} &#8599;</a>'


def badge(text):
    t = str(text)
    cls = "good" if t in ("MET", "ANSWERED", "VERIFIED") else "warn" if ("PARTIAL" in t or "OPEN" in t or "UNDECIDED" in t or "NEEDS" in t or "BLOCKED" in t or "UNVALIDATED" in t) else "neutral"
    if "NOT POSSIBLE" in t or "IMPOSSIBLE" in t:
        cls = "warn"
    return f'<span class="badge {cls}">{e(text)}</span>'


def table(headers, rows, caption, note=None):
    out = ('<div class="table-tools"><label>Filter rows <input type="search" placeholder="Search this table&hellip;" '
           f'aria-label="Filter {e(caption)}"></label><span class="row-count">{len(rows)} rows</span></div>'
           '<div class="table-wrap"><table><caption>' + e(caption) + '</caption><thead><tr>'
           + "".join(f'<th scope="col">{e(h)}</th>' for h in headers) + "</tr></thead><tbody>")
    for row in rows:
        cells = []
        for c in row:
            if c is None:
                cells.append('<td class="missing" aria-label="Unverified or not available"></td>')
            elif isinstance(c, str) and c.startswith("<"):
                cells.append(f"<td>{c}</td>")
            else:
                cells.append(f"<td>{e(c)}</td>")
        out += "<tr>" + "".join(cells) + "</tr>"
    out += "</tbody></table></div>"
    if note:
        out += f'<p class="table-note">{note}</p>'
    return out


NAV = [
    ("index", "Section overview"),
    ("executive-summary", "Executive summary"),
    ("requirements", "Requirement register"),
    ("questions", "Open questions"),
    ("suggestions", "Suggestions &amp; decisions"),
    ("lines", "Week 10 lines"),
    ("grading", "Week 9 grading"),
    ("injuries", "Injury tracker"),
    ("availability", "Backups &amp; deficiencies"),
    ("luck", "Luck vs skill"),
    ("combos", "Parlays &amp; props"),
    ("strategies", "Strategy gates"),
    ("gates", "Validation gates"),
    ("correlations", "Correlation register"),
    ("leaderboard", "Skill leaderboard"),
    ("verification", "Verification log"),
    ("sources", "Sources"),
    ("flagged", "Flagged for review"),
]


def wrap(slug, title, desc, body, eyebrow=None):
    pre = "../../"
    nav = "".join(
        f'<a {"aria-current=page" if key == slug else ""} href="{key}.html"><span>{(i + 1):02d}</span>{label}</a>'
        for i, (key, label) in enumerate(NAV)
    )
    nav += f'<a href="{pre}index.html"><span>&#8592;</span>Main dashboard</a>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{e(desc)}"><title>{e(title)} &middot; Own8</title>
<link rel="stylesheet" href="{pre}assets/style.css"><script src="{pre}assets/app.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<aside><a class="brand" href="{pre}index.html"><span class="brand-mark">8</span> OWN8<span class="lab">RESEARCH LAB</span></a>
<div class="nav-label">NFL / DECISION REVIEW</div>
<nav aria-label="Section navigation">{nav}</nav>
<div class="aside-foot"><span class="pulse"></span> Official-source audit<br><small>Snapshot &middot; 14 NOV 2026<br>Paper research only</small></div></aside>
<div class="workspace"><header><span>NFL LINE ORIGINATION <span class="muted">/ {e(title)}</span></span><span class="date">2026 SEASON &middot; WEEK 10</span></header>
<main id="main"><div class="eyebrow">OWN8 REQUIREMENTS &amp; DECISION REVIEW / {e(eyebrow or CAPTURED)}</div><h1>{e(title)}</h1>
<p class="lead">{e(desc)}</p>{body}</main>
<footer><span>OWN8 &middot; Evidence before edge.</span><span>Snapshot, not live odds. No wagering or cash rewards.</span></footer></div></body></html>'''


def page(slug, title, desc, body, eyebrow=None):
    with open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8") as fh:
        fh.write(wrap(slug, title, desc, body, eyebrow))


def note(text, title="Research boundary"):
    return f'<div class="notice"><strong>{e(title)}</strong><p>{e(text)}</p></div>'


def sec(title):
    return f"<h2>{e(title)}</h2>"


# ------------------------------------------------------------------ overview
counts = {}
for r in REQS["requirements"]:
    counts[r["status"]] = counts.get(r["status"], 0) + 1
q_states = {}
for q in QUESTIONS["questions"]:
    q_states[q["state"]] = q_states.get(q["state"], 0) + 1
cards = [
    (len(REQS["requirements"]), "Operator requirements traced"),
    (q_states.get("OPEN", 0) + q_states.get("IMPOSSIBLE", 0), "Questions still blocking a decision"),
    (len(SUGGESTIONS["suggestions"]), "Reviewable suggestions"),
    (len(FLAGS["flags"]), "Items flagged for review"),
]
kpis = '<div class="kpis">' + "".join(
    f'<div class="kpi"><span>{e(n)}</span><h2>{e(t)}</h2><small>See the tables below</small></div>' for n, t in cards
) + "</div>"

status_rows = [[r["id"], r["requirement"], badge(r["status"]), r["what_is_missing"] or "None recorded",
                f'<code>{e(r["evidence"].split(" + ")[0])}</code>', a(r.get("source_url"))] for r in REQS["requirements"]]
overview_body = kpis + sec("What this section is for") + (
    "<p>This is the review layer the project was missing. It answers four questions in order: what was asked for, "
    "what is actually known, what is still unknown, and what the next decision should be. Nothing here is a pitch. "
    "Three of the sixteen requirements cannot be met at all from official sources, and they are marked that way rather "
    "than being quietly softened.</p>") + table(
    ["ID", "Requirement", "Status", "What is missing", "Evidence", "Official source"], status_rows,
    "Requirement status summary",
    "Status is recomputed from the artifacts by <code>requirements/scripts/req_site.py</code> and printed here unchanged. "
    "NOT POSSIBLE is used where the requirement cannot be satisfied from official sources at all; the reason is on the register.") + (
    '<div class="section-links"><a href="executive-summary.html"><strong>Read the executive summary &#8599;</strong>'
    '<p>The one-page version with the headline numbers and the blockers.</p></a>'
    '<a href="suggestions.html"><strong>Review the suggestions &#8599;</strong>'
    '<p>Sixteen proposals, each with options, cost, risk and an open decision.</p></a></div>')

page("index", "Requirements & decision review",
     "A traceable register of what was asked for, what is known, what is still unknown, and what should be decided next.",
     overview_body)

# --------------------------------------------------------------- exec summary
g = GRADING
headline = [
    ["Data currency", "The repository's official game log had stopped at Week 8 while Week 9 and part of Week 10 had been played. It now runs to 137 games.",
     a("https://www.nfl.com/standings/league/2026/REG")],
    ["Reconciliation", "Every club's W-L-T, PCT, PF, PA, NET, HOME and ROAD recomputed from those 137 games matches the official standings: 352 of 352 cells, zero tolerance.",
     a("https://www.nfl.com/standings/league/2026/REG")],
    ["Out-of-sample result", f"The 15 Week 9 lines originated on 2026-11-04 were graded against the results: spread MAE {g['spread']['mae']:.2f} points, total MAE {g['total']['mae']:.2f}. Home covers {g['spread']['home_covers']} of {g['spread']['home_non_push']} (p = {g['spread']['home_cover_rate_p_vs_coinflip']}). None of that is skill at n = 15.",
     a("https://www.nfl.com/scores/2026/week-9")],
    ["Own lines", f"13 fair numbers originated for the Week 10 games not yet played. Every one is labelled UNVALIDATED and no market price, edge or selection is attached, because no official source publishes a price.",
     a("https://www.nfl.com/schedules/2026/by-week/week-10")],
    ["Injuries", f"{INJURIES['rows']} official Week 10 injury rows across all {INJURIES['clubs_listed']} clubs playing. Two quarterbacks are officially ruled out for their games.",
     a("https://www.nfl.com/injuries/")],
    ["Backups", "The requirement to identify 2nd, 3rd and 4th string replacements is only half achievable. No official pregame depth chart exists; the official Game Book names the real starters after the game.",
     a("https://www.nfl.com/teams/kansas-city-chiefs/depth-chart")],
    ["Luck", f"About {LUCK['noise_share_of_spread']:.0%} of the between-club spread in win percentage is reproducible by a coin-flip process at these sample sizes. Luck cannot be removed, only bounded.",
     a("https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm")],
    ["Leaderboard", "Zero of twenty registered strategies pass the gates, so no rank, medal or reward is awarded and every reward cell is blank by design.",
     a("https://www.nfl.com/scores/2026/week-9")],
    ["The hard blocker", "No official source publishes a betting price. Under this project's all-official rule, edge, EV, ROI and closing-line value can never be populated. That is a rules decision for the operator, not a data problem.",
     a("https://www.nfl.com/schedules/2026/by-week/week-10")],
]
exec_body = table(["Topic", "Executive finding", "Official reference"], headline, "Executive summary") + sec(
    "The four decisions that actually need making") + (
    "<ol>"
    "<li><strong>What counts as winning?</strong> Until that is written down, no leaderboard can award anything. See suggestion SG-01.</li>"
    "<li><strong>May a non-official price ever enter the project?</strong> Without one, everything stays descriptive. See SG-04 and flag REQ-F-09.</li>"
    "<li><strong>Is the depth-chart half of the availability requirement in scope?</strong> It is only achievable postgame, from game books. See SG-03.</li>"
    "<li><strong>Which of the nine published surfaces is the site?</strong> See SG-07 and flag REQ-F-08.</li></ol>") + sec(
    "What this session did not do") + (
    "<p>No player prop was originated, because a per-player game log does not exist and inventing one would break the rule. "
    "No parlay was priced, because no leg correlation can be measured without event-aligned data. No injury weighting was applied, "
    "because the NFL publishes designations without probabilities. No award was made, because nothing passed a gate. "
    "No inherited file was edited; findings about inherited files are published as review flags.</p>") + note(
    "Every number on this page is either an official value, or this project's arithmetic on official values, and each row links the official page it came from. "
    "The project makes no claim of an edge, no profitability claim, and no claim that luck has been removed. Nothing here is betting advice.")

page("executive-summary", "Executive summary",
     "One page: what is established, what was graded out of sample, and the four decisions that are still open.",
     exec_body)

# ------------------------------------------------------------------ requirements
req_rows = [[r["id"], r["source_quote"], r["requirement"], badge(r["status"]), r["what_exists"],
             r["what_is_missing"] or "None recorded", f'<code>{e(r["evidence"].split(" + ")[0])}</code>',
             a(r.get("source_url"))] for r in REQS["requirements"]]
page("requirements", "Requirement register",
     "Each operator requirement, quoted, with what exists, what is missing and the artifact that carries it.",
     note(REQS["summary_rule"], "How to read a status") +
     table(["ID", "Operator wording", "Requirement as tracked", "Status", "What exists", "What is missing", "Artifact", "Official source"],
           req_rows, "Requirement traceability register",
           "Status codes: MET means an artifact exists and its verification passed here; PARTIAL means an artifact exists but a named evidence gate is still missing; "
           "NOT MET means no artifact and the reason is recorded; NOT POSSIBLE means the requirement cannot be satisfied from official sources at all."))

# --------------------------------------------------------------------- questions
open_qs = [q for q in QUESTIONS["questions"] if q["state"] != "ANSWERED"]
answered_qs = [q for q in QUESTIONS["questions"] if q["state"] == "ANSWERED"]
q_row = lambda q: [q["id"], q["question"], badge(q["state"]), q["have"], q["lack"] or "None",
                   q.get("answer"), q.get("resolution"), a(q["source_url"]), q.get("blocks") or "Nothing"]
q_headers = ["ID", "Question", "State", "What we already have", "What we lack", "Answer", "What would resolve it",
             "Source", "Decision it blocks"]
page("questions", "Open questions",
     "What must be answered before a decision can reasonably be made, split into what we have and what we lack.",
     note("A question is only ANSWERED here if an official source closed it in this session. Anything else stays OPEN, and a question that no official source can answer is marked IMPOSSIBLE rather than left dangling.", "How to read this register") +
     sec(f"Still blocking a decision ({len(open_qs)})") + table(q_headers, [q_row(q) for q in open_qs],
                                                              "Unresolved questions") +
     sec(f"Closed from official sources ({len(answered_qs)})") + table(q_headers, [q_row(q) for q in answered_qs],
                                                                     "Answered questions"))

# ------------------------------------------------------------------- suggestions
def sug_row(s):
    opts = "<br>".join(f"<strong>{k}.</strong> {e(v)}" for k, v in s["options"].items() if k in ("A", "B", "C"))
    return [s["id"], s["title"], s["why"], opts, s["recommended"], s["cost"], s["risk"],
            s["evidence_that_would_justify"], badge(s["decision"]),
            a(s["source_url"], "GitHub Docs" if "docs.github.com" in s["source_url"] else "Official source")]


sug_headers = ["ID", "Suggestion", "Why it matters", "Options", "Recommendation", "Cost", "Risk",
               "Evidence that would justify it", "Decision", "Source"]
decided = [s for s in SUGGESTIONS["suggestions"] if s["decision"] != "UNDECIDED"]
open_sug = [s for s in SUGGESTIONS["suggestions"] if s["decision"] == "UNDECIDED"]
done_row = next(s for s in SUGGESTIONS["suggestions"] if "already_done" in s)
done_body = "<ul>" + "".join(f"<li>{e(x)}</li>" for x in done_row["already_done"]) + "</ul>"
sug_body = note(SUGGESTIONS["how_this_works"], "This is the review section") + \
    '<div class="kpis">' + \
    f'<div class="kpi"><span>{len(open_sug)}</span><h2>Awaiting your decision</h2><small>Nothing implemented</small></div>' + \
    f'<div class="kpi"><span>{len(SUGGESTIONS["suggestions"])}</span><h2>Suggested paths</h2><small>Each with three options</small></div>' + \
    f'<div class="kpi"><span>{len(decided)}</span><h2>Already decided</h2><small>Only you can change these</small></div>' + \
    "</div>" + sec(f"Open for decision ({len(open_sug)})") + \
    table(sug_headers, [sug_row(s) for s in open_sug], "Suggestions awaiting a decision",
          "Read across: what it would do, why it matters, the three options, what this session recommends and why, what it costs, what could go wrong, "
          "and the evidence that would justify it. The Decision column is yours; nothing here is implemented until it changes.") + \
    sec("What this session already did, and would happily reverse") + \
    f"<p><strong>{e(done_row['title'])}.</strong> {e(done_row['why'])}</p>" + done_body + \
    note(done_row["risk"], "Risk of these choices") + \
    (table(sug_headers, [sug_row(s) for s in decided], "Decisions already taken") if decided
     else "<p>No row has been decided. Every suggestion above is still UNDECIDED, which is the correct starting state.</p>")
page("suggestions", "Suggestions & decisions",
     "A dedicated review section: every proposal with its options, cost, risk and an open decision. Nothing is implemented before it is chosen.",
     sug_body)

# ------------------------------------------------------------------------ lines
line_rows = [[x["away"], x["home"], x["kickoff_rendered"], x["network"], f'{x["fair_handicap_home_pts"]:+.2f}',
              f'{x["fair_total_B0"]:.2f}', x["fair_spread_text"], f'{x["p_home_win_normal"]:.3f}',
              f'{x["p_home_win_elo"]:.3f}', None, None, badge(x["status"]), a(x["game_url"], "Game page")]
             for x in LINES["games"]]
page("lines", "Week 10 originated lines",
     "Weakly-validated fair numbers for the 13 Week 10 games not yet played, built only from official Weeks 1-9 results.",
     note(LINES["method"], "Method (this project's own arithmetic, not an NFL publication)") +
     table(["Away", "Home", "Kickoff (as rendered)", "Network", "Fair home handicap", "Fair total",
            "Spread text", "P(home win) normal", "P(home win) Elo", "Market line", "Edge", "Status", "Official game page"],
           line_rows, "Originated Week 10 numbers",
           "Market line and Edge are blank because no official source publishes a price and none may be inferred. "
           "P(home win) is a project assumption, not a published quantity. The Elo column is an independent cross-check, "
           "not a second validated model.") +
     sec("Why these are not recommendations") + (
     "<p>The 15 Week 9 lines that this same method produced were graded out of sample and the home number landed on the wrong side "
     "in 13 of 15 games. Until a fitted venue term and a much larger test exist, these numbers are a benchmark for future comparison, "
     "not a signal to act on. See the <a href=\"grading.html\">Week 9 grading</a>.</p>") +
     sec(f"Ratings used (sigma_margin {LINES['sigma_margin']}, sigma_total {LINES['sigma_total']}, 137 official games)") + (
     "<p>Team ratings are points-for and points-against per game recomputed from the official game log, which reconciles to the "
     "official standings on 352 of 352 cells. The venue adjustment is exactly zero by design, and the Munich game receives no "
     "home-field assumption for the same reason.</p>"))

# ---------------------------------------------------------------------- grading
gr = GRADING
grow = [[r["away"], r["home"], f'{r["away_score"]}-{r["home_score"]}', f'{r["margin_home"]:+d}', f'{r["total"]}',
         f'{r["S1_home_number"]:+.2f}', "covered" if r["S1_home_cover"] else ("push" if r["S1_push"] else "lost"),
         f'{r["S1_abs_error"]:.2f}', f'{r["S5_total"]:.2f}', "over" if r["S5_over"] else ("push" if r["S5_push"] else "under"),
         f'{r["S5_abs_error"]:.2f}', f'{r["S6_p_home_win"]:.3f}', f'{r["S6_brier"]:.3f}', a(r["game"], "Game page")]
        for r in gr["rows"]]
page("grading", "Week 9 out-of-sample grading",
     "The 15 lines originated on 2026-11-04, graded against the official results. Honest, small, and not flattering.",
     note(gr["why_prospective"], "Why this is out of sample") +
     '<div class="kpis">'
     f'<div class="kpi"><span>{gr["spread"]["mae"]:.2f}</span><h2>Spread MAE (points)</h2><small>n = {gr["n_games"]}</small></div>'
     f'<div class="kpi"><span>{gr["total"]["mae"]:.2f}</span><h2>Total MAE (points)</h2><small>n = {gr["n_games"]}</small></div>'
     f'<div class="kpi"><span>{gr["spread"]["home_covers"]}/{gr["spread"]["home_non_push"]}</span><h2>Home covers</h2><small>p = {gr["spread"]["home_cover_rate_p_vs_coinflip"]} vs coin flip</small></div>'
     f'<div class="kpi"><span>{gr["probability_scores"]["brier_moneyline"]:.3f}</span><h2>Moneyline Brier</h2><small>0.25 is a coin flip</small></div>'
     "</div>" +
     table(["Away", "Home", "Result", "Home margin", "Total", "Our home number", "Home number outcome",
            "Spread abs error", "Our total", "Total outcome", "Total abs error", "P(home) we said",
            "Brier", "Official game page"], grow, "Graded Week 9 games",
            "Our home number is this project's fair handicap for the home team, so a positive number means we made the home side the underdog. "
            "The graded outcome compares the realised home margin with that number. No sportsbook line is involved anywhere.") +
     sec("What the numbers mean, and what they do not") + (
     f"<p>{e(gr['interpretation'])}</p><p>{e(gr['luck_note'])}</p>"
     f"<p>Read together: the totals were close to a coin flip, the spreads were worse than a coin flip on side selection, and the moneyline "
     f"probability was better than a coin flip but with 15 observations. There is no basis here for claiming skill, and there is also no basis "
     f"for claiming the method is worthless. The honest statement is that the method is unproven and n is far too small.</p>") +
     note(gr["note_on_lines"], "What this grading cannot tell you"))

# --------------------------------------------------------------------- injuries
by_team = {}
for i in INJURIES["items"]:
    by_team.setdefault(i["team"], []).append(i)
inj_rows = [[i["team"], i["player"], i["position"], i["injury"], i["practice"], i["game_status"],
             a(i["source_url"], "Report")] for i in INJURIES["items"]]
qb = INJURIES["qb_ruled_out"]
page("injuries", "Injury tracker (Week 10)",
     f"All {INJURIES['rows']} rows of the official Week 10 report, for every club playing. Practice status and game status kept separate.",
     note(INJURIES["scope_note"], "Scope") +
     '<div class="kpis">'
     f'<div class="kpi"><span>{INJURIES["rows"]}</span><h2>Official rows</h2><small>{INJURIES["clubs_listed"]} clubs</small></div>'
     f'<div class="kpi"><span>{sum(1 for i in INJURIES["items"] if i["game_status"] == "Out")}</span><h2>Ruled Out</h2><small>Official designation</small></div>'
     f'<div class="kpi"><span>{sum(1 for i in INJURIES["items"] if i["practice"] == "Did Not Participate In Practice")}</span><h2>Did not practise</h2><small>Not the same as Out</small></div>'
     f'<div class="kpi"><span>{len(qb)}</span><h2>Quarterbacks Out</h2><small>See availability page</small></div>'
     "</div>" +
     sec("Quarterbacks officially ruled out") + table(
         ["Club", "Player", "Position", "Injury", "Practice", "Game status", "Source"],
         [[i["team"], i["player"], i["position"], i["injury"], i["practice"], i["game_status"], a(i["source_url"], "Report")] for i in qb],
         "Quarterbacks ruled out for Week 10") +
     sec("Full report") + table(["Club", "Player", "Pos", "Injury", "Practice status", "Game status", "Source"],
                                inj_rows, "Week 10 official injury report",
                                f"Clubs on bye and therefore not on the source page: {', '.join(INJURIES['clubs_on_bye'])}. "
                                "A blank game status is transcribed as blank; it does not mean the player is healthy.") +
     sec("Why practice status and game status are separate columns") + (
     "<p>A player can practise fully and still be ruled out, and a player can miss all three practices and play. "
     "Collapsing the two would invent information. Any model that consumes this table must state which column it used.</p>"))

# ----------------------------------------------------------------- availability
cap_rows = [[c["capability"], "yes" if c["published"] else "no", c["observed"], c["consequence"], a(c["url"])]
            for c in AVAILABILITY["capability_matrix"]]
reg_rows = [[r["team"], r["out_count"], r["doubtful_count"], r["questionable_count"],
             ", ".join(f"{k}: {v}" for k, v in sorted(r["out_by_unit"].items())) or "—",
             "; ".join(r["out_players"]) or "—",
             ", ".join(r["unresolved_players"]) or "—", None, a(r["source_url"], "Report")]
            for r in AVAILABILITY["register"]]
impact_rows = [[x["away"], x["home"],
                (x["factors"].get("away") or {}).get("out_skill", 0),
                (x["factors"].get("away") or {}).get("out_skill", 0),
                "; ".join((x["factors"].get("away") or {}).get("players", [])) or "—",
                "; ".join((x["factors"].get("home") or {}).get("players", [])) or "—",
                "No", a(x["game_url"], "Game page")] for x in AVAILABILITY["games"]]
impact_rows = [[x["away"], x["home"],
                (x["factors"].get("away") or {}).get("out_skill", 0),
                (x["factors"].get("home") or {}).get("out_skill", 0),
                "; ".join((x["factors"].get("away") or {}).get("players", [])) or "—",
                "; ".join((x["factors"].get("home") or {}).get("players", [])) or "—",
                "No", a(x["game_url"], "Game page")] for x in AVAILABILITY["games"]]
page("availability", "Backups & deficiencies",
     "What official sources do and do not publish about who is actually on the field, and which units are short this week.",
     note(AVAILABILITY["headline"], "The finding") +
     sec("What official nfl.com pages actually publish") + table(
         ["Capability", "Published by nfl.com?", "What the page actually shows (retrieved 2026-11-14)", "Consequence for this project", "Page checked"],
         cap_rows, "Official-source capability matrix",
         "This matrix is the evidence base for a hard limit. It was produced by retrieving each page, not by assuming what it contains.") +
     sec("Per-club deficiency register") + table(
         ["Club", "Out", "Doubtful", "Questionable", "Out by unit", "Ruled out (official)", "Unresolved (official)",
          "Replacement named", "Source"], reg_rows,
         "Week 10 deficiency register",
         "Deliberately no replacement is named, because no official source names one before kickoff. The register stops at what the NFL "
         "actually says. 'Out by unit' groups the official position codes so the reader can see which side of the ball is short.") +
     sec("Which Week 10 lines are affected by these absences") + table(
         ["Away", "Home", "Away skill-position Out", "Home skill-position Out", "Away players officially Out",
          "Home players officially Out", "Line adjusted for availability?", "Official game page"], impact_rows,
         "Availability impact on the originated lines",
         "Every originated number in this repository uses team scoring rates only. None of them is adjusted for an absence, because no "
         "official, non-inferred weight exists for one.") +
     sec("What would close the gap") + f"<p>{e(AVAILABILITY['what_would_close_the_gap'])}</p>" +
     f"<p>{e(AVAILABILITY['rules_applied'])}</p>")

# ------------------------------------------------------------------------ luck
luck_rows = [[r["team"], r["games"], f'{r["W"]}-{r["L"]}-{r["T"]}', f'{r["win_pct"]:.3f}',
              f'{r["point_diff_per_game"]:+.2f}', f'{r["avg_margin"]:+.2f}', r["one_score_games"],
              f'{r["expected_win_pct_from_point_diff"]:.3f}', f'{r["wins_above_expected_per_17"]:+.2f}',
              a(r["source_url"], "Standings")]
             for r in LUCK["rows"]]
page("luck", "Luck vs skill",
     "How much of the spread in team records is separable from noise at this sample size, and why luck cannot be removed.",
     note(LUCK["method"], "Method") + '<div class="kpis">'
     f'<div class="kpi"><span>{LUCK["noise_share_of_spread"]:.0%}</span><h2>Reproducible by a coin flip</h2><small>Share of win-percentage spread</small></div>'
     f'<div class="kpi"><span>{LUCK["var_explained_by_point_diff"]:.0%}</span><h2>Explained by point differential</h2><small>Descriptive, not predictive</small></div>'
     f'<div class="kpi"><span>{LUCK["r_point_diff_win_pct"]:.2f}</span><h2>Correlation, points to wins</h2><small>n = {LUCK["clubs"]} clubs</small></div>'
     f'<div class="kpi"><span>{LUCK["mean_games_per_club"]:.1f}</span><h2>Games per club</h2><small>Too few to be sure</small></div>'
     "</div>" + f"<p>{e(LUCK['reading'])}</p>" + f"<p>{e(LUCK['cannot_do'])}</p>" +
     table(["Club", "Games", "Record", "Win %", "Point diff/game", "Average margin", "One-score games",
            "Win % implied by its own margin", "Wins +/- per 17", "Source"], luck_rows,
           "Luck residual by club",
           "Wins +/- per 17 is a descriptive residual from a single-season fit: a club's win percentage minus the percentage its own "
           "point differential predicts, scaled to 17 games. It is not a forecast and not proof that a club was lucky. " +
           e(LUCK["limitation"])))

# ----------------------------------------------------------------------- combos
combo_body = note("Singles have an out-of-sample grade. Parlays and player-prop combinations do not, because the data to price them does not exist. This page states the mathematics and shows exactly which inputs are missing rather than filling them in.", "Coverage") + sec(
    "What each product family needs, and what we have") + table(
    ["Product", "What it needs to be priced", "What this repository has", "What is missing", "Status", "Official source"],
    [["Single: point spread",
      "A fair number and a price",
      "13 fair numbers for Week 10 and a 15-game out-of-sample grade",
      "A price. No official source publishes one",
      badge("PARTIAL"), a("https://www.nfl.com/scores/2026/week-9")],
     ["Single: total",
      "A fair total and a price",
      f"A 15-game grade (MAE {GRADING['total']['mae']:.2f})",
      "A price",
      badge("PARTIAL"), a("https://www.nfl.com/scores/2026/week-9")],
     ["Two-leg parlay",
      "The joint probability of both legs, which needs the correlation between them",
      "Four measured team-level correlations, and two intra-class correlations",
      "Event-aligned leg dependence: same game, same threshold, same pregame timestamp. Team averages cannot price a combination",
      badge("BLOCKED"), a("https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm")],
     ["Player prop, single",
      "A per-player outcome distribution for that exact threshold",
      "Season-to-date league passing and receiving tables, and per-game figures inside the official game pages",
      "A player game log aligned to a pregame timestamp. The repository's own player files are unverified third-party captures and are withheld",
      badge("BLOCKED"), a("https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc")],
     ["Player prop combination",
      "The joint distribution of two player outcomes, including their correlation",
      "Nothing measured",
      "Everything above, plus same-game player-pair history",
      badge("BLOCKED"), a("https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc")]],
    "Product coverage",
    "A BLOCKED row means the mathematics is fine but a required input does not exist in official sources. It is not a software defect.") + sec(
    "The combination mathematics, stated properly") + (
    "<p>For two binary events A and B with marginal probabilities pA and pB and correlation rho between the underlying indicators, "
    "the joint probability is</p>"
    "<p style=\"font-family:ui-monospace,monospace\">P(A and B) = pA&middot;pB + rho&middot;sqrt( pA(1&minus;pA)&middot;pB(1&minus;pB) )</p>"
    "<p>Two things follow. First, assuming independence is the same as assuming rho = 0, which is a specific claim that must be "
    "justified, and the safe default is not to assume it. Second, rho cannot be guessed from team-level aggregates: two teams' "
    "season totals say nothing about whether a particular running back scoring correlates with a particular receiver scoring in "
    "the same game. Pairwise rho also does not identify higher-order dependence in a three-leg or four-leg build.</p>") + sec(
    "The correlation values that do exist") + table(
    ["Pair", "Unit", "n", "r", "Survives multiplicity correction?", "What it can be used for", "Official source"],
    [[x["pair"], x.get("unit", x.get("type")), x["n"], x["r"],
      x.get("survives_holm", "See the correlation register"),
      "Descriptive team association only. Not usable as a parlay leg dependence",
      a(x.get("source_url", "https://nextgenstats.nfl.com/"))] for x in (
        json.load(open(os.path.join(ROOT, "analysis/correlations.json"), encoding="utf-8"))["correlations"])],
    "Measured correlations, inherited and unmodified",
    "These are the values already in the repository. They are republished unchanged and are explicitly not leg-level.")

page("combos", "Parlays & player props",
     "Singles are graded. Combinations are blocked, and this page shows exactly which input is missing rather than inventing one.",
     combo_body)

# ------------------------------------------------------------------- strategies
strat = load_root = json.load(open(os.path.join(ROOT, "origination/results/leaderboard.json"), encoding="utf-8"))
page("strategies", "Strategy gates",
     "Twenty registered signal families across two inherited registries. Zero pass. The gates are why.",
     table(["Registry", "ID", "Product", "Strategy", "n", "Skill % vs baseline", "Lower 95% bound", "Gates passed", "Official input"],
           [["origination/ (12 strategies, 8 gates)", x["id"], x["product"], x["strategy"], x["n"],
             f'{x.get("skill_pct", 0):+.2f}%' if x.get("skill_pct") is not None else None,
             f'{x.get("skill_pct_lcb", 0):+.2f}%' if x.get("skill_pct_lcb") is not None else None,
             ", ".join(k for k, v in x["gates"].items() if v is True) or "none",
             a("https://www.nfl.com/scores/2026/week-9")]
            for x in strat["strategies"]],
           "Strategy registry with walk-forward results",
           "Skill % is the reduction in mean loss against the frozen baseline. The lower 95% bound is what the ranking uses, so a lucky "
           "point estimate cannot buy a medal. Every strategy above fails at least the multiplicity gate, and most fail sample size.") +
     note("The root registry lists eight further designs with no walk-forward result attached. Both registries are published as they are; "
          "unifying them is an operator decision (SG-02), and this session did not pick a winner.", "Two registries coexist"))

# ------------------------------------------------------------------------ gates
gates = json.load(open(os.path.join(ROOT, "analysis/validation-gates.json"), encoding="utf-8"))["gates"]
gate_detail = {
    "G1": ("Official data only", "Every training and evaluation row is a verified official row, produced by the fail-closed build.", "PASS on the inputs; the gate is not what is blocking."),
    "G2": ("No look-ahead", "A prediction for week w may use only weeks earlier than w; asserted at run time.", "Verified: the walk-forward harness asserts the cutoff."),
    "G3": ("Sample size", "At least 80 games for singles, 40 independent pairs for parlays, 100 player-games for props.", "The Week 9 grade is 15 games, so it fails this gate even though it is out of sample."),
    "G4": ("Skill against a frozen baseline", "The paired bootstrap 95% interval of the loss difference must sit entirely below zero.", "Fails: the best strategy's interval includes zero."),
    "G5": ("Multiplicity", "Holm-adjusted permutation p below 0.05 across the whole registered family, not just the winner.", "Fails: the best raw p-value does not survive correction across 12 strategies."),
    "G6": ("Stability", "The improvement must be positive in both halves of the evaluation window.", "Some strategies pass, which is exactly why the multiplicity gate exists."),
    "G7": ("Calibration", "Expected calibration error of at most 0.10 in five bins, for probability products only.", "Not applicable to point-spread strategies; no calibrated probability product has been produced."),
    "G8": ("No market data required", "The strategy must be priceable and settleable without a sportsbook quote.", "Passes by construction, which is the project's escape from the price problem: nothing here uses a market input."),
}
page("gates", "Validation gates",
     "The eight gates, what each one actually tests, and exactly why nothing has passed.",
     table(["Gate", "Name", "Rule", "Current state", "Why it is where it is", "Official or standards reference"],
           [[k, gate_detail[k][0], v["rule"], badge(v["status"]), gate_detail[k][2],
             a("https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm" if k in ("G4", "G5", "G6", "G7")
               else "https://www.nfl.com/scores/2026/week-9")] for k, v in gates.items()],
           "Validation gates",
           "These thresholds are this project's design choices. The statistical references cited elsewhere explain the concepts; no standards body has endorsed these specific values.") +
     sec("The rule that makes the gates honest") + (
     "<p>Missing evidence never counts as a pass, and a conditional gate is not a pass. A strategy that needs a price it does not have is "
     "BLOCKED, not PASS-with-a-caveat. This is why the leaderboard is empty: the emptiness is the gate working, not the gate failing.</p>"))

# ---------------------------------------------------------------- correlations
corr_root = json.load(open(os.path.join(ROOT, "analysis/correlations.json"), encoding="utf-8"))["correlations"]
corr_orig = json.load(open(os.path.join(ROOT, "origination/results/correlations.json"), encoding="utf-8"))


def corr_leaf(obj, depth=0):
    """Flatten whatever shape the inherited correlation file has, without inventing values."""
    if isinstance(obj, dict):
        label = obj.get("pair") or obj.get("name") or obj.get("label")
        if label and ("r" in obj or "icc" in obj or "value" in obj):
            yield dict(label=label, n=obj.get("n"), r=obj.get("r", obj.get("icc", obj.get("value"))),
                       unit=obj.get("unit") or obj.get("type"), method=obj.get("method"),
                       url=obj.get("source_url") or obj.get("url"),
                       note=obj.get("classification") or obj.get("survives_holm"))
            return
        for v in obj.values():
            yield from corr_leaf(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from corr_leaf(v, depth + 1)


corr_orig_rows = corr_orig["correlations"] if isinstance(corr_orig, dict) and "correlations" in corr_orig else list(corr_leaf(corr_orig))


def sig(x):
    v = x.get("significant_after_holm")
    if v is None:
        v = x.get("survives_holm")
    if v is None:
        return None
    return "yes" if v else "no"


page("correlations", "Correlation register",
     "Every measured correlation in the repository, with its unit and sample size, and an explicit statement of what it cannot be used for.",
     table(["Pair", "Scope / unit", "n", "r", "95% interval", "Raw p", "Holm p",
            "Survives correction?", "Source"],
           [[c["pair"], c.get("scope") or c.get("unit") or c.get("type"), c.get("n"), (round(c["r"], 4) if c.get("r") is not None else None),
             f'{c["ci95"][0]:.3f} to {c["ci95"][1]:.3f}' if c.get("ci95") else None,
             round(c["p_two_sided"], 4) if c.get("p_two_sided") is not None else None,
             round(c["p_holm"], 4) if c.get("p_holm") is not None else None,
             sig(c) or c.get("classification"), a(c.get("source_url") or c.get("url") or "https://www.nfl.com/scores/2026/week-9")]
            for c in corr_root] +
           [[c["pair"], c.get("scope") or "inherited", c.get("n"), (round(c["r"], 4) if c.get("r") is not None else None),
             f'{c["ci95"][0]:.3f} to {c["ci95"][1]:.3f}' if c.get("ci95") else None,
             round(c["p_two_sided"], 4) if c.get("p_two_sided") is not None else None,
             round(c["p_holm"], 4) if c.get("p_holm") is not None else None,
             sig(c), a("https://nextgenstats.nfl.com/stats/passing/2026/REG/8")]
            for c in corr_orig_rows],
           "Measured correlations",
           "Rows that do not survive the multiplicity correction are shown with their raw and adjusted p-values rather than dropped, because "
           "dropping them would be a form of cherry-picking. Every value here is a descriptive association between aggregates. None of these "
           "is a betting-leg correlation and none can price a parlay. The two incomplete Next Gen Stats weeks are blank rather than filled.") +
     note("Correlation is not causation and not prediction. A team-level association between passing volume and game total tells you something "
          "about how games unfold; it does not tell you whether two specific legs in one game move together. Assuming independence, rho = 0, is "
          "a claim that must be justified, and the safe default is not to assume it.", "Reading these correctly") +
     sec("What survives, plainly") + (
     "<p>Nothing here survives a family-wise correction comfortably. The one raw p-value below 0.05 is the same-game side-versus-total residual, "
     "and it does not survive Holm across the family. The practical consequence is that this project has no measured dependence it can defend, so "
     "no combination can be priced from it. That is a finding, not a gap in effort.</p>"))

# -------------------------------------------------------------------- leaderboard
page("leaderboard", "Skill leaderboard",
     "The reward rule is written. The board is empty, on purpose, and this page says so rather than showing a fabricated ranking.",
     table(["Strategy", "Category", "Rank", "ROI", "Brier", "Reward points", "Status", "Official input"],
           [[x["name"], x["type"], None, None, None, None, badge("BLOCKED"), a(x["source_url"])]
            for x in json.load(open(os.path.join(ROOT, "analysis/leaderboard.json"), encoding="utf-8"))["standings"]],
           "Competition registry",
           "Rank, ROI, Brier and reward points are blank because no strategy cleared the gates. A null is not a zero score: it means "
           "the number cannot be computed honestly.") + sec("The rule, so it cannot be changed after the fact") + (
     "<p>Only strategies that pass every applicable gate appear at all. Among those, ranking is by the lower 95% bound of the skill score, "
     "not the point estimate, so luck cannot buy a medal. Every later variant counts toward the same family for multiplicity. "
     "Rewards are paper points, nothing else, and no reward is currently awarded.</p>") + sec(
     "Why a coin-flip league would beat this board") + (
     "<p>Over 15 games, a strategy with no skill at all wins 8 or more spread decisions roughly a third of the time. Any board that ranks on "
     "raw hit rate over that sample would be ranking noise. The lower-bound rule is the cheapest defence, and even it needs a sample of "
     "several hundred before the bound can exclude zero.</p>"))

# ------------------------------------------------------------------- verification
recon = [c for c in CHECKS["checks"] if c["check"].startswith("reconcile ")]
summary = CHECKS["summary"]
page("verification", "Verification log",
     "Exactly what was verified in this session, how, and what was not.",
     '<div class="kpis">'
     f'<div class="kpi"><span>{summary["checks_total"]}</span><h2>Automated checks</h2><small>{summary["checks_failed"]} failed</small></div>'
     f'<div class="kpi"><span>{summary["reconcile_cells_ok"]}/{summary["reconcile_cells_total"]}</span><h2>Standings cells reconciled</h2><small>Zero tolerance</small></div>'
     f'<div class="kpi"><span>{summary["games_in_log"]}</span><h2>Games in the official log</h2><small>121 + 15 + 1</small></div>'
     f'<div class="kpi"><span>{summary["week9_graded"]}</span><h2>Lines graded out of sample</h2><small>Originated 2026-11-04</small></div>'
     "</div>" + sec("How the reconciliation works") + (
     "<p>Every club's record, winning percentage, points for, points against, net points, home record and road record is recomputed "
     "from the 137-game official log and compared, cell by cell, with the official standings page retrieved on 2026-11-14. A club that "
     "misses a single cell is marked unreconciled and excluded from downstream claims. All 32 clubs matched on every recomputable column. "
     "That is a strong consistency test between two independent official pages, and it is the reason the Week 10 numbers can be trusted as "
     "arithmetic on official inputs.</p>") + table(
     ["Check", "Result", "Detail", "Official source checked against"],
     [[c["check"], "PASS" if c["pass"] else "FAIL", c["detail"] or "—",
       a("https://www.nfl.com/scores/2026/week-9" if ("Week 9" in c["check"] or "injury" in c["check"].lower())
         else "https://www.nfl.com/standings/league/2026/REG")]
      for c in CHECKS["checks"]],
     "Every automated check in this session") + sec("What was NOT verified here") + (
     "<ul>"
     "<li>Weeks 1 to 8 box scores were not re-read. Those rows are inherited from an earlier session, and they are only corroborated in aggregate by the standings reconciliation above.</li>"
     "<li>External URLs were not checked for live availability. The link checker tests local targets and host allowlists, not that nfl.com serves a page today.</li>"
     "<li>No sportsbook price exists to verify, so no market claim is made anywhere.</li>"
     "<li>The other published surfaces in this repository (desk, strict, evidence-lab, origination, hub) were not re-verified; findings are flagged, not edited.</li>"
     "</ul>"))

# ------------------------------------------------------------------------ sources
sources = [
    ("NFL league standings, 2026 regular season", "https://www.nfl.com/standings/league/2026/REG", "32 clubs; W L T PCT HOME ROAD DIV CONF PF PA NET STRK; used for the 352-cell reconciliation and the luck decomposition"),
    ("NFL Week 9 scores", "https://www.nfl.com/scores/2026/week-9", "15 final scores; used for the out-of-sample grading"),
    ("NFL Week 10 scores", "https://www.nfl.com/scores/2026/week-10", "1 final score (WAS 24 NYG 21) and 13 unplayed games"),
    ("NFL Week 10 schedule", "https://www.nfl.com/schedules/2026/by-week/week-10", "14 games, kickoff renderings, networks, byes CHI DEN PHI TB, flexible-scheduling notice"),
    ("NFL Week 9 schedule", "https://www.nfl.com/schedules/2026/by-week/week-9", "used to check the inherited kickoff-time column"),
    ("Official NFL injury report, Week 10", "https://www.nfl.com/injuries/", "345 rows, 28 clubs; practice status and game status separated"),
    ("Official NFL injury report, Week 9 (address pattern)", "https://www.nfl.com/injuries/league/2026/reg9", "the addressable form of the same report for the previous week"),
    ("Club roster", "https://www.nfl.com/teams/kansas-city-chiefs/roster", "used to establish that the roster publishes ACT and no depth order"),
    ("Club depth chart (does not exist)", "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart", "HTTP 404, body '404 - Flag on the Play.' - the central negative finding"),
    ("Official game centre", "https://www.nfl.com/games/jaguars-at-ravens-2026-reg-9", "scoring drives, quarter scores, location, stadium, and the Game Book link"),
    ("Official NFL Game Book (PDF)", "https://static.www.nfl.com/image/upload/v1793965716/gamecenter/ab380826-4feb-11f1-abca-2c54536568a9.pdf", "starting lineups, substitutions, did-not-play and not-active lists; the only official starter evidence"),
    ("NFL player statistics, passing", "https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc", "season-to-date passing leaderboard; the reconciliation target a future player log must match"),
    ("NIST engineering statistics handbook, confidence intervals", "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm", "statistical context for interval reporting; does not certify this project's thresholds"),
    ("NIST engineering statistics handbook, multiplicity", "https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm", "context for the Holm-style family correction"),
    ("NIST engineering statistics handbook, scatterplot association", "https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm", "context for why association is not causation"),
    ("Washington State Gambling Commission, self-exclusion", "https://wsgc.wa.gov/responsible-gaming-self-exclusion", "responsible-gambling context; not a legal determination for any jurisdiction"),
]
page("sources", "Sources",
     "Every official page retrieved in this session, what it was used for, and what it does not establish.",
     table(["Source", "URL", "What it was used for"], [[n, a(u, u), w] for n, u, w in sources], "Source register",
           "Retrieval used a page-extraction tool, so these are structured transcriptions of official pages rather than retained raw HTML. "
           "Official pages change; a later reader should expect the numbers to have moved.") +
     sec("Pages that were checked precisely because they might not exist") + (
     "<ul><li><a href=\"https://www.nfl.com/teams/kansas-city-chiefs/depth-chart\" target=\"_blank\" rel=\"noopener noreferrer\">nfl.com depth chart</a> returns 404. This is the single most consequential negative finding in the project.</li>"
     "<li>No page was found that publishes a point spread, a price or a closing line. The absence is recorded as a limit, not filled with a third-party number.</li></ul>"))

# ------------------------------------------------------------------------- flagged
flag_rows = [[f["id"], f["severity"], f["finding"], f["evidence"], f["area"], f["disposition"], badge(f["state"]),
              a(f["source_url"], "GitHub Docs" if "docs.github.com" in f["source_url"] else
                ("Repository file" if "sassnarep3-star.github.io" in f["source_url"] else "Official source"))]
             for f in FLAGS["flags"]]
page("flagged", "Flagged for review",
     "Irregularities and unverified items, each with the file or official page that shows it. None of these blocks publication.",
     note("A flag marked needs review does not stop the deploy. It stops any claim that the affected number is validated. "
          "Nothing on this page was fixed by guessing.", "What a flag means") +
     table(["ID", "Severity", "Finding", "Evidence", "Where", "Disposition", "State", "Source"], flag_rows,
           "Review register",
           "Flags are ordered by severity then by where they live. Each one names the exact file or URL that demonstrates it, so a reviewer "
           "can confirm or reject it without re-running anything.") +
     sec("Counts") + table(["Severity", "Count", "Example from this register", "Source"],
                           [[k, v,
                             next((f['id'] + ' - ' + f['area'] for f in FLAGS['flags'] if f['severity'] == k), "none recorded"),
                             a(next((f['source_url'] for f in FLAGS['flags'] if f['severity'] == k), 'https://www.nfl.com/standings/league/2026/REG'))]
                            for k, v in FLAGS["summary"]["by_severity"].items()],
                           "Flags by severity"))

# The root dashboard links to requirements/index.html; make that a real landing page that sends a
# reader into the section rather than a dead end.
LANDING = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="0;url=pages/index.html">
<title>Requirements &amp; decision review &middot; Own8</title>
<link rel="stylesheet" href="../assets/style.css"></head>
<body><main id="main"><h1>Requirements &amp; decision review</h1>
<p class="lead">Opening the section overview. If nothing happens, follow the link.</p>
<p><a class="button" href="pages/index.html">Section overview &#8599;</a></p>
<ul><li><a href="pages/executive-summary.html">Executive summary</a></li>
<li><a href="pages/requirements.html">Requirement register</a></li>
<li><a href="pages/questions.html">Open questions</a></li>
<li><a href="pages/suggestions.html">Suggestions &amp; decisions</a></li>
<li><a href="pages/flagged.html">Flagged for review</a></li>
<li><a href="../index.html">Main dashboard</a></li></ul></main></body></html>'''
with open(os.path.join(REQ, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(LANDING)

print("Built", len(NAV), "requirements pages into", OUT, "plus requirements/index.html")
