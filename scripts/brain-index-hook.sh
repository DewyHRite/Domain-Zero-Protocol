#!/usr/bin/env bash
set +e
repo="$(git rev-parse --show-toplevel 2>/dev/null)"
log_root="${LOCALAPPDATA:-$HOME/.local/share}/dzp-cortex"
if [ -n "$repo" ]; then
  data_dir="$(python -c "import sys; from pathlib import Path; repo=Path(r'''$repo''').resolve(); sys.path.insert(0, str(repo/'.protocol-state'/'brain')); from cortex import config, paths; cfg=config.load(repo); print(paths.data_dir(repo, cfg))" 2>/dev/null)"
  if [ -n "$data_dir" ]; then
    log_root="$data_dir"
  fi
fi
mkdir -p "$log_root" 2>/dev/null
lock="$log_root/index.lock"
if [ -e "$lock" ]; then
  printf '%s %s\n' "$(date -Iseconds 2>/dev/null)" "index hook skipped; lock exists" >>"$log_root/index.log" 2>/dev/null
  exit 0
fi
: >"$lock" 2>/dev/null || exit 0
trap 'rm -f "$lock" 2>/dev/null' EXIT
if [ -n "$repo" ]; then
  if command -v timeout >/dev/null 2>&1; then
    timeout 30 python "$repo/.protocol-state/brain/brain.py" --repo "$repo" index --incremental >/dev/null 2>>"$log_root/index.log"
  else
    python "$repo/.protocol-state/brain/brain.py" --repo "$repo" index --incremental >/dev/null 2>>"$log_root/index.log"
  fi
fi
exit 0
