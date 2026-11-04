"""Build a static GitHub Pages evidence dashboard; no third-party assets."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "results.json").read_text())
MANIFEST = DATA["manifest"]
GAMES = MANIFEST["files"][0]["source_url"]
SCHEMA = MANIFEST["files"][1]["source_url"]
README = MANIFEST["files"][2]["source_url"]
REPO = "https://github.com/sassnarep3-star/Own8"
NAV = [("index.html", "Overview", "01"), ("evidence.html", "Official evidence", "02"),
       ("lines.html", "Line research", "03"), ("strategies.html", "Strategy lab", "04"),
       ("correlations.html", "Correlations", "05"), ("gates.html", "Validation gates", "06"),
       ("flagged.html", "Flagged for Review", "07"), ("sources.html", "Sources & audit trail", "08")]


def esc(value):
    return html.escape(str(value), quote=True)


def fmt(value, digits=2):
    return "" if value is None else f"{value:,.{digits}f}"


def source(url, label="Official data"):
    return f'<a class="source" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} <span aria-hidden="true">↗</span></a>'


def badge(text, kind="hold"):
    return f'<span class="badge {esc(kind)}">{esc(text)}</span>'


def table(headers, rows, caption):
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join('<tr>' + ''.join(f'<td>{v}</td>' for v in row) + '</tr>' for row in rows)
    return f'<div class="table-tools"><label>Filter rows <input class="filter" type="search" placeholder="Search this table…" aria-label="Filter {esc(caption)}"></label><span class="count" aria-live="polite">{len(rows)} rows</span></div><div class="table-wrap"><table><caption>{esc(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div><p class="empty" hidden>No matching rows.</p>'


def note(text):
    return f'<aside class="notice">{text}</aside>'


def shell(filename, title, eyebrow, description, content):
    links = ''.join(f'<a href="{url}" class="{"active" if url == filename else ""}" {"aria-current=page" if url == filename else ""}><span>{num}</span>{label}</a>' for url, label, num in NAV)
    out = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc(description)}"><title>{esc(title)} · Own8 Evidence Lab</title><link rel="stylesheet" href="style.css"><script src="app.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a><aside class="sidebar"><a class="brand" href="index.html"><span class="mark">O8</span><span>OWN8<small>NFL EVIDENCE LAB</small></span></a><p class="nav-label">RESEARCH WORKSPACE</p><nav aria-label="Research categories">{links}</nav><div class="sidebar-bottom"><span class="dot"></span> Evidence before edge<p>Research only. No wagers.<br>Historical sample: 2017 W1–6</p><a href="../index.html">← Existing project dashboard</a></div></aside>
<div class="workspace"><header class="topbar"><span>NFL / Research & verification</span><span class="snapshot">Snapshot · 04 NOV 2026</span></header><main id="main"><div class="page-head"><div><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1><p class="lede">{esc(description)}</p></div>{badge('RESEARCH MODE', 'neutral')}</div>{content}</main><footer>Own8 · Independent research, not NFL-endorsed. Blank cells mean no confirmed value. <a href="flagged.html">Review limitations</a> · <a href="README.md">Reproduce this package</a></footer></div></body></html>'''
    (ROOT / filename).write_text(out)


metrics = DATA["metrics"]
summary_rows = [
    ["Evidence", f"{DATA['official_games']} game rows captured directly from the NFL publisher's GitHub repository; file hashes match the API blobs.", badge("OFFICIAL SNAPSHOT", "good"), source(GAMES)],
    ["Line origination", f"{metrics['holdout_games']} historical point forecasts; Weeks 1–2 warm-up, Weeks 3–6 held out one week at a time. No current NFL lines.", badge("DERIVED / EXPLORATORY", "neutral"), source(GAMES)],
    ["Skill leaderboard", "Seven registered research ideas. Zero eligible strategies. No rank, realized ROI, reward, or recommendation published.", badge("HOLD"), source(SCHEMA, "Dataset scope")],
    ["Parlays & props", "Matched bet-outcome histories and verified offered prices are absent. Prop and parlay correlation values remain blank.", badge("UNVERIFIED"), source(SCHEMA, "Dataset scope")],
    ["Luck & uncertainty", "No method removes outcome randomness. Chronological tests and uncertainty controls can reduce false discoveries, not guarantee skill or profit.", badge("RESEARCH POLICY", "neutral"), source(README, "Official data context")],
]
content = note('<strong>No actionable bets.</strong> This package is a conservative evidence layer, not a live odds feed. Other repository dashboards have separate owners and may contain unresolved findings. <a href="flagged.html">See Flagged for Review →</a>')
content += f'''<div class="kpis"><article><span>OFFICIAL GAME ROWS</span><strong>{DATA['official_games']}</strong><small>2017 · Weeks 1–6</small></article><article><span>HISTORICAL FORECASTS</span><strong>{metrics['holdout_games']}</strong><small>Prior-week-only training</small></article><article><span>ELIGIBLE STRATEGIES</span><strong>0<span class="small"> / 7</span></strong><small>All required gates must PASS</small></article><article><span>LIVE BET RECOMMENDATIONS</span><strong>0</strong><small>Unverified fields stay blank</small></article></div><section class="panel"><div class="section-head"><div><p class="eyebrow">DECISION BRIEF</p><h2>Executive summary</h2></div><a href="EXECUTIVE_SUMMARY.md">Read full brief ↗</a></div>'''
content += table(["Category", "Finding", "Status", "Official source / context"], summary_rows, "Executive findings and verification scope") + '</section>'
content += '<div class="two-col"><section class="panel"><p class="eyebrow">HOW TO READ THIS LAB</p><h2>Facts ≠ forecasts ≠ bets</h2><p><b>Official facts</b> are exact source-file values. <b>Derived research</b> is our reproducible calculation, not an NFL statement. <b>Unverified</b> values stay empty and block publication.</p><a href="evidence.html">Inspect all official rows →</a></section><section class="panel"><p class="eyebrow">COMPETITION DESIGN</p><h2>Earn eligibility, then rank</h2><p>Register hypotheses before testing. Freeze predictions and data cutoffs. Require official prices, calibrated probabilities, dependence checks and multi-season held-out evidence before any reward.</p><a href="gates.html">Explore validation policy →</a></section></div>'
shell("index.html", "Evidence before edge.", "OWN8 / NFL RESEARCH", "A source-linked workspace for originating NFL lines and testing strategies—without manufacturing certainty.", content)

rows = []
for g in DATA["games"]:
    rows.append([esc(g["id"]), str(g["week"]), esc(g["date"]), esc(g["away"]), esc(g["home"]), str(g["away_score"]), str(g["home_score"]), badge("CAPTURE MATCH", "good"), source(g["source_url"], "Official row")])
content = note('All displayed historical fact cells come directly from the captured official file. Verification means <strong>exact capture and immutable hash agreement</strong>, not independent checking against 91 separate gamebooks. No 2026 facts are confirmed here.')
content += '<div class="actions"><a class="button" href="evidence/games.csv" download>Download official CSV</a><a href="evidence/manifest.json">View hashes & provenance ↗</a></div><section class="panel">'
content += table(["Game ID", "Week", "Date (source)", "Away", "Home", "Away pts", "Home pts", "Verification", "Source"], rows, "Official NFL sample · 2017 Weeks 1–6") + '</section>'
shell("evidence.html", "Official evidence", "SOURCE CAPTURE / 01", "Every historical game row has a pinned official source, a line reference, and an immutable evidence trail.", content)

rows = [["Home-margin MAE", fmt(metrics["spread_mae"]), fmt(metrics["spread_baseline_mae"]), "Points; lower is better", source(GAMES)],
        ["Game-total MAE", fmt(metrics["total_mae"]), fmt(metrics["total_baseline_mae"]), "Points; lower is better", source(GAMES)],
        ["Home-margin RMSE", fmt(metrics["spread_rmse"]), "", "Points; sensitive to large errors", source(GAMES)],
        ["Game-total RMSE", fmt(metrics["total_rmse"]), "", "Points; sensitive to large errors", source(GAMES)],
        ["ROI / closing-line value", "", "", "No verified prices; not measured", source(SCHEMA, "Dataset scope")]]
content = note('<strong>Historical estimates only.</strong> These are derived model outputs, not official NFL lines or current recommendations. Model settings are a declared research choice: four pseudo-team-games of shrinkage; home advantage estimated only from prior weeks. No betting probability or return is inferred.')
content += '<section class="panel"><h2>Forecast diagnostic—not a betting leaderboard</h2><p>League-only baseline uses training mean home margin and training mean total. Sample is one season and four held-out weeks. No hyperparameter search is performed. Improvement in a small MAE sample cannot establish betting skill.</p>'
content += table(["Metric", "Team model", "League baseline", "Interpretation", "Official inputs"], rows, "Derived holdout forecast diagnostics") + '</section>'
rows = []
for r in DATA["models"]:
    rows.append([esc(r["game"]), str(r["week"]), f"W{r['training_max_week']}", fmt(r["predicted_home_margin"]), fmt(r["fair_home_handicap"]), fmt(r["predicted_total"]), "", "", badge("HOLD"), source(r["source_url"], "Official result")])
content += '<section class="panel"><h2>Expanding-window historical fair lines</h2><p>Margin = home points − away points. Fair home handicap = −predicted margin. A negative handicap means home favorite. These estimates are not rounded to a bookmaker tick and do not include payout, vig or uncertainty-based trade decisions.</p>'
content += table(["Game", "Week", "Train through", "Home margin est.", "Home handicap est.", "Total est.", "Official market", "EV", "Status", "Official input"], rows, "Derived historical forecasts; unverified market fields intentionally blank") + '</section>'
shell("lines.html", "Line research", "WALK-FORWARD / 02", "Reproducible, prior-week-only point forecasts with explicit sign conventions and honest limitations.", content)

rows = []
for s in DATA["strategies"]:
    rows.append([esc(s["id"]), f'<b>{esc(s["name"])}</b><small>{esc(s["category"])}</small>', esc(s["hypothesis"]), esc(s["missing"]), badge("HOLD"), "", "", "", source(s["source_url"], "Dataset scope")])
content = note('This is a <strong>research registry, not a performance ranking</strong>. Row order is strategy ID, not skill. Missing ranks, ROI and rewards are blank—not zero performance. No cash prizes or wagers are implemented.')
content += '<section class="panel"><h2>Seven ideas. One evidence standard.</h2>' + table(["ID", "Strategy", "Signal hypothesis / research choice", "Evidence still required", "Eligibility", "Rank", "ROI", "Reward points", "Official context"], rows, "Research registry with unlaunched leaderboard fields") + '</section>'
content += '<section class="panel"><h2>Proposed competition contract</h2><ol><li>Pre-register every attempted variant, selection rule, market, cutoff and stake cap. Reserve an untouched confirmation period; log rejected variants too.</li><li>Score only locked, executable quotes and settled outcomes. Track pushes, voids, overtime and book-specific parlay rules. No hindsight substitution.</li><li>Require all eight gates to pass before entry. Rank eligible strategies by positive, multiplicity-adjusted lower ROI bound after costs; publish uncertainty and drawdown beside rank.</li><li>Proposed non-cash reward: 10,000 × simultaneous lower ROI bound, only after eligibility. Break equal scores by registered strategy ID; never reward raw short-run profit alone.</li><li>Use season and week blocks for uncertainty. Repeated monitoring requires a new untouched sample or an anytime-valid protocol; do not repeatedly peek at a fixed-sample p-value.</li></ol><p>These rules are our proposed policy, not an existing funded contest or an official NFL scoring system.</p><a href="METHODOLOGY.md">Read full validation design →</a></section>'
shell("strategies.html", "Strategy lab", "REGISTRY / 03", "Singles, parlays and player props share the same fail-closed eligibility and evidence requirements.", content)

rows = []
for c in DATA["correlations"]:
    interval = "" if c["ci_low"] is None else f"[{fmt(c['ci_low'], 3)}, {fmt(c['ci_high'], 3)}]"
    rows.append([f'<b>{esc(c["pair"])}</b><small>{esc(c["scope"])}</small>', fmt(c["r"], 3), "" if c["n"] is None else str(c["n"]), interval, esc(c["caveat"]), badge(c["status"], "neutral" if c["r"] is not None else "hold"), source(c["source_url"], "Official inputs / scope")])
content = note('A score correlation is <strong>not</strong> a player-prop correlation or a same-game parlay leg correlation. Correlation alone does not determine joint tail probability. A low correlation is not proof of independence or profitability.')
content += '<section class="panel"><h2>What is measured—and what is not</h2>' + table(["Pair / sample", "Pearson r", "n", "Exploratory 95% interval", "Interpretation", "Status", "Official context"], rows, "Derived correlations and intentionally unestimated bet-outcome pairs") + '</section>'
content += '<section class="panel"><h2>Parlay validation rule</h2><p>Align legs on the same historical scenarios, thresholds and pregame information. Estimate joint outcomes directly, including shared factors; compare to the actual official offered payout. Do not multiply marginal probabilities unless independence has been justified. Pairwise r cannot specify a three-leg joint distribution.</p><p>The engine includes a paired-binary-outcome estimator, Fréchet bounds and tests showing why multiplying marginals fails for correlated legs. Synthetic test cases are not NFL performance evidence. Pushes and voids require book-specific rules and are rejected by this binary estimator.</p><a href="engine.py">Inspect dependence code →</a></section>'
shell("correlations.html", "Correlation library", "DEPENDENCE / 04", "Measure the right pairs, preserve shared scenarios, and leave unsupported correlation values blank.", content)

policies = [
    ("G1", "Evidence", "Every decision-critical fact and offered price matched to an archived official source, exact field and timestamp. A URL alone is insufficient.", "No verified market quotes."),
    ("G2", "Freshness", "Quote age ≤15 minutes at decision (policy choice); UTC-aware timestamps; final required injury/game status. Future-dated and ambiguous captures fail.", "Historical sample cannot support current selections."),
    ("G3", "Chronology", "Lock predictions before kickoff; inspect training IDs and feature availability; protect untouched holdout; audit publication-time leakage.", "Retrospective prototype is not a prospective locked record."),
    ("G4", "Sample", "At least 1,000 held-out bets across ≥3 seasons (provisional research thresholds, not a proof of sufficiency).", "Only one short historical season sample."),
    ("G5", "Skill", "Positive simultaneous lower ROI bound after costs; valid clustered p ≤0.05/registered trials; calibration and season robustness pass. CLV is diagnostic, not proof of profit.", "No ROI, adjusted p-value or probability calibration evidence."),
    ("G6", "Dependence", "Paired-outcome joint calibration and portfolio overlap/exposure check; singles still share team/week risk. Do not pass using unrelated proxy correlations.", "Matched bet legs and portfolio risk model absent."),
    ("G7", "Risk", "Locked stake rules; observed held-out drawdown in [0,20%] (policy choice); stress test correlated loss scenarios. No guarantee on future drawdown.", "No settled betting portfolio."),
    ("G8", "Settlement", "Official final results, verified operator-specific rules, pushes, voids, overtime and audit ledger. Unknown outcomes remain ungraded.", "Official game results exist; operator rules and bet ledger do not."),
]
rows = [[gid, f'<b>{name}</b>', esc(rule), esc(missing), badge("HOLD"), source(SCHEMA, "Official data context")] for gid, name, rule, missing in policies]
content = note('<strong>PASS means PASS.</strong> CONDITIONAL, missing, stale, UNKNOWN or NOT_COMPUTABLE is not a pass. One failed or missing required gate prevents eligibility and suppresses ranks and reward points.')
content += '<section class="panel"><h2>Eight required gates</h2><p>These are project research rules, not official NFL requirements. Source links below describe the available dataset only; the NFL does not endorse these thresholds.</p>' + table(["Gate", "Control", "Proposed requirement", "Current blocker", "Status", "Official context"], rows, "Project validation policy and current evidence gaps") + '</section>'
content += '<section class="panel"><h2>Executable guardrails</h2><p><code>all_gates_pass()</code> requires the exact required gate set and the literal PASS value for every gate. The prototype blocks every strategy. Tests cover missing facts, stale quotes, handicap signs, pushes, future-data leakage, invalid probabilities and correlated legs.</p><div class="actions"><a href="engine.py">Engine source</a><a href="test_engine.py">Regression tests</a><a href="checks.json">Latest local check report</a></div></section>'
shell("gates.html", "Validation gates", "CONTROL PLANE / 05", "A conservative research contract: incomplete evidence blocks recommendations, rankings and rewards.", content)

flags = [
    ("V-01", "Current-season facts & prices", "No official 2026 scores, injuries, offered odds or player props were retrieved in this session. Existing repository captures are not automatically re-verified by this package.", "Current factual/price cells remain blank. No recommendations.", GAMES),
    ("V-02", "Legacy dashboard findings", "Baseline audit identified reversed handicap signs, conditional gate passes and unverified candidates. Active PR owners control those files; later corrections need re-audit. This package does not certify root or historical-lab claims.", "See the existing audit and PRs #6/#8; no conflicting edits by this session.", SCHEMA),
    ("V-03", "No demonstrated skill", "Only 2017 Weeks 1–6 data, four forecast holdout weeks, no official offered prices, no multi-season betting record. Neither profit nor luck-free performance can be claimed.", "ROI, CLV, p-values, ranks and rewards blank; every strategy HOLD.", GAMES),
    ("V-04", "Prop / parlay dependence", "No matched threshold-specific player prop or bet-leg histories. Score correlations are not substitutes. Different games can still share risk factors.", "Required correlation cells blank. Joint dependence gate HOLD.", SCHEMA),
    ("V-05", "Automation scope", "Local commands reproduce captured evidence and analysis without prompts. There is no unattended current NFL ingestion, sportsbook feed, prospective prediction lock or settlement daemon.", "Do not treat static rebuilds as live updates; freshness blocks current picks.", README),
    ("V-06", "Source access & authority scope", "This environment permits GitHub but not direct NFL website retrieval. Official publisher README/schema and immutable GitHub blobs were checked. No exhaustive external re-verification of the rest of the repository occurred.", "Use pinned official links for manual review. Hash agreement proves capture integrity, not independent gamebook agreement.", README),
    ("V-07", "Weak uncertainty sample", "Week-cluster intervals use only six clusters; descriptive score pairs share structure and omit many potential confounders. Intervals are exploratory, not reliable skill validation.", "No gate or parlay recommendation passes on these estimates.", GAMES),
    ("V-08", "Jurisdiction & rewards", "Existing repo copy assumes a jurisdiction that was not established by this session. No legal eligibility, prize pool, sportsbook connection or financial reward is verified.", "Research points only; no real-money betting or legal advice. Confirm applicable rules independently.", README),
    ("V-09", "Prototype specification", "Shrinkage strength, sample minimums, freshness cutoff, risk limit and scoring rules are research assumptions, not NFL-verified factual values.", "Label derived values and policy choices; do not put estimates in official-fact cells.", SCHEMA),
]
rows = [[fid, f'<b>{esc(title)}</b>', esc(finding), esc(action), badge("NEEDS REVIEW"), source(url, "Official context / scope")] for fid, title, finding, action, url in flags]
content = note('Unverified items do not block publication of the research site. They <strong>do block actionable selections and skill claims</strong>. Official links below define the available evidence; they do not verify custom methods, missing prices or unrelated repository claims.')
content += '<section class="panel"><h2>Open evidence & integration items</h2>' + table(["ID", "Area", "Finding", "Handling / next evidence needed", "Status", "Official context"], rows, "Flagged for Review · verification package") + '</section>'
content += f'<section class="panel"><h2>Related repository review</h2><p><a href="../audit/index.html">Baseline independent audit</a> · <a href="{REPO}/pull/6">Historical-lab integration PR #6</a> · <a href="{REPO}/pull/8">Root correction PR #8</a></p><p>Those are separate work scopes. Their status and findings may change after this snapshot. Read the shared <a href="../COORDINATION.md">coordination board</a> for handoffs and deployment records.</p></section>'
shell("flagged.html", "Flagged for Review", "EVIDENCE GAPS / 06", "Visible limitations, unverified fields and cross-session integration issues—never hidden behind a performance claim.", content)

rows = []
for item in MANIFEST["files"]:
    rows.append([esc(item["path"]), f'{item["bytes"]:,}', f'<code class="hash">{item["sha256"]}</code>', source(item["source_url"], "Immutable official file"), f'<a href="evidence/{esc(item["local"])}">Local capture ↗</a>'])
content = note('Authority basis: the publisher README identifies this repository as the NFL Big Data Bowl data homepage; repository metadata links to ops.nfl.com. This session fetched the official GitHub files through the GitHub API. It did not fetch direct NFL websites or third-party mirrors.')
content += f'<section class="panel"><h2>Immutable source registry</h2><p>Captured {esc(MANIFEST["retrieved_at"])}. Commit <code>{esc(MANIFEST["commit"])}</code>. Original file bytes are preserved; every build verifies SHA-256 and Git blob SHA-1 before analysis.</p>' + table(["Official file", "Bytes", "SHA-256", "Official source", "Local evidence"], rows, "Official NFL GitHub evidence registry") + '</section>'
content += '<section class="panel"><h2>Reproduce & inspect</h2><pre>python3 evidence-lab/analyze.py\npython3 evidence-lab/build.py\npython3 evidence-lab/check.py</pre><p>The normal build is offline. <code>capture.py</code> is an explicit official-source refresh command using authenticated <code>gh api</code>; it is not a scheduled updater. All application code uses the Python standard library.</p><div class="actions"><a href="results.json">Full analysis JSON</a><a href="evidence/manifest.json">Evidence manifest</a><a href="checks.json">Check report</a><a href="repo-review.json">Repository review snapshot</a><a href="METHODOLOGY.md">Methodology</a><a href="EXECUTIVE_SUMMARY.md">Executive summary</a></div><p>Verification levels: (1) exact official capture, (2) internal consistency, (3) derived analysis, (4) unverified. Matching other repository snapshots is internal consistency—not independent source verification.</p></section>'
shell("sources.html", "Sources & audit trail", "PROVENANCE / 07", "Official source bytes, pinned revisions, explicit verification scope and a reproducible offline build.", content)
print("Built 8 verification dashboard pages")
