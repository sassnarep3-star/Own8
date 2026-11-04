"""Mirror this isolated package into the already-staged docs/ subtree.
Does not edit shared navigation, existing docs/*.html or deployment workflows.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT.parent / "docs/evidence-lab"
SUFFIXES = {".py", ".md", ".json", ".html", ".css", ".js", ".csv"}


def public_bytes(path):
    raw = path.read_bytes()
    if path.parent == ROOT and path.suffix in (".html", ".md"):
        text = raw.decode()
        text = text.replace('href="../COORDINATION.md"', 'href="https://github.com/sassnarep3-star/Own8/blob/main/COORDINATION.md"')
        text = text.replace('](../COORDINATION.md)', '](https://github.com/sassnarep3-star/Own8/blob/main/COORDINATION.md)')
        text = text.replace('href="../', 'href="../../').replace('](../', '](../../')
        raw = text.encode()
    return raw


def files():
    return [p for p in sorted(ROOT.rglob("*")) if p.is_file() and p.suffix in SUFFIXES and "__pycache__" not in p.parts]


def main():
    for path in files():
        target = PUBLIC / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(public_bytes(path))
    print(f"Published {len(files())} scoped files to docs/evidence-lab/")


if __name__ == "__main__":
    main()
