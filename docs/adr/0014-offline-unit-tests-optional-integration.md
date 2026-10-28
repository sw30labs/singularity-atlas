# 0014. Offline unit tests by default; Neo4j and corpus tests skip when unavailable

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`, `6f005f4`)

## Context

`tests/conftest.py`: "Unit tests run offline; integration tests need Neo4j."

## Decision

- Network is mocked (`httpx.MockTransport`, patched `urlopen`, monkeypatched `llm.httpx`).
- An autouse fixture redirects every on-disk state file (`seen.json`, `si_history.jsonl`, `feed_health.json`, `loop_issues/`, `loop_sync.json`) to `tmp_path`, so tests never touch real `data/`.
- Tests needing Neo4j are marked `integration` and skipped via `requires_neo4j` when the container doesn't answer; corpus tests skip when `ref/` is absent.
- API tests stub the scheduler so importing the app never starts ingests.

## Consequences

**Positive**
- `pytest` runs anywhere, fast, with no side effects.

**Negative**
- On a fresh clone the archive tests and all integration tests silently skip, so CI-like runs cover less than a local run with Neo4j and the corpus.
- No CI configuration exists in the repo; the publish scripts and the frontend have no tests.
- Integration tests write and delete fixed-ID nodes in whatever Neo4j is configured (the real one by default).

## Alternatives considered

None recorded.

## Evidence

- `tests/conftest.py`, `tests/test_*.py`, `pyproject.toml` (pytest markers)
- Commits `ed3300c`, `6f005f4`
