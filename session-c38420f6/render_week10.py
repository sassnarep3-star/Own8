#!/usr/bin/env python3
"""Render the verified Week 10 result diagnostic as a static, source-linked page."""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = json.loads((HERE / "week10-diagnostic.json").read_text(encoding="utf-8"))
e = html.escape

metric_names = {
    "S1_abs_margin_error": "S1 side-model MAE (home-margin points)",
    "S2_abs_margin_error": "S2 side-model MAE (home-margin points)",
    "S3_abs_margin_error": "S3 side-model MAE (home-margin points)",
    "market_abs_margin_error": "Locked market spread MAE (home-margin points)",
    "S4_abs_total_error": "S4 total-model MAE (points)",
    "S5_abs_total_error": "S5 total-model MAE (points)",
    "market_abs_total_error": "Locked market total MAE (points)",
    "S6_brier": "S6 moneyline Brier score",
    "market_brier": "De-vigged locked market moneyline Brier score",
}
summary_rows = "".join(
    f"<tr><td>{e(metric_names[k])}</td><td>{DATA['metrics'][k]:.4f}</td><td>n = {DATA['n_final_games']}</td><td>"
    f"<a href='{e(DATA['sources']['scores_page'])}'>NFL scores ↗</a> · "
    f"<a href='{e(DATA['sources']['price_article'])}'>NFL picks prices ↗</a> · "
    f"<a href='{e('https://www.nfl.com/schedules/2026/by-week/week-10')}'>NFL schedule ↗</a></td></tr>"
    for k in metric_names
)
rows = []
for r in DATA["rows"]:
    f = r["forecasts"]
    err = r["errors"]
    rows.append(
        "<tr>"
        f"<td>{e(r['away'])} @ {e(r['home'])}</td>"
        f"<td>{r['away_score']}–{r['home_score']}</td>"
        f"<td>{r['actual_home_margin']:+d}</td><td>{r['actual_total']}</td>"
        f"<td>{f['S1_home_margin']:+.3f}</td><td>{f['S2_home_margin']:+.3f}</td><td>{f['S3_home_margin']:+.3f}</td>"
        f"<td>{f['S4_total']:.3f}</td><td>{f['S5_total']:.3f}</td><td>{f['S6_p_home']:.4f}</td>"
        f"<td>{err['S1_abs_margin_error']:.3f}</td><td>{err['S2_abs_margin_error']:.3f}</td>"
        f"<td>{err['S4_abs_total_error']:.3f}</td><td>{err['S5_abs_total_error']:.3f}</td>"
        f"<td><a href='{e(r['official_scores_url'])}'>NFL scores ↗</a> · "
        f"<a href='{e(r['official_game_center_url'])}'>Game Center ↗</a> · "
        f"<a href='{e(r['forecast_schedule_url'])}'>NFL schedule ↗</a> · "
        f"<a href='{e(r['market']['source_url'])}'>NFL picks prices ↗</a></td>"
        "</tr>"
    )

unresolved = DATA["unresolved"][0]
body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Week 10 result reconciliation · Own8</title><link rel="stylesheet" href="../assets/style.css">
<style>.scroll{{overflow:auto}} table{{min-width:1450px}} .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}} .stat{{background:white;border:1px solid #dce3ec;border-radius:9px;padding:12px}} .stat b{{display:block;font-size:1.1rem}} .caution{{padding:14px;border-left:4px solid #d99c20;background:#fff8e6;margin:16px 0}}</style></head>
<body><main style="max-width:1400px;margin:2rem auto;padding:0 1.2rem">
<p><a href="../index.html">Own8 dashboard</a> · <a href="../ledger/results-feed.html">Verified results feed</a> · <a href="../pages/flagged.html">Flagged for Review</a></p>
<h1>Week 10: official results &amp; frozen-forecast diagnostic</h1>
<p>Capture checked at <strong>{e(DATA['generated_at_utc'])}</strong>. This is a dated addendum, not a replacement for the pre-kickoff forecast snapshot.</p>
<div class="caution"><strong>Diagnostic only — not a leaderboard result.</strong> Twelve games displayed official Final scores. One Week 10 fixture remained without an observed Final score. The forecasts remain frozen as originated on {e(DATA['forecast_originated_at'])}; no gates, ranks, prizes, or strategy promotions are changed by this page.</div>
<div class="stats"><div class="stat"><b>{DATA['n_final_games']} / {DATA['n_scheduled_forecasts']}</b>Final results observed / forecasted games</div><div class="stat"><b>{DATA['n_unresolved_games_excluded']}</b>Unresolved fixture excluded from score calculations</div><div class="stat"><b>149</b>Final scores in the ledger after the append-only update</div><div class="stat"><b>0</b>ROI / CLV values produced by this diagnostic</div></div>
<h2>Point-error summary</h2><p>All values are descriptive point estimates; smaller is not evidence of durable skill. Market comparisons use the locked-Thursday FanDuel line published in the NFL picks article, not a closing line.</p>
<div class="scroll"><table><thead><tr><th>Metric</th><th>Mean score</th><th>Sample</th><th>Official source references</th></tr></thead><tbody>{summary_rows}</tbody></table></div>
<h2>Per-game audit</h2><p>Home margin = home score − away score. Total = home score + away score. S1–S3 are separate side estimators; S4 and S5 are both published total estimators; S6 is the originated home-win probability. Official source links are attached to every game row.</p>
<div class="scroll"><table><thead><tr><th>Game</th><th>Official score (away-home)</th><th>Actual home margin</th><th>Actual total</th><th>S1 fair margin</th><th>S2 fair margin</th><th>S3 fair margin</th><th>S4 fair total</th><th>S5 fair total</th><th>S6 P(home)</th><th>|S1 error|</th><th>|S2 error|</th><th>|S4 error|</th><th>|S5 error|</th><th>Official evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>Unresolved official-source state</h2><table><thead><tr><th>Fixture</th><th>Observed</th><th>Evidence</th></tr></thead><tbody><tr><td>LAC @ BAL (Week 10)</td><td>{e(unresolved['observation'])}</td><td><a href="{e(unresolved['scores_page_url'])}">NFL scores page ↗</a> · <a href="{e(unresolved['game_url'])}">NFL Game Center ↗</a> · <a href="{e(unresolved['standings_url'])}">NFL standings ↗</a></td></tr></tbody></table>
<h2>Limits and required next steps</h2><ul>{''.join('<li>'+e(x)+'</li>' for x in DATA['limitations'])}<li>Refresh and reconcile the official standings against the result addendum before refreshing opponent-aware ratings; this check was not completed here.</li><li>Retain raw source bytes and SHA-256 hashes in scheduled captures before describing any future capture as immutable.</li></ul>
<p>Sources: <a href="{e(DATA['sources']['scores_page'])}">NFL Week 10 score page ↗</a> · <a href="{e(DATA['sources']['official_standings'])}">NFL official standings ↗</a> · <a href="{e(DATA['sources']['price_article'])}">NFL Week 10 picks and FanDuel prices ↗</a></p>
<p><small>Nothing on this page is betting advice. No live wagering, monetary rewards, or future data capture are configured.</small></p>
</main></body></html>"""
(HERE / "index.html").write_text(body, encoding="utf-8")
print("Rendered", HERE / "index.html")
