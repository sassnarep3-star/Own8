import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import strict_analyze as a
import strict_check as c

class StrictTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=a.run()
 def test_evidence_hashes(self):self.assertEqual(len(a.validate_evidence()),3)
 def test_official_url_scope(self):
  self.assertTrue(c.official(a.BDB))
  for u in ['https://nfl.com.evil.test/x','http://www.nfl.com/','https://github.com/random/Big-Data-Bowl','https://www.nfl.com@evil.test/']:
   self.assertFalse(c.official(u))
 def test_standings_coverage(self):self.assertEqual(len(self.d['standings']),32)
 def test_historical_coverage(self):self.assertEqual(len(self.d['games']),91)
 def test_predictions_coverage(self):self.assertEqual(len(self.d['historical_predictions']),60)
 def test_no_same_week_training(self):
  for p in self.d['historical_predictions']:self.assertLess(p['train_max_week'],p['week'])
 def test_future_scores_do_not_leak(self):
  games=a.historical_games();prior=[g for g in games if g['week']<3];g=next(g for g in games if g['week']==3)
  pred=a.predict_from_prior(prior,g['homeTeamAbbr'],g['visitorTeamAbbr'])
  altered=copy.deepcopy(games)
  for row in altered:
   if row['week']>=3:row['HomeScore']=99;row['VisitorScore']=0
  pred2=a.predict_from_prior([x for x in altered if x['week']<3],g['homeTeamAbbr'],g['visitorTeamAbbr'])
  self.assertEqual(pred,pred2)
 def test_spread_sign(self):
  p=a.quote_from_scores(27,20)
  self.assertEqual(p['expected_home_margin'],7)
  self.assertEqual(p['home_handicap_mean_proxy'],-7)
  self.assertEqual(p['expected_total'],47)
 def test_neutral_removes_hfa(self):
  prior=[g for g in a.historical_games() if g['week']<3]
  p=a.predict_from_prior(prior,'NE','KC');n=a.predict_from_prior(prior,'NE','KC',True)
  import statistics
  effect=statistics.mean(g['HomeScore']-g['VisitorScore'] for g in prior)
  self.assertAlmostEqual(p['expected_home_margin']-n['expected_home_margin'],effect)
  self.assertAlmostEqual(p['expected_total'],n['expected_total'])
 def test_no_empty_gates_pass(self):self.assertFalse(a.all_pass({}))
 def test_only_exact_pass(self):
  self.assertTrue(a.all_pass({'g':'PASS'}))
  for value in ['CONDITIONAL','UNKNOWN','PARTIAL','FAIL','BLOCKED',None]:self.assertFalse(a.all_pass({'one':'PASS','two':value}))
 def test_candidates_blocked(self):
  self.assertEqual(len(self.d['current_lines']),15)
  for g in self.d['current_lines']:
   self.assertFalse(g['candidate'])
   for k in ['fair_home_spread','fair_total','fair_moneyline','decimal_odds','edge','market_home_spread']:self.assertIsNone(g[k])
 def test_no_awards_or_measured_zeros(self):
  self.assertEqual(self.d['qualified_strategies'],0)
  for s in self.d['strategies']:
   self.assertFalse(s['qualified'])
   for k in ['rank','reward_points','roi','clv','skill_score']:self.assertIsNone(s[k])
 def test_bet_correlations_unknown(self):
  for c in self.d['correlations']:
   if c['unit']=='settled bet indicators':self.assertIsNone(c['r']);self.assertIsNone(c['n'])
 def test_pearson(self):
  self.assertAlmostEqual(a.pearson([1,2,3],[3,2,1]),-1)
  self.assertIsNone(a.pearson([1,1,1],[1,2,3]))
  self.assertIsNone(a.pearson([1,2],[1,2,3]))
 def test_push_ev(self):
  self.assertAlmostEqual(a.expected_return(.5,.1,2),.1)
  self.assertIsNone(a.expected_return(.6,0,None))
  self.assertAlmostEqual(a.expected_return(1/2.1,0,2.1),0)
  with self.assertRaises(ValueError):a.expected_return(.9,.2,2)
 def test_deterministic_analysis(self):
  before=(R/'strict/results.json').read_bytes();a.run();self.assertEqual(before,(R/'strict/results.json').read_bytes())
 def test_partial_injuries_unknown(self):
  rows=a.load('injuries-observed.json')['players'];self.assertEqual(len(rows),8)
  for p in rows:self.assertIsNone(p['injury']);self.assertIsNone(p['game_status'])
 def test_every_link_and_row(self):self.assertEqual(c.check()['status'],'PASS')
 def test_current_text_no_legacy_picks(self):
  text=(R/'index.html').read_text()
  self.assertNotIn('2 candidates',text);self.assertNotIn('luck-free',text)
if __name__=='__main__':unittest.main()
