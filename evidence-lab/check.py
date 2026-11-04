"""Read-only whole-repo link scan + scoped reproducibility and evidence checks.
Only writes evidence-lab/checks.json and evidence-lab/repo-review.json.
"""
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from publish import PUBLIC, files as public_files, public_bytes, main as publish
from urllib.parse import unquote, urlparse
from analyze import load_evidence

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OFFICIAL_PREFIX = "https://github.com/nfl-football-ops/Big-Data-Bowl/blob/9ad0b4b2ea36697e29e44e2399512cc1ce70358c/"


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.ids = set()
        self.rows = []
        self.row = None
        self.cell = None
        self.row_urls = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])
        if tag == "tr":
            self.row, self.row_urls = [], []
        if tag == "td":
            self.cell = []
        if tag == "a" and self.row is not None and "href" in attrs:
            self.row_urls.append(attrs["href"])

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        if tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append((self.row, self.row_urls))
            self.row = None


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_repository():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO).decode().split("\0")
    inventory = []
    for name in sorted(n for n in tracked if n and not n.startswith(("evidence-lab/", "docs/evidence-lab/"))):
        path = REPO / name
        raw = path.read_bytes()
        try:
            line_count = len(raw.decode().splitlines())
        except UnicodeDecodeError:
            line_count = None
        inventory.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                          "line_count": line_count, "verification": "Inventory only; factual contents not externally re-verified"})
    patterns = [
        ("scripts/analyze.py", "edge = model_spread_home - mkt", "CRITICAL", "Potential reversed sign: model variable is home margin, market input is signed handicap; correct cover margin adds the handicap."),
        ("scripts/analyze.py", 'in ("PASS", "CONDITIONAL")', "CRITICAL", "Conditional status admitted as pass; strict gate policy must reject it."),
        ("scripts/analyze.py", '"realized_pts": 0.0', "HIGH", "Hard-coded zero is not settled performance; ungraded results must remain blank."),
        ("README.md", "Built to remove luck", "HIGH", "Luck cannot be eliminated; skill requires uncertainty-aware prospective validation."),
        ("README.md", "candidates after all gates", "HIGH", "Candidate claim must be reconciled with official-price evidence and literal PASS gates."),
        ("research/executive-summary.md", "graded automatically by re-running", "HIGH", "Claim of automatic settlement needs a real outcome and rules-aware settlement implementation; the legacy script has placeholder realized points."),
        ("research/methodology.md", "user in the Netherlands", "MEDIUM", "Jurisdiction was asserted without evidence reviewed by this session; do not personalize legal guidance from this assumption."),
    ]
    findings = []
    for name, needle, severity, explanation in patterns:
        path = REPO / name
        if not path.exists():
            continue
        revision = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", name], cwd=REPO).decode().strip()
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if needle in line:
                findings.append({"path": name, "line": number, "line_text": line.strip(), "file_sha256": fingerprint(path),
                                 "file_revision": revision, "severity": severity, "finding": explanation,
                                 "status": "NEEDS REVIEW / revision-bound local code or copy finding, not external factual verification",
                                 "code_url": f"https://github.com/sassnarep3-star/Own8/blob/{revision}/{name}#L{number}",
                                 "official_data_context": OFFICIAL_PREFIX + "schema.md"})
    report = {"scope": "Read-only tracked-file inventory and narrow line-oriented risk-pattern scan. Not semantic line-by-line official verification of all existing datasets or prose. Existing owners handle their scopes.",
              "network_limit": "Only official publisher GitHub evidence was fetched. Direct NFL URLs, current odds, news and injuries were not externally checked in this session.",
              "inventory": inventory, "findings": findings}
    (ROOT / "repo-review.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"tracked_files_inventoried_outside_package": len(inventory), "revision_bound_findings": len(findings), "externally_verified_legacy_rows": 0}


def main():
    (ROOT / "checks.json").write_text('{"status": "RUNNING"}\n')
    review = review_repository()
    errors = []
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_*.py")
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    if not tests.wasSuccessful():
        errors.append(stream.getvalue())
    manifest, games = load_evidence()
    # Rebuild twice and require byte-identical results/HTML. Only our scope changes.
    outputs = [ROOT / "results.json", *sorted(ROOT.glob("*.html"))]
    before = {str(p.relative_to(ROOT)): fingerprint(p) for p in outputs}
    subprocess.run([sys.executable, str(ROOT / "analyze.py")], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, stdout=subprocess.DEVNULL)
    after = {str(p.relative_to(ROOT)): fingerprint(p) for p in outputs}
    if before != after:
        errors.append("Non-reproducible analysis or site: run analyze.py/build.py first")
    data = json.loads((ROOT / "results.json").read_text())
    if any(s["eligible"] or s["rank"] is not None or s["reward_points"] is not None or s["roi"] is not None for s in data["strategies"]):
        errors.append("Unsupported strategy eligibility/reward/performance")
    if any(r["official_market_handicap"] is not None or r["expected_return"] is not None or r["cover_probability"] is not None for r in data["models"]):
        errors.append("Unverified market or probability populated")
    publish()
    parsed = {p: Page(p.read_text()) for p in REPO.rglob("*.html") if not any(part in (".git", "node_modules", ".venv") for part in p.parts)}
    internal, external = 0, set()
    for path, page in parsed.items():
        for link in page.links:
            url = urlparse(link)
            if url.scheme or url.netloc:
                if url.scheme in ("http", "https"):
                    external.add(link)
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if target.is_dir():
                target /= "index.html"
            internal += 1
            if not target.is_file():
                errors.append(f"Broken internal target {path.relative_to(REPO)} -> {link}")
            elif url.fragment and target.suffix == ".html":
                other = parsed.get(target)
                if other is None:
                    other = Page(target.read_text())
                if unquote(url.fragment) not in other.ids:
                    errors.append(f"Missing internal anchor {path.relative_to(REPO)} -> {link}")
    official_rows = 0
    for path, page in parsed.items():
        if path.parent not in (ROOT, PUBLIC):
            continue
        for cells, urls in page.rows:
            if not any(url.startswith(OFFICIAL_PREFIX) for url in urls):
                errors.append(f"Missing pinned official context link in {path.name}: {cells[:2]}")
            else:
                official_rows += 1
    evidence = parsed[ROOT / "evidence.html"].rows
    if len(evidence) != len(games):
        errors.append("Evidence table row count mismatch")
    for (cells, urls), game in zip(evidence, games):
        expected = [game["id"], str(game["week"]), game["date"], game["away"], game["home"], str(game["away_score"]), str(game["home_score"])]
        if cells[:7] != expected or game["source_url"] not in urls:
            errors.append(f"Displayed official fact mismatch: {game['id']}")
    review = review_repository()
    report = {"status": "PASS" if not errors else "FAIL", "tests_run": tests.testsRun,
              "test_failures": len(tests.failures), "test_errors": len(tests.errors),
              "official_hash_matched_files": len(manifest["files"]), "official_fact_rows_checked": len(evidence),
              "displayed_direct_fact_cells_checked": len(evidence) * 7,
              "verification_table_rows_with_pinned_official_context": official_rows,
              "eligible_strategies": sum(s["eligible"] for s in data["strategies"]),
              "analysis_and_site_byte_reproducible": before == after,
              "repository_html_pages_checked": len(parsed), "internal_links_checked": internal,
              "external_urls_not_live_checked": len(external),
              "external_scope": "Static URL inspection only; external HTTP status not checked. Official evidence API blobs were actually retrieved by capture.py and their hashes rechecked locally.",
              "repository_review": review, "errors": errors}
    (ROOT / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    publish()
    for path in public_files():
        if (PUBLIC / path.relative_to(ROOT)).read_bytes() != public_bytes(path):
            raise ValueError("Public mirror mismatch")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
