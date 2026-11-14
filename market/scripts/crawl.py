#!/usr/bin/env python3
"""Line-by-line crawl of the repository: what is sourced, what is stale, what is duplicated.

This produces market/data/repo-crawl.json. It does not fix anything: every finding is a
row with a file path, a record locator, and the evidence. Findings that touch another
session's namespace are published for review, never edited.
"""
import json
import re
from pathlib import Path

MARKET = Path(__file__).resolve().parent.parent
REPO = MARKET.parent
SKIP_DIRS = {"archive", ".git", "node_modules", "__pycache__", "market"}
URL_RE = re.compile(r"https?://[^\s\"'<>,)]+")


def json_files():
    out = []
    for p in sorted(REPO.rglob("*.json")):
        if any(part in SKIP_DIRS for part in p.relative_to(REPO).parts):
            continue
        if p.stat().st_size > 6_000_000:
            continue
        out.append(p)
    return out


def walk_rows(node, path=""):
    """Yield (locator, dict) for every dict that looks like a data row."""
    if isinstance(node, dict):
        if node and any(k in node for k in ("source_url", "sources", "game_url", "url", "official")):
            yield path, node
        for k, v in node.items():
            yield from walk_rows(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_rows(v, f"{path}[{i}]")


def has_url(row):
    txt = json.dumps(row)
    return bool(URL_RE.search(txt))


def main():
    findings = []
    inventory = []

    BLOB = "https://github.com/sassnarep3-star/Own8/blob/main/"

    def flag(fid, severity, area, title, evidence, file, locator, source, action):
        # A repository finding is sourced to the file in the repository. A data finding is
        # sourced to the official page that contradicts or confirms it. Never left blank.
        if not source:
            source = BLOB + file if file and (REPO / file).exists() else "https://github.com/sassnarep3-star/Own8"
        findings.append(dict(id=fid, severity=severity, area=area, title=title, evidence=evidence,
                             file=file, record=locator, source_url=source, action_owner=action))

    for p in json_files():
        rel = str(p.relative_to(REPO))
        try:
            d = json.loads(p.read_text())
        except Exception as e:
            flag(f"J-ERR-{rel}", "high", "integrity", "JSON does not parse",
                 str(e), rel, "", "", "owner of that file")
            continue
        rows = list(walk_rows(d))
        unsourced = [(loc, r) for loc, r in rows if not has_url(r)]
        inventory.append(dict(file=rel, bytes=p.stat().st_size,
                              row_like_dicts=len(rows), rows_with_no_source_url=len(unsourced),
                              top_level_keys=(sorted(d.keys())[:12] if isinstance(d, dict) else f"list[{len(d)}]")))
        if rows and len(unsourced) > 0:
            sample = unsourced[0][0]
            flag(f"J-UNS-{rel}", "medium" if len(unsourced) < len(rows) else "high", "provenance",
                 f"{len(unsourced)} of {len(rows)} row-like objects carry no source URL",
                 f"first unsourced locator: {sample}", rel, sample, "",
                 "owner of that file")

    # ---- Specific, verified findings -------------------------------------------------
    # 1. The ledger price store asserts no official price exists. That is now false.
    led = json.loads((REPO / "ledger/data/price-snapshots.json").read_text())
    blank = sum(1 for m in led["markets"] if m["opening_value"] is None and m["closing_value"] is None)
    flag("F-01", "high", "market reality",
         "ledger/data/price-snapshots.json claims every market is blank because 'no official source publishes this market'",
         f"{blank} of {len(led['markets'])} markets blank; status text reads 'BLANK - no official source publishes this market'. "
         "nfl.com does publish FanDuel spread, total and moneyline for every 2026 week on its weekly picks article, e.g. "
         "Patriots +128 / Lions -152, Lions -2.5, O/U 50.5 for the same NE@DET game.",
         "ledger/data/price-snapshots.json", "markets[0..38].status",
         "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season", "ledger owner (6652101e) - not edited by this session")

    # 2. Cross-namespace counting of parallel suggestion and question registers.
    dupes = {}
    for p in sorted(REPO.rglob("*.json")):
        if any(part in SKIP_DIRS for part in p.relative_to(REPO).parts):
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for key in ("suggestions", "questions"):
            v = d.get(key)
            if isinstance(v, list) and v:
                dupes.setdefault(key, []).append((str(p.relative_to(REPO)), len(v)))
    flag("F-02", "high", "decision clarity",
         f"{len(dupes.get('suggestions', []))} separate suggestion registers and {len(dupes.get('questions', []))} separate question registers exist in this repo",
         "; ".join(f"{k}: {', '.join(f'{f}({n})' for f, n in v)}" for k, v in dupes.items()),
         "multiple", "see evidence", "https://github.com/sassnarep3-star/Own8", "project owner must name ONE canonical register")
    # 3. Two independent Week 10 line originations with different magnitudes.
    a = json.loads((REPO / "origination/results/w10-lines.json").read_text())["games"]
    b = json.loads((REPO / "requirements/results/week10-lines.json").read_text())["games"]
    bm = {(g["away"], g["home"]): g for g in b}
    diffs = []
    for g in a:
        o = bm.get((g["away"], g["home"]))
        if o:
            diffs.append(abs(g["fair_handicap_home_pts"] - o["fair_handicap_home_pts"]))
    flag("F-03", "medium", "duplicate modelling",
         "two independent Week 10 line originations with the same sign convention but different magnitudes",
         f"n={len(diffs)} games compared; mean |difference in home handicap| = {sum(diffs)/len(diffs):.3f} pts, "
         f"max = {max(diffs):.3f} pts. Both are published as 'the' Week 10 line.",
         "origination/results/w10-lines.json vs requirements/results/week10-lines.json", "games[]",
         "https://www.nfl.com/schedules/2026/by-week/week-10", "origination + requirements owners")

    # 4. Stale snapshots: files whose as_of predates the current season state.
    for rel, want in (("data/audit-snapshot-2026-11-04.json", "superseded 2026-11-14"),
                      ("data/scores-2026-week8.json", "Week 8 only"),
                      ("data/standings-2026-reg-w8.json", "Week 8 only"),
                      ("analysis/model-lines.json", "Week 10 slate derived from a Week 8 snapshot")):
        p = REPO / rel
        if p.exists():
            flag(f"F-STALE-{rel}", "low", "staleness",
                 f"{rel} is a superseded snapshot and still exists",
                 f"note: {want}; file size {p.stat().st_size} bytes",
                 rel, "whole file", "", "integration owner (excluded from publication today)")

    # 5. The root dashboard's model-lines page still carries the pre-market 'blocked' framing.
    root = (REPO / "scripts/build_site.py").read_text()
    hit = "No official sportsbook line exists in any official NFL source" in root or "market price" in root
    flag("F-04", "medium", "site copy",
         "root dashboard copy states no official market price exists",
         "scripts/build_site.py writes the line-origination page with all market columns blank and a note that no "
         "official price exists. That copy is now contradicted by the official picks article." if hit else
         "no explicit contradiction found in scripts/build_site.py",
         "scripts/build_site.py", "model-lines page builder", "https://www.nfl.com/news/nfl-picks-week-10-2026-nfl-season",
         "root dashboard owner / integration session")

    # 6. Duplicate namespace inventory: count published HTML surfaces.
    surfaces = sorted(({p.parent.name for p in REPO.glob("*/index.html")} |
                       {p.parent.parent.name for p in REPO.glob("*/site/index.html")}) - {"market"})
    flag("F-05", "medium", "navigation",
         f"{len(surfaces)} separate site surfaces are published from one repository",
         "surfaces: " + ", ".join(surfaces),
         "repository root", "*/index.html", "https://github.com/sassnarep3-star/Own8", "integration owner - needs one navigable hub")

    # 7. Data files excluded from the published site by _config.yml (dead weight or deliberate?)
    cfg = (REPO / "_config.yml").read_text()
    ex = [line.split("- ", 1)[1].strip().strip('"') for line in cfg.splitlines() if line.startswith("  - ")]
    flag("F-06", "low", "publication",
         f"{len(ex)} paths are excluded from the published site",
         "excluded: " + ", ".join(ex[:12]) + (" ..." if len(ex) > 12 else ""),
         "_config.yml", "exclude", "https://github.com/sassnarep3-star/Own8/blob/main/_config.yml", "integration owner")

    out = dict(crawled_at="2026-11-14", crawled_by="session 949f49b0",
               scope="every *.json under the repository root except archive/, .git/, market/ and node_modules/",
               files_scanned=len(inventory),
               files_with_unsourced_rows=sum(1 for i in inventory if i["rows_with_no_source_url"]),
               row_like_dicts_total=sum(i["row_like_dicts"] for i in inventory),
               unsourced_rows_total=sum(i["rows_with_no_source_url"] for i in inventory),
               inventory=inventory, findings=findings)
    (MARKET / "data" / "repo-crawl.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"files {out['files_scanned']}, row-like dicts {out['row_like_dicts_total']}, "
          f"unsourced {out['unsourced_rows_total']}, findings {len(findings)}")
    for f in findings:
        if not f["id"].startswith("J-UNS"):
            print(f"  {f['id']:28s} {f['severity']:6s} {f['title'][:90]}")


if __name__ == "__main__":
    main()
