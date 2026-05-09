"""Surfer Harness v2 — Hybrid browser agent benchmark.

Re-exports the public API so callers can write:
    from usersim.harnesses.surfer import Config, ClaudeClient, HoloLocalizer, ...
"""
from usersim.harnesses.surfer.harness import (
    CircuitBreaker,
    ClaudeClient,
    ClaudeLocalizer,
    Config,
    EASY_TASKS,
    HARD_TASKS,
    HoloLocalizer,
    KernelBrowser,
    LOCALIZER_PROMPT_TEMPLATE,
    SCHEMA_REMINDER,
    StepResult,
    Task,
    TaskResult,
    Tracer,
    VALIDATOR_PROMPT,
    make_navigator_prompt,
    run_benchmark,
    run_task,
)

__all__ = [
    "CircuitBreaker",
    "ClaudeClient",
    "ClaudeLocalizer",
    "Config",
    "EASY_TASKS",
    "HARD_TASKS",
    "HoloLocalizer",
    "KernelBrowser",
    "LOCALIZER_PROMPT_TEMPLATE",
    "SCHEMA_REMINDER",
    "StepResult",
    "Task",
    "TaskResult",
    "Tracer",
    "VALIDATOR_PROMPT",
    "make_navigator_prompt",
    "run_benchmark",
    "run_task",
]
