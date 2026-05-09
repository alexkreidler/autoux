from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class CodingPatch(BaseModel):
    files_changed: list[str]
    diff: str               # unified diff (output of `git diff HEAD`)
    transcript: str         # raw agent stdout / log
    duration_ms: int
    cost_usd: float = 0.0
    success: bool           # exited cleanly AND non-empty diff
    error: str | None = None


class CodingAgent(Protocol):
    name: str

    async def patch(
        self,
        *,
        repo_dir: Path,
        prompt: str,
        context_dir: Path | None = None,
        timeout_s: float = 300,
    ) -> CodingPatch:
        ...
