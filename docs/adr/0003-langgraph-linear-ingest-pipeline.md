# 0003. Ingest as a linear LangGraph StateGraph that collects errors instead of raising

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`)

## Context

Each cycle fetches ~15 public feeds, removes duplicates, classifies, stores, rescores and maybe writes a brief. Individual feeds fail regularly (GDELT rate-limits; `feeds.py` comments).

## Decision

- `pipeline.py` builds `fetch → dedupe → classify → persist → score → brief → END` as a LangGraph `StateGraph` over a `PipelineState` TypedDict; the compiled graph is cached.
- "Every node is pure-ish (errors are collected, never raised)." `feeds.fetch_all` runs every feed concurrently with `httpx.AsyncClient` and `asyncio.gather`; a failing feed is recorded in feed health and returns `[]` ("feed isolation by design").
- GDELT gets one patient retry on HTTP 429 (`GDELT_RETRY_S = 6`).
- Dedupe uses a SHA-1 fingerprint of `url|lowercased title` against `data/seen.json`.
- The same pipeline runs from the scheduler, `POST /api/ingest`, or `python -m singularity_atlas.pipeline`.

## Consequences

**Positive**
- One bad feed never stops a cycle; failures are visible in `/api/feeds` and `last_ingest.errors`.
- Node functions are individually testable (`tests/test_pipeline.py`).

**Negative**
- LangGraph is a heavyweight dependency for a fixed linear chain with no branching or checkpointing.
- `node_fetch` calls `asyncio.run`, so the pipeline can't be invoked from inside a running event loop.
- Dedupe happens before classification and persistence: if persist fails after dedupe has saved fingerprints, those items are never retried.
- The same story with a changed title is treated as new.

## Alternatives considered

None recorded. (Inferred: a plain function chain would have been enough; LangGraph may have been chosen for familiarity or future branching. See A-012.)

## Evidence

- `singularity_atlas/pipeline.py` (module docstring, nodes, `build_graph`)
- `singularity_atlas/feeds.py` `fetch_all`, `fetch_gdelt`
- `tests/test_pipeline.py`, `tests/test_feeds.py` (`TestFetchAll.test_feed_isolation`, `test_gdelt_429_retry`)
- Commit `ed3300c`
