"""Deterministic snapshot analysis. Does not fetch data or certify predictive skill."""
import hashlib,json
from pathlib import Path
from engine import GATES,baseline_line,eligible,pearson
R=Path(__file__).resolve().parents[1]
def load(p): return json.loads((R/p).read_text())
def save(p,v): (R/p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
stand=load('data/verified/standings.json')['rows']; sched=load('data/verified/schedule.json')['rows']
assert len(stand)==32 and len({t['abbr'] for t in stand})==32
for t in stand:
    g=t['W']+t['L']+t['T']
    assert t['PF']-t['PA']==t['NET'] and abs(t['PCT']-(t['W']+.5*t['T'])/g)<.00051
teams={t['abbr']:t for t in stand}
def col(k):
    return [t['NET']/(t['W']+t['L']+t['T']) if k=='margin' else (t['W']+.5*t['T'])/(t['W']+t['L']+t['T']) if k=='winpct' else t[k]/(t['W']+t['L']+t['T']) for t in stand]
corr=[dict(pair=label,r=round(pearson(col(a),col(b)),6),n=32,unit='teams, one snapshot',method='Pearson',kind='descriptive only',source_url='https://www.nfl.com/standings/') for label,a,b in [('Net points/game vs win fraction','margin','winpct'),('Points for/game vs win fraction','PF','winpct'),('Points against/game vs win fraction','PA','winpct')]]
corr += [dict(pair=p,r=None,n=None,unit='held-out game/player pairs unavailable',method='not estimable',kind='BLOCKED',source_url='https://nextgenstats.nfl.com/glossary') for p in ['QB passing over + receiver yards over','RB rushing over + QB passing under','Different-game parlay leg hits']]
strategies=[]
plans=[('S1','Regularized margin','Single spread','Opponent-adjusted scoring margin','NFL-S'),('S2','Joint score / pace','Single total','Pace and drive efficiency distribution','NFL-S'),('S3','QB volume × efficiency','Player passing','Attempts, yards/attempt and CPOE','NGS-G'),('S4','RB role × efficiency','Player rushing','Verified carries and role uncertainty','NGS-G'),('S5','Target-share receiving','Player receiving','Targets, catch probability and xYAC','NGS-G'),('S6','Cross-game joint value','Parlay','Calibrated joint probability and actual combo quote','NIST'),('S7','Coherent game-script simulation','Player-prop combo','Shared targets, yards, score-state and binary hits','NGS-G'),('S8','Regression / feature ablation','Research control','Shrink extremes and test incremental forward skill','NIST')]
sources={s['id']:s for s in load('data/verified/sources.json')}
for sid,name,kind,signal,src in plans:
    gates={g:'NOT_EVALUATED' for g in GATES}
    gates['provenance']='BLOCKED' # partial aggregate snapshot is not all required inputs
    gates['price']='BLOCKED'
    strategies.append(dict(id=sid,name=name,type=kind,hypothesis=signal,status='BLOCKED — research only',gates=gates,eligible=eligible(gates),rank=None,roi=None,skill_score=None,reward=None,n_settled_games=None,source_url=sources[src]['url']))
lines=[]
for g in sched:
    x=baseline_line(teams[g['away']],teams[g['home']],g['neutral'])
    lines.append({**g,**x,'model_version':'untrained-margin-shrink8-hfa0-v1','market_home_handicap':None,'decimal_price':None,'p_win':None,'joint_probability':None,'ev':None,'selection':None,'eligible':False,'status':'BLOCKED — no trained distribution, verified quote or current availability'})
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'data/verified').glob('*.json'))}
manifest.update({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'data/evidence').glob('*'))})
save('analysis/input-manifest.json',manifest)
save('analysis/dashboard.json',dict(as_of='2026-11-04',correlations=corr,strategies=strategies,lines=lines,eligible_count=sum(s['eligible'] for s in strategies),settled_ledger_count=0,policy='All numeric model outputs are project calculations, never official fair prices. Missing values null, never zero.'))
print(f'Analyzed {len(stand)} verified team rows; {len(lines)} experimental lines; 0 eligible strategies; no graded ledger.')
# Compatibility projections for inherited audit tests. No synthetic results/ranks.
save('analysis/model-lines-week9.json',{'games':[dict(game=g['away']+' at '+g['home'],candidate=False,gates_all_pass=False,edge_pts=None,market_spread_home=None,source_url=g['source_url']) for g in lines]})
save('analysis/leaderboard.json',{'standings':[dict(strategy_id=s['id'],rank=None,realized_pts=None,roi=None,brier=None,reward_points=None,status=s['status']) for s in strategies]})
