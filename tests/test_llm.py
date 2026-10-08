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


class OpenAIResp:
    def __init__(self, status: int, payload: dict):
        self.status_code = status
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("bad", request=None, response=None)

    def json(self):
        return self._payload


def openai_ok(content: str) -> OpenAIResp:
    return OpenAIResp(200, {"choices": [{"message": {"role": "assistant", "content": content}}]})


class TestOpenAI:
    @pytest.fixture(autouse=True)
    def _openai(self, monkeypatch):
        monkeypatch.setattr(llm.config, "LLM_PROVIDER", "openai")
        monkeypatch.setattr(llm.config, "OPENAI_MODEL", "gpt-test")
        monkeypatch.setattr(llm.config, "OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(llm.config, "OPENAI_BASE_URL", "https://api.openai.com/v1")

        def no_tags(*a, **k):
            raise AssertionError("OpenAI provider must not poll Ollama")
        monkeypatch.setattr(llm.httpx, "get", no_tags)

    def test_resolves_configured_model(self):
        assert llm.provider() == "openai"
        assert llm.resolve_model() == "gpt-test"
        assert llm.preferred_model() == "gpt-test"
        assert llm.current_model() == "gpt-test"

    def test_unavailable_without_key(self, monkeypatch):
        monkeypatch.setattr(llm.config, "OPENAI_API_KEY", "")
        assert llm.available() is False
        assert llm.chat("hi") is None

    def test_chat_request_shape(self, monkeypatch):
        captured = {}

        def fake_post(url, json=None, headers=None, timeout=None):
            captured.update(url=url, body=dict(json), headers=headers)
            return openai_ok(" hello ")

        monkeypatch.setattr(llm.httpx, "post", fake_post)
        assert llm.chat("hi", system="sys", max_tokens=50) == "hello"
        assert captured["url"] == "https://api.openai.com/v1/chat/completions"
        assert captured["headers"] == {"Authorization": "Bearer sk-test"}
        assert captured["body"]["model"] == "gpt-test"
        assert captured["body"]["max_completion_tokens"] == 50
        assert captured["body"]["messages"][0] == {"role": "system", "content": "sys"}

    def test_retries_without_rejected_temperature(self, monkeypatch):
        bodies = []

        def fake_post(url, json=None, headers=None, timeout=None):
            bodies.append(dict(json))
            if "temperature" in json:
                return OpenAIResp(400, {"error": {"param": "temperature",
                                                  "code": "unsupported_value"}})
            return openai_ok("ok")

        monkeypatch.setattr(llm.httpx, "post", fake_post)
        assert llm.chat("hi", temperature=0.7) == "ok"
        assert len(bodies) == 2 and "temperature" not in bodies[1]

    def test_other_400_is_none(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: OpenAIResp(
            400, {"error": {"param": "model", "code": "model_not_found"}}))
        assert llm.chat("hi") is None

    def test_chat_json(self, monkeypatch):
        monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: openai_ok('{"a": 1}'))
        assert llm.chat_json("x") == {"a": 1}
