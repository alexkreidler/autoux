"""Claude (Anthropic) computer-use client — implements AgentClient/AgentSession.

Targets Claude Sonnet 4.6's `computer_20241022` tool. Stateful conversation:
the session keeps the running `messages` list, appending one tool_result per
turn and asking for the next completion.

Why this exists: Northstar (Tzafon) emits actions but almost no reasoning
text (~9% coverage on real TaxCaster runs). Claude computer-use produces
verbose reasoning by default, unblocking text-keyed pattern detectors and
giving the held-out judge actual narrative to score against.

Cost is ~10× Northstar per token, but trajectories are ~5 turns so the
absolute cost is still pennies per rollout.
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, cast

from anthropic import (
    Anthropic,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from usersim.schemas import Action, AgentResponse, Observation, TurnMeta

MODEL = "claude-sonnet-4-6"
BETAS = ["computer-use-2025-01-24"]
MAX_TOKENS = 4096

_TRANSIENT = (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError, APIStatusError)


# =============================================================================
# Tool schema + action mapping
# =============================================================================

def _tools(w: int, h: int) -> list[dict[str, Any]]:
    return [{
        "type": "computer_20250124",
        "name": "computer",
        "display_width_px": w,
        "display_height_px": h,
        "display_number": 1,
    }]


def _claude_to_action(input_data: dict[str, Any]) -> Action | None:
    """Translate one Claude tool_use input → our provider-neutral Action.

    Claude's action vocabulary (computer_20250124) overlaps with OpenAI's but
    uses different names; we normalize to the OpenAI convention our worker
    already dispatches on.
    """
    a = input_data.get("action") or ""
    coord = input_data.get("coordinate") or [0, 0]
    x, y = (coord[0], coord[1]) if len(coord) >= 2 else (0, 0)

    if a == "left_click":
        return Action(type="click", args={"button": "left", "x": x, "y": y})
    if a == "right_click":
        return Action(type="click", args={"button": "right", "x": x, "y": y})
    if a == "middle_click":
        return Action(type="click", args={"button": "middle", "x": x, "y": y})
    if a == "double_click":
        return Action(type="double_click", args={"x": x, "y": y})
    if a == "triple_click":
        # No native triple_click; fire two double_clicks. Worker handles type.
        return Action(type="double_click", args={"x": x, "y": y})
    if a == "mouse_move":
        return Action(type="move", args={"x": x, "y": y})
    if a == "left_mouse_down":
        return Action(type="mouse_down", args={"button": "left"})
    if a == "left_mouse_up":
        return Action(type="mouse_up", args={"button": "left"})
    if a == "left_click_drag":
        sx, sy = input_data.get("start_coordinate", [0, 0])[:2]
        return Action(type="drag", args={"path": [{"x": sx, "y": sy}, {"x": x, "y": y}]})
    if a == "type":
        return Action(type="type", args={"text": input_data.get("text", "")})
    if a == "key":
        # Claude uses xdotool key syntax: "ctrl+l", "Return", "Tab"
        text = input_data.get("text", "")
        keys = [k for k in text.split("+") if k]
        return Action(type="keypress", args={"keys": keys})
    if a == "scroll":
        direction = input_data.get("scroll_direction", "down")
        amount = int(input_data.get("scroll_amount", 3))
        dy = amount * 100 * (1 if direction == "down" else -1) if direction in ("up", "down") else 0
        dx = amount * 100 * (1 if direction == "right" else -1) if direction in ("left", "right") else 0
        return Action(type="scroll", args={"x": x, "y": y, "scroll_x": dx, "scroll_y": dy})
    if a == "wait":
        return Action(type="wait", args={"ms": int(input_data.get("duration", 1)) * 1000})
    if a in ("screenshot", "cursor_position"):
        return Action(type="screenshot", args={})
    return None  # unknown — worker logs and continues


# =============================================================================
# Session
# =============================================================================

class ClaudeCUASession:
    def __init__(
        self,
        client: Anthropic,
        messages: list[dict[str, Any]],
        last_assistant: dict[str, Any],
        pending_tool_use_id: str | None,
        viewport_w: int,
        viewport_h: int,
        temperature: float,
    ) -> None:
        self._client = client
        self._messages = messages
        self._last_assistant = last_assistant
        self._pending_tool_use_id = pending_tool_use_id
        self._viewport_w = viewport_w
        self._viewport_h = viewport_h
        self._temperature = temperature

    async def step(self, observation: Observation) -> AgentResponse:
        if self._pending_tool_use_id is None:
            raise RuntimeError("No pending tool_use_id; agent did not request a tool last turn")

        # Append the assistant turn from last response, then the tool_result.
        self._messages.append(self._last_assistant)
        self._messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": self._pending_tool_use_id,
                "content": [_image_block(observation.screenshot_data_url)],
            }],
        })

        t0 = time.monotonic()
        resp = await asyncio.to_thread(
            _call_with_retries,
            self._client,
            self._messages,
            self._viewport_w,
            self._viewport_h,
            self._temperature,
        )
        model_ms = int((time.monotonic() - t0) * 1000)

        agent_response, last_assistant, last_tool_id = _parse_response(resp, model_ms)
        self._last_assistant = last_assistant
        self._pending_tool_use_id = last_tool_id
        return agent_response

    async def close(self) -> None:
        pass


# =============================================================================
# Client (factory)
# =============================================================================

class ClaudeCUAClient:
    MODEL = MODEL  # exposed so worker provenance records the actual model

    def __init__(self, api_key: str | None = None) -> None:
        self._client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    async def start_session(
        self,
        *,
        instruction: str,
        initial_observation: Observation,
        temperature: float = 1.0,
    ) -> tuple[ClaudeCUASession, AgentResponse]:
        obs = initial_observation
        messages: list[dict[str, Any]] = [{
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                _image_block(obs.screenshot_data_url),
            ],
        }]

        t0 = time.monotonic()
        resp = await asyncio.to_thread(
            _call_with_retries,
            self._client,
            messages,
            obs.viewport_width,
            obs.viewport_height,
            temperature,
        )
        model_ms = int((time.monotonic() - t0) * 1000)

        agent_response, last_assistant, last_tool_id = _parse_response(resp, model_ms)
        session = ClaudeCUASession(
            client=self._client,
            messages=messages,
            last_assistant=last_assistant,
            pending_tool_use_id=last_tool_id,
            viewport_w=obs.viewport_width,
            viewport_h=obs.viewport_height,
            temperature=temperature,
        )
        return session, agent_response


# =============================================================================
# Internals
# =============================================================================

@retry(
    retry=retry_if_exception_type(_TRANSIENT),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call_with_retries(
    client: Anthropic,
    messages: list[dict[str, Any]],
    w: int,
    h: int,
    temperature: float,
) -> Any:
    # Anthropic SDK types `messages` and `tools` as TypedDicts; we build dicts.
    # Runtime accepts dicts; cast to satisfy pyright without changing wire shape.
    return client.beta.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        tools=cast(Any, _tools(w, h)),
        messages=cast(Any, messages),
        betas=cast(Any, BETAS),
        temperature=temperature,
    )


def _image_block(screenshot_data_url: str) -> dict[str, Any]:
    """Convert our `data:image/png;base64,...` URI into Anthropic's image block."""
    if not screenshot_data_url.startswith("data:"):
        raise ValueError(f"unexpected screenshot URL form: {screenshot_data_url[:32]}...")
    head, b64 = screenshot_data_url.split(",", 1)
    media_type = head.split(";")[0].split(":")[1]  # "image/png"
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": b64},
    }


def _parse_response(resp: Any, model_ms: int) -> tuple[AgentResponse, dict[str, Any], str | None]:
    """Returns (AgentResponse, raw_assistant_message_for_session, last_tool_use_id)."""
    actions: list[Action] = []
    reasoning: list[str] = []
    last_tool_id: str | None = None
    raw_blocks: list[dict[str, Any]] = []

    for block in resp.content:
        if block.type == "text":
            reasoning.append(block.text)
            raw_blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            mapped = _claude_to_action(block.input)
            if mapped is not None:
                actions.append(mapped)
            last_tool_id = block.id
            raw_blocks.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })

    usage = getattr(resp, "usage", None)
    telemetry = TurnMeta(
        model_ms=model_ms,
        prompt_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
        completion_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
        cached_tokens=(
            getattr(usage, "cache_read_input_tokens", 0) or 0
            if usage else 0
        ),
    )

    # Claude says "I'm done" by emitting only text + stop_reason="end_turn", no tool_use.
    done = (
        getattr(resp, "stop_reason", None) == "end_turn"
        and not actions
    )

    agent_response = AgentResponse(
        actions=actions,
        reasoning=reasoning,
        telemetry=telemetry,
        done=done,
    )
    last_assistant = {"role": "assistant", "content": raw_blocks}
    return agent_response, last_assistant, last_tool_id
