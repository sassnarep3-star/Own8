"""Regression cases are synthetic unless a test explicitly loads official evidence."""
import copy
import math
import unittest
from engine import (GATES, Policy, all_gates_pass, assess_strategy, cluster_correlation,
                    decimal_odds, expected_return, home_cover_margin, joint_from_paired_outcomes,
                    no_vig_two_way, pearson, quantile, quote_is_fresh,
                    settle_home_spread, settle_over, walk_forward)


class BettingMath(unittest.TestCase):
    def test_american_conversion(self):
        self.assertAlmostEqual(decimal_odds(-110), 1 + 100 / 110)
        self.assertEqual(decimal_odds(150), 2.5)

    def test_invalid_odds(self):
        for x in (0, 99, -99, math.nan, math.inf, True, None):
            with self.subTest(x=x), self.assertRaises(ValueError):
                decimal_odds(x)

    def test_no_vig_two_way(self):
        a, b = no_vig_two_way(-110, -110)
        self.assertEqual((a, b), (.5, .5))

    def test_ev_accounts_for_pushes(self):
        self.assertAlmostEqual(expected_return(.5, 100, .1), .1)
        self.assertAlmostEqual(expected_return(110 / 210, -110), 0)

    def test_invalid_probability(self):
        for p in (-.1, 1.1, math.nan, None, True):
            with self.subTest(p=p), self.assertRaises(ValueError):
                expected_return(p, -110)
        with self.assertRaises(ValueError):
            expected_return(.8, -110, .3)

    def test_home_favorite_sign(self):
        self.assertEqual(home_cover_margin(7, -3), 4)
        self.assertEqual(home_cover_margin(2, -3), -1)

    def test_home_underdog_sign(self):
        self.assertEqual(home_cover_margin(-2, 3), 1)
        self.assertEqual(home_cover_margin(-7, 3), -4)

    def test_spread_push(self):
        self.assertEqual(settle_home_spread(27, 24, -3), "PUSH")

    def test_spread_win_loss(self):
        self.assertEqual(settle_home_spread(28, 24, -3), "WIN")
        self.assertEqual(settle_home_spread(26, 24, -3), "LOSS")

    def test_over_settlement(self):
        self.assertEqual(settle_over(24, 21, 45), "PUSH")
        self.assertEqual(settle_over(24, 21, 44.5), "WIN")
        self.assertEqual(settle_over(24, 21, 45.5), "LOSS")

    def test_invalid_scores(self):
        for score in (-1, 3.2, math.nan, True):
            with self.subTest(score=score), self.assertRaises(ValueError):
                settle_home_spread(score, 7, -3)
            with self.subTest(score=score), self.assertRaises(ValueError):
                settle_over(7, score, 14)


class Dependence(unittest.TestCase):
    def test_correlations(self):
        self.assertAlmostEqual(pearson([1, 2, 3], [2, 4, 6]), 1)
        self.assertAlmostEqual(pearson([1, 2, 3], [6, 4, 2]), -1)

    def test_undefined_correlations_blank(self):
        self.assertIsNone(pearson([1, 1, 1], [2, 3, 4]))
        self.assertIsNone(pearson([1, 2], [1, 2]))

    def test_misalignment_rejected(self):
        with self.assertRaises(ValueError):
            pearson([1, 2, 3], [1, 2])

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            pearson([1, 2, math.nan], [1, 2, 3])

    def test_correlated_joint_not_marginal_product(self):
        result = joint_from_paired_outcomes([[1, 1], [1, 1], [0, 0], [0, 0]])
        self.assertEqual(result["joint_probability"], .5)
        self.assertNotEqual(result["joint_probability"], math.prod(result["marginals"]))
        self.assertLessEqual(result["frechet_lower"], result["joint_probability"])
        self.assertGreaterEqual(result["frechet_upper"], result["joint_probability"])

    def test_three_leg_joint(self):
        self.assertEqual(joint_from_paired_outcomes([[1, 1, 1], [1, 0, 1], [0, 1, 1]])["joint_probability"], 1 / 3)

    def test_missing_push_or_unaligned_rejected(self):
        for rows in ([[1, 1]], [[1], [0], [1]], [[1, 1], [1], [0, 0]],
                     [[1, None], [1, 1], [0, 0]], [[1, "PUSH"], [1, 1], [0, 0]],
                     [[1, .5], [1, 1], [0, 0]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                joint_from_paired_outcomes(rows)

    def test_cluster_reproducibility(self):
        rows = [(1, 2, 1), (2, 1, 1), (3, 5, 2), (4, 4, 2), (5, 3, 3)]
        a = cluster_correlation(rows, draws=30)
        self.assertEqual(a, cluster_correlation(rows, draws=30))
        self.assertEqual(a["clusters"], 3)

    def test_quantiles(self):
        self.assertEqual(quantile([0, 10], .5), 5)
        with self.assertRaises(ValueError):
            quantile([], .5)


class FailClosedGates(unittest.TestCase):
    def passing_record(self):
        return {"official_fields_matched": True, "official_price_matched": True,
                "quote_fresh": True, "injury_status_final": True,
                "predictions_locked_before_kickoff": True, "no_leakage_audit": True,
                "holdout_bets": 1000, "seasons": 3, "registered_trials": 7,
                "cluster_adjusted_p": .001, "simultaneous_roi_lower": .01,
                "calibration_pass": True, "season_robustness_pass": True,
                "paired_dependence_validated": True, "portfolio_exposure_checked": True,
                "holdout_drawdown": .1, "stake_policy_locked": True,
                "official_results_matched": True, "book_rules_matched": True}

    def test_no_record_no_reward(self):
        result = assess_strategy({})
        self.assertFalse(result["eligible"])
        self.assertIsNone(result["reward_points"])
        self.assertIsNone(result["rank"])

    def test_synthetic_complete_record(self):
        result = assess_strategy(self.passing_record())
        self.assertTrue(result["eligible"])
        self.assertEqual(result["reward_points"], 100)

    def test_each_required_fact_can_block(self):
        for name in self.passing_record():
            record = self.passing_record()
            del record[name]
            with self.subTest(name=name):
                self.assertFalse(assess_strategy(record)["eligible"])

    def test_conditional_is_not_pass(self):
        for state in ("CONDITIONAL", "UNKNOWN", "NOT_COMPUTABLE", None, True, "pass"):
            gates = dict.fromkeys(GATES, "PASS")
            gates["freshness"] = state
            with self.subTest(state=state):
                self.assertFalse(all_gates_pass(gates))

    def test_missing_or_extra_gate_blocks(self):
        self.assertFalse(all_gates_pass({"evidence": "PASS"}))
        self.assertFalse(all_gates_pass({**dict.fromkeys(GATES, "PASS"), "x": "PASS"}))

    def test_multiple_testing(self):
        record = self.passing_record()
        record["cluster_adjusted_p"] = .01
        self.assertFalse(assess_strategy(record)["eligible"])

    def test_significant_p_without_profit_blocks(self):
        record = self.passing_record()
        record["simultaneous_roi_lower"] = 0
        self.assertFalse(assess_strategy(record)["eligible"])

    def test_invalid_metrics_block(self):
        for name, value in (("cluster_adjusted_p", -.1), ("holdout_drawdown", -.1),
                            ("holdout_bets", math.nan), ("seasons", True), ("registered_trials", 1.5)):
            record = self.passing_record()
            record[name] = value
            with self.subTest(name=name):
                self.assertFalse(assess_strategy(record)["eligible"])

    def test_stale_and_future_quotes(self):
        self.assertTrue(quote_is_fresh("2026-11-04T10:00:00Z", "2026-11-04T10:15:00Z"))
        self.assertFalse(quote_is_fresh("2026-11-04T10:00:00Z", "2026-11-04T10:15:01Z"))
        self.assertFalse(quote_is_fresh("2026-11-04T10:01:00Z", "2026-11-04T10:00:00Z"))

    def test_ambiguous_quotes_block(self):
        for stamp in (None, "today", "2026-11-04T10:00:00"):
            self.assertFalse(quote_is_fresh(stamp, "2026-11-04T10:00:00Z"))

    def test_timezone_offsets(self):
        self.assertTrue(quote_is_fresh("2026-11-04T02:00:00-08:00", "2026-11-04T10:05:00Z"))


class Chronology(unittest.TestCase):
    def games(self):
        return [{"id": str(week), "week": week, "home": "A", "away": "B",
                 "home_score": 20 + week, "away_score": 20, "source_url": "synthetic"} for week in range(1, 7)]

    def test_warmup_not_scored(self):
        self.assertEqual([r["week"] for r in walk_forward(self.games())], [3, 4, 5, 6])

    def test_training_only_prior_weeks(self):
        for r in walk_forward(self.games()):
            self.assertLess(r["training_max_week"], r["week"])
            self.assertNotIn(r["id"], r["training_ids"])

    def test_heldout_targets_do_not_affect_their_predictions(self):
        games = self.games()
        original = walk_forward(games)
        changed = copy.deepcopy(games)
        changed[2]["home_score"] = 90
        recomputed = walk_forward(changed)
        self.assertEqual(original[0]["predicted_home_margin"], recomputed[0]["predicted_home_margin"])
        self.assertNotEqual(original[1]["predicted_home_margin"], recomputed[1]["predicted_home_margin"])

    def test_handicap_opposite_margin(self):
        for r in walk_forward(self.games()):
            self.assertEqual(r["fair_home_handicap"], -r["predicted_home_margin"])
            self.assertIsNone(r["expected_return"])
            self.assertIsNone(r["official_market_handicap"])

    def test_invalid_prior(self):
        with self.assertRaises(ValueError):
            walk_forward(self.games(), prior_games=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
