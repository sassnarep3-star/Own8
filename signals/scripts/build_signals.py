#!/usr/bin/env python3
"""
SB7 — build the signal-desk pages.

Design rules, applied without exception:
  - every table row that asserts a value carries a link to the official page it came from, or to the
    official page it is about;
  - a value that no official source publishes is rendered as an empty cell, and the column header
    says so, so a blank is never mistaken for a zero;
  - every page states its own as-of date and its sample size;
  - no page says "edge", "profit", "recommendation" or "verified" about anything that is not;
  - the site is static, has no CDN, no fonts, no scripts beyond one local file.

Pages: index, baselines, market, correlations, availability, decisions, suggestions, flagged, sources.
Run: python3 signals/scripts/build_signals.py
"""
import html
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
S = R / "signals"
D = S / "data"

LADDER = json.loads((D / "baseline-ladder.json").read_text())
MARKET = json.loads((D / "market-relative.json").read_text())
CORR = json.loads((D / "correlation-legitimacy.json").read_text())
AVAIL = json.loads((D / "availability-tiers.json").read_text())
QUEUE = json.loads((D / "decision-queue.json").read_text())
FLAGS = json.loads((D / "flags.json").read_text())

AS_OF = "2026-11-14"
WEEK = "WEEK 11"

NAV = [
    ("index", "Overview", "01"),
    ("baselines", "Baseline ladder", "02"),
    ("market", "Price hurdle", "03"),
    ("correlations", "Correlations", "04"),
    ("availability", "Availability & depth", "05"),
    ("decisions", "Decision queue", "06"),
    ("suggestions", "Suggestions", "07"),
    ("flagged", "Flagged for review", "08"),
    ("sources", "Sources", "09"),
]


def e(x):
    return "" if x is None else html.escape(str(x))


def url(u, label="Official source"):
    if not u:
        return None
    return f'<a href="{e(u)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def badge(t, kind=None):
    if t is None:
        return ""
    k = kind
    if k is None:
        s = str(t).upper()
        if "PASS" in s or s in ("LEGITIMATE", "AGREES", "VERIFIED", "CLOSED"):
            k = "good"
        elif "FAIL" in s or "ILLEGITIMATE" in s or "BLOCKED" in s or "NOT PLAYABLE" in s or "P0" == s:
            k = "warn"
        elif "DUPLICATE" in s or "UNRECONCILED" in s or "NOT " in s:
            k = "neutral"
        else:
            k = "neutral"
    return f'<span class="badge {k}">{e(t)}</span>'


def table(headers, rows, caption, note=None, empty_label="not published — see note"):
    """
    rows: list of lists. A None cell renders as an empty cell with an accessible label.
    The last column is expected to be a pre-rendered link or None.
    """
    out = (f'<div class="table-tools"><label>Filter rows <input type="search" '
           f'placeholder="Search this table…" aria-label="Filter {e(caption)}"></label>'
           f'<span class="row-count">{len(rows)} rows</span></div>')
    out += '<div class="table-wrap"><table><caption>' + e(caption) + '</caption><thead><tr>'
    out += "".join(f'<th scope="col">{e(h)}</th>' for h in headers)
    out += "</tr></thead><tbody>"
    for row in rows:
        out += "<tr>"
        for c in row:
            if c is None:
                out += f'<td class="missing" aria-label="{e(empty_label)}"></td>'
            elif isinstance(c, str) and c.startswith("<"):
                out += f"<td>{c}</td>"
            else:
                out += f"<td>{e(c)}</td>"
        out += "</tr>"
    out += "</tbody></table></div>"
    out += ('<p class="table-note">' + e(note) if note else
            '<p class="table-note">Empty cells are blank on purpose: no official source publishes that '
            'value, so it is not filled in.')
    out += "</p>"
    return out


def note(title, body):
    return f'<div class="notice"><strong>{e(title)}</strong><p>{e(body)}</p></div>'


def kv(pairs):
    return ('<div class="kpis">' + "".join(
        f'<div class="kpi"><span>{e(v)}</span><h2>{e(k)}</h2><small>{e(sub)}</small></div>'
        for v, k, sub in pairs) + "</div>")


def wrap(slug, title, desc, body):
    nav = "".join(
        f'<a {"aria-current=page" if k == slug else ""} href="{k}.html"><span>{n}</span>{label}</a>'
        for k, label, n in NAV)
    nav += '<a href="../index.html"><span>↩</span>Own8 root dashboard</a>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{e(desc)}">
<title>{e(title)} · Own8 signal desk</title>
<link rel="stylesheet" href="assets/style.css"><script src="assets/app.js" defer></script>
</head><body><a class="skip" href="#main">Skip to content</a>
<aside><a class="brand" href="index.html"><span class="brand-mark">8</span> SIGNAL<span class="lab">DESK</span></a>
<div class="nav-label">NFL / DECISION SUPPORT</div>
<nav aria-label="Section navigation">{nav}</nav>
<div class="aside-foot"><span class="pulse"></span> Official-source only<br>
<small>Snapshot · 14 NOV 2026<br>Paper research. No stakes.</small></div></aside>
<div class="workspace"><header><span>SIGNAL DESK <span class="muted">/ {e(title)}</span></span>
<span class="date">2026 SEASON · {WEEK}</span></header>
<main id="main"><div class="eyebrow">OWN8 INTELLIGENCE / {AS_OF} / SESSION 8ef7f6bb</div>
<h1>{e(title)}</h1><p class="lead">{e(desc)}</p>{body}</main>
<footer><span>OWN8 · Signal desk · evidence before edge.</span>
<span>No odds feed. No wagers. No cash rewards.</span></footer></div></body></html>'''


def page(slug, title, desc, body):
    (S / f"{slug}.html").write_text(wrap(slug, title, desc, body))


# ============================================================ 1. overview
def build_index():
    sp = LADDER["findings"]["best_spread_rule"]
    prof = LADDER["findings"]["arms_profitable_at_assumed_price"]
    bk = MARKET["book_arithmetic"]
    body = kv([
        (str(LADDER["ladder"][0]["n"]), "Games in the evidence base", "walk-forward, weeks 3–9"),
        (str(len(LADDER["ladder"])), "Arms on one ladder", "baselines and strategies, same games"),
        (f"{bk['breakeven_hit_rate'] * 100:.2f}%", "Hit rate just to break even", "at an assumed -110"),
        ("0", "Strategies promoted", "two arms clear break-even, neither is promotable"),
    ])
    body += '<div class="hero"><div><span class="pill">THE ONE THING TO READ</span>'
    body += '<h2>One missing input<br>blocks everything.</h2>'
    body += ('<p>No official NFL page publishes a price. Without one, hit rate cannot become profit, a '
             'rank cannot become a stake, and a fair line cannot be compared with a market line. Nine '
             'earlier sessions built nine dashboards because a dashboard was the only thing left to '
             'build. This desk stops building and starts closing the gap.</p>'
             '<a class="button" href="decisions.html">Read the decision queue <span>↗</span></a></div>'
             '<div class="hero-stat"><span>BREAK-EVEN AT -110</span><strong>52.38<span>%</span></strong>'
             '<p>Every forecast below this line loses money, however clever it is.</p>'
             '<div class="progress"><i></i></div><small>Assumed price, not a quote.</small></div></div>')

    rows = [
        ["What the model does well",
         f"The best admissible spread rule ({sp}) has a mean absolute error of "
         f"{LADDER['findings']['best_spread_mae']} points on 104 walk-forward games, against "
         f"{next(a for a in LADDER['ladder'] if a['id'] == 'B02')['value']} for the league-mean baseline.",
         badge("MEASURED", "good"),
         url("https://www.nfl.com/scores/2026/week-3")],
        ["What that is worth",
         f"Not enough to bet. {len(prof)} of {len(LADDER['ladder'])} arms show a positive return at an "
         f"assumed -110. "
         + (f"{MARKET['market_verdict']['count_of_arms_clearing']} arms have a hit-rate interval whose "
            f"lower bound clears the {bk['breakeven_hit_rate'] * 100:.2f}% break-even rate — "
            + ", ".join(MARKET['market_verdict']['arms_whose_interval_clears_breakeven'])
            + " — but one is a naive rule and the other clears by "
            + f"{next(c['gap_points'] for c in MARKET['interval_vs_breakeven'] if c['arm'] == 'S8'):.2f} "
            "percentage points after 18 tests. That is luck, not a signal."
            if MARKET['market_verdict']['count_of_arms_clearing'] else
            "No arm's interval clears that rate.")
         + " No strategy is promoted.",
         badge("NOT PLAYABLE"),
         url("https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm")],
        ["What is missing",
         "A timestamped price, opening and closing, with a named venue. No official NFL source "
         "publishes one. This is decision-queue row DQ-01 and it blocks DQ-02, DQ-03, DQ-04 and DQ-05.",
         badge("P0 BLOCKER"),
         url("https://www.nfl.com/schedules/2026/by-week/week-11")],
        ["What is unexpectedly possible",
         "Depth of replacement is measurable from the official Game Book: starting lineups by slot, "
         "substitutions, Did Not Play and Not Active. Demonstrated on two clubs, three slot changes "
         "and six unexplained absences.",
         badge("METHOD PROVEN", "good"),
         url(AVAIL["depth_changes"][0]["source_url"])],
        ["What cannot be known before kickoff",
         "Who is 2nd, 3rd or 4th string. The official depth-chart URL returns 404 and no other "
         "official page ranks backups. Any pregame string ordinal would be invented.",
         badge("NOT POSSIBLE"),
         url("https://www.nfl.com/teams/kansas-city-chiefs/depth-chart")],
        ["What must be decided first",
         f"{QUEUE['counts'].get('P0', 0)} questions block a decision outright, "
         f"{QUEUE['counts'].get('P1', 0)} need an out-of-sample test, "
         f"{QUEUE['counts'].get('P2', 0)} need a policy call and {QUEUE['counts'].get('P3', 0)} are "
         f"housekeeping. {len(QUEUE['closed_without_new_data'])} of them need no new data at all.",
         badge(f"{len(QUEUE['queue'])} OPEN"),
         url("decisions.html")],
    ]
    body += "<h2>What the evidence says, in six lines</h2>"
    body += table(["Topic", "Finding", "Status", "Source"], rows, "Headline findings")
    body += note("Research boundary",
                 "Every number on this site is recomputed from committed official NFL rows or from a "
                 "page retrieved on 2026-11-14. No market price exists anywhere in the source family, "
                 "so every price-dependent value is blank. The -110 used in the staking arithmetic is "
                 "a stated assumption, never a quote.")
    body += '<div class="section-links">'
    body += ('<a href="baselines.html"><strong>Is it skill, or a do-nothing rule?</strong>'
             f'<p>{len(LADDER["ladder"])} arms scored on identical games, with a leakage ceiling for '
             'comparison.</p></a>')
    body += ('<a href="market.html"><strong>What would a real price have to be?</strong>'
             '<p>The number that erases the signal, computed rather than guessed.</p></a>')
    body += "</div>"
    page("index", "Overview",
         "What this repository actually knows about NFL lines, what it does not, and the single input "
         "that blocks the rest.", body)


# ============================================================ 2. baselines
def build_baselines():
    f = LADDER["findings"]
    body = kv([
        (f["best_spread_rule"], "Best admissible spread rule", "no future games used"),
        (f"{f['best_spread_mae']}", "Its mean absolute error", "points, home margin, n = 104"),
        (f"{f['leakage_ceiling_mae']}", "Leakage ceiling", "what using future games buys"),
        (f"{len(f['arms_whose_hit_rate_beats_coin_at_5pct'])}", "Arms beating a coin at p<0.05",
         "before any family correction"),
    ])
    body += note("How to read the ladder",
                 "Every arm is scored on exactly the same games, in the same walk-forward order, so the "
                 "only thing that changes is the rule. An arm earns the right to exist only if it beats "
                 "the do-nothing arms above it. ROI is computed at an ASSUMED -110 because no real "
                 "price exists; it is a hurdle, not a simulation.")
    rows = []
    for a in LADDER["ladder"]:
        b = a["betting"]
        rows.append([
            a["id"],
            a["label"],
            a["kind"],
            a["value"],
            b["n_bets"],
            b["hit_rate"],
            f"{b['roi_per_unit_assumed_price']:+.4f}" if b["roi_per_unit_assumed_price"] is not None else None,
            b["p_value_vs_coin"],
            ("LEAKAGE — excluded" if a["uses_future_games"] else
             ("beats coin" if b["p_value_vs_coin"] is not None and b["p_value_vs_coin"] < 0.05
              else "not distinguishable")),
            url(a.get("source_url") or "https://www.nfl.com/scores/2026/week-3"),
        ])
    body += "<h2>The full ladder</h2>" + table(
        ["Arm", "Rule", "Market", "Loss metric", "Bets", "Hit rate", "ROI at assumed -110",
         "p vs coin", "Reading", "Source"],
        rows, "Baseline ladder — 18 arms, identical games",
        note="Loss metric is mean absolute error in points for spreads and totals, and Brier score "
             "for moneylines, so values are not comparable across market types. Empty cells mean the "
             "arm placed no bet on that market.")

    body += "<h2>Does each strategy beat each do-nothing rule?</h2>"
    h2h = []
    for r in LADDER["head_to_head"]:
        metric = r.get("mae_improvement_points")
        if metric is None:
            metric = r.get("brier_improvement")
        h2h.append([r["strategy"], r["vs"],
                    r.get("mae_strategy", r.get("brier_strategy")),
                    r.get("mae_baseline", r.get("brier_baseline")),
                    metric,
                    badge("BEATS", "good") if r["strategy_beats_arm"] else badge("LOSES", "warn"),
                    url("https://www.nfl.com/scores/2026/week-3")])
    body += table(["Strategy", "Versus", "Strategy loss", "Baseline loss", "Improvement",
                   "Verdict", "Source"], h2h, "Head-to-head against every naive arm",
                  note="A negative improvement means the strategy is worse than the arm it is compared "
                       "with. Lower loss is better for all three metric types.")

    body += "<h2>How much of each result could be luck?</h2>"
    lk = []
    for r in LADDER["luck_decomposition"]:
        lk.append([r["id"], r["n_bets"], r["hit_rate"],
                   f"[{r['hit_rate_ci95'][0]:.4f}, {r['hit_rate_ci95'][1]:.4f}]" if r["hit_rate_ci95"][0] is not None else None,
                   r["edge_over_breakeven_points"],
                   r["coin_flip_p_value"],
                   (f"{r['games_needed_to_confirm_this_edge']:,}"
                    if r["games_needed_to_confirm_this_edge"] else None),
                   badge("beats coin", "good") if r["beats_coin_at_5pct"] else badge("inside noise", "neutral"),
                   url("https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm")])
    body += table(["Arm", "Bets", "Hit rate", "95% interval", "Edge over break-even (pts)",
                   "p vs coin", "Bets needed to confirm", "Luck verdict", "Source"],
                  lk, "Luck decomposition",
                  note="The 95% interval is Wilson. 'Bets needed to confirm' is the sample at which the "
                       "observed edge would be distinguishable at 80% power; where it is blank the "
                       "observed rate is below break-even, so no sample size would confirm it.")
    body += note("The uncomfortable part",
                 "A five-game recency rule (B11) beats a coin flip at p = 0.005 on the moneyline, and "
                 "the registered ridge strategies do no better. If the ladder cannot separate a "
                 "well-built model from a simple rule on 104 games, the ladder is measuring noise. "
                 "That is the finding, and it is published rather than buried.")
    page("baselines", "Baseline ladder",
         "Skill measured against eight do-nothing rules rather than one hand-picked benchmark, with a "
         "deliberate leakage ceiling for comparison.", body)


# ============================================================ 3. market
def build_market():
    bk = MARKET["book_arithmetic"]
    v = MARKET["market_verdict"]
    body = kv([
        (f"{bk['breakeven_hit_rate'] * 100:.2f}%", "Break-even hit rate", "at the assumed -110"),
        (f"{bk['two_way_overround_at_minus_110']:.4f}", "Two-way overround", "at the assumed -110"),
        (f"{bk['book_hold_pct_at_minus_110']:.2f}%", "Price consumed by the vig", "before the model is even considered"),
        ("0", "Markets with a real price", "none exists in any official source"),
    ])
    body += note("What this page is, and is not",
                 "No market line, spread, total or price is used anywhere. The columns labelled "
                 "'market' are blank because no official NFL source publishes them. What this page "
                 "computes instead is the number a market WOULD have to be for the signal to be worth "
                 "exactly zero. That is a property of the model and the assumed price, not a quote, and "
                 "it is the honest version of 'publish the fair line, the market line and the difference'.")
    rows = []
    for g in MARKET["week11_fair_lines"]:
        rows.append([g["game"], g["day_rendered"], g["fair_spread_text"], g["fair_total"],
                     f'{g["fair_ml_home"]:+d} / {g["fair_ml_away"]:+d}',
                     g["market_spread"], g["market_total"], g["difference_fair_minus_market"],
                     g["breakeven_market_distance_spread_points"],
                     badge("UNVALIDATED"),
                     url(g["source_url"])])
    body += "<h2>Week 11 — our fair number, the market's, and the gap</h2>"
    body += table(["Game", "Day", "Fair spread", "Fair total", "Fair moneyline",
                   "Market spread", "Market total", "Difference", "Break-even distance (pts)",
                   "Status", "Source"],
                  rows, "Fair line and market line as separate columns",
                  note="Market spread, market total and difference are blank for every row: no source "
                       "publishes them. The break-even distance is the number of points by which our "
                       "fair line would have to be better than the available line before a -110 bet "
                       "broke even. It is constant across games because it depends only on the price "
                       "and the league's scoring spread.")
    body += "<h2>What line advantage would each measured hit rate require?</h2>"
    la = []
    for r in MARKET["line_advantage_implied_by_hit_rate"]:
        la.append([r["arm"], r["kind"], r["n_bets"], r["measured_hit_rate"],
                   r["implied_line_advantage_points"],
                   r["models_own_mean_absolute_error_points"],
                   r["market_error_that_would_be_required_points"],
                   badge("LEAKAGE", "warn") if r["uses_future_games"] else "",
                   url("https://www.nfl.com/scores/2026/week-3")])
    body += table(["Arm", "Market", "Bets", "Hit rate", "Implied line advantage (pts)",
                   "Model's own error (pts)", "Error an opposing number would need (pts)",
                   "Flag", "Source"],
                  la, "Line advantage implied by the observed hit rate",
                  note="If a rule wins more than half its bets, it must have had an average advantage. "
                       "The last column adds that advantage to the rule's own measured error: it is the "
                       "accuracy a market would need for the bet to have been profitable. The market's "
                       "real accuracy is unpublished, so this is a target to test, not a result.")
    body += "<h2>The arithmetic that decides everything</h2>"
    vig = []
    for r in MARKET["vig_arithmetic"]:
        vig.append([f"{r['hit_rate'] * 100:.2f}%", r["assumed_price"], r["decimal"],
                    f"{r['breakeven_hit_rate'] * 100:.2f}%", f"{r['roi_per_unit']:+.4f}",
                    badge("survives", "good") if r["survives"] else badge("loses", "warn"),
                    url("https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm")])
    body += table(["Hit rate", "Price", "Decimal", "Break-even at that price", "ROI per unit",
                   "Verdict", "Source"], vig, "Hit rate against price",
                  note="Read across a row: at -110 a 55% forecaster loses 5% of turnover. The price "
                       "moves the break-even line, not the skill.")
    body += note("The verdict", v["verdict"])
    body += "<h2>Which arms clear the break-even rate?</h2>"
    iv = []
    for c in MARKET["interval_vs_breakeven"]:
        iv.append([c["arm"], c["kind"], c["n_bets"], c["hit_rate"],
                   f"{c['ci_low']:.4f}", c["breakeven"], c["gap_points"],
                   badge("CLEARS", "good") if c["clears"] else badge("inside noise", "neutral"),
                   url("https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm")])
    body += table(["Arm", "Market", "Bets", "Hit rate", "Interval low bound", "Break-even",
                   "Gap (pts)", "Verdict", "Source"], iv,
                  "Lower bound of the hit-rate interval against the break-even rate",
                  note="This is the only promotion test available without a price, and it is weak: it "
                       "answers 'could this be better than break-even', not 'is this better than the "
                       "market'. Two arms clear it. Both are published; neither is promoted.")
    page("market", "Price hurdle",
         "The fair number, the market number and the difference, published as three separate columns — "
         "with the market columns blank because no official source publishes them.", body)


# ============================================================ 4. correlations
def build_correlations():
    s = CORR["summary"]
    body = kv([
        (f"{len(CORR['correlations'])}", "Correlations examined", "recomputed where possible"),
        (f"{len(s['agree_on_value_and_n'])}", "Reproduce exactly", "value and n both match"),
        (f"{len(s['illegitimate_as_published'])}", "Illegitimate as published", "n counts rows, not games"),
        (f"{len(s['survive_holm_at_5pct'])}", "Survive Holm", "and both are tautological"),
    ])
    body += note("Why n is printed on every row",
                 "A correlation is only as good as its denominator. Where a row is nested inside a game "
                 "— two quarterbacks, one game — the game is the independent unit and the row count "
                 "overstates significance. Every row below prints both, and quotes the honest one.")
    rows = []
    for c in CORR["correlations"]:
        rows.append([c["id"], c["pair"], c["r"], c["n_rows"], c["n_independent"],
                     f"[{c['ci95'][0]}, {c['ci95'][1]}]" if c["ci95"][0] is not None else None,
                     c["p"], c.get("holm_p"),
                     badge(c["verdict"]),
                     url(c["source_url"])])
    body += table(["ID", "Pair", "r", "Rows", "Independent n", "95% interval", "p",
                   "Holm p", "Verdict", "Source"], rows,
                  "Correlation register, recomputed from official rows",
                  note="p is two-sided from the t approximation on the independent n. Holm p is "
                       "adjusted over the declared family on this page. Where r is blank the published "
                       "pair definition could not be reproduced and no value is claimed.")
    body += "<h2>Does the published register survive?</h2>"
    comp = []
    for c in CORR["comparison_with_published"]:
        comp.append([c["id"], c["published_r"], c["recomputed_r"], c["published_n"],
                     c["recomputed_n_independent"],
                     badge("AGREES", "good") if c["agrees"] else
                     (badge("NOT RECONCILED") if c["recomputed_r"] is None else badge("DIFFERS", "warn")),
                     url(c["source_url"])])
    body += table(["ID", "Published r", "Recomputed r", "Published n", "Independent n",
                   "Reconciliation", "Source"], comp,
                  "Published values against recomputed values",
                  note="AGREES requires the value within 0.002 AND identical n. C6's value matches but "
                       "its n does not, so it is marked differing rather than agreed.")
    body += "<h2>Combination products, and what each one needs</h2>"
    cb = []
    for c in CORR["combination_products"]:
        cb.append([c["product"], c["legs"], c["joint_probability_rule"], c["n_available"],
                   c["data_available"], badge(c["verdict"]), url(c["source_url"])])
    body += table(["Product", "Legs", "Joint probability rule", "n", "Data actually held",
                   "Verdict", "Source"], cb, "Singles, parlays and prop combos",
                  note="A joint probability is only useful with a price. Every row here can be computed "
                       "and none can be bet, because the price column does not exist.")
    body += note("The trap",
                 "The two coefficients that survive a family correction are the two most tautological "
                 "pairs in the register: a quarterback's passing yards against his own team's points, "
                 "and against the game total. Both are large, both are significant, and both would "
                 "double-count the same information if used to price a combo. Correlation is not edge.")
    page("correlations", "Correlations",
         "Every coefficient recomputed from official rows, with the independent n beside the row "
         "count, and a verdict on whether it may be used.", body)


# ============================================================ 5. availability
def build_availability():
    s = AVAIL["summary"]
    body = kv([
        (f"{s['clubs_measured']}", "Clubs measured", "weeks 5 and 10, official Game Books"),
        (f"{s['slots_changed']}", "Starter slots changed", "of 7 single-identity slots per club"),
        (f"{s['changes_with_official_out_or_doubtful_flag']}", "Explained by an Out flag", "official designation"),
        (f"{s['unexplained_absences']}", "Unexplained absences", "no official flag publishes the cause"),
    ])
    body += note("The answer to the requirement, stated plainly",
                 "The requirement is to know when a 2nd, 3rd or 4th string player replaces a starter. "
                 "That is not knowable before kickoff from any official source: the depth-chart URL "
                 "returns 404 and no other official page ranks backups. It IS knowable after the game "
                 "from the official Game Book, which prints who actually started in each slot. So the "
                 "repository measures replacement as a change against a previous official listing, and "
                 "refuses to publish a pregame string ordinal it cannot source.")
    body += "<h2>What official sources do and do not publish</h2>"
    cap = []
    for c in AVAIL["capability_matrix"]:
        cap.append([c["capability"], badge("PUBLISHED", "good") if c["published"] else badge("NOT PUBLISHED", "warn"),
                    c["observed"], c["consequence"], url(c["url"])])
    body += table(["Capability", "Published?", "What the page actually rendered", "Consequence",
                   "Source"], cap, "Capability matrix, probed 2026-11-14")
    body += "<h2>Players by tier — two clubs, Week 10</h2>"
    tiers = [[t["team"], t["player"], t["jersey"], t["position"], badge(t["tier"]),
              t["official_injury_flag"], t["official_injury"],
              t["depth_ordinal"], url(t["source_url"])] for t in AVAIL["tiers"]]
    body += table(["Team", "Player", "No.", "Pos", "Tier (from an official field)",
                   "Game status", "Injury", "Depth ordinal", "Source"], tiers,
                  "Every player the Week 10 Game Book lists, classified by the field he appears in",
                  note="Depth ordinal is blank for every row on purpose: no official source publishes "
                       "1st/2nd/3rd string, so publishing one would be invention. Tier is read directly "
                       "off the Game Book: starting slot, Substitutions, Did Not Play, or Not Active.")
    body += "<h2>Depth of replacement, measured</h2>"
    ch = []
    for c in AVAIL["depth_changes"]:
        ch.append([c["team"], c["slot"], c["week5_starter"], c["week10_starter"],
                   c["outgoing_player_week10_status"], c["official_injury_flag_outgoing"],
                   badge("EXPLAINED", "good") if c["attributable_to_injury_from_official_source"]
                   else badge("CAUSE NOT PUBLISHED"),
                   c["incoming_depth_class"], url(c["source_url"])])
    body += table(["Team", "Slot", "Week 5 starter", "Week 10 starter", "Outgoing status",
                   "Official flag", "Attribution", "Depth of the replacement", "Source"], ch,
                  "Starting-slot changes between two official Game Books",
                  note="Only positions that appear exactly once per book are compared (LT, LG, C, RG, "
                       "RT, QB, RB). Row-by-row matching of the two books was tried first and rejected: "
                       "the books order the same positions differently, and it invented about twenty "
                       "fake replacements.")
    body += "<h2>Absences with no published explanation</h2>"
    ab = []
    for a in AVAIL["unexplained_absences"]:
        ab.append([a["team"], a["player_week5_starter"], a["week5_slot"],
                   a["official_injury_flag"], badge("EXPLAINED", "good") if a["explained_by_official_source"]
                   else badge("UNEXPLAINED", "warn"), url(a["source_url"])])
    body += table(["Team", "Week 5 starter", "Slot", "Official flag", "Classification", "Source"], ab,
                  "A Week 5 starter absent from the entire Week 10 game-day listing",
                  note="These are the cases the requirement is really about. An absence without an "
                       "Out or Doubtful designation cannot be attributed to injury from an official "
                       "source, so the cause is left blank rather than guessed.")
    body += "<h2>Starter turnover by unit</h2>"
    st = [[x["team"], x["unit"], x["week5_starters_listed"], x["week10_starters_listed"],
           x["held_over"], x["incoming"], x["outgoing"],
           ", ".join(x["incoming_names"]), url(x["source_url"])] for x in AVAIL["starter_set_churn"]]
    body += table(["Team", "Unit", "Week 5 listed", "Week 10 listed", "Held over", "In", "Out",
                   "Incoming", "Source"], st, "Set overlap where slots are not a stable identity",
                  note="Defensive personnel groupings change between games, so a 'slot' on defence is "
                       "not a stable identity. Set overlap is the only defensible comparison there.")
    nxt = AVAIL["next_task_to_scale"]
    body += note("The next task, named in advance",
                 f"{nxt['task']} Cost: {nxt['cost']} Why it matters: {nxt['why_it_matters']} "
                 f"Blocking: {nxt['blocking']}")
    page("availability", "Availability & depth",
         "Who actually started, who replaced whom, and how deep the replacement was — measured from "
         "official Game Books, never inferred before kickoff.", body)


# ============================================================ 6. decisions
def build_decisions():
    body = kv([
        (str(QUEUE["counts"].get("P0", 0)), "P0 — block a decision", "no input exists"),
        (str(QUEUE["counts"].get("P1", 0)), "P1 — need out-of-sample", "input exists, untested"),
        (str(QUEUE["counts"].get("P2", 0)), "P2 — need a policy call", "analysis is done"),
        (str(QUEUE["counts"].get("P3", 0)), "P3 — housekeeping", "site and freshness"),
    ])
    body += note("The one-line answer", QUEUE["the_one_line_answer"])
    body += "<h2>The queue, in the order it must be answered</h2>"
    rows = []
    for q in QUEUE["queue"]:
        rows.append([badge(q["priority"]), q["id"], q["area"], q["question"], q["have"],
                     q["missing"], q["next_action"], q["status"], url(q["source_url"])])
    body += table(["Rank", "ID", "Area", "Question", "What we have", "What is missing",
                   "Action that closes it", "Status", "Source"], rows,
                  "Decision queue — 13 questions, ranked by what blocks a decision",
                  note="P0 blocks a decision outright. Nothing below P0 can be resolved before its P0 "
                       "parents. Every row names the action that would close it and whether that action "
                       "needs data, money, time, or only a decision.")
    body += "<h2>What could be closed this week without any new data</h2>"
    close = []
    for q in QUEUE["queue"]:
        if q["id"] in QUEUE["closed_without_new_data"]:
            close.append([q["id"], q["question"], q["next_action"], q["cost"],
                          url(q["source_url"])])
    body += table(["ID", "Question", "Action", "Cost", "Source"], close,
                  "Seven questions that need no new data")
    body += note("Why this order",
                 "Ranking by 'most interesting' produces seven open questions that never close. "
                 "Ranking by what blocks a decision produces one item at the top (a price) and a queue "
                 "of arithmetic and policy beneath it. The repository has spent many sessions on the "
                 "interesting items; this is the cheap half.")
    page("decisions", "Decision queue",
         "Every open question, ranked by whether it blocks a decision, with the exact action that "
         "would close it and what that action costs.", body)


# ============================================================ 7. suggestions
def build_suggestions():
    sug = [
        {"id": "SG-01", "priority": "P0", "suggestion": "Buy or capture a timestamped price series",
         "why": "It is the only input that converts hit rate into money. Nothing else on this site can "
                "progress far without it.",
         "what_it_costs": "One subscription, or a disciplined 10-minute capture before each slate.",
         "what_it_unlocks": "Every price column, the staking half of the leaderboard, closing-line value, "
                            "the demotion gate's promotion counterpart.",
         "risk": "A cheap or unofficial feed with no capture timestamp is worse than none, because it "
                 "looks like data.",
         "decision": None, "decision_label": "operator decision",
         "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11"},
        {"id": "SG-02", "priority": "P0", "suggestion": "Publish a required-sample figure beside every rank",
         "why": "A leaderboard ranked on 104 games is a ranking of noise. Printing the sample needed for "
                "a rank to mean something costs nothing and removes the loudest false signal on the site.",
         "what_it_costs": "The arithmetic is already computed in the luck decomposition.",
         "what_it_unlocks": "An honest leaderboard with no new data.",
         "risk": "None. It only removes claims.",
         "decision": None, "decision_label": "operator decision",
         "source_url": "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm"},
        {"id": "SG-03", "priority": "P1",
         "suggestion": "Scale the Game Book depth measurement to all 32 clubs",
         "why": "It is the only genuinely new signal available without a price feed, and the method is "
                "already proven on two clubs.",
         "what_it_costs": "Roughly 16 PDF retrievals and 1,000 transcribed lines per week.",
         "what_it_unlocks": "A testable feature: does a below-the-46 replacement predict a worse "
                            "outcome than a same-46 replacement?",
         "risk": "Transcription error. Mitigated by checking every club against its own injury report.",
         "decision": None, "decision_label": "operator decision",
         "source_url": AVAIL["depth_changes"][0]["source_url"]},
        {"id": "SG-04", "priority": "P1", "suggestion": "Reclassify S3 as a negative control, not a strategy",
         "why": "It is the worst arm on the ladder, at a 34.6% hit rate. Registering a deliberately bad "
                "rule as a candidate overstates the library.",
         "what_it_costs": "One registry edit in origination/, which this session does not own.",
         "what_it_unlocks": "A library where every entry is something the project would actually use.",
         "risk": "None.",
         "decision": None, "decision_label": "origination owner",
         "source_url": "https://www.nfl.com/standings/"},
        {"id": "SG-05", "priority": "P1", "suggestion": "Stop labelling the prop work a betting product",
         "why": "Both prop strategies score worse than a naive baseline and neither has a line to bet "
                "against. 'Player prop research' with no prop line is a descriptive yardage model.",
         "what_it_costs": "Free — a labelling change.",
         "what_it_unlocks": "Removes the most misleading category on the site.",
         "risk": "None, though it will shrink the visible strategy count.",
         "decision": None, "decision_label": "operator decision",
         "source_url": "https://nextgenstats.nfl.com/stats/passing/2026/REG/9"},
        {"id": "SG-06", "priority": "P2", "suggestion": "Approve a numeric promotion gate to pair with the demotion gate",
         "why": "A demotion gate with no promotion counterpart means nothing is ever allowed in, so the "
                "gate is never exercised.",
         "what_it_costs": "One decision, with a suggested shape already in the decision queue.",
         "what_it_unlocks": "A competition with an entrance and an exit.",
         "risk": "A gate set too loose lets noise through; too tight and the competition is empty forever.",
         "decision": None, "decision_label": "operator decision",
         "source_url": "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm"},
        {"id": "SG-07", "priority": "P2", "suggestion": "Declare the root dashboard canonical and reduce the rest to pointers",
         "why": "Eleven workspaces give eleven answers with eleven dates. A reader cannot tell which is "
                "current, which is worse than one incomplete answer.",
         "what_it_costs": "One consolidation pass, no deletion.",
         "what_it_unlocks": "A site a person can use in under a minute.",
         "risk": "Losing the audit trail. Mitigated by keeping every workspace, just demoted.",
         "decision": None, "decision_label": "operator decision",
         "source_url": "https://www.nfl.com/standings/"},
        {"id": "SG-08", "priority": "P3", "suggestion": "Schedule the official capture instead of doing it by hand",
         "why": "Both snapshots in this repository were taken one to two weeks after the data went stale.",
         "what_it_costs": "One workflow change to the existing GitHub Actions scaffolding.",
         "what_it_unlocks": "A repository that is a week old at worst, rather than three.",
         "risk": "A silent failure is worse than no schedule. The job must fail loudly on a diff.",
         "decision": None, "decision_label": "operator decision",
         "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11"},
    ]
    body = note("How to use this section, and what is not allowed here",
                "Each suggestion states what it costs, what it unlocks, and what could go wrong. Nothing "
                "is implemented before a decision is recorded, and no suggestion is ranked by how "
                "interesting it is. The decision column is blank on every row because the operator is "
                "the only actor who can fill it.")
    rows = [[s["id"], badge(s["priority"]), s["suggestion"], s["why"], s["what_it_costs"],
             s["what_it_unlocks"], s["risk"], badge(s["decision_label"]), url(s["source_url"])]
            for s in sug]
    body += table(["ID", "Rank", "Suggestion", "Why it matters", "What it costs",
                   "What it unlocks", "Risk", "Decision", "Source"], rows,
                  "Suggestions, with the decision still open on every row",
                  note="Priority follows the decision queue: P0 items block everything under them. A "
                       "suggestion moves to implementation only after its decision is recorded here.")
    body += note("The two suggestions that matter most",
                 "SG-01 (get a price) is the only one that unblocks money. SG-02 (print the required "
                 "sample beside every rank) is free, needs no new data, and removes the loudest false "
                 "claim on the site today. If only one thing is done this week, do SG-02, because it "
                 "costs nothing and is the difference between an honest leaderboard and a misleading one.")
    page("suggestions", "Suggestions",
         "A dedicated review section: proposals ranked by what they unblock, with cost, risk and an "
         "open decision on every row.", body)


# ============================================================ 8. flagged
def build_flagged():
    body = kv([
        (str(FLAGS["total"]), "Flags published", "none suppressed"),
        (str(FLAGS["counts"].get("high", 0)), "High severity", "operator action needed"),
        (str(len(FLAGS["own_work_corrections"])), "Corrections to this session's own work",
         "published deliberately"),
        ("0", "Flags that blocked the merge", "a flag is information, not a gate"),
    ])
    body += note("Why this page exists",
                 "A flag is published, never suppressed, and never blocks a release. Every row carries "
                 "the evidence that produced it and the disposition taken. Where the correct action was "
                 "a decision rather than a fix, the row says so and points at the decision queue. Two of "
                 "these flags are corrections to this session's own first draft: a corrected error is "
                 "evidence about how much noise remains elsewhere.")
    rows = [[f["id"], badge(f["severity"].upper(), "warn" if f["severity"] == "high" else None),
             f["category"], f["finding"], f["evidence"], f["impact"], f["disposition"],
             url(f["source_url"])] for f in FLAGS["flags"]]
    body += table(["ID", "Severity", "Category", "Finding", "Evidence", "Impact", "Disposition",
                   "Source"], rows, "Flagged for review — 14 items")
    page("flagged", "Flagged for review",
         "Every irregularity found, including two in this session's own work, with the evidence and the "
         "disposition for each.", body)


# ============================================================ 9. sources
def build_sources():
    src = [
        ("nfl-standings", "NFL.com league standings, 2026 regular season",
         "https://www.nfl.com/standings/", "32 club rows, 16 numeric fields each", "2026-11-14"),
        ("nfl-scores-w10", "NFL.com Week 10 scores",
         "https://www.nfl.com/scores/2026/week-10",
         "Thursday WAS 24 NYG 21 Final; 13 Sunday/Monday games unplayed at capture", "2026-11-14"),
        ("nfl-sched-w11", "NFL.com 2026 Week 11 schedule",
         "https://www.nfl.com/schedules/2026/by-week/week-11",
         "14 games, kickoffs, networks, six bye clubs, Mexico City badge on MIN at SF", "2026-11-14"),
        ("nfl-sched-w10", "NFL.com 2026 Week 10 schedule",
         "https://www.nfl.com/schedules/2026/by-week/week-10",
         "14 games; byes CHI, DEN, PHI, TB", "2026-11-14"),
        ("nfl-injuries-w10", "NFL.com official Week 10 injury report",
         "https://www.nfl.com/injuries/league/2026/reg10",
         "Player, position, injury, practice status, game status for 28 clubs; WAS and NYG re-read here",
         "2026-11-14"),
        ("nfl-injuries-w11", "NFL.com Week 11 injury report — DID NOT RESOLVE",
         "https://www.nfl.com/injuries/league/2026/reg11",
         "Returned the Week 10 page, heading included. No Week 11 report observable", "2026-11-14"),
        ("nfl-gamebook-w10", "Official NFL Game Book, WAS at NYG, Week 10",
         "https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf",
         "Starting lineups by slot, substitutions, Did Not Play, Not Active, scoring, statistics",
         "2026-11-14"),
        ("nfl-gamebook-w5", "Official NFL Game Book, NYG at WAS, Week 5",
         "https://static.www.nfl.com/image/upload/v1791805921/gamecenter/aa94b906-4feb-11f1-abca-2c54536568a9.pdf",
         "Baseline listing for the same two clubs", "2026-11-14"),
        ("nfl-game-w10", "NFL.com game centre, WAS at NYG",
         "https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
         "Scores render as 'Hidden Score'; publishes the Game Book link; no odds block of any kind",
         "2026-11-14"),
        ("nfl-game-w5", "NFL.com game centre, NYG at WAS",
         "https://www.nfl.com/games/giants-at-commanders-2026-reg-5",
         "Final 27-27; publishes the Game Book link", "2026-11-14"),
        ("nfl-depth-404", "NFL.com club depth chart — 404",
         "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart",
         "'404 - Flag on the Play.' No depth chart exists at this URL", "2026-11-14"),
        ("nfl-roster", "NFL.com club roster",
         "https://www.nfl.com/teams/kansas-city-chiefs/roster",
         "Name, jersey, position, status ACT, height, weight, experience, college. No depth order",
         "2026-11-14"),
        ("ngs-passing", "Next Gen Stats weekly passing",
         "https://nextgenstats.nfl.com/stats/passing/2026/REG/9",
         "Official NGS passing table; week 9 page re-read, weeks 1-8 from the committed transcription",
         "2026-11-14"),
        ("nist-ci", "NIST e-Handbook, confidence intervals",
         "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm",
         "Method reference for the intervals quoted throughout", "2026-11-14"),
        ("nist-mult", "NIST e-Handbook, Bonferroni and multiple comparisons",
         "https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm",
         "Method reference for the family correction", "2026-11-14"),
    ]
    body = note("What counts as a source here",
                 "An official NFL page, an official NFL PDF, or a standards body's method page. A "
                 "repository file is never evidence that an NFL fact is true; it is only evidence of what "
                 "this project computed. Every page retrieved in this session is listed, including the "
                 "one that failed, because a failed probe is a finding.")
    rows = [[k, label, scope, checked, url(u)] for k, label, u, scope, checked in src]
    body += table(["ID", "Publisher and page", "What it was used for", "Checked", "Link"],
                  rows, "Sources actually retrieved on 2026-11-14")
    body += "<h2>Probes that failed, and why they are published</h2>"
    pr = []
    for line in (D / "raw" / "probes-2026-11-14.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        pid, u, result, observed, consequence = line.split("|", 4)
        pr.append([pid, result, observed, consequence, url(u)])
    body += table(["Probe", "Result", "What came back", "Consequence", "Link"], pr,
                  "Availability probes, including the ones that failed",
                  note="A 404 on the depth chart is not a bug in this project; it is the reason the "
                       "project cannot publish a pregame depth tier.")
    page("sources", "Sources",
         "Every official page retrieved, including the ones that failed, with the exact scope each one "
         "supported.", body)


def main():
    (S / "assets").mkdir(parents=True, exist_ok=True)
    for fn in (build_index, build_baselines, build_market, build_correlations,
               build_availability, build_decisions, build_suggestions, build_flagged, build_sources):
        fn()
        print("built", fn.__name__)


if __name__ == "__main__":
    main()
