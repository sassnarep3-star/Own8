import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class TableSourceAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = 0
        self.in_tbody = 0
        self.in_row = False
        self.row_hrefs = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.in_table += 1
        elif tag == "tbody":
            self.in_tbody += 1
        elif tag == "tr" and self.in_table and self.in_tbody:
            self.in_row = True
            self.row_hrefs = []
        elif tag == "a" and self.in_row:
            self.row_hrefs.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_row:
            self.rows.append(self.row_hrefs)
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody -= 1
        elif tag == "table":
            self.in_table -= 1


class Week10DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.addendum = json.loads((ROOT / "ledger/data/week10-results-addendum.json").read_text())
        cls.doc = json.loads((HERE / "week10-diagnostic.json").read_text())
        cls.feed = json.loads((ROOT / "ledger/data/results-feed.json").read_text())

    def test_final_and_unresolved_counts(self):
        self.assertEqual(len(self.addendum["rows"]), 12)
        self.assertEqual(len(self.addendum["unresolved"]), 1)
        self.assertIsNone(self.addendum["unresolved"][0]["scores"])
        self.assertEqual(self.doc["n_final_games"], 12)
        self.assertEqual(self.doc["n_unresolved_games_excluded"], 1)

    def test_each_result_has_two_official_links_and_is_final(self):
        keys = set()
        for row in self.addendum["rows"]:
            self.assertNotIn(row["key"], keys)
            keys.add(row["key"])
            self.assertEqual(row["status"], "Final")
            self.assertEqual(row["source_url"], "https://www.nfl.com/scores/2026/week-10")
            self.assertEqual(row["game_url"].split('/')[2], "www.nfl.com")

    def test_results_feed_addition_matches_source_transcription(self):
        feed = {r["key"]: r for r in self.feed["rows"]}
        for src in self.addendum["rows"]:
            actual = feed[src["key"]]
            self.assertEqual(actual["away_score"], src["away_score"])
            self.assertEqual(actual["home_score"], src["home_score"])
            self.assertEqual(actual["verification_status"], "Final (official NFL score page + game center)")

    def test_pre_registered_forecasts_not_mutated(self):
        forecast = json.loads((ROOT / "origination/results/w10-lines.json").read_text())
        self.assertEqual(forecast["originated_at"], self.doc["forecast_originated_at"])
        self.assertEqual(len(forecast["games"]), 13)
        self.assertTrue(all(r["official_scores_url"].startswith("https://www.nfl.com/") for r in self.doc["rows"]))

    def test_report_every_table_row_has_official_nfl_source(self):
        parser = TableSourceAudit()
        parser.feed((HERE / "index.html").read_text())
        self.assertGreater(len(parser.rows), 0)
        for idx, hrefs in enumerate(parser.rows, 1):
            self.assertTrue(any(h.startswith("https://www.nfl.com/") for h in hrefs),
                            "table row %d has no official NFL source link: %r" % (idx, hrefs))

    def test_diagnostic_cannot_be_misread_as_validation_or_roi(self):
        self.assertIn("not a preregistered leaderboard result", self.doc["purpose"])
        self.assertIn("No strategy stakes", " ".join(self.doc["limitations"]))
        self.assertIn("No confidence intervals", self.doc["uncertainty"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
