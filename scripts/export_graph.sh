#!/usr/bin/env bash
# Dump the Singularity Atlas Neo4j graph + runtime data/ so another machine
# can load the same dashboard state.
#
# Run this on the Mac that has the populated graph (Docker Desktop must be up).
# Neo4j Community cannot dump while the database is open, so the container is
# stopped for the dump and started again afterward — even if the dump fails.
#
# Usage:
#   ./scripts/export_graph.sh                  # tarball on ~/Desktop/singularity-atlas-export
#   ./scripts/export_graph.sh /path/to/outdir
#   ATLAS_EXPORT_DIR=~/Desktop ./scripts/export_graph.sh
#
# Copy the tarball to the other machine, then:
#   ./scripts/import_graph.sh singularity-atlas-migrate-*.tar.gz
#
# Env: ATLAS_NEO4J_VOLUME, ATLAS_NEO4J_CONTAINER, ATLAS_NEO4J_IMAGE,
#      ATLAS_NEO4J_PASSWORD, ATLAS_EXPORT_DIR
set -euo pipefail

usage() { sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; }

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
esac

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [ -f "$SCRIPT_DIR/../docker-compose.yml" ]; then
  ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
else
  ROOT="${ATLAS_ROOT:-$PWD}"
fi

VOLUME="${ATLAS_NEO4J_VOLUME:-singularity-atlas-neo4j-data}"
CONTAINER="${ATLAS_NEO4J_CONTAINER:-singularity-atlas-neo4j}"
PASSWORD="${ATLAS_NEO4J_PASSWORD:-singularity-atlas}"
IMAGE="${ATLAS_NEO4J_IMAGE:-neo4j:5-community}"

if [ -n "${1:-}" ]; then
  OUTDIR="$1"
elif [ -n "${ATLAS_EXPORT_DIR:-}" ]; then
  OUTDIR="$ATLAS_EXPORT_DIR"
elif [ -d "$HOME/Desktop" ]; then
  OUTDIR="$HOME/Desktop/singularity-atlas-export"
else
  OUTDIR="$ROOT/atlas-export"
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$OUTDIR/singularity-atlas-migrate-$STAMP.tar.gz"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/atlas-export.XXXXXX")"
WAS_RUNNING=0

command -v docker >/dev/null 2>&1 || {
  echo "ERROR: docker is not on PATH. On a Mac, start Docker Desktop first." >&2
  exit 1
}
docker info >/dev/null 2>&1 || {
  echo "ERROR: the Docker daemon is not reachable. Start Docker Desktop and retry." >&2
  exit 1
}

if ! docker volume inspect "$VOLUME" >/dev/null 2>&1; then
  echo "ERROR: Docker volume '$VOLUME' not found. The graph lives there, not in the repo." >&2
  echo "Volumes Docker knows about:" >&2
  docker volume ls >&2
  exit 1
fi

if docker inspect "$CONTAINER" >/dev/null 2>&1; then
  IMAGE="$(docker inspect -f '{{.Config.Image}}' "$CONTAINER")"
  if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER")" = "true" ]; then
    WAS_RUNNING=1
  fi
fi

cleanup() {
  status=$?
  if [ "$WAS_RUNNING" = 1 ]; then
    echo "==> Restarting $CONTAINER"
    docker start "$CONTAINER" >/dev/null 2>&1 || true
  fi
  rm -rf "$STAGE"
  exit "$status"
}
trap cleanup EXIT

mkdir -p "$OUTDIR" "$STAGE/data"

# Snapshot counts while Bolt is still up — the dump itself is offline.
if [ "$WAS_RUNNING" = 1 ]; then
  echo "==> Graph stats (before dump)"
  docker exec "$CONTAINER" cypher-shell -u neo4j -p "$PASSWORD" --format plain \
    "MATCH (s:Story) RETURN coalesce(s.origin,'(none)') AS origin, count(*) AS n ORDER BY n DESC;" \
    2>/dev/null | tee "$STAGE/graph-stats.txt" || echo "(cypher-shell unavailable — continuing)"
fi

if [ "$WAS_RUNNING" = 1 ]; then
  echo "==> Stopping $CONTAINER (required: Community dump is offline-only)"
  docker stop "$CONTAINER" >/dev/null
fi

echo "==> Dumping $VOLUME via $IMAGE"
mkdir -p "$STAGE/dumps"
# Bind-mount the staging dumps dir; chown so the Mac user can tar it
# (the neo4j image writes files as uid 7474).
docker run --rm \
  --volume "$VOLUME":/data \
  --volume "$STAGE/dumps":/dumps \
  "$IMAGE" \
  bash -c "neo4j-admin database dump neo4j --to-path=/dumps --overwrite-destination=true && chown $(id -u):$(id -g) /dumps/neo4j.dump"

if [ ! -f "$STAGE/dumps/neo4j.dump" ]; then
  echo "ERROR: dump finished but $STAGE/dumps/neo4j.dump is missing" >&2
  exit 1
fi
mv "$STAGE/dumps/neo4j.dump" "$STAGE/neo4j.dump"

if [ -d "$ROOT/data" ]; then
  echo "==> Copying runtime data/ (seen-set, SI history, Loop fetches)"
  # seen.json and the graph must travel together; copying one without the other
  # makes the next ingest skip stories the new graph does not have.
  cp -R "$ROOT/data/." "$STAGE/data/"
  find "$STAGE/data" -name '*.bak*' -delete 2>/dev/null || true
else
  echo "!! no $ROOT/data — tarball will be graph-only" >&2
  mkdir -p "$STAGE/data"
fi

{
  echo "project: singularity-atlas"
  echo "created_utc: $STAMP"
  echo "source_host: $(hostname)"
  echo "volume: $VOLUME"
  echo "image: $IMAGE"
  echo "dump: neo4j.dump"
  if command -v shasum >/dev/null 2>&1; then
    echo "sha256: $(shasum -a 256 "$STAGE/neo4j.dump" | awk '{print $1}')"
  elif command -v sha256sum >/dev/null 2>&1; then
    echo "sha256: $(sha256sum "$STAGE/neo4j.dump" | awk '{print $1}')"
  fi
  echo "bytes: $(wc -c < "$STAGE/neo4j.dump" | tr -d ' ')"
} > "$STAGE/manifest.txt"

echo "==> Packing $ARCHIVE"
# COPYFILE_DISABLE: macOS otherwise stuffs ._* AppleDouble files into the tar.
TAR_ITEMS="manifest.txt neo4j.dump data"
[ -f "$STAGE/graph-stats.txt" ] && TAR_ITEMS="$TAR_ITEMS graph-stats.txt"
# shellcheck disable=SC2086
COPYFILE_DISABLE=1 tar -czf "$ARCHIVE" -C "$STAGE" $TAR_ITEMS

echo
echo "Export ready:"
echo "  $ARCHIVE"
echo "  $(wc -c < "$ARCHIVE" | tr -d ' ') bytes"
echo
echo "On this Mac, copy it over (fix the host/path):"
echo "  scp \"$ARCHIVE\" spark:~/Desktop/code/singularity-atlas/"
echo
echo "On the Spark, from the atlas repo:"
echo "  ./scripts/import_graph.sh \"$ARCHIVE\""
