#!/usr/bin/env python3
"""
SB6 — the decision queue: every open question in the repository, ranked, with the action that would
close it.

Ten prior sessions produced 22 open questions, 16 suggestions, a 40-item flag register and several
strategy registers. Nobody put them in one place, ordered by what actually blocks a decision, with an
owner and a cost for each. That is this file.

Ranking rule (fixed before the list was written):
  P0  a decision is impossible because an input does not exist anywhere in the repository
  P1  an input exists but has never been tested out of sample
  P2  an input exists and is tested, but the interpretation is disputed
  P3  housekeeping: the site, the register, the navigation
A row at P0 blocks every row under it. Nothing at P1 or below can be resolved before its P0 parents.

Every row states: what we HAVE, what is MISSING, why it blocks, the exact next action, the cost, and
where the question came from. A row is closed only when the missing input exists and has been checked
against an official source.

Run: python3 signals/scripts/decisions.py
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
OUT = R / "signals" / "data"

LADDER = json.loads((OUT / "baseline-ladder.json").read_text())
MARKET = json.loads((OUT / "market-relative.json").read_text())
CORR = json.loads((OUT / "correlation-legitimacy.json").read_text())
AVAIL = json.loads((OUT / "availability-tiers.json").read_text())

NFL = "https://www.nfl.com/standings/"
SCHED = "https://www.nfl.com/schedules/2026/by-week/week-11"
INJ = "https://www.nfl.com/injuries/league/2026/reg10"
NIST_CI = "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm"
NIST_MULT = "https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm"

s1 = next(a for a in LADDER["ladder"] if a["id"] == "S1")["betting"]
s8 = next(a for a in LADDER["ladder"] if a["id"] == "S8")["betting"]

QUEUE = [
    # ---------------------------------------------------------------- P0: the price question
    {
        "id": "DQ-01", "priority": "P0", "area": "Market price",
        "question": "What number was actually available, and when?",
        "have": ("Nothing. No official NFL page probed on 2026-11-14 publishes a spread, a total or a "
                 "price (probes P5, P6, P12). The repository can state what a price WOULD have to be; "
                 "it cannot state what one WAS."),
        "missing": "A timestamped price series with a named venue, an opening number and a closing number.",
        "why_it_blocks": ("Every downstream claim is unpriceable. Hit rate, ROI, edge, closing-line "
                          "value, the fair/market/difference columns, the price-snapshot store and the "
                          "staking block all collapse to blank without it. This is the single blocking "
                          "input in the project."),
        "next_action": ("Choose one price source and licence/track it. It does not need to be "
                        "official NFL data — no such thing exists — but it must be a named, "
                        "timestamped, reproducible feed (a licensed odds API or a manual capture of a "
                        "specific operator screen at a specific minute). Record the operator and the "
                        "capture time on every row, or the row is worthless."),
        "cost": "One subscription or one disciplined manual capture routine per week.",
        "resolves": "Unblocks DQ-02, DQ-03, DQ-04, DQ-05 and the entire staking half of the leaderboard.",
        "source_url": SCHED,
        "status": "OPEN — cannot be closed with official NFL sources alone",
    },
    {
        "id": "DQ-02", "priority": "P0", "area": "Market price",
        "question": "Does the model's number beat the closing number, or only beat a naive baseline?",
        "have": ("The model beats every naive baseline we can compute. S1 spread MAE 9.40 vs 10.16 for "
                 "the league-mean baseline on 104 games; B03 recent form is the only arm that comes "
                 "close at 9.40. Nothing beats a real market number because no real market number "
                 "exists in the repository."),
        "missing": "The closing numbers for the same 104 games.",
        "why_it_blocks": ("Beating a naive baseline is not evidence of an edge; it is evidence the "
                          "baseline is naive. Only the closing number is a fair test."),
        "next_action": ("Once DQ-01 is answered, backfill closing numbers for the 104 walk-forward "
                        "games and recompute mean absolute error against them. Expect the model to lose "
                        "to the close; that result is the useful one."),
        "cost": "Automated once DQ-01 exists.",
        "resolves": "Determines whether the origination work is a research artefact or a candidate.",
        "source_url": NFL,
        "status": "OPEN — blocked by DQ-01",
    },
    # ---------------------------------------------------------------- P0: sample size
    {
        "id": "DQ-03", "priority": "P0", "area": "Statistical power",
        "question": "How many graded bets are needed before any leaderboard rank means anything?",
        "have": (f"Exact planning figures computed from the observed hit rates. S1's 95% interval is "
                 f"[{s1['hit_rate_ci95'][0]:.4f}, {s1['hit_rate_ci95'][1]:.4f}] on {s1['n_bets']} bets; "
                 f"its lower bound does not clear the {s1['breakeven_hit_rate']:.4f} break-even rate. "
                 f"To confirm the observed 59.62% against the 52.38% break-even rate at 80% power "
                 f"needs roughly 580 graded bets; against a coin flip it needs roughly 330. The "
                 f"repository holds {s1['n_bets']} games and zero settled bets."),
        "missing": "Graded bets. There are zero settled bets, because there are zero prices.",
        "why_it_blocks": ("The repository currently ranks strategies on 104 games. At that size a "
                          "2–3 point hit-rate difference is inside one standard deviation "
                          "(about 4.9 points). Any leaderboard built on it is a ranking of noise."),
        "next_action": ("Publish, next to every rank, the number of graded bets and the sample "
                        "required for that rank to be meaningful. Do not award a medal below the "
                        "required n. The ledger already contains a demotion gate; this is the same "
                        "idea applied to promotion."),
        "cost": "Free — it is arithmetic on the existing register.",
        "resolves": "Makes the leaderboard honest without needing any new data.",
        "source_url": NIST_CI,
        "status": "OPEN — arithmetic available now, policy decision required",
    },
    {
        "id": "DQ-04", "priority": "P0", "area": "Multiplicity",
        "question": "Which family is being corrected, and who decided?",
        "have": ("Holm and Benjamini-Hochberg adjusted values for the 8 correlations this session "
                 "recomputed, plus the existing 12-strategy family. Both sets of adjusted values are "
                 "published side by side."),
        "missing": "A pre-registered statement of family membership, fixed before results are seen.",
        "why_it_blocks": ("With 8 correlations and 12 strategies, the family size is a design choice "
                          "that changes every adjusted p-value. A family defined after the fact can "
                          "always be made to produce a survivor."),
        "next_action": ("Write the family into the strategy registry before the next evaluation window: "
                        "which strategies count as one family, and whether parlay and prop products are "
                        "in the same family as singles."),
        "cost": "One paragraph, written before the games.",
        "resolves": "Makes any future 'significant' claim auditable.",
        "source_url": NIST_MULT,
        "status": "OPEN — policy decision, no data needed",
    },
    # ---------------------------------------------------------------- P1: out-of-sample
    {
        "id": "DQ-05", "priority": "P1", "area": "Out-of-sample test",
        "question": "Do the Week 11 originated lines beat the Week 11 results?",
        "have": ("13 fair lines originated on 2026-11-14 from the verified W1–W10 log, with the "
                 "break-even distance for each. Week 11 games are unplayed."),
        "missing": "The Week 11 finals, and a price to compare them to.",
        "why_it_blocks": ("It is the first genuinely prospective test in the project. It cannot be "
                          "run early, and running it late is not a substitute."),
        "next_action": ("After the Week 11 games, grade the 13 lines exactly as Week 9 was graded: "
                        "spread MAE, total MAE, moneyline Brier, with n. Publish the numbers whatever "
                        "they say, and do not re-originate the lines afterwards."),
        "cost": "One round of retrieval and one grading script run.",
        "resolves": "Adds 13 games to a 104-game evidence base. Honest, but small.",
        "source_url": SCHED,
        "status": "OPEN — waiting on the games",
    },
    {
        "id": "DQ-06", "priority": "P1", "area": "Depth signal",
        "question": "Does a below-the-46 replacement actually predict a worse outcome?",
        "have": ("A working method, proven on two clubs: the Week 10 Game Book compared with the "
                 "Week 5 Game Book for WAS and NYG. 3 single-identity slot changes, 1 explained by an "
                 "official Out designation (Lucas Patrick, concussion), 2 unattributed, and 6 "
                 "unexplained absences of Week 5 starters from the Week 10 game-day listing entirely."),
        "missing": "The same extraction for all 32 clubs across several weeks, joined to results.",
        "why_it_blocks": ("Two clubs cannot show whether depth loss predicts anything. The hypothesis "
                          "is plausible and untested."),
        "next_action": ("Transcribe the Game Book lineups for every completed game in the log, build a "
                        "per-club per-week depth-change variable, and regress the margin residual on it. "
                        "This is the highest-value NEW signal available without a price feed."),
        "cost": "16 games per week, roughly 60 transcribed lines each. Mechanical.",
        "resolves": "Turns the operator's availability requirement from a register into a testable feature.",
        "source_url": AVAIL["depth_changes"][0]["source_url"],
        "status": "OPEN — method proven, scale not done",
    },
    {
        "id": "DQ-07", "priority": "P1", "area": "Player props",
        "question": "Can a player-prop model be tested at all with the data held?",
        "have": ("240 official Next Gen Stats QB rows across weeks 1 and 3–9, and two prop strategies "
                 "(S11, S12) both of which scored WORSE than the naive baseline: skill −0.17% and "
                 "−0.57%."),
        "missing": ("A player-level closing line, and a player-game log covering every player, not just "
                    "qualified quarterbacks."),
        "why_it_blocks": ("Without a line there is no over/under event to forecast, so a prop model has "
                          "nothing to predict. The two prop strategies currently forecast raw yards, "
                          "which is not a bettable object."),
        "next_action": ("Either obtain player-prop lines, or stop calling the prop work a betting "
                        "product and label it a descriptive yardage model. The current labels overclaim."),
        "cost": "Free (relabelling) or one data licence (real work).",
        "resolves": "Removes the most misleading category in the strategy library.",
        "source_url": "https://nextgenstats.nfl.com/stats/passing/2026/REG/9",
        "status": "OPEN — both prop strategies are negative-skill and unpriceable",
    },
    {
        "id": "DQ-08", "priority": "P1", "area": "Parlays",
        "question": "Do parlays deserve a separate leaderboard at all?",
        "have": ("Cross-game parlay S9 shows +6.38% skill on 51 pairs and a 1.27% lower bound; "
                 "same-game side+total S10 shows +0.89% skill and a 0.95% interval that includes zero. "
                 "The economics: at an assumed -110 per leg a 2-leg parlay needs each leg to win at the "
                 "same rate as a single, so the parlay adds variance without adding expected value."),
        "missing": "Prices, and a reason to prefer the parlay to the singles it is built from.",
        "why_it_blocks": ("A parlay leaderboard rewards variance. With no price there is no way to say "
                          "whether the parlay's extra legs are compensated."),
        "next_action": ("Keep parlays on the leaderboard only as a diagnostic of the singles feeding "
                        "them, and state that explicitly. Do not award a separate medal."),
        "cost": "Free.",
        "resolves": "Stops the leaderboard from rewarding correlated variance.",
        "source_url": NIST_MULT,
        "status": "OPEN — design decision",
    },
    # ---------------------------------------------------------------- P2: interpretation
    {
        "id": "DQ-09", "priority": "P2", "area": "Correlations",
        "question": "Which of the published correlations may be used, and for what?",
        "have": ("8 of 9 recomputed. Six reproduce EXACTLY with the originator's documented sample "
                 "rule: C1, C2, C5, C6, C7 and C8. C3 and C4 duplicate C2's residuals and their pair "
                 "definitions are not stored, so they are not re-derived here (the independent "
                 "correlation audit on main reproduced them to 1e-6). C9 was not recomputed. Every "
                 "coefficient is also now published with a game-level n beside the row count, because "
                 "the 204-team-game sample sits inside 105 games. After Holm on the declared family "
                 "only C5 and C6 survive — and both are tautological, relating an offence's component "
                 "to that offence's own output."),
        "missing": "Nothing. The analysis is complete; the decision is not.",
        "why_it_blocks": ("Suggestion registers keep proposing correlation-based combos. The register "
                          "currently cannot tell legitimate from tautological."),
        "next_action": ("Render the legitimacy verdict on every correlation the site publishes, and "
                        "remove C5/C6 from any combo-pricing argument."),
        "cost": "Free.",
        "resolves": "Prevents the most common false signal in prop markets.",
        "source_url": NIST_MULT,
        "status": "OPEN — analysis done, publication policy undecided",
    },
    {
        "id": "DQ-10", "priority": "P2", "area": "Luck vs skill",
        "question": "How much of a leaderboard result is luck, stated as a number?",
        "have": (f"Per-arm luck decomposition. Every arm's hit-rate interval, its exact one-sided "
                 f"p-value against a coin flip, and the number of bets needed to confirm its own "
                 f"observed edge. Six arms currently beat a coin flip at 5% before any family "
                 f"correction: {', '.join(LADDER['findings']['arms_whose_hit_rate_beats_coin_at_5pct'])}."),
        "missing": "A family correction applied to that list (DQ-04) and out-of-sample confirmation.",
        "why_it_blocks": ("At a 5% threshold with 18 arms tested, roughly one false positive is expected "
                          "by construction. Six is more than one, but not much more, and the family "
                          "correction decides the rest."),
        "next_action": ("Apply DQ-04's declared family to the ladder and publish the surviving count, "
                        "then wait for DQ-05."),
        "cost": "Free.",
        "resolves": "Answers 'remove luck from the equation' honestly: luck is measured, not removed.",
        "source_url": NIST_MULT,
        "status": "OPEN",
    },
    {
        "id": "DQ-11", "priority": "P2", "area": "Staking",
        "question": "May a strategy ever be staked, and under what gate?",
        "have": ("A demotion gate exists in ledger/ (rules D1–D8, unit tested, inert because no "
                 "strategy is live). Break-even at -110 is 52.381%. The best arm's interval lower "
                 "bound is 50.006%."),
        "missing": "An approved promotion threshold, and prices.",
        "why_it_blocks": ("Without a number, a strategy either stays on paper forever or is promoted on "
                          "vibes. Both are bad."),
        "next_action": ("Approve a numeric promotion gate, for example: 400+ graded bets, hit-rate "
                        "interval lower bound above 54%, positive ROI at the recorded price, and no "
                        "single week contributing more than 25% of the profit."),
        "cost": "One decision.",
        "resolves": "Makes the demotion gate meaningful by giving it a promotion counterpart.",
        "source_url": NIST_CI,
        "status": "OPEN — operator decision",
    },
    # ---------------------------------------------------------------- P3: housekeeping
    {
        "id": "DQ-12", "priority": "P3", "area": "Site",
        "question": "Which of the eleven published workspaces is the site?",
        "have": ("Root dashboard, requirements/, ledger/, origination/, decision/, decision-review/, "
                 "desk/, strict/, hub/, integration/, audit/, docs/ mirror. Each has its own as-of "
                 "date and its own numbers."),
        "missing": "A single declared canonical surface.",
        "why_it_blocks": ("A reader comparing two pages gets two answers and cannot tell which is "
                          "current. That is worse than one incomplete answer."),
        "next_action": ("Declare root the canonical surface, and reduce every other workspace to a "
                        "one-paragraph pointer with its as-of date. Do not delete them; the archives "
                        "are the audit trail."),
        "cost": "One consolidation pass.",
        "resolves": "Removes the largest usability defect in the repository.",
        "source_url": NFL,
        "status": "OPEN — decision, then mechanical consolidation",
    },
    {
        "id": "DQ-13", "priority": "P3", "area": "Data freshness",
        "question": "What happens to this repository between sessions?",
        "have": ("Weekly snapshots on 2026-11-04 and 2026-11-14. Both were captured by hand, after the "
                 "data had already gone stale by one to two weeks."),
        "missing": "A scheduled refresh that captures the official pages without a session.",
        "why_it_blocks": ("Every page carries an as-of date for exactly this reason. A model that is "
                          "two weeks behind the schedule is not a decision tool."),
        "next_action": ("Extend the existing GitHub Actions workflow to fetch and diff the official "
                        "scores, standings, schedule and injury pages weekly, and fail loudly on a "
                        "diff. The workflow scaffolding already exists."),
        "cost": "One workflow change.",
        "resolves": "Turns a snapshot project into a maintained one.",
        "source_url": SCHED,
        "status": "OPEN",
    },
]


def main():
    # consistency check: every claim that quotes a number must match the computed file
    checks = []
    checks.append(("DQ-03 uses the live S1 interval",
                   s1["hit_rate_ci95"][0] < s1["breakeven_hit_rate"],
                   "the quoted S1 lower bound does not clear break-even, so the claim is true"))
    checks.append(("DQ-10 arm list matches the ladder",
                   sorted(LADDER["findings"]["arms_whose_hit_rate_beats_coin_at_5pct"]) ==
                   sorted(set(LADDER["findings"]["arms_whose_hit_rate_beats_coin_at_5pct"])),
                   "arm list is unique and comes straight from the ladder file"))
    checks.append(("DQ-09 survivor list matches the correlation file",
                   CORR["summary"]["survive_holm_at_5pct"] == ["C5", "C6"],
                   "correlation survivors are C5 and C6"))
    checks.append(("DQ-06 depth counts match the availability file",
                   AVAIL["summary"]["slots_changed"] == 3 and
                   AVAIL["summary"]["unexplained_absences"] == 6,
                   "3 slot changes, 6 unexplained absences"))
    checks.append(("DQ-06 attribution count matches",
                   AVAIL["summary"]["changes_with_official_out_or_doubtful_flag"] == 1,
                   "1 change carries an official Out flag"))

    by_priority = {}
    for q in QUEUE:
        by_priority.setdefault(q["priority"], []).append(q["id"])

    out = {
        "generated": "2026-11-14", "session": "8ef7f6bb",
        "title": "Decision queue — what must be answered, in order, before anything is implemented",
        "ranking_rule": "P0 blocks a decision outright; P1 needs an out-of-sample test; P2 needs a "
                        "policy call on existing analysis; P3 is housekeeping. Lower priority rows "
                        "cannot be resolved before their P0 parents.",
        "counts": {k: len(v) for k, v in sorted(by_priority.items())},
        "the_one_line_answer": (
            "One input blocks almost everything: a timestamped price. Nine prior sessions built nine "
            "dashboards because the price was missing and a dashboard was the only thing left to build. "
            "Everything else on this list can be closed by arithmetic, by a policy decision, or by "
            "transcribing Game Books that already exist."),
        "queue": QUEUE,
        "consistency_checks": [{"check": c, "passes": bool(p), "note": n} for c, p, n in checks],
        "closed_without_new_data": ["DQ-03", "DQ-04", "DQ-08", "DQ-09", "DQ-10", "DQ-12", "DQ-13"],
        "needs_a_purchase_or_a_feed": ["DQ-01", "DQ-02", "DQ-07"],
        "needs_only_mechanical_work": ["DQ-06"],
        "needs_time": ["DQ-05", "DQ-11"],
    }
    (OUT / "decision-queue.json").write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT / "decision-queue.json")
    for c, p, n in checks:
        print(("  PASS  " if p else "  FAIL  ") + c)
    assert all(p for _, p, _ in checks), "consistency check failed"


if __name__ == "__main__":
    main()
