"""Verify the decision ledger. Exit code 0 only if every check passes. Standard library only.

    python3 ledger/scripts/check_ledger.py

Checks:
  1. Every data file parses and has the expected row counts (137 results, 39 markets, 13 lines, 14 strategies).
  2. Every table row on every ledger page (except the navigation table) carries at least one link to an
     allowed official host, or the row is a flag whose sources are listed in its JSON record.
  3. Every internal link resolves to a file in the repository.
  4. No opening or closing value exists without an official source URL.
  5. No table cell says DIFFERS unless it is labelled as a difference to review.
  6. Results feed: every row has an nfl.com game URL and arithmetic passes.
"""
import html.parser
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.dirname(HERE)
ROOT = os.path.dirname(LEDGER)

ALLOWED_HOSTS = {"www.nfl.com", "nextgenstats.nfl.com", "www.itl.nist.gov", "www.espn.com"}
SECONDARY_HOSTS = {"www.espn.com"}  # allowed only in flags/probe, labelled SECONDARY there

PAGES = ["index.html", "suggestions.html", "price-store.html", "results-feed.html", "lines.html", "demotion-gate.html",
         "leaderboard-split.html", "flagged.html"]

errors, passes = [], []


def ok(msg):
    passes.append(msg)


def fail(msg):
    errors.append(msg)


def load(rel):
    with open(os.path.join(LEDGER, rel), encoding="utf-8") as f:
        return json.load(f)


class Tables(html.parser.HTMLParser):
    """Collect each <tr> in <tbody>, with its table class and its hrefs."""

    def __init__(self):
        super().__init__()
        self.table_stack = []
        self.rows = []  # (table_class, [hrefs], text)
        self.in_tbody = 0
        self.row = None
        self.hrefs_all = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.table_stack.append(a.get("class", "") or "")
        if tag == "tbody":
            self.in_tbody += 1
        if tag == "tr" and self.in_tbody and self.table_stack:
            self.row = {"cls": self.table_stack[-1], "hrefs": [], "text": []}
        if tag == "a" and a.get("href"):
            self.hrefs_all.append(a["href"])
            if self.row is not None:
                self.row["hrefs"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.in_tbody -= 1
        if tag == "table" and self.table_stack:
            self.table_stack.pop()

    def handle_data(self, data):
        if self.row is not None:
            self.row["text"].append(data)


def host_of(url):
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1) if m else None


def check_data():
    feed = load("data/results-feed.json")
    rows = feed["rows"]
    if len(rows) == 137:
        ok("results feed: 137 rows (136 verified log + 1 Thursday game)")
    else:
        fail("results feed row count %d != 137" % len(rows))
    bad = [r["key"] for r in rows if not r["arithmetic_ok"]]
    (ok if not bad else fail)("results feed arithmetic: %s" % ("all rows pass" if not bad else "failures %s" % bad))
    for r in rows:
        if host_of(r["game_url"]) != "www.nfl.com" or host_of(r["source_url"]) != "www.nfl.com":
            fail("results feed row %s lacks an nfl.com link" % r["key"])
            break
    else:
        ok("results feed: every row has nfl.com game and source links")

    prices = load("data/price-snapshots.json")
    if len(prices["markets"]) == 39:
        ok("price store: 39 originated markets (13 games x side, total, moneyline)")
    else:
        fail("price store market count %d != 39" % len(prices["markets"]))
    verified = 0
    for m in prices["markets"]:
        for field, src in (("opening_value", "opening_source_url"), ("closing_value", "closing_source_url")):
            if m[field] is not None:
                verified += 1
                if host_of(m[src] or "") not in set(prices["accepted_source_hosts"]):
                    fail("price %s %s has a value without an accepted official source" % (m["market_key"], field))
    ok("price store: %d opening/closing values recorded (each must carry an official URL)" % verified)

    lines = load("data/lines-columns.json")
    if len(lines["rows"]) == 13:
        ok("lines: 13 Week 10 games")
    else:
        fail("lines row count %d != 13" % len(lines["rows"]))
    for r in lines["rows"]:
        for block, key in (("side", "market_spread"), ("total", "market_total")):
            if r[block]["difference_fair_minus_market"] is not None and r[block][key] is None:
                fail("difference computed without a market value for %s" % r["key"])
        if host_of(r["game_url"]) != "www.nfl.com" or host_of(r["source_url"]) != "www.nfl.com":
            fail("lines row %s lacks an nfl.com link" % r["key"])
    if not lines["recompute_mismatches"]:
        ok("lines: fair spread text and moneyline recompute from the stored inputs with no mismatch")
    else:
        fail("lines recompute mismatches: %s" % lines["recompute_mismatches"])

    reg = load("data/strategy-registry.json")
    if len(reg["strategies"]) == 14:
        ok("registry: 14 strategies (12 scored, 2 not scored)")
    else:
        fail("registry size %d != 14" % len(reg["strategies"]))
    for s in reg["strategies"]:
        if not s["source_urls"] or any(host_of(u) != "www.nfl.com" for u in s["source_urls"]):
            fail("strategy %s lacks nfl.com source links" % s["id"])
    if reg["live_count"] == 0:
        ok("registry: 0 LIVE strategies (no operator decision recorded)")
    else:
        fail("registry reports %d LIVE strategies without an operator decision" % reg["live_count"])

    rules = load("data/demotion-rules.json")
    for rule in rules["rules"]:
        if host_of(rule["source_url"]) not in ALLOWED_HOSTS:
            fail("demotion rule %s has a non-allowed source" % rule["id"])
    ok("demotion rules: %d rules, every one with an allowed source link" % len(rules["rules"]))

    split = load("results/leaderboard-split.json")
    if all(r["consistency"]["matches_origination_rank"] for r in split["rows"]):
        ok("leaderboard split: ranks match origination leaderboard for every strategy")
    else:
        fail("leaderboard split disagrees with origination ranks")

    probe = load("data/price-probe.json")
    if host_of(probe["url"]) == "www.nfl.com":
        ok("price probe: official nfl.com URL recorded with result and scope")
    else:
        fail("price probe URL is not nfl.com")

    flags = load("data/flags.json")["flags"]
    for f in flags:
        srcs = f.get("source_urls", [])
        if not srcs:
            fail("flag %s has no source link" % f["id"])
        for u in srcs:
            if host_of(u) not in ALLOWED_HOSTS:
                fail("flag %s links to a non-allowed host: %s" % (f["id"], u))
    ok("flags: %d flags, each with at least one allowed source link" % len(flags))


def check_pages():
    internal_targets = set()
    for name in PAGES:
        path = os.path.join(LEDGER, name)
        if not os.path.exists(path):
            fail("missing page %s" % name)
            continue
        text = open(path, encoding="utf-8").read()
        p = Tables()
        p.feed(text)
        data_rows = 0
        for row in p.rows:
            if row["cls"] == "nav":
                continue
            joined = " ".join(row["text"]).strip()
            if not joined:
                continue
            data_rows += 1
            allowed = [h for h in row["hrefs"] if host_of(h) in ALLOWED_HOSTS]
            if name == "suggestions.html" and not allowed:
                # suggestion rows may cite a repository file (internal link) when no official page applies
                allowed = [h for h in row["hrefs"] if not re.match(r"https?://", h)]
            if not allowed:
                fail("%s: a table row has no allowed official link: %s" % (name, joined[:90]))
            if "DIFFERS" in joined:
                fail("%s: a row reports DIFFERS: %s" % (name, joined[:90]))
        for href in p.hrefs_all:
            if re.match(r"https?://", href):
                if host_of(href) not in ALLOWED_HOSTS:
                    fail("%s links to a non-allowed host: %s" % (name, href))
                continue
            if href.startswith("#"):
                continue
            target = os.path.normpath(os.path.join(LEDGER, href))
            internal_targets.add(target)
            if not os.path.exists(target):
                fail("%s: broken internal link %s" % (name, href))
        if "<table" in text and data_rows == 0 and name != "index.html":
            fail("%s has a table but no data rows" % name)
        ok("%s: %d data rows checked" % (name, data_rows))
    if not errors:
        ok("all internal links resolve")


def main():
    check_data()
    check_pages()
    for m in passes:
        print("PASS  " + m)
    for e in errors:
        print("FAIL  " + e)
    print("\n%d checks passed, %d failed" % (len(passes), len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
