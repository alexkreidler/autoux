"""Compose recorded session videos into an N-up grid via ffmpeg.

For N ≤ TIER_THRESHOLD (default 64) does a single-pass encode. For larger
N we tile: split inputs into chunks, encode each chunk's sub-grid in
parallel, then composite the sub-grids into the final meta-grid. Keeps
each ffmpeg run below the videotoolbox slow-path resolution wall and
parallelizes across cores.

Reads either:
  - A single iteration dir (`<dir>/manifest.jsonl` + `<dir>/replays/*.mp4`)
  - A sweep root (`<dir>/<app>/replays/*.mp4` per app)

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
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CELL_W, CELL_H = 480, 300

# Past this many cells, single-pass encode hits videotoolbox's slow path
# (output canvas exceeds the encoder's fast-buffer threshold). Tier into
# sub-grids instead.
TIER_THRESHOLD = 64

# Sub-grid chunk size at tier 1. 16 keeps each sub-encode at 4×4=1920×1200
# which is well within the hardware-encoder fast path.
TIER_CHUNK = 16


# =============================================================================
# Probing + encoder selection
# =============================================================================

def _max_duration(videos: list[Path]) -> float:
    """Probe each input and return the longest duration in seconds. Used to
    bound the output explicitly — `-shortest` doesn't reliably truncate when
    paired with infinite lavfi filler streams + hardware encoders."""
    best = 0.0
    for v in videos:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(v)],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        try:
            best = max(best, float(out))
        except ValueError:
            pass
    return best or 60.0


def _detect_hw_encoder() -> list[str]:
    """Pick the fastest video encoder available. On Apple Silicon, the
    hardware h264 encoder is 10-50x faster than libx264 for grid composition.
    Falls back to libx264 if videotoolbox is unavailable."""
    try:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, check=False,
        ).stdout
    except FileNotFoundError:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", "23"]
    if "h264_videotoolbox" in out:
        return [
            "-c:v", "h264_videotoolbox",
            "-b:v", "6M",
            "-allow_sw", "1",
            "-tag:v", "avc1",
        ]
    return ["-c:v", "libx264", "-preset", "fast", "-crf", "23"]


# =============================================================================
# Loading
# =============================================================================

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
        paths = sorted(iter_dir.glob("*/replays/*.mp4"))
    if limit:
        paths = paths[-limit:]
    if not paths:
        sys.exit(f"no replay mp4s under {iter_dir}")
    return paths


# =============================================================================
# Single-pass grid encoder (tier 0)
# =============================================================================

def grid_layout(n: int) -> tuple[int, int]:
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows


def _build_filter(n: int, cols: int, rows: int, cell_w: int, cell_h: int) -> str:
    scale_chains = [
        f"[{i}:v]scale={cell_w}:{cell_h}:force_original_aspect_ratio=decrease,"
        f"pad={cell_w}:{cell_h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[v{i}]"
        for i in range(n)
    ]
    total = cols * rows
    filler_chains = [
        f"[{n + i}:v]scale={cell_w}:{cell_h},setsar=1[v{n + i}]"
        for i in range(total - n)
    ]
    layout = "|".join(
        f"{c * cell_w}_{r * cell_h}" for r in range(rows) for c in range(cols)
    )
    inputs_concat = "".join(f"[v{i}]" for i in range(total))
    xstack = f"{inputs_concat}xstack=inputs={total}:layout={layout}:fill=black[out]"
    return ";".join([*scale_chains, *filler_chains, xstack])


def compose_grid(
    videos: list[Path],
    out: Path,
    cell_w: int = CELL_W,
    cell_h: int = CELL_H,
) -> Path:
    """Single-pass grid encode. Returns the output path on success."""
    n = len(videos)
    cols, rows = grid_layout(n)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for v in videos:
        cmd += ["-i", str(v)]
    fillers = cols * rows - n
    for _ in range(fillers):
        cmd += ["-f", "lavfi", "-i", f"color=black:size={cell_w}x{cell_h}:rate=30"]

    duration = _max_duration(videos)
    cmd += [
        "-filter_complex", _build_filter(n, cols, rows, cell_w, cell_h),
        "-map", "[out]",
        *_detect_hw_encoder(),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-movflags", "+faststart",
        "-t", f"{duration:.3f}",
        str(out),
    ]
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, KeyboardInterrupt):
        # Don't leave a partial mp4 — re-runs see "exists, skip" otherwise,
        # and partial files fail QuickTime with `moov atom not found`.
        if out.exists():
            out.unlink()
        raise
    return out


# =============================================================================
# Tiered grid (tier 1: parallel sub-grids → tier 2: meta composite)
# =============================================================================

def compose_tiered_grid(
    videos: list[Path],
    out: Path,
    cell_w: int = CELL_W,
    cell_h: int = CELL_H,
    chunk: int = TIER_CHUNK,
    parallel: int = 8,
) -> Path:
    """Two-tier encode for large N.

    1. Split inputs into chunks of `chunk` (default 16 → 4×4 sub-grids).
    2. Encode each sub-grid in parallel (default up to 4 concurrent ffmpeg).
    3. Composite the sub-grid mp4s into the final meta-grid.

    Sub-grid cells stay at (cell_w, cell_h); the meta-grid cell size is the
    sub-grid output resolution, so each original input ends up displayed at
    sub-cell-size / sub-grid-cols. With defaults, that's 480/4=120px wide.
    """
    n = len(videos)
    chunks: list[list[Path]] = [videos[i:i + chunk] for i in range(0, n, chunk)]
    print(f"  tier1: {len(chunks)} sub-grids of up to {chunk}, parallel={parallel}")

    with tempfile.TemporaryDirectory(prefix="grid_tier_") as tmp:
        tmp_root = Path(tmp)
        sub_paths = [tmp_root / f"sub_{i:03d}.mp4" for i in range(len(chunks))]

        def _encode(args):
            chunk_videos, sub_path = args
            return compose_grid(chunk_videos, sub_path, cell_w, cell_h)

        with ThreadPoolExecutor(max_workers=parallel) as ex:
            list(ex.map(_encode, [(c, sub_paths[i]) for i, c in enumerate(chunks)]))

        # Meta-cell must be SCALED DOWN from the sub-grid output, otherwise the
        # meta-canvas explodes past the fast-path threshold. Halving keeps both
        # tiers within the videotoolbox fast lane (and yields a final
        # per-rollout pixel size of ~240x150 which is fine for postage-stamp
        # grids — at this N you can't see fine detail anyway).
        sub_cols, sub_rows = grid_layout(chunk)
        meta_cell_w = (sub_cols * cell_w) // 2
        meta_cell_h = (sub_rows * cell_h) // 2
        meta_cols, meta_rows = grid_layout(len(chunks))
        canvas_mpx = (meta_cols * meta_cell_w * meta_rows * meta_cell_h) / 1_000_000
        print(f"  tier2: {len(chunks)} sub-grids → meta-grid "
              f"({meta_cell_w}x{meta_cell_h} cells, {meta_cols}x{meta_rows}, "
              f"{canvas_mpx:.1f} Mpx canvas)")
        compose_grid(sub_paths, out, meta_cell_w, meta_cell_h)
    return out


# =============================================================================
# Entrypoint
# =============================================================================

def compose_for_dir(
    iter_dir: Path,
    out: Path | None = None,
    limit: int | None = None,
) -> Path | None:
    """Auto-dispatch single-pass vs tiered based on N. Library entrypoint —
    callers (e.g. CLI hooks at sweep/run completion) use this. Returns the
    output path, or None if there were no replays to compose."""
    out = out or (iter_dir / "grid.mp4")
    try:
        videos = load_videos(iter_dir, limit)
    except SystemExit:
        return None
    n = len(videos)
    cols, rows = grid_layout(n)
    if n <= TIER_THRESHOLD:
        print(f"composing {n} videos → {cols}x{rows} single-pass grid → {out}")
        compose_grid(videos, out)
    else:
        print(f"composing {n} videos → {cols}x{rows} tiered grid → {out}")
        compose_tiered_grid(videos, out)
    print(f"done → {out} ({out.stat().st_size:,} bytes)")
    return out


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python -m usersim.grid <iter_dir> [N] [out.mp4]")
    iter_dir = Path(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    compose_for_dir(iter_dir, out=out, limit=limit)


if __name__ == "__main__":
    main()
