"""Small, dependency-free statistics toolkit used by model.py (session 4bc92a5f).

Everything here is deterministic given the seed; no external packages are required.
"""
import math
import random

SEED = 20261104  # fixed seed so every published number is reproducible


# ---------------------------------------------------------------- linear algebra
def solve(A, b):
    """Solve A x = b (A square) by Gaussian elimination with partial pivoting."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            raise ValueError("singular matrix")
        M[c], M[p] = M[p], M[c]
        piv = M[c][c]
        for r in range(c + 1, n):
            f = M[r][c] / piv
            if f:
                Mr, Mc = M[r], M[c]
                for k in range(c, n + 1):
                    Mr[k] -= f * Mc[k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = M[r][n] - sum(M[r][k] * x[k] for k in range(r + 1, n))
        x[r] = s / M[r][r]
    return x


def inverse(A):
    n = len(A)
    cols = [solve(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def ridge(X, y, penalized, lam):
    """Ridge regression with a per-coefficient penalty mask.

    Returns (beta, hat_diag) where hat_diag[i] = H_ii of the hat matrix X (X'X + lam*D)^-1 X'.
    """
    p = len(X[0])
    XtX = [[0.0] * p for _ in range(p)]
    Xty = [0.0] * p
    for xi, yi in zip(X, y):
        nz = [(j, v) for j, v in enumerate(xi) if v]
        for j, v in nz:
            Xty[j] += v * yi
            row = XtX[j]
            for k, w in nz:
                row[k] += v * w
    for j in range(p):
        if penalized[j]:
            XtX[j][j] += lam
        else:
            XtX[j][j] += 1e-9  # numerical safety only
    inv = inverse(XtX)
    beta = [sum(inv[j][k] * Xty[k] for k in range(p)) for j in range(p)]
    hat = []
    for xi in X:
        nz = [(j, v) for j, v in enumerate(xi) if v]
        hat.append(sum(v * w * inv[j][k] for j, v in nz for k, w in nz))
    return beta, hat


def loocv_ridge(X, y, penalized, grid):
    """Pick lambda by exact leave-one-out CV (closed form e_i / (1 - H_ii)). Returns dict."""
    best = None
    for lam in grid:
        beta, hat = ridge(X, y, penalized, lam)
        loo = []
        for xi, yi, h in zip(X, y, hat):
            e = yi - sum(a * b for a, b in zip(xi, beta))
            loo.append(e / (1.0 - h))
        mse = sum(e * e for e in loo) / len(loo)
        if best is None or mse < best["loo_mse"]:
            best = {"lam": lam, "beta": beta, "loo_mse": mse, "p_eff": sum(hat), "n": len(y)}
    return best


# ---------------------------------------------------------------- distributions
def phi_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def american(p):
    """Fair (no-vig) American odds for probability p."""
    if p <= 0 or p >= 1:
        return None
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)


# ---------------------------------------------------------------- descriptive
def mean(a):
    return sum(a) / len(a) if a else float("nan")


def sd(a):
    m = mean(a)
    return math.sqrt(sum((x - m) ** 2 for x in a) / (len(a) - 1)) if len(a) > 1 else float("nan")


def pearson(x, y):
    n = len(x)
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else float("nan")


def fisher_ci(r, n, z=1.959964):
    if n <= 3 or abs(r) >= 1:
        return (float("nan"), float("nan"))
    f, se = math.atanh(r), 1.0 / math.sqrt(n - 3)
    return (math.tanh(f - z * se), math.tanh(f + z * se))


def fisher_p(r, n):
    """Two-sided p-value for H0: rho = 0 (Fisher z approximation)."""
    if n <= 3 or abs(r) >= 1:
        return float("nan")
    zstat = abs(math.atanh(r)) * math.sqrt(n - 3)
    return 2 * (1 - phi_cdf(zstat))


def icc_oneway(groups):
    """ICC(1) from one-way random-effects ANOVA. groups: list of lists."""
    groups = [g for g in groups if len(g) >= 2]
    k = len(groups)
    N = sum(len(g) for g in groups)
    if k < 2:
        return float("nan")
    grand = sum(sum(g) for g in groups) / N
    ssb = sum(len(g) * (mean(g) - grand) ** 2 for g in groups)
    ssw = sum(sum((x - mean(g)) ** 2 for x in g) for g in groups)
    msb, msw = ssb / (k - 1), ssw / (N - k)
    n0 = (N - sum(len(g) ** 2 for g in groups) / N) / (k - 1)
    return (msb - msw) / (msb + (n0 - 1) * msw)


# ---------------------------------------------------------------- inference on paired loss differences
def bootstrap_ci(d, reps=10000, seed=SEED, alpha=0.05):
    rng = random.Random(seed)
    n = len(d)
    ms = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return (ms[int(reps * alpha / 2)], ms[int(reps * (1 - alpha / 2)) - 1])


def signflip_p(d, reps=10000, seed=SEED + 1):
    """One-sided p-value for H1: mean(d) < 0 (model loss lower than baseline)."""
    rng = random.Random(seed)
    obs = sum(d) / len(d)
    hits = 0
    for _ in range(reps):
        m = sum(x if rng.random() < 0.5 else -x for x in d) / len(d)
        if m <= obs:
            hits += 1
    return (hits + 1) / (reps + 1)


def holm(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def bh(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i], reverse=True)
    adj, running = [0.0] * m, 1.0
    for rank, i in enumerate(order):
        k = m - rank
        running = min(running, pvals[i] * m / k)
        adj[i] = running
    return adj


def ece(probs, outcomes, bins=5):
    """Expected calibration error with equal-width bins on [0,1]; returns (ece, table)."""
    table = []
    n = len(probs)
    tot = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(probs) if (lo <= p < hi) or (b == bins - 1 and p == 1.0)]
        if not idx:
            table.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": 0, "mean_pred": None, "observed": None})
            continue
        mp = mean([probs[i] for i in idx])
        ob = mean([outcomes[i] for i in idx])
        tot += len(idx) / n * abs(mp - ob)
        table.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": len(idx), "mean_pred": round(mp, 3), "observed": round(ob, 3)})
    return tot, table
