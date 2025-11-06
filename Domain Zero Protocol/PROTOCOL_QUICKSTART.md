# Domain Zero Protocol - Quick Start Guide

**Get up and running with Domain Zero in 2 minutes**

---

## Step 1: Configure Your Project (30 seconds)

Edit `protocol.config.yaml` and update these essential fields:

```yaml
user:
  name: "Your Name"
  contact: "your.email@example.com"

project:
  name: "Your Project Name"
  description: "What your project does"
  repo: "https://github.com/your-org/your-repo"
```

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

I use Domain Zero Protocol v6.1 for AI development. Three-agent system:
- YUUJI: Implementation (TDD)
- MEGUMI: Security review (OWASP)
- GOJO: Mission control

Protocol files: protocol/CLAUDE.md, YUUJI.md, MEGUMI.md, GOJO.md
Tiers: Rapid/Standard/Critical
Always read protocol files when I reference them.
Canonical source: https://github.com/DewyHRite/Domain_Zero_Protocol_DZP
```

**ChatGPT (Custom Instructions)**:
Add to Settings → Personalization → Custom Instructions:
```
I use Domain Zero Protocol v6.1 (three-agent AI dev framework).
Protocol files: protocol/CLAUDE.md, YUUJI.md, MEGUMI.md, GOJO.md.
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
Read protocol/GOJO.md
```

Select option 2: "**New Project Initialization**"

Gojo will set up your project state automatically.

---

## Step 5: Start Building (30 seconds)

Try your first feature:

**Tier 1 (Fast prototype, no tests)**:
```
Read protocol/YUUJI.md --tier rapid and create a hello world script
```

**Tier 2 (Production-ready with tests & security review)** [DEFAULT]:
```
Read protocol/YUUJI.md and implement user registration API endpoint
```

**Tier 3 (Critical: auth, payments, compliance)**:
```
Read protocol/YUUJI.md --tier critical and implement OAuth2 authentication
```

---

## You're Done! 🎉

**What You Just Set Up**:
- ✅ Three AI agents (Yuuji, Megumi, Gojo) ready to work
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

### Typical Workflow

```
1. You: "Read protocol/YUUJI.md and implement [feature]"
   └─> Yuuji implements with tests, tags @user-review

2. You: Review in .protocol-state/dev-notes.md
   └─> Approve: "Looks good, proceed"

3. Yuuji: Tags @security-review
   └─> Megumi conducts OWASP Top 10 audit

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

## Common Commands

### Agent Invocation
```bash
# Initialize project
"Read protocol/GOJO.md"

# Implement feature (Yuuji)
"Read protocol/YUUJI.md and implement [feature]"
"Read protocol/YUUJI.md --tier rapid and [task]"
"Read protocol/YUUJI.md --tier critical and [task]"

# Security review (Megumi)
"Read protocol/MEGUMI.md and review [module]"

# Intelligence report (Gojo)
"Read protocol/GOJO.md - Trigger 19"
```

### Standalone Questions (no implementation)
```bash
"Read protocol/YUUJI.md - How should I structure my database schema?"
"Read protocol/MEGUMI.md - What are common JWT vulnerabilities?"
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
- ✅ Automatic enforcement of protocol rules
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
.\scripts\verify-protocol.ps1
```

**macOS/Linux**:
```bash
./scripts/verify-protocol.sh
```

**What it checks**:
- ✅ Config file completeness
- ✅ Role isolation vocabulary (no forbidden cross-talk)
- ✅ Output template conformance
- ✅ CLAUDE.md protection rules

---

## Troubleshooting

### "Agent doesn't seem to follow the protocol"
→ Ensure the agent reads the protocol file first: `"Read protocol/YUUJI.md and..."`

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
│   ├── YUUJI.md                  # Implementation agent
│   ├── MEGUMI.md                 # Security agent
│   ├── GOJO.md                   # Mission control
│   └── TIER-SELECTION-GUIDE.md  # Tier selection help
│
├── .protocol-state/              # State files (gitignored)
│   ├── project-state.json        # Project config
│   ├── dev-notes.md              # Yuuji's implementation log
│   ├── security-review.md        # Megumi's security findings
│   └── trigger-19.md             # Gojo's intelligence (private)
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
- **Gojo**: Mission control, passive observation, protocol enforcement

### Protection
- **CLAUDE.md is protected**: Only YOU and GOJO (with authorization) can edit
- **Yuuji and Megumi are read-only**: Prevents accidental protocol corruption
- **trigger-19.md is gitignored**: Private intelligence for you and Gojo only

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
- Ask Gojo: `"Read protocol/GOJO.md - Trigger 19"` for intelligence reports

**Need Support?**
- Check the README.md for detailed setup instructions
- Review .protocol-state/ files for current state and logs
- Consult protocol.config.yaml for all configuration options

---

## Welcome to Domain Zero

**You're now ready to experience zero-defect development.**

**Trust the domain. Follow the protocols. Achieve ZERO.**

---

**Domain Zero Protocol v6.1** - Perfect Code Through Infinite Collaboration

*The weight is real. The protocol is absolute. Domain Zero is active.*
