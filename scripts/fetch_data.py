#!/usr/bin/env python3
"""Reproducible primary-data acquisition for the Own8 NFL project.

All files are fetched from GitHub (the only data host reachable from the build
sandbox). Release-asset downloads (objects.githubusercontent.com) are NOT
reachable, so every file below is fetched via the GitHub REST contents API
(`Accept: application/vnd.github.raw`), which stays on api.github.com.

Provenance and verification status of each dataset: docs/DATA_PROVENANCE.md
Run:  python3 scripts/fetch_data.py
"""
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

API = "https://api.github.com/repos/{repo}/contents/{path}"

FILES = [
    # (repo, path in repo, local relative path)
    ("LeeSharpe/nfldata", "data/games.csv", "games.csv"),
    ("mrcaseb/nfl-data", "data/nfl_lines_odds.csv.gz", "nfl_lines_odds.csv.gz"),
    ("ryurko/nflscrapR-data", "legacy_data/game_player_stats/game_passing_df.csv", "game_passing_df.csv"),
    ("ryurko/nflscrapR-data", "legacy_data/game_player_stats/game_receiving_df.csv", "game_receiving_df.csv"),
    ("ryurko/nflscrapR-data", "legacy_data/game_player_stats/game_rushing_df.csv", "game_rushing_df.csv"),
    ("nfl-football-ops/Big-Data-Bowl", "Data/games.csv", "bdb_official/games.csv"),
    ("nfl-football-ops/Big-Data-Bowl", "Data/plays.csv", "bdb_official/plays.csv"),
    ("nfl-football-ops/Big-Data-Bowl", "Data/players.csv", "bdb_official/players.csv"),
]
# 2021 weekly fantasy stats (modern-era robustness sample)
for w in range(1, 19):
    FILES.append((
        "fantasydatapros/LearnPythonWithFantasyFootball",
        f"2022/09-Correlation Matrices/01-Weekly Fantasy Stats - 2021/{w}.csv",
        f"fdp2021/{w}.csv",
    ))


def fetch(repo: str, path: str, dest: pathlib.Path) -> dict:
    import urllib.parse
    url = API.format(repo=repo, path=urllib.parse.quote(path))
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.raw",
        "User-Agent": "own8-data-fetch",
    })
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=300) as r:
        blob = r.read()
    dest.write_bytes(blob)
    return {
        "local": str(dest.relative_to(ROOT)),
        "repo": repo,
        "path": path,
        "api_url": url,
        "html_url": f"https://github.com/{repo}/blob/HEAD/{urllib.parse.quote(path)}",
        "bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def main() -> None:
    manifest = []
    for repo, path, local in FILES:
        dest = RAW / local
        info = fetch(repo, path, dest)
        manifest.append(info)
        print(f"fetched {local}: {info['bytes']} bytes")
    out = RAW / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"manifest written: {out}")


if __name__ == "__main__":
    main()
