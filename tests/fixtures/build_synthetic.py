"""Generate synthetic trajectory fixtures covering all terminal reasons + failure modes.

The wire format must match what TrajectoryWriter produces (header + step lines + footer).
We hand-write the lines here so this is independent of io.py landing.

Run:
    uv run python tests/fixtures/build_synthetic.py runs/synthetic_iter_0
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from usersim.schemas import (
    Action,
    Step,
    StepDelta,
    StepObservation,
    StepTiming,
    TerminalReason,
    TurnMeta,
)


def _step(
    turn: int,
    t0: datetime,
    action_type: str,
    action_args: dict,
    reasoning: list[str],
    page_url: str,
    page_title: str,
    dom_hash: str,
    dom_changed: bool = True,
    consecutive_unchanged: int = 0,
    is_dead_click: bool = False,
    model_ms: int = 1200,
    exec_ms: int = 600,
    prompt_tokens: int = 4500,
    completion_tokens: int = 80,
) -> Step:
    started = t0 + timedelta(milliseconds=turn * 2000)
    ended = started + timedelta(milliseconds=model_ms + exec_ms)
    return Step(
        turn=turn,
        started_at=started,
        ended_at=ended,
        action=Action(type=action_type, args=action_args),
        reasoning=reasoning,
        observation=StepObservation(
            page_url=page_url,
            page_title=page_title,
            dom_hash=dom_hash,
            screenshot_path=f"thumbnails/synthetic/step_{turn:02d}.jpg",
        ),
        delta=StepDelta(
            dom_changed=dom_changed,
            url_changed=False,
            is_dead_click=is_dead_click,
            consecutive_unchanged=consecutive_unchanged,
        ),
        timing=StepTiming(model_ms=model_ms, exec_ms=exec_ms, total_ms=model_ms + exec_ms),
        tokens=TurnMeta(
            model_ms=model_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=0.0024,
        ),
    )


def _write_trajectory(
    out_dir: Path,
    persona_id: str,
    task_id: str,
    target_url: str,
    steps: list[Step],
    terminal_reason: TerminalReason,
    final_url: str,
    final_title: str,
    error: str | None = None,
) -> None:
    started = steps[0].started_at if steps else datetime.now(timezone.utc)
    ended = steps[-1].ended_at if steps else started

    path = out_dir / "trajectories" / f"{persona_id}__{task_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)

    header = {
        "kind": "header",
        "persona_id": persona_id,
        "task_id": task_id,
        "target_url": target_url,
        "target_commit": "synthetic",
        "started_at": started.isoformat(),
        "viewport": {"w": 1280, "h": 800},
        "agent_model": "tzafon.northstar-cua-fast",
        "browser_session_id": f"synthetic-{persona_id}-{task_id}",
        "live_view_url": None,
    }
    footer = {
        "kind": "footer",
        "ended_at": ended.isoformat(),
        "terminal_reason": terminal_reason,
        "final_url": final_url,
        "final_title": final_title,
        "error": error,
        "replay_path": f"replays/{persona_id}__{task_id}.mp4",
    }

    with path.open("w") as f:
        f.write(json.dumps(header) + "\n")
        for step in steps:
            f.write(json.dumps({"kind": "step", **step.model_dump(mode="json")}) + "\n")
        f.write(json.dumps(footer) + "\n")


def main(out_dir: Path) -> None:
    """Build a realistic spread of trajectories for reducer testing."""
    t0 = datetime(2026, 5, 9, 18, 0, 0, tzinfo=timezone.utc)
    target = "https://turbotax.intuit.com/tax-tools/calculators/taxcaster/"

    # ---------- 1. Clean success: rushed_mobile completes basic W-2 ----------
    _write_trajectory(
        out_dir,
        "rushed_mobile",
        "single_w2_basic",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["The 'Get Started' button is centered. Tapping."],
                  target, "TaxCaster", "sha1:001a", consecutive_unchanged=0),
            _step(1, t0, "click", {"x": 320, "y": 250, "button": "left"},
                  ["Selecting 'Single' filing status."],
                  f"{target}#filing", "TaxCaster", "sha1:001b"),
            _step(2, t0, "type", {"text": "65000"},
                  ["Entering W-2 income."],
                  f"{target}#income", "TaxCaster", "sha1:001c"),
            _step(3, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Clicking calculate."],
                  f"{target}#result", "TaxCaster", "sha1:001d"),
        ],
        terminal_reason="success_dom",
        final_url=f"{target}#result",
        final_title="TaxCaster — Refund Estimate",
    )

    # ---------- 2. Clean success: power_user completes married+kids ----------
    _write_trajectory(
        out_dir,
        "power_user_skeptic",
        "married_kids",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["Engaging the calculator."], target, "TaxCaster", "sha1:002a"),
            _step(1, t0, "keypress", {"keys": ["Tab", "Tab"]},
                  ["Keyboard nav to filing status."], target, "TaxCaster", "sha1:002b"),
            _step(2, t0, "click", {"x": 380, "y": 280, "button": "left"},
                  ["Selecting MFJ."], target, "TaxCaster", "sha1:002c"),
            _step(3, t0, "type", {"text": "120000"},
                  ["Entering joint income."], target, "TaxCaster", "sha1:002d"),
            _step(4, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Submitting."], f"{target}#result", "TaxCaster", "sha1:002e"),
        ],
        terminal_reason="success_dom",
        final_url=f"{target}#result",
        final_title="TaxCaster — Refund Estimate",
    )

    # ---------- 3. Stuck loop: elderly user clicks same disabled button ----------
    _write_trajectory(
        out_dir,
        "elderly_first_time",
        "single_w2_basic",
        target,
        steps=[
            _step(0, t0, "click", {"x": 200, "y": 500, "button": "left"},
                  ["I see a 'Continue' link but I'm not sure if I clicked the right thing. Let me try again."],
                  target, "TaxCaster", "sha1:003a"),
            _step(1, t0, "click", {"x": 200, "y": 500, "button": "left"},
                  ["Hmm, nothing happened. Maybe I need to click harder. Trying once more."],
                  target, "TaxCaster", "sha1:003a", dom_changed=False, consecutive_unchanged=1),
            _step(2, t0, "click", {"x": 200, "y": 500, "button": "left"},
                  ["The page isn't responding. Maybe this button is broken? Let me click it again to be sure."],
                  target, "TaxCaster", "sha1:003a", dom_changed=False, consecutive_unchanged=2),
            _step(3, t0, "click", {"x": 200, "y": 500, "button": "left"},
                  ["I don't understand why this isn't working."],
                  target, "TaxCaster", "sha1:003a", dom_changed=False, consecutive_unchanged=3),
        ],
        terminal_reason="stuck",
        final_url=target,
        final_title="TaxCaster",
    )

    # ---------- 4. Abandoned (patience exceeded) ----------
    _write_trajectory(
        out_dir,
        "impatient_dad",
        "freelancer_1099",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["Just want the number."], target, "TaxCaster", "sha1:004a"),
            _step(1, t0, "click", {"x": 100, "y": 100, "button": "left"},
                  ["Wait, where's the 1099 option? Let me look around."],
                  target, "TaxCaster", "sha1:004a", dom_changed=False, consecutive_unchanged=1),
            _step(2, t0, "scroll", {"x": 640, "y": 400, "scroll_x": 0, "scroll_y": 200},
                  ["Scrolling down to find self-employment options."],
                  target, "TaxCaster", "sha1:004b"),
            _step(3, t0, "click", {"x": 800, "y": 50, "button": "left"},
                  ["This is taking too long. Going back."],
                  target, "TaxCaster", "sha1:004c"),
            _step(4, t0, "click", {"x": 800, "y": 50, "button": "left"},
                  ["Forget it. Closing this."],
                  target, "TaxCaster", "sha1:004d"),
            _step(5, t0, "keypress", {"keys": ["Escape"]},
                  ["I'm done with this."],
                  target, "TaxCaster", "sha1:004e"),
            _step(6, t0, "click", {"x": 800, "y": 50, "button": "left"},
                  ["Giving up. Will use a different tool."],
                  target, "TaxCaster", "sha1:004f"),
        ],
        terminal_reason="abandoned",
        final_url=target,
        final_title="TaxCaster",
    )

    # ---------- 5. Stuck on validation error (form clears) ----------
    _write_trajectory(
        out_dir,
        "esl_speaker",
        "married_kids",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["Starting the calculator."], target, "TaxCaster", "sha1:005a"),
            _step(1, t0, "click", {"x": 380, "y": 280, "button": "left"},
                  ["Selecting filing status."], target, "TaxCaster", "sha1:005b"),
            _step(2, t0, "type", {"text": "120,000"},
                  ["Entering income with comma."], target, "TaxCaster", "sha1:005c"),
            _step(3, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Submit."], target, "TaxCaster", "sha1:005d"),
            _step(4, t0, "type", {"text": "120000"},
                  ["The form rejected the comma format. Re-entering as plain digits."],
                  target, "TaxCaster", "sha1:005c"),
            _step(5, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Submit again."], target, "TaxCaster", "sha1:005d", dom_changed=False, consecutive_unchanged=1),
            _step(6, t0, "type", {"text": "120000"},
                  ["The form cleared again. I am confused, this validation error is not clear to me."],
                  target, "TaxCaster", "sha1:005c", dom_changed=False, consecutive_unchanged=2),
            _step(7, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Trying once more."], target, "TaxCaster", "sha1:005d", dom_changed=False, consecutive_unchanged=3),
        ],
        terminal_reason="stuck",
        final_url=target,
        final_title="TaxCaster",
    )

    # ---------- 6. Dead clicks: rushed_mobile taps wrong region repeatedly ----------
    _write_trajectory(
        out_dir,
        "rushed_mobile",
        "married_kids",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["Tapping the big button."], target, "TaxCaster", "sha1:006a"),
            _step(1, t0, "click", {"x": 50, "y": 600, "button": "left"},
                  ["I think I see a link."], target, "TaxCaster", "sha1:006a",
                  dom_changed=False, is_dead_click=True, consecutive_unchanged=1),
            _step(2, t0, "click", {"x": 1100, "y": 100, "button": "left"},
                  ["Tapping near the top."], target, "TaxCaster", "sha1:006a",
                  dom_changed=False, is_dead_click=True, consecutive_unchanged=2),
            _step(3, t0, "click", {"x": 30, "y": 30, "button": "left"},
                  ["Where's the menu?"], target, "TaxCaster", "sha1:006a",
                  dom_changed=False, is_dead_click=True, consecutive_unchanged=3),
        ],
        terminal_reason="stuck",
        final_url=target,
        final_title="TaxCaster",
    )

    # ---------- 7. Max turns hit: power_user goes too deep into edge cases ----------
    steps = []
    for i in range(20):
        steps.append(_step(
            i, t0,
            "click" if i % 2 == 0 else "type",
            {"x": 400 + i * 5, "y": 300, "button": "left"} if i % 2 == 0 else {"text": f"value_{i}"},
            [f"Trying combination {i} to find the edge case."],
            target, "TaxCaster", f"sha1:007_{i:02d}",
        ))
    _write_trajectory(
        out_dir,
        "power_user_skeptic",
        "freelancer_1099",
        target,
        steps=steps,
        terminal_reason="max_turns",
        final_url=target,
        final_title="TaxCaster",
    )

    # ---------- 8. Error mid-rollout (Kernel session died) ----------
    _write_trajectory(
        out_dir,
        "elderly_first_time",
        "married_kids",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["Starting carefully."], target, "TaxCaster", "sha1:008a"),
            _step(1, t0, "click", {"x": 380, "y": 280, "button": "left"},
                  ["Reading every option carefully."], target, "TaxCaster", "sha1:008b"),
        ],
        terminal_reason="error",
        final_url=target,
        final_title="TaxCaster",
        error="PlaywrightTimeoutError: Page.evaluate timed out after 30000ms",
    )

    # ---------- 9. Success via URL match ----------
    _write_trajectory(
        out_dir,
        "esl_speaker",
        "single_w2_basic",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["Beginning."], target, "TaxCaster", "sha1:009a"),
            _step(1, t0, "type", {"text": "65000"},
                  ["Income."], f"{target}#income", "TaxCaster", "sha1:009b"),
            _step(2, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Submit."], f"{target}/results?refund=2400", "Refund: $2,400", "sha1:009c"),
        ],
        terminal_reason="success_url",
        final_url=f"{target}/results?refund=2400",
        final_title="Refund: $2,400",
    )

    # ---------- 10. Stuck on form-clears (regression candidate, similar reasoning to #5) ----------
    _write_trajectory(
        out_dir,
        "impatient_dad",
        "single_w2_basic",
        target,
        steps=[
            _step(0, t0, "click", {"x": 640, "y": 400, "button": "left"},
                  ["Get started."], target, "TaxCaster", "sha1:010a"),
            _step(1, t0, "type", {"text": "65000"},
                  ["Entering W-2."], target, "TaxCaster", "sha1:010b"),
            _step(2, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Submit."], target, "TaxCaster", "sha1:010c"),
            _step(3, t0, "type", {"text": "65000"},
                  ["The form cleared after I hit submit. Re-entering income."],
                  target, "TaxCaster", "sha1:010b", dom_changed=False, consecutive_unchanged=1),
            _step(4, t0, "click", {"x": 700, "y": 600, "button": "left"},
                  ["Trying submit again."], target, "TaxCaster", "sha1:010c",
                  dom_changed=False, consecutive_unchanged=2),
            _step(5, t0, "type", {"text": "65000"},
                  ["Form cleared on validation again. Why does the form keep clearing?"],
                  target, "TaxCaster", "sha1:010b", dom_changed=False, consecutive_unchanged=3),
        ],
        terminal_reason="stuck",
        final_url=target,
        final_title="TaxCaster",
    )

    # ---------- manifest.jsonl ----------
    manifest_path = out_dir / "manifest.jsonl"
    rows = []
    for jsonl in sorted((out_dir / "trajectories").glob("*.jsonl")):
        lines = jsonl.read_text().splitlines()
        header = json.loads(lines[0])
        footer = json.loads(lines[-1])
        n_steps = len(lines) - 2
        rows.append({
            "persona_id": header["persona_id"],
            "task_id": header["task_id"],
            "jsonl_path": f"trajectories/{jsonl.name}",
            "terminal_reason": footer["terminal_reason"],
            "ended_at": footer["ended_at"],
            "n_steps": n_steps,
        })
    manifest_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    print(f"wrote {len(rows)} synthetic trajectories to {out_dir}")
    print(f"manifest at {manifest_path}")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/synthetic_iter_0")
    main(out)
