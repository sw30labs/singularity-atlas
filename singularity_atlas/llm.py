"""LLM wrapper (Ollama or OpenAI) with graceful degradation and model auto-resolution.

ATLAS_LLM_PROVIDER picks the backend. "ollama" (default) stays on this machine.
"openai" sends prompts — headlines, summaries — to the OpenAI Chat Completions
API using OPENAI_API_KEY (environment or the gitignored .env) and ATLAS_OPENAI_MODEL.

Ollama preference order: the configured ATLAS_MODEL first, then known-good fallbacks
that are already pulled. The tag list is re-polled every 60s, so when a new
model finishes `ollama pull`, the app picks it up without a restart.

If Ollama serves no usable model, every function returns None and callers
fall back to heuristics. The app never hard-depends on the LLM.
"""

from __future__ import annotations

import json
import re
import time

import httpx

from . import config

FALLBACK_MODELS = [
    "qwen3:30b-a3b-instruct-2507-q4_K_M",
    "qwen3:30b-a3b",
    "qwen3:32b",
    "qwen3:14b",
]

_cache = {"ts": 0.0, "model": None}
CACHE_TTL_S = 60


def provider() -> str:
    return "openai" if config.LLM_PROVIDER == "openai" else "ollama"


def preferred_model() -> str:
    """The configured model for the active provider (for labels)."""
    return config.OPENAI_MODEL if provider() == "openai" else config.OLLAMA_MODEL


def resolve_model() -> str | None:
    """Best available model name, or None. Re-polls /api/tags every CACHE_TTL_S."""
    if provider() == "openai":
        # no probe: a missing key is the only thing we can know without spending a call
        model = config.OPENAI_MODEL if config.OPENAI_API_KEY else None
        _cache.update(ts=time.time(), model=model)
        return model
    now = time.time()
    if now - _cache["ts"] < CACHE_TTL_S:
        return _cache["model"]
    model = None
    try:
        r = httpx.get(f"{config.OLLAMA_HOST}/api/tags", timeout=5)
        names = {m.get("name", "") for m in r.json().get("models", [])}
        for want in [config.OLLAMA_MODEL, *FALLBACK_MODELS]:
            if want in names:
                model = want
                break
            if f"{want}:latest" in names:
                model = f"{want}:latest"
                break
    except Exception:
        model = None
    _cache.update(ts=now, model=model)
    return model


def current_model() -> str | None:
    """The model in use right now (for labels), without forcing a re-poll."""
    return _cache["model"]


def available() -> bool:
    return resolve_model() is not None


def reset_cache() -> None:
    _cache.update(ts=0.0, model=None)


def chat(prompt: str, system: str = "", temperature: float = 0.7,
         max_tokens: int = 2048, think: bool = False) -> str | None:
    """Single-turn chat via the active provider. None on any failure."""
    model = resolve_model()
    if model is None:
        return None
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    if provider() == "openai":
        return _openai_chat(model, messages, temperature, max_tokens)
    try:
        r = httpx.post(
            f"{config.OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "think": think,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=config.LLM_TIMEOUT_S,
        )
        r.raise_for_status()
        text = (r.json().get("message") or {}).get("content", "").strip()
        return text or None
    except Exception:
        return None


def _openai_chat(model: str, messages: list[dict], temperature: float,
                 max_tokens: int) -> str | None:
    """POST /chat/completions. Reasoning models reject a non-default temperature;
    when the API names it as the bad parameter, retry once without it."""
    body = {"model": model, "messages": messages,
            "max_completion_tokens": max_tokens, "temperature": temperature}
    headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"}
    try:
        for _ in range(2):
            r = httpx.post(f"{config.OPENAI_BASE_URL}/chat/completions", json=body,
                           headers=headers, timeout=config.LLM_TIMEOUT_S)
            if r.status_code == 400 and "temperature" in body:
                err = (r.json().get("error") or {})
                if err.get("param") == "temperature":
                    body.pop("temperature")
                    continue
            r.raise_for_status()
            choices = r.json().get("choices") or [{}]
            text = ((choices[0].get("message") or {}).get("content") or "").strip()
            return text or None
    except Exception:
        return None
    return None


def chat_json(prompt: str, system: str = "") -> dict | list | None:
    """Chat that must return JSON. Strips code fences, tolerates prose around it."""
    text = chat(prompt, system=system + "\nRespond with JSON only.", temperature=0.2,
                max_tokens=768)
    if not text:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    # grab the outermost JSON value
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
