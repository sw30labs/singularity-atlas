# 0011. Guardrails on everything that leaves the machine: allowlist, leak scan, neutral errors, no model names, no corpus

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-10-16 (`15d73c6`, `5aa01ee`, `45179e9`, `274695c`)

## Context

The public site is built from a local machine that also holds the private corpus, local model names, filesystem paths and credentials.

## Decision

- **Neutral errors:** public pages show only "feed unavailable"-style text; raw exceptions go to the local log (`public_feed_error`, `15d73c6`).
- **No local model names:** `public_model()` maps any non-heuristic model to "local LLM"; `274695c` drops the `llm` block from the public snapshot.
- **No corpus:** the footer states the snapshot "does not ship the Innermost Loop corpus or `ref/`"; the static shim sends archive search to the newsletter's own search instead of baking text.
- **Allowlist:** the build dir may only contain `board.png index.html snapshot.json live`; the live build has a size-capped file allowlist (`ALLOWED_FILES`); the final site tree is checked against a strict path regex.
- **Leak scan** (`LEAK_RE`) over every shipped text file: `$HOME`, `/Users/<name>/`, the local hostname, corpus file names, private-key headers, GitHub tokens, `sk-` keys, `NEO4J_PASSWORD`, `neo4j://`, `bolt://`, `qwen…:` model tags, Google Fonts hosts. Any hit aborts.
- **Headers:** `_headers` sets a strict CSP (self + Cloudflare Insights), `frame-ancestors 'none'`, immutable caching for versioned assets.

## Consequences

**Positive**
- Defence in depth: a mistake in one exporter is caught by the scan before push.
- Public output is reproducible from the same inputs.

**Negative**
- The leak regex hard-codes a machine-specific hostname and author-specific paths; it is not portable to another publisher without edits.
- Regex scanning can miss encodings it doesn't list, and can block legitimate text that happens to match (e.g. a story mentioning a `qwen3:` tag would fail the publish).
- The guardrails live in a shell script with no automated tests.

## Alternatives considered

None recorded.

## Evidence

- `scripts/export_public_snapshot.py` (`public_feed_error`, `public_model`, footer)
- `scripts/publish_public_site.sh` (`ALLOWED`, `LEAK_RE`, `ALLOWED_FILES`, path regex, `_headers`)
- `web/static-shim.js` (`/api/archive/search` case)
- Commits `15d73c6`, `5aa01ee`, `45179e9`, `274695c`
