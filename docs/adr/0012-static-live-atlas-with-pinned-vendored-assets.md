# 0012. Ship the full dashboard as a read-only static site via a fetch shim and pinned vendored assets

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-10-16 (`45179e9`, `274695c`, `c2e7d71`)

## Context

The 24 h board (ADR 0010) was a screenshot plus summary. `45179e9` added a "Static live Atlas for the public site".

## Decision

- `scripts/build_live_site.py` bakes `/api/state`, `/api/globe` and per-entity graph/archive JSON into `data/`, and copies the unchanged `web/` frontend.
- `web/static-shim.js` replaces `window.fetch` for same-origin `/api/*`: GETs map to baked JSON (empty fallbacks for missing entities), non-GET returns `read-only snapshot`, ingest always reports idle. "Nothing reaches the machine that built it."
- `globe.gl.min.js` 2.46.2 and the `earth-night.jpg` texture are vendored with pinned sha256 in `web/vendor/README.md`; the builder refuses to build if the hashes change. The local dashboard still loads globe.gl from unpkg.
- `274695c`: system fonts only (no Google Fonts), tighter CSP, responsive phone/tablet layout.
- `c2e7d71`: `style.css`, `app.js`, `static-shim.js` get a `?v=<sha256[:10]>` query because the zone's browser TTL is 4 h while `index.html` revalidates.

## Consequences

**Positive**
- One frontend codebase serves both local and public modes.
- No third-party script hosts on the public site; supply-chain changes to globe.gl are caught by hash.

**Negative**
- Local and public builds load different globe.gl sources (unpkg `@2` floating vs pinned 2.46.2), so they can behave differently.
- The builder rewrites the unpkg script tag and texture URL by exact string replacement and fails if `unpkg.com` remains; a cosmetic edit to those lines in `web/` breaks the public build.
- Updating vendored assets is manual (download, hash, update README and `VENDOR`).

## Alternatives considered

None recorded.

## Evidence

- `scripts/build_live_site.py` (`VENDOR`, sha256 check, `?v=` versioning)
- `web/static-shim.js`, `web/vendor/README.md`, `web/index.html`, `web/style.css`
- Commits `45179e9`, `274695c`, `c2e7d71`
