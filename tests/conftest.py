"""Shared fixtures. Unit tests run offline; integration tests need Neo4j."""

from __future__ import annotations

import pytest

from singularity_atlas import store


@pytest.fixture()
def sample_item() -> dict:
    return {
        "id": "test-item-0001",
        "source": "test", "source_label": "Test Feed",
        "title": "NVIDIA and OpenAI break ground on 10-gigawatt datacenter in Ohio",
        "url": "https://example.com/story/1",
        "summary": "The gigawatt campus will train frontier models on H100 clusters.",
        "published_at": "2026-08-19T00:00:00+00:00",
        "vectors_hint": ["compute"],
        "extra": {},
    }


@pytest.fixture(scope="session")
def neo4j_up() -> bool:
    """True if the worldview Neo4j container answers."""
    try:
        return store.ping()
    except Exception:
        return False


@pytest.fixture()
def requires_neo4j(neo4j_up):
    if not neo4j_up:
        pytest.skip("Neo4j not available")


@pytest.fixture(autouse=True)
def _isolate_files(tmp_path, monkeypatch):
    """Point on-disk state at tmp so tests never touch the real data/ dir."""
    from singularity_atlas import config, loop_archive, moonshot_archive, moonshot_forecasts
    monkeypatch.setattr(config, "SEEN_FILE", tmp_path / "seen.json")
    monkeypatch.setattr(config, "SI_HISTORY_FILE", tmp_path / "si_history.jsonl")
    monkeypatch.setattr(config, "FEED_HEALTH_FILE", tmp_path / "feed_health.json")
    monkeypatch.setattr(config, "LOOP_FETCH_DIR", tmp_path / "loop_issues")
    monkeypatch.setattr(config, "LOOP_SYNC_STATE_FILE", tmp_path / "loop_sync.json")
    # keep unit tests off the 235 MB local transcript dump
    moonshot_dir = tmp_path / "moonshots"
    moonshot_dir.mkdir()
    monkeypatch.setattr(config, "MOONSHOT_DIR", moonshot_dir)
    monkeypatch.setattr(config, "MOONSHOT_DATES_FILE", tmp_path / "moonshot_dates.json")
    # the archive caches parsed editions in-process; keep tests independent
    loop_archive.invalidate()
    moonshot_archive.invalidate()
    moonshot_forecasts.invalidate()
    yield
    loop_archive.invalidate()
    moonshot_archive.invalidate()
    moonshot_forecasts.invalidate()
