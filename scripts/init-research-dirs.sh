#!/bin/bash
# Domain Zero Protocol - Research Directory Initializer (Bash)
# Version: 1.0.0
#
# Purpose: Properly create the research directory structure with correct path separators
# This script fixes the common issue where directories are created with missing separators
# (e.g., ".protocol-stateresearchgojo" instead of ".protocol-state/research/gojo/")
#
# Usage:
#   ./init-research-dirs.sh           # Create directories
#   ./init-research-dirs.sh --clean   # Remove malformed directories first
#   ./init-research-dirs.sh --verify  # Only verify structure, don't create

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
CLEAN=false
VERIFY=false
BASE_PATH="."

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean|-c)
            CLEAN=true
            shift
            ;;
        --verify|-v)
            VERIFY=true
            shift
            ;;
        --path|-p)
            BASE_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--clean] [--verify] [--path <directory>]"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Domain Zero Protocol - Research Directory Initializer${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Directory structure
PROTOCOL_STATE_DIR="${BASE_PATH}/.protocol-state"
RESEARCH_DIR="${PROTOCOL_STATE_DIR}/research"
AGENTS=("yuuji" "megumi" "nobara" "gojo")

# Function to find malformed directories
find_malformed() {
    local malformed=()

    # Check for common malformed patterns
    for pattern in ".protocol-stateresearch"* ".protocolstateresearch"* ".protocol-state research"*; do
        if compgen -G "${BASE_PATH}/${pattern}" > /dev/null 2>&1; then
            for dir in ${BASE_PATH}/${pattern}; do
                if [ -d "$dir" ]; then
                    malformed+=("$dir")
                fi
            done
        fi
    done

    # Check for agent-specific malformed paths
    for agent in "${AGENTS[@]}"; do
        for bad_path in ".protocol-stateresearch${agent}" ".protocolstateresearch${agent}"; do
            if [ -d "${BASE_PATH}/${bad_path}" ]; then
                malformed+=("${BASE_PATH}/${bad_path}")
            fi
        done
    done

    printf '%s\n' "${malformed[@]}" | sort -u
}

# Function to verify structure
verify_structure() {
    local issues=()

    # Check .protocol-state
    if [ ! -d "$PROTOCOL_STATE_DIR" ]; then
        issues+=("Missing: .protocol-state/")
    fi

    # Check research directory
    if [ ! -d "$RESEARCH_DIR" ]; then
        issues+=("Missing: .protocol-state/research/")
    fi

    # Check agent directories
    for agent in "${AGENTS[@]}"; do
        if [ ! -d "${RESEARCH_DIR}/${agent}" ]; then
            issues+=("Missing: .protocol-state/research/${agent}/")
        fi
    done

    # Check research-index.json
    if [ ! -f "${RESEARCH_DIR}/research-index.json" ]; then
        issues+=("Missing: .protocol-state/research/research-index.json")
    fi

    # Check README.md
    if [ ! -f "${RESEARCH_DIR}/README.md" ]; then
        issues+=("Missing: .protocol-state/research/README.md")
    fi

    printf '%s\n' "${issues[@]}"
}

# Step 1: Check for malformed directories
echo -e "${BLUE}Step 1: Checking for malformed directories...${NC}"
mapfile -t malformed < <(find_malformed)

if [ ${#malformed[@]} -gt 0 ]; then
    echo -e "${YELLOW}[!] Found ${#malformed[@]} malformed directory(s):${NC}"
    for dir in "${malformed[@]}"; do
        echo -e "    ${RED}${dir}${NC}"
    done
    echo ""

    if [ "$CLEAN" = true ]; then
        echo -e "${YELLOW}Cleaning malformed directories...${NC}"
        for dir in "${malformed[@]}"; do
            if rm -rf "$dir" 2>/dev/null; then
                echo -e "  ${GREEN}[REMOVED]${NC} $dir"
            else
                echo -e "  ${RED}[FAILED]${NC} Could not remove: $dir"
            fi
        done
        echo ""
    else
        echo -e "${YELLOW}Use --clean flag to remove these directories${NC}"
        echo ""
    fi
else
    echo -e "  ${GREEN}[OK]${NC} No malformed directories found"
    echo ""
fi

# Step 2: Verify current structure
echo -e "${BLUE}Step 2: Verifying directory structure...${NC}"
mapfile -t issues < <(verify_structure)

if [ ${#issues[@]} -gt 0 ]; then
    echo -e "${YELLOW}[!] Found ${#issues[@]} issue(s):${NC}"
    for issue in "${issues[@]}"; do
        echo -e "    ${YELLOW}${issue}${NC}"
    done
    echo ""
else
    echo -e "  ${GREEN}[OK]${NC} Directory structure is correct"
    echo ""
fi

# Exit if verify-only mode
if [ "$VERIFY" = true ]; then
    echo -e "${BLUE}Verify mode - no changes made${NC}"
    if [ ${#issues[@]} -eq 0 ] && [ ${#malformed[@]} -eq 0 ]; then
        echo -e "${GREEN}Research directory structure is correct!${NC}"
        exit 0
    else
        echo -e "${YELLOW}Issues found. Run without --verify to fix.${NC}"
        exit 1
    fi
fi

# Step 3: Create correct directory structure
echo -e "${BLUE}Step 3: Creating correct directory structure...${NC}"

# Create .protocol-state
if [ ! -d "$PROTOCOL_STATE_DIR" ]; then
    mkdir -p "$PROTOCOL_STATE_DIR"
    echo -e "  ${GREEN}[CREATED]${NC} .protocol-state/"
fi

# Create research directory
if [ ! -d "$RESEARCH_DIR" ]; then
    mkdir -p "$RESEARCH_DIR"
    echo -e "  ${GREEN}[CREATED]${NC} .protocol-state/research/"
fi

# Create agent subdirectories
for agent in "${AGENTS[@]}"; do
    agent_dir="${RESEARCH_DIR}/${agent}"
    if [ ! -d "$agent_dir" ]; then
        mkdir -p "$agent_dir"
        echo -e "  ${GREEN}[CREATED]${NC} .protocol-state/research/${agent}/"
    else
        echo -e "  ${BLUE}[EXISTS]${NC} .protocol-state/research/${agent}/"
    fi
done

# Create research-index.json if missing
index_file="${RESEARCH_DIR}/research-index.json"
if [ ! -f "$index_file" ]; then
    current_date=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    cat > "$index_file" << EOF
{
  "version": "1.0",
  "created": "${current_date}",
  "agents": {
    "yuuji": {
      "last_session": null,
      "session_count": 0,
      "topics": []
    },
    "megumi": {
      "last_session": null,
      "session_count": 0,
      "topics": []
    },
    "nobara": {
      "last_session": null,
      "session_count": 0,
      "topics": []
    },
    "gojo": {
      "last_session": null,
      "session_count": 0,
      "topics": []
    }
  }
}
EOF
    echo -e "  ${GREEN}[CREATED]${NC} .protocol-state/research/research-index.json"
fi

# Create README.md if missing
readme_file="${RESEARCH_DIR}/README.md"
if [ ! -f "$readme_file" ]; then
    cat > "$readme_file" << 'EOF'
# Domain Zero Protocol - Research Directory

This directory contains research session outputs from Domain Zero agents.

## Structure

```
.protocol-state/research/
├── research-index.json       # Global index tracking all research sessions
├── yuuji/                    # Yuuji (Implementation) research outputs
├── megumi/                   # Megumi (Security) research outputs
├── nobara/                   # Nobara (Creative Strategy/UX) research outputs
├── gojo/                     # Gojo (Mission Control) research outputs
└── README.md                 # This file
```

## File Naming Convention

- Summaries: `{timestamp}.summary.md` (version controlled)
- Raw notes: `{timestamp}.raw.log` (gitignored for privacy)

## Usage

Invoke research mode with any agent:
- `Read yuuji.agent.md --research and investigate [topic]`
- `Read megumi.agent.md --research and investigate [topic]`
- `Read nobara.agent.md --research and investigate [topic]`
- `Read gojo.agent.md --research and investigate [topic]`

## Privacy

Raw research notes (.raw.log files) are gitignored by default to protect privacy.
Only curated summaries (.summary.md) are tracked in version control.
EOF
    echo -e "  ${GREEN}[CREATED]${NC} .protocol-state/research/README.md"
fi

echo ""

# Final verification
echo -e "${BLUE}Step 4: Final verification...${NC}"
mapfile -t final_issues < <(verify_structure)

if [ ${#final_issues[@]} -eq 0 ]; then
    echo -e "  ${GREEN}[OK]${NC} All directories created successfully!"
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  Research directory structure is ready!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo "Directory structure:"
    echo "  .protocol-state/"
    echo "  └── research/"
    echo "      ├── research-index.json"
    echo "      ├── README.md"
    echo "      ├── yuuji/"
    echo "      ├── megumi/"
    echo "      ├── nobara/"
    echo "      └── gojo/"
    echo ""
    exit 0
else
    echo -e "${RED}[ERROR]${NC} Some issues remain:"
    for issue in "${final_issues[@]}"; do
        echo -e "    ${RED}${issue}${NC}"
    done
    exit 1
fi
