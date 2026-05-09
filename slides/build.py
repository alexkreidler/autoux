"""Build a self-contained `slides/dist/` for drag-and-drop deploy.

Rewrites `../demo/foo` → `demo/foo` in index.html and copies only the
assets the deck actually references. Output is a flat folder you can
drag onto app.netlify.com/drop or any static host.

Usage:
    uv run python slides/build.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
REPO = ROOT.parent
DIST = ROOT / "dist"
DEMO = REPO / "demo"


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    (DIST / "demo").mkdir()

    html = (ROOT / "index.html").read_text()

    # Find every ../demo/<file> reference; copy each, rewrite path to ./demo/<file>.
    refs = sorted(set(re.findall(r"\.\./demo/([^\s\"'<>)]+)", html)))
    for ref in refs:
        src = DEMO / ref
        if not src.exists():
            print(f"  ! missing: {src}")
            continue
        dst = DIST / "demo" / ref
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        size = src.stat().st_size
        print(f"  + demo/{ref}  ({size:,} bytes)")

    rewritten = html.replace("../demo/", "demo/")
    (DIST / "index.html").write_text(rewritten)
    print(f"  + index.html  ({len(rewritten):,} bytes)")

    # Convenience: a `_redirects` file for hosts that 404 on root requests.
    (DIST / "_redirects").write_text("/  /index.html  200\n")

    total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"\n→ {DIST}  ({total / 1_000_000:.1f} MB total, {len(refs)} assets)")
    print(f"\nDrag this folder onto https://app.netlify.com/drop")


if __name__ == "__main__":
    main()
