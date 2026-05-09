"""CLI entrypoint.

Examples:
    uv run python -m usersim run --config configs/taxcaster.yaml --out runs/iter_000
    uv run python -m usersim debug --config configs/taxcaster.yaml --persona rushed_mobile --task single_w2_basic --out runs/spike_001
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from usersim.browsers.kernel import KernelProvider
from usersim.clients import available as available_clients
from usersim.clients import get_client
from usersim.grid import compose_for_dir
from usersim.map.runner import run_iteration
from usersim.reduce.aggregator import aggregate, load_prev_feedback
from usersim.schemas import Persona, Task

load_dotenv()


def _try_compose_grid(out_dir: Path) -> None:
    """Auto-fire grid encode at end of run/sweep. Failures are logged but
    don't propagate — a bad ffmpeg run shouldn't kill an otherwise-successful
    iteration. Skips silently if there are no replays."""
    try:
        result = compose_for_dir(out_dir)
        if result is None:
            print(f"[cli] no replays under {out_dir} — skipping grid")
    except Exception as e:
        print(f"[cli] grid compose failed: {type(e).__name__}: {e}", file=sys.stderr)


def _load_personas(path: Path) -> list[Persona]:
    return [Persona(**json.loads(line)) for line in path.read_text().splitlines() if line.strip()]


def _load_tasks(config: dict) -> list[Task]:
    """Per-task success criteria override the config-level defaults (audit O5).

    Config-level `success_dom` / `success_url_pattern` apply to every task that
    doesn't specify its own. Different tasks can target different completion
    selectors without forking the YAML.
    """
    default_dom = config.get("success_dom")
    default_url = config.get("success_url_pattern")
    return [
        Task(
            id=t["id"],
            description=t["description"],
            success_dom=t.get("success_dom", default_dom),
            success_url_pattern=t.get("success_url_pattern", default_url),
            metadata=t.get("metadata", {}),
        )
        for t in config["tasks"]
    ]


def _load_config_personas(config: dict) -> list[Persona]:
    # Inline list in YAML (smoke.yaml style)
    if isinstance(config.get("personas"), list):
        return [Persona(**p) for p in config["personas"]]
    # Path to JSONL
    path = config.get("personas") or config.get("personas_path", "configs/personas/seed.jsonl")
    return _load_personas(Path(path))


def cmd_run(args: argparse.Namespace) -> int:
    config = yaml.safe_load(Path(args.config).read_text())
    personas = _load_config_personas(config)
    tasks = _load_tasks(config)

    if args.personas:
        wanted = set(args.personas.split(","))
        personas = [p for p in personas if p.id in wanted]
    if args.tasks:
        wanted = set(args.tasks.split(","))
        tasks = [t for t in tasks if t.id in wanted]

    out_dir = Path(args.out)

    # Agent: CLI overrides YAML; YAML default is "northstar".
    agent_spec = config.get("agent", {"type": "northstar"})
    if isinstance(agent_spec, str):
        agent_spec = {"type": agent_spec}
    if args.agent:
        agent_spec = {**agent_spec, "type": args.agent}
    if args.agent_endpoint:
        agent_spec["endpoint"] = args.agent_endpoint
    client = get_client(agent_spec)
    browser_provider = KernelProvider()

    print(f"[cli] target={config['target_url']}")
    print(f"[cli] agent={agent_spec.get('type')}"
          + (f" endpoint={agent_spec.get('endpoint')}" if agent_spec.get('endpoint') else ""))
    print(f"[cli] {len(personas)} personas × {len(tasks)} tasks = {len(personas)*len(tasks)} workers")
    print(f"[cli] concurrency={args.concurrency}")

    trajectories = asyncio.run(run_iteration(
        target_url=config["target_url"],
        target_commit=config.get("target_commit", "external"),
        personas=personas,
        tasks=tasks,
        client=client,
        browser_provider=browser_provider,
        out_dir=out_dir,
        concurrency=args.concurrency,
        viewport_width=config.get("viewport", {}).get("width", 1280),
        viewport_height=config.get("viewport", {}).get("height", 800),
        max_turns=args.max_turns or config.get("max_turns", 20),
        stuck_threshold=args.stuck_threshold,
        patience_override=args.patience,
    ))

    prev_path = Path(args.prev_feedback) if args.prev_feedback else None
    prev = load_prev_feedback(prev_path) if prev_path else None
    fb = aggregate(
        trajectories,
        iteration=args.iteration,
        target_commit=config.get("target_commit", "external"),
        out_dir=out_dir,
        prev_feedback=prev,
    )
    print(f"[cli] feedback → {out_dir}/feedback.json")
    print(f"[cli] success_gameable={fb.metrics.success_rate_gameable:.1%} "
          f"abandonment={fb.metrics.abandonment_rate:.1%} errors={fb.metrics.errors_per_iteration}")
    _try_compose_grid(out_dir)
    return 0


def cmd_debug(args: argparse.Namespace) -> int:
    """Single-worker spike: one persona × one task, verbose."""
    config = yaml.safe_load(Path(args.config).read_text())
    personas = _load_config_personas(config)
    tasks = _load_tasks(config)
    persona = next((p for p in personas if p.id == args.persona), None)
    task = next((t for t in tasks if t.id == args.task), None)
    if persona is None:
        print(f"persona '{args.persona}' not found", file=sys.stderr)
        return 1
    if task is None:
        print(f"task '{args.task}' not found", file=sys.stderr)
        return 1

    out_dir = Path(args.out)

    agent_spec = config.get("agent", {"type": "northstar"})
    if isinstance(agent_spec, str):
        agent_spec = {"type": agent_spec}
    if args.agent:
        agent_spec = {**agent_spec, "type": args.agent}
    if args.agent_endpoint:
        agent_spec["endpoint"] = args.agent_endpoint
    client = get_client(agent_spec)
    browser_provider = KernelProvider()

    trajectories = asyncio.run(run_iteration(
        target_url=config["target_url"],
        target_commit=config.get("target_commit", "external"),
        personas=[persona],
        tasks=[task],
        client=client,
        browser_provider=browser_provider,
        out_dir=out_dir,
        concurrency=1,
        max_turns=args.max_turns or config.get("max_turns", 20),
        stuck_threshold=args.stuck_threshold,
        patience_override=args.patience,
    ))
    if trajectories:
        t = trajectories[0]
        print(f"[debug] terminal_reason={t.terminal_reason} steps={len(t.steps)}")
    # Aggregate too — debug runs benefit from feedback.json + summary.md just
    # as much as full iterations (audit O12). Cheap with N=1.
    aggregate(
        trajectories,
        iteration=0,
        target_commit=config.get("target_commit", "external"),
        out_dir=out_dir,
    )
    _try_compose_grid(out_dir)
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    """Sweep across the apps registry. One rollout per (app, task, persona)
    triple, ALL flattened into one asyncio.gather — apps run in parallel,
    not sequentially."""
    from usersim.apps import filter_apps, load_apps
    from usersim.map.worker import run_one

    registry_path = Path(args.registry) if args.registry else None
    apps = load_apps(registry_path)
    apps = filter_apps(apps, set(args.apps.split(",")) if args.apps else None)

    config_personas: list[Persona] = (
        _load_personas(Path(args.personas_path)) if args.personas_path
        else _load_config_personas({"personas_path": "configs/personas/seed.jsonl"})
    )
    if args.personas:
        wanted = set(args.personas.split(","))
        config_personas = [p for p in config_personas if p.id in wanted]

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    agent_spec = {"type": args.agent or "surfer"}
    if args.agent_endpoint:
        agent_spec["endpoint"] = args.agent_endpoint
    client = get_client(agent_spec)
    browser_provider = KernelProvider()

    # Build the flat work list.
    triples: list[tuple] = []  # (app, persona, task)
    for app in apps:
        tasks_for_app = filter_app_tasks(app.tasks, args.tasks)
        for task in tasks_for_app:
            for persona in config_personas:
                triples.append((app, persona, task))

    print(f"[sweep] {len(apps)} apps × {len(config_personas)} personas → {len(triples)} rollouts")
    print(f"[sweep] agent={agent_spec['type']}  concurrency={args.concurrency}  out={out_root}\n")

    sem = asyncio.Semaphore(args.concurrency)

    async def _one(app, persona, task) -> dict:
        async with sem:
            app_out = out_root / app.id
            app_out.mkdir(parents=True, exist_ok=True)
            print(f"[start] {app.id:<20} {persona.id} × {task.id}", flush=True)
            traj = await run_one(
                persona, task,
                target_url=app.target_url,
                target_commit="external",
                client=client,
                browser_provider=browser_provider,
                out_dir=app_out,
                max_turns=args.max_turns or 12,
            )
            print(f"[done ] {app.id:<20} {traj.terminal_reason:<14} {len(traj.steps):2d} steps", flush=True)
            return {
                "app": app.id,
                "persona": persona.id,
                "task": task.id,
                "terminal_reason": traj.terminal_reason,
                "n_steps": len(traj.steps),
                "final_url": traj.final_url,
            }

    async def _all() -> list[dict]:
        return await asyncio.gather(*[_one(*t) for t in triples])

    results = asyncio.run(_all())

    # Per-app aggregation.
    from collections import defaultdict
    by_app: dict[str, list] = defaultdict(list)
    for r in results:
        by_app[r["app"]].append(r)
    for app_id, rs in by_app.items():
        from usersim.io import read_trajectory
        trajs = []
        for r in rs:
            p = out_root / app_id / "trajectories" / f"{r['persona']}__{r['task']}.jsonl"
            if p.exists():
                trajs.append(read_trajectory(p))
        if trajs:
            aggregate(trajs, iteration=0, target_commit="external", out_dir=out_root / app_id)

    print("\n[summary]")
    print(f"  {'app':<22} {'persona':<24} {'task':<22} {'terminal':<14} {'steps':>5}")
    for r in sorted(results, key=lambda r: (r["app"], r["persona"], r["task"])):
        print(f"  {r['app']:<22} {r['persona']:<24} {r['task']:<22} {r['terminal_reason']:<14} {r['n_steps']:>5}")
    successes = sum(1 for r in results if r["terminal_reason"] in ("success_dom", "success_url", "agent_done"))
    print(f"\n  successes: {successes}/{len(results)}")
    (out_root / "summary.json").write_text(json.dumps(results, indent=2))
    _try_compose_grid(out_root)
    return 0


def filter_app_tasks(tasks: list[Task], wanted_csv: str | None) -> list[Task]:
    if not wanted_csv:
        return tasks
    wanted = set(wanted_csv.split(","))
    return [t for t in tasks if t.id in wanted]


def main() -> int:
    p = argparse.ArgumentParser(prog="usersim")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="run a full map iteration")
    pr.add_argument("--config", required=True)
    pr.add_argument("--out", required=True)
    pr.add_argument("--concurrency", type=int, default=5)
    pr.add_argument("--personas", help="comma-separated subset of persona ids")
    pr.add_argument("--tasks", help="comma-separated subset of task ids")
    pr.add_argument("--iteration", type=int, default=0)
    pr.add_argument("--prev-feedback", help="path to previous feedback.json for regression detection")
    pr.add_argument("--agent", choices=available_clients(),
                    help="agent provider; overrides config 'agent.type'. default: from config or 'northstar'")
    pr.add_argument("--agent-endpoint",
                    help="agent endpoint URL (for http-based providers like holotron)")
    pr.add_argument("--max-turns", type=int, default=None,
                    help="hard turn cap per rollout; overrides config 'max_turns'")
    pr.add_argument("--stuck-threshold", type=int, default=3,
                    help="terminate as 'stuck' after N consecutive turns of unchanged DOM. 0 disables.")
    pr.add_argument("--patience", type=int, default=None,
                    help="override per-persona patience_steps for this run. 0 disables abandonment.")
    pr.set_defaults(func=cmd_run)

    pd = sub.add_parser("debug", help="run one persona × one task")
    pd.add_argument("--config", default="configs/taxcaster.yaml")
    pd.add_argument("--persona", required=True)
    pd.add_argument("--task", required=True)
    pd.add_argument("--out", default="runs/debug")
    pd.add_argument("--agent", choices=available_clients(),
                    help="agent provider; overrides config")
    pd.add_argument("--agent-endpoint",
                    help="agent endpoint URL")
    pd.add_argument("--max-turns", type=int, default=None)
    pd.add_argument("--stuck-threshold", type=int, default=3)
    pd.add_argument("--patience", type=int, default=None)
    pd.set_defaults(func=cmd_debug)

    ps = sub.add_parser("sweep", help="run one rollout per (app, task, persona) across the apps registry")
    ps.add_argument("--registry", help="path to apps registry JSONL (default: configs/apps/registry.jsonl)")
    ps.add_argument("--out", required=True, help="root output dir; each app gets its own subdir")
    ps.add_argument("--apps", help="comma-separated subset of app ids")
    ps.add_argument("--tasks", help="comma-separated subset of task ids (filters within each app)")
    ps.add_argument("--personas", help="comma-separated subset of persona ids")
    ps.add_argument("--personas-path", help="override personas JSONL (default: configs/personas/seed.jsonl)")
    ps.add_argument("--concurrency", type=int, default=4,
                    help="concurrent workers per app (apps run sequentially)")
    ps.add_argument("--agent", choices=available_clients())
    ps.add_argument("--agent-endpoint")
    ps.add_argument("--max-turns", type=int, default=None)
    ps.set_defaults(func=cmd_sweep)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
