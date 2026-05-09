# HyperFrames cinematic intro — brief

This is **not** the human-recorded demo. This is a 5–10 second cinematic
opener composed via HeyGen HyperFrames (HTML/CSS/JS → deterministic MP4)
that we cut into the front of the final video.

## Concept

> **Zoom out from one persona to all of them.**

Frame 0: tight close-up on a single trajectory cell — one Kernel browser
viewport with a persona avatar overlay. Could be elderly_first_time
methodically reading a Spree product page. Pulse on it for ~1.5s so the
viewer registers "this is one person doing one thing."

Frames 1–N: the camera pulls back via `transform: scale()` + `translate()`.
Other cells fade in around the focused one as they come into frame —
2 cells, then 8, then 24, then the full 40-cell grid. Each cell shows a
real persona doing a real thing.

Final frame: the entire grid is visible at low zoom. Title types in:
**"100 personas, parallel."** Hold for 1s. Cut.

Transition out: cross-fade to the live dashboard recording.

## Pacing target

| Frame | t (s) | what |
|---|---|---|
| 0 | 0.0 | single cell, 100% size |
| 1 | 1.0 | pulse + small scale-up |
| 2 | 1.5 | start zoom out, reveal 4 neighbouring cells |
| 3 | 2.5 | 8 cells visible |
| 4 | 4.0 | 24 cells visible |
| 5 | 5.5 | 40 cells visible (full grid) |
| 6 | 6.0 | title types in |
| 7 | 8.5 | hold |
| 8 | 9.0 | fade |

Total: ~9s. Trim to 6s if pacing feels slow.

## Source data

**Wait for the final canonical sweep before kicking this.** We want the
visual to feature real personas + real apps from THE demo run, not the
working sweeps. The brief assumes:

- 5 personas × N apps × open-ended tasks
- Each cell sources a single replay frame (jpg) + persona avatar
- The "focal" cell is one with rich reasoning text we can splash on screen

Likely source:
- `runs/<final_sweep_dir>/grid.mp4` — already composed, but we want the
  individual cells' *first frames* for the HTML composition, not the grid
- `runs/<final_sweep_dir>/<app>/thumbnails/<persona>__<task>/step_NN.jpg`
- `configs/personas/avatars/<persona>.png`

## HyperFrames implementation hint

```
npx skills add heygen-com/hyperframes   # one-time setup
```

Then ask Claude (in the project directory) to:
1. Read `runs/<final_sweep_dir>/manifest.jsonl` for the cell list
2. Generate an HTML page with absolute-positioned `<div>` cells in a
   grid. Each cell has a background-image of its first thumbnail jpg
   and a small absolute-positioned avatar img on top.
3. Wrap with a `<div id="camera">` and animate via GSAP:
   - frame 0–1.0: scale 4.0, translate to focal cell
   - frame 1.0–5.5: tween scale 4.0 → 1.0 + translate to grid center
   - frame 5.5+: title text fades in
4. Use `non-interactive` flag for deterministic render
5. Output to `demo/cinematic_intro.mp4`

## Title options (for the closing card)

Pick one:
- "100 personas, parallel."
- "personas diverge when the ui admits choice."
- "the same task — five different journeys."
- "open the loop."

## Constraints

- Don't kick this until the final demo run has been committed and we know
  exactly which sweep dir + which personas + which apps are featured.
- The intro must use Kernel aesthetic: cream bg #F5F0E6, ink #1A1A1A,
  earth-tone accents. NO neon, NO gradients, NO drop shadows.
- Output ~10MB max so it embeds easily into the human-recorded video.
- 1080p+ resolution.
- Subtle ambient audio is fine but the human voiceover starts immediately
  after this clip; don't cap with sound.

## When to kick

Spawn a subagent with this brief AFTER:
1. The final canonical sweep is recorded + grid.mp4 composed.
2. The `feedback.json` for that sweep has `by_persona` + findings.
3. Anything weird in the trajectories (errors, weird quotes) is filtered out.
