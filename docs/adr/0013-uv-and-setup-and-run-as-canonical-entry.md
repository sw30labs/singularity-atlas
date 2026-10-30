# 0013. uv-managed Python 3.12 project with `setup_and_run.sh` as the canonical entry point

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`, `c65189d`, `667775f`)

## Context

The project targets clone-and-run installs ("Run your own", QUICKSTART).

## Decision

- `pyproject.toml` (`requires-python >=3.12`, `uv_build` backend, Apache-2.0 with `LICENSE`/`NOTICE` as licence files) + committed `uv.lock`; `.python-version` pins the interpreter; dev group contains pytest only; pytest declares an `integration` marker.
- `setup_and_run.sh` (added `c65189d`) checks for uv, stops stale dashboards (`pgrep -f 'uvicorn singularity_atlas\.api:app'`, confirming the process is python/uvicorn), runs `uv sync`, creates the external Neo4j volume and starts compose, seeds the archive (`singularity_atlas.seed`), runs one ingest and the tests, then serves. `scripts/dev.sh` was reduced to a thin wrapper.
- QUICKSTART (`667775f`) documents a from-scratch install, optional Ollama, and what a clone doesn't include.
- Commit `4ff9f92` removed redundant zips, an unused `python-dateutil` dependency and dead code.

## Consequences

**Positive**
- Reproducible dependency set; one command to start.

**Negative**
- Requires uv and Docker; there is no non-Docker Neo4j path in the script.
- The stale-process killer matches by command line, so any process serving `singularity_atlas.api:app` (e.g. a second checkout) is stopped too.

## Alternatives considered

None recorded.

## Evidence

- `pyproject.toml`, `uv.lock` (not read line by line), `.python-version`, `setup_and_run.sh`, `scripts/dev.sh`, `QUICKSTART.md`
- Commits `ed3300c`, `4ff9f92`, `c65189d`, `667775f`
