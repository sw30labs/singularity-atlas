# 0005. Heuristic-first classification and briefs; local Ollama LLM is optional, bounded and auto-resolved

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`); default model changed 2026-10-16 (`b39f85a`)

## Context

`llm.py`: "The app never hard-depends on the LLM." README: "The LLM is optional: everything degrades to heuristics when Ollama is offline."

## Decision

- **Classification:** `taxonomy.py` scores the eight vectors by weighted keyword hits (word-boundary regex, optional plural), extracts entities from a curated gazetteer (longest match wins) and geolocates a fixed list of places. "The classifier is deliberately simple and explainable."
- **LLM refinement** (`pipeline._classify_item`) only for items with no heuristic vector or salience ≥ 2.5, with a per-cycle budget of 24 calls (6 for models whose name suggests a dense/large model: `bf16`, `fp16`, `70b`, `32b`, `27b`, `235b`). The budget is only spent on a successful JSON reply. LLM entities pass a stoplist and are canonicalised back onto the gazetteer.
- **Brief:** `node_brief` asks the LLM for a 4–6 paragraph "Welcome to <date>" edition from the top 14 stories; if no LLM, `_fallback_brief` produces an extractive heuristic edition. A heuristic brief is replaced when the LLM comes back.
- **Model resolution:** preferred `ATLAS_LLM_MODEL` / `ATLAS_MODEL` / default `qwen3:8b`, then fallbacks `qwen3:30b-a3b-instruct-2507-q4_K_M`, `qwen3:30b-a3b`, `qwen3:32b`, `qwen3:14b`; `/api/tags` re-polled every 60 s so a newly pulled model is picked up without restart. All calls go to `OLLAMA_HOST` (default localhost) with `think: false`.
- Commit `b39f85a` moved the default to a "neutral" `qwen3:8b` and added an optional untracked `.env` loader (real env vars win).

## Consequences

**Positive**
- Works offline and on machines without a GPU; the UI shows which path produced the brief.
- LLM cost per cycle is capped.

**Negative**
- Keyword taxonomy and gazetteer are hand-maintained in code and will drift as names change.
- The budget heuristic is based on substrings of the model name (A-010).
- `chat_json` grabs the outermost `{…}`/`[…]` by regex, so prose with braces can produce wrong JSON (it returns None on parse errors).
- Short gazetteer keys such as `eu`, `meta`, `figure`, `atlas` can create false positives.

## Alternatives considered

None recorded. Hosted LLM APIs were implicitly rejected ("No API keys"). A remote branch `feature/openai-models` exists but was not reviewed (not on `main`).

## Evidence

- `singularity_atlas/taxonomy.py`, `singularity_atlas/llm.py`, `singularity_atlas/pipeline.py`, `singularity_atlas/config.py` (`_load_dotenv`, `OLLAMA_MODEL`)
- `tests/test_taxonomy.py`, `tests/test_llm.py`, `tests/test_pipeline.py`
- `QUICKSTART.md` § Optional LLM
- Commits `ed3300c`, `b39f85a`
