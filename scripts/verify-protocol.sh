#!/usr/bin/env bash
# Domain Zero Protocol Verification Script (Bash)
# Version: 2.0
# Purpose: Verify protocol integrity, configuration completeness, and enforcement rules

set -o pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

ERROR_COUNT=0
WARNING_COUNT=0
PASS_COUNT=0
VERBOSE=false
QUICK_MODE=false
SKIP_CHECKS=()
ONLY_CHECKS=()
CRITICAL_ERROR=false

# Colors for output
COLOR_RESET='\033[0m'
COLOR_PASS='\033[0;32m'
COLOR_FAIL='\033[0;31m'
COLOR_WARN='\033[0;33m'
COLOR_INFO='\033[0;36m'
COLOR_HEADER='\033[0;35m'

# Available checks: name:function:level
AVAILABLE_CHECKS=(
    "dependencies:check_dependencies:critical"
    "files:test_file_existence:critical"
    "config:test_config_completeness:critical"
    "yaml:validate_yaml_syntax:critical"
    "isolation:test_isolation_vocabulary:warning"
    "templates:test_output_templates:warning"
    "protection:test_claude_md_protection:warning"
    "backup:test_backup_configuration:warning"
)

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

write_fail_with_context() {
    local message=$1
    local impact=$2
    local action=$3
    local doc_link=$4

    write_fail "$message"
    if [ -n "$impact" ]; then
        echo -e "      ${COLOR_INFO}Impact:${COLOR_RESET} $impact"
    fi
    if [ -n "$action" ]; then
        echo -e "      ${COLOR_INFO}Action:${COLOR_RESET} $action"
    fi
    if [ -n "$doc_link" ]; then
        echo -e "      ${COLOR_INFO}Docs:${COLOR_RESET} $doc_link"
    fi
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

Domain Zero Protocol Verification Script v2.0

USAGE:
    ./scripts/verify-protocol.sh [OPTIONS]

OPTIONS:
    --verbose       Show detailed information during verification
    --quick         Run only critical checks (faster)
    --skip=CHECK    Skip specific check (can be used multiple times)
    --only=CHECK    Run only specific check (can be used multiple times)
    --list          List all available checks and exit
    --help          Show this help message

DESCRIPTION:
    This script verifies the integrity and completeness of the Domain Zero Protocol
    installation. It checks:

    0. Dependencies - Verify required command-line tools are installed
    1. File Existence - Ensure all required protocol files are present
    2. Configuration Completeness - Verify protocol.config.yaml has required fields
    3. YAML Syntax - Validate YAML syntax in configuration files
    4. Isolation Vocabulary - Scan for forbidden cross-agent vocabulary
    5. Output Templates - Check role outputs conform to required headers
    6. CLAUDE.md Protection - Verify CODEOWNERS or protection rules exist
    7. Backup Configuration - Ensure backup requirements are configured

EXAMPLES:
    # Basic verification
    ./scripts/verify-protocol.sh

    # Verbose output
    ./scripts/verify-protocol.sh --verbose

    # Quick mode (critical checks only)
    ./scripts/verify-protocol.sh --quick

    # Skip isolation check
    ./scripts/verify-protocol.sh --skip=isolation

    # Run only file and config checks
    ./scripts/verify-protocol.sh --only=files --only=config

    # List available checks
    ./scripts/verify-protocol.sh --list

EXIT CODES:
    0 - All checks passed
    1 - Errors found
    2 - Warnings only (no errors)
    3 - Missing dependencies (cannot proceed)

EOF
    exit 0
}

list_checks() {
    echo ""
    echo "Available Checks:"
    echo ""
    printf "  %-15s %-10s %s\n" "NAME" "LEVEL" "DESCRIPTION"
    echo "  ─────────────────────────────────────────────────────────"

    local descriptions=(
        "dependencies:critical:Verify required command-line tools"
        "files:critical:Check protocol file existence"
        "config:critical:Validate configuration completeness"
        "yaml:critical:Check YAML syntax validity"
        "isolation:warning:Scan for forbidden vocabulary"
        "templates:warning:Check output template structure"
        "protection:warning:Verify CLAUDE.md protection"
        "backup:warning:Check backup configuration"
    )

    for desc in "${descriptions[@]}"; do
        IFS=':' read -r name level description <<< "$desc"
        printf "  %-15s %-10s %s\n" "$name" "$level" "$description"
    done

    echo ""
    echo "Usage: --skip=NAME or --only=NAME"
    echo ""
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
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --skip=*)
            SKIP_CHECKS+=("${1#*=}")
            shift
            ;;
        --only=*)
            ONLY_CHECKS+=("${1#*=}")
            shift
            ;;
        --list)
            list_checks
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

check_dependencies() {
    write_header "0. Dependency Check"

    local required_tools=("grep" "cat" "sed")
    local optional_tools=("python3" "python" "yamllint")
    local missing_required=()

    write_info "Checking required command-line tools..."
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            write_pass "Found: $tool"
        else
            missing_required+=("$tool")
            write_fail_with_context \
                "Required tool not found: $tool" \
                "Verification cannot proceed without this tool" \
                "Install $tool using your package manager (apt, brew, etc.)" \
                ""
        fi
    done

    if [ ${#missing_required[@]} -gt 0 ]; then
        echo ""
        echo -e "  ${COLOR_FAIL}✗ Missing required tools: ${missing_required[*]}${COLOR_RESET}"
        echo -e "  ${COLOR_INFO}Install them before proceeding:${COLOR_RESET}"
        echo -e "    ${COLOR_INFO}Ubuntu/Debian: sudo apt-get install ${missing_required[*]}${COLOR_RESET}"
        echo -e "    ${COLOR_INFO}macOS: brew install ${missing_required[*]}${COLOR_RESET}"
        echo ""
        exit 3
    fi

    write_info "Checking optional tools..."
    for tool in "${optional_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            write_pass "Found (optional): $tool"
        else
            write_info "Optional tool not found: $tool"
        fi
    done
}

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

    local missing_critical=()

    write_info "Checking required files..."
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            write_pass "Found: $file"
        else
            missing_critical+=("$file")
            write_fail_with_context \
                "Missing required file: $file" \
                "Protocol cannot function without this file" \
                "Copy from Domain Zero repository or re-run setup" \
                "https://github.com/DewyHRite/Domain-Zero-Protocol#installation"
        fi
    done

    if [ ${#missing_critical[@]} -gt 0 ]; then
        CRITICAL_ERROR=true
    fi

    write_info "Checking optional files..."
    for file in "${optional_files[@]}"; do
        if [ -f "$file" ]; then
            write_pass "Found: $file"
        else
            write_warn "Optional file not found: $file"
        fi
    done
}

validate_yaml_syntax() {
    write_header "3. YAML Syntax Validation"

    if [ ! -f "protocol.config.yaml" ]; then
        write_fail_with_context \
            "protocol.config.yaml not found" \
            "Cannot validate YAML syntax" \
            "Ensure protocol.config.yaml exists" \
            ""
        CRITICAL_ERROR=true
        return 1
    fi

    # Try Python validation first
    if command -v python3 &> /dev/null; then
        write_info "Validating YAML syntax with Python..."
        local validation_output
        validation_output=$(python3 -c "import yaml; yaml.safe_load(open('protocol.config.yaml'))" 2>&1)
        if [ $? -eq 0 ]; then
            write_pass "YAML syntax valid (verified with Python)"
            return 0
        fi

        if echo "$validation_output" | grep -q "ModuleNotFoundError: No module named 'yaml'"; then
            write_warn "PyYAML not installed; skipping python-based YAML validation"
            if command -v yamllint &> /dev/null; then
                write_info "Falling back to yamllint for syntax validation..."
                if yamllint -d relaxed protocol.config.yaml > /dev/null 2>&1; then
                    write_pass "YAML syntax valid (verified with yamllint)"
                    return 0
                fi
                write_fail_with_context \
                    "Invalid YAML syntax in protocol.config.yaml" \
                    "Configuration file has syntax errors" \
                    "Run 'yamllint protocol.config.yaml' for details" \
                    ""
                CRITICAL_ERROR=true
                return 1
            fi

            write_info "Install PyYAML or yamllint for syntax validation"
            return 0
        fi

        write_fail_with_context \
            "Invalid YAML syntax in protocol.config.yaml" \
            "Configuration file cannot be parsed" \
            "Fix syntax errors using a YAML validator" \
            "https://www.yamllint.com/"
        CRITICAL_ERROR=true
        return 1
    elif command -v python &> /dev/null; then
        write_info "Validating YAML syntax with Python..."
        local validation_output
        validation_output=$(python -c "import yaml; yaml.safe_load(open('protocol.config.yaml'))" 2>&1)
        if [ $? -eq 0 ]; then
            write_pass "YAML syntax valid (verified with Python)"
            return 0
        fi

        if echo "$validation_output" | grep -q "ModuleNotFoundError: No module named 'yaml'"; then
            write_warn "PyYAML not installed; skipping python-based YAML validation"
            if command -v yamllint &> /dev/null; then
                write_info "Falling back to yamllint for syntax validation..."
                if yamllint -d relaxed protocol.config.yaml > /dev/null 2>&1; then
                    write_pass "YAML syntax valid (verified with yamllint)"
                    return 0
                fi
                write_fail_with_context \
                    "Invalid YAML syntax in protocol.config.yaml" \
                    "Configuration file has syntax errors" \
                    "Run 'yamllint protocol.config.yaml' for details" \
                    ""
                CRITICAL_ERROR=true
                return 1
            fi

            write_info "Install PyYAML or yamllint for syntax validation"
            return 0
        fi

        write_fail_with_context \
            "Invalid YAML syntax in protocol.config.yaml" \
            "Configuration file cannot be parsed" \
            "Fix syntax errors using a YAML validator" \
            "https://www.yamllint.com/"
        CRITICAL_ERROR=true
        return 1
    elif command -v yamllint &> /dev/null; then
        write_info "Validating YAML syntax with yamllint..."
        if yamllint -d relaxed protocol.config.yaml > /dev/null 2>&1; then
            write_pass "YAML syntax valid (verified with yamllint)"
        else
            write_fail_with_context \
                "Invalid YAML syntax in protocol.config.yaml" \
                "Configuration file has syntax errors" \
                "Run 'yamllint protocol.config.yaml' for details" \
                ""
            CRITICAL_ERROR=true
            return 1
        fi
    else
        write_warn "YAML validation skipped (Python/yamllint not found)"
        write_info "Install Python or yamllint for syntax validation"
    fi
}

test_config_completeness() {
    write_header "2. Configuration Completeness Check"

    if [ ! -f "protocol.config.yaml" ]; then
        write_fail_with_context \
            "protocol.config.yaml not found" \
            "Cannot verify configuration" \
            "Copy protocol.config.yaml from Domain Zero repository" \
            "https://github.com/DewyHRite/Domain-Zero-Protocol"
        CRITICAL_ERROR=true
        return 1
    fi

    write_info "Reading protocol.config.yaml..."
    local config_content
    config_content=$(cat "protocol.config.yaml")

    if [ -z "$config_content" ]; then
        write_fail_with_context \
            "protocol.config.yaml is empty" \
            "No configuration available" \
            "Populate protocol.config.yaml with valid configuration" \
            ""
        CRITICAL_ERROR=true
        return 1
    fi

    # Check for placeholder values that need to be updated
    local placeholders=(
        "Your Name"
        "email@example.com"
        "Your Project Name"
        "Your Organization"
        "your-org/your-repo"
        "YYYY-MM-DD"
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
        write_fail "Configuration contains placeholder values that must be updated:"
        for placeholder in "${placeholders_found[@]}"; do
            echo -e "      ${COLOR_FAIL}✗ $placeholder${COLOR_RESET}"
        done
        echo ""
        echo -e "  ${COLOR_INFO}HOW TO FIX:${COLOR_RESET}"
        echo -e "  ${COLOR_INFO}1. Open protocol.config.yaml in your editor${COLOR_RESET}"
        echo -e "  ${COLOR_INFO}2. Search for the placeholder values listed above${COLOR_RESET}"
        echo -e "  ${COLOR_INFO}3. Replace them with your actual project information${COLOR_RESET}"
        echo ""
        echo -e "  ${COLOR_INFO}Example configuration:${COLOR_RESET}"
        echo -e "    ${COLOR_INFO}user:${COLOR_RESET}"
        echo -e "      ${COLOR_INFO}name: \"John Smith\"${COLOR_RESET}"
        echo -e "      ${COLOR_INFO}contact: \"john.smith@company.com\"${COLOR_RESET}"
        echo -e "      ${COLOR_INFO}organization: \"Acme Corp\"${COLOR_RESET}"
        echo ""
        echo -e "    ${COLOR_INFO}project:${COLOR_RESET}"
        echo -e "      ${COLOR_INFO}name: \"My Awesome Project\"${COLOR_RESET}"
        echo -e "      ${COLOR_INFO}repo: \"https://github.com/myorg/my-project\"${COLOR_RESET}"
        echo -e "      ${COLOR_INFO}created: \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"${COLOR_RESET}"
        echo ""
        echo -e "  ${COLOR_WARN}Note: The '<PINNED_SHA>' placeholder is optional and can be left as-is.${COLOR_RESET}"
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
            write_fail_with_context \
                "Missing config section: $section" \
                "Configuration incomplete" \
                "Add required section to protocol.config.yaml" \
                ""
        fi
    done
}

test_isolation_vocabulary() {
    write_header "4. Isolation Vocabulary Check"

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
    write_header "5. Output Template Check"

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
    write_header "6. CLAUDE.md Protection Check"

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
    write_header "7. Backup Configuration Check"

    if [ ! -f "protocol.config.yaml" ]; then
        write_fail_with_context \
            "protocol.config.yaml not found" \
            "Cannot verify backup configuration" \
            "Ensure protocol.config.yaml exists" \
            ""
        return 1
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
# CHECK EXECUTION LOGIC
# ============================================================================

should_run_check() {
    local check_name=$1
    local check_level=$2

    # Skip if in skip list
    if [[ " ${SKIP_CHECKS[*]} " =~ " ${check_name} " ]]; then
        return 1  # Don't run
    fi

    # Skip if only specific checks requested and this isn't one
    if [ ${#ONLY_CHECKS[@]} -gt 0 ] && ! [[ " ${ONLY_CHECKS[*]} " =~ " ${check_name} " ]]; then
        return 1  # Don't run
    fi

    # Skip non-critical if quick mode
    if [ "$QUICK_MODE" = true ] && [ "$check_level" != "critical" ]; then
        return 1  # Don't run
    fi

    return 0  # Run check
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

cat << 'EOF'

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        DOMAIN ZERO PROTOCOL VERIFICATION TOOL                 ║
║                     Version 2.0                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

EOF

write_info "Starting protocol verification..."
write_info "Working directory: $(pwd)"

if [ "$QUICK_MODE" = true ]; then
    write_info "Running in QUICK mode (critical checks only)"
fi

if [ ${#SKIP_CHECKS[@]} -gt 0 ]; then
    write_info "Skipping checks: ${SKIP_CHECKS[*]}"
fi

if [ ${#ONLY_CHECKS[@]} -gt 0 ]; then
    write_info "Running only: ${ONLY_CHECKS[*]}"
fi

# Execute checks based on configuration
for check_spec in "${AVAILABLE_CHECKS[@]}"; do
    IFS=':' read -r check_name check_func check_level <<< "$check_spec"

    if should_run_check "$check_name" "$check_level"; then
        $check_func

        # Stop if critical error occurred in critical check
        if [ "$CRITICAL_ERROR" = true ] && [ "$check_level" = "critical" ]; then
            echo ""
            echo -e "  ${COLOR_FAIL}⚠ Critical error detected. Stopping verification.${COLOR_RESET}"
            echo -e "  ${COLOR_INFO}Fix critical errors before running additional checks.${COLOR_RESET}"
            break
        fi
    else
        write_info "Skipped check: $check_name"
    fi
done

# ============================================================================
# SUMMARY
# ============================================================================

write_header "Verification Summary"

echo ""
echo -e "  ${COLOR_PASS}PASSED: $PASS_COUNT${COLOR_RESET}"
echo -e "  ${COLOR_WARN}WARNINGS: $WARNING_COUNT${COLOR_RESET}"
echo -e "  ${COLOR_FAIL}ERRORS: $ERROR_COUNT${COLOR_RESET}"
echo ""

if [ "$CRITICAL_ERROR" = true ]; then
    echo -e "  ${COLOR_FAIL}✗ Protocol verification FAILED (Critical Errors)${COLOR_RESET}"
    echo -e "    ${COLOR_FAIL}Fix critical errors before proceeding.${COLOR_RESET}"
    echo ""
    echo -e "  ${COLOR_INFO}Tip: Run with --verbose for detailed information${COLOR_RESET}"
    exit 1
elif [ $ERROR_COUNT -eq 0 ] && [ $WARNING_COUNT -eq 0 ]; then
    echo -e "  ${COLOR_PASS}✓ Protocol verification PASSED - All checks successful!${COLOR_RESET}"
    exit 0
elif [ $ERROR_COUNT -eq 0 ]; then
    echo -e "  ${COLOR_WARN}⚠ Protocol verification PASSED with WARNINGS${COLOR_RESET}"
    echo -e "    ${COLOR_WARN}Consider addressing warnings for optimal protocol operation.${COLOR_RESET}"
    exit 2
else
    echo -e "  ${COLOR_FAIL}✗ Protocol verification FAILED${COLOR_RESET}"
    echo -e "    ${COLOR_FAIL}Please fix errors before proceeding.${COLOR_RESET}"
    echo ""
    echo -e "  ${COLOR_INFO}Tip: Run with --verbose for detailed information${COLOR_RESET}"
    exit 1
fi
