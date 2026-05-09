# coder — Coding-Agent Harness

Thin driver that takes a `feedback.json` from UserSim, renders a prompt, and
invokes a coding agent to patch the target app in place.

## Usage

```bash
uv run python -m coder run \
  --repo /path/to/target-app \
  --feedback runs/iter_000/feedback.json \
  --iter 1
```

The command:
1. Stages context into `<repo>/.usersim/iter_1/` (feedback.json, screenshots, prior_patches.diff).
2. Renders the iteration prompt.
3. Invokes `claude -p <prompt>` via subprocess with file-system tools only.
4. Runs `git diff HEAD` to capture what changed.
5. Commits the patch as `iter_1: auto-ux patch [...]`.
6. Prints a JSON summary to stdout.

## Swapping agents

`CodingAgent` is a structural protocol (`src/coder/base.py`). Any class with a
`name: str` attribute and an `async def patch(...)` method is a valid impl.

Planned future implementations:
- `CursorBackgroundAgent` — drives Cursor's background-agent API.
- `CodexCliAgent` — wraps `codex -p` (OpenAI Codex CLI).
- `AiderAgent` — wraps `aider --message`.

To use an alternative agent, instantiate it and pass it to `run_loop` directly:

```python
from coder.loop import run_loop
from my_agents import CursorBackgroundAgent

patch = await run_loop(
    repo_dir=Path("target-app"),
    feedback_path=Path("runs/iter_0/feedback.json"),
    iteration=1,
    agent=CursorBackgroundAgent(),
)
```

## Target-app permissions

Copy `templates/.claude/settings.json` into the target app repo before running.
This grants the agent Edit/Write/Read/Glob/Grep and blocks Bash and WebFetch,
so it can modify files but cannot exec arbitrary shell commands or exfiltrate data.
