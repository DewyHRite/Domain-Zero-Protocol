#!/usr/bin/env bash
set -euo pipefail
# CODE-001 (Toji audit 2026-08-03, v9.12.0 Wave B1): resolve python3-first
# (PEP 394-safe) rather than invoking bare `python`. Sourced relative to
# THIS SCRIPT's own location, not cwd, so it behaves the same regardless of
# where it's invoked from -- see scripts/lib/python-probe.sh.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/python-probe.sh
. "$SCRIPT_DIR/lib/python-probe.sh"
if ! dzp_python_probe; then
    echo "brain.sh: no python3/python interpreter found on PATH" >&2
    exit 1
fi
repo="$(git rev-parse --show-toplevel)"
"$DZP_PYTHON" "$repo/.protocol-state/brain/brain.py" --repo "$repo" "$@"
