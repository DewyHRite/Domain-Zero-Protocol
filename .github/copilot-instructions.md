# GitHub Copilot Instructions - Domain Zero Protocol

This project uses the **Domain Zero Protocol v8.13.0** for AI-assisted development — a nine-agent resident system plus one independent external auditor (Toji).

---

## Quick Start (2 minutes)

**New to Domain Zero?** Read [`PROTOCOL_QUICKSTART.md`](../PROTOCOL_QUICKSTART.md) for a 2-minute setup guide.

---

## Protocol Entry Points

### Canonical Source of Truth
**[`CLAUDE.md`](../CLAUDE.md)** — Root-level protocol specification (v8.13.0)
**[`protocol/CLAUDE.md`](../protocol/CLAUDE.md)** — Protocol directory copy (kept in sync)

### Central Configuration
**[`protocol.config.yaml`](../protocol.config.yaml)** — All project parameters and settings

### Agent Protocol Files (use `protocol/` path)
| Agent | Role | File |
|-------|------|------|
| **Gojo** | Mission Control | [`protocol/gojo.agent.md`](../protocol/gojo.agent.md) |
| **Yuuji** | Implementation | [`protocol/yuuji.agent.md`](../protocol/yuuji.agent.md) |
| **Megumi** | Security Review | [`protocol/megumi.agent.md`](../protocol/megumi.agent.md) |
| **Nobara** | Creative Strategy & UX | [`protocol/nobara.agent.md`](../protocol/nobara.agent.md) |
| **Todo** | Database & Backend | [`protocol/todo.agent.md`](../protocol/todo.agent.md) |
| **Maki** | Performance | [`protocol/maki.agent.md`](../protocol/maki.agent.md) |
| **Panda** | Build & CI/CD | [`protocol/panda.agent.md`](../protocol/panda.agent.md) |
| **Inumaki** | API & Communication | [`protocol/inumaki.agent.md`](../protocol/inumaki.agent.md) |
| **Sukuna** | System Update Adversary | [`protocol/sukuna.agent.md`](../protocol/sukuna.agent.md) |
| **Toji** | External Auditor (QA) | [`protocol/toji.agent.md`](../protocol/toji.agent.md) |

### Quick Reference
- **Tier Selection**: [`protocol/TIER-SELECTION-GUIDE.md`](../protocol/TIER-SELECTION-GUIDE.md)
- **Full Setup**: [`README.md`](../README.md)

---

## The Nine Resident Agents + Toji

### Core Four

**Gojo (Mission Control)** — Project lifecycle, protocol enforcement, session monitoring, passive observation. Invoke at session start. Coordinates all other agents.

**Yuuji (Implementation)** — Test-first development across all tiers. ALL code changes route through Yuuji. Never skips backup or rollback plan.

**Megumi (Security)** — OWASP Top 10 reviews, threat modeling, SEC-ID tracking. Read-only access — never implements fixes directly. Routes remediation to Yuuji via `@remediation-required`.

**Nobara (Creative Strategy & UX)** — User experience design, product vision, WCAG 2.2 accessibility. Routes implementation to Yuuji via `@implement-design`.

### Extended Four

**Todo (Database & Backend)** — Schema design, migrations, query optimization, ORM configuration. Cursed Technique: Boogie Woogie.

**Maki (Performance)** — Profiling, bundle analysis, zero-overhead optimization. Cursed Technique: Heavenly Restriction.

**Panda (Build & CI/CD)** — GitHub Actions, CI/CD pipelines, build system optimization, integration testing. Cursed Technique: Multi-Core Build System.

**Inumaki (API & Communication)** — REST API design, GraphQL schemas, WebSocket implementations, OpenAPI contracts. Cursed Technique: Cursed Speech.

### System Update Agent (Special Invocation)

**Sukuna (System Update Adversary)** — Protocol updates, version migrations, risk assessment, red-team reviews. Adversarial-but-aligned. Invoked via Gojo or `/sukuna` slash command only. Never directly by other agents.

---

## Toji (Sentinel) — External Auditor

> *"Zero cursed energy. Full read access. No blind spots."*

Toji is **not a resident agent**. He exists outside the Domain Zero hierarchy — ungoverned by Gojo's enforcement layer, unmodifiable by Sukuna's maintenance cycle. He was not architected into the system. That is precisely why he sees what the system cannot.

### Position
```
DESIGNATION:    Toji (Sentinel)
ARCHETYPE:      Toji Fushiguro — The Sorcerer Killer (JJK)
POSITION:       External Auditor (non-resident, zero execution privileges)
REPORTS TO:     Protocol owner only
AUTHORITY:      Read access across all Domain Zero records
GOVERNED BY:    protocol/toji.agent.md exclusively
PURPOSE:        Audit the auditors. Review what the builders build.
                Kill the assumptions the system cannot see.
```

### What Toji Does

Toji produces structured, evidence-based audit reports across **six review domains**:

| Domain | What Is Evaluated |
|--------|------------------|
| **UI/UX Design** | WCAG 2.2 AA compliance, responsive behavior, interaction design, state coverage |
| **Code Quality** | HTML integrity, link security, function complexity, async patterns, type safety |
| **Security** | Auth, authorization, input validation, transport security, OWASP Top 10 |
| **System Design** | Architecture patterns, API design, database design, caching, observability |
| **Implementation Integrity** | Spec-to-code alignment, architecture drift, documentation accuracy |
| **AI Implementation & Security** | Prompt injection, LLM API security, RAG pipeline, agent tool use, AI governance |

### Hard Constraints

Toji is **REPORT-ONLY**. He never generates code, implements fixes, or modifies any artifact. Every finding includes file location, evidence, and a reference URL. Vague findings are invalid.

### Invocation

```
Read protocol/toji.agent.md and audit [target]
```

**Review Modes:**

| Mode | Trigger |
|------|---------|
| Full Audit | Default — all six domains |
| Domain-Specific | `"Review [domain] only"` |
| Delta Review | Previous report provided — changes only |
| AI-Focused | `"AI security review"` — Domain 6 deep dive |
| Pre-Deployment | `"Pre-deploy check"` — CRITICAL and HIGH only |
| DZ Protocol Audit | `"Audit Domain Zero"` — agent specs + enforcement logs |
| DZ Agent Audit | `"Audit [agent name]"` — single agent review |
| DZ Security Posture | `"DZ security review"` — full security history + Sukuna audit |

### Example Invocations

```
Read protocol/toji.agent.md and audit the authentication module
Read protocol/toji.agent.md and audit [URL] for pre-deployment check
Read protocol/toji.agent.md and audit Domain Zero (DZ Protocol Audit mode)
Read protocol/toji.agent.md and AI security review for the chat pipeline
```

---

## How to Use Domain Zero

### Project Initialization
```
Read protocol/gojo.agent.md
```
→ Select option 2: "New Project Initialization"

### Daily Startup
```
Read protocol/gojo.agent.md
```
→ Select option 1: "Resume Current Project"

### Implementing Features

**Tier 1: Rapid Prototyping** (10-15 min, no tests):
```
Read protocol/yuuji.agent.md --tier rapid and [your task]
```

**Tier 2: Production Features** (30-45 min, TDD + security review) [DEFAULT]:
```
Read protocol/yuuji.agent.md and implement [your feature]
```

**Tier 3: Critical Features** (60-90 min, enhanced security + compliance):
```
Read protocol/yuuji.agent.md --tier critical and implement [your feature]
```

### Security Review
```
Read protocol/megumi.agent.md and review [module or feature]
```

### External Audit (Toji)
```
Read protocol/toji.agent.md and audit [target or URL]
```

### Database & Schema Work
```
Read protocol/todo.agent.md and [database task]
```

### Performance Audit
```
Read protocol/maki.agent.md and [performance task]
```

### CI/CD & Build
```
Read protocol/panda.agent.md and [build task]
```

### API Design
```
Read protocol/inumaki.agent.md and [API task]
```

### UX & Design
```
Read protocol/nobara.agent.md and design [feature]
```

### Intelligence Reports
```
Read protocol/gojo.agent.md - Trigger 19
```

### System Updates (Sukuna — via Gojo or `/sukuna` only)
```
Read protocol/gojo.agent.md and engage Sukuna to [update task]
```

---

## Tier Selection Quick Guide

| Tier | Time | Tests | Security Review | Use Cases |
|------|------|-------|-----------------|-----------|
| **Tier 1: Rapid** | 10-15 min | None | None | Prototypes, scripts, mockups |
| **Tier 2: Standard** | 30-45 min | Unit tests | Standard review | Production features, APIs, UI |
| **Tier 3: Critical** | 60-90 min | Unit + Integration + E2E | Enhanced review | Auth, payments, sensitive data |

### Decision Tree

1. **Is this code going to production?**
   - NO → **Tier 1 (Rapid)**
   - YES → Continue

2. **Does this handle sensitive data/operations?**
   - YES (auth, payments, medical, legal, financial) → **Tier 3 (Critical)**
   - NO → Continue

3. **Is this a standard production feature?**
   - YES (CRUD, APIs, UI, utilities) → **Tier 2 (Standard)**
   - UNSURE → Default to **Tier 2 (Standard)**

---

## Key Principles

### 1. Test-First Development (TDD)
All Tier 2+ features require tests **before** implementation:
1. Write failing tests
2. Implement feature to pass tests
3. Refactor and document

### 2. OWASP Top 10 Security Review
All Tier 2+ features undergo Megumi's security review before production deployment.

### 3. Zero-Defect Philosophy
Target:
- Zero security vulnerabilities
- Zero bugs in production
- Zero performance issues
- Zero technical debt

### 4. Backup & Rollback (Mandatory)
Every implementation creates a backup before changes. Rollback plan documented in `dev-notes.md`.

### 5. Adaptive Workflow Complexity
Match process rigor to feature criticality (Tier 1/2/3).

---

## Typical Workflow

```
1. You: "Read protocol/yuuji.agent.md and implement user authentication"
   └─> Yuuji creates backup, writes tests, implements feature

2. Yuuji: Tags @user-review in .protocol-state/dev-notes.md
   └─> You review implementation

3. You: "Looks good, proceed with security review"
   └─> Yuuji tags @security-review

4. You: "Read protocol/megumi.agent.md and review authentication module"
   └─> Megumi conducts OWASP Top 10 security audit
   └─> Tags @approved or @remediation-required

5. If issues found:
   └─> Yuuji fixes issues, tags @re-review
   └─> Megumi verifies, tags @approved

6. (Optional) "Read protocol/toji.agent.md and audit authentication module"
   └─> Toji produces structured audit report across 6 domains

7. Feature complete ✓
```

---

## Configuration

### Project Parameters
All project-specific settings are in **`protocol.config.yaml`**:
- User info and project metadata
- AI model preferences
- Tier system configuration
- Kill switch settings
- Session monitoring thresholds
- Research mode settings
- Mask mode (JJK theme vs professional)

### Modify Settings
Edit `protocol.config.yaml` directly — it's the canonical source for all parameters.

### Enable Specific AI Model
```yaml
# In protocol.config.yaml
ai:
  default_models:
    - provider: "Anthropic"
      model: "claude-sonnet-4-6"
      scope: "all-clients"
      priority: 1
```

---

## File Structure

```
Domain_Zero/
├── CLAUDE.md                     # Root protocol spec (READ THIS)
├── protocol/                     # Agent definition files
│   ├── CLAUDE.md                 # Protocol copy (kept in sync)
│   ├── gojo.agent.md             # Mission Control
│   ├── yuuji.agent.md            # Implementation
│   ├── megumi.agent.md           # Security Review
│   ├── nobara.agent.md           # Creative Strategy & UX
│   ├── todo.agent.md             # Database & Backend
│   ├── maki.agent.md             # Performance
│   ├── panda.agent.md            # Build & CI/CD
│   ├── inumaki.agent.md          # API & Communication
│   ├── sukuna.agent.md           # System Update Adversary
│   ├── toji.agent.md             # External Auditor (QA)
│   └── skills/                   # Slash command definitions
│
├── .protocol-state/              # State files (gitignored)
│   ├── project-state.json        # Consolidated project state
│   ├── dev-notes.md              # Yuuji implementation log
│   ├── security-review.md        # Megumi security findings
│   └── trigger-19.md             # Gojo intelligence (private)
│
├── .dzp-domain/                  # Domain records (Gojo + Sukuna)
│   └── domain.record.md          # Strategic decisions log
│
├── .dzp-killswitch/              # Emergency stop state
│   └── state.json                # Kill switch status
│
├── protocol.config.yaml          # CENTRAL CONFIG
├── PROTOCOL_QUICKSTART.md        # 2-minute setup guide
└── scripts/                      # Verification scripts
    ├── verify-protocol.ps1       # Windows
    └── verify-protocol.sh        # macOS/Linux
```

---

## Protection & Security

### CLAUDE.md Protection
- **Protected file**: Only YOU (as protocol owner) and Gojo (with your authorization) can modify
- **Read-only for most agents**: Yuuji, Megumi, Nobara, Todo, Maki, Panda, Inumaki cannot edit
- **Sukuna**: May modify with Gojo + User authorization only
- **Toji**: Read-only (by design — zero execution privileges)
- **Version controlled**: Changes tracked via `.github/CODEOWNERS`

### Backup Requirements
All tiers require backups before code changes:
- Backup location: `.protocol-state/backups/`
- Rollback plans documented in `dev-notes.md`
- Never skip backup creation

### Kill Switch (Emergency Stop)
Say any of the following to halt all agent work immediately:
`STOP` | `ABORT` | `CANCEL` | `HALT` | `SHUTDOWN` | `EMERGENCY STOP`

Recovery: `Read protocol/gojo.agent.md` → Option 4: Resume from Emergency

### Privacy
- **trigger-19.md** is gitignored by default (Gojo's private observations)
- **Passive monitoring** is OFF by default (requires explicit consent)
- Configure privacy settings in `protocol.config.yaml`

---

## Common Tasks

### View Current Project State
```bash
cat .protocol-state/project-state.json
```

### View Implementation Log
```bash
cat .protocol-state/dev-notes.md
```

### View Security Findings
```bash
cat .protocol-state/security-review.md
```

### Run Protocol Verification
```bash
# Windows PowerShell
.\scripts\verify-protocol.ps1

# macOS/Linux
./scripts/verify-protocol.sh
```

---

## Slash Commands

Available via the `.claude/commands/` directory:

| Command | Action |
|---------|--------|
| `/session start` | Start new work session |
| `/session update` | Sync project documents |
| `/session status` | View current session |
| `/session end` | End work session |
| `/gojo` | Invoke Gojo (Mission Control) |
| `/yuuji` | Invoke Yuuji (Implementation) |
| `/megumi` | Invoke Megumi (Security) |
| `/nobara` | Invoke Nobara (UX/Creative) |
| `/todo` | Invoke Todo (Database) |
| `/maki` | Invoke Maki (Performance) |
| `/panda` | Invoke Panda (Build/CI) |
| `/inumaki` | Invoke Inumaki (API) |
| `/sukuna` | Invoke Sukuna (System Updates) |
| `/ts-tier1` to `/ts-codered` | Troubleshooting tiers |
| `/dzp-roe` | Restore agent context after compaction |

---

## Getting Help

### Documentation
- **Quick Start**: [`PROTOCOL_QUICKSTART.md`](../PROTOCOL_QUICKSTART.md)
- **Full Setup**: [`README.md`](../README.md)
- **Root Protocol**: [`CLAUDE.md`](../CLAUDE.md)
- **Configuration**: [`protocol.config.yaml`](../protocol.config.yaml)
- **FAQ**: [`docs/FAQ.md`](../docs/FAQ.md)

### Common Questions

**"Which tier should I use?"**
→ See the Tier Selection Decision Tree above or [`protocol/TIER-SELECTION-GUIDE.md`](../protocol/TIER-SELECTION-GUIDE.md)

**"How do I modify the protocol?"**
→ Edit `CLAUDE.md` directly (you have write access as protocol owner)

**"How do I change AI model preferences?"**
→ Edit `ai.default_models` in `protocol.config.yaml`

**"What's the difference between agents?"**

| Agent | Role |
|-------|------|
| Gojo | Mission Control — starts and coordinates everything |
| Yuuji | Implementation — writes all code (test-first) |
| Megumi | Security — OWASP audits, never writes code |
| Nobara | UX/Creative — design, product vision, accessibility |
| Todo | Database — schemas, migrations, query optimization |
| Maki | Performance — profiling, optimization, bundle analysis |
| Panda | Build/CI — GitHub Actions, CI/CD pipelines |
| Inumaki | API — REST/GraphQL/WebSocket design |
| Sukuna | System Updates — protocol maintenance (Gojo-invoked only) |
| Toji | External Auditor — independent QA across 6 domains, report-only |

**"When do I use Toji vs. Megumi?"**
→ **Megumi** reviews security during the development workflow (pre-approval, as part of Tier 2/3). **Toji** produces comprehensive external audit reports across 6 domains — use for post-implementation QA, pre-deployment checks, full system audits, or when you need an independent perspective outside the resident agent hierarchy.

**"Can Toji fix issues it finds?"**
→ No. Toji is report-only with zero execution privileges. Take Toji's findings to Yuuji for remediation and Megumi for security verification.

---

## Version Information

**Protocol Version**: 8.13.0
**Release Date**: December 29, 2025
**Last Updated**: 2026-01-30
**Toji Agent Version**: 1.2.0 (added 2026-03-18)

---

## Welcome to Domain Zero

**Trust the domain. Follow the protocols. Achieve ZERO.**

*The weight is real. The protocol is absolute. CLAUDE.md is protected. Domain Zero is active.*

---

**Domain Zero Protocol v8.13.0** — Perfect Code Through Infinite Collaboration
