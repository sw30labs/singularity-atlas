"""Store: pure helpers (offline) + integration tests against the live container."""

from __future__ import annotations


import pytest

from singularity_atlas import store


class TestDecodeStory:
    def test_decodes_extra_json(self):
        st = store._decode_story({"extra": '{"lat": 1.5}'})
        assert st["extra"] == {"lat": 1.5}

    def test_tolerates_garbage(self):
        st = store._decode_story({"extra": "{oops"})
        assert st["extra"] == {}

    def test_missing_extra(self):
        st = store._decode_story({})
        assert "extra" not in st or st.get("extra") is None


class TestSIHistoryFile:
    def test_roundtrip(self):
        assert store.si_history() == []
        store.append_si({"ts": "t1", "si": 10.0})
        store.append_si({"ts": "t2", "si": 20.0})
        hist = store.si_history()
        assert [h["si"] for h in hist] == [10.0, 20.0]

    def test_limit_and_corruption(self):
        for i in range(10):
            store.append_si({"ts": f"t{i}", "si": float(i)})
        from singularity_atlas import config
        with config.SI_HISTORY_FILE.open("a") as f:
            f.write("not-json\n")
        hist = store.si_history(limit=5)
        assert len(hist) <= 5
        assert all(isinstance(h["si"], float) for h in hist)


@pytest.mark.integration
class TestNeo4j:
    TEST_ID = "pytest-story-0001"

    def test_ping(self, requires_neo4j):
        assert store.ping() is True

    def test_schema_idempotent(self, requires_neo4j):
        store.init_schema()
        store.init_schema()  # second run must not raise

    def test_story_roundtrip(self, requires_neo4j):
        store.init_schema()
        item = {
            "id": self.TEST_ID, "source": "pytest", "source_label": "Pytest",
            "title": "Integration test story about OpenAI and TSMC in Taiwan",
            "url": "https://example.com/pytest",
            "summary": "integration", "published_at": "2099-01-01T00:00:00+00:00",
            "salience": 3.14, "vectors": {"compute": 2.0, "capability": 1.0},
            "entities": [{"name": "PytestOrg", "type": "org"}],
            "places": [{"name": "Taiwan", "lat": 23.7, "lon": 121.0}],
            "extra": {"k": "v"},
        }
        try:
            n = store.persist_items([item])
            assert n == 1
            found = self._get(self.TEST_ID)
            assert found is not None
            assert found["salience"] == pytest.approx(3.14)
            assert found["extra"] == {"k": "v"}
        finally:
            self._delete(self.TEST_ID)
        assert self._get(self.TEST_ID) is None

    def test_brief_roundtrip(self, requires_neo4j):
        store.init_schema()
        store.save_brief("pytest brief text", model="pytest", n_items=1,
                         brief_date="2099-01-01")
        try:
            b = store.latest_brief()
            assert b["date"] == "2099-01-01"
            assert b["model"] == "pytest"
            assert "2099-01-01" in [h["date"] for h in store.brief_history()]
        finally:
            with store.driver().session() as s:
                s.run("MATCH (b:Brief {id: 'brief-2099-01-01'}) DETACH DELETE b")

    def test_graph_stats_keys(self, requires_neo4j):
        stats = store.graph_stats()
        assert set(stats) == {"stories", "entities", "briefs", "edges"}
        assert all(isinstance(v, int) and v >= 0 for v in stats.values())

    def test_queries_return_lists(self, requires_neo4j):
        assert isinstance(store.recent_stories(hours=1), list)
        assert isinstance(store.convergence(hours=1), list)
        assert isinstance(store.globe_events(hours=1), list)
        assert isinstance(store.globe_arcs(hours=1), list)
        assert isinstance(store.upcoming_launches(), list)
        vs = store.vector_signals(hours=1)
        assert set(vs.keys()) == set(store.config.VECTOR_NAMES)

    def _get(self, story_id):
        with store.driver().session() as s:
            r = s.run("MATCH (s:Story {id: $id}) RETURN s", id=story_id).single()
            return store._decode_story(dict(r["s"])) if r else None

    def _delete(self, story_id):
        with store.driver().session() as s:
            s.run("MATCH (s:Story {id: $id}) DETACH DELETE s", id=story_id)
            s.run("MATCH (e:Entity {name: 'PytestOrg'}) DETACH DELETE e")
