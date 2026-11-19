#!/usr/bin/env python3
"""Checks the built site: internal links resolve, every table body row has a source link or an UNVERIFIED mark,
and every page is linked from the navigation. Exit 1 on any failure. Standard library only."""
import glob, html.parser, os, re, sys

SITE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SITE, ".."))
fails = []


class P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.tables, self.in_tbody, self.row, self.row_has = [], [], False, None, False
        self.row_links, self.bad_rows, self.depth_tbody = [], [], 0
        self.row_has_official, self.row_checks = False, []
        self.text_buf = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
            if self.row is not None:
                self.row_has = True
                if d["href"].startswith(("https://www.nfl.com/", "https://static.www.nfl.com/", "https://nextgenstats.nfl.com/")):
                    self.row_has_official = True
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row = True
            self.row_has = False
            self.row_has_official = False
            self.text_buf = []
        if tag == "table":
            self.tables.append(d.get("class", ""))

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row is not None:
            txt = "".join(self.text_buf)
            if not self.row_has and "UNVERIFIED" not in txt and "NOT FINAL" not in txt and "NOT GRADED" not in txt:
                self.bad_rows.append(txt[:80])
            self.row_checks.append((self.row_has_official, "UNVERIFIED" in txt))
            self.row = None

    def handle_data(self, data):
        if self.row is not None:
            self.text_buf.append(data)


pages = sorted(glob.glob(os.path.join(SITE, "*.html")))
names = {os.path.basename(p) for p in pages}
nav_links = set()
for p in pages:
    src = open(p, encoding="utf-8").read()
    ps = P()
    ps.feed(src)
    nav_links |= {l for l in ps.links if not l.startswith(("http", "#", "mailto"))}
    for l in ps.links:
        if l.startswith(("http://", "https://", "#", "mailto:")):
            if l.startswith("http") and not re.match(r"^https://(www\.nfl\.com|static\.www\.nfl\.com|github\.com|nextgenstats\.nfl\.com|wsgc\.wa\.gov|www\.itl\.nist\.gov)/", l):
                fails.append(f"{os.path.basename(p)}: external link not on allowed hosts: {l}")
            continue
        target = os.path.normpath(os.path.join(SITE, l))
        if not os.path.exists(target):
            fails.append(f"{os.path.basename(p)}: broken internal link {l}")
    for l in ps.links:
        m = re.match(r"https://github\.com/sassnarep3-star/Own8/(?:blob|tree)/main/([^#?]+)$", l)
        if m and not os.path.exists(os.path.join(ROOT_DIR, m.group(1))):
            fails.append(f"{os.path.basename(p)}: repo link to a file that does not exist: {m.group(1)}")
    for r in ps.bad_rows:
        fails.append(f"{os.path.basename(p)}: table row without source link or UNVERIFIED mark: {r!r}")
    if os.path.basename(p) in ("decision-guide.html", "questions.html", "correlations.html", "strategies.html"):
        for i, (has_official, explicitly_unverified) in enumerate(ps.row_checks, 1):
            if not has_official and not explicitly_unverified:
                fails.append(f"{os.path.basename(p)}: table row {i} has neither an official NFL link nor an UNVERIFIED marker")
    if os.path.basename(p).startswith("data-") and re.search(r"\bARI\b", re.sub(r"<[^>]+>", " ", src)):
        fails.append(f"{os.path.basename(p)}: legacy team code ARI in visible text")

for n in sorted(names):
    if n != "index.html" and n not in nav_links and n not in ("flagged.html",):
        pass
    if n not in nav_links and n != "index.html":
        fails.append(f"orphan page not linked from any page: {n}")

for f in ("assets/site.css", "assets/site.js"):
    if not os.path.exists(os.path.join(SITE, f)):
        fails.append(f"missing asset {f}")

for j in glob.glob(os.path.join(SITE, "data", "*.json")):
    import json
    try:
        json.load(open(j, encoding="utf-8"))
    except Exception as e:  # noqa
        fails.append(f"bad json {j}: {e}")

print(f"pages checked: {len(pages)}")
if fails:
    print("FAILURES:", len(fails))
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("OK: links resolve, every table row has a source or UNVERIFIED mark, no orphan pages")
