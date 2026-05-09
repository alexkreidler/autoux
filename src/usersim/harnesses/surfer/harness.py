#!/usr/bin/env python3
"""
Surfer Harness v2 — Hybrid browser agent benchmark.

Architecture (from Surfer 2 paper + surfer-h-cli + Lightcone):
  - Navigator: Claude Sonnet (Anthropic API) — reasoning, planning, action decisions
  - Localizer: Holo3-35B-A3B (vLLM on B200) — vision-grounded coordinate prediction
  - Validator: Claude Sonnet (Anthropic API) — answer verification with VLM-as-judge

Key features:
  1. Hybrid model architecture (smart thinker + fast action model)
  2. Flat action schema for Claude (no coordinate prediction — delegated to Holo)
  3. Holo localizer for precise pixel-level grounding
  4. Circuit breaker for repeated actions (Lightcone)
  5. Step budget warning at 70% (Lightcone)
  6. Multi-stage answer validation (Surfer 2)
  7. Expanded action space: click, type, fill, scroll, go_back, navigate, key_press, wait, answer
  8. page.fill() for reliable form input
  9. JSONL tracing for full replay
  10. Failure-mode-aware system prompt
"""

import base64, json, time, os, sys, re
from dataclasses import dataclass, field, asdict
from typing import Optional
import urllib.request
import urllib.error

# ============================================================================
# Configuration
# ============================================================================

def _load_env():
    """Load ~/.env file into os.environ for keys not already set."""
    env_path = os.path.expanduser("~/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val

_load_env()

# Default vLLM base — Cloudflare Tunnel to VAST.ai B200 in Japan.
_DEFAULT_VLLM_BASE = "https://gpu.alexkreidler.com"

# User-Agent sent on vLLM requests — Cloudflare Bot Fight Mode blocks the
# default Python-urllib UA.
_UA = "surfer-harness/2.0"


@dataclass
class Config:
    # Claude (Navigator + Validator)
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    navigator_model: str = "claude-opus-4-7"
    navigator_temperature: float = 0.3
    navigator_max_tokens: int = 1024

    # vLLM / Holo (Localizer)
    vllm_base: str = os.environ.get("VLLM_BASE", _DEFAULT_VLLM_BASE)
    localizer_model: str = os.environ.get("LOCALIZER_MODEL", "Hcompany/Holo3-35B-A3B")
    localizer_temperature: float = 0.1
    localizer_max_tokens: int = 256

    # Kernel browser-as-a-service
    kernel_api_key: str = os.environ.get("KERNEL_API_KEY", "")
    kernel_api_base: str = "https://api.onkernel.com"
    stealth: bool = False  # Enable stealth mode (residential proxy + auto CAPTCHA solving)

    # Agent loop
    max_steps: int = 25
    viewport_width: int = 1280
    viewport_height: int = 720
    action_delay: float = 1.5
    max_images_in_context: int = 3

    # Reliability
    circuit_breaker_threshold: int = 3
    budget_warning_pct: float = 0.70
    use_validator: bool = True
    max_validation_retries: int = 2

    # Output
    trace_dir: str = os.path.expanduser("~/comphack/benchmarking/data/traces")
    screenshot_dir: str = os.path.expanduser("~/comphack/benchmarking/data/screenshots")
    results_file: str = os.path.expanduser("~/comphack/benchmarking/data/surfer_results.json")

    # Fallback: use Claude for localization too (if vLLM unavailable)
    claude_only: bool = False


# ============================================================================
# System Prompts
# ============================================================================

def make_navigator_prompt(task_instruction: str, viewport_w: int, viewport_h: int) -> str:
    return f"""# Who You Are
{task_instruction}

You are SIMULATING this specific user. Your job is **not** to complete the task
optimally — your job is to behave like *this person* attempting it. That means:
- Make the kinds of mistakes they would make.
- Honor their stated quirks, tech literacy, and patience level.
- If they're rushed, click fast and skim. If they're cautious, hover, re-read, backtrack.
- A perfect, machine-fast trajectory means you're channelling Claude — not the persona.

You happen to be operating a browser. You see screenshots and emit JSON
actions. The mechanics below let you do that. But the persona above is who
*you* are; the action vocabulary is just how you *act*.

## Viewport
The browser viewport is {viewport_w}x{viewport_h} pixels.

## Available Actions
You output a JSON object with your reasoning and chosen action.

### CRITICAL — click vs fill on form inputs
**Clicking a text field does NOT enter text.** Username, password, email, search
boxes — every form input requires `action: "fill"` with a `text` parameter.
A `click` only moves the cursor; it never types.

WRONG (this will leave the field empty even though you reasoned about filling):
  {{"thought": "fill username", "action": "click", "element": "the username field"}}
RIGHT:
  {{"thought": "fill username", "action": "fill", "element": "the username field", "text": "admin"}}

If you ever reason "the field is now filled" right after a `click` action,
you were wrong — the field is still empty. Re-emit as `fill` with text.

### Action list

Actions that need a click target (the localizer will find exact coordinates):
1. **click** — Click on a button, link, checkbox, or other non-text-input element. Requires: "element" (describe PRECISELY what to click, e.g. "the Submit button with blue background", "the 'Comments' link next to '53 comments'"). NEVER use `click` on text input fields — use `fill` instead.
2. **fill** — Fill a form field with text. Required for ALL text inputs, search boxes, password fields, login forms. Requires: "element" (which field), "text" (what to type). Optional: "press_enter" (true/false).

Actions that don't need coordinates:
3. **type** — Type text into the currently focused element. Requires: "text". Optional: "press_enter" (true/false)
4. **scroll** — Scroll the page. Requires: "direction" ("up" or "down")
5. **go_back** — Go back to the previous page
6. **navigate** — Go to a URL. Requires: "text" (the URL). Use this when you know the exact URL.
7. **key_press** — Press a key combo. Requires: "text" (e.g. "Enter", "Tab", "Escape", "Control+a", "Backspace")
8. **wait** — Wait for page to load (2 second pause)
9. **new_tab** — Open a new browser tab. Optional: "text" (URL to navigate to in the new tab)
10. **switch_tab** — Switch to a different tab. Requires: "tab_index" (0-based tab index)
11. **close_tab** — Close current tab and switch to remaining tab
12. **answer** — Submit your final answer. Requires: "text" (your answer). Use ONLY when confident.

## Strategy Guide
- **Prefer fill over click+type** for all form inputs and search boxes — it clears and fills atomically
- **After typing a search query, always press Enter** — use "press_enter": true with type/fill, or key_press "Enter"
- **Be precise with element descriptions** for click — "the 'Issues' tab in the repository navigation bar" is better than "Issues"
- **Use navigate for known URLs** — if you know where to go, navigate directly instead of clicking links
- **Cookie/consent dialogs**: Click "Accept All", "Accept", "Necessary cookies only", or the X button. If stuck, try key_press "Escape"
- **CAPTCHAs**: If you encounter a CAPTCHA, try navigating directly to the target URL or use a different approach
- **Anti-bot pages**: If blocked, try navigate to a direct URL, or try a mobile/alternate version of the site
- **Clearing text fields**: key_press "Control+a" then type the new text, OR use fill which clears automatically
- **If stuck after 2-3 identical attempts**: Try a COMPLETELY different approach — different URL, different element, different method
- **Form submission**: After filling all fields, look for and click the Submit/Send button. Verify the form was submitted by checking if the page changed.
- **Multi-step tasks**: Keep track of information you've already gathered. Don't revisit pages unnecessarily.
- **Multiple sites**: Use new_tab to open a second site, switch_tab to go between them. Much better than navigating back and forth.
- **When you have the answer, submit immediately** — don't take extra steps
- **Form fields may not show values in screenshots** even when filled correctly. Trust the action result messages. After filling all fields, click Submit.

## Output Format
Always respond with a single JSON object. Examples:
{{"thought": "I need to log in. The username field is a text input — must use fill.", "action": "fill", "element": "the username text input", "text": "admin"}}
{{"thought": "Username is filled. Now the password field.", "action": "fill", "element": "the password input", "text": "admin"}}
{{"thought": "Both fields filled. Now click the submit button.", "action": "click", "element": "the 'Log In' button at the bottom of the form"}}
{{"thought": "I need to search.", "action": "fill", "element": "the search box", "text": "my query", "press_enter": true}}
{{"thought": "I can see the answer.", "action": "answer", "text": "the answer"}}"""


VALIDATOR_PROMPT = """You are an answer validator for a browser automation agent.

Given the original task, the agent's proposed answer, and recent screenshots of the browser, determine if the answer is correct and complete.

Evaluate:
1. Does the answer address what was asked?
2. Is the information consistent with what's visible in the screenshots?
3. Is the answer complete (all parts of the question answered)?

Respond with EXACTLY one of:
- "VALID: <brief explanation>" if the answer is correct and complete
- "INVALID: <what's wrong and what the agent should do instead>"

Screenshots take precedence over the text answer if they contradict."""


LOCALIZER_PROMPT_TEMPLATE = """You are a UI element localizer. Given a screenshot and an element description, output the (x, y) pixel coordinates of that element's center.

The viewport is {width}x{height} pixels.
Output ONLY a JSON object: {{"x": <pixel_x>, "y": <pixel_y>}}

Element to locate: {element_description}"""


SCHEMA_REMINDER = '\nRespond with valid JSON: {"thought": "...", "action": "...", ...}'


# ============================================================================
# JSONL Tracer
# ============================================================================

class Tracer:
    def __init__(self, trace_dir: str, task_name: str, label: str):
        os.makedirs(trace_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(trace_dir, f"{label}_{task_name}_{ts}.jsonl")
        self.f = open(self.path, "w")
        self.start_time = time.time()

    def log(self, event_type: str, data: dict = None):
        entry = {
            "t": round(time.time() - self.start_time, 3),
            "ts": time.strftime("%H:%M:%S"),
            "event": event_type,
        }
        if data:
            entry.update(data)
        self.f.write(json.dumps(entry, default=str) + "\n")
        self.f.flush()

    def close(self):
        self.f.close()


# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitBreaker:
    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.recent_actions: list[str] = []

    def action_signature(self, action_data: dict) -> str:
        action = action_data.get("action", "")
        if action == "scroll":
            return ""  # scrolling repeatedly is normal
        sig_parts = [action]
        for key in ["element", "text", "selector", "direction"]:
            if key in action_data and action_data[key] is not None:
                sig_parts.append(f"{key}={action_data[key]}")
        return "|".join(sig_parts)

    def check(self, action_data: dict) -> bool:
        sig = self.action_signature(action_data)
        if not sig:
            return False
        self.recent_actions.append(sig)
        if len(self.recent_actions) > self.threshold:
            self.recent_actions = self.recent_actions[-self.threshold:]
        if len(self.recent_actions) >= self.threshold:
            return len(set(self.recent_actions)) == 1
        return False

    @property
    def redirect_message(self) -> str:
        return (
            "You are repeating the same action and it is not working. "
            "Try a completely different approach: click somewhere else, "
            "use a different method, scroll to find the element, "
            "or if the task seems blocked, report what you can see and use the answer action."
        )


# ============================================================================
# Kernel Browser Client
# ============================================================================

class KernelBrowser:
    def __init__(self, config: Config):
        self.config = config
        self.session_id: Optional[str] = None
        self.live_url: Optional[str] = None

    def _request(self, method: str, path: str, body=None, timeout=30):
        url = f"{self.config.kernel_api_base}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.config.kernel_api_key}",
            "Content-Type": "application/json",
        })
        resp = urllib.request.urlopen(req, timeout=timeout)
        ct = resp.headers.get("Content-Type", "")
        raw = resp.read()
        if "json" in ct:
            return json.loads(raw)
        return raw

    def create(self, stealth: bool = False) -> str:
        body = {
            "timeout_seconds": 600,
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
        }
        if stealth or self.config.stealth:
            body["stealth"] = True
        resp = self._request("POST", "/browsers", body)
        self.session_id = resp["session_id"]
        self.live_url = resp.get("browser_live_view_url", "N/A")
        return self.session_id

    def destroy(self):
        if self.session_id:
            try:
                self._request("DELETE", f"/browsers/{self.session_id}", timeout=10)
            except Exception:
                pass
            self.session_id = None

    def screenshot(self) -> str:
        raw = self._request("POST", f"/browsers/{self.session_id}/computer/screenshot", {})
        return base64.b64encode(raw).decode() if isinstance(raw, bytes) else raw

    def _exec(self, code: str):
        resp = self._request("POST", f"/browsers/{self.session_id}/playwright/execute",
                             {"code": code})
        if not resp.get("success"):
            raise RuntimeError(resp.get("error", "playwright exec failed"))
        return resp.get("result")

    def navigate(self, url: str):
        escaped = url.replace("\\", "\\\\").replace('"', '\\"')
        self._exec(f'await page.goto("{escaped}", {{waitUntil: "domcontentloaded", timeout: 15000}}); return {{ok: true}}')

    def click(self, x: int, y: int):
        self._exec(f'await page.mouse.click({x}, {y}); return {{ok: true}}')

    def type_text(self, text: str, press_enter: bool = False):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        self._exec(f'await page.keyboard.type("{escaped}"); return {{ok: true}}')
        if press_enter:
            time.sleep(0.3)
            self._exec('await page.keyboard.press("Enter"); return {ok: true}')

    def fill_focused(self, text: str, press_enter: bool = False):
        """Fill the currently focused element atomically via locator.fill().

        This bypasses character-by-character typing, avoiding autocomplete
        hijacking on sites like Google.  Raises on failure so callers can
        fall back to keyboard.type() for contenteditable / non-input elements.
        """
        escaped = text.replace("\\", "\\\\").replace("'", "\\'")
        self._exec(
            f"await page.locator(':focus').fill('{escaped}'); return {{ok: true}}"
        )
        if press_enter:
            time.sleep(0.3)
            self._exec('await page.keyboard.press("Enter"); return {ok: true}')

    def fill(self, selector: str, text: str, press_enter: bool = False):
        escaped_sel = selector.replace("\\", "\\\\").replace("'", "\\'")
        escaped_text = text.replace("\\", "\\\\").replace("'", "\\'")
        self._exec(f"await page.fill('{escaped_sel}', '{escaped_text}'); return {{ok: true}}")
        if press_enter:
            time.sleep(0.3)
            self._exec('await page.keyboard.press("Enter"); return {ok: true}')

    def scroll(self, direction: str, amount: int = 3):
        delta = -amount * 200 if direction == "up" else amount * 200
        self._exec(f'await page.mouse.wheel(0, {delta}); return {{ok: true}}')

    def go_back(self):
        try:
            self._exec('await page.goBack({timeout: 15000}); return {ok: true}')
        except RuntimeError:
            # goBack can timeout if there's no history; just navigate back
            self._exec('return {ok: true, note: "no history"}')

    def key_press(self, key: str):
        # Normalize common key name variants for Playwright
        key_map = {
            "Ctrl": "Control", "ctrl": "Control",
            "Ctrl+a": "Control+a", "Ctrl+A": "Control+a",
            "Ctrl+c": "Control+c", "Ctrl+v": "Control+v",
            "Return": "Enter", "return": "Enter",
            "Esc": "Escape", "esc": "Escape",
            "Del": "Delete", "del": "Delete",
        }
        key = key_map.get(key, key)
        escaped = key.replace('"', '\\"')
        self._exec(f'await page.keyboard.press("{escaped}"); return {{ok: true}}')

    def get_url(self) -> str:
        return self._exec('return page.url()')

    def fill_by_label(self, label_text: str, text: str, press_enter: bool = False):
        """Try to fill an input by its associated label text or placeholder.
        Uses Playwright's getByLabel/getByPlaceholder for reliable form filling."""
        escaped_label = label_text.replace("\\", "\\\\").replace("'", "\\'")
        escaped_text = text.replace("\\", "\\\\").replace("'", "\\'")
        self._exec(
            f"const el = page.getByLabel('{escaped_label}', {{exact: false}}); "
            f"if (await el.count() > 0) {{ await el.first().fill('{escaped_text}'); }} "
            f"else {{ "
            f"  const ph = page.getByPlaceholder('{escaped_label}', {{exact: false}}); "
            f"  if (await ph.count() > 0) {{ await ph.first().fill('{escaped_text}'); }} "
            f"  else {{ throw new Error('No input found for label: {escaped_label}'); }} "
            f"}} "
            f"return {{ok: true}};"
        )
        if press_enter:
            time.sleep(0.3)
            self._exec('await page.keyboard.press("Enter"); return {ok: true}')

    # --- Tab management ---
    def list_tabs(self) -> list:
        """List all open tabs with their URLs and titles."""
        return self._exec(
            'const pages = context.pages(); '
            'const tabs = []; '
            'for (let i = 0; i < pages.length; i++) { '
            '  tabs.push({index: i, url: pages[i].url(), title: await pages[i].title()}); '
            '} '
            'return tabs;'
        )

    def switch_tab(self, index: int):
        """Switch to tab by index. Updates the `page` variable."""
        self._exec(
            f'const pages = context.pages(); '
            f'if ({index} < pages.length) {{ '
            f'  page = pages[{index}]; '
            f'  await page.bringToFront(); '
            f'}} '
            f'return {{ok: true, url: page.url()}};'
        )

    def close_tab(self, index: int = -1):
        """Close a tab by index (-1 = current). Switches to first remaining tab."""
        self._exec(
            f'const pages = context.pages(); '
            f'const idx = {index} < 0 ? pages.indexOf(page) : {index}; '
            f'if (idx >= 0 && idx < pages.length) {{ '
            f'  await pages[idx].close(); '
            f'  const remaining = context.pages(); '
            f'  if (remaining.length > 0) {{ page = remaining[0]; await page.bringToFront(); }} '
            f'}} '
            f'return {{ok: true, tabs: context.pages().length}};'
        )

    def new_tab(self, url: str = "") -> int:
        """Open a new tab, optionally navigating to a URL. Returns new tab count."""
        escaped = url.replace("\\", "\\\\").replace('"', '\\"')
        result = self._exec(
            f'const newPage = await context.newPage(); '
            f'page = newPage; '
            f'await page.bringToFront(); '
            + (f'await page.goto("{escaped}", {{waitUntil: "domcontentloaded", timeout: 15000}}); ' if url else '')
            + f'return {{ok: true, tabs: context.pages().length, url: page.url()}};'
        )
        return result

    # --- Form verification ---
    def verify_fill(self, selector: str) -> str:
        """Check the current value of a form field by CSS selector."""
        escaped_sel = selector.replace("\\", "\\\\").replace("'", "\\'")
        return self._exec(
            f"const el = await page.querySelector('{escaped_sel}'); "
            f"return el ? await el.inputValue() : null;"
        )


# ============================================================================
# Anthropic Claude Client (Navigator + Validator)
# ============================================================================

class ClaudeClient:
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.anthropic_api_key

    def _call(self, system: str, messages: list, max_tokens: int = 1024,
              temperature: float = 0.3) -> tuple[str, float, dict]:
        """Call Claude API. Returns (content, elapsed_seconds, usage_dict)."""
        payload = {
            "model": self.config.navigator_model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        # Opus 4.6+ doesn't accept temperature — only add for non-opus models
        model = self.config.navigator_model.lower()
        if "opus" not in model:
            payload["temperature"] = temperature

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )

        start = time.perf_counter()
        timeout = 180 if "opus" in model else 120
        resp_raw = urllib.request.urlopen(req, timeout=timeout).read()
        elapsed = time.perf_counter() - start

        resp = json.loads(resp_raw)

        # Extract text from content blocks
        content = ""
        for block in resp.get("content", []):
            if block.get("type") == "text":
                content += block["text"]

        usage = resp.get("usage", {})
        return content, elapsed, {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
        }

    def navigate(self, system_prompt: str, messages: list) -> tuple[str, float, dict]:
        """Call navigator model."""
        return self._call(
            system_prompt, messages,
            max_tokens=self.config.navigator_max_tokens,
            temperature=self.config.navigator_temperature,
        )

    def validate(self, task_instruction: str, answer: str,
                 recent_screenshots: list[str]) -> tuple[bool, str, float]:
        """Validate answer with VLM-as-judge. Returns (is_valid, rationale, elapsed)."""
        content_parts = [
            {"type": "text", "text": f"Task: {task_instruction}\n\nAgent's answer: {answer}\n\nRecent browser screenshots:"},
        ]
        for i, img_b64 in enumerate(recent_screenshots[-3:]):
            content_parts.append({"type": "text", "text": f"\nScreenshot {i+1}:"})
            content_parts.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": img_b64}
            })
        content_parts.append({"type": "text", "text": "\nIs this answer correct and complete?"})

        messages = [{"role": "user", "content": content_parts}]
        try:
            raw, elapsed, _ = self._call(VALIDATOR_PROMPT, messages, max_tokens=300, temperature=0.0)
            is_valid = "VALID" in raw.upper() and "INVALID" not in raw.upper()
            return is_valid, raw.strip(), elapsed
        except Exception as e:
            return True, f"Validation error (accepted): {e}", 0.0


# ============================================================================
# Holo Localizer Client (vLLM)
# ============================================================================

class HoloLocalizer:
    def __init__(self, config: Config):
        self.config = config

    def localize(self, screenshot_b64: str, element_description: str) -> tuple[int, int, float]:
        """Given a screenshot and element description, return (pixel_x, pixel_y, elapsed).
        Holo outputs coordinates; we parse them. Returns fallback coords if parsing fails."""

        prompt = LOCALIZER_PROMPT_TEMPLATE.format(
            width=self.config.viewport_width,
            height=self.config.viewport_height,
            element_description=element_description,
        )

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{screenshot_b64}"
                }},
            ]},
        ]

        payload = {
            "model": self.config.localizer_model,
            "messages": messages,
            "temperature": self.config.localizer_temperature,
            "max_tokens": self.config.localizer_max_tokens,
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.config.vllm_base}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": _UA},
        )

        start = time.perf_counter()
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        elapsed = time.perf_counter() - start

        raw = resp["choices"][0]["message"]["content"]
        x, y, was_fallback, elapsed = self._parse_coordinates(raw, elapsed)

        if was_fallback:
            # Signal that Holo failed so caller can try Claude fallback
            raise ValueError(f"Holo returned center fallback. Raw: {raw[:200]}")

        return x, y, elapsed

    def _parse_coordinates(self, raw: str, elapsed: float) -> tuple[int, int, bool, float]:
        """Parse coordinates from Holo output. Returns (x, y, was_fallback, elapsed)."""
        cx, cy = self.config.viewport_width // 2, self.config.viewport_height // 2

        # Try JSON parse
        try:
            data = json.loads(raw)
            x = int(data.get("x", cx))
            y = int(data.get("y", cy))
            return x, y, (x == cx and y == cy), elapsed
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        # Try Click(X, Y) pattern (surfer-h-cli format)
        match = re.search(r'Click\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', raw, re.IGNORECASE)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            return x, y, False, elapsed

        # Try coordinate patterns: (X, Y) or x=N y=N
        match = re.search(r'\(?\s*(\d+)\s*,\s*(\d+)\s*\)?', raw)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            return x, y, False, elapsed

        # Fallback: center of screen
        return cx, cy, True, elapsed

    def health_check(self) -> bool:
        try:
            req = urllib.request.Request(
                f"{self.config.vllm_base}/health",
                headers={"User-Agent": _UA},
            )
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            return False


# ============================================================================
# Coordinate Fallback: Claude-based localization
# ============================================================================

class ClaudeLocalizer:
    """Fallback localizer using Claude when Holo/vLLM is unavailable."""
    def __init__(self, claude: ClaudeClient, config: Config):
        self.claude = claude
        self.config = config

    def localize(self, screenshot_b64: str, element_description: str) -> tuple[int, int, float]:
        prompt = (
            f"Look at this screenshot of a browser ({self.config.viewport_width}x{self.config.viewport_height}). "
            f"Find the center of this element: \"{element_description}\". "
            f"Respond with ONLY a JSON object: {{\"x\": <pixel_x>, \"y\": <pixel_y>}}"
        )
        messages = [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": screenshot_b64
            }},
        ]}]

        try:
            raw, elapsed, _ = self.claude._call(
                "You are a UI element localizer. Output ONLY JSON coordinates.",
                messages, max_tokens=100, temperature=0.0
            )
            # Parse coordinates
            match = re.search(r'"x"\s*:\s*(\d+)', raw)
            match_y = re.search(r'"y"\s*:\s*(\d+)', raw)
            if match and match_y:
                return int(match.group(1)), int(match_y.group(1)), elapsed
        except Exception:
            pass
        return self.config.viewport_width // 2, self.config.viewport_height // 2, 0.0


# ============================================================================
# Task Definition
# ============================================================================

@dataclass
class Task:
    name: str
    description: str
    start_url: str
    instruction: str
    verify: str = ""
    max_steps: int = 25
    stealth: bool = False  # enable stealth mode (residential proxy + CAPTCHA solving)


# ============================================================================
# Agent Loop
# ============================================================================

@dataclass
class StepResult:
    step: int
    action: str
    thought: str
    nav_elapsed: float
    loc_elapsed: float = 0.0
    raw_action: dict = field(default_factory=dict)
    result: str = ""


@dataclass
class TaskResult:
    task: str
    answer: Optional[str]
    steps: int
    total_time: float
    nav_tokens: int  # navigator (Claude) tokens
    loc_calls: int   # localizer calls
    success: bool
    verify_match: Optional[bool]
    validation_result: Optional[str] = None
    circuit_breaker_tripped: bool = False
    budget_warning_sent: bool = False
    step_details: list = field(default_factory=list)


def _build_claude_messages(screenshot_b64: str, step_num: int,
                           prev_messages: list, max_images: int) -> list:
    """Build message list for Claude with screenshot, evicting old images."""
    img_content = [
        {"type": "text", "text": f"[Step {step_num}] Current browser screenshot:"},
        {"type": "image", "source": {
            "type": "base64", "media_type": "image/png", "data": screenshot_b64
        }},
        {"type": "text", "text": SCHEMA_REMINDER},
    ]
    messages = prev_messages + [{"role": "user", "content": img_content}]

    # Evict old images
    img_count = 0
    for i in range(len(messages) - 1, -1, -1):
        content = messages[i].get("content")
        if isinstance(content, list):
            has_img = any(
                isinstance(c, dict) and c.get("type") == "image"
                for c in content
            )
            if has_img:
                img_count += 1
                if img_count > max_images:
                    messages[i] = {"role": messages[i]["role"],
                                   "content": "[previous screenshot evicted]"}
    return messages


def run_task(config: Config, task: Task, browser: KernelBrowser,
             claude: ClaudeClient, localizer, label: str = "v2") -> TaskResult:
    """Run a single task through the hybrid agent loop."""

    tracer = Tracer(config.trace_dir, task.name, label)
    circuit_breaker = CircuitBreaker(config.circuit_breaker_threshold)

    # Screenshot directory
    ss_dir = os.path.join(config.screenshot_dir, label, task.name)
    os.makedirs(ss_dir, exist_ok=True)

    # System prompt
    system_prompt = make_navigator_prompt(
        task.instruction, config.viewport_width, config.viewport_height
    )

    claude_messages = []  # conversation history (role: user/assistant)
    recent_screenshots: list[str] = []
    nav_tokens = {"prompt_tokens": 0, "completion_tokens": 0}
    loc_calls = 0
    steps: list[StepResult] = []
    answer = None
    budget_warning_sent = False
    circuit_tripped = False
    validation_result = None
    validation_retries = 0
    task_start = time.perf_counter()

    # Navigate to start URL
    tracer.log("task_started", {"task": task.name, "url": task.start_url})
    print(f"    Navigating to {task.start_url}", flush=True)
    try:
        browser.navigate(task.start_url)
    except Exception as e:
        print(f"    [WARN] Navigate error (continuing): {e}", flush=True)
    time.sleep(2)

    effective_max_steps = task.max_steps or config.max_steps

    for step_num in range(1, effective_max_steps + 1):
        # --- Budget warning ---
        pct = step_num / effective_max_steps
        if not budget_warning_sent and pct >= config.budget_warning_pct:
            budget_warning_sent = True
            remaining = effective_max_steps - step_num
            budget_msg = (
                f"Budget warning: {step_num}/{effective_max_steps} steps used, "
                f"{remaining} remaining. Wrap up and report your answer now."
            )
            claude_messages.append({"role": "user", "content": budget_msg})
            tracer.log("budget_warning", {"step": step_num, "remaining": remaining})
            print(f"    [Step {step_num}] BUDGET WARNING: {remaining} steps left", flush=True)

        # --- Screenshot ---
        try:
            img_b64 = browser.screenshot()
            recent_screenshots.append(img_b64)
            if len(recent_screenshots) > 5:
                recent_screenshots = recent_screenshots[-5:]
        except Exception as e:
            print(f"    [Step {step_num}] Screenshot failed: {e}", flush=True)
            tracer.log("screenshot_failed", {"error": str(e)})
            break

        # Save screenshot
        try:
            ss_path = os.path.join(ss_dir, f"step_{step_num:02d}.png")
            with open(ss_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
        except Exception:
            pass

        tracer.log("screenshot", {"step": step_num})

        # --- Call Claude Navigator ---
        messages_for_call = _build_claude_messages(
            img_b64, step_num, claude_messages, config.max_images_in_context
        )

        try:
            raw, nav_elapsed, usage = claude.navigate(system_prompt, messages_for_call)
        except Exception as e:
            print(f"    [Step {step_num}] Navigator failed: {e}", flush=True)
            tracer.log("navigator_failed", {"error": str(e)})
            break

        nav_tokens["prompt_tokens"] += usage.get("prompt_tokens", 0)
        nav_tokens["completion_tokens"] += usage.get("completion_tokens", 0)

        # --- Parse navigator response ---
        action_data = None
        # Try to extract JSON from response
        try:
            action_data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to find JSON in the text
            match = re.search(r'\{[^{}]*"action"[^{}]*\}', raw, re.DOTALL)
            if match:
                try:
                    action_data = json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        if not action_data or "action" not in action_data:
            print(f"    [Step {step_num}] Parse fail: {raw[:200]}", flush=True)
            tracer.log("parse_failed", {"raw": raw[:500]})
            # Add to history and ask for retry
            claude_messages.append({"role": "user", "content": [
                {"type": "text", "text": f"[Step {step_num}] Current browser screenshot:"},
                {"type": "image", "source": {
                    "type": "base64", "media_type": "image/png", "data": img_b64
                }},
                {"type": "text", "text": SCHEMA_REMINDER},
            ]})
            claude_messages.append({"role": "assistant", "content": raw})
            claude_messages.append({"role": "user", "content":
                'Your response was not valid JSON. Respond with: {"thought": "...", "action": "...", ...}'
            })
            continue

        action = action_data.get("action", "unknown")
        thought = action_data.get("thought", "")
        loc_elapsed = 0.0

        # Add to conversation history
        claude_messages.append({"role": "user", "content": [
            {"type": "text", "text": f"[Step {step_num}] Current browser screenshot:"},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": img_b64
            }},
            {"type": "text", "text": SCHEMA_REMINDER},
        ]})
        claude_messages.append({"role": "assistant", "content": json.dumps(action_data)})

        tracer.log("navigator_action", {
            "step": step_num, "action": action, "thought": thought[:200],
            "nav_elapsed": round(nav_elapsed, 2), "data": action_data,
        })

        # --- Circuit breaker ---
        if circuit_breaker.check(action_data):
            circuit_tripped = True
            print(f"    [Step {step_num}] CIRCUIT BREAKER tripped", flush=True)
            tracer.log("circuit_breaker", {"action": action})
            claude_messages.append({"role": "user", "content": circuit_breaker.redirect_message})
            steps.append(StepResult(step_num, action, thought, nav_elapsed, 0, action_data, "circuit_breaker"))
            continue

        # --- Handle answer ---
        if action == "answer":
            proposed_answer = action_data.get("text", "")

            if config.use_validator and validation_retries < config.max_validation_retries:
                is_valid, rationale, val_elapsed = claude.validate(
                    task.instruction, proposed_answer, recent_screenshots
                )
                validation_result = rationale
                tracer.log("validation", {
                    "valid": is_valid, "rationale": rationale[:300],
                    "elapsed": round(val_elapsed, 2)
                })

                if is_valid:
                    answer = proposed_answer
                    steps.append(StepResult(step_num, action, thought, nav_elapsed, 0, action_data, "answer_validated"))
                    print(f"    [Step {step_num}] ANSWER VALIDATED: {proposed_answer[:100]}", flush=True)
                    break
                else:
                    validation_retries += 1
                    print(f"    [Step {step_num}] ANSWER REJECTED: {rationale[:100]}", flush=True)
                    claude_messages.append({"role": "user", "content":
                        f"Your answer was rejected by the validator: {rationale}\n"
                        f"Continue and find the correct answer."
                    })
                    steps.append(StepResult(step_num, action, thought, nav_elapsed, 0, action_data, "answer_rejected"))
                    continue
            else:
                answer = proposed_answer
                steps.append(StepResult(step_num, action, thought, nav_elapsed, 0, action_data, "answer_accepted"))
                print(f"    [Step {step_num}] ANSWER: {proposed_answer[:100]}", flush=True)
                break

        # --- Localize (for click/fill actions) ---
        # Chain: try primary localizer -> fall back to Claude localizer
        px, py = None, None
        if action in ("click", "fill"):
            element_desc = action_data.get("element", "the element")
            loc_source = "unknown"
            try:
                px, py, loc_elapsed = localizer.localize(img_b64, element_desc)
                loc_calls += 1
                loc_source = "holo"
                tracer.log("localized", {
                    "element": element_desc, "px": px, "py": py,
                    "source": loc_source, "elapsed": round(loc_elapsed, 2)
                })
            except Exception as e:
                # Holo failed or returned center — try Claude fallback
                print(f"    [Step {step_num}] Primary localizer failed, trying Claude: {str(e)[:80]}", flush=True)
                try:
                    claude_loc = ClaudeLocalizer(claude, config)
                    px, py, loc_elapsed = claude_loc.localize(img_b64, element_desc)
                    loc_calls += 1
                    loc_source = "claude"
                    tracer.log("localized_fallback", {
                        "element": element_desc, "px": px, "py": py,
                        "source": "claude", "elapsed": round(loc_elapsed, 2)
                    })
                except Exception as e2:
                    print(f"    [Step {step_num}] Claude localizer also failed: {e2}", flush=True)
                    tracer.log("localizer_failed", {"error": str(e2)})
                    px = config.viewport_width // 2
                    py = config.viewport_height // 2
                    loc_source = "fallback_center"

        # --- Execute action ---
        result_msg = "ok"
        try:
            if action == "click":
                browser.click(px, py)
                time.sleep(config.action_delay)
                result_msg = f"Clicked at pixel ({px}, {py})"

            elif action == "type":
                text = action_data.get("text", "")
                press_enter = action_data.get("press_enter", False)
                try:
                    browser.fill_focused(text, press_enter)
                except Exception:
                    # Fallback for contenteditable / non-input elements
                    browser.type_text(text, press_enter)
                time.sleep(config.action_delay)
                result_msg = f"Typed: {text[:50]}"

            elif action == "fill":
                text = action_data.get("text", "")
                selector = action_data.get("selector", "")
                element_desc = action_data.get("element", "")
                press_enter = action_data.get("press_enter", False)
                filled = False

                # Strategy 1: explicit CSS selector
                if selector and not filled:
                    try:
                        browser.fill(selector, text, press_enter)
                        filled = True
                    except Exception:
                        pass

                # Strategy 2: Playwright label-based locator from element description
                if not filled and element_desc:
                    try:
                        browser.fill_by_label(element_desc, text, press_enter)
                        filled = True
                    except Exception:
                        pass

                # Strategy 3: click localized coordinates, then fill focused
                if not filled and px is not None:
                    browser.click(px, py)
                    time.sleep(0.5)
                    try:
                        browser.fill_focused(text, press_enter)
                        filled = True
                    except Exception:
                        browser.type_text(text, press_enter)
                        filled = True

                time.sleep(config.action_delay)
                result_msg = f"Filled '{element_desc[:30]}' with: {text[:40]}"

            elif action == "scroll":
                direction = action_data.get("direction", "down")
                browser.scroll(direction)
                time.sleep(config.action_delay)
                result_msg = f"Scrolled {direction}"

            elif action == "go_back":
                browser.go_back()
                time.sleep(config.action_delay)
                result_msg = "Went back"

            elif action == "navigate":
                url = action_data.get("text", "")
                browser.navigate(url)
                time.sleep(config.action_delay + 1)
                result_msg = f"Navigated to {url[:80]}"

            elif action == "key_press":
                key = action_data.get("text", "Enter")
                browser.key_press(key)
                time.sleep(config.action_delay)
                result_msg = f"Pressed {key}"

            elif action == "wait":
                time.sleep(2)
                result_msg = "Waited"

            elif action == "new_tab":
                url = action_data.get("text", "")
                browser.new_tab(url)
                time.sleep(config.action_delay + 1)
                result_msg = f"Opened new tab" + (f" at {url[:60]}" if url else "")

            elif action == "switch_tab":
                idx = action_data.get("tab_index", 0)
                browser.switch_tab(idx)
                time.sleep(config.action_delay)
                result_msg = f"Switched to tab {idx}"

            elif action == "close_tab":
                browser.close_tab()
                time.sleep(config.action_delay)
                result_msg = "Closed current tab"

            else:
                result_msg = f"Unknown action: {action}"

        except Exception as e:
            result_msg = f"Action failed: {e}"
            print(f"    [Step {step_num}] Action error: {e}", flush=True)

        total_step_time = nav_elapsed + loc_elapsed
        print(f"    [Step {step_num}] {action}: {thought[:70]}  "
              f"(nav={nav_elapsed:.1f}s loc={loc_elapsed:.1f}s)", flush=True)

        tracer.log("action_executed", {"step": step_num, "result": result_msg[:200]})
        steps.append(StepResult(step_num, action, thought, nav_elapsed, loc_elapsed, action_data, result_msg))

        # Brief action result for Claude context
        claude_messages.append({"role": "user", "content": f"Action result: {result_msg}"})

    task_elapsed = time.perf_counter() - task_start
    tracer.log("task_completed", {
        "answer": answer, "steps": len(steps),
        "elapsed": round(task_elapsed, 2), "success": answer is not None,
    })
    tracer.close()

    verify_match = None
    if task.verify and answer:
        verify_match = task.verify.lower() in answer.lower()

    return TaskResult(
        task=task.name,
        answer=answer,
        steps=len(steps),
        total_time=task_elapsed,
        nav_tokens=nav_tokens["prompt_tokens"] + nav_tokens["completion_tokens"],
        loc_calls=loc_calls,
        success=answer is not None,
        verify_match=verify_match,
        validation_result=validation_result,
        circuit_breaker_tripped=circuit_tripped,
        budget_warning_sent=budget_warning_sent,
        step_details=[asdict(s) for s in steps],
    )


# ============================================================================
# Task Definitions
# ============================================================================

EASY_TASKS = [
    Task("hackernews_top", "Read HN front page",
         "https://news.ycombinator.com",
         "What is the title of the #1 story on Hacker News right now?"),
    Task("wikipedia_lookup", "Find a fact on Wikipedia",
         "https://en.wikipedia.org/wiki/Tokyo",
         "What is the population of Tokyo listed on this Wikipedia page? Report the number."),
    Task("github_stars", "Find star count on GitHub",
         "https://github.com/vllm-project/vllm",
         "How many stars does this GitHub repository have? Report the number."),
    Task("weather_check", "Check weather",
         "https://wttr.in/Tokyo",
         "What is the current temperature in Tokyo shown on this page?"),
    Task("calculator", "Use Google calculator",
         "https://www.google.com",
         "Type '1337 * 42' into the Google search box and press Enter. Report the calculator result.",
         verify="56154"),
    Task("reddit_browse", "Browse Reddit",
         "https://old.reddit.com",
         "What is the title of the top post on this Reddit page?"),
    Task("imdb_rating", "Find IMDB rating",
         "https://www.imdb.com/title/tt0111161/",
         "What is the IMDB rating of The Shawshank Redemption shown on this page?",
         verify="9"),
    Task("arxiv_search", "Search arXiv",
         "https://arxiv.org/search/?searchtype=all&query=mixture+of+experts",
         "What is the title of the first search result on this arXiv page?"),
    Task("hn_search", "Search Hacker News",
         "https://hn.algolia.com",
         "Search for 'B200 GPU' using the search box and report the title of the first result."),
    Task("read_table", "Read a data table",
         "https://en.wikipedia.org/wiki/NVIDIA",
         "Scroll down to find the 'Products' or GPU section. What year was the GeForce 256 released?",
         verify="1999"),
]

HARD_TASKS = [
    Task("wiki_comparison", "Compare two Wikipedia articles and do math",
         "https://en.wikipedia.org/wiki/Mars",
         "Find the orbital period of Mars on this page (in Earth days). "
         "Then navigate to the Wikipedia page for Venus and find its orbital period. "
         "Report both numbers and which planet has the longer orbital period.",
         verify="mars", max_steps=30),
    Task("hn_deep_dive", "Navigate HN comments and extract info",
         "https://news.ycombinator.com",
         "Find the #1 story on Hacker News. Click on the comments link (not the article). "
         "Report: (1) the title of the story, (2) how many comments it has, "
         "and (3) the username of the person who posted it.",
         max_steps=20),
    Task("github_multi_nav", "Navigate GitHub repo structure",
         "https://github.com/vllm-project/vllm",
         "Navigate to the vllm GitHub repo. Click on the 'Issues' tab. "
         "Report: (1) how many open issues there are, and (2) the title of the most recent issue.",
         max_steps=20),
    Task("multi_search_compare", "Search and compare across sites",
         "https://www.google.com",
         "Search Google for 'population of Paris 2024'. Find the answer. "
         "Then search for 'population of London 2024'. Find that answer. "
         "Report both populations and which city is larger.",
         verify="london", max_steps=30),
    Task("arxiv_paper_details", "Find paper details on arXiv",
         "https://arxiv.org",
         "Search arXiv for 'attention is all you need'. "
         "Click on the first result to go to the paper's abstract page. "
         "Report: (1) the full title, (2) the first author's name, "
         "(3) the submission date, and (4) the primary subject category.",
         verify="vaswani", max_steps=30),
    Task("form_interaction", "Fill out and submit a form",
         "https://httpbin.org/forms/post",
         "Fill out this form with: Customer name='John Doe', "
         "Telephone='555-1234', E-mail='john@example.com'. "
         "Select 'Medium' for pizza size and check 'Mushroom' as a topping. "
         "Click the Submit button. "
         "Note: filled values may not appear in screenshots — trust action result messages. "
         "After clicking Submit, the page will change. Report what the response page shows.",
         verify="john", max_steps=25),
    Task("wikipedia_table_extract", "Extract and reason over a Wikipedia table",
         "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)",
         "Find the GDP table on this page. Report the top 5 countries by GDP "
         "and their GDP values. Then calculate: what percentage of #1's GDP is #5's GDP?",
         max_steps=20),
    Task("stackoverflow_search", "Search StackOverflow and extract answer",
         "https://stackoverflow.com",
         "Search StackOverflow for 'python sort dictionary by value'. "
         "Click on the top result. Report the accepted answer's code snippet "
         "and how many upvotes it has.",
         verify="sorted", max_steps=25, stealth=True),
    Task("maps_distance", "Look up distance between two cities",
         "https://www.google.com/maps",
         "Use Google Maps to find the driving distance from San Francisco to Los Angeles. "
         "Report the distance in miles and the estimated driving time.",
         max_steps=25),
    Task("news_cross_reference", "Cross-reference news across two sources",
         "https://news.ycombinator.com",
         "Find the #1 story on Hacker News and note its title. "
         "Then use new_tab to open Google News (news.google.com) in a second tab. "
         "Search for the same topic on Google News. "
         "Use switch_tab to go between tabs if needed. "
         "Report: (1) the HN title, (2) whether Google News has coverage of the same story, "
         "and (3) the headline of the most relevant Google News result.",
         max_steps=30),
]


# ============================================================================
# Benchmark Runner
# ============================================================================

def run_benchmark(config: Config, tasks: list[Task], label: str = "benchmark"):
    """Run a full benchmark suite."""

    print("=" * 70, flush=True)
    print(f"SURFER HARNESS v2 — {label.upper()}", flush=True)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"Navigator: {config.navigator_model} (Claude)", flush=True)
    print(f"Localizer: {config.localizer_model} (Holo/vLLM)", flush=True)
    print(f"Tasks: {len(tasks)}", flush=True)
    print(f"Validator: {'Claude' if config.use_validator else 'disabled'}", flush=True)
    print(f"Circuit breaker: {config.circuit_breaker_threshold} repeats", flush=True)
    print(f"Budget warning: {config.budget_warning_pct:.0%}", flush=True)
    print("=" * 70, flush=True)

    # Initialize clients
    claude = ClaudeClient(config)

    # Try Holo localizer, fall back to Claude
    holo = HoloLocalizer(config)
    if not config.claude_only and holo.health_check():
        localizer = holo
        print(f"Localizer: Holo via vLLM at {config.vllm_base}", flush=True)
    else:
        localizer = ClaudeLocalizer(claude, config)
        config.claude_only = True
        print(f"Localizer: Claude fallback (vLLM not available)", flush=True)

    results = []
    for i, task in enumerate(tasks):
        print(f"\n{'='*50}", flush=True)
        print(f"Task {i+1}/{len(tasks)}: {task.name}", flush=True)
        print(f"  {task.instruction[:120]}", flush=True)
        print(f"{'='*50}", flush=True)

        browser = KernelBrowser(config)
        try:
            browser.create(stealth=task.stealth)
            stealth_label = " [stealth]" if task.stealth else ""
            print(f"  Browser: {browser.session_id}{stealth_label}  Live: {browser.live_url}", flush=True)
        except Exception as e:
            print(f"  [ERROR] Browser create failed: {e}", flush=True)
            results.append(TaskResult(
                task=task.name, answer=None, steps=0, total_time=0,
                nav_tokens=0, loc_calls=0, success=False, verify_match=None,
            ))
            continue

        try:
            result = run_task(config, task, browser, claude, localizer, label)
            results.append(result)

            status = "PASS" if result.success else "FAIL"
            verify = ""
            if result.verify_match is not None:
                verify = " (verified)" if result.verify_match else " (wrong answer)"
            print(f"\n  [{status}] {(result.answer or 'None')[:120]}{verify}", flush=True)
            print(f"  Steps: {result.steps}, Time: {result.total_time:.1f}s, "
                  f"Nav tokens: {result.nav_tokens}, Loc calls: {result.loc_calls}", flush=True)
            if result.circuit_breaker_tripped:
                print(f"  Circuit breaker was tripped", flush=True)
            if result.validation_result:
                print(f"  Validation: {result.validation_result[:100]}", flush=True)
        except Exception as e:
            print(f"  [ERROR] {e}", flush=True)
            import traceback
            traceback.print_exc()
            results.append(TaskResult(
                task=task.name, answer=None, steps=0, total_time=0,
                nav_tokens=0, loc_calls=0, success=False, verify_match=None,
            ))
        finally:
            browser.destroy()

    # --- Summary ---
    print(f"\n\n{'='*70}", flush=True)
    print(f"SUMMARY — {label.upper()}", flush=True)
    print(f"{'='*70}", flush=True)

    successes = sum(1 for r in results if r.success)
    verified = sum(1 for r in results if r.verify_match is True)
    total = len(results)
    avg_steps = sum(r.steps for r in results) / max(total, 1)
    avg_time = sum(r.total_time for r in results) / max(total, 1)
    total_nav = sum(r.nav_tokens for r in results)
    total_loc = sum(r.loc_calls for r in results)

    print(f"\n  Completed: {successes}/{total} ({100*successes/max(total,1):.0f}%)", flush=True)
    if verified:
        print(f"  Verified correct: {verified}", flush=True)
    print(f"  Avg steps/task: {avg_steps:.1f}", flush=True)
    print(f"  Avg time/task: {avg_time:.1f}s", flush=True)
    print(f"  Total navigator tokens: {total_nav:,}", flush=True)
    print(f"  Total localizer calls: {total_loc}", flush=True)

    print(f"\n  {'Task':<28} {'OK?':>5} {'Steps':>6} {'Time':>8} {'Answer'}", flush=True)
    print(f"  {'-'*85}", flush=True)
    for r in results:
        s = "PASS" if r.success else "FAIL"
        ans = (r.answer or "-")[:45]
        v = ""
        if r.verify_match is True:
            v = " *"
        elif r.verify_match is False:
            v = " X"
        print(f"  {r.task:<28} {s:>5} {r.steps:>6} {r.total_time:>7.1f}s {ans}{v}", flush=True)

    print(f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # Save results
    results_data = {
        "config": {
            "navigator": config.navigator_model,
            "localizer": config.localizer_model,
            "claude_only": config.claude_only,
            "validator": config.use_validator,
            "max_steps": config.max_steps,
            "nav_temperature": config.navigator_temperature,
        },
        "summary": {
            "label": label,
            "total": total,
            "successes": successes,
            "verified": verified,
            "pct": round(100 * successes / max(total, 1), 1),
            "avg_steps": round(avg_steps, 1),
            "avg_time": round(avg_time, 1),
            "total_nav_tokens": total_nav,
            "total_loc_calls": total_loc,
        },
        "results": [asdict(r) for r in results],
    }

    results_file = config.results_file.replace(".json", f"_{label}.json")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results_data, f, indent=2, default=str)
    print(f"Results saved to {results_file}", flush=True)

    return results_data


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Surfer Harness v2 — Hybrid Browser Agent Benchmark")
    parser.add_argument("--suite", choices=["easy", "hard", "all"], default="all",
                        help="Which task suite to run")
    parser.add_argument("--task", type=str, help="Run a single task by name")
    parser.add_argument("--navigator-model", type=str, default=None,
                        help="Claude model for navigation (default: claude-opus-4-7)")
    parser.add_argument("--localizer-model", type=str, default=None,
                        help="Holo model for localization")
    parser.add_argument("--vllm-base", type=str, default=None, help="vLLM base URL for localizer")
    parser.add_argument("--claude-only", action="store_true",
                        help="Use Claude for everything (no vLLM/Holo)")
    parser.add_argument("--no-validator", action="store_true", help="Disable answer validation")
    parser.add_argument("--max-steps", type=int, default=None, help="Max steps per task")
    parser.add_argument("--nav-temp", type=float, default=None, help="Navigator temperature")
    parser.add_argument("--label", type=str, default=None, help="Run label for results files")
    args = parser.parse_args()

    config = Config()

    if args.navigator_model:
        config.navigator_model = args.navigator_model
    if args.localizer_model:
        config.localizer_model = args.localizer_model
    if args.vllm_base:
        config.vllm_base = args.vllm_base
    if args.claude_only:
        config.claude_only = True
    if args.no_validator:
        config.use_validator = False
    if args.max_steps:
        config.max_steps = args.max_steps
    if args.nav_temp is not None:
        config.navigator_temperature = args.nav_temp

    # Validate keys
    if not config.anthropic_api_key:
        print("ERROR: ANTHROPIC_API_KEY not set (check ~/.env)", file=sys.stderr)
        sys.exit(1)
    if not config.kernel_api_key:
        print("ERROR: KERNEL_API_KEY not set (check ~/.env)", file=sys.stderr)
        sys.exit(1)

    label = args.label
    if args.task:
        all_tasks = EASY_TASKS + HARD_TASKS
        task = next((t for t in all_tasks if t.name == args.task), None)
        if not task:
            print(f"Unknown task: {args.task}", file=sys.stderr)
            print(f"Available: {', '.join(t.name for t in all_tasks)}", file=sys.stderr)
            sys.exit(1)
        if args.max_steps:
            task.max_steps = args.max_steps
        run_benchmark(config, [task], label or f"single_{args.task}")
    elif args.suite == "easy":
        run_benchmark(config, EASY_TASKS, label or "easy")
    elif args.suite == "hard":
        for t in HARD_TASKS:
            if args.max_steps:
                t.max_steps = args.max_steps
        run_benchmark(config, HARD_TASKS, label or "hard")
    else:
        run_benchmark(config, EASY_TASKS, label or "easy")
        run_benchmark(config, HARD_TASKS, label or "hard")


if __name__ == "__main__":
    main()
