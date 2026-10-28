# 0001. Local-first, single-process dashboard: FastAPI backend + zero-build vanilla-JS frontend on 127.0.0.1

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`)

## Context

The Atlas fuses public AI-news feeds into a globe, eight vector panels, a composite index and a daily brief (README). It is described as "a local situational-awareness dashboard", with "No API keys, no account, nothing uploaded."

## Decision

- One Python process (`uvicorn singularity_atlas.api:app`) serves both the JSON API (`/api/state`, `/api/si`, `/api/signals`, `/api/convergence`, `/api/graph`, `/api/brief`, `/api/ingest`, `/api/globe`, `/api/archive/*`, `/api/feeds`) and the static frontend (`/` and `/static`).
- The frontend (`web/index.html`, `web/app.js`, `web/style.css`) is plain JavaScript with no build step; it polls `/api/state` every 30 s, `/api/globe` every 5 min and `/api/ingest` every 2 s, and loads globe.gl from unpkg.
- The default bind is `127.0.0.1:8055` (`ATLAS_HOST`, `ATLAS_PORT`). README: "Keep the dashboard on `127.0.0.1`. It has no auth and is not meant to be internet-facing. Publish a static export instead."
- `/api/state` is a single "one-shot payload" carrying everything the page renders.

## Consequences

**Positive**
- Simple to run and to reason about; no frontend toolchain.
- One payload keeps the UI consistent and makes static export straightforward (ADR 0010).

**Negative**
- No authentication on any endpoint, including state-changing `POST /api/ingest`, `/api/brief/regenerate`, `/api/archive/sync`; safety relies entirely on the loopback bind.
- `ATLAS_HOST` can be set to a LAN address with no warning in code.
- The local dashboard depends on unpkg at runtime (only the public build vendors globe.gl, ADR 0012).
- `/api/state` recomputes several Neo4j queries on every 30 s poll.
- `web/app.js` labels any non-heuristic brief "qwen3 local", whatever model actually wrote it.

## Alternatives considered

None recorded in the repository. NOTICE contrasts the design with worldmonitor (TypeScript, Rust/Tauri, Node), which was the inspiration but not used.

## Evidence

- `singularity_atlas/api.py`, `singularity_atlas/config.py` (`API_HOST`, `API_PORT`)
- `web/index.html`, `web/app.js` (polling section)
- `README.md` § Run your own, § Notes; `NOTICE` § Acknowledgements
- Commit `ed3300c` (initial), `b202188` (Aineko ingest-watch polling)
