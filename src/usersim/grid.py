"""Compose recorded session videos into an N-up grid via ffmpeg.

Reads a single iteration directory's manifest.jsonl and stacks all replays
listed there into a single grid.mp4. Layout auto-sized: cols = ceil(sqrt(N)).

Usage:
    python -m usersim.grid runs/iter_001                    # all replays
    python -m usersim.grid runs/iter_001 4                  # last 4
    python -m usersim.grid runs/iter_001 4 path/to/out.mp4  # custom output
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

CELL_W, CELL_H = 640, 400


def load_videos(iter_dir: Path, limit: int | None) -> list[Path]:
    """Returns mp4 paths. Handles both shapes:
      - Single iter dir: `<dir>/manifest.jsonl` + `<dir>/replays/*.mp4`
      - Sweep root: `<dir>/<app>/replays/*.mp4` per app, no top-level manifest
    """
    manifest = iter_dir / "manifest.jsonl"
    paths: list[Path] = []
    if manifest.exists():
        rows = [json.loads(l) for l in manifest.read_text().splitlines() if l.strip()]
        for r in rows:
            replay = iter_dir / "replays" / f"{r['persona_id']}__{r['task_id']}.mp4"
            if replay.exists():
                paths.append(replay)
    else:
        # Sweep root — walk per-app subdirs, sorted by app name for stable layout.
        paths = sorted(iter_dir.glob("*/replays/*.mp4"))
    if limit:
        paths = paths[-limit:]
    if not paths:
        sys.exit(f"no replay mp4s under {iter_dir}")
    return paths


def grid_layout(n: int) -> tuple[int, int]:
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows


def build_filter(n: int, cols: int, rows: int) -> str:
    scale_chains = [
        f"[{i}:v]scale={CELL_W}:{CELL_H}:force_original_aspect_ratio=decrease,"
        f"pad={CELL_W}:{CELL_H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[v{i}]"
        for i in range(n)
    ]
    total = cols * rows
    filler_chains = [
        f"[{n + i}:v]scale={CELL_W}:{CELL_H},setsar=1[v{n + i}]"
        for i in range(total - n)
    ]
    layout = "|".join(
        f"{c * CELL_W}_{r * CELL_H}" for r in range(rows) for c in range(cols)
    )
    inputs_concat = "".join(f"[v{i}]" for i in range(total))
    xstack = f"{inputs_concat}xstack=inputs={total}:layout={layout}:fill=black[out]"
    return ";".join([*scale_chains, *filler_chains, xstack])


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python -m usersim.grid <iter_dir> [N] [out.mp4]")
    iter_dir = Path(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else iter_dir / "grid.mp4"

    videos = load_videos(iter_dir, limit)
    n = len(videos)
    cols, rows = grid_layout(n)
    print(f"composing {n} videos → {cols}x{rows} grid → {out}")

    cmd = ["ffmpeg", "-y"]
    for v in videos:
        cmd += ["-i", str(v)]
    fillers = cols * rows - n
    for _ in range(fillers):
        cmd += ["-f", "lavfi", "-i", f"color=black:size={CELL_W}x{CELL_H}:rate=30"]

    cmd += [
        "-filter_complex", build_filter(n, cols, rows),
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print(f"done → {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
