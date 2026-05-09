# slides/

Submission deck for **AutoUX: A CUA UserSim** (Alex Kreidler, David Bai).
Static HTML — no build step.

## Present locally

```bash
open slides/index.html
```

Navigation: **← / → / spacebar / PageUp / PageDown** to step.
**F** to enter fullscreen. **Home / End** to jump.

## Publish to Netlify (recommended for the submission)

```bash
uv run python slides/build.py
```

Builds `slides/dist/` — a self-contained ~18 MB folder with just the
deck and the two assets it references (cinematic intro + persona chart).
Paths are rewritten so `index.html` sits at the root.

**Drag-and-drop:** drop the **`slides/dist/`** folder (NOT the repo root —
the repo has a lot of unrelated stuff) onto
[app.netlify.com/drop](https://app.netlify.com/drop). You get a public
`*.netlify.app` URL in ~10 seconds. Rename to e.g. `autoux-cua` after.

**Git-linked:** connect the GitHub repo at
[app.netlify.com/start](https://app.netlify.com/start). The
`netlify.toml` at the repo root sets `command = "uv run python slides/build.py"`
and `publish = "slides/dist"`, so every push to `main` rebuilds and
auto-deploys.

Reviewers just need the URL; no Google account, no Slides upload.

## Export to Google Slides (via screenshots)

```bash
uv run python slides/screenshot.py
```

Writes `slides/exports/slide-01.png … slide-NN.png` at 1920×1080, 2× DPR.
The title slide's screenshot is a **still poster** captured at ~30% into
the cinematic intro video — it's a representative frame, not a black
first frame.

In Google Slides:
- **File → Page setup → Widescreen 16:9** (default).
- For each slide, **Insert → Image → Upload from computer**, drop `slide-NN.png`,
  fit to slide. Or select all PNGs in Finder and drag into a Slides deck —
  each becomes its own slide automatically.

### Title slide: replace the still with the actual video

For the cinematic title to play in Slides:

1. Open slide 1 (currently the still poster).
2. **Insert → Video → Upload from computer** → pick `demo/cinematic_intro.mp4`.
   (One-time upload to your Drive; ~19 MB.)
3. Resize the video to fill the slide (drag corners while holding shift).
4. Right-click the video → **Format options → Video playback**:
   - ✅ Autoplay when presenting
   - ✅ Mute audio
   - Optional: set "loop video" if it's a short loop
5. Send the still poster image **to back** (or delete it) so the video sits on top.

In presentation mode, the video plays inline with the title text overlay.

## Files

- `index.html` — the deck (single file, no deps).
- `screenshot.py` — Playwright renderer for the PNG export.
- `exports/` — generated PNGs (gitignored).
