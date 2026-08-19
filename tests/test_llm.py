"""LLM wrapper: model resolution, chat, JSON extraction — all httpx mocked."""

from __future__ import annotations

import httpx
import pytest

from singularity_atlas import llm


@pytest.fixture(autouse=True)
def _reset_llm_cache():
    llm.reset_cache()
    yield
    llm.reset_cache()


def fake_tags(*names: str):
    class Resp:
        def json(self):
            return {"models": [{"name": n} for n in names]}
    return Resp()


class ChatResp:
    def __init__(self, content: str):
        self._content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"role": "assistant", "content": self._content}}


class TestResolveModel:
    def test_preferred_wins(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "get",
                            lambda *a, **k: fake_tags("qwen3.8:27b-mtp-bf16", "qwen3:14b"))
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "qwen3.8:27b-mtp-bf16")
        assert llm.resolve_model() == "qwen3.8:27b-mtp-bf16"

    def test_fallback_chain(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "get",
                            lambda *a, **k: fake_tags("qwen3:30b-a3b-instruct-2507-q4_K_M"))
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "not-pulled:latest")
        assert llm.resolve_model() == "qwen3:30b-a3b-instruct-2507-q4_K_M"

    def test_latest_suffix_accepted(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "get", lambda *a, **k: fake_tags("qwen3:14b"))
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "qwen3:14b")
        assert llm.resolve_model() == "qwen3:14b"

    def test_none_when_empty(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "get", lambda *a, **k: fake_tags())
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "nope")
        assert llm.resolve_model() is None
        assert llm.available() is False

    def test_none_on_connection_error(self, monkeypatch):
        def boom(*a, **k):
            raise httpx.ConnectError("down")
        monkeypatch.setattr(llm.httpx, "get", boom)
        assert llm.resolve_model() is None

    def test_cache_ttl(self, monkeypatch):
        calls = {"n": 0}

        def counting_get(*a, **k):
            calls["n"] += 1
            return fake_tags("qwen3:14b")

        monkeypatch.setattr(llm.httpx, "get", counting_get)
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "qwen3:14b")
        llm.resolve_model()
        llm.resolve_model()
        assert calls["n"] == 1  # second call served from cache


class TestChat:
    def test_chat_returns_content(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "get", lambda *a, **k: fake_tags("m:latest"))
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "m")
        captured = {}

        def fake_post(url, json=None, timeout=None):
            captured.update(json or {})
            return ChatResp("hello world")

        monkeypatch.setattr(llm.httpx, "post", fake_post)
        assert llm.chat("hi", system="sys") == "hello world"
        assert captured["think"] is False
        assert captured["messages"][0] == {"role": "system", "content": "sys"}
        assert captured["messages"][1]["role"] == "user"

    def test_chat_none_without_model(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "get", lambda *a, **k: fake_tags())
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "m")
        assert llm.chat("hi") is None

    def test_chat_none_on_http_error(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "get", lambda *a, **k: fake_tags("m:latest"))
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "m")

        def boom(*a, **k):
            raise httpx.ReadTimeout("slow")

        monkeypatch.setattr(llm.httpx, "post", boom)
        assert llm.chat("hi") is None


class TestChatJson:
    def _wire(self, monkeypatch, content: str):
        monkeypatch.setattr(llm.httpx, "get", lambda *a, **k: fake_tags("m:latest"))
        monkeypatch.setattr(llm.config, "OLLAMA_MODEL", "m")
        monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: ChatResp(content))

    def test_plain_json(self, monkeypatch):
        self._wire(monkeypatch, '{"a": 1}')
        assert llm.chat_json("x") == {"a": 1}

    def test_fenced_json(self, monkeypatch):
        self._wire(monkeypatch, "```json\n{\"a\": 2}\n```")
        assert llm.chat_json("x") == {"a": 2}

    def test_json_embedded_in_prose(self, monkeypatch):
        self._wire(monkeypatch, 'Sure! Here you go: {"b": [1, 2]} hope that helps')
        assert llm.chat_json("x") == {"b": [1, 2]}

    def test_garbage_returns_none(self, monkeypatch):
        self._wire(monkeypatch, "no json at all here")
        assert llm.chat_json("x") is None

    def test_broken_json_returns_none(self, monkeypatch):
        self._wire(monkeypatch, '{"a": ')
        assert llm.chat_json("x") is None
