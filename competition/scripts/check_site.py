#!/usr/bin/env python3
"""Local links, row references, HTML structure and unknown-value safeguards.

Does not claim that an external URL returned HTTP 200, that publisher pages
have not changed, or that a hyperlink proves the adjacent value.
"""
from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids, self.duplicate_ids, self.links, self.data_rows = set(), [], [], []
        self.h1, self.main, self.lang, self.in_body, self.row = 0, 0, None, False, None
        self.header_counts, self.cell_counts = [], []
        self.header, self.cells = None, 0
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids: self.duplicate_ids.append(a["id"])
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if k in a: self.links.append((tag, a[k]))
        if tag == "html": self.lang = a.get("lang")
        if tag == "h1": self.h1 += 1
        if tag == "main": self.main += 1
        if tag == "thead": self.header = 0
        if tag == "th" and self.header is not None: self.header += 1
        if tag == "tbody": self.in_body = True
        if tag == "tr" and self.in_body:
            self.row, self.cells = [], 0
        if tag == "td" and self.row is not None: self.cells += 1
        if tag == "a" and self.row is not None: self.row.append(a.get("href", ""))
    def handle_endtag(self, tag):
        if tag == "thead":
            self.header_counts.append(self.header)
            self.header = None
        if tag == "tr" and self.row is not None:
            self.data_rows.append(self.row)
            self.cell_counts.append((self.cells, self.header_counts[-1]))
            self.row = None
        if tag == "tbody": self.in_body = False


def check():
    paths = sorted(ROOT.glob("*.html"))
    pages = {p.resolve(): Page(p.read_text()) for p in paths}
    sources = json.loads((ROOT / "data/sources.json").read_text())["sources"]
    allowed_refs = {s["url"] for s in sources}
    failures, external, links, rows = [], set(), 0, 0
    for path, page in pages.items():
        label = path.name
        if page.h1 != 1 or page.main != 1 or page.lang != "en":
            failures.append(f"{label}: missing/duplicate main/h1 or language")
        if page.duplicate_ids: failures.append(f"{label}: duplicate IDs {page.duplicate_ids}")
        if any(a != b for a, b in page.cell_counts): failures.append(f"{label}: unequal header/cell counts")
        for row in page.data_rows:
            rows += 1
            project_source = any(u.startswith("https://github.com/sassnarep3-star/Own8/blob/") for u in row)
            if not any(u in allowed_refs for u in row) and not project_source:
                failures.append(f"{label}: data row without a relevant primary source")
        for tag, url in page.links:
            u = urlsplit(url)
            if u.scheme in {"https", "http"}:
                if u.scheme != "https": failures.append(f"{label}: insecure URL {url}")
                external.add(url)
                continue
            if u.scheme:
                failures.append(f"{label}: unexpected URI scheme {u.scheme}")
                continue
            links += 1
            dest = (path.parent / unquote(u.path)).resolve() if u.path else path
            if not dest.is_relative_to(ROOT):
                failures.append(f"{label}: cross-scope relative link {url}")
                continue
            if dest.is_dir(): dest /= "index.html"
            if not dest.exists():
                failures.append(f"{label}: missing target {url}")
            elif u.fragment and dest.suffix == ".html":
                target = pages.get(dest) or Page(dest.read_text())
                if unquote(u.fragment) not in target.ids: failures.append(f"{label}: missing anchor {url}")
    audit = json.loads((ROOT / "results/entry-audit.json").read_text())
    for r in audit["rows"]:
        if any(r["values"][key] is not None for key in r["unverified_fields"]):
            failures.append(f"Audit row {r['dataset']}:{r['row']}: unverified value not null")
    board = json.loads((ROOT / "results/leaderboard.json").read_text())
    if "registered_trials" in board: failures.append("Catalog count mislabeled registered trials")
    for r in board["standings"]:
        if not r["eligible"] and (r["rank"] is not None or r["reward_points"] is not None):
            failures.append("Unqualified strategy assigned rank/reward")
        if not r["metrics"]["tickets"] and any(r["metrics"][k] is not None for k in ("roi", "simultaneous_ci_low", "simultaneous_ci_high", "p_value", "holm_adjusted_p")):
            failures.append("Empty leaderboard has fabricated performance")
    props = json.loads((ROOT / "data/props-unverified.json").read_text())
    if any(p["line"] is not None or p["odds"] is not None for p in props):
        failures.append("Ambiguous prop quote promoted")
    report = {"status":"PASS" if not failures else "FAIL", "pages":len(paths),
              "local_references_checked":links, "data_rows_with_primary_reference":rows,
              "unique_external_urls_listed":len(external), "external_http_rechecked_by_this_script":False,
              "scope":"Local HTML/assets/anchors, table structure, primary-reference presence and null/rank safeguards only. External publisher status and factual authenticity are not inferred from links.",
              "failures":failures}
    (ROOT / "results/site-check.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return not failures


if __name__ == "__main__":
    raise SystemExit(0 if check() else 1)
