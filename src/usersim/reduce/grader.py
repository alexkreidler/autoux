"""Per-trajectory grading.

Stage 1 (cheap, every trajectory): URL/DOM match + abandonment classification +
friction event extraction from per-step delta. Pure function, deterministic.

Stage 2 (expensive, periodic): held-out LLM judge — see grade_stage2_heldout.
Hidden from coding-agent's feedback path (integrity firewall).
"""
from __future__ import annotations

from usersim.schemas import FrictionEvent, Outcome, Trajectory


def grade_stage1(traj: Trajectory) -> Outcome:
    """Trajectory → Outcome. Coding agent sees this; never Stage 2."""
    success = traj.terminal_reason in ("success_dom", "success_url")
    failure_step = None if success else _last_step_index(traj)
    failure_category = None if success else _classify_failure(traj)

    return Outcome(
        persona_id=traj.persona_id,
        task_id=traj.task_id,
        success_gameable=success,
        success_heldout=None,
        failure_step=failure_step,
        failure_category=failure_category,
        friction_events=_extract_friction_events(traj),
    )


def _last_step_index(traj: Trajectory) -> int | None:
    return len(traj.steps) - 1 if traj.steps else None


_TERMINAL_TO_CATEGORY: dict[str, str] = {
    "abandoned": "abandoned_by_persona",
    "max_turns": "max_turns_exhausted",
    "stuck": "stuck_loop",
    "timeout": "timeout",
    "error": "error",
    "agent_done": "agent_terminated_without_success",
}


def _classify_failure(traj: Trajectory) -> str:
    return _TERMINAL_TO_CATEGORY.get(traj.terminal_reason, "unknown")


def _extract_friction_events(traj: Trajectory) -> list[FrictionEvent]:
    """Pull per-step friction signals out of Step.delta."""
    events: list[FrictionEvent] = []
    for step in traj.steps:
        d = step.delta
        if d.is_dead_click:
            events.append(FrictionEvent(
                step=step.turn,
                kind="dead_click",
                detail=f"click at {step.action.args.get('x')},{step.action.args.get('y')} hit no element",
            ))
        # Mark the step where stuck-loop crossed threshold (3 unchanged in a row).
        if d.consecutive_unchanged == 3:
            events.append(FrictionEvent(
                step=step.turn,
                kind="stuck",
                detail=f"DOM unchanged for 3 turns at {step.observation.page_url}",
            ))

    if traj.terminal_reason == "timeout":
        events.append(FrictionEvent(
            step=_last_step_index(traj) or 0,
            kind="timeout",
            detail="per-turn timeout fired",
        ))
    return events


def grade_stage2_heldout(traj: Trajectory) -> bool | None:  # noqa: ARG001
    """STUB until iter-2 budget approval. Returns None so aggregator skips it.

    When wired:
      - Render trajectory as text summary + 3 keyframe screenshots (turn 0, mid, last).
      - Prompt Claude Sonnet 4.6:
          "Given persona <persona> and goal <task>, the agent took these actions
           and ended at <final_url>. Did they actually achieve the goal in a way
           a real human would consider success? Superficial signals (URL match
           without genuine completion) are NO."
      - Parse YES/NO/UNSURE; map to True/False/None.
      - Run on every Nth iteration (N=5) to control budget.
      - NEVER include result in feedback.json — only in private heldout.json.
    """
    return None
