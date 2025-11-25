#!/bin/bash
# Domain Zero Protocol - File Structure Verification Script
# Version: 1.0.0
# Protocol Version: 8.3.1
# Created: 2025-11-25
#
# This script verifies that all protected files exist in the repository.
# Run this before every commit to prevent file loss.

set -e

echo "=========================================="
echo "Domain Zero Protocol - File Structure Check"
echo "Protocol Version: 8.3.1"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check if file exists
check_file() {
    local file=$1
    local level=$2  # CRITICAL or PROTECTED

    if [ -f "$file" ]; then
        echo -e "${GREEN}[OK]${NC} $file"
    else
        if [ "$level" = "CRITICAL" ]; then
            echo -e "${RED}[CRITICAL MISSING]${NC} $file"
            ((ERRORS++))
        else
            echo -e "${YELLOW}[MISSING]${NC} $file"
            ((WARNINGS++))
        fi
    fi
}

# Function to check if directory exists
check_dir() {
    local dir=$1

    if [ -d "$dir" ]; then
        echo -e "${GREEN}[OK]${NC} $dir/"
    else
        echo -e "${RED}[MISSING DIR]${NC} $dir/"
        ((ERRORS++))
    fi
}

echo "Checking CRITICAL files..."
echo "-------------------------"
check_file "protocol/CLAUDE.md" "CRITICAL"
check_file "protocol/yuuji.agent.md" "CRITICAL"
check_file "protocol/megumi.agent.md" "CRITICAL"
check_file "protocol/nobara.agent.md" "CRITICAL"
check_file "protocol/gojo.agent.md" "CRITICAL"
check_file "protocol.config.yaml" "CRITICAL"
check_file ".protocol-state/project-state.json" "CRITICAL"
check_file "FILE_STRUCTURE_PROTECTION.md" "CRITICAL"

echo ""
echo "Checking PROTECTED files..."
echo "---------------------------"

# Root files
check_file "README.md" "PROTECTED"
check_file "CHANGELOG.md" "PROTECTED"
check_file "VERSION.md" "PROTECTED"
check_file "SECURITY.md" "PROTECTED"
check_file "FAQ.md" "PROTECTED"
check_file "CODEOWNERS" "PROTECTED"
check_file "AGENT_BINDING_OATH.md" "PROTECTED"
check_file "DECISION_REASONING_TEMPLATE.md" "PROTECTED"
check_file "IMPLEMENTATION_GUIDE.md" "PROTECTED"
check_file "PROTOCOL_QUICKSTART.md" "PROTECTED"
check_file "REALITY_CHECK.md" "PROTECTED"

# Protocol files
check_file "protocol/HANDOFF_SPECIFICATION.md" "PROTECTED"
check_file "protocol/MCP_INTEGRATION.md" "PROTECTED"
check_file "protocol/ENVIRONMENT_TARGETING.md" "PROTECTED"
check_file "protocol/RESEARCH_MODE.md" "PROTECTED"
check_file "protocol/MASK_MODE.md" "PROTECTED"
check_file "protocol/MODE_INDICATORS.md" "PROTECTED"
check_file "protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md" "PROTECTED"
check_file "protocol/CANONICAL_SOURCE_ADOPTION.md" "PROTECTED"
check_file "protocol/TIER-SELECTION-GUIDE.md" "PROTECTED"

# Protocol state files
check_file ".protocol-state/dev-notes.md" "PROTECTED"
check_file ".protocol-state/security-review.md" "PROTECTED"
check_file ".protocol-state/tier-system-specification.md" "PROTECTED"
check_file ".protocol-state/work-session-alert.template.md" "PROTECTED"

# Domain Zero Agents
check_file "Domain Zero Agents/README.md" "PROTECTED"
check_file "Domain Zero Agents/AGENT_TEMPLATE.md" "PROTECTED"
check_file "Domain Zero Agents/examples/KIRA_DOCUMENTATION_SPECIALIST.md" "PROTECTED"

# Skills
check_file "protocol/skills/AGENT_SKILLS_MAP.yaml" "PROTECTED"
check_file "protocol/skills/SKILL_REGISTRY.md" "PROTECTED"
check_file "protocol/skills/skill-builder.md" "PROTECTED"

# MCP Servers
check_file "protocol/mcp-servers/package.json" "PROTECTED"
check_file "protocol/mcp-servers/handoff-server.js" "PROTECTED"

# Docs
check_file "docs/INSTRUCTION_CONFIRMATION_PROTOCOL.md" "PROTECTED"

echo ""
echo "Checking directories..."
echo "----------------------"
check_dir "protocol"
check_dir "protocol/skills"
check_dir "protocol/mcp-servers"
check_dir ".protocol-state"
check_dir ".protocol-state/research"
check_dir "Domain Zero Agents"
check_dir "Domain Zero Agents/examples"
check_dir "scripts"
check_dir "docs"

echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo -e "Critical Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo -e "${RED}FILE STRUCTURE CHECK FAILED${NC}"
    echo "Critical files are missing. DO NOT COMMIT until resolved."
    echo ""
    echo "To recover missing files:"
    echo "  git fetch new-repo main"
    echo "  git checkout new-repo/main -- <path/to/missing/file>"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}FILE STRUCTURE CHECK PASSED WITH WARNINGS${NC}"
    echo "Some protected files are missing. Consider recovering them."
    exit 0
fi

echo ""
echo -e "${GREEN}FILE STRUCTURE CHECK PASSED${NC}"
echo "All protected files are present."
exit 0
