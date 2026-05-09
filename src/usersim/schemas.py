"""Data models for the UserSim map-reduce pipeline.

Design rules:
  - Provider-agnostic. Nothing here mentions Tzafon/Kernel/OpenAI.
  - Additive evolution. Adding fields is safe; renaming is not.
  - `Feedback` is the locked contract with the coding-agent side.
  - All times are ISO8601 strings on the wire, datetimes in memory.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# =============================================================================
# Inputs to the map step
# =============================================================================

class Persona(BaseModel):
    id: str
    archetype: str
    tech_literacy: Literal["low", "medium", "high"] = "medium"
    patience_steps: int = 10
    quirks: list[str] = []
    # Extended fields — all have defaults so existing data/code is unaffected
    age_range: Literal["18-25", "26-40", "41-60", "61+"] = "26-40"
    device: Literal["desktop", "mobile", "tablet"] = "desktop"
    language_fluency: Literal["native", "proficient", "limited"] = "native"
    prior_experience: list[str] = []
    temperature: float = 0.7  # per-persona LLM temperature for the CUA model
    avatar_path: str | None = None  # relative path to generated avatar image

    def system_prompt(self, task_description: str) -> str:
        quirks = "; ".join(self.quirks) if self.quirks else "no notable quirks"
        exp = "; ".join(self.prior_experience) if self.prior_experience else "none noted"
        return (
            f"You are a real human user, not an AI. Persona: {self.archetype}. "
            f"Age range: {self.age_range}. Device: {self.device}. "
            f"Language fluency: {self.language_fluency}. "
            f"Tech literacy: {self.tech_literacy}. Quirks: {quirks}. "
            f"Prior experience with similar tasks: {exp}. "
            f"You will give up after about {self.patience_steps} unsuccessful actions. "
            f"Your goal: {task_description}. "
            f"Behave like the persona — make the kinds of mistakes this person would make. "
            f"You cannot use the browser address bar; only the page contents are interactive. "
            f"Do not narrate that you are an AI."
        )


class Task(BaseModel):
    id: str
    description: str
    success_dom: str | None = None  # CSS selector
    success_url_pattern: str | None = None  # regex
    metadata: dict[str, Any] = {}


class App(BaseModel):
    """A target web app to roll out against. Pushed by the infra teammate
    to `configs/apps/registry.jsonl` — one App per line.

    Each app owns its own tasks (so different apps can have different
    success criteria), plus optional auth credentials embedded inline so
    the agent's persona prompt knows them.
    """
    id: str                                   # slug, used in paths
    name: str                                 # human display name
    target_url: str                           # base URL; tasks may extend
    auth: dict[str, str] | None = None        # {"username": "...", "password": "..."}
    notes: str | None = None                  # one-liner from teammate
    tasks: list[Task] = []                    # at least one for the app to be runnable
    metadata: dict[str, Any] = {}


# =============================================================================
# Per-turn primitives (consumed by clients, produced into Trajectories)
# =============================================================================

class Action(BaseModel):
    """What an agent decided to do this turn. Provider-neutral.

    Type names follow the OpenAI computer-use schema (the de-facto convention,
    also used by Tzafon Northstar and Anthropic): click, double_click, move,
    drag, type, keypress, scroll, wait, screenshot, point_and_type, mouse_down,
    mouse_up, key_down, key_up.

    `args` is loose because each type has its own shape (x/y, text, keys, path,
    button, scroll_x/y, ms, ...). Worker dispatches on `type` and reads `args`.
    """
    type: str
    args: dict[str, Any] = {}


class Observation(BaseModel):
    """What an agent sees on a turn. Worker produces; client consumes."""
    screenshot_data_url: str  # data:image/png;base64,...
    viewport_width: int
    viewport_height: int
    page_url: str | None = None
    page_title: str | None = None
    extras: dict[str, Any] = {}  # provider-specific (e.g., DOM tree, accessibility tree)


class TurnMeta(BaseModel):
    """Cost/latency for a single agent call. Surfaced by every AgentClient impl."""
    model_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0


class AgentResponse(BaseModel):
    """One round-trip's worth of model output."""
    actions: list[Action] = []  # empty + done=True means the agent considers itself finished
    reasoning: list[str] = []   # chain-of-thought / message text the model emitted
    telemetry: TurnMeta = Field(default_factory=TurnMeta)
    done: bool = False          # explicit terminal signal from the model


# =============================================================================
# Per-step record (worker output, one per executed action)
# =============================================================================

class StepObservation(BaseModel):
    """Page state captured AFTER the action ran."""
    page_url: str
    page_title: str
    dom_hash: str | None = None
    screenshot_path: str | None = None  # thumbnail jpg, relative to run out_dir


class StepDelta(BaseModel):
    """What changed because of this step. Computed by the worker, used by the grader."""
    dom_changed: bool = False
    url_changed: bool = False
    is_dead_click: bool = False  # click hit no interactive element
    consecutive_unchanged: int = 0  # rolling count for stuck-loop detection


class StepTiming(BaseModel):
    model_ms: int = 0  # time spent waiting on the agent
    exec_ms: int = 0   # time spent executing the action + settle
    total_ms: int = 0


class Step(BaseModel):
    turn: int
    started_at: datetime
    ended_at: datetime

    action: Action
    reasoning: list[str] = []

    observation: StepObservation
    delta: StepDelta = Field(default_factory=StepDelta)
    timing: StepTiming = Field(default_factory=StepTiming)
    tokens: TurnMeta = Field(default_factory=TurnMeta)

    notes: list[str] = []  # free-form per-step diagnostics (e.g., "retried 1x", "playwright timeout")


# =============================================================================
# Trajectory (one (persona, task) cell)
# =============================================================================

TerminalReason = Literal[
    "success_dom",   # success_dom selector matched
    "success_url",   # success_url_pattern matched
    "agent_done",    # agent emitted done=True
    "max_turns",     # turn cap hit
    "abandoned",     # persona patience exceeded
    "stuck",         # same DOM hash N turns in a row
    "timeout",       # per-turn timeout fired
    "error",         # exception
]


class Trajectory(BaseModel):
    persona_id: str
    task_id: str
    target_url: str
    target_commit: str = "unknown"

    started_at: datetime
    ended_at: datetime

    steps: list[Step]

    final_url: str
    final_title: str
    terminal_reason: TerminalReason
    error: str | None = None

    # Provider artifacts (optional, for replay + debugging)
    browser_session_id: str | None = None
    replay_path: str | None = None  # local path to mp4, relative to run out_dir
    live_view_url: str | None = None  # only meaningful while running


# =============================================================================
# Reduce step outputs
# =============================================================================

class FrictionEvent(BaseModel):
    step: int
    kind: Literal["stuck", "dead_click", "wrong_field", "validation_error", "loop", "timeout"]
    detail: str


class Outcome(BaseModel):
    persona_id: str
    task_id: str
    success_gameable: bool
    success_heldout: bool | None = None
    failure_step: int | None = None
    failure_category: str | None = None
    friction_events: list[FrictionEvent] = []


class FrictionCluster(BaseModel):
    id: str
    description: str
    n_affected: int
    example_persona_ids: list[str]
    evidence_screenshots: list[str] = []
    suggested_dom_targets: list[str] = []
    reasoning_excerpts: list[str] = []
    suggested_fix: str | None = None  # actionable patch direction for the coding agent


class Metrics(BaseModel):
    success_rate_gameable: float
    success_rate_heldout: float | None = None
    delta_gameable_vs_heldout: float | None = None  # the reward-hacking signal
    median_steps_to_success: float | None = None
    abandonment_rate: float
    errors_per_iteration: int


class Regression(BaseModel):
    description: str
    first_seen_iter: int


class PersonaSegment(BaseModel):
    persona_id: str
    n_attempts: int
    success_rate: float
    avg_steps: float
    avg_tokens: int
    terminal_reasons: dict[str, int]
    distinctive_quotes: list[str]
    distinctive_actions: list[str]


# =============================================================================
# THE CONTRACT WITH THE CODING-AGENT SIDE — DO NOT BREAK
# =============================================================================

class Feedback(BaseModel):
    """The only artifact the coding-agent side reads. Adding fields is safe; do
    not rename or retype existing ones without coordinating with teammate."""
    iteration: int
    target_commit: str
    n_trajectories: int
    metrics: Metrics
    top_friction_clusters: list[FrictionCluster] = []
    regressions_vs_prev: list[Regression] = []
    raw_trajectory_dir: str = Field(description="relative path to per-trajectory JSONL files")
    by_persona: list[PersonaSegment] = []
    persona_divergence_score: float = 0.0
    persona_specific_findings: list[str] = []


# =============================================================================
# Live registry payload (consumed by the streaming dashboard)
# =============================================================================

class ActiveRollout(BaseModel):
    """One row in the live registry. The web grid renders one tile per row."""
    # identity
    browser_session_id: str
    persona_id: str
    task_id: str
    target_url: str
    started_at: datetime

    # streaming view
    live_view_url: str

    # rolling state, updated each turn
    current_turn: int = 0
    last_action: Action | None = None
    last_reasoning: str | None = None
    current_url: str | None = None
    current_title: str | None = None
    current_dom_hash: str | None = None
    consecutive_unchanged: int = 0

    # rolling cost
    cumulative_tokens: TurnMeta = Field(default_factory=TurnMeta)
    cumulative_ms: int = 0

    # live verdict (flips when grader detects success/abandonment)
    stage1_status: Literal["running", "success_dom", "success_url", "abandoned", "stuck", "error"] = "running"

    # heartbeat — registry.update() stamps this on every patch. Prune-loop
    # uses it to spot ghost rows whose parent process died without cleanup.
    last_step_at: datetime = Field(default_factory=datetime.now)
