#!/usr/bin/env python3
"""Fail-closed checks for source links, unknowns, and the decision-review site."""
from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urlsplit, unquote

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class AuditHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.table_rows = []
        self._table_depth = 0
        self._current_row = None
        self._current_row_has_data = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag in {"a", "link", "script"}:
            url = attrs.get("href") if tag != "script" else attrs.get("src")
            if url:
                self.links.append(url)
        if tag == "table":
            self._table_depth += 1
        elif tag == "tr" and self._table_depth:
            self._current_row = []
            self._current_row_has_data = False
        elif tag == "td" and self._current_row is not None:
            self._current_row_has_data = True
        elif tag == "a" and self._current_row is not None:
            href = attrs.get("href")
            if href:
                self._current_row.append(href)

    def handle_endtag(self, tag):
        if tag == "tr" and self._current_row is not None:
            if self._current_row_has_data:
                self.table_rows.append(self._current_row)
            self._current_row = None
            self._current_row_has_data = False
        elif tag == "table" and self._table_depth:
            self._table_depth -= 1


def is_official(url, allowlist):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme == "https" and any(host == d or host.endswith("." + d) for d in allowlist)


def check_row_sources(rows, source_ids, context):
    errors = []
    for i, row in enumerate(rows, start=1):
        refs = row.get("source_ids", [])
        missing = sorted(set(refs) - source_ids)
        if missing:
            errors.append(f"{context} row {i}: unknown source IDs {missing}")
        if not refs:
            errors.append(f"{context} row {i}: no official source IDs")
    return errors


def check():
    errors = []
    source_data = read("sources.json")
    sources = {s["id"]: s for s in source_data["sources"]}
    allowlist = set(source_data["official_host_allowlist"])
    source_ids = set(sources)

    # Every registry URL must be HTTPS and on an explicitly approved official host.
    for sid, source in sources.items():
        if not is_official(source["url"], allowlist):
            errors.append(f"Source {sid} is not HTTPS on the official host allowlist: {source['url']}")
        if not source.get("checked_at") or not source.get("scope_limit"):
            errors.append(f"Source {sid} is missing checked_at or a scope limitation")

    questions = read("questions.json")["questions"]
    suggestions = read("suggestions.json")
    availability = read("availability.json")
    flags = read("flags.json")["flags"]
    errors += check_row_sources(questions, source_ids, "questions")
    errors += check_row_sources(suggestions["paths"], source_ids, "decision paths")
    errors += check_row_sources(suggestions["recommendations"], source_ids, "suggestions")
    errors += check_row_sources(availability["offensive_groups"], source_ids, "offensive groups")
    errors += check_row_sources(availability["defensive_groups"], source_ids, "defensive groups")
    errors += check_row_sources(availability["fields"], source_ids, "availability fields")
    errors += check_row_sources(flags, source_ids, "review flags")

    # Missing values must remain null; no named player is assigned a depth tier.
    if availability.get("current_player_values") is not None:
        errors.append("availability.current_player_values must remain null until verified player rows exist")
    for row in availability["fields"]:
        if row.get("current_value") is not None:
            errors.append(f"Availability field {row['field']} has an unverified current value")
    if availability.get("tier_values") != ["Starter", "2nd", "3rd", "4th", "Unknown"]:
        errors.append("Depth tier schema changed; review the no-inference policy and update tests")
    if "UNKNOWN" not in availability.get("tier_note", "").upper():
        errors.append("Depth-tier schema must retain an Unknown state")

    # All generated HTML must exist, its internal assets/links must resolve, and every data row
    # in every HTML table must include at least one official source URL.
    html_files = sorted(ROOT.rglob("*.html"))
    if not html_files:
        errors.append("No generated HTML pages found; run decision-review/build.py first")
    total_rows = 0
    for page in html_files:
        parser = AuditHTMLParser()
        parser.feed(page.read_text(encoding="utf-8"))
        total_rows += len(parser.table_rows)
        for row_number, row_links in enumerate(parser.table_rows, start=1):
            if not any(is_official(href, allowlist) for href in row_links):
                errors.append(f"{page.relative_to(ROOT)} table row {row_number} has no official-source link")
        for link in parser.links:
            split = urlsplit(link)
            if split.scheme in {"https", "http", "mailto", "tel", "data"}:
                if split.scheme == "https" and not split.netloc:
                    errors.append(f"{page.relative_to(ROOT)} has malformed external URL: {link}")
                continue
            if link.startswith("//"):
                continue
            target_text = unquote(split.path)
            if not target_text:
                target = page
            else:
                target = (page.parent / target_text).resolve()
                if target.is_dir():
                    target = target / "index.html"
            try:
                target.relative_to(REPO.resolve())
            except ValueError:
                errors.append(f"{page.relative_to(ROOT)} link escapes repository: {link}")
                continue
            if not target.exists():
                errors.append(f"{page.relative_to(ROOT)} has broken local link: {link}")
                continue
            if split.fragment:
                fragment = unquote(split.fragment)
                target_parser = parser if target == page else None
                if target_parser is None and target.suffix.lower() == ".html":
                    target_parser = AuditHTMLParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                if target_parser is not None and fragment not in target_parser.ids:
                    errors.append(f"{page.relative_to(ROOT)} has missing anchor {link}")

    # Guard the most important review states from accidental promotion.
    must_contain = {
        "index.html": ["RESEARCH-ONLY", "No user decision is recorded"],
        "availability.html": ["NO CURRENT WEEK 11 LINEUP OR REPLACEMENT VALUES VERIFIED", "Starter / 2nd / 3rd / 4th / Unknown"],
        "flagged.html": ["DQ-F01", "Week 11 injury-report retrieval mismatch"],
        "suggestions.html": ["PATH-C", "none is user-approved"],
    }
    for filename, needles in must_contain.items():
        path = ROOT / filename
        if not path.exists():
            errors.append(f"Required page missing: {filename}")
            continue
        content = path.read_text(encoding="utf-8").lower()
        for needle in needles:
            if needle.lower() not in content:
                errors.append(f"{filename} is missing required fail-closed text: {needle}")

    if errors:
        print(f"Decision-review check FAIL: {len(errors)} issue(s)")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"Decision-review check PASS: {len(html_files)} HTML pages, {total_rows} table rows with official-source links, {len(sources)} official source records, local links/anchors resolved, current player/depth values blank.")
    print("External URL liveness is not asserted by this local checker; retrieval scopes and mismatches are documented in data/sources.json.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
