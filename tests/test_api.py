"""API surface: every endpoint returns sane JSON. Integration — needs Neo4j.

The scheduler is stubbed out so importing the app never starts ingests.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from singularity_atlas import api, config

pytestmark = pytest.mark.integration


@pytest.fixture()
def client(requires_neo4j, monkeypatch):
    monkeypatch.setattr(api.scheduler, "start", lambda: None)
    monkeypatch.setattr(api.scheduler, "stop", lambda: None)
    monkeypatch.setattr(api.scheduler, "last_run", lambda: None)
    monkeypatch.setattr(api.scheduler, "ingest_running", lambda: False)
    with TestClient(api.app) as c:
        yield c


class TestStatic:
    def test_index(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "SINGULARITY" in r.text.upper()

    def test_static_assets(self, client):
        for path in ("/static/app.js", "/static/style.css", "/static/favicon.svg"):
            assert client.get(path).status_code == 200

    def test_glyphs_in_chrome(self, client):
        html = client.get("/").text
        assert 'id="lobster"' in html
        assert 'id="aineko"' in html


class TestEndpoints:
    def test_state_shape(self, client):
        d = client.get("/api/state").json()
        for key in ("si", "si_history", "vectors", "signals", "convergence",
                    "brief", "feeds", "graph", "llm", "quotes",
                    "si_baseline_days", "ingest_running"):
            assert key in d, key
        assert 0 <= d["si"]["si"] <= 100
        # the frontend renders the delta label from this, so it must be a
        # positive number of days, not a hardcoded literal
        assert d["si_baseline_days"] == config.SI_BASELINE_DAYS > 0
        assert set(d["vectors"].keys()) == set(d["signals"].keys())

    def test_si(self, client):
        d = client.get("/api/si").json()
        assert "current" in d and "history" in d and "epochs" in d
        assert len(d["epochs"]) == 3

    def test_signals(self, client):
        d = client.get("/api/signals", params={"vector": "compute"}).json()
        assert d["vector"] == "compute"
        assert isinstance(d["stories"], list)

    def test_convergence(self, client):
        d = client.get("/api/convergence").json()
        assert isinstance(d["convergence"], list)
        for row in d["convergence"]:
            assert len(row["vecs"]) >= 2

    def test_globe_payload(self, client):
        d = client.get("/api/globe").json()
        assert set(d) >= {"sites", "events", "arcs", "launches"}
        assert len(d["sites"]) > 20
        for s in d["sites"]:
            assert -90 <= s["lat"] <= 90 and -180 <= s["lon"] <= 180

    def test_brief(self, client):
        d = client.get("/api/brief").json()
        assert "brief" in d and "history" in d
        if d["brief"]:
            assert len(d["brief"]["text"]) > 100

    def test_ingest_status(self, client):
        d = client.get("/api/ingest").json()
        assert d["running"] is False
        assert "last" in d

    def test_graph_requires_entity(self, client):
        assert client.get("/api/graph").status_code == 422
        d = client.get("/api/graph", params={"entity": "OpenAI"}).json()
        assert set(d) >= {"nodes", "edges", "loop_editions"}

    def test_archive_search(self, client):
        assert client.get("/api/archive/search", params={"q": "x"}).status_code == 422
        d = client.get("/api/archive/search", params={"q": "orbital"}).json()
        assert isinstance(d["hits"], list)

    def test_archive_entity(self, client):
        d = client.get("/api/archive/entity", params={"name": "OpenAI"}).json()
        assert d["entity"] == "OpenAI"
        assert isinstance(d["editions"], list)

    def test_feeds_health(self, client):
        d = client.get("/api/feeds").json()
        assert "feeds" in d and "configured" in d
        assert len(d["configured"]) >= 10
