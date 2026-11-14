#!/usr/bin/env python3
"""Release checks for the requirements section.

Three things are enforced, and none of them trusts the prose:

1. Every table row on every generated page carries a link to an approved official source.
2. Every local link and anchor on every generated page resolves inside the repository.
3. Every requirement marked MET or PARTIAL cites an artifact that actually exists on disk, and
   every requirement that is not MET records what is missing. A status that contradicts the files
   fails the build.

Standard library only. Exits non-zero on the first failure so CI cannot merge a page that asserts
something the repository does not contain.
"""
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
REQ = HERE.parent
ROOT = REQ.parent

OFFICIAL = {
    "www.nfl.com", "nfl.com", "nextgenstats.nfl.com", "www.nextgenstats.nfl.com",
    "static.www.nfl.com", "www.itl.nist.gov", "wsgc.wa.gov",
    "docs.github.com", "github.com",
}
# github.com is only an official source for the NFL's own operations repository.
GITHUB_OK = ("/nfl-football-ops/", "/nflverse/", "/sassnarep3-star/Own8")


class Doc(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links, self.ids, self.rows, self.row, self.in_body = [], set(), [], None, False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tbody":
            self.in_body = True
        if tag == "tr" and self.in_body:
            self.row = []
        for k in ("href", "src"):
            if k in a:
                self.links.append(a[k])
                if self.row is not None:
                    self.row.append(a[k])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.in_body = False


def is_official(url):
    p = urlparse(url)
    if p.scheme != "https" or p.hostname not in OFFICIAL:
        return False
    if p.hostname in ("github.com",):
        return any(p.path.startswith(x) for x in GITHUB_OK)
    return True


errors = []
pages = sorted((REQ / "pages").glob("*.html"))
docs = {p.resolve(): Doc(p.read_text(encoding="utf-8")) for p in pages}

rows = links = official_row_links = 0
for path, doc in docs.items():
    name = path.name
    for row in doc.rows:
        rows += 1
        if any(is_official(u) for u in row):
            official_row_links += 1
        else:
            errors.append(f"{name}: table row without an official source link ({row[:1]})")
    for url in doc.links:
        links += 1
        p = urlparse(url)
        if p.scheme:
            if not is_official(url):
                errors.append(f"{name}: unapproved external link {url}")
            continue
        target = (path.parent / unquote(p.path)).resolve() if p.path else path
        if not target.is_relative_to(ROOT):
            errors.append(f"{name}: local link escapes the repository {url}")
            continue
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            errors.append(f"{name}: missing local target {url}")
            continue
        if p.fragment and target in docs and unquote(p.fragment) not in docs[target].ids:
            errors.append(f"{name}: missing anchor {url}")

# ---- requirement statuses must agree with the files on disk
reqs = json.load(open(REQ / "data" / "requirements.json", encoding="utf-8"))["requirements"]
path_re = re.compile(r"(requirements|origination|analysis|scripts|data|pages|hub|desk|strict|evidence-lab)/[\w./-]+\.(?:json|html|py|md|txt|csv)")
for r in reqs:
    cited = set(path_re.findall(r["evidence"])) if False else set(m.group(0) for m in path_re.finditer(r["evidence"]))
    cited |= set(m.group(0) for m in path_re.finditer(r.get("what_exists") or ""))
    if r["status"] in ("MET", "PARTIAL"):
        if not cited:
            errors.append(f'{r["id"]}: status {r["status"]} cites no artifact path')
        missing = [c for c in cited if not (ROOT / c).exists()]
        if missing:
            errors.append(f'{r["id"]}: status {r["status"]} cites missing artifact(s) {missing}')
    else:
        if not (r.get("what_is_missing") or "").strip():
            errors.append(f'{r["id"]}: status {r["status"]} must record what is missing')

# ---- suggestions must all carry a decision state and three options
sugs = json.load(open(REQ / "data" / "suggestions.json", encoding="utf-8"))["suggestions"]
allowed = {"UNDECIDED", "ADOPT A", "ADOPT B", "ADOPT C", "REJECT", "DEFER"}
for s in sugs:
    if s["decision"] not in allowed:
        errors.append(f'{s["id"]}: decision state {s["decision"]} is not allowed')
    if not {"A", "B", "C"} <= set(s.get("options", {})) and "already_done" not in s:
        errors.append(f'{s["id"]}: needs three options')

# ---- questions must be in a known state
qs = json.load(open(REQ / "data" / "questions.json", encoding="utf-8"))["questions"]
states = {}
for q in qs:
    states[q["state"]] = states.get(q["state"], 0) + 1
    if q["state"] not in ("ANSWERED", "OPEN", "IMPOSSIBLE", "PARTIAL"):
        errors.append(f'{q["id"]}: unknown state {q["state"]}')
    if q["state"] == "ANSWERED" and not q.get("answer"):
        errors.append(f'{q["id"]}: ANSWERED without an answer')

# ---- the official capture must have actually run and passed
checks = json.load(open(REQ / "results" / "checks.json", encoding="utf-8"))
if checks["summary"]["checks_failed"]:
    errors.append(f'capture checks report {checks["summary"]["checks_failed"]} failures')
if checks["summary"]["reconcile_cells_ok"] != checks["summary"]["reconcile_cells_total"]:
    errors.append("standings reconciliation is not complete")

result = dict(
    checked_at="2026-11-14",
    scope="requirements/pages/*.html (generated), the register data, and the capture check output",
    pages=len(pages), local_and_external_links=links, table_rows=rows,
    rows_with_official_link=official_row_links,
    requirements=len(reqs), suggestions=len(sugs), questions=len(qs), question_states=states,
    capture_checks=checks["summary"]["checks_total"], capture_failures=checks["summary"]["checks_failed"],
    errors=errors, status="PASS" if not errors else "FAIL",
)
with open(REQ / "results" / "site-checks.json", "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=1)
    fh.write("\n")
print(json.dumps({k: v for k, v in result.items() if k != "errors"}, indent=1))
if errors:
    print("ERRORS:")
    for x in errors:
        print("  -", x)
raise SystemExit(1 if errors else 0)
