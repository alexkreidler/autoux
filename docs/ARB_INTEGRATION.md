# Plugging your CUA harness into UserSim

We have a working orchestrator that drives Kernel browsers via a CUA agent
and produces graded trajectories. Two reference implementations exist:
**Northstar** (Tzafon Lightcone, OpenAI-Responses-API-compat) and **Claude
computer-use** (Anthropic Messages API). We want yours to be the third.

**Two integration paths.** Pick whichever is less work on your end.

| Path | You do | We do |
|---|---|---|
| **A — Conform to AgentClient Protocol** | Expose an HTTP/SDK endpoint that returns next actions given a screenshot. Answer the questionnaire below. | Write a thin client class that wraps your endpoint. ~150 LOC, takes 1–2h. |
| **B — Produce trajectory JSONLs directly** | Run your own loop against Kernel (or any browser provider). Emit one JSONL per trajectory in our wire format. | Drop your `runs/iter_N/trajectories/*.jsonl` into our reducer. Zero code on our side. |

Path A gives you the live registry, replay recording, retry+cleanup, and
runs alongside Northstar/Claude in head-to-head iterations. Path B is fewer
moving parts but you reimplement the loop.

---

## Path A — AgentClient Protocol

The orchestrator only sees this Protocol (`src/usersim/clients/base.py`):

```python
class AgentClient(Protocol):
    async def start_session(
        self,
        *,
        instruction: str,                       # persona system prompt
        initial_observation: Observation,       # first screenshot + viewport
        temperature: float = 1.0,
    ) -> tuple[AgentSession, AgentResponse]: ...

class AgentSession(Protocol):
    async def step(self, observation: Observation) -> AgentResponse: ...
    async def close(self) -> None: ...
```

`Observation` (worker → you):
```python
class Observation(BaseModel):
    screenshot_data_url: str   # "data:image/png;base64,iVBOR..."
    viewport_width: int        # default 1280
    viewport_height: int       # default 800
    page_url: str | None
    page_title: str | None
    extras: dict[str, Any]     # provider-specific (DOM tree, a11y tree, ...)
```

`AgentResponse` (you → worker):
```python
class AgentResponse(BaseModel):
    actions: list[Action]      # next actions to execute, in order
    reasoning: list[str]       # any chain-of-thought / message text
    telemetry: TurnMeta        # tokens + latency for this call
    done: bool                 # True ⇒ agent considers the task complete

class Action(BaseModel):
    type: str                  # see action vocabulary below
    args: dict[str, Any]       # type-specific shape

class TurnMeta(BaseModel):
    model_ms: int              # wall-clock you spent computing the response
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int = 0
    cost_usd: float = 0.0
```

### Action vocabulary (OpenAI computer-use convention)

We dispatch on `Action.type` in `src/usersim/map/worker.py:_execute_action`.
If your model emits a different vocabulary, you map inside your client.
For reference, Claude's `_claude_to_action` in `src/usersim/clients/claude.py`
shows the translation pattern.

| `type` | required `args` |
|---|---|
| `click` | `x: int, y: int, button: "left"\|"right"\|"middle"` |
| `double_click` | `x: int, y: int` |
| `move` | `x: int, y: int` |
| `drag` | `path: [{"x", "y"}, ...]` |
| `type` | `text: str` |
| `keypress` | `keys: list[str]` (e.g. `["Tab", "Enter"]`, `["ctrl+l"]`) |
| `scroll` | `x: int, y: int, scroll_x: int, scroll_y: int` |
| `wait` | `ms: int` |
| `screenshot` | `{}` (no-op; we screenshot every turn anyway) |
| `mouse_down` / `mouse_up` | `button: "left"\|...` |
| `key_down` / `key_up` | `key: str` |

Unknown types are logged and skipped. Coordinates are **pixel space** of the
viewport you were given in `Observation.viewport_width/height`.

### Termination

- **You signal done:** emit `actions=[]` and `done=True`. Worker exits with
  `terminal_reason="agent_done"`.
- **You give up implicitly:** emit `actions=[]` and `done=False`. Worker
  exits with `terminal_reason="abandoned"` (treated as failure).
- **You loop forever:** worker enforces `max_turns` (default 20), patience
  cutoff per persona, stuck detection (3 consecutive turns no DOM change),
  per-turn timeout (60s).

### Reference impls to read first

- `src/usersim/clients/northstar.py` (~150 LOC). OpenAI-Responses-API style:
  server-side state via `previous_response_id`, dict-shaped tool results.
- `src/usersim/clients/claude.py` (~250 LOC). Anthropic Messages API style:
  client-side state, full message history each call, tool_use/tool_result blocks.

Each handles auth, retry-with-backoff (`tenacity` on transient errors),
session state, action mapping, and telemetry parsing. ~150–250 LOC end-to-end.

### What we need from you (questionnaire)

Answer these and we'll write the client:

1. **Endpoint shape** — REST URL? Streaming? Path/method?
2. **Auth** — header / bearer / none / signed?
3. **Wire format** — request body schema (JSON example) and response body schema (JSON example with all fields you emit, even optional ones).
4. **Statefulness** — do you keep server-side conversation state (we send a session id / `previous_response_id`), or do we ship full history each turn?
5. **Action vocabulary** — what action types do you emit? Send us the exhaustive list with the args shape per type.
6. **Coordinates** — pixel space or normalized? Origin top-left?
7. **Screenshot intake** — base64 data URI in the body? File upload? Pre-uploaded by URL? Max image size?
8. **Reasoning text** — do you emit chain-of-thought / messages alongside actions? Where in the response payload? (Northstar emits 9% of the time on real runs; Claude emits ~100%. Either is fine, but tell us.)
9. **Termination** — how does your model signal "I'm done"? `stop_reason`? Empty action list? Special action? An `is_complete` flag?
10. **Telemetry** — does your response include token counts (input/output/cached)? Per-call latency? Cost? If not, we'll measure wall-clock on our side.
11. **Streaming** — SSE? Single response? If SSE, what event types?
12. **Error model** — HTTP status codes? Retry-After header? Transient vs permanent classification?
13. **Rate limits** — concurrent sessions? RPS? Token-budget? We default to 5–20 concurrent rollouts; tell us where you cap.
14. **Model identifier** — what string should appear in trajectory headers as `agent_model`?

Optional but useful:
- An OpenAI-compatible `/v1/responses` or `/v1/chat/completions` shim. If you have that, we can probably point Northstar's client at your endpoint with a one-line URL change.
- A "raw" mode that lets us skip your harness's parsing and send/receive screenshots+coordinates directly.

---

## Path B — Produce trajectory JSONLs directly

If your harness is too different to wrap (custom action set, weird state
machine, gRPC-only, etc.), just emit our trajectory file format and skip
the client layer entirely.

### Required output per rollout: one JSONL file

```
runs/iter_N/trajectories/<persona_id>__<task_id>.jsonl
```

Three line types, all tagged with `"kind"`:

**Header (line 1):**
```json
{"kind":"header","persona_id":"...","task_id":"...","target_url":"...","target_commit":"...","started_at":"2026-05-09T12:00:00Z","viewport":{"w":1280,"h":800},"agent_model":"your_model_name","browser_session_id":"...","live_view_url":null}
```

**Step lines (one per executed action, fsynced on write):**
```json
{"kind":"step","turn":0,"started_at":"...","ended_at":"...","action":{"type":"click","args":{"button":"left","x":493,"y":437}},"reasoning":["I'll click the submit button"],"observation":{"page_url":"...","page_title":"...","dom_hash":"sha1:...","screenshot_path":"thumbnails/.../step_00.jpg"},"delta":{"dom_changed":true,"url_changed":false,"is_dead_click":false,"consecutive_unchanged":0},"timing":{"model_ms":1240,"exec_ms":523,"total_ms":1763},"tokens":{"prompt_tokens":4521,"completion_tokens":83,"cached_tokens":0,"cost_usd":0.0023}}
```

**Footer (last line):**
```json
{"kind":"footer","ended_at":"...","terminal_reason":"success_dom","final_url":"...","final_title":"...","error":null,"replay_path":"replays/<persona>__<task>.mp4"}
```

`terminal_reason` ∈ `success_dom | success_url | agent_done | max_turns | abandoned | stuck | timeout | error`.

Plus a **manifest** at `runs/iter_N/manifest.jsonl`, one line per finalized trajectory:
```json
{"persona_id":"...","task_id":"...","jsonl_path":"trajectories/...jsonl","terminal_reason":"...","ended_at":"...","n_steps":5}
```

Replays (mp4) and thumbnails (jpg) at the paths referenced in the JSONL are
optional but make the analytics + dashboard work.

### Verifying your output

Drop your `runs/iter_N/` into our repo and run:

```bash
uv run python tests/test_contract.py
# (or)
uv run python -c "
from pathlib import Path
from usersim.io import read_trajectory
from usersim.reduce.aggregator import aggregate
trajs = [read_trajectory(p) for p in Path('runs/iter_N/trajectories').glob('*.jsonl')]
fb = aggregate(trajs, iteration=1, target_commit='external', out_dir=Path('runs/iter_N'))
print(fb.metrics.model_dump_json(indent=2))
"
```

If that emits a valid `feedback.json` and `summary.md` without exceptions,
we're integrated.

### Schema source of truth

`src/usersim/schemas.py` — `Trajectory`, `Step`, `Action`, `TurnMeta`,
`StepObservation`, `StepDelta`, `StepTiming`, `TerminalReason`. These are
Pydantic; if your shape validates against them we're good.

---

## Decision checklist for you

- [ ] Read `src/usersim/clients/{base.py,northstar.py,claude.py}` (15 min)
- [ ] Pick Path A or Path B
- [ ] If Path A: answer the 14 questions above; we write the client.
- [ ] If Path B: emit the JSONL format; we just point our reducer at your dir.

Reply in #cua-hackathon with answers + a sample trajectory JSONL or sample
request/response payload, whichever path. We'll have your client merged
within an hour of receiving it.
