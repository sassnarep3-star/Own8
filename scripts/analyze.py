#!/usr/bin/env python3
"""Fail-closed audit pipeline. Only data/audit-snapshot.json enters calculations.
Derived values are project research, NOT official published lines or proven skill.
"""
import json
from pathlib import Path
from audit_math import baseline, pearson, ranks, all_pass
ROOT=Path(__file__).resolve().parent.parent
D=ROOT/'data'; OUT=ROOT/'analysis'; OUT.mkdir(exist_ok=True)
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
snap=json.loads((D/'audit-snapshot.json').read_text())
team={r['abbr']:r for r in snap['standings'] if r['status']=='VERIFIED'}
gates={
 'G1':dict(status='PASS',rule='Verified snapshot inputs, field-level sources; third-party prices excluded.'),
 'G2':dict(status='BLOCKED',rule='Timestamped pre-kickoff inputs and prices, with complete as-of history. Current capture dates alone do not establish availability at each past decision.'),
 'G3':dict(status='BLOCKED',rule='Chronological training / validation / untouched test; no in-sample standings used to prove predictive skill.'),
 'G4':dict(status='BLOCKED',rule='Current final injuries, active roster and usage; No Injuries Reported is not clearance.'),
 'G5':dict(status='BLOCKED',rule='Operator-native timestamped line, price, settlement and void rules. No assumed -110 pricing.'),
 'G6':dict(status='BLOCKED',rule='Out-of-sample calibrated probabilities; aligned outcomes and joint distribution for combos. Team correlations cannot price bets.'),
 'G7':dict(status='BLOCKED',rule='Positive conservative net EV after costs and pushes, robust across seasons; pre-registered family-wide uncertainty adjustment.'),
 'G8':dict(status='BLOCKED',rule='Prospective immutable paper ledger, exposure caps, drawdown stress tests. No rewards before every applicable gate passes.')}
games=[]
for g in snap['schedule']:
 calc=baseline(team[g['away']],team[g['home']])
 games.append({**g,**calc,'game':f"{g['away']} at {g['home']}",'classification':'DERIVED — B0 UNVALIDATED',
  'market_spread_home':None,'market_price':None,'edge_pts':None,'win_probability':None,'moneyline':None,
  'candidate':False,'candidate_side':None,'gates_all_pass':all_pass(gates),'gates':gates,
  'inputs_source_url':'https://www.nfl.com/standings/'})
save('model-lines-week9.json',dict(as_of=snap['as_of'],method='B0: away=(away PF/GP + home PA/GP)/2; home=(home PF/GP + away PA/GP)/2. No fitted venue adjustment (zero by design). Home handicap=away projection-home projection. No opponent, roster or uncertainty calibration. Illustrative benchmark only; not betting fair value.',games=games))
vals=list(team.values()); pct=[(t['W']+.5*t['T'])/(t['W']+t['L']+t['T']) for t in vals]
net=[t['NET']/(t['W']+t['L']+t['T']) for t in vals]; pf=[t['PF']/(t['W']+t['L']+t['T']) for t in vals]
cs=[dict(pair='Net points/game vs win fraction',type='Pearson',r=round(pearson(net,pct),6)),dict(pair='Net points/game rank vs win fraction rank',type='Spearman (average ties)',r=round(pearson(ranks(net),ranks(pct)),6)),dict(pair='Points for/game vs win fraction',type='Pearson',r=round(pearson(pf,pct),6))]
for c in cs: c.update(n=32,confidence_interval=None,classification='DERIVED — DESCRIPTIVE',source_url='https://www.nfl.com/standings/',interpretation='Cross-sectional team aggregates sharing game outcomes. Not independent game observations, not causality, not forward skill or leg correlation. No IID confidence interval asserted.')
for pair in ['QB passing over × receiver yards over','QB passing over × team total over','RB rushing over × QB passing under','Cross-game parlay outcomes']:
 cs.append(dict(pair=pair,type='Bernoulli leg dependence',r=None,n=None,confidence_interval=None,classification='UNVERIFIED',source_url='https://www.nfl.com/scores/',interpretation='Missing timestamp-aligned paired outcomes and market thresholds. Blocked; no independence assumption. Official reference is a retrieval target, not evidence for a value.'))
save('correlations.json',dict(as_of=snap['as_of'],method='Team descriptive statistics only. Game-level correlations left null.',correlations=cs))
spec=[('S1','Single: spread baseline','Single','B0 scoring means as a benchmark; test opponent-adjusted and shrinkage alternatives chronologically.','https://www.nfl.com/standings/'),('S2','Single: total / pace','Single','Research opponent-adjusted pace, drive efficiency and red-zone residuals; avoid fitting on future totals.','https://www.nfl.com/stats/team-stats/'),('S3','Single: moneyline calibration','Single','Fit a discrete margin distribution on past games; account for ties. A mean margin alone is not a win probability.','https://www.nfl.com/scores/'),('S4','Player: QB efficiency','Player prop','Test lagged completion percentage above expectation and intended air yards with dropback volume.','https://nextgenstats.nfl.com/glossary'),('S5','Player: receiver opportunity','Player prop','Test lagged target share, routes and air-yards share with verified active status. Routes/targets not verified in this audit.','https://nextgenstats.nfl.com/glossary'),('S6','Player: RB workload','Player prop','Test lagged carries, snap share and box counts; availability and game script uncertainty are mandatory.','https://nextgenstats.nfl.com/glossary'),('S7','Cross-game joint value','Parlay','Use calibrated joint outcomes, not an automatic product. Demand operator combo price and common-shock stress tests.','https://www.nfl.com/scores/'),('S8','Same-game QB + receiver','Player-prop combo','Jointly simulate attempts, completions and target allocation. Pairwise correlation alone cannot identify 3+ leg dependence.','https://nextgenstats.nfl.com/glossary')]
strats=[dict(id=i,name=n,type=t,description=d,status='BLOCKED — research only',gates=gates,source_url=u) for i,n,t,d,u in spec]
save('strategies.json',dict(as_of=snap['as_of'],strategies=strats))
save('leaderboard.json',dict(as_of=snap['as_of'],note='No eligible strategies, no verified prospective forecasts or settled paper ledger. Unobserved performance is null, not zero. No ranks, tiers or rewards awarded.',scoring='Proposed: reward 100 * positive family-adjusted lower bound of paired mean Brier improvement over a pre-registered baseline, only after all gates PASS. Use week/game blocks and a frozen trial count; no ROI-only ranking. No skill or luck-free claim.',standings=[dict(strategy_id=s['id'],name=s['name'],type=s['type'],rank=None,realized_pts=None,roi=None,brier=None,reward_points=None,status=s['status'],source_url=s['source_url']) for s in strats]))
save('prop-signals-week9.json',dict(as_of=snap['as_of'],method='No verified player game-log / active-status / event-distribution history: all prop fair lines and probabilities withheld.',signals=[dict(game=g['game'],market_prop_line=None,qb_proj_pass_yds=None,correlation=None,status='UNVERIFIED — BLOCKED',source_url=g['source_url']) for g in games]))
save('validation-gates.json',dict(as_of=snap['as_of'],gates=gates,eligible_strategies=0,candidates=0))
print(f"Audited analysis: {len(games)} B0 benchmarks; {len(cs)} correlation rows; 0 eligible strategies; 0 candidates.")
