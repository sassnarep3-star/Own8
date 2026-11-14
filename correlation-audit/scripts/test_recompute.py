"""Unit tests for recompute_correlations.py. Inputs below are SYNTHETIC TEST FIXTURES, not data."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import recompute_correlations as rc  # noqa: E402


class TestStatistics(unittest.TestCase):
    def test_pearson_perfect_positive_and_negative(self):
        x = [1, 2, 3, 4, 5]
        self.assertAlmostEqual(rc.pearson(x, [2 * v + 1 for v in x]), 1.0, places=12)
        self.assertAlmostEqual(rc.pearson(x, [-v for v in x]), -1.0, places=12)

    def test_pearson_hand_computed(self):
        # x=[1,2,3], y=[1,3,2]: cov sum = 1, sxx = 2, syy = 2 -> r = 0.5
        self.assertAlmostEqual(rc.pearson([1, 2, 3], [1, 3, 2]), 0.5, places=12)

    def test_fisher_ci_symmetric_at_zero(self):
        lo, hi = rc.fisher_ci(0.0, 100)
        self.assertAlmostEqual(lo, -hi, places=12)
        # CI is computed on the Fisher z scale and back-transformed: hi = tanh(z / sqrt(n-3))
        self.assertAlmostEqual(hi, math.tanh(1.959964 / math.sqrt(97)), places=9)

    def test_fisher_p_zero_correlation_is_one(self):
        self.assertAlmostEqual(rc.fisher_p(0.0, 50), 1.0, places=12)

    def test_holm_hand_computed(self):
        # p = [0.01, 0.04, 0.03, 0.005]; m=4
        # sorted: 0.005*4=0.02, 0.01*3=0.03, 0.03*2=0.06, 0.04*1=0.04 -> running max 0.02,0.03,0.06,0.06
        adj = rc.holm([0.01, 0.04, 0.03, 0.005])
        self.assertAlmostEqual(adj[0], 0.03, places=12)
        self.assertAlmostEqual(adj[1], 0.06, places=12)
        self.assertAlmostEqual(adj[2], 0.06, places=12)
        self.assertAlmostEqual(adj[3], 0.02, places=12)

    def test_holm_caps_at_one(self):
        self.assertEqual(rc.holm([0.9, 0.8])[0], 1.0)

    def test_icc_identical_within_groups_is_one(self):
        self.assertAlmostEqual(rc.icc1([[1, 1], [2, 2]]), 1.0, places=12)

    def test_icc_zero_between_variance_gives_negative_bound(self):
        # Equal group means -> MSB = 0. Standard ANOVA ICC(1) = -1/(k-1) = -0.5 for k=3 (not 0).
        self.assertAlmostEqual(rc.icc1([[1, 2, 3], [1, 2, 3], [1, 2, 3]]), -0.5, places=12)


if __name__ == "__main__":
    unittest.main()
