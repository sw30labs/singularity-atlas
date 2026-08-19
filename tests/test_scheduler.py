"""Scheduler mutex helpers — no Neo4j, no jobs."""

from singularity_atlas import scheduler


def test_ingest_running_tracks_the_lock():
    assert scheduler.ingest_running() is False
    assert scheduler._lock.acquire(blocking=False)
    try:
        assert scheduler.ingest_running() is True
    finally:
        scheduler._lock.release()
    assert scheduler.ingest_running() is False
