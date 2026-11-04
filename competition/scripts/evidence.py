"""Trusted-snapshot adapter; read-only to the rest of the repository.

Authority is claim-specific: NFL for fixtures/results, a primary operator for
its own observed prices. No URL/boolean is accepted as a substitute for source
review. Confirmed transcriptions are hash-checked before being normalized.
"""
from pathlib import Path

try:
    from .core import american_to_decimal
    from .ledger import EvidenceBook, digest, GithubReceipts
    from .pipeline import prepare_evidence, verify_manifest, load, ROOT
except ImportError:
    from core import american_to_decimal
    from ledger import EvidenceBook, digest, GithubReceipts
    from pipeline import prepare_evidence, verify_manifest, load, ROOT


def load_book(with_live_receipt_api=False):
    verify_manifest()
    _, fixtures, _, markets, _ = prepare_evidence()
    book = EvidenceBook(fixtures={f["event_id"]: f for f in fixtures})
    if with_live_receipt_api:
        book.receipt_provider = GithubReceipts()
    for row in markets:
        contracts = [
            ("spread", "away", row["away"], None, row["away_handicap"], row["away_spread_odds"]),
            ("spread", "home", row["home"], None, row["home_handicap"], row["home_spread_odds"]),
            ("moneyline", "away", row["away"], None, None, row["away_moneyline"]),
            ("moneyline", "home", row["home"], None, None, row["home_moneyline"]),
            ("total", "over", None, "over", row["total"], row["over_odds"]),
            ("total", "under", None, "under", row["total"], row["under_odds"])]
        for market, suffix, team, side, line, price in contracts:
            ident = f"dk-observed-20261104:{row['event_id']}:{market}:{suffix}"
            quote = {"id": ident, "event_id": row["event_id"], "market": market,
                     "american_odds": price, "decimal_odds_derived": str(american_to_decimal(price)),
                     "source_url": row["source_url"], "verification": "confirmed_transcription",
                     "quote_updated_at_utc": None, "observed_at_utc": None,
                     "snapshot_sha256": digest(row), "status": "SNAPSHOT_ONLY_FRESHNESS_UNVERIFIED"}
            if team is not None:
                quote["team"] = team
            if side is not None:
                quote["side"] = side
            if line is not None:
                quote["line"] = line
            book.quotes[ident] = quote
    # No invented source-timed prices, final injury clearances, operator rules,
    # preregistration receipts, combined prices, joint models or player stats.
    for strategy in load("data/strategy-catalog.json")["strategies"]:
        book.strategies[strategy["id"]] = {"id": strategy["id"], "version_hash": digest(strategy),
                                           "registered_at_utc": None, "receipt_verified": False}
    return book
