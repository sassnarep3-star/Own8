#!/usr/bin/env python3
"""O5 — Build the standalone origination dashboard (origination/*.html) from results/*.json + data/.
Every table row carries at least one official source link. Static HTML, no JavaScript, no external assets."""
import html
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, DATA, OUT, SCORES_URL, STANDINGS_URL, DIVISION_URL, TEAM_URL, ABBR_TO_SLUG, rec  # noqa: E402

NGS = "https://nextgenstats.nfl.com/stats/passing/2026/REG/{w}"
SCHED = "https://www.nfl.com/schedules/2026/by-week/week-9"
INJ = "https://www.nfl.com/injuries/league/2026/reg9"
REPO = "https://github.com/sassnarep3-star/Own8"
NAV = [("index.html", "Summary"), ("w9-lines.html", "Week 9 lines"), ("leaderboard.html", "Leaderboard"),
       ("correlations.html", "Correlations"), ("props.html", "QB props"), ("luck.html", "Skill vs luck"),
       ("backtest.html", "Backtest"), ("game-log.html", "Game log"), ("standings-check.html", "Standings check"),
       ("flagged.html", "Flagged for review"), ("sources.html", "Sources &amp; method")]
E = html.escape


def J(name, base=OUT):
    with open(os.path.join(base, name), encoding="utf-8") as f:
        return json.load(f)


def link(url, text=None):
    return f'<a href="{E(url)}">{E(text or url)}</a>'


def badge(text, kind):
    return f'<span class="b {kind}">{E(text)}</span>'


def f1(x):
    return "" if x is None else f"{x:.1f}"


def f3(x):
    return "" if x is None else f"{x:.3f}"


def pv(p):
    return "" if p is None else ("<0.0001" if p < 1e-4 else f"{p:.4f}")


def table(headers, rows, num=()):
    th = "".join(f'<th class="{"num" if i in num else ""}">{h}</th>' for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f'<td class="{"num" if i in num else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def page(fname, title, body, built):
    nav = "".join(f'<a href="{h}" class="{"on" if h == fname else ""}">{t}</a>' for h, t in NAV)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — Own8 line origination lab</title><link rel="stylesheet" href="assets/style.css"></head><body>
<header><h1>Own8 · NFL line origination lab (2026, through Week 8)</h1><p>Official NFL data only · walk-forward validated · no sportsbook inputs · session 4bc92a5f</p></header>
<nav>{nav}</nav><main><h2 style="margin-top:4px">{E(title)}</h2>{body}</main>
<footer>Built {E(built)} from <a href="{REPO}/tree/main/origination">origination/</a> · reproduce: <code>python3 origination/scripts/build_gamelog.py && python3 origination/scripts/model.py && python3 origination/scripts/build_pages.py</code> · <a href="../">Own8 main dashboard</a></footer>
</body></html>
"""
    with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
        f.write(doc)


def week_links(weeks, tmpl=SCORES_URL):
    return " ".join(link(tmpl.format(w=w), f"W{w}") for w in weeks)


def git_first_commit(path):
    try:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h %cI", "--", path], cwd=os.path.dirname(ROOT),
                             capture_output=True, text=True, check=True).stdout.strip().splitlines()
        return out[-1] if out else "uncommitted"
    except Exception:
        return "unknown"


def main():
    gl = J("games-2026-w1-w8.json", DATA)
    o1 = J("o1-checks.json")
    recon = J("standings-reconciliation.json")
    lb = J("leaderboard.json")
    corr = J("correlations.json")
    lk = J("luck.json")
    w9 = J("w9-lines.json")
    wf = J("walkforward-games.json")
    wp = J("walkforward-props.json")
    built = subprocess.run(["date", "-u", "+%Y-%m-%d %H:%M UTC"], capture_output=True, text=True).stdout.strip()
    w9_commit = git_first_commit("origination/results/w9-lines.json")
    S = {b["id"]: b for b in lb["strategies"]}
    eval_weeks = [3, 4, 5, 6, 7, 8]

    # ------------------------------------------------ flagged items (also written to results/flagged.json)
    w8bal = [l for l in open(os.path.join(DATA, "raw-ngs-passing-transcription.txt"), encoding="utf-8") if l.startswith("8|") and "|BAL|" in l]
    flags = [
        {"id": "OF-01", "type": "unverified (blank)", "item": "Next Gen Stats Week 2 passing table",
         "detail": "The official page rendered only the NGS logo shell on 4 attempts; Week 2 QB rows are left blank and excluded from prop work.",
         "links": [NGS.format(w=2)]},
        {"id": "OF-02", "type": "source irregularity", "item": "Week 1 NE@SEA section heading",
         "detail": "nfl.com labels the game 'Sunday Night Football, September 9th', but 2026-09-09 is a Wednesday. Recorded verbatim.",
         "links": [SCORES_URL.format(w=1), "https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1"]},
        {"id": "OF-03", "type": "unverified label", "item": "Week 9 kickoff time zone",
         "detail": "The schedule render labels kickoff times 'LOCAL' without naming a time zone; times are shown exactly as rendered. Root data/schedule-2026-week9.json labels the same times ET.",
         "links": [SCHED]},
        {"id": "OF-04", "type": "inferred label (values verified)", "item": "Two unlabeled standings columns",
         "detail": "The standings legend does not name columns 14 and 16. Their values equal each team's non-conference record and last-5 record for 32/32 teams (arithmetic proof in results/standings-reconciliation.json); the labels are inferred, the values are official.",
         "links": [STANDINGS_URL]},
        {"id": "OF-05", "type": "coverage gap", "item": "NGS lists only qualifying passers",
         "detail": "Some team-weeks have no NGS row (e.g. TB Week 7; JAX and TB Week 8). These team-games are excluded, never filled.",
         "links": [NGS.format(w=7), NGS.format(w=8)]},
        {"id": "OF-06", "type": "conditional", "item": "Week 9 QB prop lines",
         "detail": "Each line assumes the team's most recent NGS passer starts. Starters are not confirmed by an official source here; check the official injury report before use.",
         "links": [INJ, NGS.format(w=8)]},
        {"id": "OF-07", "type": "model limitation", "item": "Week 9 lines ignore injuries and QB changes",
         "detail": "Ratings use final scores only. Example: per NGS, BAL's Week 8 passer was " + (w8bal[0].split("|")[1] if w8bal else "n/a") +
                   "; a score-only model cannot price such changes.", "links": [NGS.format(w=8), INJ]},
        {"id": "OF-08", "type": "validation", "item": "No strategy passed all gates",
         "detail": (f"{sum(1 for b in lb['strategies'] if b['verdict'] == 'PASS')} of {len(lb['strategies'])} strategies passed G1–G8; "
                    f"Week 9 lines are published as UNVALIDATED estimates, not proven edges. Best: S1 (spread MAE {-S['S1']['skill_pct']:+.1f}% vs baseline, "
                    f"Holm p = {S['S1']['p_holm']:.2f})."),
         "links": [SCORES_URL.format(w=w) for w in eval_weeks]},
        {"id": "OF-09", "type": "not scored", "item": "Market-dependent strategies (incl. root dashboard W9 candidates)",
         "detail": "No official source publishes sportsbook prices, so any 'edge vs book' strategy fails G8 here. The root dashboard's W9 candidates rely on data/market-lines.json (flagged unverified by earlier sessions; see 74efc1ec audit).",
         "links": [REPO + "/blob/main/data/market-lines.json", "https://sassnarep3-star.github.io/Own8/audit/"]},
        {"id": "OF-10", "type": "source irregularity", "item": "nfl.com transient renders",
         "detail": "First render of the Week 2 scores page showed 9 games as 'Hidden Score'; one Week 6 render was an empty skeleton. Re-fetching the same official URLs showed all values; every score is confirmed by the 512/512 standings reconciliation.",
         "links": [SCORES_URL.format(w=2), SCORES_URL.format(w=6)]},
        {"id": "OF-11", "type": "process irregularity", "item": "Parallel-session coordination",
         "detail": "Two sessions claim root integration (5c4b8a3e, dd321bf5); open PRs #8 and #11 edit the same root files; 74efc1ec merged PRs #7/#9/#10 directly; PR #6 is stale; this session force-pushed its own branch once after rebasing its claim commit (content unchanged).",
         "links": [REPO + "/pull/6", REPO + "/pull/8", REPO + "/pull/11", REPO + "/pull/13"]},
        {"id": "OF-12", "type": "cosmetic", "item": "Rams abbreviation",
         "detail": "nfl.com scores text prints LAR (logo id LA); root data files use LA. Same team; values agree.",
         "links": [SCORES_URL.format(w=8)]},
    ]
    for r in o1.get("irregularities", []):
        if r["id"] not in ("O1-IR-date-label",):
            flags.append({"id": "OF-X", "type": "data check", "item": r["game"], "detail": r["detail"], "links": [r["source"]]})
    with open(os.path.join(OUT, "flagged.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "session 4bc92a5f origination lab", "flags": flags}, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # ------------------------------------------------ index
    s1 = S["S1"]
    luck = lk["summary"]
    cmap = {c["id"]: c for c in corr["correlations"]}
    best = sorted(lb["strategies"], key=lambda b: -b["skill_pct_lcb"])[0]
    n_pass = sum(1 for b in lb["strategies"] if b["verdict"] == "PASS")
    cards = [
        ("Official games verified", f'{sum(g["verified"] for g in gl["games"])}/{len(gl["games"])}', "Weeks 1–8, nfl.com scores", "game-log.html"),
        ("Standings cells reconciled", f'{recon["cells_matching"]}/{recon["cells_total"]}', "32 teams × 16 columns", "standings-check.html"),
        ("Strategies passing all gates", f"{n_pass}/{len(lb['strategies'])}", "no medals awarded", "leaderboard.html"),
        ("Luck share of win% variance", f'{luck["luck_share_of_variance"]*100:.0f}%', f'after {luck["avg_games"]:.1f} games per team', "luck.html"),
        ("Week 9 games originated", str(len(w9["games"])), "spread · total · moneyline", "w9-lines.html"),
        ("Flagged items", str(len(flags)), "published, non-blocking", "flagged.html"),
    ]
    cards_html = '<div class="cards">' + "".join(
        f'<div class="card"><div class="k">{E(k)}</div><div class="v">{E(v)}</div><div class="d">{E(d)}</div><a class="more" href="{h}">Open →</a></div>'
        for k, v, d, h in cards) + "</div>"
    top_games = sorted(w9["games"], key=lambda g: -abs(g["fair_margin_home_S1"]))[:3]
    body = cards_html + f"""
<h2>Executive summary</h2>
<ol>
<li><b>Data integrity.</b> All {len(gl['games'])} regular-season games of Weeks 1–8 were transcribed from nfl.com and every one of the
{recon['cells_total']} standings cells (W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, DIV%, CONF, CONF%, STRK and two unlabeled columns) recomputes exactly from the game log.
Root files <code>data/scores-2026-week8.json</code>, <code>data/standings-2026-reg-w8.json</code>, <code>data/schedule-2026-week9.json</code> and <code>data/nextgen-passing-2026-week8.json</code> agree with these fresh captures.</li>
<li><b>Leaderboard: no proven skill yet.</b> {len(lb['strategies'])} pre-registered strategies (spreads, totals, moneylines, 2-leg parlays, same-game parlays, QB passing-yard props) were tested walk-forward with no look-ahead.
<b>{n_pass} passed all eight gates.</b> The provisional leader, {E(best['id'])} ({E(best['strategy'])}), cuts error by {best['skill_pct']:.1f}% versus a no-information baseline
(raw one-sided p = {pv(best['p_one_sided'])}), but its bootstrap 95% interval includes zero and the multiplicity-adjusted p is {best['p_holm']:.2f}.
Naive "season point differential" ratings are {abs(S['S3']['skill_pct']):.0f}% <i>worse</i> than the baseline, which shows how rewarding hot records means betting on luck.</li>
<li><b>Luck dominates records.</b> After about {luck['avg_games']:.1f} games, {luck['luck_share_of_variance']*100:.0f}% of the variance in team win% is what coin-flip noise alone would produce.
{luck['one_score_games']} of {luck['games']} games were decided by 8 points or fewer. True-talent spread is about ±{luck['true_talent_sd_win_pct']*100:.0f} win-percentage points (1 SD).</li>
<li><b>Correlations that matter for combos.</b> These survive Holm correction: QB passing yards vs game total r = {cmap['C6']['r']:+.2f}; opposing QBs' yards r = {cmap['C9']['r']:+.2f};
QB yards vs own points r = {cmap['C5']['r']:+.2f}; QB attempts vs own margin r = {cmap['C8']['r']:+.2f}. So "both QBs over" is worth about +200 fair, not +300.
Same-game side vs total (r = {cmap['C2']['r']:+.2f}, raw p = {cmap['C2']['p_two_sided']:.3f}) does <i>not</i> survive correction. Different games in the same week behave as independent (ICC ≈ 0), so cross-game parlays can multiply legs.</li>
<li><b>Week 9 fair lines</b> (no vig, no market input). Largest fair spreads: {', '.join(E(g['away'] + ' @ ' + g['home'] + ': ' + g['fair_spread_text']) for g in top_games)}.
These lines are <b>unvalidated estimates</b> and do not see injuries or QB changes. First committed in <code>{E(w9_commit)}</code>, before the Thursday kickoff.</li>
<li><b>Market-edge betting cannot be verified from official sources.</b> No official NFL page publishes sportsbook prices, so "beat the book" strategies (including the root dashboard's W9 candidates) are listed but not scored (gate G8).</li>
</ol>
<div class="note"><b>How to read this site.</b> Every table row links to the official page(s) behind it. Values that could not be confirmed are left blank and listed on <a href="flagged.html">Flagged for review</a>.
Nothing here is a betting recommendation: a strategy earns a medal only after passing every gate, and none has yet.</div>
<h2>Pages</h2>
""" + table(["Page", "What it shows"], [
        [link("w9-lines.html", "Week 9 lines"), "Fair spread, total, win probability and moneyline for all 15 Week 9 games"],
        [link("leaderboard.html", "Leaderboard"), "12 strategies × 8 gates, skill scores with 95% CIs, permutation and Holm p-values, calibration"],
        [link("correlations.html", "Correlations"), "Same-game, cross-game and player-prop correlations, plus fair combo prices"],
        [link("props.html", "QB props"), "Conditional Week 9 QB passing-yard lines, prop backtest, and every NGS row used"],
        [link("luck.html", "Skill vs luck"), "Luck share of standings, Pythagorean expected wins, one-score records, ratings"],
        [link("backtest.html", "Backtest"), "Every walk-forward prediction for Weeks 3–8 next to the actual result"],
        [link("game-log.html", "Game log"), "121 official games with score-page and game-page links"],
        [link("standings-check.html", "Standings check"), "32 teams: official standings vs values recomputed from the game log"],
        [link("flagged.html", "Flagged for review"), "Unverified, inferred, conditional and irregular items"],
        [link("sources.html", "Sources & method"), "Every official URL used, models, gates, statistics, reproduction"],
    ])
    page("index.html", "Summary", body, built)

    # ------------------------------------------------ W9 lines
    v1 = S["S1"]["verdict"]
    rows = []
    for g in w9["games"]:
        rows.append([E(g["day"]) + "<br><span class='muted'>" + E(g["time_as_rendered"]) + " (as rendered) · " + E(g["network"]) + "</span>",
                     f"{E(g['away'])} @ {E(g['home'])}" + (" " + badge("neutral (Madrid)", "warn") if g["neutral_site"] else ""),
                     f"<b>{E(g['fair_spread_text'])}</b>", f"{g['fair_margin_home_S1']:+.1f}", f"{g['fair_margin_home_S2']:+.1f}",
                     f"<b>{g['fair_total_S4']:.1f}</b>", f"{g['away_pts_S4']:.1f}–{g['home_pts_S4']:.1f}",
                     f"{g['p_home_S6']*100:.1f}%", f"{g['fair_ml_away']:+d} / {g['fair_ml_home']:+d}",
                     badge("unvalidated", "warn"), link(g["game_url"], "game") + " · " + link(g["source_url"], "schedule")])
    m = w9["model"]
    body = f"""<div class="note">Fair (no-vig) lines originated only from the 121 verified Week 1–8 results. <b>Status: UNVALIDATED.</b> S1 verdict {E(v1)}, S4 verdict {E(S['S4']['verdict'])}.
They do not account for injuries, QB changes, weather or rest. First committed in <code>{E(w9_commit)}</code>.</div>
""" + table(["Kickoff", "Matchup", "Fair spread (S1)", "Home margin S1", "Home margin S2", "Fair total (S4)", "Proj. score A–H",
             "Home win prob", "Fair ML away / home", "Status", "Official source"], rows, num=(3, 4, 5, 7)) + f"""
<p class="muted">Spread is shown for the favourite (negative = gives points). Home margin = expected home minus away points. Win probability = Φ(margin / σ), with σ = {m['S1_sigma_loo']:.2f} (leave-one-out error of S1).
Home edge: S1 {m['S1_hfa']:+.2f} pts, S2 {m['S2_home_edge']:+.2f} pts; set to 0 for the neutral-site Madrid game. Totals: S4 offence/defence model, σ = {m['S2_sigma_total']:.2f}.
Ridge penalty by exact LOO-CV: S1 λ = {m['S1_lambda']}, S2 λ = {m['S2_lambda']}.</p>
<h3>Team ratings behind the lines (fit on Weeks 1–8)</h3>
""" + table(["#", "Team", "S1 rating (pts vs avg)", "S2 offence (pts)", "S2 defence (pts allowed vs avg)", "Official source"],
            [[str(i + 1), E(r["team"]), f"{r['rating_S1']:+.2f}", f"{r['off_S2']:+.2f}", f"{r['def_S2_points_allowed_above_avg']:+.2f}",
              link(TEAM_URL.format(slug=ABBR_TO_SLUG[r["team"]]), "team") + " · " + link(STANDINGS_URL, "standings")]
             for i, r in enumerate(m["ratings"])], num=(2, 3, 4))
    page("w9-lines.html", "Week 9 fair lines", body, built)

    # ------------------------------------------------ leaderboard
    def gate_cell(v):
        return badge("✓", "ok") if v is True else badge("✗", "bad") if v is False else badge("n/a", "na")
    rows = []
    for b in lb["strategies"]:
        src = week_links(eval_weeks) if not b["id"] in ("S11", "S12") else week_links([1, 3, 4, 5, 6, 7, 8], NGS)
        lo, hi = -b["ci95"][1] / b["loss_baseline"] * 100, -b["ci95"][0] / b["loss_baseline"] * 100
        rows.append([E(b["medal"] or ("#" + str(b["rank"]) if b["rank"] else "—")), E(b["id"]), E(b["product"]),
                     f'<span class="wrap">{E(b["strategy"])}</span>', str(b["n"]), f"{b['loss_model']:.3f}", f"{b['loss_baseline']:.3f}",
                     f"{b['skill_pct']:+.2f}%", f"[{lo:+.2f}%, {hi:+.2f}%]", pv(b["p_one_sided"]), pv(b["p_holm"]),
                     " ".join(gate_cell(b["gates"].get(g)) for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8")),
                     badge(b["verdict"], "ok" if b["verdict"] == "PASS" else "bad"), src])
    ns = [[E(x["id"]), E(x["product"]), E(x["strategy"]), badge("G8 ✗", "bad"), E(x["verdict"]),
           link("https://www.nfl.com/", "nfl.com (no odds published)")] for x in lb["not_scored"]]
    cal = []
    for sid in ("S6", "S7", "S8"):
        for t in S[sid]["calibration_table"]:
            cal.append([E(sid), E(t["bin"]), str(t["n"]), f3(t["mean_pred"]), f3(t["observed"]), week_links(eval_weeks)])
    body = f"""<div class="note"><b>{n_pass} of {len(lb['strategies'])} strategies passed every gate, so no medals are awarded.</b>
Ranking uses the <i>lower</i> 95% bound of the skill score, so a lucky point estimate cannot win. Failing strategies are listed in that order for transparency.</div>
""" + table(["Rank", "ID", "Product", "Strategy", "n", "Model loss", "Baseline loss", "Skill", "Skill 95% CI", "p (1-sided)", "Holm p",
             "Gates G1–G8", "Verdict", "Official source (evaluation weeks)"], rows, num=(4, 5, 6, 7, 9, 10)) + """
<p class="muted">Loss: absolute error (spreads, totals, props) or Brier score (moneyline, parlays). Baseline: league home edge and league average total
(props: league average passing yards), re-estimated each week from prior weeks only. Skill = % loss reduction vs baseline. p = sign-flip permutation (10,000 draws, seed 20261104).
Holm correction is applied across all 12 strategies. Evaluation: Weeks 3–8 (89 games), parlays on 44 disjoint same-week pairs, props on Weeks 4–8 (146 QB-games).</p>
<h3>Gates (fixed before results were seen)</h3>
""" + table(["Gate", "Rule", "Implemented in"], [[E(a), E(b), link("scripts/model.py", "scripts/model.py")] for a, b in [
        ("G1 official data", "Every row is a verified official row (fail-closed game log)"),
        ("G2 no leakage", "Week w is predicted only from weeks < w (asserted in code)"),
        ("G3 sample size", "≥ 80 games (singles) · ≥ 40 independent pairs (parlays) · ≥ 100 player-games (props)"),
        ("G4 skill", "Bootstrap 95% CI of mean loss difference lies entirely below 0"),
        ("G5 multiplicity", "Holm-adjusted one-sided permutation p < 0.05 across the family"),
        ("G6 stability", "Improvement in both halves of the evaluation window"),
        ("G7 calibration", "Probability products: expected calibration error ≤ 0.10"),
        ("G8 no market data", "Can be priced and settled without sportsbook odds")]]) + """
<h3>Not scored (market-dependent)</h3>""" + table(["ID", "Product", "Strategy", "Gate", "Status", "Source"], ns) + """
<h3>Calibration of probability strategies (walk-forward)</h3>""" + table(["Strategy", "Predicted bin", "n", "Mean predicted", "Observed home win rate", "Official source"], cal, num=(2, 3, 4))
    page("leaderboard.html", "Strategy leaderboard (validation gates)", body, built)

    # ------------------------------------------------ correlations
    def csrc(c):
        return week_links([1, 3, 4, 5, 6, 7, 8], NGS) + " + " + week_links([1, 3, 4, 5, 6, 7, 8]) if c["id"] in ("C5", "C6", "C7", "C8", "C9") else week_links(range(1, 9) if c["id"] == "C1" else eval_weeks)
    rows = [[E(c["id"]), E(c["pair"]), str(c["n"]), f"{c['r']:+.3f}", f"[{c['ci95'][0]:+.2f}, {c['ci95'][1]:+.2f}]", pv(c["p_two_sided"]), pv(c["p_holm"]),
             badge("yes", "ok") if c["significant_after_holm"] else badge("no", "na"), f'<span class="wrap">{E(c["use"])}</span>', csrc(c)]
            for c in corr["correlations"]]
    icc = [[E(c["id"]), E(c["pair"]), str(c["n"]), f"{c['icc']:+.3f}", E(c["use"]), week_links(eval_weeks)] for c in corr["cross_game_dependence"]]
    combo = [[E(c["id"]), E(c["combo"]), f"{c['r_used']:+.3f}", f"{c['joint_prob_both_over']*100:.1f}%", f"{c['fair_odds']:+d}",
              f"{c['independent_odds']:+d}", E(c["note"]), csrc(cmap[c["id"]])] for c in corr["combo_pricing"]]
    body = table(["ID", "Pair", "n", "r", "95% CI", "p (2-sided)", "Holm p", "Significant after Holm", "Use", "Official source"], rows, num=(2, 3, 5, 6)) + """
<p class="muted">Residual correlations (C2–C4) use walk-forward errors only. Player rows use team-weeks with exactly one NGS passer. Week 2 NGS is missing (see Flagged).</p>
<h3>Cross-game dependence</h3>""" + table(["ID", "Quantity", "n", "ICC", "Use", "Official source"], icc, num=(2, 3)) + """
<h3>Fair combo prices (both legs over their own median lines)</h3>""" + table(
        ["ID", "Combo", "r used", "Joint probability", "Fair odds", "If independent", "Note", "Official source"], combo, num=(2, 3, 4, 5)) + \
        '<p class="muted">Joint probability = 1/4 + asin(r)/(2π) under a bivariate normal, at each leg\'s own median line. Correlations that do not survive Holm are priced as independent.</p>'
    page("correlations.html", "Correlation library", body, built)

    # ------------------------------------------------ props
    pr = [[E(p["team"]) + " vs " + E(p["opp"]), E(p["qb_conditional"]), "W" + str(p["qb_last_seen_week"]), f"{p['fair_pass_yds_S11']:.1f}", f"{p['fair_pass_yds_S12']:.1f}",
           badge("conditional", "warn") + " " + badge("unvalidated", "warn"), link(p["source_url"], "NGS") + " · " + link(p["game_url"], "game") + " · " + link(INJ, "injuries")]
          for p in w9["qb_props_conditional"]]
    ngs_rows = []
    for line in open(os.path.join(DATA, "raw-ngs-passing-transcription.txt"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        w, name, team, att, yds, td, it = line.rstrip("\n").split("|")
        ngs_rows.append(["W" + w, E(name), E(team), att, yds, td, it, link(NGS.format(w=w), "NGS W" + w)])
    bt = [["W" + str(r["week"]), E(r["player"]), E(r["team"]) + " vs " + E(r["opp"]), str(r["actual_yds"]), f1(r["pred_P0"]), f1(r["pred_S11"]), f1(r["pred_S12"]),
           link(r["source_url"], "NGS") + " · " + link(r["game_url"], "game")] for r in wp["props"]]
    body = f"""<div class="note">QB passing-yard lines for Week 9 are <b>conditional</b> on the listed passer starting (most recent NGS row). They are also <b>unvalidated</b>:
S11 {E(S['S11']['verdict'])}, S12 {E(S['S12']['verdict'])}. In the backtest neither beat the league-average baseline.</div>
""" + table(["Game", "QB (conditional)", "Last NGS week", "Fair yds S11", "Fair yds S12", "Status", "Official source"], pr, num=(3, 4)) + """
<h3>Prop backtest (walk-forward, Weeks 4–8)</h3>""" + table(["Week", "QB", "Game", "Actual yds", "Baseline", "S11", "S12", "Official source"], bt, num=(3, 4, 5, 6)) + """
<h3>Every Next Gen Stats row used (Weeks 1, 3–8; Week 2 not captured)</h3>""" + table(["Week", "Player", "Team", "ATT", "YDS", "TD", "INT", "Official source"], ngs_rows, num=(3, 4, 5, 6))
    page("props.html", "QB passing-yard props", body, built)

    # ------------------------------------------------ luck
    rows = [[E(t["team"]), E(t["record"]), f"{t['win_pct']:.3f}", str(t["PF"]), str(t["PA"]), f"{t['pythag_win_pct']:.3f}", f"{t['expected_wins']:.2f}",
             f"{t['luck_wins']:+.2f}", E(t["one_score_record"]), E(t["other_record"]), f"{t['rating_S1']:+.2f}",
             link(STANDINGS_URL, "standings") + " · " + link(TEAM_URL.format(slug=ABBR_TO_SLUG[t["team"]]), "team")] for t in lk["teams"]]
    body = '<div class="cards">' + "".join(f'<div class="card"><div class="k">{E(k)}</div><div class="v">{E(v)}</div><div class="d">{E(d)}</div></div>' for k, v, d in [
        ("Luck share of win% variance", f"{luck['luck_share_of_variance']*100:.0f}%", "binomial noise ÷ observed variance"),
        ("True-talent SD", f"±{luck['true_talent_sd_win_pct']*100:.1f} pts", "win-percentage points"),
        ("One-score games", f"{luck['one_score_games']}/{luck['games']}", "margin ≤ 8 points"),
        ("Pythagorean exponent", f"{luck['pythag_exponent_fitted']:.2f}", f"fitted; r = {luck['r_pythag_vs_actual']:.2f} vs actual")]) + "</div>" + \
        table(["Team", "Record", "Win%", "PF", "PA", "Pythag win%", "Expected wins", "Luck wins", "One-score W-L-T", "Other W-L-T", "S1 rating", "Official source"],
              rows, num=(2, 3, 4, 5, 6, 7, 10)) + f'<p class="muted">{E(luck["method"])} Positive luck wins = record better than points scored and allowed imply.</p>'
    page("luck.html", "Skill vs luck in the 2026 standings", body, built)

    # ------------------------------------------------ backtest
    rows = [["W" + str(r["week"]), f"{E(r['away'])} @ {E(r['home'])}" + (" " + badge("neutral", "warn") if r["neutral"] else ""), f"{r['actual_margin']:+d}",
             f"{r['m_B']:+.1f}", f"{r['m_S1']:+.1f}", f"{r['m_S2']:+.1f}", f"{r['m_S3']:+.1f}", str(r["actual_total"]), f"{r['t_B']:.1f}", f"{r['t_S4']:.1f}",
             f"{r['p_S6']*100:.0f}%", str(r["train_games"]), link(r["source_url"], "scores W" + str(r["week"])) + " · " + link(r["game_url"], "game")] for r in wf["games"]]
    body = table(["Week", "Game", "Actual home margin", "Baseline", "S1", "S2", "S3", "Actual total", "Baseline total", "S4 total", "S6 home win", "Training games", "Official source"],
                 rows, num=(2, 3, 4, 5, 6, 7, 8, 9, 10, 11)) + '<p class="muted">Each prediction uses only games from earlier weeks (G2).</p>'
    page("backtest.html", "Walk-forward backtest (Weeks 3–8)", body, built)

    # ------------------------------------------------ game log
    rows = [["W" + str(g["week"]), E(g["date"] or ""), f'<span class="wrap">{E(g["heading"])}</span>', E(g["away"]), str(g["away_score"]), E(g["home"]), str(g["home_score"]),
             badge("international", "warn") if g["international"] else "", E(g["winner_indicator"] if g["winner_indicator"] != "NONE" else "tie"),
             badge("verified", "ok") if g["verified"] else badge("unverified", "bad"), link(g["source_url"], "scores W" + str(g["week"])) + " · " + link(g["game_url"], "game")]
            for g in gl["games"]]
    byes = [["W" + str(b["week"]), E(b["team"]), E(b["record_shown"]), link(SCORES_URL.format(w=b["week"]), "scores W" + str(b["week"]))] for b in gl["byes"]]
    body = table(["Week", "Date", "Heading (verbatim)", "Away", "Pts", "Home", "Pts", "Site", "Winner (nfl.com indicator)", "Status", "Official source"], rows, num=(4, 6)) + \
        "<h3>Teams on bye (box shows current record at capture)</h3>" + table(["Week", "Team", "Record shown", "Official source"], byes)
    page("game-log.html", "Official game log, Weeks 1–8", body, built)

    # ------------------------------------------------ standings check
    rows = []
    for t in recon["teams"]:
        c = {x["column"].split(" ")[0]: x for x in t["cells"]}
        ok = sum(x["match"] for x in t["cells"])
        rows.append([E(t["team"]), f'{c["W"]["official"]}-{c["L"]["official"]}-{c["T"]["official"]}', c["PCT"]["official"], c["PF"]["official"], c["PA"]["official"],
                     c["NET"]["official"], c["HOME"]["official"], c["ROAD"]["official"], c["DIV"]["official"], c["CONF"]["official"], c["STRK"]["official"],
                     c["col14"]["official"], c["col16"]["official"], badge(f"{ok}/{len(t['cells'])}", "ok" if ok == len(t["cells"]) else "bad"),
                     link(STANDINGS_URL, "standings") + " · " + link(t["team_url"], "team")])
    body = f"""<div class="good">All {recon['cells_matching']} of {recon['cells_total']} official standings cells equal the values recomputed from the game log.
Division membership comes from {link(DIVISION_URL, 'the division standings page')}.</div>""" + table(
        ["Team", "W-L-T", "PCT", "PF", "PA", "NET", "HOME", "ROAD", "DIV", "CONF", "STRK", "Col 14 (= non-conf.)", "Col 16 (= last 5)", "Match", "Official source"], rows, num=(2, 3, 4, 5)) + \
        '<p class="muted">Values shown are nfl.com\'s. Columns 14 and 16 are unlabeled in the source legend; their meaning was inferred because all 32 teams match (OF-04).</p>'
    page("standings-check.html", "Standings reconciliation", body, built)

    # ------------------------------------------------ flagged
    rows = [[E(f["id"]), badge(f["type"], "warn"), E(f["item"]), f'<span class="wrap">{E(f["detail"])}</span>', "<br>".join(link(u) for u in f["links"])] for f in flags]
    body = '<div class="note">Items here are published for manual review. They do not block publication. Nothing listed here was filled in or guessed.</div>' + \
        table(["ID", "Type", "Item", "Detail", "Links for manual review"], rows) + '<p class="muted">Machine-readable copy: <a href="results/flagged.json">results/flagged.json</a></p>'
    page("flagged.html", "Flagged for review", body, built)

    # ------------------------------------------------ sources & method
    src = [[link(SCORES_URL.format(w=w)), "Final scores, winner indicator, game links, bye boxes", str(sum(1 for g in gl["games"] if g["week"] == w)) + " games",
            "Standings reconciliation 512/512"] for w in range(1, 9)]
    src += [[link(STANDINGS_URL), "32 teams × 16 columns", "32 rows", "Recomputed from game log"],
            [link(DIVISION_URL), "Division membership (8 tables × 4)", "32 teams", "Same values as league view"],
            [link(SCHED), "Week 9 matchups, kickoff (as rendered), network, byes", "15 games + 2 byes", "Matches root capture"]]
    src += [[link(NGS.format(w=w)), "QB ATT, YDS, TD, INT", ("not captured (OF-01)" if w == 2 else "rows"), "Week 8 matches root capture" if w == 8 else ""] for w in range(1, 9)]
    src += [[link("https://nextgenstats.nfl.com/glossary"), "Definitions of NGS columns", "", ""], [link(INJ), "Referenced for starters (not captured)", "", "manual check"]]
    body = table(["Official URL", "Used for", "Rows", "Verification"], src) + f"""
<h3>Method</h3>
<ul>
<li><b>S1 margin ratings:</b> home margin = r<sub>home</sub> − r<sub>away</sub> + h (h = 0 at neutral sites), fit by ridge regression. λ is chosen each week by exact leave-one-out CV over {{0.5 … 80}}. Win probability = Φ(margin / σ<sub>LOO</sub>).</li>
<li><b>S2/S4 offence–defence model:</b> points = μ + off<sub>team</sub> + def<sub>opp</sub> ± s/2, ridge with LOO-CV. Gives both margin and total.</li>
<li><b>S3/S5 naive averages:</b> unshrunk season point differential and PF/PA per game, included to show the cost of chasing records.</li>
<li><b>Parlays (S9):</b> disjoint same-week pairs, legs priced independently. <b>Same-game parlay (S10):</b> bivariate normal with margin–total residual correlation from prior weeks.</li>
<li><b>Props (S11/S12):</b> empirical-Bayes shrinkage of QB passing yards toward the league mean (method-of-moments k), plus a shrunk opponent adjustment.</li>
<li><b>Inference:</b> paired bootstrap (10,000) for CIs, one-sided sign-flip permutation (10,000) for p-values, Holm across the family, binned calibration error. Seed 20261104.</li>
<li><b>Luck:</b> binomial variance 0.25/games vs observed win% variance; Pythagorean exponent fitted to 2026 data; one-score = margin ≤ 8.</li>
</ul>
<h3>Reproduce</h3><p><code>python3 origination/scripts/build_gamelog.py</code> → <code>python3 origination/scripts/model.py</code> → <code>python3 origination/scripts/build_pages.py</code> → <code>python3 origination/scripts/check_links.py</code> (standard library only).</p>
<p class="muted">Raw verbatim transcriptions: {link(REPO + '/tree/main/origination/data', 'origination/data/')} · computed outputs: {link(REPO + '/tree/main/origination/results', 'origination/results/')}</p>"""
    page("sources.html", "Sources & method", body, built)
    print("pages built:", ", ".join(h for h, _ in NAV), "| flags:", len(flags))


if __name__ == "__main__":
    main()
