"""App registry — load and validate `configs/apps/registry.jsonl`.

Each line is a Pydantic-validated `App` (see schemas.py). Teammate pushes
adds/edits to this file; the engine treats it as the single source of truth
for "what targets exist."

Convention:
  - One App per line, JSONL.
  - Add new apps at the end. Don't reorder existing ones.
  - `id` is a stable slug used in run-output paths; renaming breaks history.
"""
from __future__ import annotations

import json
from pathlib import Path

from usersim.schemas import App

DEFAULT_REGISTRY = Path("configs/apps/registry.jsonl")


def load_apps(path: Path | None = None) -> list[App]:
    p = path or DEFAULT_REGISTRY
    if not p.exists():
        raise FileNotFoundError(f"app registry not found at {p}")
    apps: list[App] = []
    for i, line in enumerate(p.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            apps.append(App.model_validate(json.loads(line)))
        except Exception as e:
            raise ValueError(f"{p}:{i}: invalid App entry: {e}") from e
    return apps


def filter_apps(apps: list[App], ids: set[str] | None) -> list[App]:
    if not ids:
        return apps
    out = [a for a in apps if a.id in ids]
    missing = ids - {a.id for a in out}
    if missing:
        raise ValueError(f"unknown app ids: {sorted(missing)}. known: {sorted(a.id for a in apps)}")
    return out
