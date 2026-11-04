"""Research primitives. All examples/tests are synthetic, never evidence of NFL skill."""
import math
import random
import statistics
from datetime import datetime

GATES = ('provenance', 'asof', 'availability', 'history', 'holdout', 'calibration',
         'multiple_testing', 'price', 'joint_distribution', 'risk', 'preregistered')

def eligible(gates):
    """Missing, conditional, stale, or unverified gates cannot pass."""
    return set(gates) == set(GATES) and all(v == 'PASS' for v in gates.values())

def pearson(x, y):
    if len(x) != len(y):
        raise ValueError('paired vectors must have equal length')
    if len(x) < 3:
        return None
    if not all(isinstance(v, (int,float)) and math.isfinite(v) for v in x+y):
        raise ValueError('finite complete pairs required')
    mx, my = statistics.mean(x), statistics.mean(y)
    a, b = sum((v-mx)**2 for v in x), sum((v-my)**2 for v in y)
    return sum((u-mx)*(v-my) for u,v in zip(x,y))/math.sqrt(a*b) if a*b else None

def decimal_odds(american):
    if not math.isfinite(american) or abs(american) < 100:
        raise ValueError('American odds must have magnitude >= 100')
    return 1 + (american/100 if american > 0 else 100/abs(american))

def devig(decimal_prices):
    if len(decimal_prices) < 2 or any(not math.isfinite(d) or d <= 1 for d in decimal_prices):
        raise ValueError('need a complete mutually exclusive price market')
    q = [1/d for d in decimal_prices]
    return [p/sum(q) for p in q]

def expected_return(p_win, p_push, decimal_price):
    if not all(math.isfinite(v) for v in (p_win,p_push,decimal_price)) or min(p_win,p_push)<0 or p_win+p_push>1 or decimal_price<=1:
        raise ValueError('invalid probability or price')
    return p_win*(decimal_price-1) - (1-p_win-p_push)

def joint_two(p, q, rho):
    if not all(math.isfinite(v) for v in (p,q,rho)) or not 0<=p<=1 or not 0<=q<=1 or not -1<=rho<=1:
        raise ValueError('invalid joint parameters')
    joint = p*q + rho*math.sqrt(p*(1-p)*q*(1-q))
    if joint < max(0,p+q-1)-1e-12 or joint > min(p,q)+1e-12:
        raise ValueError('infeasible Bernoulli correlation')
    return max(0,min(1,joint))

def settle(outcome, decimal_price, stake=1):
    if outcome not in ('win','loss','push','void') or not math.isfinite(decimal_price) or decimal_price<=1 or not math.isfinite(stake) or stake<0:
        raise ValueError('invalid settlement')
    return stake*(decimal_price-1) if outcome=='win' else -stake if outcome=='loss' else 0

def spread_result(home_score, away_score, home_handicap):
    adjusted = home_score-away_score+home_handicap
    return 'win' if adjusted>0 else 'loss' if adjusted<0 else 'push'

def baseline_line(away, home, neutral=False, hfa=0, prior_games=8):
    """Project design, not a trained model. Negative handicap means home favored.
    A verified neutral game ALWAYS overrides a nonzero home advantage.
    """
    def strength(t):
        gp=t['W']+t['L']+t['T']
        return t['NET']/(gp+prior_games)
    advantage=strength(home)-strength(away)+(0 if neutral else hfa)
    total=(away['PF']/(away['W']+away['L']+away['T'])+home['PA']/(home['W']+home['L']+home['T'])+home['PF']/(home['W']+home['L']+home['T'])+away['PA']/(away['W']+away['L']+away['T']))/2
    return {'home_handicap':round(-advantage,2),'total':round(total,2)}

def validate_asof(feature_time, prediction_time, kickoff_time):
    times=[datetime.fromisoformat(x.replace('Z','+00:00')) for x in (feature_time,prediction_time,kickoff_time)]
    if any(t.tzinfo is None for t in times):
        raise ValueError('timezone-aware timestamps required')
    return times[0] <= times[1] < times[2]

def walk_forward(records, test_week):
    """All records in a game/week stay in a single split. No shuffled rows."""
    train=[r for r in records if r['week']<test_week]
    test=[r for r in records if r['week']==test_week]
    if {r['game_id'] for r in train}&{r['game_id'] for r in test}:
        raise ValueError('game leaks across folds')
    return train,test

def brier(probabilities, outcomes):
    if len(probabilities)!=len(outcomes) or not probabilities or any(not math.isfinite(p) or not 0<=p<=1 for p in probabilities) or any(y not in (0,1) for y in outcomes):
        raise ValueError('invalid complete probability/outcome pairs')
    return statistics.mean((p-y)**2 for p,y in zip(probabilities,outcomes))

def cluster_interval(block_means, seed=566, repetitions=2000):
    """Percentile bootstrap of equal-weight game-block means (design choice).
    Only appropriate after defining independent blocks. Not a proof of skill.
    """
    if len(block_means)<2:
        return None
    if repetitions<100 or any(not math.isfinite(x) for x in block_means):
        raise ValueError('invalid bootstrap sample')
    rng=random.Random(seed)
    draws=sorted(statistics.mean(rng.choices(block_means,k=len(block_means))) for _ in range(repetitions))
    return [draws[int(.025*(repetitions-1))],draws[int(.975*(repetitions-1))]]

def holm(p_values, alpha=.05):
    """Family-wise multiple-testing gate over ALL registered experiments."""
    if any(not math.isfinite(p) or not 0<=p<=1 for p in p_values) or not 0<alpha<1:
        raise ValueError('invalid p values')
    passed=[False]*len(p_values)
    for i,j in enumerate(sorted(range(len(p_values)),key=p_values.__getitem__)):
        if p_values[j] > alpha/(len(p_values)-i):
            break
        passed[j]=True
    return passed
