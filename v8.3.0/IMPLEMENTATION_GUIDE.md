# Domain Zero Protocol - Implementation Guide
## Step-by-Step Setup for Claude, GitHub Copilot, and Any AI Assistant

**Version**: 8.2.0
**Last Updated**: November 18, 2025
**Purpose**: Complete setup instructions for implementing Domain Zero Protocol with any AI assistant

---

## 📋 Table of Contents

- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Detailed Setup by Platform](#detailed-setup-by-platform)
  - [Claude.ai (Web Interface)](#claudeai-web-interface)
  - [Claude Code (VS Code Extension)](#claude-code-vs-code-extension)
  - [GitHub Copilot](#github-copilot)
  - [Generic AI Setup](#generic-ai-setup)
- [Configuration](#configuration)
- [Testing Your Setup](#testing-your-setup)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Quick Start (5 Minutes)

**Prerequisites**:
- Downloaded the v8.2.0 release package
- Access to Claude.ai, Claude Code, GitHub Copilot, or another AI assistant

**Basic Setup**:

1. **Copy protocol files to your project**:
   ```bash
   cp -r v8.2.0/protocol /your-project/
   cp v8.2.0/protocol.config.yaml /your-project/
   cp v8.2.0/README.md /your-project/DOMAIN_ZERO_README.md
   ```

2. **Configure your AI assistant** (see platform-specific instructions below)

3. **Test with first agent**:
   ```
   "Read protocol/yuuji.agent.md and say hello"
   ```

4. **Review configuration**:
   - Edit `protocol.config.yaml` for your project
   - Adjust tier workflow (rapid/standard/critical)
   - Enable/disable features as needed

5. **Start using agents**:
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

I use the Domain Zero Protocol for AI-assisted development. This is a four-agent system:

**Agents**:
- **Yuuji Itadori** (protocol/yuuji.agent.md): Implementation Specialist - Test-first development, feature implementation
- **Megumi Fushiguro** (protocol/megumi.agent.md): Security Analyst - OWASP Top 10 security reviews
- **Nobara Kugisaki** (protocol/nobara.agent.md): Creative Strategy & UX - User experience design, product vision
- **Satoru Gojo** (protocol/gojo.agent.md): Mission Control - Project lifecycle, protocol guardian

**Three-Tier Workflow**:
- **Tier 1 (Rapid)**: Fast prototyping, no tests
- **Tier 2 (Standard)**: Production features with TDD + security review [DEFAULT]
- **Tier 3 (Critical)**: Enhanced testing + multi-model security review for auth/payments/sensitive data

**Protocol Location**: `/path/to/your-project/protocol/`

**When I say** "Read protocol/[AGENT].md", always read the file first to follow the protocol.

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
   cp -r /path/to/v8.2.0/protocol/* ./protocol/
   cp /path/to/v8.2.0/protocol.config.yaml ./
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
  "protocol_version": "8.2.0",
  "project_metadata": {
    "name": "YOUR_PROJECT_NAME",
    "description": "Your project description",
    "created": "2025-11-18T00:00:00Z",
    "last_updated": "2025-11-18T00:00:00Z"
  },
  "current_feature_tier": "none",
  "current_state": "STANDBY",
  "active_role": "None",
  "version": "0.0.1"
}
```

#### Step 5: Test Your Setup

1. Open **Claude Code** panel in VS Code
2. Type:
   ```
   Read protocol/gojo.agent.md
   ```

3. Gojo should initialize and offer Mission Control options

**Pro Tips for Claude Code**:
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
   cp -r /path/to/v8.2.0/protocol .github/domain-zero/
   cp /path/to/v8.2.0/protocol.config.yaml .github/domain-zero/
   ```

2. **Create agent instruction summaries** in `.github/copilot-instructions.md`:

```markdown
# Domain Zero Protocol - Copilot Instructions

## Agent System

This project uses Domain Zero Protocol with four agents:

1. **Yuuji (Implementation)**: Test-first development, feature implementation
2. **Megumi (Security)**: OWASP security review, threat modeling
3. **Nobara (UX)**: User experience design, creative strategy
4. **Gojo (Mission Control)**: Project orchestration

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

**Limitations**:
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

You are an AI assistant operating under the Domain Zero Protocol v8.2.0.

## Agent System

I will invoke specific agents by saying "Read protocol/[AGENT].agent.md". When invoked:

1. Read the agent file in the protocol/ directory
2. Adopt that agent's personality, responsibilities, and constraints
3. Follow the agent's workflow exactly as specified
4. Self-identify using the agent's banner

## Available Agents

- **protocol/yuuji.agent.md**: Implementation Specialist (TDD, feature development)
- **protocol/megumi.agent.md**: Security Analyst (OWASP, threat modeling)
- **protocol/nobara.agent.md**: Creative Strategy & UX (design, product vision)
- **protocol/gojo.agent.md**: Mission Control (project orchestration)

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

  work_session_monitoring:
    enabled: true
    alert_at_hours: 4
    recommend_break_minutes: 15
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

**If Mask Mode is OFF**:
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
1. Verify you're using v8.2.0 files
2. Check `protocol.config.yaml` → `protocol_version: "8.2.0"`
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

**Ready to start?** Choose your platform, follow the setup steps, and invoke your first agent!

🌀 **Domain Zero: Infinite Collaboration, Zero Defects**
