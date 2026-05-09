#!/usr/bin/env python3
"""
Build cinematic_intro_video.html — same layout as cinematic_intro.html
but with <video> elements instead of background-image thumbnails.
"""

import re
import os

BASE = "/Users/davidbai/Desktop/cua-hackathon"
HTML_IN = f"{BASE}/demo/cinematic_intro.html"
HTML_OUT = f"{BASE}/demo/cinematic_intro_video.html"

with open(HTML_IN) as f:
    src = f.read()

# For each cell div, we need to:
# 1. Extract the thumbnail path (if any) to derive the replay path
# 2. Replace background-image with a <video> element

RUNS = f"{BASE}/runs/mega2_20260509_150853"

# Pattern: finds each cell div with its style and inner avatar img
CELL_RE = re.compile(
    r'(<div class="cell(?P<focal> focal)?"\s+style="(?P<style>[^"]+)">'
    r'\s*(?P<inner>.*?)\s*</div>)',
    re.DOTALL
)

# Thumbnail path pattern inside style
THUMB_RE = re.compile(
    r"background-image:\s*url\('file://(?P<path>[^']+)'\)"
)

def thumb_to_replay(thumb_path: str):
    """Convert thumbnail path to replay path, return None if not found."""
    # thumb: .../mega2_20260509_150853/<app>/thumbnails/<persona>__<task>/step_00.jpg
    # replay: .../mega2_20260509_150853/<app>/replays/<persona>__<task>.mp4
    m = re.search(
        r'/mega2_20260509_150853/([^/]+)/thumbnails/([^/]+)/step_00\.jpg',
        thumb_path
    )
    if not m:
        return None
    app, key = m.group(1), m.group(2)
    replay = f"{RUNS}/{app}/replays/{key}.mp4"
    if os.path.exists(replay):
        return replay
    return None

replacements = {'video': 0, 'thumb': 0, 'placeholder': 0}

def replace_cell(m: re.Match) -> str:
    focal = m.group('focal') or ''
    style = m.group('style')
    inner = m.group('inner')

    # Strip background-image and background-size/position from style
    style_clean = re.sub(r'\s*background-image:[^;]+;?', '', style)
    style_clean = re.sub(r'\s*background-size:[^;]+;?', '', style_clean)
    style_clean = re.sub(r'\s*background-position:[^;]+;?', '', style_clean)
    style_clean = style_clean.strip().rstrip(';')

    # Find replay path from thumbnail
    thumb_match = THUMB_RE.search(style)
    replay_path = None
    thumb_path = None

    if thumb_match:
        thumb_path = thumb_match.group('path')
        replay_path = thumb_to_replay(thumb_path)

    if replay_path:
        replacements['video'] += 1
        media = (
            f'<video autoplay muted loop playsinline preload="auto" '
            f'style="width:100%;height:100%;object-fit:cover;object-position:top left;">'
            f'<source src="file://{replay_path}" type="video/mp4">'
            f'</video>'
        )
    elif thumb_path:
        # Keep thumbnail as <img> fallback
        replacements['thumb'] += 1
        media = (
            f'<img src="file://{thumb_path}" '
            f'style="width:100%;height:100%;object-fit:cover;object-position:top left;" />'
        )
    else:
        replacements['placeholder'] += 1
        media = ''  # dark placeholder from background-color

    # Rebuild style: keep position/size/color, drop bg-image
    return (
        f'<div class="cell{focal}" style="{style_clean}">'
        f'\n      {media}'
        f'\n      {inner}'
        f'\n    </div>'
    )

# Replace cells
new_body = CELL_RE.sub(replace_cell, src)

# Add JS to stagger video start times
stagger_js = """
// Stagger video start times so they're not in lock-step
window.addEventListener('load', () => {
  document.querySelectorAll('video').forEach(v => {
    v.currentTime = Math.random() * 3;
    v.play().catch(() => {});
  });
});
"""

# Insert before </script> closing (there's one script block at the end)
new_body = new_body.replace(
    '// Initialize to frame 0\nsetFrame(0);',
    f'// Initialize to frame 0\nsetFrame(0);\n{stagger_js}'
)

with open(HTML_OUT, 'w') as f:
    f.write(new_body)

print(f"Written: {HTML_OUT}")
print(f"  video cells:       {replacements['video']}")
print(f"  thumbnail fallback:{replacements['thumb']}")
print(f"  dark placeholder:  {replacements['placeholder']}")
