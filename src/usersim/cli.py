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
from usersim.map.runner import run_iteration
from usersim.reduce.aggregator import aggregate, load_prev_feedback
from usersim.schemas import Persona, Task

load_dotenv()


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
        max_turns=config.get("max_turns", 20),
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
        max_turns=config.get("max_turns", 20),
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
    return 0


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
    pd.set_defaults(func=cmd_debug)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
