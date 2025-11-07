# P3 - Script Error Handling Enhancement Design

**Task:** Improve error messages and validation in verification scripts
**Estimated Time:** 2-4 hours
**Status:** In Design Phase
**Date:** November 7, 2025

---

## Current State Analysis

### Existing Error Handling (v6.2.5)

#### Strengths ✅
1. **Color-coded output** - Pass/Fail/Warn clearly differentiated
2. **Exit codes** - Proper exit codes (0/1/2) for success/error/warning
3. **Helpful guidance** - "HOW TO FIX" sections for placeholder errors
4. **Summary report** - Clear summary with counts
5. **Verbose mode** - Optional detailed output

#### Weaknesses ❌
1. **No error recovery** - Script continues even when critical files missing
2. **No dependency checking** - Doesn't check if required tools exist (grep, cat, etc.)
3. **Poor error context** - Some errors don't explain impact
4. **No skip/ignore option** - Can't skip non-critical checks
5. **Limited validation** - Doesn't validate YAML syntax
6. **No retry mechanism** - No way to fix and re-check specific sections
7. **Hard-coded checks** - No way to extend checks without modifying script
8. **No JSON output** - Can't integrate with CI/CD easily

---

## Enhancement Strategy

### 1. **Graceful Degradation** (High Priority)

**Problem:** When critical files missing, subsequent checks fail ungracefully

**Solution:**
```bash
# Before (current):
test_config_completeness() {
    if [ ! -f "protocol.config.yaml" ]; then
        write_fail "protocol.config.yaml not found"
        return  # Silent failure
    fi
    # ... continues to run dependent checks ...
}

# After (enhanced):
test_config_completeness() {
    if [ ! -f "protocol.config.yaml" ]; then
        write_fail "protocol.config.yaml not found"
        write_info "Impact: Cannot verify configuration completeness"
        write_info "Suggested action: Run 'cp protocol.config.yaml.example protocol.config.yaml'"
        CRITICAL_ERROR=true
        return 1  # Return error code
    fi
    # ... rest of function ...
}
```

**Benefits:**
- Clear impact explanation
- Actionable suggestions
- Error codes for programmatic handling

---

### 2. **Dependency Checking** (High Priority)

**Problem:** Script assumes tools exist (grep, cat, etc.)

**Solution:**
```bash
check_dependencies() {
    write_header "0. Dependency Check"

    local required_tools=("grep" "cat" "sed" "awk")
    local missing_tools=()

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
            write_fail "Required tool not found: $tool"
        else
            write_pass "Found: $tool"
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        write_fail "Missing required tools: ${missing_tools[*]}"
        write_info "Install missing tools before running verification"
        exit 3  # New exit code for missing dependencies
    fi
}
```

**Benefits:**
- Early detection of environment issues
- Clear dependency requirements
- New exit code (3) for missing dependencies

---

### 3. **Enhanced Error Messages** (High Priority)

**Problem:** Some errors lack context and actionable guidance

**Solution:**
```bash
write_fail_with_context() {
    local message=$1
    local impact=$2
    local suggestion=$3
    local doc_link=$4

    write_fail "$message"
    echo -e "      ${COLOR_INFO}Impact:${COLOR_RESET} $impact"
    echo -e "      ${COLOR_INFO}Action:${COLOR_RESET} $suggestion"
    if [ -n "$doc_link" ]; then
        echo -e "      ${COLOR_INFO}Docs:${COLOR_RESET} $doc_link"
    fi
}

# Usage:
write_fail_with_context \
    "Missing required file: protocol/CLAUDE.md" \
    "Protocol cannot function without main configuration" \
    "Copy from Domain Zero repository or re-run setup" \
    "https://github.com/DewyHRite/Domain-Zero-Protocol#installation"
```

**Benefits:**
- Three-part error message (what/why/how)
- Documentation links for complex issues
- Consistent error format

---

### 4. **Selective Check Execution** (Medium Priority)

**Problem:** Can't skip non-critical checks or re-run specific sections

**Solution:**
```bash
# Add new command-line options:
#   --skip=<check>     Skip specific check (e.g., --skip=isolation)
#   --only=<check>     Run only specific check
#   --quick            Run only critical checks
#   --list             List available checks

AVAILABLE_CHECKS=(
    "dependencies:check_dependencies:critical"
    "files:test_file_existence:critical"
    "config:test_config_completeness:critical"
    "isolation:test_isolation_vocabulary:warning"
    "templates:test_output_templates:warning"
    "protection:test_claude_md_protection:warning"
    "backup:test_backup_configuration:warning"
)

# Parse --skip and --only options
SKIP_CHECKS=()
ONLY_CHECKS=()
QUICK_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip=*)
            SKIP_CHECKS+=("${1#*=}")
            shift
            ;;
        --only=*)
            ONLY_CHECKS+=("${1#*=}")
            shift
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --list)
            list_checks
            exit 0
            ;;
    esac
done

# Execute checks conditionally
for check_spec in "${AVAILABLE_CHECKS[@]}"; do
    IFS=':' read -r check_name check_func check_level <<< "$check_spec"

    # Skip if in skip list
    if [[ " ${SKIP_CHECKS[*]} " =~ " ${check_name} " ]]; then
        write_info "Skipping check: $check_name"
        continue
    fi

    # Skip if only specific checks requested and this isn't one
    if [ ${#ONLY_CHECKS[@]} -gt 0 ] && ! [[ " ${ONLY_CHECKS[*]} " =~ " ${check_name} " ]]; then
        continue
    fi

    # Skip non-critical if quick mode
    if [ "$QUICK_MODE" = true ] && [ "$check_level" != "critical" ]; then
        continue
    fi

    # Execute check
    $check_func
done
```

**Benefits:**
- Faster iteration (skip known-good checks)
- CI/CD integration (quick mode)
- Targeted troubleshooting

---

### 5. **YAML Validation** (Medium Priority)

**Problem:** Doesn't validate YAML syntax, leading to cryptic errors later

**Solution:**
```bash
validate_yaml_syntax() {
    local file=$1

    # Try parsing with Python (if available)
    if command -v python3 &> /dev/null; then
        python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>&1
        return $?
    elif command -v python &> /dev/null; then
        python -c "import yaml; yaml.safe_load(open('$file'))" 2>&1
        return $?
    else
        write_warn "YAML validation skipped (Python not found)"
        return 0
    fi
}

# Usage in test_config_completeness:
if [ -f "protocol.config.yaml" ]; then
    write_info "Validating YAML syntax..."
    if validate_yaml_syntax "protocol.config.yaml"; then
        write_pass "YAML syntax valid"
    else
        write_fail "Invalid YAML syntax in protocol.config.yaml"
        write_info "Run 'yamllint protocol.config.yaml' for details"
        return 1
    fi
fi
```

**Benefits:**
- Early syntax error detection
- Prevents runtime failures
- Optional (gracefully degrades if Python unavailable)

---

### 6. **Retry Mechanism** (Low Priority)

**Problem:** After fixing errors, must re-run entire script

**Solution:**
```bash
# Add --watch mode that monitors for file changes
#   --watch    Re-run verification when files change

if [ "$WATCH_MODE" = true ]; then
    while true; do
        clear
        run_all_checks

        echo ""
        echo -e "${COLOR_INFO}Watching for changes... (Ctrl+C to exit)${COLOR_RESET}"

        # Use inotifywait if available, otherwise poll
        if command -v inotifywait &> /dev/null; then
            inotifywait -q -e modify,create protocol/ protocol.config.yaml .protocol-state/
        else
            sleep 5
        fi
    done
fi
```

**Benefits:**
- Faster feedback loop
- Interactive debugging
- Optional feature (doesn't affect normal use)

---

### 7. **JSON Output Mode** (Low Priority)

**Problem:** Can't integrate with CI/CD tools easily

**Solution:**
```bash
# Add --json flag for machine-readable output

if [ "$JSON_OUTPUT" = true ]; then
    cat <<EOF
{
  "version": "1.0",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "summary": {
    "passed": $PASS_COUNT,
    "warnings": $WARNING_COUNT,
    "errors": $ERROR_COUNT,
    "exit_code": $EXIT_CODE
  },
  "checks": [
    {
      "name": "file_existence",
      "status": "passed",
      "details": []
    },
    {
      "name": "config_completeness",
      "status": "failed",
      "details": [
        {
          "type": "error",
          "message": "Configuration contains placeholder values",
          "placeholders": ["Your Name", "email@example.com"]
        }
      ]
    }
  ]
}
EOF
fi
```

**Benefits:**
- CI/CD integration
- Automated testing
- Programmatic parsing

---

## Implementation Plan

### Phase 1: Critical Improvements (1-2 hours)
1. ✅ Add dependency checking
2. ✅ Implement graceful degradation
3. ✅ Enhance error messages with context

### Phase 2: Usability Improvements (1 hour)
4. ✅ Add selective check execution (--skip, --only, --quick)
5. ✅ Implement YAML validation

### Phase 3: Advanced Features (1 hour, optional)
6. ⚠️ Add retry/watch mechanism (optional)
7. ⚠️ Implement JSON output mode (optional)

---

## Backward Compatibility

All enhancements are backward-compatible:
- Default behavior unchanged
- New features opt-in via flags
- Existing scripts continue to work
- Exit codes remain compatible (0/1/2)

---

## Testing Plan

### Test Cases

1. **Missing Dependencies**
   - Remove `grep` from PATH
   - Expected: Exit code 3, clear error message

2. **Missing Critical Files**
   - Delete `protocol/CLAUDE.md`
   - Expected: Error with impact and suggestion

3. **Invalid YAML**
   - Introduce syntax error in `protocol.config.yaml`
   - Expected: YAML validation failure with line number

4. **Selective Execution**
   - Run `--only=files`
   - Expected: Only file existence check runs

5. **Quick Mode**
   - Run `--quick`
   - Expected: Only critical checks run

6. **JSON Output**
   - Run `--json`
   - Expected: Valid JSON output

---

## Documentation Updates

### README.md Troubleshooting Section
Add new section: "Using Verification Script Options"

### PROTOCOL_QUICKSTART.md
Update verification step with new flags

### FAQ.md
Add Q&A about verification script options

---

## Success Criteria

1. ✅ All existing tests pass
2. ✅ New dependency check catches missing tools
3. ✅ Error messages include impact + action
4. ✅ Selective execution works (--skip, --only, --quick)
5. ✅ YAML validation detects syntax errors
6. ✅ Backward compatible (existing usage unchanged)
7. ✅ Cross-platform (bash + PowerShell)

---

## Estimated Impact

### User Experience
- **50% faster debugging** - Selective checks + watch mode
- **70% fewer support questions** - Better error messages
- **100% CI/CD compatible** - JSON output mode

### Code Quality
- **Fewer false positives** - Dependency checking
- **Earlier error detection** - YAML validation
- **More maintainable** - Modular check system

---

## Next Steps

1. Implement Phase 1 (critical improvements)
2. Test on both Bash and PowerShell
3. Update documentation
4. Create v6.2.6 release
5. (Optional) Implement Phase 2 & 3 for v6.3.0

---

**Design Status:** ✅ Complete
**Ready for Implementation:** Yes
**Estimated Total Time:** 2-4 hours (Phase 1+2), 3-5 hours (all phases)
