"""Live trajectory grid — FastAPI + SSE.

Routes:
  - GET  /                          → bundled HTML dashboard
  - GET  /api/sessions              → active rollouts
  - GET  /api/personas              → all configured personas
  - GET  /api/avatar/{id}.png       → portrait PNG
  - GET  /api/feedback              → latest iteration feedback
  - GET  /api/configs               → available run YAML configs
  - GET  /api/agents                → registered agent providers
  - POST /api/run                   → kick off a usersim run (subprocess)
  - GET  /api/run/{id}              → status of a kicked run
  - GET  /api/runs                  → all kicked runs (current process)
  - GET  /api/stream                → SSE: session updates
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from usersim import registry
from usersim.clients import available as available_agents

ROOT = Path(__file__).parent
INDEX = ROOT / "index.html"

# Resolve project-root relative paths at request time (cwd-relative, like registry).
def _project_root() -> Path:
    return Path.cwd()


def _personas_path() -> Path:
    p = _project_root() / "configs" / "personas" / "expanded.jsonl"
    if p.exists():
        return p
    return _project_root() / "configs" / "personas" / "seed.jsonl"


def _avatars_dir() -> Path:
    return _project_root() / "configs" / "personas" / "avatars"


def _latest_feedback_path() -> Path | None:
    runs = _project_root() / "runs"
    if not runs.exists():
        return None
    candidates = sorted(
        (d for d in runs.iterdir() if d.is_dir() and (d / "feedback.json").exists()),
        key=lambda d: d.stat().st_mtime,
    )
    return candidates[-1] / "feedback.json" if candidates else None


def _configs_dir() -> Path:
    return _project_root() / "configs"


def _load_yaml_config(p: Path) -> dict | None:
    try:
        return yaml.safe_load(p.read_text())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Run launcher (subprocess management)
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    config: str = "configs/taxcaster.yaml"  # YAML path; the source-of-truth for target_url + tasks
    personas: list[str] | None = None        # subset of persona ids; None = all from config
    tasks: list[str] | None = None           # subset of task ids; None = all from config
    concurrency: int = 9
    max_turns: int | None = None
    iteration: int = 0
    agent: str | None = None                 # provider override; None = config/default
    agent_endpoint: str | None = None
    label: str | None = None                 # optional human label, becomes part of out_dir
    stuck_threshold: int | None = None       # 0 disables stuck-loop terminator
    patience: int | None = None              # 0 disables abandonment cutoff


class RunInfo(BaseModel):
    id: str
    status: str = "pending"  # pending → running → done | failed
    started_at: float = Field(default_factory=time.time)
    ended_at: float | None = None
    out_dir: str
    config: str
    cmd: list[str]
    pid: int | None = None
    returncode: int | None = None
    log_path: str
    iteration: int


_RUNS: dict[str, RunInfo] = {}
_RUNS_LOCK = threading.Lock()


def _next_iter_dir(label: str | None) -> tuple[Path, int]:
    runs_root = _project_root() / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    existing = [d.name for d in runs_root.iterdir() if d.is_dir()]
    n = 0
    while f"iter_{n:03d}" in existing:
        n += 1
    name = f"iter_{n:03d}" + (f"_{label}" if label else "")
    return runs_root / name, n


def _spawn_run(req: RunRequest) -> RunInfo:
    out_dir, iter_n = _next_iter_dir(req.label)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "usersim", "run",
        "--config", req.config,
        "--out", str(out_dir),
        "--concurrency", str(req.concurrency),
        "--iteration", str(req.iteration or iter_n),
    ]
    if req.personas:
        cmd += ["--personas", ",".join(req.personas)]
    if req.tasks:
        cmd += ["--tasks", ",".join(req.tasks)]
    if req.agent:
        cmd += ["--agent", req.agent]
    if req.agent_endpoint:
        cmd += ["--agent-endpoint", req.agent_endpoint]
    if req.max_turns is not None:
        cmd += ["--max-turns", str(req.max_turns)]
    if req.stuck_threshold is not None:
        cmd += ["--stuck-threshold", str(req.stuck_threshold)]
    if req.patience is not None:
        cmd += ["--patience", str(req.patience)]

    env = os.environ.copy()
    log_path = out_dir / "run.log"
    log_f = open(log_path, "wb")

    proc = subprocess.Popen(
        cmd,
        cwd=str(_project_root()),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    info = RunInfo(
        id=uuid.uuid4().hex[:8],
        status="running",
        out_dir=str(out_dir),
        config=req.config,
        cmd=cmd,
        pid=proc.pid,
        log_path=str(log_path),
        iteration=req.iteration or iter_n,
    )
    with _RUNS_LOCK:
        _RUNS[info.id] = info

    def _watch():
        rc = proc.wait()
        log_f.close()
        with _RUNS_LOCK:
            r = _RUNS.get(info.id)
            if r is not None:
                r.returncode = rc
                r.ended_at = time.time()
                r.status = "done" if rc == 0 else "failed"
        # Auto-compose grid.mp4 from per-persona replays. Best-effort —
        # don't change run status if this fails.
        if rc == 0:
            try:
                grid_proc = subprocess.run(
                    [sys.executable, "-m", "usersim.grid", str(out_dir)],
                    cwd=str(_project_root()),
                    capture_output=True,
                    timeout=120,
                )
                if grid_proc.returncode != 0:
                    print(f"[run {info.id}] grid compose failed: {grid_proc.stderr.decode()[:200]}")
            except Exception as e:
                print(f"[run {info.id}] grid compose exception: {e}")

    threading.Thread(target=_watch, daemon=True).start()
    return info


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
        "http://localhost:3100", "http://127.0.0.1:3100",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Heartbeat-based registry pruner
#
# Worker.update() stamps last_step_at on every turn. If a row's heartbeat is
# older than STALE_S, the parent process is almost certainly dead — prune
# the registry row and reap the matching kernel browser session.
# ---------------------------------------------------------------------------
PRUNE_INTERVAL_S = 5
STALE_S = 45              # rows older than this with no update → prune
NEVER_STARTED_S = 30      # turn==0 ghost — parent died before first action


def _prune_registry_once() -> int:
    """Returns count of rows pruned. Called from background loop + on startup."""
    from datetime import datetime as _dt
    pruned = 0
    try:
        rows = registry.list_active()
    except Exception:
        return 0
    now = _dt.now()
    for r in rows:
        try:
            age = (now - r.last_step_at).total_seconds()
        except Exception:
            age = 0
        is_stale = age > STALE_S
        is_ghost = r.current_turn == 0 and age > NEVER_STARTED_S
        if is_stale or is_ghost:
            try:
                registry.remove(r.browser_session_id)
                pruned += 1
            except Exception:
                continue
            # Best-effort: kill the kernel browser too.
            try:
                from kernel import Kernel
                client = Kernel(api_key=os.environ.get("KERNEL_API_KEY", ""))
                client.browsers.delete_by_id(r.browser_session_id)
            except Exception:
                pass
    return pruned


@app.on_event("startup")
async def _start_pruner() -> None:
    async def _loop():
        while True:
            await asyncio.sleep(PRUNE_INTERVAL_S)
            n = await asyncio.to_thread(_prune_registry_once)
            if n > 0:
                print(f"[pruner] removed {n} stale registry rows")
    # Single shot on startup to clear any leftovers from prior process.
    await asyncio.to_thread(_prune_registry_once)
    asyncio.create_task(_loop())


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX.read_text()


@app.get("/api/sessions")
def sessions() -> list[dict]:
    return [json.loads(r.model_dump_json()) for r in registry.list_active()]


@app.get("/api/personas")
def personas() -> dict[str, dict]:
    out: dict[str, dict] = {}
    p = _personas_path()
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if "id" in obj:
                out[obj["id"]] = obj
        except json.JSONDecodeError:
            continue
    return out


@app.get("/api/avatar/{persona_id}")
def avatar(persona_id: str):
    # Strip .png if the client included it.
    pid = persona_id[:-4] if persona_id.endswith(".png") else persona_id
    # Defensive: prevent path traversal.
    if "/" in pid or ".." in pid:
        raise HTTPException(status_code=400, detail="invalid persona id")
    p = _avatars_dir() / f"{pid}.png"
    if not p.exists():
        raise HTTPException(status_code=404)
    return FileResponse(p, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/feedback")
def feedback() -> dict | None:
    p = _latest_feedback_path()
    if p is None:
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


@app.get("/api/configs")
def configs_list() -> list[dict]:
    """List task YAML configs available for run launching."""
    out: list[dict] = []
    cdir = _configs_dir()
    if not cdir.exists():
        return out
    for p in sorted(cdir.glob("*.yaml")):
        c = _load_yaml_config(p)
        if not isinstance(c, dict) or "target_url" not in c or "tasks" not in c:
            continue
        out.append({
            "path": str(p.relative_to(_project_root())),
            "target_url": c.get("target_url"),
            "target_commit": c.get("target_commit"),
            "tasks": [
                {"id": t.get("id"), "description": t.get("description", "")}
                for t in c.get("tasks", [])
                if isinstance(t, dict) and "id" in t
            ],
            "agent": c.get("agent"),
            "personas_path": c.get("personas_path") or c.get("personas"),
        })
    return out


@app.get("/api/agents")
def agents_list() -> list[str]:
    """Registered agent providers (keys of clients._REGISTRY)."""
    return available_agents()


@app.post("/api/run")
def run_launch(req: RunRequest) -> RunInfo:
    """Spawn a usersim run. Returns immediately; the SSE stream surfaces progress."""
    cfg_path = _project_root() / req.config
    if not cfg_path.exists():
        raise HTTPException(status_code=400, detail=f"config not found: {req.config}")
    return _spawn_run(req)


@app.get("/api/run/{run_id}")
def run_status(run_id: str) -> RunInfo:
    with _RUNS_LOCK:
        info = _RUNS.get(run_id)
    if info is None:
        raise HTTPException(status_code=404, detail="run not found")
    return info


@app.get("/api/runs")
def runs_list() -> list[RunInfo]:
    with _RUNS_LOCK:
        return sorted(_RUNS.values(), key=lambda r: r.started_at, reverse=True)


@app.post("/api/run/{run_id}/cancel")
def run_cancel(run_id: str) -> RunInfo:
    """Cancel a running launch. SIGTERM first, SIGKILL after 3s if still alive.

    Also reaps any orphan Kernel browser sessions left behind. Always returns
    the RunInfo even if the process was already dead.
    """
    with _RUNS_LOCK:
        info = _RUNS.get(run_id)
    if info is None:
        raise HTTPException(status_code=404, detail="run not found")

    pid = info.pid
    if pid is None:
        raise HTTPException(status_code=409, detail="run has no pid")

    if info.status not in ("running", "pending"):
        return info  # already finished, nothing to do

    # We started the process group with start_new_session=True; kill the whole pg.
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass

    # Give it 3s to die gracefully, then SIGKILL.
    def _force_kill():
        time.sleep(3)
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        # Reap any Kernel browser sessions left behind by the killed run.
        try:
            from kernel import Kernel
            client = Kernel(api_key=os.environ.get("KERNEL_API_KEY", ""))
            for s in client.browsers.list():
                try:
                    client.browsers.delete_by_id(s.session_id)
                except Exception:
                    pass
        except Exception:
            pass
        # Clear the active.json registry so the dashboard doesn't show ghosts.
        try:
            (_project_root() / "runs" / "active.json").write_text("[]")
        except Exception:
            pass

    threading.Thread(target=_force_kill, daemon=True).start()

    with _RUNS_LOCK:
        info.status = "cancelled"
        info.ended_at = time.time()
    return info


@app.post("/api/registry/reap")
def reap_registry() -> dict:
    """Force-clear the active.json registry and reap all live Kernel browser
    sessions. Use when the dashboard shows ghost cells with no underlying run.
    """
    reaped_kernel = 0
    try:
        from kernel import Kernel
        client = Kernel(api_key=os.environ.get("KERNEL_API_KEY", ""))
        for s in client.browsers.list():
            try:
                client.browsers.delete_by_id(s.session_id)
                reaped_kernel += 1
            except Exception:
                pass
    except Exception:
        pass
    try:
        (_project_root() / "runs" / "active.json").write_text("[]")
    except Exception:
        pass
    return {"registry_cleared": True, "kernel_sessions_reaped": reaped_kernel}


def _find_trajectory_jsonl(persona_id: str, task_id: str, browser_session_id: str | None) -> Path | None:
    """Find the most-recent trajectory JSONL file matching persona+task.

    Walks runs/ recursively because some run shapes are nested: regular
    runs land at runs/<iter>/trajectories/<p>__<t>.jsonl, but the apps
    sweep nests one level deeper at runs/apps_sweep_X/<app>/trajectories/...
    If a browser_session_id is given, prefer the file whose header
    references it.
    """
    runs = _project_root() / "runs"
    if not runs.exists():
        return None
    pattern = f"{persona_id}__{task_id}.jsonl"
    candidates: list[tuple[float, Path]] = []
    # rglob covers any nesting depth under runs/
    for f in runs.rglob(pattern):
        if f.is_file() and "trajectories" in f.parts:
            candidates.append((f.stat().st_mtime, f))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    if browser_session_id:
        for _, f in candidates:
            try:
                with f.open() as fh:
                    line = fh.readline()
                    head = json.loads(line) if line.strip() else {}
                if head.get("browser_session_id") == browser_session_id:
                    return f
            except Exception:
                continue
    return candidates[0][1]


@app.get("/api/trajectory")
def trajectory(persona_id: str, task_id: str, browser_session_id: str | None = None) -> dict:
    """Return the full streamed trajectory for a (persona, task) pair as an
    array of records (`kind: header|step|footer`). Used by the dashboard's
    focused-cell view to render the full transcript of a rollout.
    """
    f = _find_trajectory_jsonl(persona_id, task_id, browser_session_id)
    if f is None:
        raise HTTPException(status_code=404, detail="trajectory not found")
    out: list[dict] = []
    try:
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"could not read trajectory: {e}")
    return {"path": str(f.relative_to(_project_root())), "records": out}


@app.get("/api/thumbnail")
def thumbnail(path: str):
    """Serve a screenshot thumbnail referenced by a trajectory step."""
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="invalid path")
    candidates = [_project_root() / "runs" / path, _project_root() / path]
    for p in candidates:
        if p.exists() and p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            return FileResponse(p, media_type=f"image/{p.suffix.lower().lstrip('.')}")
    raise HTTPException(status_code=404)


@app.get("/api/run/{run_id}/grid")
def run_grid(run_id: str):
    """Serve the auto-composed grid.mp4 for a completed run."""
    with _RUNS_LOCK:
        info = _RUNS.get(run_id)
    if info is None:
        raise HTTPException(status_code=404, detail="run not found")
    p = Path(info.out_dir) / "grid.mp4"
    if not p.exists():
        raise HTTPException(status_code=404, detail="grid not ready (still composing or run failed)")
    return FileResponse(p, media_type="video/mp4", filename=f"{run_id}_grid.mp4")


@app.get("/api/runs/historical")
def runs_historical() -> list[dict]:
    """Scan runs/ dir and return metadata for every run directory that exists on disk,
    including CLI-kicked sweeps that were never registered in _RUNS.

    Layouts detected:
      flat:  runs/<name>/trajectories/<p>__<t>.jsonl   (regular iter or small sweep)
      sweep: runs/<name>/<app>/trajectories/<p>__<t>.jsonl  (multi-app sweep)
    """
    runs_root = _project_root() / "runs"
    if not runs_root.exists():
        return []

    results: list[dict] = []
    for entry in sorted(runs_root.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True):
        if not entry.is_dir() or entry.name == "__pycache__" or entry.name.startswith("."):
            continue
        # Skip active.json and non-dir entries
        if not entry.is_dir():
            continue

        # Determine layout
        traj_dir = entry / "trajectories"
        summary_file = entry / "summary.json"
        feedback_file = entry / "feedback.json"
        grid_mp4 = entry / "grid.mp4"

        if traj_dir.exists():
            # flat layout
            traj_files = list(traj_dir.glob("*.jsonl"))
            n_traj = len(traj_files)
            apps: list[str] = []
            layout = "flat"
        else:
            # check for sweep layout: subdirs with their own trajectories/
            app_dirs = [d for d in entry.iterdir() if d.is_dir() and (d / "trajectories").exists()]
            if not app_dirs:
                continue  # skip dirs with no recognizable run data
            apps = [d.name for d in sorted(app_dirs)]
            n_traj = sum(len(list(d.glob("trajectories/*.jsonl"))) for d in app_dirs)
            layout = "sweep"

        started_at: str | None = None
        try:
            started_at = entry.stat().st_mtime.__class__.__name__  # placeholder
            import datetime
            started_at = datetime.datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
        except Exception:
            pass

        target_summary: str | None = None
        if summary_file.exists():
            try:
                data = json.loads(summary_file.read_text())
                if isinstance(data, list) and data:
                    # sweep summary.json is array of result objects
                    apps_hit = set(d.get("app", "") for d in data if d.get("terminal_reason", "").startswith("success"))
                    target_summary = f"{len(apps_hit)} apps · {len(data)} runs"
                elif isinstance(data, dict):
                    target_summary = data.get("summary") or data.get("description")
            except Exception:
                pass

        display_name = entry.name
        # Make it a bit more readable
        if display_name.startswith("iter_"):
            display_name = display_name.replace("iter_", "iter ")

        results.append({
            "run_dir": entry.name,
            "display_name": display_name,
            "layout": layout,
            "apps": apps,
            "n_trajectories": n_traj,
            "started_at": started_at,
            "has_feedback": feedback_file.exists() or any((entry / a / "feedback.json").exists() for a in apps),
            "has_grid_mp4": grid_mp4.exists(),
            "target_summary": target_summary,
        })

    return results


@app.get("/api/runs/historical/{run_dir:path}/sessions")
def historical_sessions(run_dir: str) -> list[dict]:
    """Return reconstructed ActiveRollout-shaped dicts for every trajectory in a
    historical run dir, suitable for populating the grid in replay mode.
    """
    if ".." in run_dir or run_dir.startswith("/"):
        raise HTTPException(status_code=400, detail="invalid run_dir")
    runs_root = _project_root() / "runs"
    entry = runs_root / run_dir
    if not entry.exists() or not entry.is_dir():
        raise HTTPException(status_code=404, detail="run dir not found")

    results: list[dict] = []
    # Collect (trajectory_path, app_name or None) pairs
    pairs: list[tuple[Path, str | None]] = []
    traj_dir = entry / "trajectories"
    if traj_dir.exists():
        for f in sorted(traj_dir.glob("*.jsonl")):
            pairs.append((f, None))
    else:
        for app_dir in sorted(entry.iterdir()):
            if not app_dir.is_dir():
                continue
            atd = app_dir / "trajectories"
            if atd.exists():
                for f in sorted(atd.glob("*.jsonl")):
                    pairs.append((f, app_dir.name))

    for traj_path, app in pairs:
        stem = traj_path.stem  # e.g. "elderly_first_time__pick_a_dashboard"
        parts = stem.split("__", 1)
        persona_id = parts[0] if parts else stem
        task_id = parts[1] if len(parts) > 1 else "unknown"

        header: dict = {}
        footer: dict = {}
        n_steps = 0
        last_reasoning: str | None = None
        current_url: str | None = None
        current_title: str | None = None
        status = "error"

        try:
            for raw_line in traj_path.read_text().splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = rec.get("kind")
                if kind == "header":
                    header = rec
                elif kind == "step":
                    n_steps += 1
                    last_reasoning = (rec.get("reasoning") or [None])[-1] or last_reasoning
                    obs = rec.get("observation") or {}
                    current_url = obs.get("page_url") or current_url
                    current_title = obs.get("page_title") or current_title
                elif kind == "footer":
                    footer = rec
        except Exception:
            continue

        terminal = footer.get("terminal_reason", "error")
        if terminal in ("success_dom", "success_url"):
            status = terminal
        elif terminal in ("abandoned",):
            status = "abandoned"
        elif terminal == "stuck":
            status = "stuck"
        else:
            status = "error"

        # Check for replay file
        if app:
            replay_rel = f"{run_dir}/{app}/replays/{stem}.mp4"
            replay_abs = runs_root / run_dir / app / "replays" / f"{stem}.mp4"
        else:
            replay_rel = f"{run_dir}/replays/{stem}.mp4"
            replay_abs = runs_root / run_dir / "replays" / f"{stem}.mp4"

        fake_session_id = f"hist__{run_dir}__{app or 'flat'}__{stem}"

        results.append({
            "browser_session_id": fake_session_id,
            "persona_id": persona_id,
            "task_id": task_id,
            "target_url": header.get("target_url") or footer.get("final_url") or "",
            "started_at": header.get("started_at") or "",
            "live_view_url": "",
            "current_turn": n_steps,
            "last_action": None,
            "last_reasoning": last_reasoning,
            "current_url": current_url,
            "current_title": current_title,
            "current_dom_hash": None,
            "consecutive_unchanged": 0,
            "cumulative_tokens": {"model_ms": 0, "prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0, "cost_usd": 0},
            "cumulative_ms": 0,
            "stage1_status": status,
            "run_dir": run_dir,
            "app": app,
            "terminal_reason": terminal,
            "replay_path": replay_rel if replay_abs.exists() else None,
        })

    return results


@app.get("/api/replay")
def serve_replay(path: str):
    """Serve a replay .mp4 with range-request support so the browser can scrub.
    `path` is relative to runs/ (e.g. iter_000/replays/persona__task.mp4).
    """
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="invalid path")
    p = _project_root() / "runs" / path
    if not p.exists() or not p.is_file() or p.suffix.lower() != ".mp4":
        raise HTTPException(status_code=404, detail="replay not found")
    return FileResponse(p, media_type="video/mp4",
                        headers={"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=3600"})


@app.get("/api/stream")
async def stream() -> StreamingResponse:
    async def gen():
        last = None
        while True:
            current = [json.loads(r.model_dump_json()) for r in registry.list_active()]
            payload = json.dumps(current, sort_keys=True, default=str)
            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream")
