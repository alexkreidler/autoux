"""Avatar generation: for each persona without an avatar, call OpenAI image gen.

Generates flat-geometric vector illustrations in the Kernel aesthetic.
Writes PNGs to --avatar-dir/<persona_id>.png and updates avatar_path in the JSONL.
Idempotent: skips personas that already have a file on disk.

Usage:
    uv run python -m usersim.personas.avatars \
        --in configs/personas/expanded.jsonl \
        --out configs/personas/expanded.jsonl \
        --avatar-dir configs/personas/avatars
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parents[4] / ".env", override=False)
load_dotenv(override=False)  # fallback: search from cwd

IMAGE_SIZE = "1024x1024"

# 8 accent colors, deterministically assigned by persona_id hash
_ACCENT_COLORS = [
    ("khaki", "#B5A368"),
    ("sage", "#8FA37C"),
    ("clay", "#C19A6B"),
    ("charcoal", "#3A3A3A"),
    ("rust", "#A8624A"),
    ("tan", "#D4A574"),
    ("olive", "#7A8B5A"),
    ("amber", "#C29440"),
]


def _accent_for_persona(persona_id: str) -> str:
    """Deterministically pick an accent color from the 8-color palette by hashing persona_id."""
    idx = hash(persona_id) % len(_ACCENT_COLORS)
    name, hex_val = _ACCENT_COLORS[idx]
    return f"{name} {hex_val}"


STYLE_BASE = (
    "Flat geometric vector illustration, head-and-shoulders portrait. "
    "The head fills approximately 60% of the frame height, centered. "
    "Background: cream paper, hex #F5F0E6, completely flat. "
    "The figure is a single solid-color silhouette in a muted earth tone (accent color: {accent}). "
    "Face shown front-facing or 3/4 view. "
    "Geometric construction: head as oval, neck as rectangle, shoulders as gentle trapezoid filling lower 30% of frame. "
    "Small white slit eyes (no pupils). "
    "Distinguishing head features (hat, glasses, hairstyle, head shape, beard) should be large enough to read at 64x64 pixels. "
    "NO outlines on colored shapes. NO gradients. NO shading. NO text. NO photo realism. NO full body. NO legs. "
    "NO walking poses. NO briefcases or props that draw attention away from the head. NO props below shoulders. "
    "Two-color palette only: cream + one accent. "
    "Style: minimalist mascot icon in the tradition of Massimo Vignelli or Italian modernist design. "
    "Sharp clean edges. The portrait should be instantly recognizable at thumbnail size."
)

PERSONA_SUFFIX = (
    "The portrait represents a {archetype}. "
    "Reflect personality through head shape, hat/hair, and pose only."
)

_CANDIDATE_MODELS = ["gpt-image-2", "gpt-image-1"]
_working_model: str | None = None


def _probe_image_model(client: openai.OpenAI, model: str) -> bool:
    try:
        # Minimal 1×1 generation to probe availability
        client.images.generate(
            model=model,
            prompt="A solid blue square.",
            size="1024x1024",
            n=1,
        )
        return True
    except openai.NotFoundError:
        return False
    except openai.BadRequestError as e:
        # Model exists but prompt or params rejected — still available
        print(f"    [probe {model}] BadRequest (model exists): {e}", file=sys.stderr)
        return True
    except Exception:
        return False


def _get_image_model(client: openai.OpenAI) -> str:
    global _working_model
    if _working_model:
        return _working_model
    for m in _CANDIDATE_MODELS:
        print(f"  Probing image model {m}...", end=" ", flush=True)
        if _probe_image_model(client, m):
            print("available.")
            _working_model = m
            return m
        print("not found.")
    raise RuntimeError(f"None of {_CANDIDATE_MODELS} are available.")


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _dump_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


def _build_prompt(persona: dict, idx: int) -> str:
    accent = _accent_for_persona(persona.get("id", str(idx)))
    style = STYLE_BASE.format(accent=accent)
    suffix = PERSONA_SUFFIX.format(archetype=persona.get("archetype", "a generic person"))
    return f"{style} {suffix}"


def _generate_avatar(client: openai.OpenAI, model: str, persona: dict, idx: int, dest: Path) -> bool:
    prompt = _build_prompt(persona, idx)
    for attempt in range(3):
        try:
            kwargs: dict = dict(
                model=model,
                prompt=prompt,
                size=IMAGE_SIZE,
                n=1,
            )
            if model == "gpt-image-1":
                kwargs["quality"] = "medium"
                kwargs["response_format"] = "b64_json"
            # gpt-image-2 does not accept response_format or quality

            resp = client.images.generate(**kwargs)

            item = resp.data[0]
            if getattr(item, "b64_json", None):
                img_data = base64.b64decode(item.b64_json)
            elif getattr(item, "url", None):
                import urllib.request
                img_data = urllib.request.urlopen(item.url).read()
            else:
                raise ValueError("No image data in response")

            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(img_data)
            return True

        except openai.RateLimitError:
            wait = 2 ** attempt * 10
            print(f"\n    [rate-limit] waiting {wait}s...", file=sys.stderr)
            time.sleep(wait)
        except openai.BadRequestError as e:
            # Content filter or moderation — log and bail (don't retry)
            print(f"\n    [content-filter] {e}", file=sys.stderr)
            return False
        except Exception as e:
            if attempt == 2:
                print(f"\n    [error] {e}", file=sys.stderr)
                return False
            time.sleep(3)
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--avatar-dir", type=Path, default=Path("configs/personas/avatars"))
    parser.add_argument("--force", action="store_true", help="Re-generate even if avatar already exists")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)
    model = _get_image_model(client)
    print(f"Using image model: {model}")

    personas = _load_jsonl(args.input)
    generated = 0
    skipped = 0
    failed = 0

    for idx, persona in enumerate(personas):
        pid = persona.get("id", "unknown")
        dest = args.avatar_dir / f"{pid}.png"

        if dest.exists() and not args.force:
            persona["avatar_path"] = str(dest)
            skipped += 1
            continue

        print(f"  Generating avatar for '{pid}' ({idx+1}/{len(personas)})...", end=" ", flush=True)
        ok = _generate_avatar(client, model, persona, idx, dest)
        if ok:
            persona["avatar_path"] = str(dest)
            generated += 1
            print("done")
        else:
            failed += 1
            print("FAILED (skipping)")

    _dump_jsonl(personas, args.out)
    print(f"\nAvatars: {generated} generated, {skipped} skipped, {failed} failed. Output: {args.out}")


if __name__ == "__main__":
    main()
