#!/usr/bin/env python3
"""Small, dependency-free statistics used by the market workspace.

Everything here is a standard, citable estimator. Nothing is tuned on the data it
scores: the bootstrap returns a percentile interval, the sign-flip test is the usual
randomisation test for a paired mean difference, and the multiple-testing correction
is Holm's step-down procedure (NIST/SEMATECH e-Handbook 7.4.7.3).

References (all re-read 2026-11-14):
  https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm   Bonferroni / Holm family
  https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm    confidence intervals
  https://www.itl.nist.gov/div898/handbook/prc/section2/prc231.htm   CI for a standard deviation
"""
import math
import random

Z95 = 1.959963984540054


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def stdev(xs):
    n = len(xs)
    if n < 2:
        return None
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def american_to_decimal(ml):
    """Convert an American moneyline price to a decimal (total-return) multiplier."""
    if ml is None:
        return None
    if ml > 0:
        return 1.0 + ml / 100.0
    return 1.0 + 100.0 / abs(ml)


def american_to_implied(ml):
    """Raw implied probability. Two-way prices with vig sum to > 1 by construction."""
    if ml is None:
        return None
    if ml > 0:
        return 100.0 / (ml + 100.0)
    return abs(ml) / (abs(ml) + 100.0)


def pair_devig(p_away, p_home):
    """Multiplicative two-way de-vig: normalise the raw implied pair to sum to 1.

    This is the simplest standard bookmaker-margin removal. It is stated as an
    assumption, not a fact: it assumes the margin is applied proportionally, which
    is not guaranteed for an actual book.
    """
    if p_away is None or p_home is None:
        return None, None
    s = p_away + p_home
    if s <= 0:
        return None, None
    return p_away / s, p_home / s


def brier(p, y):
    return (p - y) ** 2


def log_loss(p, y, eps=1e-12):
    p = min(max(p, eps), 1 - eps)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def bootstrap_ci(diffs, reps=10000, seed=20261114):
    """Percentile bootstrap CI of the mean of a paired difference vector.

    diffs[i] must be a paired quantity (model loss minus baseline loss for the SAME
    observation). Resampling is over observations, so dependence between the two
    arms is preserved.
    """
    if not diffs:
        return None, None
    rng = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(reps):
        means.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int(0.025 * reps)]
    hi = means[int(0.975 * reps) - 1]
    return lo, hi


def signflip_p(diffs, reps=10000, seed=20261114):
    """One-sided randomisation p-value for H1: mean(diffs) < 0.

    Under the null the sign of each paired difference is exchangeable, so the
    reference distribution is built by flipping signs at random. Reported as
    (1 + #{stat <= observed}) / (reps + 1) so the p-value is never exactly zero.
    """
    if not diffs:
        return None
    obs = mean(diffs)
    rng = random.Random(seed)
    n = len(diffs)
    hits = 0
    for _ in range(reps):
        s = sum(d if rng.random() < 0.5 else -d for d in diffs) / n
        if s <= obs:
            hits += 1
    return (hits + 1) / (reps + 1)


def holm(pvals):
    """Holm step-down adjusted p-values, order preserved.

    p_adj(i) = max over j<=i of min(1, (m - j + 1) * p_sorted(j)).
    """
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [None] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj


def wilson(k, n):
    """Wilson score interval for a binomial proportion (better than normal at small n)."""
    if n == 0:
        return None, None
    p = k / n
    d = 1 + Z95 ** 2 / n
    centre = (p + Z95 ** 2 / (2 * n)) / d
    half = (Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n))) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n):
    """Fisher z interval for a Pearson correlation. n is the number of rows."""
    if r is None or n is None or n < 4:
        return None, None
    if abs(r) >= 1:
        return None, None
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3)
    lo, hi = z - Z95 * se, z + Z95 * se
    return math.tanh(lo), math.tanh(hi)


def r2_perm_p(xs, ys, reps=5000, seed=20261114):
    """Permutation p-value for H1: r != 0 (two-sided, by shuffling ys)."""
    obs = pearson(xs, ys)
    if obs is None:
        return None
    rng = random.Random(seed)
    ys_shuffled = list(ys)
    hits = 0
    for _ in range(reps):
        rng.shuffle(ys_shuffled)
        r = pearson(xs, ys_shuffled)
        if r is not None and abs(r) >= abs(obs):
            hits += 1
    return (hits + 1) / (reps + 1)


def kl_binomial(p, q, n):
    """KL divergence in bits between a Bernoulli(p) model and Bernoulli(q) truth."""
    def h(x):
        if x <= 0 or x >= 1:
            return 0.0
        return -x * math.log2(x) - (1 - x) * math.log2(1 - x)
    return n * (h(p) - h(q))
