"""Idempotent append-only grading and official-score correction revisions.

No current production prediction can be settled: the real ledger is empty,
price-update/participation/rulebook gates are held. These APIs are exercised
only with clearly synthetic fixtures in the separate tests directory.
"""
from pathlib import Path
import fcntl

try:
    from .core import EvidenceError, american_to_decimal, grade_leg, settle_ticket, timestamp
    from .ledger import EvidenceBook, admission, _append_under_lock, digest, read_chain
except ImportError:
    from core import EvidenceError, american_to_decimal, grade_leg, settle_ticket, timestamp
    from ledger import EvidenceBook, admission, _append_under_lock, digest, read_chain


def settle_prediction(ledger_path: Path, prediction_hash: str, official_outcomes: dict,
                      book: EvidenceBook, checked_at_utc: str) -> dict:
    with ledger_path.with_suffix(".lock").open("a") as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX)
        return _settle_under_lock(ledger_path, prediction_hash, official_outcomes, book, checked_at_utc)


def _settle_under_lock(ledger_path, prediction_hash, official_outcomes, book, checked_at_utc):
    records = read_chain(ledger_path)
    matches = [r for r in records if r["sha256"] == prediction_hash and r["kind"] == "prediction"]
    if len(matches) != 1:
        raise EvidenceError("Unknown/ambiguous immutable prediction hash")
    prediction = matches[0]
    payload = prediction["payload"]
    # Re-read the external receipt, original price/participation evidence and
    # all original admission gates. It is not enough to remember a PASS flag.
    check = admission(payload, prediction["receipt"], book)
    if not check["eligible_for_paper_ticket"]:
        return {"status": "HOLD_ADMISSION", "admission": check}
    timestamp(checked_at_utc)
    outcomes, grades = {}, []
    for leg in payload["legs"]:
        result = official_outcomes.get(leg["event_id"])
        if result is not None:
            outcomes[leg["event_id"]] = result
        grades.append(grade_leg(leg, result))
    if len(payload["legs"]) == 1:
        quote = book.quotes[payload["legs"][0]["quote_id"]]
        price = str(american_to_decimal(quote["american_odds"]))
    else:
        price = book.quotes.get(payload.get("combined_quote_id"), {}).get("decimal_odds")
    settled = settle_ticket({"legs": payload["legs"], "stake_units": payload["stake_units"],
                             "quoted_decimal_odds": price}, grades, book.rulebooks.get(payload["rulebook_id"]))
    if settled["status"] != "SETTLED":
        return {"status": settled["status"], "settlement": settled}
    evidence_hash = digest(outcomes)
    prior = [r for r in records if r["kind"] == "settlement_revision" and r["payload"].get("prediction_sha256") == prediction_hash]
    if prior and prior[-1]["payload"].get("outcomes_sha256") == evidence_hash:
        return {"status": "UNCHANGED", "revision": prior[-1]}
    revision = {"prediction_sha256": prediction_hash,
                "supersedes_revision_sha256": prior[-1]["sha256"] if prior else None,
                "outcomes_sha256": evidence_hash, "outcomes": outcomes,
                "checked_at_utc": checked_at_utc, "leg_grades": grades,
                "settlement": settled, "strategy_id": payload["strategy_id"],
                "warning": "Official corrections append a revision; the original prediction and earlier settlements remain intact."}
    row = _append_under_lock(ledger_path, records, "settlement_revision", revision)
    return {"status": "SETTLED_REVISION_APPENDED", "revision": row}


def latest_settlements(records):
    """Latest revision per immutable entry; earlier returns are not double-counted."""
    predictions = {r["sha256"] for r in records if r["kind"] == "prediction"}
    latest = {}
    for row in records:
        if row["kind"] != "settlement_revision":
            continue
        ref = row["payload"].get("prediction_sha256")
        if ref not in predictions:
            raise EvidenceError("Settlement references a missing prediction")
        expected = latest[ref]["sha256"] if ref in latest else None
        if row["payload"].get("supersedes_revision_sha256") != expected:
            raise EvidenceError("Broken settlement revision chain")
        latest[ref] = row
    return latest
