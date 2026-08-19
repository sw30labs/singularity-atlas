"""APScheduler wiring: ingest every N minutes, single-instance, boot catch-up."""

from __future__ import annotations

import threading

from apscheduler.schedulers.background import BackgroundScheduler

from . import config, pipeline, store

_lock = threading.Lock()
_scheduler: BackgroundScheduler | None = None
_last_run: dict | None = None


def run_ingest_safe() -> dict:
    """Ingest with a mutex so scheduler and manual triggers never overlap."""
    global _last_run
    if not _lock.acquire(blocking=False):
        return {"skipped": "ingest already running"}
    try:
        _last_run = pipeline.run_ingest()
        return _last_run
    finally:
        _lock.release()


def last_run() -> dict | None:
    return _last_run


def start() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    store.init_schema()
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(run_ingest_safe, "interval",
                       minutes=config.INGEST_INTERVAL_MIN,
                       id="ingest", max_instances=1, coalesce=True)
    _scheduler.start()
    # boot cycle in background so the server is immediately responsive
    threading.Thread(target=run_ingest_safe, daemon=True).start()


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
