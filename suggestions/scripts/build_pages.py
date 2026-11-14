#!/usr/bin/env python3
"""Build the Own8 suggestions + review static pages from structured JSON.

Standard library only. Reads review/results/*.json and suggestions/results/*.json
and writes self-contained HTML that reuses the canonical root assets via relative
links. Every data table row carries an official source link; unverified cells are
rendered blank (with an aria-label) and the row is flagged. No values are inferred.
"""
from __future__ import annotations

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]  # /home/user/Own8
REVIEW_DATA = ROOT / "review" / "results"
SUGG_DATA = ROOT / "suggestions" / "results"
REVIEW_OUT = ROOT / "review"
SUGG_OUT = ROOT / "suggestions"

SEVERITY_BADGE = {"high": "bad", "medium": "warn", "low": "neutral", "info": "neutral"}
STATUS_BADGE = {
    "verified": "good",
    "needs review": "warn",
    "open": "warn",
    "proposed": "neutral",
    "BLOCKED": "bad",
}


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def cell(value, missing_label="Unverified or not available") -> str:
    if value is None or value == "" or value == "UNVERIFIED":
        return f'<td class="missing" aria-label="{esc(missing_label)}"></td>'
    return f"<td>{esc(value)}</td>"


def badge(text, kind="neutral") -> str:
    return f'<span class="badge {kind}">{esc(text)}</span>'


def source_cell(url) -> str:
    if not url:
        return '<td class="missing" aria-label="No source"></td>'
    return (
        '<td><a href="'
        + esc(url)
        + '" target="_blank" rel="noopener noreferrer">Official source &#8599;</a></td>'
    )


def nav(items, current):
    out = []
    for label, href in items:
        cur = ' aria-current="page"' if href == current else ""
        out.append(f'<a{cur} href="{esc(href)}">{esc(label)}</a>')
    return "\n".join(out)


def write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def shell(title, description, ctx, nav_items, current, body) -> str:
    """ctx: dict with assets_rel, root_index, and page-dir-relative base for assets."""
    app_rel = ctx["assets_rel"].replace("style.css", "app.js")
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta name="description" content="{esc(description)}">'
        f"<title>{esc(title)}</title>"
        f'<link rel="stylesheet" href="{ctx["assets_rel"]}">'
        f'<script src="{app_rel}" defer></script>'
        "</head><body>"
        '<a class="skip" href="#main">Skip to content</a>'
        '<aside><a class="brand" href="' + esc(ctx["root_index"]) + '"><span class="brand-mark">8</span> OWN8'
        '<span class="lab">RESEARCH LAB</span></a>'
        '<div class="nav-label">SUGGESTIONS &amp; RE-REVIEW</div>'
        '<nav aria-label="Suggestions navigation">' + nav(nav_items, current) + "</nav>"
        '<div class="aside-foot"><span class="pulse"></span> Official-source re-review<br>'
        "<small>Snapshot · 14 NOV 2026<br>Paper research only</small></div></aside>"
        '<div class="workspace"><header><span>OWN8 / SUGGESTIONS &amp; RE-REVIEW<span class="muted">'
        f" / {esc(title)}</span></span><span class=\"date\">2026 SEASON · WEEK 10</span></header>"
        f'<main id="main">{body}</main>'
        '<footer><span>OWN8 · Evidence before edge.</span>'
        "<span>Snapshot, not live odds. No wagering or cash rewards.</span></footer></div></body></html>"
    )


def table_tools(count, placeholder, label) -> str:
    return (
        '<div class="table-tools"><label>Filter rows <input type="search" placeholder="'
        + esc(placeholder)
        + '" aria-label="'
        + esc(label)
        + '"></label><span class="row-count">'
        + str(count)
        + " rows</span></div>"
    )


# --------------------------------------------------------------------------- #
# review pages
# --------------------------------------------------------------------------- #
def build_review(data):
    # index page context: one level below root
    idx_ctx = {"assets_rel": "../assets/style.css", "root_index": "../index.html"}
    idx_items = [("Independent re-review", "index.html"), ("Repo review", "pages/repo-review.html")]
    # subpage context: two levels below root
    sub_ctx = {"assets_rel": "../../assets/style.css", "root_index": "../../index.html"}
    sub_items = [("Independent re-review", "../index.html"), ("Repo review", "repo-review.html")]

    findings = data["findings"]
    idx_body = (
        '<div class="eyebrow">OWN8 INTELLIGENCE / 2026-11-14</div>'
        "<h1>Independent re-review</h1>"
        '<p class="lead">A line-by-line re-check of the committed canonical workspace against '
        "live official sources, with every finding source-linked.</p>"
        '<div class="kpis">'
        f'<a class="kpi"><span>{len(findings)}</span><h2>Findings</h2><small>RV-01 .. RV-06</small></a>'
        f'<a class="kpi"><span>{len(data["reviewed_files"])}</span><h2>Files reviewed</h2>'
        "<small>Canonical + CI</small></a>"
        '<a class="kpi"><span>32</span><h2>Standings re-captured</h2><small>Official source &#8599;</small></a>'
        f'<a class="kpi"><span>{len(data["official_sources_checked"])}</span><h2>Official sources checked</h2>'
        "<small>Live on 2026-11-14</small></a>"
        "</div>"
        '<div class="section-links"><a href="pages/repo-review.html"><strong>Open the review table &#8599;</strong>'
        "<p>Every finding with its official source link and status.</p></a></div>"
        '<p class="table-note">Empty cells are intentionally blank: unavailable or unverified. '
        "Links on unverified rows are verification targets, not proof.</p>"
    )
    write(REVIEW_OUT / "index.html", shell("Independent re-review", "Own8 independent re-review against official sources.", idx_ctx, idx_items, "index.html", idx_body))

    rows = []
    for f in findings:
        kind = SEVERITY_BADGE.get(f["severity"], "neutral")
        rows.append(
            "<tr>"
            f'<td>{esc(f["id"])}</td>'
            f'<td>{badge(f["severity"], kind)}</td>'
            f"<td>{esc(f['area'])}</td>"
            f"<td>{esc(f['finding'])}</td>"
            f"<td>{esc(f['impact'])}</td>"
            f'<td>{badge(f["status"], STATUS_BADGE.get(f["status"], "neutral"))}</td>'
            + source_cell(f["source_url"])
            + "</tr>"
        )
    body = (
        '<div class="eyebrow">OWN8 INTELLIGENCE / 2026-11-14</div>'
        "<h1>Repository review</h1>"
        '<p class="lead">Line-by-line re-review findings. Each row links the official source '
        "that was re-fetched on 2026-11-14.</p>"
        + table_tools(len(findings), "Search findings…", "Filter review findings")
        + '<div class="table-wrap"><table><caption>Review findings</caption>'
        "<thead><tr><th scope=\"col\">ID</th><th scope=\"col\">Severity</th><th scope=\"col\">Area</th>"
        "<th scope=\"col\">Finding</th><th scope=\"col\">Impact</th><th scope=\"col\">Status</th>"
        "<th scope=\"col\">Source</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></div>"
        '<p class="table-note">Empty cells are intentionally blank: unavailable or unverified. '
        "Links on unverified rows are verification targets, not proof.</p>"
        "<h2>Official sources checked</h2>"
        + table_tools(len(data["official_sources_checked"]), "Search sources…", "Filter official sources")
        + '<div class="table-wrap"><table><caption>Official sources re-checked</caption>'
        "<thead><tr><th scope=\"col\">ID</th><th scope=\"col\">Source</th><th scope=\"col\">URL</th>"
        "<th scope=\"col\">Checked</th><th scope=\"col\">Result</th></tr></thead><tbody>"
        + "\n".join(
            "<tr>"
            f'<td>{esc(s["id"])}</td><td>{esc(s["label"])}</td>'
            f'<td><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["url"])}</a></td>'
            f'<td>{esc(s["checked_at"])}</td><td>{esc(s["result"])}</td></tr>'
            for s in data["official_sources_checked"]
        )
        + "</tbody></table></div>"
        "<h2>Files reviewed</h2>"
        + table_tools(len(data["reviewed_files"]), "Search files…", "Filter reviewed files")
        + '<div class="table-wrap"><table><caption>Files reviewed</caption>'
        "<thead><tr><th scope=\"col\">Path</th><th scope=\"col\">Check performed</th></tr></thead><tbody>"
        + "\n".join(
            f"<tr><td><code>{esc(r['path'])}</code></td><td>{esc(r['check'])}</td></tr>"
            for r in data["reviewed_files"]
        )
        + "</tbody></table></div>"
    )
    write(REVIEW_OUT / "pages" / "repo-review.html", shell("Repository review", "Own8 repository line-by-line review findings.", sub_ctx, sub_items, "repo-review.html", body))


# --------------------------------------------------------------------------- #
# suggestions pages
# --------------------------------------------------------------------------- #
def build_suggestions(sugg, dq, li, exec_sum):
    idx_ctx = {"assets_rel": "../assets/style.css", "root_index": "../index.html"}
    sub_ctx = {"assets_rel": "../../assets/style.css", "root_index": "../../index.html"}

    suggestions = sugg["suggestions"]
    idx_items = [
        ("Suggestions", "index.html"),
        ("Improvement suggestions", "pages/suggestions.html"),
        ("Decision questions", "pages/decision-questions.html"),
        ("Lineup impact", "pages/lineup-impact.html"),
        ("Executive summary", "pages/executive-summary.html"),
    ]
    sub_items = [
        ("Suggestions", "../index.html"),
        ("Improvement suggestions", "suggestions.html"),
        ("Decision questions", "decision-questions.html"),
        ("Lineup impact", "lineup-impact.html"),
        ("Executive summary", "executive-summary.html"),
    ]

    idx_body = (
        '<div class="eyebrow">OWN8 INTELLIGENCE / 2026-11-14</div>'
        "<h1>Suggestions &amp; decision readiness</h1>"
        '<p class="lead">A dedicated workspace to review improvement suggestions and the '
        "information needed before any decision — choose the best path before implementing.</p>"
        '<div class="kpis">'
        f'<a class="kpi"><span>{len(suggestions)}</span><h2>Suggestions</h2><small>Proposed, reviewable</small></a>'
        f'<a class="kpi"><span>{len(dq["questions"])}</span><h2>Decision questions</h2>'
        "<small>What we have / lack</small></a>"
        f'<a class="kpi"><span>{len(li["signals"])}</span><h2>Lineup signals</h2>'
        "<small>Injury / backups</small></a>"
        f'<a class="kpi"><span>{len(exec_sum["sections"])}</span><h2>Summary sections</h2>'
        "<small>Important details</small></a>"
        "</div>"
        '<div class="section-links">'
        '<a href="pages/suggestions.html"><strong>Review suggestions &#8599;</strong>'
        "<p>Prioritized improvements for the site and decision-making.</p></a>"
        '<a href="pages/decision-questions.html"><strong>Open decision questions &#8599;</strong>'
        "<p>The information we have and lack before any decision.</p></a>"
        '<a href="pages/executive-summary.html"><strong>Read the executive summary &#8599;</strong>'
        "<p>Important details in one place.</p></a>"
        "</div>"
        '<p class="table-note">Suggestions are project-design proposals, not verified external facts. '
        "Verified facts carry official source links; missing values are blank and flagged.</p>"
    )
    write(SUGG_OUT / "index.html", shell("Suggestions & decision readiness", "Own8 suggestions and decision-readiness workspace.", idx_ctx, idx_items, "index.html", idx_body))

    # suggestions.html
    rows = []
    for s in suggestions:
        prio_kind = "good" if s["priority"] == "P1" else ("warn" if s["priority"] == "P2" else "neutral")
        rows.append(
            "<tr>"
            f'<td>{esc(s["id"])}</td><td>{badge(s["priority"], prio_kind)}</td>'
            f"<td>{esc(s['area'])}</td><td>{esc(s['suggestion'])}</td>"
            f"<td>{esc(s['why'])}</td>"
            f"<td><code>{esc(s['files_scope'])}</code></td>"
            f"<td>{esc(s['verification_required'])}</td>"
            f'<td>{badge(s["status"], "neutral")}</td>'
            + source_cell(s["source_url"])
            + "</tr>"
        )
    body = (
        '<div class="eyebrow">OWN8 INTELLIGENCE / 2026-11-14</div>'
        "<h1>Improvement suggestions</h1>"
        '<p class="lead">Prioritized suggestions to improve the site and decision-making. '
        "Each is a proposal for a reviewer to accept or reject before implementation.</p>"
        + table_tools(len(suggestions), "Search suggestions…", "Filter suggestions")
        + '<div class="table-wrap"><table><caption>Suggestions register</caption>'
        "<thead><tr><th scope=\"col\">ID</th><th scope=\"col\">Priority</th><th scope=\"col\">Area</th>"
        "<th scope=\"col\">Suggestion</th><th scope=\"col\">Why it matters</th><th scope=\"col\">Scope</th>"
        "<th scope=\"col\">Verification required</th><th scope=\"col\">Status</th><th scope=\"col\">Source</th>"
        "</tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></div>"
        '<p class="table-note">Suggestions are project-design proposals; the linked source is the '
        "official reference or methodology the proposal relies on. Status starts at 'proposed'.</p>"
    )
    write(SUGG_OUT / "pages" / "suggestions.html", shell("Improvement suggestions", "Own8 improvement suggestions register.", sub_ctx, sub_items, "suggestions.html", body))

    # decision-questions.html
    rows = []
    for q in dq["questions"]:
        prio_kind = "good" if q["priority"] == "P1" else ("warn" if q["priority"] == "P2" else "neutral")
        rows.append(
            "<tr>"
            f'<td>{esc(q["id"])}</td><td>{badge(q["priority"], prio_kind)}</td>'
            f"<td>{esc(q['question'])}</td>"
            f"<td>{esc(q['we_have'])}</td>"
            f"<td>{esc(q['we_lack'])}</td>"
            f"<td>{esc(q['why_matters'])}</td>"
            f"<td>{esc(q['discovery_action'])}</td>"
            f'<td>{badge(q["status"], "warn")}</td>'
            + source_cell(q["source_url"])
            + "</tr>"
        )
    body = (
        '<div class="eyebrow">OWN8 INTELLIGENCE / 2026-11-14</div>'
        "<h1>Decision-readiness questions</h1>"
        '<p class="lead">The questions that must be answered, and the information we already have '
        "and lack, before any decision can be reasonably made.</p>"
        + table_tools(len(dq["questions"]), "Search questions…", "Filter decision questions")
        + '<div class="table-wrap"><table><caption>Decision-readiness register</caption>'
        "<thead><tr><th scope=\"col\">ID</th><th scope=\"col\">Priority</th><th scope=\"col\">Question</th>"
        "<th scope=\"col\">What we have</th><th scope=\"col\">What we lack</th><th scope=\"col\">Why it matters</th>"
        "<th scope=\"col\">Suggested discovery action</th><th scope=\"col\">Status</th><th scope=\"col\">Source</th>"
        "</tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></div>"
        '<p class="table-note">' + esc(dq["note"]) + "</p>"
    )
    write(SUGG_OUT / "pages" / "decision-questions.html", shell("Decision questions", "Own8 decision-readiness questions and answers.", sub_ctx, sub_items, "decision-questions.html", body))

    # lineup-impact.html
    rows = []
    for s in li["signals"]:
        status_kind = STATUS_BADGE.get(s["status"].split(" ")[0], "neutral")
        rows.append(
            "<tr>"
            f'<td>{esc(s["id"])}</td><td>{esc(s["signal"])}</td>'
            f"<td>{esc(s['what_to_capture'])}</td>"
            + cell(s["verified_example"])
            + cell(s["string_designation"])
            + f'<td>{badge(s["status"], status_kind)}</td>'
            + source_cell(s["source_url"])
            + "</tr>"
        )
    body = (
        '<div class="eyebrow">OWN8 INTELLIGENCE / 2026-11-14</div>'
        "<h1>Lineup-impact signals</h1>"
        '<p class="lead">Tracking injuries and deficiencies when 2nd/3rd/4th-string backups replace '
        "starters on offense and defense. Verified values are transcribed from the official report; "
        "the 'string' designation is left blank until an official roster/depth-chart source confirms it.</p>"
        + table_tools(len(li["signals"]), "Search signals…", "Filter lineup signals")
        + '<div class="table-wrap"><table><caption>Lineup-impact framework</caption>'
        "<thead><tr><th scope=\"col\">ID</th><th scope=\"col\">Signal</th><th scope=\"col\">What to capture</th>"
        "<th scope=\"col\">Verified example</th><th scope=\"col\">String</th><th scope=\"col\">Status</th>"
        "<th scope=\"col\">Source</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table></div>"
        '<p class="table-note">' + esc(li["note"]) + "</p>"
    )
    write(SUGG_OUT / "pages" / "lineup-impact.html", shell("Lineup impact", "Own8 injury and backup-deficiency lineup-impact signals.", sub_ctx, sub_items, "lineup-impact.html", body))

    # executive-summary.html
    sec_blocks = []
    for sec in exec_sum["sections"]:
        pts = "\n".join(f"<li>{esc(p)}</li>" for p in sec["points"])
        sec_blocks.append(
            "<section><h2>"
            + esc(sec["heading"])
            + '</h2><ul>'
            + pts
            + "</ul>"
            + source_cell(sec["source_url"]).replace("<td>", '<p class="src">').replace("</td>", "</p>")
            + "</section>"
        )
    body = (
        '<div class="eyebrow">OWN8 INTELLIGENCE / 2026-11-14</div>'
        "<h1>Executive summary</h1>"
        '<p class="lead">' + esc(exec_sum["statement"]) + "</p>"
        + "\n".join(sec_blocks)
        + '<p class="table-note">Verified statements carry official source links; derived values are '
        "labeled as project calculations; missing values are blank and flagged, never inferred.</p>"
    )
    write(SUGG_OUT / "pages" / "executive-summary.html", shell("Executive summary", "Own8 executive summary of important details.", sub_ctx, sub_items, "executive-summary.html", body))


def main():
    review = json.loads((REVIEW_DATA / "review-findings.json").read_text(encoding="utf-8"))
    sugg = json.loads((SUGG_DATA / "suggestions.json").read_text(encoding="utf-8"))
    dq = json.loads((SUGG_DATA / "decision-questions.json").read_text(encoding="utf-8"))
    li = json.loads((SUGG_DATA / "lineup-impact.json").read_text(encoding="utf-8"))
    exec_sum = json.loads((SUGG_DATA / "executive-summary.json").read_text(encoding="utf-8"))
    build_review(review)
    build_suggestions(sugg, dq, li, exec_sum)
    print("Built review + suggestions pages.")


if __name__ == "__main__":
    main()
