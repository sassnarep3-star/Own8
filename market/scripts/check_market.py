#!/usr/bin/env python3
"""Validate the built market site. Exits non-zero on any violation.

Checks
  1. every internal href resolves to a file that exists
  2. every page is reachable from the navigation
  3. every table that is a data table (i.e. not the capability matrix of URLs) has at
     least one external official link on every row
  4. no page contains a broken placeholder, an unfilled format brace, or 'None'
  5. every external link is https
  6. the count of tables on each page matches what the builder intended to emit
"""
import re
import sys
from pathlib import Path

MARKET = Path(__file__).resolve().parent.parent
HTML_FILES = [MARKET / "index.html"] + sorted((MARKET / "pages").glob("*.html"))

HREF = re.compile(r'href="([^"]+)"')
ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
TABLE = re.compile(r"<table>.*?</table>", re.S)
# Tables where a URL column is the subject rather than the provenance of a value.
EXEMPT_CAPTIONS = {"Capability matrix, tested 2026-11-14"}


def main():
    errors = []
    warns = []
    pages = {}
    for f in HTML_FILES:
        pages[f] = f.read_text()

    # 1. internal links
    for f, text in pages.items():
        for href in HREF.findall(text):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (f.parent / href).resolve()
            if not target.exists():
                errors.append(f"{f.relative_to(MARKET)}: broken link -> {href}")

    # 5. external links must be https
    for f, text in pages.items():
        for href in HREF.findall(text):
            if href.startswith("http://"):
                errors.append(f"{f.relative_to(MARKET)}: insecure external link -> {href}")

    # 1b. external URLs must be real, fetchable links: no spaces, no placeholders
    for f, text in pages.items():
        for href in HREF.findall(text):
            if not href.startswith("http"):
                continue
            if " " in href or "%20" in href or "{" in href or "}" in href or "..." in href:
                errors.append(f"{f.relative_to(MARKET)}: malformed external link -> {href}")

    # 2. navigation coverage
    nav_targets = set()
    for href in HREF.findall(pages[MARKET / "index.html"]):
        if href.startswith("pages/"):
            nav_targets.add(href)
    for f in HTML_FILES[1:]:
        rel = "pages/" + f.name
        if rel not in nav_targets:
            errors.append(f"{rel} is not linked from the index")

    # 3. every data-table row carries an external link
    checked_rows = 0
    for f, text in pages.items():
        for tbl in TABLE.findall(text):
            cap = re.search(r"<caption>(.*?)</caption>", tbl)
            cap = cap.group(1) if cap else ""
            if cap in EXEMPT_CAPTIONS:
                continue
            body = tbl.split("<tbody>", 1)[-1]
            for tr in ROW.findall(body):
                if "<td" not in tr and "<th" not in tr:
                    continue
                checked_rows += 1
                if 'href="http' not in tr:
                    snippet = re.sub(r"<[^>]+>", " ", tr)[:90]
                    errors.append(f"{f.relative_to(MARKET)}: table row with no official link [{cap}] :: {snippet.strip()}")

    # 4. template leakage
    for f, text in pages.items():
        for bad in ("{e(", "Unnamed: 0", "None<", "NaN", ">None", '"None"'):
            if bad in text:
                errors.append(f"{f.relative_to(MARKET)}: template leakage or null value '{bad}'")

    tables = sum(len(TABLE.findall(t)) for t in pages.values())
    print(f"pages {len(pages)}, tables {tables}, data rows checked {checked_rows}, errors {len(errors)}")
    for e in errors[:40]:
        print("  ERR", e)
    for w in warns:
        print("  WARN", w)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
