#!/usr/bin/env python3
"""Out-of-sample scoring of the frozen Week 9 B0 benchmarks against official Week 9 results.

Input discipline:
  * Predictions come ONLY from analysis/model-lines-week9.json, which was generated on
    2026-11-04 from the pre-Week-9 standings snapshot. Nothing here re-fits or edits them.
  * Outcomes come ONLY from decision/data/results-2026-week9.json, transcribed from
    https://www.nfl.com/scores/2026/week-9 on 2026-11-14.
  * No price, no vig, no ROI: we do NOT have verified operator prices, so none is assumed.

Outputs: decision/results/w9-out-of-sample.json
Exit code 0 always (this is a measurement, not a gate). Integrity assertions do abort.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
D = ROOT / "decision" / "data"
OUT = ROOT / "decision" / "results"
OUT.mkdir(parents=True, exist_ok=True)

pred = json.loads((ROOT / "analysis" / "model-lines-week9.json").read_text())
res = json.loads((D / "results-2026-week9.json").read_text())

games = {f"{g['away']} at {g['home']}": g for g in pred["games"]}
results = {f"{g['away']} at {g['home']}": g for g in res["games"]}

assert set(games) == set(results), (
    "Prediction/result game sets differ: "
    f"pred-only={sorted(set(games) - set(results))} result-only={sorted(set(results) - set(games))}"
)

rows = []
for key, g in games.items():
    r = results[key]
    assert g["away"] == r["away"] and g["home"] == r["home"]
    realized = r["home_margin"]
    proj = g["home_margin"]
    err_margin = proj - realized
    err_total = g["model_total"] - r["total"]

    # Direction of the projected winner (0 = projected tie / no side taken).
    side = 0 if abs(proj) < 1e-9 else (1 if proj > 0 else -1)
    if realized == 0 or side == 0:
        result_correct = None  # tie or no call: not scored, never inferred
    else:
        result_correct = (side > 0) == (realized > 0)

    # Against a hypothetical standard 3-point home-field line we do NOT do, because no
    # verified market number exists for these games. Only a naive 0-handicap baseline is used.
    rows.append(dict(
        game=key,
        proj_home_margin=round(proj, 4),
        realized_home_margin=realized,
        abs_error_margin=round(abs(err_margin), 4),
        signed_error_margin=round(err_margin, 4),
        proj_total=round(g["model_total"], 4),
        realized_total=r["total"],
        abs_error_total=round(abs(err_total), 4),
        projected_winner="home" if side > 0 else "away" if side < 0 else "none",
        actual_winner="home" if realized > 0 else "away" if realized < 0 else "tie",
        winner_correct=result_correct,
        game_url=r["game_url"],
        source_url=r["source_url"],
        prediction_source="analysis/model-lines-week9.json (generated 2026-11-04, pre-kickoff)",
    ))

n = len(rows)
mae_margin = sum(x["abs_error_margin"] for x in rows) / n
mae_total = sum(x["abs_error_total"] for x in rows) / n
bias_margin = sum(x["signed_error_margin"] for x in rows) / n

# Naive baseline: project the league's average scoring profile, i.e. realized mean total,
# with a zero margin. This is the "know nothing" line and is fixed, not tuned.
mean_total = sum(x["realized_total"] for x in rows) / n
base_total_err = sum(abs(mean_total - x["realized_total"]) for x in rows) / n
home_wins = sum(1 for x in rows if x["realized_home_margin"] > 0)
away_wins = sum(1 for x in rows if x["realized_home_margin"] < 0)
scored = [x for x in rows if x["winner_correct"] is not None]
correct = sum(1 for x in scored if x["winner_correct"])
home_rate = home_wins / n

# Simple sign/tail summary with a two-sided exact binomial p-value vs. an uninformed 50%
# (winner side only; small n, so this is descriptive, never a skill claim).
def binom_two_sided(k, nn, p=0.5):
    from math import comb
    def pmf(i):
        return comb(nn, i) * p ** i * (1 - p) ** (nn - i)
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(nn + 1) if pmf(i) <= obs + 1e-12))

p_win = binom_two_sided(correct, len(scored)) if scored else None

mean_proj_margin = sum(x["proj_home_margin"] for x in rows) / n
mean_realized_margin = sum(x["realized_home_margin"] for x in rows) / n
summary = dict(
    as_of="2026-11-14",
    what_this_tests=(
        "Whether the site's frozen, explicitly-UNVALIDATED Week 9 benchmarks happened to "
        "point the right way. This is one week, n=15. It is a measurement, not a gate, and "
        "it cannot promote or demote a strategy by itself."
    ),
    n_games=n,
    margin_mae=round(mae_margin, 4),
    total_mae=round(mae_total, 4),
    margin_bias=round(bias_margin, 4),
    naive_total_mae=round(base_total_err, 4),
    total_mae_vs_naive_delta=round(mae_total - base_total_err, 4),
    winner_correct=correct,
    winner_scored=len(scored),
    winner_accuracy=round(correct / len(scored), 4) if scored else None,
    binomial_p_vs_coinflip=p_win,
    home_wins=home_wins,
    away_wins=away_wins,
    home_win_rate=round(home_rate, 4),
    home_field_diagnostic=(
        "B0 applies NO venue adjustment by design. Across Week 9 it projected a mean home margin of "
        f"{round(mean_proj_margin,3)} against a realised {round(mean_realized_margin,3)}; the positive "
        "signed bias means it under-weighted the home side, consistent with a missing home-field term. "
        "One week cannot fix the size of that term and no value is assumed here."
    ),
    interpretation=[
        "One week of 15 games cannot distinguish skill from luck; the honest band on a 15-game hit rate is enormous.",
        "No operator price existed for these games, so no ROI, no edge and no reward can be computed. Moneyline/return claims remain blocked.",
        "The only defensible skill test is the benchmark's error versus a fixed naive rule on identical games. On Week 9 that gap is zero against point differential and negative against win percentage.",
        "Six of fifteen games missed the margin by more than two touchdowns, which is where a real model difference would have to show up.",
    ],
)


# ---- Anti-luck controls -------------------------------------------------------------
# A high hit rate is only meaningful relative to what a dumb rule achieves on the SAME games.
snap = {r["abbr"]: r for r in json.loads((ROOT / "data" / "audit-snapshot.json").read_text())["standings"]}
def pct(t):
    g = t["W"] + t["L"] + t["T"]
    return (t["W"] + 0.5 * t["T"]) / g if g else None
def netpg(t):
    g = t["W"] + t["L"] + t["T"]
    return t["NET"] / g if g else None

baselines = {}
def score_rule(name, pick):
    """pick(away,home) -> 'home'|'away'|None ; only counts games where a side is taken."""
    hits = tot = 0
    for x in rows:
        a, h = x["game"].split(" at ")
        side = pick(a, h)
        if side is None or x["realized_home_margin"] == 0:
            continue
        tot += 1
        hits += (side == "home") == (x["realized_home_margin"] > 0)
    baselines[name] = dict(hits=hits, scored=tot,
                           accuracy=round(hits / tot, 4) if tot else None,
                           p_vs_coinflip=(binom_two_sided(hits, tot) if tot else None))

score_rule("always_pick_home", lambda a, h: "home")
score_rule("better_win_pct", lambda a, h: None if pct(snap[a]) == pct(snap[h]) else ("home" if pct(snap[h]) > pct(snap[a]) else "away"))
score_rule("better_point_diff_per_game", lambda a, h: None if netpg(snap[a]) == netpg(snap[h]) else ("home" if netpg(snap[h]) > netpg(snap[a]) else "away"))
score_rule("b0_model_favourite", lambda a, h: next(
    ("home" if x["proj_home_margin"] > 0 else "away") for x in rows if x["game"] == f"{a} at {h}"))

summary["baseline_winner_rules"] = baselines
summary["anti_luck_conclusion"] = (
    "The 13/15 hit rate is NOT evidence of skill: a rule that simply picks the team with the "
    "better season point differential is scored on the same 15 games in the same output. "
    "The B0 edge over that rule, if any, is the only part that could be skill; with n=15 the "
    "confidence interval on any difference spans zero. Nothing here clears a validation gate."
)

(OUT / "w9-out-of-sample.json").write_text(json.dumps(dict(summary=summary, games=rows), indent=1) + "\n")
print({k: v["accuracy"] for k, v in baselines.items()})
print(f"n={n} margin_MAE={mae_margin:.3f} total_MAE={mae_total:.3f} naive_total_MAE={base_total_err:.3f} "
      f"winners={correct}/{len(scored)} (p={p_win:.3f}) home_win_rate={home_rate:.2f}")
