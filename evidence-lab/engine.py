"""Dependency-free, fail-closed research primitives. No wagering integration.
All thresholds are research-policy choices, not facts published by the NFL.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import random
from statistics import mean


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("Expected a finite number")
    return float(value)


def probability(value):
    value = finite(value)
    if not 0 <= value <= 1:
        raise ValueError("Probability outside [0,1]")
    return value


def decimal_odds(american):
    american = finite(american)
    if abs(american) < 100:
        raise ValueError("American odds must be <= -100 or >= +100")
    return 1 + (american / 100 if american > 0 else 100 / -american)


def no_vig_two_way(odds_a, odds_b):
    """Proportional normalization; two exhaustive outcomes excluding pushes only.
    This is a modeling assumption, not a true probability guarantee.
    """
    a, b = 1 / decimal_odds(odds_a), 1 / decimal_odds(odds_b)
    return a / (a + b), b / (a + b)


def expected_return(p_win, odds, p_push=0):
    p_win, p_push = probability(p_win), probability(p_push)
    if p_win + p_push > 1:
        raise ValueError("Win and push probabilities exceed one")
    return p_win * (decimal_odds(odds) - 1) - (1 - p_win - p_push)


def home_cover_margin(predicted_home_margin, signed_home_handicap):
    """Home score minus away score plus signed home handicap.
    E.g., predicted home +7 margin, home -3 handicap -> +4 cover margin.
    A cover margin is NOT expected profit or cover probability.
    """
    return finite(predicted_home_margin) + finite(signed_home_handicap)


def settle_home_spread(home_score, away_score, handicap):
    for score in (home_score, away_score):
        if finite(score) < 0 or int(score) != score:
            raise ValueError("Scores must be nonnegative integers")
    margin = home_cover_margin(home_score - away_score, handicap)
    return "WIN" if margin > 0 else "LOSS" if margin < 0 else "PUSH"


def settle_over(home_score, away_score, total):
    for score in (home_score, away_score):
        if finite(score) < 0 or int(score) != score:
            raise ValueError("Scores must be nonnegative integers")
    total = finite(total)
    if total < 0:
        raise ValueError("Negative total")
    margin = home_score + away_score - total
    return "WIN" if margin > 0 else "LOSS" if margin < 0 else "PUSH"


def pearson(xs, ys):
    if len(xs) != len(ys):
        raise ValueError("Paired observations must have matching lengths")
    if len(xs) < 3:
        return None
    xs, ys = [finite(x) for x in xs], [finite(y) for y in ys]
    ax, ay = mean(xs), mean(ys)
    vx, vy = sum((x - ax) ** 2 for x in xs), sum((y - ay) ** 2 for y in ys)
    if not vx or not vy:
        return None
    return max(-1.0, min(1.0, sum((x - ax) * (y - ay) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)))


def joint_from_paired_outcomes(scenarios):
    """Empirical joint probability on aligned, complete binary outcomes only.
    Reject missing legs/pushes. These require explicit book-specific settlement.
    No product-of-marginals or rho-only approximation is substituted.
    """
    if len(scenarios) < 3:
        raise ValueError("At least three paired scenarios required")
    legs = len(scenarios[0])
    if legs < 2 or any(len(row) != legs for row in scenarios):
        raise ValueError("At least two consistently aligned legs required")
    if any(type(x) not in (int, bool) or x not in (0, 1) for row in scenarios for x in row):
        raise ValueError("Only settled binary outcomes are accepted")
    n = len(scenarios)
    marginals = [sum(row[j] for row in scenarios) / n for j in range(legs)]
    joint = sum(all(row) for row in scenarios) / n
    return {"n": n, "joint_probability": joint, "marginals": marginals,
            "frechet_lower": max(0.0, sum(marginals) - legs + 1), "frechet_upper": min(marginals)}


def quantile(values, p):
    p = probability(p)
    values = sorted(finite(x) for x in values)
    if not values:
        raise ValueError("No quantile for empty data")
    index = (len(values) - 1) * p
    lo = int(index)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (index - lo)


def cluster_correlation(rows, seed=3408, draws=2000):
    """rows=(x,y,week). Resample whole weeks; exploratory with just six clusters."""
    point = pearson([r[0] for r in rows], [r[1] for r in rows])
    groups = {}
    for row in rows:
        groups.setdefault(row[2], []).append(row)
    keys = sorted(groups)
    if point is None or len(keys) < 2:
        return {"r": point, "n": len(rows), "clusters": len(keys), "ci_low": None, "ci_high": None}
    rng = random.Random(seed)
    rs = []
    for _ in range(draws):
        sample = [r for _ in keys for r in groups[rng.choice(keys)]]
        r = pearson([r[0] for r in sample], [r[1] for r in sample])
        if r is not None:
            rs.append(r)
    return {"r": point, "n": len(rows), "clusters": len(keys),
            "ci_low": quantile(rs, .025) if rs else None, "ci_high": quantile(rs, .975) if rs else None}


@dataclass(frozen=True)
class Policy:
    min_holdout_bets: int = 1000
    min_seasons: int = 3
    family_alpha: float = .05
    quote_max_age_minutes: int = 15
    max_drawdown: float = .20


GATES = ("evidence", "freshness", "chronology", "sample", "skill", "dependence", "risk", "settlement")


def all_gates_pass(gates):
    """Missing gates, extra keys, CONDITIONAL, UNKNOWN, and None cannot pass."""
    return set(gates) == set(GATES) and all(type(v) is str and v == "PASS" for v in gates.values())


def assess_strategy(record, policy=Policy()):
    """Absent evidence defaults to HOLD. Metadata must come from a real pipeline.
    Do not use this record schema as a substitute for evidence review.
    """
    def number(name, default):
        value = record.get(name)
        try:
            return finite(value)
        except ValueError:
            return default
    gates = {name: "HOLD" for name in GATES}
    if record.get("official_fields_matched") is True and record.get("official_price_matched") is True:
        gates["evidence"] = "PASS"
    if record.get("quote_fresh") is True and record.get("injury_status_final") is True:
        gates["freshness"] = "PASS"
    if record.get("predictions_locked_before_kickoff") is True and record.get("no_leakage_audit") is True:
        gates["chronology"] = "PASS"
    if number("holdout_bets", -1) >= policy.min_holdout_bets and number("seasons", -1) >= policy.min_seasons:
        gates["sample"] = "PASS"
    trials = number("registered_trials", 0)
    p = number("cluster_adjusted_p", float("inf"))
    if (trials >= 1 and int(trials) == trials and 0 <= p <= policy.family_alpha / trials
            and number("simultaneous_roi_lower", -1) > 0 and record.get("calibration_pass") is True
            and record.get("season_robustness_pass") is True):
        gates["skill"] = "PASS"
    if record.get("paired_dependence_validated") is True and record.get("portfolio_exposure_checked") is True:
        gates["dependence"] = "PASS"
    drawdown = number("holdout_drawdown", float("inf"))
    if 0 <= drawdown <= policy.max_drawdown and record.get("stake_policy_locked") is True:
        gates["risk"] = "PASS"
    if record.get("official_results_matched") is True and record.get("book_rules_matched") is True:
        gates["settlement"] = "PASS"
    eligible = all_gates_pass(gates)
    return {"gates": gates, "eligible": eligible,
            "reward_points": round(10000 * number("simultaneous_roi_lower", 0), 2) if eligible else None,
            "rank": None}


def quote_is_fresh(observed_at, decision_at, max_age_minutes=15):
    """Explicit UTC-aware timestamps; future quotes and ambiguous timestamps fail."""
    try:
        a = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        b = datetime.fromisoformat(decision_at.replace("Z", "+00:00"))
        if a.tzinfo is None or b.tzinfo is None:
            return False
        age = b.astimezone(timezone.utc) - a.astimezone(timezone.utc)
        return timedelta(0) <= age <= timedelta(minutes=max_age_minutes)
    except (TypeError, ValueError, AttributeError):
        return False


def walk_forward(games, prior_games=4):
    """Illustrative point forecasts, not market lines or recommendations.
    Train on prior WEEKS only; warm-up Weeks 1–2. Shrink team means toward
    training league mean with four pseudo-team-games (predeclared assumption).
    No fitting/tuning on held-out targets. Every record includes training IDs.
    """
    if finite(prior_games) <= 0:
        raise ValueError("Positive shrinkage prior required")
    out = []
    for week in sorted({g["week"] for g in games}):
        if week < 3:
            continue
        training = [g for g in games if g["week"] < week]
        if not training:
            continue
        league = mean([score for g in training for score in (g["home_score"], g["away_score"])])
        hfa = mean(g["home_score"] - g["away_score"] for g in training)
        teams = {}
        for g in training:
            for team, pf, pa in ((g["home"], g["home_score"], g["away_score"]), (g["away"], g["away_score"], g["home_score"])):
                teams.setdefault(team, []).append((pf, pa))
        def rating(team, column):
            rows = teams.get(team, [])
            return (sum(r[column] for r in rows) + prior_games * league) / (len(rows) + prior_games)
        for game in sorted((g for g in games if g["week"] == week), key=lambda x: x["id"]):
            home = (rating(game["home"], 0) + rating(game["away"], 1)) / 2 + hfa / 2
            away = (rating(game["away"], 0) + rating(game["home"], 1)) / 2 - hfa / 2
            out.append({"id": game["id"], "week": week, "game": f"{game['away']} at {game['home']}",
                        "training_ids": sorted(g["id"] for g in training), "training_max_week": max(g["week"] for g in training),
                        "predicted_home_margin": home - away, "fair_home_handicap": away - home,
                        "predicted_total": home + away, "baseline_margin": hfa, "baseline_total": 2 * league,
                        "actual_margin": game["home_score"] - game["away_score"], "actual_total": game["home_score"] + game["away_score"],
                        "official_market_handicap": None, "cover_probability": None, "expected_return": None,
                        "source_url": game["source_url"], "status": "EXPLORATORY / NOT ELIGIBLE"})
    return out
