#!/bin/bash
# Publish Singularity Atlas 24h public snapshot to GitHub Pages (main /docs).
# Runs on the Mac Studio itself via LaunchAgent. Never publishes ref/ or loop_issues.
set -euo pipefail
REPO="/Users/spider/REPOS/singularity-atlas"
cd "$REPO"
export PATH="/Users/spider/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
LOGDIR="$HOME/Library/Logs/singularity-atlas"
mkdir -p "$LOGDIR"
stamp() { date '+%Y-%m-%d %H:%M:%S %Z'; }

echo "$(stamp) start publish_public_snapshot"

# Keep dash up
if ! curl -sf --max-time 3 "http://127.0.0.1:8055/" >/dev/null; then
  echo "$(stamp) uvicorn down — restarting"
  /usr/bin/screen -dmS singularity-atlas bash -lc "cd '$REPO' && exec uv run uvicorn singularity_atlas.api:app --host 127.0.0.1 --port 8055"
  for i in 1 2 3 4 5 6 7 8 9 10; do
    sleep 2
    curl -sf --max-time 3 "http://127.0.0.1:8055/api/state" >/dev/null && break
  done
fi
curl -sf --max-time 15 "http://127.0.0.1:8055/api/state" >/dev/null || {
  echo "$(stamp) FAIL: /api/state not ready" >&2
  exit 1
}

uv run python scripts/export_public_snapshot.py

# Best-effort globe still
uv run --with playwright python - <<'PY' || echo "$(stamp) board.png capture skipped"
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT = Path("/Users/spider/REPOS/singularity-atlas/docs/board.png")
URL = "http://127.0.0.1:8055/?demo=1"
with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome", headless=True,
        args=["--ignore-gpu-blocklist","--enable-webgl","--use-gl=angle","--use-angle=metal","--hide-scrollbars"],
    )
    page = browser.new_page(viewport={"width":1440,"height":900}, device_scale_factor=1)
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_selector("#globe canvas", timeout=30_000)
    page.wait_for_function("() => document.querySelector('#si-value')?.textContent !== '—'", timeout=30_000)
    page.wait_for_timeout(3500)
    page.screenshot(path=str(OUT), type="png")
    browser.close()
print("board.png", OUT.stat().st_size)
PY

git add docs/index.html docs/snapshot.json docs/board.png
if git diff --cached --quiet; then
  echo "$(stamp) no docs changes — nothing to push"
  exit 0
fi
DAY=$(date '+%Y-%m-%d')
git commit -m "Publish 24h public snapshot ${DAY}"
git push origin main
echo "$(stamp) pushed $(git rev-parse --short HEAD)"
