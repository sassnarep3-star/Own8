#!/usr/bin/env python3
"""W5 — Rebuild the origination dashboard for the Week 10 state (session e8155046).

New pages: executive-summary.html, w10-lines.html, suggestions.html, questions.html.
Refreshed: index, leaderboard, correlations, props, luck, backtest, game-log, standings-check,
flagged, sources — all from the W1-W9 results. w9-lines.html stays as the frozen Week 9 record
built by build_pages.py (never regenerated here).

Every table row carries at least one official nfl.com / nextgenstats.nfl.com source link
(enforced by check_links.py). Static HTML, no JavaScript, no external assets.
"""
import html
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, DATA, OUT, SCORES_URL, STANDINGS_URL, DIVISION_URL, TEAM_URL, ABBR_TO_SLUG  # noqa: E402
from build_pages import E, link, badge, table, f1, f3, pv, J, week_links, git_first_commit  # noqa: E402

NGS = "https://nextgenstats.nfl.com/stats/passing/2026/REG/{w}"
SCHED9 = "https://www.nfl.com/schedules/2026/by-week/week-9"
SCHED10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJ9 = "https://www.nfl.com/injuries/league/2026/reg9"
INJ10 = "https://www.nfl.com/injuries/league/2026/reg10"
REPO = "https://github.com/sassnarep3-star/Own8"
CROSSCHECK = REPO + "/blob/main/requirements/results/week10-lines.json"
NGS_WEEKS = [1, 3, 4, 5, 6, 7, 8]
EVAL0 = [3, 4, 5, 6, 7, 8]
EVAL1 = [3, 4, 5, 6, 7, 8, 9]

NAV = [("index.html", "Summary"), ("executive-summary.html", "Executive summary"),
       ("w10-lines.html", "Week 10 lines"), ("leaderboard.html", "Leaderboard"),
       ("correlations.html", "Correlations"), ("props.html", "QB props"), ("luck.html", "Skill vs luck"),
       ("backtest.html", "Backtest"), ("game-log.html", "Game log"), ("standings-check.html", "Standings check"),
       ("suggestions.html", "Suggestions"), ("questions.html", "Questions"), ("flagged.html", "Flagged for review"),
       ("sources.html", "Sources &amp; method")]


def page(fname, title, body, built):
    nav = "".join(f'<a href="{h}" class="{"on" if h == fname else ""}">{t}</a>' for h, t in NAV)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — Own8 line origination lab</title><link rel="stylesheet" href="assets/style.css"></head><body>
<header><h1>Own8 · NFL line origination lab (2026, through Week 10)</h1><p>Official NFL data only · walk-forward validated · no sportsbook inputs · session e8155046 (W1–W10 data; framework from 4bc92a5f)</p></header>
<nav>{nav}</nav><main><h2 style="margin-top:4px">{E(title)}</h2>{body}</main>
<footer>Built {E(built)} from <a href="{REPO}/tree/main/origination">origination/</a> · reproduce: <code>python3 origination/scripts/build_gamelog_w10.py && python3 origination/scripts/model_w10.py && python3 origination/scripts/build_pages_w10.py && python3 origination/scripts/check_links.py</code> · <a href="../">Own8 main dashboard</a></footer>
</body></html>
"""
    with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
        f.write(doc)


def gate_cell(v):
    return badge("✓", "ok") if v is True else badge("✗", "bad") if v is False else badge("n/a", "na")


def main():
    gl = J("games-2026-w1-w9.json", DATA)
    w2 = J("w2-checks.json")
    recon = J("standings-reconciliation-2026-11-14.json")
    lb0 = J("leaderboard.json")            # original W3-W8 run (4bc92a5f)
    val = J("validation-w10.json")         # refreshed W3-W9 gate matrix
    lbw = J("leaderboard-w10.json")        # refreshed points-only ranking
    corr = J("correlations-w10.json")
    lk = J("luck-w10.json")
    w10 = J("w10-lines.json")
    xc = J("w10-crosscheck.json")
    wf = J("walkforward-games-w10.json")
    wp = J("walkforward-props-w10.json")
    built = subprocess.run(["date", "-u", "+%Y-%m-%d %H:%M UTC"], capture_output=True, text=True).stdout.strip()
    w9_commit = git_first_commit("origination/results/w9-lines.json")
    w10_commit = git_first_commit("origination/results/w10-lines.json")
    S = {b["id"]: b for b in val["strategies"]}
    S0 = {b["id"]: b for b in lb0["strategies"]}
    n_pass = sum(1 for b in val["strategies"] if b["verdict"] == "PASS")
    medals = {r["id"]: r["medal"] for r in lbw["rows"]}
    cmap = {c["id"]: c for c in corr["correlations"]}
    luck = lk["summary"]

    # ------------------------------------------------ flags (results/flagged.json + flagged.html)
    w8bal = [l for l in open(os.path.join(DATA, "raw-ngs-passing-transcription.txt"), encoding="utf-8")
             if l.startswith("8|") and "|BAL|" in l]
    flags = [
        {"id": "OF-01", "type": "unverified (blank)", "item": "Next Gen Stats Week 2 passing table",
         "detail": "The official page rendered only the NGS logo shell on 4 attempts; Week 2 QB rows are left blank and excluded from prop work.",
         "links": [NGS.format(w=2)]},
        {"id": "OF-02", "type": "source irregularity", "item": "Week 1 NE@SEA section heading",
         "detail": "nfl.com labels the game 'Sunday Night Football, September 9th', but 2026-09-09 is a Wednesday. Recorded verbatim.",
         "links": [SCORES_URL.format(w=1), "https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1"]},
        {"id": "OF-03", "type": "unverified label", "item": "Kickoff time zone",
         "detail": "Schedule renders label kickoff times 'LOCAL' without naming a time zone (Weeks 9 and 10); times are shown exactly as rendered. Root data/schedule-2026-week9.json labels the same times ET — not confirmed by the page itself.",
         "links": [SCHED9, SCHED10]},
        {"id": "OF-04", "type": "inferred label (values verified)", "item": "Two unlabeled standings columns",
         "detail": "The standings legend does not name columns 14 and 16. Their values equal each team's non-conference record and last-5 record for 32/32 teams (512/512 cells in results/standings-reconciliation-2026-11-14.json); the labels are inferred, the values are official.",
         "links": [STANDINGS_URL]},
        {"id": "OF-05", "type": "coverage gap", "item": "NGS lists only qualifying passers",
         "detail": "Some team-weeks have no NGS row (e.g. TB Week 7; JAX and TB Week 8). These team-games are excluded, never filled.",
         "links": [NGS.format(w=7), NGS.format(w=8)]},
        {"id": "OF-06", "type": "conditional", "item": "Week 10 QB prop lines",
         "detail": "Each line assumes the team's most recent NGS passer (Weeks 1, 3–8) starts. Starters are not confirmed by an official source here; check the official injury report before use.",
         "links": [INJ10, NGS.format(w=8)]},
        {"id": "OF-07", "type": "model limitation", "item": "Week 10 lines ignore injuries and QB changes",
         "detail": "Ratings use final scores only. Example: per NGS, BAL's Week 8 passer was " + (w8bal[0].split("|")[1] if w8bal else "n/a") +
                   "; a score-only model cannot price such changes.",
         "links": [NGS.format(w=8), INJ10]},
        {"id": "OF-08", "type": "validation", "item": "Strategy validation status (W3–W9 refresh)",
         "detail": (f"{n_pass} of {len(val['strategies'])} strategies passed all eight gates on the extended W3–W9 window "
                    f"(original W3–W8 run: 0 of 12; the Week 9 slate drove the change). Passing = statistically detectable skill "
                    "vs pre-registered naive baselines on official scores — NOT profit: no market prices exist, so ROI/EV is never computed. "
                    f"Best: S6 (win probability), skill {S['S6']['skill_pct']:+.2f}%, Holm p = {S['S6']['p_holm']:.4f}."),
         "links": [SCORES_URL.format(w=w) for w in EVAL1]},
        {"id": "OF-09", "type": "not scored", "item": "Market-dependent strategies (incl. root dashboard candidates)",
         "detail": "No official source publishes sportsbook prices, so any 'edge vs book' strategy fails G8 here. The root dashboard's candidates rely on data/market-lines.json (flagged unverified by earlier sessions).",
         "links": [REPO + "/blob/main/data/market-lines.json", "https://sassnarep3-star.github.io/Own8/audit/"]},
        {"id": "OF-10", "type": "source irregularity", "item": "nfl.com transient renders",
         "detail": "First render of the Week 2 scores page showed 9 games as 'Hidden Score'; one Week 6 render was an empty skeleton. Re-fetching the same official URLs showed all values; every score is confirmed by the 512/512 standings reconciliation.",
         "links": [SCORES_URL.format(w=2), SCORES_URL.format(w=6)]},
        {"id": "OF-11", "type": "process irregularity", "item": "Parallel-session coordination",
         "detail": "Multiple sessions claim root integration; PRs #36–#38 merged while this session's board claim was unpushed to main, producing two independent Week 10 origins (see OF-18). This session rebased onto main and force-updated only its own branch once after the initial push was rejected.",
         "links": [REPO + "/pull/37", REPO + "/pull/38", REPO + "/blob/main/COORDINATION.md"]},
        {"id": "OF-12", "type": "cosmetic", "item": "Rams abbreviation",
         "detail": "nfl.com renders the Rams as LA in some views and LAR in others (Week 9: scores page LAR, schedule page LA — same games, same scores). Root data and this lab use LAR; the cross-check maps LA↔LAR. Same team; values agree.",
         "links": [SCORES_URL.format(w=9), SCHED9]},
        {"id": "OF-13", "type": "unverified (blank)", "item": "Next Gen Stats Week 9 passing table",
         "detail": "https://nextgenstats.nfl.com/stats/passing/2026/REG/9 rendered empty (logo shell only) on 4 attempts on 2026-11-14, while Week 8 renders normally. Week 9 QB props are therefore not evaluable; the prop evaluation window stays Weeks 4–8. No values were filled.",
         "links": [NGS.format(w=9), NGS.format(w=8)]},
        {"id": "OF-14", "type": "excluded from lines", "item": "Week 10 Thursday game already played",
         "detail": "WAS 24, NYG 21 (Thursday, November 12th) was final before origination. It is excluded from the 13 Week 10 lines to avoid grading a known result, recorded under w10-lines.json → excluded_completed, and its result is on the Week 10 scores page.",
         "links": [SCORES_URL.format(w=10)]},
        {"id": "OF-15", "type": "source irregularity", "item": "Injuries page week/URL mismatch",
         "detail": "The official injuries capture at URL .../injuries/league/2026/reg9 renders the page title '2026 Injuries' (league year) while the path says reg9 (2025). The 2026 injuries page was used only for manual starter checks, never as a data input.",
         "links": [INJ9, INJ10]},
        {"id": "OF-16", "type": "coverage gap", "item": "No official depth-chart pages",
         "detail": "nfl.com returns 404 for /depth-charts/ and /teams/<team>/depth-chart/ (checked 2026-11-14). Roster pages exist but list no depth ordering. String-level depth (2nd/3rd-string replacements) therefore cannot be confirmed officially and is left blank — never inferred.",
         "links": ["https://www.nfl.com/teams/baltimore-ravens/roster/", "https://www.nfl.com/depth-charts/"]},
        {"id": "OF-17", "type": "label hazard (fixed forward)", "item": "Week 9 spread text label (REQ-F-01)",
         "detail": "results/w9-lines.json renders fair_spread_text from the favourite's perspective while the numeric field is the home margin — a labelling hazard flagged by session f6e60a81. That frozen file is never edited; the Week 10 output carries explicit fields (fair_spread_favourite_text, fair_spread_favourite_team, fair_handicap_home_pts, fair_home_margin_S1) so the perspectives cannot be confused.",
         "links": [SCORES_URL.format(w=9), SCHED10]},
        {"id": "OF-18", "type": "process irregularity", "item": "Two independent Week 10 origins",
         "detail": "This session's board claim (2026-11-14 01:03 UTC) and session f6e60a81's PR #38 (merged 01:08 UTC) both originated Week 10 lines without seeing each other's section. Both are published: theirs in requirements/results/week10-lines.json (B0 rate benchmark + Elo), this lab's in results/w10-lines.json (walk-forward ridge). Cross-check: favourite side agrees 13/13; mean home-margin difference 0.2 points.",
         "links": [SCHED10, CROSSCHECK]},
        {"id": "W9-IR-1", "type": "source irregularity", "item": "Week 9 Rams renders as LA or LAR",
         "detail": "Week 9 final scores page renders the Rams as LAR; the Week 9 schedule page renders LA. Values identical (NYG 19–11 PHI; LAR 20–13 WAS). Recorded in results/w9-checks.json; abbreviations mapped in the cross-check.",
         "links": [SCORES_URL.format(w=9), SCHED9]},
        {"id": "OF-19", "type": "coordination", "item": "Board claim not on main before PR #38",
         "detail": "This session's COORDINATION.md claim section reached main only with its own PR; sessions reading main before that could not see it. The race is documented in the board log; the standing fix is the claim-then-push-immediately rule (claim was pushed within ~4 minutes, but PR #38 merged before the next main sync).",
         "links": [REPO + "/blob/main/COORDINATION.md"]},
    ]
    for r in w2.get("irregularities", []):
        flags.append({"id": "OF-X", "type": "data check", "item": r.get("game", "w2 check"),
                      "detail": r.get("detail", ""), "links": [r.get("source", SCORES_URL.format(w=9))]})
    with open(os.path.join(OUT, "flagged.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "session e8155046 origination lab (W1-W10)", "flags": flags}, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # ------------------------------------------------ index (dashboard landing)
    cards = [
        ("Official games verified", f'{sum(g["verified"] for g in gl["games"])}/{len(gl["games"])}', "Weeks 1–9, nfl.com scores", "game-log.html"),
        ("Standings cells reconciled", f'{recon["cells_matching"]}/{recon["cells_total"]}', "32 teams × 16 columns", "standings-check.html"),
        ("Strategies passing all gates", f"{n_pass}/{len(val['strategies'])}", "Gold S6 · Silver S1 · Bronze S7", "leaderboard.html"),
        ("Week 10 games originated", str(len(w10["games"])), "spread · total · moneyline (prospective)", "w10-lines.html"),
        ("Cross-check vs requirements/", f'{xc["favourite_agrees"]}/{xc["games_compared"]}', "favourite agreement, two origins", "w10-lines.html"),
        ("Luck share of win% variance", f'{luck["luck_share_of_variance"] * 100:.0f}%', f'after {luck["avg_games"]:.1f} games per team', "luck.html"),
        ("Flagged items", str(len(flags)), "published, non-blocking", "flagged.html"),
    ]
    cards_html = '<div class="cards">' + "".join(
        f'<div class="card"><div class="k">{E(k)}</div><div class="v">{E(v)}</div><div class="d">{E(d)}</div><a class="more" href="{h}">Open →</a></div>'
        for k, v, d, h in cards) + "</div>"
    top_games = sorted(w10["games"], key=lambda g: -abs(g["fair_home_margin_S1"]))[:3]
    body = cards_html + f"""
<h2>What changed at Week 10</h2>
<ol>
<li><b>Data.</b> The verified game log now covers Weeks 1–9: {len(gl["games"])} games, every score confirmed against the
{recon["cells_total"]}-cell standings reconciliation (W9 slate independently matched the schedule transcription 15/15).
Week 10 schedule transcribed: 14 games + 4 byes; the Thursday game (WAS 24–21 NYG) was already final and is excluded from lines (OF-14).</li>
<li><b>Validation refresh (W3–W9).</b> The same 12 pre-registered strategies were re-evaluated on 104 walk-forward games.
<b>{n_pass} now pass all eight gates</b> — {", ".join(E(r["id"]) + " " + E(r["medal"]) for r in lbw["rows"] if r["medal"])} —
whereas the original W3–W8 run passed 0 of 12. Both halves of the window are positive for all four passers (G6), and Holm-adjusted
permutation p ≤ {max(S[r["id"]]["p_holm"] for r in lbw["rows"] if r["medal"]):.4f}. The Week 9 slate drove most of the improvement;
Week 10 is the prospective test (see <a href="executive-summary.html">Executive summary</a>).</li>
<li><b>Week 10 fair lines</b> (no vig, no market input), trained on all 136 W1–W9 games. Largest fair spreads:
{", ".join(E(g["away"] + " @ " + g["home"] + ": " + g["fair_spread_favourite_text"]) for g in top_games)}.
Committed in <code>{E(w10_commit)}</code>, before Sunday kickoff. Status: PROSPECTIVE / UNVALIDATED.</li>
<li><b>Two origins, one slate.</b> Session f6e60a81 independently originated the same 13 games (B0 + Elo). Side-by-side:
favourite agrees 13/13, mean home-margin difference 0.2 points — published together on <a href="w10-lines.html">Week 10 lines</a> (OF-18).</li>
<li><b>Luck still dominates.</b> {luck["luck_share_of_variance"] * 100:.0f}% of win% variance is binomial noise after {luck["avg_games"]:.1f} games per team;
{luck["one_score_games"]} of {luck["games"]} games decided by ≤ 8 points. Skill, where it exists, is small and recent — see
<a href="luck.html">Skill vs luck</a>.</li>
<li><b>Still impossible from official sources:</b> any market edge (no official prices exist), any depth-chart string
(no official depth pages — OF-16), and Week 9 QB props (NGS empty render — OF-13).</li>
</ol>
<div class="note"><b>How to read this site.</b> Every table row links to the official page(s) behind it. Values that could not be confirmed are
left blank and listed on <a href="flagged.html">Flagged for review</a>. Nothing here is a betting recommendation: medals recognise
walk-forward skill vs naive baselines on official scores, and no price, edge or return is ever computed.</div>
<h2>Pages</h2>
""" + table(["Page", "What it shows"], [
        [link("executive-summary.html", "Executive summary"), "The important details in one place: data, validation, lines, gaps"],
        [link("w10-lines.html", "Week 10 lines"), "13 prospective fair lines, excluded Thursday game, cross-check vs requirements/, ratings"],
        [link("leaderboard.html", "Leaderboard"), "12 strategies × 8 gates: original W3–W8 run + W3–W9 refresh with medals"],
        [link("correlations.html", "Correlations"), "Same-game, cross-game and player-prop correlations, plus fair combo prices"],
        [link("props.html", "QB props"), "Conditional Week 10 QB passing-yard lines, prop backtest W4–W8, every NGS row used"],
        [link("luck.html", "Skill vs luck"), "Luck share of standings, Pythagorean expected wins, one-score records, ratings"],
        [link("backtest.html", "Backtest"), "Every walk-forward prediction for Weeks 3–9 next to the actual result"],
        [link("game-log.html", "Game log"), "136 official games with score-page and game-page links"],
        [link("standings-check.html", "Standings check"), "32 teams: official standings vs values recomputed from the game log"],
        [link("suggestions.html", "Suggestions"), "Pickable improvement paths for the site before implementation"],
        [link("questions.html", "Questions"), "What must be answered before any decision: have / lack / discovery path"],
        [link("flagged.html", "Flagged for review"), "Unverified, inferred, conditional and irregular items"],
        [link("sources.html", "Sources & method"), "Every official URL used, models, gates, statistics, reproduction"],
        [link("w9-lines.html", "Week 9 lines (frozen)"), "Historical Week 9 origin, committed pre-kickoff; never regenerated"],
    ])
    page("index.html", "Summary", body, built)

    # ------------------------------------------------ executive summary
    medal_rows = [[str(r["rank"]), E(r["id"]), E(r["medal"]), E(r["product"]),
                   f'{r["skill_pct"]:+.2f}%', f'{r["skill_pct_lcb"]:+.2f}%',
                   pv(S[r["id"]]["p_holm"]), str(S[r["id"]]["n"]),
                   link(SCORES_URL.format(w=9), "scores W9") + " · " + link(SCORES_URL.format(w=10), "scores W10")]
                  for r in lbw["rows"] if r["medal"]]
    data_rows = [
        ["Game log W1–W9", f'{sum(g["verified"] for g in gl["games"])}/{len(gl["games"])} games verified, 0 failed checks',
         link(SCORES_URL.format(w=9), "scores W9") + " · " + link(STANDINGS_URL, "standings")],
        ["Standings reconciliation", f'{recon["cells_matching"]}/{recon["cells_total"]} cells recompute from the log (incl. Thursday post-cutoff game for WAS/NYG)',
         link(STANDINGS_URL, "standings")],
        ["W9 slate vs schedule", "15/15 finals match the November 4th schedule transcription (independent check)",
         link(SCHED9, "schedule W9")],
        ["W10 slate", f'{len(w10["games"])} lines originated + 1 completed game excluded; 4 byes; Munich international game rendered neutral',
         link(SCHED10, "schedule W10")],
    ]
    body = f"""
<div class="note"><b>Purpose.</b> Everything a reviewer needs to decide what to trust, in one place. Every number below links to the official
source or the machine-readable file behind it. Full detail lives on the linked pages.</div>
<h3>1. Data integrity</h3>
{table(["Check", "Result", "Official source"], data_rows)}
<h3>2. Validation: {n_pass} of 12 strategies pass all gates (W3–W9 refresh)</h3>
<p>The original run (Weeks 3–8, committed pre-Week-9) passed 0 of 12. Extending the walk-forward window to include Week 9 flips four
singles strategies to PASS under the <i>same pre-registered gates</i> — G1–G8 unchanged, Holm across the same family of 12, seed 20261104,
both halves of the window positive. The Week 9 slate was strongly model-favourable (see the backtest), so treat this as a
<b>promising but recent</b> result: Week 10 is the prospective confirmation test, and parlays (S9, Holm p = {S["S9"]["p_holm"]:.3f})
and props (S11/S12) still fail.</p>
{table(["Rank", "ID", "Medal", "Product", "Skill", "Skill LCB", "Holm p", "n", "Official source"], medal_rows, num=(4, 5, 6, 7))}
<p class="muted">Medals are research recognition for gate-passing strategies — not profit. No market price exists in any official source,
so no ROI, edge or expected value is computed anywhere on this site (gate G8 / M1–M2 not scored).</p>
<h3>3. The Week 10 slate</h3>
<ol>
<li><b>13 prospective lines</b> trained on all 136 verified games: e.g. {E(top_games[0]["away"] + " @ " + top_games[0]["home"])} at
{E(top_games[0]["fair_spread_favourite_text"])}, total {top_games[0]["fair_total_S4"]:.1f}. The neutral Munich game carries no home edge.
Committed <code>{E(w10_commit)}</code> before Sunday kickoff; grade only after finals (pre-registered protocol: <a href="suggestions.html">SG-09</a>).</li>
<li><b>Thursday excluded:</b> WAS 24–21 NYG was final before origination (OF-14) — recorded, never graded as a line.</li>
<li><b>Cross-check:</b> f6e60a81's independent B0 origin agrees on the favourite in {xc["favourite_agrees"]}/{xc["games_compared"]} games;
mean home-margin difference {sum(abs(r["home_margin_diff_S1_minus_B0"]) for r in xc["rows"]) / len(xc["rows"]):.2f} points.
Two different models, one conclusion — side-by-side on <a href="w10-lines.html">Week 10 lines</a>.</li>
</ol>
<h3>4. Luck and correlations (what strategy can and cannot claim)</h3>
<ol>
<li><b>{luck["luck_share_of_variance"] * 100:.0f}% of win% variance is luck</b> after {luck["avg_games"]:.1f} games per team; true-talent spread ≈ ±{luck["true_talent_sd_win_pct"] * 100:.0f} win-pct points.
Naive season point-diff ratings (S3) remain <i>worse</i> than the baseline ({S0["S3"]["skill_pct"]:+.1f}% originally, {S["S3"]["skill_pct"]:+.1f}% now) — chasing records is betting on luck.</li>
<li><b>Combo-relevant correlations surviving Holm:</b> QB yards↔own points {cmap["C5"]["r"]:+.2f}, QB yards↔game total {cmap["C6"]["r"]:+.2f},
opposing QBs' yards {cmap["C9"]["r"]:+.2f}, QB attempts↔own margin {cmap["C8"]["r"]:+.2f}. Same-game side vs total does <b>not</b> survive
(raw p = {cmap["C2"]["p_two_sided"]:.3f}); cross-game ICC ≈ 0 → cross-game parlays multiply legs, same-game legs need the joint-probability adjustment (<a href="correlations.html">Correlations</a>).</li>
<li><b>Conditional QB props</b> for Week 10 (26 team-games) assume the most recent NGS passer starts; NGS Week 9 is an empty render (OF-13),
so prop evaluation stays W4–W8 and both prop strategies still fail their gates.</li>
</ol>
<h3>5. What is deliberately missing (never inferred)</h3>
<ol>
<li><b>Market prices / edges</b> — no official NFL source publishes sportsbook lines; all price fields are null (OF-09).</li>
<li><b>Depth-chart strings</b> — official depth-chart URLs 404 (OF-16); 2nd/3rd-string status stays blank.</li>
<li><b>Week 9 NGS rows</b> — 4 empty renders (OF-13); blank, excluded from prop work.</li>
<li><b>Named kickoff time zones</b> — rendered as "LOCAL" only (OF-03).</li>
<li><b>Starter confirmation</b> — props are conditional; the injuries page is the official check (OF-06).</li>
</ol>
<h3>6. Open decisions</h3>
<p>Before acting on any of this, the blocking questions — with what we have, what we lack, and how to discover it — are on
<a href="questions.html">Questions</a>; pickable improvement paths are on <a href="suggestions.html">Suggestions</a>.</p>
"""
    page("executive-summary.html", "Executive summary", body, built)

    # ------------------------------------------------ Week 10 lines + cross-check
    rows = []
    for g in w10["games"]:
        rows.append([E(g["day"]) + "<br><span class='muted'>" + E(g["time_as_rendered"]) + " (as rendered) · " + E(g["network"]) + "</span>",
                     f"{E(g['away'])} @ {E(g['home'])}" + (" " + badge("neutral (Munich)", "warn") if g["neutral_site"] else ""),
                     f"<b>{E(g['fair_spread_favourite_text'])}</b>", f"{g['fair_home_margin_S1']:+.1f}", f"{g['fair_home_margin_S2']:+.1f}",
                     f"<b>{g['fair_total_S4']:.1f}</b>", f"{g['away_pts_S4']:.1f}–{g['home_pts_S4']:.1f}",
                     f"{g['p_home_S6'] * 100:.1f}%", f"{g['fair_ml_away']:+d} / {g['fair_ml_home']:+d}",
                     badge("prospective", "warn"), link(g["game_url"], "game") + " · " + link(g["source_url"], "schedule")])
    exc = [[E(x["away"]) + " @ " + E(x["home"]), E(x["reason"]), link(x["result_source_url"], "scores W10") + " · " + link(x["game_url"], "game")]
           for x in w10["excluded_completed"]]
    xc_rows = []
    for r in xc["rows"]:
        xc_rows.append([E(r["away"]) + " @ " + E(r["home"]),
                        f'{r["home_margin_origination_S1"]:+.2f}', f'{r["home_margin_crosscheck_B0"]:+.2f}', f'{r["home_margin_diff_S1_minus_B0"]:+.2f}',
                        E(r["favourite_origination"]) + (" ✓" if r["favourite_agrees"] else " ✗"),
                        f'{r["total_origination_S4"]:.1f}', f'{r["total_crosscheck_B0"]:.1f}', f'{r["total_diff_S4_minus_B0"]:+.1f}',
                        f'{r["p_home_origination_S6"]:.3f} / {r["p_home_crosscheck_normal"]:.3f}',
                        link(r["source_url_origination"], "schedule")])
    m = w10["model"]
    body = f"""<div class="note"><b>Status: PROSPECTIVE — UNVALIDATED.</b> Fair (no-vig) lines originated only from the {len(gl["games"])} verified
Week 1–9 results; no market input; committed <code>{E(w10_commit)}</code> before Sunday kickoff. Injuries, QB changes, weather and rest are not priced (OF-06/OF-07).
The already-played Thursday game is excluded (OF-14). S1 verdict {E(S["S1"]["verdict"])}, S4 {E(S["S4"]["verdict"])} on the W3–W9 refresh.</div>
""" + table(["Kickoff", "Matchup", "Fair spread (favourite, S1)", "Home margin S1", "Home margin S2", "Fair total (S4)", "Proj. score A–H",
             "Home win prob", "Fair ML away / home", "Status", "Official source"], rows, num=(3, 4, 5, 7)) + f"""
<p class="muted">Spread is shown for the favourite (negative = gives points) — explicit fields in the JSON: fair_spread_favourite_text /
fair_spread_favourite_team / fair_handicap_home_pts (home perspective) / fair_home_margin_S1 (home perspective) — REQ-F-01 fixed forward (OF-17).
Home edge S1 {m["S1_hfa"]:+.2f} pts, S2 {m["S2_home_edge"]:+.2f} pts, set to 0 for the neutral Munich game. Win probability = Φ(margin / σ), σ = {m["S1_sigma_loo"]:.2f}.
Totals: S4, σ = {m["S2_sigma_total"]:.2f}. Ridge λ by exact LOO-CV: S1 {m["S1_lambda"]}, S2 {m["S2_lambda"]}. Trained on {m["trained_on"]}.</p>
<h3>Excluded: completed before origination</h3>
""" + table(["Game", "Reason", "Official source"], exc) + f"""
<h3>Cross-check vs session f6e60a81's independent origin (requirements/results/week10-lines.json)</h3>
<div class="note">Two independent official-data origins for the same slate: this lab's walk-forward ridge (S1/S4/S6) vs B0 points-rate
benchmark + Elo. Favourite agrees <b>{xc["favourite_agrees"]}/{xc["games_compared"]}</b>; neither is validated — disagreements are facts
about model choice, not errors (OF-18). Machine-readable: <a href="results/w10-crosscheck.json">results/w10-crosscheck.json</a>.</div>
""" + table(["Game", "Home margin S1", "Home margin B0", "Δ (S1−B0)", "Favourite (S1 / agree)", "Total S4", "Total B0", "Δ",
             "p(home) S6 / B0", "Official source"], xc_rows, num=(1, 2, 3, 5, 6, 7, 8)) + f"""
<h3>Team ratings behind the lines (fit on Weeks 1–9)</h3>
""" + table(["#", "Team", "S1 rating (pts vs avg)", "S2 offence (pts)", "S2 defence (pts allowed vs avg)", "Official source"],
            [[str(i + 1), E(r["team"]), f"{r['rating_S1']:+.2f}", f"{r['off_S2']:+.2f}", f"{r['def_S2_points_allowed_above_avg']:+.2f}",
              link(TEAM_URL.format(slug=ABBR_TO_SLUG[r["team"]]), "team") + " · " + link(STANDINGS_URL, "standings")]
             for i, r in enumerate(m["ratings"])], num=(2, 3, 4))
    page("w10-lines.html", "Week 10 fair lines", body, built)

    # ------------------------------------------------ leaderboard (original run + refresh)
    def lb_table(strategies, eval_weeks, ngs_weeks=None, show_rank=True):
        out = []
        for b in strategies:
            src = week_links(eval_weeks) if b["id"] not in ("S11", "S12") else week_links(ngs_weeks or NGS_WEEKS, NGS)
            lo, hi = -b["ci95"][1] / b["loss_baseline"] * 100, -b["ci95"][0] / b["loss_baseline"] * 100
            rank = (medals.get(b["id"]) or ("#" + str(b["rank"]) if b.get("rank") else "—")) if show_rank else "—"
            out.append([E(rank), E(b["id"]), E(b["product"]), f'<span class="wrap">{E(b["strategy"])}</span>', str(b["n"]),
                        f"{b['loss_model']:.3f}", f"{b['loss_baseline']:.3f}", f"{b['skill_pct']:+.2f}%",
                        f"[{lo:+.2f}%, {hi:+.2f}%]", pv(b["p_one_sided"]), pv(b["p_holm"]),
                        " ".join(gate_cell(b["gates"].get(g)) for g in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8")),
                        badge(b["verdict"], "ok" if b["verdict"] == "PASS" else "bad"), src])
        return out

    hdr = ["Rank", "ID", "Product", "Strategy", "n", "Model loss", "Baseline loss", "Skill", "Skill 95% CI", "p (1-sided)", "Holm p",
           "Gates G1–G8", "Verdict", "Official source (evaluation weeks)"]
    rows_now = lb_table(val["strategies"], EVAL1)
    rows_orig = lb_table(lb0["strategies"], EVAL0, ngs_weeks=NGS_WEEKS)
    ns = [[E(x["id"]), E(x["product"]), E(x["strategy"]), badge("G8 ✗", "bad"), E(x["verdict"]),
           link("https://www.nfl.com/", "nfl.com (no odds published)")] for x in val["not_scored"]]
    cal = []
    for sid in ("S6", "S7", "S8"):
        for t in S[sid]["calibration_table"]:
            cal.append([E(sid), E(t["bin"]), str(t["n"]), f3(t["mean_pred"]), f3(t["observed"]), week_links(EVAL1)])
    best = lbw["rows"][0]
    body = f"""<div class="note"><b>Current leaderboard (W3–W9 refresh): {n_pass} of {len(val["strategies"])} strategies passed every gate —
medals awarded: {", ".join(E(r["medal"]) + " " + E(r["id"]) for r in lbw["rows"] if r["medal"])}.</b>
Ranking uses the <i>lower</i> 95% bound of the skill score, so a lucky point estimate cannot win. The original pre-Week-9 run
(W3–W8) passed 0 of 12 and is preserved below for comparison. Passing ≠ profit: no market prices exist, so ROI is never computed (G8 / M1–M2).</div>
<h3>Current: walk-forward W3–W9 ({sum(1 for r in wf["games"])} games, refreshed 2026-11-14)</h3>
""" + table(hdr, rows_now, num=(4, 5, 6, 7, 9, 10)) + f"""
<p class="muted">Loss: absolute error (spreads, totals, props) or Brier score (moneyline, parlays). Baseline: league home edge and league average total
(props: league average passing yards), re-estimated each week from prior weeks only. Skill = % loss reduction vs baseline. p = sign-flip permutation
(10,000 draws, seed 20261104). Holm correction across all 12 strategies. Evaluation: Weeks 3–9 (104 games), halves W3–W6 / W7–W9,
parlays on 51 disjoint same-week pairs, props on Weeks 4–8 (146 QB-games; NGS W9 empty — OF-13).</p>
<h3>Original run: walk-forward W3–W8 (committed 2026-11-08, preserved)</h3>
""" + table(hdr, rows_orig, num=(4, 5, 6, 7, 9, 10)) + """
<p class="muted">Same gates, same family, same seed, one week less of data: 0 of 12 passed. The difference between the two runs is the
Week 9 slate — a reminder that gate-passing at n≈104 is fragile and must be confirmed out-of-sample (Week 10, then W11+).</p>
<h3>Gates (fixed before results were seen)</h3>
""" + table(["Gate", "Rule", "Implemented in"], [[E(a), E(b), link("scripts/model_w10.py", "scripts/model_w10.py")] for a, b in [
        ("G1 official data", "Every row is a verified official row (fail-closed game log)"),
        ("G2 no leakage", "Week w is predicted only from weeks < w (asserted in code)"),
        ("G3 sample size", "≥ 80 games (singles) · ≥ 40 independent pairs (parlays) · ≥ 100 player-games (props)"),
        ("G4 skill", "Bootstrap 95% CI of mean loss difference lies entirely below 0"),
        ("G5 multiplicity", "Holm-adjusted one-sided permutation p < 0.05 across the family"),
        ("G6 stability", "Improvement in both halves of the evaluation window (W3–W6 and W7–W9)"),
        ("G7 calibration", "Probability products: expected calibration error ≤ 0.10"),
        ("G8 no market data", "Can be priced and settled without sportsbook odds")]]) + """
<h3>Not scored (market-dependent)</h3>""" + table(["ID", "Product", "Strategy", "Gate", "Status", "Source"], ns) + """
<h3>Calibration of probability strategies (walk-forward W3–W9)</h3>""" + table(["Strategy", "Predicted bin", "n", "Mean predicted", "Observed home win rate", "Official source"], cal, num=(2, 3, 4)) + f"""
<p class="muted">Machine-readable: <a href="results/validation-w10.json">validation-w10.json</a> (gate matrix),
<a href="results/leaderboard-w10.json">leaderboard-w10.json</a> (ranking), <a href="results/leaderboard.json">leaderboard.json</a> (original run).</p>"""
    page("leaderboard.html", "Strategy leaderboard (validation gates)", body, built)

    # ------------------------------------------------ correlations
    def csrc(c):
        return week_links([1, 3, 4, 5, 6, 7, 8], NGS) + " + " + week_links([1, 3, 4, 5, 6, 7, 8]) if c["id"] in ("C5", "C6", "C7", "C8", "C9") else week_links(list(range(1, 10)) if c["id"] == "C1" else EVAL1)
    rows = [[E(c["id"]), E(c["pair"]), str(c["n"]), f"{c['r']:+.3f}", f"[{c['ci95'][0]:+.2f}, {c['ci95'][1]:+.2f}]", pv(c["p_two_sided"]), pv(c["p_holm"]),
             badge("yes", "ok") if c["significant_after_holm"] else badge("no", "na"), f'<span class="wrap">{E(c["use"])}</span>', csrc(c)]
            for c in corr["correlations"]]
    icc = [[E(c["id"]), E(c["pair"]), str(c["n"]), f"{c['icc']:+.3f}", E(c["use"]), week_links(EVAL1)] for c in corr["cross_game_dependence"]]
    combo = [[E(c["id"]), E(c["combo"]), f"{c['r_used']:+.3f}", f"{c['joint_prob_both_over'] * 100:.1f}%", f"{c['fair_odds']:+d}",
              f"{c['independent_odds']:+d}", E(c["note"]), csrc(cmap[c["id"]])] for c in corr["combo_pricing"]]
    body = table(["ID", "Pair", "n", "r", "95% CI", "p (2-sided)", "Holm p", "Significant after Holm", "Use", "Official source"], rows, num=(2, 3, 5, 6)) + """
<p class="muted">Refreshed on the W1–W9 log (C1 n=136; residual C2–C4 n=104 walk-forward; player rows n=204 team-weeks with exactly one NGS passer,
Weeks 1, 3–8 — NGS W9 empty, OF-13). Residual correlations use walk-forward errors only.</p>
<h3>Cross-game dependence</h3>""" + table(["ID", "Quantity", "n", "ICC", "Use", "Official source"], icc, num=(2, 3)) + """
<h3>Fair combo prices (both legs over their own median lines)</h3>""" + table(
        ["ID", "Combo", "r used", "Joint probability", "Fair odds", "If independent", "Note", "Official source"], combo, num=(2, 3, 4, 5)) + \
        '<p class="muted">Joint probability = 1/4 + asin(r)/(2π) under a bivariate normal, at each leg\'s own median line. Correlations that do not survive Holm are priced as independent.</p>'
    page("correlations.html", "Correlation library", body, built)

    # ------------------------------------------------ props (W10 conditional + backtest + NGS rows)
    pr = [[E(p["team"]) + " vs " + E(p["opp"]), E(p["qb_conditional"]), "W" + str(p["qb_last_seen_week"]), f"{p['fair_pass_yds_S11']:.1f}",
           f"{p['fair_pass_yds_S12']:.1f}", badge("conditional", "warn") + " " + badge("prospective", "warn"),
           link(p["source_url"], "NGS") + " · " + link(p["game_url"], "game") + " · " + link(INJ10, "injuries")]
          for p in w10["qb_props_conditional"]]
    ngs_rows = []
    for line in open(os.path.join(DATA, "raw-ngs-passing-transcription.txt"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        w, name, team, att, yds, td, it = line.rstrip("\n").split("|")
        ngs_rows.append(["W" + w, E(name), E(team), att, yds, td, it, link(NGS.format(w=w), "NGS W" + w)])
    bt = [["W" + str(r["week"]), E(r["player"]), E(r["team"]) + " vs " + E(r["opp"]), str(r["actual_yds"]), f1(r["pred_P0"]), f1(r["pred_S11"]), f1(r["pred_S12"]),
           link(r["source_url"], "NGS") + " · " + link(r["game_url"], "game")] for r in wp["props"]]
    body = f"""<div class="note">QB passing-yard lines for Week 10 are <b>conditional</b> on the listed passer starting (most recent NGS row, Weeks 1/3–8).
They are also <b>prospective and unvalidated</b>: S11 {E(S["S11"]["verdict"])}, S12 {E(S["S12"]["verdict"])} on the W3–W9 refresh — neither beats the
league-average baseline. NGS Week 9 is an empty render (OF-13), so no Week 9 props exist. Starters: check the official injury report (OF-06).</div>
""" + table(["Game", "QB (conditional)", "Last NGS week", "Fair yds S11", "Fair yds S12", "Status", "Official source"], pr, num=(3, 4)) + """
<h3>Prop backtest (walk-forward, Weeks 4–8)</h3>""" + table(["Week", "QB", "Game", "Actual yds", "Baseline", "S11", "S12", "Official source"], bt, num=(3, 4, 5, 6)) + """
<h3>Every Next Gen Stats row used (Weeks 1, 3–8; Week 2 and Week 9 not captured)</h3>""" + table(["Week", "Player", "Team", "ATT", "YDS", "TD", "INT", "Official source"], ngs_rows, num=(3, 4, 5, 6))
    page("props.html", "QB passing-yard props", body, built)

    # ------------------------------------------------ luck
    rows = [[E(t["team"]), E(t["record"]), f"{t['win_pct']:.3f}", str(t["PF"]), str(t["PA"]), f"{t['pythag_win_pct']:.3f}", f"{t['expected_wins']:.2f}",
             f"{t['luck_wins']:+.2f}", E(t["one_score_record"]), E(t["other_record"]), f"{t['rating_S1']:+.2f}",
             link(STANDINGS_URL, "standings") + " · " + link(TEAM_URL.format(slug=ABBR_TO_SLUG[t["team"]]), "team")] for t in lk["teams"]]
    body = '<div class="cards">' + "".join(f'<div class="card"><div class="k">{E(k)}</div><div class="v">{E(v)}</div><div class="d">{E(d)}</div></div>' for k, v, d in [
        ("Luck share of win% variance", f"{luck['luck_share_of_variance'] * 100:.0f}%", "binomial noise ÷ observed variance"),
        ("True-talent SD", f"±{luck['true_talent_sd_win_pct'] * 100:.1f} pts", "win-percentage points"),
        ("One-score games", f"{luck['one_score_games']}/{luck['games']}", "margin ≤ 8 points"),
        ("Pythagorean exponent", f"{luck['pythag_exponent_fitted']:.2f}", f"fitted; r = {luck['r_pythag_vs_actual']:.2f} vs actual")]) + "</div>" + \
        table(["Team", "Record", "Win%", "PF", "PA", "Pythag win%", "Expected wins", "Luck wins", "One-score W-L-T", "Other W-L-T", "S1 rating", "Official source"],
              rows, num=(2, 3, 4, 5, 6, 7, 10)) + f'<p class="muted">{E(luck["method"])} Positive luck wins = record better than points scored and allowed imply. Refreshed on W1–W9 (was 60% at W1–W8 — luck share falls as games accumulate).</p>'
    page("luck.html", "Skill vs luck in the 2026 standings", body, built)

    # ------------------------------------------------ backtest (W3-W9)
    rows = [["W" + str(r["week"]), f"{E(r['away'])} @ {E(r['home'])}" + (" " + badge("neutral", "warn") if r["neutral"] else ""), f"{r['actual_margin']:+d}",
             f"{r['m_B']:+.1f}", f"{r['m_S1']:+.1f}", f"{r['m_S2']:+.1f}", f"{r['m_S3']:+.1f}", str(r["actual_total"]), f"{r['t_B']:.1f}", f"{r['t_S4']:.1f}",
             f"{r['p_S6'] * 100:.0f}%", str(r["train_games"]), link(r["source_url"], "scores W" + str(r["week"])) + " · " + link(r["game_url"], "game")] for r in wf["games"]]
    body = table(["Week", "Game", "Actual home margin", "Baseline", "S1", "S2", "S3", "Actual total", "Baseline total", "S4 total", "S6 home win", "Training games", "Official source"],
                 rows, num=(2, 3, 4, 5, 6, 7, 8, 9, 10, 11)) + '<p class="muted">Each prediction uses only games from earlier weeks (G2). Weeks 3–9, 104 games. The Week 9 slate is strongly model-favourable — see the leaderboard note on recency.</p>'
    page("backtest.html", "Walk-forward backtest (Weeks 3–9)", body, built)

    # ------------------------------------------------ game log (W1-W9)
    rows = [["W" + str(g["week"]), E(g["date"] or ""), f'<span class="wrap">{E(g["heading"])}</span>', E(g["away"]), str(g["away_score"]), E(g["home"]), str(g["home_score"]),
             badge("international", "warn") if g["international"] else "", E(g["winner_indicator"] if g["winner_indicator"] != "NONE" else "tie"),
             badge("verified", "ok") if g["verified"] else badge("unverified", "bad"),
             link(g["source_url"], "scores W" + str(g["week"])) + " · " + link(g["game_url"], "game")]
            for g in gl["games"]]
    byes = [["W" + str(b["week"]), E(b["team"]), E(b["record_shown"]), link(SCORES_URL.format(w=b["week"]), "scores W" + str(b["week"]))] for b in gl["byes"]]
    body = table(["Week", "Date", "Heading (verbatim)", "Away", "Pts", "Home", "Pts", "Site", "Winner (nfl.com indicator)", "Status", "Official source"], rows, num=(4, 6)) + \
        "<h3>Teams on bye (box shows current record at capture)</h3>" + table(["Week", "Team", "Record shown", "Official source"], byes)
    page("game-log.html", "Official game log, Weeks 1–9", body, built)

    # ------------------------------------------------ standings check
    rows = []
    for t in recon["teams"]:
        c = {x["column"].split(" ")[0]: x for x in t["cells"]}
        ok = sum(x["match"] for x in t["cells"])
        rows.append([E(t["team"]), f'{c["W"]["official"]}-{c["L"]["official"]}-{c["T"]["official"]}', c["PCT"]["official"], c["PF"]["official"], c["PA"]["official"],
                     c["NET"]["official"], c["HOME"]["official"], c["ROAD"]["official"], c["DIV"]["official"], c["CONF"]["official"], c["STRK"]["official"],
                     c["col14"]["official"], c["col16"]["official"], badge(f"{ok}/{len(t['cells'])}", "ok" if ok == len(t["cells"]) else "bad"),
                     link(STANDINGS_URL, "standings") + " · " + link(t["team_url"], "team")])
    body = f"""<div class="good">All {recon["cells_matching"]} of {recon["cells_total"]} official standings cells equal the values recomputed from the
W1–W9 game log (recon = W1–W9 log + the completed Thursday game for WAS/NYG only). Division membership comes from
{link(DIVISION_URL, 'the division standings page')}.</div>""" + table(
        ["Team", "W-L-T", "PCT", "PF", "PA", "NET", "HOME", "ROAD", "DIV", "CONF", "STRK", "Col 14 (= non-conf.)", "Col 16 (= last 5)", "Match", "Official source"], rows, num=(2, 3, 4, 5)) + \
        '<p class="muted">Values shown are nfl.com\'s. Columns 14 and 16 are unlabeled in the source legend; their meaning was inferred because all 32 teams match (OF-04).</p>'
    page("standings-check.html", "Standings reconciliation", body, built)

    # ------------------------------------------------ suggestions (pickable paths)
    sg = [
        ["SG-01", "Automate the weekly capture", "A reviewer should not depend on a human transcription each week; the fail-closed builder pattern already exists for W1–W9.",
         "Medium", "origination/scripts/ (add build_gamelog_w11…), data/ raw transcriptions", "None — pattern proven (114 checks, 0 failed)",
         link(SCORES_URL.format(w=10), "scores W10")],
        ["SG-02", "Keep two origins per slate (standing cross-check)", "Two independent models agreeing (13/13 favourites at W10) is the strongest validation available without prices; disagreement is diagnostic.",
         "Low", "origination/results/w10-crosscheck.json + requirements/results/ (read-only)", "Coordination note already in COORDINATION.md (OF-18)",
         link(SCHED10, "schedule W10")],
        ["SG-03", "Condition props on the official injury report", "Props currently assume the most recent NGS passer starts; the official injuries page is the only pre-game official starter signal.",
         "Low", "origination/scripts/model_w10.py (condition text + flag OF-06)", "Injuries page must render for the week (reg10 exists; reg9 title mismatch OF-15)",
         link(INJ10, "injuries W10")],
        ["SG-04", "Capture starter names from official Game Book / post-game official recaps", "Depth-chart pages 404 (OF-16); the official post-game documents are the only official depth evidence — useful for retroactively validating conditional props.",
         "Medium", "origination/data/ (new raw capture), results/ (validation of conditions)", "Manual official-document retrieval (no API)",
         link("https://www.nfl.com/games/", "nfl.com game center")],
        ["SG-05", "Retry NGS for missing weeks on a schedule", "W2 and W9 rendered empty while other weeks render fine — a retry ladder would recover props coverage without ever filling values.",
         "Low", "flagged OF-01 / OF-13 only", "None", link(NGS.format(w=9), "NGS W9")],
        ["SG-06", "Root dashboard nav links to origination pages", "The reviewer's landing page (root index) should reach this lab in one click; root pages/ is owned by the integration session — request, don't edit.",
         "Low", "pages/index.html (integration session), COORDINATION.md request", "Integration session availability (60-min rule)",
         link("../", "Own8 main dashboard") + " · " + link("https://www.nfl.com/", "nfl.com")],
        ["SG-07", "Keep all price/edge fields null until an official price source exists", "Any UI that shows an edge without an official price would violate the never-infer rule; the null + unavailable_reason pattern already does this.",
         "Low", "results/w10-lines.json (already null), pages (already blank cells)", "None — current state is correct",
         link(REPO + "/blob/main/data/market-lines.json", "market-lines.json (unverified)") + " · " + link("https://www.nfl.com/", "nfl.com")],
        ["SG-08", "Batch Pages deploys (≈10 builds/hour soft limit)", "The site went 'errored' earlier from build pacing; batching pushes/merges keeps the live site green.",
         "Low", "push/merge cadence; .github/workflows (root, integration-owned)", "None", link(REPO + "/actions", "Actions") + " · " + link(SCORES_URL.format(w=10), "scores W10")],
        ["SG-09", "Pre-register the Week 10 grading protocol now", "Grading after seeing results invites hindsight; the protocol (same gates, same family, both origins) must be fixed before kickoff.",
         "Low", "this page + COORDINATION.md", "None — pre-registered here 2026-11-14",
         link(SCORES_URL.format(w=10), "scores W10 (after MNF Nov 16)")],
        ["SG-10", "Request named time zones from the schedule render", "'LOCAL' cannot be converted officially (OF-03); until nfl.com names the zone, times stay as rendered.",
         "Low", "flagged OF-03 (already)", "Upstream nfl.com change (out of our control)",
         link(SCHED10, "schedule W10")],
        ["SG-11", "Continue walk-forward into W11+ before trusting medals", "S9 missed G5 by a hair (Holm 0.10) and the four medals rest on a model-friendly Week 9; more weeks are the only honest arbiter.",
         "Medium", "origination/scripts/model_w10.py (EVAL_WEEKS += w)", "Week 10+ finals",
         link(SCORES_URL.format(w=9), "scores W9")],
        ["SG-12", "Keep Flagged-for-review in the root nav", "Irregularities must stay one click from the landing page (root nav already links data/flagged.json; keep both in sync).",
         "Low", "pages/ (integration), data/flagged.json + origination/results/flagged.json", "Integration session",
         link("flagged.html", "this lab's flagged page") + " · " + link(STANDINGS_URL, "standings")],
    ]
    body = '<div class="note">Pickable improvement paths for this site and lab, each with effort, scope, prerequisite and the official source it depends on. ' \
           'Nothing here has been implemented yet — a reviewer chooses; implementation follows the parallel-session claim protocol.</div>' + \
           table(["ID", "Suggestion", "Why it matters", "Effort", "Files / scope", "Prerequisite", "Official source"], sg)
    page("suggestions.html", "Suggestions (pick before implementation)", body, built)

    # ------------------------------------------------ questions (blocking decisions)
    qs = [
        ["Q-01", "Can any line be called profitable? (blocks: bankroll, staking, 'beat the book' claims)",
         "Fair lines, walk-forward skill vs naive baselines, calibration, Holm-controlled p-values.",
         "Official sportsbook prices (spread/total/juice) — no official NFL source publishes them.",
         "Not answerable within the official-source rule: edge/EV stay null; strategies M1–M2 not scored (G8).",
         "If an official NFL odds page ever appears, capture it like scores; otherwise the question stays closed by policy (never infer).",
         link("https://www.nfl.com/", "nfl.com (no odds page)")],
        ["Q-02", "Who starts at QB in Week 10? (blocks: unconditional prop lines, injury-adjusted spreads)",
         "Injuries page (reg10), NGS last-seen passers (W1/3–8), roster pages (no depth order).",
         "Official depth chart (404) and pre-game starter confirmation.",
         "Conditional only: every prop names its assumption (OF-06); lines are score-only (OF-07).",
         "Check the official injury report before kickoff; use official post-game documents to grade conditions afterwards (SG-04).",
         link(INJ10, "injuries W10")],
        ["Q-03", "Is the new gate-passing skill real or Week-9 luck? (blocks: trusting medals, escalating any strategy)",
         "104-game walk-forward, both halves positive, Holm p ≤ 0.0054 for all four passers, original run 0/12 documented.",
         "Out-of-sample weeks beyond W9 (the W9 slate alone flipped the board).",
         "Open: promising, not confirmed. Week 10 is the pre-registered prospective test (SG-09).",
         "Grade all 13 W10 lines after MNF Nov 16 with the same gates; repeat at W11+ (SG-11).",
         link(SCORES_URL.format(w=10), "scores W10")],
        ["Q-04", "Which origin is 'the' Week 10 line? (blocks: publishing a single number)",
         "Two independent origins; favourite agrees 13/13; mean home-margin Δ 0.2 pts; max Δ 1.6 pts.",
         "An adjudicator (neither model is validated yet).",
         "Publish both side-by-side (current w10-lines page); grade both after finals.",
         "Compare both against W10 finals; keep the cross-check as a standing artefact (SG-02).",
         link(SCHED10, "schedule W10")],
        ["Q-05", "Do parlays and props have any skill? (blocks: expanding medal claims beyond singles)",
         "S9 skill +6.38% but Holm 0.10 and half1 +0.001 (fails G5/G6); S11/S12 negative skill; n = 51 pairs / 146 player-games.",
         "More weeks (G3 samples) and NGS W9/W10 renders for props.",
         "No: currently fail-closed, listed transparently on the leaderboard.",
         "Continue walk-forward (SG-11); retry NGS (SG-05).",
         link(NGS.format(w=9), "NGS W9")],
        ["Q-06", "What do kickoff times mean exactly? (blocks: any schedule-dependent automation)",
         "Times exactly as rendered ('LOCAL', e.g. 9:30 AM for Munich).",
         "A named time zone on the page.",
         "Not answerable from the page; shown as rendered (OF-03); root data's ET label is unconfirmed.",
         "Watch for an nfl.com legend change; do not convert until then (SG-10).",
         link(SCHED10, "schedule W10")],
        ["Q-07", "Are the unlabeled standings columns what we think? (blocks: using col14/col16 in analysis)",
         "Arithmetic proof: 512/512 cells equal non-conf record and last-5 record for all 32 teams.",
         "An official legend naming the columns.",
         "Values official, labels inferred (OF-04) — usable with the caveat.",
         "Re-check the legend after each standings render; no other official source exists.",
         link(STANDINGS_URL, "standings")],
        ["Q-08", "Which team's depth is 2nd/3rd-string depleted? (blocks: backup-adjusted lines, injury-deficiency strategy)",
         "Roster pages (official, unordered), official injuries page (designations).",
         "Official depth ordering (depth-chart URLs 404).",
         "Blank + flagged (OF-16); no string-level claim is made anywhere on this site.",
         "Use official post-game documents for retro depth evidence (SG-04); watch for an official depth page.",
         link("https://www.nfl.com/teams/baltimore-ravens/roster/", "roster page")],
        ["Q-09", "Should the root dashboard link this lab? (blocks: reviewer navigation)",
         "Claim + PR from this session; root pages/ owned by integration session.",
         "Integration session's decision/timing.",
         "Requested in COORDINATION.md; not edited unilaterally (protocol).",
         "Integration session adds nav links (SG-06) or merges this session's request.",
         link("../", "root dashboard") + " · " + link(SCORES_URL.format(w=10), "scores W10")],
        ["Q-10", "Is Week 9 NGS data recoverable? (blocks: W9 prop grading, full prop window)",
         "4 empty renders on 2026-11-14; Week 8 renders fine (control).",
         "A working render of REG/9.",
         "Not answerable now: blank, excluded (OF-13); evaluation stays W4–W8.",
         "Scheduled retries (SG-05); if it never renders, the gap stays permanently flagged.",
         link(NGS.format(w=9), "NGS W9")],
    ]
    body = '<div class="note">Questions that must be answered before any decision can be made from this data — with what we have, what we lack, ' \
           'the current answer (or why none exists), and a suggested way to discover the missing information. Nothing here was guessed.</div>' + \
           table(["ID", "Question (blocks what)", "What we HAVE", "What we LACK", "Answer now", "Suggested discovery path", "Official source"], qs)
    page("questions.html", "Questions (answer before deciding)", body, built)

    # ------------------------------------------------ flagged
    rows = [[E(f["id"]), badge(f["type"], "warn"), E(f["item"]), f'<span class="wrap">{E(f["detail"])}</span>', "<br>".join(link(u) for u in f["links"])] for f in flags]
    body = '<div class="note">Items here are published for manual review. They do not block publication. Nothing listed here was filled in or guessed.</div>' + \
        table(["ID", "Type", "Item", "Detail", "Links for manual review"], rows) + '<p class="muted">Machine-readable copy: <a href="results/flagged.json">results/flagged.json</a></p>'
    page("flagged.html", "Flagged for review", body, built)

    # ------------------------------------------------ sources & method
    src = [[link(SCORES_URL.format(w=w)), "Final scores, winner indicator, game links, bye boxes", str(sum(1 for g in gl["games"] if g["week"] == w)) + " games",
            "Standings reconciliation 512/512"] for w in range(1, 10)]
    src += [[link(STANDINGS_URL), "32 teams × 16 columns (as of 2026-11-14, incl. Thursday W10 game for WAS/NYG)", "32 rows", "Recomputed from game log"],
            [link(DIVISION_URL), "Division membership (8 tables × 4)", "32 teams", "Same values as league view"],
            [link(SCHED10), "Week 10 matchups, kickoff (as rendered), network, byes", "14 games + 4 byes", "Transcribed verbatim; 1 excluded as completed"],
            [link(SCHED9), "Week 9 schedule (independent check of W9 slate)", "15 games + 2 byes", "W9 finals match 15/15"]]
    src += [[link(NGS.format(w=w)), "QB ATT, YDS, TD, INT", ("empty render ×4 (OF-13)" if w == 9 else "not captured (OF-01)" if w == 2 else "rows"),
             "Week 8 matches root capture" if w == 8 else ""] for w in range(1, 10)]
    src += [[link("https://nextgenstats.nfl.com/glossary"), "Definitions of NGS columns", "", ""],
            [link(INJ10), "Week 10 starters (manual check for prop conditions; not a data input)", "", "OF-06"],
            [link(INJ9), "Week 9 injuries capture (title/URL mismatch, OF-15)", "", "manual check"],
            [link("https://www.nfl.com/depth-charts/"), "Depth charts — 404 on 2026-11-14 (OF-16)", "0", "blank + flag"],
            [link(CROSSCHECK) + " · " + link(SCHED10, "schedule W10"), "Independent Week 10 origin (session f6e60a81, read-only)", "13 lines", "cross-check 13/13 favourites"]]
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
<li><b>W10 origination:</b> fit on all 136 W1–W9 games; 13 unplayed games only; Thursday excluded (OF-14); cross-check vs requirements/results/week10-lines.json (OF-18).</li>
</ul>
<h3>Reproduce</h3><p><code>python3 origination/scripts/build_gamelog_w10.py</code> → <code>python3 origination/scripts/model_w10.py</code> → <code>python3 origination/scripts/build_pages_w10.py</code> → <code>python3 origination/scripts/check_links.py</code> (standard library only).</p>
<p class="muted">Raw verbatim transcriptions: {link(REPO + '/tree/main/origination/data', 'origination/data/')} · computed outputs: {link(REPO + '/tree/main/origination/results', 'origination/results/')}</p>"""
    page("sources.html", "Sources & method", body, built)
    print("pages built:", ", ".join(h for h, _ in NAV), "| flags:", len(flags))


if __name__ == "__main__":
    main()
