"""Pipeline: dedupe, classify (heuristic + mocked-LLM), brief logic, graph assembly."""

from __future__ import annotations

from singularity_atlas import llm, pipeline


class TestFingerprint:
    def test_stable(self):
        item = {"url": "https://x.com/a", "title": "Hello"}
        assert pipeline._fingerprint(item) == pipeline._fingerprint(item)

    def test_title_case_insensitive(self):
        a = pipeline._fingerprint({"url": "https://x.com/a", "title": "Hello"})
        b = pipeline._fingerprint({"url": "https://x.com/a", "title": "HELLO"})
        assert a == b

    def test_distinct(self):
        a = pipeline._fingerprint({"url": "https://x.com/a", "title": "A"})
        b = pipeline._fingerprint({"url": "https://x.com/b", "title": "A"})
        assert a != b

    def test_launch_net_is_part_of_the_fingerprint(self):
        early = {"source": "launches", "url": "https://ll.example/1",
                 "title": "Falcon 9", "published_at": "2026-12-31T00:00:00Z"}
        slipped = dict(early, published_at="2026-11-29T15:47:00Z")
        news = {"source": "verge-ai", "url": "https://x.com/a", "title": "Hello",
                "published_at": "2026-11-19T00:00:00Z"}
        assert pipeline._fingerprint(early) != pipeline._fingerprint(slipped)
        assert pipeline._fingerprint(news) == pipeline._fingerprint(
            dict(news, published_at="2026-11-18T00:00:00Z"))


class TestDedupeNode:
    def test_filters_seen(self):
        items = [{"url": "https://x.com/1", "title": "one"},
                 {"url": "https://x.com/2", "title": "two"}]
        state = {"raw_items": items}
        out1 = pipeline.node_dedupe(state)
        assert out1["stats"] == {"fetched": 2, "new": 2}
        out2 = pipeline.node_dedupe({"raw_items": items})
        assert out2["stats"]["new"] == 0
        assert out2["items"] == []

    def test_launch_is_readmitted_when_its_net_changes(self):
        launch = {"id": "L1", "source": "launches", "url": "https://ll.example/1",
                  "title": "Falcon 9", "published_at": "2026-12-31T00:00:00Z"}
        out1 = pipeline.node_dedupe({"raw_items": [launch]})
        assert out1["stats"]["new"] == 1
        slipped = dict(launch, published_at="2026-11-29T15:47:00Z")
        out2 = pipeline.node_dedupe({"raw_items": [slipped]})
        assert [it["published_at"] for it in out2["items"]] == ["2026-11-29T15:47:00Z"]


class TestLaunchRetirement:
    def test_retire_runs_only_after_a_real_launch_fetch(self, monkeypatch):
        calls = []
        monkeypatch.setattr(pipeline.store, "persist_items", lambda items: 0)
        monkeypatch.setattr(pipeline.store, "retire_stale_launches",
                            lambda ids: calls.append(list(ids)) or 2)
        skipped = pipeline.node_persist({"items": [], "launch_ids": None})
        assert "launches_retired" not in skipped["stats"]
        assert calls == []
        out = pipeline.node_persist({"items": [], "launch_ids": ["a", "b"]})
        assert calls == [["a", "b"]]
        assert out["stats"]["launches_retired"] == 2


class TestClassifyItem:
    def test_heuristic_path(self, monkeypatch, sample_item):
        monkeypatch.setattr(llm, "chat_json", lambda *a, **k: None)
        out = pipeline._classify_item(dict(sample_item), [99])
        assert out["vectors"]["compute"] >= 1.5  # hint + keywords
        names = {e["name"] for e in out["entities"]}
        assert "NVIDIA" in names and "OpenAI" in names
        assert any(p["name"] == "Ohio" for p in out["places"])
        assert out["salience"] > 0

    def test_llm_refinement_merges(self, monkeypatch, sample_item):
        monkeypatch.setattr(llm, "chat_json", lambda *a, **k: {
            "vectors": {"security": 4, "bogus-vector": 5},
            "entities": [{"name": "data centers", "type": "tech"},   # stoplisted
                         {"name": "nvidia", "type": "org"},            # canonicalized
                         {"name": "Anthropic", "type": "org"}],
            "oneline": "A wry line.",
        })
        out = pipeline._classify_item(dict(sample_item), [1])
        assert out["vectors"]["security"] == 4.0
        assert "bogus-vector" not in out["vectors"]
        names = [e["name"] for e in out["entities"]]
        assert names.count("NVIDIA") == 1           # canonical dedupe
        assert "Anthropic" in names
        assert "data centers" not in names          # stoplist applied
        assert out["oneline"] == "A wry line."

    def test_budget_spent_only_on_success(self, monkeypatch, sample_item):
        calls = {"n": 0}

        def sometimes(*a, **k):
            calls["n"] += 1
            return None  # failure → budget untouched

        monkeypatch.setattr(llm, "chat_json", sometimes)
        budget = [1]
        pipeline._classify_item(dict(sample_item), budget)
        assert budget[0] == 1  # not decremented on failure
        assert calls["n"] == 1


class TestEntityStoplist:
    def test_stoplist_entries_rejected(self):
        out = pipeline._clean_llm_entities(
            [{"name": n, "type": "tech"} for n in
             ["AI", "data centers", "LLM", "NVIDIA"]], set())
        assert [e["name"] for e in out] == ["NVIDIA"]

    def test_canonicalization(self):
        out = pipeline._clean_llm_entities([{"name": "openai", "type": "org"}], set())
        assert out == [{"name": "OpenAI", "type": "org"}]

    def test_unknown_entity_kept_with_declared_type(self):
        out = pipeline._clean_llm_entities([{"name": "PORTS-Pike", "type": "project"}], set())
        assert out == [{"name": "PORTS-Pike", "type": "project"}]


class TestFallbackBrief:
    def test_contains_essentials(self):
        stories = [{"title": "Thing happened", "url": "https://x.com/a",
                    "source_label": "Test", "vectors": {"compute": 2.0}}]
        si = {"si": 42.0, "epoch": {"name": "Point of Inflexion"},
              "countdown": {"days": 100, "target": "2045-01-01"}, "n_stories_24h": 7}
        text = pipeline._fallback_brief(stories, si)
        assert "# Welcome to" in text
        assert "42.0/100" in text
        assert "[Thing happened](https://x.com/a)" in text
        assert "heuristic" in text.lower()


class TestBriefRefreshLogic:
    def _si(self):
        return {"si": 50.0, "epoch": {"name": "Point of Inflexion"},
                "countdown": {"days": 100, "target": "2045-01-01"}, "n_stories_24h": 5}

    def test_skip_when_few_new_and_fresh_brief(self, monkeypatch):
        monkeypatch.setattr(pipeline.store, "latest_brief",
                            lambda: {"model": "ollama", "date": _today()})
        monkeypatch.setattr(pipeline.scoring, "compute_si", self._si)
        out = pipeline.node_brief({"stats": {"new": 0}, "si": self._si()})
        assert out["brief"] is None

    def test_refresh_when_brief_is_heuristic_and_llm_back(self, monkeypatch):
        monkeypatch.setattr(pipeline.store, "latest_brief",
                            lambda: {"model": "heuristic", "date": _today()})
        monkeypatch.setattr(pipeline.store, "recent_stories", lambda **k: [
            {"title": "T", "url": "https://x.com", "source_label": "S",
             "vectors": {}, "summary": "s", "salience": 1.0}])
        monkeypatch.setattr(pipeline.store, "save_brief",
                            lambda text, model, n_items: "2026-08-19")
        monkeypatch.setattr(llm, "available", lambda: True)
        monkeypatch.setattr(llm, "chat", lambda *a, **k: "# Welcome\ntext")
        monkeypatch.setattr(llm, "current_model", lambda: "m:latest")
        out = pipeline.node_brief({"stats": {"new": 0}, "si": self._si()})
        assert out["brief_model"] == "m:latest"
        assert out["brief"] == "# Welcome\ntext"

    def test_refresh_heuristic_when_the_baked_index_drifted(self, monkeypatch):
        monkeypatch.setattr(pipeline.store, "latest_brief", lambda: {
            "model": "heuristic", "date": _today(),
            "text": "The Singularity Index reads **70.7/100** — Singularity.",
        })
        monkeypatch.setattr(pipeline.store, "recent_stories", lambda **k: [
            {"title": "T", "url": "https://x.com", "source_label": "S",
             "vectors": {}, "summary": "s", "salience": 1.0}])
        saved = {}

        def save(text, model, n_items):
            saved["text"] = text
            saved["model"] = model
            return _today()

        monkeypatch.setattr(pipeline.store, "save_brief", save)
        monkeypatch.setattr(llm, "available", lambda: False)
        monkeypatch.setattr(llm, "chat", lambda *a, **k: None)
        monkeypatch.setattr(llm, "current_model", lambda: None)
        out = pipeline.node_brief({"stats": {"new": 0}, "si": self._si()})
        assert out["brief_model"] == "heuristic"
        assert "50.0/100" in saved["text"]

    def test_skip_heuristic_when_the_baked_index_still_matches(self, monkeypatch):
        monkeypatch.setattr(pipeline.store, "latest_brief", lambda: {
            "model": "heuristic", "date": _today(),
            "text": "The Singularity Index reads **50.0/100** — Point of Inflexion.",
        })
        monkeypatch.setattr(llm, "available", lambda: False)
        out = pipeline.node_brief({"stats": {"new": 0}, "si": self._si()})
        assert out["brief"] is None


def _today() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).date().isoformat()


class TestGraphAssembly:
    def test_compiles(self):
        g = pipeline.build_graph()
        assert g is not None

    def test_node_order(self):
        g = pipeline.build_graph()
        # the compiled graph exposes its node names
        names = set(g.get_graph().nodes.keys())
        assert {"fetch", "dedupe", "classify", "persist", "score", "brief"} <= names
