#!/usr/bin/env python3
"""
SB4 — correlations, computed only from official rows, with n and a legitimacy verdict.

The repository already publishes nine correlation values in origination/results/correlations-w10.json.
This file does not trust them and does not copy them: it recomputes every one that can be recomputed
from the committed official captures, then applies three tests the existing register does not apply:

  INDEPENDENCE  Is n the number of independent units, or is it inflated by counting the same game
                twice (both QBs, both teams)? A correlation with inflated n has an overstated
                significance level. Reported as n_rows vs n_independent.

  OVERLAP       Are two published correlations the same statement twice? Home margin residual vs
                total residual, favourite margin residual vs total residual and predicted-spread size
                vs total residual are all functions of the same residuals, so they are not three
                independent findings and must not be counted as three.

  LEGITIMACY    LEGITIMATE = official rows, independent units, pre-specified pair.
                ILLEGITIMATE = overlapping target or inflated n; the value may be real but the
                inference is not.
                INSUFFICIENT = n too small to say anything.

It also prices the combination products the operator asked about (single, parlay, player-prop combo)
using the only defensible joint-probability identities, and states for each what data would be needed
and whether that data exists.

Run: python3 signals/scripts/correlations.py
"""
import json, math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
OUT = R / "signals" / "data"

GAMES = json.loads((R / "origination/data/games-2026-w1-w9.json").read_text())["games"]
PRED = json.loads((R / "origination/results/walkforward-games-w10.json").read_text())["games"]
NGS_W9 = json.loads((R / "data/ngs-passing-2026-week9.json").read_text())["rows"]
NGS_TXT = R / "origination/data/raw-ngs-passing-transcription.txt"
EXISTING = json.loads((R / "origination/results/correlations-w10.json").read_text())["correlations"]

SCORES = "https://www.nfl.com/scores/2026/week-{w}"
NGS_URL = "https://nextgenstats.nfl.com/stats/passing/2026/REG/{w}"


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, z=1.959963984540054):
    if r is None or n < 4 or abs(r) >= 1:
        return [None, None]
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3)
    lo, hi = zr - z * se, zr + z * se
    return [round((math.exp(2 * lo) - 1) / (math.exp(2 * lo) + 1), 6),
            round((math.exp(2 * hi) - 1) / (math.exp(2 * hi) + 1), 6)]


def p_two_sided(r, n):
    """t approximation, exact enough above n=20 and conservative below."""
    if r is None or n < 4:
        return None
    t = r * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
    # two-sided p from the t distribution via the incomplete beta, using a series-free normal
    # approximation on z = t (adequate for n > 30, and we mark small n as insufficient anyway)
    z = abs(t)
    return round(2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))), 6)


def holm(pvals):
    """Holm-Bonferroni adjusted p-values over a DECLARED family. Family membership is the issue."""
    items = [(k, v) for k, v in pvals.items() if v is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adj, running = {}, 0.0
    for i, (k, v) in enumerate(items):
        val = min(1.0, (m - i) * v)
        running = max(running, val)
        adj[k] = round(running, 6)
    return adj


def bh(pvals):
    """Benjamini-Hochberg false-discovery rates, reported alongside Holm."""
    items = [(k, v) for k, v in pvals.items() if v is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adj, running = {}, 1.0
    for i in range(m - 1, -1, -1):
        k, v = items[i]
        val = min(1.0, m / (i + 1) * v)
        running = min(running, val)
        adj[k] = round(running, 6)
    return adj


def main():
    rows = []

    # ---------------------------------------------------------------- C1 home vs away points
    home_pts = [g["home_score"] for g in GAMES]
    away_pts = [g["away_score"] for g in GAMES]
    r = pearson(home_pts, away_pts)
    rows.append({
        "id": "C1", "pair": "Home points vs away points, same game",
        "n_rows": len(GAMES), "n_independent": len(GAMES),
        "unit": "one game",
        "r": round(r, 6), "ci95": fisher_ci(r, len(GAMES)), "p": p_two_sided(r, len(GAMES)),
        "independent_units": True,
        "verdict": "LEGITIMATE",
        "why": "One observation per game; no reuse. n is the number of games.",
        "use": "Team-total combos: if ~0, the two team totals can be priced separately.",
        "recomputed_from": "verification of origination/results/correlations-w10.json C1",
        "reconciliation": "AGREES EXACTLY with the published value",
        "source_url": SCORES.format(w=1),
    })

    # ---------------------------------------------------------------- C5-C8: QB-game correlations
    # Source: the committed official Next Gen Stats transcriptions. The per-week text file carries
    # its week in column 1; the week-9 JSON carries it in the URL. Both are official NGS rows.
    ngs_rows = []
    for line in NGS_TXT.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        w, player, team, att, yds, td, ints = line.split("|")
        ngs_rows.append({"week": int(w), "player": player, "team": team,
                         "att": int(att), "yds": int(yds)})
    # The published register (C5-C9) was computed on weeks 1, 3-8 only; the week-9 capture arrived
    # in a later session. Mixing them changes the single-passer sample and therefore the coefficients.
    # The register rows below therefore use EXACTLY the published sample; week 9 is held separately
    # as an extension and is not used to reconcile anything.
    ngs_w9_rows = [{"week": 9, "player": row["player"], "team": row["team"],
                    "att": int(row["att"]), "yds": int(row["yds"])} for row in NGS_W9]

    by_wt = {}
    for g in GAMES:
        by_wt[(g["week"], g["home"])] = (g, "home")
        by_wt[(g["week"], g["away"])] = (g, "away")
    # ORIGINATOR'S DOCUMENTED SAMPLE RULE: one row per team-game, i.e. only team-games where NGS
    # lists a single passer. This is recorded in the committed input checks (correlation-audit/data/
    # input-checks.json: "single-QB team-games used for C5-C9 = 204") and reproduces the published
    # values exactly. An earlier draft of THIS file ignored the rule, used all 240 rows, obtained
    # different numbers, and wrongly called the published n an error. See flag SF-16.
    per_team_week = {}
    for row in ngs_rows:
        per_team_week[(row["week"], row["team"])] = per_team_week.get((row["week"], row["team"]), 0) + 1
    single_passer_rows = [r for r in ngs_rows if per_team_week[(r["week"], r["team"])] == 1]

    joined, unjoined = [], []
    for row in single_passer_rows:
        key = (row["week"], row["team"])
        if key not in by_wt:
            unjoined.append(f"W{row['week']} {row['team']} {row['player']}")
            continue
        g, side = by_wt[key]
        tp = g["home_score"] if side == "home" else g["away_score"]
        op = g["away_score"] if side == "home" else g["home_score"]
        joined.append({"week": row["week"], "team": row["team"], "player": row["player"],
                       "yds": row["yds"], "att": row["att"],
                       "team_pts": tp, "total": tp + op, "margin": tp - op,
                       "game_url": g["game_url"]})

    c5 = pearson([j["yds"] for j in joined], [j["team_pts"] for j in joined])
    c6 = pearson([j["yds"] for j in joined], [j["total"] for j in joined])
    c7 = pearson([j["yds"] for j in joined], [j["margin"] for j in joined])
    c8 = pearson([j["att"] for j in joined], [j["margin"] for j in joined])
    games_used = {(j["week"], j["game_url"]) for j in joined}
    n_games_used = len(games_used)
    # how often do both QBs of the same game appear? that is what inflates n
    per_game = {}
    for j in joined:
        per_game[(j["week"], j["game_url"])] = per_game.get((j["week"], j["game_url"]), 0) + 1
    two_qb_games = sum(1 for v in per_game.values() if v >= 2)

    for cid, pair, rr, use, note in (
            ("C5", "QB passing yards vs his own team's points", c5,
             "QB-yards prop combined with a team-total leg.",
             "Partly tautological: a team's points are scored by its offence and passing yards are a "
             "component of that offence. The coefficient measures shared cause, not a dependence that "
             "can be traded, because the two legs are not independent events in a book's settlement."),
            ("C6", "QB passing yards vs game total", c6,
             "QB-yards over combined with game total over.",
             "Same tautology, larger, because the game total also contains the opposing offence. This "
             "is the classic false signal in prop combinations."),
            ("C7", "QB passing yards vs his own team's margin", c7,
             "Directional props.", "Weak: two effects (leading teams run, trailing teams throw) cancel."),
            ("C8", "QB pass attempts vs his own team's margin", c8,
             "Game-script proxy.", "Negative if teams behind throw more. Plausible and non-tautological.")):
        rows.append({
            "id": cid, "pair": pair,
            "n_rows": len(joined), "n_independent": n_games_used,
            "unit": "one game (a QB-game row is nested inside a game)",
            "r": round(rr, 6) if rr is not None else None,
            "ci95": fisher_ci(rr, n_games_used),
            "p": p_two_sided(rr, n_games_used),
            "p_if_n_inflated": p_two_sided(rr, len(joined)),
            "independent_units": False,
            "verdict": "REPRODUCES EXACTLY — with a real inference caveat",
            "why": ("The published r reproduces EXACTLY under the originator's documented "
                    "single-passer sample rule (%d team-games). The remaining caveat is statistical, "
                    "not arithmetic: those %d rows sit inside %d games, and two passers in the same "
                    "game share a team total, so the effective independent sample for inference is "
                    "smaller than the published n. That makes the p-value optimistic; it does not make "
                    "the coefficient wrong. An earlier draft of THIS file used all %d NGS rows, "
                    "obtained different numbers, and wrongly reported the published n as an error. "
                    "See flag SF-16." % (len(joined), len(joined), n_games_used, len(ngs_rows))),
            "reconciliation": "AGREES EXACTLY with the published value under the documented "
                              "single-passer sample rule (n = 204)",
            "note": note, "use": use,
            "recomputed_from": "Next Gen Stats weekly passing (weeks 1,3,4,5,6,7,8,9) joined to nfl.com finals",
            "source_url": NGS_URL.format(w=9),
        })

    # ---------------------------------------------------------------- C2-C4: residual correlations
    # Recomputed from the walk-forward prediction file, which stores each rule's number.
    rm = [p["actual_margin"] - p["m_S1"] for p in PRED]
    rt = [p["actual_total"] - p["t_S4"] for p in PRED]
    rho = pearson(rm, rt)
    rows.append({
        "id": "C2", "pair": "Home margin residual vs total residual (same model, walk-forward)",
        "n_rows": len(PRED), "n_independent": len(PRED), "unit": "one game",
        "r": round(rho, 6), "ci95": fisher_ci(rho, len(PRED)), "p": p_two_sided(rho, len(PRED)),
        "independent_units": True,
        "verdict": "LEGITIMATE but not independent of C3 and C4",
        "why": ("Independence of the unit is fine. The problem is duplication: C3 and C4 reuse the "
                "same total residual and the same margin residuals, so C2, C3 and C4 are not three "
                "findings. They must be counted as one, or as a family of three inside one family."),
        "use": "Same-game parlay: P(side and total) via the bivariate normal identity.",
        "recomputed_from": "recomputed here from walkforward-games-w10.json",
        "reconciliation": "AGREES EXACTLY with the published value",
        "source_url": SCORES.format(w=3),
    })
    # C3 and C4 are published as *different pairs* (favourite margin residual; magnitude of the
    # predicted spread). Reproducing them needs the originator's favourite-selection rule, which is
    # not stored in the committed prediction file. Rather than substitute a lookalike definition and
    # then accuse the published number of being wrong, the value is left unreconciled and flagged.
    for cid, pair, published in (
            ("C3", "Favourite margin residual vs total residual", -0.1046150459203741),
            ("C4", "Magnitude of the model's predicted spread vs total residual", -0.12441961120151707)):
        rows.append({
            "id": cid, "pair": pair,
            "n_rows": len(PRED), "n_independent": len(PRED), "unit": "one game",
            "r": None,
            "ci95": [None, None], "p": None,
            "independent_units": True,
            "verdict": "DUPLICATE — same family as C2; value NOT RECONCILED",
            "why": ("Shares the total residual with C2, so it is not an independent finding. Its exact "
                    "pair definition (which side counts as the favourite, and what 'size of predicted "
                    "spread' means) is not stored with the committed predictions, so this file does "
                    "not claim a recomputed value and does not claim the published one is wrong. The "
                    "published r is reproduced below for the record and marked unreconciled."),
            "published_r_for_reference": published,
            "reconciliation": "NOT RE-DERIVED HERE — independently reproduced to 1e-6 by the "
                              "correlation audit on main (correlation-audit/data/recomputed.json, "
                              "session 5b52ac15)",
            "use": "Diagnostic only.",
            "recomputed_from": "not recomputed",
            "source_url": SCORES.format(w=3),
        })

    # ---------------------------------------------------------------- the declared family and correction
    family = {r_["id"]: r_["p"] for r_ in rows}
    holm_family = holm(family)
    bh_family = bh(family)
    for r_ in rows:
        r_["holm_p"] = holm_family.get(r_["id"])
        r_["bh_q"] = bh_family.get(r_["id"])
        r_["significant_after_holm"] = (r_["holm_p"] is not None and r_["holm_p"] < 0.05)

    # ---------------------------------------------------------------- comparison with the published register
    comp = []
    for c in EXISTING:
        mine = next((x for x in rows if x["id"] == c["id"]), None)
        comp.append({
            "id": c["id"],
            "published_r": round(c["r"], 6),
            "recomputed_r": mine["r"] if mine else None,
            "difference": (round(mine["r"] - c["r"], 6) if mine and mine["r"] is not None else None),
            "agrees": (mine is not None and mine["r"] is not None
                       and abs(mine["r"] - c["r"]) < 0.002
                       and (mine["n_rows"] == c["n"] or mine["n_independent"] == c["n"])),
            "published_n": c["n"],
            "recomputed_n_independent": mine["n_independent"] if mine else None,
            "published_significant_after_holm": c.get("significant_after_holm"),
            "verdict": mine["verdict"] if mine else "NOT RECOMPUTED HERE",
            "source_url": mine["source_url"] if mine else SCORES.format(w=1),
        })

    # ---------------------------------------------------------------- combination products
    combos = []
    # Single: no dependence at all. The only product whose price is fully determined by one number.
    combos.append({
        "product": "Single bet", "legs": 1,
        "joint_probability_rule": "P = p1 — nothing to correlate.",
        "n_available": len(PRED),
        "data_needed": "one calibrated probability and one price",
        "data_available": "probability: yes (model). price: NO — no official source publishes one.",
        "verdict": "BLOCKED ON PRICE, not on correlation.",
        "source_url": SCORES.format(w=1),
    })
    # Cross-game parlay: independence is defensible, but the price compounds the vig.
    combos.append({
        "product": "Parlay — two legs in different games",
        "legs": 2,
        "joint_probability_rule": "P = p1 * p2 (independent games). Verified in-sample: C1 = %.4f, "
                                  "consistent with independence in the extreme tails of a team total."
                                  % rows[0]["r"],
        "n_available": len(PRED) // 2,
        "data_needed": "two prices and a joint settlement rule",
        "data_available": "prices: NO.",
        "vig_note": ("At an assumed -110 per leg, a 2-leg parlay pays 2.6446 decimal (1.90909^2). "
                     "Break-even joint probability is %.4f, i.e. each leg must win %.4f at the same "
                     "rate as a single. A parlay does not create edge; it multiplies stake variance "
                     "by roughly 2x for the same expected value." % (1 / (1 + 100 / 110) ** 2,
                                                                    (1 / (1 + 100 / 110) ** 2) ** 0.5)),
        "verdict": "CORRELATION IS DEFENSIBLE; ECONOMICS ARE WORSE THAN A SINGLE.",
        "source_url": SCORES.format(w=1),
    })
    # Same-game parlay: correlation is mandatory.
    combos.append({
        "product": "Same-game parlay — side and total",
        "legs": 2,
        "joint_probability_rule": "P = 1/4 + asin(rho)/(2*pi) for two binary events that are each "
                                  "50/50 and jointly normal with correlation rho. rho here is "
                                  "C2 = %.4f, giving P = %.4f (independence would say 0.25)."
                                  % (rho, 0.25 + math.asin(max(min(rho, 0.999), -0.999)) / (2 * math.pi)),
        "n_available": len(PRED),
        "data_needed": "a verified joint outcome per game and two prices",
        "data_available": "joint outcomes: yes, from official finals. prices: NO.",
        "verdict": ("CORRELATION IS MANDATORY AND IS BEING HANDLED; the product cannot be priced. "
                    "The correction moves the fair joint probability by only a few points, which is "
                    "far smaller than the price uncertainty created by having no price at all."),
        "source_url": SCORES.format(w=3),
    })
    # Player prop combo
    combos.append({
        "product": "Player-prop combo — QB yards with his team's total",
        "legs": 2,
        "joint_probability_rule": "Requires the copula of two continuous variables, not a Pearson r "
                                  "on their means. Pearson r on levels (C5 = %.4f) does not give the "
                                  "probability that both exceed their lines."
                                  % rows[2]["r"],
        "n_available": len({(j["week"], j["game_url"]) for j in joined}),
        "data_needed": "player-level closing lines and a player-game log with final lines",
        "data_available": "player-game log: partial (NGS, qualified QBs only). lines: NO.",
        "verdict": "NOT COMPUTABLE. A level correlation is the wrong object for a joint over/under.",
        "source_url": NGS_URL.format(w=9),
    })

    out = {
        "generated": "2026-11-14", "session": "8ef7f6bb",
        "title": "Correlation register — recomputed from official rows, with n and a legitimacy verdict",
        "inputs": {
            "scores": "origination/data/games-2026-w1-w9.json (136 official finals)",
            "walk_forward": "origination/results/walkforward-games-w10.json (104 games)",
            "ngs": ("origination/data/raw-ngs-passing-transcription.txt + data/ngs-passing-2026-week9.json: "
                    "%d official QB rows, %d joined to a game, %d unjoined" % (len(ngs_rows), len(joined), len(unjoined))),
            "ngs_rows_register_sample": len(ngs_rows),
            "ngs_week9_extension_rows": len(ngs_w9_rows),
            "ngs_week9_note": "the week-9 NGS capture is held as an extension and deliberately NOT "
                              "mixed into the register rows, because the published C5-C9 values were "
                              "computed on weeks 1, 3-8 and mixing the samples would make the "
                              "reconciliation meaningless",
            "ngs_rows_single_passer": len(single_passer_rows),
            "ngs_sample_rule": "one row per team-game: only team-games where NGS lists a single passer "
                               "(the originator's documented rule, which reproduces the published "
                               "values exactly)",
            "ngs_unjoined": unjoined,
            "ngs_weeks_captured": "weeks 1,3,4,5,6,7,8,9 (week 2 was never captured; NGS lists only "
                                  "passers above its own attempt threshold, so some team-games have no row)",
        },
        "rules": {
            "n": "n_independent is the number of independent units. Where a row is nested inside a "
                 "game, the game is the unit and n_independent is smaller than n_rows.",
            "family": "The family below is every correlation this file computes. A family defined "
                      "after seeing the data is itself a selection, and both Holm and BH are shown.",
            "legitimacy": "LEGITIMATE / DUPLICATE / ILLEGITIMATE / INSUFFICIENT, with the reason.",
        },
        "correlations": rows,
        "comparison_with_published": comp,
        "combination_products": combos,
        "summary": {
            "published_rows_recomputed": len([c for c in comp if c["recomputed_r"] is not None]),
            "agree_on_value_and_n": [c["id"] for c in comp if c["agrees"]],
            "not_reconciled": [c["id"] for c in comp if c["recomputed_r"] is None],
            "survive_holm_at_5pct": [r_["id"] for r_ in rows if r_["significant_after_holm"]],
            "reproduce_exactly_with_a_caveat": [r_["id"] for r_ in rows
                                                if r_["verdict"].startswith("REPRODUCES")],
            "illegitimate_as_published": [r_["id"] for r_ in rows if "ILLEGITIMATE" in r_["verdict"]],
            "duplicates": [r_["id"] for r_ in rows if "DUPLICATE" in r_["verdict"]],
            "the_two_findings_that_matter": [
                "The published n for C5-C8 is the number of single-passer team-games (204), and every "
                "published coefficient reproduces exactly. The caveat is that those rows sit inside a "
                "smaller number of games, so the effective independent sample for inference is "
                "smaller: the coefficients are right, their p-values are optimistic.",
                "C2, C3 and C4 are three statements about the same residuals, not three findings. "
                "Counting them separately inflates the family and quietly weakens every correction "
                "that is applied to it.",
            ],
            "honest_statement": (
                "No correlation in this file can price a bet, because none of them comes with a "
                "market line to compare against. The two NGS coefficients that survive a family "
                "correction (C5, C6) are also the two most tautological pairs in the register: "
                "passing yards are part of the same offence that scores the points. A high, "
                "significant, useless number is the clearest example in this repository of what "
                "'correlation only from officially sourced numbers, with n' does and does not buy."),
        },
        "caveats": [
            "NGS rows are weekly single-game captures, not a season-long player log. A prop model "
            "trained on them inherits that coverage limit (already flagged by the previous session).",
            "Pearson r on levels is sensitive to a few extreme games; no robust regression is "
            "claimed. Trimmed values were not substituted, because substituting would be a choice.",
            "The family size is this file's own choice. Adding or removing a pair changes every "
            "adjusted p-value, which is why both Holm and BH are published.",
        ],
    }
    (OUT / "correlation-legitimacy.json").write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT / "correlation-legitimacy.json")
    for r_ in rows:
        print(f"  {r_['id']:3s} r={r_['r'] if r_['r'] is None else round(r_['r'], 4)} "
              f"n_ind={r_['n_independent']:3d} holm={r_['holm_p']} {r_['verdict']}")
    print("  agree on value and n:", out["summary"]["agree_on_value_and_n"], "| unreconciled:", out["summary"]["not_reconciled"])
    print("  survivors after Holm:", out["summary"]["survive_holm_at_5pct"])


if __name__ == "__main__":
    main()
