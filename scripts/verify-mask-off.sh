#!/usr/bin/env bash
# Mask-Off Mode Verification Script
# Version: 1.0
# Purpose: Scan for prohibited themed vocabulary when mask_mode.enabled=false

set -euo pipefail

CONFIG_PATH="${1:-protocol.config.yaml}"
STRICT_MODE=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict) STRICT_MODE=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        *) shift ;;
    esac
done

echo "🎭 Domain Zero Protocol - Mask-Off Verification Script v1.0"
echo "======================================================================"
echo ""

# Check if config exists
if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "[ERROR] Configuration file not found: $CONFIG_PATH"
    exit 1
fi

# Read config to check mask mode setting
MASK_ENABLED=$(grep -A 2 "^mask_mode:" "$CONFIG_PATH" | grep "enabled:" | grep -q "true" && echo "true" || echo "false")
STRICT_PROF=$(grep "strict_professional:" "$CONFIG_PATH" | grep -q "true" && echo "true" || echo "false")

echo "[INFO] Mask Mode Status:"
echo "  - mask_mode.enabled: $MASK_ENABLED"
echo "  - strict_professional: $STRICT_PROF"
echo ""

if [[ "$MASK_ENABLED" == "true" ]]; then
    echo "[SKIP] Mask mode is ENABLED (JJK theme active)"
    echo "       Verification only runs when mask_mode.enabled=false"
    exit 0
fi

echo "[INFO] Mask mode is DISABLED - checking for prohibited themed vocabulary..."
echo ""

# Define banned terms (should not appear in mask-off mode)
BANNED_TERMS=(
    "Domain Zero"
    "Domain Expansion"
    "The Weight"
    "Trigger 19"
    "🛠️"
    "🛡️"
    "🌀"
    "🎯"
)

# Files to scan (agent output, state files, etc.)
FILES_TO_SCAN=(
    ".protocol-state/dev-notes.md"
    ".protocol-state/security-review.md"
    ".protocol-state/trigger-19.md"
)

VIOLATIONS=()
FILES_SCANNED=0

for file in "${FILES_TO_SCAN[@]}"; do
    if [[ ! -f "$file" ]]; then
        [[ "$VERBOSE" == "true" ]] && echo "[SKIP] File not found: $file"
        continue
    fi

    ((FILES_SCANNED++))

    for term in "${BANNED_TERMS[@]}"; do
        if grep -Fq "$term" "$file"; then
            VIOLATIONS+=("$file:$term")
            [[ "$VERBOSE" == "true" ]] && echo "[VIOLATION] Found '$term' in $file"
        fi
    done
done

echo "Files scanned: $FILES_SCANNED"
echo ""

if [[ ${#VIOLATIONS[@]} -eq 0 ]]; then
    echo "✅ [PASS] No prohibited themed vocabulary detected"
    echo ""
    echo "Mask-off mode verification successful!"
    exit 0
else
    echo "❌ [FAIL] Found ${#VIOLATIONS[@]} prohibited term(s) in mask-off mode:"
    echo ""

    for violation in "${VIOLATIONS[@]}"; do
        IFS=':' read -r file term <<< "$violation"
        echo "  File: $file"
        echo "    - Prohibited term: $term"
    done

    echo ""
    echo "[ACTION] Fix these violations:"
    echo "  1. Ensure mask_mode.enabled=false in protocol.config.yaml"
    echo "  2. Clear agent session/context and restart"
    echo "  3. Reseed AI memory with professional mode template (see MASK_MODE.md)"
    echo "  4. Re-run this script to verify"
    echo ""

    if [[ "$STRICT_PROF" == "true" ]]; then
        echo "[STRICT MODE] strict_professional=true requires ZERO themed vocabulary"
        exit 1
    else
        echo "[WARN] Consider enabling strict_professional=true for compliance"
        exit 1
    fi
fi
