# The Singularity Atlas

An independent Python application inspired by [worldmonitor](https://github.com/koala73/worldmonitor)'s
situational-awareness dashboard, re-aimed at a single subject: **the approach of the Singularity**.
No worldmonitor code is used here — see [NOTICE](NOTICE).

A 3D globe of the AI build-out (datacenters, fabs, labs, launch pads), eight live signal panels,
a cross-stream convergence radar, a composite **Singularity Index**, and a daily digest
synthesized by a local LLM in the register of Alex Wissner-Gross's *The Innermost Loop* —
all fed by public no-auth feeds, digested by a **LangGraph** pipeline, remembered by **Neo4j**.

```
./setup_and_run.sh      # deps + neo4j + seed + first ingest + tests + serve → http://localhost:8055
```

Fresh machine from a clone: [QUICKSTART.md](QUICKSTART.md).

## Ideas borrowed from worldmonitor, and what they became here

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
(kept current from the author's official Substack feed) seeded into the graph
and full-text searchable —
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

- Ingest runs every 15 min **inside the dashboard process** (APScheduler, not
  cron — it stops when uvicorn does); `POST /api/ingest` for a manual cycle,
  `POST /api/brief/regenerate` to re-synthesize today's edition.
- The Loop Archive syncs daily from the author's official Substack feed. New
  editions are written to `data/loop_issues/` and pushed straight into the
  graph; `POST /api/archive/sync` pulls immediately. `/api/state.loop_sync`
  reports when the feed was last checked and what arrived.
- The LLM is optional: everything degrades to heuristics when Ollama is offline.

## Setup

Clone-from-scratch, prerequisites, and what a fresh clone does *not* include:
[QUICKSTART.md](QUICKSTART.md).

```bash
uv sync
docker compose up -d          # singularity-atlas-neo4j: http :7476 · bolt :7689 (neo4j/singularity-atlas)
ollama pull qwen3.8:27b-mtp-bf16                    # optional, for the LLM brief (any qwen3 works — auto-detected)
uv run python -m singularity_atlas.seed           # local archive → graph (once)
./setup_and_run.sh --sync                         # or all of the above in one step, plus Loop feed + first ingest
```

Useful CLIs: `uv run python -m singularity_atlas.feeds` (smoke-test all feeds) ·
`uv run python -m singularity_atlas.pipeline` (one ingest cycle).

`./setup_and_run.sh` is the canonical entry point (`--setup-only`, `--no-tests`,
`--sync`, `--help`); it runs one feed ingest before serving so the dashboard
is not empty on first paint, then uvicorn's scheduler keeps ingesting every
15 min (not cron). It clears a stale dashboard holding the port before
starting, since a forgotten instance keeps ingesting in the background.
`scripts/dev.sh` is a shim that forwards to it.

## Configuration

Everything lives in `singularity_atlas/config.py`: feeds, vector weights, epoch years,
globe site catalog, ports, model name. Env overrides: `ATLAS_PORT`, `ATLAS_NEO4J_URI`,
`ATLAS_NEO4J_PASSWORD`, `ATLAS_MODEL`, `OLLAMA_HOST`.

## Notes

- `ref/innermost-loop/` is **not in version control**: the newsletter archive is
  all-rights-reserved third-party content, so it is kept locally and never
  published. A fresh clone therefore starts with an empty archive — the archive
  panels return nothing until the daily sync (or `POST /api/archive/sync`)
  populates `data/loop_issues/` from the public feed, which exposes the latest
  20 editions. *Accelerando* stays in `ref/` under its own CC licence.
- Nothing is uploaded anywhere.
- Feeds are all public: no auth, no registration, no API keys.
- Neo4j browser: http://localhost:7476 (try `MATCH (e:Entity)<-[:MENTIONS]-(s:Story)
  RETURN e, s LIMIT 80`).

## Licence

Apache 2.0 — see [LICENSE](LICENSE). That grant covers the code in this
repository only.

It does **not** cover `ref/`, which redistributes two third-party published
works under their own, more restrictive terms: *Accelerando* (Charles Stross,
CC BY-NC-ND 2.5 — noncommercial, no derivatives) and the *Innermost Loop*
archive (Dr. Alex Wissner-Gross, all rights reserved). [NOTICE](NOTICE) records
the full attribution, the acknowledgements, and the scope of each licence.
