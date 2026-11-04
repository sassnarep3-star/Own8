import json, math, unittest
from datetime import datetime,timezone
from pathlib import Path
from audit_math import all_pass,baseline,pearson,ranks,fresh,decimal_odds,expected_return,binary_joint,score_forecast,settle
R=Path(__file__).resolve().parent.parent
class MathTests(unittest.TestCase):
 def test_pearson(self):
  self.assertAlmostEqual(pearson([1,2,3],[3,2,1]),-1)
  self.assertIsNone(pearson([1,1,1],[1,2,3]))
  self.assertIsNone(pearson([1,2],[1,2]))
  self.assertIsNone(pearson([1,2,3],[1,2]))
  self.assertIsNone(pearson([1,2,math.nan],[1,2,3]))
 def test_rank_ties(self): self.assertEqual(ranks([10,10,30]),[1.5,1.5,3])
 def test_strict_gate(self):
  self.assertFalse(all_pass({})); self.assertTrue(all_pass({'G':{'status':'PASS'}}))
  for bad in ('CONDITIONAL','BLOCKED','FAIL','NOT_COMPUTABLE','',None): self.assertFalse(all_pass({'a':{'status':'PASS'},'b':{'status':bad}}))
 def test_sign(self):
  a={'W':1,'L':0,'T':0,'PF':10,'PA':30}; h={'W':1,'L':0,'T':0,'PF':30,'PA':10}
  r=baseline(a,h); self.assertEqual(r['home_margin'],20);self.assertEqual(r['home_handicap'],-20)
  self.assertEqual(baseline(h,a)['home_handicap'],20)
 def test_no_sample(self):
  with self.assertRaises(ValueError): baseline({'W':0,'L':0,'T':0,'PF':0,'PA':0},{})
 def test_freshness(self):
  now=datetime(2026,11,4,20,tzinfo=timezone.utc)
  self.assertTrue(fresh('2026-11-04T10:00:00Z',now))
  for t in ('2026-11-01T00:00:00Z','2026-11-05T00:00:00Z','2026-11-04','junk',None): self.assertFalse(fresh(t,now))
 def test_prices(self):
  self.assertAlmostEqual(decimal_odds(-110),1+100/110); self.assertEqual(decimal_odds(150),2.5)
  for x in (0,99,-99,math.nan,math.inf):
   with self.assertRaises(ValueError): decimal_odds(x)
 def test_ev(self):
  self.assertAlmostEqual(expected_return(.5,0,2),0)
  self.assertAlmostEqual(expected_return(.5,.1,2),.1)
  for args in ((.9,.2,2),(.5,0,1),(math.nan,0,2)):
   with self.assertRaises(ValueError): expected_return(*args)
 def test_joint(self):
  self.assertAlmostEqual(binary_joint(.5,.5,0),.25);self.assertAlmostEqual(binary_joint(.5,.5,1),.5)
  with self.assertRaises(ValueError): binary_joint(.9,.1,1)
  with self.assertRaises(ValueError): binary_joint(0,.5,0)
 def test_proper_score(self):
  self.assertAlmostEqual(score_forecast(.5,1)['brier'],.25)
  self.assertAlmostEqual(score_forecast(.5,0)['log_loss'],math.log(2))
  with self.assertRaises(ValueError): score_forecast(0,1)
 def test_settlement(self):
  self.assertEqual([settle(s,2) for s in ('win','loss','push','void')],[1,-1,0,0])
  with self.assertRaises(ValueError): settle('unknown',2)
class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.s=json.loads((R/'data/audit-snapshot.json').read_text())
 def test_teams(self):
  ts=self.s['standings'];self.assertEqual(len(ts),32);self.assertEqual(len({r['abbr'] for r in ts}),32)
  self.assertEqual(sum(r['PF'] for r in ts),sum(r['PA'] for r in ts));self.assertEqual(sum(r['W'] for r in ts),sum(r['L'] for r in ts))
  for r in ts:
   self.assertEqual(r['PF']-r['PA'],r['NET']);self.assertAlmostEqual((r['W']+.5*r['T'])/(r['W']+r['L']+r['T']),r['PCT'],delta=.00051)
 def test_schedule(self):
  games=self.s['schedule'];self.assertEqual(len(games),15)
  teams=[g[k] for g in games for k in ('away','home')];self.assertEqual(len(set(teams)),30)
  for g in games: self.assertIsNone(g['venue'])
 def test_score_blanks(self):
  for g in self.s['scores']:
   if g['status']!='VERIFIED': self.assertIsNone(g['away_score']);self.assertIsNone(g['home_score'])
 def test_injuries(self):
  self.assertEqual(len(self.s['injuries']),28)
  for r in self.s['injuries']: self.assertIsNone(r['game_status']);self.assertIsNone(r['injury'])
 def test_no_candidates(self):
  for g in json.loads((R/'analysis/model-lines-week9.json').read_text())['games']:
   self.assertFalse(g['candidate']);self.assertFalse(g['gates_all_pass']);self.assertIsNone(g['edge_pts'])
 def test_no_fabricated_rewards(self):
  for r in json.loads((R/'analysis/leaderboard.json').read_text())['standings']:
   for k in ('rank','realized_pts','roi','brier','reward_points'): self.assertIsNone(r[k])
 def test_inventory_blank(self):
  for r in json.loads((R/'analysis/audit-inventory.json').read_text())['rows']: self.assertIsNone(r['values'])
if __name__=='__main__': unittest.main()
