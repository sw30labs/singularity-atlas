#!/bin/bash
# DRAFT — not installed. Publish Singularity Atlas public snapshot to the
# publish-only site repo (sw30labs/singularity-atlas-site), served by Cloudflare Pages.
#
# One-way push of static files only. Nothing on the internet connects back to this Mac.
# Never ships ref/, loop_issues, data/, *.zip, or anything from export_graph.sh.
#
# Layout of the site repo after each run:
#   /index.html  /snapshot.json  /board.png      <- latest
#   /YYYY-MM-DD/{index.html,snapshot.json,board.png}  <- dated archive (immutable once written)
#   /archive/index.html                           <- list of all dated boards
#   /_headers  /robots.txt  /404.html             <- static site chrome (Cloudflare Pages)
set -euo pipefail

SRC="${ATLAS_SRC_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"   # private working repo (source of truth)
SITE="${ATLAS_SITE_DIR:-$HOME/REPOS/singularity-atlas-site}"  # clone of the publish-only repo
SITE_REMOTE="git@github-atlas-site:sw30labs/singularity-atlas-site.git"  # ssh alias -> deploy key
BRANCH="main"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
# Never prompt under launchd: the deploy key has no passphrase and needs no agent.
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o IdentitiesOnly=yes"
export GIT_TERMINAL_PROMPT=0
LOGDIR="$HOME/Library/Logs/singularity-atlas"
mkdir -p "$LOGDIR"
stamp() { date '+%Y-%m-%d %H:%M:%S %Z'; }
DAY=$(TZ=America/New_York date '+%Y-%m-%d')

echo "$(stamp) start publish_public_site ($DAY)"

BUILD=$(mktemp -d "${TMPDIR:-/tmp}/atlas-build.XXXXXX")
trap 'rm -rf "$BUILD"' EXIT
cd "$SRC"
if [ -n "${ATLAS_FROM_COMMIT:-}" ]; then
  # Backfill mode: take the 3 public files exactly as committed in the old docs/ publishing.
  for f in index.html snapshot.json board.png; do git show "${ATLAS_FROM_COMMIT}:docs/$f" > "$BUILD/$f"; done
  DAY=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['generated_et'][:10])" "$BUILD/snapshot.json")
  echo "$(stamp) backfill from ${ATLAS_FROM_COMMIT} as ${DAY}"
else
# ---------------------------------------------------------------- 1. backend up (local only)
if ! curl -sf --max-time 3 "http://127.0.0.1:8055/" >/dev/null; then
  echo "$(stamp) uvicorn down — restarting (bound to 127.0.0.1 only)"
  /usr/bin/screen -dmS singularity-atlas bash -lc "cd '$SRC' && exec uv run uvicorn singularity_atlas.api:app --host 127.0.0.1 --port 8055"
  for i in $(seq 1 15); do
    sleep 2
    curl -sf --max-time 3 "http://127.0.0.1:8055/api/state" >/dev/null && break
  done
fi
curl -sf --max-time 15 "http://127.0.0.1:8055/api/state" >/dev/null || {
  echo "$(stamp) FAIL: /api/state not ready" >&2; exit 1; }

# ---------------------------------------------------------------- 2. build into a private temp dir

# A freshly restarted uvicorn runs its startup pipeline, which writes today's brief ~30-60s later.
# Wait (max ~3 min) for it so the board doesn't show yesterday's brief. Read-only polling.
TODAY_UTC=$(date -u '+%Y-%m-%d')
for i in $(seq 1 36); do
  BD=$(curl -sf --max-time 5 "http://127.0.0.1:8055/api/state" | python3 -c "import json,sys;print((json.load(sys.stdin).get('brief') or {}).get('date') or '')" 2>/dev/null || true)
  [ "$BD" = "$TODAY_UTC" ] && break
  sleep 5
done
echo "$(stamp) brief date: ${BD:-none} (today UTC ${TODAY_UTC})"

# Export straight into the build dir when the exporter supports --out (keeps docs/ untouched);
# older exporter versions only write docs/, so fall back to copying from there.
if grep -q -- '"--out"' scripts/export_public_snapshot.py; then
  uv run python scripts/export_public_snapshot.py --out "$BUILD"
else
  uv run python scripts/export_public_snapshot.py
  cp docs/index.html docs/snapshot.json "$BUILD/"
fi

BOARD_OUT="$BUILD/board.png" uv run --with playwright python - <<'PY' || echo "$(stamp) board.png capture skipped"
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT = Path(os.environ["BOARD_OUT"])
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
# If the capture failed, fall back to yesterday's latest board so the page isn't broken.
[ -s "$BUILD/board.png" ] || { [ -s "$SITE/board.png" ] && cp "$SITE/board.png" "$BUILD/board.png"; }

fi

# ---------------------------------------------------------------- 3. guardrails on the build
# Allowlist: exactly these files, nothing else, ever.
ALLOWED="board.png index.html snapshot.json"
for f in "$BUILD"/*; do
  b=$(basename "$f")
  case " $ALLOWED " in *" $b "*) ;; *) echo "$(stamp) FAIL: unexpected file in build: $b" >&2; exit 1;; esac
done
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$BUILD/snapshot.json" || {
  echo "$(stamp) FAIL: snapshot.json is not valid JSON" >&2; exit 1; }
# Size sanity: refuse anything that looks like a corpus slipped in.
for f in index.html snapshot.json; do
  sz=$(stat -f%z "$BUILD/$f"); [ "$sz" -lt 1000000 ] || { echo "$(stamp) FAIL: $f too large ($sz)" >&2; exit 1; }
done
# Leak scan: local paths, secrets, private data dirs. (Footer text mentioning localhost:8055 is fine.)
if grep -EIl "$HOME"'|/Users/[A-Za-z0-9._-]+/|loop_issues|innermost-loop-markdown|ALL_ISSUES\.md|Accelerando\.md|BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,}|NEO4J_PASSWORD|bolt://' \
     "$BUILD/index.html" "$BUILD/snapshot.json" >/dev/null; then
  echo "$(stamp) FAIL: leak scan matched — refusing to publish" >&2; exit 1
fi

# ---------------------------------------------------------------- 4. assemble site tree
if [ ! -d "$SITE/.git" ]; then
  git clone -q "$SITE_REMOTE" "$SITE" 2>/dev/null || { mkdir -p "$SITE"; git -C "$SITE" init -q -b "$BRANCH"; git -C "$SITE" remote add origin "$SITE_REMOTE"; }
fi
cd "$SITE"
git remote set-url origin "$SITE_REMOTE"
# Sync to the remote if it has the branch (the site repo is publish-only, so local edits are discarded).
if git ls-remote --exit-code origin "$BRANCH" >/dev/null 2>&1; then
  git fetch -q origin "$BRANCH" && git checkout -q -B "$BRANCH" "origin/$BRANCH" && git reset -q --hard "origin/$BRANCH"
fi

# latest at root
rsync -a --checksum --include='index.html' --include='snapshot.json' --include='board.png' --exclude='*' "$BUILD/" "$SITE/"
# dated archive (overwrite only today's folder; older days are never touched)
mkdir -p "$SITE/$DAY"
rsync -a --checksum --include='index.html' --include='snapshot.json' --include='board.png' --exclude='*' "$BUILD/" "$SITE/$DAY/"

# archive index (regenerated from the folders present)
mkdir -p "$SITE/archive"
python3 - "$SITE" <<'PY'
import json, re, sys, html
from pathlib import Path
site = Path(sys.argv[1])
days = sorted((d.name for d in site.iterdir() if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name)), reverse=True)
rows = []
for d in days:
    si = "—"
    try:
        s = json.loads((site / d / "snapshot.json").read_text())
        v = s.get("si"); si = v.get("value", v) if isinstance(v, dict) else v
    except Exception:
        pass
    rows.append(f'<li><a href="../{d}/">{d}</a> <span class="si">SI {html.escape(str(si))}</span></li>')
(site / "archive" / "index.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Singularity Atlas — archive</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:40rem;margin:3rem auto;padding:0 1rem;background:#0b0d10;color:#e6e6e6}}
a{{color:#7cc4ff}}li{{margin:.3rem 0}}.si{{color:#999;font-family:ui-monospace,monospace;margin-left:.6rem}}</style></head>
<body><h1>Singularity Atlas — daily boards</h1><p><a href="../">Latest</a></p><ul>
{chr(10).join(rows)}
</ul></body></html>
""")
print("archive days:", len(days))
PY

# static chrome (written once; harmless to rewrite)
cat > "$SITE/_headers" <<'H'
/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com; connect-src 'self' https://cloudflareinsights.com; frame-ancestors 'none'; base-uri 'self'
/snapshot.json
  Cache-Control: public, max-age=300
/*/snapshot.json
  Cache-Control: public, max-age=86400
H
cat > "$SITE/404.html" <<'NF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Not found · The Singularity Atlas</title>
  <meta name="robots" content="noindex" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root { --paper:#f5f5f5; --ink:#2d3142; --muted:#4f5d75; --accent:#eb6c36;
      --sans:'Geist',system-ui,sans-serif; --serif:'Instrument Serif',serif; --mono:'Geist Mono',ui-monospace,monospace; }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:var(--sans); background:var(--paper); color:var(--ink); line-height:1.5; }
    main { max-width:42rem; margin:0 auto; padding:5rem 1.5rem; }
    .eyebrow { font-family:var(--mono); font-size:.68rem; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); }
    .code { font-family:var(--serif); font-size:6rem; line-height:1; color:var(--accent); margin:.6rem 0 .4rem; }
    h1 { font-family:var(--serif); font-size:2rem; font-weight:400; margin-bottom:.6rem; }
    p { color:var(--muted); margin:.5rem 0; }
    nav { margin-top:1.6rem; font-family:var(--mono); font-size:.85rem; }
    a { color:var(--accent); text-decoration:none; margin-right:1.4rem; }
    a:hover { text-decoration:underline; }
  </style>
</head>
<body>
  <main>
    <div class="eyebrow">The Singularity Atlas</div>
    <div class="code">404</div>
    <h1>Nothing at this coordinate.</h1>
    <p>This page doesn't exist. The site only holds the daily public board and its dated archive.</p>
    <nav><a href="/">Today's board</a><a href="/archive/">Archive</a></nav>
  </main>
</body>
</html>
NF
[ -f "$SITE/robots.txt" ] || printf 'User-agent: *\nAllow: /\n' > "$SITE/robots.txt"

# Final allowlist check over the whole site tree (excluding .git).
BAD=$(find "$SITE" -path "$SITE/.git" -prune -o -type f -print | sed "s|^$SITE/||" | \
      grep -Ev '^(index\.html|snapshot\.json|board\.png|_headers|robots\.txt|404\.html|README\.md|archive/index\.html|[0-9]{4}-[0-9]{2}-[0-9]{2}/(index\.html|snapshot\.json|board\.png))$' || true)
[ -z "$BAD" ] || { echo "$(stamp) FAIL: non-allowlisted files in site repo:"$'\n'"$BAD" >&2; exit 1; }

# ---------------------------------------------------------------- 5. commit + push (site repo only)
git add -A .
if git rev-parse -q --verify HEAD >/dev/null && git diff --cached --quiet; then
  echo "$(stamp) no site changes — nothing to push"; exit 0
fi
git -c user.name="Atlas publisher" -c user.email="atlas-publisher@users.noreply.github.com" \
    commit -q -m "Publish 24h public snapshot ${DAY}"
if [ "${ATLAS_NO_PUSH:-0}" = "1" ]; then
  echo "$(stamp) ATLAS_NO_PUSH=1 — committed locally $(git rev-parse --short HEAD), not pushed"; exit 0
fi
git push origin "$BRANCH"
echo "$(stamp) pushed site $(git rev-parse --short HEAD)"
