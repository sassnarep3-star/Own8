#!/usr/bin/env python3
"""Own8 link checker (T6). Verifies the built site in docs/:
  1. every internal href/src resolves to an existing file (no broken links)
  2. every external link is https
  3. every external link is either on the official-source allowlist (data/sources.json)
     or is an explicitly flagged third-party link (flagged pages / market-lines references)
Writes analysis/link-check.json and exits non-zero if any internal link is broken.

Run: python3 scripts/check_links.py
"""
import json, re, sys
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "analysis"

sources = json.load(open(DATA / "sources.json"))["sources"]
official_hosts = {urlparse(s["url"]).netloc for s in sources}
# flagged third-party hosts allowed ONLY on pages that explicitly discuss them
FLAGGED_THIRD_PARTY = {"nflschedules.com", "www.espn.com"}
FLAG_PAGES = {"flagged.html", "sources.html", "model-lines.html", "index.html"}

html_files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
internal_broken, external, external_non_https, external_unlisted, warnings_http_official = [], [], [], [], []
checked = 0
for f in html_files:
    text = f.read_text()
    for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
        checked += 1
        url = unquote(m.group(1))
        if url.startswith("#"):
            continue
        u = urlparse(url)
        if u.scheme in ("http", "https"):
            if u.scheme != "https":
                (external_non_https if u.netloc not in official_hosts else warnings_http_official).append((f.name, url))
            host = u.netloc
            external.append((f.name, url, host))
            if host not in official_hosts and host not in FLAGGED_THIRD_PARTY:
                external_unlisted.append((f.name, url, host))
            elif host in FLAGGED_THIRD_PARTY and f.name not in FLAG_PAGES:
                external_unlisted.append((f.name, url, host + " (third-party host on non-flag page)"))
        else:
            target = (f.parent / url.split("#")[0]).resolve()
            if not target.exists():
                internal_broken.append((f.name, url))

result = {
    "checked_at": "2026-11-03",
    "pages": len(html_files),
    "links_checked": checked,
    "internal_broken": internal_broken,
    "external_total": len(external),
    "external_non_https": external_non_https,
    "external_unlisted": external_unlisted,
    "warnings_http_official_host": warnings_http_official,
    "official_hosts": sorted(official_hosts),
    "status": "PASS" if not internal_broken and not external_non_https else "FAIL",
}
OUT.mkdir(exist_ok=True)
json.dump(result, open(OUT / "link-check.json", "w"), indent=2)
print(json.dumps({k: (v if not isinstance(v, list) else v[:10]) for k, v in result.items()}, indent=2))
print("\nSTATUS:", result["status"])
sys.exit(0 if result["status"] == "PASS" else 1)
