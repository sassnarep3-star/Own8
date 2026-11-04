#!/usr/bin/env python3
"""Read-only reproducible audit of the existing Week 9 snapshot.

Does not fetch or overwrite the canonical site, analysis or data files. NFL source
pages must be reviewed separately; a URL in the input is NOT proof of verification.
Run: python3 audit/check.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent

def read(path):
    return json.loads((ROOT / path).read_text())

lines = read('analysis/model-lines-week9.json')['games']
standings = read('data/standings-2026-reg-w8.json')['teams']
schedule = read('data/schedule-2026-week9.json')['games']
board = read('analysis/leaderboard.json')
assert len(standings) == 32 and len(schedule) == len(lines) == 15
assert len({t['abbr'] for t in standings}) == 32
assert len({(g['away'], g['home']) for g in lines}) == 15
assert {(g['away'], g['home']) for g in schedule} == {(g['away'], g['home']) for g in lines}
for t in standings:
    assert t['PF'] - t['PA'] == t['NET'], t['abbr']
    assert abs(t['PCT'] - (t['W'] + .5*t['T']) / (t['W'] + t['L'] + t['T'])) <= .0005, t['abbr']

# The published model spread is a home *winning margin*, positive when home is
# favored. A sportsbook home spread is a signed handicap (negative when favored).
# Home value under the hypothetical handicap = model home margin + home handicap.
rows = []
for g in lines:
    handicap = g['market_spread_home']
    correct = round(g['model_spread_home'] + handicap, 2) if handicap is not None else None
    shown = g['edge_pts']
    if handicap is not None:
        assert round(g['model_spread_home'] - handicap, 2) == shown, g['game']
    rows.append({
        'game': g['game'], 'source_url': g['game_url'],
        'official_market_handicap': None,
        'official_market_edge': None,
        'published_candidate': g['candidate'],
        'published_gate_g4': g['gates']['G4_injury_news_check']['status'],
        'published_gate_g6': g['gates']['G6_edge_vs_market']['status'],
        'published_gate_g1': g['gates']['G1_official_sources_only']['status'],
        # Diagnostic ONLY: the third-party, unverified handicap is not published
        # as an official value. This field is NOT an actionable trading edge.
        'diagnostic_sign_error_pts': round(shown-correct, 2) if shown is not None else None,
        'sign_flips_side': ((shown > 0) != (correct > 0)) if shown is not None and correct != 0 else None,
    })

assert all(g['market_verified'] is False for g in lines)
assert sum(g['candidate'] for g in lines) == 2
assert all(g['gates']['G4_injury_news_check']['status'] == 'CONDITIONAL' for g in lines)
assert all(g['gates']['G1_official_sources_only']['status'] == 'PASS' for g in lines)
assert all(b['realized_pts'] == 0 for b in board['standings'])
report = {
    'audit_date': '2026-11-04',
    'scope': 'Independent static/code audit of the committed 2026-11-03 Week 9 snapshot; NOT a live official-source data refresh or exhaustive external verification.',
    'checks': {'standings_arithmetic_rows': 32, 'schedule_join_rows': 15,
               'model_rows': 15, 'non_null_unverified_market_rows': sum(g['market_spread_home'] is not None for g in lines),
               'published_candidates_with_unverified_market': sum(g['candidate'] and not g['market_verified'] for g in lines),
               'g4_conditional_rows': sum(g['gates']['G4_injury_news_check']['status'] == 'CONDITIONAL' for g in lines),
               'sign_error_rows': sum(r['diagnostic_sign_error_pts'] not in (None, 0) for r in rows)},
    'rows': rows,
    'findings': [
        {'id':'A-01', 'severity':'critical', 'finding':'Spread sign convention is reversed in scripts/analyze.py: model_spread_home is home winning margin (+ for home), while market_spread_home is the signed home handicap (- for home favorite). Code subtracts handicap; correct diagnostic expression is model margin + handicap. All 6 displayed comparisons using the unverified third-party market are arithmetically invalid; 6 flip preferred side. Published candidates CIN at ATL and NYG at PHI are not valid edge calls. Leave market/edge blank pending official sportsbook verification.', 'official_source':'https://www.nfl.com/schedules/2026/by-week/week-9', 'code':'scripts/analyze.py:market_spread_home / edge assignment'},
        {'id':'A-02', 'severity':'critical', 'finding':'The two published candidates pass G1 and G6 despite market_verified=false and G4=CONDITIONAL. The user requires every gate to pass; conditional is not PASS. Publication of an unverified betting edge violates the blank-if-unconfirmed rule. Hold all actionable selections.', 'official_source':'https://www.nfl.com/injuries/league/2026/reg9', 'code':'scripts/analyze.py:gates / all_pass / candidate'},
        {'id':'A-03', 'severity':'high', 'finding':'The official NFL Week 9 injury report is now present and lists practice participation for Jaguars and Ravens (including Lamar Jackson); the live site says it has not been published and still uses Week 8. Practice status is not a game status. Recheck each game before making a selection.', 'official_source':'https://www.nfl.com/injuries/league/2026/reg9', 'code':'data/flagged.json:F-04 / pages/injuries.html'},
        {'id':'A-04', 'severity':'high', 'finding':'The leaderboard claims automatic grading after official scores post, but scripts/analyze.py writes realized_pts=0.0 for every strategy on each run and contains no outcome fetch/settlement loop; projected edge is an unverified-market aggregate. Rank is list order, not skill-based. Use blank for ungraded results and label competition unlaunched until out-of-sample outcomes exist.', 'official_source':'https://www.nfl.com/scores/2026/week-9', 'code':'scripts/analyze.py:leaderboard assignment'},
        {'id':'A-05', 'severity':'medium', 'finding':'Cross-sectional correlations across 32 teams (pass YDS/game vs PF/game) are not measured same-game QB-prop/total correlations. Different games do not guarantee zero correlation when weather, team, or market factors are shared. Do not pass the same-game or parlay correlation gate on these proxies; measure paired historical bet-outcome legs and uncertainty.', 'official_source':'https://www.nfl.com/stats/team-stats/', 'code':'scripts/analyze.py:correlations / S6 / S7'},
        {'id':'A-06', 'severity':'medium', 'finding':'As written the site rebuilds from frozen JSON captures; there is no automated official-source fetch or refreshed grading. A source link only establishes provenance, not current accuracy. Date each snapshot and require freshness failures rather than claiming unattended current picks.', 'official_source':'https://www.nfl.com/standings/', 'code':'scripts/analyze.py:load / G2 / leaderboard'},
    ]
}
(OUT/'results.json').write_text(json.dumps(report, indent=2)+'\n')

def e(v): return html.escape(str(v), quote=True)
def official_link(url): return f'<a href="{e(url)}" rel="noopener noreferrer" target="_blank">NFL source ↗</a>'
finding_rows = ''.join(f'<tr><td>{e(f["id"])}</td><td>{e(f["severity"])}</td><td>{e(f["finding"])}</td><td>{e(f["code"])}</td><td>{official_link(f["official_source"])}</td></tr>' for f in report['findings'])
game_rows = ''.join(f'<tr><td>{e(r["game"])}</td><td>{"Yes — INVALID" if r["published_candidate"] else "No"}</td><td>— unverified</td><td>— unverified</td><td>{e(r["diagnostic_sign_error_pts"]) if r["diagnostic_sign_error_pts"] is not None else "—"}</td><td>{official_link(r["source_url"])}</td></tr>' for r in rows)
site = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Own8 · Independent Audit</title><style>
:root{{font-family:system-ui,-apple-system,sans-serif;color:#17243b;background:#f5f7fa}}*{{box-sizing:border-box}}body{{margin:0}}header{{background:#10233c;color:white;padding:2rem max(1.2rem,calc((100vw - 1100px)/2))}}header a{{color:#add3ff}}main{{max-width:1100px;margin:auto;padding:1.5rem 1.2rem 3rem}}h1{{font-size:clamp(1.7rem,4vw,2.5rem);margin:.2rem 0}}h2{{margin-top:2rem}}.panel{{background:white;border:1px solid #d9e2ed;border-radius:12px;padding:1.2rem;margin:1rem 0}}.alert{{border-left:6px solid #ba3333}}.muted{{color:#4f6176}}.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:.75rem;text-align:left;vertical-align:top;border-bottom:1px solid #d9e2ed;font-size:.9rem}}th{{background:#e7edf5}}a{{color:#135cb2}}.tag{{color:#9b2525;font-weight:bold}}code{{overflow-wrap:anywhere}}footer{{font-size:.85rem;color:#4f6176}}</style></head><body>
<header><a href="../index.html">← Main dashboard</a><h1>Independent verification audit</h1><p>2026-11-04 · Review findings; do not treat model lines as actionable bets.</p></header><main>
<div class="panel alert"><strong>Selection hold.</strong> No Week 9 bet passes all seven gates on the committed snapshot: market inputs are unverified, the sign convention is wrong, and the injury gate is conditional. The site’s two “candidates” are invalid as published. This audit is a separate report; the main site has not yet been corrected.</div>
<div class="panel"><strong>Scope:</strong> static code/data checks only. Rechecked selected values on the <a href="https://www.nfl.com/standings/">official NFL standings</a> (BUF 6–1–0, 233 PF/181 PA; NE 5–3–0, 184/162), <a href="https://www.nfl.com/schedules/2026/by-week/week-9">Week 9 schedule</a> (JAX at BAL Nov 5; CIN at ATL Nov 8) and <a href="https://www.nfl.com/injuries/league/2026/reg9">Week 9 injury report</a> (now present, JAX/BAL practice entries). These are spot checks, NOT external line-by-line source verification of every row. Internal arithmetic passed for 32 standing rows; 15 schedules joined. No independent sportsbook source was verified. <a href="results.json">Machine-readable audit</a>.</div>
<h2>Flagged for review</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Severity</th><th>Evidence &amp; requested remedy</th><th>Repository location</th><th>Official source</th></tr></thead><tbody>{finding_rows}</tbody></table></div>
<h2>Per-game gate audit</h2><p class="muted">Official NFL game links support matchups, NOT market numbers. The market and edge columns remain blank by rule. “Sign error” is only the algebraic discrepancy between two calculations on the same <em>unverified</em> input; it is not a verified edge.</p><div class="scroll"><table><thead><tr><th>Game</th><th>Published candidate</th><th>Verified market</th><th>Verified edge</th><th>Sign error (pts; diagnostic)</th><th>Official game source</th></tr></thead><tbody>{game_rows}</tbody></table></div>
<div class="panel"><strong>Next steps for integration owner:</strong> correct the handicap conversion, invalidate existing edges/candidates, make conditional/unverified gates fail closed, refresh official Week 9 injuries, implement genuine outcome grading, and estimate paired leg correlations before enabling parlays. Rebuild the primary dashboard, executive summary and flagged page together. Until then, this audit is the visible warning.</div>
<footer>Research only · No real-money wagers or guaranteed skill. Every row links to an official NFL page for the underlying matchup/data; calculated diagnostics are explicitly distinguished from official values.</footer></main></body></html>'''
(OUT/'index.html').write_text(site+'\n')
print(json.dumps(report['checks'], indent=2))
print('Wrote audit/results.json and audit/index.html (canonical site untouched)')
