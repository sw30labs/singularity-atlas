# The Singularity Atlas

A Python port of [worldmonitor](https://github.com/koala73/worldmonitor)'s situational-awareness
experience, re-aimed at a single subject: **the approach of the Singularity**.

A 3D globe of the AI build-out (datacenters, fabs, labs, launch pads), eight live signal panels,
a cross-stream convergence radar, a composite **Singularity Index**, and a daily digest
synthesized by a local LLM in the register of Alex Wissner-Gross's *The Innermost Loop* —
all fed by public no-auth feeds, digested by a **LangGraph** pipeline, remembered by **Neo4j**.

```
./setup_and_run.sh      # deps + neo4j + seed + tests + serve → http://localhost:8055
```

## What was ported / cannibalized from worldmonitor

| worldmonitor | The Singularity Atlas |
|---|---|
| 3D globe (globe.gl) + layer catalog | Same library. Layers: datacenters, fabs, labs, launch pads + upcoming launches, geolocated AI signals, co-mention flow arcs |
| Panel inventory | 8 vector panels: Capability · Compute · Capital · Embodiment · Agency · Security · Space · Culture |
| AI-synthesized briefs | **The Daily Loop** — qwen3 (Ollama) writes today's edition from the top signals |
| Country Instability Index | **Singularity Index** — composite 0–100, 8 sub-indices, sparkline, Stross epoch dial (Slow Takeoff → Point of Inflexion → Singularity) + countdown to 2045 |
| Cross-stream correlation | **Convergence radar** — entities crossing ≥2 streams in 72h (click for constellation + "Alex wrote about this") |
| Feed freshness tracking | `/api/feeds` health (last fetch, items, errors) |
| Local AI via Ollama | Same. Zero API keys, zero registration |

Plus what only this atlas has: the **Loop Archive** — the *Innermost Loop* editions
(218 shipped in `ref/innermost-loop/…`, kept current from the author's official
Substack feed) seeded into the graph and full-text searchable —
and the *Accelerando* epoch dial with rotating Stross quotes.

## Architecture

```
feeds (RSS / arXiv / HN / LaunchLibrary / GDELT)
        │  async, no auth
        ▼
LangGraph StateGraph   fetch → dedupe → classify → persist → score → brief
        │                                   │            │          └ qwen3 via Ollama (heuristic fallback)
        ▼                                   ▼            ▼
     seen.json                       Neo4j (:Story)-[:ABOUT]->(:Vector)      SI snapshots (JSONL)
                                    (:Story)-[:MENTIONS]->(:Entity)
                                    (:Story)-[:LOCATED]->(:Place)
        ▼
FastAPI  /api/state /api/globe /api/brief /api/si /api/convergence
         /api/signals /api/graph /api/archive/search /api/archive/sync /api/feeds
        ▼
web/  zero-build dashboard — globe.gl + vanilla JS
```

- Ingest runs every 15 min (APScheduler); `POST /api/ingest` for a manual cycle,
  `POST /api/brief/regenerate` to re-synthesize today's edition.
- The Loop Archive syncs daily from the author's official Substack feed. New
  editions are written to `data/loop_issues/` and pushed straight into the
  graph; `POST /api/archive/sync` pulls immediately. `/api/state.loop_sync`
  reports when the feed was last checked and what arrived.
- The LLM is optional: everything degrades to heuristics when Ollama is offline.

## Setup

```bash
uv sync
docker compose up -d          # singularity-atlas-neo4j: http :7476 · bolt :7689 (neo4j/singularity-atlas)
ollama pull qwen3.8:27b-mtp-bf16                    # optional, for the LLM brief (any qwen3 works — auto-detected)
uv run python -m singularity_atlas.seed           # shipped editions → graph (once)
./setup_and_run.sh                                # or all of the above in one step
```

Useful CLIs: `uv run python -m singularity_atlas.feeds` (smoke-test all feeds) ·
`uv run python -m singularity_atlas.pipeline` (one ingest cycle).

`./setup_and_run.sh` is the canonical entry point (`--setup-only`, `--no-tests`,
`--sync`, `--help`); it clears a stale dashboard holding the port before
starting, since a forgotten instance keeps ingesting in the background.
`scripts/dev.sh` is a shim that forwards to it.

## Configuration

Everything lives in `singularity_atlas/config.py`: feeds, vector weights, epoch years,
globe site catalog, ports, model name. Env overrides: `ATLAS_PORT`, `ATLAS_NEO4J_URI`,
`ATLAS_NEO4J_PASSWORD`, `ATLAS_MODEL`, `OLLAMA_HOST`.

## Notes

- Reference corpora stay in `ref/` (the 218 shipped editions; *Accelerando* for the
  epoch dial + header quotes). Nothing is uploaded anywhere.
- Feeds are all public: no auth, no registration, no API keys.
- Neo4j browser: http://localhost:7476 (try `MATCH (e:Entity)<-[:MENTIONS]-(s:Story)
  RETURN e, s LIMIT 80`).
