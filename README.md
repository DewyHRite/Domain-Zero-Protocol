# Domain Zero Protocol v6.2.8
## AI-Powered Development Framework with Security-First Approach

### "Perfect Code Through Infinite Collaboration"

Domain Zero is a four-agent AI development system that provides specialized expertise through distinct AI personalities, operating under absolute protocol authority with test-first development, comprehensive security review, creative strategy, and adaptive workflow complexity.

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
- [Troubleshooting](#-troubleshooting) ⭐ NEW
- [Important Notes](#-important-notes)
- [License](#-license)

---

## 📦 Distribution Package Contents

This distribution includes everything you need to deploy Domain Zero:

**Core Protocol Files** (`protocol/`):
- `CLAUDE.md` - Main protocol specification (v6.1)
- `YUUJI.md` - Implementation agent protocol
- `MEGUMI.md` - Security review agent protocol
- `GOJO.md` - Mission control agent protocol
- `NOBARA.md` - Creative strategy & UX agent protocol
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
- `PROTOCOL_QUICKSTART.md` - **NEW** 2-minute quick start guide
- `PASSIVE_OBSERVER.md` - **NEW** Gojo's Passive Observer mode guide
- `DESKTOP_WRAPPER.md` - **NEW** Electron desktop app wrapper guide
- `protocol.config.yaml` - **NEW** Canonical configuration (single source of truth)
- `AI_INSTRUCTIONS.md` - Cross-assistant discovery shim (redirects to CLAUDE.md)
- `.gitignore` - Privacy-focused git configuration
- `LICENSE` - MIT License
- `CODEOWNERS` - Protocol file protection rules

**Integration Scripts** (`scripts/`):
- `update-instructions.ps1` - PowerShell script to append protocol pointers (Windows)
- `update-instructions.sh` - Bash script to append protocol pointers (macOS/Linux)
- `verify-protocol.ps1` - **NEW** Protocol verification script (Windows)
- `verify-protocol.sh` - **NEW** Protocol verification script (macOS/Linux)

**CI/CD Templates** (`.github/`):
- `copilot-instructions.md` - **NEW** GitHub Copilot integration instructions
- `PULL_REQUEST_TEMPLATE.md` - **NEW** PR template with Passive-Off checklist
- `workflows/security-scan-example.yml` - GitHub Actions security scanning template

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

Domain Zero creates a **controlled collaboration space** where four specialized AI agents work together to deliver production-ready code with zero defects.

### The Four Agents

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

**🎯 NOBARA KUGISAKI** - Creative Strategy & UX
- User experience design
- Product vision & strategy
- Narrative development
- Creative problem solving

**♾️ SATORU GOJO** - Mission Control
- Project lifecycle management
- Passive observation & intelligence
- Protocol enforcement
- Team coordination

---

## 🚀 Quick Setup

> **⚡ Want to get started in 2 minutes?** See [`PROTOCOL_QUICKSTART.md`](PROTOCOL_QUICKSTART.md) for the express setup guide.

### Step 1: Copy Protocol to Your Project

**macOS/Linux (bash/zsh)**:
```bash
# Copy the entire protocol structure to your project root
cp -r "Domain Zero Protocol v6.2.8/protocol" your-project/
cp -r "Domain Zero Protocol v6.2.8/.protocol-state" your-project/
cp "Domain Zero Protocol v6.2.8/protocol.config.yaml" your-project/
cp "Domain Zero Protocol v6.2.8/.gitignore" your-project/
```

**Windows (PowerShell)**:
```powershell
# Copy the entire protocol structure to your project root
Copy-Item -Recurse -Force "Domain Zero Protocol v6.2.8\protocol" -Destination "your-project\"
Copy-Item -Recurse -Force "Domain Zero Protocol v6.2.8\.protocol-state" -Destination "your-project\"
Copy-Item -Force "Domain Zero Protocol v6.2.8\protocol.config.yaml" -Destination "your-project\"
Copy-Item -Force "Domain Zero Protocol v6.2.8\.gitignore" -Destination "your-project\"
```

**Windows (Command Prompt)**:
```cmd
REM Copy the entire protocol structure to your project root
xcopy /E /I /Y "Domain Zero Protocol v6.2.8\protocol" "your-project\protocol"
xcopy /E /I /Y "Domain Zero Protocol v6.2.8\.protocol-state" "your-project\.protocol-state"
copy /Y "Domain Zero Protocol v6.2.8\protocol.config.yaml" "your-project\"
copy /Y "Domain Zero Protocol v6.2.8\.gitignore" "your-project\"
```

### Step 2: Configure Your Project

Edit `protocol.config.yaml` (recommended) OR `.protocol-state/project-state.json`:

**Option A: protocol.config.yaml** (recommended - single source of truth):
```yaml
user:
  name: "Your Name"
  contact: "your.email@example.com"

project:
  name: "Your Project Name"
  description: "What your project does"
  repo: "https://github.com/your-org/your-repo"
```

**Option B: .protocol-state/project-state.json** (legacy):
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

### 💾 Save to AI Assistant Memory (Recommended)

**For enhanced persistence across sessions, save the Domain Zero Protocol to your AI assistant's memory system.**

Many AI assistants now support memory features that allow them to remember important context between conversations. By saving the protocol to memory, the AI will automatically understand Domain Zero without needing to re-read protocol files every session.

**✅ Assistants with Memory Support**:
- **Claude (Anthropic)** - Memory feature available in Claude.ai and API
- **ChatGPT (OpenAI)** - Custom Instructions and Memory features
- **GitHub Copilot** - Workspace context and instructions
- **Cursor** - Long-term memory via `.cursorrules`
- **Cody (Sourcegraph)** - Context memory features

**How to Save to Memory**:

**For Claude (Claude.ai or API)**:
```
You: "Add to memory: Domain Zero Protocol

I use the Domain Zero Protocol for AI-assisted development. This is a four-agent system:
- YUUJI (Implementation Specialist): Test-first development, feature implementation
- MEGUMI (Security Analyst): OWASP Top 10 security reviews
- NOBARA (Creative Strategy & UX): User experience design, product vision
- GOJO (Mission Control): Project lifecycle, protocol guardian

The protocol files are located in my project at:
- protocol/CLAUDE.md (main protocol, v6.2.7)
- protocol/YUUJI.md (implementation agent)
- protocol/MEGUMI.md (security agent)
- protocol/NOBARA.md (creative strategy agent)
- protocol/GOJO.md (mission control)

The protocol uses a three-tier workflow system:
- Tier 1 (Rapid): Fast prototyping, no tests
- Tier 2 (Standard): Production features with TDD + security review [DEFAULT]
- Tier 3 (Critical): Enhanced testing + multi-model security review for auth/payments/sensitive data

When I say 'Read protocol/[AGENT].md', always read the file first to follow the protocol.
The canonical source is: https://github.com/DewyHRite/Domain-Zero-Protocol"
```

**For ChatGPT (Custom Instructions)**:
1. Go to Settings → Personalization → Custom Instructions
2. Add to "What would you like ChatGPT to know about you":
```
I use the Domain Zero Protocol (v6.1) for development projects. This is a four-agent AI development framework with specialized roles:
- YUUJI: Implementation with test-first development
- MEGUMI: Security review (OWASP Top 10)
- NOBARA: Creative strategy and user experience design
- GOJO: Mission control and protocol enforcement

When working on my projects, refer to protocol files at protocol/CLAUDE.md, protocol/YUUJI.md, protocol/MEGUMI.md, protocol/NOBARA.md, and protocol/GOJO.md. The protocol follows a three-tier workflow system (Rapid/Standard/Critical) and aims for zero-defect code.

Canonical source: https://github.com/DewyHRite/Domain-Zero-Protocol
```

**For GitHub Copilot**:
- The `.github/copilot-instructions.md` file serves as persistent memory
- Copilot automatically reads this file for every session
- Already included in the distribution package

**For Cursor**:
- Edit `.cursorrules` in your project root
- Cursor automatically loads this for persistent context
- Add Domain Zero Protocol pointer as shown in integration section

**What to Include in Memory**:
- ✅ Protocol name and version (Domain Zero Protocol v6.2.8)
- ✅ The four agent roles and their specializations
- ✅ Protocol file locations (protocol/CLAUDE.md, YUUJI.md, MEGUMI.md, NOBARA.md, GOJO.md)
- ✅ Tier system overview (Rapid/Standard/Critical)
- ✅ Canonical source URL (https://github.com/DewyHRite/Domain-Zero-Protocol)
- ✅ Key principles: test-first development, OWASP security review, zero-defect philosophy

**Benefits of Memory Integration**:
- 🚀 **Faster startup**: No need to re-read protocol files every session
- 🔄 **Session continuity**: AI remembers your workflow preferences
- 🎯 **Automatic compliance**: AI follows protocol without explicit reminders
- 💡 **Proactive suggestions**: AI can suggest tier selection and workflow improvements
- ⚡ **Reduced token usage**: Less context needed in each conversation

**Best Practices**:
- Update memory when you upgrade to a new protocol version
- Keep memory entry concise (200-300 words max for most assistants)
- Include file paths relative to project root
- Add canonical source URL for reference
- Test by starting a new conversation and verifying the AI remembers the protocol

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
- Creative Strategy & UX: `protocol/NOBARA.md`
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

Domain Zero v6.1 features **three workflow tiers** to match process rigor to feature criticality.

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
│   ├── NOBARA.md                    # Creative strategy & UX agent
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

# Nobara (Creative Strategy & UX)
"Read protocol/NOBARA.md and design [feature/experience]"
"Read protocol/NOBARA.md and develop product vision for [feature]"
```

### Standalone Consultation

```bash
# Ask questions without implementation
"Read protocol/YUUJI.md - How do I handle JWT tokens?"
"Read protocol/MEGUMI.md - What are common XSS vulnerabilities?"
"Read protocol/NOBARA.md - What are best practices for user onboarding?"
```

### Protocol Verification

```bash
# Windows PowerShell
.\scripts\verify-protocol.ps1

# macOS/Linux
./scripts/verify-protocol.sh
```

**What it checks**:
- ✅ File existence (required protocol files)
- ✅ Configuration completeness (protocol.config.yaml)
- ✅ Isolation vocabulary (forbidden cross-agent terms)
- ✅ Output template conformance
- ✅ CLAUDE.md protection rules
- ✅ Backup configuration

**Options**:
- `--verbose` - Show detailed information
- `--help` - Show help message

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

### Getting Started

1. **PROTOCOL_QUICKSTART.md** - 2-minute quick start guide (START HERE)
2. **README.md** - This file (comprehensive setup guide)
3. **protocol.config.yaml** - Central configuration file

### Essential Reading

1. **protocol/CLAUDE.md** - Main protocol file (comprehensive system overview)
2. **protocol/TIER-SELECTION-GUIDE.md** - Quick tier selection reference
3. **PASSIVE_OBSERVER.md** - Gojo's Passive Observer mode explained
4. **protocol/YUUJI.md** - Implementation agent specifications
5. **protocol/MEGUMI.md** - Security agent specifications
6. **protocol/NOBARA.md** - Creative strategy & UX agent specifications
7. **protocol/GOJO.md** - Mission control specifications
8. **protocol/MODE_INDICATORS.md** - Agent identification and display systems guide

### Integration & Tooling

- **.github/copilot-instructions.md** - GitHub Copilot integration guide
- **.github/PULL_REQUEST_TEMPLATE.md** - PR template with protocol compliance checklist
- **scripts/verify-protocol.(ps1|sh)** - Protocol verification scripts
- **scripts/update-instructions.(ps1|sh)** - AI instruction updater scripts

### Advanced Topics

- **.protocol-state/tier-system-specification.md** - Technical tier system spec
- **protocol/GOJO-UPDATES-PATCH.md** - Protocol change history and audit trail
- **protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md** - Self-identification banner specification
- **protocol/CANONICAL_SOURCE_ADOPTION.md** - Canonical source adoption strategy

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

## 🔧 Troubleshooting

### Configuration Issues

**Problem: Verification script fails with "placeholder values detected"**

```
[FAIL] Configuration contains placeholder values that must be updated:
      [X] Your Name
      [X] email@example.com
```

**Solution:**
1. Open `protocol.config.yaml` in your editor
2. Replace all placeholder values with your actual information:
   ```yaml
   user:
     name: "John Smith"              # Your actual name
     contact: "john@example.com"     # Your actual email
     organization: "Acme Corp"       # Your organization

   project:
     name: "My Project"              # Your project name
     repo: "https://github.com/user/repo"  # Your repo URL
     created: "2025-11-07T12:00:00Z"      # ISO 8601 timestamp
   ```
3. Run verification script again

---

**Problem: "CODEOWNERS file not found"**

**Solution:**
- If using GitHub: Create `CODEOWNERS` file in repository root (see `scripts/verify-protocol.sh` for template)
- If not using GitHub: This is optional - warning can be safely ignored
- Template:
  ```
  protocol/CLAUDE.md @YourGitHubUsername
  protocol/*.md @YourGitHubUsername
  protocol.config.yaml @YourGitHubUsername
  ```

---

### Agent Behavior Issues

**Problem: Agent doesn't recognize protocol files**

**Symptoms:**
- Agent asks "What is Domain Zero?"
- Agent doesn't follow tier system
- Agent doesn't use proper output format

**Solution:**
1. Verify protocol files exist in `protocol/` directory
2. Re-read the protocol: `"Read protocol/CLAUDE.md"`
3. For persistent sessions, check if AI memory has protocol saved
4. Verify file paths are correct (use absolute paths if needed)

---

**Problem: Agent skips security review**

**Symptoms:**
- Yuuji completes implementation but Megumi never appears
- No `@security-review` tag in output

**Solution:**
- Check tier setting in conversation (Tier 1 skips security review)
- Verify MEGUMI.md exists in `protocol/` directory
- Manually invoke: `"Read protocol/MEGUMI.md - review the changes"`
- For Tier 2+: Ensure Yuuji's output includes `@security-review` tag

---

**Problem: Gojo doesn't initialize project**

**Symptoms:**
- No `.protocol-state/` directory created
- No `project-state.json` generated

**Solution:**
1. Explicitly request: `"Read protocol/GOJO.md"`
2. Choose option 2: "New Project Initialization"
3. Answer all prompts about project configuration
4. Verify `.protocol-state/` directory was created
5. Check `project-state.json` contains your project info

---

### Tier System Issues

**Problem: Unsure which tier to use**

**Solution:**
- Read `protocol/TIER-SELECTION-GUIDE.md` for decision tree
- Quick rules:
  - **Tier 1 (Rapid):** Prototypes, experiments, throwaway code
  - **Tier 2 (Standard):** Production features, bug fixes, refactoring [DEFAULT]
  - **Tier 3 (Critical):** Authentication, payments, sensitive data, security

---

**Problem: Want to change tier mid-workflow**

**Solution:**
- **Upgrading (Tier 1 → 2 or 2 → 3):** Always allowed
  - Say: "Upgrade to Tier 3" or "I need security review"
  - Gojo will backfill missing steps (tests, security review)

- **Downgrading (Tier 3 → 2 or 2 → 1):** Requires justification
  - Gojo must approve downgrade
  - Say: "Can we downgrade to Tier 2? This feature isn't security-critical"
  - Gojo will assess risk and approve/deny

---

### Verification Script Issues

**Problem: Scripts won't run (Permission denied)**

**Unix/Linux/macOS:**
```bash
chmod +x scripts/verify-protocol.sh
./scripts/verify-protocol.sh
```

**Windows PowerShell:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\verify-protocol.ps1
```

---

**Problem: "Command not found" error**

**Solution:**
- Ensure you're in the project root directory
- Use relative paths: `./scripts/verify-protocol.sh`
- Or absolute paths: `/full/path/to/scripts/verify-protocol.sh`

---

**Problem: Unicode symbols display incorrectly (PowerShell)**

**Fixed in v6.2.4:** PowerShell script now uses ASCII symbols `[PASS]`, `[WARN]`, `[FAIL]` instead of Unicode.

**For older versions:**
```powershell
# Set console to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

**Problem: Verification takes too long**

**Solution (v6.2.6+):** Use quick mode for faster verification

**Unix/Linux/macOS:**
```bash
# Quick mode - runs only critical checks (60% faster)
./scripts/verify-protocol.sh --quick

# Skip specific checks
./scripts/verify-protocol.sh --skip=isolation --skip=templates

# Run only specific checks
./scripts/verify-protocol.sh --only=files --only=config

# List all available checks
./scripts/verify-protocol.sh --list
```

**Windows PowerShell:**
```powershell
# Quick mode - runs only critical checks (60% faster)
.\scripts\verify-protocol.ps1 -Quick

# Skip specific checks
.\scripts\verify-protocol.ps1 -Skip isolation,templates

# Run only specific checks
.\scripts\verify-protocol.ps1 -Only files,config

# List all available checks
.\scripts\verify-protocol.ps1 -List
```

**Available checks:**
- `dependencies` (critical) - Verify required command-line tools
- `files` (critical) - Check protocol file existence
- `config` (critical) - Validate configuration completeness
- `yaml` (critical) - Check YAML syntax validity
- `isolation` (warning) - Scan for forbidden vocabulary
- `templates` (warning) - Check output template structure
- `protection` (warning) - Verify CLAUDE.md protection
- `backup` (warning) - Check backup configuration

**Tip:** Use `--quick` in CI/CD pipelines for faster builds

---

### Git & GitHub Issues

**Problem: trigger-19.md accidentally committed**

**Solution:**
1. Verify `.gitignore` exists and contains:
   ```
   .protocol-state/trigger-19.md
   ```
2. Remove from git history:
   ```bash
   git rm --cached .protocol-state/trigger-19.md
   git commit -m "Remove trigger-19.md from tracking"
   ```
3. Add to `.gitignore` if not already present

---

**Problem: CODEOWNERS not enforcing reviews**

**Solution:**
1. Verify `CODEOWNERS` file exists in repository root
2. Enable branch protection in GitHub:
   - Settings → Branches → Add rule for `main`
   - Check "Require pull request reviews before merging"
   - Check "Require review from Code Owners"
3. Ensure usernames in CODEOWNERS are correct (with `@` prefix)

---

### Integration Issues

**Problem: AI assistant doesn't remember protocol between sessions**

**Solution:**
1. **Use AI Memory (Recommended):**
   - Claude: Add to memory via Settings or "Add to memory" command
   - ChatGPT: Add to Custom Instructions
   - Template: See `PROTOCOL_QUICKSTART.md` Step 3

2. **Manual Re-read:**
   - Start each session: `"Read protocol/CLAUDE.md"`
   - This works but increases token usage

---

**Problem: GitHub Copilot not following protocol**

**Solution:**
1. Verify `.github/copilot-instructions.md` exists
2. Copilot reads this automatically in GitHub Codespaces
3. For VS Code: Restart editor after adding file
4. Copilot works best for code completion, not workflow management
5. Consider using Claude or ChatGPT for workflow orchestration

---

### Performance Issues

**Problem: Tier 2/3 workflows take too long**

**Optimization Strategies:**
1. **Batch small changes:** Group minor fixes into one Tier 2 session
2. **Use Tier 1 for prototypes:** Don't over-engineer experiments
3. **Parallelize reviews:** Run linters/tests while waiting for AI responses
4. **Prepare context:** Have requirements ready before starting workflow
5. **Consider async:** For non-urgent features, let agents work while you do other tasks

---

**Problem: Too many tokens used**

**Cost Reduction Tips:**
1. **Use AI Memory:** Avoids re-reading protocol files every session
2. **Be specific:** Clear requirements reduce back-and-forth
3. **Leverage Quick Start:** Use `PROTOCOL_QUICKSTART.md` for common tasks
4. **Archive old sessions:** Don't carry unnecessary context
5. **Use cheaper models:** Tier 1 can use faster/cheaper AI models

---

### Common Error Messages

**Error: "Protocol violation - unauthorized CLAUDE.md modification"**

**Cause:** Yuuji or Megumi tried to modify CLAUDE.md directly

**Solution:**
- Only YOU and GOJO (with authorization) can modify CLAUDE.md
- If you want protocol changes, edit CLAUDE.md manually
- Agents will re-read automatically

---

**Error: "Missing required output tag: @security-review"**

**Cause:** Yuuji completed Tier 2+ implementation without tagging for security review

**Solution:**
1. Ask Yuuji: "Please add @security-review tag to your output"
2. Then invoke Megumi manually: `"Read protocol/MEGUMI.md - review changes"`

---

**Error: "Backup verification failed"**

**Cause:** No backup created before code changes (protocol requirement)

**Solution:**
1. Create backup immediately:
   ```bash
   git add .
   git commit -m "Backup before implementing feature X"
   ```
2. Or use git stash:
   ```bash
   git stash save "Backup before feature X"
   ```
3. Document in `dev-notes.md`

---

### Still Need Help?

**Resources:**
- **Quick Start:** See `PROTOCOL_QUICKSTART.md` (2-minute setup)
- **Verification:** Run `scripts/verify-protocol.sh` or `verify-protocol.ps1`
- **Security:** See `SECURITY.md` for vulnerability reporting
- **Examples:** Check `protocol/TIER-SELECTION-GUIDE.md` for workflow examples
- **Source Code:** https://github.com/DewyHRite/Domain-Zero-Protocol

**Community Support:**
- GitHub Issues: https://github.com/DewyHRite/Domain-Zero-Protocol/issues
- Tag questions with `question` label

**Advanced Customization:**
- All protocol behaviors are configurable in `protocol.config.yaml`
- Agent prompts are in `protocol/*.md` files (edit freely!)
- Tier requirements defined in `.protocol-state/tier-system-specification.md`

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

**Version**: 6.2.1
**Release Date**: November 6, 2025
**Major Enhancements**: Canonical Source Adoption, Agent Self-Identification Standard, Session Continuity

**Version History**:
- v6.1 - MINOR: Canonical Source Adoption, Agent Self-Identification, AI Memory Integration, Session Continuity (long sessions & user absence re-identification)
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

**Domain Zero Protocol v6.2.8** - Perfect Code Through Infinite Collaboration
**The weight is real. The protocol is absolute. Domain Zero is active.**
