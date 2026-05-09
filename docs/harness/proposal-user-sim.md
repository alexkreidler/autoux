# UserSim: AI-Powered Website Optimization via Simulated User Agents

## Hackathon Proposal (6 hours)

---

## One-liner

Point AI user agents at any website, simulate dozens of diverse personas trying to accomplish real tasks, surface friction/drop-off points, and auto-generate concrete UI/UX fixes.

---

## The Problem

Traditional UX optimization is slow and expensive: recruit users, run sessions, watch recordings, manually synthesize findings, then hand off to design/eng. Tools like Hotjar/FullStory help but still require real traffic and manual interpretation. A/B testing requires significant traffic volume and weeks of runtime.

**What if you could simulate 50 diverse users in 5 minutes and get both the diagnosis AND the fix?**

---

## Core Insight

LLMs are surprisingly good proxies for human web navigation behavior. They can:
- Reason about what a UI element probably does
- Get confused by the same things real users get confused by (ambiguous CTAs, hidden nav, jargon)
- Represent different personas (tech-savvy dev vs. elderly first-time user vs. impatient mobile shopper)
- Articulate *why* they're stuck, not just *where*

The key differentiator from traditional automated testing: these agents have **goals and opinions**, not scripts.

---

## Architecture

```
                                    ┌─────────────────────┐
                                    │   Target Website     │
                                    │   (any public URL)   │
                                    └──────────┬──────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                         ┌────▼────┐     ┌─────▼────┐    ┌─────▼────┐
                         │ Agent 1 │     │ Agent 2  │    │ Agent N  │
                         │"Elderly │     │"Impatient│    │"Screen   │
                         │ shopper"│     │ dev"     │    │ reader"  │
                         └────┬────┘     └─────┬────┘    └─────┬────┘
                              │                │                │
                              │  Browser-Use / Stagehand        │
                              │  (Playwright under the hood)    │
                              │                │                │
                              └────────────────┼────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   Session Recorder   │
                                    │  - screenshots/step  │
                                    │  - agent reasoning   │
                                    │  - time per action   │
                                    │  - backtrack events   │
                                    │  - failure points     │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   Analysis Engine    │
                                    │  - aggregate across  │
                                    │    all agents/tasks  │
                                    │  - rank issues by    │
                                    │    severity/frequency│
                                    └──────────┬──────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                       ┌──────▼──────┐  ┌──────▼──────┐ ┌──────▼──────┐
                       │  UX Report  │  │  Fix Diffs  │ │ Replay UI  │
                       │  (ranked    │  │  (actual    │ │ (step-by-  │
                       │   issues)   │  │   patches)  │ │  step viz) │
                       └─────────────┘  └─────────────┘ └─────────────┘
```

---

## Technical Stack (all OSS)

| Layer | Tool | Why this one |
|-------|------|-------------|
| Browser automation | **browser-use** or **stagehand** | LLM-native browser control. Agent sees the page, reasons about it, acts. No selectors to write. |
| Underlying browser | **Playwright** | Headless Chromium, screenshot capture, network interception, mobile emulation |
| LLM backbone | **Claude API** (Sonnet for agents, Haiku for bulk analysis) | Vision + reasoning. Agents need to *see* the page, not just parse DOM |
| Orchestration | **Python async** or **Node.js** | Run N agents concurrently against the same site |
| Reporting | **Simple HTML/React dashboard** | Show findings, screenshots, diffs |

### Why browser-use / stagehand over raw Playwright + LLM?

These libraries solve the hard plumbing: converting page state into LLM-digestible context, handling action execution, managing retries. Writing this from scratch would eat the entire hackathon.

---

## Persona System

Each simulated user gets a persona card that shapes their behavior:

```python
personas = [
    {
        "name": "Martha, 68",
        "description": "Retired teacher. Uses iPad. Not tech-savvy. Types slowly.",
        "goal": "Find and purchase a birthday gift under $50",
        "patience": "low",      # gives up after N failed attempts
        "tech_literacy": "low", # avoids technical jargon, confused by complex UIs
        "device": "tablet",
    },
    {
        "name": "Raj, 29",
        "description": "Software engineer. Evaluating the product for his team.",
        "goal": "Find pricing for team plan, understand API limits, sign up for trial",
        "patience": "medium",
        "tech_literacy": "high",
        "device": "desktop",
    },
    {
        "name": "Screen Reader User",
        "description": "Blind user navigating with NVDA. Only has access to aria labels and heading structure.",
        "goal": "Navigate to account settings and update email",
        "patience": "high",
        "tech_literacy": "high",
        "device": "desktop",
        "accessibility": "screen_reader",  # agent only sees aria tree, not visual layout
    },
    # ... 5-10 more covering: mobile user on slow connection, 
    # non-native English speaker, power user, first-time visitor, etc.
]
```

**Critical design choice:** The persona doesn't just change the prompt — it changes the *simulation parameters*. A "slow connection" persona gets throttled network. A "tablet" persona gets tablet viewport. A "screen reader" persona only receives the accessibility tree, not screenshots. This makes the simulation realistic rather than theatrical.

---

## What We Actually Measure

Not vanity metrics. Actionable signals:

| Signal | How captured | Why it matters |
|--------|-------------|---------------|
| **Task completion** | Did agent achieve its goal? | The only metric that ultimately matters |
| **Steps to goal** | Count of actions taken | More steps = more friction |
| **Backtrack events** | Agent hits "back" or re-navigates | Signal of confusion or wrong path taken |
| **Hesitation points** | Agent's reasoning shows uncertainty ("I'm not sure if...") | Maps to real user confusion |
| **Rage indicators** | Repeated clicks on same element, cycling between pages | Frustration proxy |
| **Drop-off point** | Where agent gives up (if patience exhausted) | Exact location of conversion killer |
| **Time-per-step** | Clock time for each action | Identifies slow-loading or complex interactions |
| **Agent commentary** | Free-text reasoning at each step | The *why* behind the behavior |

### Aggregation is where the magic happens

A single agent's session is anecdotal. But when 8/10 personas fail to find the pricing page, or 6/10 backtrack from the same modal, that's a statistically meaningful signal — and it maps directly to a specific UI element that needs fixing.

---

## The Fix Engine (the ambitious part)

Most tools stop at "here's what's wrong." We go further:

1. **Capture the page source** at each friction point (DOM snapshot + CSS)
2. **Feed the issue + page source to Claude** with the prompt: "N out of M simulated users struggled with [specific issue] on this page. Here's the current HTML/CSS. Generate a minimal fix."
3. **Output a diff** that can be applied directly or reviewed

Examples of fixable issues:
- CTA button has low contrast → CSS color change
- Navigation menu hides pricing under unexpected submenu → restructure nav HTML
- Sign-up form has 12 fields on one page → split into multi-step form
- Mobile layout breaks at tablet width → media query fix
- Key action requires scrolling below the fold → reorder sections

**Scope guard:** We limit fixes to HTML/CSS/copy changes. No backend logic, no JS behavior changes. This keeps diffs reviewable and safe.

---

## 6-Hour Timeline

| Hour | Phase | Deliverable |
|------|-------|------------|
| **0-1** | Setup + Core Loop | Single agent can navigate a target site, take screenshots, log reasoning. Use browser-use/stagehand out of the box. |
| **1-2** | Persona System + Concurrency | Multiple agents with different personas run in parallel. Session data captured to structured JSON. |
| **2-3** | Task Framework | Define 3-5 common task types (find info, complete purchase, sign up, change settings). Agents given specific goals. |
| **3-4** | Analysis Engine | Aggregate sessions. Rank friction points by frequency and severity. Generate the UX report. |
| **4-5** | Fix Generation | For top-3 issues, capture DOM, generate fix diffs. Build simple before/after preview. |
| **5-6** | Demo Polish + Edge Cases | Dashboard/CLI output. Run against 2-3 real websites for demo. Handle common failures gracefully. |

### What gets cut if behind schedule

- Hour 5 (fix generation) is the stretch goal. The tool is valuable even as diagnosis-only.
- Fancy dashboard → fall back to CLI output + markdown report
- 10 personas → 3-4 is enough to show the concept

---

## Demo Script (for judging)

1. **Pick a real website** (e-commerce site, SaaS landing page, or a teammate's side project)
2. Run: `usersim https://example.com --personas all --tasks "sign up for free trial" "find pricing" "buy cheapest product"`
3. Show the live agent sessions (split screen, multiple browsers navigating simultaneously)
4. Show the aggregated report: "7/10 agents failed to find pricing. 5/10 abandoned sign-up at the address form. Screen reader user couldn't navigate past the hero section."
5. Show the generated fix diffs
6. Apply one fix, re-run the agents, show improvement

**The money shot:** Side-by-side replay of "confused agent backtracking" vs. "agent sailing through the fixed version."

---

## Why This Wins a Hackathon

1. **Visually compelling** — watching AI agents navigate websites in real-time is inherently interesting
2. **Immediately useful** — point it at any URL and get value. No setup, no integration
3. **Novel framing** — "synthetic user testing" exists in concept but the LLM-vision + persona + fix-generation combo is new
4. **Technically deep** — browser automation + LLM orchestration + concurrent agents + aggregation + code generation
5. **Clear impact story** — "this tool found 3 conversion-killing UX bugs in your website in 5 minutes and wrote the fixes"

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| browser-use/stagehand flaky on complex SPAs | Pre-test on target sites. Have 2-3 backup demo sites. Fall back to simpler sites if needed. |
| LLM agents don't behave like real users | Lean into this honestly — they're a *complement* to real user testing, not a replacement. The value is speed and breadth, not perfect fidelity. |
| Generated fixes are bad/wrong | Frame as "suggestions for review," not "auto-apply." Show diffs, not deployed changes. |
| Rate limits / cost with many concurrent agents | Use Haiku for lightweight agents, Sonnet for analysis. Cache page states. Most sites are 5-10 pages — bounded cost. |
| 6 hours isn't enough | The core loop (agent navigates + logs) works in hour 1 with existing OSS. Everything else is layering value on top. |

---

## Team Composition (ideal: 2-3 people)

- **Person 1:** Agent orchestration — browser-use setup, persona system, concurrency
- **Person 2:** Analysis + reporting — aggregation logic, ranking algorithm, dashboard/output
- **Person 3 (stretch):** Fix engine — DOM capture, diff generation, before/after preview

Works solo too — just cut the fix engine and focus on diagnosis.

---

## Open Questions Worth Exploring

- **Can agents discover tasks on their own?** Instead of specifying "find pricing," just say "explore this site as a new visitor" and see what they naturally try to do. More realistic but harder to aggregate.
- **Can we calibrate against real user data?** If someone has Hotjar/FullStory recordings, we could validate whether synthetic agents get stuck in the same places real users do. This would be a killer follow-up study.
- **Multi-step conversion funnels:** The most valuable application is probably e-commerce checkout flows. Can agents fill in realistic (fake) payment info and navigate the full funnel?
- **Competitive analysis:** Run the same personas/tasks against two competing sites. "Users completed checkout 40% faster on Site A than Site B, primarily because..."
