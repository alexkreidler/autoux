"""Provider-agnostic agent interface.

Worker code only sees Observation/Action/AgentResponse. Provider-specific state
(OpenAI response_ids, message history, anything stateful) is hidden inside the
session. This lets us swap Northstar ↔ Holotron ↔ Claude ↔ anything without
touching worker code.
"""
from __future__ import annotations

from typing import Protocol

from usersim.schemas import AgentResponse, Observation


class AgentSession(Protocol):
    """One conversation between the worker and the agent. Stateful."""

    async def step(self, observation: Observation) -> AgentResponse:
        """Send an observation, get the agent's next response."""
        ...

    async def close(self) -> None:
        """Release any resources held by the session."""
        ...


class AgentClient(Protocol):
    """Stateless factory. One client serves many sessions."""

    async def start_session(
        self,
        *,
        instruction: str,
        initial_observation: Observation,
        temperature: float = 1.0,
    ) -> tuple[AgentSession, AgentResponse]:
        """Open a new conversation. Returns (session, first response).

        The first response is returned alongside the session so the worker can
        act on it without an extra .step() call. If first response has empty
        actions and done=False, the agent is asking for more context — worker
        should treat this as an abandonment signal.

        `temperature` is a per-persona LLM sampling temperature. Implementations
        that don't expose temperature can ignore the kwarg.
        """
        ...
