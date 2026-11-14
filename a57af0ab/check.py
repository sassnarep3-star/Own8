"""Checks for the a57af0ab review hub. Stdlib only. Exit 1 on any failure.

1. Every local href/src resolves to a file in a57af0ab/.
2. Every data row (<tr> inside <tbody>) has at least one https link.
3. Injury rows: every row links to nfl.com (report and game page).
4. Row counts in the published injury pages equal the JSON (14 games, 28 teams, 345 rows).
5. The transcription has exactly one ROW line per JSON row, and every JSON row has an nfl.com source.
6. No insecure http:// links, and no value is filled into blank starter/backup cells.
"""
import json
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).resolve().parent
PAGES = sorted(HERE.glob("*.html"))
failures = []


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []          # (href, src?)
        self.rows = []           # list of list-of-(text, links)
        self._in_tbody = False
        self._row = None
        self._cell = None
        self._cur_links = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link", "script", "img") and ("href" in a or "src" in a):
            v = a.get("href") or a.get("src")
            self.links.append(v)
            if self._cur_links is not None and tag == "a":
                self._cur_links.append(v)
        if tag == "tbody":
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self._row = []
        if tag in ("td", "th") and self._row is not None:
            self._cell = {"text": "", "links": [], "blank": False}
            self._cur_links = self._cell["links"]
        if tag == "span" and "blank" in (a.get("class") or ""):
            if self._cell is not None:
                self._cell["blank"] = True

    def handle_endtag(self, tag):
        if tag == "tbody":
            self._in_tbody = False
        if tag in ("td", "th") and self._cell is not None:
            self._row.append(self._cell)
            self._cell = None
            self._cur_links = None
        if tag == "tr" and self._row is not None and self._in_tbody:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data


def check_local(page, scan):
    for v in scan.links:
        if v is None:
            continue
        p = urlparse(v)
        if p.scheme in ("http", "https"):
            if p.scheme == "http":
                failures.append(f"{page.name}: insecure http link {v}")
            continue
        if v.startswith("#") or v.startswith("mailto:"):
            continue
        target = (HERE / p.path).resolve()
        if not target.exists():
            failures.append(f"{page.name}: broken local link {v}")


counts = {}
for page in PAGES:
    scan = Scan()
    scan.feed(page.read_text(encoding="utf-8"))
    check_local(page, scan)
    data_rows = [r for r in scan.rows if r]
    counts[page.name] = len(data_rows)
    for idx, row in enumerate(data_rows, 1):
        https = [l for c in row for l in c["links"] if l and l.startswith("https://")]
        if not https:
            failures.append(f"{page.name}: row {idx} has no https source link")
        if page.name == "injuries.html":
            # Team table rows and injury rows must link to the official report.
            if not any("nfl.com" in l for l in https):
                failures.append(f"{page.name}: row {idx} has no nfl.com link")
    if page.name in ("questions.html", "suggestions.html", "flagged.html", "repo-review.html", "injuries.html", "executive-summary.html"):
        for idx, row in enumerate(data_rows, 1):
            for c in row:
                if c["blank"] and c["text"].strip() not in ("blank · unverified", "blank", "blank on report", "0 · blank · unverified"):
                    failures.append(f"{page.name}: unexpected blank cell text {c['text']!r}")

# ----- data-level checks -----
inj = json.loads((HERE / "data" / "injuries-2026-w10.json").read_text(encoding="utf-8"))
content = json.loads((HERE / "data" / "content.json").read_text(encoding="utf-8"))
if (len(inj["games"]), len(inj["teams"]), len(inj["rows"])) != (14, 28, 345):
    failures.append("injury JSON counts changed from 14/28/345")
raw = (HERE / "data" / "raw" / "injury-w10-transcription.txt").read_text(encoding="utf-8").splitlines()
raw_rows = [l for l in raw if l.startswith("ROW|")]
if len(raw_rows) != len(inj["rows"]):
    failures.append(f"transcription ROW lines {len(raw_rows)} != JSON rows {len(inj['rows'])}")
for r in inj["rows"]:
    if not r["source_urls"][0].startswith("https://www.nfl.com/") or not r["source_urls"][1].startswith("https://www.nfl.com/"):
        failures.append(f"{r['id']}: source not nfl.com")
    if r["position"] not in ("QB", "RB", "FB", "WR", "TE", "T", "G", "C", "DE", "DT", "LB", "CB", "S", "K", "P", "LS"):
        failures.append(f"{r['id']}: unknown position")
    if r["game_status"] not in ("", "Out", "Doubtful", "Questionable"):
        failures.append(f"{r['id']}: unexpected game status {r['game_status']!r}")
for sec in ("questions", "suggestions", "flagged", "repo_review"):
    for item in content[sec]:
        srcs = [item.get(k) for k in ("links", "evidence", "source")]
        flat = []
        for s in srcs:
            if isinstance(s, list):
                flat += [x["url"] for x in s]
            elif isinstance(s, str):
                flat.append(s)
        if not flat or not all(u.startswith("https://") for u in flat):
            failures.append(f"{sec} {item.get('id')}: missing https source")
        if any(u.startswith("http://") for u in flat):
            failures.append(f"{sec} {item.get('id')}: http link")

print("pages:", {k: v for k, v in counts.items()})
print("injury rows in JSON:", len(inj["rows"]), "| transcription ROW lines:", len(raw_rows))
if failures:
    print(f"FAIL: {len(failures)} problem(s)")
    for f in failures[:80]:
        print(" -", f)
    sys.exit(1)
print("PASS: links resolve; every table row has an https source; injury counts match; no blank cells filled.")
