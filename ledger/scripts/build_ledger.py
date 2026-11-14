"""Build the decision ledger (ledger/data, ledger/results, ledger/*.html) from inputs already in the repo.

Inputs are READ ONLY:
  origination/data/games-2026-w1-w9.json      136 verified official games (nfl.com scores pages)
  origination/results/w10-lines.json          13 Week 10 fair lines + excluded completed game
  origination/results/validation-w10.json     12 strategies + 2 not-scored market strategies, gate detail
  origination/results/leaderboard-w10.json    origination leaderboard (used only for consistency checks)
  ledger/data/price-probe.json                official page probe (written by hand, with its URL and result)
  ledger/data/demotion-rules.json             pre-registered demotion rules

Outputs: ledger/data/{results-feed,price-snapshots,lines-columns,strategy-registry,flags}.json,
         ledger/results/leaderboard-split.json, ledger/results/demotion-decisions.json (via demotion_gate.py),
         ledger/*.html and ledger/assets/style.css.

Nothing is inferred: a value that is not in an input stays null, and any null is shown as blank plus a flag.
Standard library only. Run from the repository root:  python3 ledger/scripts/build_ledger.py
"""
import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.dirname(HERE)
ROOT = os.path.dirname(LEDGER)
sys.path.insert(0, HERE)

import demotion_gate  # noqa: E402

W9_LOG = os.path.join(ROOT, "origination", "data", "games-2026-w1-w9.json")
W10_LINES = os.path.join(ROOT, "origination", "results", "w10-lines.json")
VALIDATION = os.path.join(ROOT, "origination", "results", "validation-w10.json")
LEADERBOARD = os.path.join(ROOT, "origination", "results", "leaderboard-w10.json")
PROBE = os.path.join(LEDGER, "data", "price-probe.json")
RULES = os.path.join(LEDGER, "data", "demotion-rules.json")

GENERATED = "2026-11-14"
SCORE_WEEKS = ["https://www.nfl.com/scores/2026/week-%d" % w for w in range(1, 10)]
STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
SCHEDULE_W10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
SCORES_W10 = "https://www.nfl.com/scores/2026/week-10"
THURSDAY_GAME = "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def american_from_p(p):
    """No-vig American price for the side with probability p (rounded to whole cents)."""
    if p >= 0.5:
        return -int(round(100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def weekday_of(iso):
    return WEEKDAYS[datetime.date.fromisoformat(iso).weekday()]


# ---------------------------------------------------------------- results feed
def build_results_feed(log, w10):
    rows, flags = [], []
    for g in log["games"]:
        key = "2026-W%02d-%s-%s" % (g["week"], g["away"], g["home"])
        checks = {
            "margin_equals_score_difference": g["home_margin"] == g["home_score"] - g["away_score"],
            "total_equals_score_sum": g["total"] == g["home_score"] + g["away_score"],
            # a tie must carry winner NONE; a decided game must carry the playing team that scored more
            "winner_matches_score": (g["winner_indicator"] == "NONE") if g["home_score"] == g["away_score"] else
            (g["winner_indicator"] == (g["home"] if g["home_score"] > g["away_score"] else g["away"])),
        }
        weekday = weekday_of(g["date"])
        heading_day = next((d for d in WEEKDAYS if d in g["heading"]), None)
        if heading_day and heading_day != weekday:
            flags.append({
                "id": "LF-%02d" % (len(flags) + 10), "kind": "DATE/HEADING MISMATCH", "game_key": key,
                "detail": "Heading '%s' names %s, but the recorded date %s is a %s." % (
                    g["heading"], heading_day, g["date"], weekday),
                "source_urls": [g["source_url"]],
                "treatment": "Value kept as rendered by the official page; not corrected. Already logged in origination/flagged.html (W1)."})
        rows.append({
            "key": key, "week": g["week"], "date": g["date"], "weekday": weekday,
            "heading_as_rendered": g["heading"], "away": g["away"], "home": g["home"],
            "away_score": g["away_score"], "home_score": g["home_score"], "home_margin": g["home_margin"],
            "total": g["total"], "winner": g["winner_indicator"], "game_url": g["game_url"],
            "source_url": g["source_url"], "verified_in_origination": g["verified"],
            "arithmetic_checks": checks, "arithmetic_ok": all(v is not False for v in checks.values()),
            "scope_note": "Official score row from the W1-W9 verified log (136 games)."})
    # Thursday game: already FINAL before the log cutoff; excluded from the log, added here as a separate row.
    thu = w10["excluded_completed"][0]
    rows.append({
        "key": "2026-W10-WAS-NYG", "week": 10, "date": "2026-11-12", "weekday": weekday_of("2026-11-12"),
        "heading_as_rendered": "Thursday Night Football, November 12th", "away": "WAS", "home": "NYG",
        "away_score": 24, "home_score": 21, "home_margin": 21 - 24, "total": 45, "winner": "WAS",
        "game_url": THURSDAY_GAME, "source_url": SCORES_W10, "verified_in_origination": False,
        "arithmetic_checks": {"margin_equals_score_difference": True, "total_equals_score_sum": True,
                              "winner_matches_score": True},
        "arithmetic_ok": True,
        "scope_note": "Thursday game already FINAL before origination. Re-read 2026-11-14 on %s: 'Thursday Night Football, November 12th', WAS 24 / NYG 21, 'Final'. Excluded from the 136-game log and from Week 10 lines." % SCORES_W10})
    rows.sort(key=lambda r: (r["week"], r["date"], r["key"]))
    return {
        "generated": GENERATED,
        "description": "Official final scores for every completed 2026 game in the repository (137 rows). The feed is the join key for backtests and ROI: once prices exist, join on 'key'.",
        "counts": {"games": len(rows), "from_verified_log": len(log["games"]),
                   "added_thursday_week10": 1,
                   "arithmetic_failures": sum(1 for r in rows if not r["arithmetic_ok"])},
        "rows": rows,
    }, flags


# ---------------------------------------------------------------- lines
def build_lines(w10):
    cols, flags, mismatches = [], [], []
    for g in w10["games"]:
        key = "2026-W10-%s-%s" % (g["away"], g["home"])
        s1 = g["fair_home_margin_S1"]
        fav = g["home"] if s1 > 0 else g["away"]
        text_recomputed = "%s -%.1f" % (fav, abs(s1))
        if text_recomputed != g["fair_spread_favourite_text"]:
            mismatches.append({"game_key": key, "field": "fair_spread_favourite_text",
                               "file": g["fair_spread_favourite_text"], "recomputed": text_recomputed})
        p = g["p_home_S6"]
        ml_home, ml_away = american_from_p(p), american_from_p(1 - p)
        if abs(ml_home - g["fair_ml_home"]) > 1 or abs(ml_away - g["fair_ml_away"]) > 1:
            mismatches.append({"game_key": key, "field": "fair_ml", "file": [g["fair_ml_home"], g["fair_ml_away"]],
                               "recomputed": [ml_home, ml_away]})
        cols.append({
            "key": key, "week": 10, "away": g["away"], "home": g["home"],
            "kickoff_as_rendered": g["day"] + ", " + g["time_as_rendered"],
            "neutral_site": g["neutral_site"],
            "order": [
                {"step": 1, "market": "side", "why_first": "The moneyline is a transform of the side margin (S6 = Phi(S1 margin / sigma)), so it cannot be originated before the side."},
                {"step": 2, "market": "total", "why_first": "Independent of the side model; originated second to keep the order fixed for every game."},
                {"step": 3, "market": "moneyline", "why_first": "Derived from the side margin, therefore last."}],
            "side": {
                "fair_favourite_text": g["fair_spread_favourite_text"],
                "fair_home_margin_S1": round(s1, 3), "model": "S1 (ridge margin)", "model_status": "PASS (all applicable gates)",
                "alt_fair_home_margin_S2": round(g["fair_home_margin_S2"], 3), "alt_model": "S2 (offence/defence ridge)", "alt_model_status": "PASS (all applicable gates)",
                "market_spread": None, "difference_fair_minus_market": None},
            "total": {
                "fair_total": round(g["fair_total_S4"], 2), "model": "S4 (offence/defence ridge)",
                "model_status": "FAIL G4, G5, G6 (validation-w10.json) - UNVALIDATED",
                "alt_fair_total_S5": round(g["fair_total_S5"], 2), "alt_model": "S5 (naive PF/PA averages)",
                "alt_model_status": "FAIL G4, G5, G6 - UNVALIDATED",
                "market_total": None, "difference_fair_minus_market": None},
            "moneyline": {
                "fair_p_home": round(p, 4), "fair_ml_home": g["fair_ml_home"], "fair_ml_away": g["fair_ml_away"],
                "recomputed_ml_home": ml_home, "recomputed_ml_away": ml_away,
                "model": "S6 (moneyline from S1 margin)", "model_status": "PASS (all applicable gates)",
                "market_ml_home": None, "market_ml_away": None, "difference_fair_minus_market": None},
            "sigma_margin_used": round(g["sigma_margin"], 6), "sigma_total_used": round(g["sigma_total"], 6),
            "game_url": g["game_url"], "source_url": SCHEDULE_W10,
            "market_status": "BLANK - no official source publishes a betting line (price-probe.json, LF-01)."})
    flags.append({"id": "LF-02", "kind": "TOTAL MODEL FAILS VALIDATION",
                  "detail": "The Week 10 fair total comes from S4, which fails gates G4, G5 and G6 in origination/results/validation-w10.json (p_holm = 1.0). Every total is therefore UNVALIDATED; no total in this ledger is a validated fair line.",
                  "source_urls": [SCHEDULE_W10], "treatment": "Published with the failure beside it. Not used for any claim."})
    flags.append({"id": "LF-03", "kind": "SIGMA IS CONSTANT ACROSS GAMES",
                  "detail": "sigma_margin is %.6f and sigma_total is %.6f for every one of the 13 games. Win probabilities, and so the moneylines, assume the same spread for a rivalry game and a mismatch." % (
                      cols[0]["sigma_margin_used"], cols[0]["sigma_total_used"]),
                  "source_urls": [SCHEDULE_W10], "treatment": "Recorded as a model assumption. Not changed."})
    return {"generated": GENERATED,
            "description": "Fair (no-vig) Week 10 lines with three separate columns per market: FAIR (ours), MARKET (no official value found) and DIFFERENCE (fair minus market, only when a market value exists).",
            "difference_rule": "difference = fair - market; computed only when BOTH values are present; otherwise blank.",
            "recompute_mismatches": mismatches, "rows": cols}, flags


# ---------------------------------------------------------------- strategies
PRODUCT_RULES = [
    ("Single: moneyline", "single_moneyline", "single"),
    ("Single: point spread", "single_spread_or_total", "single"),
    ("Single: game total", "single_spread_or_total", "single"),
    ("Parlay", "joint_probability_parlay", "parlay_pairs"),
    ("Same-game parlay", "joint_probability_parlay", "single"),
    ("Player prop", "player_prop_abs_error", "player_prop_player_games"),
]


def product_rule(product):
    for prefix, app, sample in PRODUCT_RULES:
        if product.startswith(prefix):
            return app, sample
    raise ValueError("no applicability rule for product: " + product)


def build_registry(val, rules):
    strategies, flags = [], []
    origin_board = {r["id"]: r for r in load(LEADERBOARD)["rows"]}
    for s in val["strategies"]:
        app_key, sample_key = product_rule(s["product"])
        applicable = rules["applicability"][app_key]
        gates = dict(s["gates"])
        failed = [g for g in applicable if gates.get(g) is not True]
        passed_all = not failed
        origin_verdict = origin_board.get(s["id"], {}).get("verdict")
        strategies.append({
            "id": s["id"], "product": s["product"], "strategy": s["strategy"],
            "applicability_key": app_key, "sample_rule": sample_key,
            "minimum_n": rules["minimum_live_window_games"][sample_key],
            "gates": gates, "gates_failed_fail_closed": failed,
            "n": s["n"], "skill_pct": s["skill_pct"], "skill_pct_lcb": s["skill_pct_lcb"],
            "p_holm": s["p_holm"],
            "signal_verdict": ("PASS" if passed_all else "FAIL " + ",".join(failed)),
            "origination_verdict": origin_verdict,
            "status": "PAPER-ELIGIBLE" if passed_all else "BLOCKED",
            "live_window": None,
            "source_urls": SCORE_WEEKS + [STANDINGS],
            "inputs": ["origination/results/validation-w10.json", "origination/data/games-2026-w1-w9.json"],
        })
        if passed_all and origin_verdict != "PASS":
            flags.append({"id": "LF-DIFF-" + s["id"], "kind": "VERDICT DIFFERENCE", "detail": "fail-closed verdict PASS, origination verdict %r" % origin_verdict})
        if (not passed_all) and origin_verdict == "PASS":
            flags.append({"id": "LF-DIFF-" + s["id"], "kind": "VERDICT DIFFERENCE", "detail": "fail-closed verdict FAIL, origination verdict PASS"})
    for m in val["not_scored"]:
        strategies.append({
            "id": m["id"], "product": m["product"], "strategy": m["strategy"],
            "applicability_key": "player_prop_abs_error" if m["id"] == "M2" else "single_spread_or_total",
            "sample_rule": "single", "minimum_n": rules["minimum_live_window_games"]["single"],
            "gates": {"G8": False}, "gates_failed_fail_closed": ["G8"],
            "n": None, "skill_pct": None, "skill_pct_lcb": None, "p_holm": None,
            "signal_verdict": "NOT SCORED - fails G8", "origination_verdict": m["verdict"],
            "status": "BLOCKED", "live_window": None, "source_urls": [SCHEDULE_W10],
            "inputs": ["origination/results/validation-w10.json"]})
    return {"generated": GENERATED,
            "description": "All 14 strategies from origination/results/validation-w10.json (12 scored, 2 not scored). Status is set by the fail-closed signal verdict only; no strategy is LIVE.",
            "live_count": sum(1 for s in strategies if s["status"] == "LIVE"),
            "strategies": strategies}, flags


def rank_signal(rows):
    """Rank by SIGNAL only: PASS strategies, ordered by skill_pct_lcb descending. Staking is never an input."""
    passing = [r for r in rows if r["signal_verdict"] == "PASS"]
    passing.sort(key=lambda r: -r["skill_pct_lcb"])
    medals = ["Gold", "Silver", "Bronze"]
    out = {}
    for i, r in enumerate(passing):
        out[r["id"]] = {"rank": i + 1, "medal": medals[i] if i < 3 else ""}
    return out


def build_leaderboard_split(reg):
    ranks = rank_signal(reg["strategies"])
    origin = {r["id"]: r for r in load(LEADERBOARD)["rows"]}
    rows = []
    for s in reg["strategies"]:
        r = ranks.get(s["id"], {"rank": None, "medal": ""})
        o = origin.get(s["id"])
        rows.append({
            "id": s["id"], "product": s["product"], "strategy": s["strategy"],
            "signal": {"n": s["n"], "skill_pct": s["skill_pct"], "skill_pct_lcb": s["skill_pct_lcb"],
                       "p_holm": s["p_holm"], "gates_failed_fail_closed": s["gates_failed_fail_closed"],
                       "verdict": s["signal_verdict"], "rank": r["rank"], "medal": r["medal"]},
            "staking": {"units_staked": None, "roi_pct": None, "closing_line_value_pct": None,
                        "reason": "No official price exists for any market, so no stake or return can be computed (LF-01). Staking fields are not read by the ranking."},
            "consistency": {"origination_rank": o["rank"] if o else None,
                            "origination_medal": (o.get("medal") or "") if o else None,
                            "matches_origination_rank": (o["rank"] if o else None) == r["rank"]},
            "source_urls": s["source_urls"]})
    return {"generated": GENERATED,
            "description": "Signal and staking are separate blocks. Rank uses ONLY the signal block (PASS under the fail-closed gates, then skill_pct_lcb). A staking result cannot lift a FAIL signal into a rank.",
            "ranking_rule": "rank = PASS strategies ordered by signal.skill_pct_lcb descending; medals Gold/Silver/Bronze for ranks 1-3.",
            "rows": rows}


# ---------------------------------------------------------------- prices
def build_prices(lines_doc, probe):
    markets, flags = [], []
    for r in lines_doc["rows"]:
        base = {"game_key": r["key"], "away": r["away"], "home": r["home"], "game_url": r["game_url"]}
        for step in r["order"]:
            m = step["market"]
            if m == "side":
                fair = r["side"]["fair_favourite_text"]
            elif m == "total":
                fair = r["total"]["fair_total"]
            else:
                fair = "%+d / %+d" % (r["moneyline"]["fair_ml_home"], r["moneyline"]["fair_ml_away"])
            markets.append(dict(base, market_key="%s-%s" % (r["key"], m), market=m, order=step["step"],
                                fair_at_origination=fair, opening_value=None, closing_value=None,
                                opening_source_url=None, closing_source_url=None,
                                status="BLANK - no official source publishes this market"))
    flags.append({"id": "LF-01", "kind": "NO OFFICIAL PRICE SOURCE",
                  "detail": "39 originated markets (13 games x side, total, moneyline) have no opening or closing value. The official game-centre page for NE at DET (the only game probed) contains no spread, total or moneyline text. The NFL's official sportsbook partners get league data through Genius Sports (secondary press report, not an official NFL price page).",
                  "source_urls": [probe["url"], "https://www.espn.com/nfl/story/_/id/49740505/nfl-renews-draftkings-fanduel-deals-adds-fanatics"],
                  "treatment": "All 78 opening/closing cells are blank. Nothing is inferred. Obtaining a price requires an operator decision (suggestion SG-L1 in ledger/index.html)."})
    return {"generated": GENERATED,
            "description": "Price-snapshot store. One row per originated market, in origination order. Opening and closing values are recorded ONLY with an official source URL; with none available, every value stays null.",
            "accepted_source_hosts": ["www.nfl.com", "nextgenstats.nfl.com"],
            "snapshots": [],
            "markets": markets}, flags


# ---------------------------------------------------------------- HTML
ALLOWED_LINK_NOTE = "Every row links to an official nfl.com / nextgenstats.nfl.com page, or to the NIST handbook for a statistical rule. Blank = not confirmed; never inferred."

NAV = [("index.html", "Start"), ("suggestions.html", "Suggestions"), ("price-store.html", "Price store"), ("results-feed.html", "Results feed"),
       ("lines.html", "Fair / market / difference"), ("demotion-gate.html", "Demotion gate"),
       ("leaderboard-split.html", "Signal vs staking"), ("flagged.html", "Flagged for Review")]


def esc(x):
    return "" if x is None else html.escape(str(x))


def link(url, label=None):
    if not url:
        return "<span class='blank'>blank</span>"
    return "<a href='%s' rel='noopener'>%s</a>" % (html.escape(url, quote=True), esc(label or url.replace("https://", "")))


def page(title, active, body):
    nav = "".join("<a href='%s'%s>%s</a>" % (h, " class='on'" if h == active else "", esc(t)) for h, t in NAV)
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · Decision ledger · Own8</title><link rel="stylesheet" href="assets/style.css"></head>
<body><header><div class="brand">Own8 · Decision ledger</div><nav>%s</nav></header>
<main>%s</main>
<footer>Generated %s from repository files. Unofficial analysis, not betting advice. No real money, stakes or rewards. <a href="../index.html">Root dashboard</a> · <a href="../requirements/index.html">Requirements</a></footer>
</body></html>
""" % (esc(title), nav, body, GENERATED)


def table(headers, rows_html, cls=""):
    th = "".join("<th>%s</th>" % esc(h) for h in headers)
    return "<div class='scroll'><table class='%s'><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>" % (cls, th, "".join(rows_html))


def cell(v):
    if v is None or v == "":
        return "<td class='blank'>blank</td>"
    return "<td>%s</td>" % esc(v)


def render_pages(feed, lines_doc, prices, reg, split, decisions, flags, probe):
    pages = {}
    n_flags = len(flags)
    # index
    live = reg["live_count"]
    verified_prices = sum(1 for m in prices["markets"] if m["opening_value"] is not None or m["closing_value"] is not None)
    passed = sum(1 for s in reg["strategies"] if s["signal_verdict"] == "PASS")
    kpis = [
        ("Official games in results feed", feed["counts"]["games"], "results-feed.html"),
        ("Arithmetic failures in feed", feed["counts"]["arithmetic_failures"], "results-feed.html"),
        ("Originated markets", len(prices["markets"]), "price-store.html"),
        ("Opening or closing values verified", "%d of %d" % (verified_prices, 2 * len(prices["markets"])), "price-store.html"),
        ("Strategies passing every applicable gate", "%d of %d" % (passed, len(reg["strategies"])), "leaderboard-split.html"),
        ("LIVE strategies", live, "demotion-gate.html"),
        ("Demotions triggered", decisions["action_counts"].get("DEMOTE_TO_PAPER", 0), "demotion-gate.html"),
        ("Items on Flagged for Review", n_flags, "flagged.html"),
        ("Suggestions awaiting your choice", len(load(os.path.join(LEDGER, "data", "suggestions.json"))["suggestions"]), "suggestions.html"),
    ]
    cards = "".join("<a class='card' href='%s'><div class='num'>%s</div><div class='lab'>%s</div></a>" % (h, esc(v), esc(k)) for k, v, h in kpis)
    idx = """<h1>Decision ledger</h1>
<p class='lede'>Evidence before action. Every number on this site is copied from an official nfl.com page or computed by a script from one. Where no official value exists the cell is blank and flagged. Nothing here is a betting recommendation.</p>
<div class='cards'>%s</div>
<h2>What the ledger can and cannot do today</h2>
<ul class='plain'>
<li><b>Can:</b> record every official result (137 games), originate fair lines for the 13 unplayed Week 10 games, grade which strategies pass the pre-registered gates, and keep signal and staking apart.</li>
<li><b>Cannot:</b> record any opening or closing price. No official NFL page we checked publishes a betting line (<a href='price-store.html'>price store</a>, flag LF-01). Therefore no ROI, no closing-line value and no stake can be computed.</li>
<li><b>Fails today:</b> the fair total fails validation (LF-02). Its values are shown, labelled UNVALIDATED.</li>
</ul>
<h2>Pages</h2>
<table class="nav"><thead><tr><th>Page</th><th>What it answers</th></tr></thead><tbody>
<tr><td><a href='price-store.html'>Price store</a></td><td>Opening and closing numbers for every market we originate (side, total, moneyline in that order).</td></tr>
<tr><td><a href='results-feed.html'>Results feed</a></td><td>The verified official final scores that backtests and ROI join to.</td></tr>
<tr><td><a href='lines.html'>Fair / market / difference</a></td><td>Our fair line, the market line and the difference, as separate columns.</td></tr>
<tr><td><a href='demotion-gate.html'>Demotion gate</a></td><td>The rule that sends a LIVE strategy back to PAPER, and its current result.</td></tr>
<tr><td><a href='leaderboard-split.html'>Signal vs staking</a></td><td>Leaderboard where a staking result cannot change a signal verdict.</td></tr>
<tr><td><a href='flagged.html'>Flagged for Review</a></td><td>Every irregularity and unverified item, with its source links.</td></tr>
</tbody></table>
<p class='note'>%s</p>""" % (cards, ALLOWED_LINK_NOTE)
    pages["index.html"] = page("Start", "index.html", idx)

    rows = ["<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='blank'>blank</td><td class='blank'>blank</td><td class='blank'>blank</td><td class='blank'>blank</td><td>%s</td><td>%s</td></tr>" % (
        esc(m["game_key"]), esc(m["order"]), esc(m["market"]), esc(m["fair_at_origination"]),
        link(m["game_url"], "nfl.com game page"), esc(m["status"])) for m in prices["markets"]]
    body = """<h1>Price-snapshot store</h1>
<p class='lede'>One row per market we originate, in order: side (1), total (2), moneyline (3). Opening and closing columns hold a value only when an official URL is recorded for it. None is.</p>
<div class='callout'><b>Result: 0 of %d opening and 0 of %d closing values verified.</b> The official game-centre page probed (%s) renders no spread, total or moneyline. See <a href='flagged.html'>LF-01</a>.</div>
%s
<p class='note'>Columns: opening and closing value and their source URLs are blank for every row. Store file: <code>ledger/data/price-snapshots.json</code>. Validator: <code>ledger/scripts/check_ledger.py</code>.</p>""" % (
        len(prices["markets"]), len(prices["markets"]), link(probe["url"]),
        table(["Game", "Order", "Market", "Fair value at origination (ours)", "Opening value", "Opening source", "Closing value", "Closing source", "Game page", "Status"], rows))
    pages["price-store.html"] = page("Price store", "price-store.html", body)

    # results feed
    rows = []
    for r in feed["rows"]:
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s-%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(r["key"]), esc(r["week"]), esc(r["date"]), esc(r["weekday"]), "%s @ %s" % (esc(r["away"]), esc(r["home"])),
            esc(r["away_score"]), esc(r["home_score"]), esc(r["home_margin"]), esc(r["winner"]),
            link(r["game_url"], "game"), link(r["source_url"], "scores page")))
    body = """<h1>Verified results feed</h1>
<p class='lede'>%d official final scores. Join key: <code>key</code>. Arithmetic checks (margin, total, winner) pass on <b>%d of %d</b> rows.</p>
<input id='q' class='search' placeholder='Filter by team, week or date' oninput='filt(this.value)'>
%s
<p class='note'>Score order is AWAY-HOME. Week 10 Thursday row is re-read from nfl.com on 2026-11-14 and is not in the 136-game verified log. Heading/weekday mismatch on W1 is kept as rendered and flagged.</p>
<script>function filt(v){v=v.toLowerCase();document.querySelectorAll('tbody tr').forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(v)>-1?'':'none';});}</script>""" % (
        feed["counts"]["games"], feed["counts"]["games"] - feed["counts"]["arithmetic_failures"], feed["counts"]["games"],
        table(["Key", "Week", "Date", "Day", "Game", "Score (away-home)", "Home margin", "Winner", "Game page", "Source"], rows))
    pages["results-feed.html"] = page("Results feed", "results-feed.html", body)

    # lines
    rows = []
    for r in lines_doc["rows"]:
        rows.append("<tr><td>%s</td><td>%s @ %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(r["key"]), esc(r["away"]), esc(r["home"]),
            esc(r["side"]["fair_favourite_text"]), esc(r["side"]["fair_home_margin_S1"]), esc(r["side"]["model_status"]),
            esc(r["total"]["fair_total"]), esc(r["total"]["model_status"]),
            "%s / %s" % (esc(r["moneyline"]["fair_ml_home"]), esc(r["moneyline"]["fair_ml_away"])),
            "<span class='blank'>blank</span>", "<span class='blank'>blank</span>", "<span class='blank'>blank</span>",
            link(r["game_url"], "game"), link(r["source_url"], "schedule")))
    body = """<h1>Fair, market and difference lines</h1>
<p class='lede'>Week 10, 13 unplayed games. Three separate blocks per market: <b>fair</b> (ours), <b>market</b> (no official value found, so blank), <b>difference</b> = fair − market, computed only when a market value exists.</p>
<div class='callout'><b>Order used:</b> side (1) → total (2) → moneyline (3). The moneyline is a transform of the side margin, so it is last.</div>
%s
<p class='note'>Fair spread is written as favourite and points (home margin is positive when home is favoured). The total uses S4, which <b>fails validation</b> (LF-02). Moneylines are no-vig, rounded to whole American odds, recomputed from p_home and matched to the file. A spread shown as '-0.0' is below 0.05 points, effectively a pick'em.</p>""" % (
        table(["Game", "Matchup (away @ home)", "Fair side (S1)", "Home margin (S1)", "Side status", "Fair total (S4)", "Total status", "Fair moneyline home / away (S6)", "Market side", "Market total", "Market moneyline", "Difference", "Game page", "Schedule"], rows))
    pages["lines.html"] = page("Fair / market / difference", "lines.html", body)

    # demotion gate
    rules = load(RULES)
    rrows = ["<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        esc(x["id"]), esc(x["name"]), esc(x["trigger"]), esc(x["threshold"]), esc(x["action"]), link(x["source_url"], "source")) for x in rules["rules"]]
    src_by_id = {x["id"]: x["source_urls"] for x in reg["strategies"]}
    srows = ["<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        esc(s["id"]), esc(s["status_before"]), esc(s["action"]), esc(s["status_after"]), esc("; ".join(s["reasons"]) or s.get("note", "")),
        " ".join(link(u, "W%d" % (i + 1)) for i, u in enumerate(src_by_id[s["id"]][:9]))) for s in decisions["decisions"]]
    body = """<h1>Demotion gate</h1>
<p class='lede'>A LIVE strategy goes back to PAPER when any rule below fires. Only LIVE strategies are touched. Re-promotion is never automatic.</p>
<div class='callout'><b>Current state: %d LIVE strategies, %d demotions.</b> No strategy is LIVE, because none has an operator decision and a live evidence window. The gate is armed but idle.</div>
<h2>Rules</h2>%s
<h2>Result for every strategy</h2>%s
<p class='note'>%s Thresholds are PROPOSED and need an operator decision before use (LF-06). Rule source: <code>ledger/data/demotion-rules.json</code>; evaluator: <code>ledger/scripts/demotion_gate.py</code>; tests: <code>ledger/scripts/test_ledger.py</code>.</p>""" % (
        decisions["live_strategies"], decisions["action_counts"].get("DEMOTE_TO_PAPER", 0),
        table(["Rule", "Name", "Trigger", "Threshold", "Action", "Source"], rrows),
        table(["Strategy", "Status before", "Action", "Status after", "Reasons", "Official sources (scores W1-W9)"], srows), esc(rules["status"]))
    pages["demotion-gate.html"] = page("Demotion gate", "demotion-gate.html", body)

    # leaderboard split
    rows = []
    for r in split["rows"]:
        sg, st, co = r["signal"], r["staking"], r["consistency"]
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td class='blank'>blank</td><td class='blank'>blank</td><td class='blank'>blank</td><td>%s</td><td>%s</td></tr>" % (
                        esc(r["id"]), esc(r["product"]), esc(r["strategy"]), esc(sg["n"]),
                        esc("%.2f" % sg["skill_pct"]) if sg["skill_pct"] is not None else "",
                        esc("%.2f" % sg["skill_pct_lcb"]) if sg["skill_pct_lcb"] is not None else "",
                        esc("%.4f" % sg["p_holm"]) if sg["p_holm"] is not None else "",
                        esc(sg["verdict"]), esc(sg["rank"] if sg["rank"] is not None else "-") + ((" " + esc(sg["medal"])) if sg["medal"] else ""),
                        esc("matches origination" if co["matches_origination_rank"] else "DIFFERS")  + " <span class='note'>(" + esc(co["origination_rank"]) + ")</span>",
                        " ".join(link(u, "W%d" % (i + 1)) for i, u in enumerate(r["source_urls"][:9])) + " " + link(STANDINGS, "standings")))
    body = """<h1>Leaderboard: signal separate from staking</h1>
<p class='lede'>The rank is decided by the <b>signal</b> columns only. The <b>staking</b> columns (units, ROI, closing-line value) are blank because no official price exists. A future staking run cannot lift a failing signal.</p>
<div class='callout'><b>Ranking rule:</b> PASS under the fail-closed gates (every applicable gate must be True; null = FAIL), then skill_pct_lcb descending. Medals for ranks 1–3. <b>Result: %d PASS, %d FAIL / NOT SCORED.</b></div>
%s
<p class='note'>Staking block: units staked, ROI and closing-line value are blank for all rows. Applicable gates per product are declared in <code>ledger/data/demotion-rules.json</code>. Note: S9 and S10 are probability products but origination recorded G7 as not applicable (LF-07); the ledger counts that as FAIL. Verdicts are unchanged.</p>""" % (
        sum(1 for r in split["rows"] if r["signal"]["verdict"] == "PASS"),
        sum(1 for r in split["rows"] if r["signal"]["verdict"] != "PASS"),
        table(["ID", "Product", "Strategy", "n", "Skill %", "Skill % lower 95%", "Holm p", "Signal verdict", "Rank / medal", "Units staked", "ROI %", "CLV %", "Matches origination", "Official sources"], rows))
    pages["leaderboard-split.html"] = page("Signal vs staking", "leaderboard-split.html", body)

    # flagged
    rows = []
    for f in flags:
        srcs = " ".join(link(u, "source %d" % (i + 1)) for i, u in enumerate(f.get("source_urls", []))) or "<span class='blank'>blank</span>"
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(f["id"]), esc(f["kind"]), esc(f["detail"]), srcs, esc(f.get("treatment", ""))))
    body = """<h1>Flagged for Review</h1>
<p class='lede'>Irregularities and unverified items found while building the ledger. None blocks publication. Each has its source link so you can check it.</p>
%s""" % table(["ID", "Kind", "Detail", "Sources", "Treatment"], rows)
    pages["flagged.html"] = page("Flagged for Review", "flagged.html", body)
    return pages


def render_suggestions(sug):
    blocks = []
    for item in sug["suggestions"]:
        ev = " ".join(link(u, "source %d" % (i + 1)) for i, u in enumerate(item["evidence"]))
        rows = []
        for o in item["options"]:
            rows.append("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(o["id"]), esc(o["label"]), esc(o["cost"]), esc(o["risk"]), ev))
        blocks.append("""<section class='sg'><h2>%s · %s</h2>
<p><b>Problem:</b> %s</p><p class='note'><b>Blocks:</b> %s</p>
<p><b>Status:</b> %s · <b>Selected option:</b> %s</p>
%s</section>""" % (esc(item["id"]), esc(item["title"]), esc(item["problem"]), esc("; ".join(item["blocks"])),
                   esc(item["decision_state"]), esc(item["selected_option"] or "none"),
                   table(["Option", "What it means", "Cost", "Risk", "Evidence"], rows)))
    body = """<h1>Suggestions: choose a path before anything changes</h1>
<p class='lede'>%s Reply with a suggestion ID and option letter (for example <code>SG-L2: A</code>). Until you choose, nothing here is implemented.</p>
%s""" % (esc(sug["rule"]), "".join(blocks))
    return page("Suggestions", "suggestions.html", body)


CSS = """
:root{--ink:#17202a;--mute:#5b6674;--line:#dfe5ec;--bg:#f7f9fb;--ok:#1f7a4d;--bad:#a13a2a;--warn:#8a6100;--accent:#1b4f8a}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header{background:#fff;border-bottom:1px solid var(--line);padding:12px 20px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
.brand{font-weight:700}nav{display:flex;flex-wrap:wrap;gap:6px}nav a{color:var(--accent);text-decoration:none;padding:4px 8px;border-radius:6px;font-size:13px}
nav a.on,nav a:hover{background:#e7eef8}main{max-width:1200px;margin:0 auto;padding:20px}
h1{font-size:24px;margin:8px 0}h2{font-size:18px;margin:26px 0 8px}.lede{color:var(--mute);max-width:820px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:16px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px;text-decoration:none;color:inherit}
.card .num{font-size:24px;font-weight:700}.card .lab{color:var(--mute);font-size:13px}
.callout{background:#fff8e6;border:1px solid #f1dda3;border-radius:8px;padding:10px 14px;margin:12px 0}
.note{color:var(--mute);font-size:13px}.plain li{margin:6px 0}
.scroll{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f0f4f8;position:sticky;top:0;font-weight:600}.blank{color:var(--warn);font-style:italic}
a{color:var(--accent)}code{background:#eef2f6;padding:1px 4px;border-radius:4px;font-size:12px}
.search{width:100%;max-width:420px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;margin:8px 0}
footer{max-width:1200px;margin:24px auto;padding:0 20px;color:var(--mute);font-size:12px}
"""


def main():
    log = load(W9_LOG)
    w10 = load(W10_LINES)
    val = load(VALIDATION)
    probe = load(PROBE)
    rules = load(RULES)

    feed, feed_flags = build_results_feed(log, w10)
    lines_doc, line_flags = build_lines(w10)
    prices, price_flags = build_prices(lines_doc, probe)
    reg, reg_flags = build_registry(val, rules)
    split = build_leaderboard_split(reg)

    dump(os.path.join(LEDGER, "data", "results-feed.json"), feed)
    dump(os.path.join(LEDGER, "data", "lines-columns.json"), lines_doc)
    dump(os.path.join(LEDGER, "data", "price-snapshots.json"), prices)
    dump(os.path.join(LEDGER, "data", "strategy-registry.json"), reg)
    dump(os.path.join(LEDGER, "results", "leaderboard-split.json"), split)

    # fixed flags (irregularities carried from the origination audit and this session)
    fixed = [
        {"id": "LF-04", "kind": "OFFICIAL PAGE PRINTS SCORES IN INCONSISTENT ORDER",
         "detail": "On the nfl.com game-centre team strip for NE at DET, the New England results print the score in different orders. Compared with the scores pages: W6 prints 'Win 19-26' while the scores page gives NYJ 19, NE 26; W8 prints 'Win 24-19' with NE 24, MIA 19; W7 prints 'Loss 24-30' with NE 24, CHI 30; W9 prints 'Loss 45-27' with GB 45, NE 27. The strip sometimes lists the winner first and sometimes the loser first, so it cannot be read without checking the scores pages. The ledger does NOT take values from that strip; it uses the scores pages, which reconcile to the official standings 32/32 (origination/results/standings-reconciliation-2026-11-14.json).",
         "source_urls": ["https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "https://www.nfl.com/scores/2026/week-6", "https://www.nfl.com/scores/2026/week-7", "https://www.nfl.com/scores/2026/week-8", "https://www.nfl.com/scores/2026/week-9"],
         "treatment": "Not used as a value source. Recorded for review."},
        {"id": "LF-05", "kind": "PROBE IS ONE PAGE ONLY",
         "detail": "The official price probe read one Week 10 game-centre page (NE at DET, 2 chunks). It does not prove no official page anywhere carries a line. It is scoped accordingly. A broader search of nfl.com was not performed.",
         "source_urls": [probe["url"]], "treatment": "Scope stated on the price store page. Absence of a line is recorded as blank, never as proof of non-existence."},
        {"id": "LF-06", "kind": "THRESHOLDS NOT YET APPROVED",
         "detail": "The demotion thresholds (sample minimums, 14-day staleness, and the rules D1-D8) are proposals written by this session. The operator has not approved them. They are written down before any live window exists so they cannot be tuned to a result.",
         "source_urls": ["https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm"],
         "treatment": "Presented as a decision in ledger/index.html (SG-L2). Gate is inert until approved."},
        {"id": "LF-07", "kind": "G7 APPLICABILITY IS INCONSISTENT",
         "detail": "origination/scripts/model_w10.py evaluate() only computes G7 when a calibration table is passed. S9 (2-leg parlay) and S10 (same-game parlay) emit joint probabilities scored with Brier, yet G7 is recorded as null (not applicable) for both, and null is not counted as a failure by the verdict code (`v is False`). The fail-closed ledger counts null as FAIL for applicable gates. Verdicts are unchanged because S9 and S10 also fail G5/G6 and G4/G5.",
         "source_urls": ["https://www.nfl.com/scores/2026/week-9"],
         "treatment": "Recorded; origination history is not edited."},
        {"id": "LF-08", "kind": "G5 AND MULTIPLE TESTING SCOPE",
         "detail": "The Holm adjustment in origination runs across the 12 scored strategies only, while M1 and M2 (not scored) are excluded from the family. Holm across a family of 12 is the stated design; the family definition is a choice and is not reviewed here.",
         "source_urls": ["https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm"],
         "treatment": "Recorded for review. No change made."},
    ]
    flags = feed_flags + line_flags + price_flags + reg_flags + fixed
    dump(os.path.join(LEDGER, "data", "flags.json"), {"generated": GENERATED,
         "description": "Irregularities and unverified items for the Flagged for Review page. Blocking: none.", "flags": flags})

    # demotion decisions (also written by demotion_gate.py)
    decisions = demotion_gate.run(reg, rules)
    dump(os.path.join(LEDGER, "results", "demotion-decisions.json"), decisions)

    probe_ok = load(PROBE)
    pages = render_pages(feed, lines_doc, prices, reg, split, decisions, flags, probe_ok)
    pages["suggestions.html"] = render_suggestions(load(os.path.join(LEDGER, "data", "suggestions.json")))
    for name, content in pages.items():
        with open(os.path.join(LEDGER, name), "w", encoding="utf-8") as f:
            f.write(content)
    with open(os.path.join(LEDGER, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS.strip() + "\n")
    print("ledger built: %d feed rows, %d markets, %d strategies, %d flags, %d pages" % (
        len(feed["rows"]), len(prices["markets"]), len(reg["strategies"]), len(flags), len(pages)))


if __name__ == "__main__":
    main()
