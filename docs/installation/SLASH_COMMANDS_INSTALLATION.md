<!-- [CORE FILE] - Domain Zero Protocol v9.12.0 -->
# Slash Commands Installation Guide

> **Protocol Version**: v9.12.0
> **Purpose**: Set up `.claude/commands/` for quick agent invocation
> **Target Environment**: Claude Code CLI
> **Last Updated**: 2026-07-13

---

## Overview

Domain Zero Protocol agents can be invoked via **slash commands** in Claude Code. Instead of typing full `"Read protocol/gojo.agent.md and..."` commands, you can use shortcuts like `/gojo` directly.

This guide shows you how to set up `.claude/commands/` for all 8 Domain Zero agents.

---

## Quick Setup (Recommended)

Copy the pre-built slash commands from the `slash-commands/` folder:

```bash
# From your project root (where protocol/ is located)
mkdir -p .claude/commands
cp -r slash-commands/* .claude/commands/
```

That's it! All 9 commands are now ready to use.

---

## Manual Setup (Alternative)

If you prefer to create commands manually:

### Step 1: Create Commands Directory

```bash
# From your project root
mkdir -p .claude/commands
```

### Step 2: Create Command Files

Create these 8 files in `.claude/commands/`:

| Agent | File | Shortcut |
|-------|------|----------|
| **Gojo** (Mission Control) | `.claude/commands/gojo.md` | `/gojo` |
| **Yuuji** (Implementation) | `.claude/commands/yuuji.md` | `/yuuji` |
| **Megumi** (Security) | `.claude/commands/megumi.md` | `/megumi` |
| **Nobara** (Creative/UX) | `.claude/commands/nobara.md` | `/nobara` |
| **Todo** (Database) | `.claude/commands/todo.md` | `/todo` |
| **Maki** (Performance) | `.claude/commands/maki.md` | `/maki` |
| **Panda** (Build/CI) | `.claude/commands/panda.md` | `/panda` |
| **Inumaki** (API) | `.claude/commands/inumaki.md` | `/inumaki` |

### Step 3: Add Content to Each File

Copy the appropriate content below into each file:

#### `.claude/commands/gojo.md`
```markdown
---
description: Invoke Gojo (Mission Control) for project planning, lifecycle management, and protocol enforcement
---

Read protocol/gojo.agent.md and
```

#### `.claude/commands/yuuji.md`
```markdown
---
description: Invoke Yuuji (Implementation Specialist) for test-first development and feature implementation
---

Read protocol/yuuji.agent.md and
```

#### `.claude/commands/megumi.md`
```markdown
---
description: Invoke Megumi (Security Analyst) for OWASP Top 10 security reviews
---

Read protocol/megumi.agent.md and
```

#### `.claude/commands/nobara.md`
```markdown
---
description: Invoke Nobara (Creative Strategy & UX) for user experience design and product vision
---

Read protocol/nobara.agent.md and
```

#### `.claude/commands/todo.md`
```markdown
---
description: Invoke Todo (Database & Backend Specialist) for schema design, migrations, and query optimization
---

Read protocol/todo.agent.md and
```

#### `.claude/commands/maki.md`
```markdown
---
description: Invoke Maki (Performance Optimization Specialist) for Lighthouse audits, profiling, and zero-overhead optimization
---

Read protocol/maki.agent.md and
```

#### `.claude/commands/panda.md`
```markdown
---
description: Invoke Panda (Build & Integration Specialist) for CI/CD, GitHub Actions, Docker, and multi-core build modes
---

Read protocol/panda.agent.md and
```

#### `.claude/commands/inumaki.md`
```markdown
---
description: Invoke Inumaki (API & Communication Specialist) for REST/GraphQL/WebSocket design and OpenAPI documentation
---

Read protocol/inumaki.agent.md and
```

---

## Usage Examples

Once installed, invoke agents with slash commands:

```bash
# Mission Control - Project planning
/gojo brief me on project status

# Implementation - Add new feature
/yuuji implement user authentication with tier 2

# Security Review
/megumi review the authentication implementation

# UX Design
/nobara design the login flow with accessibility in mind

# Database Design
/todo create schema for user management system

# Performance Audit
/maki analyze bundle size and suggest optimizations

# CI/CD Setup
/panda configure GitHub Actions workflow for production builds

# API Design
/inumaki design REST endpoints for user CRUD operations
```

---

## Verification

Test that commands work:

```bash
# In Claude Code CLI
/gojo verify protocol installation
```

Expected response: Gojo should self-identify with the Mission Control banner.

---

## Advanced: Custom Slash Commands

You can create project-specific commands in `.claude/commands/`:

### `.claude/commands/review-pr.md`
```markdown
---
description: Review a pull request with security and implementation checks
---

Read protocol/megumi.agent.md and review PR #$ARGUMENTS for security issues, then
Read protocol/yuuji.agent.md and review PR #$ARGUMENTS for implementation quality
```

Usage:
```bash
/review-pr 42
```

---

## Directory Structure

After setup, your project should have:

```text
your-project/
├── .claude/
│   └── commands/
│       ├── gojo.md
│       ├── yuuji.md
│       ├── megumi.md
│       ├── nobara.md
│       ├── todo.md
│       ├── maki.md
│       ├── panda.md
│       └── inumaki.md
├── protocol/
│   ├── CLAUDE.md
│   ├── gojo.agent.md
│   ├── yuuji.agent.md
│   ├── megumi.agent.md
│   ├── nobara.agent.md
│   ├── todo.agent.md
│   ├── maki.agent.md
│   ├── panda.agent.md
│   └── inumaki.agent.md
└── ...
```

---

## Troubleshooting

### Command Not Found

**Problem**: `/gojo` returns "Unknown command"

**Solution**: Verify `.claude/commands/gojo.md` exists and Claude Code has reloaded:
```bash
ls -la .claude/commands/
# Restart Claude Code CLI
```

### Agent Not Self-Identifying

**Problem**: Command works but agent doesn't show identification banner

**Solution**: Ensure agent file uses v8.0.0+ format with YAML frontmatter:
```bash
head -20 protocol/gojo.agent.md
```

Look for:
```yaml
---
target: claude-code
agent_name: Gojo Satoru
...
---
```

### Wrong Agent Invoked

**Problem**: `/yuuji` invokes wrong agent

**Solution**: Check command file content points to correct agent:
```bash
cat .claude/commands/yuuji.md
# Should show: Read protocol/yuuji.agent.md and
```

---

## Git Configuration

Add to `.gitignore` if commands are project-specific:

```gitignore
# Uncomment to ignore slash commands (user-specific)
# .claude/commands/
```

**Recommendation**: Commit `.claude/commands/` to share shortcuts with team.

---

## Next Steps

- Read [PROTOCOL_QUICKSTART.md](../PROTOCOL_QUICKSTART.md) for agent usage patterns
- Read [README.md](../README.md) for installation and setup
- Explore [Domain Zero Agents - Full JJK Edition/](../Domain%20Zero%20Agents%20-%20Full%20JJK%20Edition/) for detailed agent documentation

---

**Questions?** Open an issue: [GitHub Issues](https://github.com/DewyHRite/Domain-Zero-Protocol/issues)
