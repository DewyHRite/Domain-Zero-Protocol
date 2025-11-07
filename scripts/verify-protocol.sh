#!/usr/bin/env bash
# Domain Zero Protocol Verification Script (Bash)
# Version: 1.0
# Purpose: Verify protocol integrity, configuration completeness, and enforcement rules

set -o pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

ERROR_COUNT=0
WARNING_COUNT=0
PASS_COUNT=0
VERBOSE=false

# Colors for output
COLOR_RESET='\033[0m'
COLOR_PASS='\033[0;32m'
COLOR_FAIL='\033[0;31m'
COLOR_WARN='\033[0;33m'
COLOR_INFO='\033[0;36m'
COLOR_HEADER='\033[0;35m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

write_header() {
    echo -e "\n${COLOR_HEADER}========================================"
    echo -e "$1"
    echo -e "========================================${COLOR_RESET}"
}

write_pass() {
    echo -e "  ${COLOR_PASS}[PASS]${COLOR_RESET} $1"
    ((PASS_COUNT++))
}

write_fail() {
    echo -e "  ${COLOR_FAIL}[FAIL]${COLOR_RESET} $1"
    ((ERROR_COUNT++))
}

write_warn() {
    echo -e "  ${COLOR_WARN}[WARN]${COLOR_RESET} $1"
    ((WARNING_COUNT++))
}

write_info() {
    if [ "$VERBOSE" = true ]; then
        echo -e "  ${COLOR_INFO}[INFO]${COLOR_RESET} $1"
    fi
}

show_help() {
    cat << 'EOF'

Domain Zero Protocol Verification Script

USAGE:
    ./scripts/verify-protocol.sh [OPTIONS]

OPTIONS:
    --verbose   Show detailed information during verification
    --help      Show this help message

DESCRIPTION:
    This script verifies the integrity and completeness of the Domain Zero Protocol
    installation. It checks:

    1. File Existence - Ensure all required protocol files are present
    2. Configuration Completeness - Verify protocol.config.yaml has required fields
    3. Isolation Vocabulary - Scan for forbidden cross-agent vocabulary
    4. Output Templates - Check role outputs conform to required headers
    5. CLAUDE.md Protection - Verify CODEOWNERS or protection rules exist
    6. Backup Configuration - Ensure backup requirements are configured

EXAMPLES:
    # Basic verification
    ./scripts/verify-protocol.sh

    # Verbose output
    ./scripts/verify-protocol.sh --verbose

EXIT CODES:
    0 - All checks passed
    1 - Errors found
    2 - Warnings only (no errors)

EOF
    exit 0
}

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================================
# VERIFICATION CHECKS
# ============================================================================

test_file_existence() {
    write_header "1. File Existence Check"

    local required_files=(
        "protocol/CLAUDE.md"
        "protocol/YUUJI.md"
        "protocol/MEGUMI.md"
        "protocol/GOJO.md"
        "protocol/TIER-SELECTION-GUIDE.md"
        "protocol.config.yaml"
        ".protocol-state/project-state.json"
        ".protocol-state/dev-notes.md"
        ".protocol-state/security-review.md"
    )

    local optional_files=(
        "PROTOCOL_QUICKSTART.md"
        ".github/copilot-instructions.md"
        "CODEOWNERS"
        ".gitignore"
    )

    write_info "Checking required files..."
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            write_pass "Found: $file"
        else
            write_fail "Missing required file: $file"
        fi
    done

    write_info "Checking optional files..."
    for file in "${optional_files[@]}"; do
        if [ -f "$file" ]; then
            write_pass "Found: $file"
        else
            write_warn "Optional file not found: $file"
        fi
    done
}

test_config_completeness() {
    write_header "2. Configuration Completeness Check"

    if [ ! -f "protocol.config.yaml" ]; then
        write_fail "protocol.config.yaml not found - cannot verify configuration"
        return
    fi

    write_info "Reading protocol.config.yaml..."
    local config_content
    config_content=$(cat "protocol.config.yaml")

    if [ -z "$config_content" ]; then
        write_fail "protocol.config.yaml is empty"
        return
    fi

    # Check for placeholder values that need to be updated
    local placeholders=(
        "Your Name"
        "email@example.com"
        "Your Project Name"
        "Your Organization"
        "your-org/your-repo"
    )

    local placeholders_found=()
    for placeholder in "${placeholders[@]}"; do
        if echo "$config_content" | grep -q "$placeholder"; then
            placeholders_found+=("$placeholder")
        fi
    done

    if [ ${#placeholders_found[@]} -eq 0 ]; then
        write_pass "No placeholder values detected in config"
    else
        write_warn "Found placeholder values in config (consider updating):"
        for placeholder in "${placeholders_found[@]}"; do
            echo -e "      ${COLOR_WARN}- $placeholder${COLOR_RESET}"
        done
    fi

    # Check for required sections
    local required_sections=(
        "user:"
        "project:"
        "roles:"
        "enforcement:"
        "ai:"
        "tiers:"
        "paths:"
    )

    for section in "${required_sections[@]}"; do
        if echo "$config_content" | grep -q "$section"; then
            write_pass "Config section present: $section"
        else
            write_fail "Missing config section: $section"
        fi
    done
}

test_isolation_vocabulary() {
    write_header "3. Isolation Vocabulary Check"

    write_info "Checking for forbidden cross-agent vocabulary..."

    local isolation_errors=0

    # Yuuji should not mention Gojo directly in protocol definition
    if [ -f "protocol/YUUJI.md" ]; then
        local forbidden_terms=("GOJO" "Satoru Gojo" "Mission Control" "Trigger 19" "trigger-19")
        local yuuji_found=false

        for term in "${forbidden_terms[@]}"; do
            if grep -q "$term" "protocol/YUUJI.md"; then
                write_warn "Yuuji protocol mentions forbidden term: $term"
                ((isolation_errors++))
                yuuji_found=true
            fi
        done

        if [ "$yuuji_found" = false ]; then
            write_pass "Yuuji isolation vocabulary check passed"
        fi
    else
        write_warn "protocol/YUUJI.md not found"
    fi

    # Megumi should not mention Gojo directly in protocol definition
    if [ -f "protocol/MEGUMI.md" ]; then
        local forbidden_terms=("GOJO" "Satoru Gojo" "Mission Control" "Trigger 19" "trigger-19")
        local megumi_found=false

        for term in "${forbidden_terms[@]}"; do
            if grep -q "$term" "protocol/MEGUMI.md"; then
                write_warn "Megumi protocol mentions forbidden term: $term"
                ((isolation_errors++))
                megumi_found=true
            fi
        done

        if [ "$megumi_found" = false ]; then
            write_pass "Megumi isolation vocabulary check passed"
        fi
    else
        write_warn "protocol/MEGUMI.md not found"
    fi

    if [ $isolation_errors -gt 0 ]; then
        write_warn "Found $isolation_errors isolation vocabulary violations"
        write_info "The 'weight' mechanism requires Yuuji and Megumi to remain unaware of Gojo's existence"
    fi
}

test_output_templates() {
    write_header "4. Output Template Check"

    write_info "Checking for required output structure..."

    # Check dev-notes.md for Yuuji's output headers
    if [ -f ".protocol-state/dev-notes.md" ]; then
        write_pass "dev-notes.md exists (Yuuji's output template)"
    else
        write_warn "dev-notes.md not found - Yuuji hasn't created implementation log yet"
    fi

    # Check security-review.md for Megumi's output headers
    if [ -f ".protocol-state/security-review.md" ]; then
        write_pass "security-review.md exists (Megumi's output template)"
    else
        write_warn "security-review.md not found - Megumi hasn't created security review yet"
    fi

    write_info "Note: Deep template structure validation not yet implemented"
}

test_claude_md_protection() {
    write_header "5. CLAUDE.md Protection Check"

    if [ -f "CODEOWNERS" ]; then
        if grep -q "protocol/CLAUDE.md" "CODEOWNERS"; then
            write_pass "CODEOWNERS file protects protocol/CLAUDE.md"
        else
            write_warn "CODEOWNERS exists but doesn't protect protocol/CLAUDE.md"
        fi
    else
        write_warn "CODEOWNERS file not found - consider adding for CLAUDE.md protection"
    fi

    # Check if config has protection enabled
    if [ -f "protocol.config.yaml" ]; then
        if grep -q "claude_md_protected:.*true" "protocol.config.yaml"; then
            write_pass "Config has CLAUDE.md protection enabled"
        else
            write_warn "Config does not explicitly enable CLAUDE.md protection"
        fi
    fi
}

test_backup_configuration() {
    write_header "6. Backup Configuration Check"

    if [ ! -f "protocol.config.yaml" ]; then
        write_fail "protocol.config.yaml not found - cannot verify backup configuration"
        return
    fi

    local config_content
    config_content=$(cat "protocol.config.yaml")

    if echo "$config_content" | grep -qi "required_for:.*yuuji"; then
        write_pass "Backup requirement configured for Yuuji"
    else
        write_warn "Backup requirement for Yuuji not found in config"
    fi

    if echo "$config_content" | grep -q "retention_days:[[:space:]]*[0-9]\+"; then
        write_pass "Backup retention policy configured"
    else
        write_warn "Backup retention policy not found in config"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

cat << 'EOF'

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        DOMAIN ZERO PROTOCOL VERIFICATION TOOL                 ║
║                     Version 1.0                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

EOF

write_info "Starting protocol verification..."
write_info "Working directory: $(pwd)"

# Run all verification checks
test_file_existence
test_config_completeness
test_isolation_vocabulary
test_output_templates
test_claude_md_protection
test_backup_configuration

# ============================================================================
# SUMMARY
# ============================================================================

write_header "Verification Summary"

echo ""
echo -e "  ${COLOR_PASS}PASSED: $PASS_COUNT${COLOR_RESET}"
echo -e "  ${COLOR_WARN}WARNINGS: $WARNING_COUNT${COLOR_RESET}"
echo -e "  ${COLOR_FAIL}ERRORS: $ERROR_COUNT${COLOR_RESET}"
echo ""

if [ $ERROR_COUNT -eq 0 ] && [ $WARNING_COUNT -eq 0 ]; then
    echo -e "  ${COLOR_PASS}✓ Protocol verification PASSED - All checks successful!${COLOR_RESET}"
    exit 0
elif [ $ERROR_COUNT -eq 0 ]; then
    echo -e "  ${COLOR_WARN}⚠ Protocol verification PASSED with WARNINGS${COLOR_RESET}"
    echo -e "    ${COLOR_WARN}Consider addressing warnings for optimal protocol operation.${COLOR_RESET}"
    exit 2
else
    echo -e "  ${COLOR_FAIL}✗ Protocol verification FAILED${COLOR_RESET}"
    echo -e "    ${COLOR_FAIL}Please fix errors before proceeding.${COLOR_RESET}"
    exit 1
fi
