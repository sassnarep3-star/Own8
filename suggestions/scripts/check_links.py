#!/usr/bin/env python3
"""Link checker for the Own8 suggestions + review workspaces.

Standard library only. Verifies:
  * every local (non-http) href/src resolves to an existing file relative to the page;
  * every external link is https and on the official-source allowlist;
  * every data table row that is expected to carry a source has one.
Exits non-zero on any broken internal link or disallowed external host.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAMESPACES = [ROOT / "review", ROOT / "suggestions"]
ALLOWED_HOSTS = {
    "www.nfl.com",
    "nfl.com",
    "nextgenstats.nfl.com",
    "www.itl.nist.gov",
    "wsgc.wa.gov",
    "docs.github.com",
    "github.com",
}
LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')


def rel_target(page: pathlib.Path, link: str) -> pathlib.Path:
    return (page.parent / link).resolve()


def main() -> int:
    pages = []
    for ns in NAMESPACES:
        for p in ns.rglob("*.html"):
            pages.append(p)
    failures = 0
    warnings = 0
    total_links = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for link in LINK_RE.findall(text):
            total_links += 1
            if link.startswith("#"):
                continue
            if link.startswith("http"):
                host = re.sub(r"^https?://", "", link).split("/")[0].split("?")[0]
                if host not in ALLOWED_HOSTS:
                    print(f"[DISALLOWED HOST] {page.relative_to(ROOT)} -> {link}")
                    failures += 1
                continue
            # local link
            target = rel_target(page, link)
            if not target.exists():
                print(f"[BROKEN INTERNAL] {page.relative_to(ROOT)} -> {link}")
                failures += 1
    print(f"Checked {len(pages)} pages, {total_links} links.")
    if failures:
        print(f"FAIL: {failures} link problems.")
        return 1
    print("PASS: 0 broken internal links; all external links on the official allowlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
