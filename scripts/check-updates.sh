#!/usr/bin/env bash
# DZP downstream update check — READ-ONLY.
# Compares THIS install's protocol_version against the canonical 'release' branch and
# reports whether an update is available + where to report issues.
#
# ONE-WAY INVARIANT: this script only READS from canonical (raw VERSION.md over HTTPS).
# It never pushes to, modifies, or otherwise writes the canonical DZP dev repo. Downstream
# installs consume releases and report issues via GitHub; they cannot modify canonical.
set -euo pipefail

CANON="https://github.com/DewyHRite/Domain-Zero-Protocol"
# HEAD resolves to the repo's DEFAULT branch (the latest published DZP-vX.Y.Z), so this
# stays correct as published version branches are added — no hard-coded branch name.
RELEASE_VERSION_RAW="https://raw.githubusercontent.com/DewyHRite/Domain-Zero-Protocol/HEAD/VERSION.md"
ISSUES="$CANON/issues"
SECURITY="$CANON/security/advisories"

REPO="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
state="$REPO/.protocol-state/project-state.json"

local_ver="$(grep -m1 -oE '"protocol_version"[[:space:]]*:[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+"' "$state" 2>/dev/null \
            | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo '?')"
canon_ver="$(curl -fsSL --max-time 15 "$RELEASE_VERSION_RAW" 2>/dev/null \
            | grep -m1 -oE 'v?[0-9]+\.[0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo '')"

echo "Canonical source : $CANON (branch: release)"
echo "Local version    : ${local_ver}"
if [ -z "$canon_ver" ]; then
  echo "Canonical version: (unreachable — check network, or the 'release' branch is not published yet)"
  echo "Status           : UNKNOWN"
else
  echo "Canonical version: ${canon_ver}"
  if [ "$local_ver" = "$canon_ver" ]; then
    echo "Status           : UP TO DATE"
  else
    echo "Status           : UPDATE AVAILABLE (local ${local_ver} -> canonical ${canon_ver})"
    echo "How to update    : pull the published 'release' branch from canonical (one-way)."
    echo "                   Do NOT hand-copy protocol files, and never push changes upstream."
  fi
fi
echo ""
echo "Report an issue  : $ISSUES"
echo "Report security  : $SECURITY"
