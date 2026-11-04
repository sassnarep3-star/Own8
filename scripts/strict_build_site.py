#!/usr/bin/env python3
"""Static dashboard, no CDN, no third-party browser requests. All table rows cite context.
Official evidence ≠ calculated analysis ≠ project policy. Unknown metrics render blank.
"""
import json
import html
from pathlib import Path
from strict_analyze import run, BDB, NGS, NIST, STANDINGS
R=Path(__file__).resolve().parents[1]
PAGES=[('index','Overview','01'),('executive-summary','Executive summary','02'),('standings','Official standings','03'),('schedule','Upcoming schedule','04'),('model-lines','Line origination','05'),('benchmark','Historical benchmark','06'),('strategies','Signal library','07'),('parlays','Parlays & combos','08'),('correlations','Correlations','09'),('validation-gates','Validation gates','10'),('leaderboard','Leaderboard','11'),('injuries','Availability','12'),('player-stats','Player props','13'),('methodology','Methodology','14'),('repo-review','Repository audit','15'),('sources','Sources & evidence','16'),('flagged','Flagged for Review','17'),('responsible-gambling','Research safeguards','18')]

def esc(v):return html.escape(str(v))
def fmt(v):return '' if v is None else f'{v:.3f}' if isinstance(v,float) else esc(v)
def source(url):return f'<a class="source" href="{esc(url)}" rel="noopener noreferrer">Official source ↗</a>'
def table(headers,rows,caption):
    head=''.join(f'<th scope="col"><button type="button" class="sort" aria-label="Sort by {esc(h)}">{esc(h)} <span aria-hidden="true">↕</span></button></th>' for h in headers)
    body=''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)
    return f'<div class="table-wrap"><table><caption>{esc(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div><p class="no-results" hidden>No matching entries. Clear the search to see all rows.</p>'
def badge(s):return f'<span class="tag {"warn" if any(k in s for k in ["BLOCK","UNVERIFIED","REVIEW","PARTIAL"]) else "good" if "OFFICIAL" in s else "neutral"}">{esc(s)}</span>'
def note(t):return '<div class="notice">'+t+'</div>'
def build():
 d=run(); flags=json.loads((R/'strict/flags.json').read_text()); inv=json.loads((R/'strict/repository-inventory.json').read_text())
 out=R/'pages'; out.mkdir(exist_ok=True)
 contents={}
 contents['index']=('The evidence comes first.','An NFL research workspace for originating lines, testing signals and rewarding demonstrated skill—not a lucky run.',
 '<div class="metric-grid"><article class="metric"><span>Official snapshot</span><strong>32 <small>teams</small></strong><p>Selected standings fields rechecked</p></article><article class="metric"><span>Historical evidence</span><strong>91 <small>games</small></strong><p>NFL-published • 2017 weeks 1–6</p></article><article class="metric"><span>Strategy proposals</span><strong>11 <small>ideas</small></strong><p>Singles, parlays and player combos</p></article><article class="metric caution"><span>Skill-qualified</span><strong>0 <small>strategies</small></strong><p>No ranks or rewards awarded</p></article></div>'
 +'<section class="split"><article class="panel dark"><span class="eyebrow">THE RESEARCH STANDARD</span><h2>Make the line.<br>Then try to disprove it.</h2><p>Separate observed inputs from model estimates. Freeze decisions before kickoff. Test out of sample. Decline a trade when evidence is missing.</p><a class="button" href="pages/executive-summary.html">Read executive summary →</a></article><article class="panel"><span class="eyebrow">CURRENT DECISION</span><h2>Research only. No active picks.</h2><p>There is no calibrated current-season model or primary price archive. Current lines, expected returns and bet-leg correlations remain blank.</p><a href="pages/validation-gates.html">Inspect every validation gate →</a><hr><p>Randomness cannot be eliminated. Good evaluation can reduce false discoveries and quantify uncertainty.</p></article></section>'
 +table(['Workstream','Finding','Classification','Evidence'],[
 ['Official facts','32 team rows / 15 upcoming matchups','Observed, dated snapshot',source(STANDINGS)],
 ['Predictive benchmark','60 rolling-week predictions, not a profitable betting claim','Derived / developmental',source(BDB)],
 ['Leaderboard','All strategies blocked pending independent validation','Own8 competition policy',source(NIST)],
 ['Review queue',f'{len(flags)} new audit findings + 13 legacy flags retained','Published, non-blocking for site release',source(NGS)]], 'Research status • 2026-11-04'))
 contents['executive-summary']=('Executive summary','What is established, what is proposed, and what still cannot be claimed.',
 note('<strong>Bottom line:</strong> the project has a verified, limited evidence foundation and a reproducible research pipeline. It does not yet establish a profitable or selectively skill-based betting strategy.')
 +table(['Area','Executive finding','Evidence / context'],[
 ['Objective','Originate spread, total, moneyline and player-prop distributions; compare to primary prices only after independent validation.',source(BDB)],
 ['Verified evidence','32 current team rows, seven numerical fields each; 15 Week 9 matchups/dates. Immutable NFL repository provides 91 historical game rows.',source(STANDINGS)+' '+source(BDB)],
 ['Analysis','Three descriptive correlations and a 60-game rolling-week score benchmark. Neither establishes betting-leg dependence or future skill.',source(BDB)],
 ['Integrity fixes','Withdrawn legacy candidate flags; corrected margin/handicap signs; removed conditional-gate pass-through and team-to-bet correlation proxy.',source(NGS)],
 ['Signal research','11 proposed strategies cover singles, parlays, same-game combinations and player props. None passes every gate.',source(NGS)],
 ['Rewards','Non-monetary badges/points only after pre-registered out-of-sample and prospective validation. Ranks, ROI, CLV and awards blank now.',source(NIST)],
 ['Risk','Randomness remains. Multiple testing, leakage, role changes, quote availability and clustered outcomes can create false skill.',source(NIST)],
 ['Missing prerequisites','Full multi-season official player-game panel, primary timestamped odds/payout/rules, calibrated predictive models, robust forward outcomes.',source(BDB)],
 ['Release','Publish findings and flags, not unsupported picks. No manual input, no automated wagers, no paid credentials requested.',source('https://wsgc.wa.gov/tribal-partnerships/sports-wagering')]
 ],'Executive decisions • derived findings and Own8 policy, not official recommendations'))
 contents['standings']=('Official standings','Selected fields observed directly on NFL.com on November 4, 2026. No tail-column labels inferred.',
 note('32 teams • <strong>224 numeric cells</strong> compared with the earlier capture, all matching. Verification is limited to W, L, T, PCT, PF, PA and NET; agreement between two repository files alone is not verification.')
 +table(['Team','W','L','T','PCT','PF','PA','NET','Status','Source'],[[esc(t['name']),*[fmt(t[k]) for k in ['W','L','T','PCT','PF','PA','NET']],badge(t['status']),source(t['source_url'])] for t in d['standings']],'2026 regular-season standings • observed snapshot, not a live feed'))
 contents['schedule']=('Upcoming schedule','Week 9 matchups and calendar dates observed on the official NFL schedule. Times and venues omitted where not re-certified.',
 table(['Away','Home / designated host','Date','Context','Status','Source'],[[esc(g['away']),esc(g['home']),esc(g['date']),'Madrid / neutral site label' if g['neutral_site'] else '',badge('OFFICIAL OBSERVED'),source(g['source_url'])] for g in d['current_lines']],'15 upcoming games • official snapshot checked 2026-11-04'))
 contents['model-lines']=('Line origination','An honest blank is more useful than an unsupported edge.',
 note('Current fair lines and market quotes are <strong>unverified / not established</strong>, so numeric cells are blank. The historical engine estimates mean scores; these are not current fair handicaps, calibrated quantiles or executable betting prices.')
 +table(['Game','Fair home spread','Fair total','Fair moneyline','Market home spread','Edge','Decision','Source'],[[esc(g['away']+' at '+g['home']),'','','','','',badge('BLOCKED'),source(g['source_url'])] for g in d['current_lines']],'Current lines • blank means unavailable, not zero')
 +table(['Output','Definition / research requirement','Official context'],[
 ['Spread','Fit discrete margin distribution M = home − away. Home handicap h is opposite the margin. Price using P(M+h > 0), P(M+h = 0) and actual settlement rules; the mean need not be the fair median.',source(BDB)],
 ['Total','Fit discrete total T = home + away, including overtime/settlement rules; price over/under/push jointly.',source(BDB)],
 ['Moneyline','Fit home/away/tie outcome probabilities. With no push, fair decimal odds = 1/p; actual rules may void ties or treat them differently.',source(BDB)],
 ['Expected net return','p(win) × (decimal odds − 1) − p(loss). Push returns stake. Leave blank without observed prices and calibrated probabilities.',source(BDB)],
 ['No-vig baseline','For a complete market normalize inverse decimal odds as a baseline, not a uniquely correct fair probability. No assumed −110.',source(NIST)]
 ],'Own8 analytical definitions • not values published by the NFL'))
 contents['benchmark']=('Historical benchmark','A small, reproducible score-prediction experiment. Not a betting backtest.',
 note('Official 2017 weeks 1–6 only. Weeks 1–2 initialize training; weeks 3–6 give 60 test predictions. Fit only earlier weeks, shrink team PF/PA to prior league means with four pseudo-games (project assumption). Compare to prior league-average margin/total. Retrospective development: not a preregistered untouched test.')
 +table(['Target','Test games','Model MAE (pts)','Baseline MAE (pts)','MAE improvement','Illustrative 95% interval','Decision','Source'],[[esc(b['target']),fmt(b['n']),fmt(b['model_mae']),fmt(b['baseline_mae']),fmt(b['mae_improvement']),f"[{b['illustrative_95_interval'][0]:.3f}, {b['illustrative_95_interval'][1]:.3f}]",badge('NOT SKILL VALIDATED'),source(b['source_url'])] for b in d['benchmarks']],'Derived metrics • improvement = baseline MAE − model MAE; higher is better')
 +'<p>Intervals: seeded percentile bootstrap, 4,000 resamples of test-week blocks. Only four clusters, repeated teams and a single partial season make these intervals illustrative, not reliable skill certification. Historical neutral venues are not fully classified. No prices, ROI, CLV or player-prop outcomes are inferred.</p>'
 +table(['Game ID / test week','Matchup','Train through week','Mean home margin','Mean total','Actual margin','Actual total','Source'],[[esc(p['game_id'])+' / '+str(p['week']),esc(p['away']+' at '+p['home']),str(p['train_max_week']),fmt(p['expected_home_margin']),fmt(p['expected_total']),fmt(p['actual_margin']),fmt(p['actual_total']),source(p['source_url']+f"#L{p['source_row']}")] for p in d['historical_predictions']],'All 60 predictions • derived estimates, not official model outputs'))
 contents['strategies']=('Signal library','Eleven testable hypotheses. No claimed edges, fabricated returns or premature winners.',
 note('Every strategy below is <strong>proposed and unvalidated</strong>. Official links document data or definitions—not evidence that the proposed strategy works. Features must be timestamped before kickoff and tested for incremental out-of-sample value.')
 +table(['ID','Category','Strategy','Research hypothesis','Missing prerequisites','Status','Official context'],[[s['id'],esc(s['category']),esc(s['name']),esc(s['hypothesis']),esc(s['required_inputs']),badge(s['status']),source(s['source_url'])] for s in d['strategies']],'Strategy register • Own8 research proposals'))
 contents['parlays']=('Parlays & player combos','Price the joint event. Do not multiply marginal probabilities without evidence.',
 note('No matched official bet-indicator sample or primary combo payouts were acquired. Joint probabilities, correlations and returns remain blank. Positive raw-yard correlation is not the correlation of two threshold bets.')
 +table(['Strategy','Joint probability','Bet-leg correlation','Payout','Decision','Official context'],[[esc(s['name']),'','','',badge('BLOCKED'),source(s['source_url'])] for s in d['strategies'] if s['id'] in ['S08','S09','S10','S11']],'Combination eligibility • blank is unknown')
 +table(['Requirement','Own8 research rule','Official context'],[
 ['Joint model','Share pace, game script, player availability and volume across legs; validate joint exceedances at quoted thresholds.',source(NGS)],
 ['Two binary legs','P(A∩B) = pA·pB + ρ√[pA(1−pA)pB(1−pB)]. This requires binary-event ρ and feasible bounds; never substitute yardage correlation.',source(NIST)],
 ['Bounds','max(0,pA+pB−1) ≤ P(A∩B) ≤ min(pA,pB). Enforce for every pair; pairwise consistency alone does not define a multileg joint distribution.',source(NIST)],
 ['Three or more legs','Pairwise correlations alone are insufficient. Use a coherent multivariate generative model, held-out tail calibration and actual operator rules.',source(NIST)],
 ['Exposure','Report joint downside and aggregate game/player exposure. A parlay is not inherently a better edge; no risk limit itself proves skill.',source(NIST)]
 ],'Mathematical identities / Own8 requirements; official links provide statistical or football context, not parlay endorsement'))
 contents['correlations']=('Correlation library','Know what the unit of observation is before using the coefficient.',
 table(['Pair','r','n','Observation unit','Classification','Limitation','Source / context'],[[esc(c['pair']),fmt(c['r']),fmt(c['n']),esc(c['unit']),badge(c['status']),esc(c['limitation']),source(c['source_url'])] for c in d['correlations']],'Three descriptive estimates; four bet-level estimates intentionally blank')
 +'<p>Pearson r is computed from centered paired observations in the checked evidence. No confidence interval is asserted for the team snapshot: teams share opponents and results. These estimates neither establish causality nor parameterize current parlays.</p>')
 contents['validation-gates']=('Validation gates','Only an exact PASS counts. Unknown, partial, conditional and failed checks block promotion.',
 table(['Gate','Name','Requirement','Current state','Official context'],[[g['id'],esc(g['gate']),esc(g['rule']),badge(g['status']),source(g['source_url'])] for g in d['gates']],'Own8 proposed governance • thresholds are policy, not official NFL or NIST requirements')
 +table(['Strategy']+[g['id'] for g in d['gates']]+['Eligible','Context'],[[s['id']]+[badge(s['gates'][g['id']]) for g in d['gates']]+['No',source(s['source_url'])] for s in d['strategies']],'Per-strategy gate matrix • all blocked'))
 contents['leaderboard']=('The skill leaderboard','No winners manufactured from noise.',
 note('<strong>0 qualified strategies. 0 rewards awarded.</strong> Ranks, scores, ROI and CLV are blank because qualifying evaluation does not exist—not because measured performance is zero. No historical contest prizes or external funding are implied.')
 +table(['Rank','Strategy','Category','ROI','CLV','Skill score','Reward points','Status','Context'],[['',s['id']+' · '+esc(s['name']),esc(s['category']),'','','','',badge('NOT ELIGIBLE'),source(s['source_url'])] for s in d['strategies']],'Competition ledger • project policy; no gambling or cash rewards')
 +table(['Stage','Proposed eligibility & reward rule','Official context'],[
 ['Registered','Version and freeze the strategy, features, thresholds, sample, trials and scoring before the evaluation window. No reward.',source(NIST)],
 ['Validated badge','All nine gates PASS, including powered out-of-sample/prospective evidence, calibrated predictions and multiplicity-adjusted lower net-return bound above zero.',source(NIST)],
 ['Ranking','Among eligible entries only: lower confidence bound of after-cost return on the identical frozen test window; proper-score improvement and stable season results required. Positive CLV is supporting evidence only.',source(NIST)],
 ['Recognition','Proposed non-cash points: first = 3, second = 2, third = 1 per completed eligible contest. Ties share place; no eligible entries means no awards. Not yet activated.',source(NIST)],
 ['Drawdown / overlap','Publish realized and expected drawdowns, game/player exposure and duplicate-signal families; failed gates suspend rather than silently reset history.',source(NIST)]
 ],'Reward design • Own8 policy, not a claim from cited institutions'))
 inj=json.loads((R/'strict/evidence/injuries-observed.json').read_text())
 contents['injuries']=('Availability & injury evidence','Week 9 official page is now accessible. Practice participation is not final game status.',
 note(esc(inj['scope'])+' Earlier November 3 report-availability notes are superseded. Do not interpret “No Injuries Reported” or an empty status as cleared to play.')
 +table(['Team','Player','Practice participation','Injury','Game status','Classification','Source'],[[esc(p['team']),esc(p['player']),esc(p['practice']),'','',badge('PARTIAL OBSERVATION'),source(p['source_url'])] for p in inj['players']],'Selected DNP observations only • checked 2026-11-04')
 +table(['News','Verified wording / limit','Source'],[['Jalen Hurts article','Official article says likely out / expected to miss remainder of 2026 season. No numerical adjustment or replacement-player projection is established.',source('https://www.nfl.com/news/eagles-qb-jalen-hurts-out-2026-season-blood-clots')]],'News observation • not medical advice; source uncertainty preserved'))
 contents['player-stats']=('Player props','Workload first. Role uncertainty always. No invented player projections.',
 note('Legacy season leader tables were partial and are not a matched player-game validation panel. No numeric player projections or prop thresholds are certified here. Official metric definitions were retrieved; the strategies remain proposals.')
 +table(['Strategy','Projection','Quoted prop','Bet-leg correlation','Prerequisite','Status','Official definitions'],[[esc(s['name']),'','','',esc(s['required_inputs']),badge('UNVERIFIED — BLOCKED'),source(s['source_url'])] for s in d['strategies'] if s['category'] in ['Player prop','Player combo']],'Player-prop research register')
 +table(['Metric','Definition observed in official glossary','Source'],[
 ['Completion above expectation','Actual completion percentage compared to expected completion percentage.',source(NGS)],
 ['Time to throw','Average time from snap to throw on pass attempts; sacks excluded.',source(NGS)],
 ['Targeted air-yards share','Receiver intended air yards divided by the team intended air yards, represented as a percentage.',source(NGS)],
 ['YAC above expectation','Yards after catch compared to expected YAC.',source(NGS)]
 ],'Official definitions • no predictive value claimed'))
 contents['methodology']=('Methodology & skill controls','Transparent assumptions, reproducible code, explicit refusal states.',
 table(['Layer','Method / limit','Official context'],[
 ['Evidence','GitHub official NFL files pinned to commit and SHA-256 checked before every run. Web observations transcribed as selected fields, dated and scoped—not presented as full HTML archives.',source(BDB)],
 ['Historical prediction','For each week 3–6, use only earlier weeks. Team PF/PA are shrunk with 4 league-mean pseudo-games; expected team score averages own PF and opponent PA, plus/minus half training home-margin effect.',source(BDB)],
 ['Benchmark baseline','Prior-week league mean margin and mean total. MAE is average absolute prediction error. Improvement = baseline error − model error.',source(BDB)],
 ['Bootstrap','Seed 20261104; 4,000 week-block resamples of paired errors. Four test-week clusters are inadequate for reliable inference; intervals are illustrative. No skill p-value is asserted.',source(NIST)],
 ['Not fully unbiased','This benchmark was developed after evidence retrieval. Rolling-origin separation prevents same-week leakage, not retrospective model selection. A genuinely untouched forward test is still required.',source(NIST)],
 ['Signal evaluation plan','Pre-register all trials; nested rolling-season training/tuning, outer holdout seasons and a final prospective season. Fit transforms only on training data; audit availability timestamps.',source(NIST)],
 ['Multiple tests','Group duplicate strategy families; preregister family-wise or false-discovery correction. Do not choose a lucky variant after viewing holdout returns.',source(NIST)],
 ['Calibration plan','Assess Brier/log loss for outcomes, discrete score calibration, quantile coverage, ROI after costs, CLV on matched prices, regime stability and cluster-aware uncertainty. Not implemented without the required data.',source(NIST)],
 ['Current refusal rule','No calibrated current model or timestamped primary price evidence → null fair lines, market lines, returns and candidates. No assumption fills an official-data gap.',source(STANDINGS)],
 ['Automation','One command rebuilds deterministic analysis, site, tests and link report. CI repeats on pushes/PRs. Snapshot dates do not auto-refresh; no live trading daemon or self-learning skill claim.',source(BDB)]
 ],'Own8 methods • cited institutions do not endorse project policies'))
 contents['repo-review']=('Repository audit','Inventory is not certification. Every inherited file has an explicit review scope.',
 note(f'{len(inv)} tracked text files inventoried at the base review, with line counts and SHA-256 digests. Original executable analysis was inspected for gate, sign, missing-value and dependence errors; findings A01–A17 are published. This is not a claim that every inherited factual assertion was independently verified.')
 +table(['Finding','Severity','Audit result','Official context'],[[f['id']+' · '+esc(f['title']),badge(f['severity']),esc(f['finding']),source(f['source_url'])] for f in flags],'Code/provenance audit • local findings, official context references')
 +table(['Legacy file','Lines','Review classification','Context (not file verification)'],[[esc(i['file']),str(i['lines']),esc(i['review_status']),source(i['source_url'])] for i in inv],'Complete base tracked-text inventory • full digests in downloadable JSON'))
 manifest=d['manifest']
 contents['sources']=('Sources & evidence','Official origin, exact scope, and a trail you can inspect.',
 note('Source links are classified by role. An official-context link on a proposed strategy or audit finding is <strong>not</strong> proof of that proposal or a verified numerical edge. Primary NFL files are immutable; web pages can change. External links were retrieved as noted, not continuously monitored.')
 +table(['Evidence','Scope','Verification','Official source'],[
 ['NFL standings','32 team names; W,L,T,PCT,PF,PA,NET','Selected values observed 2026-11-04, 224 numeric cells match legacy JSON.',source(STANDINGS)],
 ['NFL schedule','15 Week 9 matchups/dates; Madrid label','All schedule chunks retrieved 2026-11-04. Times/venues excluded.',source('https://www.nfl.com/schedules/2026/by-week/week-9')],
 ['NFL injury report','8 selected JAX/BAL DNP rows','Partial observation on 2026-11-04. Injury/game statuses blank.',source('https://www.nfl.com/injuries/league/2026/reg9')],
 ['NFL news','Hurts article wording','Likely / expected preserved; no model injury adjustment inferred.',source('https://www.nfl.com/news/eagles-qb-jalen-hurts-out-2026-season-blood-clots')],
 ['NFL Next Gen Stats','Metric definitions only','Glossary retrieved 2026-11-04; not a complete stat feed.',source(NGS)],
 ['NFL Football Operations','Big Data Bowl overview','Official analytics contest context, not evidence of betting profitability.',source('https://operations.nfl.com/programs-initiatives/innovation/big-data-bowl')],
 ['NIST','Autocorrelation and randomness assumptions','Handbook page retrieved; supports dependence caution, not project thresholds.',source(NIST)],
 ['Washington regulator','Local official sports-wagering information','Retrieved 2026-11-04; legal eligibility not assessed.',source('https://wsgc.wa.gov/tribal-partnerships/sports-wagering')]
 ],'Web evidence ledger • snapshot date 2026-11-04')
 +table(['Immutable file','Bytes','SHA-256','Official source'],[[esc(m['file']),str(m['bytes']),'<code>'+esc(m['sha256'])+'</code>',source(m['source_url'])] for m in manifest],'NFL repository files • pinned commit 9ad0b4b2ea36697e29e44e2399512cc1ce70358c')
 +'<div class="downloads"><a href="../strict/results.json">Analysis JSON ↓</a><a href="../strict/flags.json">Review register ↓</a><a href="../strict/repository-inventory.json">File audit & digests ↓</a><a href="../strict/evidence/manifest.json">Evidence manifest ↓</a><a href="../strict/evidence/standings-observed.json">Standings observation ↓</a><a href="../strict/evidence/web-checks.json">Web-check log ↓</a><a href="../strict/evidence/games-2017.csv">Official historical CSV ↓</a></div>')
 legacy=json.loads((R/'data/flagged.json').read_text())['items']
 legacy_rows=[]
 for f in legacy:
    url=f.get('source_url')
    if not url or not any(h in url for h in ['nfl.com','kansspelautoriteit.nl']):url=STANDINGS
    legacy_rows.append([esc(f['id']),esc(f['severity']),esc(f['item']),'',badge('LEGACY — NOT RE-CERTIFIED'),source(url)])
 contents['flagged']=('Flagged for Review','Published limitations do not block the site. They do block unsupported claims.',
 note('Any unconfirmed numerical value remains blank. Flags are not silently resolved by linking an official homepage. The legacy register below is historical testimony, <strong>not fresh verification</strong>; old candidate, jurisdiction and injury-availability statements are superseded by A01–A17.')
 +table(['ID','Severity','Finding','Resolution / current limit','Value','Official context'],[[f['id'],badge(f['severity']),esc(f['title']),esc(f['finding']),'',source(f['source_url'])] for f in flags],'Current audit register • 17 needs-review items')
 +table(['ID','Severity','Inherited claim (historical, not re-certified)','Confirmed value','Status','Official context'],legacy_rows,'All 13 inherited flags retained for manual review'))
 contents['responsible-gambling']=('Research safeguards','A paper competition—not a sportsbook, prediction guarantee, or financial advice.',
 table(['Safeguard','Policy / resource','Official context'],[
 ['No wagering','This code places no bets and accepts no deposits. Rewards are proposed points/badges; no cash rewards funded or promised.',source('https://wsgc.wa.gov/tribal-partnerships/sports-wagering')],
 ['No guaranteed skill','Chance cannot be removed. Historical results, illustrative intervals, good calibration and positive CLV do not guarantee future profitability.',source(NIST)],
 ['Washington information','Consult Washington State Gambling Commission for current sports-wagering rules. This project does not establish any person’s eligibility or permission to wager.',source('https://wsgc.wa.gov/tribal-partnerships/sports-wagering')],
 ['Support','Official Washington regulator navigation includes Responsible Gaming & Self-Exclusion. Use that resource if gambling is causing concern; no helpline number is asserted without a fresh check.',source('https://wsgc.wa.gov/tribal-partnerships/sports-wagering')],
 ['Data privacy','No user account, bankroll entry, tracking cookies or external analytics. All browser assets are local.',source('https://wsgc.wa.gov/tribal-partnerships/sports-wagering')]
 ],'Own8 safeguards • official regulator resource, not legal advice'))
 for slug,label,num in PAGES:
    title,description,body=contents[slug]
    prefix='' if slug=='index' else '../'
    nav=""
    for k,l,n in PAGES:
        active="active" if k==slug else ""
        current='aria-current="page"' if k==slug else ""
        href=prefix+("index.html" if k=="index" else "pages/"+k+".html")
        nav+=f'<a class="{active}" {current} href="{href}"><span>{n}</span>{esc(l)}</a>'
    page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc(description)}"><title>{esc(label)} · Own8 NFL Research</title><link rel="stylesheet" href="{prefix}assets/style.css"><script src="{prefix}assets/app.js" defer></script></head><body><a class="skip" href="#main">Skip to content</a><aside class="sidebar"><a class="brand" href="{prefix}index.html"><b>O<span>8</span></b><div>OWN8<small>NFL RESEARCH LAB</small></div></a><div class="nav-label">WORKSPACE</div><nav aria-label="Primary">{nav}</nav><div class="sidebar-footer"><span class="dot"></span> Paper research only<br><small>No live picks. No wagers.</small></div></aside><div class="workspace"><header class="topbar"><span>NFL / <strong>{esc(label)}</strong></span><span class="snapshot">SNAPSHOT <b>04 NOV 2026</b></span></header><main id="main"><div class="page-heading"><div><span class="eyebrow">EVIDENCE-LED FOOTBALL ANALYTICS</span><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p></div><span class="research-badge">RESEARCH MODE</span></div><div class="toolbar"><label for="row-search">Find an entry</label><input id="row-search" type="search" placeholder="Search tables on this page…" autocomplete="off"><span class="helper">Blank = unknown · sources on every row</span></div>{body}<footer><strong>Own8</strong> · Verified scope, not verified profits. <a href="{prefix}pages/sources.html">Evidence trail</a> · <a href="{prefix}pages/flagged.html">Flagged for Review</a><p>Observed facts · Derived analysis · Proposed methods · Unverified values. Updated 2026-11-04. Not a live data feed.</p></footer></main></div></body></html>'''
    (R/'index.html' if slug=='index' else out/(slug+'.html')).write_text(page)
 # Canonical old category URLs remain navigable, without unsupported numbers.
 for old,new in {'scores':'benchmark','team-stats':'standings','prop-signals':'player-stats'}.items():
    (out/(old+'.html')).write_text(redirect(new+'.html'))
 # Duplicate public legacy trees are superseded. Raw data/docs stay in repo for provenance.
 for directory in [R/'docs',R/'archive']:
    for p in directory.rglob('*.html'):
        target=Path(__import__('os').path.relpath(out/'flagged.html',p.parent)).as_posix()
        p.write_text(redirect(target))
 for filename,rows in [('model-lines-week9.json',{'games':d['current_lines']}),('correlations.json',{'correlations':d['correlations']}),('leaderboard.json',{'strategies':d['strategies'],'qualified_strategies':0}),('strategies.json',{'strategies':d['strategies']}),('prop-signals-week9.json',{'prop_signals':[]})]:
    (R/'analysis'/filename).write_text(json.dumps({'as_of':d['as_of'],'status':'SUPERSEDES LEGACY — STRICT AUDIT','notice':'No current actionable values or skill-qualified entries; see strict/results.json.',**rows},indent=2)+'\n')
 print('Built',len(PAGES),'dashboard pages, compatibility redirects, quarantined duplicate HTML routes.')

def redirect(target):
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url='+esc(target)+'"><title>Own8 · Superseded evidence</title></head><body><h1>This snapshot has been superseded</h1><p>Old claims are not current verified recommendations.</p><a href="'+esc(target)+'">Continue to current audit and findings</a></body></html>'

if __name__=='__main__':build()
