---
marp: true
theme: gaia
paginate: true
backgroundColor: "#0a0a0a"
color: "#e6e6e6"
style: |
  section {
    font-family: "Inter", "Helvetica Neue", system-ui, sans-serif;
    font-size: 26px;
    padding: 60px 80px;
  }
  h1 { color: #ffffff; font-weight: 700; letter-spacing: -0.01em; }
  h2 { color: #ffffff; font-weight: 600; border-bottom: 1px solid #2a2a2a; padding-bottom: 0.2em; }
  strong { color: #ffffff; }
  a { color: #4ea1ff; text-decoration: none; }
  a:hover { text-decoration: underline; }
  code { background: #1a1a1a; color: #d4d4d4; border-radius: 4px; padding: 0.1em 0.3em; }
  pre, pre code {
    background: #141414; color: #d4d4d4; border: 1px solid #222; border-radius: 8px;
    font-size: 0.62em; line-height: 1.4;
  }
  blockquote { border-left: 3px solid #444; color: #aaa; padding-left: 1em; }
  table { font-size: 0.62em; border-collapse: collapse; }
  th, td { border: 1px solid #2a2a2a; padding: 0.4em 0.7em; }
  th { background: #1a1a1a; }
  ul, ol { line-height: 1.45; }
  li { margin-bottom: 0.25em; }
  .small { font-size: 0.7em; color: #888; }
  section.title { text-align: center; justify-content: center; }
  section.title h1 { font-size: 1.6em; margin-bottom: 0.3em; }
  section.title .authors { color: #888; font-size: 0.9em; }
---

<!-- _class: title -->

# AutoUX: A CUA UserSim

<div class="authors">

**Alex Kreidler** · **David Bai** · 2026
[github.com/alexkreidler/computer-hack](https://github.com/alexkreidler/computer-hack)

</div>

---

## Priors we hold (and why they're validated)

| prior | grounding |
|---|---|
| **CUAs can drive real browsers tractably.** | [Anthropic computer-use (2024)](https://www.anthropic.com/news/3-5-models-and-computer-use); [OSWorld](https://os-world.github.io/) ~38% on web tasks; [WebVoyager](https://arxiv.org/abs/2401.13919); [Browser-Use](https://github.com/browser-use/browser-use) |
| **Planner+grounder beats end-to-end vision** for pixel-precise UI work. | [H Company Holo3](https://www.hcompany.ai/), [Magentic-One (Microsoft, 2024)](https://www.microsoft.com/en-us/research/publication/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/); we use this for `surfer` (Claude Opus + Holo3-35B). |
| **Personas produce measurably different UX trajectories,** not just stylistic noise. | [PersonaHub (Tencent, 2024)](https://arxiv.org/abs/2406.20094); HCI persona literature ([Cooper, 1999](https://www.cooper.com/journal/2003/8/the_origin_of_personas/)); we observe 4× variance in step-count across personas on the same task. |
| **LLM-as-user-simulator is a viable eval pattern**, established for chat. | [DeepEval](https://github.com/confident-ai/deepeval), [LangWatch](https://langwatch.ai/), [MLflow eval](https://mlflow.org/docs/latest/llms/llm-evaluate/). We extend this from text → browser. |
| **Reward hacking is real in iterative agent loops** — coding agents *will* game observable metrics. | [Skalse et al., 2022 — Defining Reward Hacking](https://arxiv.org/abs/2209.13085); [Specification Gaming, DeepMind](https://deepmind.google/discover/blog/specification-gaming-the-flip-side-of-ai-ingenuity/); [Anthropic on auditing](https://arxiv.org/abs/2310.13548). Our held-out judge is the firewall against this. |

---

## The gap

Every UserSim project we found is **text-only chat eval**. None drive a real browser.

| project | shape | drives a browser? |
|---|---|---|
| [DeepEval multi-turn sim](https://github.com/confident-ai/deepeval) | persona+goal chatbot eval | ✗ |
| [MLflow conversation sim](https://mlflow.org/docs/latest/llms/llm-evaluate/) | scenario YAML, chat | ✗ |
| [LangWatch user sim](https://langwatch.ai/) | regression detection | ✗ |
| [OASIS / MiroFish (CAMEL-AI)](https://github.com/camel-ai/oasis) | 1M-agent social sim | ✗ |
| [TREC UserSim 2026](https://trec.nist.gov/) | conversational IR | ✗ |
| **AutoUX (this work)** | **CUA-driven personas on real web apps** | **✓** |

To our knowledge **the first CUA/BUA-based UserSim framework**. The evaluation surface (real browser, real DOM, real friction) is qualitatively different from text-only chat sim — and it's what the actual deployment surface looks like for most product teams.

---

## Architecture

Closed loop, fully reproducible, all schemas Pydantic-validated.

```
   ┌──── MAP ───────────────────────────────────────────┐
   │  N personas × M tasks × K apps   (registry-defined)│
   │   ↓  asyncio fanout, semaphore-bounded             │
   │  per-cell: Kernel browser ↔ CUA agent              │
   │            streaming JSONL + replay mp4            │
   └─────────────────────────┬──────────────────────────┘
                             ↓
   ┌──── REDUCE ────────────────────────────────────────┐
   │  Stage 1: rule-based patterns + URL/DOM match      │
   │  Stage 2: held-out Claude judge   (HIDDEN)         │
   │  Per-persona segmentation + distinctive quotes     │
   └─────────────────────────┬──────────────────────────┘
                             ↓
                runs/iter_N/feedback.json
                             ↓
   ┌──── CODER ────────────────────────────────────────┐
   │  read feedback → patch app → redeploy → repeat    │
   └────────────────────────────────────────────────────┘
```

[engine](https://github.com/alexkreidler/computer-hack/tree/main/src/usersim) · [coder harness](https://github.com/alexkreidler/computer-hack/tree/main/src/coder) · [dashboard](https://github.com/alexkreidler/computer-hack/tree/main/apps/dashboard) · [app registry](https://github.com/alexkreidler/computer-hack/blob/main/configs/apps/registry.jsonl) · [persona registry](https://github.com/alexkreidler/computer-hack/blob/main/configs/personas/seed.jsonl)

---

## Personas + agents

**24 personas** spanning age, device, language fluency, tech literacy, prior experience, with explicit `quirks` injected into each rollout's system prompt. 5 hand-curated ([seed.jsonl](https://github.com/alexkreidler/computer-hack/blob/main/configs/personas/seed.jsonl)) + 19 LLM-expanded with [PersonaHub-style](https://arxiv.org/abs/2406.20094) negative-example dedup.

**3 pluggable CUA agents** behind one [`AgentClient` Protocol](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/clients/base.py):

| agent | family | grounding |
|---|---|---|
| `northstar` | [Tzafon Lightcone](https://docs.lightcone.ai) (4B end-to-end CUA) | end-to-end vision, OpenAI-compat Responses API |
| `claude` | [Anthropic computer-use](https://docs.claude.com/en/docs/build-with-claude/computer-use) | end-to-end vision, tool_use loop |
| `surfer` | [Claude Opus + Holo3-35B](https://www.hcompany.ai/) | **planner + grounder split** (current SOTA) |

Adding a 4th = one file + one line in [`clients/__init__.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/clients/__init__.py). Same trajectory format across all of them.

---

## Reduce — two-stage reward (the reward-hacking firewall)

Coding agents trained to maximize observable metrics will [game the metric](https://arxiv.org/abs/2209.13085). Our defense:

```
Stage 1 (cheap, every trajectory) — VISIBLE TO CODER:
  success_gameable    URL/DOM match
  pattern detectors   form_clears_on_submit, stuck_on_button,
                      dead_click_storm, patience_exhausted, …
  (rule-based; mapped 1:1 to suggested fixes)

Stage 2 (periodic, every Nth iter) — HIDDEN FROM CODER:
  Claude judge over text trajectory + 3 keyframes
  prompt: "would a real human consider this a real success?"
  → success_heldout

  signal:  delta = success_gameable − success_heldout
  if delta widens iter→iter, the coder is HACKING the goalpost.
```

Falsifiable, auditable measure of reward hacking in the loop. [`reduce/grader.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/reduce/grader.py) · [`reduce/patterns.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/reduce/patterns.py) · [`reduce/aggregator.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/reduce/aggregator.py)

---

## Reduce — per-persona segmentation

`Feedback.by_persona` gives the coding agent **persona-aware signal**, not aggregate noise. For each persona: success rate, avg steps, distinctive actions (action types this persona uses ≥2× the cohort median), distinctive quotes (reasoning lines unique to this persona by substring fingerprint).

![bg right:55% w:90%](../demo/persona_divergence.png)

The whole point: a coder reading "median user clicks 5 times" is useless. A coder reading "elderly_first_time abandons at step 4 with `'I don't understand why this isn't working'`, esl_speaker pauses at the income field" can write the right patch. [`reduce/aggregator.py:_compute_persona_segments`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/reduce/aggregator.py)

---

## Implementation grounding

**Engine** — 11 modules, ~3k LOC, [pyright-clean](https://github.com/alexkreidler/computer-hack/blob/main/docs/CODE_QUALITY.md), Pydantic-validated everywhere.
- [`schemas.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/schemas.py) — `Persona`, `Task`, `App`, `Action`, `Step`, `Trajectory`, `Feedback`
- [`map/worker.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/map/worker.py) — async per-cell loop with stuck-detection, retries, replay recording
- [`io.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/io.py) — streaming JSONL with `header` / `step` / `footer` discriminator, `fsync` per step (crash-safe)
- [`harnesses/surfer/`](https://github.com/alexkreidler/computer-hack/tree/main/src/usersim/harnesses/surfer) — Surfer planner+grounder vendored in-tree

**Apps** — [26-app registry](https://github.com/alexkreidler/computer-hack/blob/main/configs/apps/registry.jsonl) of real OSS targets (Metabase, Kanboard, Grafana, BookStack, Mastodon, …). Each Pydantic-validated; teammate pushes adds, the engine consumes them as first-class data.

**Live dashboard** — Next.js + FastAPI, iframes Kernel's `browser_live_view_url` for real-time grid view. [`apps/dashboard/`](https://github.com/alexkreidler/computer-hack/tree/main/apps/dashboard).

---

## What's novel

1. **First CUA/BUA-based UserSim framework.** Prior work is text-only chat eval ([DeepEval](https://github.com/confident-ai/deepeval), [LangWatch](https://langwatch.ai/), [OASIS](https://github.com/camel-ai/oasis)). We extend the user-simulator pattern to real browsers, real DOMs, real visual UI.
2. **Per-persona reduction.** `Feedback.by_persona` surfaces signal traditional clustering hides; coding agent gets *persona-specific* fixes ("elderly user uniquely abandons at step 4"), not median-user platitudes.
3. **Held-out reward firewall.** Two-stage reward — Stage 1 visible, Stage 2 hidden — gives a falsifiable measure of [reward hacking (Skalse 2022)](https://arxiv.org/abs/2209.13085) in auto-UX loops. We don't think this exists for CUA-driven product loops anywhere.
4. **Provider-agnostic agent comparison.** Same trajectory format across `northstar`, `claude`, `surfer`; agent comparison is one CLI flag.
5. **End-to-end reproducible.** Apps + personas as Pydantic registries, JSONL trajectories, ffmpeg replay grids, deterministic Stage 1 — every claim re-runnable from `git clone`.

---

## Future work + open questions

**Near-term:**
- Wire Stage 2 judge at full iteration cadence ([`grade_stage2_heldout`](https://github.com/alexkreidler/computer-hack/blob/main/src/usersim/reduce/grader.py) is currently stubbed).
- Close the redeploy loop: [`coder/loop.py`](https://github.com/alexkreidler/computer-hack/blob/main/src/coder/loop.py) reads feedback and runs Claude CLI; we haven't yet auto-deployed the patch.

**Research questions:**
- Does `delta_gameable_vs_heldout` reliably catch reward hacking *before* a human notices? Need N≥20 iterations.
- How sensitive is the friction signal to persona pool size? Is there a knee?
- Can a held-out persona pool detect overfitting to the training persona pool?
- Are pattern detectors generalizable across domains, or does each app need its own?

**Public benchmark:** open the 26-app registry + persona pool as a community baseline for CUA-driven UX research.

---

<!-- _class: title -->

# Thanks

**Alex Kreidler** · **David Bai**

[github.com/alexkreidler/computer-hack](https://github.com/alexkreidler/computer-hack)
