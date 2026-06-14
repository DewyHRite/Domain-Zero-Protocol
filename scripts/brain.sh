#!/usr/bin/env bash
set -euo pipefail
repo="$(git rev-parse --show-toplevel)"
python "$repo/.protocol-state/brain/brain.py" --repo "$repo" "$@"
