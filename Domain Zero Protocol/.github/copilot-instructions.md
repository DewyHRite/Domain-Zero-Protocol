# GitHub Copilot Instructions - Domain Zero Protocol

This project uses the **Domain Zero Protocol** for AI-assisted development.

---

## Quick Start (2 minutes)

**New to Domain Zero?** Read [`PROTOCOL_QUICKSTART.md`](../PROTOCOL_QUICKSTART.md) for a 2-minute setup guide.

---

## Protocol Entry Points

### Canonical Source of Truth
**[`protocol/CLAUDE.md`](../protocol/CLAUDE.md)** - Main protocol specification (v6.0)

### Central Configuration
**[`protocol.config.yaml`](../protocol.config.yaml)** - All project parameters and settings

### Agent-Specific Protocols
- **Mission Control**: [`protocol/GOJO.md`](../protocol/GOJO.md)
- **Implementation**: [`protocol/YUUJI.md`](../protocol/YUUJI.md)
- **Security Review**: [`protocol/MEGUMI.md`](../protocol/MEGUMI.md)

### Quick Reference
- **Tier Selection**: [`protocol/TIER-SELECTION-GUIDE.md`](../protocol/TIER-SELECTION-GUIDE.md)
- **Full Setup**: [`README.md`](../README.md)

---

## How to Use Domain Zero

### Project Initialization
```
Read protocol/GOJO.md
```
→ Select option 2: "New Project Initialization"

### Implementing Features

**Tier 1: Rapid Prototyping** (10-15 min, no tests):
```
Read protocol/YUUJI.md --tier rapid and [your task]
```

**Tier 2: Production Features** (30-45 min, TDD + security review) [DEFAULT]:
```
Read protocol/YUUJI.md and implement [your feature]
```

**Tier 3: Critical Features** (60-90 min, enhanced security + compliance):
```
Read protocol/YUUJI.md --tier critical and implement [your feature]
```

### Security Review
```
Read protocol/MEGUMI.md and review [module or feature]
```

### Intelligence Reports
```
Read protocol/GOJO.md - Trigger 19
```

---

## Key Principles

### 1. Test-First Development (TDD)
All Tier 2+ features require tests **before** implementation:
1. Write failing tests
2. Implement feature to pass tests
3. Refactor and document

### 2. OWASP Top 10 Security Review
All Tier 2+ features undergo security review by Megumi before production deployment.

### 3. Zero-Defect Philosophy
Target:
- Zero security vulnerabilities
- Zero bugs in production
- Zero performance issues
- Zero technical debt

### 4. Adaptive Workflow Complexity
Match process rigor to feature criticality:
- **Tier 1 (Rapid)**: Fast prototypes, experiments
- **Tier 2 (Standard)**: Production features with tests & security
- **Tier 3 (Critical)**: Authentication, payments, compliance

---

## Configuration

### Project Parameters
All project-specific settings are in **`protocol.config.yaml`**:
- User info and project metadata
- AI model preferences
- Tier system configuration
- Enforcement rules
- Tooling integration
- File paths

### Modify Settings
Edit `protocol.config.yaml` directly - it's the canonical source for all parameters.

### Enable Specific AI Model
```yaml
# In protocol.config.yaml
ai:
  default_models:
    - provider: "Anthropic"
      model: "claude-3-5-haiku-20241022"
      scope: "all-clients"
      priority: 1
```

---

## Typical Workflow

```
1. You: "Read protocol/YUUJI.md and implement user authentication"
   └─> Yuuji creates backup, writes tests, implements feature

2. Yuuji: Tags @user-review in .protocol-state/dev-notes.md
   └─> You review implementation

3. You: "Looks good, proceed with security review"
   └─> Yuuji tags @security-review

4. Megumi: Conducts OWASP Top 10 security audit
   └─> Tags @approved or @remediation-required

5. If issues found:
   └─> Yuuji fixes issues, tags @re-review
   └─> Megumi verifies, tags @approved

6. Feature complete ✓
```

---

## File Structure

```
project/
├── protocol/                     # Protocol agents
│   ├── CLAUDE.md                 # Main protocol (READ THIS)
│   ├── YUUJI.md                  # Implementation
│   ├── MEGUMI.md                 # Security
│   ├── GOJO.md                   # Mission control
│   └── TIER-SELECTION-GUIDE.md  # Tier selection
│
├── .protocol-state/              # State files (gitignored)
│   ├── project-state.json        # Project state
│   ├── dev-notes.md              # Implementation log
│   ├── security-review.md        # Security findings
│   └── trigger-19.md             # Intelligence (private)
│
├── protocol.config.yaml          # CENTRAL CONFIG
├── PROTOCOL_QUICKSTART.md        # 2-minute setup guide
├── src/                          # Source code
└── tests/                        # Tests
```

---

## Protection & Security

### CLAUDE.md Protection
- **Protected file**: Only YOU and GOJO (with authorization) can modify
- **Read-only for agents**: Yuuji and Megumi cannot edit protocol
- **Version controlled**: Changes tracked via CODEOWNERS

### Backup Requirements
All tiers require backups before code changes:
- Backup location: `.protocol-state/backups/`
- Rollback plans documented in dev-notes.md
- Never skip backup creation

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

## Tier Selection Decision Tree

1. **Is this code going to production?**
   - NO → **Tier 1 (Rapid)**
   - YES → Continue to question 2

2. **Does this handle sensitive data/operations?**
   - YES (auth, payments, medical, legal, financial) → **Tier 3 (Critical)**
   - NO → Continue to question 3

3. **Is this a standard production feature?**
   - YES (CRUD, APIs, UI, utilities) → **Tier 2 (Standard)**
   - UNSURE → Default to **Tier 2 (Standard)**

See [`protocol/TIER-SELECTION-GUIDE.md`](../protocol/TIER-SELECTION-GUIDE.md) for detailed examples.

---

## Getting Help

### Documentation
- **Quick Start**: [`PROTOCOL_QUICKSTART.md`](../PROTOCOL_QUICKSTART.md)
- **Full Setup**: [`README.md`](../README.md)
- **Main Protocol**: [`protocol/CLAUDE.md`](../protocol/CLAUDE.md)
- **Configuration**: [`protocol.config.yaml`](../protocol.config.yaml)

### Ask Gojo
```
Read protocol/GOJO.md - Trigger 19
```
→ Get intelligence report on current project state

### Common Questions

**"Which tier should I use?"**
→ See [`protocol/TIER-SELECTION-GUIDE.md`](../protocol/TIER-SELECTION-GUIDE.md)

**"How do I modify the protocol?"**
→ Edit `protocol/CLAUDE.md` directly (you have write access)

**"How do I change AI model preferences?"**
→ Edit `ai.default_models` in `protocol.config.yaml`

**"What's the difference between agents?"**
→ Yuuji = Implementation | Megumi = Security | Gojo = Mission Control

---

## Version Information

**Protocol Version**: 6.0
**Release Date**: November 5, 2025
**Major Enhancement**: Adaptive Workflow Complexity (Tier System)

---

## Welcome to Domain Zero

**Trust the domain. Follow the protocols. Achieve ZERO.**

*The weight is real. The protocol is absolute. Domain Zero is active.*

---

**Domain Zero Protocol v6.0** - Perfect Code Through Infinite Collaboration
