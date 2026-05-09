# cua-hackathon — Auto-UX with Reward Hacking

A closed-loop system that uses a CUA (computer-use agent) to roll out
synthetic personas against a target web app, distills the trajectories into
actionable friction signal, and hands that signal to a coding agent to patch
the app — then repeats. The research thesis is **detecting reward hacking**:
two-stage reward (gameable + held-out) lets us see when the coding agent is
gaming the goalpost rather than fixing real problems.

> Read this end-to-end before touching anything. If you're an agent picking
> up work, also read `docs/HANDOFF.md` (rolling task list),
> `docs/USERSIM_PLAN.md` (architecture decisions), and
> `docs/CODE_QUALITY.md` (audit + open items).

---

## The loop

```
   ┌─────────────── MAP (src/usersim/) ───────────────┐
   │  N personas × M tasks                            │
   │   ↓                                              │
   │  asyncio fanout (semaphore-bounded)              │
   │   ↓                                              │
   │  per (persona, task):                            │
   │    Kernel browser  ←→  Northstar (Tzafon CUA)    │
   │    streaming JSONL trajectory + replay mp4       │
   └──────────────────────┬───────────────────────────┘
                          ↓
   ┌────────────── REDUCE (src/usersim/reduce/) ──────┐
   │  Stage 1: URL/DOM match → success_gameable       │
   │  Stage 2: Claude judge → success_heldout (HIDDEN)│
   │  Patterns:  form_clears_on_submit,               │
   │             stuck_on_button,                     │
   │             dead_click_storm,                    │
   │             patience_exhausted,                  │
   │             edge_case_thrashing,                 │
   │             navigation_confusion                 │
   │  Residual:  HDBSCAN over reasoning embeddings    │
   └──────────────────────┬───────────────────────────┘
                          ↓
              runs/iter_N/feedback.json   ← the contract
                          ↓
   ┌────────────── CODER (src/coder/) ────────────────┐
   │  read feedback.json → render prompt → run agent  │
   │  → git diff → commit as `iter_N: auto-ux patch`  │
   └──────────────────────────────────────────────────┘
                          ↓
                redeploy target, increment N, repeat
```

The MAP step is what we own primarily. The REDUCE step's `feedback.json`
schema is **the locked interface** with `src/coder/`. Adding fields is safe;
renaming/retyping is a sync point.

---

## Quickstart

Single `.env` at repo root with `TZAFON_API_KEY` and `KERNEL_API_KEY`:

```bash
# smoke test (cheap, ~10s) — example.com end-to-end
uv run python -m usersim run --config configs/smoke.yaml --out runs/smoke --concurrency 1

# real iteration — TaxCaster, all personas × all tasks
uv run python -m usersim run --config configs/taxcaster.yaml --out runs/iter_001 --iteration 1

# single (persona, task) spike, verbose
uv run python -m usersim debug --config configs/taxcaster.yaml \
    --persona rushed_mobile --task single_w2_basic --out runs/spike_001

# offline reducer test (no Kernel/Tzafon needed)
uv run python tests/test_contract.py

# post-hoc grid of N replays from one iteration
uv run python -m usersim.grid runs/iter_001 9    # 3×3 grid

# diagnostics on an iteration (reasoning coverage, action histogram, friction patterns)
uv run python -m usersim.analyze runs/iter_001

# typecheck the engine
uv run pyright src/coder src/usersim tests

# live dashboard (FastAPI server + Next.js frontend)
uv run uvicorn usersim.web.server:app --host 127.0.0.1 --port 8766    # backend
cd apps/dashboard && npm install && npm run dev                       # frontend → :3001
```

After a `run`: `runs/<out>/feedback.json` is the artifact the coder reads,
`summary.md` is human-readable, `manifest.jsonl` is one-line-per-trajectory,
`trajectories/*.jsonl` are the per-rollout streamed records (header + steps
+ footer), `replays/*.mp4` are the Kernel session videos, `outcomes.jsonl`
is one Outcome per trajectory.

---

## Where things live (monorepo)

```
cua-hackathon/                # repo root
├── .env                      # secrets (gitignored)
├── .gitignore                # secrets, runs/, replays/, node_modules, .next, …
├── pyproject.toml            # uv-managed; one Python project covers usersim+coder
├── uv.lock
├── README.md                 # this file
│
├── apps/                     # deployable applications
│   └── dashboard/            #   Next.js dashboard — Kernel aesthetic, autoscale
│                             #   grid, run modal. Consumes FastAPI backend at :8766.
│
├── src/                      # Python source (usersim + coder, single uv project)
│   ├── usersim/              #   ENGINE (provider-agnostic)
│   │   ├── schemas.py        #     ← LOCKED data models. Adding fields safe.
│   │   ├── io.py             #     streaming JSONL writer/reader/manifest
│   │   ├── registry.py       #     live ActiveRollout registry (file-backed)
│   │   ├── cli.py            #     `python -m usersim run|debug`
│   │   ├── clients/
│   │   │   ├── base.py       #     AgentClient/AgentSession Protocol (LOCKED)
│   │   │   ├── northstar.py  #     Tzafon Northstar impl
│   │   │   └── claude.py     #     Anthropic computer-use impl
│   │   ├── browsers/
│   │   │   ├── base.py       #     BrowserProvider/BrowserSession (LOCKED)
│   │   │   └── kernel.py     #     Kernel impl
│   │   ├── map/              #     async worker + fanout
│   │   ├── reduce/           #     grader + patterns + aggregator → Feedback
│   │   ├── personas/         #     LLM expansion + avatar generation
│   │   ├── web/              #     FastAPI server (backend for apps/dashboard)
│   │   ├── grid.py           #     post-hoc ffmpeg replay grid composer
│   │   └── analyze.py        #     per-iteration trajectory diagnostics
│   └── coder/                #   CODING-AGENT HALF (claude-cli wrapper, swappable)
│
├── configs/                  # shared declarative config
│   ├── smoke.yaml            #   example.com smoke (free, fast)
│   ├── taxcaster.yaml        #   real target (TurboTax TaxCaster)
│   └── personas/
│       ├── seed.jsonl        #   5 hand-curated archetypes
│       ├── expanded.jsonl    #   24 LLM-expanded personas
│       └── avatars/*.png     #   Kernel-aesthetic portraits (committed)
│
├── deploy/                   # deployment infra
│   └── k8s/                  #   Kubernetes manifests (placeholder)
│
├── docs/
│   ├── HANDOFF.md            #   rolling task list — start here for context
│   ├── USERSIM_PLAN.md       #   architecture decisions, prior-art notes
│   ├── CODE_QUALITY.md       #   audit + open items
│   └── ARB_INTEGRATION.md    #   integration notes
│
├── tests/
│   ├── fixtures/             #   synthetic trajectories for offline testing
│   └── test_contract.py      #   offline reducer + Feedback verifier
│
├── templates/                # files copied into the target app
│   └── .claude/settings.json #   coder permissions/hooks template
│
└── runs/                     # outputs (GITIGNORED)
    └── _archive_pre_repo/    #   pre-repo smoke runs (will be cleared)
```

---

## Locked contracts (do not break without sync)

1. **`Feedback` in `src/usersim/schemas.py`** — read by `src/coder/`. Adding
   fields is safe; renaming or retyping is a sync point.
2. **`AgentClient` Protocol in `src/usersim/clients/base.py`** — any new CUA
   provider (Holotron, Claude computer-use, etc.) implements this.
3. **`BrowserProvider` Protocol in `src/usersim/browsers/base.py`** — any
   new browser host (Browserbase, local Chromium, etc.) implements this.
4. **JSONL trajectory wire format** in `src/usersim/io.py` —
   `{"kind":"header"|"step"|"footer", ...}`. Adding a fourth `kind` is
   non-breaking. Header keys can grow; existing keys can't move.

---

## Key concepts

- **Two-stage reward.** Stage 1 (`success_gameable`) is cheap URL/DOM match
  shown to the coding agent. Stage 2 (`success_heldout`) is a Claude-as-judge
  pass over a text trajectory summary, run every Nth iteration, **never
  shown to the coding agent**. `delta_gameable_vs_heldout` widening over
  iterations is the reward-hacking signal.
- **Pattern detection over statistical clustering.** `reduce/patterns.py`
  has six rule-based detectors that map 1:1 to coding-agent fixes:
  `form_clears_on_submit`, `stuck_on_button`, `dead_click_storm`,
  `patience_exhausted`, `edge_case_thrashing`, `navigation_confusion`.
  HDBSCAN over reasoning embeddings only handles the residual (failures
  matching no known pattern).
- **Streaming JSONL.** Each trajectory is `header → step* → footer`,
  fsynced per step. A crash mid-rollout still leaves a parseable file (and
  `read_trajectory` synthesizes an error footer for trajectories cut short).
- **Cleanup is sacred.** Every `BrowserSession.release()` is idempotent and
  in a `finally`. A failed worker never leaks a Kernel session — that's
  budget on fire.
- **Provider-agnostic engine.** `usersim/` mentions Tzafon/Kernel only in
  the impl files (`clients/northstar.py`, `browsers/kernel.py`). The map
  step + reduce step never reach into a provider SDK.

---

## State of the world (May 2026)

Engine is end-to-end clean: 3,040 LOC, 0 pyright errors, 0 TODO/FIXME.
- ✅ Map: async worker, retry inside client, replay recording, registry
- ✅ Reduce: Stage 1 grader, 6 pattern detectors, HDBSCAN residual,
     Feedback contract verified roundtrip
- ✅ Coder: `src/coder/` reads feedback.json, drives Claude CLI, commits
- ⚠️ Stage 2 held-out judge: stubbed (`grade_stage2_heldout` returns None)
- ⚠️ Persona expansion: 5 hand-written + LLM-expansion code in
     `usersim/personas/expand.py`; not wired into the default flow
- ⚠️ Live dashboard: `usersim/web/` works but has been deprioritized
- ❌ HDBSCAN residual still uses TF-IDF; production swap to OpenAI
     `text-embedding-3-small` pending budget
- ❌ Process-level lock on `runs/active.json` not implemented
     (single-process runs only for now — see `CODE_QUALITY.md` O6)

---

## Running into trouble?

- Engine imports fine, pyright complains in editor → editor pyright cache is
  stale; `uv run pyright src/usersim` is the source of truth.
- Kernel session leak after a crash → `kernel.browsers.list()` to inspect;
  there's no reaper script yet (see `CODE_QUALITY.md`).
- Tzafon 429s under concurrency=20+ → already retried inside
  `NorthstarClient` with exp backoff; if persistent, drop to 10 and revisit.
- Feedback.json validation fails → schema change without sync; recheck
  `Feedback` in `schemas.py` against what `src/coder/` expects.
