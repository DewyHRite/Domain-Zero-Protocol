<!-- [CORE FILE] - Domain Zero Protocol v8.8.0 -->
# Domain Zero Protocol - Quick Start Guide

## Get Up and Running with Domain Zero in 2 Minutes

---

## Step 1: Configure Your Project (30 seconds)

Edit `protocol.config.yaml` and update these essential fields:

```yaml
user:
  name: "Your Name"                          # Replace with your actual name
  contact: "your.email@example.com"          # Replace with your email
  organization: "Your Organization"          # Replace with your org name

project:
  name: "Your Project Name"                  # Replace with project name
  description: "What your project does"      # Replace with description
  repo: "https://github.com/your-org/your-repo"  # Replace with repo URL
  created: "YYYY-MM-DDTHH:MM:SSZ"            # Replace with creation date
```

**⚠️ Important:** The verification scripts will fail if you leave placeholder values unchanged. This ensures your protocol is properly configured before use.

That's it! Everything else has sensible defaults.

---

## Step 2: Copy Protocol to Your Project (30 seconds)

**Windows PowerShell**:
```powershell
Copy-Item -Recurse "Domain Zero Protocol\protocol" -Destination "your-project\"
Copy-Item -Recurse "Domain Zero Protocol\.protocol-state" -Destination "your-project\"
Copy-Item "Domain Zero Protocol\protocol.config.yaml" -Destination "your-project\"
```

**macOS/Linux Bash**:
```bash
cp -r "Domain Zero Protocol/protocol" your-project/
cp -r "Domain Zero Protocol/.protocol-state" your-project/
cp "Domain Zero Protocol/protocol.config.yaml" your-project/
```

---

## Step 3: Save to AI Memory (Optional, 30 seconds)

**For persistent context across sessions, save the protocol to your AI assistant's memory:**

**Claude (Claude.ai or API)**:
```
Add to memory: Domain Zero Protocol

I use Domain Zero Protocol v8.8.0 for AI development. Nine-agent system:

Core Four:
- YUUJI: Implementation (TDD)
- MEGUMI: Security review (OWASP)
- NOBARA: Creative strategy & UX
- GOJO: Mission control

Extended Four:
- TODO: Database & backend
- MAKI: Performance optimization
- PANDA: Build & integration
- INUMAKI: API & communication

Special Agent:
- SUKUNA: System update adversary (Gojo-invoked only)

Protocol files: protocol/CLAUDE.md, protocol/yuuji.agent.md, protocol/megumi.agent.md, protocol/nobara.agent.md, protocol/gojo.agent.md, protocol/todo.agent.md, protocol/maki.agent.md, protocol/panda.agent.md, protocol/inumaki.agent.md, protocol/sukuna.agent.md
Tiers: Rapid/Standard/Critical
Always read protocol files when I reference them.
Canonical source: https://github.com/DewyHRite/Domain-Zero-Protocol
```

**ChatGPT (Custom Instructions)**:
Add to Settings → Personalization → Custom Instructions:
```
I use Domain Zero Protocol v8.8.0 (nine-agent AI dev framework).
Protocol files: protocol/CLAUDE.md, protocol/yuuji.agent.md, protocol/megumi.agent.md, protocol/nobara.agent.md, protocol/gojo.agent.md, protocol/todo.agent.md, protocol/maki.agent.md, protocol/panda.agent.md, protocol/inumaki.agent.md, protocol/sukuna.agent.md.
Always read protocol files first.
```

**Why Memory?**
- ✅ No need to re-read protocol files every session
- ✅ AI automatically understands your workflow
- ✅ Faster startup, reduced token usage
- ✅ Session continuity

**Skip this step if:**
- You prefer to read protocol files each session
- Your AI assistant doesn't support memory
- You're just testing Domain Zero

---

## Step 4: Initialize with Gojo (30 seconds)

In your AI assistant (Claude, GitHub Copilot, Cursor, etc.):

```
Read protocol/gojo.agent.md
```

Select option 2: "**New Project Initialization**"

Gojo will set up your project state automatically.

---

## Step 5: Start Building (30 seconds)

Try your first feature:

**Tier 1 (Fast prototype, no tests)**:
```
Read protocol/yuuji.agent.md --tier rapid and create a hello world script
```

**Tier 2 (Production-ready with tests & security review)** [DEFAULT]:
```
Read protocol/yuuji.agent.md and implement user registration API endpoint
```

**Tier 3 (Critical: auth, payments, compliance)**:
```
Read protocol/yuuji.agent.md --tier critical and implement OAuth2 authentication
```

---

## Step 6: Use Dual-AI Workflow (Recommended for Power Users)

**For optimal token efficiency**, use two AI assistants together:

| AI Role | Tool | Purpose |
|---------|------|---------|
| **Prompt Generator** | IDE AI (VS Code, Cursor, Antigravity, etc.) | Reads `gojo.prompt.md`, generates `prompt.md` |
| **Main Executor** | Claude CLI | Executes the generated `prompt.md` |

### Quick Setup

1. **Copy meta prompt** to your project:
   ```bash
   cp /path/to/Domain-Zero/gojo.prompt.md your-project/
   ```

2. **In IDE AI** (e.g., Antigravity):
   ```bash
   "Read gojo.prompt.md and create a prompt for implementing user authentication"
   ```

3. **In Claude CLI**:
   ```bash
   "Read prompt.md"
   ```

### Why This Works

- **IDE AI** has full project context (files, imports, structure)
- **Token savings**: 70-80% reduction on main AI
- **Better prompts**: IDE AI references actual code when generating
- **Faster iteration**: Pre-built prompts execute immediately

**See:** [Dual-AI Meta Prompt Workflow](README.md#-dual-ai-meta-prompt-workflow-recommended) in README.md for detailed setup.

---

## You're Done! 🎉

**What You Just Set Up**:
- ✅ Nine AI agents (Yuuji, Megumi, Nobara, Gojo, Todo, Maki, Panda, Inumaki, Sukuna) ready to work
- ✅ Three-tier workflow system (Rapid/Standard/Critical)
- ✅ Test-first development (TDD) by default
- ✅ OWASP Top 10 security review
- ✅ Backup & rollback protection
- ✅ Zero-defect development philosophy

---

## Next Steps

### Learn the Basics (15 minutes)
1. **Read protocol/CLAUDE.md** - Full system overview
2. **Read protocol/TIER-SELECTION-GUIDE.md** - When to use which tier
3. **Try a Tier 2 feature** - Experience the full workflow

### Typical Workflow (v7.1.0 - Prompted Security Handoff)

```
1. You: "Read protocol/yuuji.agent.md and implement [feature]"
   └─> Yuuji implements with tests, tags @user-review

2. You: Review in .protocol-state/dev-notes.md
   └─> Approve: "Looks good, proceed"

3. **PROMPTED**: Gojo facilitates handoff to Megumi (Tier 2/3)
   └─> Megumi receives context and conducts OWASP Top 10 audit
   └─> **Option**: Skip with "Skip security review for [feature]" (tracked + reminded)

4. Megumi: Tags @approved or @remediation-required
   └─> If issues found, Yuuji fixes and re-submits

5. Feature complete ✓
```

---

## Understanding the Three Tiers

| Tier | Use Case | Time | What You Get |
|------|----------|------|--------------|
| **TIER 1: RAPID** 🚀 | Prototypes, experiments, throwaway code | 10-15 min | Fast implementation, backup only |
| **TIER 2: STANDARD** ⚖️ | Production features, APIs, CRUD | 30-45 min | TDD + OWASP review + backup |
| **TIER 3: CRITICAL** 🔒 | Auth, payments, compliance | 60-90 min | Enhanced tests + multi-model review + compliance |

**Decision Tree**:
1. Going to production? NO → Tier 1
2. Handles sensitive data? YES → Tier 3
3. Standard production feature? YES → Tier 2

---

## Non-Code Projects (School Work, Research, Writing)

Domain Zero works for non-code projects too! Use agents for:

| Task | Command |
|------|---------|
| **Draft essay outline** | `"Read protocol/yuuji.agent.md and draft an outline for [topic]"` |
| **Verify sources** | `"Read protocol/megumi.agent.md and check my citations for accuracy"` |
| **Improve structure** | `"Read protocol/nobara.agent.md and improve the flow of my introduction"` |
| **Track progress** | `"Read protocol/gojo.agent.md"` → Use project management |

**Setup for school projects:**
```bash
# Windows PowerShell
mkdir "C:\Users\YourName\Documents\School\MyProject\protocol"
Copy-Item "C:\Path\To\Domain-Zero\protocol\*" ".\protocol\" -Recurse
claude  # Start Claude Code

# macOS/Linux
mkdir -p ~/Documents/School/MyProject/protocol
cp -r /path/to/Domain-Zero/protocol/* ./protocol/
claude
```

See [README.md § Non-Code Projects](README.md#-non-code-projects-school-work-research--academic-writing) for detailed examples.

---

## Common Commands

### Agent Invocation
```bash
# Initialize project
"Read protocol/gojo.agent.md"

# Implement feature (Yuuji)
"Read protocol/yuuji.agent.md and implement [feature]"
"Read protocol/yuuji.agent.md --tier rapid and [task]"
"Read protocol/yuuji.agent.md --tier critical and [task]"

# Security review (Megumi) - PROMPTED for Tier 2/3, or standalone for existing code
"Read protocol/megumi.agent.md and audit [existing module]"  # Standalone audit of existing code

# Creative strategy & UX (Nobara)
"Read protocol/nobara.agent.md and design [feature/experience]"

# Intelligence report (Gojo)
"Read protocol/gojo.agent.md - Trigger 19"
```

### Standalone Questions (no implementation)
```bash
"Read protocol/yuuji.agent.md - How should I structure my database schema?"
"Read protocol/megumi.agent.md - What are common JWT vulnerabilities?"
"Read protocol/nobara.agent.md - What are best practices for user onboarding flows?"
```

---

## Configuration Tips

### Enable Claude Haiku 4.5 for All Clients
Edit `protocol.config.yaml`:
```yaml
ai:
  default_models:
    - provider: "Anthropic"
      model: "claude-3-5-haiku-20241022"
      scope: "all-clients"
      priority: 1
```

### Use Faster Models for Rapid Prototyping
```yaml
ai:
  default_models:
    - provider: "Anthropic"
      model: "claude-3-5-haiku-20241022"
      scope: "rapid-tier"
      priority: 1
```

### Adjust Enforcement Strictness
```yaml
enforcement:
  isolation: "moderate"  # strict, moderate, advisory
  quality_gates:
    block_on_failure: false  # Warn instead of block
```

### Enable Multi-Model Security Review (Tier 3)
```yaml
ai:
  multi_model_review:
    enabled: true
    models: ["claude-3-5-sonnet-20241022", "claude-3-5-opus-20241022"]
```

### Enable Passive Observer (Gojo's Background Monitoring)

> **⚠️ NOTICE**: Passive Observer is **OFF by default** for privacy reasons.

**What is it?**
Gojo's background monitoring system that provides:
- ✅ Protocol enforcement through prompts
- ✅ Proactive safety nudges and backup reminders
- ✅ Risk detection and auto-escalation
- ✅ Rich intelligence reports (Trigger 19)
- ✅ Session continuity tracking

**When OFF** (default):
- ❌ No background monitoring or automatic enforcement
- ❌ Gojo only available via explicit invocation
- ❌ Manual checkpoints and PR template enforcement required
- ✅ Privacy-focused: no session data collection

**When ON** (opt-in):
- ✅ Proactive safety and automatic enforcement
- ✅ Background monitoring and pattern detection
- ✅ Rich intelligence reports
- ⚠️ Session data collected (local storage, 14-day retention, gitignored)

**To Enable**:
```yaml
privacy:
  passive_monitoring:
    enabled: true              # Enable background monitoring
    consent_given: true        # Explicit consent (required)
    consent_date: "2025-11-05T00:00:00Z"
    data_retention_days: 14
    storage_location: "local"  # Never uploaded
```

**Learn More**: See [`PASSIVE_OBSERVER.md`](PASSIVE_OBSERVER.md) for:
- Detailed comparison (OFF vs ON)
- Privacy and consent considerations
- When to enable/disable
- Passive-Off checklist for PR templates

**Recommendation**: Enable for high-risk projects (auth, payments, compliance) where proactive monitoring adds value. Keep OFF for privacy-sensitive environments.

---

## Verification

Run protocol verification (optional, requires setup):

**Windows PowerShell**:
```powershell
# Quick verification (recommended for first run)
.\scripts\verify-protocol.ps1 -Quick

# Full verification
.\scripts\verify-protocol.ps1
```

**macOS/Linux**:
```bash
# Quick verification (recommended for first run)
./scripts/verify-protocol.sh --quick

# Full verification
./scripts/verify-protocol.sh
```

**What it checks**:
- ✅ Dependencies (required command-line tools)
- ✅ File existence (all protocol files present)
- ✅ Config file completeness (no placeholders)
- ✅ YAML syntax validation
- ✅ Role isolation vocabulary (no forbidden cross-talk)
- ✅ Output template conformance
- ✅ CLAUDE.md protection rules
- ✅ Backup configuration

**Tip:** Use `--quick` / `-Quick` for faster verification (runs only critical checks)

---

## Troubleshooting

### "Agent doesn't seem to follow the protocol"
→ Ensure the agent reads the protocol file first: `"Read protocol/yuuji.agent.md and..."`

### "How do I modify the protocol?"
→ Edit `protocol/CLAUDE.md` directly (you have write access) or use Gojo with authorization

### "What's the difference between tiers?"
→ See `protocol/TIER-SELECTION-GUIDE.md` for detailed examples and decision tree

### "How do I integrate with GitHub Copilot/Cursor?"
→ See README.md section "AI Assistant Integration & Canonical Source"

### "Can I customize agent personalities?"
→ Yes! Edit `protocol.config.yaml` under `roles.output_style`

---

## File Structure Reference

```
your-project/
├── protocol/                     # Protocol agents
│   ├── CLAUDE.md                 # Main protocol (READ THIS)
│   ├── yuuji.agent.md                  # Implementation agent
│   ├── megumi.agent.md                 # Security agent
│   ├── nobara.agent.md                 # Creative strategy & UX agent
│   ├── gojo.agent.md                   # Mission control
│   └── TIER-SELECTION-GUIDE.md  # Tier selection help
│
├── .protocol-state/              # State files (gitignored)
│   ├── project-state.json        # Project config
│   ├── dev-notes.md              # Yuuji's implementation log
│   ├── security-review.md        # Megumi's security findings
│   └── trigger-19.md             # Gojo's intelligence (private)
│
├── .dzp-domain/                  # Domain Record (Gojo/Sukuna ONLY, v8.8.0+)
│   ├── domain.record.md          # Shared notes repository
│   ├── archive/                  # Rotated archives (auto at 5k lines)
│   └── .rotation-metadata.json   # Rotation tracking
│
├── protocol.config.yaml          # CENTRAL CONFIG (edit this!)
├── src/                          # Your code
└── tests/                        # Your tests
```

---

## Key Concepts

### The Domain
A controlled collaboration space where agents operate under absolute protocol authority.

### Zero Philosophy
- ✅ Zero security vulnerabilities
- ✅ Zero bugs in production
- ✅ Zero performance issues
- ✅ Zero technical debt
- ✅ Zero unauthorized protocol changes

**Zero Flaws ≠ Perfection**. Perfection is the horizon we walk toward, not the destination we reach.

### Agent Roles
- **Yuuji**: Implementation, TDD, documentation
- **Megumi**: Security review, OWASP Top 10, approval/rejection
- **Nobara**: Creative strategy, UX design, product vision
- **Gojo**: Mission control, passive observation, protocol enforcement

### Protection
- **CLAUDE.md is protected**: Only YOU and GOJO (with authorization) can edit
- **Yuuji, Megumi, and Nobara are read-only**: Prevents accidental protocol corruption
- **trigger-19.md is gitignored**: Private intelligence for you and Gojo only
- **domain.record.md (v8.8.0+)**: Shared notes for Gojo and Sukuna only - prevents agent file bloat, enables crash recovery, auto-rotates at 5,000 lines

---

## Success Criteria

You'll know Domain Zero is working when:

1. ✅ Yuuji writes tests **before** implementation (TDD)
2. ✅ Megumi blocks deployment until security issues are fixed
3. ✅ Backups are created automatically before any changes
4. ✅ Features are completed with zero defects
5. ✅ You feel confident deploying code immediately after approval

---

## Getting Help

**Have Questions?**
- Read `protocol/CLAUDE.md` for comprehensive docs
- Read `protocol/TIER-SELECTION-GUIDE.md` for tier examples
- Ask Gojo: `"Read protocol/gojo.agent.md - Trigger 19"` for intelligence reports

**Need Support?**
- Check the README.md for detailed setup instructions
- Review .protocol-state/ files for current state and logs
- Consult protocol.config.yaml for all configuration options

---

## Welcome to Domain Zero

**You're now ready to experience zero-defect development.**

**Trust the domain. Follow the protocols. Achieve ZERO.**

---

**Domain Zero Protocol v8.8.0** - Perfect Code Through Infinite Collaboration

*The weight is real. The protocol is absolute. Domain Zero is active.*
