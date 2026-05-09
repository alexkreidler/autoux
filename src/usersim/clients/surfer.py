"""Surfer Harness client — implements AgentClient/AgentSession protocols.

Wraps the Navigator (Claude) + Localizer (Holo3 on vLLM) pipeline from the
benchmarking harness as a UserSim agent.  The orchestrator owns the browser;
we only receive screenshots and return actions in the UserSim vocabulary.

Architecture:
  Navigator: Claude Opus (Anthropic API) — reasoning, planning, action decisions
  Localizer: Holo3-35B-A3B (vLLM on B200 via Cloudflare Tunnel) — pixel-level grounding
  Fallback:  Claude vision for localization when vLLM is unreachable

vLLM endpoint: defaults to https://gpu.alexkreidler.com (Cloudflare Tunnel →
VAST.ai B200 in Japan). Override with VLLM_BASE env var or spec["vllm_base"].
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from usersim.schemas import Action, AgentResponse, Observation, TurnMeta

# ---------------------------------------------------------------------------
# Import surfer harness components from the benchmarking directory.
# ---------------------------------------------------------------------------
_BENCHMARKING_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "benchmarking")
)
if _BENCHMARKING_DIR not in sys.path:
    sys.path.insert(0, _BENCHMARKING_DIR)

from surfer_harness import (  # noqa: E402
    Config as SurferConfig,
    ClaudeClient,
    HoloLocalizer,
    ClaudeLocalizer,
    CircuitBreaker,
    make_navigator_prompt,
    SCHEMA_REMINDER,
)

# Default vLLM base — Cloudflare Tunnel to VAST.ai B200 in Japan.
_DEFAULT_VLLM_BASE = "https://gpu.alexkreidler.com"


# ---------------------------------------------------------------------------
# Action mapping: surfer JSON → UserSim Action (Pydantic)
# ---------------------------------------------------------------------------

def _map_surfer_action(
    action_data: dict[str, Any],
    px: int | None,
    py: int | None,
) -> list[Action]:
    """Convert a surfer harness action dict to UserSim Action(s)."""
    action = action_data.get("action", "unknown")
    actions: list[Action] = []

    if action == "click":
        actions.append(Action(type="click", args={
            "x": px or 0, "y": py or 0, "button": "left",
        }))

    elif action == "fill":
        # fill = click target + select-all + type text (+ optional Enter)
        if px is not None and py is not None:
            actions.append(Action(type="click", args={
                "x": px, "y": py, "button": "left",
            }))
        actions.append(Action(type="keypress", args={"keys": ["ctrl+a"]}))
        actions.append(Action(type="type", args={"text": action_data.get("text", "")}))
        if action_data.get("press_enter"):
            actions.append(Action(type="keypress", args={"keys": ["Enter"]}))

    elif action == "type":
        actions.append(Action(type="type", args={"text": action_data.get("text", "")}))
        if action_data.get("press_enter"):
            actions.append(Action(type="keypress", args={"keys": ["Enter"]}))

    elif action == "scroll":
        direction = action_data.get("direction", "down")
        scroll_y = -600 if direction == "up" else 600
        actions.append(Action(type="scroll", args={
            "x": 640, "y": 400, "scroll_x": 0, "scroll_y": scroll_y,
        }))

    elif action == "go_back":
        actions.append(Action(type="keypress", args={"keys": ["Alt+Left"]}))

    elif action == "navigate":
        url = action_data.get("text", "")
        actions.append(Action(type="keypress", args={"keys": ["ctrl+l"]}))
        actions.append(Action(type="type", args={"text": url}))
        actions.append(Action(type="keypress", args={"keys": ["Enter"]}))

    elif action == "key_press":
        key = action_data.get("text", "Enter")
        key = key.replace("Control+", "ctrl+")
        actions.append(Action(type="keypress", args={"keys": [key]}))

    elif action == "wait":
        actions.append(Action(type="wait", args={"ms": 2000}))

    elif action in ("new_tab", "switch_tab", "close_tab"):
        # Tab management — not yet in UserSim action vocabulary.
        # Degrade gracefully: screenshot request so the orchestrator retries.
        actions.append(Action(type="screenshot", args={}))

    elif action == "answer":
        pass  # terminal — handled by caller

    return actions


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class SurferSession:
    """Wraps the Navigator + Localizer pipeline as a stateful session."""

    def __init__(
        self,
        config: SurferConfig,
        claude: ClaudeClient,
        localizer: HoloLocalizer | ClaudeLocalizer,
        system_prompt: str,
        temperature: float,
    ) -> None:
        self._config = config
        self._claude = claude
        self._localizer = localizer
        self._system_prompt = system_prompt
        self._temperature = temperature

        self._messages: list[dict[str, Any]] = []
        self._circuit_breaker = CircuitBreaker(config.circuit_breaker_threshold)
        self._step_num = 0
        self._budget_warning_sent = False

    @staticmethod
    def _extract_b64(obs: Observation) -> str:
        s = obs.screenshot_data_url
        if s.startswith("data:"):
            return s.split(",", 1)[1]
        return s

    def _build_messages(self, img_b64: str) -> list[dict[str, Any]]:
        img_content: list[dict[str, Any]] = [
            {"type": "text", "text": f"[Step {self._step_num}] Current browser screenshot:"},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": img_b64,
            }},
            {"type": "text", "text": SCHEMA_REMINDER},
        ]
        messages = self._messages + [{"role": "user", "content": img_content}]

        # Evict old images beyond max_images_in_context
        img_count = 0
        for i in range(len(messages) - 1, -1, -1):
            content = messages[i].get("content")
            if isinstance(content, list):
                has_img = any(
                    isinstance(c, dict) and c.get("type") == "image"
                    for c in content
                )
                if has_img:
                    img_count += 1
                    if img_count > self._config.max_images_in_context:
                        messages[i] = {
                            "role": messages[i]["role"],
                            "content": "[previous screenshot evicted]",
                        }
        return messages

    async def step(self, observation: Observation) -> AgentResponse:
        self._step_num += 1
        img_b64 = self._extract_b64(observation)

        # Budget warning
        max_steps = self._config.max_steps
        if not self._budget_warning_sent and self._step_num / max_steps >= self._config.budget_warning_pct:
            self._budget_warning_sent = True
            remaining = max_steps - self._step_num
            self._messages.append({
                "role": "user",
                "content": f"Budget warning: {self._step_num}/{max_steps} steps used, "
                           f"{remaining} remaining. Wrap up and report your answer now.",
            })

        # --- Call Claude Navigator ---
        messages = self._build_messages(img_b64)
        total_prompt = 0
        total_completion = 0

        start = time.perf_counter()
        try:
            raw, nav_elapsed, usage = await asyncio.to_thread(
                self._claude.navigate, self._system_prompt, messages
            )
        except Exception as e:
            return AgentResponse(
                actions=[],
                reasoning=[f"Navigator error: {e}"],
                telemetry=TurnMeta(
                    model_ms=int((time.perf_counter() - start) * 1000),
                ),
                done=False,
            )

        total_prompt += usage.get("prompt_tokens", 0)
        total_completion += usage.get("completion_tokens", 0)

        # --- Parse navigator response ---
        action_data: dict[str, Any] | None = None
        try:
            action_data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r'\{[^{}]*"action"[^{}]*\}', raw, re.DOTALL)
            if match:
                try:
                    action_data = json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        if not action_data or "action" not in action_data:
            # Parse failure — inject retry prompt
            self._messages.append({"role": "user", "content": [
                {"type": "text", "text": f"[Step {self._step_num}] Current browser screenshot:"},
                {"type": "image", "source": {
                    "type": "base64", "media_type": "image/png", "data": img_b64,
                }},
                {"type": "text", "text": SCHEMA_REMINDER},
            ]})
            self._messages.append({"role": "assistant", "content": raw})
            self._messages.append({"role": "user", "content":
                'Your response was not valid JSON. Respond with: {"thought": "...", "action": "...", ...}'
            })
            return AgentResponse(
                actions=[Action(type="screenshot", args={})],
                reasoning=[f"Parse failure, retrying: {raw[:200]}"],
                telemetry=TurnMeta(
                    model_ms=int(nav_elapsed * 1000),
                    prompt_tokens=total_prompt,
                    completion_tokens=total_completion,
                ),
                done=False,
            )

        action = action_data.get("action", "unknown")
        thought = action_data.get("thought", "")

        # Update conversation history
        self._messages.append({"role": "user", "content": [
            {"type": "text", "text": f"[Step {self._step_num}] Current browser screenshot:"},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": img_b64,
            }},
            {"type": "text", "text": SCHEMA_REMINDER},
        ]})
        self._messages.append({"role": "assistant", "content": json.dumps(action_data)})

        # --- Circuit breaker ---
        if self._circuit_breaker.check(action_data):
            self._messages.append({
                "role": "user",
                "content": self._circuit_breaker.redirect_message,
            })
            return AgentResponse(
                actions=[Action(type="screenshot", args={})],
                reasoning=[thought, "Circuit breaker tripped — retrying with different approach"],
                telemetry=TurnMeta(
                    model_ms=int(nav_elapsed * 1000),
                    prompt_tokens=total_prompt,
                    completion_tokens=total_completion,
                ),
                done=False,
            )

        # --- Handle answer (terminal) ---
        if action == "answer":
            return AgentResponse(
                actions=[],
                reasoning=[thought, f"ANSWER: {action_data.get('text', '')}"],
                telemetry=TurnMeta(
                    model_ms=int(nav_elapsed * 1000),
                    prompt_tokens=total_prompt,
                    completion_tokens=total_completion,
                ),
                done=True,
            )

        # --- Localize if needed ---
        px, py = None, None
        loc_elapsed = 0.0
        if action in ("click", "fill"):
            element_desc = action_data.get("element", "the element")
            try:
                px, py, loc_elapsed = await asyncio.to_thread(
                    self._localizer.localize, img_b64, element_desc
                )
            except Exception:
                try:
                    fallback = ClaudeLocalizer(self._claude, self._config)
                    px, py, loc_elapsed = await asyncio.to_thread(
                        fallback.localize, img_b64, element_desc
                    )
                except Exception:
                    px = observation.viewport_width // 2
                    py = observation.viewport_height // 2

        # --- Map to UserSim actions ---
        actions = _map_surfer_action(action_data, px, py)

        total_ms = int((nav_elapsed + loc_elapsed) * 1000)

        # Add action result to context for next turn
        if actions:
            desc = f"{action} executed"
            if px is not None:
                desc = f"{action} at ({px}, {py})"
            self._messages.append({
                "role": "user",
                "content": f"Action result: {desc}",
            })

        return AgentResponse(
            actions=actions,
            reasoning=[thought] if thought else [],
            telemetry=TurnMeta(
                model_ms=total_ms,
                prompt_tokens=total_prompt,
                completion_tokens=total_completion,
            ),
            done=False,
        )

    async def close(self) -> None:
        self._messages.clear()


# ---------------------------------------------------------------------------
# Client (factory)
# ---------------------------------------------------------------------------

class SurferClient:
    """AgentClient that wraps the Surfer Harness multi-model pipeline.

    Spec keys (all optional):
      - vllm_base:        vLLM endpoint URL (default: https://gpu.alexkreidler.com)
      - navigator_model:  Claude model for reasoning (default: claude-opus-4-7)
      - localizer_model:  vLLM model for grounding (default: Hcompany/Holo3-35B-A3B)
      - api_key:          Anthropic API key (default: ANTHROPIC_API_KEY env var)
      - claude_only:      Skip vLLM, use Claude for localization too (default: false)
      - max_steps:        Step budget for the navigator (default: 25)
    """

    MODEL = "surfer-v2"  # exposed so worker provenance records a stable identifier

    def __init__(
        self,
        vllm_base: str | None = None,
        navigator_model: str | None = None,
        localizer_model: str | None = None,
        api_key: str | None = None,
        claude_only: bool = False,
        max_steps: int = 25,
    ) -> None:
        self._config = SurferConfig(
            anthropic_api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
            navigator_model=navigator_model or "claude-opus-4-7",
            vllm_base=vllm_base or os.environ.get("VLLM_BASE", _DEFAULT_VLLM_BASE),
            localizer_model=localizer_model or os.environ.get(
                "LOCALIZER_MODEL", "Hcompany/Holo3-35B-A3B"
            ),
            claude_only=claude_only,
            max_steps=max_steps,
        )

        self._claude = ClaudeClient(self._config)

        # Try Holo localizer; fall back to Claude if vLLM is unreachable.
        if not claude_only:
            holo = HoloLocalizer(self._config)
            if holo.health_check():
                self._localizer: HoloLocalizer | ClaudeLocalizer = holo
            else:
                self._localizer = ClaudeLocalizer(self._claude, self._config)
                self._config.claude_only = True
        else:
            self._localizer = ClaudeLocalizer(self._claude, self._config)
            self._config.claude_only = True

    async def start_session(
        self,
        *,
        instruction: str,
        initial_observation: Observation,
        temperature: float = 1.0,
    ) -> tuple[SurferSession, AgentResponse]:
        system_prompt = make_navigator_prompt(
            instruction,
            initial_observation.viewport_width,
            initial_observation.viewport_height,
        )

        session = SurferSession(
            config=self._config,
            claude=self._claude,
            localizer=self._localizer,
            system_prompt=system_prompt,
            temperature=temperature,
        )

        first_response = await session.step(initial_observation)
        return session, first_response
