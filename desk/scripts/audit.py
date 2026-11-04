"""Inventory every baseline tracked file and every legacy data row; no implied verification."""
import csv,hashlib,io,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
BASE='7c2f5459350c8a94f13cd12d4315ba92b044275a'
NFL='https://www.nfl.com/standings/'
def git(*args): return subprocess.check_output(['git',*args],cwd=R)
files=[]; entries=[]
for name in git('ls-tree','-r','--name-only',BASE).decode().splitlines():
    raw=git('show',f'{BASE}:{name}'); text=raw.decode(errors='replace')
    files.append(dict(path=name,sha256=hashlib.sha256(raw).hexdigest(),lines=len(text.splitlines()),disposition='Baseline inventory; not independently fact-verified. Historical content excluded from deployed artifact.' if name.startswith(('archive/','docs/')) else 'Reviewed for provenance and publication; see findings and selected-field verification. No blanket verification.',source_url=NFL))
    if not name.startswith('data/') or not name.endswith(('.csv','.json')): continue
    try:
        d=json.loads(text) if name.endswith('.json') else None
        if d is None:
            rows=list(csv.DictReader(io.StringIO(text))); source=NFL
        else:
            source=d.get('source_url',NFL)
            rows=next((d[k] for k in ('teams','players','games','items','lines','sources') if isinstance(d.get(k),list)),[])
        for i,row in enumerate(rows,1):
            if not isinstance(row,dict): continue
            src=row.get('source_url',source) or NFL
            if not src.startswith(('https://www.nfl.com/','https://nextgenstats.nfl.com/')): src='https://www.nfl.com/stats/player-stats/'
            label=row.get('name') or row.get('abbr') or row.get('item') or row.get('game') or row.get('label') or row.get('id') or f"{row.get('away','')} at {row.get('home','')}"
            entries.append(dict(file=name,row=i,legacy_label=str(label),verified_value=None,status='UNVERIFIED legacy row; numeric values withheld. Selected independently checked fields appear only on Verified Data.',source_url=src))
    except (ValueError,TypeError):
        raise
out={'baseline_commit':BASE,'checked_at':'2026-11-04','scope':'Every baseline tracked text file inventoried by hash and line count; all legacy structured data rows enumerated. Static code review is not independent fact verification. Official URLs below are review targets, not endorsements of legacy values.','files':files,'legacy_rows':entries}
(R/'analysis/repository-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(f'Inventory: {len(files)} files, {sum(f["lines"] for f in files)} text lines, {len(entries)} legacy rows')
