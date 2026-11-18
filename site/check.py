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
        self.text_buf = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
            if self.row is not None:
                self.row_has = True
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row = True
            self.row_has = False
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

# --- capture integrity: stored captures unchanged (sha256); JSON re-parsed from captures without drift ---
import hashlib, json as _json
_man_path = os.path.join(SITE, "data", "captures", "manifest.json")
if not os.path.exists(_man_path):
    fails.append("capture manifest missing: data/captures/manifest.json")
else:
    _man = _json.load(open(_man_path, encoding="utf-8"))
    for _c in _man["captures"]:
        _p = os.path.join(ROOT_DIR, _c["file"])
        if not os.path.exists(_p):
            fails.append(f"capture file missing: {_c['file']}")
            continue
        _data = open(_p, "rb").read()
        if hashlib.sha256(_data).hexdigest() != _c["sha256"] or len(_data) != _c["bytes"]:
            fails.append(f"capture changed since manifest hash: {_c['file']}")
        if not _c["source_url"].startswith("https://"):
            fails.append(f"capture without https source: {_c['file']}")
    sys.path.insert(0, os.path.join(SITE, "scripts"))
    try:
        import captures as _cap
        _ip, _inir = _cap.parse_injuries(open(_cap.INJ_MD, encoding="utf-8").read())
        _ipub = _json.load(open(os.path.join(SITE, "data", "injuries-w11.json"), encoding="utf-8"))
        if _ipub["players"] != _ip or _ipub["games_no_injuries_reported"] != _inir:
            fails.append("injuries-w11.json differs from its capture (re-run site/scripts/captures.py)")
        if len(_ip) != 26 or len(_inir) != 12:
            fails.append(f"Week 11 injury capture counts changed: {len(_ip)} players, {len(_inir)} NIR games (expected 26, 12)")
        _sc, _lu, _ina, _fin = _cap.parse_gamebook(open(_cap.GB_MD, encoding="utf-8").read())
        _gpub = _json.load(open(os.path.join(SITE, "data", "gamebook-w10-lac-bal.json"), encoding="utf-8"))
        if _gpub["lineups"] != _lu or _gpub["scoring_plays"] != _sc or _gpub["inactives"] != _ina:
            fails.append("gamebook-w10-lac-bal.json differs from its capture (re-run site/scripts/captures.py)")
        if (_fin["visitor_score"], _fin["home_score"]) != (23, 20):
            fails.append("Game Book final score is not 23-20 as recorded")
        _wr = _json.load(open(os.path.join(SITE, "data", "week10-results.json"), encoding="utf-8"))
        _lac = [g for g in _wr.get("finals", []) if g.get("away") == "LAC" and g.get("home") == "BAL"]
        if len(_lac) != 1 or (_lac[0].get("away_score"), _lac[0].get("home_score")) != (_fin["visitor_score"], _fin["home_score"]):
            fails.append("week10-results finals LAC@BAL score disagrees with the Game Book capture")
        if _lac and _lac[0].get("game_book_url") != _gpub["game_book_url"]:
            fails.append("week10-results LAC@BAL Game Book URL differs from the captured Game Book URL")
    except Exception as _e:  # noqa
        fails.append(f"capture re-parse failed: {_e}")

print(f"pages checked: {len(pages)}")
if fails:
    print("FAILURES:", len(fails))
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("OK: links resolve, every table row has a source or UNVERIFIED mark, no orphan pages")
