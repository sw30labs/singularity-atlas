# 0002. Neo4j as the graph store, with small JSON/JSONL files for dedupe, SI history and feed health

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`)

## Context

The dashboard needs entity co-mentions, cross-vector convergence, ego networks and geolocated events. NOTICE describes the app as "Python application (FastAPI, LangGraph, Neo4j)".

## Decision

- Neo4j 5 community runs in Docker (`docker-compose.yml`, container `singularity-atlas-neo4j`) on non-default host ports **7476** (HTTP) and **7689** (Bolt), with heap/pagecache capped (512m–1G), `restart: unless-stopped`, and an **external** named volume `singularity-atlas-neo4j-data` that `setup_and_run.sh` creates.
- Graph model (`store.py` docstring): `Story`, `Vector`, `Entity`, `Brief`; relations `ABOUT {score}`, `MENTIONS`, `LOCATED {lat, lon}`, `CO_OCCURS {stories}`. Uniqueness constraints on `Story.id`, `Vector.name`, `Entity.name`, `Brief.id`; index on `Story.published_at`.
- `CO_OCCURS` edges are rebuilt after each persist from stories ingested in the last 7 days.
- Some state deliberately lives outside the graph, in `data/` (gitignored): `seen.json` (dedupe fingerprints, capped at 50k), `si_history.jsonl` ("tiny, append-only, survives graph resets"), `feed_health.json`, `loop_sync.json`, `loop_issues/`.
- Credentials default to `neo4j` / `singularity-atlas`, overridable with `ATLAS_NEO4J_URI`, `ATLAS_NEO4J_USER`, `ATLAS_NEO4J_PASSWORD`.

## Consequences

**Positive**
- Graph queries (convergence, ego network, arcs) are direct Cypher.
- SI history and dedupe survive a wiped graph; the external volume survives `docker compose down`.

**Negative**
- Docker is required for a full install; without Neo4j the app starts with an empty graph (setup script continues).
- `docker-compose.yml` publishes 7476/7689 on all host interfaces with a password committed in the repo (see A-002).
- `Entity` is unique by name only, so the same name can't carry two types (last `SET e.type` wins).
- `_save_seen` keeps `set(list(seen)[-50000:])`; a Python set has no insertion order, so "keep the most recent" isn't guaranteed (A-011).
- State is split across Neo4j and files; a backup needs both (QUICKSTART notes the volume dump separately).

## Alternatives considered

None recorded.

## Evidence

- `docker-compose.yml`, `singularity_atlas/store.py`, `singularity_atlas/config.py` (Paths, Neo4j sections)
- `singularity_atlas/pipeline.py` `_save_seen`
- `setup_and_run.sh` (volume create, wait for Bolt)
- `QUICKSTART.md` § What a clone does not include
- Commit `ed3300c`
