"""Northstar (Tzafon Lightcone) client — implements AgentClient/AgentSession protocols.

Retries transient API errors (429, 5xx, timeouts) inside this layer with
exponential backoff so the worker / Kernel session don't get torn down on a
blip — see audit item O1.
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any, cast

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tzafon import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    Lightcone,
    RateLimitError,
)
from tzafon.types.response_create_params import Tool

from usersim.schemas import Action, AgentResponse, Observation, TurnMeta

MODEL = "tzafon.northstar-cua-fast"

_TRANSIENT = (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)


def _tools(w: int, h: int) -> list[Tool]:
    return cast(list[Tool], [{
        "type": "computer_use_preview",
        "display_width": w,
        "display_height": h,
        "environment": "browser",
    }])


def _parse_response(resp: Any, model_ms: int) -> tuple[AgentResponse, str | None]:
    actions: list[Action] = []
    reasoning: list[str] = []
    last_call_id: str | None = None

    for o in resp.output:
        if o.type == "computer_call":
            actions.append(Action(
                type=o.action.type,
                args=o.action.model_dump(exclude={"type"}),
            ))
            last_call_id = o.call_id
        elif o.type == "message":
            for c in o.content:
                if c.type in ("output_text", "text"):
                    reasoning.append(c.text)
        elif o.type == "reasoning":
            # some models emit explicit reasoning blocks
            text = getattr(o, "content", None) or getattr(o, "text", None)
            if isinstance(text, str):
                reasoning.append(text)
            elif isinstance(text, list):
                for item in text:
                    t = getattr(item, "text", None) or (item if isinstance(item, str) else None)
                    if t:
                        reasoning.append(t)

    usage = getattr(resp, "usage", None)
    cached = 0
    if usage:
        details = getattr(usage, "input_tokens_details", None)
        if details:
            cached = getattr(details, "cached_tokens", 0) or 0
    telemetry = TurnMeta(
        model_ms=model_ms,
        prompt_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
        completion_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
        cached_tokens=cached,
    )

    done = len(actions) == 0 and len(reasoning) > 0

    agent_response = AgentResponse(
        actions=actions,
        reasoning=reasoning,
        telemetry=telemetry,
        done=done,
    )
    return agent_response, last_call_id


class NorthstarSession:
    def __init__(
        self,
        client: Lightcone,
        response_id: str,
        pending_call_id: str | None,
        viewport_w: int,
        viewport_h: int,
        temperature: float = 0.7,
    ) -> None:
        self._client = client
        self._response_id = response_id
        self._pending_call_id = pending_call_id
        self._viewport_w = viewport_w
        self._viewport_h = viewport_h
        self._temperature = temperature

    async def step(self, observation: Observation) -> AgentResponse:
        call_id = self._pending_call_id
        if call_id is None:
            raise RuntimeError("No pending call_id; cannot step without a prior computer_call")

        t0 = time.monotonic()

        @retry(
            retry=retry_if_exception_type(_TRANSIENT),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
        )
        def _call():
            return self._client.responses.create(
                model=MODEL,
                previous_response_id=self._response_id,
                input=[{
                    "type": "computer_call_output",
                    "call_id": call_id,
                    "output": {
                        "type": "computer_screenshot",
                        "image_url": observation.screenshot_data_url,
                    },
                }],
                tools=_tools(self._viewport_w, self._viewport_h),
                truncation="auto",
                temperature=self._temperature,
            )

        resp = await asyncio.to_thread(_call)
        model_ms = int((time.monotonic() - t0) * 1000)
        agent_response, last_call_id = _parse_response(resp, model_ms)

        self._response_id = resp.id
        if last_call_id is not None:
            self._pending_call_id = last_call_id

        return agent_response

    async def close(self) -> None:
        pass  # stateless on Tzafon side


class NorthstarClient:
    MODEL = MODEL  # exposed so worker.read_trajectory header records the actual model

    def __init__(self, api_key: str | None = None) -> None:
        self._client = Lightcone(api_key=api_key or os.environ["TZAFON_API_KEY"])

    async def start_session(
        self,
        *,
        instruction: str,
        initial_observation: Observation,
        temperature: float = 0.7,
    ) -> tuple[NorthstarSession, AgentResponse]:
        obs = initial_observation
        t0 = time.monotonic()

        @retry(
            retry=retry_if_exception_type(_TRANSIENT),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
        )
        def _call():
            return self._client.responses.create(
                model=MODEL,
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": instruction},
                        {"type": "input_image", "image_url": obs.screenshot_data_url, "detail": "auto"},
                    ],
                }],
                tools=_tools(obs.viewport_width, obs.viewport_height),
                truncation="auto",
                temperature=temperature,
            )

        resp = await asyncio.to_thread(_call)
        model_ms = int((time.monotonic() - t0) * 1000)
        agent_response, last_call_id = _parse_response(resp, model_ms)

        session = NorthstarSession(
            client=self._client,
            response_id=resp.id,
            pending_call_id=last_call_id,
            viewport_w=obs.viewport_width,
            viewport_h=obs.viewport_height,
            temperature=temperature,
        )
        return session, agent_response
