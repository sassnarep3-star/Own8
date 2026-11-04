#!/usr/bin/env python3
"""Build the Own8 static dashboard from data/results/*.json + docs/*.md.

Output: site/  (deployed to GitHub Pages by .github/workflows/pages.yml).
Every data table row carries a Source link. OFFICIAL rows link to NFL sources;
DERIVED rows link to the primary dataset + methodology and are labeled DERIVED;
market data is labeled PRIMARY (non-NFL) and flagged. No value is inferred.
"""
from __future__ import annotations

import html
import json
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / "data" / "results"
SITE = ROOT / "site"
SITE.mkdir(parents=True, exist_ok=True)
(SITE / "assets").mkdir(exist_ok=True)

DATASET_LINKS = {
    "D1": ("LeeSharpe/nfldata games.csv", "https://github.com/LeeSharpe/nfldata/blob/master/data/games.csv"),
    "D2": ("mrcaseb/nfl-data odds", "https://github.com/mrcaseb/nfl-data/blob/master/data/nfl_lines_odds.csv.gz"),
    "D3": ("nflscrapR player-game stats", "https://github.com/ryurko/nflscrapR-data/tree/master/legacy_data/game_player_stats"),
    "D4": ("FantasyDataPros 2021 weekly", "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball/tree/master/2022/09-Correlation%20Matrices/01-Weekly%20Fantasy%20Stats%20-%202021"),
    "D5": ("NFL official Big Data Bowl", "https://github.com/nfl-football-ops/Big-Data-Bowl/blob/master/Data/games.csv"),
}
METHOD_URL = "methodology.html"

NAV = [
    ("index.html", "Home"),
    ("executive-summary.html", "Executive Summary"),
    ("singles.html", "Single Bets"),
    ("parlays.html", "Parlays"),
    ("props.html", "Player Props"),
    ("correlations.html", "Correlations"),
    ("validation.html", "Validation & Gates"),
    ("official-facts.html", "Official Facts"),
    ("data-sources.html", "Data & Sources"),
    ("methodology.html", "Methodology"),
    ("flagged.html", "Flagged for Review"),
]


def esc(x):
    return html.escape(str(x))


def link(url, label=None):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label or url)} <span class="ext">↗</span></a>'


def badge(tier):
    cls = {"Gold": "gold", "Silver": "silver", "Bronze": "bronze", "Rejected": "rejected",
           "OFFICIAL": "official", "DERIVED": "derived", "PRIMARY (non-NFL)": "primary",
           "UNVERIFIED": "unverified", "RESEARCH": "research"}.get(tier, "derived")
    return f'<span class="badge {cls}">{esc(tier)}</span>'


def gate_pills(gates):
    out = []
    for k, v in gates.items():
        short = k.split("_")[0]
        out.append(f'<span class="gate {"pass" if v else "fail"}" title="{esc(k)}: {"pass" if v else "fail"}">{short}</span>')
    return '<span class="gates">' + "".join(out) + "</span>"


def source_cell(datasets, derived=True, extra=""):
    parts = []
    if derived:
        parts.append(badge("DERIVED"))
    for d in datasets:
        label, url = DATASET_LINKS[d]
        parts.append(link(url, label))
    parts.append(f'<a href="{METHOD_URL}">method</a>')
    if extra:
        parts.append(extra)
    return '<div class="src">' + " · ".join(parts) + "</div>"


def table(headers, rows, tid="t", sortable=True):
    cls = "data-table" + (" sortable" if sortable else "")
    h = "".join(f"<th>{c}</th>" for c in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    return (f'<div class="table-wrap"><table class="{cls}" id="{esc(tid)}">'
            f"<thead><tr>{h}</tr></thead><tbody>{''.join(body)}</tbody></table></div>")


def fmt_pct(x):
    return "—" if x is None else f"{100*x:.1f}%"


def fmt_num(x, nd=3):
    return "—" if x is None else f"{x:.{nd}f}"


def page(title, subtitle, body, active, wide=False):
    nav = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{esc(label)}</a>'
        for href, label in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Own8 NFL</title>
<meta name="description" content="{esc(subtitle)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <div class="brand"><a href="index.html">Own8 <span>NFL Line Lab</span></a></div>
  <button class="nav-toggle" aria-label="Toggle navigation" onclick="document.body.classList.toggle('nav-open')">☰</button>
</header>
<nav class="sidebar"><div class="nav-title">Dashboard</div>{nav}
  <div class="nav-foot">Verified 2026-11-03 · session 28cc78aa</div>
</nav>
<main class="content{' wide' if wide else ''}">
  <div class="page-head"><h1>{esc(title)}</h1><p class="sub">{esc(subtitle)}</p></div>
  {body}
  <footer class="foot">
    <p>Own8 NFL Line Lab · research &amp; education only, not betting advice. Market data is
    <strong>PRIMARY (non-NFL)</strong> and flagged; official facts link to NFL sources.
    See <a href="flagged.html">Flagged for Review</a> and <a href="data-sources.html">Data &amp; Sources</a>.</p>
  </footer>
</main>
<script src="assets/app.js"></script>
</body>
</html>"""


def _linkify(md):
    # Wrap bare URLs in autolink brackets so they render as clickable links.
    # Skip URLs already inside markdown links ](url), (url), or autolinks <url>.
    return re.sub(r"(?<!\]\()(?<!\()(?<!<)(https?://[^\s<>()\[\]|]+)", r"<\1>", md)


def md_doc(path):
    text = _linkify((ROOT / path).read_text())
    return markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])


# ---------------------------------------------------------------- pages
def build_index(strategies, leaderboard, validation, facts, market):
    top = leaderboard[0]
    s2 = next(s for s in strategies if s["id"] == "S2")
    cards = [
        ("Games in dataset", "7,548", "1999–2026 · results + closing lines"),
        ("Official NFL facts", str(len(facts["facts"])), "verified verbatim from NFL sources"),
        ("Official score anchor", "91 / 91", "exact match vs NFL Big Data Bowl"),
        ("Strategies tested", str(len(strategies)), "singles · parlays · player props"),
        ("Top signal (S2)", f"+{s2['holdout_clv_mean_pts']} pts CLV", f"z = {s2['holdout_clv_z']} · {badge(s2['tier'])}"),
        ("Gold-tier edges", "0", "strict gates; honest outcome"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="card-label">{esc(l)}</div><div class="card-value">{v}</div><div class="card-sub">{s}</div></div>'
        for l, v, s in cards)
    lb_rows = []
    for i, r in enumerate(leaderboard, 1):
        strat = next(s for s in strategies if s["id"] == r["id"])
        cat_link = {"Single bet": "singles.html", "Parlay": "parlays.html", "Player prop": "props.html"}[r["category"]]
        lb_rows.append([
            str(i), f'<strong>{esc(r["id"])}</strong>',
            f'<a href="{cat_link}#{r["id"]}">{esc(r["name"])}</a>',
            esc(r["category"]), f'{r["score"]:.1f}', f'{r["gates_passed"]}/7',
            badge(r["tier"]), source_cell(strat["data"], derived=True)])
    lb = table(["#", "ID", "Strategy", "Category", "Score", "Gates", "Tier", "Source"], lb_rows, "leaderboard")
    summary = f"""
    <section class="hero">
      <p class="lead">A verified, reproducible NFL line-origination lab. We originate our own spreads,
      totals, moneylines and player-prop lines, measure <strong>closing-line value</strong> to separate
      skill from luck, and run every strategy through seven validation gates on a reward leaderboard.</p>
    </section>
    <section class="cards">{card_html}</section>
    <section class="panel">
      <h2>Leaderboard</h2>
      <p class="muted">Ranked by the transparent score in <a href="validation.html">Validation &amp; Gates</a>.
      The only non-rejected strategy is <strong>S2</strong> (Silver): the model beats the opening game total
      by ~0.8 pts (z≈5.7) — a genuine, luck-free skill signal whose profit consistency is not yet proven.
      No strategy reached Gold.</p>
      <input class="filter" data-table="leaderboard" placeholder="Filter strategies…">
      {lb}
    </section>
    <section class="panel">
      <h2>Read the details</h2>
      <div class="quicklinks">
        <a href="executive-summary.html">Executive Summary →</a>
        <a href="correlations.html">Correlation library →</a>
        <a href="official-facts.html">Official NFL facts →</a>
        <a href="flagged.html">Flagged for Review →</a>
      </div>
    </section>"""
    (SITE / "index.html").write_text(page("Own8 NFL Line Lab", "Originate lines · measure skill · validate everything", summary, "index.html", wide=True))


def strategy_block(s):
    cat = s["category"]
    rows = []
    if cat == "Player prop":
        metrics = [
            ("Player-games evaluated", s["n_player_games"]),
            ("MAE (yards)", s["mae_yds"]),
            ("RMSE — accuracy line", s["rmse_model"]),
            ("RMSE — best naive baseline", s["rmse_best_baseline"]),
            ("RMSE skill vs baseline", f'{s["rmse_skill_pct"]}% (CI {s["rmse_skill_ci"][0]}–{s["rmse_skill_ci"][1]}%)'),
            ("Out-of-sample R²", s["oos_r2"]),
            ("Fair-line over-hit rate", f'{fmt_pct(s["over_hit_rate"])} (CI {fmt_pct(s["over_hit_ci"][0])}–{fmt_pct(s["over_hit_ci"][1])})'),
            ("2021 robustness skill", f'{s["robustness_2021_skill_pct"]}%' if s["robustness_2021_skill_pct"] is not None else "—"),
            ("2021 fair-line over-hit", fmt_pct(s["robustness_2021_over_hit"])),
        ]
    else:
        ho = s.get("holdout", {})
        metrics = [
            ("Window (full / holdout)", f'{s.get("full_window","—")} / {s.get("holdout_window","—")}'),
            ("Holdout bets", ho.get("n_bets", "—")),
            ("Holdout ROI", f'{fmt_pct(ho.get("roi"))} (CI {fmt_pct(ho.get("roi_ci_low"))}–{fmt_pct(ho.get("roi_ci_high"))})'),
            ("Holdout win rate", fmt_pct(ho.get("win_rate"))),
            ("Full-window ROI", fmt_pct(s.get("full", {}).get("roi"))),
        ]
        if s.get("holdout_clv_mean_pts") is not None:
            metrics.append(("Holdout CLV (pts)", f'{s["holdout_clv_mean_pts"]} (CI {s["holdout_clv_ci"][0]}–{s["holdout_clv_ci"][1]}, z {s["holdout_clv_z"]})'))
        if s.get("luck_p_value") is not None:
            metrics.append(("Luck null p-value", f'{s["luck_p_value"]:.3g}'))
        rob = s.get("robustness_holdout", {})
        if rob:
            metrics.append(("Seasons positive / drop-best ROI", f'{fmt_pct(rob.get("seasons_positive"))} / {fmt_pct(rob.get("drop_best_roi"))}'))
        if cat == "Parlay":
            metrics += [
                ("P(leg A) · P(leg B)", f'{s["p_leg_a"]} · {s["p_leg_b"]}'),
                ("Joint P empirical / independent", f'{s["p_joint_empirical"]} / {s["p_joint_independent"]}'),
                ("Correlation lift", fmt_pct(s["correlation_lift"])),
                ("Fair decimal odds (empirical)", s["fair_decimal_odds"]),
            ]
        if "threshold_chosen_on_train" in s:
            metrics.append(("Threshold (chosen on train)", s["threshold_chosen_on_train"]))
    mrows = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in metrics)
    return f"""
    <article class="strategy" id="{s['id']}">
      <div class="strategy-head">
        <h3>{esc(s['id'])} · {esc(s['name'])} {badge(s['tier'])}</h3>
        <div class="strategy-meta">Score <strong>{s['score']}</strong> · Gates {s['gates_passed']}/7 {gate_pills(s['gates'])}</div>
      </div>
      <p class="muted">{esc(s['description'])}</p>
      <div class="table-wrap"><table class="kv"><tbody>{mrows}</tbody></table></div>
      <div class="src-row">Source: {source_cell(s['data'], derived=True)}</div>
    </article>"""


def build_category(strategies, cat, filename, title, subtitle, intro):
    items = [s for s in strategies if s["category"] == cat]
    body = f'<section class="panel"><p class="lead">{intro}</p></section>'
    body += "".join(strategy_block(s) for s in items)
    (SITE / filename).write_text(page(title, subtitle, body, filename, wide=True))


def build_correlations(correlations):
    rows = []
    for c in correlations:
        val = "—" if c["pearson"] is None else f'{c["pearson"]:.3f}'
        ci = "—" if c["ci_low"] is None else f'{c["ci_low"]:.3f} – {c["ci_high"]:.3f}'
        rho = "—" if c["spearman"] is None else f'{c["spearman"]:.3f}'
        extra = ""
        if "p_joint" in c:
            extra = f'<div class="muted small">P(both)={c["p_joint"]} vs independent {c["p_independent"]}</div>'
        rows.append([esc(c["pair"]), val, ci, rho, str(c["n"]), esc(c["era"]),
                     badge(c["tier"]), source_cell([c["dataset"]], derived=(c["tier"] == "DERIVED")) + extra])
    t = table(["Pair", "Pearson r", "95% CI", "Spearman ρ", "n", "Era", "Tier", "Source"], rows, "corr")
    body = f"""
    <section class="panel">
      <p class="lead">Dependency estimates for parlay &amp; player-prop combo pricing. Pearson r with
      2,000-sample bootstrap 95% CIs; Spearman ρ as a robustness check. Base era 2009–2017 (D3),
      re-checked on 2021 (D4). <strong>DERIVED</strong> from primary data — see
      <a href="flagged.html">provenance flags</a>.</p>
      <input class="filter" data-table="corr" placeholder="Filter pairs…">
      {t}
    </section>
    <section class="panel">
      <h2>How to use these</h2>
      <ul>
        <li><strong>QB + WR yards (r≈0.70–0.76):</strong> strongly positively correlated — price same-game
        parlays with the empirical joint distribution, never by multiplying independent legs.</li>
        <li><strong>WR1 + WR2 (r≈0.49):</strong> positive, not negative — stacking same-team receivers does not diversify.</li>
        <li><strong>QB + own RB yards (r≈−0.18):</strong> negatively correlated (game script) — a rare negative SGP pair.</li>
        <li><strong>Cover + total (φ≈0):</strong> ~independent — standard 2-leg parlay pricing is roughly fair; no edge.</li>
      </ul>
    </section>"""
    (SITE / "correlations.html").write_text(page("Correlation Library", "Dependency values for combos & parlays", body, "correlations.html", wide=True))


def build_validation(validation, leaderboard, strategies):
    checks = []
    labels = {
        "A1_official_anchor": ("Official NFL score anchor", "D5"),
        "A2_line_crosscheck": ("Independent odds cross-check", "D1"),
        "A3_player_internal": ("Player-stats internal consistency", "D3"),
        "A4_player_schedule_coverage": ("Player stats ↔ schedule coverage", "D3"),
        "A5_fdp_coverage": ("2021 sample ↔ schedule coverage", "D4"),
    }
    for k, (label, ds) in labels.items():
        v = validation[k]
        detail = v.get("description", "")
        stat = ""
        if k == "A1_official_anchor":
            stat = f'{v["n_exact_score_matches"]}/{v["n_official_games"]} exact'
        elif k == "A2_line_crosscheck":
            stat = f'spread {fmt_pct(v["spread_within_0.5"])} / total {fmt_pct(v["total_within_0.5"])} within 0.5'
        elif k == "A3_player_internal":
            stat = f'{fmt_pct(v["exact_match_rate"])} exact, median diff {v["median_abs_diff"]}'
        else:
            stat = f'{v["n_valid"]}/{v["n_team_weeks"]}' if "n_team_weeks" in v else f'{v["n_covered"]}/{v["n_dates"]}'
        flag = f'<div class="muted small">⚑ {esc(v["flag"])}</div>' if v.get("flag") else ""
        checks.append([esc(label), esc(detail), stat,
                       '<span class="gate pass">PASS</span>' if v["pass"] else '<span class="gate fail">FAIL</span>',
                       source_cell([ds], derived=(k != "A1_official_anchor"),
                                   extra=link(v["official_source"], "official source") if k == "A1_official_anchor" else "") + flag])
    ct = table(["Check", "What it verifies", "Result", "Status", "Source"], checks, "checks")
    gates_md = (ROOT / "docs/VALIDATION_GATES.md").read_text().split("## Current leaderboard")[0]
    gates_html = markdown.markdown(gates_md, extensions=["tables", "fenced_code"])
    lb_rows = []
    for r in leaderboard:
        s = next(x for x in strategies if x["id"] == r["id"])
        lb_rows.append([esc(r["id"]), esc(r["name"]), f'{r["score"]:.1f}', f'{r["gates_passed"]}/7',
                        badge(r["tier"]), gate_pills(s["gates"]), source_cell(s["data"])])
    lt = table(["ID", "Strategy", "Score", "Gates", "Tier", "Gate detail", "Source"], lb_rows, "vleaderboard")
    body = f"""
    <section class="panel"><h2>Data validation (Part A)</h2>
      <p class="muted">Overall: {'<span class="gate pass">ALL PASS</span>' if validation['all_pass'] else '<span class="gate fail">FAIL</span>'}.
      Tolerances are documented; flagged items are non-blocking and listed on <a href="flagged.html">Flagged for Review</a>.</p>
      {ct}</section>
    <section class="panel doc">{gates_html}</section>
    <section class="panel"><h2>Leaderboard with gate detail</h2>{lt}</section>"""
    (SITE / "validation.html").write_text(page("Validation & Gates", "Data checks · 7 gates · leaderboard rules", body, "validation.html", wide=True))


def build_official_facts(facts):
    rows = []
    for f in facts["facts"]:
        rows.append([esc(f["id"]), esc(f["category"]), esc(f["fact"]), f'<strong>{esc(f["value"])}</strong>',
                     esc(f["rule"]), f'<span class="quote">“{esc(f["quote"])}”</span>',
                     badge(f["tier"]), link(f["url"], f["source_id"])])
    t = table(["ID", "Category", "Fact", "Value", "Rule", "Verbatim quote", "Tier", "Official source"], rows, "facts")
    body = f"""
    <section class="panel">
      <p class="lead">{len(facts['facts'])} facts verified verbatim from NFL-owned sources on
      {esc(facts['verification_date'])}. Every row links to the official source and quotes the exact text.
      Nothing here is inferred.</p>
      <input class="filter" data-table="facts" placeholder="Filter facts…">
      {t}
    </section>"""
    (SITE / "official-facts.html").write_text(page("Official NFL Facts", "Rules · scoring · season structure — verified", body, "official-facts.html", wide=True))


def build_flagged(strategies, validation):
    items = [
        ("Market-line provenance", "PRIMARY (non-NFL)",
         "The NFL does not publish betting lines. All spread/total/moneyline values come from public primary mirrors (D1/D2), cross-checked between two independent sources, and are never presented as official.",
         [("D1", DATASET_LINKS["D1"][1]), ("D2", DATASET_LINKS["D2"][1])]),
        ("Spread close disagreement between mirrors", "DERIVED",
         f'Independent mirrors agree within 0.5 pt on {fmt_pct(validation["A2_line_crosscheck"]["spread_within_0.5"])} of spreads (MAD {validation["A2_line_crosscheck"]["spread_mad"]}). Disagreements concentrate in 2006–2013 consensus snapshots; 25 games (0.6%) differ by >1.5 pt. Tolerance documented; does not block.',
         [("D1/D2 cross-check", DATASET_LINKS["D2"][1])]),
        ("Legacy player-stat yardage quirks", "DERIVED",
         f'{fmt_pct(validation["A3_player_internal"]["exact_match_rate"])} of team-games have exactly matching passer/receiver yards; ~3.1% differ (lateral/sack attribution in legacy nflscrapR aggregation), median diff 0. Correlations use receiver-side yards; flagged, not silently corrected.',
         [("D3", DATASET_LINKS["D3"][1])]),
        ("Player-prop correlation era caveat", "DERIVED",
         "Correlations estimated on 2009–2017 (D3) with a 2021 robustness check (D4). The modern passing environment may shift magnitudes; CIs and the 2021 check are reported so the reader can judge.",
         [("D3", DATASET_LINKS["D3"][1]), ("D4", DATASET_LINKS["D4"][1])]),
        ("No archived market player-prop lines", "UNVERIFIED",
         "Historical market prop lines are not publicly archived in any reachable primary source. Prop strategies are therefore evaluated as line origination (accuracy + fairness), NOT as ROI backtests against market prop lines. No prop lines were fabricated.",
         [("Methodology", METHOD_URL)]),
        ("Empty starting repository", "INFO",
         "The repo contained only a 6-byte README at session start; all deliverables are new. Nothing pre-existing required external verification.",
         [("Repo review", "repo-review.html")]),
        ("Branch-policy note", "INFO",
         "The task requested session-<id>/<task> branches, but the Arena platform pins this session to arena/28cc78aa-own8 and forbids other branches. That branch serves as both work and integration branch.",
         [("COORDINATION.md", "https://github.com/sassnarep3-star/Own8/blob/main/COORDINATION.md")]),
    ]
    rows = []
    for title, tier, desc, links in items:
        src = " · ".join(link(u, l) for l, u in links)
        rows.append([f"<strong>{esc(title)}</strong>", badge(tier), esc(desc), src])
    t = table(["Item", "Tier", "Detail", "Source / review link"], rows, "flagged")
    body = f"""
    <section class="panel">
      <p class="lead">Clearly labeled irregularities and unverified items. These are
      <strong>non-blocking</strong> — they are published for review after the site is live, and do not
      prevent merge. Values that cannot be confirmed from an official source are left blank and marked
      <span class="badge unverified">UNVERIFIED</span>; derived statistics are labeled
      <span class="badge derived">DERIVED</span> with their primary-data provenance.</p>
      {t}
    </section>"""
    (SITE / "flagged.html").write_text(page("Flagged for Review", "Irregularities & unverified items (non-blocking)", body, "flagged.html", wide=True))


def build_doc_page(filename, title, subtitle, docs, active):
    body = "".join(f'<section class="panel doc">{md_doc(d)}</section>' for d in docs)
    (SITE / filename).write_text(page(title, subtitle, body, active, wide=True))


def main():
    strategies = json.loads((RES / "strategies.json").read_text())
    leaderboard = json.loads((RES / "leaderboard.json").read_text())
    validation = json.loads((RES / "validation.json").read_text())
    correlations = json.loads((RES / "correlations.json").read_text())
    facts = json.loads((ROOT / "data" / "official_facts.json").read_text())
    market = json.loads((RES / "market_context.json").read_text())

    build_index(strategies, leaderboard, validation, facts, market)
    build_category(strategies, "Single bet", "singles.html", "Single Bets",
                   "Spread · total · moneyline strategies",
                   "Model-originated lines vs market. Skill is measured by closing-line value (CLV) where we bet the opening number, and by out-of-sample ROI at the closing number. Every strategy is gated; most are rejected because the closing market is efficient.")
    build_category(strategies, "Parlay", "parlays.html", "Parlays",
                   "Same-game 2-leg cover + total combos",
                   "Same-game parlays priced at standard +260. Joint probabilities are estimated empirically (not as independent legs). Cover and total legs are ~independent (φ≈0), so these lose the vig — see the correlation library for where real dependence lives (player props).")
    build_category(strategies, "Player prop", "props.html", "Player Props",
                   "Fair-line origination + correlation-aware combos",
                   "No historical market prop lines are publicly archived, so props are evaluated as line origination (accuracy vs baselines + fair 50/50 line), not ROI backtests. The real combo value is the strong QB↔WR correlation (r≈0.70) — see Correlations.")
    build_correlations(correlations)
    build_validation(validation, leaderboard, strategies)
    build_official_facts(facts)
    build_flagged(strategies, validation)
    build_doc_page("executive-summary.html", "Executive Summary", "Important details at a glance", ["EXECUTIVE_SUMMARY.md"], "executive-summary.html")
    build_doc_page("methodology.html", "Methodology", "Strategy research + validation gates", ["docs/STRATEGY_RESEARCH.md", "docs/VALIDATION_GATES.md"], "methodology.html")
    build_doc_page("data-sources.html", "Data & Sources", "Provenance · verification tiers · source registry", ["docs/DATA_PROVENANCE.md", "docs/SOURCES.md"], "data-sources.html")
    build_doc_page("repo-review.html", "Repo Review", "Line-by-line audit of the starting repository", ["docs/REPO_REVIEW.md"], "data-sources.html")
    (SITE / ".nojekyll").write_text("")
    print("site built:", len(list(SITE.glob('*.html'))), "pages")


if __name__ == "__main__":
    main()
