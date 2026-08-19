"""Capture a looping README gif of the live dashboard.

Requires the Atlas serving locally and Playwright + system Chrome:

    uv run uvicorn singularity_atlas.api:app --host 127.0.0.1 --port 8055
    uv run --with playwright python scripts/capture_readme_gif.py

Uses ?demo=1 (slightly faster globe + ticker) so ~10s of gif shows motion
without looking frantic.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "dashboard.gif"
URL = "http://127.0.0.1:8055/?demo=1"
WIDTH, HEIGHT = 1440, 900
FPS = 8
SECONDS = 10
SCALE = 1200


def main() -> int:
    if shutil.which("ffmpeg") is None:
        print("ERROR: ffmpeg is not on PATH", file=sys.stderr)
        return 1

    from playwright.sync_api import sync_playwright

    n_frames = FPS * SECONDS
    with tempfile.TemporaryDirectory(prefix="atlas-gif-") as tmp:
        tmp_path = Path(tmp)
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=True,
                args=[
                    "--ignore-gpu-blocklist",
                    "--enable-webgl",
                    "--use-gl=angle",
                    "--use-angle=metal",
                    "--hide-scrollbars",
                ],
            )
            page = browser.new_page(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=1,
            )
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_selector("#globe canvas", timeout=30_000)
            page.wait_for_function(
                "() => document.querySelector('#si-value')?.textContent !== '—'",
                timeout=30_000,
            )
            # earth texture + first auto-rotate tick
            page.wait_for_timeout(3500)
            canvas_ok = page.evaluate(
                "() => { const c = document.querySelector('#globe canvas');"
                " return !!(c && c.width > 0 && c.height > 0); }"
            )
            if not canvas_ok:
                print("ERROR: globe canvas has no size — WebGL likely failed", file=sys.stderr)
                browser.close()
                return 1
            # Pace frames to wall-clock FPS so playback is not faster than capture
            # (screenshot() itself takes ~100ms; a blind extra wait stacked on that).
            t0 = time.monotonic()
            for i in range(n_frames):
                page.screenshot(
                    path=str(tmp_path / f"frame_{i:03d}.png"),
                    type="png",
                )
                remaining_ms = (t0 + (i + 1) / FPS - time.monotonic()) * 1000
                if remaining_ms > 0:
                    page.wait_for_timeout(int(remaining_ms))
            browser.close()

        palette = tmp_path / "palette.png"
        frames = tmp_path / "frame_%03d.png"
        subprocess.check_call([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(frames),
            "-vf", f"scale={SCALE}:-1:flags=lanczos,palettegen=max_colors=128:stats_mode=diff",
            str(palette),
        ])
        OUT.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(frames),
            "-i", str(palette),
            "-lavfi",
            f"scale={SCALE}:-1:flags=lanczos,fps={FPS} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3",
            "-loop", "0",
            str(OUT),
        ])

    size_mb = OUT.stat().st_size / 1_000_000
    print(f"wrote {OUT} ({size_mb:.2f} MB, {n_frames} frames @ {FPS} fps)")
    if size_mb > 8:
        print("WARNING: gif is large for GitHub README; consider lowering SCALE or SECONDS",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
