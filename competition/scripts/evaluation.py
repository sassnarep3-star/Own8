"""Frozen-look paper leaderboard with week-block uncertainty and no fake ranks.

Method references: NIST bootstrap/CI handbook; statsmodels Holm documentation.
The thresholds below are PROPOSED PROJECT POLICIES, not externally registered
plans or official NFL standards. They do not eliminate luck or guarantee profit.
"""
from __future__ import annotations

from collections import defaultdict
from math import ceil, floor
import random
from statistics import mean

try:
    from .core import EvidenceError, all_pass, number, timestamp
except ImportError:
    from core import EvidenceError, all_pass, number, timestamp


DEFAULT_POLICY = {
    "version": "competition-v1",
    "minimum_settled_tickets": 200,
    "minimum_distinct_weeks": 20,
    "minimum_tickets_each_fold": 100,
    "alpha": 0.05,
    "bootstrap_resamples": 5000,
    "random_seed": 2783,
    "evaluation_at_utc": "2027-03-01T00:00:00Z",
    "reward_points": [100, 60, 30],
    "cash_value": None,
    "policy_note": "Fixed research policies only. One frozen final look; extra variants/looks must join the multiplicity family. Minimum counts alone do not prove skill."
}


def quantile(values: list[float], p: float) -> float:
    if not values or not 0 <= p <= 1:
        raise EvidenceError("Nonempty quantile sample and p in [0,1] required")
    xs = sorted(values)
    index = (len(xs) - 1) * p
    lo, hi = floor(index), ceil(index)
    return xs[lo] * (hi - index) + xs[hi] * (index - lo) if hi != lo else xs[lo]


def holm_adjust(pvalues: list[float | None]) -> list[float | None]:
    """All registered tests count, including unavailable ones (displayed blank).

    Missing tests use 1 ONLY internally to reserve their place in the family,
    never as a fabricated observed p-value.
    """
    for p in pvalues:
        if p is not None and not 0 <= float(number(p)) <= 1:
            raise EvidenceError("Invalid p-value")
    vals = [1.0 if p is None else float(p) for p in pvalues]
    order = sorted(range(len(vals)), key=vals.__getitem__)
    result, previous = [None] * len(vals), 0.0
    for rank, i in enumerate(order):
        previous = min(1.0, max(previous, (len(vals) - rank) * vals[i]))
        if pvalues[i] is not None:
            result[i] = previous
    return result


def _group_rows(rows):
    groups = defaultdict(list)
    seen = set()
    for r in rows:
        ident = r.get("entry_hash")
        if not isinstance(ident, str) or ident in seen:
            raise EvidenceError("Each settled ticket needs a unique immutable entry hash")
        seen.add(ident)
        if not isinstance(r.get("week_id"), str) or not r["week_id"]:
            raise EvidenceError("NFL season-week cluster ID required; no inferred dates")
        if number(r.get("risk_units")) <= 0:
            raise EvidenceError("Positive explicit settled risk required")
        number(r.get("profit_units"))
        groups[r["week_id"]].append(r)
    return groups


def week_block_summary(rows: list[dict], family_size=1, policy=None) -> dict:
    policy = policy or DEFAULT_POLICY
    empty = {"tickets": len(rows), "week_clusters": 0, "roi": None,
             "simultaneous_ci_low": None, "simultaneous_ci_high": None,
             "p_value": None, "folds": {}, "method": "NFL season-week cluster percentile bootstrap; all tickets in a week resampled together"}
    if not rows:
        return empty
    groups = _group_rows(rows)
    risk = sum(float(number(r["risk_units"])) for r in rows)
    profit = sum(float(number(r["profit_units"])) for r in rows)
    roi = profit / risk
    folds = {}
    for fold in ("holdout_1", "holdout_2"):
        part = [r for r in rows if r.get("frozen_fold") == fold]
        folds[fold] = {"tickets": len(part), "roi": sum(float(number(r["profit_units"])) for r in part) / sum(float(number(r["risk_units"])) for r in part) if part else None}
    result = {**empty, "week_clusters": len(groups), "roi": roi, "folds": folds}
    if len(groups) < policy["minimum_distinct_weeks"]:
        return {**result, "uncertainty_status": "HOLD_INSUFFICIENT_WEEK_CLUSTERS"}
    if not isinstance(family_size, int) or family_size < 1:
        raise EvidenceError("Positive registered trial-family size required")
    blocks = [(sum(float(number(r["profit_units"])) for r in part), sum(float(number(r["risk_units"])) for r in part)) for part in groups.values()]
    # Degenerate samples must not manufacture a zero-width certainty interval.
    block_rois = [p / s for p, s in blocks]
    if max(block_rois) - min(block_rois) < 1e-12:
        return {**result, "uncertainty_status": "HOLD_DEGENERATE_BOOTSTRAP"}
    rng = random.Random(policy["random_seed"])
    draws, null_draws = [], []
    for _ in range(policy["bootstrap_resamples"]):
        sample = [rng.choice(blocks) for _ in blocks]
        s = sum(s for _, s in sample)
        draws.append(sum(p for p, _ in sample) / s)
        # Null-centered block bootstrap, one-sided H0 net ROI <= 0.
        null_draws.append(sum(p - roi * stake for p, stake in sample) / s)
    alpha_tail = policy["alpha"] / (2 * family_size)
    return {**result, "simultaneous_ci_low": quantile(draws, alpha_tail),
            "simultaneous_ci_high": quantile(draws, 1 - alpha_tail),
            "p_value": (1 + sum(v >= roi for v in null_draws)) / (1 + len(null_draws)),
            "uncertainty_status": "ESTIMATED_NOT_PROOF",
            "confidence_level_per_strategy": 1 - policy["alpha"] / family_size,
            "bootstrap_resamples": len(draws),
            "assumption": "Week clusters treated as exchangeable; cross-week dependence/regime change can invalidate coverage. No claim of luck-free skill."}


def evaluate_leaderboard(strategies: list[dict], settlements: list[dict], evaluated_at_utc: str, policy=None) -> dict:
    policy = policy or DEFAULT_POLICY
    if len({s["id"] for s in strategies}) != len(strategies):
        raise EvidenceError("Duplicate registered strategy ID")
    ids = {s["id"] for s in strategies}
    if any(r.get("strategy_id") not in ids for r in settlements):
        raise EvidenceError("Unregistered strategy results cannot be silently dropped")
    # Only a validated ledger adapter should ever supply settlements here.
    # A dictionary's flags alone do not prove official-source verification.
    if any(r.get("admission_verified") is not True or r.get("receipt_rechecked") is not True or r.get("outcome_rechecked") is not True for r in settlements):
        raise EvidenceError("Unverified / receipt-unchecked rows cannot enter a performance leaderboard")
    summaries = [week_block_summary([r for r in settlements if r["strategy_id"] == s["id"]], len(strategies), policy) for s in strategies]
    adjusted = holm_adjust([r["p_value"] for r in summaries])
    board = []
    for strategy, summary, p_adj in zip(strategies, summaries, adjusted):
        rows = [r for r in settlements if r["strategy_id"] == strategy["id"]]
        fold_ok = all(summary["folds"].get(f, {}).get("tickets", 0) >= policy["minimum_tickets_each_fold"] and (summary["folds"].get(f, {}).get("roi") or 0) > 0 for f in ("holdout_1", "holdout_2"))
        # These report fields must be COMPUTED by the independent validation
        # adapter. This module does not invent them from price snapshots.
        report = strategy.get("independent_validation_report", {})
        report_complete = report.get("report_sha256") and report.get("receipt_verified") is True
        gates = {
            "V1_integrity": {"status": "PASS" if rows and all(r.get("admission_verified") and r.get("receipt_rechecked") and r.get("outcome_rechecked") for r in rows) else "HOLD", "detail": "External prediction receipts and official final outcomes independently rechecked"},
            "V2_effective_sample": {"status": "PASS" if summary["tickets"] >= policy["minimum_settled_tickets"] and summary["week_clusters"] >= policy["minimum_distinct_weeks"] else "HOLD", "detail": "At least 200 settled tickets AND 20 season-week clusters (project screening policy)"},
            "V3_simultaneous_roi": {"status": "PASS" if summary["simultaneous_ci_low"] is not None and summary["simultaneous_ci_low"] > 0 else "HOLD", "detail": "Positive multiplicity-adjusted lower net-return bootstrap limit, exact prices after costs"},
            "V4_holm_null": {"status": "PASS" if p_adj is not None and p_adj <= policy["alpha"] else "HOLD", "detail": "One-sided null-centered block-bootstrap p, Holm across ALL registered variants"},
            "V5_independent_folds": {"status": "PASS" if fold_ok and report_complete and report.get("fold_boundaries_preregistered") is True else "HOLD", "detail": "Two frozen non-overlapping holdouts, no test-set tuning or hindsight slicing"},
            "V6_calibration_benchmark": {"status": "PASS" if report_complete and report.get("brier_improvement_ci_low") is not None and report["brier_improvement_ci_low"] > 0 else "HOLD", "detail": "Proper-score improvement against a contemporaneous normalized market baseline with uncertainty"},
            "V7_clv_support": {"status": "PASS" if report_complete and report.get("matched_clv_ci_low") is not None and report["matched_clv_ci_low"] > 0 else "HOLD", "detail": "Positive matched-contract CLV support; CLV alone is never proof of profitability"},
            "V8_exposure": {"status": "PASS" if rows and all(number(r.get("risk_units")) <= 1 for r in rows) and report_complete and report.get("portfolio_exposure_check") == "PASS" else "HOLD", "detail": "Ticket and overlapping-event portfolio caps enforced; no duplicated legs as independent samples"},
            "V9_frozen_final_look": {"status": "PASS" if timestamp(evaluated_at_utc) >= timestamp(policy["evaluation_at_utc"]) and report_complete and report.get("trial_family_frozen") is True else "HOLD", "detail": "One preregistered final decision date; no repeated significance peeking"},
        }
        eligible = all_pass(gates)
        board.append({"strategy_id": strategy["id"], "name": strategy["name"], "category": strategy["category"],
                      "rank": None, "reward_points": None, "eligible": eligible,
                      "status": "VALIDATION_PASSED" if eligible else "RESEARCH_HOLD",
                      "metrics": {**summary, "holm_adjusted_p": p_adj}, "validation_gates": gates})
    ranked = sorted([r for r in board if r["eligible"]], key=lambda r: (-r["metrics"]["simultaneous_ci_low"], r["strategy_id"]))
    # Equal lower bounds share a rank/reward; no arbitrary ID tie-break reward.
    last_score, last_rank = None, None
    for position, row in enumerate(ranked, 1):
        score = row["metrics"]["simultaneous_ci_low"]
        rank = last_rank if score == last_score else position
        row["rank"] = rank
        row["reward_points"] = policy["reward_points"][rank - 1] if rank <= len(policy["reward_points"]) else 0
        last_score, last_rank = score, rank
    return {"evaluation_at_utc": evaluated_at_utc, "policy": policy, "trial_family_size": len(strategies),
            "registration_note": "Catalog membership reserves a multiplicity-family slot; it does not establish external preregistration.",
            "eligible_strategies": len(ranked), "settled_tickets": len(settlements), "standings": board,
            "warning": "Ranks and rewards are blank until EVERY promotion gate passes. Statistical screening cannot eliminate luck or guarantee future profits."}
