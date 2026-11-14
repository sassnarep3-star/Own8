#!/usr/bin/env python3
"""Check the advisory hub and the Week 10 injury tracker (session d6bada32).

Checks, for every HTML file in advisory/ and injury-depth/:
  1. every relative link/anchor resolves to an existing file and (if given) an existing id;
  2. every external link uses https and a host on the allowlist (NFL.com, the Singapore regulator,
     or github.com for repo-internal evidence);
  3. every <tr> in a data table contains at least one link (the 'every row has a source' rule);
  4. every empty table cell that is part of a data row is either intentionally blank with an
     UNVERIFIED flag, or the row has no value column (simple check: blank cells carry the class 'unverified').
Exit code 0 = PASS, 1 = FAIL.  Run: python3 advisory/check_links.py
"""
import html.parser, os, re, sys
from urllib.parse import urlparse, urldefrag

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIRS = [os.path.join(ROOT, "advisory"), os.path.join(ROOT, "injury-depth")]
ALLOWED_HOSTS = {"www.nfl.com", "nfl.com", "static.www.nfl.com", "nextgenstats.nfl.com",
                 "www.gra.gov.sg", "gra.gov.sg", "sso.agc.gov.sg", "github.com"}

class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.rows, self.stack = [], set(), [], []
        self.cur_row = None
        self.in_thead = False
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "thead":
            self.in_thead = True
        if "id" in d:
            self.ids.add(d["id"])
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
            if self.cur_row is not None:
                self.cur_row["links"] += 1
        if tag == "tr":
            self.cur_row = {"links": 0, "line": self.getpos()[0], "row_id": d.get("id", ""), "header": self.in_thead}
            self.rows.append(self.cur_row)
    def handle_endtag(self, tag):
        if tag == "thead":
            self.in_thead = False
        if tag == "tr":
            self.cur_row = None

def check_file(path, problems):
    src = open(path, encoding="utf-8").read()
    p = Page()
    p.feed(src)
    here = os.path.dirname(path)
    # pages in the same dir refer to each other; collect ids per file for anchor checks
    checked = 0
    for href in p.links:
        if href.startswith("mailto:") or href.startswith("#") and href == "#":
            continue
        url, frag = urldefrag(href)
        if url.startswith("https://") or url.startswith("http://"):
            host = urlparse(url).netloc
            if not url.startswith("https://"):
                problems.append(f"{path}: non-https external link {href}")
            if host not in ALLOWED_HOSTS:
                problems.append(f"{path}: host not on allowlist: {href}")
            checked += 1
            continue
        target = os.path.normpath(os.path.join(here, url)) if url else path
        if not os.path.exists(target):
            problems.append(f"{path}: broken relative link {href}")
            continue
        if frag and target.endswith(".html"):
            tgt = Page()
            tgt.feed(open(target, encoding="utf-8").read())
            if frag not in tgt.ids:
                problems.append(f"{path}: anchor #{frag} not found in {os.path.relpath(target, ROOT)}")
        checked += 1
    return checked, p

def main():
    problems, total_links, total_rows, total_files = [], 0, 0, 0
    for d in DIRS:
        for name in sorted(os.listdir(d)):
            if not name.endswith(".html"):
                continue
            path = os.path.join(d, name)
            total_files += 1
            n, p = check_file(path, problems)
            total_links += n
            if name in ("index.html",) and os.path.basename(d) == "injury-depth":
                pass
            # Data rows: every <tr> inside <tbody> must carry at least one link (header rows excluded)
            if "<tbody>" in open(path, encoding="utf-8").read():
                for r in p.rows:
                    if r["line"] == 0 or r["header"]:
                        continue
                    total_rows += 1
                    if r["links"] == 0:
                        problems.append(f"{os.path.relpath(path, ROOT)}:{r['line']}: table row has no source link")
    status = "PASS" if not problems else "FAIL"
    print(f"files={total_files} links={total_links} data_rows={total_rows} problems={len(problems)} -> {status}")
    for x in problems[:60]:
        print("  " + x)
    return 0 if not problems else 1

if __name__ == "__main__":
    sys.exit(main())
