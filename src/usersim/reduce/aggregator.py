"""Reduce step: trajectories → Outcomes → Feedback.

Feedback is THE contract with the coding-agent side. Adding fields is safe;
renaming/retyping is a sync point with teammate.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from usersim.reduce.cluster import cluster_failures
from usersim.reduce.grader import grade_stage1
from usersim.schemas import (
    Feedback,
    Metrics,
    Outcome,
    Regression,
    Trajectory,
)


def aggregate(
    trajectories: list[Trajectory],
    *,
    iteration: int,
    target_commit: str,
    out_dir: Path,
    prev_feedback: Feedback | None = None,
    raw_trajectory_dir: str = "trajectories/",
) -> Feedback:
    outcomes: list[Outcome] = [grade_stage1(t) for t in trajectories]

    metrics = _compute_metrics(outcomes, trajectories)
    clusters = cluster_failures(outcomes, trajectories)
    regressions = _detect_regressions(prev_feedback, metrics)

    feedback = Feedback(
        iteration=iteration,
        target_commit=target_commit,
        n_trajectories=len(trajectories),
        metrics=metrics,
        top_friction_clusters=clusters,
        regressions_vs_prev=regressions,
        raw_trajectory_dir=raw_trajectory_dir,
    )

    _persist(feedback, outcomes, out_dir)
    return feedback


def _compute_metrics(outcomes: list[Outcome], trajectories: list[Trajectory]) -> Metrics:
    n = len(outcomes)
    if n == 0:
        return Metrics(
            success_rate_gameable=0.0,
            abandonment_rate=0.0,
            errors_per_iteration=0,
        )

    successes = [o for o in outcomes if o.success_gameable]
    held_out_known = [o for o in outcomes if o.success_heldout is not None]

    by_key = {(t.persona_id, t.task_id): t for t in trajectories}
    success_step_counts = [
        len(by_key[(o.persona_id, o.task_id)].steps)
        for o in successes
        if (o.persona_id, o.task_id) in by_key
    ]

    gameable = len(successes) / n
    heldout = (
        sum(1 for o in held_out_known if o.success_heldout) / len(held_out_known)
        if held_out_known
        else None
    )
    delta = (gameable - heldout) if heldout is not None else None

    return Metrics(
        success_rate_gameable=gameable,
        success_rate_heldout=heldout,
        delta_gameable_vs_heldout=delta,
        median_steps_to_success=statistics.median(success_step_counts) if success_step_counts else None,
        abandonment_rate=sum(1 for o in outcomes if o.failure_category == "abandoned_by_persona") / n,
        errors_per_iteration=sum(1 for o in outcomes if o.failure_category == "error"),
    )


def _detect_regressions(prev: Feedback | None, metrics: Metrics) -> list[Regression]:
    if prev is None:
        return []
    out: list[Regression] = []
    drop = prev.metrics.success_rate_gameable - metrics.success_rate_gameable
    if drop > 0.10:
        out.append(Regression(
            description=f"gameable success rate dropped {drop:.1%} vs iter {prev.iteration}",
            first_seen_iter=prev.iteration + 1,
        ))
    if (
        metrics.delta_gameable_vs_heldout is not None
        and prev.metrics.delta_gameable_vs_heldout is not None
        and metrics.delta_gameable_vs_heldout - prev.metrics.delta_gameable_vs_heldout > 0.10
    ):
        out.append(Regression(
            description=(
                f"reward-hacking signal: gameable - heldout widened "
                f"{prev.metrics.delta_gameable_vs_heldout:+.1%} → {metrics.delta_gameable_vs_heldout:+.1%}"
            ),
            first_seen_iter=prev.iteration + 1,
        ))
    return out


def _persist(feedback: Feedback, outcomes: list[Outcome], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "feedback.json").write_text(feedback.model_dump_json(indent=2))
    (out_dir / "outcomes.jsonl").write_text(
        "\n".join(o.model_dump_json() for o in outcomes) + "\n"
    )
    (out_dir / "summary.md").write_text(_render_summary(feedback))


def _render_summary(fb: Feedback) -> str:
    m = fb.metrics
    lines = [
        f"# Iteration {fb.iteration}  (target `{fb.target_commit}`)",
        "",
        f"- Trajectories: **{fb.n_trajectories}**",
        f"- Success (gameable): **{m.success_rate_gameable:.1%}**",
    ]
    if m.success_rate_heldout is not None:
        lines.append(f"- Success (held-out judge): **{m.success_rate_heldout:.1%}**")
    if m.delta_gameable_vs_heldout is not None:
        lines.append(f"- Δ gameable − held-out: **{m.delta_gameable_vs_heldout:+.1%}** ← reward-hacking signal")
    lines.append(f"- Abandonment rate: {m.abandonment_rate:.1%}")
    lines.append(f"- Errors: {m.errors_per_iteration}")
    if m.median_steps_to_success is not None:
        lines.append(f"- Median steps to success: {m.median_steps_to_success:.0f}")

    if fb.top_friction_clusters:
        lines += ["", "## Top friction clusters"]
        for c in fb.top_friction_clusters:
            lines.append(f"### {c.id}  ({c.n_affected} affected)")
            lines.append(f"{c.description}")
            if c.example_persona_ids:
                lines.append(f"- Personas: {', '.join(c.example_persona_ids)}")
            if c.suggested_dom_targets:
                lines.append(f"- DOM hints: {', '.join(c.suggested_dom_targets)}")
            for ex in c.reasoning_excerpts[:3]:
                lines.append(f"  > {ex}")
            lines.append("")

    if fb.regressions_vs_prev:
        lines += ["## Regressions"]
        for r in fb.regressions_vs_prev:
            lines.append(f"- {r.description}")
        lines.append("")

    return "\n".join(lines) + "\n"


def load_prev_feedback(path: Path) -> Feedback | None:
    if not path.exists():
        return None
    return Feedback.model_validate(json.loads(path.read_text()))
