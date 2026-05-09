"""Concrete failure-pattern detectors.

Each detector takes a Trajectory and returns a `PatternMatch | None`. A match
means: this trajectory exhibits a specific, named friction pattern, with
evidence (which step indices triggered) and a suggestion (what the coding
agent should consider patching).

Patterns are RULE-BASED, not statistical. With N=10–100 trajectories per
iteration there isn't enough data for statistical clustering to be meaningful;
we want signal that maps 1:1 to a fixable defect. HDBSCAN over residual
trajectories (those matching no pattern) catches the long tail.

Adding a pattern: write a `detect_*` function returning PatternMatch | None,
register it in PATTERNS at the bottom.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from usersim.schemas import Step, Trajectory


@dataclass(frozen=True)
class PatternMatch:
    pattern_id: str          # e.g., "form_clears_on_submit"
    description: str         # 1-line, specific. Coding agent reads this.
    evidence_steps: list[int]  # step turns that triggered the match
    severity: str            # "high" | "medium" | "low"
    suggested_fix: str       # specific patch direction


# =============================================================================
# Pattern: form clears on submit
# =============================================================================
# Signature: type(field) → click(submit) → DOM unchanged → type(same field again).
# The "again" appears in reasoning. This is the classic validation-clears-form
# defect — the highest-leverage thing the coding agent can fix.

_RETYPE_HINTS = re.compile(
    r"\b(again|cleared|re-?enter|re-?type|disappeared|wiped|lost)\b",
    re.IGNORECASE,
)


def detect_form_clears_on_submit(traj: Trajectory) -> PatternMatch | None:
    steps = traj.steps
    if len(steps) < 4:
        return None

    evidence: list[int] = []
    for i in range(2, len(steps)):
        s = steps[i]
        prev = steps[i - 1]
        prev2 = steps[i - 2]
        if (
            s.action.type == "type"
            and prev.action.type == "click"
            and prev2.action.type == "type"
            and prev.delta.consecutive_unchanged >= 1
            and _matches_reasoning(s, _RETYPE_HINTS)
        ):
            evidence.append(s.turn)

    if not evidence:
        return None

    # Try to extract a field name from the typed text or reasoning.
    field_hint = _guess_field(steps, evidence[0])
    desc = (
        f"Form input cleared on submit — user re-entered "
        f"{field_hint or 'a field'} after validation rejected it."
    )
    return PatternMatch(
        pattern_id="form_clears_on_submit",
        description=desc,
        evidence_steps=evidence,
        severity="high",
        suggested_fix=(
            f"On validation error, persist the user's input in the {field_hint or 'rejected'} "
            f"field instead of clearing it. Show the validation message inline."
        ),
    )


def _guess_field(steps: list[Step], retype_turn: int) -> str | None:
    for s in steps[: retype_turn + 1]:
        if s.action.type == "type":
            text = s.action.args.get("text") or ""
            if re.fullmatch(r"[\d,.]+", text):
                return "income"
            if "@" in text:
                return "email"
            if re.fullmatch(r"\d{5}", text):
                return "zip code"
    return None


# =============================================================================
# Pattern: stuck on button (same coordinate, no DOM change)
# =============================================================================

def detect_stuck_on_button(traj: Trajectory, *, eps_px: int = 12) -> PatternMatch | None:
    """3+ consecutive clicks at near-identical coords with no DOM change."""
    runs: list[list[int]] = []  # list of consecutive-click groups (turn indices)
    current: list[int] = []
    last_xy: tuple[int, int] | None = None

    for s in traj.steps:
        if s.action.type != "click":
            current = []
            last_xy = None
            continue
        x = s.action.args.get("x")
        y = s.action.args.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            current = []
            last_xy = None
            continue
        if (
            s.delta.dom_changed is False
            and last_xy is not None
            and abs(x - last_xy[0]) <= eps_px
            and abs(y - last_xy[1]) <= eps_px
        ):
            current.append(s.turn)
        else:
            if len(current) >= 3:
                runs.append(current)
            current = [s.turn]
        last_xy = (x, y)
    if len(current) >= 3:
        runs.append(current)

    if not runs:
        return None

    longest = max(runs, key=len)
    bad_step = traj.steps[longest[0]]
    x = bad_step.action.args.get("x")
    y = bad_step.action.args.get("y")
    return PatternMatch(
        pattern_id="stuck_on_button",
        description=(
            f"User clicked the same point near ({x}, {y}) "
            f"{len(longest)} times with no page change."
        ),
        evidence_steps=longest,
        severity="high",
        suggested_fix=(
            f"Check the element at viewport coords ({x}, {y}). "
            f"It looks clickable to the user but produces no effect — likely a "
            f"disabled button, missing handler, or non-interactive styled element."
        ),
    )


# =============================================================================
# Pattern: dead-click storm (multiple dead clicks at varied coords)
# =============================================================================

def detect_dead_click_storm(traj: Trajectory, *, min_dead: int = 3) -> PatternMatch | None:
    dead_steps = [s for s in traj.steps if s.delta.is_dead_click]
    if len(dead_steps) < min_dead:
        return None

    coords = [
        (s.action.args.get("x"), s.action.args.get("y"))
        for s in dead_steps
        if isinstance(s.action.args.get("x"), int) and isinstance(s.action.args.get("y"), int)
    ]
    return PatternMatch(
        pattern_id="dead_click_storm",
        description=(
            f"User clicked {len(dead_steps)} times in regions with no interactive "
            f"element (sample coords: {coords[:3]})."
        ),
        evidence_steps=[s.turn for s in dead_steps],
        severity="medium",
        suggested_fix=(
            "Audit the visual hierarchy in the regions clicked: users perceived "
            "these areas as interactive (link/button styling, hover hints) but they "
            "don't fire. Either add the missing handler or reduce the affordance."
        ),
    )


# =============================================================================
# Pattern: patience exhausted (persona gave up explicitly)
# =============================================================================

_GIVE_UP = re.compile(
    r"\b(give up|giving up|forget it|done with this|too long|"
    r"different tool|I'?m out|never mind|abandon)\b",
    re.IGNORECASE,
)


def detect_patience_exhausted(traj: Trajectory) -> PatternMatch | None:
    if traj.terminal_reason != "abandoned":
        return None

    triggering: list[int] = []
    for s in traj.steps:
        if any(_GIVE_UP.search(r) for r in s.reasoning):
            triggering.append(s.turn)
    if not triggering:
        # abandonment without explicit giveup language — still real, lower confidence
        triggering = [traj.steps[-1].turn] if traj.steps else [0]

    return PatternMatch(
        pattern_id="patience_exhausted",
        description=(
            f"Persona explicitly gave up after {len(traj.steps)} steps."
        ),
        evidence_steps=triggering,
        severity="medium",
        suggested_fix=(
            "Look at the last 3 steps before abandonment — those are the friction "
            "points that broke the persona's patience. Reduce required steps or "
            "improve discoverability of the next action."
        ),
    )


# =============================================================================
# Pattern: edge-case thrashing (power user explores limits, not real friction)
# =============================================================================

def detect_edge_case_thrashing(traj: Trajectory) -> PatternMatch | None:
    if traj.terminal_reason != "max_turns":
        return None
    if len(traj.steps) < 10:
        return None
    action_types = {s.action.type for s in traj.steps}
    looks_exploratory = (
        len(action_types) >= 3
        and any(
            re.search(r"\b(edge case|combination|trying|test)\b", r, re.IGNORECASE)
            for s in traj.steps
            for r in s.reasoning
        )
    )
    if not looks_exploratory:
        return None
    return PatternMatch(
        pattern_id="edge_case_thrashing",
        description=(
            "Persona explored edge cases without hitting real friction — "
            "this is power-user behavior, not a UX defect."
        ),
        evidence_steps=[s.turn for s in traj.steps[-3:]],
        severity="low",
        suggested_fix="None. Filter this trajectory class out of friction prioritization.",
    )


# =============================================================================
# Pattern: navigation confusion (URL bouncing without progress)
# =============================================================================

_LOST = re.compile(
    r"\b(where am I|where is|how do I|wrong page|back|go back|wrong place)\b",
    re.IGNORECASE,
)


def detect_navigation_confusion(traj: Trajectory) -> PatternMatch | None:
    urls = [s.observation.page_url for s in traj.steps]
    if len(set(urls)) < 3:
        return None
    confused = [s.turn for s in traj.steps if any(_LOST.search(r) for r in s.reasoning)]
    if not confused:
        return None
    return PatternMatch(
        pattern_id="navigation_confusion",
        description=(
            f"User bounced across {len(set(urls))} URLs while expressing "
            f"confusion about location."
        ),
        evidence_steps=confused,
        severity="medium",
        suggested_fix=(
            "Add breadcrumbs or persistent step indicator. The current navigation "
            "doesn't communicate progress through the multi-step flow."
        ),
    )


# =============================================================================
# Helpers + registry
# =============================================================================

def _matches_reasoning(step: Step, pattern: re.Pattern) -> bool:
    return any(pattern.search(r) for r in step.reasoning)


PATTERNS = [
    detect_form_clears_on_submit,
    detect_stuck_on_button,
    detect_dead_click_storm,
    detect_navigation_confusion,
    detect_patience_exhausted,
    detect_edge_case_thrashing,
]


def detect_all(traj: Trajectory) -> list[PatternMatch]:
    """Run every detector against a trajectory; return all matches.

    A trajectory can match multiple patterns (e.g. form_clears + patience_exhausted).
    """
    out: list[PatternMatch] = []
    for fn in PATTERNS:
        m = fn(traj)
        if m is not None:
            out.append(m)
    return out
