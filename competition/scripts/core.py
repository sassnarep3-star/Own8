"""Pure paper-competition mathematics. No network, default odds, or real bets.

Official background: DraftKings' reading-odds/football guides; SciPy pearsonr.
Project policies and synthetic test fixtures are not official NFL facts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite, sqrt
from statistics import mean
from urllib.parse import urlsplit


class EvidenceError(ValueError):
    """Input cannot be established without guessing."""


NFL_HOSTS = frozenset({"www.nfl.com", "nfl.com", "nextgenstats.nfl.com"})
OPERATOR_HOSTS = frozenset({"sportsbook.draftkings.com"})


def number(value) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise EvidenceError("A finite numeric value is required, not null/bool")
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise EvidenceError("Not a number") from None
    if not out.is_finite():
        raise EvidenceError("Non-finite numbers are forbidden")
    return out


def probability(value) -> float:
    out = number(value)
    if not 0 <= out <= 1:
        raise EvidenceError("Probability must be in [0, 1]")
    return float(out)


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise EvidenceError("A timezone-aware timestamp is required")
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise EvidenceError("Invalid timestamp") from None
    if out.tzinfo is None or out.utcoffset() is None:
        raise EvidenceError("Timezone must not be guessed")
    return out.astimezone(timezone.utc)


def official_url(url: str, authority: str = "league") -> bool:
    try:
        u = urlsplit(url)
        hosts = NFL_HOSTS if authority == "league" else OPERATOR_HOSTS
        return u.scheme == "https" and u.hostname in hosts and not u.username and not u.password and u.port in (None, 443)
    except (TypeError, ValueError):
        return False


def american_to_decimal(odds) -> Decimal:
    a = number(odds)
    if a != a.to_integral_value() or abs(a) < 100:
        raise EvidenceError("American odds must be an integer >= +100 or <= -100")
    return Decimal(1) + (a / 100 if a > 0 else Decimal(100) / -a)


def decimal_odds(value) -> Decimal:
    d = number(value)
    if d <= 1:
        raise EvidenceError("Decimal odds must exceed 1")
    return d


def implied_probability(odds) -> float:
    return float(1 / american_to_decimal(odds))


def two_way_normalization(odds_a, odds_b) -> dict:
    """Proportional normalization is a METHOD CHOICE, not a true probability.

    In a two-way NFL moneyline market these shares are conditional on a
    non-tie settlement; this routine does not estimate tie or push probability.
    """
    a, b = implied_probability(odds_a), implied_probability(odds_b)
    return {"a_share": a / (a + b), "b_share": b / (a + b),
            "overround": a + b - 1,
            "method": "proportional two-way normalization; not a model forecast"}


def expected_roi(p_win, p_push, odds_decimal) -> float:
    w, p = probability(p_win), probability(p_push)
    if w + p > 1 + 1e-12:
        raise EvidenceError("Win + push probability exceeds 1")
    return w * float(decimal_odds(odds_decimal)) + p - 1


def fair_decimal(p_win, p_push) -> float:
    w, p = probability(p_win), probability(p_push)
    if w <= 0 or w + p > 1 + 1e-12 or p >= 1:
        raise EvidenceError("Fair odds are undefined for these probabilities")
    return (1 - p) / w


def brier_score(forecast: list, outcome_index: int) -> float:
    ps = [probability(v) for v in forecast]
    if not ps or abs(sum(ps) - 1) > 1e-9 or isinstance(outcome_index, bool) or not isinstance(outcome_index, int) or not 0 <= outcome_index < len(ps):
        raise EvidenceError("Use normalized probabilities and a valid outcome index")
    return sum((p - (i == outcome_index)) ** 2 for i, p in enumerate(ps))


def joint_binary_probability(p_a, p_b, rho) -> float:
    """Two BINARY threshold outcomes only. Never use yards correlation here.

    The full joint distribution is still needed for three or more legs.
    Correlation must describe the same indicators, thresholds and population.
    """
    a, b = probability(p_a), probability(p_b)
    r = float(number(rho))
    if not -1 <= r <= 1 or a in (0, 1) or b in (0, 1):
        raise EvidenceError("Nondegenerate marginals and rho in [-1, 1] required")
    joint = a * b + r * sqrt(a * (1 - a) * b * (1 - b))
    lo, hi = max(0, a + b - 1), min(a, b)
    if joint < lo - 1e-12 or joint > hi + 1e-12:
        raise EvidenceError("Pair violates the Frechet probability bounds")
    return joint


def paired_correlation(x_by_id: dict, y_by_id: dict) -> dict:
    """Join keys BEFORE deleting missing values; never zip separately filtered arrays."""
    pairs = []
    for key in sorted(x_by_id.keys() & y_by_id.keys()):
        x, y = x_by_id[key], y_by_id[key]
        if x is None or y is None:
            continue
        pairs.append((float(number(x)), float(number(y))))
    n = len(pairs)
    if n < 2:
        return {"n": n, "r": None, "status": "HOLD_INSUFFICIENT_PAIRS"}
    xs, ys = zip(*pairs)
    mx, my = mean(xs), mean(ys)
    dx, dy = sum((x - mx) ** 2 for x in xs), sum((y - my) ** 2 for y in ys)
    if dx == 0 or dy == 0:
        return {"n": n, "r": None, "status": "HOLD_CONSTANT_INPUT"}
    r = sum((x - mx) * (y - my) for x, y in pairs) / sqrt(dx * dy)
    return {"n": n, "r": max(-1.0, min(1.0, r)), "status": "DESCRIPTIVE_ONLY"}


def all_pass(gates: dict) -> bool:
    return bool(gates) and all(isinstance(g, dict) and g.get("status") == "PASS" for g in gates.values())


def _verified_result(result: dict, fields: set) -> bool:
    return (result.get("verification") == "confirmed_transcription"
            and official_url(result.get("source_url"))
            and fields.issubset(set(result.get("confirmed_fields", []))))


def grade_leg(leg: dict, result: dict | None) -> dict:
    """Grade an outcome, not a bet payout. Unknown never becomes a loss or zero."""
    def out(status, reason):
        return {"status": status, "reason": reason, "source_url": (result or {}).get("source_url")}
    if result is None:
        return out("PENDING", "No confirmed official outcome")
    if leg.get("event_id") != result.get("event_id"):
        return out("HOLD", "Event identity mismatch")
    if result.get("status") != "Final":
        return out("PENDING", "Official event is not final; no guessed cancellation/void")
    market = leg.get("market")
    if market == "player_prop":
        key = f"player:{leg.get('player_id')}:{leg.get('stat')}"
        if not _verified_result(result, {key, "participation", "status"}):
            return out("HOLD", "Player statistic or participation unverified")
        participation = result.get("participation", {}).get(leg.get("player_id"))
        if participation == "did_not_play":
            return out("HOLD", "DNP requires verified market-specific operator rules")
        if participation != "played":
            return out("HOLD", "Participation unknown")
        value = result.get("player_stats", {}).get(key)
        if value is None:
            return out("HOLD", "Player statistic is missing, not zero")
        delta = number(value) - number(leg.get("line"))
    else:
        if not _verified_result(result, {"home_score", "away_score", "status", "home", "away"}):
            return out("HOLD", "Final game-score fields are not verified")
        hs, aws = number(result.get("home_score")), number(result.get("away_score"))
        if hs < 0 or aws < 0 or hs != hs.to_integral_value() or aws != aws.to_integral_value():
            raise EvidenceError("Official scores must be nonnegative integers")
        if market in {"spread", "moneyline"}:
            team = leg.get("team")
            if team not in {result.get("home"), result.get("away")}:
                return out("HOLD", "Selected team is not a participant")
            margin = (hs - aws) if team == result["home"] else (aws - hs)
            if market == "moneyline":
                if margin == 0:
                    return out("HOLD", "Tie requires verified two-/three-way market rules")
                return out("WIN" if margin > 0 else "LOSS", "Official final result")
            delta = margin + number(leg.get("line"))  # signed selected-team handicap
        elif market == "total":
            delta = hs + aws - number(leg.get("line"))
        else:
            return out("HOLD", "Unsupported market; no fallback settlement")
    if market in {"total", "player_prop"}:
        side = leg.get("side")
        if side not in {"over", "under"}:
            return out("HOLD", "Over/under side required")
        if side == "under":
            delta = -delta
    return out("PUSH" if delta == 0 else ("WIN" if delta > 0 else "LOSS"), "Confirmed threshold comparison")


def settle_ticket(ticket: dict, leg_grades: list[dict], rule_evidence: dict | None = None) -> dict:
    """Use exact quoted combined odds; never infer an SGP payout by multiplying.

    Refunds/repricing on push, void, DNP or ties are HELD unless a reviewed
    operator settlement rule AND exact revised subset quote are supplied.
    That adapter is deliberately absent from the production evidence package.
    """
    risk = number(ticket.get("stake_units"))
    if risk <= 0:
        raise EvidenceError("Positive explicit paper stake required")
    if len(leg_grades) != len(ticket.get("legs", [])) or not leg_grades:
        raise EvidenceError("Exactly one grade per leg is required")
    states = [g.get("status") for g in leg_grades]
    base = {"profit_units": None, "returned_units": None, "risk_units": float(risk), "leg_states": states}
    if any(s in {"HOLD", "PUSH", "VOID"} for s in states):
        return {**base, "status": "HOLD_RULES", "reason": "Unknown/repriced/refunded settlement is not inferred"}
    if any(s == "PENDING" for s in states):
        return {**base, "status": "PENDING", "reason": "Wait for all final verified outcomes"}
    if any(s not in {"WIN", "LOSS"} for s in states):
        return {**base, "status": "HOLD_RULES", "reason": "Unrecognized leg state"}
    rule_evidence = rule_evidence or {}
    if rule_evidence.get("verification") != "reviewed_market_rules" or not official_url(rule_evidence.get("source_url"), "operator"):
        return {**base, "status": "HOLD_RULES", "reason": "Reviewed operator market-rule evidence required; ticket flags cannot self-certify"}
    # Exact combined quote even for different games. No default -110.
    try:
        d = decimal_odds(ticket.get("quoted_decimal_odds"))
    except EvidenceError:
        return {**base, "status": "HOLD_PRICE", "reason": "No verified exact combined price"}
    returned = Decimal(0) if "LOSS" in states else risk * d
    return {**base, "status": "SETTLED", "profit_units": float(returned - risk),
            "returned_units": float(returned), "reason": "All leg states known; exact locked price"}


def point_clv(market, side, entry_line, closing_line):
    """Line-only CLV; valid only for same event, period and selection contract."""
    entry, close = number(entry_line), number(closing_line)
    if market == "spread":
        return float(entry - close)  # +3 captured before +2 is +1 point of CLV
    if market in {"total", "player_prop"} and side in {"over", "under"}:
        return float(close - entry if side == "over" else entry - close)
    raise EvidenceError("No comparable point CLV for this contract")


def baseline_lines(away: dict, home: dict) -> dict:
    """Untrained B0 benchmark ONLY. No HFA, injury adjustment, or win probability.

    Explicit project equation, NOT an official value or a validated fair price.
    """
    def rates(t):
        gp = sum(int(t[k]) for k in ("W", "L", "T"))
        if gp <= 0:
            raise EvidenceError("Cannot impute scoring rates without games")
        return float(number(t["PF"])) / gp, float(number(t["PA"])) / gp
    apf, apa = rates(away)
    hpf, hpa = rates(home)
    away_points, home_points = (apf + hpa) / 2, (hpf + apa) / 2
    return {"home_margin": home_points - away_points,
            "home_handicap": away_points - home_points,
            "total": away_points + home_points, "home_win_probability": None,
            "status": "UNVALIDATED_REFERENCE_BASELINE", "candidate": False,
            "edge": None, "uncertainty": None}
