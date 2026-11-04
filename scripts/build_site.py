"""Build isolated GitHub Pages artifact. No legacy data or historical HTML is deployed."""
import html,json,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]; OUT=R/'_site'
def load(p): return json.loads((R/p).read_text())
def esc(v): return html.escape(str(v),quote=True)
def link(u,label='Official reference ↗'): return f'<a href="{esc(u)}" rel="noopener">{esc(label)}</a>'
def cell(v): return '<span class="blank" aria-label="unverified value left blank"></span>' if v is None else esc(v)
def table(headers,rows,caption):
    return '<div class="table-wrap"><table><caption>'+esc(caption)+'</caption><thead><tr>'+''.join('<th scope="col">'+esc(h)+'</th>' for h in headers+['Official reference'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+cell(v)+'</td>' for v in vals)+'<td>'+link(src)+'</td></tr>' for vals,src in rows)+'</tbody></table></div>'
def text(t): return '<p>'+t+'</p>'
def section(t): return '<h2>'+esc(t)+'</h2>'
def note(t): return '<div class="notice">'+t+'</div>'
def md_render(t):
    result=[]; paragraph=[]
    def flush():
        if paragraph:
            s=esc(' '.join(paragraph)); s=re.sub(r'(https://[^\s]+)',lambda m:link(m[1].rstrip('.'),m[1].rstrip('.')),s)
            result.append('<p>'+s+'</p>'); paragraph.clear()
    for line in t.splitlines():
        if line.startswith('#'):
            flush(); level=min(4,len(line)-len(line.lstrip('#'))); result.append(f'<h{level}>'+esc(line.lstrip('# '))+f'</h{level}>')
        elif not line.strip(): flush()
        elif line.startswith('- '): flush(); result.append('<p class="bullet">'+esc(line[2:])+'</p>')
        else: paragraph.append(line)
    flush(); return ''.join(result)
D=load('analysis/dashboard.json'); audit=load('analysis/repository-audit.json'); findings=load('data/review-findings.json'); sources=load('data/verified/sources.json')
NFL='https://www.nfl.com/standings/'; NGS='https://nextgenstats.nfl.com/glossary'; NIST='https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm'
pages={}
pages['index']=('Overview','An evidence-first NFL research desk.',
    '<div class="hero"><div><div class="eyebrow">OWN8 / NFL LINE LAB</div><h2>Build the line.<br>Test the edge.</h2><p>A transparent research workspace for singles, parlays and player props. Separate what is observed from what is merely promising.</p><a class="button" href="pages/executive-summary.html">Read executive summary →</a></div><div class="hero-note"><span class="status">RESEARCH MODE</span><h3>No qualified strategies.</h3><p>No verified operator quotes, untouched holdout or settled prediction ledger. There is no supported betting edge to report.</p></div></div>'
    +'<div class="metrics">'+''.join(f'<div><span>{n}</span><p>{label}</p></div>' for n,label in [('32','checked team rows'),('27','checked Week 8 QB rows'),('15','research-only lines'),('0','eligible strategies')])+'</div>'
    +note('Snapshot independently checked 04 Nov 2026. This is not a live feed. Blank cells mean unavailable or unverified, not zero. No real-money wagering or cash rewards.')
    +text('<a href="strict/site/index.html">Open the complementary historical benchmark workspace →</a> — official NFL Big Data Bowl file bytes rechecked at an immutable commit. Developmental, not skill-qualified.')+section('Start here')+'<div class="cards">'+''.join(f'<a class="card" href="pages/{slug}.html"><small>{tag}</small><h3>{title} →</h3><p>{desc}</p></a>' for slug,tag,title,desc in [('verified-data','01 / OBSERVATIONS','Verified data','Selected official fields, checked dates and scope.'),('model-lines','02 / CALCULATIONS','Research lines','Transparent untrained baselines. No selections.'),('strategies','03 / HYPOTHESES','Strategy registry','Eight ideas, eleven strict validation gates.'),('flagged','04 / ACCOUNTABILITY','Flagged for Review','Material issues, corrections and open evidence gaps.')])+'</div>'
    +section('What changed in this audit')+table(['Finding','Disposition'],[(['Unverified market-based candidates','Withdrawn; prices and EV blank'],NFL),(['Team correlation used for parlay legs','Removed; real bet-leg correlations blank'],NIST),(['Ranked leaderboard without settled bets','Unranked; rewards withheld'],NFL)],'Publication corrections — official links are review context, not endorsement of project policies.'))
exec_rows=[(['Decision','Research only; no eligible betting strategy or recommended selection'],NFL),(['Verified observations','32 standings rows (selected columns), 15 matchup/date pairs and 27 Week 8 QB rows (selected columns), checked 2026-11-04'],NFL),(['Lines','15 transparent, untrained baselines. No official fair price, calibrated probability, quote or EV is claimed'],NFL),(['Signals','Scoring margin, pace, volume/efficiency, target share and coherent joint distributions are hypotheses, not proven edges'],NGS),(['Correlation','Three cross-team descriptive Pearson values computed. Bet-leg correlations and joint win probabilities unavailable'],NIST),(['Skill test','Chronological holdout, clustered uncertainty, calibration, all-experiment multiplicity control and prospective trial required; not completed'],NIST),(['Competition','Proposed points-only badges; no actual ranks, settled ROI or rewards without evidence'],NFL),(['Automation','Fixed-input build, checks and static deployment run unattended; live collection, quote refresh and grading are not implemented'],NGS),(['Remaining risk','Source timestamps, raw-page archives, event-level history, availability and direct operator quotes are incomplete'],NFL)]
pages['executive-summary']=('Executive summary','The decision, the evidence and the limits.',
    note('Randomness cannot be removed from football. The objective is to measure repeatable skill while limiting overfitting—not to promise risk-free or exclusively skill-based outcomes.')
    +table(['Category','Summary'],exec_rows,'Executive assessment. Proposed methods and project decisions are not official NFL findings.')
    +text('The earlier dashboard overstated validation. Its candidate selections are withdrawn. Matching two captures, descriptive correlations and arbitrary edge caps did not establish a betting advantage. Current official-field checks support a snapshot, not a performance claim.')
    +text('A strategy can become eligible only after every gate passes on timestamped, event-level evidence. The site can publish open review items without blocking deployment; a model cannot bypass a failed evidence gate.'))
stand=load('data/verified/standings.json')['rows']; passing=load('data/verified/passing.json')['rows']; sched=load('data/verified/schedule.json')['rows']
pages['verified-data']=('Verified data','Selected official observations. No inferred cells.',
    note('Checked via official-page retrieval on 2026-11-04. These are dated snapshots, not live statistics. Only the columns shown below are independently checked. Excerpts are transcriptions, not original HTML archives.')
    +section('2026 standings snapshot')+table(['Team code','W','L','T','Displayed PCT','PF','PA','NET'],[([t[k] for k in ('abbr','W','L','T','PCT','PF','PA','NET')],t['source_url']) for t in stand],'32 official standings rows; no tail-column labels inferred.')
    +section('Week 8 passing snapshot')+table(['Player','Team as rendered','ATT','YDS','CPOE (percentage points)'],[([p[k] for k in ('name','team','ATT','YDS','CPOE')],p['source_url']) for p in passing],'27 rendered NGS rows. Week 8 only, not season totals. Coverage is not all players.')
    +section('Week 9 matchup/date snapshot')+table(['Away','Designated home','Date','Kickoff ET','Venue','Scope'],[([g['away'],g['home'],g['date'],None,None,g['neutral_status']],g['source_url']) for g in sched],'Matchup/date verified. LOCAL schedule labels do not establish ET; kickoff time and venue withheld.')
    +text('Download selected-field observations: <a href="../public-data/standings.json">standings JSON</a> · <a href="../public-data/passing.json">passing JSON</a> · <a href="../public-data/schedule.json">schedule JSON</a>.'))
pages['model-lines']=('Research lines','Originate a transparent baseline. Do not confuse it with a validated price.',
    note('PROJECT CALCULATIONS — not official NFL fair prices. All 15 rows are BLOCKED. Market handicap, quoted payout, win probability, EV and selection remain blank. The mean total is not a calibrated distribution.')
    +text('Strength = NET / (games + 8); predicted home margin = home strength − away strength. Fair home handicap = negative predicted home margin. HFA = 0 everywhere because it has not been estimated; Madrid is explicitly neutral. Shrinkage of eight games is a design choice. Total = average of the two teams’ per-game scoring/allowing matchups. No injury adjustment is inferred.')
    +table(['Away → home','Date','Baseline home handicap','Baseline total','Market handicap','Decimal price','P(win)','EV','Selection','Status'],[([f"{g['away']} → {g['home']}",g['date'],g['home_handicap'],g['total'],None,None,None,None,None,'BLOCKED'],g['source_url']) for g in D['lines']],'Calculated from verified standings; each schedule link supports the matchup, not the forecast.')
    +text(link(NFL,'Official standings inputs ↗')+' · Model version: untrained-margin-shrink8-hfa0-v1. This is a reproducible reference baseline, not a recommended bet.'))
pages['strategies']=('Strategy registry','Eight hypotheses. No performance claims.',
    note('Every strategy is BLOCKED. Source links support feature definitions or general statistical context, not profitable signals or project thresholds.')
    +table(['ID','Strategy','Market family','Hypothesis','Status'],[([s['id'],s['name'],s['type'],s['hypothesis'],s['status']],s['source_url']) for s in D['strategies']],'Research registry — no discovered edge has been validated.')
    +section('How a signal earns promotion')+text('Run feature ablations within expanding chronological training folds. Compare against a frozen baseline on the same future games, check calibration and quoted-price net EV, and include every attempted variant in multiplicity adjustment. A good-looking in-sample chart does not pass a strategy.')
    +text('Detailed volume/efficiency decompositions, no-look-ahead requirements and combo modeling are in the <a href="methodology.html">full research protocol</a>.'))
gate_rules=[('provenance','Official evidence for every input/result plus direct operator quote; a URL alone is insufficient.'),('asof','Timezone-aware feature ≤ prediction < kickoff; no postgame features. Policy freshness: 24h context, 15m quote.'),('availability','Current official participation, injuries/inactives and roles; missing information fails closed.'),('history','Policy: ≥3 training seasons plus a separate untouched complete evaluation season; game-level data required.'),('holdout','Nested chronological development, untouched season and subsequent prospective shadow trial.'),('calibration','Paired baseline improvement and positive lower 95% game-cluster bounds; calibrated tails/pushes and EV.'),('multiple_testing','All registered variants; Holm family-wise alpha 0.05. No winner-only testing.'),('price','Timestamped executable exact market/side/threshold, actual decimal payout and settlement rules.'),('joint_distribution','Singles document no multi-leg exposure; combos require feasible held-out calibrated joints.'),('risk','Points-only policy: flat 1 unit; ≤1 aggregate unit/game and ≤5/week; deduplicate shared exposure.'),('preregistered','Prediction, input/model/quote hashes, rules and stakes frozen before kickoff; append-only corrections.')]
pages['validation-gates']=('Validation gates','Only explicit PASS clears a gate.',
    note('All eleven gates must pass. CONDITIONAL is not PASS. Missing gates block promotion. Numeric thresholds below are proposed project policies, not official league requirements or proven power guarantees.')
    +table(['Gate','Required evidence / project policy','Current outcome'],[([g,r,'BLOCKED / NOT EVALUATED'],NIST if g in ('history','holdout','calibration','multiple_testing','risk') else NGS) for g,r in gate_rules],'No strategy currently passes the complete gate set.')
    +text('The executable strict-gate helper is regression-tested. The statistical trial and a live collector are not implemented. Publication of flagged items does not waive any research gate.'))
pages['correlations']=('Correlations','Describe the sample. Respect the observational unit.',
    note('Cross-team associations cannot be substituted for game-level bet-leg dependence. Teams play each other; n=32 is not 32 independent games. No ordinary independent-row confidence intervals or causal/skill claims are reported.')
    +table(['Pair','Method','n','Unit','r','Scope'],[([c['pair'],c['method'],c['n'],c['unit'],c['r'],c['kind']],c['source_url']) for c in D['correlations']],'First three rows: project calculations on checked standings. Blank rows: bet-leg correlation not estimable.')
    +text('Pair observations by stable game/player IDs and as-of time. Estimate residual and threshold-hit dependence on held-out games. For two legs, enforce feasible Bernoulli joint bounds; three or more legs require a full coherent joint model. Different games are not automatically independent.')
    +text('NIST: '+link(NIST,'Association is not causation ↗')+' The complete mathematical conventions and limitations are in the research protocol.'))
pages['leaderboard']=('Skill leaderboard','An empty result is more honest than an invented winner.',
    note('No settled prediction ledger exists. Ranks, observed game counts, ROI, skill scores and rewards are intentionally blank—not zero. List order is registry order, not rank.')
    +table(['Rank','ID','Strategy','Settled games','Unit ROI','Skill score','Reward','Status'],[([None,s['id'],s['name'],None,None,None,None,'UNRANKED — blocked'],s['source_url']) for s in D['strategies']],'No qualified strategies; no actual reward has been awarded.')
    +section('Proposed qualification and ranking')+text('Points-only, no entry fee or cash prize. Require all gates, frozen holdout plus a prospective shadow season, at least 200 distinct settled game clusters over 12 weeks, positive lower 95% bound for paired Brier improvement and net quoted-price EV, and Holm-adjusted prespecified test success. These are policy minima, not power guarantees.')
    +text('Rank by lower confidence bound of paired baseline Brier improvement, then lower ROI confidence bound, then lower clustered drawdown. Share unresolved ties. Gold/Silver/Bronze badges are proposed for the first three qualified ranks only. Never award based on projections, sum weekly ROI percentages, or assume −110 payouts.'))
pages['sources']=('Sources & provenance','What was actually checked—and what was not.',
    note('Official-source links are for manual review. A checked source is not blanket verification of every field on that site. Unfetched references and future review targets are not marked verified.')
    +table(['ID','Publisher / source','Checked','Verification scope'],[([s['id'],s['label'],s['checked_at'],s['scope']],s['url']) for s in sources],'Retrieval log, 2026-11-04. Full scope and selected transcriptions retained in the repository.')
    +text('Source evidence: <a href="../public-data/standings-excerpt.txt">standings transcription</a> · <a href="../public-data/passing-excerpt.txt">NGS transcription</a> · <a href="../public-data/schedule-excerpt.txt">schedule transcription</a> · <a href="../public-data/input-manifest.json">SHA-256 input manifest</a>. A hash supports reproducibility, not truth or an original source timestamp.')
    +section('Current injury-report scope')+text('The official Week 9 report now exists. In retrieved chunk 0, CIN/ATL and NYG/PHI sections say No Injuries Reported; Lamar Jackson is listed Did Not Participate In Practice with a blank game-status cell. These are report observations, not healthy-roster or final active-status guarantees. No quantitative injury adjustment or eligibility pass is inferred. '+link('https://www.nfl.com/injuries/league/2026/reg9','Official Week 9 report ↗'))+section('Legacy provenance')+text('All baseline files and structured rows are inventoried on the repository audit page. Old CSV column issues, top-25 coverage and third-party quotes have not silently been promoted to verified data. The independent selected-field snapshot is the only data consumed by the current model.'))
pages['flagged']=('Flagged for Review','Published limitations. No silent passes.',
    note('These findings do not block website publication. They do block unsupported model eligibility. References below are official review context; code locations identify project defects, not statements by those publishers.')
    +table(['ID','Severity','Irregularity','Location','Disposition'],[([f['id'],f['severity'],f['item'],f['location'],f['resolution']],f['source_url']) for f in findings],'Independent audit — material findings, corrections and deployment limits.')
    +section('Earlier review register')+table(['Legacy ID','Current disposition'],[([f['id'],'Retained as historical claim; not independently reverified in full. Legacy numeric values withheld; see repository audit.'],(f.get('source_url') if (f.get('source_url') or '').startswith(('https://www.nfl.com/','https://nextgenstats.nfl.com/')) else NFL)) for f in load('data/flagged.json')['items']],'Earlier F-register identifiers retained; not represented as newly verified findings.')
    +text('All legacy dataset rows—including unconfirmed player statistics, injuries, scores, news and market inputs—remain accessible as a redacted inventory on the audit page. Their numerical values are blank until independently confirmed.'))
pages['repository-audit']=('Repository audit','A complete baseline inventory—not a blanket accuracy certificate.',
    note(f"Baseline commit {audit['baseline_commit']}. {len(audit['files'])} tracked files, {sum(f['lines'] for f in audit['files'])} text lines inventoried; {len(audit['legacy_rows'])} legacy structured rows enumerated. Hash/line scans are mechanical coverage, not a claim that every historical factual sentence was independently verified.")
    +table(['Baseline file','Text lines','SHA-256','Disposition'],[([f['path'],f['lines'],f['sha256'],f['disposition']],f['source_url']) for f in audit['files']],'All baseline tracked files. Official links are review targets only.')
    +section('Every legacy structured data row')+table(['Legacy file','Row','Legacy label (unverified claim)','Verified legacy value','Status'],[([r['file'],r['row'],r['legacy_label'][:110],None,r['status']],r['source_url']) for r in audit['legacy_rows']],'Legacy inventory. Labels identify original claims, not confirmed identities or events. Numeric values deliberately withheld.')
    +text('Download the complete inventory: <a href="../public-data/repository-audit.json">repository-audit.json</a>. Historical scripts/docs/HTML remain in Git, excluded from the isolated Pages artifact.'))
pages['methodology']=('Full research protocol','Reproducible methods, explicit assumptions and unimplemented work.',md_render((R/'research/methodology.md').read_text()))
pages['responsible-gambling']=('Research & safety','No wagering or cash-reward competition.',
    text('This project does not place bets, connect sportsbook accounts, accept deposits or run a paid contest. Its proposed badges are non-monetary. No performance or profit is guaranteed; skill and luck cannot be perfectly separated in finite samples.')
    +text('Do not infer legal permission from approximate location. The Washington State Gambling Commission describes a limited tribal-casino framework and requires on-premises geofencing for mobile sports wagers. '+link('https://www.wsgc.wa.gov/tribal-partnerships/sports-wagering/sports-wagering-requirements-and-rules','Read the regulator’s requirements ↗'))
    +text(link('https://www.wsgc.wa.gov/responsible-gaming-self-exclusion','Official help and self-exclusion resources ↗')+' This is not personalized legal advice.'))
OUT.mkdir(exist_ok=True)
# Clean ONLY generated artifact, never repository root or arbitrary directories.
for p in list(OUT.iterdir()):
    if p.is_dir(): shutil.rmtree(p)
    else: p.unlink()
(OUT/'pages').mkdir(); (OUT/'assets').mkdir(); (OUT/'public-data').mkdir()
for p in (R/'assets').glob('*'):
    if p.is_file(): shutil.copy2(p,OUT/'assets'/p.name)
nav_order=['index','executive-summary','verified-data','model-lines','strategies','validation-gates','correlations','leaderboard','flagged','sources','repository-audit','methodology','responsible-gambling']
for slug,(title,subtitle,body) in pages.items():
    pre='' if slug=='index' else '../'
    nav=''.join(f'<a class="{"active" if slug==k else ""}" href="{pre}{"index.html" if k=="index" else "pages/"+k+".html"}"'+(' aria-current="page"' if slug==k else '')+'>'+esc(pages[k][0])+'</a>' for k in nav_order)
    doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Evidence-first NFL line origination research. Verified snapshots, experimental baselines and strict validation gates."><title>{esc(title)} · Own8 NFL Lab</title><link rel="stylesheet" href="{pre}assets/style.css"><script src="{pre}assets/app.js" defer></script></head><body><a class="skip" href="#main">Skip to content</a><aside><a class="brand" href="{pre}index.html"><b>8</b> OWN8<span>NFL RESEARCH LAB</span></a><nav aria-label="Categories">{nav}</nav><div class="sidebar-foot">INDEPENDENT RESEARCH<br>Snapshot · 04 Nov 2026<br>No wagering. No guaranteed edge.</div></aside><div class="workspace"><header><span>NFL / RESEARCH DESK</span><span class="dot">DATED SNAPSHOT</span></header><main id="main"><div class="page-heading"><div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div><label class="search">Filter rows on this page<input type="search" placeholder="Search table rows…" aria-label="Filter table rows"></label></div>{body}<p id="filter-status" role="status" aria-live="polite"></p></main><footer>OWN8 · Observations ≠ predictions ≠ validated skill.<br>Blank numeric cells are unavailable or unverified. Official links do not endorse project methods.<br><a href="{pre}pages/sources.html">Provenance</a> · <a href="{pre}pages/flagged.html">Flagged for Review</a></footer></div></body></html>'''
    dest=Path('index.html') if slug=='index' else Path('pages')/(slug+'.html')
    (OUT/dest).write_text(doc); (R/dest).parent.mkdir(exist_ok=True); (R/dest).write_text(doc)
# Old incoming URLs remain usable but never show stale facts.
aliases={'standings':'verified-data','schedule':'verified-data','scores':'repository-audit','team-stats':'repository-audit','player-stats':'verified-data','injuries':'flagged','prop-signals':'strategies'}
for old,new in aliases.items():
    doc=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={new}.html"><title>Moved · Own8</title></head><body><p>This historical page was superseded by the independent audit. <a href="{new}.html">Continue to the current page</a>.</p></body></html>'
    (OUT/'pages'/f'{old}.html').write_text(doc); (R/'pages'/f'{old}.html').write_text(doc)
# Root checkout preview and legacy main/root deployment can serve downloads too.
public=R/'public-data'; public.mkdir(exist_ok=True)
for p in list((R/'data/verified').glob('*.json'))+list((R/'data/evidence').glob('*'))+[R/'analysis/input-manifest.json',R/'analysis/repository-audit.json',R/'analysis/dashboard.json',R/'data/review-findings.json']:
    shutil.copy2(p,OUT/'public-data'/p.name); shutil.copy2(p,public/p.name)
if (R/'strict').exists():
    shutil.copytree(R/'strict',OUT/'strict')
(OUT/'audit').mkdir(exist_ok=True)
(OUT/'audit/index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../pages/flagged.html"><title>Historical audit superseded</title></head><body><p>The historical audit is preserved in Git. <a href="../pages/flagged.html">Read current review findings</a>.</p></body></html>')
(OUT/'verification').mkdir(exist_ok=True)
shutil.copy2(R/'verification/README.md',OUT/'verification/README.md')
(OUT/'.nojekyll').write_text('')
print(f'Built {len(pages)} category pages + {len(aliases)} legacy redirects; artifact excludes historical HTML and unverified numeric datasets.')
