"""Unit tests for the ledger. Standard library only.

Run from the repository root:
    python3 -m unittest discover -s ledger/scripts -p 'test_ledger.py' -v

Every strategy dictionary built in this file is a SYNTHETIC TEST FIXTURE used to exercise the rules.
None of them is a result, and none is written to any data file.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_ledger  # noqa: E402
import demotion_gate  # noqa: E402

RULES = demotion_gate.load_json(demotion_gate.RULES_PATH)
REGISTRY = demotion_gate.load_json(demotion_gate.REGISTRY_PATH)

ALL_GATES_TRUE = {"G1": True, "G2": True, "G3": True, "G4": True, "G5": True, "G6": True, "G7": True, "G8": True}
GOOD_WINDOW = {"n": 120, "skill_pct_lcb": 1.5, "p_holm": 0.01, "half1_diff": -0.2, "half2_diff": -0.4,
               "days_since_last_official_result": 3}


def live(**kw):
    """SYNTHETIC TEST FIXTURE: a LIVE strategy that passes everything unless overridden."""
    base = {"id": "T", "status": "LIVE", "applicability_key": "single_moneyline", "sample_rule": "single",
            "gates": dict(ALL_GATES_TRUE), "live_window": dict(GOOD_WINDOW)}
    base.update(kw)
    return base


def reasons_of(strategy):
    return " | ".join(demotion_gate.evaluate(strategy, RULES)["reasons"])


class DemotionRules(unittest.TestCase):
    def test_good_live_strategy_is_kept(self):
        d = demotion_gate.evaluate(live(), RULES)
        self.assertEqual(d["action"], "KEEP_LIVE")
        self.assertEqual(d["reasons"], [])

    def test_paper_and_blocked_strategies_are_never_touched(self):
        for status in ("PAPER-ELIGIBLE", "BLOCKED", "PAPER"):
            failing = live(status=status, gates=dict(ALL_GATES_TRUE, G1=False), live_window=None)
            d = demotion_gate.evaluate(failing, RULES)
            self.assertEqual(d["action"], "NO_ACTION", status)
            self.assertEqual(d["reasons"], [], status)

    def test_D1_provenance_failure_demotes(self):
        self.assertIn("D1", reasons_of(live(gates=dict(ALL_GATES_TRUE, G1=False))))
        self.assertEqual(demotion_gate.evaluate(live(gates=dict(ALL_GATES_TRUE, G1=False)), RULES)["action"],
                         "DEMOTE_TO_PAPER")

    def test_D2_market_dependence_demotes(self):
        self.assertIn("D2", reasons_of(live(gates=dict(ALL_GATES_TRUE, G8=False))))

    def test_D3_null_on_applicable_gate_counts_as_fail(self):
        # moneyline: G7 applies, so a null G7 is a FAIL (fail-closed)
        self.assertIn("D3", reasons_of(live(gates=dict(ALL_GATES_TRUE, G7=None))))

    def test_D3_null_on_non_applicable_gate_does_not_demote(self):
        # spread/total: G7 is not applicable, so a null G7 is not a failure
        spread = live(applicability_key="single_spread_or_total", gates=dict(ALL_GATES_TRUE, G7=None))
        self.assertEqual(demotion_gate.evaluate(spread, RULES)["action"], "KEEP_LIVE")

    def test_D4_missing_window_demotes_fail_closed(self):
        self.assertIn("D4", reasons_of(live(live_window=None)))

    def test_D4_sample_below_minimum_demotes(self):
        self.assertIn("D4", reasons_of(live(live_window=dict(GOOD_WINDOW, n=79))))
        self.assertNotIn("D4", reasons_of(live(live_window=dict(GOOD_WINDOW, n=80))))

    def test_D4_parlay_uses_40_pair_minimum(self):
        parlay = live(applicability_key="joint_probability_parlay", sample_rule="parlay_pairs",
                      live_window=dict(GOOD_WINDOW, n=39))
        self.assertIn("D4", reasons_of(parlay))

    def test_D5_negative_lower_bound_demotes(self):
        self.assertIn("D5", reasons_of(live(live_window=dict(GOOD_WINDOW, skill_pct_lcb=-0.01))))

    def test_D6_multiplicity_fails_at_0_05(self):
        self.assertIn("D6", reasons_of(live(live_window=dict(GOOD_WINDOW, p_holm=0.05))))
        self.assertNotIn("D6", reasons_of(live(live_window=dict(GOOD_WINDOW, p_holm=0.049))))

    def test_D7_either_half_not_improving_demotes(self):
        self.assertIn("D7", reasons_of(live(live_window=dict(GOOD_WINDOW, half2_diff=0.0))))
        self.assertIn("D7", reasons_of(live(live_window=dict(GOOD_WINDOW, half1_diff=0.1))))

    def test_D8_stale_results_demote(self):
        self.assertIn("D8", reasons_of(live(live_window=dict(GOOD_WINDOW, days_since_last_official_result=15))))

    def test_missing_values_are_failures_not_passes(self):
        self.assertIn("D5", reasons_of(live(live_window=dict(GOOD_WINDOW, skill_pct_lcb=None))))
        self.assertIn("D6", reasons_of(live(live_window=dict(GOOD_WINDOW, p_holm=None))))

    def test_current_registry_has_no_live_strategy_and_no_demotion(self):
        result = demotion_gate.run(REGISTRY, RULES)
        self.assertEqual(result["live_strategies"], 0)
        self.assertEqual(result["action_counts"], {"NO_ACTION": len(REGISTRY["strategies"])})

    def test_rules_file_thresholds_match_gate_text(self):
        self.assertEqual(RULES["minimum_live_window_games"]["single"], 80)
        self.assertEqual(RULES["minimum_live_window_games"]["parlay_pairs"], 40)
        self.assertEqual(RULES["minimum_live_window_games"]["player_prop_player_games"], 100)


class SignalStakingSeparation(unittest.TestCase):
    @staticmethod
    def rows():
        return [
            {"id": "A", "signal_verdict": "PASS", "skill_pct_lcb": 2.0},
            {"id": "B", "signal_verdict": "PASS", "skill_pct_lcb": 1.0},
            {"id": "C", "signal_verdict": "FAIL G4", "skill_pct_lcb": 9.0},  # a big number must not rank a FAIL
        ]

    def test_only_pass_strategies_get_a_rank(self):
        ranks = build_ledger.rank_signal(self.rows())
        self.assertNotIn("C", ranks)
        self.assertEqual(ranks["A"]["rank"], 1)
        self.assertEqual(ranks["B"]["rank"], 2)

    def test_medals_go_to_top_three_passes_only(self):
        rows = [{"id": "P%d" % i, "signal_verdict": "PASS", "skill_pct_lcb": float(10 - i)} for i in range(5)]
        ranks = build_ledger.rank_signal(rows)
        self.assertEqual([ranks["P%d" % i]["medal"] for i in range(5)], ["Gold", "Silver", "Bronze", "", ""])

    def test_staking_fields_cannot_change_rank(self):
        plain = build_ledger.rank_signal(self.rows())
        loaded = []
        for r in self.rows():
            r = dict(r, roi_pct={"A": -90.0, "B": 500.0, "C": 900.0}[r["id"]], units_staked=10_000)
            loaded.append(r)
        self.assertEqual(build_ledger.rank_signal(loaded), plain)

    def test_split_file_has_blank_staking_and_signal_rank_only(self):
        split = demotion_gate.load_json(os.path.join(LEDGER, "results", "leaderboard-split.json"))
        for row in split["rows"]:
            self.assertIsNone(row["staking"]["units_staked"])
            self.assertIsNone(row["staking"]["roi_pct"])
            self.assertIsNone(row["staking"]["closing_line_value_pct"])
        passes = [r["id"] for r in split["rows"] if r["signal"]["verdict"] == "PASS"]
        self.assertEqual(sorted(passes), ["S1", "S2", "S6", "S7"])
        self.assertTrue(all(r["consistency"]["matches_origination_rank"] for r in split["rows"]))


class Arithmetic(unittest.TestCase):
    def test_no_vig_american_prices(self):
        self.assertEqual(build_ledger.american_from_p(0.6), -150)
        self.assertEqual(build_ledger.american_from_p(0.4), 150)
        self.assertEqual(build_ledger.american_from_p(0.5), -100)

    def test_results_feed_has_149_rows_and_no_arithmetic_failure(self):
        feed = demotion_gate.load_json(os.path.join(LEDGER, "data", "results-feed.json"))
        self.assertEqual(len(feed["rows"]), 149)
        self.assertEqual(feed["counts"]["added_week10_finals"], 12)
        self.assertEqual(feed["counts"]["week10_unresolved"], 1)
        self.assertEqual(feed["counts"]["arithmetic_failures"], 0)
        self.assertEqual(sum(1 for r in feed["rows"] if r["winner"] == "NONE"), 1)
        self.assertEqual(len({r["key"] for r in feed["rows"]}), 149)
        self.assertEqual(len(feed["unresolved"]), 1)
        self.assertIsNone(feed["unresolved"][0]["scores"])

    def test_price_store_has_no_unverified_values(self):
        prices = demotion_gate.load_json(os.path.join(LEDGER, "data", "price-snapshots.json"))
        self.assertEqual(len(prices["markets"]), 39)
        for m in prices["markets"]:
            if m["opening_value"] is not None or m["closing_value"] is not None:
                self.assertIsNotNone(m["opening_source_url"] or m["closing_source_url"])
            self.assertIsNone(m["opening_value"])   # no official open/close series exists (LF-01)
            self.assertIsNone(m["closing_value"])
        # snapshots carry the published FanDuel lines (locked 2 p.m. ET Thursday) and every one
        # must cite its official nfl.com picks-article URL (SG-03 correction, 2026-11-15)
        self.assertEqual(len(prices["snapshots"]), 87)  # 29 games x 3 markets, Weeks 9-10
        for s in prices["snapshots"]:
            self.assertTrue(s["source_url"].startswith("https://www.nfl.com/news/nfl-picks-week-"))
            self.assertIn(s["market"], ("side", "total", "moneyline"))
            self.assertIsNotNone(s["value"])

    def test_devig_p_home_normalises_two_way_american_prices(self):
        def dv(h, a):
            ph, pa = build_ledger.american_to_p(h), build_ledger.american_to_p(a)
            return ph / (ph + pa)
        self.assertAlmostEqual(dv(-152, 128), 0.5790, places=4)
        self.assertAlmostEqual(dv(-110, -110), 0.5, places=6)
        self.assertAlmostEqual(build_ledger.american_to_p(128), 100.0 / 228, places=6)
        self.assertAlmostEqual(build_ledger.american_to_p(-152), 152.0 / 252, places=6)


if __name__ == "__main__":
    unittest.main()
