#!/usr/bin/env bash
# Domain Zero Protocol - Instruction File Updater (Bash)
#
# Purpose: Safely append Domain Zero Protocol pointers to existing AI instruction files
# Safety: Dry-run by default, only modifies with --apply flag
# Idempotent: Won't add duplicate pointers

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Default options
APPLY=false
TARGET_PATH="."
CREATE_BACKUP=true
DRY_RUN=true

# Protocol pointer template
read -r -d '' PROTOCOL_SECTION << 'EOF' || true

---

## Domain Zero Protocol

This project follows the Domain Zero Protocol for AI-assisted development.

**Primary entrypoint**: [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

**Workflow guidance**:
- Mission Control & initialization: `protocol/GOJO.md`
- Feature implementation: `protocol/YUUJI.md`
- Security review: `protocol/MEGUMI.md`
- Tier selection guide: `protocol/TIER-SELECTION-GUIDE.md`

For complete protocol details, read [`protocol/CLAUDE.md`](protocol/CLAUDE.md) - the canonical source of truth.

---
EOF

# Common instruction file patterns
INSTRUCTION_PATTERNS=(
    "AI_INSTRUCTIONS.md"
    "AI.md"
    ".github/copilot-instructions.md"
    ".github/instructions/*.md"
    ".cursorrules"
    "CONTRIBUTING.md"
    "DEVELOPMENT.md"
    ".vscode/instructions.md"
    ".idea/instructions.md"
)

# Usage information
usage() {
    cat << USAGE
Domain Zero Protocol - Instruction File Updater

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --apply         Actually modify files (default: dry-run)
    --path PATH     Root directory to scan (default: current directory)
    --no-backup     Don't create backup files
    -h, --help      Show this help message

EXAMPLES:
    $0                          # Dry-run mode - show what would change
    $0 --apply                  # Actually append protocol pointers
    $0 --apply --path ~/project # Update specific directory

USAGE
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --apply)
            APPLY=true
            DRY_RUN=false
            shift
            ;;
        --path)
            TARGET_PATH="$2"
            shift 2
            ;;
        --no-backup)
            CREATE_BACKUP=false
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${RESET}"
            usage
            ;;
    esac
done

# Check if file already has protocol pointer
has_protocol_pointer() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        return 1
    fi

    # Check for protocol pointer indicators
    if grep -q "protocol/CLAUDE\.md" "$file" 2>/dev/null || \
       grep -q "Domain Zero Protocol" "$file" 2>/dev/null; then
        return 0
    fi

    return 1
}

# Append protocol pointer to file
append_protocol_pointer() {
    local file="$1"
    local dry_run="$2"

    if has_protocol_pointer "$file"; then
        echo -e "  ${YELLOW}[SKIP]${RESET} Already has protocol pointer: $file"
        return 1
    fi

    if [[ "$dry_run" == "true" ]]; then
        echo -e "  ${BLUE}[DRY-RUN]${RESET} Would append to: $file"
        return 0
    fi

    # Create backup if requested
    if [[ "$CREATE_BACKUP" == "true" ]]; then
        cp "$file" "$file.backup"
        echo -e "  ${GREEN}[BACKUP]${RESET} Created: $file.backup"
    fi

    # Append protocol pointer
    echo "$PROTOCOL_SECTION" >> "$file"
    echo -e "  ${GREEN}[UPDATED]${RESET} Appended protocol pointer to: $file"
    return 0
}

# Main execution
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}║  Domain Zero Protocol - Instruction File Updater         ║${RESET}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${RESET}"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}⚠️  DRY-RUN MODE${RESET} - No files will be modified"
    echo "   Use --apply to actually update files"
    echo ""
fi

# Arrays to track files
declare -a FOUND_FILES
declare -a WILL_UPDATE

# Scan for instruction files
echo "Scanning for instruction files in: $TARGET_PATH"
echo ""

for pattern in "${INSTRUCTION_PATTERNS[@]}"; do
    # Use find with name pattern
    while IFS= read -r -d '' file; do
        # Skip if in protocol/ directory
        if [[ "$file" == *"/protocol/"* ]]; then
            continue
        fi

        # Skip if it's AI_INSTRUCTIONS.md (our shim)
        if [[ "$(basename "$file")" == "AI_INSTRUCTIONS.md" ]]; then
            continue
        fi

        FOUND_FILES+=("$file")

        if ! has_protocol_pointer "$file"; then
            WILL_UPDATE+=("$file")
        fi
    done < <(find "$TARGET_PATH" -name "$(basename "$pattern")" -type f -print0 2>/dev/null)
done

# Report findings
if [[ ${#FOUND_FILES[@]} -eq 0 ]]; then
    echo -e "${YELLOW}No instruction files found.${RESET}"
    echo ""
    echo "Common locations:"
    echo "  - .github/copilot-instructions.md"
    echo "  - .cursorrules"
    echo "  - CONTRIBUTING.md"
    echo ""
    exit 0
fi

echo "Found ${#FOUND_FILES[@]} instruction file(s):"
echo ""

# Process each file
UPDATED_COUNT=0
for file in "${FOUND_FILES[@]}"; do
    if append_protocol_pointer "$file" "$DRY_RUN"; then
        ((UPDATED_COUNT++)) || true
    fi
done

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${RESET}"
echo "Summary:"
echo "  Files found: ${#FOUND_FILES[@]}"
echo "  Files that need update: ${#WILL_UPDATE[@]}"

if [[ "$APPLY" == "true" ]]; then
    echo -e "  ${GREEN}Files updated: $UPDATED_COUNT${RESET}"
    if [[ "$CREATE_BACKUP" == "true" ]]; then
        echo -e "  ${GREEN}Backups created: $UPDATED_COUNT${RESET}"
    fi
else
    echo -e "  ${YELLOW}Files would be updated: $UPDATED_COUNT${RESET} (use --apply to modify)"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${RESET}"
echo ""

if [[ "$DRY_RUN" == "true" && ${#WILL_UPDATE[@]} -gt 0 ]]; then
    echo -e "${YELLOW}▶ Next Steps:${RESET}"
    echo "  1. Review the files listed above"
    echo "  2. Run with --apply to actually update them:"
    echo -e "     ${GREEN}./update-instructions.sh --apply${RESET}"
    echo ""
fi

if [[ "$APPLY" == "true" && $UPDATED_COUNT -gt 0 ]]; then
    echo -e "${GREEN}✓ Update complete!${RESET}"
    echo ""
    echo "Modified files now point to protocol/CLAUDE.md as canonical source."
    echo "Backup files created (*.backup) - delete these when confirmed working."
    echo ""
fi

# Exit codes
if [[ "$APPLY" == "true" ]]; then
    exit 0  # Success
else
    if [[ ${#WILL_UPDATE[@]} -gt 0 ]]; then
        exit 1  # Dry-run found files to update
    else
        exit 0  # Nothing to do
    fi
fi
