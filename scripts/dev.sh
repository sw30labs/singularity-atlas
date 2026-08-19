#!/usr/bin/env bash
# Kept for muscle memory and older docs. The canonical entry point is
# ./setup_and_run.sh at the repo root — see it for flags and env overrides.
set -euo pipefail
exec "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)/setup_and_run.sh" "$@"
