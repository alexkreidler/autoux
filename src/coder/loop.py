"""Driver: stages context, invokes agent, commits result."""
from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from coder.base import CodingAgent, CodingPatch
from coder.prompts import render_iteration_prompt
from usersim.schemas import Feedback


async def run_loop(
    repo_dir: Path,
    feedback_path: Path,
    iteration: int,
    agent: CodingAgent,
) -> CodingPatch:
    feedback = Feedback.model_validate_json(feedback_path.read_text())

    context_dir = repo_dir / ".usersim" / f"iter_{iteration}"
    context_dir.mkdir(parents=True, exist_ok=True)

    # Stage feedback.json
    shutil.copy(feedback_path, context_dir / "feedback.json")

    # Stage screenshots referenced in friction clusters
    screenshots_dir = context_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    for cluster in feedback.top_friction_clusters:
        for src_path in cluster.evidence_screenshots:
            src = Path(src_path)
            if src.exists():
                shutil.copy(src, screenshots_dir / src.name)

    # Build cumulative prior_patches.diff
    prior_diff = await _cumulative_diff(repo_dir)
    (context_dir / "prior_patches.diff").write_text(prior_diff)

    prompt = render_iteration_prompt(feedback, Path(".usersim") / f"iter_{iteration}")
    patch = await agent.patch(repo_dir=repo_dir, prompt=prompt, context_dir=context_dir)

    if patch.success:
        await _git_commit(repo_dir, iteration, patch)

    return patch


async def _cumulative_diff(repo_dir: Path) -> str:
    """Return git log -p for commits tagged auto-ux, or empty string."""
    proc = await asyncio.create_subprocess_exec(
        "git", "log", "-p", "--grep=iter_", "--all",
        cwd=repo_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    return out.decode(errors="replace")


async def _git_commit(repo_dir: Path, iteration: int, patch: CodingPatch) -> None:
    changed = ", ".join(patch.files_changed[:5])
    if len(patch.files_changed) > 5:
        changed += f" (+{len(patch.files_changed) - 5} more)"
    msg = f"iter_{iteration}: auto-ux patch [{changed}]"

    add = await asyncio.create_subprocess_exec(
        "git", "add", "-A",
        cwd=repo_dir,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await add.wait()

    commit = await asyncio.create_subprocess_exec(
        "git", "commit", "-m", msg,
        cwd=repo_dir,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await commit.wait()
