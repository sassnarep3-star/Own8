import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from engine import *
class EngineTests(unittest.TestCase):
    def test_fail_closed(self):
        g={k:'PASS' for k in GATES}; self.assertTrue(eligible(g))
        for v in ['CONDITIONAL','NOT_EVALUATED',None,'FAIL','UNVERIFIED']:
            self.assertFalse(eligible({**g,'availability':v}))
        g.pop('price'); self.assertFalse(eligible(g)); self.assertFalse(eligible({}))
    def test_odds(self):
        self.assertAlmostEqual(decimal_odds(-110),1+100/110); self.assertEqual(decimal_odds(150),2.5)
        self.assertAlmostEqual(sum(devig([1.91,1.91])),1)
        for x in [0,99,float('nan')]:
            with self.assertRaises(ValueError): decimal_odds(x)
    def test_ev(self):
        self.assertAlmostEqual(expected_return(.55,.05,2),.15)
        self.assertAlmostEqual(expected_return(.5,0,2),0)
        with self.assertRaises(ValueError): expected_return(.8,.3,2)
    def test_joint(self):
        self.assertEqual(joint_two(.5,.5,0),.25)
        self.assertEqual(joint_two(.5,.5,1),.5)
        self.assertEqual(joint_two(.5,.5,-1),0)
        with self.assertRaises(ValueError): joint_two(.9,.9,-1)
        with self.assertRaises(ValueError): joint_two(float('nan'),.5,0)
    def test_settlement(self):
        self.assertEqual([settle(o,2.5) for o in ('win','loss','push','void')],[1.5,-1,0,0])
        self.assertEqual(spread_result(24,21,-3),'push')
        self.assertEqual(spread_result(24,21,-2.5),'win')
        self.assertEqual(spread_result(24,21,-3.5),'loss')
    def test_sign_and_neutral(self):
        a=dict(W=4,L=4,T=0,NET=0,PF=160,PA=160)
        h=dict(W=6,L=2,T=0,NET=80,PF=240,PA=160)
        self.assertEqual(baseline_line(a,h)['home_handicap'],-5)
        self.assertEqual(baseline_line(a,h,True,hfa=3)['home_handicap'],-5)
        self.assertEqual(baseline_line(a,h,False,hfa=3)['home_handicap'],-8)
    def test_correlation_pairs(self):
        self.assertEqual(pearson([1,2,3],[2,4,6]),1)
        self.assertIsNone(pearson([1,1,1],[1,2,3]))
        self.assertIsNone(pearson([1,2],[2,3]))
        with self.assertRaises(ValueError): pearson([1,2,3],[2,3])
        with self.assertRaises(ValueError): pearson([1,float('nan'),3],[2,3,4])
    def test_asof(self):
        self.assertTrue(validate_asof('2026-11-04T10:00Z','2026-11-04T11:00Z','2026-11-05T10:00Z'))
        self.assertFalse(validate_asof('2026-11-06T10:00Z','2026-11-04T11:00Z','2026-11-05T10:00Z'))
        with self.assertRaises(ValueError): validate_asof('2026-11-04','2026-11-05','2026-11-06')
    def test_walkforward(self):
        r=[dict(week=1,game_id='a'),dict(week=2,game_id='b'),dict(week=2,game_id='b')]
        a,b=walk_forward(r,2); self.assertEqual(len(a),1); self.assertEqual(len(b),2)
        with self.assertRaises(ValueError): walk_forward(r+[dict(week=1,game_id='b')],2)
    def test_brier(self):
        self.assertEqual(brier([1,0],[1,0]),0); self.assertEqual(brier([.5,.5],[1,0]),.25)
        with self.assertRaises(ValueError): brier([],[])
    def test_uncertainty(self):
        self.assertIsNone(cluster_interval([1]))
        self.assertEqual(cluster_interval([0,0]),[0,0])
        self.assertEqual(cluster_interval([1,2,3]),cluster_interval([1,2,3]))
    def test_multiple_testing(self):
        self.assertEqual(holm([.001,.02,.2]),[True,True,False])
        self.assertEqual(holm([.04,.04]),[False,False])
        self.assertEqual(holm([]),[])
if __name__=='__main__': unittest.main()
