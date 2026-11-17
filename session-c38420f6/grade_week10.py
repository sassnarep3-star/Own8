#!/usr/bin/env python3
"""Create a transparent diagnostic of the frozen W10 forecast against observed NFL finals.

This is not a validation-gate implementation or leaderboard result. It reads pre-kickoff
forecast artifacts and the separately timestamped official-score addendum, leaves the one
unresolved game out, and emits reproducible point errors plus source URLs.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "week10-diagnostic.json"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def mean_abs(rows, key):
    vals = [abs(r[key]) for r in rows]
    return round(sum(vals) / len(vals), 4) if vals else None


def main():
    predictions = load("origination/results/w10-lines.json")
    observed = load("ledger/data/week10-results-addendum.json")
    market_doc = load("ledger/data/lines-columns.json")
    pred = {(g["away"], g["home"]): g for g in predictions["games"]}
    market = {(g["away"], g["home"]): g for g in market_doc["rows"]}
    rows = []
    for result in observed["rows"]:
        key = (result["away"], result["home"])
        p = pred[key]
        m = market[key]
        actual_margin = result["home_score"] - result["away_score"]
        actual_total = result["home_score"] + result["away_score"]
        home_win = result["home_score"] > result["away_score"]
        outcome = 1.0 if home_win else 0.0
        s = m["side"]
        t = m["total"]
        ml = m["moneyline"]
        market_home_margin = -s["market_spread"] if s["market_spread"] is not None else None
        rows.append({
            "key": result["key"], "away": result["away"], "home": result["home"],
            "away_score": result["away_score"], "home_score": result["home_score"],
            "actual_home_margin": actual_margin, "actual_total": actual_total,
            "actual_home_win": home_win,
            "forecasts": {
                "S1_home_margin": p["fair_home_margin_S1"],
                "S2_home_margin": p["fair_home_margin_S2"],
                "S3_home_margin": p["fair_home_margin_S3"],
                "S4_total": p["fair_total_S4"],
                "S5_total": p["fair_total_S5"],
                "S6_p_home": p["p_home_S6"],
            },
            "market": {
                "locked_home_margin": market_home_margin,
                "locked_total": t["market_total"],
                "devigged_p_home": ml["market_p_home_devig"],
                "source_url": m["market_source_url"],
            },
            "errors": {
                "S1_abs_margin_error": abs(p["fair_home_margin_S1"] - actual_margin),
                "S2_abs_margin_error": abs(p["fair_home_margin_S2"] - actual_margin),
                "S3_abs_margin_error": abs(p["fair_home_margin_S3"] - actual_margin),
                "market_abs_margin_error": abs(market_home_margin - actual_margin),
                "S4_abs_total_error": abs(p["fair_total_S4"] - actual_total),
                "S5_abs_total_error": abs(p["fair_total_S5"] - actual_total),
                "market_abs_total_error": abs(t["market_total"] - actual_total),
                "S6_brier": (p["p_home_S6"] - outcome) ** 2,
                "market_brier": (ml["market_p_home_devig"] - outcome) ** 2,
            },
            "official_scores_url": result["source_url"],
            "official_game_center_url": result["game_url"],
            "forecast_artifact": "origination/results/w10-lines.json (originated_at %s)" % predictions["originated_at"],
            "forecast_schedule_url": p["source_url"],
        })

    metric_keys = ["S1_abs_margin_error", "S2_abs_margin_error", "S3_abs_margin_error",
                   "market_abs_margin_error", "S4_abs_total_error", "S5_abs_total_error",
                   "market_abs_total_error", "S6_brier", "market_brier"]
    metrics = {}
    for key in metric_keys:
        vals = [r["errors"][key] for r in rows]
        metrics[key] = round(sum(vals) / len(vals), 6) if vals else None
    doc = {
        "generated_at_utc": observed["captured_at_utc"],
        "purpose": "Exploratory postgame diagnostic for Week 10 forecasts originated before kickoff. It is not a preregistered leaderboard result and does not clear any validation gate.",
        "n_final_games": len(rows),
        "n_scheduled_forecasts": len(predictions["games"]),
        "n_unresolved_games_excluded": len(observed.get("unresolved", [])),
        "forecast_originated_at": predictions["originated_at"],
        "metrics": metrics,
        "uncertainty": "No confidence intervals, Holm adjustment, or cluster lower bound are computed in this exploratory diagnostic. With only 12 completed games and one unresolved result, do not rank, reward, or infer skill from these point estimates.",
        "limitations": [
            "The fair numbers are the original frozen forecast values, not re-fit after results.",
            "The 12 results are official NFL finals, but the remaining Week 10 LAC at BAL row had no official Final label or final score at the capture time and is excluded.",
            "Vig-free market probabilities are arithmetic transformations of the published FanDuel lines in the official NFL picks article; the article is a locked-Thursday snapshot, not closing odds.",
            "No strategy stakes, bet selections, void/push rules, or settlement records are applied; ROI and CLV remain blank.",
            "The raw NFL HTTP response bodies were not retained by the fetch mechanism, so this is a timestamped structured transcription, not a hash-verified immutable raw capture.",
            "The recorded UTC timestamp is the local UTC time recorded immediately after retrieval, not an NFL server timestamp."
        ],
        "sources": {
            "scores_page": observed["scores_page_url"],
            "price_article": "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season",
            "official_standings": "https://www.nfl.com/standings/league/2026/REG",
        },
        "rows": rows,
        "unresolved": observed.get("unresolved", []),
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote %s (%d final games; %d unresolved)" % (OUT, len(rows), len(doc["unresolved"])))
    for key, val in metrics.items():
        print("%s = %s" % (key, val))


if __name__ == "__main__":
    main()
