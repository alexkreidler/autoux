"""Client registry + factory.

The orchestrator (worker/runner/CLI) is provider-agnostic. All deltas between
agents (auth, wire format, action vocabulary, temperature handling, statefulness)
live inside the concrete client class. Adding a new provider = one new file +
one line in `_REGISTRY` below.
"""
from __future__ import annotations

from typing import Any, Callable

from usersim.clients.base import AgentClient
from usersim.clients.claude import ClaudeCUAClient
from usersim.clients.northstar import NorthstarClient
from usersim.clients.surfer import SurferClient

# Registry: name → factory(spec_dict) → AgentClient
_REGISTRY: dict[str, Callable[[dict[str, Any]], AgentClient]] = {
    "northstar": lambda spec: NorthstarClient(api_key=spec.get("api_key")),
    "claude": lambda spec: ClaudeCUAClient(api_key=spec.get("api_key")),
    "surfer": lambda spec: SurferClient(
        vllm_base=spec.get("vllm_base"),
        navigator_model=spec.get("navigator_model"),
        localizer_model=spec.get("localizer_model"),
        api_key=spec.get("api_key"),
        claude_only=spec.get("claude_only", False),
        max_steps=spec.get("max_steps", 25),
    ),
}


def register(name: str, factory: Callable[[dict[str, Any]], AgentClient]) -> None:
    """Register a new agent provider. Call this from a plugin module if needed."""
    _REGISTRY[name] = factory


def available() -> list[str]:
    return sorted(_REGISTRY.keys())


def get_client(spec: dict[str, Any] | str) -> AgentClient:
    """Resolve a client spec to an AgentClient.

    Spec forms:
      - "northstar"                              (string shorthand)
      - {"type": "northstar"}
      - {"type": "holotron", "endpoint": "...", "api_key": "..."}
    """
    if isinstance(spec, str):
        spec = {"type": spec}
    name = spec.get("type")
    if not name:
        raise ValueError("client spec missing 'type'")
    factory = _REGISTRY.get(name)
    if factory is None:
        raise ValueError(f"unknown agent type: {name!r}. available: {available()}")
    return factory(spec)


__all__ = [
    "AgentClient",
    "ClaudeCUAClient",
    "NorthstarClient",
    "SurferClient",
    "available",
    "get_client",
    "register",
]
