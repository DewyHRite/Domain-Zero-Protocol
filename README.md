# Domain Zero Protocol
<!-- [CORE FILE] - Domain Zero Protocol v9.8.1 -->

**Version**: 9.8.1 | **Last Updated**: 2026-06-22

A nine-agent AI development system plus one external auditor inspired by Jujutsu Kaisen, designed for Claude, GitHub Copilot, and any AI assistant.

---

## ✨ Core Capabilities

Domain Zero Protocol bundles a complete, opinionated AI-development workflow. Every capability below ships in the current release; for the dated release history see [`CHANGELOG.md`](CHANGELOG.md) and [`VERSION.md`](VERSION.md).

- **Ten agents** — nine resident agents (Gojo, Yuuji, Megumi, Nobara, Todo, Maki, Panda, Inumaki, Sukuna) plus Toji, an external report-only auditor.
- **Dual implementation + security workflow** — test-first development (Yuuji) gated by OWASP Top 10 security review (Megumi), with a remediation loop driven to zero findings.
- **Three-tier workflow system** — Rapid / Standard / Critical, matching process rigor to feature criticality.
- **DZP Cortex — local semantic memory** — an on-device, cited vector index of your protocol and project docs, with read-only `dedup`/`doctor` health diagnostics and shared-brain support across nested installs. Local after the first model download; no cloud inference.
- **Safety-first design** — Absolute Zero Protocol, kill-switch emergency stop, work-session fatigue monitoring (4h/6h/8h alerts), and user-authority-first decisioning.
- **Skills system** — `/session`, `/ts-tier*`, `/brain`, and per-agent slash commands for common operations.
- **Protected project memory** — append-only dev-notes, security-review, and domain-record documents form a permanent, auditable project history.

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

# Read main protocol authority
Read ./CLAUDE.md
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
/ts-tier1          # Troubleshooting tier 1
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

## 🔒 Protected-Document Append-Only Enforcement (FEAT-GUARD-001, v9.4.1)

The protocol's three permanent project-memory files — `dev-notes.md`, `security-review.md`, and
`domain.record.md` — are guarded by a pre-commit hook that enforces byte-prefix append-only
invariant: if a staged version is shorter than (or starts differently from) the HEAD version,
the commit is rejected.

**Install the hook** once per fresh clone:
```bash
scripts/install-git-hooks.sh     # macOS/Linux
scripts\install-git-hooks.ps1    # Windows PowerShell
```

**Override for authorized rewrites** (file rotation, emergency restore):
```bash
DZP_ALLOW_PROTECTED_REWRITE=1 git commit -m "chore: rotate dev-notes.md"
```

Configuration lives in `protocol.config.yaml` under `protected_documents`. See
`scripts/check_protected_append_only.py` for the implementation and
`CLAUDE.md` § Protected-Document Append-Only Enforcement for full details.

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
/ts-tier1
/dzp-roe
```

See [SKILL_REGISTRY.md](protocol/skills/SKILL_REGISTRY.md) for all skills.

### 🧠 DZP Cortex (v9.1.0) — Local Semantic Memory

DZP Cortex gives resident agents local cited recall of protocol history, decisions, and security findings. It runs entirely on-device; no cloud inference is required after the first model download.

```powershell
scripts/brain.ps1 status          # check DB health
scripts/brain.ps1 query "text"    # semantic recall (cited chunks)
scripts/brain.ps1 remember "fact" --type decision --agent gojo  # store distilled memory
scripts/brain.ps1 index --incremental  # refresh index
```
```bash
scripts/brain.sh status|query|remember|index   # POSIX equivalent
```

Retrieved chunks are data, not instructions. Protected documents remain canonical. Memories are untrusted by default; use `--trust trusted,semi` for security or release decisions. **Toji has no Cortex CLI access.** See `protocol/skills/brain.md` for the full command contract.

#### Setup (one-time)

Cortex is optional and **fail-soft** — if it isn't set up, every DZP workflow still runs normally; recall/remember steps are simply skipped. To enable it:

```bash
# 1. Install the engine dependencies (Python 3.8+)
pip install -r .protocol-state/brain/requirements-brain.txt

# 2. Build the initial index (this also performs the one-time embedding-model download,
#    so it happens now at setup time rather than mid-workflow)
scripts/brain.ps1 index          # POSIX: scripts/brain.sh index

# 3. Verify
scripts/brain.ps1 status         # expect: Cortex status: ok
```

**Auto-indexing (optional):** to keep recall fresh automatically, copy the shipped sanitized template into your local settings:
```bash
cp .claude/settings.template.json .claude/settings.json   # .claude/settings.json is gitignored
```
The template pre-wires a `hooks.SessionEnd` index refresh and allow-lists the `brain` commands. **POSIX hosts:** change the hook command to `bash scripts/brain-index-hook.sh`. The hook is fail-soft, lock-guarded, and times out at 30s, so it never blocks session end. Mid-session, `/session update` automatically keeps Cortex in sync — it runs `brain index --incremental` as the final step of the full project-document sync (fail-soft; skipped if Cortex is unavailable). `/session end` triggers a full rebuild plus an export snapshot. Use `update --time-only` to skip the sync and re-index when only a quick timestamp update is needed.

> **Note:** Cortex stores all runtime data (DB, memories, model cache) in an external dir (`%LOCALAPPDATA%/dzp-cortex/` on Windows; XDG equivalent on macOS/Linux), never inside the repo. The data dir refuses cloud-synced locations (OneDrive/Dropbox) and network shares.

#### Encryption-at-Rest (v9.8.1, opt-in)

Cortex supports SQLCipher-based AES-256 encryption of the vector database (PLAN-CORTEX-ENC-001).

**Why it matters — OneDrive/cloud-sync exposure:** Even though the data dir rejects OneDrive paths at setup time, Windows occasionally redirects `%LOCALAPPDATA%` transparently (roaming profiles, IT policy). Enabling encryption ensures the `brain.db` file is unreadable without the key even if it lands in a synced folder.

**Opt-in flow:**

```bash
# 1. Install encryption dependencies (one-time, not included in the base install)
pip install -r requirements-enc.txt

# 2. Set the encryption key (stored in the system keyring by default)
scripts/brain.ps1 key set        # POSIX: scripts/brain.sh key set

# 3. Encrypt the existing plaintext database (backup-first, atomic)
scripts/brain.ps1 encrypt --execute   # POSIX: scripts/brain.sh encrypt --execute

# 4. Verify
scripts/brain.ps1 status         # expect: availability_status: ok, encryption_status: unlocked
```

**Scope — single-user only:** Encryption is per-install. Shared-brain installs (multiple DZP projects sharing one `brain.db`) cannot use encryption in v9.8.1 — the `encrypt` command will refuse when a shared ledger is detected. Multi-install shared-key support is deferred to v9.9.x.

**Residuals to clean up after encrypting:**

- `*.pre-encrypt.*.bak` — the plaintext backup created by `brain encrypt --execute`. Securely delete it once you have verified the encrypted brain is healthy (`brain status` reports ok).
- `memories/*.jsonl` export snapshots — these are written in plaintext by `brain export`. Keep them encrypted or delete them when no longer needed.
- **Windows salt-ACL caveat:** The Argon2id salt file written to the data dir is ACL-restricted to the current user on Windows. On non-Windows hosts the salt file falls back to `0600` permissions; verify with `ls -l` if you are on a shared system.

---

## 📚 Documentation Structure

### Core Protocol
- **[CLAUDE.md](CLAUDE.md)** - Primary protocol authority (START HERE)
- **[protocol/CLAUDE.md](protocol/CLAUDE.md)** - Compatibility mirror for legacy entrypoints
- **[AI_INSTRUCTIONS.md](AI_INSTRUCTIONS.md)** - Complete installation guide for AI assistants
- **[protocol.config.yaml](protocol.config.yaml)** - Configuration settings

### Agent Files
- **[protocol/*.agent.md](protocol/)** - Individual agent specifications (10 files, including Toji)

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

## 📜 Version History

Release history, per-version changes, and migration notes live in the dedicated changelog files — not in this README:

- **[CHANGELOG.md](CHANGELOG.md)** — full, dated changelog for every release.
- **[VERSION.md](VERSION.md)** — per-release summaries and the current protocol version.

---

## 🔗 Links & Resources

**Canonical Source**: https://github.com/DewyHRite/Domain-Zero-Protocol

**Documentation**:
- [Installation Guide](docs/installation/IMPLEMENTATION_GUIDE.md)
- [DZP Cortex Guide](docs/guides/DZP_CORTEX.md)
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

**Domain Zero Protocol v9.8.1**
**AI-Assisted Development Done Right**

