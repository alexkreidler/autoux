"""Streaming trajectory persistence.

Three-tag JSONL format:
  header line: {"kind":"header", ...}
  step lines:  {"kind":"step", ...}
  footer line: {"kind":"footer", ...}
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from usersim.schemas import Step, Trajectory, TerminalReason


# =============================================================================
# Header / Footer models
# =============================================================================

class TrajectoryHeader(BaseModel):
    kind: Literal["header"] = "header"
    persona_id: str
    task_id: str
    target_url: str
    target_commit: str
    started_at: datetime
    viewport: dict[str, int]  # {"w": ..., "h": ...}
    agent_model: str
    browser_session_id: str | None = None
    live_view_url: str | None = None


class TrajectoryFooter(BaseModel):
    kind: Literal["footer"] = "footer"
    ended_at: datetime
    terminal_reason: TerminalReason
    final_url: str
    final_title: str
    error: str | None = None
    replay_path: str | None = None


# =============================================================================
# Writer
# =============================================================================

class TrajectoryWriter:
    """Context manager that streams trajectory lines to a JSONL file."""

    def __init__(self, path: Path, header: TrajectoryHeader) -> None:
        self._path = path
        self._footer_written = False
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("w", encoding="utf-8")
        self._fh.write(header.model_dump_json() + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def write_step(self, step: Step) -> None:
        line = {"kind": "step"} | json.loads(step.model_dump_json())
        self._fh.write(json.dumps(line) + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def finalize(self, footer: TrajectoryFooter) -> None:
        if self._footer_written:
            return
        self._fh.write(footer.model_dump_json() + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._footer_written = True

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()

    def __enter__(self) -> "TrajectoryWriter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._footer_written:
            # Write error footer if none was written
            footer = TrajectoryFooter(
                ended_at=datetime.now(),
                terminal_reason="error",
                final_url="",
                final_title="",
                error=f"{exc_type.__name__}: {exc_val}" if exc_type else "writer exited without footer",
            )
            try:
                self.finalize(footer)
            except Exception:
                pass
        self.close()


# =============================================================================
# Reader
# =============================================================================

def read_trajectory(path: Path) -> Trajectory:
    """Recompose a Trajectory from a JSONL trajectory file.

    Soft-tolerant of partial files: a missing footer becomes a synthetic
    error footer so the reducer can still chew the trajectory (audit O8).
    Crash artifacts and ctrl-C'd runs no longer take out the iteration.
    """
    header_raw: dict[str, Any] | None = None
    steps_raw: list[dict[str, Any]] = []
    footer_raw: dict[str, Any] | None = None

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = obj.get("kind")
        if kind == "header":
            header_raw = obj
        elif kind == "step":
            steps_raw.append(obj)
        elif kind == "footer":
            footer_raw = obj

    if header_raw is None:
        raise ValueError(f"Trajectory has no header: {path}")
    if footer_raw is None:
        last_url = (steps_raw[-1].get("observation", {}).get("page_url")
                    if steps_raw else header_raw.get("target_url", ""))
        footer_raw = {
            "kind": "footer",
            "ended_at": datetime.now().isoformat(),
            "terminal_reason": "error",
            "final_url": last_url or "",
            "final_title": "",
            "error": "trajectory file missing footer (likely crashed mid-run)",
            "replay_path": None,
        }

    steps = [Step(**{k: v for k, v in s.items() if k != "kind"}) for s in steps_raw]

    return Trajectory(
        persona_id=header_raw["persona_id"],
        task_id=header_raw["task_id"],
        target_url=header_raw["target_url"],
        target_commit=header_raw["target_commit"],
        started_at=header_raw["started_at"],
        ended_at=footer_raw["ended_at"],
        steps=steps,
        final_url=footer_raw["final_url"],
        final_title=footer_raw["final_title"],
        terminal_reason=footer_raw["terminal_reason"],
        error=footer_raw.get("error"),
        browser_session_id=header_raw.get("browser_session_id"),
        replay_path=footer_raw.get("replay_path"),
        live_view_url=header_raw.get("live_view_url"),
    )


# =============================================================================
# Manifest writer
# =============================================================================

class ManifestWriter:
    """Appends one line per finalized trajectory to manifest.jsonl."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        persona_id: str,
        task_id: str,
        jsonl_path: str,
        terminal_reason: str,
        ended_at: datetime,
        n_steps: int,
    ) -> None:
        record = {
            "persona_id": persona_id,
            "task_id": task_id,
            "jsonl_path": jsonl_path,
            "terminal_reason": terminal_reason,
            "ended_at": ended_at.isoformat(),
            "n_steps": n_steps,
        }
        with self._path.open("a") as f:
            f.write(json.dumps(record) + "\n")
