<!-- [CORE FILE] - Domain Zero Protocol v8.5.1 -->
# MCP Server Setup Guide
## Domain Zero Protocol MCP Server Implementation

**Version**: 1.0.0
**Protocol Version**: 8.5.1
**Last Updated**: November 27, 2025
**Purpose**: Set up the Domain Zero Protocol MCP server for token-optimized agent operations

---

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Server Architecture](#server-architecture)
- [Tool Registry](#tool-registry)
- [Token Usage Impact](#token-usage-impact)
- [Installation](#installation)
- [Configuration](#configuration)
- [Key Design Decisions](#key-design-decisions)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Domain Zero Protocol MCP Server provides optimized access to protocol files, agent information, and project state through the Model Context Protocol. This reduces token usage by 70-90% compared to direct file operations.

**Key Benefits**:
- Atomic state updates without full file reads
- Structured responses instead of raw file content
- Search results limited to relevant matches
- Pre-approved tools for common operations

---

## Directory Structure

```text
project-root/
├── .mcp.json                          # MCP server configuration
├── protocol.config.yaml               # Protocol settings
├── protocol/                          # Agent protocol files
│   ├── CLAUDE.md
│   ├── yuuji.agent.md
│   ├── megumi.agent.md
│   ├── nobara.agent.md
│   └── gojo.agent.md
└── .protocol-state/                   # State directory
    ├── mcp/
    │   ├── dzp_server.py        # MCP server source (637 lines)
    │   └── __pycache__/               # Compiled Python
    ├── project-state.json             # Central state file
    ├── dev-notes.md                   # Development notes
    ├── security-review.md             # Security findings
    ├── trigger-19.md                  # Intelligence report
    └── ...                            # Other state files
```

---

## Server Architecture

**File**: `.protocol-state/mcp/dzp_server.py`

| Component | Description |
|-----------|-------------|
| **Framework** | `mcp.server` (Model Context Protocol SDK) |
| **Transport** | `stdio_server` (stdin/stdout communication) |
| **Config** | Hardcoded paths to PROTOCOL_ROOT, PROTOCOL_DIR, STATE_DIR |

### Initialization Flow

```text
Claude Code starts → reads .mcp.json → spawns `python dzp_server.py`
                                                ↓
                                        Server registers 13 tools
                                                ↓
                                        Awaits tool calls via stdio
```

---

## Tool Registry

The MCP server exposes 13 tools across 4 categories:

### Protocol Tools

| Tool | Purpose |
|------|---------|
| `dzp_read_protocol` | Read specific .md file from protocol/ |
| `dzp_search_protocol` | Grep across all protocol files |
| `dzp_list_files` | List all DZP files |

### Agent Tools

| Tool | Purpose |
|------|---------|
| `dzp_invoke_agent` | Generate invocation command for agent |
| `dzp_agent_info` | Get agent capabilities summary |

### State Tools

| Tool | Purpose |
|------|---------|
| `dzp_get_state` | Read project-state.json |
| `dzp_update_state` | Atomic field update (dot notation) |
| `dzp_read_dev_notes` | Read dev-notes.md |
| `dzp_read_security_review` | Read security-review.md |
| `dzp_read_trigger_19` | Read trigger-19.md (intelligence) |

### Meta Tools

| Tool | Purpose |
|------|---------|
| `dzp_list_subprojects` | List tracked subprojects |
| `dzp_protocol_version` | Get version/status summary |

---

## Token Usage Impact

### Without MCP (Traditional Approach)

| Operation | Token Cost |
|-----------|------------|
| `Read(project-state.json)` | ~2000 tokens (139 lines raw JSON) |
| `Read(yuuji.agent.md)` | ~3500 tokens (full file) |
| Grep + Glob to search | Multiple tool calls + full results |
| `Edit(project-state.json)` | Read → Parse → Modify → Write entire file |

### With MCP (Optimized)

| Operation | Token Cost |
|-----------|------------|
| `dzp_get_state()` | ~400 tokens (formatted JSON) |
| `dzp_agent_info("yuuji")` | ~200 tokens (structured summary) |
| `dzp_search_protocol("query")` | ~100 tokens (matching lines only) |
| `dzp_update_state("field")` | ~50 tokens (atomic update) |

### Savings: 70-90% token reduction per operation

---

## Installation

### Prerequisites

- Python 3.10+
- `mcp` Python package
- Claude Code with MCP support

### Step 1: Install MCP SDK

```bash
pip install mcp
```

### Step 2: Create Server Directory

```bash
mkdir -p .protocol-state/mcp
```

### Step 3: Copy Server File

Copy `dzp_server.py` to `.protocol-state/mcp/`:

```bash
cp /path/to/dzp_server.py .protocol-state/mcp/
```

### Step 4: Configure Server Paths

Edit `.protocol-state/mcp/dzp_server.py` and update the path constants:

```python
# Update these paths to match your installation
PROTOCOL_ROOT = Path("/path/to/your/project")
PROTOCOL_DIR = PROTOCOL_ROOT / "protocol"
STATE_DIR = PROTOCOL_ROOT / ".protocol-state"
```

---

## Configuration

### .mcp.json Configuration

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "dzp": {
      "command": "python",
      "args": [".protocol-state/mcp/dzp_server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Claude Code Settings

Ensure MCP is enabled in Claude Code:

1. Open Claude Code settings
2. Enable "MCP Servers" feature
3. Restart Claude Code to load the server

### Pre-Approved Tools

Add these tools to your Claude Code allow list for seamless operation:

```text
dzp_read_protocol
dzp_search_protocol
dzp_list_files
dzp_invoke_agent
dzp_agent_info
dzp_get_state
dzp_update_state
dzp_read_dev_notes
dzp_read_security_review
dzp_read_trigger_19
dzp_list_subprojects
dzp_protocol_version
```

---

## Key Design Decisions

### 1. Stdio Transport
- No network exposure
- Runs as subprocess of Claude Code
- Secure by default

### 2. Hardcoded Paths
- Server is installation-specific
- Not portable between installations
- Requires path configuration per project

### 3. Dot Notation Updates
```python
# Example: Update nested JSON atomically
dzp_update_state("mission_status.yuuji_briefed", "true")
```
- Modifies only the specified field
- No full file read/write cycle
- Atomic operation prevents race conditions

### 4. Search Result Limits
- Returns max 5 matches per file
- Controls response size
- Prevents token explosion on broad queries

### 5. Pre-Approved Tools
- Protocol read operations don't require user confirmation
- State updates are atomic and safe
- Reduces confirmation fatigue

---

## Troubleshooting

### Server Not Starting

**Symptoms**: MCP tools not available in Claude Code

**Solutions**:
1. Check Python is in PATH: `python --version`
2. Verify MCP package installed: `pip show mcp`
3. Check server file exists: `ls .protocol-state/mcp/dzp_server.py`
4. Test server manually: `python .protocol-state/mcp/dzp_server.py`

### Tools Not Found

**Symptoms**: "Tool not available" errors

**Solutions**:
1. Restart Claude Code to reload MCP servers
2. Check `.mcp.json` syntax is valid JSON
3. Verify `cwd` path is correct
4. Check server logs for registration errors

### Path Errors

**Symptoms**: "File not found" when reading protocols

**Solutions**:
1. Verify `PROTOCOL_ROOT` path in server file
2. Check `PROTOCOL_DIR` points to `protocol/` folder
3. Ensure `STATE_DIR` points to `.protocol-state/`
4. Use absolute paths for reliability

### State Update Failures

**Symptoms**: `dzp_update_state` not persisting changes

**Solutions**:
1. Check file permissions on `project-state.json`
2. Verify dot notation syntax is correct
3. Ensure JSON value is properly formatted
4. Check for concurrent write conflicts

---

## Example Usage

### Reading Agent Info

```text
User: "What can Yuuji do?"

Claude Code calls: dzp_agent_info("yuuji")

Response: {
  "name": "Yuuji Itadori",
  "role": "Implementation Specialist",
  "tier_support": ["1", "2", "3"],
  "primary_tools": ["read", "write", "edit", "bash"],
  "handoff_to": ["megumi"]
}
```

### Searching Protocol

```text
User: "Find all references to OWASP"

Claude Code calls: dzp_search_protocol("OWASP")

Response: {
  "matches": [
    {"file": "megumi.agent.md", "line": 45, "text": "OWASP Top 10 review..."},
    {"file": "CLAUDE.md", "line": 234, "text": "...OWASP security standards..."}
  ],
  "total": 2
}
```

### Updating State

```text
User: "Mark feature as complete"

Claude Code calls: dzp_update_state("current_state", "COMPLETE")

Response: {
  "success": true,
  "field": "current_state",
  "old_value": "IN_PROGRESS",
  "new_value": "COMPLETE"
}
```

---

## Version History

- **1.0.0** (2025-11-27): Initial MCP server setup guide for v8.5.1

---

*End of MCP_SERVER_SETUP.md*
