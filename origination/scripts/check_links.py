#!/usr/bin/env python3
"""O5 — Link + provenance checker for origination/*.html (standard library only).

1. Every internal (relative) href must resolve to an existing file in the repository.
2. Every external href must be https.
3. Every data-table body row must contain at least one link to an official NFL domain
   (nfl.com / nextgenstats.nfl.com). Structural tables (navigation, gate definitions) and the
   Flagged-for-review table (process items may cite GitHub PRs) are checked for >= 1 link instead.
Exit code 1 on any failure. External sites are not fetched (sandbox egress is restricted); they are
listed in results/external-links.txt for manual review.
"""
import os
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # origination/
OFFICIAL = ("www.nfl.com", "nfl.com", "nextgenstats.nfl.com")
STRUCTURAL_HEADERS = ({"Page", "What it shows"}, {"Gate", "Rule"})


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.tables = [], []
        self._t = None
        self._row = None
        self._in_th = False
        self._th_text = ""
        self._in_tbody = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link") and "href" in a:
            self.links.append(a["href"])
            if self._row is not None and tag == "a":
                self._row.append(a["href"])
        if tag == "table":
            self._t = {"headers": [], "rows": []}
        elif tag == "th":
            self._in_th, self._th_text = True, ""
        elif tag == "tbody":
            self._in_tbody = True
        elif tag == "tr" and self._in_tbody:
            self._row = []

    def handle_endtag(self, tag):
        if tag == "th":
            self._in_th = False
            self._t["headers"].append(self._th_text.strip())
        elif tag == "tr" and self._row is not None:
            self._t["rows"].append(self._row)
            self._row = None
        elif tag == "tbody":
            self._in_tbody = False
        elif tag == "table":
            self.tables.append(self._t)
            self._t = None

    def handle_data(self, data):
        if self._in_th:
            self._th_text += data


def main():
    fails, external, n_rows, n_links = [], set(), 0, 0
    pages = sorted(f for f in os.listdir(HERE) if f.endswith(".html"))
    for page in pages:
        p = P()
        with open(os.path.join(HERE, page), encoding="utf-8") as f:
            p.feed(f.read())
        for href in p.links:
            n_links += 1
            u = urlparse(href)
            if u.scheme in ("http", "https"):
                if u.scheme != "https":
                    fails.append(f"{page}: non-https link {href}")
                external.add(href)
            elif u.scheme in ("", None) and not href.startswith("#"):
                target = os.path.normpath(os.path.join(HERE, u.path))
                if os.path.isdir(target):
                    target = os.path.join(target, "index.html")
                if not os.path.exists(target):
                    fails.append(f"{page}: broken internal link {href}")
        for t in p.tables:
            hdr = set(t["headers"])
            structural = any(s <= hdr for s in STRUCTURAL_HEADERS)
            flagged = page == "flagged.html"
            for i, row in enumerate(t["rows"]):
                n_rows += 1
                if structural or flagged:
                    if not row:
                        fails.append(f"{page}: table {t['headers'][:2]} row {i+1} has no link")
                    continue
                if not any(urlparse(h).netloc in OFFICIAL for h in row):
                    fails.append(f"{page}: table {t['headers'][:2]} row {i+1} lacks an official source link")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "external-links.txt"), "w", encoding="utf-8") as f:
        f.write("# External links on origination/*.html (not fetched by the checker; for manual review)\n")
        f.write("\n".join(sorted(external)) + "\n")
    print(f"pages={len(pages)} links={n_links} external_unique={len(external)} table_rows={n_rows} failures={len(fails)}")
    for x in fails[:50]:
        print("FAIL", x)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
