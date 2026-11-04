"""Check isolated artifact paths/fragments, HTTPS, allowlist and per-table-row references.
This is NOT an external HTTP reachability or semantic fact checker.
"""
import json,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
R=Path(__file__).resolve().parents[1]; SITE=R/'_site'
OFFICIAL={'www.nfl.com','nextgenstats.nfl.com','www.itl.nist.gov','www.wsgc.wa.gov','docs.github.com','operations.nfl.com','wsgc.wa.gov','kansspelautoriteit.nl'}
def official_url(raw):
    u=urlsplit(raw)
    return u.hostname in OFFICIAL or (u.hostname=='github.com' and (u.path=='/nfl-football-ops/Big-Data-Bowl' or u.path.startswith('/nfl-football-ops/Big-Data-Bowl/')))
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.urls=[];self.ids=set();self.row=False;self.in_body=False;self.row_sources=[];self.missing_rows=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for k in ('href','src'):
            if k in a:self.urls.append(a[k])
        if tag=='tbody':self.in_body=True
        if tag=='tr' and self.in_body:self.row=True;self.row_sources=[]
        if self.row and tag=='a' and official_url(a.get('href','')):self.row_sources.append(a['href'])
    def handle_endtag(self,tag):
        if tag=='tr' and self.row:
            if not self.row_sources:self.missing_rows+=1
            self.row=False
        if tag=='tbody':self.in_body=False
pages={}; errors=[];count=0
for p in SITE.rglob('*.html'):
    v=Page();v.feed(p.read_text());pages[p.resolve()]=v
for p,v in pages.items():
    if v.missing_rows:errors.append(f'{p.relative_to(SITE)}: {v.missing_rows} rows lack an official reference')
    for raw in v.urls:
        count+=1;u=urlsplit(raw)
        if u.scheme:
            if u.scheme!='https' or not official_url(raw):errors.append(f'{p.name}: disallowed URL {raw}')
            continue
        target=(p.parent/unquote(u.path)).resolve() if u.path else p
        if not target.is_relative_to(SITE.resolve()):errors.append(f'{p.name}: path escapes artifact {raw}');continue
        if target.is_dir():target=target/'index.html'
        if not target.exists():errors.append(f'{p.name}: missing {raw}');continue
        if u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:errors.append(f'{p.name}: missing fragment {raw}')
report=dict(checked_at='2026-11-04',pages=len(pages),links=count,errors=errors,status='PASS' if not errors else 'FAIL',scope='Isolated artifact internal files/fragments, official per-row reference presence and HTTPS/host policy. External HTTP reachability and semantic evidence support NOT certified.')
(R/'analysis/link-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.exit(bool(errors))
