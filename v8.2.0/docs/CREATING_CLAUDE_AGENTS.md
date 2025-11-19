# Creating Claude Agents - Complete Guide

**Domain Zero Protocol v8.2.0**

A comprehensive guide to creating custom Claude agents using the .agent.md format for AI-assisted development workflows.

---

## Table of Contents

- [What Are Claude Agents?](#what-are-claude-agents)
- [Quick Start](#quick-start)
- [Agent File Structure](#agent-file-structure)
- [YAML Frontmatter Reference](#yaml-frontmatter-reference)
- [Tool Access Matrix](#tool-access-matrix)
- [Handoff Mechanisms](#handoff-mechanisms)
- [Step-by-Step Agent Creation](#step-by-step-agent-creation)
- [Best Practices](#best-practices)
- [Testing Your Agent](#testing-your-agent)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

---

## What Are Claude Agents?

Claude agents in Domain Zero Protocol are **specialized AI personas with defined roles, tools, and behaviors**. They are:

- **Structured markdown files** (.agent.md format) with YAML frontmatter
- **Role-specific prompts** that guide Claude's behavior for specific tasks
- **Tool-restricted environments** with explicit access controls
- **Context-aware workflows** with declarative handoff mechanisms

**Key Concept**: Agents are not separate AI models—they're the **same Claude AI reading different instruction files** with specific behavioral constraints.

---

## Quick Start

### 1. Copy the Template

Start with the basic agent template:

```bash
# Copy from the template directory
cp "Domain Zero Agents - Full JJK Edition/JJK_AGENT_TEMPLATE.md" protocol/myagent.agent.md
```

Or create manually:

```yaml
---
target: vscode
name: "Agent Name - Role Description"
description: "Brief description of what this agent does"
argument-hint: "How to invoke this agent"
model: "claude-sonnet-4-5-20250929"

tools:
  - read
  - write
  - edit

handoffs:
  - agent: target_agent
    trigger: "@handoff-keyword"
    context:
      - context_field
---

## 🛠️ TOOL ACCESS MATRIX

| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read all project files |
| **Write** | ✅ Full Access | Create new files |

# Agent Documentation Here
```

### 2. Customize the Agent

Edit the YAML frontmatter and documentation to match your agent's purpose.

### 3. Test the Agent

Invoke your agent:

```bash
"Read protocol/myagent.agent.md and [task description]"
```

---

## Agent File Structure

Every .agent.md file has three main sections:

```text
┌─────────────────────────────────────┐
│ 1. YAML FRONTMATTER                 │  ← Configuration (required)
│    - Metadata                       │
│    - Tool list                      │
│    - Handoff definitions            │
├─────────────────────────────────────┤
│ 2. TOOL ACCESS MATRIX               │  ← Permissions table (required)
│    - Tool-by-tool breakdown         │
│    - Access levels                  │
│    - Usage descriptions             │
├─────────────────────────────────────┤
│ 3. AGENT DOCUMENTATION              │  ← Instructions (required)
│    - Role description               │
│    - Workflow steps                 │
│    - Examples                       │
│    - Protocol rules                 │
└─────────────────────────────────────┘
```

### Minimal Example

```markdown
---
target: vscode
name: "Code Reviewer - Quality Assurance Specialist"
description: "Reviews code for quality, maintainability, and best practices"
argument-hint: "Use: 'review [file/module]'"
model: "claude-sonnet-4-5-20250929"

tools:
  - read
  - grep
  - glob

handoffs:
  - agent: implementation_agent
    trigger: "@needs-refactor"
    context:
      - files_reviewed
      - issues_found
---

## 🛠️ TOOL ACCESS MATRIX

| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read source files for review |
| **Grep** | ✅ Full Access | Search for patterns/anti-patterns |
| **Glob** | ✅ Full Access | Find files by pattern |

## Role

I am a Code Reviewer. I analyze code for:
- Maintainability
- Readability
- Best practices
- Performance issues
- Security concerns (basic - defer to security specialist)

## Workflow

1. Receive files to review
2. Analyze code quality
3. Document findings with line numbers
4. Suggest improvements
5. Tag @needs-refactor if major issues found
```

---

## YAML Frontmatter Reference

### Required Fields

```yaml
target: vscode              # Environment: "vscode" or "github"
name: "Agent Name"          # Full name with role
description: "Brief desc"   # One-line summary
argument-hint: "Usage"      # Invocation example
model: "claude-sonnet-4-5-20250929"  # Stable model snapshot

tools:                      # List of available tools
  - read
  - write

handoffs:                   # Agent-to-agent transitions
  - agent: target_agent
    trigger: "@keyword"
    context:
      - field1
```

### Field Details

#### `target`

Specifies the execution environment:

- **`vscode`**: Full features (MCP, all tools, automated handoffs)
- **`github`**: Limited features (GitHub Copilot compatibility)

**Choose vscode for most agents.**

#### `name`

Full agent name including role. Format: `"[Name] - [Role]"`

**Examples**:
- ✅ `"Alex Chen - DevOps Automation Specialist"`
- ✅ `"Database Optimizer - Performance Tuning Expert"`
- ❌ `"Alex"` (too vague)
- ❌ `"Specialist"` (no context)

#### `description`

Brief one-line summary (max 150 chars).

**Examples**:
- ✅ `"CI/CD pipeline automation, Docker orchestration, and infrastructure monitoring"`
- ✅ `"SQL query optimization, index tuning, and database performance analysis"`
- ❌ `"Does stuff"` (too vague)

#### `argument-hint`

Shows users how to invoke the agent.

**Examples**:
- ✅ `"Use: 'optimize [database]' or 'analyze query [sql]'"`
- ✅ `"Use: 'deploy [service]' or '--env prod [task]'"`

#### `model`

**Always use the stable snapshot**: `claude-sonnet-4-5-20250929`

❌ **Don't use alias**: `claude-sonnet-4-5` (can change behavior)
✅ **Use snapshot**: `claude-sonnet-4-5-20250929` (stable)

**Rationale**: Per Anthropic recommendations, pinned snapshots ensure production stability.

#### `tools`

List of tools this agent can use. Available tools:

**File Operations**:
- `read` - Read files
- `write` - Create files
- `edit` - Modify files
- `glob` - Find files by pattern
- `grep` - Search file contents

**System Operations**:
- `bash` - Execute shell commands
- `todowrite` - Manage task lists

**Advanced**:
- `task` - Spawn sub-agents
- `webfetch` - Fetch web content
- `websearch` - Search the web

**Example**:
```yaml
tools:
  - read      # Always needed for context
  - write     # If agent creates files
  - bash      # If agent runs commands
```

#### `handoffs`

Define agent-to-agent transitions:

```yaml
handoffs:
  - agent: security_reviewer
    trigger: "@security-review"
    context:
      - files_modified
      - implementation_scope
      - tier_level
```

**Fields**:
- `agent`: Target agent filename (without .agent.md)
- `trigger`: Tag/keyword to trigger handoff
- `context`: Data to pass to target agent

---

## Tool Access Matrix

The Tool Access Matrix is a **required table** after the YAML frontmatter showing formalized tool permissions.

### Template

```markdown
## 🛠️ TOOL ACCESS MATRIX

| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read all project files |
| **Write** | ⚠️ Conditional Access | Create files (with backup requirement) |
| **Bash** | ✅ Full Access | Execute commands, run tests |
| **Edit** | ❌ Prohibited | Not available to this agent |
```

### Access Levels

- **✅ Full Access**: Unrestricted use
- **⚠️ Conditional Access**: Restricted or requires authorization
- **❌ Prohibited**: Tool not available to this agent

### Example: Security Reviewer

```markdown
| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read all source files for security review |
| **Grep** | ✅ Full Access | Search for security anti-patterns |
| **Glob** | ✅ Full Access | Find files by extension/pattern |
| **Write** | ❌ Prohibited | Security reviewers only audit, never implement |
| **Bash** | ⚠️ Conditional Access | Run security scanners only (no deployment) |
```

---

## Handoff Mechanisms

Handoffs enable agents to pass work to other specialized agents.

### Basic Handoff

```yaml
handoffs:
  - agent: code_reviewer
    trigger: "@review-request"
    context:
      - files_modified
      - implementation_notes
```

**How it works**:
1. Agent A completes work
2. Agent A tags `@review-request` in documentation
3. Mission Control (Gojo) detects trigger
4. Context payload prepared automatically
5. Agent B (code_reviewer) receives context and continues

### Multi-Context Handoff

```yaml
handoffs:
  - agent: security_specialist
    trigger: "@security-audit"
    context:
      - files_modified
      - authentication_changes
      - data_flow_diagram
      - tier_level
      - compliance_requirements
```

**Pass more context for complex handoffs.**

### Conditional Handoff

Define in agent documentation:

```markdown
## Handoff Logic

I hand off to security_specialist when:
- ✅ Authentication/authorization changes detected
- ✅ Payment processing implemented
- ✅ User data handling modified
- ✅ Tier 3 (Critical) features completed

Otherwise, I complete the workflow independently.
```

---

## Step-by-Step Agent Creation

### Example: Creating a "Database Optimizer" Agent

#### Step 1: Define the Role

**What does this agent do?**
- Analyzes database queries
- Suggests index optimizations
- Reviews schema design
- Detects N+1 queries

#### Step 2: Choose Tools

**What tools are needed?**
- `read` - Read SQL files, ORM models
- `grep` - Search for query patterns
- `glob` - Find all migration files
- `bash` - Run `EXPLAIN ANALYZE` (conditional)

#### Step 3: Create the File

```bash
touch protocol/database_optimizer.agent.md
```

#### Step 4: Write YAML Frontmatter

```yaml
---
target: vscode
name: "Database Optimizer - Performance Tuning Specialist"
description: "SQL query optimization, index recommendations, schema analysis, and N+1 query detection"
argument-hint: "Use: 'optimize [query/table]' or 'analyze schema'"
model: "claude-sonnet-4-5-20250929"

tools:
  - read
  - grep
  - glob
  - bash

handoffs:
  - agent: implementation_specialist
    trigger: "@apply-optimization"
    context:
      - optimization_recommendations
      - affected_queries
      - index_suggestions
---
```

#### Step 5: Create Tool Access Matrix

```markdown
## 🛠️ TOOL ACCESS MATRIX

| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read SQL files, ORM models, migration files |
| **Grep** | ✅ Full Access | Search for query patterns and anti-patterns |
| **Glob** | ✅ Full Access | Find database-related files |
| **Bash** | ⚠️ Conditional Access | Run EXPLAIN ANALYZE (read-only queries only) |
```

#### Step 6: Write Agent Documentation

```markdown
## Role

I am a Database Optimizer. My expertise includes:
- SQL query performance analysis
- Index strategy recommendations
- Schema design review
- N+1 query detection
- Query execution plan analysis

## Workflow

**Standard Optimization Process**:

1. **Analyze Request**
   - Identify target: query, table, or full schema
   - Determine scope and constraints

2. **Gather Context**
   - Read relevant SQL files
   - Review ORM models
   - Check existing indexes
   - Examine migration history

3. **Performance Analysis**
   - Run EXPLAIN ANALYZE (if permitted)
   - Identify slow queries
   - Detect missing indexes
   - Find N+1 query patterns

4. **Generate Recommendations**
   - Document findings with query IDs
   - Suggest specific index additions
   - Propose query rewrites
   - Estimate performance impact

5. **Handoff (if needed)**
   - Tag @apply-optimization for implementation
   - Pass recommendations to implementation specialist

## Invocation Examples

**Optimize a specific query**:
```bash
"Read database_optimizer.agent.md and optimize the user search query"
```

**Full schema analysis**:
```bash
"Read database_optimizer.agent.md and analyze the entire database schema"
```

**N+1 query detection**:
```bash
"Read database_optimizer.agent.md and find all N+1 queries in the API layer"
```

## Output Format

### Optimization Report

```text
# Database Optimization Report

## Query: [Query ID]
**File**: path/to/query.sql
**Line**: 45-52

**Current Performance**:
- Execution time: 450ms
- Rows scanned: 125,000
- Index usage: None

**Recommendation**:
Add composite index on (user_id, created_at)

**Expected Impact**:
- Execution time: ~25ms (95% improvement)
- Rows scanned: ~500 (99.6% reduction)

**Suggested SQL**:
```sql
CREATE INDEX idx_user_activity ON activity_log(user_id, created_at);
```

**Priority**: HIGH (affects main dashboard query)
```

## Constraints

- ❌ Cannot modify database directly
- ❌ Cannot run write queries
- ✅ Can analyze read-only
- ✅ Can suggest migrations
- ⚠️ Bash access limited to EXPLAIN commands only
```

#### Step 7: Test the Agent

```bash
# Test invocation
"Read protocol/database_optimizer.agent.md and analyze the user query performance"
```

---

## Best Practices

### 1. Single Responsibility

**✅ Good**: One clear, focused role
```yaml
name: "API Documentation Generator - OpenAPI Specialist"
description: "Generates OpenAPI/Swagger specs from code annotations"
```

**❌ Bad**: Multiple unrelated responsibilities
```yaml
name: "API Docs, Testing, and Deployment Agent"
description: "Does API docs, writes tests, and deploys to production"
```

### 2. Minimal Tool Access

**Give agents only the tools they need.**

**✅ Good**: Documentation generator
```yaml
tools:
  - read   # Read source code
  - write  # Write documentation
```

**❌ Bad**: Unnecessary permissions
```yaml
tools:
  - read
  - write
  - bash   # Why does a doc generator need bash?
  - edit
```

### 3. Clear Invocation Patterns

**✅ Good**: Explicit and actionable
```yaml
argument-hint: "Use: 'generate docs [module]' or 'update spec [endpoint]'"
```

**❌ Bad**: Vague or unclear
```yaml
argument-hint: "Just ask me to do stuff"
```

### 4. Descriptive Context Handoffs

**✅ Good**: Specific context fields
```yaml
handoffs:
  - agent: security_reviewer
    trigger: "@security-review"
    context:
      - files_modified
      - authentication_changes
      - tier_level
      - api_endpoints_added
```

**❌ Bad**: Generic context
```yaml
handoffs:
  - agent: security_reviewer
    trigger: "@security-review"
    context:
      - stuff
```

### 5. Stable Model Snapshots

**✅ Always use**: `claude-sonnet-4-5-20250929` (stable snapshot)
**❌ Never use**: `claude-sonnet-4-5` (floating alias)

**Why?** Floating aliases can change behavior when Anthropic updates them. Snapshots guarantee consistent behavior.

### 6. Complete Tool Access Matrix

**Every tool in `tools:` must appear in the matrix.**

**✅ Good**: Complete mapping
```yaml
tools:
  - read
  - write
  - bash
```

```markdown
| **Read** | ✅ Full Access | ... |
| **Write** | ✅ Full Access | ... |
| **Bash** | ⚠️ Conditional Access | ... |
```

**❌ Bad**: Missing tools
```yaml
tools:
  - read
  - write
  - bash
```

```markdown
| **Read** | ✅ Full Access | ... |
| **Write** | ✅ Full Access | ... |
<!-- Where's bash? -->
```

---

## Testing Your Agent

### 1. Syntax Validation

```bash
# PowerShell validation script
./scripts/validate-agents.ps1
```

**Checks**:
- ✅ YAML frontmatter valid
- ✅ Required fields present
- ✅ Tool Access Matrix exists
- ✅ No old .md file references

### 2. Functional Testing

**Test Checklist**:

```markdown
- [ ] Agent responds to invocation
- [ ] Tools work as expected
- [ ] Handoffs trigger correctly
- [ ] Context passes to target agents
- [ ] Error handling works
- [ ] Output format matches specification
```

**Example Test Session**:

```bash
# 1. Basic invocation
"Read protocol/database_optimizer.agent.md and analyze the user table"

# 2. Tool usage
# Verify: Agent uses read, grep, glob correctly

# 3. Handoff test
# Verify: @apply-optimization triggers implementation_specialist

# 4. Error handling
"Read protocol/database_optimizer.agent.md and optimize non-existent table"
# Verify: Clear error message, graceful failure
```

### 3. Integration Testing

**Test with other agents**:

```bash
# Test: database_optimizer → implementation_specialist handoff
"Read protocol/database_optimizer.agent.md and optimize user queries"
# Optimizer should tag @apply-optimization
# Implementation specialist should receive context
```

---

## Advanced Features

### 1. Multi-Model Support (Future)

Prepare for different models per agent:

```yaml
model: "claude-sonnet-4-5-20250929"  # Default
model_fallback: "claude-haiku-4-0"   # For simple tasks
model_critical: "claude-opus-4-5"    # For critical analysis
```

### 2. MCP Integration

Connect agents to external services:

```yaml
# Future: MCP server connections
mcp_servers:
  - database_inspector
  - jira_integration
```

**Configuration**: MCP servers configured in `~/.config/claude-code/mcp.json`

### 3. Environment-Specific Behavior

```yaml
target: vscode  # Full features

# Alternative for GitHub Copilot:
target: github  # Limited tools, manual handoffs
```

### 4. Tier-Aware Agents

Agents can adjust behavior based on tier:

```markdown
## Tier Handling

**Tier 1 (Rapid)**:
- Quick analysis, basic recommendations
- Skip detailed profiling

**Tier 2 (Standard)**:
- Full analysis with EXPLAIN ANALYZE
- Comprehensive recommendations

**Tier 3 (Critical)**:
- Deep dive with execution plan analysis
- Performance benchmarking
- Load testing recommendations
```

---

## Troubleshooting

### Agent Not Found

**Error**: `Agent file not found: protocol/myagent.agent.md`

**Solution**:
- Verify file exists in `protocol/` directory
- Check filename uses `.agent.md` extension (not `.md`)
- Use correct path in invocation: `protocol/myagent.agent.md`

### YAML Parse Error

**Error**: `Invalid YAML frontmatter`

**Solution**:
- Validate YAML syntax: https://www.yamllint.com/
- Ensure `---` delimiters are on their own lines
- Check for proper indentation (2 spaces, not tabs)
- Verify all strings with special characters are quoted

### Tool Access Denied

**Error**: `Tool 'bash' not available to this agent`

**Solution**:
- Add tool to `tools:` list in YAML frontmatter
- Add tool to Tool Access Matrix table
- Verify tool name is spelled correctly (lowercase)

### Handoff Not Triggering

**Error**: Trigger tag doesn't activate handoff

**Solution**:
- Verify trigger keyword matches exactly: `@security-review` (case-sensitive)
- Check target agent exists: `protocol/target_agent.agent.md`
- Ensure Mission Control (Gojo) is aware of handoff configuration
- Tag must appear in agent's output documentation

### Model Identifier Error

**Error**: `Unknown model: claude-sonnet-4-5`

**Solution**:
- Use stable snapshot: `claude-sonnet-4-5-20250929`
- Don't use floating alias: `claude-sonnet-4-5`
- Check Anthropic docs for latest snapshot IDs

---

## Template Collection

### 1. Minimal Agent Template

```yaml
---
target: vscode
name: "Agent Name - Role"
description: "Brief description"
argument-hint: "Use: 'action [target]'"
model: "claude-sonnet-4-5-20250929"

tools:
  - read

handoffs: []
---

## 🛠️ TOOL ACCESS MATRIX

| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read project files |

## Role
[Agent role description]

## Workflow
1. Step 1
2. Step 2
```

### 2. Full-Featured Agent Template

See: `Domain Zero Agents - Full JJK Edition/JJK_AGENT_TEMPLATE.md`

### 3. Code Reviewer Template

```yaml
---
target: vscode
name: "Code Reviewer - Quality Assurance"
description: "Code quality review, maintainability analysis, best practices enforcement"
argument-hint: "Use: 'review [file/module]'"
model: "claude-sonnet-4-5-20250929"

tools:
  - read
  - grep
  - glob

handoffs:
  - agent: implementation_specialist
    trigger: "@refactor-required"
    context:
      - files_reviewed
      - issues_found
      - refactor_suggestions
---

## 🛠️ TOOL ACCESS MATRIX

| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read source files for review |
| **Grep** | ✅ Full Access | Search for patterns/anti-patterns |
| **Glob** | ✅ Full Access | Find files by pattern |

## Role
I review code for quality, maintainability, and best practices.

## Workflow
1. Receive files to review
2. Analyze code quality (readability, maintainability, performance)
3. Check for common anti-patterns
4. Document findings with line numbers
5. Suggest improvements
6. Tag @refactor-required if major issues found
```

### 4. Testing Specialist Template

```yaml
---
target: vscode
name: "Test Engineer - Quality Assurance"
description: "Test strategy, test generation, coverage analysis, test automation"
argument-hint: "Use: 'test [feature]' or 'generate tests [module]'"
model: "claude-sonnet-4-5-20250929"

tools:
  - read
  - write
  - bash
  - grep

handoffs:
  - agent: implementation_specialist
    trigger: "@fix-failing-tests"
    context:
      - test_failures
      - affected_modules
---

## 🛠️ TOOL ACCESS MATRIX

| Tool | Access Level | Usage |
|------|--------------|-------|
| **Read** | ✅ Full Access | Read source code to understand behavior |
| **Write** | ✅ Full Access | Generate test files |
| **Bash** | ✅ Full Access | Run test suites, measure coverage |
| **Grep** | ✅ Full Access | Find existing tests |

## Role
I generate comprehensive tests and analyze test coverage.

## Workflow
1. Analyze code to be tested
2. Design test strategy (unit, integration, E2E)
3. Generate test files
4. Run tests to verify
5. Measure coverage
6. Report results
```

---

## Next Steps

1. **Read existing agents**: Study `protocol/yuuji.agent.md`, `protocol/megumi.agent.md` for examples
2. **Copy a template**: Start with `JJK_AGENT_TEMPLATE.md` or minimal template
3. **Create your first agent**: Follow the step-by-step guide
4. **Test thoroughly**: Use validation scripts and functional testing
5. **Iterate**: Refine based on real usage

---

## Additional Resources

**Protocol Documentation**:
- `protocol/CLAUDE.md` - Main protocol file
- `protocol/HANDOFF_SPECIFICATION.md` - Complete handoff guide
- `protocol/MCP_INTEGRATION.md` - MCP server integration
- `protocol/ENVIRONMENT_TARGETING.md` - VS Code vs GitHub targeting

**Example Agents**:
- `protocol/yuuji.agent.md` - Implementation specialist
- `protocol/megumi.agent.md` - Security analyst
- `protocol/nobara.agent.md` - Creative strategy & UX
- `protocol/gojo.agent.md` - Mission control

**Validation**:
- `scripts/validate-agents.ps1` - Agent validation script

**Templates**:
- `Domain Zero Agents - Full JJK Edition/JJK_AGENT_TEMPLATE.md`
- `Domain Zero Agents - Full JJK Edition/README.md`

---

## Version Information

**Guide Version**: 1.0.0
**Protocol Version**: 8.2.0
**Last Updated**: 2025-11-18

---

**Happy Agent Building!** 🤖

Create agents that make your development workflow faster, safer, and more efficient.
