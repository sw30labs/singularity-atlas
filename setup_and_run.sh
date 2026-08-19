#!/usr/bin/env bash
# The Singularity Atlas — one-shot setup + run: dependencies, Neo4j, the Loop
# Archive seed, one feed ingest, then the dashboard.
#
# Usage:
#   ./setup_and_run.sh                # sync deps, Neo4j up, seed, ingest, test, serve
#   ./setup_and_run.sh --setup-only   # everything except serving
#   ./setup_and_run.sh --no-tests     # skip the suite (faster restarts)
#   ./setup_and_run.sh --sync         # pull new Loop editions now, then ingest + serve
#   ./setup_and_run.sh --help
#
# Env overrides: ATLAS_HOST, ATLAS_PORT, ATLAS_NEO4J_URI, ATLAS_NEO4J_PASSWORD,
# ATLAS_MODEL, OLLAMA_HOST (see singularity_atlas/config.py).
#
# This project is uv-native and ships a lockfile, so setup is `uv sync` rather
# than the venv+pip bootstrap used by the non-uv projects in this repo family.
set -euo pipefail

cd "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

HOST="${ATLAS_HOST:-127.0.0.1}"
PORT="${ATLAS_PORT:-8055}"
SETUP_ONLY=0
RUN_TESTS=1
SYNC_NOW=0

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

while (($#)); do
  case "$1" in
    --setup-only) SETUP_ONLY=1 ;;
    --no-tests)   RUN_TESTS=0 ;;
    --sync)       SYNC_NOW=1 ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "ERROR: unknown option '$1' (try --help)" >&2; exit 1 ;;
  esac
  shift
done

command -v uv >/dev/null 2>&1 || {
  echo "ERROR: uv is not on PATH. Install it: https://docs.astral.sh/uv/" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# A dashboard left over from an earlier run keeps its scheduler alive: it goes
# on ingesting every 15 minutes and writing to data/, and it holds the port —
# which makes a fresh start look like a hang. Clear ours, refuse to fight
# anyone else's. Only processes whose executable is python count, so a shell or
# editor whose command line merely mentions the module is never a kill target.
# ---------------------------------------------------------------------------
dashboard_pids() {
  local pid comm
  for pid in $(pgrep -f 'uvicorn singularity_atlas\.api:app' 2>/dev/null || true); do
    [ "$pid" = "$$" ] && continue
    comm="$(ps -o comm= -p "$pid" 2>/dev/null || true)"
    case "${comm##*/}" in
      python | python[0-9]* | uvicorn) printf '%s\n' "$pid" ;;
    esac
  done
}

stop_stale_dashboards() {
  local pids
  pids="$(dashboard_pids)"
  if [ -n "$pids" ]; then
    echo "==> Stopping stale dashboard process(es): $(echo "$pids" | tr '\n' ' ')"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 2
    pids="$(dashboard_pids)"
    if [ -n "$pids" ]; then
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      sleep 1
    fi
  fi
  if command -v lsof >/dev/null 2>&1 &&
     lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERROR: port $PORT is held by a process that is not an Atlas dashboard:" >&2
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2
    echo "Stop it, or set ATLAS_PORT to a free port." >&2
    exit 1
  fi
}

echo "==> uv sync"
uv sync

if docker info >/dev/null 2>&1; then
  echo "==> Neo4j (singularity-atlas-neo4j, http :7476 / bolt :7689)"
  # The compose volume is declared external, so it must exist before `up`.
  docker volume create singularity-atlas-neo4j-data >/dev/null
  docker compose up -d
  echo "==> Waiting for Neo4j"
  ready=0
  for _ in $(seq 1 30); do
    if uv run python -c \
       "from singularity_atlas import store; exit(0 if store.ping() else 1)" \
       2>/dev/null; then
      ready=1
      break
    fi
    sleep 2
  done
  if [ "$ready" -eq 1 ]; then
    echo "    Neo4j is up"
  else
    echo "!! Neo4j did not answer within 60s — continuing; the graph will be empty" >&2
  fi
else
  echo "!! docker not available — expecting Neo4j at ${ATLAS_NEO4J_URI:-bolt://localhost:7689}"
fi

if [ "$RUN_TESTS" -eq 1 ]; then
  echo "==> Running test suite"
  uv run pytest
fi

echo "==> Seeding the Loop Archive (idempotent)"
uv run python -m singularity_atlas.seed

if [ "$SYNC_NOW" -eq 1 ]; then
  echo "==> Pulling new Innermost Loop editions"
  uv run python -c "
from singularity_atlas import loop_sync, store
r = loop_sync.sync_and_persist(store)
print(f\"    new={r['new']} persisted={r['persisted']} latest={r.get('latest')} error={r['error']}\")
"
fi

# One cycle before bind so the first page load is not an empty graph. Later
# cycles are APScheduler jobs inside uvicorn (every 15 min) — not cron.
echo "==> First feed ingest (one cycle)"
uv run python -m singularity_atlas.pipeline

if [ "$SETUP_ONLY" -eq 1 ]; then
  echo "==> Setup complete (--setup-only); not starting the server"
  exit 0
fi

stop_stale_dashboards

echo "==> Serving  →  http://${HOST}:${PORT}   (Ctrl+C to stop)"
exec uv run uvicorn singularity_atlas.api:app --host "$HOST" --port "$PORT"
