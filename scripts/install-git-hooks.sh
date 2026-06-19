#!/bin/sh
# Domain Zero Protocol - Git Hook Installer (FEAT-GUARD-001, v9.7.2)
#
# Installs the DZP unified pre-commit hook (publish-branch skip + append-only
# guard + agent/protected-file guard + protocol validation). Git cannot
# auto-install hooks from a clone, so this opt-in installer is part of setup.
#
# Usage:  sh scripts/install-git-hooks.sh   [--uninstall]
set -eu

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
HOOKS_DIR=$(git rev-parse --git-path hooks 2>/dev/null || echo "$ROOT/.git/hooks")
SRC="$ROOT/scripts/git-hooks/pre-commit"
DEST="$HOOKS_DIR/pre-commit"

# Match either the new unified hook header or the legacy FEAT-REQ-001 header.
_is_dzp_hook() {
    grep -qE "Domain Zero Protocol - (Unified Pre-commit Hook|Agent / Protected-File Commit Guard)" "$1" 2>/dev/null
}

if [ "${1:-}" = "--uninstall" ]; then
    if [ -f "$DEST" ] && _is_dzp_hook "$DEST"; then
        rm -f "$DEST"
        echo "[OK] Removed DZP pre-commit hook: $DEST"
    else
        echo "[--] No DZP pre-commit hook found at: $DEST"
    fi
    exit 0
fi

if [ ! -f "$SRC" ]; then
    echo "[ERROR] Hook source not found: $SRC" >&2
    exit 1
fi

mkdir -p "$HOOKS_DIR"

if [ -f "$DEST" ] && ! _is_dzp_hook "$DEST"; then
    backup="$DEST.dzp-backup.$(date +%Y%m%d_%H%M%S)"
    cp "$DEST" "$backup"
    echo "[!] Existing pre-commit hook backed up to: $backup"
fi

cp "$SRC" "$DEST"
chmod +x "$DEST" 2>/dev/null || true
echo "[OK] Installed DZP unified pre-commit hook: $DEST"
echo "    Guards: publish-branch skip, append-only docs, protected paths,"
echo "    and protocol state validation."
echo "    Protects: protocol/, .claude/agents/, protocol.config.yaml, and other"
echo "    custom_agent_security.file_protection.immutable_paths entries."
echo "    Override a single commit with: git commit --no-verify"
