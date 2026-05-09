"""One worker = one (persona, task) pair → one Trajectory.

Pure async function. No shared state. Cleanup is sacred — every session must die.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from playwright.async_api import Page, async_playwright

from usersim import registry
from usersim.browsers.base import BrowserProvider
from usersim.clients.base import AgentClient
from usersim.io import (
    TrajectoryFooter,
    TrajectoryHeader,
    TrajectoryWriter,
    read_trajectory,
)
from usersim.schemas import (
    Action,
    ActiveRollout,
    Observation,
    Persona,
    Step,
    StepDelta,
    StepObservation,
    StepTiming,
    Task,
    Trajectory,
    TurnMeta,
)

def _agent_model_name(client: AgentClient) -> str:
    """Pull the model identifier from the client. Loose because AgentClient
    Protocol doesn't require it — we surface "unknown" if the impl doesn't
    expose one. Used only for trajectory provenance."""
    return getattr(client, "MODEL", None) or getattr(client, "model_name", None) or "unknown"


# =============================================================================
# Helpers
# =============================================================================

async def _screenshot_data_url(page: Page) -> str:
    png = await page.screenshot(type="png", full_page=False)
    return "data:image/png;base64," + base64.b64encode(png).decode()


async def _save_thumbnail(page: Page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(path), type="jpeg", quality=70, full_page=False)


def _dom_hash(html: str) -> str:
    return hashlib.sha1(html.encode()).hexdigest()


async def _check_success(page: Page, task: Task) -> tuple[bool, str | None]:
    if task.success_dom:
        try:
            count = await page.locator(task.success_dom).count()
            if count > 0:
                return True, "success_dom"
        except Exception:
            pass
    if task.success_url_pattern:
        if re.search(task.success_url_pattern, page.url):
            return True, "success_url"
    return False, None


# Map common lower/short modifier names → Playwright's `KeyboardModifier`
# spelling. Playwright is strict: `Control+A` works, `ctrl+a` does not.
# We accept either case from clients (some agents narrate keys naturally,
# e.g. "ctrl+a") and rewrite to the canonical form before dispatching.
_KEY_ALIASES: dict[str, str] = {
    "ctrl": "Control", "control": "Control",
    "alt": "Alt", "option": "Alt",
    "shift": "Shift",
    "meta": "Meta", "cmd": "Meta", "command": "Meta", "win": "Meta",
    "esc": "Escape", "escape": "Escape",
    "enter": "Enter", "return": "Enter",
    "tab": "Tab", "backspace": "Backspace", "delete": "Delete",
    "space": "Space", "spacebar": "Space",
    "up": "ArrowUp", "down": "ArrowDown",
    "left": "ArrowLeft", "right": "ArrowRight",
    "pageup": "PageUp", "pagedown": "PageDown",
    "home": "Home", "end": "End",
}


def _normalize_key(spec: str) -> str:
    """Normalize a keypress spec to Playwright form. Accepts `ctrl+a`,
    `Control+A`, `cmd+shift+p`, single chars, named keys (`Enter`)."""
    if not spec:
        return spec
    parts = spec.split("+")
    out: list[str] = []
    for p in parts:
        low = p.strip().lower()
        if low in _KEY_ALIASES:
            out.append(_KEY_ALIASES[low])
        elif len(p) == 1 and p.isalpha():
            out.append(p.upper())  # Playwright wants `A` not `a` when chained with modifier
        else:
            out.append(p)  # already-canonical (Enter, F1, etc.) or unknown — pass through
    return "+".join(out)


async def _execute_action(page: Page, action: Action) -> None:
    t = action.type
    a = action.args
    try:
        if t == "click":
            button = a.get("button", "left")
            await page.mouse.click(a["x"], a["y"], button=button)
        elif t == "double_click":
            await page.mouse.dblclick(a["x"], a["y"])
        elif t == "move":
            await page.mouse.move(a["x"], a["y"])
        elif t == "drag":
            path_pts = a.get("path", [])
            if path_pts:
                await page.mouse.move(path_pts[0]["x"], path_pts[0]["y"])
                await page.mouse.down()
                for p in path_pts[1:]:
                    await page.mouse.move(p["x"], p["y"])
                await page.mouse.up()
        elif t == "type":
            await page.keyboard.type(a.get("text", ""))
        elif t == "keypress":
            for k in a.get("keys", []):
                await page.keyboard.press(_normalize_key(k))
        elif t == "scroll":
            await page.mouse.move(a["x"], a["y"])
            await page.mouse.wheel(a.get("scroll_x", 0), a.get("scroll_y", 0))
        elif t == "wait":
            await asyncio.sleep(a.get("ms", 1000) / 1000)
        elif t in ("screenshot", "point_and_type"):
            if t == "point_and_type":
                await page.mouse.click(a["x"], a["y"])
                await page.keyboard.type(a.get("text", ""))
        elif t == "mouse_down":
            await page.mouse.down(button=a.get("button", "left"))
        elif t == "mouse_up":
            await page.mouse.up(button=a.get("button", "left"))
        elif t == "key_down":
            await page.keyboard.down(_normalize_key(a.get("key", "")))
        elif t == "key_up":
            await page.keyboard.up(_normalize_key(a.get("key", "")))
        else:
            print(f"  ! unhandled action type: {t}", file=sys.stderr)
    except Exception as e:
        print(f"  ! action {t} failed: {e}", file=sys.stderr)


def _error_trajectory(
    persona: Persona,
    task: Task,
    target_url: str,
    target_commit: str,
    started: datetime,
    error: str,
    out_dir: Path,
    agent_model: str = "unknown",
) -> Trajectory:
    """Emit a header + error footer through TrajectoryWriter (single write path
    for all trajectory files — audit O2). Reused when browser acquire fails."""
    p = out_dir / "trajectories" / f"{persona.id}__{task.id}.jsonl"
    header = TrajectoryHeader(
        persona_id=persona.id,
        task_id=task.id,
        target_url=target_url,
        target_commit=target_commit,
        started_at=started,
        viewport={"w": 1280, "h": 800},
        agent_model=agent_model,
    )
    footer = TrajectoryFooter(
        ended_at=datetime.now(),
        terminal_reason="error",
        final_url=target_url,
        final_title="",
        error=error,
    )
    with TrajectoryWriter(p, header) as writer:
        writer.finalize(footer)
    return read_trajectory(p)


# =============================================================================
# Main worker
# =============================================================================

async def run_one(
    persona: Persona,
    task: Task,
    target_url: str,
    target_commit: str,
    client: AgentClient,
    browser_provider: BrowserProvider,
    out_dir: Path,
    *,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    max_turns: int = 20,
    per_turn_timeout_s: float = 60.0,
    step_settle_ms: int = 500,
    record_replay: bool = True,
    registry_callback: Optional[Callable[[ActiveRollout], None]] = None,
    stuck_threshold: int = 3,         # turns of no DOM change → terminate "stuck"
    patience_override: int | None = None,  # if set, overrides persona.patience_steps
) -> Trajectory:
    started = datetime.now()
    traj_key = f"{persona.id}__{task.id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "trajectories" / f"{traj_key}.jsonl"
    agent_model = _agent_model_name(client)

    # --- Acquire browser -------------------------------------------------------
    try:
        browser_session = await browser_provider.acquire(
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            stealth=True,
        )
    except Exception as e:
        err = f"browser acquire failed: {type(e).__name__}: {e}"
        return _error_trajectory(
            persona, task, target_url, target_commit, started, err, out_dir,
            agent_model=agent_model,
        )

    replay_id: str | None = None
    agent_session = None
    terminal_reason: str = "error"
    error: str | None = None
    final_url = target_url
    final_title = ""
    replay_path: str | None = None
    writer: TrajectoryWriter | None = None

    try:
        # --- Start recording ---------------------------------------------------
        if record_replay:
            try:
                replay_id = await browser_session.start_recording()
            except Exception as e:
                print(f"[worker] recording start failed: {e}", file=sys.stderr)

        # --- Build header & writer --------------------------------------------
        header = TrajectoryHeader(
            persona_id=persona.id,
            task_id=task.id,
            target_url=target_url,
            target_commit=target_commit,
            started_at=started,
            viewport={"w": viewport_width, "h": viewport_height},
            agent_model=agent_model,
            browser_session_id=browser_session.session_id,
            live_view_url=browser_session.live_view_url,
        )
        writer = TrajectoryWriter(jsonl_path, header)

        # --- Connect Playwright -----------------------------------------------
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(browser_session.cdp_ws_url)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
            await page.goto(target_url, wait_until="domcontentloaded")

            # --- Register active rollout --------------------------------------
            rollout = ActiveRollout(
                browser_session_id=browser_session.session_id,
                persona_id=persona.id,
                task_id=task.id,
                target_url=target_url,
                started_at=started,
                live_view_url=browser_session.live_view_url or "",
                current_url=page.url,
            )
            try:
                registry.add(rollout)
            except Exception as e:
                print(f"[worker] registry.add failed: {e}", file=sys.stderr)

            # --- Initial observation ------------------------------------------
            shot_url = await _screenshot_data_url(page)
            obs = Observation(
                screenshot_data_url=shot_url,
                viewport_width=viewport_width,
                viewport_height=viewport_height,
                page_url=page.url,
                page_title=await page.title(),
            )

            # --- First agent call ---------------------------------------------
            agent_session, response = await client.start_session(
                instruction=persona.system_prompt(task.description),
                initial_observation=obs,
                temperature=persona.temperature,
            )

            # Track DOM hash for diff
            prev_html = await page.evaluate("document.documentElement.outerHTML")
            prev_dom_hash = _dom_hash(prev_html)
            prev_url = page.url
            consecutive_unchanged = 0
            cumulative_tokens = TurnMeta()
            cumulative_ms = 0
            thumb_dir = out_dir / "thumbnails" / traj_key

            # --- Turn loop ---------------------------------------------------
            for turn in range(max_turns):
                # Success check before executing action
                success, reason = await _check_success(page, task)
                if success and reason:
                    terminal_reason = reason
                    break

                if response.done and not response.actions:
                    terminal_reason = "agent_done"
                    break

                if not response.actions:
                    terminal_reason = "abandoned"
                    break

                action = response.actions[0]
                turn_started = datetime.now()

                t0 = time.monotonic()
                await _execute_action(page, action)
                await page.wait_for_timeout(step_settle_ms)
                exec_ms = int((time.monotonic() - t0) * 1000)

                # Compute delta
                current_url = page.url
                try:
                    current_html = await page.evaluate("document.documentElement.outerHTML")
                    current_dom_hash = _dom_hash(current_html)
                except Exception:
                    current_dom_hash = prev_dom_hash
                    current_html = prev_html

                dom_changed = current_dom_hash != prev_dom_hash
                url_changed = current_url != prev_url
                if dom_changed or url_changed:
                    consecutive_unchanged = 0
                else:
                    consecutive_unchanged += 1
                # A click that produced neither DOM nor URL change is a "dead click" —
                # the strongest signal we have without a real DOM hit-test.
                is_dead_click = (
                    action.type == "click"
                    and not dom_changed
                    and not url_changed
                )

                # Save thumbnail
                thumb_path = thumb_dir / f"step_{turn:02d}.jpg"
                try:
                    await _save_thumbnail(page, thumb_path)
                    screenshot_rel = str(thumb_path.relative_to(out_dir))
                except Exception:
                    screenshot_rel = None

                try:
                    final_title = await page.title()
                except Exception:
                    final_title = ""
                final_url = current_url

                turn_ended = datetime.now()
                total_ms = response.telemetry.model_ms + exec_ms
                step = Step(
                    turn=turn,
                    started_at=turn_started,
                    ended_at=turn_ended,
                    action=action,
                    reasoning=response.reasoning,
                    observation=StepObservation(
                        page_url=current_url,
                        page_title=final_title,
                        dom_hash=current_dom_hash,
                        screenshot_path=screenshot_rel,
                    ),
                    delta=StepDelta(
                        dom_changed=dom_changed,
                        url_changed=url_changed,
                        is_dead_click=is_dead_click,
                        consecutive_unchanged=consecutive_unchanged,
                    ),
                    timing=StepTiming(
                        model_ms=response.telemetry.model_ms,
                        exec_ms=exec_ms,
                        total_ms=total_ms,
                    ),
                    tokens=response.telemetry,
                )
                assert writer is not None
                writer.write_step(step)

                # Update cumulative stats
                tok = response.telemetry
                cumulative_tokens = TurnMeta(
                    model_ms=cumulative_tokens.model_ms + tok.model_ms,
                    prompt_tokens=cumulative_tokens.prompt_tokens + tok.prompt_tokens,
                    completion_tokens=cumulative_tokens.completion_tokens + tok.completion_tokens,
                    cached_tokens=cumulative_tokens.cached_tokens + tok.cached_tokens,
                )
                cumulative_ms += total_ms

                # Update registry. Build the patch as a JSON-ready dict
                # explicitly so registry storage stays homogeneous and pyright
                # can verify each conversion site (audit O7).
                rollout_patch: dict[str, Any] = {
                    "current_turn": turn + 1,
                    "last_action": action.model_dump(),
                    "last_reasoning": response.reasoning[0] if response.reasoning else None,
                    "current_url": current_url,
                    "current_title": final_title,
                    "current_dom_hash": current_dom_hash,
                    "consecutive_unchanged": consecutive_unchanged,
                    "cumulative_tokens": cumulative_tokens.model_dump(),
                    "cumulative_ms": cumulative_ms,
                }
                try:
                    registry.update(browser_session.session_id, **rollout_patch)
                except Exception:
                    pass

                if registry_callback is not None:
                    try:
                        updated = ActiveRollout(**{
                            **json.loads(rollout.model_dump_json()),
                            **rollout_patch,
                        })
                        registry_callback(updated)
                    except Exception:
                        pass

                # Stuck detection (disable by passing stuck_threshold=0 or negative)
                if stuck_threshold > 0 and consecutive_unchanged >= stuck_threshold:
                    terminal_reason = "stuck"
                    break

                # Patience cutoff
                effective_patience = patience_override if patience_override is not None else persona.patience_steps
                if effective_patience > 0 and turn + 1 >= effective_patience:
                    terminal_reason = "abandoned"
                    break

                # Next observation + agent step
                shot_url = await _screenshot_data_url(page)
                next_obs = Observation(
                    screenshot_data_url=shot_url,
                    viewport_width=viewport_width,
                    viewport_height=viewport_height,
                    page_url=current_url,
                    page_title=final_title,
                )
                try:
                    response = await asyncio.wait_for(
                        agent_session.step(next_obs),
                        timeout=per_turn_timeout_s,
                    )
                except asyncio.TimeoutError:
                    terminal_reason = "timeout"
                    break

                prev_dom_hash = current_dom_hash
                prev_url = current_url

            else:
                terminal_reason = "max_turns"

            # Final success check after loop ends
            success, reason = await _check_success(page, task)
            if success and reason:
                terminal_reason = reason

    except Exception as e:
        error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        terminal_reason = "error"

    finally:
        # Stop + download recording
        if replay_id and browser_session is not None:
            try:
                await browser_session.stop_recording(replay_id)
                await asyncio.sleep(1)  # give kernel time to finalize
                replay_dest = out_dir / "replays" / f"{traj_key}.mp4"
                await browser_session.download_recording(replay_id, replay_dest)
                replay_path = str(replay_dest.relative_to(out_dir))
                print(f"[worker] replay saved: {replay_dest} ({replay_dest.stat().st_size:,} bytes)")
            except Exception as e:
                print(f"[worker] replay failed: {e}", file=sys.stderr)

        # Finalize writer
        if writer is not None:
            try:
                footer = TrajectoryFooter(
                    ended_at=datetime.now(),
                    terminal_reason=terminal_reason,  # type: ignore[arg-type]
                    final_url=final_url,
                    final_title=final_title,
                    error=error,
                    replay_path=replay_path,
                )
                writer.finalize(footer)
            except Exception as e:
                print(f"[worker] writer.finalize failed: {e}", file=sys.stderr)
            try:
                writer.close()
            except Exception:
                pass

        # Close agent session
        if agent_session is not None:
            try:
                await agent_session.close()
            except Exception:
                pass

        # Release browser
        if browser_session is not None:
            try:
                await browser_session.release()
            except Exception as e:
                print(f"[worker] browser release failed: {e}", file=sys.stderr)

        # Remove from registry
        if browser_session is not None:
            try:
                registry.remove(browser_session.session_id)
            except Exception:
                pass

    return read_trajectory(jsonl_path)
