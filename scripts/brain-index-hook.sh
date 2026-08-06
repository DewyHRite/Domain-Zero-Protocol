#!/usr/bin/env bash
set +e
# CODE-001 (Toji audit 2026-08-03, v9.12.0 Wave B1): resolve python3-first
# (PEP 394-safe) rather than bare `python`. This hook is fail-soft by design
# (never blocks session end -- see the header comment at the end of this
# file), so an absent interpreter degrades to the SAME "skip, don't block"
# behavior it already had: DZP_PYTHON stays empty, the python-dependent
# steps below are skipped rather than attempted with an empty command.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/python-probe.sh
if [ -f "$SCRIPT_DIR/lib/python-probe.sh" ]; then
  . "$SCRIPT_DIR/lib/python-probe.sh"
  dzp_python_probe
fi
repo="$(git rev-parse --show-toplevel 2>/dev/null)"
log_root="${LOCALAPPDATA:-$HOME/.local/share}/dzp-cortex"
if [ -n "$repo" ] && [ -n "${DZP_PYTHON:-}" ]; then
  # B6: pass $repo as a DATA argument (sys.argv[1]) rather than interpolating
  # it into the Python source string.  Interpolation breaks on paths that
  # contain apostrophes and can alter the snippet being executed.
  data_dir="$("$DZP_PYTHON" -c 'import sys; from pathlib import Path; repo=Path(sys.argv[1]).resolve(); sys.path.insert(0, str(repo/".protocol-state"/"brain")); from cortex import config, paths; cfg=config.load(repo); print(paths.data_dir(repo, cfg))' "$repo" 2>/dev/null)"
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
# Staleness threshold: a lock older than this is treated as orphaned.
# 600 s is well above any real index run (timeout cap: 30 s).
STALE_SECONDS=600
lock_acquired=0
if (set -C; : >"$lock") 2>/dev/null; then
  lock_acquired=1
else
  # Lock already exists — check if it is stale (orphaned from a killed hook).
  # Portable mtime: try GNU stat (-c %Y), then BSD/macOS stat (-f %m).
  lock_mtime=""
  if lock_mtime=$(stat -c %Y "$lock" 2>/dev/null); then
    :
  elif lock_mtime=$(stat -f %m "$lock" 2>/dev/null); then
    :
  fi
  if [ -n "$lock_mtime" ]; then
    now_ts=$(date +%s 2>/dev/null)
    if [ -n "$now_ts" ] && [ "$((now_ts - lock_mtime))" -gt "$STALE_SECONDS" ] 2>/dev/null; then
      printf '%s %s\n' "$(date -Iseconds 2>/dev/null)" "index hook: reaping stale lock (age > ${STALE_SECONDS}s); retrying acquire" >>"$log_root/index.log" 2>/dev/null
      rm -f "$lock" 2>/dev/null
      # Retry acquire once after reaping the stale lock.
      if (set -C; : >"$lock") 2>/dev/null; then
        lock_acquired=1
      else
        printf '%s %s\n' "$(date -Iseconds 2>/dev/null)" "index hook skipped; lock re-acquired by concurrent run after reap" >>"$log_root/index.log" 2>/dev/null
        exit 0
      fi
    else
      printf '%s %s\n' "$(date -Iseconds 2>/dev/null)" "index hook skipped; lock exists (concurrent run)" >>"$log_root/index.log" 2>/dev/null
      exit 0
    fi
  else
    # Cannot determine lock age; fall back to current skip behavior.
    printf '%s %s\n' "$(date -Iseconds 2>/dev/null)" "index hook skipped; lock exists (concurrent run)" >>"$log_root/index.log" 2>/dev/null
    exit 0
  fi
fi
trap '[ "$lock_acquired" = "1" ] && rm -f "$lock" 2>/dev/null' EXIT
if [ -n "$repo" ] && [ -n "${DZP_PYTHON:-}" ]; then
  if command -v timeout >/dev/null 2>&1; then
    timeout 30 "$DZP_PYTHON" "$repo/.protocol-state/brain/brain.py" --repo "$repo" index --incremental >/dev/null 2>>"$log_root/index.log"
  else
    "$DZP_PYTHON" "$repo/.protocol-state/brain/brain.py" --repo "$repo" index --incremental >/dev/null 2>>"$log_root/index.log"
  fi
elif [ -n "$repo" ]; then
  printf '%s %s\n' "$(date -Iseconds 2>/dev/null)" "index hook skipped; no python3/python interpreter found on PATH" >>"$log_root/index.log" 2>/dev/null
fi
exit 0
