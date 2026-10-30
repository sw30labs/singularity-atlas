# 0009. Keep the Loop Archive current from the author's official Substack RSS, in the corpus's own format

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`6f005f4`)

## Context

The local reference corpus under `ref/` "stops at whatever edition it was exported at" (`loop_sync.py`). Commit `6f005f4` added "Keep the Loop Archive current from Alex's official Substack feed".

## Decision

- `innermost_loop.py` is a standard-library-only fetcher for `https://theinnermostloop.substack.com/feed`: argument validation, bounded reads, retries on transient errors (`URLError`, `IncompleteRead`), sort by real instant across mixed timezone offsets, de-duplication by GUID, and cleanup of Substack widget/interface noise. NOTICE says it is "vendored from a sibling project".
- `loop_sync.sync()` writes new editions to gitignored `data/loop_issues/` in the same front-matter markdown format as the shipped corpus, named `NNN--YYYY-MM-DD--slug.md`, continuing numbering from the highest existing edition.
- **Dating rule:** a "Welcome to <Month D, YYYY>" title is authoritative over the feed's `pubDate` (edition 218 was published 08-18 but is dated 08-17); otherwise fall back to `published_at`.
- Already-archived editions are skipped; feed failures are recorded in `loop_sync.json` (`checked_at`, `error`), never raised.
- Only new editions are persisted to Neo4j as `origin: archive` stories (`sync_and_persist`). Runs daily from the scheduler (ADR 0004) or via `POST /api/archive/sync`.

## Consequences

**Positive**
- Search and "on this date" stay current without re-exporting the corpus.
- One parser (`loop_archive`) reads both shipped and fetched editions; a round-trip test enforces the format.

**Negative**
- Depends on the Substack feed layout and holding ~20 recent issues; gaps longer than that can't be backfilled.
- Edition numbers for fetched issues are local and may diverge from the newsletter's numbering if the corpus is absent (a fresh clone starts at 001).
- Licence of the vendored fetcher and local storage of full text are open questions (A-004, A-005).

## Alternatives considered

None recorded.

## Evidence

- `singularity_atlas/innermost_loop.py`, `singularity_atlas/loop_sync.py`, `singularity_atlas/loop_archive.py`
- `tests/test_innermost_loop.py`, `tests/test_loop_sync.py`
- `NOTICE` (innermost_loop.py provenance)
- Commit `6f005f4`
