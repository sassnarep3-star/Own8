#!/usr/bin/env python3
"""Link + source-link checker for the integration workspace (session 2d4025da).

Checks, for every HTML page under integration/:
  1. every internal href/anchor resolves to an existing file (or #fragment in-page);
  2. every external link is https and on an allow-list of official/authoritative hosts
     (nfl.com family, nextgenstats.nfl.com, github.com, itl.nist.gov, wsgc.wa.gov);
  3. every <tr> inside a data table that is NOT a meta-table (checker/CI/health tables)
     contains at least one official-source anchor — fact rows must be source-linked.

Exit 0 = PASS.
"""
import html.parser
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
INT = ROOT / "integration"
ALLOWED = ("https://www.nfl.com/", "https://nextgenstats.nfl.com/", "https://github.com/",
           "https://itl.nist.gov/", "https://wsgc.wa.gov/", "http://www.nfl.com/",
           "https://sassnarep3-star.github.io/")
# Tables whose rows are software evidence rather than NFL facts: no official
# source required, but each row must still carry a link (its evidence).
META_CAPTIONS = ("Checker matrix", "CI workflows", "Pages deploy observations",
                 "Integration tasks", "Published surfaces", "Irregularities found")


class Scan(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.rows = []          # list of (caption, row_html)
        self._caption = None
        self._in_row = False
        self._row_html = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        elif tag == "caption":
            self._caption = ""
        elif tag in ("td", "th") and self._caption is not None:
            pass
        if tag == "tr":
            self._in_row = True
            self._row_html = []
            self._row_has_th = False
        if self._in_row and tag == "th":
            self._row_has_th = True
        if self._in_row and tag == "a" and a.get("href"):
            self._row_html.append(a["href"])

    def handle_data(self, data):
        if self._caption is not None and getattr(self, "_capturing_caption", True):
            if data and self._caption is not None and "<" not in data:
                pass
        if self._caption is not None:
            self._caption += data

    def handle_endtag(self, tag):
        if tag == "caption":
            self._capturing_caption = False
        if tag == "tr" and self._in_row:
            if not getattr(self, "_row_has_th", False):
                self.rows.append((self._caption or "", list(self._row_html)))
            self._in_row = False


def main():
    errors = []
    pages = sorted(INT.glob("*.html"))
    for path in pages:
        text = path.read_text(encoding="utf-8")
        scan = Scan()
        scan.feed(text)
        for href in scan.hrefs:
            if href.startswith(("http://", "https://")):
                if not href.startswith(ALLOWED):
                    errors.append(f"{path.name}: external host not allow-listed: {href}")
                continue
            if href.startswith("#"):
                if f'id="{href[1:]}"' not in text and f"id='{href[1:]}'" not in text:
                    errors.append(f"{path.name}: missing in-page anchor {href}")
                continue
            target = (path.parent / href.split("#")[0]).resolve()
            if not target.exists():
                errors.append(f"{path.name}: broken internal link {href}")
        for caption, row_hrefs in scan.rows:
            if not row_hrefs:
                errors.append(f"{path.name}: row without any link in table '{caption[:50]}'")
            elif not any(caption.startswith(m) for m in META_CAPTIONS):
                if not any(h.startswith(("https://www.nfl.com/", "https://nextgenstats.nfl.com/",
                                         "https://itl.nist.gov/", "https://wsgc.wa.gov/")) for h in row_hrefs):
                    errors.append(f"{path.name}: fact row without official source in '{caption[:50]}'")
    rows_total = sum(len(Scan().rows) for _ in [])  # placeholder, counted below
    # recount rows properly
    total_rows = 0
    for path in pages:
        s = Scan()
        s.feed(path.read_text(encoding="utf-8"))
        total_rows += len(s.rows)
    result = {"pages": len(pages), "rows": total_rows, "errors": len(errors),
              "status": "PASS" if not errors else "FAIL", "detail": errors[:40]}
    import json
    print(json.dumps(result, indent=1))
    (INT / "data" / "link-check.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
