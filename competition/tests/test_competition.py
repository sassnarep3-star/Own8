"""SYNTHETIC unit fixtures only. Never imported as production NFL predictions.

Artificial scores, receipts, dates, probabilities and prices below test software
branches. They are not verified sports data, strategies, backtests or returns.
"""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from core import (EvidenceError, all_pass, american_to_decimal, baseline_lines, brier_score,
                  expected_roi, fair_decimal, grade_leg, implied_probability, joint_binary_probability,
                  number, official_url, paired_correlation, point_clv, settle_ticket, timestamp,
                  two_way_normalization)
from ledger import (EvidenceBook, admission, append_record, digest, open_risk_from_chain,
                    publish_prediction, read_chain, receipt_body, validate_payload)
from evaluation import DEFAULT_POLICY, evaluate_leaderboard, holm_adjust, quantile, week_block_summary
from evidence import load_book
from pipeline import prepare_evidence, verify_manifest, inherited_coverage
from settlement import latest_settlements, settle_prediction


class SyntheticReceipts:
    """Explicit in-memory TEST double, not an alternative production adapter."""
    def __init__(self, payload):
        self.payload = payload
        self.edited = False
        self.bad_hash = False
        self.created_at = "2025-09-01T00:10:00Z"
    def create(self, _payload_hash):
        return {"comment_id": 1, "url": "https://github.com/example/test/issues/1#issuecomment-1"}
    def load(self, reference):
        return {"body": receipt_body("wrong" if self.bad_hash else digest(self.payload)),
                "created_at": self.created_at, "updated_at": "2025-09-01T00:11:00Z" if self.edited else self.created_at,
                **reference}


def synthetic_payload():
    return {"entry_id": "SYNTHETIC-DO-NOT-PUBLISH", "strategy_id": "TEST-ONLY", "strategy_version": "test-version",
            "training_cutoff_utc": "2025-08-31T00:00:00Z", "stake_units": 1,
            "rulebook_id": "test-rules", "legs": [{"event_id": "test-game", "market": "spread", "team": "HOME", "line": -3, "quote_id": "test-q"}]}


def synthetic_book(payload):
    return EvidenceBook(
        fixtures={"test-game": {"verification": "confirmed_transcription", "source_url": "https://www.nfl.com/schedules/", "kickoff_utc": "2025-09-02T00:00:00Z"}},
        quotes={"test-q": {"event_id": "test-game", "market": "spread", "team": "HOME", "line": -3,
                            "american_odds": -110, "source_url": "https://sportsbook.draftkings.com/",
                            "verification": "confirmed_transcription", "quote_updated_at_utc": "2025-09-01T00:05:00Z", "observed_at_utc": "2025-09-01T00:06:00Z"}},
        clearance={"test-game": {"status": "confirmed_final_report", "source_url": "https://www.nfl.com/injuries/", "reported_at_utc": "2025-08-31T23:00:00Z"}},
        strategies={"TEST-ONLY": {"version_hash": "test-version", "receipt_verified": True, "registered_at_utc": "2025-08-01T00:00:00Z"}},
        rulebooks={"test-rules": {"verification": "reviewed_market_rules", "source_url": "https://sportsbook.draftkings.com/", "applies_to": ["spread"]}},
        receipt_provider=SyntheticReceipts(payload))


def synthetic_result():
    return {"event_id": "test-game", "home": "HOME", "away": "AWAY", "home_score": 24, "away_score": 17,
            "status": "Final", "verification": "confirmed_transcription", "source_url": "https://www.nfl.com/scores/",
            "confirmed_fields": ["home", "away", "home_score", "away_score", "status"]}


class OddsMathTests(unittest.TestCase):
    def test_positive_american(self):
        self.assertEqual(float(american_to_decimal(150)), 2.5)
    def test_negative_american(self):
        self.assertAlmostEqual(float(american_to_decimal(-110)), 1 + 100 / 110)
    def test_even_money(self):
        self.assertEqual(american_to_decimal(100), american_to_decimal(-100))
    def test_no_default_odds(self):
        for value in (None, 0, 50, -99, True, "NaN", "Infinity", 110.5):
            with self.subTest(value=value), self.assertRaises(EvidenceError):
                american_to_decimal(value)
    def test_implied_probability(self):
        self.assertAlmostEqual(implied_probability(-200), 2 / 3)
    def test_overround_and_normalization(self):
        q = two_way_normalization(-110, -110)
        self.assertEqual(q["a_share"], .5)
        self.assertAlmostEqual(q["overround"], 2 * 110 / 210 - 1)
    def test_ev_has_push_probability(self):
        self.assertAlmostEqual(expected_roi(.5, .1, 2), .1)
    def test_ev_does_not_assume_push_zero(self):
        with self.assertRaises(EvidenceError):
            expected_roi(.5, None, 2)
    def test_ev_rejects_impossible_probabilities(self):
        with self.assertRaises(EvidenceError):
            expected_roi(.8, .3, 2)
    def test_fair_odds(self):
        self.assertAlmostEqual(fair_decimal(.5, .1), 1.8)
    def test_no_fair_odds_for_zero_win(self):
        with self.assertRaises(EvidenceError):
            fair_decimal(0, 0)
    def test_brier_three_outcomes(self):
        self.assertAlmostEqual(brier_score([.5, .4, .1], 0), .42)
    def test_brier_rejects_unnormalized(self):
        with self.assertRaises(EvidenceError):
            brier_score([.5, .6], 0)
    def test_binary_joint_not_independence_by_default(self):
        self.assertAlmostEqual(joint_binary_probability(.5, .5, .4), .35)
    def test_joint_enforces_frechet_bounds(self):
        with self.assertRaises(EvidenceError):
            joint_binary_probability(.9, .1, 1)
    def test_constant_input_not_zero_correlation(self):
        self.assertIsNone(paired_correlation({1: 1, 2: 1}, {1: 2, 2: 3})["r"])
    def test_pair_before_missing_deletion(self):
        result = paired_correlation({1: 1, 2: None, 3: 3}, {1: None, 2: 2, 3: 3})
        self.assertEqual(result["n"], 1)
        self.assertIsNone(result["r"])
    def test_pearson_identity(self):
        self.assertAlmostEqual(paired_correlation({1: 1, 2: 2, 3: 3}, {1: 3, 2: 2, 3: 1})["r"], -1)
    def test_spread_clv_sign(self):
        self.assertEqual(point_clv("spread", None, -3, -4), 1)
        self.assertEqual(point_clv("spread", None, 3, 2), 1)
    def test_total_clv_sign(self):
        self.assertEqual(point_clv("total", "over", 45, 46), 1)
        self.assertEqual(point_clv("total", "under", 46, 45), 1)
    def test_moneyline_no_fake_point_clv(self):
        with self.assertRaises(EvidenceError):
            point_clv("moneyline", None, -120, -130)
    def test_baseline_signed_handicap(self):
        row = baseline_lines({"W": 1, "L": 0, "T": 0, "PF": 10, "PA": 20}, {"W": 1, "L": 0, "T": 0, "PF": 20, "PA": 10})
        self.assertEqual(row["home_margin"], 10)
        self.assertEqual(row["home_handicap"], -10)
        self.assertFalse(row["candidate"])
        self.assertIsNone(row["home_win_probability"])
    def test_url_authority_not_substring(self):
        self.assertTrue(official_url("https://www.nfl.com/scores/"))
        for bad in ("https://www.nfl.com.attacker.test/", "http://www.nfl.com", "https://attacker@www.nfl.com/", "https://www.nfl.com:8080/", None):
            self.assertFalse(official_url(bad))
    def test_timezone_not_guessed(self):
        with self.assertRaises(EvidenceError):
            timestamp("2026-11-04T15:14:47")
    def test_conditional_is_not_pass(self):
        self.assertFalse(all_pass({"g": {"status": "CONDITIONAL"}}))
        self.assertFalse(all_pass({}))


class SettlementMathTests(unittest.TestCase):
    def setUp(self):
        self.leg = synthetic_payload()["legs"][0]
        self.result = synthetic_result()
        self.rule = synthetic_book(synthetic_payload()).rulebooks["test-rules"]
    def test_home_handicap_added_to_home_margin(self):
        self.assertEqual(grade_leg(self.leg, self.result)["status"], "WIN")
    def test_away_spread_sign(self):
        self.assertEqual(grade_leg({**self.leg, "team": "AWAY", "line": 8}, self.result)["status"], "WIN")
    def test_spread_push(self):
        self.assertEqual(grade_leg({**self.leg, "line": -7}, self.result)["status"], "PUSH")
    def test_over_under_push(self):
        leg = {"event_id": "test-game", "market": "total", "line": 41, "side": "under"}
        self.assertEqual(grade_leg(leg, self.result)["status"], "PUSH")
        leg["line"] = 42
        self.assertEqual(grade_leg(leg, self.result)["status"], "WIN")
    def test_missing_outcome_not_loss(self):
        self.assertEqual(grade_leg(self.leg, None)["status"], "PENDING")
    def test_unfinalized_not_settled(self):
        self.assertEqual(grade_leg(self.leg, {**self.result, "status": "In Progress"})["status"], "PENDING")
    def test_wrong_event_not_settled(self):
        self.assertEqual(grade_leg(self.leg, {**self.result, "event_id": "other"})["status"], "HOLD")
    def test_unverified_result_not_settled(self):
        self.assertEqual(grade_leg(self.leg, {**self.result, "verification": "UNVERIFIED"})["status"], "HOLD")
    def test_moneyline_tie_needs_rules(self):
        self.assertEqual(grade_leg({**self.leg, "market": "moneyline"}, {**self.result, "home_score": 17})["status"], "HOLD")
    def test_player_zero_is_not_dnp(self):
        key = "player:TEST:passing_yards"
        prop = {"event_id": "test-game", "market": "player_prop", "player_id": "TEST", "stat": "passing_yards", "line": .5, "side": "under"}
        result = {**self.result, "confirmed_fields": [key, "participation", "status"], "player_stats": {key: 0}, "participation": {"TEST": "played"}}
        self.assertEqual(grade_leg(prop, result)["status"], "WIN")
        result["participation"]["TEST"] = "did_not_play"
        self.assertEqual(grade_leg(prop, result)["status"], "HOLD")
    def test_no_default_single_payout(self):
        ticket = {"legs": [self.leg], "stake_units": 1}
        self.assertEqual(settle_ticket(ticket, [{"status": "WIN"}], self.rule)["status"], "HOLD_PRICE")
    def test_profit_vs_return(self):
        ticket = {"legs": [self.leg], "stake_units": 1, "quoted_decimal_odds": 2.5}
        settled = settle_ticket(ticket, [{"status": "WIN"}], self.rule)
        self.assertEqual(settled["profit_units"], 1.5)
        self.assertEqual(settled["returned_units"], 2.5)
    def test_ticket_cannot_self_certify_rules(self):
        ticket = {"legs": [self.leg], "stake_units": 1, "quoted_decimal_odds": 2.5, "settlement_rule_verified": True, "rule_source_url": "https://sportsbook.draftkings.com/"}
        self.assertEqual(settle_ticket(ticket, [{"status": "WIN"}])["status"], "HOLD_RULES")
    def test_parlay_requires_exact_combined_price(self):
        ticket = {"legs": [self.leg, self.leg], "stake_units": 1}
        self.assertEqual(settle_ticket(ticket, [{"status": "WIN"}, {"status": "WIN"}], self.rule)["status"], "HOLD_PRICE")
    def test_parlay_push_never_infers_subset_price(self):
        ticket = {"legs": [self.leg, self.leg], "stake_units": 1, "quoted_decimal_odds": 4}
        result = settle_ticket(ticket, [{"status": "WIN"}, {"status": "PUSH"}], self.rule)
        self.assertEqual(result["status"], "HOLD_RULES")
        self.assertIsNone(result["profit_units"])
    def test_loss_exact_risk(self):
        ticket = {"legs": [self.leg], "stake_units": .5, "quoted_decimal_odds": 2}
        self.assertEqual(settle_ticket(ticket, [{"status": "LOSS"}], self.rule)["profit_units"], -.5)


class AdmissionAndLedgerTests(unittest.TestCase):
    def setUp(self):
        self.payload = synthetic_payload()
        self.book = synthetic_book(self.payload)
        self.reference = self.book.receipt_provider.create(digest(self.payload))
    def check(self):
        return admission(self.payload, self.reference, self.book)
    def test_non_string_contract_reference_rejected(self):
        for key in ("event_id", "quote_id", "team"):
            with self.subTest(key=key):
                bad = copy.deepcopy(self.payload); bad["legs"][0][key] = ["wrong-type"]
                with self.assertRaises(EvidenceError): validate_payload(bad)
    def test_empty_optional_reference_rejected(self):
        self.payload["joint_report_id"] = " "
        with self.assertRaises(EvidenceError): validate_payload(self.payload)
    def test_parallel_publishers_cannot_overspend(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"; path.write_text("")
            second = copy.deepcopy(self.payload); second["entry_id"] = "SECOND-SYNTHETIC"
            books = [synthetic_book(self.payload), synthetic_book(second)]
            for b in books: b.open_risk_cap = 1
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(publish_prediction, path, p, b) for p,b in zip((self.payload,second),books)]
                statuses = sorted(f.result()["status"] for f in futures)
            self.assertEqual(statuses, ["HELD", "LOCKED_PAPER_ONLY"])
            self.assertEqual(len(read_chain(path)), 1)
    def test_parallel_graders_are_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"; path.write_text("")
            entry = publish_prediction(path, self.payload, self.book)["record"]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(settle_prediction, path, entry["sha256"], {"test-game": synthetic_result()}, self.book, "2025-09-03T00:00:00Z") for _ in range(2)]
                statuses = sorted(f.result()["status"] for f in futures)
            self.assertEqual(statuses, ["SETTLED_REVISION_APPENDED", "UNCHANGED"])
            self.assertEqual(len(read_chain(path)), 2)
            self.assertEqual(len(latest_settlements(read_chain(path))), 1)
    def test_complete_synthetic_single_passes(self):
        self.assertTrue(self.check()["eligible_for_paper_ticket"])
    def test_null_source_time_fails_closed(self):
        self.book.quotes["test-q"]["quote_updated_at_utc"] = None
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_stale_price_fails(self):
        self.book.quotes["test-q"]["quote_updated_at_utc"] = "2025-08-31T00:00:00Z"
        self.assertEqual(self.check()["gates"]["G3_exact_primary_price"]["status"], "HOLD")
    def test_post_lock_observation_fails(self):
        self.book.quotes["test-q"]["observed_at_utc"] = "2025-09-01T00:11:00Z"
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_edited_receipt_fails(self):
        self.book.receipt_provider.edited = True
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_receipt_hash_mismatch_fails(self):
        self.book.receipt_provider.bad_hash = True
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_receipt_after_kickoff_fails(self):
        self.book.receipt_provider.created_at = "2025-09-03T00:00:00Z"
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_training_leakage_fails(self):
        self.payload["training_cutoff_utc"] = "2025-09-02T00:00:00Z"
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_practice_report_not_clearance(self):
        self.book.clearance["test-game"]["status"] = "No Injuries Reported"
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_stale_participation_report_fails(self):
        self.book.clearance["test-game"]["reported_at_utc"] = "2025-08-01T00:00:00Z"
        self.assertFalse(self.check()["eligible_for_paper_ticket"])
    def test_overexposure_fails(self):
        self.assertFalse(admission(self.payload, self.reference, self.book, open_risk=10)["eligible_for_paper_ticket"])
    def test_self_certified_unknown_flag_rejected(self):
        self.payload["all_gates_pass"] = True
        with self.assertRaises(EvidenceError):
            self.check()
    def test_duplicate_leg_rejected(self):
        self.payload["legs"].append(copy.deepcopy(self.payload["legs"][0]))
        with self.assertRaises(EvidenceError):
            self.check()
    def test_different_games_not_independent(self):
        second = copy.deepcopy(self.payload["legs"][0]); second["event_id"] = "another-game"; second["quote_id"] = "another-q"
        self.payload["legs"].append(second)
        self.assertEqual(self.check()["gates"]["G5_joint_distribution"]["status"], "HOLD")
    def test_real_snapshot_can_never_qualify_quote_gate(self):
        book = load_book()
        self.assertEqual(len(book.quotes), 90)
        self.assertTrue(all(q["quote_updated_at_utc"] is None for q in book.quotes.values()))
        self.assertEqual(book.rulebooks, {})
    def test_hash_chain_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"; path.write_text("")
            append_record(path, "prediction", self.payload)
            text = path.read_text().replace('"stake_units":1', '"stake_units":2')
            path.write_text(text)
            with self.assertRaises(EvidenceError):
                read_chain(path)
    def test_checkpoint_detects_removed_tail(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"; path.write_text("")
            row = append_record(path, "prediction", self.payload)
            path.write_text("")
            with self.assertRaises(EvidenceError):
                read_chain(path, row["sha256"], 1)
    def test_missing_ledger_not_silently_empty(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(EvidenceError):
            read_chain(Path(d) / "does-not-exist")
    def test_duplicate_id_cannot_replace_prediction(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"; path.write_text("")
            append_record(path, "prediction", self.payload)
            with self.assertRaises(EvidenceError):
                append_record(path, "prediction", self.payload)
    def test_publisher_checks_atomic_open_risk(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"; path.write_text("")
            self.book.open_risk_cap = 1
            self.assertEqual(publish_prediction(path, self.payload, self.book)["status"], "LOCKED_PAPER_ONLY")
            second = copy.deepcopy(self.payload); second["entry_id"] = "SECOND-SYNTHETIC"
            self.book.receipt_provider.payload = second
            self.assertEqual(publish_prediction(path, second, self.book)["status"], "HELD")
            self.assertEqual(len(read_chain(path)), 1)
    def test_corrections_are_idempotent_revisions(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"; path.write_text("")
            entry = publish_prediction(path, self.payload, self.book)["record"]
            result = synthetic_result()
            first = settle_prediction(path, entry["sha256"], {"test-game": result}, self.book, "2025-09-03T00:00:00Z")
            self.assertEqual(first["status"], "SETTLED_REVISION_APPENDED")
            same = settle_prediction(path, entry["sha256"], {"test-game": result}, self.book, "2025-09-03T00:01:00Z")
            self.assertEqual(same["status"], "UNCHANGED")
            corrected = {**result, "home_score": 17, "away_score": 24}
            second = settle_prediction(path, entry["sha256"], {"test-game": corrected}, self.book, "2025-09-04T00:00:00Z")
            self.assertEqual(second["status"], "SETTLED_REVISION_APPENDED")
            chain = read_chain(path)
            self.assertEqual(len(chain), 3)
            latest = latest_settlements(chain)
            self.assertEqual(len(latest), 1)
            self.assertEqual(latest[entry["sha256"]]["payload"]["settlement"]["profit_units"], -1)
            self.assertEqual(open_risk_from_chain(chain), 0)


class SkillGateTests(unittest.TestCase):
    def test_empty_metrics_blank_not_zero(self):
        board = evaluate_leaderboard([{"id": "TEST", "name": "Synthetic", "category": "single"}], [], "2026-11-04T00:00:00Z")
        row = board["standings"][0]
        self.assertEqual(board["eligible_strategies"], 0)
        for key in ("rank", "reward_points"):
            self.assertIsNone(row[key])
        self.assertIsNone(row["metrics"]["roi"])
    def test_holm_counts_missing_trial(self):
        self.assertEqual(holm_adjust([.01, None, .04]), [.03, None, .08])
    def test_holm_rejects_invalid(self):
        with self.assertRaises(EvidenceError):
            holm_adjust([1.1])
    def test_quantile_interpolation(self):
        self.assertEqual(quantile([0, 10], .5), 5)
    def test_lucky_single_week_cannot_pass(self):
        rows = [{"entry_hash": str(i), "week_id": "2026-W01", "risk_units": 1, "profit_units": 1} for i in range(200)]
        summary = week_block_summary(rows)
        self.assertIsNone(summary["simultaneous_ci_low"])
    def test_constant_returns_not_infinite_confidence(self):
        rows = [{"entry_hash": str(i), "week_id": f"2025-W{i}", "risk_units": 1, "profit_units": 1} for i in range(20)]
        self.assertEqual(week_block_summary(rows)["uncertainty_status"], "HOLD_DEGENERATE_BOOTSTRAP")
    def test_duplicate_returns_rejected(self):
        row = {"entry_hash": "same", "week_id": "2025-W01", "risk_units": 1, "profit_units": 1}
        with self.assertRaises(EvidenceError):
            week_block_summary([row, row])
    def test_unverified_returns_never_ranked(self):
        with self.assertRaises(EvidenceError):
            evaluate_leaderboard([{"id":"TEST","name":"Synthetic","category":"single"}], [{"strategy_id":"TEST","profit_units":99}], "2027-04-01T00:00:00Z")
    def test_unregistered_trial_not_dropped(self):
        with self.assertRaises(EvidenceError):
            evaluate_leaderboard([], [{"strategy_id":"UNKNOWN"}], "2026-11-04T00:00:00Z")
    def test_bootstrap_is_reproducible(self):
        rows = [{"entry_hash": str(i), "week_id": f"2025-W{i}", "risk_units": 1, "profit_units": (i % 5 - 1) / 2} for i in range(20)]
        policy = {**DEFAULT_POLICY, "bootstrap_resamples": 300}
        self.assertEqual(week_block_summary(rows, 8, policy), week_block_summary(rows, 8, policy))


class ActualEvidenceTests(unittest.TestCase):
    def test_malformed_inherited_csv_is_preserved_as_a_flag(self):
        standings, fixtures, scores, _, _ = prepare_evidence()
        rows = inherited_coverage(standings, fixtures, scores)["rows"]
        problems = [r for r in rows if r["parse_issue"]]
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]["dataset"], "data/nfl-2026-standings.csv")
        self.assertIn("__unlabeled_surplus_columns", problems[0]["unverified_fields"])
        self.assertIsNone(problems[0]["values"]["source"])
    def test_catalog_size_not_mislabeled_as_preregistered(self):
        board = evaluate_leaderboard([{"id":"TEST", "name":"Synthetic", "category":"single"}], [], "2026-11-04T00:00:00Z")
        self.assertNotIn("registered_trials", board)
        self.assertEqual(board["trial_family_size"], 1)
    def test_all_manifest_rows_unchanged(self):
        self.assertEqual(len(verify_manifest()), 5)
    def test_actual_counts_and_zero_scores_preserved(self):
        standings, fixtures, scores, markets, injuries = prepare_evidence()
        self.assertEqual([len(x) for x in (standings, fixtures, scores, markets, injuries)], [32, 15, 14, 15, 28])
        self.assertEqual(next(s for s in scores if s["away"] == "ATL")["away_score"], 0)
    def test_kickoff_discrepancy_is_flagged(self):
        _, fixtures, _, markets, _ = prepare_evidence()
        sf = next(f for f in fixtures if f["home"] == "SF")
        self.assertEqual(sf["kickoff_est"], "4:25 PM")
        self.assertTrue(next(m for m in markets if m["home"] == "SF")["kickoff_discrepancy"])
    def test_unreported_injury_fields_null(self):
        injuries = prepare_evidence()[-1]
        self.assertTrue(all(r["injury"] is None and r["game_status"] is None for r in injuries))
    def test_unconfirmed_inherited_fields_null(self):
        standings, fixtures, scores, _, _ = prepare_evidence()
        report = inherited_coverage(standings, fixtures, scores)
        for row in report["rows"]:
            self.assertTrue(all(row["values"][key] is None for key in row["unverified_fields"]))
        core = [r for r in report["rows"] if r["dataset"] == "data/standings-2026-reg-w8.json"]
        self.assertEqual(len(core), 32)
        self.assertTrue(all(len(r["confirmed_fields"]) == 10 for r in core))


if __name__ == "__main__":
    unittest.main()
