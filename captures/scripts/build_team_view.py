#!/usr/bin/env python3
"""Regenerates site/data-team-view.html from the Week 11 captures (standard library only).

Counts only: no player names are written. Starters out, replacements named and the net injury
count stay UNVERIFIED (no official depth source; net-count definition not set by the operator).
Run: python3 captures/scripts/build_team_view.py
"""
import collections, html, json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORT = "https://www.nfl.com/injuries/league/2026/reg11"
NAMES = {
    "AZ": "Arizona Cardinals", "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills", "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "DAL": "Dallas Cowboys", "DEN": "Denver Broncos",
    "DET": "Detroit Lions", "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NO": "New Orleans Saints", "NYG": "New York Giants", "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
PR_SHORT = {"Did Not Participate In Practice": "DNP", "Limited Participation in Practice": "LP", "Full Participation in Practice": "FP"}


def read_tsv(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        lines = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    hdr = lines[0]
    return [dict(zip(hdr, r)) for r in lines[1:]]


meta = json.load(open(os.path.join(ROOT, "captures/2026-11-19/injury-report-w11-r2.meta.json"), encoding="utf-8"))
new = read_tsv("private-store/injury-report-2026-w11-r2.tsv")
old = read_tsv("private-store/injury-report-2026-w11.tsv")
old_key = {(r["team"], r["player"]): r for r in old}
game_of = {}
for g in meta["games"]:
    game_of[g["away"]] = ("at " + g["home"], g)
    game_of[g["home"]] = ("vs " + g["away"], g)
nets = {t for t in NAMES}
per = collections.defaultdict(lambda: collections.Counter())
changes = collections.Counter()
for r in new:
    c = per[r["team"]]
    c["rows"] += 1
    c[PR_SHORT[r["practice_status"]]] += 1
    if r["game_status"]:
        c[r["game_status"]] += 1
    k = (r["team"], r["player"])
    if k in old_key and old_key[k]["practice_status"] != r["practice_status"]:
        changes[r["team"]] += 1

prior_no_inj = set(NAMES) - {r["team"] for r in old}  # 24 clubs the 18 Nov read marked 'No Injuries Reported'
rows_html = []
for t in sorted(NAMES, key=lambda x: NAMES[x]):
    c = per[t]
    if t in meta["teams_listed_no_injuries"]:
        listed = "No Injuries Reported"
        counts = ["0", "0", "0", "0", "0", "0"]
        read = "'No Injuries Reported' on this read"
    else:
        counts = [str(c["rows"]), str(c["DNP"]), str(c["LP"]), str(c["FP"]), str(c["Out"]), str(c["Questionable"] + c["Doubtful"])]
        read = f"{c['rows']} player rows listed"
    if t in ("IND", "HOU"):
        prior = f"{changes[t]} practice-status change(s) vs 18 Nov read (IND and HOU rows only)"
    elif t in prior_no_inj:
        prior = "18 Nov read said 'No Injuries Reported'; " + ("now lists rows (F-26 contradicted)" if t not in meta["teams_listed_no_injuries"] else "still reads 'No Injuries Reported'")
    else:
        prior = "not in the 18 Nov read"
    sg, g = game_of[t]
    game_txt = f"{sg} {g['day'].split(',')[0]} {g['kickoff_et']}"
    cells = "".join(f"<td>{x}</td>" for x in counts)
    rows_html.append(
        f"<tr><td>{html.escape(NAMES[t])} ({t})</td><td>{html.escape(game_txt)}</td>"
        f"<td>{'No Injuries Reported' if t in meta['teams_listed_no_injuries'] else counts[0]}</td>"
        f"<td>{counts[1]}</td><td>{counts[2]}</td><td>{counts[3]}</td>"
        f"<td>{counts[4]}</td><td>{counts[5]}</td>"
        f"<td><span class=\"flag\">UNVERIFIED: no official depth source</span></td>"
        f"<td><span class=\"flag\">UNVERIFIED: no official depth source</span></td>"
        f"<td><span class=\"flag\">UNVERIFIED: net count not defined</span></td>"
        f"<td>{html.escape(prior)}</td>"
        f"<td><a href=\"{REPORT}\">Injury report</a></td></tr>")

total_rows = len(new)
clubs_with_rows = len({r["team"] for r in new})
desig = sum(1 for r in new if r["game_status"])
out_n = sum(1 for r in new if r["game_status"] == "Out")
q_n = sum(1 for r in new if r["game_status"] == "Questionable")
lines_summary = [
    ("Games on the report", "13", "https://www.nfl.com/schedules/2026/by-week/week-11"),
    ("Clubs on the report", "26", REPORT),
    ("Player rows read (19 Nov, all 7 chunks)", str(total_rows), REPORT),
    ("Clubs listing player rows", f"{clubs_with_rows} (CIN and WAS read 'No Injuries Reported')", REPORT),
    ("Game designations (Out / Questionable)", f"{desig} ({out_n} Out, {q_n} Questionable), all in the Thursday game IND at HOU", REPORT),
    ("Friday report", "Not read. Game designations for Sunday and Monday games are blank on this read.", REPORT),
]
summary_html = "".join(f"<tr><td>{a}</td><td>{html.escape(b)}</td><td><a href=\"{u}\">Source</a></td></tr>" for a, b, u in lines_summary)

skeleton = open(os.path.join(ROOT, "site/data-team-view.html"), encoding="utf-8").read()
head, rest = skeleton.split("<main>", 1)
_, foot = rest.split("</main>", 1)
head = head.replace("Latest official sources re-read 2026-11-18", "Official report re-read 2026-11-19")
body = f"""<main>
<h1>Per-team injury view</h1>
<p class="lead">Week 11, counts per club from the official report read on 19 Nov 2026. Starters out, replacements named and the net injury count are not verified.</p>

<p class="meta">Official NFL injury report, Week 11, all 7 chunks read on 19 Nov 2026 (fetch time not recorded by the fetch tool; upper bound {meta['retrieved_utc_upper_bound']}). Counts only: no player names on this page. Each row links the official report.</p>
<p class="flag-line"><b>Correction.</b> The 18 Nov read of this page said 24 clubs read 'No Injuries Reported'. The full report read on 19 Nov lists player rows for 24 clubs. Only CIN and WAS read 'No Injuries Reported' (F-26 contradicted; F-34).</p>
<p class="flag-line"><b>Read this first.</b> Game designations exist only for the Thursday game (IND at HOU). Sunday and Monday game-status cells are blank until the Friday report. A club listing rows is not confirmed healthy or out; starters out, replacements named and the net injury count need a verified depth source and an operator definition, so those cells are UNVERIFIED.</p>
<h2>Capture summary</h2>
<div class="tw"><table><thead><tr><th>Measure</th><th>Value</th><th>Source</th></tr></thead><tbody>{summary_html}</tbody></table></div>
<h2>Per club</h2>
<p class="meta">Columns: DNP, LP and FP are practice-status counts; Out and Questionable are game-status counts (Doubtful is folded into Questionable: none appear). The 19 Nov counts are on the same 26 clubs as the report.</p>
<input class="filter" type="search" placeholder="Filter rows…" aria-label="Filter rows" data-target="team-view"><div class="tw"><table class="dense" id="team-view" data-filter="team-view"><thead><tr><th>Club</th><th>Week 11 game</th><th>Player rows</th><th>DNP</th><th>LP</th><th>FP</th><th>Out</th><th>Questionable</th><th>Starters out</th><th>Replacements named</th><th>Net injury count</th><th>Change since prior read</th><th>Source</th></tr></thead><tbody>{''.join(rows_html)}</tbody></table></div>
<h2>Not captured, and why</h2>
<ul>
<li>Depth charts: the Houston depth-chart page returned NFL's 404 page on 19 Nov (F-29). Without an official depth order, a starter cannot be named, so no starter or replacement is shown.</li>
<li>Transactions: the official transactions URL returned 404 (F-29). Injured-reserve moves visible on nfl.com are news reports only, for example <a href="https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start">Dolphins place QB Malik Willis on injured reserve</a> (F-30).</li>
<li>Change since prior read: computed only for IND and HOU, the two clubs in both reads. The 18 Nov read covered no other club's rows.</li>
</ul>
<p class="flag-line"><b>Storage split.</b> Row-level player data is held in <code>private-store/</code>, which the Pages build excludes. The repository itself is public, so that exclusion does not make the file private (F-31). The manifest with hashes is in <a href="https://github.com/sassnarep3-star/Own8/blob/main/captures/manifest.json">captures/manifest.json</a>; the delta is in <a href="https://github.com/sassnarep3-star/Own8/blob/main/captures/2026-11-19/delta-w11-r1-to-r2.json">captures/2026-11-19/delta-w11-r1-to-r2.json</a>; the generator is <a href="https://github.com/sassnarep3-star/Own8/blob/main/captures/scripts/build_team_view.py">captures/scripts/build_team_view.py</a>.</p>

"""
open(os.path.join(ROOT, "site/data-team-view.html"), "w", encoding="utf-8").write(head + body + "</main>" + foot)
print("wrote site/data-team-view.html: clubs", len(NAMES), "rows", total_rows)
