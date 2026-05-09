# Engine code-quality audit

Date: 2026-05-09. Manual review of `src/usersim/`, post-consolidation. Pyright
warnings about unresolved imports are environment cache (the `.venv` is real and
imports work at runtime); ignored unless they signal real bugs.

Rank: **High** = real bug or signal-breaker. **Medium** = brittleness or
maintainability cost. **Low** = nice-to-have.

---

## Fixed in this pass

| # | Severity | File | Issue | Fix |
|---|---|---|---|---|
| F1 | High | `map/worker.py` | `is_dead_click` was hardcoded `False`, breaking the `dead_click_storm` pattern detector — i.e. one of the friction signals never fired on real data. | Compute as `action.type=="click" AND not dom_changed AND not url_changed`. Cheap, doesn't require Playwright hit-testing, captures the signal we care about. |
| F2 | High | `reduce/cluster.py` + `schemas.py` | Suggested fixes were stuffed as a `"FIX: ..."` prefix into `reasoning_excerpts[0]`. Semantic abuse — that field is supposed to be user reasoning. | Added `suggested_fix: str \| None` to `FrictionCluster`. Reducer now sets it cleanly from `PatternMatch.suggested_fix`. Additive schema change, safe per HANDOFF rules. |
| F3 | High | `map/worker.py` | `MODEL_NAME = "tzafon.northstar-cua-fast"` hardcoded in worker. Wrong layer — worker doesn't own model identity. Would lie in trajectory headers when we add other clients. | Worker reads `client.MODEL` (or falls back to `"unknown"`). `NorthstarClient.MODEL` exposed at class scope. |
| F4 | Medium | `registry.py` | `ACTIVE_FILE = Path("runs/active.json")` evaluated at import time. If cwd changes between import and use, registry silently writes to the wrong place. | Resolve lazily inside `_active_file()`. Honors `USERSIM_REGISTRY_FILE` env var for explicit override. |
| F5 | Low | `io.py` | `path.open("w")` used platform default encoding. | Now `encoding="utf-8"`. Non-ASCII reasoning won't blow up on weird locales. |
| F6 | Medium | `scripts/grid.py` | Hard-broken — pointed at `runs/runs.jsonl` which was the old layout. | Rewrote to consume `runs/iter_*/manifest.jsonl` produced by the runner. |

---

## Resolved in second pass (post first-audit)

| # | Severity | What |
|---|---|---|
| O1 | High | Retry inside `NorthstarClient` via `tenacity` (3 attempts, 1–8s exp backoff, only on `APIConnectionError`/`APITimeoutError`/`InternalServerError`/`RateLimitError`). Worker no longer tears down a Kernel session on a transient API blip. |
| O2 | Medium | `_error_trajectory` now uses `TrajectoryWriter` instead of writing JSONL by hand. One write path. |
| O3 | Medium | `temperature: float = 1.0` added to `AgentClient.start_session` Protocol signature. Worker call is now type-safe. |
| O5 | Medium | `_load_tasks` now reads per-task `success_dom` / `success_url_pattern` with config-level fallback as defaults. Heterogeneous tasks supported in a single YAML. |
| O7 | Low | `rollout_patch` is now an explicit `dict[str, Any]` with each value materialized at construction time. The `hasattr(v, "model_dump")` comprehension is gone — fixes the `model_dump-on-None` pyright error too. |
| O8 | Low | `read_trajectory` soft-fails on missing footer (synthesizes an error footer) and skips invalid JSON lines. A crashed worker can't take out the iteration's reducer pass. |
| O11 | Low | Empty `src/usersim/tasks/` directory removed. |
| O12 | Low | `cmd_debug` now calls `aggregate()` after the worker. `feedback.json` exists for one-off spikes too. |
| O13 | Low | Worker no longer keeps a parallel `steps: list[Step]` in memory — it was unread; `read_trajectory(jsonl_path)` rebuilds it from the streamed JSONL at the end. |

**Pyright run:** `uv run pyright src/coder src/usersim tests scripts` → 0 errors, 0 warnings. Editor pyright was stale cache; the actual run is clean.

**Sklearn / Tzafon SDK type-narrowing**: Tzafon's `responses.create(tools=...)` is typed as `Iterable[Tool]` but accepts dicts at runtime; we use `cast(list[Tool], ...)` on `_tools()` so pyright accepts the call without changing runtime behavior. Sklearn's `fit_transform` return type is loose; one `# type: ignore[union-attr]` covers it.

**Red herrings cleaned:** stale `runs/iter_001`, `runs/iter_audit`, `runs/active.json`, empty `src/usersim/tasks/`. Future agents won't waste cycles wondering whether they're meaningful.

---

## Open items (documented, NOT fixed in this pass)

### Medium

- **O4** — `registry.update(session_id, **patch)` silently does nothing if
  `session_id` isn't found. Documented as intentional (stale-update tolerance
  during teardown races). Add `logger.debug` if it ever masks a real bug.
- **O6** — No process-level lock on `runs/active.json`. Threading lock only
  guards intra-process races; two `usersim run` commands clobber each other.
  Use `fcntl.flock` or a content-addressed per-rollout file in a directory.

### Low

- **O9** — No tests for `io.py`, `registry.py`, `worker.py`. Only
  `tests/test_contract.py` exercises the reducer end-to-end. Per user
  preference, deferred.
- **O10** — `web/` is in the engine package but is a separate concern (and per
  the user, deprioritized). Move to its own top-level dir if it stays around.

### Architectural (sync points, not bugs)

- **A1** — Should `AgentClient` be the right place to retry, OR should the
  worker retry the agent call? Picking a layer matters for budget accounting.
- **A2** — Held-out judge (Stage 2) is still stubbed. Wiring is HANDOFF P1.
- **A3** — Embedding for residual HDBSCAN clustering is TF-IDF (local, free,
  weak). Swap to OpenAI `text-embedding-3-small` once API budget is approved.
- **A4** — No persona LLM-expansion. 5 hand-written archetypes is fine for a
  demo iteration; real iterations need ≥50 for diversity (HANDOFF P1).

---

## Things that are NOT slop (positive notes)

- `schemas.py` substructuring (StepObservation/StepDelta/StepTiming/TurnMeta)
  pays off in `worker.py` — each subobject has a clear owner and update site.
  No fights over field ownership when implementations multiply.
- Three-tag JSONL format (header/step/footer) with `kind` discriminator is
  parseable in 5 lines and adding a new kind (e.g. `"checkpoint"`) is a
  non-breaking extension.
- Pattern detection (`reduce/patterns.py`) is rule-based, not statistical —
  with N=10 trajectories, statistical clustering is mush. Each detector
  produces 1 short specific description + 1 actionable `suggested_fix` per
  cluster, mapping 1:1 to a coding-agent fix candidate.
- HDBSCAN survives only as the *residual* fallback for failures matching no
  known pattern — labeled `unmatched_*` so the consumer knows the signal is
  unstructured.
- Browser/Agent/Trajectory provider abstractions are minimal Protocols, not
  ABCs. Cheap to implement a second provider without inheritance ceremony.
- Cleanup is bulletproof: `KernelSession.release()` is idempotent (`_released`
  flag), worker has individual try/except around each finally step so one
  failure can't cascade.
