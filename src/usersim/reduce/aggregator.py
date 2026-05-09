"""Reduce step: trajectories → Outcomes → Feedback.

Feedback is THE contract with the coding-agent side. Adding fields is safe;
renaming/retyping is a sync point with teammate.
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from usersim.reduce.cluster import cluster_failures
from usersim.reduce.grader import grade_stage1
from usersim.schemas import (
    Feedback,
    Metrics,
    Outcome,
    PersonaSegment,
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

    segments = _compute_persona_segments(trajectories, outcomes)
    divergence = _persona_divergence_score(segments)
    findings = _persona_specific_findings(segments)

    feedback = Feedback(
        iteration=iteration,
        target_commit=target_commit,
        n_trajectories=len(trajectories),
        metrics=metrics,
        top_friction_clusters=clusters,
        regressions_vs_prev=regressions,
        raw_trajectory_dir=raw_trajectory_dir,
        by_persona=segments,
        persona_divergence_score=divergence,
        persona_specific_findings=findings,
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


def _compute_persona_segments(
    trajectories: list[Trajectory],
    outcomes: list[Outcome],
) -> list[PersonaSegment]:
    outcome_map: dict[tuple[str, str], Outcome] = {
        (o.persona_id, o.task_id): o for o in outcomes
    }

    by_persona: dict[str, list[Trajectory]] = defaultdict(list)
    for t in trajectories:
        by_persona[t.persona_id].append(t)

    # Collect all reasoning text per persona for distinctive-quote detection.
    all_reasoning: dict[str, list[str]] = {
        pid: [r for t in trajs for s in t.steps for r in s.reasoning]
        for pid, trajs in by_persona.items()
    }

    # Build a set of long reasoning strings from OTHER personas for dedup.
    def _other_text(pid: str) -> str:
        return " ".join(
            r for other_pid, rs in all_reasoning.items() if other_pid != pid for r in rs
        ).lower()

    # Action-type frequency per persona (normalized to calls-per-step).
    action_freq: dict[str, Counter] = {}
    for pid, trajs in by_persona.items():
        c: Counter = Counter()
        total_steps = sum(len(t.steps) for t in trajs)
        for t in trajs:
            for s in t.steps:
                c[s.action.type] += 1
        action_freq[pid] = Counter(
            {k: v / max(total_steps, 1) for k, v in c.items()}
        )

    # Median frequency per action type across personas.
    all_action_types = {a for c in action_freq.values() for a in c}
    median_freq: dict[str, float] = {
        atype: statistics.median(action_freq[pid].get(atype, 0.0) for pid in by_persona)
        for atype in all_action_types
    }

    segments: list[PersonaSegment] = []
    for pid, trajs in by_persona.items():
        persona_outcomes = [outcome_map[(t.persona_id, t.task_id)] for t in trajs if (t.persona_id, t.task_id) in outcome_map]
        n = len(trajs)
        success_rate = sum(1 for o in persona_outcomes if o.success_gameable) / n if n else 0.0
        avg_steps = statistics.mean(len(t.steps) for t in trajs) if trajs else 0.0
        avg_tokens = int(statistics.mean(
            sum(s.tokens.prompt_tokens + s.tokens.completion_tokens for s in t.steps)
            for t in trajs
        )) if trajs else 0
        terminal_reasons: dict[str, int] = dict(Counter(t.terminal_reason for t in trajs))

        # Distinctive quotes: longest reasoning per trajectory not found verbatim in other personas.
        other_text = _other_text(pid)
        quotes: list[str] = []
        for t in trajs:
            candidates = sorted(
                (r for s in t.steps for r in s.reasoning if len(r) > 30),
                key=len, reverse=True
            )
            for candidate in candidates:
                # Use first 60 chars as fingerprint for substring check
                if candidate[:60].lower() not in other_text:
                    quotes.append(candidate[:200])
                    break
        distinctive_quotes = quotes[:3]

        # Distinctive actions: action types where this persona's rate > 2x median.
        distinctive_actions = [
            atype for atype in action_freq[pid]
            if median_freq.get(atype, 0.0) > 0 and action_freq[pid][atype] > 2 * median_freq[atype]
        ]

        segments.append(PersonaSegment(
            persona_id=pid,
            n_attempts=n,
            success_rate=success_rate,
            avg_steps=avg_steps,
            avg_tokens=avg_tokens,
            terminal_reasons=terminal_reasons,
            distinctive_quotes=distinctive_quotes,
            distinctive_actions=distinctive_actions,
        ))

    segments.sort(key=lambda s: s.avg_steps)
    return segments


def _persona_divergence_score(segments: list[PersonaSegment]) -> float:
    if len(segments) < 2:
        return 0.0
    steps = [s.avg_steps for s in segments]
    tokens = [float(s.avg_tokens) for s in segments]
    step_div = (max(steps) - min(steps)) / max(steps) if max(steps) > 0 else 0.0
    token_div = (max(tokens) - min(tokens)) / max(tokens) if max(tokens) > 0 else 0.0
    return min(1.0, max(step_div, token_div))


def _persona_specific_findings(segments: list[PersonaSegment]) -> list[str]:
    if not segments:
        return []
    findings: list[str] = []

    # Step range finding
    by_steps = sorted(segments, key=lambda s: s.avg_steps)
    if len(by_steps) >= 2 and by_steps[-1].avg_steps > 0:
        ratio = by_steps[-1].avg_steps / max(by_steps[0].avg_steps, 1)
        if ratio >= 2:
            findings.append(
                f"Step count spans {ratio:.1f}x from {by_steps[0].persona_id} "
                f"({by_steps[0].avg_steps:.0f} steps) to {by_steps[-1].persona_id} "
                f"({by_steps[-1].avg_steps:.0f} steps)."
            )

    # Token range finding
    by_tokens = sorted(segments, key=lambda s: s.avg_tokens)
    if len(by_tokens) >= 2 and by_tokens[0].avg_tokens > 0:
        ratio = by_tokens[-1].avg_tokens / by_tokens[0].avg_tokens
        if ratio >= 2:
            findings.append(
                f"Token usage scales {ratio:.1f}x from {by_tokens[0].persona_id} "
                f"({by_tokens[0].avg_tokens:,} tokens) to {by_tokens[-1].persona_id} "
                f"({by_tokens[-1].avg_tokens:,} tokens)."
            )

    # Success rate outliers
    success_rates = [s.success_rate for s in segments]
    if success_rates:
        avg_sr = statistics.mean(success_rates)
        for seg in segments:
            if seg.success_rate == 0.0 and avg_sr > 0.3:
                findings.append(
                    f"{seg.persona_id} succeeded on 0% of attempts while the overall average is {avg_sr:.0%}."
                )
            elif seg.success_rate == 1.0 and avg_sr < 0.7:
                findings.append(
                    f"{seg.persona_id} succeeded on every attempt while the overall average is {avg_sr:.0%}."
                )

    # Persona-specific terminal reasons
    all_reasons_union = {r for seg in segments for r in seg.terminal_reasons}
    for reason in all_reasons_union:
        has_reason = [seg for seg in segments if reason in seg.terminal_reasons]
        no_reason = [seg for seg in segments if reason not in seg.terminal_reasons]
        if has_reason and no_reason and len(has_reason) <= len(segments) // 2:
            pids = ", ".join(s.persona_id for s in has_reason)
            findings.append(
                f"Terminal reason '{reason}' appears only for {pids}."
            )

    # Distinctive action finding
    for seg in segments:
        if seg.distinctive_actions:
            actions_str = ", ".join(seg.distinctive_actions)
            findings.append(
                f"{seg.persona_id} uses {actions_str} more than 2x the median rate."
            )

    return findings[:5]


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

    if fb.by_persona:
        lines += [f"## Per-persona breakdown  (divergence score: {fb.persona_divergence_score:.2f})", ""]
        for seg in fb.by_persona:
            reasons_str = ", ".join(f"{k}×{v}" for k, v in seg.terminal_reasons.items())
            lines.append(f"### {seg.persona_id}")
            lines.append(f"- Attempts: {seg.n_attempts}  Success: {seg.success_rate:.0%}  "
                         f"Avg steps: {seg.avg_steps:.1f}  Avg tokens: {seg.avg_tokens:,}")
            lines.append(f"- Terminal reasons: {reasons_str}")
            if seg.distinctive_actions:
                lines.append(f"- Distinctive actions: {', '.join(seg.distinctive_actions)}")
            for q in seg.distinctive_quotes:
                lines.append(f"  > {q}")
            lines.append("")
        if fb.persona_specific_findings:
            lines.append("### Key findings")
            for f_ in fb.persona_specific_findings:
                lines.append(f"- {f_}")
            lines.append("")

    return "\n".join(lines) + "\n"


def load_prev_feedback(path: Path) -> Feedback | None:
    if not path.exists():
        return None
    return Feedback.model_validate(json.loads(path.read_text()))
