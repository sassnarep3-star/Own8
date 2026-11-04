#!/usr/bin/env python3
"""Read-only row-source QA of the currently fetched PR #6 ref. No network required.

Run git fetch origin arena/28cc78aa-own8 then python3 verification/check_pr6.py.
This only tests whether each rendered table row contains an official NFL link;
it does NOT validate the factual correctness of the linked value.
"""
import json
import subprocess
from html.parser import HTMLParser
from urllib.parse import urlparse

REF = 'origin/arena/28cc78aa-own8'

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_row = False; self.in_header = False
        self.row = None; self.rows = []; self.cell = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'thead': self.in_header = True
        if tag == 'tr' and not self.in_header:
            self.in_row = True; self.row = {'links': [], 'text': ''}; self.cell = 0
        if tag == 'td' and self.in_row: self.cell += 1
        if tag == 'a' and self.in_row and 'href' in a:
            self.row['links'].append(a['href'])
    def handle_data(self, data):
        if self.in_row: self.row['text'] += data
    def handle_endtag(self, tag):
        if tag == 'tr' and self.in_row:
            self.in_row = False
            if self.cell: self.rows.append(self.row)
        if tag == 'thead': self.in_header = False

def official(url):
    host = urlparse(url).hostname or ''
    return host == 'nfl.com' or host.endswith('.nfl.com') or (host == 'github.com' and urlparse(url).path.startswith('/nfl-football-ops/'))

def main():
    files = subprocess.check_output(['git', 'ls-tree', '--name-only', REF, 'site/'], text=True).splitlines()
    # ls-tree site/ emits directory in some git versions: recursively enumerate
    files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', REF, 'site/'], text=True).splitlines()
    result = {'ref': REF, 'scope': 'Rendered site HTML table rows, official-link PRESENCE only; not field verification.', 'pages': {}, 'total_rows': 0, 'rows_without_official_link': 0}
    for file in files:
        if not file.endswith('.html'): continue
        source = subprocess.check_output(['git', 'show', f'{REF}:{file}'], text=True)
        p = Rows(); p.feed(source)
        absent = [{'row': i+1, 'text': ' '.join(r['text'].split())[:180], 'links': r['links']} for i,r in enumerate(p.rows) if not any(official(link) for link in r['links'])]
        result['pages'][file] = {'rows': len(p.rows), 'without_official_link': len(absent), 'examples': absent[:5]}
        result['total_rows'] += len(p.rows)
        result['rows_without_official_link'] += len(absent)
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()
