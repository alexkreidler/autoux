"""Screenshot every slide in slides/index.html as 1920×1080 PNG.

Output: slides/exports/slide-01.png … slide-NN.png

These are 16:9 and Google Slides-default sized — drop the folder into
Slides via Insert → Image → upload, or use a multi-image-per-slide layout.

Usage:
    uv run python slides/screenshot.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "exports"
DECK = ROOT / "index.html"

WIDTH, HEIGHT = 1920, 1080


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("slide-*.png"):
        old.unlink()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=2)
        page = ctx.new_page()
        page.goto(DECK.absolute().as_uri())
        page.add_style_tag(content="html, body, * { scroll-behavior: auto !important; }")
        # Wait for video on the title slide to be ready, then seek to a
        # representative frame (~30% of duration) so the title-slide poster
        # has actual cinematic content, not a black first frame.
        page.evaluate("""
            async () => {
                const v = document.querySelector('section.hero video');
                if (!v) return;
                v.pause();
                if (v.readyState < 2) {
                    await new Promise((r) => v.addEventListener('loadeddata', r, { once: true }));
                }
                v.currentTime = (v.duration || 9) * 0.30;
                await new Promise((r) => v.addEventListener('seeked', r, { once: true }));
            }
        """)
        # Wait for Mermaid diagrams to finish rendering — they replace
        # `.mermaid` divs with inline SVG asynchronously after CDN load.
        page.wait_for_function(
            """
            () => {
              const blocks = [...document.querySelectorAll('.mermaid')];
              if (!blocks.length) return true;
              return blocks.every(b => b.querySelector('svg'));
            }
            """,
            timeout=15000,
        )
        n_slides = page.evaluate("document.querySelectorAll('section.slide').length")
        print(f"deck has {n_slides} slides")
        for i in range(n_slides):
            page.evaluate(
                "(i) => document.querySelectorAll('section.slide')[i].scrollIntoView({block: 'start'})",
                i,
            )
            page.wait_for_timeout(200)
            out = OUT / f"slide-{i+1:02d}.png"
            page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT})
            print(f"  → {out}")
        browser.close()


if __name__ == "__main__":
    main()
