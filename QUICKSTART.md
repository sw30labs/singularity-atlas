# Quick start — install from a clone

A new machine can bring the Atlas up from this repository. No API keys, no
registration. Feeds are public.

The one-shot path:

```bash
git clone https://github.com/sw30labs/singularity-atlas.git
cd singularity-atlas
./setup_and_run.sh --sync
```

Dashboard: http://localhost:8055
Neo4j browser: http://localhost:7476 (`neo4j` / `singularity-atlas`)

`--sync` pulls the latest Innermost Loop editions from the public Substack
feed before serving. Omit it if you only want the dashboard; the daily job
will catch up once the process is running.

Flags: `--setup-only` (stop after seed + first ingest), `--no-tests`,
`--sync`, `--help`. `scripts/dev.sh` forwards to the same script.

## Prerequisites

| Tool | Required? | Why |
|---|---|---|
| git | yes | clone |
| [uv](https://docs.astral.sh/uv/) | yes | Python ≥3.12 env from `uv.lock` |
| Docker + Compose | yes, unless Neo4j already listens on Bolt | graph store |
| Ollama + a qwen3 model | no | Daily Loop briefs; heuristics if Ollama is down |

Install uv (macOS / Linux):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Python 3.12+ is required (`requires-python` in `pyproject.toml`). `uv sync`
will fetch a matching interpreter if the machine does not have one.

## What `./setup_and_run.sh` does

1. `uv sync`
2. `docker volume create singularity-atlas-neo4j-data` (the compose volume is
   `external: true` — `docker compose up` fails without this; the script
   creates it)
3. `docker compose up -d` and wait for Bolt
4. `uv run pytest` (skip with `--no-tests`)
5. `uv run python -m singularity_atlas.seed` (idempotent; a no-op if the local
   Loop corpus is absent)
6. optional Loop-feed pull (`--sync`)
7. **one feed ingest cycle** so the dashboard is not empty on first paint
8. `uvicorn` on `127.0.0.1:8055`

If Docker is missing, the script continues and expects Neo4j at
`${ATLAS_NEO4J_URI:-bolt://localhost:7689}`.

Manual equivalent:

```bash
uv sync
docker volume create singularity-atlas-neo4j-data
docker compose up -d
uv run python -m singularity_atlas.seed
uv run python -m singularity_atlas.pipeline    # one ingest cycle
uv run uvicorn singularity_atlas.api:app --host 127.0.0.1 --port 8055
```

## Feed updates are not cron

There is no crontab, launchd plist, or systemd unit. Updates live **inside
the dashboard process**, wired by APScheduler in `singularity_atlas/scheduler.py`
when uvicorn starts:

| Job | Cadence | Boot |
|---|---|---|
| Feed ingest (RSS / arXiv / HN / Launch Library / GDELT → classify → graph → SI) | every **15 min** (`INGEST_INTERVAL_MIN`) | yes — a background thread runs one cycle immediately |
| Innermost Loop archive sync | every **24 h** (`LOOP_SYNC_INTERVAL_H`) | yes — only if the last check is older than 24 h (always true on a fresh clone) |

`Ctrl+C` stops uvicorn and **stops both jobs**. A forgotten instance left
running keeps ingesting in the background and holds the port;
`setup_and_run.sh` kills a stale Atlas dashboard on restart.

Keep the process up (a terminal, tmux, or your own service wrapper) if you
want the graph to stay current. Nothing else on the machine polls the feeds.

On-demand, while the server is up:

```bash
curl -X POST http://127.0.0.1:8055/api/ingest          # one feed cycle
curl -X POST http://127.0.0.1:8055/api/archive/sync    # Loop editions now
curl -X POST http://127.0.0.1:8055/api/brief/regenerate
```

Without the server: `uv run python -m singularity_atlas.pipeline` (one ingest)
and `uv run python -m singularity_atlas.feeds` (smoke-test every feed).
`/api/feeds` and `/api/state.last_ingest` show freshness.

## What a clone does not include

These are gitignored or live outside git:

- **`data/`** — seen-set, SI history, feed health, fetched Loop issues. Starts
  empty; ingest and archive sync fill it.
- **`ref/innermost-loop/`** — the 218-edition local corpus. All-rights-reserved
  third-party content, never published. Seed is a no-op without it.
- **`ref/accelerando/`** — the local *Accelerando* copy (CC BY-NC-ND 2.5).
  Never published; read the author's free edition instead.
- **Neo4j volume** — graph is empty until seed + ingest.
- **`.venv`** — `uv sync` recreates it.

Without the local corpus, archive panels start empty. `--sync` or the daily
job pulls the latest **20** editions from the public feed into
`data/loop_issues/` and into the graph. That is enough for a working
install.

To bring the full 218-issue corpus across machines, copy the directory
separately (do not commit it):

```bash
rsync -a --exclude '.venv' --exclude '__pycache__' \
  /path/to/this/singularity-atlas/ \
  new-pc:~/singularity-atlas/
```

Then `uv run python -m singularity_atlas.seed` on the new box. Neo4j data
still has to be recreated (or dump/restore the Docker volume
`singularity-atlas-neo4j-data`). Runtime `data/` can be copied too if you
want the seen-set and SI history; otherwise ingest rebuilds them.

## Optional LLM

Default model in `singularity_atlas/config.py` is `qwen3.8:27b-mtp-bf16`.
That is a large local model. On a smaller machine pull something that fits:

```bash
ollama pull qwen3:14b
```

The resolver also accepts several qwen3 fallbacks already present in Ollama
(`qwen3:30b-a3b-instruct-2507-q4_K_M`, `qwen3:30b-a3b`, `qwen3:32b`,
`qwen3:14b`). Override with `ATLAS_MODEL` / `OLLAMA_HOST`. No usable model
→ briefs use heuristics; the rest of the dashboard still works.

## Ports and env

| Port | Service |
|---|---|
| 8055 | dashboard |
| 7476 | Neo4j HTTP |
| 7689 | Neo4j Bolt |
| 11434 | Ollama (if used) |

Overrides: `ATLAS_HOST`, `ATLAS_PORT`, `ATLAS_NEO4J_URI`,
`ATLAS_NEO4J_PASSWORD`, `ATLAS_MODEL`, `OLLAMA_HOST`. Tunables (feeds,
weights, cadence) live in `singularity_atlas/config.py`.
