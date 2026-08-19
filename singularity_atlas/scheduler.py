"""APScheduler wiring: ingest every N minutes and a daily Loop Archive sync,
single-instance, with boot catch-up for both."""

from __future__ import annotations

import threading

from apscheduler.schedulers.background import BackgroundScheduler

from . import config, loop_sync, pipeline, store

_lock = threading.Lock()
_loop_lock = threading.Lock()
_scheduler: BackgroundScheduler | None = None
_last_run: dict | None = None
_last_loop_sync: dict | None = None


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


def run_loop_sync_safe() -> dict:
    """Pull new Innermost Loop editions and push them into the graph."""
    global _last_loop_sync
    if not _loop_lock.acquire(blocking=False):
        return {"skipped": "loop sync already running"}
    try:
        _last_loop_sync = loop_sync.sync_and_persist(store)
        return _last_loop_sync
    finally:
        _loop_lock.release()


def last_loop_sync() -> dict | None:
    return _last_loop_sync


def _loop_sync_catchup() -> None:
    """Sync at boot only if the feed has not been checked recently."""
    if loop_sync.due():
        run_loop_sync_safe()


def start() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    store.init_schema()
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(run_ingest_safe, "interval",
                       minutes=config.INGEST_INTERVAL_MIN,
                       id="ingest", max_instances=1, coalesce=True)
    _scheduler.add_job(run_loop_sync_safe, "interval",
                       hours=config.LOOP_SYNC_INTERVAL_H,
                       id="loop-sync", max_instances=1, coalesce=True)
    _scheduler.start()
    # boot cycles in background so the server is immediately responsive
    threading.Thread(target=run_ingest_safe, daemon=True).start()
    threading.Thread(target=_loop_sync_catchup, daemon=True).start()


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
