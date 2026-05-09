# Handoff to Executing Agent

You are picking up the UserSim half of a CUA hackathon project. **Read `USERSIM_PLAN.md` first** — it has the full architecture, schema contracts, and decision log.

## What's done (scaffolded, runtime-verified)

- `src/usersim/schemas.py` — Pydantic schemas: `Persona`, `Task`, `Step`, `Trajectory`, `Outcome`, `FrictionCluster`, `Metrics`, `Feedback`. **`Feedback` is the contract with the coding-agent side. Don't break it.**
- `src/usersim/clients/northstar.py` — async wrapper around Tzafon Lightcone Responses API.
- `src/usersim/clients/base.py` — `AgentClient` protocol.
- `src/usersim/map/worker.py` — async worker: one (persona, task) pair → one Trajectory. Lifted from `northstar_kernel/run.py`, ported to async Playwright. Cleanup wrapped in `finally`.
- `src/usersim/map/runner.py` — asyncio fanout with semaphore-bounded concurrency, retries, persistence.
- `src/usersim/reduce/grader.py` — Stage 1 grading (URL/DOM match, abandonment). Stage 2 (held-out judge) is a stub.
- `src/usersim/reduce/aggregator.py` — combines trajectories + outcomes → `Feedback`. Includes basic friction clustering by failure category, regression detection vs prev iter, summary.md renderer.
- `src/usersim/cli.py` — `run` and `debug` commands.
- `configs/taxcaster.yaml` — TurboTax TaxCaster smoke target.
- `configs/personas/seed.jsonl` — 5 hand-written personas.

CLI is wired end-to-end. `uv sync` clean. All imports resolve (Pyright complains but runtime is fine).

## Verify it works (your hour 0)

```bash
# 1. Single persona × single task spike on TaxCaster.
uv run python -m usersim debug \
  --config configs/taxcaster.yaml \
  --persona rushed_mobile \
  --task single_w2_basic \
  --out runs/spike_000

# Expected: one Kernel session spins up, Northstar drives the browser,
# trajectory written to runs/spike_000/trajectories/rushed_mobile__single_w2_basic.json,
# feedback.json + summary.md emitted.
```

If this works, scale up:

```bash
# 2. Full 5×3 = 15 workers, concurrency=5
uv run python -m usersim run \
  --config configs/taxcaster.yaml \
  --out runs/iter_000 \
  --concurrency 5 \
  --iteration 0
```

## Things to watch for in hour 1

1. **Anti-bot on TaxCaster.** TurboTax may serve a fingerprint check. `stealth=True` should clear it. If not: switch target to `https://www.healthcare.gov/see-plans/` or our own deliberately-mid Next.js form (teammate task).
2. **`success_dom` selector.** I guessed `[data-testid='refund-amount']` — verify in DevTools on a real run, fix the YAML.
3. **Tzafon rate limits.** 5 concurrent should be safe. If 429s appear, drop to 3 and add backoff in `_retrying`.
4. **Kernel session leaks.** After a run, `kernel.browsers.list()` should be empty. If not, write a reaper.

## What's missing (build in this order)

### P0 — needed for first real demo iteration

1. **DOM diff in `worker.py`.** Currently `dom_changed=True` always. Compute a real diff (page hash before/after action) so the grader can detect "stuck" loops.
2. **Verify `success_dom` selector by hand on TaxCaster.** Put a real selector in the YAML.
3. **Holotron client (`clients/holotron.py`).** Once teammate's vLLM endpoint is up, write the OpenAI-compat client and select via `--client holotron` flag. Use Tzafon API as fallback.

### P1 — needed before scaling to 100 personas

4. **Failure clustering with embeddings.** Replace `_stub_clusters` in `aggregator.py` with HDBSCAN over embeddings of step.reasoning fields for failed trajectories. `hdbscan` is in deps. Use OpenAI text-embedding-3-small or a local model.
5. **Held-out Stage-2 judge.** Wire `grade_stage2_heldout` to Claude Sonnet 4.6. Run on every 5th iteration only. Hide from coding-agent's feedback path.
6. **Trajectory cache.** Key on `(persona_id, task_id, target_commit_sha)`; skip re-running unchanged cells.

### P2 — polish

7. **Live dashboard.** Streamlit or Next.js page that polls `runs/<iter>/trajectories/` and shows the 100-grid with thumbnails + status.
8. **Persona LLM-expansion** beyond the 5 seeds. Generate 50+ via Claude/GPT.
9. **Hack detection panel.** Plot `delta_gameable_vs_heldout` over iterations. Spike = reward hacking starting.

## Interface contract (DO NOT BREAK)

The coding-agent side reads `runs/<iter>/feedback.json`. Its schema is `Feedback` in `schemas.py`:

```python
class Feedback(BaseModel):
    iteration: int
    target_commit: str
    n_trajectories: int
    metrics: Metrics
    top_friction_clusters: list[FrictionCluster]
    regressions_vs_prev: list[Regression]
    raw_trajectory_dir: str
```

Coordinate with teammate before changing field names or types. Adding fields is safe.

## Open questions (resolve at next regroup)

See bottom of `USERSIM_PLAN.md` for the running list.

## Things I deliberately did NOT do

- LLM-expand personas (5 hand-written first to verify steering works)
- Build the live dashboard (Hour 6+ task)
- Implement Holotron client (waiting on teammate's vLLM endpoint)
- Wire Claude held-out judge (waiting on iter-2 budget approval)
- DOM diffing (P0 but not critical for first spike)
