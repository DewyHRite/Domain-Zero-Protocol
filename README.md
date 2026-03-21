# Domain Zero Protocol
<!-- [CORE FILE] - Domain Zero Protocol v8.13.0 -->

**Version**: 8.13.0 | **Last Updated**: 2026-03-20

A nine-agent AI development system plus one external auditor inspired by Jujutsu Kaisen, designed for Claude, GitHub Copilot, and any AI assistant.

---

## 🎯 What is Domain Zero Protocol?

Domain Zero Protocol (DZP) is a structured framework for AI-assisted development using specialized agents, each with distinct roles and expertise. The protocol enforces test-first development, security reviews, and collaborative workflows while maintaining safety through escape paths and emergency stops.

**Key Features**:
- 🤖 Nine specialized agents with clear responsibilities
- 🔐 Built-in security reviews (OWASP Top 10)
- ✅ Test-driven development (TDD) workflows
- 🎨 UX and accessibility focus (WCAG 2.2)
- 📊 Three-tier workflow system
- 🛡️ Safety-first design with escape paths
- 🔄 Session monitoring and fatigue detection
- 📝 Skills system for common operations

---

## 👥 The Nine Agents

### Core Four

**Satoru Gojo** - Mission Control
[`protocol/gojo.agent.md`](protocol/gojo.agent.md)
- Project lifecycle management
- Protocol guardian and coordination
- Session monitoring and checkpoints
- Passive observation and intelligence reports

**Yuuji Itadori** - Implementation Specialist
[`protocol/yuuji.agent.md`](protocol/yuuji.agent.md)
- Test-first development (TDD)
- ALL code implementation routes through Yuuji
- Feature implementation across all tiers
- Dev notes and documentation

**Megumi Fushiguro** - Security Analyst
[`protocol/megumi.agent.md`](protocol/megumi.agent.md)
- OWASP Top 10 security reviews
- Threat modeling and SEC-ID tracking
- Security-review.md documentation
- Routes remediation to Yuuji via @remediation-required

**Nobara Kugisaki** - Creative Strategy & UX
[`protocol/nobara.agent.md`](protocol/nobara.agent.md)
- User experience design
- Product vision and strategy
- Accessibility (WCAG 2.2)
- Routes implementation to Yuuji via @implement-design

### Extended Four

**Aoi Todo** - Database & Backend Specialist
[`protocol/todo.agent.md`](protocol/todo.agent.md)
- Schema design and migrations
- Query optimization and ORM configuration
- Database architecture decisions
- Routes implementation to Yuuji via @implementation

**Maki Zenin** - Performance Optimization Specialist
[`protocol/maki.agent.md`](protocol/maki.agent.md)
- Profiling and bundle analysis
- Zero-overhead optimization philosophy
- Performance audits and recommendations
- Routes implementation to Yuuji via @implementation

**Panda** - Build & Integration Specialist
[`protocol/panda.agent.md`](protocol/panda.agent.md)
- CI/CD pipelines (GitHub Actions, GitLab CI)
- Build system optimization
- Docker and containerization
- Routes implementation to Yuuji via @implementation

**Toge Inumaki** - API & Communication Specialist
[`protocol/inumaki.agent.md`](protocol/inumaki.agent.md)
- REST, GraphQL, WebSocket design
- OpenAPI specifications
- Cursed Speech for declarative contracts
- Routes implementation to Yuuji via @implementation

### Special Agent

**Ryomen Sukuna** - System Update Adversary
[`protocol/sukuna.agent.md`](protocol/sukuna.agent.md)
- Protocol updates and version migrations (Gojo-invoked only)
- Adversarial review and red-team analysis
- Stress-testing changes and rollback verification
- System integrity challenges

---

## 🚀 Quick Start

### 1. Installation

**Fresh Install**:
```bash
# Clone or download release
git clone https://github.com/DewyHRite/Domain-Zero-Protocol.git
cd Domain-Zero-Protocol

# Verify installation
python scripts/verify-installation.py

# Sync templates
python scripts/sync-templates.py

# Read main protocol
Read protocol/CLAUDE.md
```

**In-Place Upgrade**:
See [IMPLEMENTATION_GUIDE.md](docs/installation/IMPLEMENTATION_GUIDE.md) for upgrade procedures.

### 2. Invoke Your First Agent

```bash
# Mission Control (project initialization)
Read protocol/gojo.agent.md

# Implementation (test-first development)
Read protocol/yuuji.agent.md and implement user authentication tier 2

# Security Review (OWASP Top 10)
Read protocol/megumi.agent.md and review authentication module

# Creative/UX (design and accessibility)
Read protocol/nobara.agent.md and design login flow WCAG 2.2
```

### 3. Using Slash Commands (Optional)

If using Claude Code with slash commands installed:
```bash
/gojo              # Mission Control
/yuuji             # Implementation
/megumi            # Security
/nobara            # Creative/UX
/dzp-roe           # Post-compaction recovery
/session start     # Begin work session
/ts tier1          # Troubleshooting tier 1
```

---

## 📊 Three-Tier Workflow System

| Tier | Name | Testing | Security | Use Cases |
|------|------|---------|----------|-----------|
| **Tier 1** | Rapid | None | None | Prototypes, experiments, learning |
| **Tier 2** | Standard | TDD (unit + integration) | OWASP review | Production features [DEFAULT] |
| **Tier 3** | Critical | Enhanced (TDD + E2E) | Multi-model review | Auth, payments, sensitive data |

**Flag Usage**:
```bash
Read protocol/yuuji.agent.md and implement payment processing --tier critical
```

---

## 🔑 Key Restrictions

**Implementation Routing**:
- ❌ **Nobara, Todo, Maki, Panda, Inumaki CANNOT write code**
- ✅ **MUST route through Yuuji** via `@implementation` handoff
- ✅ **Only Yuuji, Gojo, Sukuna have Edit/Write/Bash for code**

**Domain Record Access**:
- ✅ **Gojo + Sukuna ONLY** have READ/WRITE `.dzp-domain/domain.record.md`
- ❌ **All other 7 agents DENIED**

**Agent File Protection**:
- ❌ **No agent** may edit another agent's `.agent.md` file
- ✅ **READ-ONLY** access for study
- ✅ **Changes require** User direct edit OR Gojo coordination

---

## 🛠️ Skills System

**Active Skills** (v8.13.0):

| Skill | Commands | Purpose | Owner |
|-------|----------|---------|-------|
| **session** | start, status, update, break, continue, end | Work session management | Gojo |
| **ts** | tier1-4, codered, status, history, escalate, complete | Troubleshooting tiers | Gojo |
| **dzp-roe** | N/A | Post-compaction recovery | Gojo |

**Invocation**:
```bash
skill: "session"
args: "start"

# Or via slash command
/session start
/ts tier1
/dzp-roe
```

See [SKILL_REGISTRY.md](protocol/skills/SKILL_REGISTRY.md) for all skills.

---

## 📚 Documentation Structure

### Core Protocol
- **[protocol/CLAUDE.md](protocol/CLAUDE.md)** - Main protocol file (START HERE)
- **[AI_INSTRUCTIONS.md](AI_INSTRUCTIONS.md)** - Complete installation guide for AI assistants
- **[protocol.config.yaml](protocol.config.yaml)** - Configuration settings

### Agent Files
- **[protocol/*.agent.md](protocol/)** - Individual agent specifications (9 files)

### Procedures & Modules
- **[protocol/gojo-procedures/](protocol/gojo-procedures/)** - Mission Control operational procedures
- **[protocol/modules/](protocol/modules/)** - Shared protocol modules (safety, escape paths, etc.)

### Skills
- **[protocol/skills/](protocol/skills/)** - Skill definitions and registry

### Documentation
- **[docs/guides/](docs/guides/)** - Usage guides and tutorials
- **[docs/installation/](docs/installation/)** - Installation and implementation guides
- **[docs/reference/](docs/reference/)** - Reference documentation

### State Management
- **[.protocol-state/](/.protocol-state/)** - Runtime state files (JSON, logs, checkpoints)
- **[.dzp-domain/](/.dzp-domain/)** - Domain record (Gojo + Sukuna only)

---

## 🔄 Workflow Example

**Implementing a New Feature** (Tier 2 - Standard):

1. **Start Session**:
   ```bash
   /session start
   ```

2. **Invoke Yuuji for Implementation**:
   ```bash
   Read protocol/yuuji.agent.md and implement password reset feature tier 2
   ```

3. **Yuuji's TDD Workflow**:
   - Writes failing tests first
   - Implements feature to pass tests
   - Routes to Megumi for security review via `@security-review`

4. **Megumi's Security Review**:
   - Reviews against OWASP Top 10
   - Documents findings in security-review.md
   - Routes remediation to Yuuji via `@remediation-required` if issues found

5. **Completion**:
   - Tests pass, security clean
   - Dev notes updated
   - Session checkpoint via `/session update`

---

## 🛡️ Safety Features

**Emergency Stop Protocol**:
- Immediate work halt on user command
- State preservation in `.dzp-killswitch/`
- Resume from last checkpoint

**Escape Paths**:
- All agents have fallback strategies
- Never hang or fail silently
- Always ask rather than guess

**Session Monitoring**:
- 4-hour initial alert
- 6-hour critical threshold (high-risk operation blocking)
- 8-hour maximum (read-only mode enforcement)

**Validation**:
- Protocol validation via `scripts/validate-protocol.py`
- Pre-commit hooks for state file schema compliance
- GitHub Actions workflow for CI validation

---

## 📦 What's New in v8.13.0

### PATCH-SESSION-005: Toji External Auditor
Added Toji Fushiguro (Sentinel) as the 10th Domain Zero agent — an independent external auditor with zero execution privileges.

**Key Additions**:
- `protocol/toji.agent.md` (v1.2.0) — 6 review domains, 8 review modes, structured report output
- Position: EXTERNAL — not governed by Gojo, Sukuna, or any resident agent
- REPORT-ONLY: Never generates code, implements fixes, or modifies artifacts
- Tool Access Matrix expanded to 10 columns
- `.github/copilot-instructions.md` fully synced to v8.13.0
- `AI_INSTRUCTIONS.md` updated with Toji references
- `~/.claude/agents/toji.md` Claude Code agent stub created

---

## 📦 What's New in v8.12.0

### PATCH-SESSION-004: Session Monitoring Enhancement
Closes critical coverage gap (70-85% → 85-90%) identified through adversarial analysis. PATCH-SESSION-003 was vulnerable to context compaction, agent bypass, and prompt non-compliance.

**5 Defensive Layers**:
1. **Configurable Debounce** - Adjustable alert frequency (15-60 min range) via `protocol.config.yaml` + CLI `--debounce` flag
2. **Compaction-Resistant Markers** - HTML comments protect AUTO-INVOKED section in `gojo.agent.md` from context compaction removal
3. **Alert Tracking Dashboard** - `session-monitoring-report.py` detects alert undercount and verifies section integrity
4. **Verification Script** - `scripts/verify-auto-invoked.py` for CI/CD validation (exit codes 0/1)
5. **Invocation Tracking** - Tracks agent bypass patterns (direct vs routed invocations), detects 10-15% coverage gap

**Bug Fix**: Windows compatibility - replaced 20+ Unicode emojis with ASCII equivalents in `session_monitor.py` (resolves `UnicodeEncodeError` on Windows cmd.exe).

See [CHANGELOG.md](CHANGELOG.md#8120---2025-12-29) for full details.

---

## 📦 What's New in v8.11.0 (Previous Release)

### Session Management Skill
Unified interface for work session tracking via `/session` slash command:
- 6 commands: start, status, update, break, continue, end
- Checkpoint file syncing (dev-notes, project-state, domain.record, security-review, session-state)
- Gojo-owned skill with domain.record.md write access

### TS Troubleshooting Tier System
5-tier hybrid bug resolution workflow via `/ts` slash command:
- Tier 1-4: Progressive escalation (Yuuji + Megumi, then + support agents)
- Tier 5 (Codered): All 9 agents, mandatory plan mode
- Hybrid escalation: severity-based initial tier + auto-escalation after failed attempts
- 9 commands: tier1, tier2, tier3, tier4, codered, status, history, escalate, complete

### DZP ROE v2.0.0 (Refactored)
- 46.9% size reduction (15KB → 8.5KB) for faster post-compaction reference
- Parallel workflow enforcement (validation checklist, imperative MUST/MUST NOT language)
- Anti-pattern examples (show what NOT to do)
- Gojo-owned (was ALL agents)

See [AI_INSTRUCTIONS.md](AI_INSTRUCTIONS.md#whats-new-in-v8110) for full changelog.

---

## 🔗 Links & Resources

**Canonical Source**: https://github.com/DewyHRite/Domain-Zero-Protocol

**Documentation**:
- [Installation Guide](docs/installation/IMPLEMENTATION_GUIDE.md)
- [Quick Start](PROTOCOL_QUICKSTART.md)
- [FAQ](docs/FAQ.md)
- [Security Policy](SECURITY.md)

**Agent Specifications**:
- [Gojo (Mission Control)](protocol/gojo.agent.md)
- [Yuuji (Implementation)](protocol/yuuji.agent.md)
- [Megumi (Security)](protocol/megumi.agent.md)
- [Nobara (Creative/UX)](protocol/nobara.agent.md)
- [Todo (Database)](protocol/todo.agent.md)
- [Maki (Performance)](protocol/maki.agent.md)
- [Panda (Build/CI)](protocol/panda.agent.md)
- [Inumaki (API)](protocol/inumaki.agent.md)
- [Sukuna (System Updates)](protocol/sukuna.agent.md)

---

## 📜 License

Domain Zero Protocol is released under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please read the contribution guidelines and submit pull requests to the canonical repository.

---

**Domain Zero Protocol v8.13.0**
**AI-Assisted Development Done Right**

