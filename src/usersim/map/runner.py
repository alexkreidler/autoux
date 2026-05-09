"""Map step: fan out (persona × task) workers, gather Trajectories."""
from __future__ import annotations

import asyncio
from itertools import product
from pathlib import Path

from usersim.browsers.base import BrowserProvider
from usersim.clients.base import AgentClient
from usersim.io import ManifestWriter
from usersim.map.worker import run_one
from usersim.schemas import Persona, Task, Trajectory


async def _retrying(coro_factory, attempts: int = 2) -> Trajectory | None:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return await coro_factory()
        except Exception as e:
            last = e
            await asyncio.sleep(1.5 * (i + 1))
    print(f"[runner] worker exhausted retries: {last}")
    return None


async def run_iteration(
    *,
    target_url: str,
    target_commit: str,
    personas: list[Persona],
    tasks: list[Task],
    client: AgentClient,
    browser_provider: BrowserProvider,
    out_dir: Path,
    concurrency: int = 10,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    max_turns: int = 20,
    per_turn_timeout_s: float = 60.0,
    step_settle_ms: int = 500,
    record_replay: bool = True,
) -> list[Trajectory]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    results: list[Trajectory] = []
    manifest = ManifestWriter(out_dir / "manifest.jsonl")

    async def _job(p: Persona, t: Task) -> None:
        async with sem:
            print(f"[runner] start {p.id} × {t.id}")
            traj = await _retrying(lambda: run_one(
                p, t, target_url, target_commit,
                client, browser_provider, out_dir,
                viewport_width=viewport_width,
                viewport_height=viewport_height,
                max_turns=max_turns,
                per_turn_timeout_s=per_turn_timeout_s,
                step_settle_ms=step_settle_ms,
                record_replay=record_replay,
            ))
            if traj is not None:
                results.append(traj)
                manifest.append(
                    persona_id=traj.persona_id,
                    task_id=traj.task_id,
                    jsonl_path=str(out_dir / "trajectories" / f"{traj.persona_id}__{traj.task_id}.jsonl"),
                    terminal_reason=traj.terminal_reason,
                    ended_at=traj.ended_at,
                    n_steps=len(traj.steps),
                )
                print(f"[runner] done  {p.id} × {t.id} → {traj.terminal_reason} ({len(traj.steps)} steps)")

    await asyncio.gather(*[_job(p, t) for p, t in product(personas, tasks)])
    return results
