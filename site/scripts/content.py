#!/usr/bin/env python3
"""Writes the register content (requirements, questions, suggestions, flags, sources, repo review).

Every row is either (a) an official nfl.com URL that was read on 2026-11-17, (b) a repository
artifact (a derived calculation or an inherited artifact, labelled as such), or (c) a statement
that no source exists (status BLOCKED / NOT STARTED). Nothing here is inferred from memory.
"""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(ROOT, "site", "data")
FETCH = "2026-11-17"
REPO = "https://github.com/sassnarep3-star/Own8/blob/main/"
OFF = dict(
    standings="https://www.nfl.com/standings/league/2026/REG",
    scores="https://www.nfl.com/scores/2026/week-10",
    sched11="https://www.nfl.com/schedules/2026/by-week/week-11",
    sched10="https://www.nfl.com/schedules/2026/by-week/week-10",
    inj10="https://www.nfl.com/injuries/league/2026/reg10",
    inj11="https://www.nfl.com/injuries/league/2026/reg11",
    depthTEX="https://www.nfl.com/teams/houston-texans/depth-chart",
    picks10="https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season",
    colts_game="https://www.nfl.com/games/colts-at-texans-2026-reg-11",
)

# ---------------------------------------------------------------- requirements
# status vocabulary: DONE | PARTIAL | BLOCKED | NOT STARTED | NOT DONE | REJECTED | NOT POSSIBLE AS STATED | DECISION NEEDED
REQ = [
 # id, group, requirement (operator brief, short), status, what exists (repo path or URL), gap / blocker, source
 ("R-01","Data","Official results feed so backtests and ROI can be computed","PARTIAL","site/data/week10-results.json (13 finals) + origination/data/games-2026-w1-w9.json (136 games)","Week 10 Monday game (LAC@BAL) is not final on nfl.com as read; ROI needs a settled price series with stakes, which does not exist.",OFF["scores"]),
 ("R-02","Data","Verified standings reconciled to the game log","DONE","site/data/standings-2026-11-17.json: 160/160 cells (W, L, T, PF, PA) match the 136-game log plus 13 Week 10 finals","Reconciliation excludes the unfinished Monday game, as nfl.com shows it.",OFF["standings"]),
 ("R-03","Data","All 14 Week 10 games read as final","PARTIAL","13 of 14 read as FINAL on nfl.com","LAC@BAL shows 8:15 PM with no score on the scores, standings and picks pages as read (F-04).",OFF["scores"]),
 ("R-04","Injuries","Official NFL injury report captured and republished","PARTIAL","Week 10 report page 1 of 8 re-read 2026-11-17; Lions rows verified (see R-05)","Full 8-page re-capture not completed this session; five earlier captures disagree on row counts (F-05).",OFF["inj10"]),
 ("R-05","Injuries","Populate the three missing Lions game-status cells (Joseph, Mays, Reed)","DONE","Verified 2026-11-17: all three show Out (Knee, Ankle, Hip; Did Not Participate)","None for these three rows.",OFF["inj10"]),
 ("R-06","Injuries","Week 11 injury report captured","BLOCKED","Probe 2026-11-17: the reg11 URL serves Week 10 content; the Colts game centre says the injury report is not yet available","Not published as of read. Re-check Wed 18, Thu 19, Fri 20 Nov (F-07).",OFF["inj11"]),
 ("R-07","Injuries","Every injury-hub read stored with its clock time; publish the delta, never the level","NOT STARTED","Single-time captures only","No time series exists, so no delta can be computed.",OFF["inj10"]),
 ("R-08","Injuries","Immutable daily snapshots Wed to kickoff with raw hashes","NOT STARTED","None (see S-04)","No scheduler is configured for nfl.com capture; the sandbox cannot curl nfl.com (SSL error on 2026-11-17), so captures are fetch-tool transcriptions only.",OFF["inj10"]),
 ("R-09","Injuries","Treat the injury report as a timestamped series; measure DNP to LP to FP evolution","NOT STARTED","None","Requires R-08.",OFF["inj10"]),
 ("R-10","Injuries","Injury signal as a surprise (change), never a level","BLOCKED","None","Requires R-07 to R-09 (a change needs two timestamped reads).",""),
 ("R-11","Injuries","Immutable official availability snapshots (injury reports, depth pages, inactives) with raw hashes, timestamps and conflict flags","NOT STARTED","None","Requires R-08 and a depth source (R-23).",""),
 ("R-12","Injuries","Point-in-time ledger for injuries, depth and inactives (no lookahead)","NOT STARTED","None","Requires R-11.",""),
 ("R-13","Injuries","Official inactive lists and snap counts captured","BLOCKED","None captured. No official snap-count source was located or verified in this session","Source unknown (Q-03).",""),
 ("R-14","Injuries","Official NFL Game Books used for actual starters and game-day status (no inference)","BLOCKED","None captured","Game Books publish after kickoff; the repo's own README (section 'What changed on 2026-11-15', RQ-12) estimates 6 to 8 game-weeks of postgame Game Books before a test is possible.",""),
 ("R-15","Injuries","Archive weekly injury reports for past seasons","NOT STARTED","Only 2026 Week 10 and earlier 2026 weeks in the repo","Past-season archive not captured (Q-04).",""),
 ("R-16","Injuries","Calibrate what 'Questionable' means from play rates with confidence intervals","BLOCKED","None","Requires R-14 and R-15. Official text gives no percentages.",""),
 ("R-17","Injuries","Designation reliability scored before a designation becomes a model feature","BLOCKED","None","Requires R-15 and R-13.",""),
 ("R-18","Schedule","Venue of every fixture transcribed from the official game centre and published","PARTIAL","1 of 13 Week 11 venues verified: IND@HOU, Reliant Stadium, Houston, TX (game centre)","12 venues blank: not transcribed this session.",OFF["colts_game"]),
 ("R-19","Schedule","Dated schedule announcement published beside the live schedule page","PARTIAL","nfl.com Week 11 schedule page (read 17 Nov) states that the Week 16, 17 and 18 designated matchups have TBD dates: Week 16 no later than immediately after Week 14, Week 17 no later than immediately after Week 15, Week 18 after Week 17 (quoted on data-schedule.html)","No dated announcement was located on the captured pages.",OFF["sched11"]),
 ("R-20","Schedule","Fixture-context features built only from published schedule facts","NOT STARTED","Schedule facts captured for Week 11 (13 games, 6 byes, kickoff times, networks)","No feature set built.",OFF["sched11"]),
 ("R-21","Schedule","Stadium roof/surface and NWS hourly wind/precipitation overlay","NOT STARTED","None","No official roof designation or NWS grid captured.",""),
 ("R-22","Depth","Official depth-chart register with date and source per row","BLOCKED","None","nfl.com team depth-chart page returns 404 (Texans probe, 2026-11-17).",OFF["depthTEX"]),
 ("R-23","Depth","Depth order from per-club official pages, verified for all 32 clubs (route a) or from official snap counts (route b)","BLOCKED","Route a: 404 on the one club probed. Route b: no official source verified","Neither route verified for all 32 clubs. The backup-deficiency feature cannot be built until one is (S-03).",OFF["depthTEX"]),
 ("R-24","Depth","Fix the two depth-parsing failures (Texans image; Packers jersey prefixes)","BLOCKED","No depth page is parsed in this repo","The Texans image needs an authorised structured source; transcription by eye is not allowed.",""),
 ("R-25","Depth","Depth slots modelled as groups (ties, shared slots, empty slots)","NOT STARTED","Design requirement only","No depth data.",""),
 ("R-26","Depth","Depth modelled from playing time (snap share), not jersey order","NOT STARTED","No snap data","Compliant so far: this session derives no depth order from jersey, experience or salary.",""),
 ("R-27","Depth","Backup-deficiency feature (2nd to 4th string replacing starters, both sides of the ball)","BLOCKED","None","Requires R-22 to R-26.",""),
 ("R-28","Depth","Offense vs defense matchup deficiency matrix (1st to 4th string)","BLOCKED","None","Requires R-22.",""),
 ("R-29","Depth","Per-team view: starters out, replacements named, net injury count","BLOCKED","Team view not built","Requires R-22 and R-06.",""),
 ("R-30","Depth","Announced-starter evidence field (not an inferred replacement)","NOT STARTED","None","The brief cites Lock, McCord and Brissett as VR-24, VR-25, VQ-05. Those identifiers are not in the repo and were not found on nfl.com (F-22).",""),
 ("R-31","Depth","Flag stale depth rows against the official transactions log","BLOCKED","None captured. The nfl.com picks article read 2026-11-17 says Lamar Jackson is on IR (quoted, not a transactions record)","No transactions capture; no depth row to test.",OFF["picks10"]),
 ("R-32","Depth","Roster turnover as a first-class data event (depth versioned to the last official roster event)","NOT STARTED","None","Requires a transactions capture (Q-18).",""),
 ("R-33","Depth","Shared and empty depth slots represented faithfully","BLOCKED","None","Requires R-22.",""),
 ("R-34","Depth","Reject depth order from jersey number, experience or salary","REJECTED","Policy recorded here; nothing built on it","Operator's rejection honoured.",""),
 ("R-35","Depth","Run the 32-team roster/IR sweep before any team-level model is trusted","NOT STARTED","Not run. B0 is team-strength only","Gate not cleared. B0 must not be read as injury-aware.",""),
 ("R-36","Models","Injury and personnel ablations instead of fixed penalties (with and without features, chronological holdouts)","BLOCKED","None","No personnel features exist to ablate (R-22, R-13).",""),
 ("R-37","Models","Injury and depth ablations, not fixed penalties","BLOCKED","None","As R-36.",""),
 ("R-38","Models","Ratings made opponent-aware from game-level results","PARTIAL","Repo variants S1/S2 (ridge) use game-level results (origination/results/validation-w10.json). B0 uses unadjusted PF/PA averages","The published B0 baseline is NOT opponent-adjusted.",""),
 ("R-39","Models","Singles-only shadow baseline, pre-registered, versions frozen, forecasts recorded before kickoff","PARTIAL","B0 (site/scripts/model_b0.py). Week 10 lines: originated_at 2026-11-14 in requirements/results/week10-lines.json. Week 11 lines written in beca9d2 on 2026-11-17 from PRE-MONDAY standings (provisional, F-23)","Baseline is team-strength only (see R-35).",""),
 ("R-40","Models","Store every model output as a probability plus its inputs, not only a pick","DONE","B0 outputs store H, A, margin, total and p_home with their standings inputs (site/data/b0-*.json)","Repo-wide coverage is PARTIAL (older files store picks in places).",""),
 ("R-41","Models","Originate the side first, then the total, then the moneyline","DONE","B0 computes margin (side) first, then total, then p_home (site/scripts/model_b0.py)","","" ),
 ("R-42","Models","Price a line ourselves and publish the residual against the market on a schedule from day one","PARTIAL","Week 10: 12 settled games graded against nfl.com prices (site/data-lines.html). Week 11: fair lines frozen, market not captured","No schedule automation. Week 11 market values are blank (F-11).",OFF["picks10"]),
 ("R-43","Models","Publish fair line, market line and difference as separate columns","DONE","Week 10 lines page: fair, market and difference in separate columns (12 settled games). Week 11 page shows fair only","Week 11 market and difference columns blank (no verified capture).",OFF["picks10"]),
 ("R-44","Models","Vig-free market consensus vs originated fair-line decomposition","DONE","Week 10 de-vigged market probabilities (proportional method) next to B0 probabilities, per game","Week 10 only.",OFF["picks10"]),
 ("R-45","Models","Publish every model total twice until one estimator wins (with a gap column)","PARTIAL","Repo has two estimators for Week 10 totals (S4 and S5 in origination/results/w10-lines.json); the site shows B0 only","Second estimator not yet on the site.",""),
 ("R-46","Models","Turn the 136-game log into the pre-registered backtest corpus","PARTIAL","136-game log reconciles to the standings (R-02)","The log was not frozen before it was used, so it cannot count as pre-registered.",""),
 ("R-47","Models","Split data into train, validation and final-holdout seasons","BLOCKED","Only the 2026 season is in the repo","Requires prior seasons (Q-14).",""),
 ("R-48","Models","Weekly 'what changed' diff (rank, rating, availability)","NOT STARTED","Two snapshots exist (repo 2026-11-14 raw; this session 2026-11-17) but no diff is rendered","Requires a snapshot store (R-41).",""),
 ("R-49","Models","Onside-kick regime priors filter for 2026 kickoffs","NOT STARTED","None","No official rule or data captured.",""),
 ("R-50","Models","Parlays and prop combos behind a joint-evidence gate","DONE","Gate G7/G8 defined; combos registered as NOT SCORED (no official joint or prop prices)","No combo can be ranked.",""),
 ("R-51","Correlation","Correlation values from officially sourced numbers only, with n published","PARTIAL","Nine descriptive correlations with n and 95% CI (origination/results/correlations.json; see correlations.html)","Leg-level dependence is not published officially, so parlay correlations stay blank. C2 is not Holm-significant (F-13).","" ),
 ("R-52","Leaderboard","Pre-register every strategy; backtest numbers never appear on the leaderboard","PARTIAL","Registry of 14 strategies (ledger/data/strategy-registry.json); this site shows none on a leaderboard","Four strategies carry PAPER-ELIGIBLE labels built on backtest gates (F-01). Operator ruling needed (Q-08).",""),
 ("R-53","Leaderboard","Freeze a rule before it sees data; the commit hash is the registration","DONE","B0 Week 11 at commit beca9d2 (2026-11-17), before Thu 2026-11-19 kickoff","","" ),
 ("R-54","Leaderboard","Two-sided 'what would change our mind' field on every strategy entry","NOT DONE","Checked the 14 registry entries: no such field exists (key listing, ledger/data/strategy-registry.json)","Field to be added; not inferred.",""),
 ("R-55","Leaderboard","Demotion gate that sends a live strategy back to paper","DONE","ledger/data/demotion-rules.json; ledger/scripts/demotion_gate.py","No live strategy exists, so no demotion has been applied.",""),
 ("R-56","Leaderboard","Signal separated from staking on the leaderboard","PARTIAL","ledger/results/leaderboard-split.json","No staking rule is pre-registered and no staking run exists.",""),
 ("R-57","Leaderboard","Proper-score divisions: singles, game parlays, same-game parlays, prop combos","PARTIAL","Divisions defined in the ledger registry","Only singles have scored entries; the others are NOT SCORED or BLOCKED.",""),
 ("R-58","Leaderboard","Rank by benchmark-relative Brier skill with a game-cluster lower bound and multiplicity adjustment","PARTIAL","Brier skill and bootstrap CI for Week 10 B0 (site/data/b0-w10-grading.json); family-wise Holm adjustment in origination/results/validation-w10.json (family of 12)","Game-cluster lower bound not computed for the site; no leaderboard.",""),
 ("R-59","Leaderboard","Two-stage leaderboard: proper-score qualification, then prospective CLV/ROI escrow","BLOCKED","Stage 1 numbers exist for backtests only","Stage 2 needs a closing-line source (R-60).",""),
 ("R-60","Leaderboard","Opening and closing numbers stored for every market originated","PARTIAL","87 locked nfl.com FanDuel line snapshots, Weeks 9 to 10 (ledger/data/price-snapshots.json)","No official opening or closing series located (Q-01). Opening and closing cells stay blank.",OFF["picks10"]),
 ("R-61","Leaderboard","Control baselines (random picks; favourites only) on every leaderboard run","PARTIAL","Coin-flip Brier control (0.25) for Week 10 B0 (site/data/b0-w10-grading.json)","Favourites-only and random-pick simulations not run.",""),
 ("R-62","Leaderboard","'Removal of luck' panel on the dashboard","NOT POSSIBLE AS STATED","Uncertainty intervals shown instead (correlations.html, data-lines.html)","Luck cannot be removed from a finite sample (repo register RQ-10). Re-scoped to uncertainty.",""),
 ("R-63","Leaderboard","Strategies that are selectively skill-based (luck removed)","NOT POSSIBLE AS STATED","No strategy passes against the market","As R-62. Re-scoped to pre-registered tests with uncertainty.",""),
 ("R-64","Leaderboard","Reward top-performing strategies","DECISION NEEDED","No reward rule exists; repo policy: paper points only, none awarded","Operator must define the reward (S-09).",""),
 ("R-65","Leaderboard","Reject ranking strategies by season-long ROI","REJECTED","Policy recorded; ROI is not used for ranking","Operator's rejection honoured.",""),
 ("R-66","Leaderboard","Ratings and leaderboards use only verified data; every row has a source","PARTIAL","Applied on all new pages; inherited pages (root, legacy namespaces) not re-verified","See repo-review.html and F-09.",""),
 ("R-67","Governance","Official-source link on every table row; blank and flagged if unverified","PARTIAL","Applied on the pages in this site","Derived model rows carry 'model output, not official' and link their inputs.",""),
 ("R-68","Governance","Public analysis layer separated from a private raw-data layer until nfl.com terms are read","DECISION NEEDED","Current site republishes nfl.com standings and scores in table form","Terms not read (Q-10). Options in S-05.",""),
 ("R-69","Governance","Durable snapshot storage outside the static site; freshness monitoring; alerts on source or schema change","NOT STARTED","None. Repo CI runs checks but no alerting","Store and alert channel are operator decisions (Q-13, S-04).",""),
 ("R-70","Governance","Drift alarm on every scraper (pinned row counts and fields; fail loudly)","NOT STARTED","No scrapers. Transcriptions in site/data carry explicit row-count and sum checks (site/check.py)","Automated scrapers do not exist.",""),
 ("R-71","Governance","Suggestions section where the operator chooses the path before anything is implemented","DONE","site/suggestions.html (10 items, each awaiting a choice)","","" ),
 ("R-72","Governance","Open questions register: what is known, what is missing, how to answer","DONE","site/questions.html","","" ),
 ("R-73","Governance","Decision-readiness table, one row per requirement, with the gate and the number that clears it","DONE","site/requirements.html (every register row carries its gate and clearing condition)","","" ),
 ("R-74","Governance","Executive summary","DONE","site/executive-summary.html","","" ),
 ("R-75","Governance","GitHub Pages landing page with category subpages; tables with source links; simple to read","DONE","site/index.html and category pages (see README)","Deployment confirmed only after merge (R-80).","" ),
 ("R-76","Governance","Flagged for Review page with source links for irregularities and unverified items","DONE","site/flagged.html","","" ),
 ("R-77","Governance","Repo review line by line, flagging irregularities","PARTIAL","site/repo-review.html covers the items the session checked; roughly 600 non-archive files were not read line by line","Stated limit.","" ),
 ("R-78","Governance","Parallel sessions coordinated through COORDINATION.md","DONE","Claim and log recorded on the board (875583e4)","Pinned branch used per session rules; session-<id>/<task> names not used.","" ),
 ("R-79","Governance","Pull request to main, merged without waiting, Pages deploy confirmed, record kept","PENDING","Scheduled as the last step of this session","Result is recorded on the board and on the Flagged page once it happens.","" ),
 ("R-80","Governance","No manual input from the operator needed to finish all tasks","PARTIAL","Session in progress (claim 875583e4 in COORDINATION.md); not complete until the PR is merged and Pages confirmed","Ten suggestions need an operator choice; several blocked items need a source decision (Q-02, Q-03, Q-10).","" ),
]

# ---------------------------------------------------------------- questions
QUESTIONS = [
 ("Q-01","Does any official source publish opening and closing prices for each market?","Locked Thursday 2 PM ET nfl.com picks-article lines (FanDuel), 87 snapshots W9 to W10","No open or close series located","Check nfl.com picks articles over time; decide licensed-feed option (S-01)","R-60, R-59"),
 ("Q-02","Which official source gives depth order for all 32 clubs?","One club's depth page probed: 404 (2026-11-17)","Any verified per-club depth page; any authorised structured feed","Probe all 32 club depth routes; ask the operator whether an authorised feed can be licensed (S-03)","R-22, R-23, R-27"),
 ("Q-03","Does an official snap-count source exist, for all 32 clubs?","Nothing captured","Source, format and coverage unknown","Locate the official snap-count page; verify 32 clubs (route b)","R-13, R-23, R-26"),
 ("Q-04","Do designations change game outcomes or play rates?","2026 Week 10 report only","Archived reports and inactive lists for past seasons","Feasibility probe for an archive of past weekly reports (S-08)","R-15, R-16, R-17"),
 ("Q-05","Is the Week 10 Monday game final?","nfl.com pages as read show no score","A final score on nfl.com","Re-read the scores page after the operator confirms; this moves 12 graded games to 13 and changes W11 inputs (F-04)","R-01, R-03"),
 ("Q-06","What is the correct Week 10 injury row count?","Five captures with different counts (F-05)","One complete 8-page capture reconciled to one count","Full re-capture of reg10 (8 pages), hashed and dated","R-04"),
 ("Q-07","What do the Week 11 injury designations say?","Week 11 content present on official URL when re-read 2026-11-18; no raw capture","Week 11 report content","Re-read Wed 18, Thu 19 and Fri 20 Nov, with fetch times","R-06"),
 ("Q-08","May backtest-gate passes appear on the leaderboard?","Four strategies pass G1 to G8 on a walk-forward backtest (n=104 game-evaluations, W3 to W9)","Operator ruling on the rule 'backtest numbers never appear on the leaderboard'","Operator decision (S-02)","R-52"),
 ("Q-09","Does the model beat the market, with enough sample to say so?","Week 10, 12 games: no significant difference in spread or moneyline error (site/data-lines.html)","Prospective sample of about 80 singles games (the repo's own G3 threshold)","Keep locking lines each week (S-07); no conclusion before the sample size","R-42, R-58, R-59"),
 ("Q-10","Can nfl.com-derived standings, scores and prices be republished?","Pages are public; terms not read in this session","nfl.com terms of use reading and an operator ruling","Read nfl.com terms (operator or counsel); then decide S-05","R-68"),
 ("Q-11","What is the reward for a top-performing strategy?","Repo policy: paper points only, none awarded","An operator-defined reward","Operator definition (S-09)","R-64"),
 ("Q-12","Where should immutable snapshots live, and who gets alerts?","Git only (this repo)","A durable store and an alert channel","Operator choice (S-04)","R-69, R-08"),
 ("Q-13","Which seasons form train, validation and holdout?","2026 only in the repo","Earlier seasons, archived","Archive capture decision (S-08)","R-47"),
 ("Q-14","Which official page defines an 'announced starter'?","None identified","An official page that names starters for each game","Identify the page; capture it with a timestamp","R-30"),
 ("Q-15","What do the VR-xx and VQ-xx identifiers in the brief refer to?","Only VR-08 and VR-12 found in earlier repo registers; the other 14 cited identifiers are not in the repo (grep, 2026-11-17)","The source document for those identifiers","Operator to supply the document or confirm they can be dropped","R-30, R-31"),
 ("Q-16","What are the venues of the remaining Week 11 games?","1 of 13 verified (IND@HOU)","Game-centre venue for each of 12 games","Read each game-centre page (one fetch per game)","R-18"),
 ("Q-17","Do trades and releases change depth rows?","Brief cites a Colts trade and a Ravens QB situation; not verified in this session","Official transactions records dated to each change","Capture nfl.com transactions with dates; reconcile to depth rows","R-32, R-31"),
 ("Q-18","Which onside-kick rule regime applies for 2026?","None captured","Official rule text and any declared regime","Official rules capture (NFL rule book), dated","R-49"),
 ("Q-19","Does a 2-point gap between two totals estimators matter?","Week 10 B0 vs repo S4/S5 estimators (origination file)","Walk-forward comparison result that picks one","Run the walk-forward comparison once more games settle","R-45"),
 ("Q-20","Is the B0 team-strength baseline acceptable before the 32-team sweep?","B0 is team-strength only","An operator ruling and the sweep result","Operator decision after the sweep (S-06)","R-35"),
]

# ---------------------------------------------------------------- suggestions
SUGGESTIONS = [
 dict(id="S-01", title="Price-data policy (must be decided before any backtest is published)", requirement="R-60, R-59, R-42",
  options=[
   dict(label="A. Official-only", text="Keep nfl.com locked-Thursday FanDuel lines as the only market input; publish no opening or closing values; no CLV claims.", cost="Low (already built)", risk="Cannot measure closing-line value; grading uses one lock time."),
   dict(label="B. Licensed odds feed", text="License a feed that records opening and closing numbers for every market, with its terms reviewed first.", cost="Recurring fee; terms review", risk="Terms and licence need operator approval; not verifiable from this sandbox."),
   dict(label="C. Hybrid", text="Official-only for grading now; a licensed feed for CLV research only, labelled separately.", cost="Medium", risk="Two price series to keep consistent."),
  ], recommendation="A now; decide B before any CLV claim is published.", decision="Choose A, B or C."),
 dict(id="S-02", title="Leaderboard eligibility of the four backtest-gate passes (S6, S1, S7, S2)", requirement="R-52, F-01",
  options=[
   dict(label="A. Keep off the leaderboard", text="Show them as backtest-only candidates; no rank until prospective weeks settle (the operator's rule).", cost="None", risk="Slower; consistent with the rule."),
   dict(label="B. Two-stage admission", text="Admit the walk-forward result as stage 1 with a prospective escrow stage 2. This requires changing the operator's rule.", cost="Operator rule change", risk="Backtest numbers would appear on the leaderboard, which the rule forbids."),
   dict(label="C. Retire", text="Withdraw the four strategies and keep only B0 as the shadow baseline.", cost="None", risk="Loses the walk-forward work."),
  ], recommendation="A.", decision="Choose A, B or C."),
 dict(id="S-03", title="Depth-order source (route a per-club pages, route b snap counts, or a licensed structured feed)", requirement="R-22, R-23, R-27",
  options=[
   dict(label="A. Verify route a club by club", text="Probe all 32 club depth routes; keep only those that load and parse. The one probed route (Texans) returns 404.", cost="32 probes, then parsing work", risk="Pages may not exist for every club."),
   dict(label="B. Verify route b snap counts", text="Locate an official snap-count source for all 32 clubs; derive starter share from it.", cost="Discovery work", risk="No official source has been confirmed to exist."),
   dict(label="C. Licensed structured feed", text="Operator authorises a structured depth feed; no transcription by eye.", cost="Recurring fee; authorisation", risk="Terms and provenance need review."),
  ], recommendation="Run the route b discovery first (cheap), then A; C only if A and B fail.", decision="Choose the order, or choose C."),
 dict(id="S-04", title="Automated, immutable availability snapshots (Wed to kickoff) with alerts", requirement="R-08, R-11, R-69",
  options=[
   dict(label="A. Scheduled GitHub Actions capture", text="A cron job captures the injury report and any depth page daily Wed to Sat, stores raw bytes and SHA-256 hashes in git, and fails loudly on a row-count or field change.", cost="Low; uses existing CI", risk="Not testable from this sandbox (nfl.com unreachable by curl); may be blocked by nfl.com bot rules; needs a test run."),
   dict(label="B. External durable store", text="Same capture, stored in an external bucket outside the static site, with alert email on failure.", cost="Storage cost; account setup", risk="Needs an account and credentials; operator must provide."),
   dict(label="C. Manual fetches", text="Operator-run or session-run fetches on set days.", cost="Staff time", risk="Gaps in the series; breaks the no-manual-input rule."),
  ], recommendation="A, with B for long-term storage.", decision="Choose A, B or C, and name the alert channel."),
 dict(id="S-05", title="Public analysis layer vs private raw-data layer", requirement="R-68, Q-10",
  options=[
   dict(label="A. Derived only until terms are read", text="Publish indices, model output and links; keep row-level copies of nfl.com data out of the public site.", cost="Low", risk="Less visible raw evidence for reviewers."),
   dict(label="B. Keep current publication", text="Publish the nfl.com-derived tables as they are.", cost="None", risk="Possible terms conflict until the terms are read."),
   dict(label="C. Hybrid", text="Publish short extracts with links; keep full tables private.", cost="Medium", risk="Still needs the terms reading."),
  ], recommendation="A until the nfl.com terms are read.", decision="Choose A, B or C."),
 dict(id="S-06", title="Roster sweep before the team-level model is trusted", requirement="R-35, Q-20",
  options=[
   dict(label="A. Run the 32-team sweep first", text="Capture each team's roster and IR status before any team-level claim; use B0 only as a team-strength baseline until then.", cost="32 captures", risk="Depends on S-03 and R-08."),
   dict(label="B. Accept B0 as is, labelled", text="Keep B0 published as team-strength only, with the sweep listed as NOT RUN.", cost="None", risk="Readers may over-read the baseline."),
  ], recommendation="B now, A before any injury-aware claim.", decision="Choose A or B."),
 dict(id="S-07", title="Weekly locked-line schedule and a second total estimator", requirement="R-42, R-45, Q-09",
  options=[
   dict(label="A. Lock every week, publish both totals", text="Originate lines before each Thursday lock, publish both total estimators with the gap column, and grade after finals.", cost="Weekly operator review", risk="Small samples for a long time."),
   dict(label="B. Lock only when a market capture exists", text="Originate only when the nfl.com picks article is captured.", cost="Lower", risk="Gaps in the record."),
  ], recommendation="A.", decision="Choose A or B."),
 dict(id="S-08", title="Archive past-season injury reports for designation calibration", requirement="R-15, R-16, R-17, Q-04",
  options=[
   dict(label="A. Probe the archive, then capture", text="Test whether nfl.com archive pages for past weeks exist; if they do, capture a fixed window with hashes.", cost="Probe first, then capture", risk="Archive may be unavailable."),
   dict(label="B. Use 2026 only", text="Accept the small 2026 sample; report the calibration as not estimable.", cost="None", risk="No power to calibrate."),
  ], recommendation="A (probe first).", decision="Choose A or B."),
 dict(id="S-09", title="Definition of a reward for top strategies", requirement="R-64, Q-11",
  options=[
   dict(label="A. Paper points only", text="Points on a paper leaderboard; no money; no awards until gates pass.", cost="None", risk="Low motivation."),
   dict(label="B. No rewards", text="Remove the reward concept from the leaderboard.", cost="None", risk="Departs from the brief."),
  ], recommendation="A.", decision="Choose A or B (C is not offered: money-linked rewards conflict with the repo's responsible-research policy)."),
 dict(id="S-10", title="Legacy namespaces: 15 parallel dashboards and duplicate copies", requirement="R-66, F-09",
  options=[
   dict(label="A. Mark superseded, keep in place", text="Add a banner to each legacy root page pointing at this site; change nothing else.", cost="Low", risk="Clutter remains."),
   dict(label="B. Move to archive/", text="Move legacy namespaces under archive/ (no deletion), keep links working via redirects.", cost="Medium", risk="Moves can break cross-links; needs a link check."),
  ], recommendation="A now; B after the operator approves.", decision="Choose A or B."),
]

# ---------------------------------------------------------------- flags
FLAGS = [
 ("F-01","Leaderboard status conflict","Ledger registry (ledger/data/strategy-registry.json, generated 2026-11-14) lists S6, S1, S7 and S2 as PAPER-ELIGIBLE with n=104; the root README and analysis state zero eligible strategies. The PAPER-ELIGIBLE labels rest on a walk-forward backtest (W3 to W9) against naive baselines, not against the market, with no prospective settlement. Under the operator's rule they are shown here as NOT ELIGIBLE pending Q-08.", "ledger/data/strategy-registry.json; origination/results/validation-w10.json; README.md", REPO+"ledger/data/strategy-registry.json", "OPEN"),
 ("F-02","Method text does not match the implemented formula","requirements/results/week10-lines.json states the away projection as (away PF/G + away PA/G)/2. The stored values reproduce only with (away PF/G + HOME PA/G)/2. Verified: all 13 stored Week 10 B0 games reproduce to within 0.0006 with the symmetric form (site/scripts/model_b0.py, check_b0).", "requirements/results/week10-lines.json", REPO+"requirements/results/week10-lines.json", "OPEN (formula verified 13/13; method text not yet edited)"),
 ("F-03","nfl.com picks article contradicts the scores page","The Week 10 picks article (read 2026-11-17) labels all five author picks 'Incorrect pick' for the Patriots at Lions game, including the four picks for Detroit. The scores page (same day) shows DET 35, NE 10. Both are nfl.com; the cause is not stated. Not used for grading: grading uses the scores page.", "nfl.com picks article; nfl.com scores", OFF["picks10"], "OPEN"),
 ("F-04","Week 10 Monday game not final on nfl.com as read","LAC at BAL (Nov 16) shows 8:15 PM with no score on the scores, standings and picks pages. Excluded from grading (12 graded, 1 pending) and from the Week 11 inputs. If it is final, W11 lines change.", "nfl.com scores 2026-11-17", OFF["scores"], "OPEN (Q-05)"),
 ("F-05","Week 10 injury row counts disagree across captures","Five Week 10 captures in the repo disagree: requirements/results/injuries-w10.json (about 358 rows by a heuristic count), integration/data/injuries-2026-week10.json and a57af0ab/data/injuries-2026-w10.json (about 345), decision/data/injuries-2026-week10.json (about 114), hub/data/injuries-w10.csv (67 data rows). The live page has 8 pages; one was re-read today. Counts above are from a rough parse of each file and are not verified.", "see paths", OFF["inj10"], "OPEN (Q-06)"),
 ("F-06","Depth page for Houston returns 404","https://www.nfl.com/teams/houston-texans/depth-chart returns 404 on 2026-11-17. The Texans image-depth problem in the brief cannot be checked against an official page.", "nfl.com", OFF["depthTEX"], "OPEN (S-03)"),
 ("F-07","Week 11 report content available; raw capture missing","The official reg11 URL served Week 11 content when re-read 2026-11-18; exact capture time/hash unavailable.", "nfl.com", OFF["inj11"], "OPEN (Q-07)"),
 ("F-08","Team codes differ across files","ARI and AZ both appear in JSON files outside archive/ (AZ in 71 files, ARI in 5); LA and LAR both appear (LA in 40 files, LAR in 34; not every occurrence is the Rams). The repo's game log and this site use AZ and LAR (nfl.com scores text). Files still using ARI: desk/analysis/repository-audit.json, desk/public-data/repository-audit.json, docs/evidence-lab/results.json, evidence-lab/results.json, strict/results.json.", "listed files", REPO+"origination/data/games-2026-w1-w9.json", "OPEN (S-10)"),
 ("F-09","Root landing page was stale and cluttered","Root index.html was a 14 Nov snapshot linking to 15 parallel namespaces. This session replaces it with a redirect to site/index.html. Legacy pages are not re-verified.", "index.html; scripts/build_site.py", REPO+"index.html", "RESOLVED (redirect written 17 Nov; see F-24 for the CI conflict)"),
 ("F-10","COORDINATION.md is 1,270 lines with stale claims","Many 'in progress' claims from 14 Nov sessions are never closed; the file is 224 KB. Recorded for the operator; not edited beyond this session's section.", "COORDINATION.md", REPO+"COORDINATION.md", "OPEN"),
 ("F-11","Week 11 market column is blank","No nfl.com picks article for Week 11 was captured this session; the Week 11 market and difference columns stay blank.", "site/data/b0-w11-lines.json", REPO+"site/data/b0-w11-lines.json", "OPEN"),
 ("F-12","Week 10 market rows: two of 14 re-verified today","Captured 14 Nov by session 949f49b0. This session compared the Patriots at Lions and Chargers at Ravens rows with the picks article: both match. The other 12 rows are not re-verified today.", "market/data/raw/official-prices-w10.json", REPO+"market/data/raw/official-prices-w10.json", "OPEN (2 of 14 verified: NE at DET, LAC at BAL)"),
 ("F-13","One published correlation is not significant after multiplicity correction","origination/results/correlations.json marks C2 (home margin residual vs total residual; n=89; p=0.026) as significant at 5%. Holm across the nine published correlations keeps C5, C6, C8 and C9 but not C2. Stated on correlations.html.", "origination/results/correlations.json", REPO+"origination/results/correlations.json", "OPEN"),
 ("F-14","Sum checks on the captured standings","League PF = PA = 6,880; wins = losses = 148; ties = 2 (one tie game, NYG 27 WAS 27, Week 5 in the repo log; the tie date was not verified this session). These are checks on the transcription, not on the NFL's data.", "site/data/standings-2026-11-17.json", OFF["standings"], "PASS"),
 ("F-15","Lions designations verified","Kerby Joseph (Knee), Cade Mays (Ankle) and D.J. Reed (Hip) all show Out with Did Not Participate in Practice on the Week 10 report as read on 2026-11-17.", "nfl.com injury report", OFF["inj10"], "VERIFIED"),
 ("F-16","Unverified operator references","The brief cites 16 VR- and VQ- identifiers. Only VR-08 and VR-12 appear in earlier repo registers (data/flagged.json, COORDINATION.md, session-08643438/verification.json), and they match the Lions item (R-05). The other 14 (VR-04 to VR-07, VR-17, VR-21, VR-23 to VR-26, VQ-05 to VQ-08) appear in no file in the repo outside this session's own register (grep, 2026-11-17). Items that depend only on those 14 are NOT verified here.", "repository search", "", "OPEN (Q-15)"),
 ("F-17","Colts trade and Ravens depth claims not verified","The brief cites two Colts starting-receiver trades (Week 10 release) and Ravens depth rows for Jackson and Huntley. This session read only the picks article's statement that Jackson is on IR; no transactions page or depth row was verified.", "nfl.com picks article", OFF["picks10"], "OPEN (Q-17)"),
 ("F-18","Shared and empty depth slots, Seattle and Washington","Not verifiable: no depth page reachable (F-06).", "", "", "OPEN (R-33)"),
 ("F-19","Game-Book starters not captured","No Game Book was captured. Any starter or designation claim that depends on a Game Book is unverified.", "", "", "OPEN (R-14)"),
 ("F-20","Week 11 fixture venues","Only IND@HOU venue verified (game centre). Other venues blank.", "", OFF["colts_game"], "OPEN (Q-16)"),
 ("F-21","Malik Willis reserve status","Brief says he is on injured reserve (VR-25/VQ-06). Not verified this session; the reserve list is not captured.", "", "", "OPEN (R-20)"),
 ("F-22","'Announced starter' changes for Lock, McCord and Brissett","Brief cites VR-24, VR-25, VQ-05. Not verified. The picks article mentions a Ravens trade for Jacoby Brissett; its terms are not read.", "nfl.com picks article", OFF["picks10"], "OPEN (Q-14)"),
 ("F-23","Week 11 fair lines were built on pre-Monday standings (provisional)","site/data/b0-w11-lines.json was written in beca9d2 on 17 Nov from the standings snapshot taken before the Monday Chargers at Ravens game, which is not verified final. The lines are provisional and must be re-originated after that game is verified final. Frozen values stay in git history.","site/data/b0-w11-lines.json; site/data/standings-2026-11-17.json","https://github.com/sassnarep3-star/Own8/blob/main/site/data/b0-w11-lines.json","OPEN (re-originate after F-04 clears)"),
 ("F-24","Root index.html now redirects; the requirements workflow will fail its clean-diff check on its next run","Root index.html was replaced with a redirect to site/index.html (17 Nov). scripts/build_site.py regenerates the legacy root index.html on every run. .github/workflows/requirements.yml runs build_site.py and then fails if git diff is not empty. Tested in a scratch copy: with the legacy index committed the regenerated file is identical; with the redirect committed the regenerated legacy dashboard differs. The workflow runs only on pushes or PRs touching requirements/**, scripts/build_site.py, scripts/check_links.py, or the workflow file, so this PR does not trigger it. The requirements session (f6e60a81) must decide the fix: stop build_site.py writing index.html, or keep the redirect and exempt it from the diff check.","README.md; index.html; scripts/build_site.py; .github/workflows/requirements.yml","https://github.com/sassnarep3-star/Own8/blob/main/.github/workflows/requirements.yml","OPEN (owner decision: requirements session)"),
]

# ---------------------------------------------------------------- repo review
REPO_REVIEW = [
 ("RR-01","Root landing page","index.html was a 14 Nov snapshot ('Snapshot · 14 NOV 2026') with links to 15 parallel namespaces.","Replaced with a redirect to site/index.html (this session).","index.html","F-09"),
 ("RR-02","Conflicting leaderboard status","ledger registry: 4 PAPER-ELIGIBLE; root README: 0 eligible.","Flagged; shown as NOT ELIGIBLE pending ruling.","ledger/data/strategy-registry.json; README.md","F-01"),
 ("RR-03","Method text vs formula","B0 written method has an asymmetric away projection; stored values use the symmetric form.","Verified and recorded (F-02); text not yet edited (it is an inherited file).","requirements/results/week10-lines.json","F-02"),
 ("RR-04","Injury row counts","Five Week 10 captures; counts disagree.","Open (F-05).","see F-05","F-05"),
 ("RR-05","Team codes","ARI/AZ and LA/LAR used inconsistently across files.","Open (F-08).","see F-08","F-08"),
 ("RR-06","Correlation significance","C2 labelled significant; not Holm-significant across nine tests.","Stated on correlations.html (F-13).","origination/results/correlations.json","F-13"),
 ("RR-07","CI runs a site build on each push and daily","audit.yml runs scripts/build_site.py on push and daily (cron 17 8 * * *). Whether it writes root index.html was not re-checked this session.","Read the workflow before relying on root index.html staying a redirect.",".github/workflows/audit.yml","—"),
 ("RR-08","Namespace count","597 files outside archive/, 204 HTML pages, 15 parallel namespaces linked from the root page.","Consolidation suggested (S-10).","repo tree","F-09"),
 ("RR-09","Duplicate evidence-lab copies","evidence-lab/ and docs/evidence-lab/ both exist.","Open; not compared line by line.","evidence-lab/; docs/evidence-lab/","—"),
 ("RR-10","Coordination board size","COORDINATION.md is 1,270 lines and holds 28 session sections, many with stale claims.","Open (F-10).","COORDINATION.md","F-10"),
 ("RR-11","Untraceable identifiers","VR-xx and VQ-xx identifiers in the brief are not in the repo.","Open (F-16).","repository search","F-16"),
 ("RR-12","Picks article labels","'Incorrect pick' labels on five Lions picks contradict the scores page.","Open (F-03).","nfl.com picks article","F-03"),
 ("RR-13","Pages build","Pages is built from main, root folder (legacy). Whether _config.yml excludes site/ was not checked this session.","Check _config.yml before relying on site/ being published.","_config.yml","—"),
 ("RR-14","Unreviewed bulk","Inherited pages and data (root pages/, docs/, desk/, hub/, market/, signals/, integration/, decision*/) not re-verified this session.","Stated limit (R-66).","see paths","—"),
]

SOURCES = [
 dict(id="SRC-01", label="NFL standings, 2026 regular season (league view)", url=OFF["standings"], read=FETCH, used_for="32-team reconciliation (R-02)", kind="official"),
 dict(id="SRC-02", label="NFL scores, Week 10 (3 pages read)", url=OFF["scores"], read=FETCH, used_for="Week 10 finals (R-01, R-03)", kind="official"),
 dict(id="SRC-03", label="NFL schedule, Week 11 (3 pages read)", url=OFF["sched11"], read=FETCH, used_for="Week 11 fixtures (R-18 to R-20)", kind="official"),
 dict(id="SRC-04", label="NFL injury report, Week 10 (page 1 of 8 read)", url=OFF["inj10"], read=FETCH, used_for="Lions designations (R-05); report shape", kind="official"),
 dict(id="SRC-05", label="NFL injury report URL, Week 11 (probe)", url=OFF["inj11"], read=FETCH, used_for="Week 11 availability (R-06)", kind="official probe"),
 dict(id="SRC-06", label="NFL game centre, Colts at Texans, Week 11", url=OFF["colts_game"], read=FETCH, used_for="Venue (R-18)", kind="official"),
 dict(id="SRC-07", label="NFL Houston Texans depth chart (probe: 404)", url=OFF["depthTEX"], read=FETCH, used_for="Depth source status (R-22, R-23)", kind="official probe"),
 dict(id="SRC-08", label="NFL.com Week 10 picks article (FanDuel lines, locked Thu 2 PM ET)", url=OFF["picks10"], read=FETCH, used_for="Spot-check of two Week 10 market rows (F-12); Monday game shape (F-04); Lions 'Incorrect' labels (F-03)", kind="official"),
 dict(id="SRC-09", label="Repo: 136-game official log W1 to W9", url=REPO+"origination/data/games-2026-w1-w9.json", read=FETCH, used_for="Reconciliation and B0 inputs", kind="repository (inherited, reconciled)"),
 dict(id="SRC-10", label="Repo: Week 10 lines (originated 2026-11-14)", url=REPO+"requirements/results/week10-lines.json", read=FETCH, used_for="B0 check and Week 10 fair lines", kind="repository (derived)"),
 dict(id="SRC-11", label="Repo: Week 10 market prices (captured 2026-11-14 from SRC-08)", url=REPO+"market/data/raw/official-prices-w10.json", read=FETCH, used_for="Market column (R-42, R-43)", kind="repository (inherited)"),
 dict(id="SRC-12", label="Repo: strategy registry and validation (2026-11-14)", url=REPO+"ledger/data/strategy-registry.json", read=FETCH, used_for="Strategy status (R-52, F-01)", kind="repository (derived)"),
 dict(id="SRC-13", label="Repo: correlations (n and CI)", url=REPO+"origination/results/correlations.json", read=FETCH, used_for="Correlations page (R-51, F-13)", kind="repository (derived)"),
 dict(id="SRC-14", label="Repo: requirement register (16 rows, 2026-11-14)", url=REPO+"requirements/data/requirements.json", read=FETCH, used_for="Cross-check of prior statuses", kind="repository (inherited)"),
]

def main():
    os.makedirs(D, exist_ok=True)
    reqs = [dict(id=a, group=b, requirement=c, status=d, exists=e, gap=f, source=g) for a, b, c, d, e, f, g in REQ]
    json.dump(dict(as_of=FETCH, rows=reqs, status_legend={
        "DONE": "Built and checked for the scope stated.",
        "PARTIAL": "Built for part of the scope; the gap is stated.",
        "BLOCKED": "Cannot proceed until a named missing input exists.",
        "NOT STARTED": "No work done.", "NOT DONE": "Checked; the requirement is not met.",
        "REJECTED": "The operator rejected it; policy recorded.",
        "NOT POSSIBLE AS STATED": "Cannot be met as written; re-scoped as stated.",
        "DECISION NEEDED": "Needs an operator choice (see suggestions).",
        "PENDING": "Happens at the end of this session."}), open(os.path.join(D, "requirements.json"), "w"), indent=1)
    json.dump(dict(as_of=FETCH, rows=[dict(id=a, question=b, have=c, lack=d, how_to_answer=e, blocks=f) for a, b, c, d, e, f in QUESTIONS]),
              open(os.path.join(D, "questions.json"), "w"), indent=1)
    json.dump(dict(as_of=FETCH, status="ALL AWAITING OPERATOR CHOICE. Nothing below has been implemented.", rows=SUGGESTIONS),
              open(os.path.join(D, "suggestions.json"), "w"), indent=1)
    json.dump(dict(as_of=FETCH, rows=[dict(id=a, title=b, detail=c, evidence=d, link=e, status=f) for a, b, c, d, e, f in FLAGS]),
              open(os.path.join(D, "flags.json"), "w"), indent=1)
    json.dump(dict(as_of=FETCH, rows=[dict(id=a, item=b, finding=c, action=d, file=e, flag=f) for a, b, c, d, e, f in REPO_REVIEW]),
              open(os.path.join(D, "repo-review.json"), "w"), indent=1)
    json.dump(dict(as_of=FETCH, rows=SOURCES), open(os.path.join(D, "sources.json"), "w"), indent=1)
    from collections import Counter
    print("requirements", len(reqs), dict(Counter(r["status"] for r in reqs)))
    print("questions", len(QUESTIONS), "suggestions", len(SUGGESTIONS), "flags", len(FLAGS), "repo-review", len(REPO_REVIEW), "sources", len(SOURCES))

if __name__ == "__main__":
    main()
