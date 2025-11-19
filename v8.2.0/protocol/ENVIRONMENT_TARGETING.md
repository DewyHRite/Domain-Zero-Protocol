# Environment Targeting Guide
## Target Field Specification for .agent.md Format

**Version**: 1.0.0
**Created**: November 18, 2025
**Status**: Production-Ready
**Purpose**: Configure Domain Zero agents for specific AI assistant environments

---

## Table of Contents

- [Overview](#overview)
- [Target Field Specification](#target-field-specification)
- [VS Code Target](#vs-code-target)
- [GitHub Copilot Target](#github-copilot-target)
- [Multi-Target Support](#multi-target-support)
- [Feature Comparison](#feature-comparison)
- [Migration Guide](#migration-guide)
- [Best Practices](#best-practices)

---

## Overview

The **`target` field** in .agent.md YAML frontmatter specifies which AI assistant environment the agent is optimized for. This enables environment-specific features while maintaining cross-platform compatibility.

**Supported Targets**:
- `vscode`: Claude Code, VS Code extensions (full feature set)
- `github`: GitHub Copilot (limited feature set with constraints)

**Key Principle**: Agents should be **target-aware** but **functionally consistent** - core behavior remains the same, but advanced features may be environment-specific.

---

## Target Field Specification

### YAML Frontmatter Format

```yaml
---
target: vscode | github
name: "Agent Name"
description: "Agent description"
# ... other fields
---
```

### Field Definition

| Property | Type | Required | Values | Default |
|----------|------|----------|--------|---------|
| `target` | string | ✅ Yes | `vscode`, `github` | N/A |

### Examples

**VS Code Agent**:
```yaml
---
target: vscode
name: "Yuuji Itadori - Implementation Specialist"
description: "Test-first development with full MCP integration"
# ... MCP-enabled features available
---
```

**GitHub Copilot Agent**:
```yaml
---
target: github
name: "Yuuji Itadori - Implementation Specialist"
description: "Test-first development (GitHub Copilot compatible)"
# ... Limited to GitHub Copilot capabilities
---
```

---

## VS Code Target

### Overview

**Target**: `vscode`

**Environments**:
- Claude Code (Desktop app)
- VS Code with Claude extension
- Any VS Code-compatible AI assistant

**Full Feature Set**: All Domain Zero Protocol capabilities supported

### Capabilities

#### 1. **MCP Integration** ✅

VS Code target supports full Model Context Protocol integration:

```yaml
---
target: vscode
# ...
---

# MCP servers configured in:
# - ~/.config/claude-code/mcp.json
# - .claude-code/mcp.json

# Agent can use:
# - Built-in tools (Read, Write, Edit, Bash, etc.)
# - MCP tools from connected servers (database queries, API calls, etc.)
# - MCP resources (documentation, knowledge bases, etc.)
```

**Example**: Yuuji with database MCP server
```markdown
User: "Yuuji, implement user profile endpoint"

Yuuji (vscode target):
1. Calls database MCP server: list_tables()
2. Gets "users" table schema via MCP
3. Implements endpoint with correct fields
4. MCP integration seamless!
```

#### 2. **Advanced Handoffs** ✅

VS Code target supports rich agent-to-agent handoffs:

```yaml
handoffs:
  - agent: megumi
    trigger: "@security-review"
    context:
      - files_modified
      - tier_level
      - implementation_scope
      - test_coverage
      - mcp_data_sources  # MCP context can be passed!
```

**Benefit**: Full context including MCP-sourced data passes between agents

#### 3. **Tool Access Matrix** ✅

VS Code target has full tool access:

```yaml
tools:
  - read
  - write
  - edit
  - bash
  - grep
  - glob
  - todowrite
  - task
  - webfetch
  - websearch
```

**All tools available** without restrictions.

#### 4. **Real-Time State Management** ✅

VS Code target can maintain persistent state:

```markdown
- .protocol-state/project-state.json (read/write)
- .protocol-state/dev-notes.md (append/modify)
- .protocol-state/security-review.md (update)
- .protocol-state/trigger-19.md (passive monitoring)
```

#### 5. **Interactive Workflows** ✅

VS Code target supports interactive user prompts:

```markdown
User invokes Gojo:
┌────────────────────────────────────────┐
│  SELECT OPERATIONAL MODE:              │
│  [1] Resume Current Project            │
│  [2] New Project Initialization        │
│  [3] Trigger 19 Intelligence Report    │
└────────────────────────────────────────┘

User selects option → Gojo proceeds accordingly
```

### Configuration Example

**Complete VS Code agent** (yuuji.agent.md):
```yaml
---
target: vscode
name: "Yuuji Itadori - Implementation Specialist"
description: "Test-first development, MCP-enabled"
argument-hint: "Use: 'Read yuuji.agent.md and implement [feature]'"
model: "claude-3-5-sonnet-20241022"

tools:
  - read
  - write
  - edit
  - bash
  - grep
  - glob
  - todowrite
  - task
  - webfetch
  - websearch

handoffs:
  - agent: megumi
    trigger: "@security-review"
    context:
      - files_modified
      - tier_level
      - implementation_scope
      - test_coverage
---
```

---

## GitHub Copilot Target

### Overview

**Target**: `github`

**Environments**:
- GitHub Copilot Chat
- GitHub Copilot in VS Code (via chat interface)
- GitHub Copilot X

**Limited Feature Set**: Subset of Domain Zero Protocol capabilities due to GitHub Copilot constraints

### Constraints

#### 1. **No MCP Integration** ❌

GitHub Copilot does NOT support Model Context Protocol:

```yaml
---
target: github
# ...
# MCP servers ignored - GitHub Copilot cannot connect to MCP servers
---
```

**Impact**: Agents cannot access external data sources via MCP

**Workaround**: Use built-in tools only (Read, Write, etc.) or provide data manually

#### 2. **Limited Tool Access** ⚠️

GitHub Copilot has restricted tool set:

```yaml
tools:
  - read        # ✅ Available
  - write       # ✅ Available (limited)
  - edit        # ✅ Available (limited)
  - bash        # ⚠️ Restricted (read-only commands only)
  - grep        # ✅ Available
  - glob        # ✅ Available
  - todowrite   # ❌ Not available
  - task        # ❌ Not available
  - webfetch    # ⚠️ Limited
  - websearch   # ⚠️ Limited
```

**Restrictions**:
- Bash: Cannot execute write operations or destructive commands
- TodoWrite: Not supported (no persistent state management)
- Task: Cannot spawn sub-agents
- WebFetch/WebSearch: Rate-limited and may require authentication

#### 3. **No Persistent State** ❌

GitHub Copilot cannot maintain `.protocol-state/` files:

```markdown
❌ Cannot update project-state.json
❌ Cannot append to dev-notes.md
❌ Cannot track passive observations
❌ No Trigger 19 intelligence reports
```

**Impact**: Agent behavior is stateless - no memory across sessions

#### 4. **Simplified Handoffs** ⚠️

GitHub Copilot handoffs are manual:

```yaml
handoffs:
  - agent: megumi
    trigger: "@security-review"
    context:
      - files_modified  # User must provide manually
      - tier_level
```

**Workflow**:
1. User invokes Yuuji for implementation
2. Yuuji tags @security-review
3. **User manually extracts context** (file list, tier level)
4. User invokes Megumi with context as prompt
5. Megumi performs review

**vs. VS Code target** (automated handoff orchestration via Gojo)

### Configuration Example

**GitHub Copilot agent** (yuuji.agent.md):
```yaml
---
target: github
name: "Yuuji Itadori - Implementation Specialist"
description: "Test-first development (GitHub Copilot compatible)"
argument-hint: "Use: '@yuuji implement [feature]'"
model: "gpt-4"  # GitHub Copilot uses GPT-4

tools:
  - read
  - write
  - edit
  - bash  # Limited to safe commands
  - grep
  - glob

handoffs:
  - agent: megumi
    trigger: "@security-review"
    context:
      - files_modified
      - tier_level
      - implementation_scope
# Note: Context transfer is manual in GitHub Copilot
---
```

### Invocation Differences

**VS Code**:
```markdown
User: "Read yuuji.agent.md and implement user authentication"
```

**GitHub Copilot**:
```markdown
User: "@yuuji implement user authentication"
# or
User: "#yuuji implement user authentication"
# or via Copilot Chat UI
```

---

## Multi-Target Support

### Dual-Target Agents

Agents can be configured for multiple targets by creating variants:

**Project Structure**:
```
protocol/
├── yuuji.agent.md           # VS Code version (full features)
├── yuuji.copilot.agent.md   # GitHub Copilot version (limited features)
├── megumi.agent.md
├── megumi.copilot.agent.md
├── nobara.agent.md
├── nobara.copilot.agent.md
├── gojo.agent.md
└── gojo.copilot.agent.md    # Gojo has minimal copilot support
```

**Target Selection**:
```yaml
# protocol/yuuji.agent.md (VS Code)
---
target: vscode
# ... full feature set
---

# protocol/yuuji.copilot.agent.md (GitHub Copilot)
---
target: github
# ... limited feature set
---
```

**Usage**:
- **VS Code users**: Use `yuuji.agent.md`
- **GitHub Copilot users**: Use `yuuji.copilot.agent.md`

### Feature Parity Matrix

| Feature | VS Code | GitHub Copilot |
|---------|---------|----------------|
| **Read files** | ✅ Full | ✅ Full |
| **Write files** | ✅ Full | ⚠️ Limited |
| **Edit files** | ✅ Full | ⚠️ Limited |
| **Bash commands** | ✅ Full | ⚠️ Read-only |
| **MCP integration** | ✅ Yes | ❌ No |
| **Agent handoffs** | ✅ Automated | ⚠️ Manual |
| **Persistent state** | ✅ Yes (.protocol-state/) | ❌ No |
| **Trigger 19 reports** | ✅ Yes | ❌ No |
| **Tool access** | ✅ All tools | ⚠️ Subset |
| **Passive monitoring** | ✅ Yes | ❌ No |

---

## Migration Guide

### From GitHub Copilot to VS Code

**Scenario**: User starts with GitHub Copilot, wants to migrate to VS Code for full features

**Steps**:

1. **Install Claude Code**:
   ```bash
   # Download from https://claude.ai/code
   # Or install VS Code extension
   ```

2. **Copy Agent Files**:
   ```bash
   # If using .copilot.agent.md variants:
   cp protocol/yuuji.copilot.agent.md protocol/yuuji.agent.md
   cp protocol/megumi.copilot.agent.md protocol/megumi.agent.md
   cp protocol/nobara.copilot.agent.md protocol/nobara.agent.md
   cp protocol/gojo.copilot.agent.md protocol/gojo.agent.md
   ```

3. **Update `target` field**:
   ```yaml
   # Change from:
   target: github

   # To:
   target: vscode
   ```

4. **Enable Full Feature Set**:
   ```yaml
   tools:
     # Add previously unavailable tools:
     - todowrite
     - task
     - webfetch
     - websearch
   ```

5. **Configure MCP Servers** (optional):
   ```bash
   # Create MCP configuration
   mkdir -p ~/.config/claude-code
   cat > ~/.config/claude-code/mcp.json <<EOF
   {
     "mcpServers": {
       "database": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-postgres"],
         "env": {
           "POSTGRES_CONNECTION_STRING": "postgresql://localhost:5432/mydb"
         }
       }
     }
   }
   EOF
   ```

6. **Initialize State Management**:
   ```bash
   # Create .protocol-state directory
   mkdir -p .protocol-state

   # Initialize state files (Gojo will create these on first run)
   ```

7. **Test Migration**:
   ```markdown
   # Invoke agent in VS Code
   "Read yuuji.agent.md and implement test feature"

   # Verify:
   # ✅ All tools work
   # ✅ MCP integration (if configured)
   # ✅ State files created (.protocol-state/)
   # ✅ Handoffs work correctly
   ```

### From VS Code to GitHub Copilot

**Scenario**: User wants to use Domain Zero in GitHub Copilot (e.g., GitHub Codespaces)

**Steps**:

1. **Create Copilot Variants**:
   ```bash
   # Copy and rename agent files
   cp protocol/yuuji.agent.md protocol/yuuji.copilot.agent.md
   cp protocol/megumi.agent.md protocol/megumi.copilot.agent.md
   cp protocol/nobara.agent.md protocol/nobara.copilot.agent.md
   cp protocol/gojo.agent.md protocol/gojo.copilot.agent.md
   ```

2. **Update `target` field**:
   ```yaml
   # In all .copilot.agent.md files:
   target: github
   ```

3. **Remove Unsupported Tools**:
   ```yaml
   tools:
     - read
     - write
     - edit
     - bash  # Limited
     - grep
     - glob
     # Remove:
     # - todowrite
     # - task
     # - webfetch (or mark as limited)
     # - websearch (or mark as limited)
   ```

4. **Simplify Handoffs**:
   ```yaml
   # Add note in handoffs section:
   # Note: Handoffs are manual in GitHub Copilot
   # User must provide context explicitly
   ```

5. **Document Limitations**:
   ```markdown
   # In agent file header, add:
   **GitHub Copilot Limitations**:
   - No MCP integration
   - No persistent state (.protocol-state/)
   - Manual context transfer for handoffs
   - Limited bash commands (read-only)
   ```

6. **Test in GitHub Copilot**:
   ```markdown
   # Invoke via Copilot Chat
   @yuuji implement test feature

   # Verify:
   # ✅ Basic tools work
   # ✅ Agent follows protocol
   # ⚠️ Manual handoff required
   # ⚠️ No state persistence
   ```

---

## Best Practices

### 1. **Target-Specific Documentation**

**Add target-specific notes** in agent file headers:

```yaml
---
target: vscode
# ...
---

# VS Code Features
This agent supports:
- ✅ Full MCP integration
- ✅ Automated handoffs via Gojo
- ✅ Persistent state management
- ✅ All tool access

# Not compatible with GitHub Copilot (use yuuji.copilot.agent.md)
```

### 2. **Graceful Degradation**

**Design agents to work in both environments** when possible:

```markdown
## MCP Data Sources (VS Code only)

When running in VS Code with MCP configured, I can:
- Query project database directly
- Fetch API documentation
- Access external knowledge bases

When running in GitHub Copilot:
- I'll request this information from you directly
- Provide database schema, API docs, etc. in your prompt
```

### 3. **Clear Invocation Patterns**

**Document both invocation methods**:

```markdown
## Invocation

**VS Code / Claude Code**:
Read yuuji.agent.md and implement [feature]

**GitHub Copilot**:
@yuuji implement [feature]
```

### 4. **Test Both Targets**

**If maintaining dual-target agents**, test in both environments:

```bash
# Test VS Code version
code .
# Invoke: "Read yuuji.agent.md and implement test"

# Test GitHub Copilot version
# Open in GitHub Codespaces or local VS Code with Copilot
# Invoke: "@yuuji implement test"
```

### 5. **Document Migration Path**

**In README.md**, document how to switch between targets:

```markdown
## Environment Support

Domain Zero Protocol supports:
- **VS Code / Claude Code**: Full feature set (recommended)
- **GitHub Copilot**: Limited feature set (MCP not supported)

### Using with VS Code
Use `.agent.md` files in `protocol/` directory

### Using with GitHub Copilot
Use `.copilot.agent.md` files in `protocol/` directory

See ENVIRONMENT_TARGETING.md for details.
```

---

## Appendix: Target Detection

### Automatic Target Detection

Agents can detect their environment at runtime (in future versions):

```yaml
---
target: auto  # Detect environment automatically
# ...
---
```

**Detection Logic**:
```javascript
// Pseudo-code
if (environment === "claude-code" || environment === "vscode") {
  target = "vscode";
  enableMCP();
  enableFullToolset();
} else if (environment === "github-copilot") {
  target = "github";
  disableMCP();
  limitToolset();
}
```

**Status**: Proposed for v8.1.0 (not yet implemented)

---

## Version History

- **1.0.0** (2025-11-18): Initial environment targeting guide for v8.0.0

---

**END OF ENVIRONMENT_TARGETING.md**
