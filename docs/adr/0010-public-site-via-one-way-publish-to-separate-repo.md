# 0010. Publish the public site as a one-way static push to a separate publish-only repo (Cloudflare Pages), replacing GitHub Pages `docs/`

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** first 2026-08-28 (`9e553aa`, GitHub Pages from `docs/`); superseded 2026-10-16 (`5aa01ee`, `45179e9`, `d205579`)

## Context

The dashboard has no auth and must stay on loopback (ADR 0001). A public view was still wanted.

## Decision

**Phase 1 (2026-08-28 → 2026-10-16).** `scripts/export_public_snapshot.py` wrote a 24 h static board (`docs/index.html`, `docs/snapshot.json`, `docs/board.png`) and it was committed to `main` daily ("Publish 24h public snapshot", 42 such commits, plus a few differently-worded ones). GitHub Pages serves `main:/docs`.

**Phase 2 (from 2026-10-16).** `scripts/publish_public_site.sh` publishes to **sw30labs/singularity-atlas-site** (Cloudflare Pages), one way:
- ensures the local dashboard is up (starts uvicorn on 127.0.0.1:8055 in `screen` if needed) and waits up to ~3 min for today's brief;
- captures the board screenshot (Playwright), exports the snapshot to a temp `BUILD` dir (`--out`), builds the static live Atlas (`scripts/build_live_site.py`, ADR 0012);
- copies into a fresh clone of the site repo, writes `_headers` (CSP, cache), `robots.txt`, `404.html`, per-day archive pages;
- pushes over SSH alias `github-atlas-site` (deploy key; "Never prompt under launchd"); `ATLAS_SITE_BRANCH` for preview, `ATLAS_NO_PUSH=1`, `ATLAS_FROM_COMMIT` to backfill a day from old `docs/` commits.
- `d205579` marks the old GitHub Pages board "moved … no longer updated", pointing to singularityatlas.ai.

Guardrails are in ADR 0011.

## Consequences

**Positive**
- The source repo no longer gets daily churn commits (≈7.5 MB GIF + ~560 KB PNG rewrites stopped).
- Public hosting is isolated from code; the site repo can only receive generated, scanned output.

**Negative**
- `main` history still carries ~42 snapshot commits with binary churn.
- GitHub Pages is **still enabled** on this repo with source `main:/docs` (checked via API 2026-10-28), so anything added under `docs/` is published there (A-007). This ADR set itself lives in `docs/`.
- The publisher depends on a launchd job, a deploy key and an SSH alias that aren't in the repo (A-006).
- `export_public_snapshot.py` still defaults `--out` to `docs/`, so a bare run would overwrite the retired board's "moved" notice.

## Alternatives considered

GitHub Pages from `docs/` was used first and replaced; the commit history doesn't say why (A-014).

## Evidence

- `scripts/export_public_snapshot.py`, `scripts/publish_public_site.sh`, `scripts/build_live_site.py`
- `docs/index.html` line 48 (moved notice)
- Commits `9e553aa`, `d29fe87`, `1cae791`, daily "Publish 24h public snapshot" commits 2026-08-30 … 2026-10-16, `15d73c6`, `5aa01ee`, `d205579`, `45179e9`, `274695c`, `70461b5`, `0243680`
- GitHub API `repos/sw30labs/singularity-atlas/pages` (legacy build, `main` `/docs`)
