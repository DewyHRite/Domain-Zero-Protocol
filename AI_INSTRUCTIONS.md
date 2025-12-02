<!-- [CORE FILE] - Domain Zero Protocol v8.6.0 -->
# AI Instructions - Domain Zero Protocol

**Version**: 8.6.0 | **Last Updated**: 2025-12-02

> **This is a redirect file.** The canonical protocol is maintained in [`protocol/CLAUDE.md`](protocol/CLAUDE.md).

---

## For AI Assistants

**Primary Instructions**: Read [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

This project uses the **Domain Zero Protocol** - a 9-agent AI development framework with:
- Security-first approach (OWASP Top 10 reviews)
- Test-driven development enforcement
- Three-tier workflow complexity (Rapid/Standard/Critical)
- Kill Switch emergency stop with project protection
- Modular architecture for token optimization
- Cross-agent edit restrictions (agent file protection)

---

## Quick Start

### Core Four Agents

**Mission Control** (Project initialization, lifecycle management):
```
Read protocol/gojo.agent.md
```

**Implementation** (Test-first feature development):
```
Read protocol/yuuji.agent.md and [your task]
```

**Security Review** (OWASP Top 10 vulnerability assessment):
```
Read protocol/megumi.agent.md and review [module/feature]
```

**Creative Strategy & UX** (Product design, user experience, accessibility):
```
Read protocol/nobara.agent.md and [design/strategy task]
```

### Extended Four Agents (v8.0+)

**Task Orchestration** (Complex multi-step coordination):
```
Read protocol/todo.agent.md and [orchestration task]
```

**Performance & Infrastructure** (Optimization, DevOps):
```
Read protocol/maki.agent.md and [performance task]
```

**Quality Assurance** (Testing strategy, test generation):
```
Read protocol/panda.agent.md and [QA task]
```

**Documentation** (Technical writing, API docs):
```
Read protocol/inumaki.agent.md and [documentation task]
```

### Slash Commands (Claude Code CLI)

If slash commands are installed (see `docs/installation/SLASH_COMMANDS_INSTALLATION.md`):

| Command | Agent | Purpose |
|---------|-------|---------|
| `/gojo` | Mission Control | Project lifecycle, protocol enforcement |
| `/yuuji` | Implementation | Test-first development |
| `/megumi` | Security | OWASP reviews, threat modeling |
| `/nobara` | Creative/UX | Design, accessibility, product vision |
| `/todo` | Orchestration | Multi-step task coordination |
| `/maki` | Performance | Optimization, infrastructure |
| `/panda` | QA | Testing strategy, coverage |
| `/inumaki` | Documentation | Technical writing |
| `/sukuna` | System Update | Protocol updates (via Gojo only) |

---

## Protocol Files

All protocol specifications are in the `protocol/` directory:

### Core Files
- **[`protocol/CLAUDE.md`](protocol/CLAUDE.md)** - **START HERE** (Main protocol specification)
- [`protocol.config.yaml`](protocol.config.yaml) - Protocol configuration

### Agent Files (.agent.md format)
- [`protocol/gojo.agent.md`](protocol/gojo.agent.md) - Mission Control & Protocol Guardian
- [`protocol/yuuji.agent.md`](protocol/yuuji.agent.md) - Implementation Specialist
- [`protocol/megumi.agent.md`](protocol/megumi.agent.md) - Security Analyst
- [`protocol/nobara.agent.md`](protocol/nobara.agent.md) - Creative Strategy & UX
- [`protocol/todo.agent.md`](protocol/todo.agent.md) - Task Orchestrator
- [`protocol/maki.agent.md`](protocol/maki.agent.md) - Performance Specialist
- [`protocol/panda.agent.md`](protocol/panda.agent.md) - QA Engineer
- [`protocol/inumaki.agent.md`](protocol/inumaki.agent.md) - Documentation Specialist
- [`protocol/sukuna.agent.md`](protocol/sukuna.agent.md) - System Update Agent (Gojo-invoked only)

### Quick Reference
- [`protocol/TIER-SELECTION-GUIDE.md`](protocol/TIER-SELECTION-GUIDE.md) - Workflow tier selection
- [`protocol/HANDOFF_SPECIFICATION.md`](protocol/HANDOFF_SPECIFICATION.md) - Agent handoff protocol
- [`protocol/EMERGENCY_STOP_STANDARD.md`](protocol/EMERGENCY_STOP_STANDARD.md) - Kill Switch reference

---

## Key v8.5.1 Features

### Kill Switch Protocol
Emergency stop with project protection. Say **"STOP"**, **"ABORT"**, or **"EMERGENCY STOP"** to:
- Halt all agent work instantly
- Create checkpoint for recovery
- Block destructive operations until resumed

### Modular Architecture
Shared protocol modules reduce token usage by ~40-60%:
- `protocol/modules/SAFETY_FIRST.md` - Safety principles
- `protocol/modules/BINDING_OATH.md` - Agent commitment
- `protocol/modules/ESCAPE_PATH_PROTOCOL.md` - Agent guidance
- `protocol/modules/EMERGENCY_STOP_PROTOCOL.md` - Kill switch behavior

### Three-Tier Workflow
| Tier | Use Case | Requirements |
|------|----------|--------------|
| **Tier 1 (Rapid)** | Prototypes, POCs | Fast iteration, minimal ceremony |
| **Tier 2 (Standard)** | Production features | TDD + security review [DEFAULT] |
| **Tier 3 (Critical)** | Auth, payments, compliance | Enhanced testing + multi-model review |

### Mask Mode
Toggle between JJK-themed and professional presentation:
- `mask_mode: false` - JJK character personalities (default)
- `mask_mode: true` - Professional agent names

### Sukuna System Update Agent (v8.5.1+)
Adversarial-but-aligned agent for protocol updates:
- **Gojo-invoked only** - cannot be called directly by users
- Stress-tests proposed changes before implementation
- Questions assumptions, finds edge cases
- Invocation: `Read protocol/gojo.agent.md and engage Sukuna for [update task]`

### Cross-Agent Edit Restrictions (v8.5.1+)
Non-Gojo agents have **READ-ONLY** access to all `.agent.md` files:
- Prevents agents from modifying their own behavior
- User and Gojo retain full edit permissions
- Sukuna operates via Gojo with explicit authorization

---

## Why This Structure?

**CLAUDE.md is the canonical source of truth**:
- Single source of truth (no duplication)
- Version controlled and protected (via CODEOWNERS)
- Auditable change history
- Works across all AI assistants

**This file exists for discoverability**:
- Many AI tools look for `AI_INSTRUCTIONS.md`, `AI.md`, or `.github/copilot-instructions.md`
- This shim ensures they find the Domain Zero Protocol
- No protocol logic duplicated here - just a pointer

---

## Cross-Assistant Compatibility

This approach works with:
- **Claude** (Anthropic) - via this file or direct protocol file reading
- **GitHub Copilot** - via `.github/copilot-instructions.md` (append pointer)
- **Cursor** - via `.cursorrules` or this file
- **Cody** (Sourcegraph) - via this file
- **Any AI assistant** that reads markdown instruction files

### Integration Template

Append this to your existing instruction files:

```markdown
## Domain Zero Protocol

This project follows the Domain Zero Protocol for AI-assisted development.

**Primary entrypoint**: [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

For workflow guidance, read the appropriate agent file in `protocol/`.
```

**Automated updater**: See `scripts/update-instructions.ps1` (Windows) or `scripts/update-instructions.sh` (macOS/Linux).

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`README.md`](README.md) | Complete setup guide |
| [`PROTOCOL_QUICKSTART.md`](PROTOCOL_QUICKSTART.md) | 5-minute quick start |
| [`docs/installation/IMPLEMENTATION_GUIDE.md`](docs/installation/IMPLEMENTATION_GUIDE.md) | Full implementation guide |
| [`docs/installation/SLASH_COMMANDS_INSTALLATION.md`](docs/installation/SLASH_COMMANDS_INSTALLATION.md) | Slash commands setup |
| [`docs/reference/REALITY_CHECK.md`](docs/reference/REALITY_CHECK.md) | Honest assessment of capabilities |
| [`PASSIVE_OBSERVER.md`](PASSIVE_OBSERVER.md) | Gojo's background monitoring guide |

---

## Canonical Source

> **Repository**: https://github.com/DewyHRite/Domain-Zero-Protocol
> **Version**: 8.5.1
> **Canonical File**: `protocol/CLAUDE.md`

All protocol updates originate from the canonical source. Run `./scripts/verify-protocol.(ps1|sh)` to check alignment.
