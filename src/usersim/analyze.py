"""Per-iteration trajectory analytics.

Reads runs/<iter>/ and prints a structured report:
  - terminal-reason mix
  - duration / step / token distributions
  - reasoning coverage (% of steps with any text — surfaces the
    Northstar-emits-no-reasoning blind spot)
  - action-type histogram
  - click-coordinate heatmap (10×10 grid) — concentration vs spread
  - per-persona behavior comparison
  - which friction patterns actually fire on real data

Usage:
    uv run python -m usersim.analyze runs/iter_002
    uv run python -m usersim.analyze runs/iter_002 runs/iter_001  # compare iters
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Make `from usersim...` work when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from usersim.io import read_trajectory  # noqa: E402
from usersim.reduce.patterns import detect_all  # noqa: E402
from usersim.schemas import Trajectory  # noqa: E402

VIEWPORT_W, VIEWPORT_H = 1280, 800
GRID_W, GRID_H = 10, 10


# =============================================================================
# Loading
# =============================================================================

def load_iter(iter_dir: Path) -> list[Trajectory]:
    return [read_trajectory(p) for p in sorted((iter_dir / "trajectories").glob("*.jsonl"))]


# =============================================================================
# Aggregate sections
# =============================================================================

def section_terminal_mix(trajs: list[Trajectory]) -> str:
    counts = Counter(t.terminal_reason for t in trajs)
    n = len(trajs)
    lines = ["## Terminal-reason mix"]
    for reason, c in counts.most_common():
        bar = "█" * int(40 * c / n)
        lines.append(f"  {reason:14s} {c:3d}/{n}  {bar}")
    return "\n".join(lines)


def section_distributions(trajs: list[Trajectory]) -> str:
    durations = [(t.ended_at - t.started_at).total_seconds() for t in trajs]
    step_counts = [len(t.steps) for t in trajs]
    prompt_tokens = [sum(s.tokens.prompt_tokens for s in t.steps) for t in trajs]
    completion_tokens = [sum(s.tokens.completion_tokens for s in t.steps) for t in trajs]
    model_ms = [sum(s.timing.model_ms for s in t.steps) for t in trajs]

    def stats(xs: list[float]) -> str:
        if not xs:
            return "(empty)"
        return f"min={min(xs):.1f}  med={statistics.median(xs):.1f}  max={max(xs):.1f}  Σ={sum(xs):.0f}"

    lines = [
        "## Distributions",
        f"  duration (s)    : {stats(durations)}",
        f"  steps           : {stats([float(x) for x in step_counts])}",
        f"  prompt tokens   : {stats([float(x) for x in prompt_tokens])}",
        f"  completion toks : {stats([float(x) for x in completion_tokens])}",
        f"  model wall (ms) : {stats([float(x) for x in model_ms])}",
        f"  Σ prompt tokens across iter : {sum(prompt_tokens):,}",
        f"  Σ completion tokens         : {sum(completion_tokens):,}",
    ]
    return "\n".join(lines)


def section_reasoning_coverage(trajs: list[Trajectory]) -> str:
    """How often does the agent emit ANY reasoning text? Surfaces the
    Northstar-fast blind spot — text-keyed pattern detectors fail without it."""
    total_steps = sum(len(t.steps) for t in trajs)
    with_reason = sum(1 for t in trajs for s in t.steps if s.reasoning)
    chars = sum(sum(len(r) for r in s.reasoning) for t in trajs for s in t.steps)
    lines = [
        "## Reasoning coverage",
        f"  steps with reasoning text : {with_reason}/{total_steps} "
        f"({(with_reason/total_steps*100 if total_steps else 0):.1f}%)",
        f"  total reasoning chars      : {chars:,}",
    ]
    if total_steps and with_reason / total_steps < 0.3:
        lines.append(
            f"  ⚠️  WARNING: low reasoning coverage. Text-regex pattern detectors\n"
            f"     (form_clears, patience_exhausted, navigation_confusion) cannot\n"
            f"     fire reliably on this data. Either prompt the agent for narration\n"
            f"     or rely on geometric pattern detectors only."
        )
    return "\n".join(lines)


def section_action_histogram(trajs: list[Trajectory]) -> str:
    actions = Counter(s.action.type for t in trajs for s in t.steps)
    n = sum(actions.values())
    lines = ["## Action types"]
    for action, c in actions.most_common():
        bar = "█" * int(40 * c / n) if n else ""
        lines.append(f"  {action:14s} {c:3d}/{n}  ({c/n*100:.0f}%) {bar}")
    return "\n".join(lines)


def section_click_heatmap(trajs: list[Trajectory]) -> str:
    coords: list[tuple[int, int]] = []
    for t in trajs:
        for s in t.steps:
            if s.action.type != "click":
                continue
            x = s.action.args.get("x")
            y = s.action.args.get("y")
            if isinstance(x, int) and isinstance(y, int):
                coords.append((x, y))

    if not coords:
        return "## Click heatmap\n  (no click actions)"

    grid = [[0] * GRID_W for _ in range(GRID_H)]
    for x, y in coords:
        gx = min(GRID_W - 1, x * GRID_W // VIEWPORT_W)
        gy = min(GRID_H - 1, y * GRID_H // VIEWPORT_H)
        grid[gy][gx] += 1

    peak = max(max(row) for row in grid) or 1
    chars = " ·▁▂▃▄▅▆▇█"
    lines = [
        f"## Click heatmap  ({len(coords)} clicks across "
        f"{VIEWPORT_W}×{VIEWPORT_H} viewport, bucketed into {GRID_W}×{GRID_H})",
    ]
    for row in grid:
        line = "  " + "".join(chars[min(len(chars) - 1, int(v / peak * (len(chars) - 1)))] for v in row)
        lines.append(line)
    # Top hotspots
    flat = sorted(
        ((grid[gy][gx], gx, gy) for gy in range(GRID_H) for gx in range(GRID_W) if grid[gy][gx] > 0),
        reverse=True,
    )[:5]
    lines.append("  hotspots (cell → approx px):")
    for c, gx, gy in flat:
        px = (gx + 0.5) * VIEWPORT_W // GRID_W
        py = (gy + 0.5) * VIEWPORT_H // GRID_H
        lines.append(f"    cell ({gx}, {gy}) ≈ ({int(px)}, {int(py)}) — {c} clicks")
    return "\n".join(lines)


def section_per_persona(trajs: list[Trajectory]) -> str:
    by_persona: dict[str, list[Trajectory]] = defaultdict(list)
    for t in trajs:
        by_persona[t.persona_id].append(t)

    lines = ["## Per-persona breakdown"]
    lines.append(f"  {'persona':<32}  {'n':>2}  {'steps':>6}  {'reason':<14}  {'tokens':>8}")
    for pid, ts in sorted(by_persona.items()):
        avg_steps = statistics.mean(len(t.steps) for t in ts)
        reasons = Counter(t.terminal_reason for t in ts).most_common(1)[0][0]
        tokens = sum(s.tokens.prompt_tokens for t in ts for s in t.steps)
        lines.append(
            f"  {pid:<32}  {len(ts):>2}  {avg_steps:>6.1f}  {reasons:<14}  {tokens:>8,}"
        )
    return "\n".join(lines)


def section_pattern_firing(trajs: list[Trajectory]) -> str:
    """Which friction patterns actually trigger on real data?"""
    fires: Counter = Counter()
    matched_trajs: set[tuple[str, str]] = set()
    for t in trajs:
        for m in detect_all(t):
            fires[m.pattern_id] += 1
            matched_trajs.add((t.persona_id, t.task_id))

    lines = ["## Friction patterns fired"]
    if not fires:
        lines.append("  (none — likely because reasoning coverage is too low)")
    else:
        for pid, c in fires.most_common():
            lines.append(f"  {pid:<28} {c:3d} matches")
    failed = sum(1 for t in trajs if t.terminal_reason not in ("success_dom", "success_url", "agent_done"))
    lines.append(f"  → {len(matched_trajs)}/{failed} failed trajectories matched ≥1 pattern")
    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================

def analyze_one(iter_dir: Path) -> str:
    trajs = load_iter(iter_dir)
    if not trajs:
        return f"# {iter_dir.name}\n  (no trajectories)"

    parts = [f"# {iter_dir.name}  ({len(trajs)} trajectories)"]
    parts.append(section_terminal_mix(trajs))
    parts.append(section_distributions(trajs))
    parts.append(section_reasoning_coverage(trajs))
    parts.append(section_action_histogram(trajs))
    parts.append(section_click_heatmap(trajs))
    parts.append(section_per_persona(trajs))
    parts.append(section_pattern_firing(trajs))
    return "\n\n".join(parts)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python -m usersim.analyze <iter_dir> [<iter_dir> ...]")
    for arg in sys.argv[1:]:
        print(analyze_one(Path(arg)))
        print("\n" + "=" * 78 + "\n")


if __name__ == "__main__":
    main()
