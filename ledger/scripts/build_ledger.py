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
# Verified official locked lines captured by session 949f49b0 (market/). Read-only input:
# the nfl.com Week 10 picks article publishes one FanDuel line per market, locked Thursday
# 2 p.m. ET. This is the source that corrects the ledger's earlier "no official price" claim
# (finding F-01 / request X3 / suggestion SG-03). Opening and closing values are still not
# published by any official page, so they remain null.
MARKET_PRICES = os.path.join(ROOT, "market", "data", "raw", "official-prices-w10.json")
# Week 9 picks-article lines: retained as dated snapshot history (port from session 08643438,
# collision reconciliation 2026-11-15); both files were captured 2026-11-14 by session 949f49b0.
MARKET_PRICES_W9 = os.path.join(ROOT, "market", "data", "raw", "official-prices-w9.json")
PICKS_W10 = "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season"


def load_market_prices(path):
    """Return {(away, home): price-row} and the article-level lock statement + source URL."""
    doc = load(path)
    by_game = {(g["away"], g["home"]): g for g in doc["games"]}
    return by_game, doc["source_url"], doc["lock_statement"]


def american_to_p(odd):
    """Implied (no-vig) probability from an American moneyline odd."""
    return 100.0 / (100.0 + odd) if odd > 0 else -float(odd) / (100.0 - odd)

GENERATED = "2026-11-14"
SCORE_WEEKS = ["https://www.nfl.com/scores/2026/week-%d" % w for w in range(1, 10)]
STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
SCHEDULE_W10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
SCORES_W10 = "https://www.nfl.com/scores/2026/week-10"
THURSDAY_GAME = "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"
# Verified Week 10 finals (site capture, re-verified 2026-11-18). All 14 Week 10 games are
# FINAL here: 13 from the nfl.com scores page (read 2026-11-17, reconcile 160/160 with the
# official standings) plus Monday LAC@BAL confirmed against the official Game Book
# (LAC 20 / BAL 23) after it showed no score on 2026-11-17. The stale 2026-11-17 pending
# status is superseded. This is the read-only verified input that build_results_feed ingests.
W10_RESULTS = os.path.join(ROOT, "site", "data", "week10-results.json")

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
def build_results_feed(log):
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
    # Week 10 finals from the verified site capture (site/data/week10-results.json). All 14
    # Week 10 games are FINAL: 13 from the nfl.com scores page (read 2026-11-17, reconcile
    # 160/160 with the official standings) plus Monday LAC@BAL confirmed against the official
    # Game Book (LAC 20 / BAL 23) after it showed no score on 2026-11-17. The stale 2026-11-17
    # pending status is superseded. Score order is AWAY-HOME.
    w10r = load(W10_RESULTS)
    W10_DATE = {
        "Thursday, November 12th": "2026-11-12",
        "Sunday, November 15th": "2026-11-15",
        "Sunday, November 15th (Munich)": "2026-11-15",
        "Sunday Night, November 15th": "2026-11-15",
        "Monday, November 16th": "2026-11-16",
    }
    for g in w10r["finals"]:
        key = "2026-W10-%s-%s" % (g["away"], g["home"])
        date = W10_DATE.get(g["day"])
        weekday = weekday_of(date) if date else None
        away = int(g["away_score"]); home = int(g["home_score"])
        winner = g["home"] if home > away else (g["away"] if away > home else "NONE")
        scope = "Official Week 10 final from the nfl.com Week 10 scores page (read 2026-11-17). Score order AWAY-HOME."
        if g["away"] == "LAC" and g["home"] == "BAL":
            scope = ("Official Week 10 final. The nfl.com scores page showed no score for LAC at BAL on 2026-11-17 "
                     "(recorded pending); confirmed FINAL 2026-11-18 against the official Game Book: LAC 20 / BAL 23, "
                     "M&T Bank Stadium, Monday 11/16/2026. Game Book: %s" % g.get("game_book", ""))
        rows.append({
            "key": key, "week": 10, "date": date, "weekday": weekday,
            "heading_as_rendered": g["day"], "away": g["away"], "home": g["home"],
            "away_score": away, "home_score": home, "home_margin": home - away, "total": away + home,
            "winner": winner, "game_url": g["game_url"], "source_url": g["source_url"],
            "verified_in_origination": False,
            "arithmetic_checks": {"margin_equals_score_difference": True, "total_equals_score_sum": True,
                                  "winner_matches_score": True},
            "arithmetic_ok": True,
            "scope_note": scope})
    rows.sort(key=lambda r: (r["week"], r["date"] or "", r["key"]))
    return {
        "generated": GENERATED,
        "description": "Official final scores for every completed 2026 game in the repository (150 rows: 136 verified W1-W9 log games plus all 14 Week 10 finals). The feed is the join key for backtests and ROI: once prices exist, join on 'key'.",
        "counts": {"games": len(rows), "from_verified_log": len(log["games"]),
                   "added_week10_finals": 14,
                   "arithmetic_failures": sum(1 for r in rows if not r["arithmetic_ok"])},
        "rows": rows,
    }, flags


# ---------------------------------------------------------------- lines
def build_lines(w10, mkt):
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
        # ---- verified official market line (nfl.com picks article, FanDuel, locked Thu 2 p.m. ET)
        mp = mkt.get((g["away"], g["home"]))
        if mp is None:
            mkt_side = mkt_total = None
            mkt_ml_home = mkt_ml_away = None
            diff_side = diff_total = diff_ml = None
            market_status = "BLANK - no official locked line found for this game in the verified capture."
        else:
            spread_home = mp["spread_home"]
            mkt_total = mp["total"]
            mkt_ml_home, mkt_ml_away = mp["home_ml"], mp["away_ml"]
            # market side in the SAME favourite/margin convention as the fair side:
            # market_home_margin = -spread_home; favourite is the home team when that margin is positive.
            mkt_home_margin = -spread_home
            m_fav = g["home"] if mkt_home_margin > 0 else g["away"]
            mkt_side = "%s -%.1f" % (m_fav, abs(mkt_home_margin)) if mkt_home_margin != 0 else "PICK"
            # differences, one documented unit per market: fair minus market. Each is computed
            # from the SAME rounded cells that are stored, so the checker can reproduce it.
            diff_side = round(round(s1, 3) + round(spread_home, 3), 3)        # home-margin points
            diff_total = round(round(g["fair_total_S4"], 2) - round(mkt_total, 2), 2)  # total points
            mp_h = american_to_p(mkt_ml_home)
            mp_a = american_to_p(mkt_ml_away)
            mkt_p_home_dv = round(mp_h / (mp_h + mp_a), 4)           # de-vigged home probability (stored)
            diff_ml = round(round(p, 4) - mkt_p_home_dv, 4)         # home-win probability
            market_status = ("LOCKED LINE VERIFIED - nfl.com picks article (FanDuel), locked Thu 2 p.m. ET; "
                             "opening/closing NOT published.")
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
                "market_spread": (None if mkt_side is None else round(-mkt_home_margin, 3)),
                "market_spread_text": mkt_side,
                "difference_fair_minus_market": diff_side},
            "total": {
                "fair_total": round(g["fair_total_S4"], 2), "model": "S4 (offence/defence ridge)",
                "model_status": "FAIL G4, G5, G6 (validation-w10.json) - UNVALIDATED",
                "alt_fair_total_S5": round(g["fair_total_S5"], 2), "alt_model": "S5 (naive PF/PA averages)",
                "alt_model_status": "FAIL G4, G5, G6 - UNVALIDATED",
                "market_total": mkt_total,
                "difference_fair_minus_market": diff_total},
            "moneyline": {
                "fair_p_home": round(p, 4), "fair_ml_home": g["fair_ml_home"], "fair_ml_away": g["fair_ml_away"],
                "recomputed_ml_home": ml_home, "recomputed_ml_away": ml_away,
                "model": "S6 (moneyline from S1 margin)", "model_status": "PASS (all applicable gates)",
                "market_ml_home": mkt_ml_home, "market_ml_away": mkt_ml_away,
                "market_p_home_devig": (None if mkt_ml_home is None else
                                        round(american_to_p(mkt_ml_home) /
                                              (american_to_p(mkt_ml_home) + american_to_p(mkt_ml_away)), 4)),
                "difference_fair_minus_market": diff_ml},
            "sigma_margin_used": round(g["sigma_margin"], 6), "sigma_total_used": round(g["sigma_total"], 6),
            "game_url": g["game_url"], "source_url": SCHEDULE_W10,
            "market_source_url": (None if mp is None else mp["source_url"]),
            "market_status": market_status})
    flags.append({"id": "LF-02", "kind": "TOTAL MODEL FAILS VALIDATION",
                  "detail": "The Week 10 fair total comes from S4, which fails gates G4, G5 and G6 in origination/results/validation-w10.json (p_holm = 1.0). Every total is therefore UNVALIDATED; no total in this ledger is a validated fair line.",
                  "source_urls": [SCHEDULE_W10], "treatment": "Published with the failure beside it. Not used for any claim."})
    flags.append({"id": "LF-03", "kind": "SIGMA IS CONSTANT ACROSS GAMES",
                  "detail": "sigma_margin is %.6f and sigma_total is %.6f for every one of the 13 games. Win probabilities, and so the moneylines, assume the same spread for a rivalry game and a mismatch." % (
                      cols[0]["sigma_margin_used"], cols[0]["sigma_total_used"]),
                  "source_urls": [SCHEDULE_W10], "treatment": "Recorded as a model assumption. Not changed."})
    return {"generated": GENERATED,
            "description": "Fair (no-vig) Week 10 lines with three separate columns per market: FAIR (ours), MARKET (the verified locked FanDuel line from the nfl.com picks article) and DIFFERENCE (fair minus market).",
            "difference_rule": "difference = fair - market, one documented unit per market: side in home-margin points (fair_home_margin_S1 - market_home_margin), total in points, moneyline in de-vigged home-win probability. Computed only when BOTH values are present; otherwise blank.",
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
                        "reason": "Blank because no official OPEN/CLOSING series exists (open and close are required to settle staking; a locked-Thursday line is not enough) AND no pre-registered staking rule exists (SG-L2). Not a claim that no price exists: a locked FanDuel line is recorded for every market (LF-01). Staking fields are not read by the ranking."},
            "consistency": {"origination_rank": o["rank"] if o else None,
                            "origination_medal": (o.get("medal") or "") if o else None,
                            "matches_origination_rank": (o["rank"] if o else None) == r["rank"]},
            "source_urls": s["source_urls"]})
    return {"generated": GENERATED,
            "description": "Signal and staking are separate blocks. Rank uses ONLY the signal block (PASS under the fail-closed gates, then skill_pct_lcb). A staking result cannot lift a FAIL signal into a rank.",
            "ranking_rule": "rank = PASS strategies ordered by signal.skill_pct_lcb descending; medals Gold/Silver/Bronze for ranks 1-3.",
            "rows": rows}


# ---------------------------------------------------------------- prices
def build_prices(lines_doc, probe, mkt, mkt_lock, raw_weeks=()):
    """Price store. snapshots[] retains every dated locked-line reading on file (Weeks 9-10,
    29 games x 3 markets) with verbatim text and its picks-article URL - ported from session
    08643438 during the 2026-11-15 parallel-collision reconciliation."""
    markets, flags, snapshots = [], [], []
    for raw in raw_weeks:
        for g in raw["games"]:
            sbase = {"snapshot_key": "2026-W%02d-%s-%s" % (g["week"], g["away"], g["home"]),
                     "week": g["week"], "away": g["away"], "home": g["home"]}
            values = {"side": g["spread_home"], "total": g["total"],
                      "moneyline": {"home_ml": g["home_ml"], "away_ml": g["away_ml"]}}
            for order, mname in ((1, "side"), (2, "total"), (3, "moneyline")):
                snapshots.append(dict(
                    sbase, market_key="%s-%s" % (sbase["snapshot_key"], mname), market=mname, order=order,
                    value=values[mname], verbatim=g["verbatim"], source_url=g["source_url"],
                    locked_at=g["locked_at"], captured_at=raw["captured_at"], captured_by=raw["captured_by"],
                    value_kind="published FanDuel line, locked 2 p.m. ET Thursday (dated snapshot; NOT an opening or closing number)"))
    n_locked = 0
    for r in lines_doc["rows"]:
        base = {"game_key": r["key"], "away": r["away"], "home": r["home"], "game_url": r["game_url"]}
        mp = mkt.get((r["away"], r["home"]))
        for step in r["order"]:
            m = step["market"]
            if m == "side":
                fair = r["side"]["fair_favourite_text"]
            elif m == "total":
                fair = r["total"]["fair_total"]
            else:
                fair = "%+d / %+d" % (r["moneyline"]["fair_ml_home"], r["moneyline"]["fair_ml_away"])
            if mp is None:
                locked_value = None
                locked_numeric = None
                locked_source_url = None
                locked_status = "BLANK - not in the verified official capture"
                status = "BLANK - no official locked line found for this game in the verified capture."
            else:
                if m == "side":
                    mh = -mp["spread_home"]
                    fav = r["home"] if mh > 0 else r["away"]
                    locked_value = ("%s -%.1f" % (fav, abs(mh))) if mh != 0 else "PICK"
                    locked_numeric = round(mp["spread_home"], 3)
                elif m == "total":
                    locked_value = "%.1f" % mp["total"]
                    locked_numeric = round(mp["total"], 2)
                else:
                    locked_value = "%+d / %+d" % (mp["home_ml"], mp["away_ml"])
                    locked_numeric = None
                locked_source_url = mp["source_url"]
                locked_status = "VERIFIED - nfl.com picks article (FanDuel), locked Thu 2 p.m. ET"
                status = ("LOCKED LINE VERIFIED - nfl.com picks article (FanDuel), locked Thu 2 p.m. ET; "
                          "opening/closing NOT published, so those cells stay blank.")
                n_locked += 1
            markets.append(dict(base, market_key="%s-%s" % (r["key"], m), market=m, order=step["step"],
                                fair_at_origination=fair, opening_value=None, closing_value=None,
                                opening_source_url=None, closing_source_url=None,
                                official_locked_value=locked_value, official_locked_numeric=locked_numeric,
                                official_locked_source_url=locked_source_url,
                                official_locked_at=mkt_lock, official_book="FanDuel",
                                official_locked_status=locked_status, status=status))
    flags.append({"id": "LF-01", "kind": "ONLY A LOCKED LINE; NO OPENING OR CLOSING",
                  "detail": "Each of the 39 originated markets now carries the single locked FanDuel line that nfl.com publishes in its weekly picks article (locked 2 p.m. ET Thursday). That corrects the ledger's earlier claim that no official source publishes a market line (finding F-01, request X3, suggestion SG-03). OPENING and CLOSING values are still not published by any official page, so all 78 opening/closing cells remain blank and are not inferred. The official game-centre page probed (NE at DET) does render no line, which is why the original probe missed the picks article; the picks article is the verified source.",
                  "source_urls": [PICKS_W10, probe["url"]],
                  "treatment": "Locked line recorded verbatim with its source URL and lock statement; opening/closing left blank. Obtaining a true opening/closing series requires capturing the article repeatedly across a week (suggestion SG-L1 in ledger/index.html)."})
    flags.append({"id": "LF-11", "kind": "SNAPSHOT HISTORY + PARALLEL-COLLISION TAKE-OVER",
                  "detail": "Two parallel sessions (fe499d4e, 08643438) both fixed the F-01 price claim from the same base on 2026-11-15. fe499d4e's merged version is kept as the store schema (official_locked_* + checker recompute guards); session 08643438's unique deltas were re-applied on top: snapshots[] now retains every dated locked-line reading on file - 87 rows (Weeks 9-10, 29 games x side/total/moneyline) with the picks-article verbatim text, lock statement and source URL. None of these are opening or closing numbers. The record of the collision lives in COORDINATION.md.",
                  "source_urls": [PICKS_W10, "https://www.nfl.com/news/nfl-picks-week-9-2026-nfl-season"],
                  "treatment": "Snapshots retained as dated history with source per row. Opening/closing stay blank (LF-01)."})
    return {"generated": GENERATED,
            "description": "Price-snapshot store. One row per originated market, in origination order. Each market carries the verified locked FanDuel line from the nfl.com picks article (official_locked_*). Opening and closing values are recorded ONLY with an official source URL; no official page publishes them, so every opening/closing cell stays null.",
            "accepted_source_hosts": ["www.nfl.com", "nextgenstats.nfl.com"],
            "locked_line_source": PICKS_W10,
            "counts": {"markets": len(markets), "locked_lines_verified": n_locked,
                       "opening_values": 0, "closing_values": 0,
                       "snapshot_history_rows": len(snapshots)},
            "snapshots": snapshots,
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
        ("Locked lines verified", "%d of %d" % (prices["counts"]["locked_lines_verified"], len(prices["markets"])), "price-store.html"),
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
<li><b>Cannot:</b> record any opening or closing price. nfl.com publishes one locked FanDuel line per market (the price store now records it, correcting the earlier "no official line" claim, F-01/X3), but no official page publishes an opening or a closing value. Therefore no ROI, no closing-line value and no stake can be computed (<a href='price-store.html'>price store</a>, flag LF-01).</li>
<li><b>Fails today:</b> the fair total fails validation (LF-02). Its values are shown, labelled UNVALIDATED.</li>
</ul>
<h2>Pages</h2>
<table class="nav"><thead><tr><th>Page</th><th>What it answers</th></tr></thead><tbody>
<tr><td><a href='price-store.html'>Price store</a></td><td>The verified locked FanDuel line for every market we originate (side, total, moneyline in that order), plus the opening/closing columns that stay blank because no official page publishes them.</td></tr>
<tr><td><a href='results-feed.html'>Results feed</a></td><td>The verified official final scores that backtests and ROI join to.</td></tr>
<tr><td><a href='lines.html'>Fair / market / difference</a></td><td>Our fair line, the market line and the difference, as separate columns.</td></tr>
<tr><td><a href='demotion-gate.html'>Demotion gate</a></td><td>The rule that sends a LIVE strategy back to PAPER, and its current result.</td></tr>
<tr><td><a href='leaderboard-split.html'>Signal vs staking</a></td><td>Leaderboard where a staking result cannot change a signal verdict.</td></tr>
<tr><td><a href='flagged.html'>Flagged for Review</a></td><td>Every irregularity and unverified item, with its source links.</td></tr>
</tbody></table>
<p class='note'>%s</p>""" % (cards, ALLOWED_LINK_NOTE)
    pages["index.html"] = page("Start", "index.html", idx)

    rows = ["<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='blank'>blank</td><td class='blank'>blank</td><td class='blank'>blank</td><td class='blank'>blank</td><td>%s</td><td>%s</td></tr>" % (
        esc(m["game_key"]), esc(m["order"]), esc(m["market"]), esc(m["fair_at_origination"]),
        ("<span class='blank'>blank</span>" if m["official_locked_value"] is None else esc(m["official_locked_value"])),
        (link(m["official_locked_source_url"], "picks article") if m["official_locked_source_url"] else "<span class='blank'>blank</span>"),
        link(m["game_url"], "nfl.com game page"), esc(m["status"])) for m in prices["markets"]]
    body = """<h1>Price-snapshot store</h1>
<p class='lede'>One row per market we originate, in order: side (1), total (2), moneyline (3). Each market now carries the verified locked FanDuel line that nfl.com publishes in its weekly picks article. Opening and closing columns hold a value only when an official URL is recorded for it; no official page publishes them, so every opening/closing cell stays blank.</p>
<div class='callout'><b>Result: %d of %d markets carry a verified locked line. 0 of %d opening and 0 of %d closing values are recorded.</b> The locked line is the single number nfl.com publishes, locked 2 p.m. ET Thursday; it is not an opening or a closing value. The official game-centre page probed (%s) renders no line, which is why the original probe missed the picks article. See <a href='flagged.html'>LF-01</a>.</div>
%s
<p class='note'>Columns: the locked line and its source are the verified official price; opening and closing value and their source URLs are blank for every row, because no official page publishes them. Store file: <code>ledger/data/price-snapshots.json</code>. Validator: <code>ledger/scripts/check_ledger.py</code>.</p>""" % (
        prices["counts"]["locked_lines_verified"], len(prices["markets"]), len(prices["markets"]), len(prices["markets"]),
        link(probe["url"]),
        table(["Game", "Order", "Market", "Fair value at origination (ours)", "Locked line (official)", "Locked source", "Opening value", "Opening source", "Closing value", "Closing source", "Game page", "Status"], rows))
    snap_rows = []
    for s in prices["snapshots"]:
        val = s["value"] if not isinstance(s["value"], dict) else "%+d / %+d" % (s["value"]["home_ml"], s["value"]["away_ml"])
        snap_rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(s["snapshot_key"]), esc(s["order"]), esc(s["market"]), esc(val),
            link(s["source_url"], "picks article (verbatim)"), esc(s["locked_at"]),
            esc(s["captured_at"]), esc(s["value_kind"])))
    body += """<h2>Recorded market snapshot history</h2>
<p class='lede'>Every dated locked-line reading on file, with verbatim text and source URL. These are published FanDuel lines locked 2 p.m. ET Thursday - dated snapshots, NOT opening or closing numbers. The Week 9 set is retained so the store carries history from the first week we originate.</p>
%s
<p class='note'>Snapshot rows: %d (29 games x 3 markets, Weeks 9-10). Each row carries its picks-article URL and the verbatim text it was transcribed from. Independent re-transcription of the lines (suggestion SG-09) is still open; these values were captured from market/data/raw/ (session 949f49b0).</p>""" % (
        table(["Snapshot", "Order", "Market", "Value", "Source (verbatim in JSON)", "Locked at", "Captured at", "Value kind"], snap_rows), len(snap_rows))
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
    def cell(v, fmt="%s"):
        return "<span class='blank'>blank</span>" if v is None else esc(fmt % v)
    rows = []
    for r in lines_doc["rows"]:
        sd = r["side"]["difference_fair_minus_market"]
        td = r["total"]["difference_fair_minus_market"]
        md = r["moneyline"]["difference_fair_minus_market"]
        mkt_total = r["total"]["market_total"]
        mkt_ml = (r["moneyline"]["market_ml_home"], r["moneyline"]["market_ml_away"])
        rows.append("<tr><td>%s</td><td>%s @ %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(r["key"]), esc(r["away"]), esc(r["home"]),
            esc(r["side"]["fair_favourite_text"]), cell(r["side"].get("market_spread_text")), cell(sd, "%+.3f"),
            esc(r["total"]["fair_total"]), cell(mkt_total, "%.1f"), cell(td, "%+.2f"),
            esc(r["total"]["model_status"]),
            "%s / %s" % (esc(r["moneyline"]["fair_ml_home"]), esc(r["moneyline"]["fair_ml_away"])),
            (("%s / %s" % (esc(mkt_ml[0]), esc(mkt_ml[1]))) if mkt_ml[0] is not None else "<span class='blank'>blank</span>"),
            cell(md, "%+.4f"),
            link(r["game_url"], "game"), link(r["source_url"], "schedule")))
    body = """<h1>Fair, market and difference lines</h1>
<p class='lede'>Week 10, 13 unplayed games. Three separate blocks per market: <b>fair</b> (ours), <b>market</b> (the verified locked FanDuel line from the nfl.com picks article) and <b>difference</b> = fair − market. Each is its own column.</p>
<div class='callout'><b>Order used:</b> side (1) → total (2) → moneyline (3). The moneyline is a transform of the side margin, so it is last. Every market value is the single locked line nfl.com publishes; no opening or closing line is published by any official page.</div>
%s
<p class='note'>Side difference is in home-margin points; total difference in points; moneyline difference in de-vigged home-win probability. Fair spread is written as favourite and points (home margin is positive when home is favoured). The total uses S4, which <b>fails validation</b> (LF-02). Moneylines are no-vig, rounded to whole American odds, recomputed from p_home and matched to the file. Market source: <a href='%s'>nfl.com Week 10 picks article</a>.</p>""" % (
        table(["Game", "Matchup (away @ home)", "Fair side (S1)", "Market side", "Diff side", "Fair total (S4)", "Market total", "Diff total", "Total status", "Fair ML (home / away)", "Market ML (home / away)", "Diff ML", "Game page", "Schedule"], rows), PICKS_W10)
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
<p class='lede'>The rank is decided by the <b>signal</b> columns only. The <b>staking</b> columns (units, ROI, closing-line value) are blank: no official OPEN/CLOSING series exists to settle staking against (a locked-Thursday FanDuel line is recorded but is not a close), and no pre-registered staking rule exists. A future staking run cannot lift a failing signal.</p>
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
    mkt, mkt_url, mkt_lock = load_market_prices(MARKET_PRICES)
    raw_w9, raw_w10 = load(MARKET_PRICES_W9), load(MARKET_PRICES)

    feed, feed_flags = build_results_feed(log)
    lines_doc, line_flags = build_lines(w10, mkt)
    prices, price_flags = build_prices(lines_doc, probe, mkt, mkt_lock, [raw_w9, raw_w10])
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
