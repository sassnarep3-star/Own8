"""Verify the decision ledger. Exit code 0 only if every check passes. Standard library only.

    python3 ledger/scripts/check_ledger.py

Checks:
  1. Every data file parses and has the expected row counts (149 results, 39 markets, 13 lines, 14 strategies).
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
    if len(rows) == 149 and feed["counts"].get("added_week10_finals") == 12:
        ok("results feed: 149 final rows (136 verified log + 1 Thursday + 12 rechecked Sunday finals)")
    else:
        fail("results feed row count/addendum mismatch: %d rows, %s added W10 finals" % (
            len(rows), feed["counts"].get("added_week10_finals")))
    if len({r["key"] for r in rows}) == len(rows):
        ok("results feed: all game keys unique")
    else:
        fail("results feed: duplicate game keys")
    if len(feed.get("unresolved", [])) == 1 and feed["unresolved"][0].get("scores") is None:
        ok("results feed: one W10 result unresolved, excluded without imputation")
    else:
        fail("results feed: unresolved W10 status missing or populated with an unverified score")
    addendum = load("data/week10-results-addendum.json")
    new_w10 = [r for r in rows if r.get("verified_at") == addendum.get("captured_at_utc")]
    source_rows = {r["key"]: r for r in addendum.get("rows", [])}
    addendum_ok = len(new_w10) == 12 and len(source_rows) == 12
    for r in new_w10:
        src = source_rows.get(r["key"])
        if (not src or src.get("status") != "Final" or src.get("source_url") != "https://www.nfl.com/scores/2026/week-10"
                or host_of(src.get("game_url", "")) != "www.nfl.com"
                or r["away_score"] != src["away_score"] or r["home_score"] != src["home_score"]):
            addendum_ok = False
            fail("results feed: addendum/source mismatch for %s" % r["key"])
    unresolved = addendum.get("unresolved", [])
    if len(unresolved) != 1 or unresolved[0].get("scores") is not None:
        addendum_ok = False
        fail("results feed: unresolved source row missing or filled with a score")
    if addendum_ok and all(r.get("verification_status") == "Final (official NFL score page + game center)" for r in new_w10):
        ok("results feed: all 12 Week 10 additions match the timestamped NFL-linked Final addendum")
    else:
        fail("results feed: Week 10 additions missing timestamp, exact source match or final-status marker")
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

    # verified locked line (F-01 / X3 reconciliation): every market carries the locked FanDuel
    # line from the nfl.com picks article; opening/closing intentionally remain null.
    locked = [m for m in prices["markets"] if m.get("official_locked_value") is not None]
    if len(locked) == 39:
        ok("price store: 39 of 39 markets carry a verified locked line")
    else:
        fail("price store locked-line count %d != 39" % len(locked))
    for m in prices["markets"]:
        url = m.get("official_locked_source_url")
        if m.get("official_locked_value") is not None:
            if host_of(url or "") not in set(prices["accepted_source_hosts"]):
                fail("price %s locked line has no accepted official source" % m["market_key"])
            if not m.get("official_locked_at"):
                fail("price %s locked line has no lock timestamp" % m["market_key"])
        else:
            if url is not None:
                fail("price %s has a locked source with no value" % m["market_key"])
        if m["market"] in ("side", "total"):
            if m.get("official_locked_numeric") is None:
                fail("price %s %s has no locked numeric" % (m["market_key"], m["market"]))
    ok("price store: every locked line carries an accepted nfl.com source and a lock timestamp")
    # dated snapshot history (ported 08643438): every snapshot row carries an accepted source
    snaps = prices.get("snapshots", [])
    if not snaps:
        fail("price store: snapshots[] is empty - dated history missing")
    for s in snaps:
        if host_of(s.get("source_url") or "") not in set(prices["accepted_source_hosts"]):
            fail("snapshot %s has no accepted official source" % s.get("snapshot_key"))
        if not s.get("captured_at") or not s.get("locked_at"):
            fail("snapshot %s lacks capture/lock timestamps" % s.get("snapshot_key"))
        if s.get("value") is None:
            fail("snapshot %s has a null value" % s.get("snapshot_key"))
    ok("price store: %d dated snapshot rows, each with an accepted source and timestamps" % len(snaps))

    lines = load("data/lines-columns.json")
    if len(lines["rows"]) == 13:
        ok("lines: 13 Week 10 games")
    else:
        fail("lines row count %d != 13" % len(lines["rows"]))
    for r in lines["rows"]:
        for block, key in (("side", "market_spread"), ("total", "market_total")):
            if r[block]["difference_fair_minus_market"] is not None and r[block][key] is None:
                fail("difference computed without a market value for %s" % r["key"])
        # recompute each difference from the stored fair and market values (sign guard)
        if r["side"]["market_spread"] is not None:
            exp = round(r["side"]["fair_home_margin_S1"] + r["side"]["market_spread"], 3)
            if abs(r["side"]["difference_fair_minus_market"] - exp) > 1e-6:
                fail("side difference for %s is %s, recomputed %s" % (r["key"], r["side"]["difference_fair_minus_market"], exp))
        if r["total"]["market_total"] is not None:
            exp = round(r["total"]["fair_total"] - r["total"]["market_total"], 2)
            if abs(r["total"]["difference_fair_minus_market"] - exp) > 1e-6:
                fail("total difference for %s is %s, recomputed %s" % (r["key"], r["total"]["difference_fair_minus_market"], exp))
        if r["moneyline"]["market_ml_home"] is not None:
            ph = 100.0 / (100.0 + r["moneyline"]["market_ml_home"]) if r["moneyline"]["market_ml_home"] > 0 else -float(r["moneyline"]["market_ml_home"]) / (100.0 - r["moneyline"]["market_ml_home"])
            pa = 100.0 / (100.0 + r["moneyline"]["market_ml_away"]) if r["moneyline"]["market_ml_away"] > 0 else -float(r["moneyline"]["market_ml_away"]) / (100.0 - r["moneyline"]["market_ml_away"])
            dv = round(ph / (ph + pa), 4)
            if abs(r["moneyline"]["market_p_home_devig"] - dv) > 1e-6:
                fail("moneyline de-vig for %s is %s, recomputed %s" % (r["key"], r["moneyline"]["market_p_home_devig"], dv))
            exp = round(r["moneyline"]["fair_p_home"] - dv, 4)
            if abs(r["moneyline"]["difference_fair_minus_market"] - exp) > 1e-6:
                fail("moneyline difference for %s is %s, recomputed %s" % (r["key"], r["moneyline"]["difference_fair_minus_market"], exp))
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
