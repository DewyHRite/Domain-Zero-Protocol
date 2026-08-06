<!-- [CORE FILE] - Domain Zero Protocol v9.12.0 -->
# Domain Zero Protocol - Frequently Asked Questions (FAQ)

**Version:** v9.11.0
**Last Updated:** 2026-08-03

---

## Table of Contents

- [Getting Started](#getting-started)
  - [What is the Dual-AI Meta Prompt workflow?](#what-is-the-dual-ai-meta-prompt-workflow) 🆕
- [Tier System](#tier-system)
- [Agent Behavior](#agent-behavior)
- [Configuration](#configuration)
- [Security & Privacy](#security--privacy)
- [Integration](#integration)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Getting Started

### What is Domain Zero Protocol?

Domain Zero is a nine-agent AI development framework that provides specialized expertise through distinct AI personalities:

**Core Four Agents:**
- **YUUJI** - Implementation Specialist (test-first development)
- **MEGUMI** - Security Analyst (OWASP Top 10 reviews)
- **NOBARA** - Creative Strategy & UX (user experience design)
- **GOJO** - Mission Control (project lifecycle, protocol guardian)

**Extended Four Agents:**
- **TODO** - Database & Backend Specialist (schema design, migrations)
- **MAKI** - Performance Optimization Specialist (profiling, optimization)
- **PANDA** - Build & Integration Specialist (CI/CD, build systems)
- **INUMAKI** - API & Communication Specialist (REST, GraphQL, WebSockets)

**Special Agent (v8.5.1+):**
- **SUKUNA** - System Update Agent (adversarial-but-aligned, Gojo-invoked only)

The protocol uses a three-tier workflow system (Rapid/Standard/Critical) to balance speed and rigor.

---

### How do I get started?

**Quick Start (2 minutes):**
1. Configure `protocol.config.yaml` with your project details
2. Copy protocol files to your project
3. Read `protocol/GOJO.md` and choose "New Project Initialization"
4. Start implementing with `protocol/YUUJI.md`

**Detailed Guide:** See `PROTOCOL_QUICKSTART.md`

---

### Do I need all four agents?

**No.** You can use any combination:
- **Minimum:** Yuuji alone (implementation only, no security review)
- **Recommended:** Yuuji + Megumi (implementation + security)
- **Full System:** All four agents for complete workflow

Configure which agents are enabled in `protocol.config.yaml`:
```yaml
roles:
  enabled: ["yuuji", "megumi", "gojo", "nobara"]  # Customize this list
```

---

### Which AI assistant should I use?

Domain Zero works with any AI assistant that can read files:
- **Claude** (Anthropic) - Recommended, best protocol understanding
- **ChatGPT** (OpenAI) - Works well, use GPT-4+ for best results
- **GitHub Copilot** - Good for code completion, limited workflow management
- **Cursor** - Supports file reading, good IDE integration

**Tip:** Use Claude or ChatGPT for workflow orchestration, Copilot for code completion.

---

### What is the Dual-AI Meta Prompt workflow?

**The recommended way to use Domain Zero** for optimal token efficiency and project context.

**How it works:**
1. **IDE AI** (VS Code, Cursor, Antigravity, etc.) reads `gojo.prompt.md` and generates a `prompt.md` file
2. **Main AI** (Claude CLI) executes the generated prompt by running `"Read prompt.md"`

**Why use two AIs?**
- IDE AI has full project context (files, structure, imports)
- Saves 70-80% tokens on your main AI
- Better prompts because IDE AI can reference actual code
- Separation of concerns: generation vs execution

**Example:**
```bash
# In IDE AI (e.g., Antigravity)
"Read gojo.prompt.md and create a prompt for implementing user login"

# In Claude CLI
"Read prompt.md"
```

**See:** [Dual-AI Meta Prompt Workflow](../README.md#-dual-ai-meta-prompt-workflow-recommended) in README.md

---

### Is this free?

**Protocol:** Yes, Domain Zero Protocol is MIT licensed (free and open source)

**AI Costs:** Depends on your AI assistant:
- Claude API: Pay per token (~$0.01-0.10 per workflow)
- ChatGPT Plus: $20/month unlimited
- GitHub Copilot: $10/month (limited to code completion)

**Cost Optimization:** Use AI Memory to avoid re-reading protocol files every session.

---

## Tier System

### Which tier should I use?

**Quick Decision Tree:**

```text
Is this production code?
├─ No → Tier 1 (Rapid)
└─ Yes → Does it handle sensitive data, auth, or payments?
    ├─ Yes → Tier 3 (Critical)
    └─ No → Tier 2 (Standard) [DEFAULT]
```

**Detailed Guide:** See `protocol/TIER-SELECTION-GUIDE.md`

---

### What's the difference between tiers?

| Feature | Tier 1 (Rapid) | Tier 2 (Standard) | Tier 3 (Critical) |
|---------|---------------|-------------------|-------------------|
| **Time** | 10-15 min | 30-45 min | 60-90 min |
| **Tests** | Optional | TDD (required) | Enhanced TDD |
| **Security Review** | None | OWASP Top 10 | Multi-model review |
| **Code Review** | None | Standard | Enhanced |
| **Use Cases** | Prototypes, experiments | Production features | Auth, payments, sensitive data |

---

### Can I change tier mid-workflow?

**Upgrading (Tier 1 → 2 or 2 → 3):** Always allowed
- Say: "Upgrade to Tier 3" or "I need security review"
- Gojo will backfill missing steps (tests, security review)

**Downgrading (Tier 3 → 2 or 2 → 1):** Requires justification
- Gojo must approve downgrade
- Say: "Can we downgrade to Tier 2? This feature isn't security-critical"
- Gojo will assess risk and approve/deny

---

### Do I always need to run Tier 3 for authentication?

**Yes**, for new authentication implementations:
- Login/logout systems
- Password handling
- Token management
- OAuth integration
- API key handling

**No**, for minor auth-related changes:
- UI text updates in login form (use Tier 1 or 2)
- Adding a "remember me" checkbox (use Tier 2)
- Refactoring existing auth code (use Tier 2, unless changing security logic)

**Rule of Thumb:** If it changes how authentication works, use Tier 3. If it's cosmetic, lower tiers are fine.

---

## Agent Behavior

### Why doesn't the agent follow the protocol?

**Common Causes:**
1. **Protocol files not read:** Say `"Read CLAUDE.md"` (repository root; `protocol/CLAUDE.md` is a compatibility pointer/stub since v9.11.0 that redirects to the root file, not the protocol itself)
2. **Wrong file path:** Verify `protocol/` directory exists
3. **AI memory conflict:** Clear memory and re-read protocol
4. **Outdated context:** Start a new conversation session

**Verification:** Ask the agent: "What tier system do you use?"
- **Correct:** Agent describes Tier 1/2/3 system
- **Incorrect:** Agent doesn't know or describes different system

---

### Can agents modify protocol files?

**CLAUDE.md Protection:**
- **YOU** (user): Can edit manually anytime ✅
- **GOJO**: Can modify with your explicit authorization ✅
- **YUUJI, MEGUMI, NOBARA**: READ-ONLY access ❌

**Agent Files (.agent.md) - Cross-Agent Edit Restrictions (v8.5.1+):**
- **YOU** (user): Full access ✅
- **GOJO**: Full access (with authorization) ✅
- **SUKUNA**: Via Gojo with explicit authorization ✅
- **All other agents**: READ-ONLY access ❌

**Why?** Prevents agents from accidentally changing their own or other agents' behavior.

---

### How do I invoke a specific agent?

**Standard Invocation:**
```text
Read protocol/YUUJI.md
```

**With Context:**
```text
Read protocol/MEGUMI.md - review the authentication changes in auth.py
```

**Agent Handoff:** Agents prompt for handoff to each other:
- Yuuji completes implementation → prompts for Megumi invocation → Megumi appears
- Megumi finds issues → Yuuji fixes them
- Gojo monitors entire process

---

### What if an agent makes a mistake?

**You're in control:**
1. **Review all changes** before accepting
2. **Request corrections:** "This doesn't handle edge case X, please fix"
3. **Reject changes:** "This approach won't work, let's try Y instead"
4. **Escalate:** Call Gojo for second opinion: `"Read protocol/GOJO.md - assess this implementation"`

**Protocol Requirement:** YOU must approve all code before it's considered complete.

---

### What is Sukuna and how do I invoke it?

**Sukuna** is the System Update Agent (v8.5.1+), designed for protocol updates and improvements.

**Key Characteristics:**
- **Adversarial-but-aligned**: Questions assumptions, finds edge cases
- **Gojo-invoked only**: Cannot be called directly by users
- **Stress-tests changes**: Before protocol modifications are applied

**Invocation (via Gojo only):**
```text
Read protocol/gojo.agent.md and engage Sukuna for [update task]
```

**Why Gojo-mediated?** Ensures proper authorization and oversight for protocol changes.

---

### What are Cross-Agent Edit Restrictions?

**v8.5.1 Feature:** Non-Gojo agents now have READ-ONLY access to all `.agent.md` files.

**Access Levels:**
| Entity | CLAUDE.md | .agent.md files |
|--------|-----------|-----------------|
| User | Full | Full |
| Gojo | With auth | Full |
| Sukuna | None | Via Gojo |
| Other agents | None | READ-ONLY |

**Purpose:** Prevents agents from modifying their own behavior definitions.

---

## Configuration

### What's protocol.config.yaml?

**The single source of truth** for all protocol parameters:
- User and project information
- Tier system requirements
- Agent behavior settings
- Safety and wellbeing boundaries
- Backup and enforcement rules

**Important:** Replace all placeholder values before use (verification scripts will fail otherwise).

---

### Do I need to configure everything in protocol.config.yaml?

**No.** Only configure what matters to you:

**Minimum Configuration (Required):**
```yaml
user:
  name: "Your Name"
  contact: "your@email.com"

project:
  name: "Your Project Name"
  repo: "https://github.com/user/repo"
```

**Everything else has sensible defaults.**

**Optional Customization:**
- Tier requirements (test coverage, security depth)
- Work session monitoring (duration, alert intervals)
- Backup policies (retention, required agents)
- Agent-specific settings

---

### Where is my project state stored?

**Directory:** `.protocol-state/`

**Files:**
- `project-state.json` - Project configuration, tier history
- `dev-notes.md` - Yuuji's implementation log
- `security-review.md` - Megumi's security findings
- `trigger-19.md` - Gojo's intelligence report (gitignored by default)
- `tier-system-specification.md` - Technical tier requirements

**Privacy:** `.protocol-state/` is local to your machine. trigger-19.md is gitignored by default.

---

## Security & Privacy

### Is my data private?

**Yes.** Domain Zero Protocol is completely local:
- All protocol files are stored in your project
- No data sent to external servers (except AI API calls)
- trigger-19.md is gitignored by default
- CODEOWNERS and .gitignore protect sensitive files

**What's sent to AI:**
- Your prompts
- Protocol file contents (when read)
- Code you're working on

**What's NOT sent:**
- Other files in your project (unless you explicitly share them)
- trigger-19.md (unless you explicitly share it)
- Your git history

---

### How do I report security vulnerabilities?

**See SECURITY.md for complete policy.**

**Quick Summary:**
- **Email:** the project's GitHub Security Advisories page (https://github.com/DewyHRite/Domain-Zero-Protocol/security/advisories) (critical issues)
- **GitHub Security Advisories:** https://github.com/DewyHRite/Domain-Zero-Protocol/security/advisories (preferred)
- **Response Time:** Best effort (typically 7-14 days)
- **Disclosure:** 90-day coordinated disclosure

**Safe Harbor:** Security research is protected if you follow responsible disclosure guidelines.

---

### What's Trigger 19 and why is it gitignored?

**Trigger 19:** Gojo's intelligence report based on passive observation

**Contents:**
- Code quality patterns observed
- Potential refactoring opportunities
- Security concerns noticed
- Productivity bottlenecks

**Why Gitignored:**
- Private intelligence for you and Gojo only
- Other agents are unaware it exists
- Contains potentially sensitive observations
- Privacy-first by default

**How to Access:**
```text
Read protocol/GOJO.md - Trigger 19
```

---

## Integration

### How do I use Domain Zero with GitHub Copilot?

**Setup:**
1. Create `.github/copilot-instructions.md` with protocol pointer
2. Copilot reads this automatically in GitHub Codespaces
3. For VS Code: Restart editor after adding file

**Limitations:**
- Copilot is best for code completion, not workflow management
- Doesn't understand multi-agent systems well
- Consider using Claude/ChatGPT for orchestration, Copilot for completion

**Template:** See `PROTOCOL_QUICKSTART.md` for copilot-instructions.md content

---

### Can I use Domain Zero in CI/CD?

**Yes!** Example use cases:
- Automated security reviews on PRs (Megumi)
- Code quality checks (Gojo's analysis)
- Test generation (Yuuji's TDD)

**Example GitHub Actions:**
```yaml
- name: Domain Zero Security Review
  run: |
    # Use AI API to run Megumi's security review
    curl -X POST https://api.anthropic.com/v1/complete \
      -d "prompt=Read protocol/MEGUMI.md - review changes in $(git diff HEAD~1)"
```

**Note:** Requires AI API access and careful prompt engineering.

---

### Does Domain Zero work with [my IDE]?

**Yes.** Domain Zero is IDE-agnostic:
- Works with any editor that can read markdown files
- No special plugins required
- AI integration depends on AI assistant, not IDE

**Recommended IDEs:**
- **VS Code** - Great with GitHub Copilot, Cursor
- **JetBrains** - Built-in AI features
- **Vim/Emacs** - Works via terminal AI assistants

---

## Troubleshooting

### Verification script fails with "placeholder values detected"

**Solution:**
1. Open `protocol.config.yaml`
2. Replace ALL placeholder values:
   - `"Your Name"` → Your actual name
   - `"email@example.com"` → Your actual email
   - `"Your Project Name"` → Your project name
   - `"your-org/your-repo"` → Your repository URL
   - `"YYYY-MM-DD"` → Actual date (ISO 8601 format)
3. Run verification script again

**See Also:** README.md → Troubleshooting → Configuration Issues

---

### Agent doesn't appear after @security-review tag

**Causes:**
1. **Tier 1 selected:** Security review is optional in Tier 1
2. **MEGUMI.md not found:** Verify file exists in `protocol/` directory
3. **Manual invocation needed:** Say `"Read protocol/MEGUMI.md - review changes"`

**Prompted Handoff Only Works:**
- In Tier 2 and Tier 3
- When Yuuji outputs prompt for Megumi invocation
- When MEGUMI.md is present

---

### Scripts won't execute (Permission denied)

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

### Can I speed up verification or skip certain checks?

**Yes!** Version 6.2.6+ added selective execution options:

**Quick Mode (60% faster):**
```bash
./scripts/verify-protocol.sh --quick          # Unix/Linux/macOS
.\scripts\verify-protocol.ps1 -Quick          # Windows
```
Runs only critical checks (dependencies, files, config, yaml)

**Skip Specific Checks:**
```bash
./scripts/verify-protocol.sh --skip=isolation --skip=templates
.\scripts\verify-protocol.ps1 -Skip isolation,templates
```

**Run Only Specific Checks:**
```bash
./scripts/verify-protocol.sh --only=files --only=config
.\scripts\verify-protocol.ps1 -Only files,config
```

**List All Available Checks:**
```bash
./scripts/verify-protocol.sh --list
.\scripts\verify-protocol.ps1 -List
```

**Available Checks:**
- `dependencies` (critical)
- `files` (critical)
- `config` (critical)
- `yaml` (critical)
- `isolation` (warning)
- `templates` (warning)
- `protection` (warning)
- `backup` (warning)

**Use Cases:**
- **CI/CD:** Use `--quick` for faster builds
- **Debugging:** Use `--only=config` to test specific issues
- **Development:** Skip non-critical checks with `--skip`

---

## Advanced Topics

### Can I customize agent prompts?

**Yes!** Edit the protocol files directly:
- `protocol/YUUJI.md` - Customize implementation approach
- `protocol/MEGUMI.md` - Adjust security checklist
- `protocol/NOBARA.md` - Modify UX principles
- `protocol/GOJO.md` - Change project management style

**Agents will re-read automatically.**

**Tip:** Make small changes and test. Keep backups.

---

### How do I extend the tier system (add Tier 4)?

**Approach:**
1. Edit `.protocol-state/tier-system-specification.md`
2. Define Tier 4 requirements (tests, reviews, documentation, etc.)
3. Update `CLAUDE.md` (repository root; `protocol/CLAUDE.md` is a compatibility pointer/stub since v9.11.0) to reference Tier 4
4. Update `protocol.config.yaml` with tier4 settings
5. Update `protocol/TIER-SELECTION-GUIDE.md` with decision tree

**Example Use Case for Tier 4:**
- Compliance-critical code (HIPAA, PCI-DSS)
- Multiple security reviews (AI + human)
- Formal verification or proof
- Extensive documentation requirements

---

### Can I run multiple agents in parallel?

**Yes**, for independent tasks:
- Yuuji implements Feature A
- Nobara designs UX for Feature B
- Megumi reviews Feature C

**No**, for dependent tasks:
- Megumi can't review code that doesn't exist yet
- Yuuji needs Megumi's findings before fixing issues

**Orchestration:** Gojo can manage parallel workflows.

---

### How do I migrate from v6.x to v7.x (future major version)?

**When v7.0.0 is released:**
1. Read `MIGRATION_GUIDE_v6_to_v7.md` (will be provided)
2. Review breaking changes in CHANGELOG
3. Create git branch for migration
4. Update protocol files incrementally
5. Run verification scripts
6. Test thoroughly before switching

**Migration guides will be provided** for all major version updates.

---

### Can I use Domain Zero for non-code projects?

**Yes!** Adapt for:
- **Documentation Projects:** Yuuji writes, Megumi checks accuracy
- **Design Projects:** Nobara creates designs, Megumi reviews accessibility
- **Data Science:** Yuuji implements analysis, Megumi checks statistical validity

**Customization Required:** Edit agent prompts to focus on your domain instead of code.

---

### What is domain.record.md? (v8.8.0+)

**A:** A shared notes repository for Gojo (Mission Control) and Sukuna (System Update Adversary) that prevents their agent files from exceeding token limits. It stores:
- Session observations and notes
- Strategic decisions with rationale
- Protocol update tracking
- Learning patterns across sessions
- Crash recovery checkpoints

**Access:** Gojo + Sukuna ONLY (all other agents denied)
**Location:** `.dzp-domain/domain.record.md`
**Auto-rotation:** Archives at 5,000 lines to `.dzp-domain/archive/`
**Git tracking:** Gitignored by default (configurable via `protocol.config.yaml`)

---

### Why can't other agents access domain.record.md?

**A:** Access is restricted to Gojo and Sukuna to:
1. Maintain clear separation between operational notes (domain.record.md) and agent-specific logs (dev-notes.md, security-review.md)
2. Prevent cross-contamination of strategic intelligence
3. Preserve the integrity of crash recovery checkpoints
4. Enforce the three-tier authorization hierarchy (USER > Gojo/Sukuna > Other agents)

**Other agents** use their own dedicated logs:
- Yuuji → `.protocol-state/dev-notes.md`
- Megumi → `.protocol-state/security-review.md`
- Gojo/Sukuna → `.dzp-domain/domain.record.md` (shared)

---

### How do I rotate the domain record when it gets large?

**A:** The system auto-rotates at 5,000 lines, but you can manually trigger rotation:

```bash
# Check current size
python scripts/domain-record-rotate.py --check

# Force rotation (creates archive)
python scripts/domain-record-rotate.py --rotate
```

**What happens during rotation:**
1. Current `domain.record.md` archived to `.dzp-domain/archive/domain.record_YYYYMMDD_HHMMSS.md`
2. Fresh template created for new notes
3. Rotation metadata updated (`.dzp-domain/.rotation-metadata.json`)
4. Old archives cleaned up (keeps last 10 by default)

---

## Still Have Questions?

**Resources:**
- **README.md** - Complete protocol documentation
- **PROTOCOL_QUICKSTART.md** - 2-minute quick start
- **SECURITY.md** - Security and vulnerability reporting
- **Troubleshooting** - README.md → Troubleshooting section

**Community:**
- **GitHub Issues:** https://github.com/DewyHRite/Domain-Zero-Protocol/issues
- **Discussions:** Tag with `question` label

**Direct Support:**
- Critical issues: the project's GitHub Security Advisories page (https://github.com/DewyHRite/Domain-Zero-Protocol/security/advisories)
- General questions: GitHub Issues

---

**Last Updated:** August 3, 2026
**Protocol Version:** v9.11.0
**Canonical Source:** https://github.com/DewyHRite/Domain-Zero-Protocol
