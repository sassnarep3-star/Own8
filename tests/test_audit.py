"""Regression checks demonstrating audit findings without importing the legacy pipeline."""
import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AuditEvidence(unittest.TestCase):
    def test_week9_neutral_game_in_schedule(self):
        data = json.loads((ROOT / 'data/schedule-2026-week9.json').read_text())
        game = next(g for g in data['games'] if g['away'] == 'CIN' and g['home'] == 'ATL')
        self.assertIn('Madrid', game['venue'])

    def test_spread_sign_example(self):
        home_margin, home_handicap = 3, -3
        self.assertEqual(home_margin + home_handicap, 0)
        self.assertNotEqual(home_margin - home_handicap, 0)

    def test_legacy_script_contains_no_score_fetch(self):
        tree = ast.parse((ROOT / 'scripts/analyze.py').read_text())
        imports = {a.name.split('.')[0] for n in ast.walk(tree)
                   if isinstance(n, ast.Import) for a in n.names}
        self.assertFalse(imports.intersection({'requests', 'urllib', 'http', 'httpx'}))

if __name__ == '__main__':
    unittest.main()
