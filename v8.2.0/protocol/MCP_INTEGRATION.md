# MCP Integration Guide
## Model Context Protocol for Domain Zero Agents

**Version**: 1.0.0
**Created**: November 18, 2025
**Status**: Production-Ready
**Purpose**: Enable Domain Zero agents to connect with MCP servers for enhanced capabilities

---

## Table of Contents

- [Overview](#overview)
- [What is MCP?](#what-is-mcp)
- [Benefits of MCP Integration](#benefits-of-mcp-integration)
- [Architecture](#architecture)
- [MCP Server Configuration](#mcp-server-configuration)
- [Agent MCP Capabilities](#agent-mcp-capabilities)
- [Example Integrations](#example-integrations)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Model Context Protocol (MCP)** is an open standard that enables AI agents to connect to external data sources, tools, and services through a unified interface. Domain Zero Protocol v8.0.0 supports MCP integration through the .agent.md format.

**Key Capabilities**:
- ✅ Connect agents to databases, APIs, file systems
- ✅ Extend agent tool access beyond built-in tools
- ✅ Enable real-time data access during agent execution
- ✅ Standardized connection management
- ✅ Security boundaries and authorization

---

## What is MCP?

### Core Concepts

**MCP Server**: A service that exposes resources (data, tools, prompts) to AI agents through a standardized protocol

**MCP Client**: The AI agent/environment that connects to MCP servers (e.g., Claude Code, VS Code)

**Resources**: Data sources agents can read (files, databases, APIs)

**Tools**: Functions agents can execute (search, compute, transform)

**Prompts**: Pre-defined templates for common tasks

### MCP vs Built-in Tools

| Feature | Built-in Tools | MCP Integration |
|---------|----------------|-----------------|
| **Scope** | Limited to environment | Extensible to any service |
| **Configuration** | Pre-configured | User-configurable |
| **Examples** | Read, Write, Bash | Database queries, API calls, custom tools |
| **Authorization** | Environment-level | Per-server authorization |
| **Setup** | Automatic | Requires server configuration |

---

## Benefits of MCP Integration

### For Domain Zero Agents

**Yuuji (Implementation)**:
- Query project databases directly
- Access API documentation from external sources
- Fetch code examples from knowledge bases
- Integrate with package managers

**Megumi (Security)**:
- Query vulnerability databases (CVE, NVD)
- Access OWASP knowledge bases
- Integrate with security scanning tools
- Fetch compliance checklists

**Nobara (Creative & UX)**:
- Access design system documentation
- Query user research databases
- Fetch analytics data for UX insights
- Integrate with design tools (Figma API)

**Gojo (Mission Control)**:
- Query project management tools (Jira, Linear)
- Access team calendars and availability
- Fetch historical project data
- Integrate with CI/CD platforms

### For Users

- ✅ **Enhanced Agent Capabilities**: Agents can access real-world data and services
- ✅ **Custom Integrations**: Connect to proprietary internal tools
- ✅ **Reduced Context Switching**: Agents fetch data automatically
- ✅ **Standardized Configuration**: One format for all integrations

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────┐
│           Claude Code / VS Code                  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  Yuuji   │  │  Megumi  │  │  Nobara  │      │
│  │ .agent.md│  │ .agent.md│  │ .agent.md│      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │              │            │
│       └─────────────┴──────────────┘            │
│                     │                           │
│              MCP Client Layer                   │
│                     │                           │
└─────────────────────┼───────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼─────┐            ┌─────▼────┐
    │ MCP      │            │ MCP      │
    │ Server 1 │            │ Server 2 │
    │ (DB)     │            │ (API)    │
    └──────────┘            └──────────┘
```

### .agent.md MCP Configuration

The `target` field in YAML frontmatter determines MCP compatibility:

```yaml
---
target: vscode     # MCP integration supported
name: "Agent Name"
# ...
---
```

**Supported targets**:
- `vscode`: Full MCP support (Claude Code, VS Code extensions)
- `github`: Limited MCP (GitHub Copilot constraints)

---

## MCP Server Configuration

### Global MCP Configuration

MCP servers are configured in Claude Code settings (not in .agent.md files):

**Location**: `~/.config/claude-code/mcp.json` or VS Code settings

**Format**:
```json
{
  "mcpServers": {
    "database": {
      "command": "node",
      "args": ["path/to/database-mcp-server.js"],
      "env": {
        "DATABASE_URL": "postgresql://localhost:5432/mydb"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Per-Project MCP Configuration

Projects can define MCP servers in `.claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "project-db": {
      "command": "node",
      "args": ["./mcp-servers/project-database.js"],
      "env": {
        "DATABASE_URL": "${PROJECT_DATABASE_URL}"
      }
    },
    "jira": {
      "command": "node",
      "args": ["./mcp-servers/jira-server.js"],
      "env": {
        "JIRA_API_TOKEN": "${JIRA_TOKEN}",
        "JIRA_HOST": "https://yourcompany.atlassian.net"
      }
    }
  }
}
```

**Note**: .agent.md files do NOT configure MCP servers directly - they specify which tools agents can use, and MCP servers expose additional tools.

---

## Agent MCP Capabilities

### Tool Discovery

When MCP servers are configured, agents can discover available tools:

**Example**: Yuuji with database MCP server

```yaml
---
target: vscode
name: "Yuuji Itadori - Implementation Specialist"
# ...
tools:
  - read
  - write
  - edit
  - bash
  # Built-in tools (always available)

  # MCP tools (auto-discovered from connected servers):
  # - query_database (from database MCP server)
  # - fetch_schema (from database MCP server)
  # - search_github (from GitHub MCP server)
---
```

**How it works**:
1. Agent starts execution
2. Claude Code connects to configured MCP servers
3. Servers expose available tools
4. Agent can use both built-in tools AND MCP tools
5. Tool calls routed to appropriate MCP server

### Resource Access

MCP servers can expose resources (read-only data):

**Example**: Megumi accessing OWASP knowledge base

```yaml
---
target: vscode
name: "Megumi Fushiguro - Security Analyst"
# ...
# MCP resources (auto-discovered):
# - resource://owasp/top10/2021
# - resource://cve-database/search
# - resource://security-checklists/pci-dss
---
```

**Usage in agent workflow**:
```markdown
Megumi can now access:
- OWASP Top 10 documentation via MCP resource
- CVE database searches via MCP tool
- Compliance checklists via MCP resource

No need to manually search or copy-paste documentation!
```

---

## Example Integrations

### Example 1: Database MCP Server for Yuuji

**Use Case**: Yuuji needs to query project database schema during implementation

**MCP Server**: `@modelcontextprotocol/server-postgres`

**Configuration** (`.claude-code/mcp.json`):
```json
{
  "mcpServers": {
    "project-db": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://localhost:5432/myproject"
      }
    }
  }
}
```

**Exposed Tools**:
- `query_database(sql)`: Execute SQL queries
- `list_tables()`: Get all table names
- `describe_table(name)`: Get table schema

**Example Workflow**:
```markdown
User: "Yuuji, implement user profile update endpoint"

Yuuji:
1. Calls list_tables() via MCP → sees "users" table
2. Calls describe_table("users") → gets schema
3. Implements UPDATE endpoint with correct fields
4. Writes tests based on actual schema
5. No manual schema lookup needed!
```

### Example 2: GitHub MCP Server for Megumi

**Use Case**: Megumi needs to check known vulnerabilities in dependencies

**MCP Server**: `@modelcontextprotocol/server-github`

**Configuration**:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Exposed Tools**:
- `search_code(query, repo)`: Search code
- `get_issue(repo, number)`: Fetch issue details
- `list_pull_requests(repo)`: List PRs

**Example Workflow**:
```markdown
User: "Megumi, review authentication implementation"

Megumi:
1. Reviews src/auth/jwt.ts
2. Identifies jsonwebtoken@8.5.1 dependency
3. Calls search_code("jsonwebtoken vulnerability", "advisories/github-advisory-database")
4. Finds known CVE in this version
5. Adds SEC-001: Upgrade jsonwebtoken to 9.0.0
```

### Example 3: Jira MCP Server for Gojo

**Use Case**: Gojo needs to sync project status with Jira

**MCP Server**: Custom Jira server

**Configuration**:
```json
{
  "mcpServers": {
    "jira": {
      "command": "node",
      "args": ["./mcp-servers/jira-server.js"],
      "env": {
        "JIRA_API_TOKEN": "${JIRA_TOKEN}",
        "JIRA_HOST": "https://company.atlassian.net",
        "JIRA_PROJECT": "PROJ"
      }
    }
  }
}
```

**Exposed Tools**:
- `get_project_status()`: Fetch project metrics
- `list_open_issues()`: Get open issues
- `create_issue(summary, description)`: Create new issue

**Example Workflow**:
```markdown
User: "Gojo, generate Trigger 19 intelligence report"

Gojo:
1. Compiles passive observations
2. Calls get_project_status() via Jira MCP
3. Calls list_open_issues() to get blockers
4. Cross-references local observations with Jira data
5. Generates comprehensive intelligence report with external context
```

---

## Security Considerations

### 1. **Credential Management**

**Rule**: Never hardcode credentials in MCP configuration

**Bad**:
```json
{
  "mcpServers": {
    "database": {
      "env": {
        "DATABASE_PASSWORD": "plaintextpassword123"  // ❌ NEVER
      }
    }
  }
}
```

**Good**:
```json
{
  "mcpServers": {
    "database": {
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"  // ✅ Environment variable
      }
    }
  }
}
```

**Best Practices**:
- ✅ Use environment variables (`${VAR_NAME}`)
- ✅ Store secrets in system keychain/vault
- ✅ Gitignore MCP configuration files with secrets
- ✅ Document required environment variables in README

### 2. **Authorization Boundaries**

**Agent Tool Access** (from .agent.md):
```yaml
tools:
  - read      # Can read local files
  - write     # Can write local files
  - bash      # Can execute commands
```

**MCP Server Authorization** (separate layer):
```json
{
  "mcpServers": {
    "database": {
      "permissions": ["read", "write"],  // MCP server permissions
      "scope": "project-database-only"   // Limit scope
    }
  }
}
```

**Layered Security**:
1. **.agent.md tools**: Which built-in tools agent can use
2. **MCP server config**: Which external services agent can access
3. **MCP server permissions**: What operations allowed on those services

### 3. **Data Exposure**

**Rule**: MCP servers should not expose sensitive data in responses

**Example**: Database MCP server should sanitize results

**Bad**:
```json
{
  "results": [
    {
      "id": 1,
      "email": "user@example.com",
      "password_hash": "$2b$10$..." // ❌ Never expose password hashes
    }
  ]
}
```

**Good**:
```json
{
  "results": [
    {
      "id": 1,
      "email": "user@example.com"
      // password_hash excluded from MCP responses
    }
  ]
}
```

### 4. **Audit Logging**

**Recommendation**: Log all MCP tool calls for audit trail

**Implementation** (in MCP server):
```javascript
// mcp-server.js
server.tool("query_database", async (args) => {
  // Log tool call
  logger.info({
    tool: "query_database",
    query: args.sql,
    user: process.env.USER,
    timestamp: new Date().toISOString()
  });

  // Execute query
  const result = await db.query(args.sql);
  return result;
});
```

**Benefits**:
- ✅ Track which agent accessed what data
- ✅ Identify unauthorized access attempts
- ✅ Debug MCP integration issues
- ✅ Compliance with audit requirements

---

## Troubleshooting

### Issue 1: MCP Server Not Connecting

**Symptoms**:
- Agent cannot find MCP tools
- "MCP server failed to start" error

**Diagnosis**:
```bash
# Check MCP server configuration
cat ~/.config/claude-code/mcp.json

# Test MCP server manually
node path/to/mcp-server.js

# Check environment variables
echo $DATABASE_URL
```

**Common Fixes**:
- ✅ Verify MCP server executable exists
- ✅ Check environment variables are set
- ✅ Ensure correct Node.js version
- ✅ Review server startup logs

### Issue 2: Agent Can't Use MCP Tools

**Symptoms**:
- MCP server running
- Agent says "tool not available"

**Diagnosis**:
```yaml
# Check .agent.md has correct target
---
target: vscode  # ✅ Required for MCP
---

# Check MCP server exposes tools correctly
# In MCP server code:
server.tool("tool_name", async (args) => { ... });
```

**Common Fixes**:
- ✅ Ensure `target: vscode` in .agent.md
- ✅ Verify MCP server registered tools
- ✅ Restart Claude Code to reload MCP servers
- ✅ Check MCP server logs for errors

### Issue 3: Permission Denied

**Symptoms**:
- MCP tool call fails with "permission denied"

**Diagnosis**:
```json
// Check MCP server permissions
{
  "mcpServers": {
    "database": {
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost/db"
      }
    }
  }
}
```

**Common Fixes**:
- ✅ Verify database user has required permissions
- ✅ Check API token has correct scopes
- ✅ Ensure MCP server runs with correct user
- ✅ Review service-level access controls

### Issue 4: Slow MCP Responses

**Symptoms**:
- Agent waits long time for MCP tool responses
- Timeout errors

**Diagnosis**:
```javascript
// Add timing to MCP server
server.tool("query_database", async (args) => {
  const start = Date.now();
  const result = await db.query(args.sql);
  const duration = Date.now() - start;

  logger.info({ tool: "query_database", duration_ms: duration });
  return result;
});
```

**Common Fixes**:
- ✅ Optimize database queries (add indexes)
- ✅ Implement caching in MCP server
- ✅ Increase timeout limits
- ✅ Use async/streaming for large responses

---

## Appendix: Creating Custom MCP Servers

### Basic MCP Server Template

```javascript
// custom-mcp-server.js
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  {
    name: "custom-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Register a tool
server.tool(
  "my_custom_tool",
  "Description of what this tool does",
  {
    arg1: {
      type: "string",
      description: "Description of arg1",
    },
  },
  async (args) => {
    // Tool implementation
    const result = await doSomething(args.arg1);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }
);

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Testing Custom MCP Server

```bash
# Install dependencies
npm install @modelcontextprotocol/sdk

# Test server
node custom-mcp-server.js

# Configure in Claude Code
# Add to ~/.config/claude-code/mcp.json:
{
  "mcpServers": {
    "custom": {
      "command": "node",
      "args": ["path/to/custom-mcp-server.js"]
    }
  }
}

# Restart Claude Code and test
```

---

## Version History

- **1.0.0** (2025-11-18): Initial MCP integration guide for v8.0.0

---

**END OF MCP_INTEGRATION.md**
