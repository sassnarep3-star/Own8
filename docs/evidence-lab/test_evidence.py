"""Tests that explicitly use the captured official historical sample."""
import csv
import unittest
from pathlib import Path
from analyze import load_evidence
from engine import walk_forward

ROOT = Path(__file__).resolve().parent


class OfficialEvidence(unittest.TestCase):
    def test_pinned_capture_hashes_and_scope(self):
        manifest, games = load_evidence()
        self.assertEqual(manifest["commit"], "9ad0b4b2ea36697e29e44e2399512cc1ce70358c")
        self.assertEqual(manifest["files"][0]["sha256"], "f5bbd13d9c711c07e3d4a5b674eb25c1f5f9ced099729337bfd366b5229199ed")
        self.assertEqual(len(games), 91)
        self.assertEqual({g["season"] for g in games}, {2017})
        self.assertEqual({g["week"] for g in games}, set(range(1, 7)))

    def test_all_raw_fact_cells_preserved(self):
        _, games = load_evidence()
        with (ROOT / "evidence/games.csv").open(newline="") as f:
            raw = list(csv.DictReader(f))
        for source, game in zip(raw, games):
            self.assertEqual(source, game["official_fields"])
            self.assertEqual(game["home_score"], int(source["HomeScore"]))
            self.assertEqual(game["away_score"], int(source["VisitorScore"]))

    def test_unique_rows_and_per_row_official_provenance(self):
        _, games = load_evidence()
        self.assertEqual(len({g["id"] for g in games}), 91)
        for i, game in enumerate(games, 2):
            self.assertTrue(game["source_url"].startswith("https://github.com/nfl-football-ops/Big-Data-Bowl/blob/"))
            self.assertTrue(game["source_url"].endswith(f"#L{i}"))

    def test_official_sample_holdout_and_blank_market(self):
        _, games = load_evidence()
        rows = walk_forward(games)
        self.assertEqual(len(rows), 60)
        for row in rows:
            self.assertLess(row["training_max_week"], row["week"])
            self.assertTrue(all(next(g["week"] for g in games if g["id"] == key) < row["week"] for key in row["training_ids"]))
            self.assertIsNone(row["official_market_handicap"])
            self.assertIsNone(row["cover_probability"])
            self.assertIsNone(row["expected_return"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
