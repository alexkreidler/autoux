# AutoUX demo — screen recording shot list

Target: ~90s video. Cut to 60s if needed; trim from the middle B-roll, keep the bookends.

## Hero artifacts (already produced)

| File | Purpose |
|---|---|
| `demo/persona_divergence.png` | Chart: token + step variance per persona, 3 open-ended UIs |
| `demo/persona_quotes.png` | 5-card "what each persona was thinking" — Spree task |
| `runs/sweep_open_20260509_144457/grid.mp4` | 7×6 grid, 40 cells, all 5 personas × 6 OSS demos |
| `runs/sweep_25c_20260509_142022/grid.mp4` | 9×9 grid, 75 cells (cluster) — for "scale" beat |
| `runs/iter_002/grid.mp4` | smaller 9-up if we want a single-task focus |

## Shot list (ordered)

### 0:00–0:08 — Opening
- **Shot:** title card. "AutoUX — persona-driven UX testing for the agentic web." Names underneath.
- **Source:** static image OR HyperFrames (already discussed; make in 30 min if time).
- **Voiceover:** *"We built a system that drives a hundred personas through real web apps simultaneously, and surfaces UX bugs that only certain users hit."*

### 0:08–0:18 — The problem
- **Shot:** still of `demo/persona_quotes.png` — pan slowly down the 5 personas.
- **VO:** *"Different users notice different things. A rushed mobile user clicks the first thing. A careful elderly user reads every label. A skeptical power user pokes at edge cases. Today UX testing collapses all of them into 'an average user'."*

### 0:18–0:30 — The system, live
- **Shot:** dashboard at http://localhost:3001 — empty state → click "+ new run" → modal → pick all 5 personas + an open-ended app → kick.
- **Then cut to:** grid populating live. 25 cells with persona avatars, iframes streaming Kernel browsers.
- **VO:** *"This is AutoUX. We pick personas, pick a task, and the harness runs them in parallel against any web app — surfer-style hierarchical agent driving a real Kernel browser per persona."*

### 0:30–0:42 — The persona divergence finding
- **Shot:** `demo/persona_divergence.png` chart with the title "personas diverge when ui admits choice".
- **VO:** *"On narrow tasks — login, click sidebar — every persona converges to the same trajectory. But on open-ended tasks — browse, shop, explore — token usage spreads 6× across personas, predicted by archetype. The rushed mobile user takes 5 steps on Spree. The power user takes 14 and finds bugs."*

### 0:42–0:55 — The actual reasoning, comparative
- **Shot:** focus a single cell from the running grid → side panel transcript with reasoning bubbles. Scroll through 3-4 turns.
- **VO:** *"And the model's reasoning isn't just longer for some personas — it's qualitatively different. Power users say 'let me try edge case 9999.' Elderly users narrate prices and compare. ESL speakers re-read instructions. The persona shapes what the model sees and decides."*

### 0:55–1:08 — Scale — the 75-cell grid
- **Shot:** play `sweep_open_20260509_144457/grid.mp4` (or the 9×9 cluster grid for max impact). Quarter-screen, sped up 3-4× if too long.
- **VO:** *"We ran 75 rollouts across 15 production OSS apps × 5 personas. Surfer hits 100% on 7 of them. The other 8 reveal real persona-specific failures — anti-bot blocks, modal interludes, setup wizards that elderly users get stuck on but rushed users abandon away from."*

### 1:08–1:20 — The feedback artifact
- **Shot:** dashboard → past runs sidebar (FE subagent shipping this) → click `sweep_open` → result view shows per-persona breakdown table with success rates and quotes.
- **VO:** *"Every run produces structured persona-segmented feedback that a coding agent can consume directly — quotes from each persona, actions only that persona used, divergence score across the iteration. This is the feedback loop UX engineering has been missing: who fails, how, and what they were trying to do."*

### 1:20–1:30 — Outro
- **Shot:** title card "open-source on github.com/alexkreidler/computer-hack" → team names → sponsors logos (Kernel, Tzafon, Anthropic; NVIDIA if NemoClaw integration ships).
- **VO:** *"Built in 36 hours. 100 personas. 15 apps. The full repo, traces, and research notes are open."*

## Pre-recording checklist

- [ ] All servers up: FastAPI on :8766, Next.js on :3001, vLLM (Holo3 localizer) reachable
- [ ] Dashboard hard-refreshed in a clean browser window
- [ ] One sweep already loaded in past-runs sidebar (sweep_open is ideal)
- [ ] Browser zoom 100%, screen recording at 1080p+
- [ ] Voiceover script printed; practice run once
- [ ] Backup screenshot if iframe shows "Session not found" mid-record
- [ ] Mute notifications + close noisy tabs

## Polish tasks remaining (can ship without)

- HyperFrames title/outro card (10 min if you skip animation)
- Per-trajectory replay video in focused view (FE subagent track 2)
- Captioning the voiceover (CapCut auto-captions — 2 min)
- Background music: subtle, non-vocal, royalty-free; mute during reasoning quotes section so it can be read

## What NOT to demo

- The CLI. Stay entirely in the dashboard.
- The kanboard sweep (only 4/5 succeeded — uneven storytelling).
- The plausible / twenty failures unless we explain them.
- NemoClaw / NVIDIA bonus track unless we actually integrate.

## If only 30 seconds

Cut everything except: opening hook (5s), `persona_divergence.png` chart (10s), live grid populating (10s), outro (5s). The chart is the load-bearing artifact.
