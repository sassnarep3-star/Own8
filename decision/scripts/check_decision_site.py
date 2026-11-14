#!/usr/bin/env python3
"""Offline checks for decision/site: internal links/anchors, per-row official sources,
and that every external link is https.

Explicitly does NOT test whether external sites are live (the build shell has no network).
Writes decision/results/link-check.json and exits non-zero on any failure.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent.parent
SITE = ROOT / "decision" / "site"
# Official / authoritative hosts this section is allowed to cite.
OFFICIAL = {"www.nfl.com", "nextgenstats.nfl.com", "www.itl.nist.gov", "wsgc.wa.gov",
            "github.com", "www.github.com"}


class Doc(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links, self.ids, self.rows = [], set(), []
        self.row, self.in_body = None, False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tbody":
            self.in_body = True
        if tag == "tr" and self.in_body:
            self.row = []
        for k in ("href", "src"):
            if k in a:
                self.links.append(a[k])
                if self.row is not None:
                    self.row.append(a[k])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.in_body = False


def official(u):
    p = urlparse(u)
    return p.scheme == "https" and p.hostname in OFFICIAL


files = sorted(SITE.glob("*.html"))
docs = {p.resolve(): Doc(p.read_text()) for p in files}
errors, links, rows = [], 0, 0
for p, d in docs.items():
    for row in d.rows:
        rows += 1
        if not any(official(u) for u in row):
            errors.append(f"{p.name}: table row has no official source link")
    for url in d.links:
        links += 1
        u = urlparse(url)
        if u.scheme:
            if u.scheme != "https":
                errors.append(f"{p.name}: non-HTTPS {url}")
            elif not official(url):
                errors.append(f"{p.name}: not an approved authoritative host {url}")
            continue
        target = (p.parent / unquote(u.path)).resolve() if u.path else p
        if SITE not in target.parents and target != SITE:
            errors.append(f"{p.name}: escapes section root {url}")
            continue
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            errors.append(f"{p.name}: missing {url}")
        elif u.fragment and (target not in docs or unquote(u.fragment) not in docs[target].ids):
            errors.append(f"{p.name}: missing anchor {url}")

result = dict(checked_at="2026-11-14", scope="decision/site only; external liveness not tested",
              pages=len(files), links_checked=links, table_rows_checked=rows,
              errors=errors, status="PASS" if not errors else "FAIL")
(ROOT / "decision" / "results" / "link-check.json").write_text(json.dumps(result, indent=1) + "\n")
print(json.dumps(result, indent=1))
raise SystemExit(bool(errors))
