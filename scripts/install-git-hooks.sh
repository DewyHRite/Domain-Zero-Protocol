#!/bin/sh
# Domain Zero Protocol - Git Hook Installer (FEAT-REQ-001, v9.3.0)
#
# Installs the DZP agent/protected-file protection pre-commit hook. Git cannot
# auto-install hooks from a clone, so this opt-in installer is part of setup.
#
# Usage:  sh scripts/install-git-hooks.sh   [--uninstall]
set -eu

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
HOOKS_DIR=$(git rev-parse --git-path hooks 2>/dev/null || echo "$ROOT/.git/hooks")
SRC="$ROOT/scripts/git-hooks/pre-commit"
DEST="$HOOKS_DIR/pre-commit"

if [ "${1:-}" = "--uninstall" ]; then
    if [ -f "$DEST" ] && grep -q "Domain Zero Protocol - Agent / Protected-File Commit Guard" "$DEST" 2>/dev/null; then
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

if [ -f "$DEST" ] && ! grep -q "Domain Zero Protocol - Agent / Protected-File Commit Guard" "$DEST" 2>/dev/null; then
    backup="$DEST.dzp-backup.$(date +%Y%m%d_%H%M%S)"
    cp "$DEST" "$backup"
    echo "[!] Existing pre-commit hook backed up to: $backup"
fi

cp "$SRC" "$DEST"
chmod +x "$DEST" 2>/dev/null || true
echo "[OK] Installed DZP pre-commit hook: $DEST"
echo "    Protects: protocol/, .claude/agents/, protocol.config.yaml, and other"
echo "    custom_agent_security.file_protection.immutable_paths entries."
echo "    Override a single commit with: git commit --no-verify"
