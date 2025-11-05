# Domain Zero Protocol v6.0
## AI-Powered Development Framework with Security-First Approach

**"Perfect Code Through Infinite Collaboration"**

Domain Zero is a three-agent AI development system that provides specialized expertise through distinct AI personalities, operating under absolute protocol authority with test-first development, comprehensive security review, and adaptive workflow complexity.

---

## 📋 Table of Contents

- [What is Domain Zero?](#-what-is-domain-zero)
- [Prerequisites & Optional Integrations](#-prerequisites--optional-integrations)
- [Quick Setup](#-quick-setup)
- [AI Assistant Integration & Canonical Source](#-ai-assistant-integration--canonical-source)
- [Adaptive Workflow Complexity (Tier System)](#-adaptive-workflow-complexity-tier-system)
- [Tier Selection Guide](#-tier-selection-guide)
- [Typical Workflow](#-typical-workflow)
- [File Structure](#-file-structure)
- [Learning Path](#-learning-path)
- [Security Features](#-security-features)
- [Productivity Gains](#-productivity-gains-observed-estimates)
- [Common Commands](#-common-commands)
- [Success Criteria](#-success-criteria)
- [Documentation](#-documentation)
- [Getting Help](#-getting-help)
- [License](#-license)

---

## 📦 Distribution Package Contents

This distribution includes everything you need to deploy Domain Zero:

**Core Protocol Files** (`protocol/`):
- `CLAUDE.md` - Main protocol specification (v6.0)
- `YUUJI.md` - Implementation agent protocol
- `MEGUMI.md` - Security review agent protocol
- `GOJO.md` - Mission control agent protocol
- `TIER-SELECTION-GUIDE.md` - Quick reference for tier selection
- `GOJO-UPDATES-PATCH.md` - Protocol change audit trail

**State Templates** (`.protocol-state/`):
- `project-state.json` - Project configuration template
- `dev-notes.md` - Implementation log template
- `security-review.md` - Security findings template
- `trigger-19.md` - Intelligence report template (gitignored by default)
- `tier-system-specification.md` - Technical tier system specification

**Setup Files**:
- `README.md` - This file (comprehensive setup guide)
- `AI_INSTRUCTIONS.md` - Cross-assistant discovery shim (redirects to CLAUDE.md)
- `.gitignore` - Privacy-focused git configuration
- `LICENSE` - MIT License
- `CODEOWNERS` - Protocol file protection rules

**Integration Scripts** (`scripts/`):
- `update-instructions.ps1` - PowerShell script to append protocol pointers (Windows)
- `update-instructions.sh` - Bash script to append protocol pointers (macOS/Linux)

**CI/CD Templates** (`.github/workflows/`):
- `security-scan-example.yml` - GitHub Actions security scanning template

---

## 🔧 Prerequisites & Optional Integrations

### Required
- **AI Assistant Access**: Access to Claude (via Anthropic, Claude.ai, or API)
- **Git**: Version control for change tracking and CODEOWNERS enforcement
- **Text Editor**: Any editor for viewing/editing markdown files

### Recommended (Optional but Beneficial)

**Security & Quality Tools** (integrates with Tier 2 & 3):
- **SAST** (Static Application Security Testing): Snyk Code, SonarQube, Semgrep, CodeQL
- **SCA** (Software Composition Analysis): Snyk Open Source, Dependabot, WhiteSource
- **DAST** (Dynamic Application Security Testing): OWASP ZAP, Burp Suite (for web apps)
- **IaC Scanning**: Snyk Infrastructure as Code, Checkov, tfsec (for Terraform/K8s)

**Testing Frameworks** (per language):
- Python: pytest, unittest
- JavaScript/TypeScript: Jest, Mocha, Vitest
- Java: JUnit, TestNG
- Go: testing package, testify
- Ruby: RSpec, Minitest
- C#: xUnit, NUnit, MSTest

**CI/CD Integration**:
- GitHub Actions, GitLab CI, Jenkins, CircleCI (for automated workflows)
- Branch protection rules and required status checks

**Development Tools**:
- Pre-commit hooks (for local validation)
- Code formatters (Black, Prettier, gofmt, etc.)
- Linters (ESLint, Pylint, RuboCop, etc.)

_Note: Domain Zero works standalone without these tools, but integration enhances measurable security coverage and automates validation._

---

## 🌀 What is Domain Zero?

Domain Zero creates a **controlled collaboration space** where three specialized AI agents work together to deliver production-ready code with zero defects.

### The Three Agents

**🔥 YUUJI ITADORI** - Implementation Specialist
- Test-first development (TDD)
- Feature implementation
- Bug fixes and remediation
- Documentation

**⚡ MEGUMI FUSHIGURO** - Security Analyst
- OWASP Top 10 security review
- Vulnerability detection
- Performance analysis
- Code approval/rejection

**♾️ SATORU GOJO** - Mission Control
- Project lifecycle management
- Passive observation & intelligence
- Protocol enforcement
- Team coordination

---

## 🚀 Quick Setup

### Step 1: Copy Protocol to Your Project

**macOS/Linux (bash/zsh)**:
```bash
# Copy the entire protocol structure to your project root
cp -r "Domain Zero Protocol/protocol" your-project/
cp -r "Domain Zero Protocol/.protocol-state" your-project/
cp "Domain Zero Protocol/.gitignore" your-project/
```

**Windows (PowerShell)**:
```powershell
# Copy the entire protocol structure to your project root
Copy-Item -Recurse -Force "Domain Zero Protocol\protocol" -Destination "your-project\"
Copy-Item -Recurse -Force "Domain Zero Protocol\.protocol-state" -Destination "your-project\"
Copy-Item -Force "Domain Zero Protocol\.gitignore" -Destination "your-project\"
```

**Windows (Command Prompt)**:
```cmd
REM Copy the entire protocol structure to your project root
xcopy /E /I /Y "Domain Zero Protocol\protocol" "your-project\protocol"
xcopy /E /I /Y "Domain Zero Protocol\.protocol-state" "your-project\.protocol-state"
copy /Y "Domain Zero Protocol\.gitignore" "your-project\"
```

### Step 2: Update Project Metadata

Edit `.protocol-state/project-state.json`:
```json
{
  "project_metadata": {
    "name": "YOUR_PROJECT_NAME",
    "description": "Your project description",
    "created": "2025-11-05T00:00:00Z",
    "last_updated": "2025-11-05T00:00:00Z"
  }
}
```

### Step 3: Initialize with Gojo

In your AI assistant (Claude):
```
"Read protocol/GOJO.md"
```

Gojo will present Mission Control with 3 options:
1. Resume Current Project
2. **New Project Initialization** ← Select this
3. Trigger 19 Intelligence Report

### Step 4: Start Implementing

```
"Read protocol/YUUJI.md and implement [your feature]"
```

---

## 🤖 AI Assistant Integration & Canonical Source

**Domain Zero Protocol uses `protocol/CLAUDE.md` as the canonical source of truth.**

### Cross-Assistant Compatibility

Domain Zero works with any AI assistant that can read markdown files:

**✅ Supported Assistants**:
- Claude (Anthropic) - via Claude.ai, API, or Claude Code
- GitHub Copilot - via `.github/copilot-instructions.md`
- Cursor - via `.cursorrules` or project instructions
- Cody (Sourcegraph) - via project context
- Tabnine - via project instructions
- Any AI assistant with file reading capabilities

### Discovery Files

To ensure AI assistants discover the protocol, we provide multiple entry points:

**`AI_INSTRUCTIONS.md`** (included in distribution):
- Primary discovery file for most AI tools
- Simple redirect/shim to `protocol/CLAUDE.md`
- Works cross-assistant without duplication

**Why This Structure?**:
- **Single source of truth**: `protocol/CLAUDE.md` is authoritative
- **No duplication**: Prevents drift between instruction files
- **Protected**: CLAUDE.md is version-controlled with CODEOWNERS
- **Discoverable**: Multiple entry points all redirect to canonical source

### Integrating with Existing Instructions

If you already have AI instruction files (e.g., `.github/copilot-instructions.md`, `.cursorrules`, `CONTRIBUTING.md`), you can safely append a protocol pointer without replacing your existing content.

**Manual Integration**:

Add this section to your existing instruction files:

```markdown
## Domain Zero Protocol

This project follows the Domain Zero Protocol for AI-assisted development.

**Primary entrypoint**: [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

**Workflow guidance**:
- Mission Control: `protocol/GOJO.md`
- Implementation: `protocol/YUUJI.md`
- Security Review: `protocol/MEGUMI.md`
```

**Automated Integration** (Safe & Opt-In):

We provide scripts to safely append protocol pointers to existing files:

**Windows (PowerShell)**:
```powershell
# Dry-run (shows what would change)
.\scripts\update-instructions.ps1

# Actually update files
.\scripts\update-instructions.ps1 -Apply
```

**macOS/Linux (Bash)**:
```bash
# Dry-run (shows what would change)
./scripts/update-instructions.sh

# Actually update files
./scripts/update-instructions.sh --apply
```

**Script Features**:
- ✅ **Safe**: Dry-run mode by default
- ✅ **Idempotent**: Won't add duplicates
- ✅ **Backup**: Creates `.backup` files before modifying
- ✅ **Non-destructive**: Appends without replacing existing content
- ✅ **Reversible**: Easy to undo with backups

**What It Does**:
1. Scans for common instruction file patterns
2. Checks if protocol pointer already exists
3. Appends "Domain Zero Protocol" section if missing
4. Preserves all existing content

**Files Scanned**:
- `AI_INSTRUCTIONS.md`, `AI.md`
- `.github/copilot-instructions.md`, `.github/instructions/*.md`
- `.cursorrules`
- `CONTRIBUTING.md`, `DEVELOPMENT.md`
- `.vscode/instructions.md`, `.idea/instructions.md`

### Best Practices

**DO**:
- ✅ Always point to `protocol/CLAUDE.md` as canonical source
- ✅ Use provided shims (`AI_INSTRUCTIONS.md`) for discoverability
- ✅ Run updater scripts in dry-run mode first
- ✅ Keep protocol pointers brief (just redirect to CLAUDE.md)

**DON'T**:
- ❌ Duplicate protocol logic in multiple files
- ❌ Auto-rewrite CLAUDE.md into other instruction files
- ❌ Modify `protocol/CLAUDE.md` without going through proper authorization (see CODEOWNERS)

### Migration from Other Systems

If migrating from other AI instruction systems:

1. **Keep existing instructions**: Don't delete them
2. **Append protocol pointer**: Use updater scripts or manual addition
3. **Test incrementally**: Verify AI assistants find the protocol
4. **Gradual adoption**: Can run hybrid (existing + Domain Zero) during transition

---

## 🎯 Adaptive Workflow Complexity (Tier System)

Domain Zero v6.0 introduces **three workflow tiers** to match process rigor to feature criticality.

### TIER 1: RAPID 🚀 (10-15 minutes)

**Use Cases**: Prototypes, experiments, throwaway code, learning exercises

**What You Get**: Fast implementation, no tests, no security review, backup maintained

**Invocation**:
```
"Read protocol/YUUJI.md --tier rapid and create file renaming script"
```

---

### TIER 2: STANDARD ⚖️ (30-45 minutes) [DEFAULT]

**Use Cases**: Production features, CRUD operations, API endpoints, UI components

**What You Get**: Test-first development, full OWASP security review, comprehensive documentation, backup + rollback plan

**Invocation**:
```
"Read protocol/YUUJI.md and implement user authentication"
```

---

### TIER 3: CRITICAL 🔒 (60-90 minutes)

**Use Cases**: Authentication, payment processing, sensitive data, compliance requirements

**What You Get**: Enhanced testing (unit + integration + E2E), multi-model security review, risk prioritization, performance benchmarking, compliance analysis

**Invocation**:
```
"Read protocol/YUUJI.md --tier critical and implement Stripe payment processing"
```

---

## 📋 Tier Selection Guide

**Decision Tree**:

1. **Is this code going to production?**
   - NO → Tier 1 (Rapid)
   - YES → Continue to question 2

2. **Does this handle sensitive data/operations?**
   - YES (auth, payments, medical, legal, financial) → Tier 3 (Critical)
   - NO → Continue to question 3

3. **Is this a standard production feature?**
   - YES (CRUD, APIs, UI, utilities) → Tier 2 (Standard)
   - UNSURE → Default to Tier 2 (Standard)

**Quick Reference**: See `protocol/TIER-SELECTION-GUIDE.md` for detailed examples

---

## 🔄 Typical Workflow

### 1. Implementation Phase (Yuuji)

```
You: "Read protocol/YUUJI.md and implement user registration"

Yuuji:
- Creates backup
- Writes tests first (TDD)
- Implements feature to pass tests
- Documents in dev-notes.md
- Creates rollback plan
- Tags @user-review
```

### 2. User Review

```
You: Review the implementation in .protocol-state/dev-notes.md
You: "Looks good, proceed with security review"
```

### 3. Security Review (Megumi)

```
Yuuji: Tags @security-review
Megumi:
- Reads implementation
- Conducts OWASP Top 10 review
- Documents findings in security-review.md
- Tags @approved or @remediation-required
```

### 4. Remediation (if needed)

```
Yuuji: Fixes issues documented by Megumi
Yuuji: Tags @re-review
Megumi: Verifies fixes
Megumi: Tags @approved
```

### 5. Feature Complete ✓

---

## 📁 File Structure

After setup, your project will have:

```
your-project/
├── protocol/                        # Core protocol system
│   ├── CLAUDE.md                    # Main protocol (READ THIS FIRST)
│   ├── YUUJI.md                     # Implementation agent
│   ├── MEGUMI.md                    # Security agent
│   ├── GOJO.md                      # Mission control
│   ├── TIER-SELECTION-GUIDE.md     # Quick tier reference
│   └── GOJO-UPDATES-PATCH.md       # Protocol change log
│
├── .protocol-state/                 # State management (gitignored by default)
│   ├── project-state.json           # Project configuration
│   ├── dev-notes.md                 # Implementation log (Yuuji)
│   ├── security-review.md           # Security findings (Megumi)
│   ├── trigger-19.md                # Intelligence reports (Gojo, private)
│   └── tier-system-specification.md # Tier system details
│
├── src/                             # Your source code
├── tests/                           # Your tests
└── .gitignore                       # Git ignore (trigger-19.md excluded)
```

---

## 🎓 Learning Path

### New to Domain Zero?

1. **Read protocol/CLAUDE.md** - Understand the system (15 minutes)
2. **Read protocol/TIER-SELECTION-GUIDE.md** - Learn tier selection (5 minutes)
3. **Initialize with Gojo** - Set up your project (5 minutes)
4. **Try Tier 1 feature** - Fast prototyping practice (10 minutes)
5. **Try Tier 2 feature** - Full workflow experience (30 minutes)

### Recommended First Features

**Tier 1 Practice**:
```
"Read protocol/YUUJI.md --tier rapid and create a hello world script"
```

**Tier 2 Practice**:
```
"Read protocol/YUUJI.md and implement a simple todo list API"
```

**Tier 3 Practice** (when ready):
```
"Read protocol/YUUJI.md --tier critical and implement user authentication"
```

---

## 🔒 Security Features

Domain Zero is **security-first by design**:

- ✅ **OWASP Top 10** security review on all Tier 2+ features
- ✅ **Test-first development** (TDD) ensures functionality before deployment
- ✅ **Mandatory security review** before production (Tier 2+)
- ✅ **Risk-based prioritization** (P0/P1/P2/P3) for Tier 3
- ✅ **Multi-model security analysis** (dual LLM review, when available) for Tier 3
- ✅ **Compliance analysis** (PCI/HIPAA/SOC2) for Tier 3
- ✅ **Backup and rollback** requirements for ALL tiers

**Security Review Coverage** (Target Estimates):
- Tier 1 (Rapid): No security review (acceptable for non-production)
- Tier 2 (Standard): Target ~80% vulnerability detection (typical single-model review)
- Tier 3 (Critical): Target ~95% vulnerability detection (dual-model review, when available)

_Note: Detection rates are targets based on internal evaluations. Actual coverage varies by stack, tooling, and team expertise. Consider integrating SAST/SCA tools for measurable results._

---

## 📊 Productivity Gains (Observed Estimates)

**Compared to manual development**:

- **Tier 1**: Target ~70% faster for simple features (10-15 min vs 30-45 min)
- **Tier 2**: Balanced quality and speed (30-45 min)
- **Tier 3**: Target ~50% more thorough security analysis (60-90 min)

**Overall**: Observed ~50% average productivity gains across mixed workload in internal evaluations.

_Note: Productivity metrics are estimates from internal use. Actual gains vary significantly by team experience, tech stack, existing processes, and feature complexity. Your mileage may vary._

---

## 🛠️ Common Commands

### Agent Invocation

```bash
# Gojo (Mission Control)
"Read protocol/GOJO.md"
"Read protocol/GOJO.md - Trigger 19"  # Intelligence report

# Yuuji (Implementation)
"Read protocol/YUUJI.md and implement [feature]"
"Read protocol/YUUJI.md --tier rapid and [task]"
"Read protocol/YUUJI.md --tier critical and [task]"

# Megumi (Security Review)
"Read protocol/MEGUMI.md and review [module]"
"Read protocol/MEGUMI.md --tier critical and review [module]"
```

### Standalone Consultation

```bash
# Ask questions without implementation
"Read protocol/YUUJI.md - How do I handle JWT tokens?"
"Read protocol/MEGUMI.md - What are common XSS vulnerabilities?"
```

---

## 🎯 Success Criteria

Within Domain Zero, the goal is always **ZERO**:

- ✅ **Zero security vulnerabilities** in production
- ✅ **Zero bugs** reach production
- ✅ **Zero performance issues**
- ✅ **Zero technical debt**
- ✅ **Zero unauthorized protocol modifications**

**Domain Zero Philosophy**:
- Zero Flaws = Ship it confidently
- Zero Flaws ≠ Perfect (always improve)
- Perfection is the horizon we walk toward, not the destination we reach

---

## 📚 Documentation

### Essential Reading

1. **protocol/CLAUDE.md** - Main protocol file (comprehensive system overview)
2. **protocol/TIER-SELECTION-GUIDE.md** - Quick tier selection reference
3. **protocol/YUUJI.md** - Implementation agent specifications
4. **protocol/MEGUMI.md** - Security agent specifications
5. **protocol/GOJO.md** - Mission control specifications

### Advanced Topics

- **.protocol-state/tier-system-specification.md** - Technical tier system spec
- **protocol/GOJO-UPDATES-PATCH.md** - Protocol change history and audit trail

---

## 🤝 Getting Help

### Common Questions

**"How do I start?"**
→ Read protocol/CLAUDE.md, then "Read protocol/GOJO.md" to initialize

**"Which tier should I use?"**
→ See protocol/TIER-SELECTION-GUIDE.md for decision tree and examples

**"How do I get a security review?"**
→ Yuuji will automatically tag @security-review after you approve implementation

**"Can I modify the protocol?"**
→ Yes! Edit protocol/CLAUDE.md manually. Agents will re-read for updates.

**"What's Trigger 19?"**
→ Intelligence report from Gojo's passive observations: "Read protocol/GOJO.md - Trigger 19"

---

## ⚠️ Important Notes

### Backup Requirements

**ALL tiers require backups** (even Tier 1 Rapid):
- Backup created before any code changes
- Rollback plan documented in dev-notes.md
- Never skip backup creation

### Protocol Protection

**CLAUDE.md is protected**:
- YOU (user) can edit manually anytime
- Gojo can modify with your authorization
- Yuuji and Megumi have READ-ONLY access
- Unauthorized modification triggers protocol violation

### Git Privacy

**trigger-19.md is gitignored by default**:
- Contains Gojo's passive observations
- Agents are unaware of its existence
- Private intelligence for you and Gojo only

---

## 🎊 You're Ready!

Domain Zero is now set up in your project.

**Next Steps**:

1. Read protocol/CLAUDE.md for full system understanding
2. Run "Read protocol/GOJO.md" to initialize
3. Start your first feature with Yuuji
4. Experience the power of zero-defect development

**Welcome to Domain Zero. Trust the domain. Follow the protocols. Achieve ZERO.**

---

## 📝 Version Information

**Version**: 6.0
**Release Date**: November 5, 2025
**Major Enhancement**: Adaptive Workflow Complexity (Tier System)

**Version History**:
- v6.0 - MAJOR: Adaptive Workflow Complexity (Tier System)
- v5.1 - CLAUDE.md Protection System, Backup & Rollback Requirements
- v5.0 - Mission Control, Passive Observation, Three-Tier Enforcement
- v4.0 - Custom Trigger System
- v3.0 - Dual Workflow Implementation
- v2.0 - Three-Agent Architecture
- v1.0 - Initial Single-Agent System

---

## 📄 License

Domain Zero Protocol is released under the **MIT License**.

See the [LICENSE](LICENSE) file for full details.

**Summary**: Free to use, modify, and distribute. Provided as-is without warranty. Customize and adapt as needed for your workflow.

---

**Domain Zero Protocol v6.0** - Perfect Code Through Infinite Collaboration
**The weight is real. The protocol is absolute. Domain Zero is active.**
