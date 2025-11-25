---
description: "Install Domain Zero Protocol - Setup guide for new projects and users (v8.3.1)"
---

# DOMAIN ZERO PROTOCOL INSTALLATION GUIDE

**Version:** 8.3.1 | **Canonical Source:** <https://github.com/DewyHRite/Domain-Zero-Protocol>

## Quick Start Installation

### Step 1: Copy Protocol Files

Copy these files to your project's `protocol/` directory:

```text
protocol/
  CLAUDE.md          # Main protocol file
  yuuji.agent.md     # Implementation Specialist
  megumi.agent.md    # Security Analyst
  nobara.agent.md    # Creative Strategy & UX
  gojo.agent.md      # Mission Control & Protocol Guardian
```

### Step 2: Create State Directory

```bash
mkdir -p .protocol-state
```

### Step 3: Initialize Configuration

Create `protocol.config.yaml` in your project root with your settings.

### Step 4: Add to .gitignore

```text
.protocol-state/trigger-19.md
.protocol-state/research/**/**.raw.log
```

---

## Agent Invocation Patterns

**Gojo (Mission Control):**
```text
"Read protocol/gojo.agent.md"
```

**Yuuji (Implementation):**
```text
"Read protocol/yuuji.agent.md and implement [feature]"
"Read protocol/yuuji.agent.md --tier rapid and create [script]"
"Read protocol/yuuji.agent.md --tier critical and implement [auth feature]"
```

**Megumi (Security):**
```text
"Read protocol/megumi.agent.md and review [module]"
```

**Nobara (UX/Design):**
```text
"Read protocol/nobara.agent.md and design [feature]"
```

---

## Tier System

| Tier | Flag | Use Case | Time |
|------|------|----------|------|
| Rapid | `--tier rapid` | Prototypes, scripts | 10-15 min |
| Standard | (default) | Production features | 30-45 min |
| Critical | `--tier critical` | Auth, payments | 60-90 min |

---

## First Time Setup

After copying files, invoke Gojo to initialize your project:

```text
"Read protocol/gojo.agent.md"
```

Select **[2] New Project Initialization** to create state files and configure your project.

---

**Need Help?** See the full documentation at `protocol/CLAUDE.md` or visit the [GitHub repository](https://github.com/DewyHRite/Domain-Zero-Protocol).
