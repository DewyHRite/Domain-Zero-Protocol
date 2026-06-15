#!/usr/bin/env bash
set +e
repo="$(git rev-parse --show-toplevel 2>/dev/null)"
log_root="${LOCALAPPDATA:-$HOME/.local/share}/dzp-cortex"
if [ -n "$repo" ]; then
  # B6: pass $repo as a DATA argument (sys.argv[1]) rather than interpolating
  # it into the Python source string.  Interpolation breaks on paths that
  # contain apostrophes and can alter the snippet being executed.
  data_dir="$(python -c 'import sys; from pathlib import Path; repo=Path(sys.argv[1]).resolve(); sys.path.insert(0, str(repo/".protocol-state"/"brain")); from cortex import config, paths; cfg=config.load(repo); print(paths.data_dir(repo, cfg))' "$repo" 2>/dev/null)"
  if [ -n "$data_dir" ]; then
    log_root="$data_dir"
  fi
fi
mkdir -p "$log_root" 2>/dev/null
lock="$log_root/index.lock"
# B7: atomic lock acquisition via noclobber redirection (POSIX).
# Eliminates the TOCTOU window of the prior [ -e "$lock" ] + truncate sequence:
# the shell raises an error if the file already exists when O_EXCL is implied
# by noclobber, making test+create a single atomic operation.
# lock_acquired tracks ownership so the EXIT trap only removes a lock that THIS
# invocation created (ownership-safe cleanup).
lock_acquired=0
if (set -C; : >"$lock") 2>/dev/null; then
  lock_acquired=1
else
  printf '%s %s\n' "$(date -Iseconds 2>/dev/null)" "index hook skipped; lock exists (concurrent run)" >>"$log_root/index.log" 2>/dev/null
  exit 0
fi
trap '[ "$lock_acquired" = "1" ] && rm -f "$lock" 2>/dev/null' EXIT
if [ -n "$repo" ]; then
  if command -v timeout >/dev/null 2>&1; then
    timeout 30 python "$repo/.protocol-state/brain/brain.py" --repo "$repo" index --incremental >/dev/null 2>>"$log_root/index.log"
  else
    python "$repo/.protocol-state/brain/brain.py" --repo "$repo" index --incremental >/dev/null 2>>"$log_root/index.log"
  fi
fi
exit 0
