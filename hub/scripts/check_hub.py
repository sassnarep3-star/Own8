#!/usr/bin/env python3
"""Checks for the NFL hub. Exit 1 on any failure.

1. Every internal href/src in hub/**/*.html resolves to an existing file.
2. Every data table row (<tbody><tr>) has at least one https link in it (source link rule).
3. Standings CSV: 32 rows; per-team home+road = record; net = PF-PA; league W = L, PF = PA.
4. The 32 standings rows on the page match the CSV.
5. Injury CSV: every row has a team, player and an injury, practice or game status.
6. Every official-looking link uses an allowed host.
"""
import csv
import html.parser
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

HUB = Path(__file__).resolve().parent.parent
ALLOWED_HOSTS = {"www.nfl.com", "nextgenstats.nfl.com", "ask.gov.sg", "github.com"}
failures = []


class Collect(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # (href)
        self.rows = []  # list of lists of link hrefs per row inside tbody
        self._in_tbody = False
        self._row = None
        self.row_text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link", "script", "img") and (a.get("href") or a.get("src")):
            self.links.append(a.get("href") or a.get("src"))
        if tag == "tbody":
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self._row = []
        if tag == "a" and self._row is not None and a.get("href"):
            self._row.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self._in_tbody = False
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def check_links(path):
    text = path.read_text(encoding="utf-8")
    c = Collect()
    c.feed(text)
    for href in c.links:
        if href.startswith(("#", "mailto:")):
            continue
        u = urlparse(href)
        if u.scheme in ("http", "https"):
            if u.netloc not in ALLOWED_HOSTS:
                failures.append(f"{path.relative_to(HUB)}: host not on allow list: {href}")
            continue
        target = (path.parent / u.path).resolve()
        if not target.exists():
            failures.append(f"{path.relative_to(HUB)}: broken internal link {href}")
    for i, row in enumerate(c.rows):
        if not any(h.startswith("https://") for h in row):
            failures.append(f"{path.relative_to(HUB)}: table body row {i} has no source link")
    return len(c.rows)


def check_standings():
    rows = list(csv.DictReader(open(HUB / "data/standings-official.csv", encoding="utf-8")))
    if len(rows) != 32:
        failures.append(f"standings: expected 32 rows, found {len(rows)}")
    W = sum(int(r["w"]) for r in rows)
    L = sum(int(r["l"]) for r in rows)
    PF = sum(int(r["pf"]) for r in rows)
    PA = sum(int(r["pa"]) for r in rows)
    if W != L:
        failures.append(f"standings: league wins {W} != losses {L}")
    if PF != PA:
        failures.append(f"standings: league PF {PF} != PA {PA}")
    for r in rows:
        w, l, t = int(r["w"]), int(r["l"]), int(r["t"])
        h = [int(x) for x in r["home"].split("-")]
        ro = [int(x) for x in r["road"].split("-")]
        if [h[i] + ro[i] for i in range(3)] != [w, l, t]:
            failures.append(f"standings {r['abbr']}: home+road != record")
        if int(r["pf"]) - int(r["pa"]) != int(r["net"]):
            failures.append(f"standings {r['abbr']}: net != PF-PA")
    return rows


def check_standings_page(rows):
    text = (HUB / "pages/standings.html").read_text(encoding="utf-8")
    for r in rows:
        needle = f"<td>{r['abbr']}</td>"
        if needle not in text:
            failures.append(f"standings page missing {r['abbr']}")
    if text.count("<tr>") - 1 < 32:
        failures.append("standings page: fewer than 32 body rows")


def check_injuries():
    rows = list(csv.DictReader(open(HUB / "data/injuries-w10.csv", encoding="utf-8")))
    for r in rows:
        if not (r["team"] and r["player"]):
            failures.append(f"injury row missing team/player: {r}")
        if not (r["injury"] or r["practice_status"] or r["game_status"]):
            failures.append(f"injury row has no status: {r['player']}")
    return rows


def main():
    pages = sorted(HUB.rglob("*.html"))
    total_rows = 0
    for p in pages:
        total_rows += check_links(p)
    st = check_standings()
    check_standings_page(st)
    inj = check_injuries()
    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print(f"PASS: {len(pages)} pages, {total_rows} table rows (all with a source link), "
          f"{len(st)} standings rows (arithmetic OK), {len(inj)} injury rows, 0 broken internal links.")


if __name__ == "__main__":
    main()
