"""python -m coder run --repo <path> --feedback <path> --iter <n>"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from coder.claude_cli import ClaudeCliAgent
from coder.loop import run_loop


def main() -> None:
    parser = argparse.ArgumentParser(prog="coder")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run one coding-agent iteration")
    run_p.add_argument("--repo", required=True, type=Path)
    run_p.add_argument("--feedback", required=True, type=Path)
    run_p.add_argument("--iter", required=True, type=int, dest="iteration")
    run_p.add_argument("--timeout", type=float, default=300.0)

    args = parser.parse_args()

    if args.cmd == "run":
        patch = asyncio.run(_run(args))
        print(json.dumps({
            "success": patch.success,
            "files_changed": patch.files_changed,
            "cost_usd": patch.cost_usd,
            "duration_ms": patch.duration_ms,
            "error": patch.error,
            "diff_lines": len(patch.diff.splitlines()),
        }, indent=2))


async def _run(args: argparse.Namespace):
    agent = ClaudeCliAgent()
    return await run_loop(
        repo_dir=args.repo.resolve(),
        feedback_path=args.feedback.resolve(),
        iteration=args.iteration,
        agent=agent,
    )


if __name__ == "__main__":
    main()
