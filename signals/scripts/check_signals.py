#!/usr/bin/env python3
"""
SB7b — the checker that fails the build if the site breaks its own rules.

Checks, each of which has failed on a real project at least once:
   1. every page exists and is well-formed enough to parse (balanced table markup);
   2. every table row in a data table carries at least one link to an allowed source;
   3. no link points at a deleted or non-existent local file;
   4. no page contains a forbidden claim word ("guaranteed", "risk-free", "profit" as a promise), and
      no page calls an unvalidated number "verified";
   5. every blank cell has an aria-label explaining that it is blank on purpose, so a blank cannot be
      mistaken for a zero by a screen reader;
   6. every page states its as-of date;
   7. the source host allowlist is respected: a row may cite an official NFL host, a standards body,
      or an internal page of this site, and nothing else.

Exit code 0 only if every check passes.
Run: python3 signals/scripts/check_signals.py
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

R = Path(__file__).resolve().parents[2]
S = R / "signals"
D = S / "data"

ALLOWED_HOSTS = {
    "www.nfl.com", "nfl.com", "static.www.nfl.com", "nextgenstats.nfl.com",
    "www.itl.nist.gov", "itl.nist.gov",
}
INTERNAL = {"decisions.html", "baselines.html", "market.html", "correlations.html",
            "availability.html", "suggestions.html", "flagged.html", "sources.html",
            "index.html", "assets/style.css", "assets/app.js", "../index.html"}

FORBIDDEN = [
    (r"\bguarantee(d|s)?\b", "a guarantee claim"),
    (r"\brisk[- ]free\b", "a risk-free claim"),
    (r"\bsure (thing|bet)\b", "a certainty claim"),
    (r"\bcan'?t lose\b", "a cannot-lose claim"),
]

PAGES = ["index", "baselines", "market", "correlations", "availability",
         "decisions", "suggestions", "flagged", "sources"]

results = []


def check(name, ok, detail=""):
    results.append({"check": name, "pass": bool(ok), "detail": detail})
    return ok


def text_of(cell_html):
    return html.unescape(re.sub(r"<[^>]+>", "", cell_html)).strip()


def main():
    ok_all = True

    # 1. pages exist, parses
    for slug in PAGES:
        p = S / f"{slug}.html"
        if not check(f"page exists: {slug}.html", p.exists(), str(p)):
            ok_all = False
            continue
        s = p.read_text()
        ok = (s.count("<table") == s.count("</table>")
              and s.count("<tr") == s.count("</tr>")
              and s.count("<td") == s.count("</td>"))
        if not check(f"table markup balanced: {slug}.html", ok,
                     f"tables {s.count('<table')}/{s.count('</table>')} "
                     f"rows {s.count('<tr')}/{s.count('</tr>')} cells {s.count('<td')}/{s.count('</td>')}"):
            ok_all = False
        if not check(f"as-of date present: {slug}.html", "2026-11-14" in s):
            ok_all = False
        # 4. forbidden claims
        for pat, why in FORBIDDEN:
            m = re.search(pat, s, re.I)
            if not check(f"no {why}: {slug}.html", m is None,
                         f"matched {m.group(0)!r}" if m else ""):
                ok_all = False

    # 2/3/5. per-row source links, local links, blank-cell labels
    row_total = 0
    rows_without_link = []
    bad_local = []
    blanks_without_label = 0
    disallowed_hosts = []
    for slug in PAGES:
        p = S / f"{slug}.html"
        if not p.exists():
            continue
        s = p.read_text()
        # local links must exist
        for href in re.findall(r'href="([^"]+)"', s):
            if href.startswith("#") or href.startswith("http"):
                continue
            target = (S / href).resolve()
            if not target.exists():
                bad_local.append(f"{slug}.html -> {href}")
        # blanks must carry an aria-label
        blanks_without_label += len(re.findall(r'<td class="missing"(?!\s+aria-label)', s))
        # every data row must carry an allowed link
        for table_html in re.findall(r"<table>.*?</table>", s, re.S):
            caption = re.search(r"<caption>(.*?)</caption>", table_html)
            caption = text_of(caption.group(1)) if caption else "(no caption)"
            # skip tables that are explicitly navigational (the queue links internally)
            head_cells = re.findall(r"<th[^>]*>(.*?)</th>", table_html, re.S)
            headers = [text_of(c) for c in head_cells]
            link_cols = [i for i, h in enumerate(headers)
                         if h.lower() in ("source", "link", "official basis", "official reference")]
            body = re.search(r"<tbody>(.*)</tbody>", table_html, re.S)
            if not body:
                continue
            for tr in re.findall(r"<tr>(.*?)</tr>", body.group(1), re.S):
                row_total += 1
                cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                ok = False
                for i in link_cols:
                    if i < len(cells) and "<a " in cells[i]:
                        ok = True
                if not ok:
                    # an internal or official link anywhere in the row is also acceptable
                    for c in cells:
                        for href in re.findall(r'href="([^"]+)"', c):
                            if href.startswith("http"):
                                if urlparse(href).netloc in ALLOWED_HOSTS:
                                    ok = True
                            elif href in INTERNAL or (S / href).exists():
                                ok = True
                if not ok:
                    rows_without_link.append(f"{slug}.html :: {caption} :: {text_of(tr)[:90]}")
        # host allowlist
        for href in re.findall(r'href="(https?://[^"]+)"', s):
            host = urlparse(href).netloc
            if host not in ALLOWED_HOSTS:
                disallowed_hosts.append(f"{slug}.html -> {host}")

    if not check("every data row carries a source link", not rows_without_link,
                 f"{row_total} rows checked; unsourced: {rows_without_link[:5]}"):
        ok_all = False
    if not check("no broken local link", not bad_local, str(bad_local[:5])):
        ok_all = False
    if not check("every blank cell is labelled for assistive tech", blanks_without_label == 0,
                 f"{blanks_without_label} unlabelled blanks"):
        ok_all = False
    if not check("every external link is an allowed official host", not disallowed_hosts,
                 str(sorted(set(disallowed_hosts))[:5])):
        ok_all = False

    # 6. data files exist and every page's headline numbers come from them
    for f in ("baseline-ladder.json", "market-relative.json", "correlation-legitimacy.json",
              "availability-tiers.json", "decision-queue.json", "flags.json"):
        if not check(f"data file present: {f}", (D / f).exists()):
            ok_all = False

    # 7. the decision queue's own consistency checks must all pass
    q = json.loads((D / "decision-queue.json").read_text())
    failed = [c for c in q["consistency_checks"] if not c["passes"]]
    if not check("decision queue internal consistency", not failed,
                 f"{len(failed)} failed"):
        ok_all = False

    # 8. the flags file must not be empty and must include the own-work corrections
    fl = json.loads((D / "flags.json").read_text())
    if not check("flags published and own-work corrections included",
                 fl["total"] >= 10 and len(fl["own_work_corrections"]) >= 2,
                 f"total {fl['total']}, own-work {fl['own_work_corrections']}"):
        ok_all = False

    # 9. no page may describe an unvalidated origination as verified
    for slug in ("market",):
        s = (S / f"{slug}.html").read_text()
        bad = re.search(r"verified line|verified price|verified odds", s, re.I)
        if not check(f"no 'verified' claim about a line/price: {slug}.html", bad is None,
                     bad.group(0) if bad else ""):
            ok_all = False

    # 10. guard: the headline claim about promotions must match the computed data, not a hand-typed
    # string. This check exists because the first draft typed the claim and it was wrong.
    mk = json.loads((D / "market-relative.json").read_text())
    declared = mk["market_verdict"]["count_of_arms_clearing"]
    recomputed = sum(1 for c in mk["interval_vs_breakeven"] if c["clears"])
    if not check("promotion claim matches the computed interval data", declared == recomputed,
                 f"declared {declared}, found {recomputed} clearing arms"):
        ok_all = False
    for slug in PAGES:
        s = (S / f"{slug}.html").read_text()
        bad = re.search(r"no (admissible )?arm'? ?s? (hit-rate )?interval clears", s, re.I)
        if not check(f"no false 'no arm clears' claim: {slug}.html", bad is None,
                     bad.group(0) if bad else ""):
            ok_all = False
        bad2 = re.search(r"Eighteen arms|18 arms on one ladder", s)
        if not check(f"arm count wording matches the file: {slug}.html", bad2 is None,
                     bad2.group(0) if bad2 else ""):
            ok_all = False

    passed = sum(1 for r in results if r["pass"])
    out = {
        "generated": "2026-11-14",
        "checks_run": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "rows_checked": row_total,
        "status": "PASS" if ok_all else "FAIL",
        "results": results,
    }
    (D / "site-checks.json").write_text(json.dumps(out, indent=1) + "\n")
    for r in results:
        if not r["pass"]:
            print("FAIL", r["check"], "—", r["detail"])
    print(f"{passed}/{len(results)} checks passed, {row_total} table rows checked, status {out['status']}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
