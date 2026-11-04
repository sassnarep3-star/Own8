"""Reproduce a small official-only evidence ledger and exploratory analysis."""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from engine import assess_strategy, cluster_correlation, walk_forward

ROOT = Path(__file__).resolve().parent


def load_evidence():
    manifest = json.loads((ROOT / "evidence/manifest.json").read_text())
    for entry in manifest["files"]:
        raw = (ROOT / "evidence" / entry["local"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError(f"SHA-256 evidence mismatch: {entry['local']}")
        if hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() != entry["git_blob_sha1"]:
            raise ValueError("Git blob hash mismatch")
    raw_games = list(csv.DictReader((ROOT / "evidence/games.csv").open(newline="")))
    if len(raw_games) != manifest["files"][0]["rows"]:
        raise ValueError("Official row count changed")
    games = []
    seen = set()
    for line, row in enumerate(raw_games, 2):
        if row["gameId"] in seen:
            raise ValueError("Duplicate official game identifier")
        seen.add(row["gameId"])
        g = {"id": row["gameId"], "season": int(row["season"]), "week": int(row["week"]),
             "date": row["gameDate"], "home": row["homeTeamAbbr"], "away": row["visitorTeamAbbr"],
             "home_score": int(row["HomeScore"]), "away_score": int(row["VisitorScore"]),
             "source_url": manifest["files"][0]["source_url"] + f"#L{line}",
             "source_line": line, "verification": "Exact official file capture; SHA-256 + Git blob match",
             "official_fields": row}
        if g["season"] != 2017 or not 1 <= g["week"] <= 6 or min(g["home_score"], g["away_score"]) < 0:
            raise ValueError("Unexpected official sample domain")
        games.append(g)
    return manifest, games


STRATEGIES = [
    ("S1", "Shrunk team-strength spread", "Single / spread", "Expanding team points scored and allowed; shrink to training league mean. Train prior weeks only.", "Official timestamped handicap and payout; calibrated predictive residuals; multi-season held-out settlement."),
    ("S2", "Shrunk scoring total", "Single / total", "Same point model; compare home+away forecast to a genuine executable total. Report MAE separately from betting profit.", "Official timestamped total and odds; weather/injury freshness; multi-season holdout."),
    ("S3", "Calibrated win distribution", "Single / moneyline", "Research proposal: fit and calibrate a predictive score distribution using training-only residuals; account for ties.", "Verified moneyline; untouched probability-calibration holdout; no moneyline probability estimated here."),
    ("S4", "Cross-game value portfolio", "Parlay / different games", "Research proposal: joint scenarios with shared team/week/weather factors; price the offered parlay directly.", "Paired leg outcomes, official parlay payout and rules; cross-game dependence not assumed zero."),
    ("S5", "Side + game-total joint model", "Parlay / same game", "Research proposal: simulate joint scores; derive side and total leg outcomes from the same draw.", "Matched historical bet outcomes, joint calibration, official same-game payout; game-score r is not bet-leg r."),
    ("S6", "Opportunity-adjusted prop", "Player prop / single", "Research proposal: project opportunity then per-opportunity production; propagate role/injury uncertainty.", "Official player-game outcomes, pregame role data, prop line, price, timestamp, and settlement rules."),
    ("S7", "QB + receiver prop combination", "Player prop / combo", "Research proposal: joint opportunity/production model with coherent QB and receiver constraints.", "Matched player prop thresholds and outcomes; era robustness; official combo price; no correlation borrowed from team aggregates."),
]


def main():
    manifest, games = load_evidence()
    models = walk_forward(games)
    for row in models:
        if row["training_max_week"] >= row["week"] or row["id"] in row["training_ids"]:
            raise ValueError("Chronology regression")
    metrics = {"holdout_games": len(models), "holdout_weeks": sorted({r["week"] for r in models}),
               "warmup_weeks": [1, 2], "seasons": 1,
               "spread_mae": mean(abs(r["predicted_home_margin"] - r["actual_margin"]) for r in models),
               "spread_baseline_mae": mean(abs(r["baseline_margin"] - r["actual_margin"]) for r in models),
               "total_mae": mean(abs(r["predicted_total"] - r["actual_total"]) for r in models),
               "total_baseline_mae": mean(abs(r["baseline_total"] - r["actual_total"]) for r in models),
               "spread_rmse": math.sqrt(mean((r["predicted_home_margin"] - r["actual_margin"]) ** 2 for r in models)),
               "total_rmse": math.sqrt(mean((r["predicted_total"] - r["actual_total"]) ** 2 for r in models)),
               "roi": None, "clv": None, "skill_rank": None,
               "source_url": manifest["files"][0]["source_url"],
               "interpretation": "Exploratory point-forecast error only. Four held-out weeks are not a prospective betting record; no verified market quotes exist in this evidence bundle."}
    correlations = []
    for label, pairs, caveat in [
        ("Home points ↔ away points", [(g["home_score"], g["away_score"], g["week"]) for g in games], "Game scores, not bet outcomes. Do not use as prop or parlay correlation."),
        ("Home winning margin ↔ game total", [(g["home_score"] - g["away_score"], g["home_score"] + g["away_score"], g["week"]) for g in games], "Shares input variables by construction; not evidence of a tradeable side/total edge."),
    ]:
        correlations.append({"pair": label, **cluster_correlation(pairs), "status": "DERIVED / EXPLORATORY",
                             "scope": "2017 Weeks 1–6; weekly-cluster bootstrap, 2,000 draws, seed 3408; only 6 clusters, unreliable for strong inference.",
                             "caveat": caveat, "source_url": manifest["files"][0]["source_url"]})
    for pair in ("QB passing prop ↔ WR receiving prop", "Side cover ↔ total over at offered thresholds", "Cross-game parlay leg outcomes"):
        correlations.append({"pair": pair, "r": None, "n": None, "clusters": None, "ci_low": None, "ci_high": None,
                             "status": "UNVERIFIED / HOLD", "scope": "Required matched bet-outcome sample absent",
                             "caveat": "No estimate substituted; dependence gate remains HOLD.", "source_url": manifest["files"][1]["source_url"]})
    strategies = []
    for sid, name, category, hypothesis, missing in STRATEGIES:
        strategies.append({"id": sid, "name": name, "category": category, "hypothesis": hypothesis,
                           "missing": missing, **assess_strategy({}), "roi": None, "clv": None, "skill_p": None,
                           "status": "HOLD / RESEARCH ONLY", "source_url": manifest["files"][1]["source_url"]})
    output = {"as_of": "2026-11-04", "scope": manifest["scope"], "official_games": len(games),
              "manifest": manifest, "games": games, "models": models, "metrics": metrics,
              "correlations": correlations, "strategies": strategies, "eligible_strategies": 0,
              "verification_scope": "All displayed historical fact cells map directly to the hash-matched official games file. Derived estimates are labeled, not official facts. Other repository datasets were not re-verified against official sources in this session."}
    (ROOT / "results.json").write_text(json.dumps(output, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps(metrics, indent=2))
    print(f"Official games: {len(games)}; eligible strategies: 0")


if __name__ == "__main__":
    main()
