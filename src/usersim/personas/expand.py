"""Persona expansion: given N seed personas, generate M related-but-distinct ones.

Uses persona-to-persona prompting (PersonaHub pattern) with negative-example injection
to prevent duplicates across batches.

Usage:
    uv run python -m usersim.personas.expand \
        --seed configs/personas/seed.jsonl \
        --out configs/personas/expanded.jsonl \
        --target-n 25
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import openai
from dotenv import load_dotenv

from usersim.schemas import Persona

load_dotenv(dotenv_path=Path(__file__).parents[4] / ".env", override=False)
load_dotenv(override=False)  # fallback: search from cwd

PER_SEED = 4  # expansions per seed (5 seeds × 4 = 20 + 5 originals = 25)

SYSTEM = (
    "You are a UX research assistant generating diverse user personas for usability testing. "
    "Output only valid JSON — no markdown, no explanation."
)

EXPAND_PROMPT = """\
Seed persona:
{seed_json}

Already-generated personas (avoid duplicates):
{negatives}

Generate {n} related but distinct people who might attempt the same kind of task as the seed persona.
Vary: age_range, device, language_fluency, tech_literacy, patience_steps, and behavioral quirks.
Include a short prior_experience list (1-3 items) showing relevant past interactions.

Return a JSON object with a single key "personas" whose value is an array of {n} objects.
Each object must have these exact keys:
  id (snake_case string), archetype (1 sentence), tech_literacy ("low"|"medium"|"high"),
  patience_steps (int 3-20), quirks (list of 2-4 short strings),
  age_range ("18-25"|"26-40"|"41-60"|"61+"), device ("desktop"|"mobile"|"tablet"),
  language_fluency ("native"|"proficient"|"limited"), prior_experience (list of 1-3 strings),
  temperature (float 0.5-1.0)
"""

_CANDIDATE_MODELS = ["gpt-5.5", "gpt-5", "gpt-4o"]
_working_model: str | None = None


def _probe_model(client: openai.OpenAI, model: str) -> bool:
    try:
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_completion_tokens=5,
        )
        return True
    except openai.NotFoundError:
        return False
    except openai.BadRequestError:
        # Model exists but rejects the ping for some other reason — still available
        return True
    except Exception:
        return False


def _get_model(client: openai.OpenAI) -> str:
    global _working_model
    if _working_model:
        return _working_model
    for m in _CANDIDATE_MODELS:
        print(f"  Probing model {m}...", end=" ", flush=True)
        if _probe_model(client, m):
            print(f"available.")
            _working_model = m
            return m
        print("not found.")
    raise RuntimeError(f"None of {_CANDIDATE_MODELS} are available.")


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _dump_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")


# Aliases the model frequently emits that don't match Persona's strict Literals.
_DEVICE_MAP = {
    "laptop": "desktop", "computer": "desktop", "pc": "desktop",
    "chromebook": "desktop", "macbook": "desktop", "netbook": "desktop",
    "phone": "mobile", "smartphone": "mobile", "iphone": "mobile", "android": "mobile",
    "ipad": "tablet", "ipad_mini": "tablet",
}
_TL_MAP = {"novice": "low", "beginner": "low", "expert": "high", "advanced": "high",
           "intermediate": "medium", "moderate": "medium"}
_LF_MAP = {"fluent": "native", "near-native": "native",
           "advanced": "proficient", "intermediate": "proficient",
           "basic": "limited", "beginner": "limited"}
_AGE_MAP = {
    "18-24": "18-25", "20-30": "26-40", "20-25": "18-25", "25-30": "26-40",
    "25-35": "26-40", "30-40": "26-40", "30-45": "26-40",
    "40-50": "41-60", "50-60": "41-60", "60-70": "61+",
    "60+": "61+", "65+": "61+", "70+": "61+",
}


def _coerce(raw: dict) -> dict:
    """Normalize model output to match Persona's Literal fields."""
    if isinstance(raw.get("device"), str):
        raw["device"] = _DEVICE_MAP.get(raw["device"].lower().strip(), raw["device"])
    if isinstance(raw.get("tech_literacy"), str):
        raw["tech_literacy"] = _TL_MAP.get(raw["tech_literacy"].lower().strip(), raw["tech_literacy"])
    if isinstance(raw.get("language_fluency"), str):
        raw["language_fluency"] = _LF_MAP.get(raw["language_fluency"].lower().strip(), raw["language_fluency"])
    if isinstance(raw.get("age_range"), str):
        ar = raw["age_range"].replace(" ", "").replace("yrs", "").replace("years", "")
        raw["age_range"] = _AGE_MAP.get(ar, raw["age_range"])
    return raw


def _expand(client: openai.OpenAI, model: str, seed: dict, negatives: list[dict], n: int) -> list[dict]:
    neg_str = json.dumps([p.get("archetype", p.get("id")) for p in negatives], indent=None)
    prompt = EXPAND_PROMPT.format(
        seed_json=json.dumps(seed, indent=2),
        negatives=neg_str,
        n=n,
    )

    # Try structured JSON schema first; fall back to json_object mode
    for attempt in range(3):
        try:
            create_kwargs: dict = dict(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=4096,
            )
            # gpt-5.5 only supports default temperature (1); omit to be safe
            if model not in ("gpt-5.5",):
                create_kwargs["temperature"] = 0.9
            resp = client.chat.completions.create(**create_kwargs)
            text = resp.choices[0].message.content.strip()
            parsed = json.loads(text)
            # Handle both {"personas": [...]} and bare array
            if isinstance(parsed, list):
                return parsed
            if "personas" in parsed:
                return parsed["personas"]
            # Some models wrap in a different key — take first list value
            for v in parsed.values():
                if isinstance(v, list):
                    return v
            return [parsed]
        except openai.RateLimitError:
            wait = 2 ** attempt * 5
            print(f"\n    [rate-limit] waiting {wait}s...", file=sys.stderr)
            time.sleep(wait)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"\n    [retry {attempt+1}] {e}", file=sys.stderr)
            time.sleep(2)
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=Path("configs/personas/seed.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("configs/personas/expanded.jsonl"))
    parser.add_argument("--target-n", type=int, default=25)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    seeds = _load_jsonl(args.seed)
    client = openai.OpenAI(api_key=api_key)

    model = _get_model(client)
    print(f"Using model: {model}")

    all_personas: list[dict] = list(seeds)
    expansions_needed = max(0, args.target_n - len(seeds))
    per_seed = max(1, expansions_needed // len(seeds))

    print(f"Seeds: {len(seeds)}. Expanding ~{per_seed} per seed → target {args.target_n}.")

    # Over-request a bit to absorb validation drops (~25% loss observed empirically).
    request_n = max(per_seed, int(per_seed * 1.4))

    # Parallel per-seed expansion (each call ~30s; 5 seeds in parallel → ~30s total)
    from concurrent.futures import ThreadPoolExecutor

    def _expand_one(seed: dict) -> tuple[str, list[dict]]:
        try:
            new_raw = _expand(client, model, seed, all_personas, request_n)
        except Exception as e:
            print(f"\n  [error] '{seed['id']}': {e}", file=sys.stderr)
            return seed["id"], []
        validated = []
        for raw in new_raw:
            try:
                p = Persona(**_coerce(raw))
                validated.append(p.model_dump())
            except Exception as e:
                print(f"    [warn] '{seed['id']}' dropped invalid ({raw.get('id', '?')}): {str(e)[:80]}", file=sys.stderr)
        return seed["id"], validated

    with ThreadPoolExecutor(max_workers=len(seeds)) as ex:
        for sid, batch in ex.map(_expand_one, seeds):
            print(f"  '{sid}' → {len(batch)} valid")
            all_personas.extend(batch)

    # Dedupe by id (rare but possible across parallel batches), then trim to target.
    seen: set[str] = set()
    deduped = []
    for p in all_personas:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        deduped.append(p)
    all_personas = deduped[: args.target_n]

    _dump_jsonl(all_personas, args.out)
    print(f"\nWrote {len(all_personas)} personas to {args.out}")


if __name__ == "__main__":
    main()
