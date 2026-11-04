#!/usr/bin/env python3
"""Record scope honestly: static review != external factual verification.
Inventory legacy captures row by row, withholding every unverified value.
"""
import csv, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
D=ROOT/'data'; A=ROOT/'analysis'
def save(p,x): p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
s=json.loads((D/'audit-snapshot.json').read_text())
old={t['abbr']:t for t in json.loads((D/'standings-2026-reg-w8.json').read_text())['teams']}
diffs=[]; checks=0
for row in s['standings']:
 for k in ('W','L','T','PCT','PF','PA','NET','STRK'):
  checks+=1
  if old[row['abbr']][k]!=row[k]: diffs.append(f"{row['abbr']}.{k}")
 if row['PF']-row['PA']!=row['NET']: diffs.append(f"{row['abbr']} NET arithmetic")
 n=row['W']+row['L']+row['T']
 if abs((row['W']+.5*row['T'])/n-row['PCT'])>.00051: diffs.append(f"{row['abbr']} PCT arithmetic")
assert not diffs, diffs
legacy=[]
for p in sorted(D.glob('*.json')):
 if p.name.startswith('audit-') or p.name in ('flagged.json','sources.json'): continue
 d=json.loads(p.read_text()); field=next((k for k in ('teams','games','players','items','lines') if isinstance(d.get(k),list)),None)
 if not field: continue
 # Audited fields are displayed separately; this inventory makes no claims about the remainder.
 for i,r in enumerate(d[field],1):
  label=r.get('name') or r.get('abbr') or r.get('game') or (f"{r['away']} at {r['home']}" if 'away' in r and 'home' in r else r.get('headline')) or f'Row {i}'
  url=d.get('source_url') or r.get('source_url') or r.get('player_url') or 'https://www.nfl.com/stats/player-stats/'
  if not (url.startswith('https://www.nfl.com/') or url.startswith('https://nextgenstats.nfl.com/')): url='https://www.nfl.com/scores/'
  if p.name=='market-lines.json': label=f'Legacy market row {i}'
  verified_core=p.name in ('standings-2026-reg-w8.json','schedule-2026-week9.json')
  legacy.append(dict(file=p.name,row=i,label=label,values=None,status='PARTIAL — see audited fields' if verified_core else 'UNVERIFIED — legacy values withheld',source_url=url))
for p in sorted(D.glob('*.csv')):
 with p.open() as f:
  for i,r in enumerate(csv.DictReader(f),1):
   legacy.append(dict(file=p.name,row=i,label=r.get('player') or r.get('player_name') or r.get('team') or f'CSV row {i}',values=None,status='UNVERIFIED — legacy CSV not promoted',source_url='https://www.nfl.com/standings/' if 'standings' in p.name else 'https://nextgenstats.nfl.com/'))
save(A/'audit-inventory.json',dict(as_of=s['as_of'],rows=legacy,note='Labels identify inherited entries, NOT verified identities. Numbers intentionally absent. Official source links are verification targets unless separately listed in audit-snapshot.json.'))
files=[]
for name in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines():
 p=ROOT/name
 if not p.is_file(): continue
 raw=p.read_bytes()
 try: lines=len(raw.decode().splitlines())
 except UnicodeDecodeError: lines=None
 role='Historical artifact — not served, not independently verified' if name.startswith(('archive/','docs/')) else 'Source capture — only explicit audited fields promoted' if name.startswith('data/') else 'Executable/source or generated output — static checks; not official factual evidence'
 generated=(name=='index.html' or name.startswith(('pages/','analysis/')) or (name.startswith('docs/') and name.endswith('.html')))
 files.append(dict(path=name,lines=None if generated else lines,sha256=None if generated else hashlib.sha256(raw).hexdigest(),review=('Generated artifact — hashes/line counts omitted to avoid a self-referential audit manifest' if generated else role),source_url='https://www.nfl.com/standings/'))
save(A/'repo-audit.json',dict(as_of=s['as_of'],files=files,note='Every tracked file inventoried with line counts and SHA-256; this is NOT a claim to verify every historical assertion. Official-source coverage is explicitly bounded by audit-snapshot.json.',official_standings_fields_checked=checks,standings_mismatches=diffs,verified_score_rows=sum(g['status']=='VERIFIED' for g in s['scores']),unverified_score_rows=sum(g['status']!='VERIFIED' for g in s['scores'])))
print(f'Audit: {checks} standings field comparisons, 0 mismatches; {len(legacy)} inherited entries inventoried.')
