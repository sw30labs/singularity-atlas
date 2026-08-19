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
