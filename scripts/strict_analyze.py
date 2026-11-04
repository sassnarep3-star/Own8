#!/usr/bin/env python3
"""Auditable descriptive analysis + small historical predictive benchmark. No wagers.
No packages/network required. Missing official inputs remain null. All-PASS is mandatory.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics as st

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'strict/evidence'
OUTPUT = ROOT / 'strict/results.json'
AS_OF = '2026-11-04'
BDB = 'https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/Data/games.csv'
STANDINGS = 'https://www.nfl.com/standings/'
NGS = 'https://nextgenstats.nfl.com/glossary'
NIST = 'https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm'


def load(name):
    return json.loads((EVIDENCE / name).read_text())


def pearson(x, y):
    if len(x) != len(y) or len(x) < 3:
        return None
    mx, my = st.mean(x), st.mean(y)
    den = math.sqrt(sum((i-mx)**2 for i in x)*sum((i-my)**2 for i in y))
    return sum((i-mx)*(j-my) for i,j in zip(x,y))/den if den else None


def all_pass(gates):
    return bool(gates) and all(g == 'PASS' for g in gates.values())


def expected_return(p_win, p_push, decimal_odds):
    """Expected net return per unit. Push returns stake; odds must be observed."""
    if any(v is None for v in (p_win, p_push, decimal_odds)):
        return None
    if not (0 <= p_win <= 1 and 0 <= p_push <= 1-p_win and decimal_odds > 1):
        raise ValueError('Invalid probability or decimal odds')
    return p_win * (decimal_odds-1) - (1-p_win-p_push)


def quote_from_scores(home, away):
    """Model mean margin, not a calibrated median or sportsbook quote."""
    return {'expected_home_margin':home-away, 'home_handicap_mean_proxy':away-home, 'expected_total':home+away}


def validate_evidence():
    manifest=load('manifest.json')
    for m in manifest:
        b=(ROOT/m['file']).read_bytes()
        if hashlib.sha256(b).hexdigest()!=m['sha256'] or len(b)!=m['bytes']:
            raise ValueError('Evidence digest mismatch: '+m['file'])
    return manifest


def historical_games():
    games=[]
    with (EVIDENCE/'games-2017.csv').open(newline='') as f:
        for rownum,g in enumerate(csv.DictReader(f),2):
            for key in ['season','week','HomeScore','VisitorScore']:
                g[key]=int(g[key])
            assert g['season']==2017 and 1<=g['week']<=6
            assert min(g['HomeScore'],g['VisitorScore'])>=0
            g['source_row']=rownum
            games.append(g)
    assert len(games)==len({g['gameId'] for g in games})==91
    return sorted(games,key=lambda g:(g['week'],g['gameId']))


def predict_from_prior(prior, home, away, neutral=False):
    """Research heuristic: team PF/PA shrink to prior league mean, k=4 pseudo-games.
    HFA estimated only on prior data. Neutral sites receive no HFA.
    No final scores from the current test week can enter the fit.
    """
    if not prior:
        return None
    avg=st.mean([g[k] for g in prior for k in ('HomeScore','VisitorScore')])
    hfa=st.mean(g['HomeScore']-g['VisitorScore'] for g in prior)
    def rates(team):
        scored=[]; allowed=[]
        for g in prior:
            if g['homeTeamAbbr']==team:
                scored.append(g['HomeScore']); allowed.append(g['VisitorScore'])
            elif g['visitorTeamAbbr']==team:
                scored.append(g['VisitorScore']); allowed.append(g['HomeScore'])
        return ((sum(scored)+4*avg)/(len(scored)+4),(sum(allowed)+4*avg)/(len(allowed)+4))
    hf,ha=rates(home); af,aa=rates(away)
    ph=(hf+aa)/2+(0 if neutral else hfa/2)
    pa=(af+ha)/2-(0 if neutral else hfa/2)
    return quote_from_scores(ph,pa)


def block_interval(rows, key, repetitions=4000):
    """Week-cluster percentile bootstrap; only 4 clusters, illustrative NOT validation."""
    weeks=sorted({r['week'] for r in rows})
    byweek={w:[r[key] for r in rows if r['week']==w] for w in weeks}
    rng=random.Random(20261104); vals=[]
    for _ in range(repetitions):
        sample=[v for w in rng.choices(weeks,k=len(weeks)) for v in byweek[w]]
        vals.append(st.mean(sample))
    vals.sort()
    return [vals[int(.025*repetitions)],vals[int(.975*repetitions)]]


def run():
    manifest=validate_evidence()
    teams=load('standings-observed.json')['teams']
    assert len({t['abbr'] for t in teams})==32
    for t in teams:
        assert t['NET']==t['PF']-t['PA']
        assert abs(t['PCT']-(t['W']+.5*t['T'])/(t['W']+t['L']+t['T']))<=.00051
    gp=lambda t:t['W']+t['L']+t['T']
    correlations=[]
    for name,x,y in [
        ('Net points/game vs win fraction',[t['NET']/gp(t) for t in teams],[(t['W']+.5*t['T'])/gp(t) for t in teams]),
        ('Points for/game vs points allowed/game',[t['PF']/gp(t) for t in teams],[t['PA']/gp(t) for t in teams])]:
        correlations.append({'pair':name,'r':pearson(x,y),'n':32,'unit':'team season-to-date','status':'DERIVED DESCRIPTIVE ONLY','source_url':STANDINGS,'limitation':'Shared opponents and outcomes; cross-sectional association, not causality, future skill, or bet-leg dependence. No independent-sample CI asserted.'})
    games=historical_games()
    correlations.append({'pair':'Home score vs visitor score','r':pearson([g['HomeScore'] for g in games],[g['VisitorScore'] for g in games]),'n':len(games),'unit':'game, 2017 weeks 1–6','status':'DERIVED DESCRIPTIVE ONLY','source_url':BDB,'limitation':'Repeated teams, old short sample. Score correlation is not cover/over or prop-over correlation.'})
    for name in ['QB passing over + WR receiving over','RB rushing over + team win','Favorite cover + game over','Cross-game two-leg parlay']:
        correlations.append({'pair':name,'r':None,'n':None,'unit':'settled bet indicators','status':'UNVERIFIED — BLOCKED','source_url':NGS if 'QB' in name or 'RB' in name else BDB,'limitation':'No official matched player-game thresholds/quotes/settlement sample. Source is scope context only; it supplies no correlation.'})
    predictions=[]
    for g in games:
        if g['week']<3: continue
        prior=[p for p in games if p['week']<g['week']]
        p=predict_from_prior(prior,g['homeTeamAbbr'],g['visitorTeamAbbr'])
        actual_m=g['HomeScore']-g['VisitorScore']; actual_t=g['HomeScore']+g['VisitorScore']
        bm=st.mean(x['HomeScore']-x['VisitorScore'] for x in prior)
        bt=st.mean(x['HomeScore']+x['VisitorScore'] for x in prior)
        predictions.append({'game_id':g['gameId'],'week':g['week'],'train_max_week':max(x['week'] for x in prior),'away':g['visitorTeamAbbr'],'home':g['homeTeamAbbr'],**p,'actual_margin':actual_m,'actual_total':actual_t,'margin_absolute_error':abs(p['expected_home_margin']-actual_m),'total_absolute_error':abs(p['expected_total']-actual_t),'baseline_margin_error':abs(bm-actual_m),'baseline_total_error':abs(bt-actual_t),'margin_improvement':abs(bm-actual_m)-abs(p['expected_home_margin']-actual_m),'total_improvement':abs(bt-actual_t)-abs(p['expected_total']-actual_t),'source_row':g['source_row'],'source_url':BDB,'status':'RETROSPECTIVE DEVELOPMENT BENCHMARK'})
    benchmarks=[]
    for target in ['margin','total']:
        benchmarks.append({'target':target,'n':len(predictions),'model_mae':st.mean(x[target+'_absolute_error'] for x in predictions),'baseline_mae':st.mean(x['baseline_'+target+'_error'] for x in predictions),'mae_improvement':st.mean(x[target+'_improvement'] for x in predictions),'illustrative_95_interval':block_interval(predictions,target+'_improvement'),'source_url':BDB,'status':'NOT SKILL VALIDATED — 4 test-week clusters, 1 partial season; selected retrospectively'})
    # All live values requiring missing primary quotes / calibrated model remain null.
    current=[]
    for g in load('schedule-observed.json')['games']:
        current.append({**g,'fair_home_spread':None,'fair_total':None,'fair_moneyline':None,'market_home_spread':None,'market_total':None,'decimal_odds':None,'edge':None,'candidate':False,'status':'BLOCKED — no calibrated current model / official price archive'})
    gates=[
        ('G1','Provenance','Observed official inputs, immutable snapshot, hashes, row-level source and capture time. Never equate a domain with verification.','PARTIAL',BDB),
        ('G2','As-of / leakage','All features and quotes available before locked prediction cutoff; train_max_week < test_week.','PARTIAL',BDB),
        ('G3','Availability','Fresh official game-status report and confirmed role; blanks are unknown, DNP is not out.','BLOCKED','https://www.nfl.com/injuries/league/2026/reg9'),
        ('G4','Calibration','Nested rolling-origin seasons; compare score distribution, Brier/log loss, MAE and calibration to frozen baselines.','BLOCKED',BDB),
        ('G5','Sample / stability','Project policy: ≥3 completed held-out seasons, ≥30 game-week clusters and ≥500 settled singles; props/combinations need their own powered sample. Not a universal statistical guarantee.','BLOCKED',NIST),
        ('G6','Executable prices','Primary bookmaker quote, timestamp, rules, decimal odds, limits, availability and closing price; no assumed -110.','BLOCKED','https://wsgc.wa.gov/tribal-partnerships/sports-wagering'),
        ('G7','Dependence','Estimate conditional bet-indicator dependence out of sample; joint model and held-out calibration required for all combos. No team-level proxies.','BLOCKED',NGS),
        ('G8','Skill / multiplicity','Pre-register strategy/version; week/season-block resampling, adjusted tests across all tried variants; positive lower bounds on net return and proper-score improvement. CLV corroborates, never proves skill.','BLOCKED',NIST),
        ('G9','Risk / prospective lock','Paper only; aggregate game/team/player exposures, reserve untouched forward season; unknown inputs or any non-PASS → no promotion.','PASS',NIST)]
    gate_rows=[dict(zip(['id','gate','rule','status','source_url'],g),source_scope='Official context / input availability. Thresholds and decision rules are Own8 proposals, not NFL or NIST requirements.') for g in gates]
    proposals=[
        ('S01','Single','Shrunk team efficiency spread','Estimate opponent-adjusted offense/defense and home/neutral effects; regress unstable conversion and turnover components.','Team game scores and pregame features, long official history.',BDB),
        ('S02','Single','Pace × efficiency total','Drive count and scoring distributions; separate weather, venue and overtime regimes.','Official play/drive history, timestamps, forecasts available at cutoff.',BDB),
        ('S03','Single','Calibrated moneyline','Fit joint score distribution; sum win/tie probabilities, use actual settlement rules.','Out-of-sample score distributions, observed primary quotes.',BDB),
        ('S04','Single','NGS completion residual','Shrink completion above expectation; test incremental held-out proper-score improvement, not raw season record.','Official game-level xCOMP, attempts, availability and exposure.',NGS),
        ('S05','Player prop','QB passing workload','Model dropbacks → attempts → completions → yardage; account for sacks, injury and role uncertainty.','Official player-game workload and primary prop history.',NGS),
        ('S06','Player prop','Receiver target-share shrinkage','Hierarchical route/target shares and distribution of depth/YAC; avoid top-25 survivor sample.','Complete player-game targets, routes and role histories.',NGS),
        ('S07','Player prop','RB rushing role model','Carries × yards distribution with game-script uncertainty and correlated volume.','Official carries, participation, injury reports and primary quotes.',NGS),
        ('S08','Parlay','Cross-game pair','Join calibrated joint outcomes, test shared-week/team factors; never assume independence because games differ.','Synchronized primary leg quotes, payouts and outcomes.',BDB),
        ('S09','Same-game parlay','Side + total','Simulate joint home/away scores; evaluate cover/over indicators at actual quoted thresholds.','Calibrated joint score distribution and primary SGP payouts.',BDB),
        ('S10','Player combo','QB + receiver overs','Shared play-level opportunities and yardage allocation; evaluate joint exceedance, not raw-yard correlation.','Matched player-game observations and primary combo payout.',NGS),
        ('S11','Player combo','RB + receiver / opponent pair','Model pace and game-script mixtures, test injury scenarios and joint-tail risk.','Complete matched player-game observations and exact settlement rules.',NGS)]
    strategies=[]
    for i,cat,name,hyp,req,src in proposals:
        states={g['id']:g['status'] for g in gate_rows}
        strategies.append({'id':i,'category':cat,'name':name,'hypothesis':hyp,'required_inputs':req,'source_url':src,'source_scope':'Official definitions/data context, not endorsement or verified predictive edge.','status':'PROPOSED — NOT VALIDATED','gates':states,'qualified':all_pass(states),'rank':None,'reward_points':None,'roi':None,'clv':None,'skill_score':None})
    result={'as_of':AS_OF,'policy':'Facts observed / derived descriptive / proposed / unverified are separate. No strategy can eliminate chance.','manifest':manifest,'standings':teams,'games':games,'current_lines':current,'correlations':correlations,'historical_predictions':predictions,'benchmarks':benchmarks,'gates':gate_rows,'strategies':strategies,'qualified_strategies':sum(s['qualified'] for s in strategies),'rewards_awarded':0,'real_money_wagers':0}
    OUTPUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(f'Official historical games: {len(games)}; held-out-week predictions: {len(predictions)}; qualified strategies: 0')
    return result

if __name__=='__main__':run()
