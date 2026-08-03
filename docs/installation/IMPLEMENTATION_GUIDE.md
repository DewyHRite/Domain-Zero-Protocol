<!-- [CORE FILE] - Domain Zero Protocol v9.11.0 -->
# Domain Zero Protocol - Implementation Guide
## Step-by-Step Setup for Claude, GitHub Copilot, and Any AI Assistant

**Version**: 9.11.0
**Last Updated**: 2026-08-03
**Purpose**: Complete setup instructions for implementing Domain Zero Protocol with any AI assistant

> **9.x note**: v9.x adds **DZP Cortex** (local semantic memory) and a consolidated
> state model. After copying files, complete the **[DZP Cortex Setup](#dzp-cortex-setup-9x)**
> step, and if you are upgrading an 8.x install, run the **[8.x → 9.x state migration](#8x--9x-state-migration)**.

---

## 📋 Table of Contents

- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Detailed Setup by Platform](#detailed-setup-by-platform)
  - [Claude.ai (Web Interface)](#claudeai-web-interface)
  - [Claude Code (VS Code Extension)](#claude-code-vs-code-extension)
  - [GitHub Copilot](#github-copilot)
  - [Generic AI Setup](#generic-ai-setup)
- [Dual-AI Meta Prompt Setup](#dual-ai-meta-prompt-setup-recommended) 🆕 RECOMMENDED
- [Configuration](#configuration)
- [Testing Your Setup](#testing-your-setup)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Quick Start (5 Minutes)

**Prerequisites**:
- Downloaded the latest `DZP-v9.x` release package
- Access to Claude.ai, Claude Code, GitHub Copilot, or another AI assistant
- Python 3.8+ (for state tooling and DZP Cortex)

---

### CRITICAL: Fresh Install vs In-Place Upgrade

**Before proceeding, determine your installation type:**

| Scenario | Installation Type | Instructions |
|----------|------------------|--------------|
| New project (no existing DZP) | **Fresh Install** | Use [Fresh Install Flow](#fresh-install-flow-new-projects) |
| Existing project with DZP already installed | **In-Place Upgrade** | Use [In-Place Upgrade Flow](#in-place-upgrade-flow-existing-projects) |

**WARNING:** Using Fresh Install commands on an existing DZP project will overwrite your project-specific state (dev-notes.md, security-review.md, project-state.json). Always use the correct flow for your situation.

---

### Obtaining a Release (Verified Payload — recommended, v9.10.2+)

Every release publishes a **GitHub Release asset pair**: `dzp-payload-vX.Y.Z.zip` and its sibling
`dzp-payload-vX.Y.Z.manifest.json`. Verify BEFORE you extract — `scripts/verify-payload.py` is
**stdlib-only** (no DZP install, no third-party packages needed) and is exactly what you'd want to
run against a file you just downloaded from the internet:

```bash
# 1. Download both files from the release's "Assets" section (same release page).
# 2. Verify + extract in ONE step (never verify now and install later from a moved/copied
#    file -- that reintroduces the exact time-of-check/time-of-use gap this flag exists to close):
python scripts/verify-payload.py dzp-payload-v9.10.2.zip --extract-to DZP-v9.10.2
```

What this checks, in order, before it will extract anything: the zip's own hash matches its
manifest; the manifest bundled inside the zip matches the one you downloaded; the shipped verifier
script inside the zip matches its own recorded hash; every file the manifest declares is present
with a matching hash (and the zip contains nothing UNDECLARED); and — the step that distinguishes
this from a plain checksum file — that the manifest's recorded release branch genuinely resolves,
on this project's **canonical public GitHub repository**, to the manifest's recorded commit
(`git ls-remote`, using your local `git`). That last check requires a working internet connection
and a `git` binary on `PATH`; if you are genuinely offline, `--skip-origin-check` will proceed
without it, printing a loud warning that this step alone provides no supply-chain provenance
assurance beyond internal self-consistency — it should not be your everyday default.

The result of a successful run is a plain directory (`DZP-v9.10.2/` in the example above) with the
exact same layout as an unpacked release archive — use it as `DZP_SRC` in either flow below.

**Trust model, briefly:** this check confirms the download is internally consistent AND points
somewhere real on the project's own GitHub repository — the same trust boundary as cloning that
repository directly. It is a supply-chain consistency check, not a code-review substitute, and (in
its default mode) it does not cryptographically bind the zip's file bytes to that commit's git
tree object — pass `--deep-verify` for a stronger (network- and time-costly) check that shallow-clones
the canonical commit and byte-compares every file directly. Run `python scripts/verify-payload.py --help`
for the full option list and exit-code meanings.

---

### Fresh Install Flow (New Projects)

**Use this flow ONLY if:**
- Your project has NO existing `protocol/` directory
- Your project has NO existing `.protocol-state/` directory

```bash
# macOS/Linux  (DZP_SRC = the unpacked release dir, e.g. DZP-vX.Y.Z)
DZP_SRC=DZP-vX.Y.Z
mkdir -p your-project/protocol your-project/.protocol-state
cp -r "$DZP_SRC/protocol" your-project/
cp -r "$DZP_SRC/.protocol-state" your-project/
cp "$DZP_SRC/protocol.config.yaml" your-project/
cp "$DZP_SRC/requirements-dev.txt" your-project/
cp "$DZP_SRC/README.md" your-project/DOMAIN_ZERO_README.md

# Windows PowerShell
$DzpSrc = "DZP-vX.Y.Z"
New-Item -ItemType Directory -Force -Path "your-project\protocol", "your-project\.protocol-state"
Copy-Item -Recurse "$DzpSrc\protocol" -Destination your-project\
Copy-Item -Recurse "$DzpSrc\.protocol-state" -Destination your-project\
Copy-Item "$DzpSrc\protocol.config.yaml" -Destination your-project\
Copy-Item "$DzpSrc\requirements-dev.txt" -Destination your-project\
```

After copying, customize `.protocol-state/project-state.json` with your project metadata,
then complete the **[DZP Cortex Setup](#dzp-cortex-setup-9x)** step below.

---

### In-Place Upgrade Flow (Existing Projects)

**Use this flow if you already have DZP installed in your project.**

#### Step 1: Backup (MANDATORY)
```bash
# Create timestamped backup of ALL existing files including .protocol-state/ (capture timestamp once)
BACKUP_DIR="backup/dzp-pre-upgrade-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp -r protocol/ "$BACKUP_DIR/"
cp -r .protocol-state/ "$BACKUP_DIR/"
cp protocol.config.yaml "$BACKUP_DIR/"
echo "✅ Backup created in: $BACKUP_DIR"
```

#### Step 2: Sync Protocol Files ONLY (Safe to Overwrite)
```bash
# DZP_SRC = the unpacked release dir, e.g. DZP-vX.Y.Z
DZP_SRC=DZP-vX.Y.Z
# These files are protocol artifacts - safe to overwrite
mkdir -p your-project/protocol your-project/docs your-project/.dzp-killswitch your-project/.claude/commands
cp -r "$DZP_SRC/protocol/"* your-project/protocol/
cp -r "$DZP_SRC/docs/"* your-project/docs/
cp -r "$DZP_SRC/.claude/commands/"* your-project/.claude/commands/
cp -r "$DZP_SRC/.dzp-killswitch/"* your-project/.dzp-killswitch/ 2>/dev/null || true
# 9.x: also sync the Cortex engine + dev requirements
cp -r "$DZP_SRC/.protocol-state/brain" your-project/.protocol-state/
cp "$DZP_SRC/requirements-dev.txt" your-project/
```

#### Step 3: DO NOT Copy .protocol-state/ Wholesale
```bash
# ✗ NEVER DO THIS on existing projects:
# cp -r "$DZP_SRC/.protocol-state/"* your-project/.protocol-state/  # WRONG! clobbers your state

# ✓ Instead, update protocol_version in project-state.json to 9.3.0
#   (the 8.x → 9.x migration below adds any newly-required keys for you).
```

#### Step 4: Verify Your Project State
```bash
# Confirm your project-specific files are intact:
cat .protocol-state/dev-notes.md        # Should have YOUR project's implementation history
cat .protocol-state/security-review.md  # Should have YOUR project's security findings
cat .protocol-state/project-state.json  # Should have YOUR project metadata
```

**Protected Files (NEVER Overwritten):**
- `.protocol-state/dev-notes.md` - Your implementation history
- `.protocol-state/security-review.md` - Your security findings
- `.protocol-state/trigger-19.md` - Your private intelligence
- `.protocol-state/project-state.json` - Your project metadata (update version only)

#### Step 5 (8.x → 9.x only): Run the state migration

See **[8.x → 9.x state migration](#8x--9x-state-migration)** below — it additively adds the
new required 9.x keys (`tier_settings`, `validation_state`, `agent_registry`) and repairs any
naive timestamps, preserving all of your existing state.

#### Step 6: Set up DZP Cortex

See **[DZP Cortex Setup (9.x)](#dzp-cortex-setup-9x)** below to install dependencies and build
the first semantic index.

---

### 8.x → 9.x State Migration

v9.x requires three top-level keys a pre-9.x `project-state.json` lacks (`tier_settings`,
`validation_state`, `agent_registry`). The migration is **additive** (never overwrites your
data) and also repairs legacy naive timestamps that can otherwise disable the wellbeing
safety check.

```bash
# Dry run (shows exactly what would change; makes no edits):
python .protocol-state/migrate_state_9x.py --check

# Apply (a timestamped backup is written first):
python .protocol-state/migrate_state_9x.py --execute

# Verify:
pip install -r requirements-dev.txt   # jsonschema + PyYAML, if not already installed
python scripts/validate-protocol.py --check
```

If anything looks wrong: `python .protocol-state/migrate_state_9x.py --rollback`.

---

### DZP Cortex Setup (9.x)

DZP Cortex is the local, on-device semantic memory layer. It has no cloud calls after the
first model download.

```bash
# 1) Install the Cortex runtime
python -m pip install -r .protocol-state/brain/requirements-brain.txt

# 2) Build the first index (downloads the embedding model on first run)
scripts/brain.sh index           # POSIX
# scripts/brain.ps1 index        # Windows PowerShell

# 3) Confirm it works
scripts/brain.sh status
scripts/brain.sh query "prior security decision"
```

Cortex data lives **outside** the repo (`%LOCALAPPDATA%\dzp-cortex\<id>` on Windows;
`~/.local/share/dzp-cortex/<id>` elsewhere) and never ships in the repo or distro.

**Projects under OneDrive/Dropbox/iCloud**: the default location is already outside the synced
folder, so no action is needed. **Sharing one brain across a parent repo + nested submodules**:
set the same `install_group:` in each install's `brain.config.yaml` (or `DZP_CORTEX_INSTALL_GROUP`).
See `.protocol-state/brain/README.md` for both recipes.

#### Cortex Schema Migrations (v1 → v4)

If you are upgrading an existing Cortex installation, you need to run the schema migration
scripts in sequence. Each migration is backup-first, parity-gated, and idempotent — always
run `--check` before `--execute`.

**Always run `--check` first.** Each script backs up the database before any changes.

```bash
# v1 → v2: Content-addressed storage (v9.4.0)
# Requires: sqlite-vec installed (pip install -r .protocol-state/brain/requirements-brain.txt)
python .protocol-state/migrate_cortex_storage_9_4.py --check
python .protocol-state/migrate_cortex_storage_9_4.py --execute

# v2 → v3: Graph structured recall (v9.6.0)
python .protocol-state/migrate_cortex_graph_9_6.py --check
python .protocol-state/migrate_cortex_graph_9_6.py --execute

# v3 → v4: Storage elasticity (v9.7.0)
python .protocol-state/brain/migrate_cortex_elastic_9_7.py --check
python .protocol-state/brain/migrate_cortex_elastic_9_7.py --execute
```

If a migration fails, each script exposes a `--rollback` flag that restores from the
backup created before the run. Run `scripts/brain.sh status` after each migration to
confirm the schema version advanced.

For the full Cortex architecture, retention configuration, and per-install storage
budgets, see **[docs/guides/DZP_CORTEX.md](../guides/DZP_CORTEX.md)**.

#### Post-upgrade / post-clone: install (or re-install) the git hooks

After every DZP upgrade or fresh clone, run the hook installer once to wire the
unified pre-commit guard (append-only enforcement, protected-path guard, protocol
validation):

```bash
# POSIX (macOS / Linux / WSL)
sh scripts/install-git-hooks.sh

# Windows PowerShell
pwsh scripts\install-git-hooks.ps1
```

The script backs up any non-DZP hook that was already present, then installs the
DZP unified hook.

**Husky repos**: if your project uses [Husky](https://typicode.github.io/husky/), the
hook must live in `.husky/pre-commit` instead of `.git/hooks/pre-commit`. Run the
installer scripts — they handle Husky detection automatically:

```bash
# macOS/Linux
bash scripts/install-git-hooks.sh

# Windows (PowerShell)
pwsh scripts\install-git-hooks.ps1
```

Or, if you prefer a manual copy, overwrite (do not append) the hook file to avoid
duplicating the guard on reinstall:

```bash
cp scripts/git-hooks/pre-commit .husky/pre-commit
```

This guard is the mechanical enforcement of the append-only rule for the three
protected documents (`dev-notes.md`, `security-review.md`, `domain.record.md`).
See the **FEAT-GUARD-001** section in `CLAUDE.md` for override instructions.

#### Bypassing the guard for legitimate edits

The guard protects the three append-only docs and immutable protocol paths. For
**authorized** single-commit overrides (e.g. editing `protocol.config.yaml` when the
agent-file guard blocks it, or performing a Sukuna-via-Gojo-sanctioned config change):

```bash
# One-shot bypass — skips all DZP pre-commit checks for this commit only:
git commit --no-verify -m "chore: update protocol.config.yaml (authorized)"
```

For **authorized full rewrites** of the three protected documents specifically
(file rotation, emergency snapshot restore — see `scripts/file-rotate.py`):

```bash
DZP_ALLOW_PROTECTED_REWRITE=1 git commit -m "chore: rotate dev-notes.md"
```

`DZP_ALLOW_PROTECTED_REWRITE=1` bypasses only the append-only guard; all other
hook checks still run. `--no-verify` skips the entire hook.

**Important**: `--no-verify` bypasses are sanctioned only through the Sukuna
(System Update Adversary) via Gojo coordination or by explicit User authorization.
All uses should be noted in the session domain record.

---

### Basic Setup (After Installation)

1. **Configure your AI assistant** (see platform-specific instructions below)

2. **Test with first agent**:
   ```
   "Read protocol/yuuji.agent.md and say hello"
   ```

3. **Review configuration**:
   - Edit `protocol.config.yaml` for your project
   - Adjust tier workflow (rapid/standard/critical)
   - Enable/disable features as needed

4. **Start using agents**:
   ```
   "Read protocol/yuuji.agent.md and implement user authentication"
   ```

---

## Detailed Setup by Platform

---

### Claude.ai (Web Interface)

**Best For**: Quick prototyping, learning the protocol, personal projects

#### Step 1: Prepare Custom Instructions

1. **Create a custom instructions file** from the template below
2. **Save as**: `claude-custom-instructions.md`

**Template**:
```markdown
# Domain Zero Protocol Custom Instructions

I use the Domain Zero Protocol for AI-assisted development. This is a nine-agent system:

**Core Four Agents**:
- **Yuuji Itadori** (protocol/yuuji.agent.md): Implementation Specialist - Test-first development, feature implementation
- **Megumi Fushiguro** (protocol/megumi.agent.md): Security Analyst - OWASP Top 10 security reviews
- **Nobara Kugisaki** (protocol/nobara.agent.md): Creative Strategy & UX - User experience design, product vision
- **Satoru Gojo** (protocol/gojo.agent.md): Mission Control - Project lifecycle, protocol guardian

**Extended Four Agents**:
- **Aoi Todo** (protocol/todo.agent.md): Database & Backend Specialist - Schema design, migrations, query optimization
- **Maki Zenin** (protocol/maki.agent.md): Performance Optimization Specialist - Profiling, bundle analysis, zero-overhead
- **Panda** (protocol/panda.agent.md): Build & Integration Specialist - CI/CD, GitHub Actions, Docker
- **Toge Inumaki** (protocol/inumaki.agent.md): API & Communication Specialist - REST, GraphQL, WebSocket design

**Special Agent (v8.5.1+)**:
- **Ryomen Sukuna** (protocol/sukuna.agent.md): System Update Agent - Protocol updates, adversarial analysis (Gojo-invoked only)

**Three-Tier Workflow**:
- **Tier 1 (Rapid)**: Fast prototyping, no tests
- **Tier 2 (Standard)**: Production features with TDD + security review [DEFAULT]
- **Tier 3 (Critical)**: Enhanced testing + multi-model security review for auth/payments/sensitive data

**Protocol Location**: `/path/to/your-project/protocol/`

**When I say** "Read protocol/[AGENT].agent.md", always read the file first to follow the protocol.

**Main Protocol**: protocol/CLAUDE.md
**Configuration**: protocol.config.yaml
```

#### Step 2: Upload Protocol Files

**Option A: Upload to Claude.ai Project**

1. Go to https://claude.ai
2. Create a new **Project** (recommended for Domain Zero)
3. Click **"Add content"** → **"Upload files"**
4. Upload these files:
   - `protocol/CLAUDE.md`
   - `protocol/yuuji.agent.md`
   - `protocol/megumi.agent.md`
   - `protocol/nobara.agent.md`
   - `protocol/gojo.agent.md`
   - `protocol.config.yaml`
   - (Optional) Other protocol specs as needed

5. In **Project Instructions**, paste your custom instructions

**Option B: Upload Per Conversation**

1. Start a new conversation
2. Click the **paperclip icon** (attach files)
3. Upload the protocol files you need
4. In the first message, paste your custom instructions

#### Step 3: Invoke Your First Agent

**Test Message**:
```
Read protocol/yuuji.agent.md

I'm working on a React application. Can you help me implement user authentication using the standard tier workflow?
```

**Expected Response**:
```
🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"

Hey! I'm Yuuji Itadori, your Implementation Specialist. I've read my protocol...
[Agent continues with implementation guidance]
```

#### Step 4: Configure for Your Project

Edit `protocol.config.yaml` in your uploaded files:

```yaml
# Set your project metadata
project_metadata:
  name: "Your Project Name"
  description: "Your project description"

# Enable/disable features
mask_mode:
  enabled: true  # true = JJK theme, false = professional mode

# Set default tier
workflow:
  default_tier: "standard"  # rapid, standard, critical
```

---

### Claude Code (VS Code Extension)

**Best For**: Full development workflow, MCP integration, file editing

#### Step 1: Install Claude Code

1. Open **VS Code**
2. Go to **Extensions** (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for **"Claude Code"**
4. Click **"Install"**
5. Sign in with your Anthropic account

#### Step 2: Add Protocol to Your Project

1. **Copy protocol files** to your VS Code workspace:
   ```bash
   cd /your-project
   mkdir -p protocol
   cp -r /path/to/DZP-vX.Y.Z/protocol/* ./protocol/
   cp /path/to/DZP-vX.Y.Z/protocol.config.yaml ./
   ```

2. **Create `.protocol-state` directory** (for state management):
   ```bash
   mkdir .protocol-state
   ```

3. **Update `.gitignore`**:
   ```gitignore
   # Domain Zero Protocol state (local only)
   .protocol-state/
   .protocol-state/trigger-19.md
   .protocol-state/research/*.raw.log

   # Keep these (project state tracking)
   !.protocol-state/project-state.json
   !.protocol-state/dev-notes.md
   !.protocol-state/security-review.md
   !.protocol-state/research/*.summary.md
   ```

#### Step 3: Configure Claude Code Custom Instructions

1. Open **Command Palette** (Ctrl+Shift+P / Cmd+Shift+P)
2. Search for **"Claude Code: Open Custom Instructions"**
3. Paste this configuration:

```markdown
# Domain Zero Protocol

I use the Domain Zero Protocol for AI-assisted development. Protocol files are in this workspace.

**Core Agents**:
- protocol/yuuji.agent.md - Implementation Specialist
- protocol/megumi.agent.md - Security Analyst
- protocol/nobara.agent.md - Creative Strategy & UX
- protocol/gojo.agent.md - Mission Control

**Main Protocol**: protocol/CLAUDE.md
**Configuration**: protocol.config.yaml

**When I say** "Read protocol/[AGENT].agent.md", read the file to activate that agent's behavior.

**Default Tier**: Standard (TDD + Security Review)
```

#### Step 4: Initialize Project State

Create `.protocol-state/project-state.json`:

```json
{
  "protocol_version": "9.3.0",
  "project_metadata": {
    "name": "YOUR_PROJECT_NAME",
    "description": "Your project description",
    "created": "2025-12-22T00:00:00Z",
    "last_updated": "2025-12-22T00:00:00Z"
  },
  "current_feature_tier": "none",
  "current_state": "STANDBY",
  "active_role": "None",
  "version": "9.3.0"
}
```

#### Step 5: Test Your Setup

1. Open **Claude Code** panel in VS Code
2. Type:
   ```
   Read protocol/gojo.agent.md
   ```

3. Gojo should initialize and offer Mission Control options

### Pro Tips for Claude Code
- Use **@file** mentions to reference specific files: `@protocol/yuuji.agent.md`
- Claude Code can read, write, and edit files directly
- Full MCP (Model Context Protocol) support for tool integration
- Research mode works seamlessly with WebSearch tool

---

### GitHub Copilot

**Best For**: Inline code suggestions, GitHub-integrated workflows

**Note**: GitHub Copilot has more limited protocol support compared to Claude Code. The agents work as instruction sets rather than interactive sessions.

#### Step 1: Add Protocol to Repository

1. **Copy protocol files** to your repo:
   ```bash
   mkdir -p .github/domain-zero
   cp -r /path/to/DZP-vX.Y.Z/protocol .github/domain-zero/
   cp /path/to/DZP-vX.Y.Z/protocol.config.yaml .github/domain-zero/
   ```

2. **Create agent instruction summaries** in `.github/copilot-instructions.md`:

```markdown
# Domain Zero Protocol - Copilot Instructions

## Agent System

This project uses Domain Zero Protocol with nine agents:

**Core Four:**
1. **Yuuji (Implementation)**: Test-first development, feature implementation
2. **Megumi (Security)**: OWASP security review, threat modeling
3. **Nobara (UX)**: User experience design, creative strategy
4. **Gojo (Mission Control)**: Project orchestration

**Extended Four:**
5. **Todo (Database)**: Schema design, migrations, query optimization
6. **Maki (Performance)**: Profiling, bundle analysis, optimization
7. **Panda (Build/CI)**: CI/CD pipelines, GitHub Actions, Docker
8. **Inumaki (API)**: REST, GraphQL, WebSocket design

**System Update Agent:**
9. **Sukuna (System Update Adversary)**: Gojo-invoked only, adversarial-but-aligned protocol updates

## Workflow Tiers

- **Tier 1 (Rapid)**: Prototypes, no tests
- **Tier 2 (Standard)**: TDD + security review [DEFAULT]
- **Tier 3 (Critical)**: Enhanced tests + dual security review (auth/payments)

## Agent Activation

When user references an agent (e.g., "Yuuji, implement feature X"), follow that agent's protocol from `.github/domain-zero/protocol/[agent].agent.md`.

## Core Principles

- Test-first development (Tier 2/3)
- Security review before deployment (Tier 2/3)
- Backup before changes (all tiers)
- User safety is absolute priority
```

#### Step 2: Configure Copilot for Workspace

Create `.github/copilot.yml`:

```yaml
# GitHub Copilot Workspace Configuration
instructions:
  - file: .github/copilot-instructions.md

# Enable protocol awareness
context:
  - .github/domain-zero/protocol/CLAUDE.md
  - .github/domain-zero/protocol.config.yaml
```

#### Step 3: Use Agents in Comments

**In your code files**, use comments to invoke agents:

```python
# Yuuji: Implement user authentication with JWT tokens (Tier 2 - Standard)
# Requirements:
# - Test-first development
# - Backup before changes
# - Tag @security-review when ready

def login(username: str, password: str):
    # Agent will generate implementation here
    pass
```

```python
# Megumi: Review this authentication implementation for OWASP Top 10
# Focus areas:
# - A01:2021 Broken Access Control
# - A02:2021 Cryptographic Failures
# - A07:2021 Identification and Authentication Failures

def login(username: str, password: str):
    # Implementation to review
    ...
```

### Limitations
- GitHub Copilot doesn't have persistent state management
- No automatic handoff between agents
- Manual security review prompting required
- Limited to inline suggestions, not full conversational sessions

---

### Generic AI Setup

**Best For**: ChatGPT, Gemini, other AI assistants

#### Step 1: Create System Prompt

Save this as `domain-zero-system-prompt.md`:

```markdown
# Domain Zero Protocol System Prompt

You are an AI assistant operating under the Domain Zero Protocol DZP-vX.Y.Z.

## Agent System

I will invoke specific agents by saying "Read protocol/[AGENT].agent.md". When invoked:

1. Read the agent file in the protocol/ directory
2. Adopt that agent's personality, responsibilities, and constraints
3. Follow the agent's workflow exactly as specified
4. Self-identify using the agent's banner

## Available Agents

**Core Four:**
- **protocol/yuuji.agent.md**: Implementation Specialist (TDD, feature development)
- **protocol/megumi.agent.md**: Security Analyst (OWASP, threat modeling)
- **protocol/nobara.agent.md**: Creative Strategy & UX (design, product vision)
- **protocol/gojo.agent.md**: Mission Control (project orchestration)

**Extended Four:**
- **protocol/todo.agent.md**: Database & Backend (schema design, migrations)
- **protocol/maki.agent.md**: Performance (profiling, optimization)
- **protocol/panda.agent.md**: Build & Integration (CI/CD, deployment)
- **protocol/inumaki.agent.md**: API & Communication (REST, GraphQL, WebSocket)

**System Update Agent:**
- **protocol/sukuna.agent.md**: System Update Adversary (Gojo-invoked only)

## Workflow Tiers

- **Tier 1 (Rapid)**: Prototypes, experiments - no tests, no security review
- **Tier 2 (Standard)**: Production code - TDD + security review [DEFAULT]
- **Tier 3 (Critical)**: Sensitive features - enhanced tests + dual security review

## Core Principles

1. User safety is absolute priority
2. Test-first development (Tier 2/3)
3. Security review before deployment (Tier 2/3)
4. Create backups before changes (all tiers)
5. Transparency in all recommendations

## Protocol Files

Main protocol: protocol/CLAUDE.md
Configuration: protocol.config.yaml
```

#### Step 2: Upload Protocol Files

**For ChatGPT**:
1. Start a new chat
2. Upload protocol files (CLAUDE.md, agent files, config)
3. Paste the system prompt as your first message

**For Gemini**:
1. Use "Upload to Google Drive" integration
2. Share protocol folder with Gemini
3. Reference files in conversation

**For Other AIs**:
- Upload files via their file attachment feature
- Or paste relevant agent content directly into conversation
- Maintain system prompt at start of each session

#### Step 3: Invoke Agents

**Basic Invocation**:
```
Read protocol/yuuji.agent.md

I need to implement a user registration feature for my web app. Use Tier 2 (Standard) workflow.
```

**With Handoff**:
```
1. Read protocol/yuuji.agent.md and implement user registration
2. After implementation, read protocol/megumi.agent.md and review the code
```

---

## Dual-AI Meta Prompt Setup (Recommended)

**For power users**: Use two AI assistants together for optimal token efficiency and project context.

### Overview

Domain Zero includes `gojo.prompt.md`, a meta prompt that generates orchestrated workflow prompts. The recommended workflow:

1. **IDE AI** (prompt generator) - VS Code, Cursor, Antigravity, etc. reads `gojo.prompt.md`, generates `prompt.md`
2. **Main AI** (executor) - Claude CLI reads and executes `prompt.md`

### Why Use Two AIs?

| Benefit | Explanation |
|---------|-------------|
| **Full Project Context** | IDE AI has complete access to your codebase |
| **Token Savings** | 70-80% reduction on main AI usage |
| **Better Prompts** | IDE AI references actual files and code patterns |
| **Faster Iteration** | Pre-built prompts execute immediately |

### Setup Steps

#### Step 1: Place the Meta Prompt

Copy `gojo.prompt.md` to your project root:

```bash
cp /path/to/DZP-vX.Y.Z/gojo.prompt.md your-project/
```

#### Step 2: Configure IDE AI

**For Antigravity** (Recommended):
- Built-in AI has automatic project context
- No additional configuration needed
- Full file system access

**For Cursor**:
- Enable "Codebase" context in settings
- Cursor automatically indexes your project

**For GitHub Copilot Chat**:
- Use `@workspace` to include project context
- Example: `@workspace Read gojo.prompt.md and generate a prompt for...`

**For Cody (Sourcegraph)**:
- Enable repository indexing
- Use `@repo` mention for full context

#### Step 3: Generate Prompts

In your IDE AI:

```bash
Read gojo.prompt.md and generate a prompt for implementing user authentication with JWT
```

The IDE AI will:
1. Read your project structure
2. Auto-detect Tier 3 (Critical) for authentication
3. Generate `prompt.md` with:
   - Pre-execution checks
   - Agent assignments (Yuuji + Megumi)
   - Project-specific context
   - Success criteria

#### Step 4: Execute in Main AI

In Claude CLI:

```bash
claude
> "Read prompt.md"
```

Claude executes the complete workflow without re-reading protocol files.

### Example Session

```bash
# Terminal 1: IDE with Antigravity
$ code your-project/

# In Antigravity chat:
"Read gojo.prompt.md and create a prompt for adding Stripe payment integration"

# Antigravity generates prompt.md with:
# - Tier 3 (Critical) auto-detected
# - Yuuji + Megumi agents
# - OWASP payment security checklist
# - Your existing payment utils referenced

# Terminal 2: Claude CLI
$ cd your-project
$ claude
> "Read prompt.md"

# Claude executes the pre-built workflow
```

### Tips for Dual-AI Workflow

1. **Keep prompt.md in .gitignore** - It's session-specific
2. **Review generated prompts** - Verify tier and agent selection
3. **Iterate on generation** - Ask IDE AI to refine if needed
4. **Use for complex tasks** - Simple tasks can use direct agent invocation

### Supported IDE AIs

| IDE AI | Context Quality | Setup Difficulty |
|--------|----------------|------------------|
| **VS Code + Copilot Chat** | Good | Use @workspace |
| **Antigravity** | Excellent | None (VS Code extension) |
| **Cursor** | Excellent | Minimal |
| **Cody** | Good | Enable indexing |
| **Continue** | Variable | Model-dependent |

---

## Configuration

### protocol.config.yaml Essentials

Edit your `protocol.config.yaml` file to customize the protocol:

#### Project Metadata

```yaml
project_metadata:
  name: "Your Project Name"
  description: "Brief project description"
  stack: "React, Node.js, PostgreSQL"  # Your tech stack
  repository: "https://github.com/user/repo"
```

#### Mask Mode (JJK Theme Toggle)

```yaml
mask_mode:
  enabled: true  # true = JJK theme, false = professional mode

  # Granular controls
  settings:
    use_domain_banners: true      # "🛠️ IMPLEMENTATION DOMAIN ACTIVATED"
    use_agent_personality: true   # Yuuji's enthusiasm, Megumi's caution
    use_jjk_terminology: true     # "Domain Expansion", "Cursed Technique"
    use_emoji_identifiers: true   # ⚡🛡️🎯🌀 emojis
    use_narrative_framing: true   # "The Weight", character backgrounds
```

**When to disable Mask Mode**:
- Corporate/enterprise projects
- Client-facing work
- Regulated industries
- Team members unfamiliar with JJK

**Set to** `enabled: false` for professional mode

#### Workflow Defaults

```yaml
workflow:
  default_tier: "standard"  # rapid, standard, critical

  # Tier-specific settings
  tiers:
    tier_1_rapid:
      require_tests: false
      require_security_review: false
      require_backup: true  # Always required

    tier_2_standard:
      require_tests: true
      require_security_review: true
      require_backup: true
      test_coverage_target: 80  # percentage

    tier_3_critical:
      require_tests: true
      require_security_review: true
      require_backup: true
      require_integration_tests: true
      require_e2e_tests: true
      test_coverage_target: 95
      dual_model_security: true  # If available
```

#### Research Mode

```yaml
research:
  enabled: true

  cadence:
    yuuji: "weekly"      # Implementation knowledge
    megumi: "weekly"     # Security threats
    nobara: "biweekly"   # UX/accessibility
    gojo: "monthly"      # Strategic trends

  max_session_minutes: 25

  source_policy:
    max_sources: 12
    min_primary_sources: 3  # OWASP, NIST, W3C, RFC
```

#### Safety & Wellbeing

```yaml
safety:
  enabled: true  # Cannot be disabled

  boundaries:
    max_continuous_work_hours: 4
    late_night_warning_hour: 22  # 10 PM
    fatigue_check_interval_hours: 2

  session_tracking:
    enabled: true
    state_file: ".protocol-state/session-state.json"
    session_continuation_threshold_minutes: 30
    auto_archive_on_end: true
    block_high_risk_when_fatigued: true
    high_risk_session_threshold_minutes: 360  # 6 hours
```

#### Domain Record System (DZP-v9.3.0+)

```yaml
# Shared notes repository for Gojo and Sukuna
# Prevents agent files from exceeding token limits
domain_record:
  enabled: true
  location: ".dzp-domain/domain.record.md"

  # Access Control (Gojo and Sukuna ONLY)
  allowed_agents:
    - gojo
    - sukuna

  # Auto-Rotation Settings
  rotation:
    enabled: true
    threshold_lines: 5000                # Archive at 5,000 lines
    archive_location: ".dzp-domain/archive/"
    keep_archives: 10                     # Keep last 10 rotations

  # Git Tracking
  git_tracked: false  # true = commit to repo, false = gitignored (DEFAULT)

  # Content Types
  content_types:
    - session_notes
    - strategic_decisions
    - protocol_updates
    - learning_patterns
    - crash_recovery

  # File Integrity Monitoring
  integrity_monitoring: true  # Track in file-integrity.json
```

**Purpose**: domain.record.md stores session notes, strategic decisions, and crash recovery checkpoints for Gojo and Sukuna. It auto-rotates at 5,000 lines to prevent bloat.

**Manual rotation**:
```bash
python scripts/domain-record-rotate.py --check   # Check size
python scripts/domain-record-rotate.py --rotate  # Force rotation
```

---

## Testing Your Setup

### Test 1: Agent Activation

**Command**:
```
Read protocol/yuuji.agent.md and say hello
```

**Expected Response**:
```
🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"

Hey! I'm Yuuji Itadori, your Implementation Specialist...
```

### If Mask Mode is OFF
```
Implementation Specialist - Active

Hello! I'm your Implementation Specialist, ready to help...
```

### Test 2: Tier Workflow

**Command**:
```
Read protocol/yuuji.agent.md --tier rapid and create a simple "Hello World" Python script
```

**Expected Behavior**:
- Yuuji creates script without tests (Tier 1)
- Creates backup first
- No security review mentioned
- Fast implementation

### Test 3: Security Handoff

**Command**:
```
Read protocol/yuuji.agent.md --tier standard and implement JWT token generation

After implementation, read protocol/megumi.agent.md and review the code
```

**Expected Behavior**:
1. Yuuji implements with tests
2. Yuuji tags `@security-review` in dev-notes
3. Megumi activates and conducts OWASP review
4. Megumi documents findings with SEC-IDs
5. If issues found, remediation loop begins

### Test 4: Mission Control

**Command**:
```
Read protocol/gojo.agent.md
```

**Expected Response**:
```
🌀 MISSION CONTROL DOMAIN ACTIVATED 🌀
"Orchestration, Review, and Passive Observation"

Welcome. I'm Gojo, Mission Control and Protocol Guardian.

[Presents 3 options]
1. Resume Current Project
2. New Project Initialization
3. Trigger 19 Intelligence Report
```

### Test 5: Configuration Check

**Command**:
```
Read protocol.config.yaml and tell me:
1. What's my default tier?
2. Is mask mode enabled?
3. Is research mode enabled?
```

**Expected**: Agent reads config and reports current settings

---

## Troubleshooting

### Agent Not Activating

**Problem**: Agent doesn't self-identify or follow protocol

**Solutions**:
1. Ensure protocol file is uploaded/accessible
2. Use exact syntax: `Read protocol/[agent].agent.md`
3. Check custom instructions are configured
4. Try uploading CLAUDE.md alongside agent file

**Test**: `Read protocol/CLAUDE.md` to verify file access

### Mask Mode Not Working

**Problem**: JJK theme not appearing or not disabling

**Solutions**:
1. Check `protocol.config.yaml` → `mask_mode.enabled`
2. Re-upload config file
3. Explicitly state: "Use MASK ON mode" or "Use MASK OFF mode"

**Override**: In prompt, say "Use professional mode regardless of config"

### Security Review Skipped

**Problem**: Megumi not invoked after Yuuji implementation

**Solutions**:
1. Ensure Tier 2 or 3 is used (not Tier 1)
2. Explicitly request handoff: "After implementation, invoke Megumi"
3. Check dev-notes.md for @security-review tag

**Manual Invocation**: `Read protocol/megumi.agent.md and review [feature]`

### Files Not Found

**Problem**: Agent says "Cannot read protocol/[file]"

**Solutions**:
1. **Claude.ai**: Ensure files are uploaded to Project or conversation
2. **Claude Code**: Verify files exist in workspace
3. **GitHub Copilot**: Check `.github/domain-zero/protocol/` path
4. Use absolute paths if needed

**Verify**: Ask AI to list files in protocol/ directory

### Version Mismatch

**Problem**: Agent references old version or features

**Solutions**:
1. Verify you're using the DZP-vX.Y.Z files matching your intended release
2. Check `protocol.config.yaml` → `versioning.protocol_version` matches that release (not an earlier version)
3. Re-upload all protocol files
4. Clear conversation and start fresh

---

## Advanced Configuration

### Multi-Project Setup

Managing multiple projects with Domain Zero:

**Option 1: Separate Configs Per Project**

```
project-a/
├── protocol/
│   └── (same agent files)
├── protocol.config.yaml  # Project A config
└── .protocol-state/

project-b/
├── protocol/
│   └── (same agent files)
├── protocol.config.yaml  # Project B config
└── .protocol-state/
```

**Option 2: Shared Protocol, Project-Specific State**

```
~/domain-zero-protocol/  # Shared
├── protocol/
└── protocol.config.yaml (template)

~/projects/
├── project-a/
│   ├── protocol.config.yaml  # Links to shared protocol
│   └── .protocol-state/
└── project-b/
    ├── protocol.config.yaml
    └── .protocol-state/
```

### Custom Agent Creation

Create your own agents following the `.agent.md` format:

**Template**:
```yaml
---
target: vscode
name: "Your Agent Name - Specialist Role"
description: "Brief description of agent purpose"
argument-hint: "Usage: 'implement [task]'"
model: "claude-3-5-sonnet-20241022"

tools:
  - read
  - write
  - edit

handoffs:
  - agent: yuuji
    trigger: "@implement"
    context: ["design_spec", "requirements"]
---

## TOOL ACCESS MATRIX
[Define tool permissions]

# [Rest of agent protocol]
```

Place in `protocol/custom-agent.agent.md`

### MCP Server Integration (Claude Code Only)

Configure MCP servers in `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "database": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_DIRECTORIES": "/path/to/project"
      }
    }
  }
}
```

Agents can then access MCP tools (database queries, filesystem operations, etc.)

### Research Mode Customization

Configure research output in `protocol.config.yaml`:

```yaml
research:
  output_format: "structured"  # structured, markdown, json

  storage:
    location: ".protocol-state/research/"
    keep_raw_notes: false  # gitignored by default
    summary_retention_days: 90

  quality_gates:
    min_primary_sources: 3
    require_corroboration: true  # High confidence = 2+ sources

  domain_specific:
    megumi:
      require_cve_mapping: true
      require_owasp_mapping: true
    nobara:
      require_wcag_mapping: true
      wcag_level: "AA"  # A, AA, AAA
```

### Research Directory Initialization

**IMPORTANT**: When setting up Domain Zero Protocol, you must properly initialize the research directory structure. Incorrect initialization can create malformed directories.

**Use the initialization script** (recommended):

```powershell
# Windows PowerShell
.\scripts\init-research-dirs.ps1

# With cleanup of malformed directories
.\scripts\init-research-dirs.ps1 -Clean

# Verify only (no changes)
.\scripts\init-research-dirs.ps1 -Verify
```

```bash
# Linux/macOS
./scripts/init-research-dirs.sh

# With cleanup of malformed directories
./scripts/init-research-dirs.sh --clean

# Verify only (no changes)
./scripts/init-research-dirs.sh --verify
```

**Correct directory structure**:
```
.protocol-state/
└── research/
    ├── research-index.json
    ├── README.md
    ├── yuuji/
    ├── megumi/
    ├── nobara/
    └── gojo/
```

**Common Issue**: Directories created without proper path separators (e.g., `.protocol-stateresearchgojo` instead of `.protocol-state/research/gojo/`). Use `--clean` flag to remove malformed directories.

---

## Next Steps

Once setup is complete:

1. **Read the Quick Start Guide**: `PROTOCOL_QUICKSTART.md`
2. **Review Main Protocol**: `protocol/CLAUDE.md`
3. **Try a Simple Feature**: Use Tier 2 workflow for a small feature
4. **Experiment with Agents**: Invoke each agent to understand their personalities
5. **Customize Configuration**: Adjust `protocol.config.yaml` for your needs
6. **Join the Community**: Share your experience and ask questions

---

## Support

**Documentation**:
- Main Protocol: `protocol/CLAUDE.md`
- Agent Files: `protocol/*.agent.md`
- FAQ: `FAQ.md`
- Reality Check: `REALITY_CHECK.md`

**Issues**:
- GitHub Issues: https://github.com/DewyHRite/Domain-Zero-Protocol/issues

**Repository**:
- Canonical Source: https://github.com/DewyHRite/Domain-Zero-Protocol

---

## Subagent Escape Paths (CRITICAL)

### The Problem

Subagents (spawned via the Task tool) can hang, fail silently, or output "Done" without results if they encounter:
- Hard requirements they cannot meet
- Missing information with no way to obtain it
- Blocking conditions with no alternative path

**Symptoms of Missing Escape Paths**:
- Agent says "Done" but produces no output
- Agent loops infinitely trying to meet impossible requirements
- Agent hangs without any response
- Agent provides generic/unhelpful output

### The Solution: Escape Paths

Every subagent instruction MUST include escape paths - alternative actions when the primary path is blocked.

#### Pattern 1: Soft Requirements (PREFERRED)

```markdown
# GOOD - Soft requirement with fallback
**Before starting**:
- Check if package.json exists (PREFERRED)
  - If missing: Ask user about package manager via AskUserQuestion
  - If user unavailable: Use generic npm template

# BAD - Hard requirement with no escape
**Before starting**:
- MUST have package.json (will hang if missing)
```

#### Pattern 2: Progressive Fallback

```markdown
**Finding configuration**:
1. TRY: Read protocol.config.yaml
2. IF NOT FOUND: Read .protocol-state/project-state.json
3. IF NOT FOUND: Ask user via AskUserQuestion
4. IF NO RESPONSE: Use sensible defaults and document assumptions
```

#### Pattern 3: Graceful Degradation

```markdown
**Security scan steps**:
1. Run automated SAST scan
   - IF SAST unavailable: Perform manual code review
   - IF manual review scope too large: Focus on auth/payment code only
   - IF no code to review: Return "No security-relevant code found in scope"
```

#### Pattern 4: Clear "I'm Blocked" Output

```markdown
## When You Cannot Proceed

If you are blocked and no escape path exists, output:

\`\`\`
## BLOCKED: [Task Name]

**Reason**: [Clear explanation of what's blocking you]

**What I Need**:
1. [Specific item 1]
2. [Specific item 2]

**User Can**:
- Provide [X] by saying: "[exact phrase]"
- Skip this step (consequence: [Y])
- Abort task entirely

**Partial Results** (if any):
[Whatever you accomplished before being blocked]
\`\`\`
```

### Escape Path Examples by Agent

#### Yuuji (Implementation)

```markdown
**Implementing feature**:
1. Write tests first
   - IF test framework unknown: Ask user which framework
   - IF no test framework installed: Create implementation without tests, note as technical debt

2. Implement feature
   - IF unclear requirements: Ask user via AskUserQuestion with specific options
   - IF conflicting requirements: Document conflict, use safest interpretation

3. Create backup
   - IF cannot create backup: WARN user, ask for confirmation to proceed without backup
```

#### Megumi (Security)

```markdown
**Security review**:
1. Review OWASP Top 10
   - IF code inaccessible: Ask user for file paths
   - IF code too large: Focus on security-critical paths (auth, payments, data handling)

2. Document findings
   - IF no findings: Explicitly state "No security issues found in [scope]"
   - IF partial review: Document what was reviewed and what was skipped
```

#### Gojo (Mission Control)

```markdown
**Project initialization**:
1. Read project state
   - IF no state file: Create new from template
   - IF corrupted state: Ask user to reset or provide working version

2. Brief team
   - IF agent file missing: Use default agent behavior, note missing file
```

### Implementing Escape Paths in Task Tool Prompts

When spawning subagents via the Task tool, include escape instructions:

```
Task prompt: "Implement user authentication feature"

**Requirements** (with escape paths):
1. Read protocol/yuuji.agent.md for behavior guidelines
   - If file not found: Use standard TDD approach

2. Create comprehensive tests before implementation
   - If test framework unclear: Ask user via AskUserQuestion
   - If no test directory exists: Create /tests/ directory first

3. Implement authentication logic
   - If auth method unspecified: Default to JWT, note assumption
   - If database unclear: Use in-memory for prototype

4. Document in dev-notes.md
   - If dev-notes.md not found: Create it with template

**IF BLOCKED**: Output partial results with BLOCKED template above.
**NEVER**: Hang silently or output "Done" without results.
```

---

## Using Skills for Token Efficiency

> **Complete Guide:** See **[TOKEN_EFFICIENCY_RECOMMENDATIONS.md](../TOKEN_EFFICIENCY_RECOMMENDATIONS.md)** for comprehensive token efficiency guidelines including modular architecture, delegation patterns, and day-to-day usage recommendations.

### Why Skills Matter

Skills save tokens by:
- Avoiding repeated instructions across conversations
- Providing pre-structured workflows for common operations
- Reducing context window usage
- Ensuring consistency across sessions

### Skill Types

| Type | Purpose | Example |
|------|---------|---------|
| **Example Skills** | Anthropic-provided common patterns | webapp-testing, mcp-server |
| **Document Skills** | Process document types | docx, xlsx, pdf |
| **Custom Skills** | Domain-specific workflows | owasp-checklist, tdd-checklist |

### Skill Invocation

```
skill: "skill-name"

[Your context/task]
```

### Recommended Skills by Agent

#### Yuuji (Implementation)
```yaml
skills:
  - webapp-testing      # Playwright-based UI testing
  - mcp-server          # MCP integration guidance
  - tdd-checklist       # Test-driven development workflow
  - async-patterns      # Async/await best practices
  - testing-fixtures    # Test fixture management
```

#### Megumi (Security)
```yaml
skills:
  - owasp-checklist     # OWASP Top 10 review workflow
  - threat-modeling     # Structured threat analysis
  - jwt-audit           # JWT security review
  - secrets-review      # Secrets/credentials detection
  - dependency-audit    # SCA/supply chain review
```

#### Nobara (UX/Creative)
```yaml
skills:
  - a11y-review         # Accessibility audit
  - ux-writing          # UX copy guidelines
  - onboarding-flows    # User onboarding patterns
  - design-system-glossary # Design system reference
```

#### Gojo (Mission Control)
```yaml
skills:
  - skill-builder       # Create new skills rapidly
  - protocol-verify     # Protocol compliance check
  - release-briefing    # Release preparation workflow
  - version-audit       # Version consistency check
```

### Creating Custom Skills

Use the skill-builder skill:

```
skill: "skill-builder"

Create a skill for: [your description]
```

The skill-builder will:
1. Ask clarifying questions via AskUserQuestion
2. Generate properly formatted skill template
3. Include escape paths for all requirements
4. Register in AGENT_SKILLS_MAP.yaml

See `protocol/skills/skill-builder.md` for the complete skill-builder specification.

---

## AskUserQuestion Integration (CRITICAL)

### Why AskUserQuestion is Essential

The `AskUserQuestion` tool provides:
- **Nice UI**: Multiple-choice options instead of free-form text
- **Reduced Ambiguity**: Users select from defined choices
- **Better UX**: Clear decision points in the workflow
- **Token Efficiency**: Shorter, more focused responses

### When to Use AskUserQuestion

**ALWAYS use AskUserQuestion for**:
- Tier selection (rapid/standard/critical)
- Approach decisions (multiple valid paths)
- Missing information (what framework? what database?)
- User preferences (strict mode? verbose output?)
- Confirmation before destructive actions
- Clarifying ambiguous requirements

### AskUserQuestion Patterns

#### Pattern 1: Tier Selection
```json
{
  "questions": [
    {
      "question": "Which workflow tier should I use for this feature?",
      "header": "Tier",
      "options": [
        {"label": "Tier 1 - Rapid", "description": "Prototype, no tests, fast iteration"},
        {"label": "Tier 2 - Standard", "description": "Production code with TDD + security review"},
        {"label": "Tier 3 - Critical", "description": "Auth/payments/sensitive data with enhanced review"}
      ],
      "multiSelect": false
    }
  ]
}
```

#### Pattern 2: Approach Decision
```json
{
  "questions": [
    {
      "question": "How should I implement authentication?",
      "header": "Auth Method",
      "options": [
        {"label": "JWT", "description": "Stateless tokens, best for APIs"},
        {"label": "Session", "description": "Server-side sessions, best for web apps"},
        {"label": "OAuth 2.0", "description": "Third-party auth, best for social login"}
      ],
      "multiSelect": false
    }
  ]
}
```

#### Pattern 3: Missing Information
```json
{
  "questions": [
    {
      "question": "Which testing framework does your project use?",
      "header": "Test Framework",
      "options": [
        {"label": "Jest", "description": "JavaScript/TypeScript testing"},
        {"label": "Pytest", "description": "Python testing"},
        {"label": "JUnit", "description": "Java testing"},
        {"label": "None yet", "description": "Help me set one up"}
      ],
      "multiSelect": false
    }
  ]
}
```

#### Pattern 4: Multi-Select (Features/Options)
```json
{
  "questions": [
    {
      "question": "Which security checks should I include in the review?",
      "header": "Checks",
      "options": [
        {"label": "OWASP Top 10", "description": "Core web vulnerabilities"},
        {"label": "Dependency Audit", "description": "Third-party package vulnerabilities"},
        {"label": "Secrets Scan", "description": "Check for hardcoded credentials"},
        {"label": "Performance", "description": "N+1 queries, memory leaks"}
      ],
      "multiSelect": true
    }
  ]
}
```

### Agent-Specific AskUserQuestion Guidance

#### Yuuji Should Ask About:
- Test framework preference
- Tier selection if not specified
- Database/ORM choice
- API design approach (REST vs GraphQL)
- Error handling strategy

#### Megumi Should Ask About:
- Review scope (full audit vs focused)
- Risk tolerance (block on P2? P3?)
- Compliance requirements (PCI, HIPAA, SOC2)
- External scan tool availability

#### Nobara Should Ask About:
- Target user persona
- Accessibility level (WCAG A/AA/AAA)
- Design system constraints
- Brand guidelines availability

#### Gojo Should Ask About:
- Project initialization details
- Tier workflow preferences
- Team configuration
- Monitoring preferences

### Best Practices

1. **Max 4 options per question**: More than 4 is overwhelming
2. **Clear, concise labels**: 1-5 words per option label
3. **Helpful descriptions**: Explain consequences of each choice
4. **Always include "Other"**: Users can always provide custom input
5. **Multi-select sparingly**: Only when choices aren't mutually exclusive
6. **Ask early**: Don't wait until you're stuck to ask

---

## Add-to-Memory Prompts (Copy-Paste Ready)

### For Claude.ai / Claude API

Copy and paste this prompt to save Domain Zero Protocol to Claude's memory:

```
Add to memory: Domain Zero Protocol

I use the Domain Zero Protocol for AI-assisted development. This is a nine-agent system:

**Core Four:**
- YUUJI (Implementation Specialist): Test-first development, feature implementation
- MEGUMI (Security Analyst): OWASP Top 10 security reviews
- NOBARA (Creative Strategy & UX): User experience design, product vision
- GOJO (Mission Control): Project lifecycle, protocol guardian

**Extended Four:**
- TODO (Database & Backend): Schema design, migrations, query optimization
- MAKI (Performance): Profiling, bundle analysis, zero-overhead optimization
- PANDA (Build & Integration): CI/CD, GitHub Actions, Docker
- INUMAKI (API & Communication): REST, GraphQL, WebSocket design

The protocol files are located in my project at:
- CLAUDE.md (main protocol, repository root, DZP-vX.Y.Z; `protocol/CLAUDE.md` is a compatibility pointer/stub since v9.11.0 that redirects here)
- protocol/yuuji.agent.md (implementation agent)
- protocol/megumi.agent.md (security agent)
- protocol/nobara.agent.md (creative strategy agent)
- protocol/gojo.agent.md (mission control)

The protocol uses a three-tier workflow system:
- Tier 1 (Rapid): Fast prototyping, no tests
- Tier 2 (Standard): Production features with TDD + security review [DEFAULT]
- Tier 3 (Critical): Enhanced testing + multi-model security review for auth/payments/sensitive data

Key features:
- Use skills for common operations to save tokens (skill: "skill-name")
- Use AskUserQuestion tool frequently for clarification and nice UI
- All agents have escape paths - they will ask for help rather than hang

When I say 'Read protocol/[AGENT].agent.md', always read the file first to follow the protocol.
The canonical source is: https://github.com/DewyHRite/Domain-Zero-Protocol
```

### For ChatGPT (Custom Instructions)

Add to "What would you like ChatGPT to know about you?":

```
I use the Domain Zero Protocol (DZP-vX.Y.Z) for development projects. The main protocol file is `CLAUDE.md` at the repository root (`protocol/CLAUDE.md` is a compatibility pointer/stub since v9.11.0 that redirects there). This is a nine-agent AI development framework with specialized roles:

**Core Four:**
- YUUJI: Implementation with test-first development
- MEGUMI: Security review (OWASP Top 10)
- NOBARA: Creative strategy and user experience design
- GOJO: Mission control and protocol enforcement

**Extended Four:**
- TODO: Database & backend specialist
- MAKI: Performance optimization specialist
- PANDA: Build & integration specialist
- INUMAKI: API & communication specialist

When working on my projects, refer to protocol files at CLAUDE.md (repository root; `protocol/CLAUDE.md` is a compatibility pointer/stub since v9.11.0), protocol/yuuji.agent.md, protocol/megumi.agent.md, protocol/nobara.agent.md, protocol/gojo.agent.md, protocol/todo.agent.md, protocol/maki.agent.md, protocol/panda.agent.md, and protocol/inumaki.agent.md. The protocol follows a three-tier workflow system (Rapid/Standard/Critical) and aims for zero-defect code.

Important:
- Use skills for common operations (saves tokens)
- Ask clarifying questions frequently (better than guessing)
- All instructions should have escape paths (what to do if blocked)

Canonical source: https://github.com/DewyHRite/Domain-Zero-Protocol
```

### For Claude Code (CLAUDE.md / Custom Instructions)

Add to your global or project-level custom instructions:

```
- Add to memory: Domain Zero Protocol

I use the Domain Zero Protocol for AI-assisted development. This is a nine-agent system:

**Core Four:**
- YUUJI (Implementation Specialist): Test-first development, feature implementation
- MEGUMI (Security Analyst): OWASP Top 10 security reviews
- NOBARA (Creative Strategy & UX): User experience design, product vision
- GOJO (Mission Control): Project lifecycle, protocol guardian

**Extended Four:**
- TODO (Database & Backend): Schema design, migrations, query optimization
- MAKI (Performance): Profiling, bundle analysis, zero-overhead optimization
- PANDA (Build & Integration): CI/CD, GitHub Actions, Docker
- INUMAKI (API & Communication): REST, GraphQL, WebSocket design

The protocol files are located in my project at:
- CLAUDE.md (main protocol, repository root, DZP-vX.Y.Z; `protocol/CLAUDE.md` is a compatibility pointer/stub since v9.11.0 that redirects here)
- protocol/yuuji.agent.md (implementation agent)
- protocol/megumi.agent.md (security agent)
- protocol/nobara.agent.md (creative strategy agent)
- protocol/gojo.agent.md (mission control)

The protocol uses a three-tier workflow system:
- Tier 1 (Rapid): Fast prototyping, no tests
- Tier 2 (Standard): Production features with TDD + security review [DEFAULT]
- Tier 3 (Critical): Enhanced testing + multi-model security review for auth/payments/sensitive data

When I say 'Read protocol/[AGENT].agent.md', always read the file first to follow the protocol.
The canonical source is: https://github.com/DewyHRite/Domain-Zero-Protocol
```

---

## Context Compaction Recovery (DZP-v9.3.0+)

### The Problem

After context compaction in Claude Code, agents lose critical DZP protocol context including:
- Agent roles and restrictions
- Implementation routing (5 agents route through Yuuji)
- Domain record access (Gojo/Sukuna only)
- Tier validation workflows
- Parallel workflow patterns

Users previously had to manually re-explain these rules repeatedly.

### The Solution: /dzp-roe

The **DZP Rules of Engagement (ROE)** slash command provides single-command recovery:

**Invocation**:
```bash
/dzp-roe
```

Or as a skill:
```bash
skill: "dzp-roe"

Context: Just recovered from compaction, need DZP rules refresher
```

**What It Does**:
1. Outputs complete DZP protocol summary (9 agents, restrictions, patterns)
2. Updates state tracking (project-state.json, domain.record.md, dev-notes.md)
3. Runs protocol validation
4. Prompts agent to continue previous work with proper DZP workflow

**When to Use**:
- Immediately after context compaction
- When agents forget implementation routing rules
- When agents forget domain record access restrictions
- When agents need reminder of tier validation requirements

**File**: `protocol/skills/dzp-roe.md` (510 lines, 9-step workflow)
**Slash Command**: `.claude/commands/dzp-roe.md`
**Available To**: ALL 9 agents (gojo, yuuji, megumi, nobara, todo, maki, panda, inumaki, sukuna)

---

## Changelog

### DZP-v9.3.0 (2025-12-28)

#### New Features
1. **Session Management Skill** (`/session`) - Unified session lifecycle interface
   - Commands: start, status, update, break, continue, end
   - Checkpoint file syncing (dev-notes, project-state, domain.record, security-review, session-state)
   - Gojo-owned skill with domain.record.md write access
   - File: `protocol/skills/session.md`

2. **TS Troubleshooting Tier System** (`/ts`) - 5-tier hybrid bug resolution
   - Tier 1-4: Progressive escalation (Yuuji + Megumi, then + support agents)
   - Tier 5 (Codered): All 9 agents, mandatory plan mode
   - Hybrid escalation: severity-based initial tier + auto-escalation after failed attempts
   - Context-dependent support agent selection (Todo/Panda/Maki/Inumaki/Nobara)
   - Commands: tier1, tier2, tier3, tier4, codered, status, history, escalate, complete
   - File: `protocol/skills/ts.md`

3. **DZP ROE v2.0.0** - Refactored for brevity (46.9% smaller) with parallel enforcement
   - 510 lines → 307 lines (46.9% reduction)
   - Added parallel workflow validation checklist
   - Added MUST/MUST NOT imperative language
   - Added anti-pattern examples
   - Changed ownership from ALL agents to Gojo only
   - File: `protocol/skills/dzp-roe.md`

#### Installation Instructions

**Fresh Install**:
Skills auto-installed via protocol/ directory. Verify with:
```bash
ls protocol/skills/
# Should show: session.md, ts.md, dzp-roe.md, SKILL_REGISTRY.md
```

**In-Place Upgrade**:
1. **Backup current state**:
   ```bash
   cp .protocol-state/project-state.json .protocol-state/backups/project-state-$(date +%Y%m%d).json
   ```

2. **Update protocol files** (pull latest from repo or copy from release):
   ```bash
   cp -r DZP-vX.Y.Z/protocol/skills/* protocol/skills/
   ```

3. **Update project-state.json** (manual or via script):
   ```json
   {
     "protocol_version": "9.3.0",
     "troubleshooting_session": {
       "session_id": null,
       "active": false,
       "current_tier": 0,
       "attempts_count": 0,
       "bug_description": "",
       "affected_files": [],
       "selected_support_agents": [],
       "escalation_history": [],
       "plan_mode_active": false,
       "started_at": null
     },
     "troubleshooting_statistics": {
       "total_sessions": 0,
       "sessions_by_tier": {
         "tier1": 0,
         "tier2": 0,
         "tier3": 0,
         "tier4": 0,
         "codered": 0
       },
       "average_resolution_minutes": {
         "tier1": 0,
         "tier2": 0,
         "tier3": 0,
         "tier4": 0,
         "codered": 0
       },
       "total_escalations": 0,
       "auto_escalations": 0,
       "manual_escalations": 0
     }
   }
   ```

4. **Test skills**:
   ```bash
   /session start
   /ts tier1
   /dzp-roe
   ```

#### Breaking Changes
None. All changes are additive. DZP ROE v2.0.0 is breaking for skill structure but non-breaking for usage.

#### Deprecations
None.

---

### DZP-v9.3.0 (2025-12-25)

#### New Features
- DZP Rules of Engagement (dzp-roe) skill for post-compaction recovery
- Context restoration after Claude Code compaction
- State tracking for compaction recovery

---

## Quick Reference Card

### Agent Invocation

| Agent | Command | Purpose |
|-------|---------|---------|
| Yuuji | `Read protocol/yuuji.agent.md and [task]` | Implementation |
| Megumi | `Read protocol/megumi.agent.md and [task]` | Security review |
| Nobara | `Read protocol/nobara.agent.md and [task]` | UX/Creative |
| Gojo | `Read protocol/gojo.agent.md` | Mission Control |

### Slash Commands (DZP-v9.3.0+)

| Command | Purpose | Availability |
|---------|---------|--------------|
| `/dzp-roe` | Post-compaction DZP rules recovery | ALL agents |
| `/gojo` | Mission Control activation | gojo |
| `/yuuji` | Implementation specialist activation | yuuji |
| `/sukuna` | System update (Gojo-invoked only) | sukuna |

### Tier Flags

| Tier | Flag | Use Case |
|------|------|----------|
| Rapid | `--tier rapid` | Prototypes, experiments |
| Standard | (default) | Production features |
| Critical | `--tier critical` | Auth, payments, sensitive data |

### Skill Invocation

```
skill: "skill-name"
[context]
```

### Key Principles

1. **Always ask rather than guess** - Use AskUserQuestion
2. **Always have an escape path** - Never hang or fail silently
3. **Use skills for common operations** - Save tokens
4. **Test-first for Tier 2/3** - TDD is non-negotiable
5. **User safety first** - Above all other objectives

---

**Ready to start?** Choose your platform, follow the setup steps, and invoke your first agent!

🌀 **Domain Zero: Infinite Collaboration, Zero Defects**
