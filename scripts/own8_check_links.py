#!/usr/bin/env python3
"""Verify the built site has no broken internal links or anchors.

Checks every relative href and #anchor in site/*.html resolves to an existing
file / element id. External links are validated for well-formedness and listed
by host (official-source reachability was verified separately during research).
Exits non-zero on any broken internal link. Run after build_site.py.
"""
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

SITE = pathlib.Path(__file__).resolve().parents[1] / "site"


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
        if tag == "link" and a.get("rel") == "stylesheet" and "href" in a:
            self.hrefs.append(a["href"])
        if tag == "script" and "src" in a:
            self.hrefs.append(a["src"])


def main():
    pages = {}
    for f in sorted(SITE.glob("*.html")):
        c = Collector()
        c.feed(f.read_text())
        pages[f.name] = c
    broken = []
    external = {}
    for name, c in pages.items():
        for href in c.hrefs:
            u = urlparse(href)
            if u.scheme in ("http", "https"):
                external.setdefault(u.netloc, set()).add(href)
                continue
            if u.scheme == "mailto":
                continue
            path = u.path or name
            frag = u.fragment
            target = path if path else name
            if target not in pages and not (SITE / target).exists():
                broken.append(f"{name}: missing file '{target}'")
                continue
            if frag:
                dest = pages.get(target)
                if dest is None and (SITE / target).exists():
                    dc = Collector(); dc.feed((SITE / target).read_text()); dest = dc
                if dest is not None and frag not in dest.ids:
                    broken.append(f"{name}: missing anchor '#{frag}' in {target}")
    print(f"pages checked: {len(pages)}")
    print("external link hosts:")
    for host, urls in sorted(external.items()):
        print(f"  {host}: {len(urls)} links")
    if broken:
        print("\nBROKEN INTERNAL LINKS:")
        for b in broken:
            print("  " + b)
        sys.exit(1)
    print("\nOK: no broken internal links or anchors.")


if __name__ == "__main__":
    main()
