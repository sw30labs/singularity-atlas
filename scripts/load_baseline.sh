#!/usr/bin/env bash
# Load the committed graph snapshot in baseline/ into Neo4j and data/.
# Fresh clones start from this snapshot instead of an empty graph.
#
# The snapshot is an unpacked neo4j.dump (plus JSON under baseline/data/),
# not a tarball: GitHub allows .tar.gz, but the 100 MB file cap and some
# org push rules make a ~445 KB dump the safer in-repo form. A local
# migrate tarball in baseline/ is still accepted if the dump is absent.
#
# Usage:
#   ./scripts/load_baseline.sh           # load only if the graph is empty
#   ./scripts/load_baseline.sh --force   # replace the current graph
#   ./scripts/load_baseline.sh PATH      # dump dir or migrate .tar.gz
#
# Env: ATLAS_NEO4J_VOLUME, ATLAS_NEO4J_CONTAINER, ATLAS_NEO4J_PASSWORD
set -euo pipefail

usage() { awk '/^#($| )/{sub(/^# ?/,""); print} /^set -euo/{exit}' "$0"; }

FORCE=0
SRC=""
while (($#)); do
  case "$1" in
    -h|--help)  usage; exit 0 ;;
    --force)    FORCE=1 ;;
    -*)         echo "ERROR: unknown option '$1' (try --help)" >&2; exit 1 ;;
    *)          SRC="$1" ;;
  esac
  shift
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
cd "$ROOT"

VOLUME="${ATLAS_NEO4J_VOLUME:-singularity-atlas-neo4j-data}"
CONTAINER="${ATLAS_NEO4J_CONTAINER:-singularity-atlas-neo4j}"
PASSWORD="${ATLAS_NEO4J_PASSWORD:-singularity-atlas}"

resolve_src() {
  if [ -n "$SRC" ]; then
    printf '%s\n' "$SRC"
    return
  fi
  if [ -f "$ROOT/baseline/neo4j.dump" ]; then
    printf '%s\n' "$ROOT/baseline"
    return
  fi
  # fallback: a migrate tarball sitting in baseline/ (gitignored)
  local tarball
  tarball="$(ls -1t "$ROOT"/baseline/singularity-atlas-migrate-*.tar.gz 2>/dev/null | head -1 || true)"
  if [ -n "$tarball" ]; then
    printf '%s\n' "$tarball"
    return
  fi
  return 1
}

if ! SRC="$(resolve_src)"; then
  echo "==> No graph baseline under $ROOT/baseline — skipping (empty graph)"
  exit 0
fi

if [ ! -e "$SRC" ]; then
  echo "ERROR: baseline path does not exist: $SRC" >&2
  exit 1
fi

verify_dump_checksum() {
  local dump="$1" manifest="$2" expected actual
  [ -f "$manifest" ] || return 0
  expected="$(awk -F': ' '/^sha256:/{print $2; exit}' "$manifest")"
  [ -n "$expected" ] || return 0
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$dump" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$dump" | awk '{print $1}')"
  else
    return 0
  fi
  if [ "$actual" != "$expected" ]; then
    echo "ERROR: neo4j.dump sha256 mismatch (expected $expected, got $actual)" >&2
    exit 1
  fi
}

if [ -d "$SRC" ] && [ -f "$SRC/neo4j.dump" ]; then
  verify_dump_checksum "$SRC/neo4j.dump" "$SRC/manifest.txt"
fi

story_count() {
  docker exec "$CONTAINER" cypher-shell -u neo4j -p "$PASSWORD" --format plain \
    "MATCH (s:Story) RETURN count(s) AS n;" 2>/dev/null \
    | awk 'NF && $1 != "n" { gsub(/"/, ""); print $1; exit }'
}

container_running() {
  docker inspect "$CONTAINER" >/dev/null 2>&1 \
    && [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null || echo false)" = "true" ]
}

if [ "$FORCE" != 1 ]; then
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "!! docker not available — cannot load the graph baseline" >&2
    exit 1
  fi
  if ! container_running; then
    echo "ERROR: Neo4j is not running. Start it, or pass --force to load the volume offline." >&2
    exit 1
  fi
  n="$(story_count || true)"
  if [ -z "$n" ]; then
    echo "ERROR: could not count stories in Neo4j (pass --force to load anyway)" >&2
    exit 1
  fi
  if [ "$n" -gt 0 ]; then
    echo "==> Graph already has $n stories — leaving it alone (pass --force to replace)"
    exit 0
  fi
  echo "==> Graph is empty — loading baseline from $SRC"
else
  echo "==> Loading baseline from $SRC (--force, replaces the graph)"
fi

exec "$SCRIPT_DIR/import_graph.sh" "$SRC"
