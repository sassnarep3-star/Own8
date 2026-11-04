"""Append-only paper prediction receipts, admission gates and hash-chain integrity.

A hash is NOT proof of publication time. Admission re-reads a GitHub comment
from GitHub's API, checks its server timestamps and exact body hash, and locks
before the NFL kickoff. Offline inspection only checks local integrity.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    from .core import EvidenceError, all_pass, american_to_decimal, decimal_odds, number, official_url, probability, timestamp
except ImportError:
    from core import EvidenceError, all_pass, american_to_decimal, decimal_odds, number, official_url, probability, timestamp


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def receipt_body(payload_hash: str) -> str:
    return f"Own8 paper prediction receipt\nsha256:{payload_hash}\nNo real-money wager."


class GithubReceipts:
    """Receipt IDs are returned by GitHub, never manufactured locally."""
    def __init__(self, repo="sassnarep3-star/Own8", issue_number=16):
        self.repo, self.issue_number = repo, issue_number

    @staticmethod
    def _api(*args):
        p = subprocess.run(["gh", "api", *args], check=True, text=True, capture_output=True, timeout=30)
        return json.loads(p.stdout)

    def create(self, payload_hash):
        obj = self._api(f"repos/{self.repo}/issues/{self.issue_number}/comments", "-f", f"body={receipt_body(payload_hash)}")
        return {"comment_id": obj["id"], "url": obj["html_url"]}

    def load(self, reference):
        ident = reference.get("comment_id")
        if isinstance(ident, bool) or not isinstance(ident, int) or ident <= 0:
            raise EvidenceError("Receipt ID must come from an actual GitHub API response")
        obj = self._api(f"repos/{self.repo}/issues/comments/{ident}")
        prefix = f"https://github.com/{self.repo}/"
        if not obj.get("html_url", "").startswith(prefix) or obj["html_url"] != reference.get("url"):
            raise EvidenceError("Wrong receipt repository or URL")
        return {"body": obj["body"], "created_at": obj["created_at"], "updated_at": obj["updated_at"],
                "url": obj["html_url"], "comment_id": obj["id"]}


@dataclass
class EvidenceBook:
    """Loaded from reviewed evidence snapshots, NOT values inside an entry.

    The caller is the trusted evidence adapter; arbitrary uploaded dictionaries
    are not an official-source verification service. Production rules and joint
    reports are intentionally empty until independent evidence is acquired.
    """
    fixtures: dict = field(default_factory=dict)
    quotes: dict = field(default_factory=dict)
    clearance: dict = field(default_factory=dict)
    strategies: dict = field(default_factory=dict)
    joint_reports: dict = field(default_factory=dict)
    rulebooks: dict = field(default_factory=dict)
    receipt_provider: object = None
    quote_ttl_seconds: int = 900  # project policy; not an official recommendation
    single_risk_cap: float = 1.0
    open_risk_cap: float = 10.0


def validate_payload(payload):
    allowed = {"entry_id", "strategy_id", "strategy_version", "training_cutoff_utc", "legs",
               "stake_units", "combined_quote_id", "joint_report_id", "rulebook_id", "model_probability"}
    required = {"entry_id", "strategy_id", "strategy_version", "training_cutoff_utc", "legs", "stake_units", "rulebook_id"}
    if not isinstance(payload, dict) or not required <= payload.keys() or payload.keys() - allowed:
        raise EvidenceError("Missing/unknown prediction fields; self-certified gate flags are forbidden")
    for key in ("entry_id", "strategy_id", "strategy_version", "rulebook_id"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            raise EvidenceError(f"Nonempty {key} required")
    timestamp(payload["training_cutoff_utc"])
    number(payload["stake_units"])
    for key in ("combined_quote_id", "joint_report_id"):
        if key in payload and (not isinstance(payload[key], str) or not payload[key].strip()):
            raise EvidenceError(f"Nonempty {key} reference required when provided")
    if "model_probability" in payload:
        probability(payload["model_probability"])
    legs = payload["legs"]
    if not isinstance(legs, list) or not 1 <= len(legs) <= 2:
        raise EvidenceError("This version supports one or two legs only; no three-leg inference")
    seen = set()
    for leg in legs:
        if not isinstance(leg, dict) or not {"event_id", "market", "quote_id"} <= leg.keys():
            raise EvidenceError("Each leg needs an explicit event, market and quote reference")
        for key in ("event_id", "quote_id", "market"):
            if not isinstance(leg[key], str) or not leg[key].strip():
                raise EvidenceError(f"Nonempty leg {key} required")
        if leg["market"] not in {"moneyline", "spread", "total", "player_prop"}:
            raise EvidenceError("Unsupported market")
        if leg.keys() - {"event_id", "market", "quote_id", "team", "side", "line", "player_id", "stat"}:
            raise EvidenceError("Unknown leg field")
        for key in ("team", "player_id", "stat"):
            if key in leg and (not isinstance(leg[key], str) or not leg[key].strip()):
                raise EvidenceError(f"Nonempty string leg {key} required")
        if leg["market"] in {"moneyline", "spread"} and (not isinstance(leg.get("team"), str) or not leg["team"].strip()):
            raise EvidenceError("Selected team required")
        if leg["market"] in {"total", "player_prop"} and leg.get("side") not in {"over", "under"}:
            raise EvidenceError("Over/under side required")
        if leg["market"] != "moneyline":
            number(leg.get("line"))
        if leg["market"] == "player_prop" and (not leg.get("player_id") or not leg.get("stat")):
            raise EvidenceError("Explicit player ID/stat required; a team rate is not a player projection")
        contract = (leg["event_id"], leg["market"], leg.get("team"), leg.get("side"), str(leg.get("line")), leg.get("player_id"), leg.get("stat"))
        if contract in seen:
            raise EvidenceError("Duplicate parlay leg")
        seen.add(contract)


def admission(payload: dict, receipt_reference: dict | None, book: EvidenceBook, open_risk=0) -> dict:
    validate_payload(payload)
    gates = {}
    def gate(key, ok, detail):
        gates[key] = {"status": "PASS" if ok else "HOLD", "detail": detail}
    legs, fixtures = payload["legs"], [book.fixtures.get(l["event_id"], {}) for l in payload["legs"]]
    fixture_ok = all(f.get("verification") == "confirmed_transcription" and official_url(f.get("source_url")) and f.get("kickoff_utc") for f in fixtures)
    gate("G1_fixture_evidence", fixture_ok, "Exact official event IDs and timezone-aware NFL kickoff required")
    receipt = None
    try:
        if book.receipt_provider is None or receipt_reference is None:
            raise EvidenceError("External receipt absent")
        receipt = book.receipt_provider.load(receipt_reference)
        if receipt.get("body") != receipt_body(digest(payload)) or receipt.get("created_at") != receipt.get("updated_at"):
            raise EvidenceError("Receipt edited or payload hash does not match")
        lock = timestamp(receipt["created_at"])
        lock_ok = fixture_ok and timestamp(payload["training_cutoff_utc"]) < lock and all(lock < timestamp(f["kickoff_utc"]) for f in fixtures)
        # Future-dated receipt responses are not a valid server receipt.
        lock_ok = lock_ok and lock <= datetime.now(timezone.utc)
    except (EvidenceError, KeyError, ValueError, subprocess.SubprocessError, OSError):
        lock_ok = False
        receipt = None
    gate("G2_external_pregame_lock", lock_ok, "Re-read unedited GitHub server receipt; training cutoff < publication < EVERY kickoff")
    quote_ok, exact_prices = bool(lock_ok), []
    for leg in legs:
        q = book.quotes.get(leg["quote_id"], {})
        fields = ["event_id", "market"] + [k for k in ("team", "side", "line", "player_id", "stat") if k in leg]
        same = all(q.get(k) == leg.get(k) for k in fields)
        try:
            price = american_to_decimal(q.get("american_odds"))
            updated = timestamp(q.get("quote_updated_at_utc"))
            observed = timestamp(q.get("observed_at_utc"))
            fresh = lock_ok and updated <= observed <= lock and (lock - updated).total_seconds() <= book.quote_ttl_seconds
        except EvidenceError:
            price, fresh = None, False
        quote_ok = quote_ok and same and q.get("verification") == "confirmed_transcription" and official_url(q.get("source_url"), "operator") and fresh
        exact_prices.append(price)
    if len(legs) == 2:
        cq = book.quotes.get(payload.get("combined_quote_id"), {})
        try:
            decimal_odds(cq.get("decimal_odds"))
            same_contract = cq.get("leg_quote_ids") == sorted(l["quote_id"] for l in legs)
            updated = timestamp(cq.get("quote_updated_at_utc"))
            observed = timestamp(cq.get("observed_at_utc"))
            fresh = lock_ok and updated <= observed <= lock and (lock - updated).total_seconds() <= book.quote_ttl_seconds
            quote_ok = quote_ok and same_contract and fresh and cq.get("verification") == "confirmed_transcription" and official_url(cq.get("source_url"), "operator")
        except EvidenceError:
            quote_ok = False
    gate("G3_exact_primary_price", bool(quote_ok), "No default odds; verified source update/observation times; exact combined quote for a parlay")
    clearance_ok = bool(lock_ok)
    for leg in legs:
        c = book.clearance.get(leg["event_id"], {})
        try:
            reported = timestamp(c.get("reported_at_utc"))
            fresh = lock_ok and reported <= lock and (lock - reported).total_seconds() <= 86400
        except EvidenceError:
            fresh = False
        clearance_ok = clearance_ok and c.get("status") == "confirmed_final_report" and official_url(c.get("source_url")) and fresh
    gate("G4_participation_rules", bool(clearance_ok), "Dated final participation evidence, at most 24 hours old at publication; practice / No Injuries Reported is not clearance")
    if len(legs) == 1:
        joint_ok = True
        detail = "Single leg: joint model not applicable; explicit PASS, not a skipped gate"
    else:
        report = book.joint_reports.get(payload.get("joint_report_id"), {})
        expected_ids = sorted(l["quote_id"] for l in legs)
        try:
            p = number(report.get("joint_win_probability"))
            joint_ok = (report.get("target_leg_quote_ids") == expected_ids
                        and report.get("kind") == "matched_binary_outcomes"
                        and report.get("independently_validated") is True
                        and report.get("distinct_week_clusters", 0) >= 20
                        and report.get("paired_observations", 0) >= 200
                        and 0 < p < 1 and lock_ok
                        and timestamp(report.get("training_cutoff_utc")) < lock)
        except EvidenceError:
            joint_ok = False
        detail = "Two actual threshold outcomes, matched sample and calibrated joint probability; different games do not imply independence"
    gate("G5_joint_distribution", joint_ok, detail)
    strategy = book.strategies.get(payload["strategy_id"], {})
    try:
        prereg_ok = (lock_ok and strategy.get("version_hash") == payload["strategy_version"]
                      and strategy.get("receipt_verified") is True
                      and timestamp(strategy.get("registered_at_utc")) < lock)
    except EvidenceError:
        prereg_ok = False
    gate("G6_preregistered_version", prereg_ok, "Frozen version, feature cutoff and trial family must predate the prediction")
    risk = number(payload["stake_units"])
    gate("G7_paper_exposure", 0 < risk <= number(book.single_risk_cap) and number(open_risk) >= 0 and number(open_risk) + risk <= number(book.open_risk_cap), "Fixed explicit research units, <=1 per ticket and <=10 open units (project policy)")
    rule = book.rulebooks.get(payload["rulebook_id"], {})
    rule_ok = rule.get("verification") == "reviewed_market_rules" and official_url(rule.get("source_url"), "operator") and rule.get("applies_to") == sorted(set(l["market"] for l in legs))
    gate("G8_operator_rulebook", rule_ok, "Reviewed period, overtime, tie, void, DNP and repricing rules; introductory guides are insufficient")
    return {"eligible_for_paper_ticket": all_pass(gates), "gates": gates,
            "payload_sha256": digest(payload), "receipt": receipt}


def read_chain(path: Path, expected_head=None, expected_count=None) -> list:
    records, previous = [], None
    if not path.exists():
        raise EvidenceError("Prediction ledger is missing; not silently initialized")
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            raise EvidenceError("Blank/truncated ledger record")
        row = json.loads(line)
        claimed = row.pop("sha256", None)
        if row.get("sequence") != line_no or row.get("previous_sha256") != previous or claimed != digest(row):
            raise EvidenceError(f"Ledger integrity failure at line {line_no}")
        row["sha256"] = claimed
        records.append(row)
        previous = claimed
    if expected_count is not None and len(records) != expected_count:
        raise EvidenceError("Ledger tail removed or checkpoint count mismatched")
    if expected_head is not None and previous != expected_head:
        raise EvidenceError("Ledger checkpoint head mismatched")
    ids = [r["payload"].get("entry_id") for r in records if r.get("kind") == "prediction"]
    if len(ids) != len(set(ids)):
        raise EvidenceError("Duplicate prediction entry ID")
    return records


def _append_under_lock(path, records, kind, payload, receipt=None):
    if kind not in {"prediction", "settlement_revision"}:
        raise EvidenceError("Unknown record kind")
    if kind == "prediction" and any(r.get("kind") == "prediction" and r["payload"].get("entry_id") == payload.get("entry_id") for r in records):
        raise EvidenceError("Entry IDs cannot be replaced")
    row = {"sequence": len(records) + 1, "previous_sha256": records[-1]["sha256"] if records else None,
           "kind": kind, "payload": payload, "receipt": receipt}
    row["sha256"] = digest(row)
    with path.open("a") as out:
        out.write(canonical(row) + "\n")
        out.flush()
        os.fsync(out.fileno())
    return row


def append_record(path: Path, kind: str, payload: dict, receipt=None) -> dict:
    """Low-level append for reviewed adapters and synthetic tests, not admission.

    Production publishers must use publish_prediction instead. Calling this
    helper manually does not make a prediction competitive or verified.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX)
        return _append_under_lock(path, read_chain(path), kind, payload, receipt)


def open_risk_from_chain(records):
    latest = {}
    for row in records:
        if row["kind"] == "settlement_revision":
            latest[row["payload"]["prediction_sha256"]] = row["payload"]["settlement"]["status"]
    return sum(number(row["payload"]["stake_units"]) for row in records
               if row["kind"] == "prediction" and latest.get(row["sha256"]) != "SETTLED")


def publish_prediction(path: Path, payload: dict, book: EvidenceBook) -> dict:
    """Create a server receipt, then atomically recheck ledger exposure/admission.

    The API receipt is deliberately created before admission; a failed entry
    may leave a rejected receipt, never a qualified prediction or reward.
    Concurrent publishers cannot both spend the same open-risk allowance.
    """
    validate_payload(payload)
    if book.receipt_provider is None:
        raise EvidenceError("No trusted external publication adapter")
    reference = book.receipt_provider.create(digest(payload))
    with path.with_suffix(".lock").open("a") as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX)
        records = read_chain(path)
        result = admission(payload, reference, book, open_risk_from_chain(records))
        if not result["eligible_for_paper_ticket"]:
            return {"status": "HELD", "admission": result}
        record = _append_under_lock(path, records, "prediction", payload, reference)
    return {"status": "LOCKED_PAPER_ONLY", "record": record, "admission": result}
