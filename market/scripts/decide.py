#!/usr/bin/env python3
"""Build the decision gate and the suggestions register.

These are the two documents the operator asked for by name:
  * a clear list of questions, information and answers that must be settled before a
    decision can reasonably be made, including which of them CANNOT be answered from
    information that currently exists, and how to go and get it;
  * a suggestions section where each proposal can be reviewed and chosen before
    anything is implemented.

Both are generated from the data files this session produced, so a number quoted in a
question is the same number published elsewhere on the site. Nothing here is
implemented: every suggestion carries state "OPEN - FOR OPERATOR DECISION".
"""
import json
from pathlib import Path

MARKET = Path(__file__).resolve().parent.parent
REPO = MARKET.parent


def load(p):
    return json.loads((REPO / p).read_text())


def main():
    grading = load("market/data/grading.json")
    tour = load("market/data/tournament.json")
    own = load("market/data/own-lines.json")
    corr = load("market/data/correlations.json")
    depth = load("market/data/depth.json")
    crawl = load("market/data/repo-crawl.json")
    ver = load("market/data/verification.json")

    w9 = grading["week9"]["overall"]
    h2h = own["week9_head_to_head"]["summary"]
    lcb = {r["id"]: r for r in tour["leaderboard"]}

    # ------------------------------------------------------------------ questions
    Q = []

    def q(qid, question, why_it_blocks, have, lack, answerable, source, discovery, blocks, owner):
        Q.append(dict(id=qid, question=question, why_it_blocks_a_decision=why_it_blocks,
                      what_we_have=have, what_we_lack=lack,
                      answerable_from_current_information=answerable,
                      source_url=source, discovery_plan=discovery,
                      blocks=blocks, who_can_answer=owner))

    q("Q-01", "Can our own line beat the market's line on the same games?",
      "Every reward, ranking and stake rule depends on this. If our number is worse than the market's, a leaderboard that rewards 'line accuracy' rewards noise.",
      f"Week 9, the only week with both an official price and an official result: our spread MAE {h2h['side']['own_mae']} vs the market's {h2h['side']['market_mae']}; "
      f"our number was closer in {h2h['side']['games_own_closer']} of {h2h['n']} games; mean paired difference +{h2h['side']['mean_paired_diff_own_minus_market']} pts "
      f"with a 95% interval of [{h2h['side']['paired_diff_ci95'][0]}, {h2h['side']['paired_diff_ci95'][1]}]; moneyline Brier {h2h['moneyline']['own_brier']} vs {h2h['moneyline']['market_devig_brier']} de-vigged.",
      "n. Fifteen games cannot settle this either way, and Week 10 had not been played at capture time.",
      "NO - not from information that exists today. The direction is unfavourable and the interval is wide.",
      h2h["side"] and "https://www.nfl.com/scores/2026/week-9",
      "Score 60+ priced games. That means collecting the weekly picks article every week from here, which is a repeatable 15-minute job, and grading only after finals. No new data source is needed.",
      "the entire leaderboard reward rule, and any decision to promote a live strategy", "project owner, after 4-6 more weeks of capture")

    q("Q-02", "What counts as 'winning' the leaderboard, and how is a reward earned?",
      "Six suggestion registers and four leaderboards rank on four different quantities (loss, LCB of loss reduction, skill, ROI). A reward attached to the wrong one pays luck.",
      f"A signal/staking split now exists: {lcb['S6']['roi']*100:+.1f}% flat-stake ROI sits beside a mean per-bet skill of {lcb['S6']['mean_skill']:+.4f} "
      f"(lower bound {lcb['S6']['lower_bound_skill']:+.4f}) for the same 15 bets, and none of the three moneyline strategies survives the family correction.",
      "A decision. The data can rank; only the operator can say what is rewarded.",
      "NO - this is a policy choice, not a measurement.",
      "https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm",
      "Pick one ranking quantity from SG-01 below and write it into the registry before any week is scored. Nothing else is needed.",
      "every reward, every medal, every 'top strategy' claim on the site", "project owner")

    q("Q-03", "Does an official price series exist that we may lawfully and repeatably collect?",
      "Without it, no ROI, no edge, no backtest and no leaderboard reward can be computed at all.",
      "YES - nfl.com publishes a weekly picks article stating the lines are provided by FanDuel and locked at 2 p.m. ET Thursday. Captured today for Weeks 9 and 10: "
      f"{len(load('market/data/raw/official-prices-w9.json')['games'])} + {len(load('market/data/raw/official-prices-w10.json')['games'])} games x 3 markets.",
      "No opening line (the first number posted), no closing line (the number at kickoff), no price on spreads or totals, and no terms-of-use review.",
      "PARTLY - a Thursday-locked single-book number exists; open/close and spread/total prices do not.",
      "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season",
      "To get a true opening/closing pair, capture the same page on Tuesday and again 90 minutes before kickoff. That is 2 fetches per week and no new source.",
      "the price-snapshot store, the closing-line-value metric, and any 'did we beat the close' claim", "project owner decides whether one book at one time is enough")

    q("Q-04", "Is the injury-and-replacement signal obtainable before kickoff?",
      "The operator asked for 2nd/3rd/4th-string tracking. A model that ignores a quarterback change is measurably worse; one that invents depth is worse still.",
      f"{len(depth['club_injury_load'])} clubs, {sum(c['rows'] for c in depth['club_injury_load'])} official injury rows, and {len(depth['verified_replacement_cases'])} replacement cases confirmed with official URLs. "
      "The depth-chart URL returns the official 404; the roster publishes a transaction status, not an order; the Game Book PDF names the 11 starters but only after the game.",
      "Any pregame source of depth order. There is none on nfl.com, at any URL tested today.",
      "NO for pregame depth order. YES for named quarterback changes and postgame starter facts.",
      "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart",
      "Collect the postgame Game Book every week and join it to the pregame injury report. After 6-8 weeks you have a measured 'backup started' event set. That is the only honest route.",
      "any injury adjustment inside the line model", "project owner decides whether to run the 6-8 week collection")

    q("Q-05", "Which correlation numbers may be used inside a parlay price, and which may not?",
      "A same-game parlay is priced from a joint probability. Using the wrong correlation silently misprices every combo.",
      f"{len(corr['rows'])} values, each with n on the row. Three survive Holm: QB yards vs own points r={corr['rows'][3]['r']} (n={corr['rows'][3]['n']}), "
      f"QB yards vs game total r={corr['rows'][4]['r']} (n={corr['rows'][4]['n']}), opposing QBs r={corr['rows'][5]['r']} (n={corr['rows'][5]['n']}). "
      f"Side vs total on realised outcomes is r={corr['rows'][1]['r']} (n={corr['rows'][1]['n']}) and does NOT survive correction.",
      "Any correlation measured on the residual of a forecast rather than on raw outcomes, and any dependence estimate that survives out of sample.",
      "PARTLY - the surviving values are usable as raw associations; none of them is a priced joint distribution.",
      "https://nextgenstats.nfl.com/stats/passing/2026/REG/9",
      "Model the joint distribution directly on residual pairs, walk-forward, and score the resulting joint probability against the realised joint outcome. Needs no new data.",
      "pricing for parlays, same-game parlays and prop combos", "project owner + modelling owner")

    q("Q-06", "What is the demotion rule that sends a live strategy back to paper?",
      "Without a pre-registered demotion rule, a live strategy can only ever be promoted.",
      "ledger/data/demotion-rules.json holds rules D1-D8 written before any live window, with an evaluator and 23 unit tests; 0 strategies are live, so 0 demotions have fired.",
      "The numeric thresholds. They are a policy choice and were never approved.",
      "NO - awaiting an operator decision.",
      "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm",
      "Approve or amend the thresholds in SG-06 below. The evaluator already implements them and will fire automatically once a strategy is live.",
      "whether any strategy may ever be called live", "project owner")

    q("Q-07", "How many bets make a result interpretable?",
      "A 13-of-15 moneyline run looks like 86.7% skill and is entirely consistent with a coin flip at these prices.",
      f"At the Week 9 prices the break-even rate is {w9['breakeven_rate_at_prices']:.3f}; 13 of 15 wins gives a Wilson 95% interval of "
      f"[{w9['hit_rate_wilson95'][0]:.3f}, {w9['hit_rate_wilson95'][1]:.3f}] and a two-sided p of {w9['p_value_vs_breakeven']:.3f} against break-even.",
      "A sample size large enough to separate a 3% edge from zero. With ~150 games per week-priced slate, that is a season, not a week.",
      "YES - the arithmetic is settled. 15 cannot do it; the site now refuses to call anything an edge below 30 settled bets.",
      "https://www.itl.nist.gov/div898/handbook/prc/section2/prc231.htm",
      "Nothing to discover. The rule is implemented; the wait is calendar time.",
      "any claim of a profitable strategy before a season of data", "nobody - it is arithmetic")

    q("Q-08", "Which of the 14 published site surfaces is authoritative?",
      "A reader who finds two different Week 10 lines, or six suggestion registers, cannot act on either.",
      f"{len(crawl['findings'])} findings from a line-by-line crawl; F-02 records six suggestion registers and six question registers; "
      "F-03 records two independent Week 10 line originations that differ by a mean of 0.2 points and a max of 1.6 points on the same 13 games; "
      f"F-05 records {len([x for x in crawl['findings'] if x['id']=='F-05'])} navigation surfaces.",
      "A named canonical surface. This is a governance decision, not a data problem.",
      "NO - only the project owner can name it.",
      "https://github.com/sassnarep3-star/Own8",
      "See SG-07. Merging is not required: one canonical hub with explicit 'input' labels on the rest is enough.",
      "every downstream link, every reader, and the value of the whole site", "project owner")

    q("Q-09", "Do the official prices survive a two-way cross-check, or is the capture wrong?",
      "Every ROI number on this site rests on 29 transcribed price rows.",
      f"{ver['checks_passed']} of {ver['checks_total']} fresh re-verification checks passed today, including that the moneyline favourite agrees with the spread favourite "
      "on all 14 Week 10 games and that every two-way implied sum exceeds 1 (the book margin is present in the data).",
      "A second independent reader of the same page. One session transcribed the page once.",
      "PARTLY - internal consistency is verified; independent re-reading is not.",
      "https://www.nfl.com/news/nfl-picks-week-9-2026-nfl-season",
      "Have a second session re-transcribe one week from the same URL and diff it against market/data/raw/official-prices-w9.json. That is a 20-line script.",
      "confidence in every published ROI figure", "any second session")

    q("Q-10", "Is the Week 10 line set even comparable to the market?",
      "The difference between our handicap and the market's is the basis of every 'edge' column. If the two are on different scales, the column is meaningless.",
      "Our Week 10 home handicap and the market's, on the same row, in one convention, for 13 games. The market-implied handicap is derived through our own sigma, "
      "and where it disagrees with the published handicap the gap is our model's sigma, not the market being wrong.",
      "An independent estimate of the game-margin standard deviation from realised results rather than from the model's own training residuals.",
      "PARTLY - comparable in convention, not yet comparable in calibration.",
      "https://www.nfl.com/schedules/2026/by-week/week-10",
      "Estimate sigma from the realised margin distribution of the 136-game log and re-derive. ~10 lines of code, no new data.",
      "the 'difference' columns and any threshold set on them", "modelling owner")

    q("Q-11", "What is the reward, and is it real?",
      "The operator asked for rewards for top strategies. Any cash or property reward for forecasting contests carries legal exposure that varies by jurisdiction.",
      "Nothing. This repository has never awarded anything and contains no reward terms.",
      "A decision, and legal advice if the reward has value.",
      "NO - outside the scope of a data repository.",
      "https://wsgc.wa.gov/responsible-gaming-self-exclusion",
      "Decide whether rewards are paper points only. If paper, SG-05 needs no legal review. If not, stop and take advice.",
      "the entire competition layer", "project owner")

    # ------------------------------------------------------------------ suggestions
    S = []

    def s(sid, title, problem, options, recommendation, cost, gate_impact, verification, source, priority):
        S.append(dict(id=sid, title=title, problem=problem, options=options,
                      recommendation=recommendation, cost=cost, gate_impact=gate_impact,
                      verification_required=verification, source_url=source,
                      state="OPEN - FOR OPERATOR DECISION", priority=priority))

    s("SG-01", "Name one ranking quantity and retire the other three",
      "Four leaderboards rank on four quantities. A reward attached to loss-reduction is paid to a forecaster; a reward attached to ROI is paid to a staking run. Neither is 'skill' without a correction.",
      {"A": "Rank on the lower 95% bound of per-bet skill vs the de-vigged market price, after Holm. ROI is displayed and never ranked.",
       "B": "Rank on flat-stake ROI but require the lower bound of per-bet skill to exceed 0 as an entry gate.",
       "C": "Two boards: a Signal board (skill, ranked) and a Staking board (ROI, not ranked, no reward).",
       "D": "Leave all four in place and let the reader decide."},
      "C. It is the only option where a lucky staking run cannot mask a bad signal, and it is what the Week 9 data already shows: three moneyline strategies with identical +21.0% ROI and skill from -0.112 to +0.028.",
      "1 page of copy and a change to one ranking key. No new data.",
      "Decides whether any strategy can ever be 'ranked'. No gate is relaxed.",
      "Rank order must be reproducible byte-for-byte from market/data/tournament.json.",
      "https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm", "P1")

    s("SG-02", "Capture the price page twice a week to get a real opening and closing pair",
      "The site now has one price per game, locked Thursday 2 p.m. ET. It has no opening number and no closing number, so closing-line value - the standard test of whether a model adds anything - cannot be computed.",
      {"A": "Capture Tuesday and 90 minutes before kickoff, every week, and store both.",
       "B": "Capture only the Thursday-locked number and never claim closing-line value.",
       "C": "Capture every 6 hours and build a full price path."},
      "A. Two fetches a week, and it unlocks the single most respected test available without extra data.",
      "2 fetches per week, ~5 minutes, plus a small append-only store.",
      "Adds a real gate: a strategy must beat the closing number, not a mid-week number.",
      "Re-read the same page twice and confirm the numbers actually moved before claiming a close.",
      "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season", "P1")

    s("SG-03", "Replace the 'no official price exists' claim with the verified price rows",
      "ledger/data/price-snapshots.json, origination/results/w10-lines.json and the root dashboard all state that no official sportsbook line exists. That is now demonstrably false and it is the single most consequential wrong statement in the repository.",
      {"A": "Add the verified FanDuel rows from this session to the ledger price store, with the -110 spread/total assumption labelled as an assumption.",
       "B": "Leave the old files untouched and let market/ carry the prices, with a pointer.",
       "C": "Delete the blank rows."},
      "A, but only by that file's owner. This session did not edit another session's file (finding F-01).",
      "1 data merge plus a rebuild.",
      "Unblocks gates that were marked 'cannot be scored' purely for lack of a price.",
      "Every merged price must keep its source URL and lock time.",
      "https://www.nfl.com/news/nfl-picks-week-9-2026-nfl-season", "P1")

    s("SG-04", "Start the postgame Game Book collection to build a real replacement dataset",
      "The operator wants 2nd/3rd/4th-string tracking. Pregame depth order does not exist officially, so any pregame depth weight would be invented.",
      {"A": "Collect the Game Book PDF for all 14 Week 10 games, extract the 22 named starters per game, and join to the pregame injury report.",
       "B": "Wait until the season ends and collect retroactively.",
       "C": "Use a third-party depth chart."},
      "A. B loses the ability to test anything this season. C breaks the official-source rule the whole repository is built on.",
      "14 PDFs this week, then ~16 per week. Parsing is mechanical.",
      "Creates the only route to an injury adjustment that is measured rather than assumed.",
      "A replacement event must be supported by both an injury-report row and a Game Book starter line.",
      "https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf", "P1")

    s("SG-05", "Decide now whether rewards are paper-only",
      "Rewards are promised in the brief and nothing in the repository defines them. A forecasting contest with a thing of value attached is regulated activity in some jurisdictions.",
      {"A": "Paper points only, no transferable value, stated on every page.",
       "B": "Real reward, with legal review before any rule is written.",
       "C": "Drop rewards entirely and keep the leaderboard as a research ranking."},
      "A or C. Both are safe today; B needs advice before a single line of code.",
      "Copy only for A/C.",
      "Determines whether the competition layer may exist at all.",
      "The published rules must match what the code actually pays out.",
      "https://wsgc.wa.gov/responsible-gaming-self-exclusion", "P1")

    s("SG-06", "Approve the demotion thresholds so a live strategy can be sent back to paper",
      "Rules D1-D8 exist and are tested, but no threshold was ever approved, so the gate cannot fire.",
      {"A": "Demote when the lower 95% bound of per-bet skill is below 0 over the last 40 priced bets.",
       "B": "Demote on a drawdown of 20 units.",
       "C": "Demote when the strategy's Brier score is worse than the de-vigged market over 40 bets.",
       "D": "Never demote."},
      "A and C together. B is a staking rule and belongs on the staking board, not the signal board.",
      "One config change; the evaluator already implements all of them.",
      "Makes the live/paper distinction real rather than decorative.",
      "Re-run the 23 existing unit tests after the thresholds change.",
      "https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm", "P2")

    s("SG-07", "Publish one canonical hub and label everything else as an input",
      "Fourteen site surfaces, six suggestion registers and two Week 10 line sets. A reader cannot tell which number to believe.",
      {"A": "market/ becomes the canonical decision surface and every other namespace keeps its own pages, linked and labelled 'input'.",
       "B": "Merge everything into the root dashboard.",
       "C": "Leave as is and add a disclaimer."},
      "A. It is the only option that needs no deletion and no cross-session edit.",
      "One navigation change plus labels.",
      "Governance only; no numbers change.",
      "Every canonical page must state its as-of date and the official URL behind it.",
      "https://github.com/sassnarep3-star/Own8", "P1")

    s("SG-08", "Estimate sigma from realised results before publishing any more 'implied' numbers",
      "The market-implied handicap is produced by running a probability through our normal model. If sigma is wrong, the implied column is wrong and the difference column is wrong with it.",
      {"A": "Estimate sigma from the realised margin distribution of the 136-game log and re-derive, showing both.",
       "B": "Keep the model-residual sigma and label the column 'model-implied'.",
       "C": "Drop the implied column and publish only the market's own numbers."},
      "A, with C as the fallback if the two sigmas disagree materially.",
      "~10 lines of code, no new data.",
      "Improves the credibility of every difference column.",
      "Both sigmas must be printed side by side.",
      "https://www.nfl.com/scores/2026/week-9", "P2")

    s("SG-09", "Re-transcribe one price week independently and diff it",
      "Twenty-nine price rows were read once, by one session. Internal consistency is verified; independent reading is not.",
      {"A": "A second session re-reads Week 9 and diffs against the stored file.",
       "B": "Accept the single reading."},
      "A. It is twenty lines of code and it is the difference between a verified figure and a believed one.",
      "Small.",
      "Protects every ROI number on the site.",
      "Zero differences, or a published diff.",
      "https://www.nfl.com/news/nfl-picks-week-9-2026-nfl-season", "P2")

    s("SG-10", "Kill or clearly mark the superseded snapshots",
      "data/audit-snapshot-2026-11-04.json, data/scores-2026-week8.json, data/standings-2026-reg-w8.json and analysis/model-lines.json still exist and are still linked from older pages.",
      {"A": "Move them to archive/ and add a redirect.",
       "B": "Add a banner to every page that renders them.",
       "C" : "Leave them."},
      "A. The repository already has an archive/ convention.",
      "Small.",
      "Prevents a reader acting on a two-week-old number.",
      "No live page may reference a superseded file.",
      "https://www.nfl.com/standings/league/2026/REG", "P2")

    s("SG-11", "Add a parlay and prop price source, or state plainly that combos cannot be priced",
      "Parlays and prop combos are half the operator's brief and cannot be scored at all, because no official source publishes their prices.",
      {"A": "State plainly, everywhere a combo is mentioned, that it is unpriceable from official sources.",
       "B": "Adopt a non-official price source and label every derived number as non-official.",
       "C": "Drop combos from the brief."},
      "A. B breaks the evidence rule the repository is built on; C throws away a real research direction.",
      "Copy only for A.",
      "Keeps S9-S12 correctly unscored instead of quietly estimated.",
      "Any page mentioning a combo must carry the 'unpriceable' label.",
      "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season", "P2")

    s("SG-12", "Put the sample size on the face of every number",
      "The site has 13-of-15 results that look extraordinary and are not. A reader will still believe them unless n is in the same glance.",
      {"A": "Every ROI and hit rate prints n and a verdict word next to it.",
       "B": "A footnote at the bottom of the page."},
      "A. It is already implemented in this workspace's tables; it needs to be the house style everywhere.",
      "Copy and one table template.",
      "None. It only stops overclaiming.",
      "Spot-check 10 rows: each must show n.",
      "https://www.itl.nist.gov/div898/handbook/prc/section2/prc231.htm", "P3")

    # recommended path
    path = dict(
        headline="The shortest defensible path to a competition that rewards skill rather than luck",
        steps=[
            "SG-05 first, because it decides whether the competition may exist at all. Paper points only.",
            "SG-01 second, because a reward needs a ranking quantity and there are currently four.",
            "SG-03 third, because the repository's central claim about prices is now wrong and everything downstream inherits the error.",
            "SG-02 and SG-04 in parallel, because they are the only two things that add real information rather than rearranging what exists.",
            "SG-06 and SG-07 last, because a demotion gate and a canonical hub are only meaningful once there is something to demote and somewhere to read it.",
        ],
        what_not_to_do=[
            "Do not promote any strategy to live before 60 priced games are scored (Q-07).",
            "Do not attach a reward to ROI alone (SG-01).",
            "Do not use a third-party depth chart to fill the injury gap (SG-04).",
            "Do not adopt a blend weight fitted on 15 games (own-lines blend analysis).",
        ])

    out = dict(generated="2026-11-14", generated_by="session 949f49b0",
               how_to_use="Every question is answerable-or-not from information that exists today. Every suggestion is un-implemented. Choose a path, then implement; do not implement, then choose.",
               counts=dict(questions=len(Q),
                           answerable_now=sum(1 for x in Q if x["answerable_from_current_information"].startswith("YES")),
                           partly=sum(1 for x in Q if x["answerable_from_current_information"].startswith("PARTLY")),
                           not_answerable=sum(1 for x in Q if x["answerable_from_current_information"].startswith("NO")),
                           suggestions=len(S)),
               questions=Q, suggestions=S, recommended_path=path)
    (MARKET / "data" / "decision-gate.json").write_text(json.dumps(out, indent=1) + "\n")
    c = out["counts"]
    print(f"questions {c['questions']} (yes {c['answerable_now']}, partly {c['partly']}, no {c['not_answerable']}), suggestions {c['suggestions']}")


if __name__ == "__main__":
    main()
