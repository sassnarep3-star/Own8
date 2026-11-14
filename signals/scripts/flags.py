#!/usr/bin/env python3
"""
SB7a — the flag register. Every irregularity this session found, including the ones it found in its
own first draft. A flag is published, never suppressed, and never blocks a merge.
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
OUT = R / "signals" / "data"

AVAIL = json.loads((OUT / "availability-tiers.json").read_text())
CORR = json.loads((OUT / "correlation-legitimacy.json").read_text())
LADDER = json.loads((OUT / "baseline-ladder.json").read_text())

SCHED11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
INJ = "https://www.nfl.com/injuries/league/2026/reg10"
GB10 = "https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf"
GB5 = "https://static.www.nfl.com/image/upload/v1791805921/gamecenter/aa94b906-4feb-11f1-abca-2c54536568a9.pdf"
NGS = "https://nextgenstats.nfl.com/stats/passing/2026/REG/9"
NFL = "https://www.nfl.com/standings/"

FLAGS = [
    {"id": "SF-01", "severity": "high", "category": "Data availability",
     "finding": "No official NFL source publishes a betting line, total or price. Every probe "
                "returned records and statistics only.",
     "evidence": "Probes P5, P6 and P12 in signals/data/raw/probes-2026-11-14.txt; the game-centre "
                 "page prints 'Hidden Score' and no odds block.",
     "impact": "Makes ROI, edge, closing-line value and every staking decision uncomputable. Blocks "
               "decision-queue rows DQ-01 and DQ-02.",
     "disposition": "Price columns stay null everywhere. The repository publishes what a price WOULD "
                    "have to be instead. Operator action required outside the NFL data family.",
     "source_url": SCHED11},
    {"id": "SF-02", "severity": "medium", "category": "Statistical validity",
     "finding": "C5–C8 publish n = 204, the number of single-passer team-games. Every coefficient "
                "reproduces exactly, but those 204 rows sit inside 105 distinct games (two passers in a "
                "game share the same team points, total and margin), so the effective independent "
                "sample for inference is smaller and the published p-values are optimistic.",
     "evidence": "origination/results/correlations-w10.json (n = 204 for C5–C8); recomputed here on "
                 "the same sample in signals/data/correlation-legitimacy.json, where n_independent = 105.",
     "impact": "The coefficients are correct; the significance levels overstate the evidence.",
     "disposition": "Published with the game-level n alongside. The values are NOT changed and the "
                    "register is NOT accused of an arithmetic error.",
     "source_url": NGS},
    {"id": "SF-16", "severity": "high", "category": "Own work — corrected",
     "finding": "This session's first draft declared C5–C8 'ILLEGITIMATE as published' and implied the "
                "published n was a mistake. It was wrong twice: it ignored the originator's documented "
                "single-passer sample rule, and it quietly mixed in a week-9 NGS capture that arrived "
                "after the register was computed.",
     "evidence": "Recomputing with the single-passer rule on weeks 1, 3–8 reproduces all four values "
                 "exactly: C5 0.395306, C6 0.436017, C7 0.101358, C8 -0.196869 against the published "
                 "values to six decimals.",
     "impact": "A false accusation of error against another session's work, published on a site whose "
               "entire claim is that it does not overstate. This is the most serious defect this "
               "session found, and it was in its own output.",
     "disposition": "Verdict changed to REPRODUCES EXACTLY with the inference caveat retained. The "
                    "sample-rule and week-9 handling are now explicit in signals/scripts/correlations.py.",
     "source_url": NGS},
    {"id": "SF-03", "severity": "medium", "category": "Statistical validity",
     "finding": "Correlations C2, C3 and C4 are three statements about the same residuals, so they "
                "are not three independent findings.",
     "evidence": "All three reuse the total residual; C3 and C4 reuse the margin residual from the "
                 "same model. See signals/data/correlation-legitimacy.json.",
     "impact": "Counting them separately inflates the multiple-testing family and weakens every "
               "correction applied to it.",
     "disposition": "Flagged as DUPLICATE. C3 and C4 are left unreconciled rather than re-derived "
                    "from a lookalike definition.",
     "source_url": "https://www.nfl.com/scores/2026/week-3"},
    {"id": "SF-04", "severity": "medium", "category": "Own work — corrected",
     "finding": "This session's first draft measured 'depth of replacement' by matching the two Game "
                "Books row by row. That produced about twenty fake replacements.",
     "evidence": "The two PDFs order the same positions differently, for example the NYG offence "
                 "reads WR/LT/LG/C/RG/RT/TE/WR/QB/FB/RB in Week 5 but WR/TE/LT/LG/C/RG/RT/LB/WR/TE/QB/RB "
                 "in Week 10.",
     "impact": "Would have published a completely false availability finding.",
     "disposition": "Method replaced: only positions that appear exactly once per book are compared "
                    "one to one; everything else is compared as a set. Recorded here because a "
                    "corrected error is evidence about the noise in the rest of the register.",
     "source_url": GB5},
    {"id": "SF-05", "severity": "medium", "category": "Source anomaly",
     "finding": "In the Week 10 Game Book the New York Giants offensive column prints 'LB 52 A.Reese' "
                "as a starting row, while the same player also appears on defence. A linebacker is "
                "not an offensive starter.",
     "evidence": "'| RT | 72 J.Eluemunor | LB | 52 A.Reese |' followed by '| LB | 52 A.Reese | CB | "
                 "20 G.Newsome |' in the retrieved table.",
     "impact": "The NYG offensive listing has 12 rows where 11 are expected. One genuine starter may "
               "be missing or one cell may have been carried across the column boundary.",
     "disposition": "The ambiguous row is excluded from slot comparison and from the tier table. "
                    "Counts are published as observed; nothing is guessed to fill the gap.",
     "source_url": GB10},
    {"id": "SF-06", "severity": "medium", "category": "Data availability",
     "finding": "The Week 11 injury report could not be observed. /injuries/league/2026/reg11 returned "
                "the Week 10 page, heading included.",
     "evidence": "Probe P4. Page title and heading both re-rendered as WEEK 10.",
     "impact": "No Week 11 pregame availability join is possible, so every Week 11 availability cell "
               "in this repository is blank.",
     "disposition": "Recorded as a gap with the reason attached rather than filled from the Week 10 "
                    "report.",
     "source_url": INJ},
    {"id": "SF-07", "severity": "high", "category": "Interpretation",
     "finding": "The two strongest surviving correlations (C5, C6) are tautological: passing yards are "
                "part of the same offence that scores the points being correlated against.",
     "evidence": "C5 r = 0.4479 and C6 r = 0.4379 both survive Holm on the declared family; both "
                 "pairs relate a component of an offence to that offence's output.",
     "impact": "A high, significant, useless number. Using these to price a QB-yards-plus-team-total "
               "combo would double-count the same information.",
     "disposition": "Published with the verdict and excluded from every combo-pricing argument.",
     "source_url": NGS},
    {"id": "SF-08", "severity": "medium", "category": "Statistical validity",
     "finding": "Six of eighteen ladder arms beat a coin flip at the 5% level before any family "
                "correction, and one of them is a naive recent-form rule (B11), not a registered "
                "strategy.",
     "evidence": "signals/data/baseline-ladder.json: B11, S1, S2, S6, S7, S8 all have p < 0.05.",
     "impact": "The registered strategies are not special. A five-game recency rule does as well or "
               "better on the moneyline than the ridge models.",
     "disposition": "Published. The honest conclusion is that the ladder does not separate the "
                    "strategies from a simple rule, and that all six results are inside the range "
                    "that multiplicity can manufacture.",
     "source_url": NFL},
    {"id": "SF-09", "severity": "medium", "category": "Interpretation",
     "finding": "Two arms DO have a hit-rate interval whose lower bound clears the break-even rate: "
                "B11 (naive recent form, 63.11%, low bound 53.47%) and S8 (registered, 62.14%, low "
                "bound 52.49%). Neither may be promoted.",
     "evidence": "signals/data/market-relative.json interval_vs_breakeven, computed from the ladder. "
                 "Break-even at an assumed -110 is 52.38%.",
     "impact": ("This is the strongest result in the repository and it is still not promotable. The "
                "clearing margins are 1.09 and 0.11 percentage points, on about 100 bets, after testing "
                "18 arms. A naive rule clears by more than every registered strategy, which is the "
                "clearest evidence that the ladder is not separating skill from noise."),
     "disposition": "Published. No promotion. Promotion requires a price and an out-of-sample season, "
                    "not a marginally higher hit rate.",
     "source_url": "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm"},
    {"id": "SF-15", "severity": "medium", "category": "Own work — corrected",
     "finding": "This session published 'no admissible arm clears the break-even rate' in its first "
                "draft of the overview and the price-hurdle page. That statement was FALSE: two arms "
                "clear it.",
     "evidence": "signals/scripts/market.py interval_vs_breakeven: B11 ci_low 0.5347 and S8 ci_low "
                 "0.5249, both above the 0.5238 break-even rate.",
     "impact": ("A false negative is as damaging as a false positive in a project whose whole claim is "
                "that it does not overstate. The draft understated the evidence."),
     "disposition": "Corrected in the data and on the pages, and a build-time guard was added so the "
                    "headline claim is now computed from the file rather than typed.",
     "source_url": "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm"},
    {"id": "SF-10", "severity": "low", "category": "Interpretation",
     "finding": "S3, described in the registry as a 'naive season point differential' strategy, is "
                "the WORST arm in the entire ladder: 34.6% hit rate and −33.9% ROI on 104 games.",
     "evidence": "signals/data/baseline-ladder.json arm S3.",
     "impact": "It is registered as a strategy rather than as a foil, which overstates the library.",
     "disposition": "Flagged. No registry file was edited by this session; the correction belongs to "
                    "the origination owner. It should be reclassified as a negative control.",
     "source_url": NFL},
    {"id": "SF-11", "severity": "low", "category": "Own work — corrected",
     "finding": "This session's first draft of the market analysis computed the break-even cushion "
                "from the probability of winning, not the probability of covering, and also inverted "
                "the spread sign on the favourite.",
     "evidence": "Draft output showed a cushion that varied by game (0.86 to 12.86 points), which is "
                 "wrong: the break-even distance depends only on the price and the league's scoring "
                 "spread, so it must be a constant.",
     "impact": "Would have published 13 wrong numbers.",
     "disposition": "Corrected. The cushion is now a single constant, 0.63 points per side at an "
                    "assumed -110, and the script states why it cannot vary by game.",
     "source_url": "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm"},
    {"id": "SF-12", "severity": "low", "category": "Reproducibility",
     "finding": "Correlations C3, C4 and C9 could not be reconciled. Their pair definitions are not "
                "stored with the committed predictions, so this session cannot reproduce or refute "
                "the published values.",
     "evidence": "signals/data/correlation-legitimacy.json comparison_with_published: C3, C4, C9 "
                 "recomputed_r = null.",
     "impact": "Three of nine published coefficients are unverifiable.",
     "disposition": "Marked NOT RECONCILED. No substitute definition was used and no claim is made "
                    "that the published values are wrong.",
     "source_url": "https://www.nfl.com/scores/2026/week-3"},
    {"id": "SF-13", "severity": "low", "category": "Provenance",
     "finding": "The repository now contains eleven parallel workspaces with different as-of dates "
                "and different numbers for the same objects.",
     "evidence": "Root dashboard, requirements/, ledger/, origination/, decision/, decision-review/, "
                 "desk/, strict/, hub/, integration/, audit/, docs/ mirror.",
     "impact": "A reader can find two answers to the same question and cannot tell which is current.",
     "disposition": "Flagged and raised as decision-queue row DQ-12. Consolidation is a policy "
                    "decision, not a build task, so it was not performed unilaterally here.",
     "source_url": NFL},
    {"id": "SF-14", "severity": "low", "category": "Scope",
     "finding": "The depth-of-replacement measurement covers two clubs and two weeks. It is a "
                "demonstration of method, not a league-wide result.",
     "evidence": "signals/data/availability-tiers.json summary: clubs_measured = 2, weeks [5, 10], "
                 "3 slot changes, 6 unexplained absences.",
     "impact": "Nothing here generalises. A depth model cannot be fitted on two clubs.",
     "disposition": "Published with the sample size in the headline. Scaling is decision-queue "
                    "row DQ-06.",
     "source_url": GB10},
]


def main():
    by_sev = {}
    for f in FLAGS:
        by_sev.setdefault(f["severity"], []).append(f["id"])
    out = {
        "generated": "2026-11-14", "session": "8ef7f6bb",
        "title": "Flagged for review — irregularities found, including in this session's own work",
        "reading_rule": ("A flag does not block publication and is never suppressed. Every flag has "
                         "the exact evidence that produced it and the disposition taken. Where the "
                         "correct action was a decision rather than a fix, the row says so and "
                         "points at the decision queue."),
        "counts": {k: len(v) for k, v in sorted(by_sev.items())},
        "total": len(FLAGS),
        "flags": FLAGS,
        "own_work_corrections": [f["id"] for f in FLAGS if "Own work" in f["category"]],
        "requires_operator_action": [f["id"] for f in FLAGS
                                     if f["severity"] == "high"],
    }
    (OUT / "flags.json").write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT / "flags.json", out["counts"], "total", out["total"])


if __name__ == "__main__":
    main()
