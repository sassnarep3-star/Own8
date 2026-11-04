"""Pure, tested research primitives. No betting recommendations or fitted claims."""
import math
from datetime import datetime, timezone
from statistics import mean


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in [*xs, *ys]):
        return None
    a, b = mean(xs), mean(ys)
    den = math.sqrt(sum((x-a)**2 for x in xs)*sum((y-b)**2 for y in ys))
    return sum((x-a)*(y-b) for x, y in zip(xs, ys))/den if den else None


def ranks(values):
    return [1 + sum(x < v for x in values) + (sum(x == v for x in values)-1)/2 for v in values]


def baseline(away, home):
    """Own8 B0 unadjusted scoring baseline. Home handicap = -expected margin.
    Zero venue adjustment is a DESIGN CHOICE, not a league estimate.
    No distribution fitted: no probabilities, moneyline, or prop fair lines.
    """
    def rate(t, key):
        n = t['W']+t['L']+t['T']
        if n <= 0:
            raise ValueError('No games')
        return t[key]/n
    a = (rate(away, 'PF')+rate(home, 'PA'))/2
    h = (rate(home, 'PF')+rate(away, 'PA'))/2
    return {'proj_away': round(a, 4), 'proj_home': round(h, 4),
            'home_margin': round(h-a, 4), 'home_handicap': round(a-h, 4), 'model_total': round(a+h, 4)}


def all_pass(gates):
    # Neither CONDITIONAL, missing values nor an empty set is a pass.
    return bool(gates) and all(g.get('status') == 'PASS' for g in gates.values())


def fresh(captured_at, now, max_age_hours=24):
    try:
        t=datetime.fromisoformat(captured_at.replace('Z','+00:00'))
        if t.tzinfo is None or now.tzinfo is None:
            return False
        return 0 <= (now-t).total_seconds() <= max_age_hours*3600
    except (ValueError, TypeError, AttributeError):
        return False


def decimal_odds(american):
    if not isinstance(american, (int,float)) or not math.isfinite(american) or abs(american)<100:
        raise ValueError('Invalid American odds')
    return 1+american/100 if american>0 else 1+100/abs(american)


def expected_return(p_win, p_push, price):
    if not all(isinstance(p, (int,float)) and math.isfinite(p) and 0<=p<=1 for p in (p_win,p_push)) or p_win+p_push>1:
        raise ValueError('Invalid probability mass')
    if not math.isfinite(price) or price<=1:
        raise ValueError('Invalid decimal price')
    return p_win*(price-1)-(1-p_win-p_push)


def binary_joint(pa,pb,r):
    """Two Bernoulli events only. Reject infeasible correlation, never clamp it.
    Not a multi-leg pricing model; requires verified event-specific estimates.
    """
    if not all(math.isfinite(x) for x in (pa,pb,r)) or not (0<pa<1 and 0<pb<1 and -1<=r<=1):
        raise ValueError('Invalid probabilities/correlation')
    p=pa*pb+r*math.sqrt(pa*(1-pa)*pb*(1-pb))
    if p < max(0,pa+pb-1)-1e-12 or p > min(pa,pb)+1e-12:
        raise ValueError('Infeasible Bernoulli joint probability')
    return p


def score_forecast(p, outcome):
    """Proper scoring rules, binary settled outcomes only. Pushes excluded."""
    if not math.isfinite(p) or not 0<p<1 or outcome not in (0,1):
        raise ValueError('Need non-degenerate forecast and binary outcome')
    return {'brier':(p-outcome)**2,'log_loss':-math.log(p if outcome else 1-p)}


def settle(outcome, price):
    if not math.isfinite(price) or price<=1 or outcome not in ('win','loss','push','void'):
        raise ValueError('Invalid settlement')
    return price-1 if outcome=='win' else -1 if outcome=='loss' else 0
