#!/usr/bin/env python3
"""Check every active/legacy HTML link, fragments, and source on each active table row.
External checks are syntax + explicit official URL scope, NOT HTTP liveness checks.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse,unquote
R=Path(__file__).resolve().parents[1]
class Document(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.links=[];self.ids=set();self.rows=[];self.row=None;self.in_body=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  for key in ['href','src']:
   if key in a:self.links.append(a[key])
  if tag=='tbody':self.in_body=True
  if tag=='tr' and self.in_body:self.row=[]
  if tag=='a' and self.row is not None:self.row.append(a.get('href',''))
 def handle_endtag(self,tag):
  if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
  if tag=='tbody':self.in_body=False

def official(url):
 u=urlparse(url)
 return u.scheme=='https' and (u.hostname in {'www.nfl.com','operations.nfl.com','nextgenstats.nfl.com','www.itl.nist.gov','wsgc.wa.gov','www.wsgc.wa.gov','kansspelautoriteit.nl'} or (u.hostname=='github.com' and u.path.startswith('/nfl-football-ops/Big-Data-Bowl')))

def check():
 docs={}
 for p in R.rglob('*.html'):
  if any(x in p.parts for x in ['.git','node_modules','.venv']):continue
  parser=Document();parser.feed(p.read_text());docs[p]=parser
 errors=[];count=0;rows=0
 for p,doc in docs.items():
  for link in doc.links:
   count+=1;u=urlparse(link)
   if u.scheme:
    if u.scheme!='https':errors.append(f'{p.relative_to(R)}: insecure link {link}')
    if (p==R/'index.html' or p.parent==R/'pages') and not official(link):errors.append(f'{p.relative_to(R)}: not explicit official scope {link}')
    continue
   target=(p.parent/unquote(u.path)).resolve() if u.path else p
   if target.is_dir():target=target/'index.html'
   if not target.is_file():errors.append(f'{p.relative_to(R)}: missing {link}');continue
   if u.fragment and target.suffix=='.html' and target in docs and unquote(u.fragment) not in docs[target].ids:errors.append(f'{p.relative_to(R)}: missing anchor {link}')
  if p==R/'index.html' or p.parent==R/'pages':
   for row in doc.rows:
    rows+=1
    if not any(official(link) for link in row):errors.append(f'{p.relative_to(R)}: row lacks official context/source')
 result={'checked_at':'2026-11-04','html_pages':len(docs),'links_checked':count,'active_table_rows':rows,'errors':errors,'external_http_liveness':'NOT TESTED by this checker; see dated source retrieval ledger','status':'PASS' if not errors else 'FAIL'}
 (R/'strict/link-check.json').write_text(json.dumps(result,indent=2)+'\n')
 (R/'analysis/link-check.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
 return result
if __name__=='__main__':raise SystemExit(0 if check()['status']=='PASS' else 1)
