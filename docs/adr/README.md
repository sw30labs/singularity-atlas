# Architecture Decision Records

These are **retrospective** ADRs, inferred on 2026-10-28 from the code and git history of `main` at `c2e7d71f1ac2b5bc092c9082a2565efc45fa9ca3`. They record decisions already visible in the repository. Where the reason for a decision isn't written down, it isn't invented here; it is logged as an assumption in [`../assumptions.md`](../assumptions.md) for the author to confirm or correct.

Format: Title, Status, Context, Decision, Consequences (positive/negative), Alternatives considered, Evidence.

| # | Decision | Status |
|---|---|---|
| [0001](0001-local-first-single-process-dashboard.md) | Local-first, single-process FastAPI + zero-build JS dashboard on 127.0.0.1, no auth | Accepted (retrospective) |
| [0002](0002-neo4j-graph-store-plus-local-json-state.md) | Neo4j graph store plus small JSON/JSONL state files | Accepted (retrospective) |
| [0003](0003-langgraph-linear-ingest-pipeline.md) | Linear LangGraph ingest pipeline; errors collected, feeds isolated | Accepted (retrospective) |
| [0004](0004-in-process-apscheduler-not-cron.md) | In-process APScheduler instead of cron/launchd/systemd | Accepted (retrospective) |
| [0005](0005-heuristic-first-classification-optional-local-llm.md) | Heuristic-first classification and briefs; optional, bounded local Ollama LLM | Accepted (retrospective) |
| [0006](0006-transparent-heuristic-singularity-index.md) | Transparent, bounded heuristic Singularity Index | Accepted (retrospective) |
| [0007](0007-public-no-auth-feeds-only.md) | Public, no-auth data sources only | Accepted (retrospective) |
| [0008](0008-third-party-content-kept-out-of-repo.md) | Third-party works kept out of the repo; Apache-2.0 scoped to original code | Accepted (retrospective) |
| [0009](0009-loop-sync-from-official-substack-feed.md) | Loop Archive kept current from the official Substack feed | Accepted (retrospective) |
| [0010](0010-public-site-via-one-way-publish-to-separate-repo.md) | Public site: GitHub Pages `docs/` replaced by one-way publish to a separate Cloudflare Pages repo | Accepted (retrospective); supersedes the `docs/` Pages snapshot |
| [0011](0011-public-output-guardrails.md) | Guardrails on public output (allowlist, leak scan, neutral errors, no model names) | Accepted (retrospective) |
| [0012](0012-static-live-atlas-with-pinned-vendored-assets.md) | Static live Atlas via fetch shim and sha256-pinned vendored assets | Accepted (retrospective) |
| [0013](0013-uv-and-setup-and-run-as-canonical-entry.md) | uv-managed project; `setup_and_run.sh` as canonical entry point | Accepted (retrospective) |
| [0014](0014-offline-unit-tests-optional-integration.md) | Offline unit tests; Neo4j/corpus tests skip when unavailable | Accepted (retrospective) |

## Scope and limits of this review

- Read in full: all Python modules, tests, scripts, `web/` sources, README, QUICKSTART, NOTICE, LICENSE header, compose and project files, and the full `git log` (68 commits; the 42+ daily snapshot commits were reviewed by `--stat` only).
- Not read line by line: `uv.lock`, `web/vendor/globe.gl.min.js` (minified, checked against its pinned hash only by the build script), generated `docs/index.html` / `docs/snapshot.json` / `docs/architecture.html` (structure only), and binary images.
- Remote branches `feature/openai-models` and `moonshots-archive` were not reviewed; these ADRs describe `main` only.

New decisions should be added as new numbered files; superseded ADRs should be marked rather than deleted.
