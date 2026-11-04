"""Capture small immutable official NFL files through the permitted GitHub API.
Run only when intentionally refreshing evidence; build.py never uses the network.
"""
import base64
import csv
import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = "nfl-football-ops/Big-Data-Bowl"
COMMIT = "9ad0b4b2ea36697e29e44e2399512cc1ce70358c"
FILES = {"Data/games.csv": "games.csv", "schema.md": "official-schema.md", "README.md": "official-readme.md"}


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


def main():
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    manifest = {"retrieved_at": datetime.now(timezone.utc).isoformat(), "repository": REPO,
                "commit": COMMIT, "authority_basis": "Publisher README identifies this as the NFL Big Data Bowl data homepage; repository metadata homepage links to ops.nfl.com/big-data-bowl. No independent website fetch was possible in this network environment.",
                "scope": "Official publisher's 2017 Weeks 1–6 sample only. Not 2026 data, market odds, or player props.", "files": []}
    for source, target in FILES.items():
        meta = api(f"repos/{REPO}/contents/{source}?ref={COMMIT}")
        blob = api(f"repos/{REPO}/git/blobs/{meta['sha']}")
        raw = base64.b64decode(blob["content"])
        git_hash = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if git_hash != meta["sha"] or len(raw) != meta["size"]:
            raise ValueError("Official API blob hash/size mismatch")
        (evidence / target).write_bytes(raw)
        entry = {"local": target, "path": source, "bytes": len(raw), "git_blob_sha1": git_hash,
                 "sha256": hashlib.sha256(raw).hexdigest(),
                 "source_url": f"https://github.com/{REPO}/blob/{COMMIT}/{source}"}
        if source.endswith(".csv"):
            entry["rows"] = len(list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))))
        manifest["files"].append(entry)
    (evidence / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
