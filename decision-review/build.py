#!/usr/bin/env python3
"""Build the isolated, official-source-linked decision-review dashboard."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPO = ROOT.parent


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


sources_data = read("sources.json")
SOURCES = {source["id"]: source for source in sources_data["sources"]}
ALLOWLIST = set(sources_data["official_host_allowlist"])
QUESTIONS = read("questions.json")["questions"]
SUGGESTIONS = read("suggestions.json")
AVAILABILITY = read("availability.json")
FLAGS = read("flags.json")["flags"]


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def official_link(source_id: str) -> str:
    source = SOURCES[source_id]
    host = urlparse(source["url"]).hostname or ""
    allowed = any(host == domain or host.endswith("." + domain) for domain in ALLOWLIST)
    if source.get("publisher") is None or not allowed:
        raise ValueError(f"Source is not on the official host allowlist: {source_id} {source.get('url')}")
    return (
        f'<a class="source-link" href="{esc(source["url"])}" target="_blank" '
        f'rel="noopener noreferrer">{esc(source["label"])} ↗</a>'
    )


def source_cell(source_ids) -> str:
    if not source_ids:
        raise ValueError("Every displayed data row must cite at least one official source")
    return "<div class=\"source-stack\">" + "".join(official_link(sid) for sid in source_ids) + "</div>"


def repo_cell(paths) -> str:
    if not paths:
        return "<span class=\"muted\">—</span>"
    links = []
    for path in paths:
        clean = str(path).lstrip("/")
        url = f"https://github.com/sassnarep3-star/Own8/blob/main/{clean}"
        links.append(f'<a class="repo-link" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(path)} ↗</a>')
    return "<div class=\"source-stack\">" + "".join(links) + "</div>"


def badge(status: str) -> str:
    upper = status.upper()
    cls = "good" if upper.startswith("PASS") or upper.startswith("VERIFIED") else "warn" if any(x in upper for x in ("BLOCKED", "UNKNOWN", "UNVERIFIED", "MISMATCH", "HOLD", "PARTIAL", "NEEDS REVIEW")) else "neutral"
    return f'<span class="badge {cls}">{esc(status)}</span>'


def table(headers, rows, caption: str, row_fn) -> str:
    if not rows:
        return f'<p class="empty">No rows are available.</p>'
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join("<tr>" + row_fn(row) + "</tr>" for row in rows)
    return (
        '<div class="table-tools"><label>Filter rows '
        f'<input type="search" placeholder="Search this table…" aria-label="Filter {esc(caption)}"></label>'
        f'<span class="row-count">{len(rows)} rows</span></div>'
        f'<div class="table-wrap"><table><caption>{esc(caption)}</caption>'
        f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
        '<p class="table-note">Every row links to an official publisher or regulator page. A reference is context or a verification target unless the exact field and retrieval scope are explicitly marked as checked. Unknown values stay blank.</p>'
    )


def td(value, cls: str = "") -> str:
    class_attr = f' class="{esc(cls)}"' if cls else ""
    if value is None or value == "":
        return f'<td{class_attr} aria-label="Not verified or not available"></td>'
    return f"<td{class_attr}>{value}</td>"


def wrap(active: str, title: str, description: str, body: str) -> str:
    nav_items = [
        ("index", "Overview", "01"),
        ("executive-summary", "Executive summary", "02"),
        ("requirements", "Questions & requirements", "03"),
        ("suggestions", "Suggestions & paths", "04"),
        ("availability", "Injury & depth schema", "05"),
        ("sources", "Official sources", "06"),
        ("flagged", "Flagged for Review", "07"),
    ]
    nav = "".join(
        f'<a {"aria-current=page" if key == active else ""} href="{key + ".html" if key != "index" else "index.html"}">'
        f'<span>{number}</span>{esc(label)}</a>'
        for key, label, number in nav_items
    )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <title>{esc(title)} · Own8 Decision Review</title>
  <link rel="stylesheet" href="assets/style.css">
  <script src="assets/app.js" defer></script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <aside class="sidebar">
    <a class="brand" href="index.html"><span class="brand-mark">8</span><span>OWN8<small>DECISION REVIEW</small></span></a>
    <p class="nav-label">REVIEW WORKSPACE</p>
    <nav aria-label="Decision review navigation">{nav}</nav>
    <div class="sidebar-foot"><span class="dot"></span> Research-only review<br><small>Reviewed 14 Nov 2026<br>No live signals or rewards</small></div>
  </aside>
  <div class="workspace">
    <header><span>OWN8 / DECISION SUPPORT <span class="muted">/ {esc(title)}</span></span><a href="../index.html">Main NFL dashboard ↗</a></header>
    <main id="main">
      <div class="eyebrow">REVIEWED 2026-11-14 · PROJECT SNAPSHOT 2026-11-04</div>
      <h1>{esc(title)}</h1>
      <p class="lead">{esc(description)}</p>
      <div class="notice"><strong>Evidence boundary</strong><p>This is a decision and research review, not a betting recommendation. Official links show source context; they do not independently prove every project claim. Current unknowns are left blank and flagged.</p></div>
      {body}
    </main>
    <footer><span>OWN8 · Evidence before edge.</span><span>Research only · no wagers, live odds, cash prizes, or luck-free claims.</span></footer>
  </div>
</body>
</html>'''


def render_question(row) -> str:
    return "".join([
        td(esc(row["id"])),
        td(esc(row["category"])),
        td(esc(row["question"])),
        td(esc(row["known_answer"])),
        td(esc(row["missing_information"])),
        td(esc(row["suggested_discovery"])),
        td(esc(row["decision_gate"])),
        td(badge(row["status"])),
        td(repo_cell(row.get("repo_evidence", []))),
        td(source_cell(row["source_ids"])),
    ])


def render_suggestion(row) -> str:
    return "".join([
        td(esc(row["id"])),
        td(esc(row["priority"])),
        td(esc(row["title"])),
        td(esc(row["problem"])),
        td(esc(row["proposal"])),
        td(esc(row["discovery_steps"])),
        td(esc(row["acceptance_test"])),
        td(badge(row["status"])),
        td(source_cell(row["source_ids"])),
    ])


def render_path(row) -> str:
    return "".join([
        td(esc(row["id"])),
        td(esc(row["title"])),
        td(badge(row["status"])),
        td(esc(row["description"])),
        td(esc(row["benefit"])),
        td(esc(row["tradeoff"])),
        td(esc(row["next_action"])),
        td(esc(row["acceptance_criteria"])),
        td(source_cell(row["source_ids"])),
    ])


def render_group(row) -> str:
    return "".join([
        td(esc(row["group"])),
        td(esc(row["project_scope"])),
        td("Proposed Own8 coverage group; no player assignment."),
        td(source_cell(row["source_ids"])),
    ])


def render_availability_field(row) -> str:
    return "".join([
        td(f'<code>{esc(row["field"])}</code>'),
        td(esc(row["purpose"])),
        td(esc(row["verification_rule"])),
        td(esc(row["current_value"]) if row["current_value"] is not None else ""),
        td(badge(row["status"])),
        td(source_cell(row["source_ids"])),
    ])


def render_flag(row) -> str:
    return "".join([
        td(esc(row["id"])),
        td(esc(row["priority"])),
        td(esc(row["issue"])),
        td(esc(row["finding"])),
        td(esc(row["safe_handling"])),
        td(repo_cell(row.get("repo_evidence", []))),
        td(source_cell(row["source_ids"])),
    ])


def render_source(row) -> str:
    return "".join([
        td(esc(row["publisher"])),
        td(official_link(row["id"])),
        td(esc(row["checked_at"])),
        td(badge(row["retrieval_status"])),
        td(esc(row["observed"])),
        td(esc(row["scope_limit"])),
    ])


def build():
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "index.html").write_text(build_index(), encoding="utf-8")

    q_headers = ["ID", "Category", "Decision question", "Known answer from repo/review", "Missing information", "Suggested discovery", "Decision gate", "Status", "Project evidence", "Official source"]
    req_body = (
        '<p class="callout">The “known answer” column describes what was found in the current repository and bounded official-source retrieval. It is not a blanket audit of all legacy files. Cells about unavailable numeric, player, price, or depth values remain empty.</p>'
        + table(q_headers, QUESTIONS, "Decision questions and full requirements register", render_question)
    )
    write_page("requirements", "Questions & requirements", "The information and answers required before a decision can reasonably be made.", req_body)

    path_headers = ["Path", "Option", "Status", "Description", "Benefit", "Trade-off / prerequisite", "Next action", "Acceptance criteria", "Official source"]
    sug_headers = ["ID", "Priority", "Suggestion", "Problem addressed", "Proposed change", "How to discover missing information", "Acceptance test", "Status", "Official source"]
    paths_body = (
        '<h2>Choose the sequence, not an unsupported signal</h2>'
        '<p class="callout"><strong>Provisional recommendation from current evidence:</strong> use Path A now; revisit Path B only after all applicable gates pass; keep Path C on hold. None is user-approved or launched in this review.</p>'
        + table(path_headers, SUGGESTIONS["paths"], "Decision paths for review", render_path)
        + '<h2>Actionable suggestion backlog</h2>'
        + table(sug_headers, SUGGESTIONS["recommendations"], "Prioritized suggestions and measurable acceptance tests", render_suggestion)
    )
    write_page("suggestions", "Suggestions & paths", "A dedicated section to review recommendations, compare paths, and select a gated next step before implementation.", paths_body)

    availability_body = (
        '<div class="kpis">'
        '<div class="kpi"><span>Current Week 11 player rows</span><strong>—</strong><small>Not verified; Week 11 request returned Week 10 content.</small></div>'
        '<div class="kpi"><span>Verified depth tiers</span><strong>—</strong><small>No starter/2nd/3rd/4th-string mapping captured.</small></div>'
        '<div class="kpi"><span>Replacement impact estimates</span><strong>—</strong><small>No estimate or uncertainty computed.</small></div>'
        '</div>'
        f'<p class="callout"><strong>{esc(AVAILABILITY["coverage_status"])}</strong><br>{esc(AVAILABILITY["schema_note"])}</p>'
        '<h2>Offense coverage groups</h2>'
        + table(["Own8 group", "Proposed scope (preserve source position)", "Current coverage", "Official source"], AVAILABILITY["offensive_groups"], "Offensive role groups to monitor", render_group)
        + '<h2>Defense coverage groups</h2>'
        + table(["Own8 group", "Proposed scope (preserve source position)", "Current coverage", "Official source"], AVAILABILITY["defensive_groups"], "Defensive role groups to monitor", render_group)
        + '<h2>Required source-backed fields</h2>'
        + table(["Field", "Purpose", "Verification rule", "Current value", "Status", "Official source"], AVAILABILITY["fields"], "Availability, role, and replacement evidence schema", render_availability_field)
        + '<h2>Role-tier policy</h2>'
        + '<p>Own8 schema labels: <strong>Starter / 2nd / 3rd / 4th / Unknown</strong>. These are not attributed to any current player. Require a dated official depth chart or explicit lineup source for a non-blank tier; otherwise use Unknown. An injury list or roster order is not a replacement map.</p>'
    )
    write_page("availability", "Injury & depth schema", "A source-first design for injuries, lineups, starter and backup tiers, and replacement-impact evidence on both sides of the ball.", availability_body)

    flag_body = (
        f'<p class="callout">{esc(read("flags.json")["status_label"])}</p>'
        + table(["ID", "Priority", "Issue", "Observed finding", "Safe handling", "Project evidence", "Official source"], FLAGS, "Decision-review flags", render_flag)
    )
    write_page("flagged", "Flagged for Review", "Bounded source irregularities and evidence gaps. Missing evidence blocks affected signals; it does not block publication of the review.", flag_body)

    source_body = (
        f'<p class="callout">{esc(sources_data["method"])}</p>'
        + table(["Publisher", "Official page", "Checked", "Retrieval status", "What was observed", "Scope limit"], sources_data["sources"], "Official source register", render_source)
    )
    write_page("sources", "Official sources", "Primary source pages checked for context and exact evidence boundaries.", source_body)

    summary_body = build_summary()
    write_page("executive-summary", "Executive summary", "Decision brief · current state, unresolved inputs, safe next path, and release boundary.", summary_body)
    print(f"Built decision-review dashboard: {len(QUESTIONS)} questions, {len(SUGGESTIONS['recommendations'])} suggestions, {len(AVAILABILITY['fields'])} availability fields, {len(FLAGS)} flags, {len(sources_data['sources'])} official sources.")


def write_page(slug, title, description, body):
    (ROOT / f"{slug}.html").write_text(wrap(slug, title, description, body), encoding="utf-8")


def build_index():
    snapshot = f'''<div class="kpis">
      <div class="kpi"><span>Decision questions</span><strong>{len(QUESTIONS)}</strong><small>Known answers, unknowns, and gates</small></div>
      <div class="kpi"><span>Prioritized suggestions</span><strong>{len(SUGGESTIONS['recommendations'])}</strong><small>Each with a discovery step and acceptance test</small></div>
      <div class="kpi"><span>Eligible strategies</span><strong>0</strong><small>Canonical registry: all eight remain blocked</small></div>
      <div class="kpi"><span>Current player status rows</span><strong>—</strong><small>Week 11 not verified in this retrieval</small></div>
    </div>'''
    findings = [
        {"area": "Snapshot freshness", "answer": "Project capture is dated 2026-11-04; this review is dated 2026-11-14.", "status": "STALE FOR CURRENT SIGNALS", "source_ids": ["nfl-schedule-week11", "nfl-injuries-week11-request"]},
        {"area": "Lines and prices", "answer": "B0 is a derived scoring benchmark. Canonical market lines, prices, edges and probabilities are null.", "status": "BLOCKED", "source_ids": ["nfl-standings", "nfl-scores-week10"]},
        {"area": "Injuries and replacements", "answer": "The requested Week 11 injury page returned Week 10 content; no current depth/replacement mapping is verified.", "status": "UNVERIFIED", "source_ids": ["nfl-injuries-week11-request", "nfl-team-directory"]},
        {"area": "Skill / rewards", "answer": "Zero strategies qualify; no rank or reward is awarded. Luck cannot be eliminated.", "status": "BLOCKED", "source_ids": ["nist-confidence-intervals", "nist-multiple-comparisons"]}
    ]
    def row(r):
        return td(esc(r["area"])) + td(esc(r["answer"])) + td(badge(r["status"])) + td(source_cell(r["source_ids"]))
    body = (
        '<div class="hero"><div><span class="pill">EVIDENCE BEFORE EDGE</span><h2>Make the next decision visible.</h2>'
        '<p>This workspace organizes what is known, what is missing, and what must be discovered before any line, lineup adjustment, competition rank, or reward can be defended.</p>'
        '<a class="button" href="suggestions.html">Review paths & suggestions ↗</a></div>'
        '<div class="hero-stat"><span>PROVISIONAL NEXT STEP</span><strong>A<span> / C</span></strong><p>Research-only now.<br>Real-money/value rewards held.</p><small>No user decision is recorded.</small></div></div>'
        + snapshot
        + '<h2>Decision snapshot</h2>'
        + table(["Area", "Current answer", "Status", "Official reference"], findings, "Decision snapshot", row)
        + '<h2>Start here</h2><div class="link-cards">'
        '<a href="requirements.html"><strong>Questions & requirements ↗</strong><span>Clear question, current answer, missing input, discovery action, decision gate.</span></a>'
        '<a href="suggestions.html"><strong>Suggestions & paths ↗</strong><span>Compare evidence-first, shadow-competition, and held product paths.</span></a>'
        '<a href="availability.html"><strong>Injury & depth schema ↗</strong><span>Plan source-backed offense/defense starter and replacement coverage without guessing.</span></a>'
        '<a href="flagged.html"><strong>Flagged for Review ↗</strong><span>Review the Week 11 source mismatch and other blockers.</span></a></div>'
        '<p class="callout">Recommended sequence is provisional: keep Path A research-only now; consider Path B only after all applicable evidence and skill gates pass; keep Path C held for separate legal/regulatory review. The suggestions are not user-approved implementation.</p>'
    )
    return wrap("index", "Decision Review", "A source-linked decision workspace for requirements, unknowns, recommendations, and review flags.", body)


def build_summary():
    rows = [
        {"topic": "Verified foundation", "answer": "Bounded audit dated 2026-11-04; not an exhaustive verification of every inherited file.", "status": "PARTIAL", "source_ids": ["nfl-standings", "nfl-schedule-week11"]},
        {"topic": "Own lines", "answer": "B0 is a derived PF/PA scoring benchmark; no calibrated probability, market price, or current roster adjustment.", "status": "UNVALIDATED", "source_ids": ["nfl-standings", "nfl-scores-week10"]},
        {"topic": "Availability", "answer": "Week 11 injury request returned Week 10 content; no current player status or backup tier entered.", "status": "UNVERIFIED", "source_ids": ["nfl-injuries-week11-request", "nfl-team-directory"]},
        {"topic": "Correlation", "answer": "Three descriptive team-level values; listed bet-event coefficients and counts are null.", "status": "BLOCKED", "source_ids": ["nfl-scores-week10", "nist-association"]},
        {"topic": "Leaderboard", "answer": "Eight designs; zero eligible strategies, no verified ranking, no reward awarded.", "status": "BLOCKED", "source_ids": ["nist-confidence-intervals", "nist-multiple-comparisons"]},
        {"topic": "Prizes / wagering", "answer": "No project-specific legal determination. Keep research-only and obtain qualified review before any value or wagering feature.", "status": "HOLD", "source_ids": ["gra-class-licences", "gra-betting-faq"]}
    ]
    def row(r):
        return td(esc(r["topic"])) + td(esc(r["answer"])) + td(badge(r["status"])) + td(source_cell(r["source_ids"]))
    return (
        '<h2>Executive findings</h2>'
        + table(["Topic", "Current answer", "Status", "Official context"], rows, "Executive findings", row)
        + '<h2>Recommended decision sequence</h2>'
        '<ol class="steps"><li><strong>Now:</strong> Path A — preserve research-only publication and source/freshness checks.</li>'
        '<li><strong>Later, only after gates:</strong> Path B — immutable paper forecasts and a shadow leaderboard with no valued prizes.</li>'
        '<li><strong>Hold:</strong> Path C — no real-money wagering or value rewards without separate product-specific legal/regulatory clearance.</li></ol>'
        '<p class="callout">A model cannot remove luck. No strategy is qualified, no live line/price is verified, and this module does not give legal advice or a betting recommendation.</p>'
        '<p><a class="button" href="suggestions.html">Read the options and acceptance tests ↗</a></p>'
    )


if __name__ == "__main__":
    build()
