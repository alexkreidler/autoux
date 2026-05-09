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

# Registry: name → factory(spec_dict) → AgentClient
_REGISTRY: dict[str, Callable[[dict[str, Any]], AgentClient]] = {
    "northstar": lambda spec: NorthstarClient(api_key=spec.get("api_key")),
    "claude": lambda spec: ClaudeCUAClient(api_key=spec.get("api_key")),
}

# Surfer is optional — depends on the harness in `usersim/harnesses/surfer/`,
# which itself imports anthropic + the vLLM client lazily. Register only if
# the import succeeds; everything else still works without it.
try:
    from usersim.clients.surfer import SurferClient
except ImportError:
    SurferClient = None  # type: ignore[assignment,misc]
else:
    def _surfer_factory(spec: dict[str, Any]) -> AgentClient:
        assert SurferClient is not None
        return SurferClient(
            vllm_base=spec.get("vllm_base"),
            navigator_model=spec.get("navigator_model"),
            localizer_model=spec.get("localizer_model"),
            api_key=spec.get("api_key"),
            claude_only=spec.get("claude_only", False),
            max_steps=spec.get("max_steps", 25),
        )
    _REGISTRY["surfer"] = _surfer_factory


def register(name: str, factory: Callable[[dict[str, Any]], AgentClient]) -> None:
    """Register a new agent provider. Call this from a plugin module if needed."""
    _REGISTRY[name] = factory


# Required env vars per provider — used by `preflight_keys` to fail fast
# when invoking a CLI command with a missing credential, before we spin
# up Kernel sessions / start burning rollout time.
REQUIRED_ENV: dict[str, list[str]] = {
    "northstar": ["TZAFON_API_KEY"],
    "claude": ["ANTHROPIC_API_KEY"],
    "surfer": ["ANTHROPIC_API_KEY"],  # Surfer's Navigator uses Anthropic
}


def preflight_keys(agent_name: str) -> list[str]:
    """Returns a list of missing env vars for the given agent. Empty = OK."""
    import os
    return [k for k in REQUIRED_ENV.get(agent_name, []) if not os.environ.get(k)]


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
