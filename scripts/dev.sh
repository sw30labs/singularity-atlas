#!/usr/bin/env bash
# The Singularity Atlas — one-command dev start: Neo4j up, archive seeded, server live.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> uv sync"
uv sync

if docker info >/dev/null 2>&1; then
  echo "==> neo4j (singularity-atlas-neo4j, http :7476 / bolt :7689)"
  docker volume create singularity-atlas-neo4j-data >/dev/null
  docker compose up -d
  echo "==> waiting for neo4j"
  for i in $(seq 1 30); do
    if uv run python -c "from singularity_atlas import store; exit(0 if store.ping() else 1)" 2>/dev/null; then
      break
    fi
    sleep 2
  done
else
  echo "!! docker not available — expecting Neo4j at ${ATLAS_NEO4J_URI:-bolt://localhost:7689}"
fi

echo "==> seeding the Loop archive (idempotent)"
uv run python -m singularity_atlas.seed

echo "==> serving  →  http://localhost:${ATLAS_PORT:-8055}"
exec uv run uvicorn singularity_atlas.api:app --host "${ATLAS_HOST:-127.0.0.1}" --port "${ATLAS_PORT:-8055}"
