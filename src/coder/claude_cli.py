"""ClaudeCliAgent — drives `claude -p` as a subprocess."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from coder.base import CodingPatch


class ClaudeCliAgent:
    name = "claude-cli"

    async def patch(
        self,
        *,
        repo_dir: Path,
        prompt: str,
        context_dir: Path | None = None,
        timeout_s: float = 300,
    ) -> CodingPatch:
        started = time.monotonic()
        cmd = [
            "claude", "-p", prompt,
            "--output-format=stream-json",
            "--dangerously-skip-permissions",
            "--allowedTools", "Edit,Write,Read,Glob,Grep",
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=repo_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            try:
                raw_out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return CodingPatch(
                    files_changed=[],
                    diff="",
                    transcript="",
                    duration_ms=int((time.monotonic() - started) * 1000),
                    success=False,
                    error="timeout",
                )

            transcript = raw_out.decode(errors="replace")
            duration_ms = int((time.monotonic() - started) * 1000)
            cost_usd = _parse_cost(transcript)

            if proc.returncode != 0:
                return CodingPatch(
                    files_changed=[],
                    diff="",
                    transcript=transcript,
                    duration_ms=duration_ms,
                    cost_usd=cost_usd,
                    success=False,
                    error=f"exit code {proc.returncode}",
                )

            diff, files_changed = await _git_diff(repo_dir)
            return CodingPatch(
                files_changed=files_changed,
                diff=diff,
                transcript=transcript,
                duration_ms=duration_ms,
                cost_usd=cost_usd,
                success=bool(diff.strip()),
            )

        except Exception as exc:
            return CodingPatch(
                files_changed=[],
                diff="",
                transcript="",
                duration_ms=int((time.monotonic() - started) * 1000),
                success=False,
                error=str(exc),
            )


async def _git_diff(repo_dir: Path) -> tuple[str, list[str]]:
    async def _run(args: list[str]) -> str:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        return out.decode(errors="replace")

    diff = await _run(["diff", "HEAD"])
    names_raw = await _run(["diff", "HEAD", "--name-only"])
    files = [f for f in names_raw.splitlines() if f.strip()]
    return diff, files


def _parse_cost(transcript: str) -> float:
    """Best-effort: pull cost_usd from the last stream-json line that has it."""
    cost = 0.0
    for line in transcript.splitlines():
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and "cost_usd" in obj:
                cost = float(obj["cost_usd"])
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return cost
