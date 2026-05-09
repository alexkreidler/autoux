"""File-backed registry of active rollouts. Atomic via os.replace.

Default location is `runs/active.json` resolved from the current working
directory at *call time*, not import time, so the registry follows whichever
out-dir the run is using. Override with `USERSIM_REGISTRY_FILE` env var.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock

from usersim.schemas import ActiveRollout

_LOCK = Lock()


def _active_file() -> Path:
    override = os.environ.get("USERSIM_REGISTRY_FILE")
    return Path(override) if override else Path.cwd() / "runs" / "active.json"


def _read() -> list[dict]:
    p = _active_file()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _write(rows: list[dict]) -> None:
    p = _active_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".active.", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(rows, f, indent=2, default=str)
    os.replace(tmp, p)


def add(rollout: ActiveRollout) -> None:
    with _LOCK:
        rows = _read()
        rows = [r for r in rows if r.get("browser_session_id") != rollout.browser_session_id]
        rows.append(json.loads(rollout.model_dump_json()))
        _write(rows)


def update(session_id: str, **patch) -> None:
    with _LOCK:
        rows = _read()
        for row in rows:
            if row.get("browser_session_id") == session_id:
                row.update(patch)
        _write(rows)


def remove(session_id: str) -> None:
    with _LOCK:
        rows = [r for r in _read() if r.get("browser_session_id") != session_id]
        _write(rows)


def list_active() -> list[ActiveRollout]:
    return [ActiveRollout(**r) for r in _read()]
