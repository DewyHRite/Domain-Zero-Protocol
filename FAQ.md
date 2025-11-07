# Domain Zero Protocol - Frequently Asked Questions (FAQ)

**Version:** v6.2.4
**Last Updated:** November 7, 2025

---

## Table of Contents

- [Getting Started](#getting-started)
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

Domain Zero is a four-agent AI development framework that provides specialized expertise through distinct AI personalities:
- **YUUJI** - Implementation Specialist (test-first development)
- **MEGUMI** - Security Analyst (OWASP Top 10 reviews)
- **NOBARA** - Creative Strategy & UX (user experience design)
- **GOJO** - Mission Control (project lifecycle, protocol guardian)

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

```
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
1. **Protocol files not read:** Say `"Read protocol/CLAUDE.md"`
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

**Other protocol files (YUUJI.md, MEGUMI.md, etc.):**
- All agents have READ-ONLY access
- Only you can modify

**Why?** Prevents agents from accidentally changing their own behavior.

---

### How do I invoke a specific agent?

**Standard Invocation:**
```
Read protocol/YUUJI.md
```

**With Context:**
```
Read protocol/MEGUMI.md - review the authentication changes in auth.py
```

**Agent Handoff:** Agents will automatically hand off to each other:
- Yuuji completes implementation → tags @security-review → Megumi appears
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
- **Email:** dwaynewright1@outlook.com (critical issues)
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
```
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

**Automatic Handoff Only Works:**
- In Tier 2 and Tier 3
- When Yuuji includes @security-review tag
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
3. Update `protocol/CLAUDE.md` to reference Tier 4
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
- Critical issues: dwaynewright1@outlook.com
- General questions: GitHub Issues

---

**Last Updated:** November 7, 2025
**Protocol Version:** v6.2.4
**Canonical Source:** https://github.com/DewyHRite/Domain-Zero-Protocol
