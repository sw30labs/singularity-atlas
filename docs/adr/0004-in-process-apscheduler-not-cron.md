# 0004. Schedule ingest and archive sync inside the web process (APScheduler), not with cron

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`, extended `6f005f4`, `c65189d`)

## Context

Feeds must be polled continuously and the Innermost Loop archive checked daily. QUICKSTART § "Feed updates are not cron" documents the choice explicitly.

## Decision

- FastAPI's lifespan hook calls `scheduler.start()`: a `BackgroundScheduler` with an ingest job every `INGEST_INTERVAL_MIN = 15` minutes and a loop-sync job every `LOOP_SYNC_INTERVAL_H = 24` hours, both `max_instances=1, coalesce=True`.
- On boot, one ingest runs immediately in a background thread, and loop sync runs only if the last check is older than 24 h (`loop_sync.due()`).
- Each job is guarded by a non-blocking `threading.Lock`, so a manual `POST /api/ingest` and the scheduler never overlap ("ingest already running" is returned instead).
- "There is no crontab, launchd plist, or systemd unit." `Ctrl+C` stops both jobs.
- `setup_and_run.sh` kills stale Atlas dashboards (python/uvicorn processes only) before serving, because "a forgotten instance keeps ingesting in the background and holds the port".

## Consequences

**Positive**
- Nothing to install at OS level; the graph is fresh whenever the dashboard is up.
- Overlap protection is in one place.

**Negative**
- Freshness depends on the dashboard process staying up; there is no catch-up for missed ingest intervals other than the boot run.
- Running several uvicorn workers would start several schedulers (the lock is per-process).
- Scheduler state (`_last_run`) is in memory and lost on restart.
- The public publisher (ADR 0010) has to restart uvicorn itself if it's down, via `screen`.

## Alternatives considered

Cron, launchd and systemd were considered and rejected in the docs ("not cron"). The reason isn't stated beyond keeping updates "inside the dashboard process" (see A-013).

## Evidence

- `singularity_atlas/scheduler.py`, `singularity_atlas/api.py` `lifespan`
- `QUICKSTART.md` § Feed updates are not cron; `README.md` § Architecture
- `setup_and_run.sh` `stop_stale_dashboards`
- `tests/test_scheduler.py`
- Commits `ed3300c`, `6f005f4`, `c65189d`
