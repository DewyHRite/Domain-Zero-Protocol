<!-- [CORE FILE] - Domain Zero Protocol v9.11.0 -->
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
Copy-Item -Recurse "Domain Zero Protocol\scripts" -Destination "your-project\"
Copy-Item -Recurse "Domain Zero Protocol\.claude\commands" -Destination "your-project\.claude\"
Copy-Item "Domain Zero Protocol\protocol.config.yaml" -Destination "your-project\"
Copy-Item "Domain Zero Protocol\CLAUDE.md" -Destination "your-project\"
```

**macOS/Linux Bash**:
```bash
cp -r "Domain Zero Protocol/protocol" your-project/
cp -r "Domain Zero Protocol/.protocol-state" your-project/
cp -r "Domain Zero Protocol/scripts" your-project/
mkdir -p your-project/.claude && cp -r "Domain Zero Protocol/.claude/commands" your-project/.claude/
cp "Domain Zero Protocol/protocol.config.yaml" your-project/
cp "Domain Zero Protocol/CLAUDE.md" your-project/
```

`scripts/` and `.claude/commands/` are what make the day-one subsystems in Step 6 (Cortex, `/session`, the git-hook guards, `verify-installation.py`) and the native `/gojo`, `/yuuji`, etc. slash commands work — don't skip them.

---

## Step 3: Save to AI Memory (Optional, 30 seconds)

**For persistent context across sessions, save the protocol to your AI assistant's memory:**

**Claude (Claude.ai or API)**:
```
Add to memory: Domain Zero Protocol

I use Domain Zero Protocol v9.11.0 for AI development. Nine resident agents
plus one external, non-resident auditor:

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

External Auditor (non-resident, report-only):
- TOJI: Independent audits across UI/UX, code quality, security, system
  design, implementation integrity, and AI security. Not part of the
  Gojo-coordinated chain of command.

Main protocol: CLAUDE.md (repository root — the single source of truth
since v9.11.0; protocol/CLAUDE.md is just a compatibility stub/redirect).
Agent files: protocol/yuuji.agent.md, protocol/megumi.agent.md,
protocol/nobara.agent.md, protocol/gojo.agent.md, protocol/todo.agent.md,
protocol/maki.agent.md, protocol/panda.agent.md, protocol/inumaki.agent.md,
protocol/sukuna.agent.md, protocol/toji.agent.md
Tiers: Rapid/Standard/Critical
Always read protocol files when I reference them.
Canonical source: https://github.com/DewyHRite/Domain-Zero-Protocol
```

**ChatGPT (Custom Instructions)**:
Add to Settings → Personalization → Custom Instructions:
```
I use Domain Zero Protocol v9.11.0 (nine resident agents + one external,
non-resident auditor).
Main protocol: CLAUDE.md (repository root).
Agent files: protocol/yuuji.agent.md, protocol/megumi.agent.md, protocol/nobara.agent.md, protocol/gojo.agent.md, protocol/todo.agent.md, protocol/maki.agent.md, protocol/panda.agent.md, protocol/inumaki.agent.md, protocol/sukuna.agent.md, protocol/toji.agent.md.
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

## Step 6: Wire Up the Day-One Subsystems (2 minutes, all optional but recommended)

These ship with the protocol but aren't active until you turn them on. None are required to start
Step 5 above — add them whenever you're ready.

**Session lifecycle** — tracks a work session from start to handoff, keeping `.protocol-state/`
and (if enabled) Cortex in sync automatically:
```
/session start      # begin a tracked session
/session update      # full sync: project documents + Cortex re-index + timestamp
/session transfer     # sync + end + write a durable handoff brief for next time
/session end         # end the session
```

**DZP Cortex** (local semantic memory, no cloud calls after first model download) — lets agents
recall prior decisions and security findings instead of rereading files cold every session:
```bash
scripts/brain.sh status    # POSIX — or scripts/brain.ps1 status on Windows
scripts/brain.sh index     # build the local index
scripts/brain.sh query "prior security decision"
```

**Protected-document guard (FEAT-GUARD-001)** — installs a pre-commit hook that blocks any commit
which would overwrite or truncate `.protocol-state/dev-notes.md`, `.protocol-state/security-review.md`,
or `.dzp-domain/domain.record.md`:
```bash
scripts/install-git-hooks.sh     # POSIX — or scripts\install-git-hooks.ps1 on Windows
```

**Installation + integrity check** — confirm every required file is present, then create a
SHA-256 baseline so future tampering or accidental deletion is detectable:
```bash
python scripts/verify-installation.py
python scripts/verify-installation.py --init-integrity   # run once, before manual edits
```

---

## You're Done! 🎉

**What You Just Set Up**:
- ✅ Nine resident AI agents (Yuuji, Megumi, Nobara, Gojo, Todo, Maki, Panda, Inumaki, Sukuna) ready to work, plus Toji — an external, non-resident, report-only auditor for independent audits (`Read protocol/toji.agent.md and audit [target]`)
- ✅ Three-tier workflow system (Rapid/Standard/Critical)
- ✅ Test-first development (TDD) by default
- ✅ OWASP Top 10 security review
- ✅ Backup & rollback protection
- ✅ Zero-defect development philosophy

---

## Next Steps

### Learn the Basics (15 minutes)
1. **Read `CLAUDE.md`** (repository root) - Full system overview (`protocol/CLAUDE.md` is a compatibility stub that redirects there)
2. **Read protocol/TIER-SELECTION-GUIDE.md** - When to use which tier
3. **Try a Tier 2 feature** - Experience the full workflow

### Typical Workflow (Prompted Security Handoff)

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

See `docs/reference/REALITY_CHECK.md` for an honest breakdown of what this framework does and doesn't get you before you invest time customizing it for non-code work.

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

# Extended specialists (Todo/database, Maki/performance, Panda/build+CI, Inumaki/API)
"Read protocol/todo.agent.md and design schema for [feature]"
"Read protocol/maki.agent.md and audit [component] performance"
"Read protocol/panda.agent.md and configure [pipeline/build task]"
"Read protocol/inumaki.agent.md and design REST API for [resource]"

# External audit (Toji) - report-only, independent of the other nine agents
"Read protocol/toji.agent.md and audit [target]"

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

### Enable Claude Haiku for All Clients
Edit `protocol.config.yaml`. `ai.model_policy` is the single source of truth for model IDs — update
it (and the per-agent `model:` front-matter) together, then keep `default_models` in sync:
```yaml
ai:
  default_models:
    - provider: "Anthropic"
      model: "claude-haiku-4-5-20251001"
      scope: "all-clients"
      priority: 1
```

### Use Faster Models for Rapid Prototyping
```yaml
ai:
  default_models:
    - provider: "Anthropic"
      model: "claude-haiku-4-5-20251001"
      scope: "rapid-tier"
      priority: 1
```

### Adjust Enforcement Strictness
```yaml
enforcement:
  isolation: "strict"  # strict (current default), moderate, advisory
  quality_gates:
    block_on_failure: false  # Warn instead of block
```

### Enable Multi-Model Security Review (Tier 3)
```yaml
ai:
  multi_model_review:
    enabled: true
    models: ["claude-sonnet-4-6", "claude-opus-4-8"]
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
→ Edit `CLAUDE.md` directly at the repository root (you have write access) or use Gojo with
authorization. `protocol/CLAUDE.md` is only a compatibility stub that redirects to the root file —
editing it does nothing.

### "What's the difference between tiers?"
→ See `protocol/TIER-SELECTION-GUIDE.md` for detailed examples and decision tree

### "How do I integrate with GitHub Copilot/Cursor?"
→ DZP is harness-agnostic — it's markdown files any AI assistant can read, not a plugin. See
README.md § "What DZP Is — and Is Not" for exactly which protections are real regardless of
harness (mechanical, git/filesystem-level) versus harness-dependent (per-agent tool allowlists)
versus convention-only (prompt instructions).

### "Can I customize agent personalities?"
→ Yes! Edit `protocol.config.yaml` under `roles.output_style`

---

## File Structure Reference

```
your-project/
├── CLAUDE.md                     # Main protocol — THE single source of truth (READ THIS)
├── protocol.config.yaml          # CENTRAL CONFIG (edit this!)
│
├── protocol/                     # Agent files, tier guide, skill definitions
│   ├── CLAUDE.md                 # Compatibility stub — redirects to root CLAUDE.md
│   ├── gojo.agent.md             # Mission control
│   ├── yuuji.agent.md            # Implementation agent
│   ├── megumi.agent.md           # Security agent
│   ├── nobara.agent.md           # Creative strategy & UX agent
│   ├── todo.agent.md             # Database & backend agent
│   ├── maki.agent.md             # Performance agent
│   ├── panda.agent.md            # Build & integration agent
│   ├── inumaki.agent.md          # API & communication agent
│   ├── sukuna.agent.md           # System update agent (Gojo-invoked only)
│   ├── toji.agent.md             # External auditor (report-only, non-resident)
│   ├── TIER-SELECTION-GUIDE.md   # Tier selection help
│   └── skills/                   # Slash-command skill definitions (session, ts-*, brain, dzp-roe, ...)
│
├── .claude/commands/              # Native Claude Code slash commands (/gojo, /yuuji, /session, ...)
│
├── .protocol-state/               # State + Cortex (mixed: some files tracked, most gitignored)
│   ├── project-state.json         # Tracked — central state (session tracking, tier stats, etc.)
│   ├── dev-notes.md               # Tracked, append-only — Yuuji's implementation log
│   ├── security-review.md         # Tracked, append-only — Megumi's security findings
│   ├── issue-registry.jsonl       # Tracked, append-only — issue-ID ledger (once enabled)
│   └── brain/                     # DZP Cortex local semantic-memory engine (data dir is external, not in the repo)
│
├── .dzp-domain/                   # Domain Record (Gojo/Sukuna only; gitignored — see CLAUDE.md for why)
│   └── domain.record.md           # Shared notes repository, append-only, auto-rotates at 5,000 lines
│
├── src/                           # Your code
└── tests/                         # Your tests
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

**Core Four**
- **Yuuji**: Implementation, TDD, documentation
- **Megumi**: Security review, OWASP Top 10, approval/rejection
- **Nobara**: Creative strategy, UX design, product vision
- **Gojo**: Mission control, passive observation, protocol enforcement

**Extended Four**
- **Todo**: Database schema, migrations, query optimization
- **Maki**: Performance profiling and optimization
- **Panda**: CI/CD pipelines and build systems
- **Inumaki**: REST/GraphQL/WebSocket API design

**Special Agent**
- **Sukuna**: Protocol/system updates, red-team reviews (Gojo-invoked only)

**External Auditor**
- **Toji**: Independent, report-only audits across 6 domains (UI/UX, code quality, security, system design, implementation integrity, AI security). Outside the Gojo-coordinated chain of command; reports to you only.

### Protection
- **CLAUDE.md** (repository root): only you, and Gojo with your authorization, are expected to edit it. That expectation is enforced by convention (every other agent's prompt refuses) plus GitHub CODEOWNERS if you have branch protection enabled — check `scripts/install-git-hooks.sh`'s protected-path guard coverage in your own install before assuming a local commit is blocked.
- **Yuuji, Megumi, Nobara, Todo, Maki, Panda, and Inumaki are read-only** on protocol files: prevents accidental protocol corruption
- **`dev-notes.md` / `security-review.md`**: append-only, mechanically enforced by the FEAT-GUARD-001 pre-commit guard once you run `scripts/install-git-hooks.sh`/`.ps1`
- **`domain.record.md`**: shared notes for Gojo and Sukuna only — gitignored (never committed), prevents agent-file bloat, enables crash recovery, auto-rotates at 5,000 lines
- **Trigger 19 reports**: written on-demand to a gitignored `.protocol-state/trigger-19.md` only when you ask Gojo for one — nothing runs in the background unless you opt into Passive Observer (below)

---

## Issue-ID Governance (Optional, Ships Disabled)

Domain Zero ships an optional append-only issue-ID registry + fail-closed commit gate
(`FEAT-IDGOV-001`) that mints and validates tracker IDs (e.g. `SEC-001`, `BUG-042`) cited in your
protected records. **It ships disabled** — a fresh install has no backfilled registry history, so a
live gate would fail-close your very first protected-record commit.

**To enable it**:
1. `python scripts/backfill_issue_registry.py --dry-run --corpus <path>` (repeat `--corpus` for
   each file/directory to scan) to preview, then re-run the same command WITHOUT `--dry-run` and
   with `DZP_ALLOW_ISSUE_ID_OVERRIDE=1` set to actually backfill from existing history
   (non-destructive — see the script's `--help`).
2. `scripts/secid.sh` / `scripts/secid.ps1` — mint your first record. **Do not invoke
   `python scripts/issue_id.py` directly**: it requires a signature (`IDGOV_SIG`/`IDGOV_NONCE`)
   that only the signed wrapper can produce and refuses `new`/`state` otherwise.
3. Set `issue_governance.enabled: true` in your **local** `protocol.config.yaml`.
4. Re-run `scripts/install-git-hooks.sh` / `scripts\install-git-hooks.ps1` to wire the gate into pre-commit.

**Overrides** (loud, never silent): `DZP_ALLOW_ISSUE_ID_OVERRIDE=1` for authorized exceptions
(backfill/migration/restore); `DZP_ALLOW_MISSING_ISSUE_ID_GATE=1` if the gate script itself is
unexpectedly missing. See `AI_INSTRUCTIONS.md` § Issue-ID Governance for the full contract.

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
- Read `CLAUDE.md` (repository root) for comprehensive docs
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

**Domain Zero Protocol v9.11.0** - Perfect Code Through Infinite Collaboration

*The weight is real. The protocol is absolute. Domain Zero is active.*
