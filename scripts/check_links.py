#!/usr/bin/env python3
"""Offline release checks: local URLs/anchors, per-row official links, null safety.
Does NOT claim to test HTTP availability of external sites or their every claim.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
R=Path(__file__).resolve().parent.parent
OFFICIAL={'www.nfl.com','nextgenstats.nfl.com','www.itl.nist.gov','wsgc.wa.gov','github.com','docs.github.com'}
class Doc(HTMLParser):
 def __init__(self,text):
  super().__init__(); self.links=[]; self.ids=set(); self.rows=[]; self.row=None; self.body=False; self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a: self.ids.add(a['id'])
  if tag=='tbody': self.body=True
  if tag=='tr' and self.body: self.row=[]
  for k in ('href','src'):
   if k in a:
    self.links.append(a[k])
    if self.row is not None: self.row.append(a[k])
 def handle_endtag(self,tag):
  if tag=='tr' and self.row is not None: self.rows.append(self.row); self.row=None
  if tag=='tbody': self.body=False

def official(u):
 p=urlparse(u)
 return p.scheme=='https' and p.hostname in OFFICIAL and (p.hostname!='github.com' or p.path.startswith('/nfl-football-ops/'))
files=[R/'index.html',*sorted((R/'pages').glob('*.html')),*sorted((R/'docs').glob('*.html')),*sorted((R/'audit').glob('*.html'))]
docs={p.resolve():Doc(p.read_text()) for p in files}; errors=[]; rows=0; links=0
for p,d in docs.items():
 for row in d.rows:
  rows+=1
  if not any(official(u) for u in row): errors.append(f'{p.relative_to(R)}: row missing official reference')
 for url in d.links:
  links+=1; u=urlparse(url)
  if u.scheme:
   if u.scheme!='https': errors.append(f'{p.name}: non-HTTPS URL {url}')
   elif not official(url): errors.append(f'{p.name}: unapproved official host/path {url}')
   continue
  target=(p.parent/unquote(u.path)).resolve() if u.path else p
  if R not in target.parents and target!=R: errors.append(f'{p.name}: escaped root {url}'); continue
  if target.is_dir(): target=target/'index.html'
  if not target.exists(): errors.append(f'{p.name}: missing {url}')
  if u.fragment and (target not in docs or unquote(u.fragment) not in docs[target].ids): errors.append(f'{p.name}: missing anchor {url}')
# Audit-independent canonical output assertions.
lines=json.loads((R/'analysis/model-lines-week9.json').read_text())['games']
for g in lines:
 if g['candidate'] or g['gates_all_pass'] or any(g[k] is not None for k in ('market_spread_home','edge_pts','market_price','moneyline','win_probability')): errors.append(g['game']+': evidence boundary violated')
for c in json.loads((R/'analysis/correlations.json').read_text())['correlations']:
 if c['type']=='Bernoulli leg dependence' and (c['r'] is not None or c['n'] is not None): errors.append('Unverified leg estimate populated')
result=dict(checked_at='2026-11-04',scope='Canonical root + pages + docs redirects + preserved baseline audit; external HTTP checks not performed by this checker',pages=len(files),links_checked=links,table_rows_checked=rows,errors=errors,status='PASS' if not errors else 'FAIL')
(R/'analysis/link-check.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
