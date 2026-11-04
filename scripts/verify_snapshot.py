"""Check selected numeric data against retained transcriptions and legacy differences.
This repeats an evidence consistency check, not a new network verification.
"""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_text())
errors=[];count=0
rows=load('data/verified/standings.json')['rows']; old={r['abbr']:r for r in load('data/standings-2026-reg-w8.json')['teams']}
lines=(R/'data/evidence/standings-excerpt.txt').read_text().split('Columns: abbr W L T PCT PF PA NET\n')[1].strip().splitlines()
assert len(lines)==len(rows)==32
for t,line in zip(rows,lines):
    a,w,l,tie,pct,pf,pa,net=line.split()
    expected=dict(abbr=a,W=int(w),L=int(l),T=int(tie),PCT=float(pct),PF=int(pf),PA=int(pa),NET=int(net))
    for k,v in expected.items():
        count+=1
        if t[k]!=v:errors.append(f'{a}.{k}: transcription mismatch')
        if old[a][k]!=v:errors.append(f'{a}.{k}: legacy mismatch; requires review')
    gp=t['W']+t['L']+t['T']
    if t['PF']-t['PA']!=t['NET'] or abs((t['W']+.5*t['T'])/gp-t['PCT'])>.00051:errors.append(f'{a}: arithmetic error')
ngs=load('data/verified/passing.json')['rows']
lines=(R/'data/evidence/passing-excerpt.txt').read_text().split('name|team|ATT|YDS|CPOE\n')[1].strip().splitlines()
assert len(lines)==len(ngs)==27
for row,line in zip(ngs,lines):
    name,team,a,y,c=line.split('|')
    for k,v in dict(name=name,team=team,ATT=int(a),YDS=int(y),CPOE=float(c)).items():
        count+=1
        if row[k]!=v:errors.append(f'{name}.{k}: transcription mismatch')
schedule=load('data/verified/schedule.json')['rows']
assert len(schedule)==15 and len({g['away'] for g in schedule}|{g['home'] for g in schedule})==30
for g in schedule:
    assert g['kickoff_et'] is None and g['venue'] is None
manifest=load('analysis/input-manifest.json')
for path,digest in manifest.items():
    if hashlib.sha256((R/path).read_bytes()).hexdigest()!=digest:errors.append(f'{path}: changed since analysis')
dashboard=load('analysis/dashboard.json')
assert dashboard['eligible_count']==0 and dashboard['settled_ledger_count']==0
for s in dashboard['strategies']:
    assert not s['eligible'] and all(s[k] is None for k in ('rank','roi','skill_score','reward','n_settled_games'))
for g in dashboard['lines']:
    assert not g['eligible'] and all(g[k] is None for k in ('market_home_handicap','decimal_price','p_win','joint_probability','ev','selection'))
report=dict(checked_at='2026-11-04',status='PASS' if not errors else 'FAIL',selected_cells_compared=count,errors=errors,scope='Selected fields vs retained independent-review transcriptions, arithmetic, input hashes and fail-closed output invariants. Not a fresh HTTP source check or a certification of legacy data.')
(R/'analysis/verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
