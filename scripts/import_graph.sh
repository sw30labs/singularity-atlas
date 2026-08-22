#!/usr/bin/env bash
# Load a tarball produced by scripts/export_graph.sh into this machine's
# Neo4j volume and data/. Replaces the graph (Community load is offline and
# overwrite-only). seen.json is restored with it so ingest does not skip
# stories the new graph does not have.
#
# Usage:
#   ./scripts/import_graph.sh ~/singularity-atlas-migrate-YYYYMMDDThhmmssZ.tar.gz
#   ./scripts/import_graph.sh /path/to/dir     # dir containing neo4j.dump
#
# Env: ATLAS_NEO4J_VOLUME, ATLAS_NEO4J_CONTAINER, ATLAS_NEO4J_IMAGE,
#      ATLAS_NEO4J_PASSWORD
set -euo pipefail

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

case "${1:-}" in
  "") usage; exit 1 ;;
  -h|--help) usage; exit 0 ;;
esac

SRC="$1"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
cd "$ROOT"

VOLUME="${ATLAS_NEO4J_VOLUME:-singularity-atlas-neo4j-data}"
CONTAINER="${ATLAS_NEO4J_CONTAINER:-singularity-atlas-neo4j}"
PASSWORD="${ATLAS_NEO4J_PASSWORD:-singularity-atlas}"
IMAGE="${ATLAS_NEO4J_IMAGE:-neo4j:5-community}"
PORT="${ATLAS_PORT:-8055}"

command -v docker >/dev/null 2>&1 || {
  echo "ERROR: docker is not on PATH." >&2
  exit 1
}
docker info >/dev/null 2>&1 || {
  echo "ERROR: the Docker daemon is not reachable." >&2
  exit 1
}

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/atlas-import.XXXXXX")"
WAS_RUNNING=0
cleanup() {
  status=$?
  rm -rf "$STAGE"
  if [ "$WAS_RUNNING" = 1 ] && docker inspect "$CONTAINER" >/dev/null 2>&1; then
    if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null || echo false)" != "true" ]; then
      echo "==> Restarting $CONTAINER after failure" >&2
      docker start "$CONTAINER" >/dev/null 2>&1 || true
    fi
  fi
  exit "$status"
}
trap cleanup EXIT

if [ -d "$SRC" ]; then
  cp -R "$SRC/." "$STAGE/"
elif [ -f "$SRC" ]; then
  echo "==> Unpacking $SRC"
  tar -xzf "$SRC" -C "$STAGE"
else
  echo "ERROR: not a file or directory: $SRC" >&2
  exit 1
fi

DUMP=""
for candidate in "$STAGE/neo4j.dump" "$STAGE/dumps/neo4j.dump"; do
  [ -f "$candidate" ] && DUMP="$candidate" && break
done
if [ -z "$DUMP" ]; then
  echo "ERROR: no neo4j.dump in the archive (run scripts/export_graph.sh on the Mac)." >&2
  ls -la "$STAGE" >&2
  exit 1
fi

if [ -f "$STAGE/manifest.txt" ]; then
  echo "==> Manifest"
  cat "$STAGE/manifest.txt"
  echo
fi

if docker inspect "$CONTAINER" >/dev/null 2>&1; then
  IMAGE="$(docker inspect -f '{{.Config.Image}}' "$CONTAINER")"
  if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER")" = "true" ]; then
    WAS_RUNNING=1
  fi
fi

# A dashboard left running will keep ingesting against a graph we are about to
# replace, and it holds seen.json open in spirit (the next cycle rewrites it).
dashboard_pids() {
  local pid comm
  for pid in $(pgrep -f 'uvicorn singularity_atlas\.api:app' 2>/dev/null || true); do
    comm="$(ps -o comm= -p "$pid" 2>/dev/null || true)"
    case "${comm##*/}" in
      python | python[0-9]* | uvicorn) printf '%s\n' "$pid" ;;
    esac
  done
}
PIDS="$(dashboard_pids)"
if [ -n "$PIDS" ]; then
  echo "==> Stopping dashboard so ingest cannot race the load: $PIDS"
  # shellcheck disable=SC2086
  kill $PIDS 2>/dev/null || true
  sleep 2
fi

docker volume create "$VOLUME" >/dev/null

if [ "$WAS_RUNNING" = 1 ]; then
  echo "==> Stopping $CONTAINER (load is offline-only)"
  docker stop "$CONTAINER" >/dev/null
fi

mkdir -p "$STAGE/dumps"
cp "$DUMP" "$STAGE/dumps/neo4j.dump"

echo "==> Loading dump into $VOLUME"
docker run --rm \
  --volume "$VOLUME":/data \
  --volume "$STAGE/dumps":/dumps \
  "$IMAGE" \
  neo4j-admin database load neo4j --from-path=/dumps --overwrite-destination=true

if [ -d "$STAGE/data" ]; then
  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  if [ -d "$ROOT/data" ] && [ "$(ls -A "$ROOT/data" 2>/dev/null || true)" ]; then
    BAK="$ROOT/data.bak-before-import-$STAMP"
    echo "==> Backing up existing data/ → $BAK"
    mv "$ROOT/data" "$BAK"
  fi
  echo "==> Restoring runtime data/ (seen-set + SI history)"
  mkdir -p "$ROOT/data"
  cp -R "$STAGE/data/." "$ROOT/data/"
fi

echo "==> Starting Neo4j"
if docker inspect "$CONTAINER" >/dev/null 2>&1; then
  docker start "$CONTAINER" >/dev/null
  WAS_RUNNING=0
else
  docker compose up -d
  WAS_RUNNING=0
fi

echo "==> Waiting for Bolt"
ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" cypher-shell -u neo4j -p "$PASSWORD" \
       "RETURN 1;" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [ "$ready" -eq 1 ]; then
  echo "    Neo4j is up"
  docker exec "$CONTAINER" cypher-shell -u neo4j -p "$PASSWORD" --format plain \
    "MATCH (s:Story) RETURN coalesce(s.origin,'(none)') AS origin, count(*) AS n ORDER BY n DESC;" \
    2>/dev/null || true
else
  echo "!! Neo4j did not answer within 60s" >&2
fi

if [ "${ATLAS_IMPORT_QUIET:-0}" != 1 ]; then
  echo
  echo "Graph loaded. Start the dashboard (skip tests; seed is idempotent):"
  echo "  ./setup_and_run.sh --no-tests"
  echo "  # or: uv run uvicorn singularity_atlas.api:app --host 127.0.0.1 --port $PORT"
fi
