# Screenshots

Drop dashboard captures here. The top-level README's `<!-- screenshots -->`
block names the four canonical files. Once you've placed them, replace
the comment in the README with:

```markdown
| | |
|---|---|
| ![empty](docs/screenshots/01-empty-state.png) | ![grid](docs/screenshots/02-live-grid.png) |
| ![focus](docs/screenshots/03-focused-cell.png) | ![results](docs/screenshots/04-results-view.png) |
```

## What to capture (1920×1080 each)

| File | Scene | How |
|---|---|---|
| `01-empty-state.png` | Dashboard's casting-reel hero, before any run | Open http://localhost:3001 with `runs/active.json` empty. Persona avatars in a 5×5 grid + "live · waiting for runs". Click an avatar to open the profile popover, capture with the popover open. |
| `02-live-grid.png` | A live run mid-flight | Kick `configs/demo_live.yaml` with all 5 archetype personas + concurrency=5. Wait until cells have screenshots in their iframes (~15s in). Capture. |
| `03-focused-cell.png` | Focused-cell zoom with full transcript on the right | Click the ⛶ icon on any cell. The right side panel shows turn-by-turn reasoning + step thumbnails. |
| `04-results-view.png` | Past-run results panel | Open the past-runs dropdown → pick `mega2_20260509_150853` → click "results". Per-persona breakdown table renders. |

## Capture tips

- macOS: `Cmd+Shift+4` then space for window-only screenshots
- Hide system tray clutter (`Cmd+Option+H` to hide other apps first)
- Keep the dashboard's top-bar clean (no error banners, no console open)
- Save as PNG, not JPG — text is the dominant signal

## Optional extras

- `05-cinematic-still.png` — a still from `demo/cinematic_intro.mp4` at the
  fully-zoomed-out moment, for press / Twitter
- `06-chart.png` — copy of `demo/persona_divergence_mega2.png` if you want
  the chart inline in the README too

These aren't required for the README — just nice if you want to use them.
