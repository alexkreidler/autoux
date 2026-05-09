"""Fake coding-agent contract verifier.

Closes the loop end-to-end against synthetic data, no Kernel/Tzafon required:

    1. Build synthetic trajectory fixtures (build_synthetic.py).
    2. Load them back as pydantic Trajectories.
    3. Run grader → outcomes.
    4. Run aggregator → feedback.json.
    5. Pretend to be the coding-agent: read feedback.json, validate against
       schema, plan synthetic patches based on top friction clusters.
    6. Show what each cluster would prompt the coding agent to do.

Run:
    uv run python tests/test_contract.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from usersim.io import read_trajectory
from usersim.reduce.aggregator import aggregate, load_prev_feedback
from usersim.schemas import Feedback


def load_iter(iter_dir: Path) -> list:
    return [read_trajectory(p) for p in sorted((iter_dir / "trajectories").glob("*.jsonl"))]


ROOT = Path(__file__).parent.parent
SYNTH_DIR = ROOT / "runs" / "synthetic_iter_0"


def coding_agent_consume(feedback: Feedback) -> list[str]:
    """Pretend to be the coding-agent. Pull actionable items from the contract."""
    actions: list[str] = []

    # Triage by overall metrics
    m = feedback.metrics
    if m.success_rate_gameable < 0.5:
        actions.append(
            f"PRIORITY: success rate is {m.success_rate_gameable:.0%}; "
            f"the dominant failure mode below should drive the next patch."
        )

    # Plan one patch per friction cluster
    for cluster in feedback.top_friction_clusters:
        actions.append(
            f"[{cluster.id}] {cluster.n_affected} users affected → {cluster.description}"
        )
        for hint in cluster.suggested_dom_targets[:1]:
            actions.append(f"  ↳ probe DOM: {hint}")
        for excerpt in cluster.reasoning_excerpts[:2]:
            actions.append(f"  ↳ user said: \"{excerpt}\"")

    # Reward-hacking flag
    if m.delta_gameable_vs_heldout is not None and m.delta_gameable_vs_heldout > 0.15:
        actions.append(
            f"⚠️  REWARD HACKING SUSPECTED: gameable success exceeds held-out by "
            f"{m.delta_gameable_vs_heldout:+.1%}. Investigate before patching further."
        )

    for r in feedback.regressions_vs_prev:
        actions.append(f"REGRESSION: {r.description}")

    return actions


def main() -> int:
    if not SYNTH_DIR.exists():
        print(f"missing fixtures at {SYNTH_DIR}", file=sys.stderr)
        print("run: uv run python tests/fixtures/build_synthetic.py runs/synthetic_iter_0", file=sys.stderr)
        return 1

    print(f"# Loading trajectories from {SYNTH_DIR}")
    trajectories = load_iter(SYNTH_DIR)
    print(f"  loaded {len(trajectories)} trajectories")
    for t in trajectories:
        print(f"  - {t.persona_id}__{t.task_id}: {t.terminal_reason} ({len(t.steps)} steps)")

    out_dir = SYNTH_DIR
    prev = load_prev_feedback(out_dir / "feedback.json")
    print(f"\n# Running aggregator")
    feedback = aggregate(
        trajectories,
        iteration=0,
        target_commit="synthetic",
        out_dir=out_dir,
        prev_feedback=prev,
    )
    print(f"  wrote {out_dir / 'feedback.json'}")
    print(f"  wrote {out_dir / 'summary.md'}")
    print(f"  wrote {out_dir / 'outcomes.jsonl'}")

    print(f"\n# Validating Feedback contract")
    raw = json.loads((out_dir / "feedback.json").read_text())
    Feedback.model_validate(raw)  # roundtrip check
    print("  ✓ feedback.json validates against Feedback schema")

    print(f"\n# Pretending to be the coding agent")
    actions = coding_agent_consume(feedback)
    for a in actions:
        print(a)

    print(f"\n--- summary.md ---")
    print((out_dir / "summary.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
