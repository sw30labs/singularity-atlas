"""The ingest pipeline as a LangGraph StateGraph.

    fetch ─► dedupe ─► classify ─► persist ─► score ─► brief ─► END

State flows through typed nodes; every node is pure-ish (errors are
collected, never raised). Runs on a schedule (scheduler.py) or on demand
(POST /api/ingest, CLI `python -m singularity_atlas.pipeline`).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from . import config, feeds, llm, scoring, store, taxonomy


class PipelineState(TypedDict, total=False):
    raw_items: list[dict]
    items: list[dict]
    si: dict
    brief: str | None
    brief_model: str | None
    errors: list[str]
    stats: dict


# ---------------------------------------------------------------------------
# Dedupe persistence (seen fingerprints on disk)
# ---------------------------------------------------------------------------

def _load_seen() -> set[str]:
    if config.SEEN_FILE.exists():
        try:
            return set(json.loads(config.SEEN_FILE.read_text()))
        except Exception:
            return set()
    return set()


def _save_seen(seen: set[str]) -> None:
    # bound the set — keep the most recent ~50k
    if len(seen) > 50_000:
        seen = set(list(seen)[-50_000:])
    config.SEEN_FILE.write_text(json.dumps(list(seen)))


def _fingerprint(item: dict) -> str:
    base = (item.get("url") or "") + "|" + (item.get("title") or "").lower().strip()
    return hashlib.sha1(base.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def node_fetch(state: PipelineState) -> dict:
    items, errors = asyncio.run(feeds.fetch_all())
    return {"raw_items": items, "errors": errors}


def node_dedupe(state: PipelineState) -> dict:
    seen = _load_seen()
    fresh = []
    for item in state.get("raw_items", []):
        fp = _fingerprint(item)
        if fp in seen:
            continue
        seen.add(fp)
        fresh.append(item)
    _save_seen(seen)
    stats = {"fetched": len(state.get("raw_items", [])), "new": len(fresh)}
    return {"items": fresh, "stats": stats}


LLM_REFINE_PROMPT = """You classify technology news for a Singularity monitor.

Vectors: capability (frontier models/benchmarks), compute (chips/fabs/datacenters/energy),
capital (funding/valuations/M&A), embodiment (robots/drones/AVs), agency (agents/tool-use/open-weights),
security (safety/alignment/cyber/regulation), space (launches/orbital/lunar), culture (society/jobs/art/backlash).

Item:
Title: {title}
Summary: {summary}

Return JSON:
{{"vectors": {{"<vector>": <0-5 relevance>, ...}} (only vectors with relevance >= 2),
 "entities": [{{"name": "<canonical>", "type": "org|person|model|place|tech"}}...] (max 6, proper nouns only — no generic concepts like "AI chips" or "data centers"),
 "oneline": "<one dense, wry sentence in the register of a singularity daily newsletter>"}}"""


# Generic phrases the LLM keeps proposing as "entities" — filtered out.
ENTITY_STOPLIST = {
    "ai", "artificial intelligence", "agi", "machine learning", "deep learning",
    "ai chips", "ai chip", "data centers", "data center", "datacenter",
    "ai training", "ai models", "large language models", "llm", "llms",
    "exclusive arrangement", "open source", "the singularity", "singularity",
    "technology", "tech", "software", "hardware", "chips", "models",
}

# Case-insensitive canonicalization back onto the gazetteer.
_CANONICAL = {}
for _key, (_t, _canon) in taxonomy.GAZETTEER.items():
    _CANONICAL[_canon.lower()] = (_t, _canon)


def _clean_llm_entities(raw_entities: list, known: set[str]) -> list[dict]:
    out = []
    for e in raw_entities:
        if not isinstance(e, dict) or not e.get("name"):
            continue
        name = str(e["name"]).strip()
        low = name.lower()
        if low in ENTITY_STOPLIST or len(low) < 3:
            continue
        if low in _CANONICAL:
            etype, canon = _CANONICAL[low]
        else:
            etype, canon = (e.get("type") or "thing"), name
        if canon in known:
            continue
        known.add(canon)
        out.append({"name": canon, "type": etype})
    return out


def _classify_item(item: dict, llm_budget: list[int]) -> dict:
    text = f"{item.get('title', '')}\n{item.get('summary', '')}"
    scores = taxonomy.classify_text(text)
    for v in item.get("vectors_hint", []):
        scores[v] = scores.get(v, 0.0) + 1.5
    entities = taxonomy.extract_entities(text)
    places = taxonomy.extract_places(text)
    sal = taxonomy.salience(text, scores)

    # LLM refinement for ambiguous or high-signal items (bounded per cycle)
    if llm_budget[0] > 0 and (not scores or sal >= 2.5):
        refined = llm.chat_json(
            LLM_REFINE_PROMPT.format(title=item.get("title", ""),
                                     summary=(item.get("summary") or "")[:500]))
        if isinstance(refined, dict):
            llm_budget[0] -= 1
            for v, s in (refined.get("vectors") or {}).items():
                if v in config.VECTORS and isinstance(s, (int, float)):
                    scores[v] = max(scores.get(v, 0.0), min(5.0, float(s)))
            known = {e["name"] for e in entities}
            entities.extend(_clean_llm_entities(refined.get("entities") or [], known))
            if refined.get("oneline"):
                item["oneline"] = refined["oneline"]

    item["vectors"] = {v: round(s, 2) for v, s in scores.items() if v in config.VECTORS}
    item["entities"] = entities[:8]
    item["places"] = places[:3]
    item["salience"] = sal
    return item


def _refine_budget() -> int:
    """LLM refinements per cycle — dense models are slow, spend them wisely."""
    name = (llm.resolve_model() or "").lower()
    if any(tag in name for tag in ("bf16", "fp16", "70b", "32b", "27b", "235b")):
        return 6
    return 24


def node_classify(state: PipelineState) -> dict:
    budget = [_refine_budget()]
    items = [_classify_item(dict(it), budget) for it in state.get("items", [])]
    return {"items": items}


def node_persist(state: PipelineState) -> dict:
    n = store.persist_items(state.get("items", []))
    stats = dict(state.get("stats") or {})
    stats["persisted"] = n
    return {"stats": stats}


def node_score(state: PipelineState) -> dict:
    si = scoring.compute_si()
    store.append_si(si)
    return {"si": si}


BRIEF_SYSTEM = """You are the voice of a daily Singularity digest. Style rules, learned from
The Innermost Loop: dense linked prose; 4-6 paragraphs; each paragraph develops one theme
drawn from the signals; wry, allusive, aphoristic sentences; end the final paragraph with a
short aphoristic kicker. Never use bullet lists. Never mention that you are an AI writing a digest.
Cite sources as markdown links on the key noun phrase. Present tense. Comma splices allowed."""


def _brief_prompt(stories: list[dict], si: dict) -> str:
    lines = []
    for st in stories:
        vecs = ",".join((st.get("vectors") or {}).keys())
        lines.append(f"- [{st['title']}]({st.get('url', '')}) — {st.get('source_label', '')}"
                     f" — vectors: {vecs} — {(st.get('summary') or '')[:220]}")
    return (
        f"Today is {datetime.now(timezone.utc):%B %d, %Y}. "
        f"The Singularity Index reads {si['si']}/100 ({si['epoch']['name']}).\n\n"
        f"Today's signals (highest salience first):\n" + "\n".join(lines) +
        "\n\nWrite today's edition: 4-6 paragraphs, markdown links on the key claims. "
        "Open with a one-sentence thesis about what today means. Title the edition "
        "'Welcome to <Month D, YYYY>' as an H1."
    )


def _fallback_brief(stories: list[dict], si: dict) -> str:
    """Extractive brief when no LLM is available."""
    today = datetime.now(timezone.utc)
    parts = [f"# Welcome to {today:%B %d, %Y}".replace(" 0", " ")]
    parts.append(
        f"The Singularity Index reads **{si['si']}/100** — {si['epoch']['name']}. "
        f"{si['countdown']['days']} days to {si['countdown']['target']}. "
        f"{si['n_stories_24h']} signals crossed the wire in the last cycle."
    )
    for st in stories[:10]:
        vecs = ", ".join((st.get("vectors") or {}).keys())
        parts.append(f"[{st['title']}]({st.get('url', '')}) — *{st.get('source_label', '')}*"
                     + (f" · {vecs}" if vecs else ""))
    parts.append("\n*Heuristic edition — local LLM offline.*")
    return "\n\n".join(parts)


def node_brief(state: PipelineState) -> dict:
    stats = state.get("stats") or {}
    si = state.get("si") or scoring.compute_si()

    latest = store.latest_brief()
    today = datetime.now(timezone.utc).date().isoformat()
    should_refresh = (
        stats.get("new", 0) >= config.BRIEF_MIN_NEW_ITEMS
        or latest is None
        or (latest.get("model") == "heuristic" and llm.available())
        or latest.get("date") != today
    )
    if not should_refresh:
        return {"brief": None, "brief_model": None}

    stories = store.recent_stories(hours=24, limit=config.BRIEF_TOP_N)
    if not stories:
        return {"brief": None, "brief_model": None}

    text = llm.chat(_brief_prompt(stories, si), system=BRIEF_SYSTEM,
                    temperature=0.75, max_tokens=2200)
    model = (llm.current_model() or "ollama") if text else "heuristic"
    if not text:
        text = _fallback_brief(stories, si)
    brief_date = store.save_brief(text, model=model, n_items=len(stories))
    return {"brief": text, "brief_model": model,
            "stats": {**stats, "brief_date": brief_date}}


def run_brief_only() -> dict:
    """Force-regenerate today's brief (manual endpoint)."""
    si = scoring.compute_si()
    stories = store.recent_stories(hours=24, limit=config.BRIEF_TOP_N)
    if not stories:
        return {"error": "no stories in the last 24h"}
    text = llm.chat(_brief_prompt(stories, si), system=BRIEF_SYSTEM,
                    temperature=0.75, max_tokens=2200)
    model = (llm.current_model() or "ollama") if text else "heuristic"
    if not text:
        text = _fallback_brief(stories, si)
    brief_date = store.save_brief(text, model=model, n_items=len(stories))
    return {"brief_date": brief_date, "model": model}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    g = StateGraph(PipelineState)
    g.add_node("fetch", node_fetch)
    g.add_node("dedupe", node_dedupe)
    g.add_node("classify", node_classify)
    g.add_node("persist", node_persist)
    g.add_node("score", node_score)
    g.add_node("brief", node_brief)
    g.add_edge(START, "fetch")
    g.add_edge("fetch", "dedupe")
    g.add_edge("dedupe", "classify")
    g.add_edge("classify", "persist")
    g.add_edge("persist", "score")
    g.add_edge("score", "brief")
    g.add_edge("brief", END)
    return g.compile()


_PIPELINE = None


def pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = build_graph()
    return _PIPELINE


def run_ingest() -> dict:
    """One full cycle. Returns final state stats."""
    final: dict[str, Any] = pipeline().invoke({
        "raw_items": [], "items": [], "errors": [], "stats": {},
        "brief": None, "brief_model": None,
    })
    return {
        "stats": final.get("stats", {}),
        "si": final.get("si", {}).get("si"),
        "brief_model": final.get("brief_model"),
        "errors": final.get("errors", []),
    }


if __name__ == "__main__":
    store.init_schema()
    print(json.dumps(run_ingest(), indent=1))
