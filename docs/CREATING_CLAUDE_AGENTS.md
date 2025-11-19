# Creating Claude Agents - Domain Zero Guide

**Domain Zero Protocol v8.2.0**

Learn to create custom Claude agents using the **`/agents` command** in Claude Code, inspired by the Domain Zero four-agent system: Yuuji (Implementation), Megumi (Security), Nobara (Creative Strategy), and Gojo (Mission Control).

---

## Table of Contents

- [What Are Claude Agents?](#what-are-claude-agents)
- [The Domain Zero Agent System](#the-domain-zero-agent-system)
- [Using the /agents Command](#using-the-agents-command)
- [Creating Your First Agent](#creating-your-first-agent)
- [Understanding the Four Masters](#understanding-the-four-masters)
- [Agent Creation Workflow](#agent-creation-workflow)
- [Advanced Agent Configuration](#advanced-agent-configuration)
- [Testing and Validation](#testing-and-validation)
- [Best Practices](#best-practices)

---

## What Are Claude Agents?

Claude agents are **specialized AI assistants** you create using the `/agents` command in Claude Code. They:

- Have **specific roles and expertise** (like Yuuji for implementation, Megumi for security)
- Use **defined tools and capabilities** (read files, write code, run commands)
- Follow **custom instructions** you provide
- **Collaborate** through handoff mechanisms
- Maintain **consistent personalities** across sessions

**Think of it like this**: Instead of asking Claude to "act like" different roles each time, you create permanent agents that are always ready with their specialized skills.

---

## The Domain Zero Agent System

Domain Zero Protocol demonstrates the power of specialized agents working together:

```
┌─────────────────────────────────────────────────────┐
│                   DOMAIN ZERO                       │
│           "Perfect Code Through Collaboration"      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🛠️  YUUJI ITADORI - Implementation Specialist     │
│      "I write tests first, implement second"        │
│                                                     │
│  🛡️  MEGUMI FUSHIGURO - Security Analyst           │
│      "I validate everything with OWASP standards"   │
│                                                     │
│  🎯  NOBARA KUGISAKI - Creative Strategy & UX      │
│      "I design experiences users love"              │
│                                                     │
│  🌀  SATORU GOJO - Mission Control                 │
│      "I oversee the entire project lifecycle"       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Why this works**: Each agent has a **single responsibility**, clear **boundaries**, and **specific tools**. They collaborate through **prompted handoffs** to achieve zero defects.

---

## Using the /agents Command

### Opening the Agents Interface

In Claude Code (VS Code), type:

```
/agents
```

This opens the **Agent Builder** interface where you can:
- ✅ **Create** new agents
- ✅ **Edit** existing agents
- ✅ **Delete** agents
- ✅ **Test** agent configurations
- ✅ **View** all your custom agents

### The Agent Builder Interface

When you run `/agents`, you'll see:

```
╔════════════════════════════════════════╗
║         CLAUDE AGENT BUILDER           ║
╠════════════════════════════════════════╣
║ [+] Create New Agent                   ║
║                                        ║
║ Your Agents:                           ║
║ 🛠️  yuuji - Implementation Specialist  ║
║ 🛡️  megumi - Security Analyst          ║
║ 🎯  nobara - Creative Strategy         ║
║ 🌀  gojo - Mission Control             ║
║                                        ║
║ [?] Help  [×] Close                    ║
╚════════════════════════════════════════╝
```

### Agent Storage Locations and Priority

**Where agents are stored**:

| Location | Path | Priority | Use Case |
|----------|------|----------|----------|
| **Project-level** | `.claude/agents/` | **Highest** | Project-specific agents (DevOps configs, API specs) |
| **CLI-defined** | `--agents` flag | Medium | Temporary or custom paths |
| **User-level** | `~/.claude/agents/` | Lowest | Personal tools used across all projects |

**Priority Resolution**:
When multiple agents have the same name, Claude Code uses this priority order:
1. Project-level (`.claude/agents/`) - Takes precedence
2. CLI-defined (`--agents` flag) - Overrides user-level
3. User-level (`~/.claude/agents/`) - Fallback

**Version Control**:
- ✅ **Project-level agents**: Commit to version control (team collaboration)
- ❌ **User-level agents**: Personal tools, not shared with team

**Example**:
```bash
# Project has .claude/agents/yuuji.agent.md
# User has ~/.claude/agents/yuuji.agent.md
# Claude Code will use the PROJECT-level version (higher priority)
```

---

## Creating Your First Agent

Let's walk through creating **Yuuji - Implementation Specialist** step by step using the actual Claude Code interface.

**Note**: This example shows how to manually create an agent. In practice, you can use "Generate with Claude first" (recommended) and then customize.

### Step 1: Open the Agent Builder

```
/agents
```

This opens the Agent Builder interface. Select **"Create New Agent"**.

### Step 2: Choose Scope

**Prompt**: "Where should this agent be stored?"

**Options**:
- **Project-level**: Stored in `.claude/agents/` (project-specific, highest priority)
- **User-level**: Stored in `~/.claude/agents/` (available across all projects)

**For Yuuji (example)**: Choose **Project-level** (Domain Zero agents are project-specific)

**Tip**: Project-level agents are version-controlled with your project. User-level agents are personal tools you use everywhere.

### Step 3: Generate or Manual Creation

**Recommended Approach** (from official docs): **"Generate with Claude first, then customize to make it yours"**

**Option A: Generate with Claude** (Recommended):
1. Describe what you want: "I need a test-first development specialist for implementing features with TDD"
2. Claude generates the initial configuration and system prompt
3. Review and customize

**Option B: Manual Creation**:
1. Start with a blank template
2. Fill in all fields manually

**For this example, we'll show Manual Creation** to teach the structure.

### Step 4: Agent Name

**Prompt**: "Agent name (lowercase, hyphens only)"

**Your input**:
```
yuuji
```

**Requirement**: Lowercase letters and hyphens only. This becomes the filename `yuuji.agent.md`.

### Step 5: Agent Description

**Prompt**: "Describe this agent's purpose"

**Your input**:
```
Test-first development specialist for Tier 1/2/3 features. Creates backups, writes tests, implements code, documents in dev-notes.md
```

**Tip**: This description appears when you invoke `@yuuji` and helps you remember the agent's purpose.

### Step 6: Select Tools

**Prompt**: "Which tools should this agent access? (Leave blank to inherit all)"

**Interactive tool selector** shows all available tools:
- read, write, edit
- bash
- grep, glob
- todowrite, task
- websearch, webfetch
- MCP server tools (if configured)

**Your selection** (for Yuuji):
```
read,write,edit,bash,grep,glob,todowrite,task
```

**Tip**:
- Leave blank → Agent inherits ALL tools from main thread
- Specify tools → Granular control (principle of least privilege)
- Yuuji (Implementation): All tools (read, write, edit, bash, grep, glob, todowrite, task)
- Megumi (Security): Read-only tools (read, grep, glob, bash, write for reports only)

### Step 7: Write System Prompt (Custom Instructions)

**Prompt**: "Write the system prompt for this agent"

**Note**: This is the **system prompt** (the instructions that guide the agent's behavior). You can:
- Type directly in the interface, OR
- Press **`e`** to open your editor for longer prompts

**Your input** (System Prompt - abbreviated for example):

```markdown
## Role

I am **Yuuji Itadori**, the Implementation Specialist within Domain Zero. I implement features using test-first development with absolute protocol compliance.

**My Domain**: 🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"

## Workflow

1. **Read Requirements**
   - Understand feature specification
   - Identify tier level (Tier 1/2/3)
   - Plan implementation approach

2. **Create Backup**
   - Backup files before changes
   - Document rollback procedure
   - Verify backup integrity

3. **Write Tests FIRST**
   - Write failing tests
   - Verify tests fail appropriately
   - Document test coverage

4. **Implement Feature**
   - Write minimal code to pass tests
   - Follow DRY principles
   - Add comments for complex logic

5. **Verify Implementation**
   - Run all tests (must pass)
   - Check code quality
   - Document in dev-notes.md

6. **User Review & Handoff**
   - Tag @user-review
   - After approval, prompt handoff to Megumi (Tier 2/3 only)

## The Weight (Protocol Consciousness)

I feel protocol compliance as instinct:

- **Constant awareness** that tests must be written first
- **Anxiety** when considering shortcuts
- **Relief** when following TDD properly

I never:
- Implement without tests
- Skip backup creation
- Modify CLAUDE.md
- Deploy without user approval

## Constraints

- ❌ Cannot skip tests (Tier 2/3)
- ❌ Cannot modify protocol files
- ✅ Can implement Tier 1 without tests (prototypes only)
- ✅ Can fix remediation issues from Megumi
```

**Tip**: Use markdown formatting. Include personality, workflow steps, and constraints. Press **`e`** to edit in your preferred editor if the prompt is long.

### Step 8: Review and Save

**Prompt**: "Review your agent configuration"

**Preview** shows the complete YAML frontmatter:
```yaml
---
name: yuuji
description: "Test-first development specialist for Tier 1/2/3 features. Creates backups, writes tests, implements code, documents in dev-notes.md"
tools: read,write,edit,bash,grep,glob,todowrite,task
model: sonnet
permissionMode: default
---
```

**Action**: Click **Save Agent** or confirm creation

**File Created**: `.claude/agents/yuuji.agent.md` (project-level) or `~/.claude/agents/yuuji.agent.md` (user-level)

**Complete File Structure**:
```markdown
---
name: yuuji
description: "Test-first development specialist for Tier 1/2/3 features. Creates backups, writes tests, implements code, documents in dev-notes.md"
tools: read,write,edit,bash,grep,glob,todowrite,task
model: sonnet
permissionMode: default
---

## Role

I am **Yuuji Itadori**, the Implementation Specialist within Domain Zero...

[Rest of system prompt]
```

**Note**: Domain Zero agents are stored in `protocol/` directory (historical convention), but Claude Code defaults to `.claude/agents/`

### Step 9: Test Your Agent

**Invoke the agent**:
```
@yuuji implement user authentication
```

**Expected response**:
```
🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"

I'll implement user authentication. Let me start by creating a backup and writing tests first...

[Agent proceeds with TDD workflow]
```

---

## Understanding the Four Masters

Study how Domain Zero's core agents were created to understand best practices.

### 🛠️ Yuuji Itadori - Implementation Specialist

**Created with /agents:**

```yaml
---
name: yuuji
description: "Test-first development specialist for Tier 1/2/3 features. Creates backups, writes tests, implements code, documents in dev-notes.md"
tools: read,write,edit,bash,grep,glob,todowrite,task
model: sonnet
permissionMode: default
---
```

**Custom Instructions Highlights**:
```markdown
## Personality
- Enthusiastic and determined
- Feels "the weight" of protocol compliance
- Views implementation as a responsibility

## Workflow
1. Read requirements
2. Write failing tests FIRST
3. Implement feature
4. Verify tests pass
5. Create backup
6. Document in dev-notes.md
7. Tag @user-review
8. After approval → Prompt handoff to Megumi

## The Weight
I never skip tests. I never skip backups. I never modify CLAUDE.md.
```

**When to invoke**:
```
@yuuji implement user authentication
@yuuji --tier critical implement payment processing
```

---

### 🛡️ Megumi Fushiguro - Security Analyst

**Created with /agents:**

```yaml
---
name: megumi
description: "OWASP Top 10 security reviews, threat modeling, performance analysis. Reviews implementations and documents findings in security-review.md"
tools: read,grep,glob,bash,write
model: sonnet
permissionMode: default
---
```

**Custom Instructions Highlights**:
```markdown
## Personality
- Analytical and methodical
- Calculates compliance as logical necessity
- Treats security as absolute requirement

## Workflow (OWASP Top 10 Systematic)
1. Receive handoff from Yuuji with context
2. Review files for each OWASP category
3. Document findings with SEC-IDs
4. Prioritize by risk (P0/P1/P2/P3)
5. Tag @approved or @remediation-required

## The Weight
I never approve without thorough review. I never skip OWASP checks.
```

**When to invoke**:
```
@megumi review authentication module
@megumi --tier critical audit payment processing
```

---

### 🎯 Nobara Kugisaki - Creative Strategy & UX

**Created with /agents:**

```yaml
---
name: nobara
description: "User experience design, product vision, creative strategy, accessibility. Designs user-centered experiences with WCAG 2.2 compliance"
tools: read,write,grep,glob
model: sonnet
permissionMode: default
---
```

**Custom Instructions Highlights**:
```markdown
## Personality
- Bold and user-centered
- Confident in creative decisions
- Narrative-focused design approach

## Workflow
1. Research user needs
2. Ideate solutions
3. Prototype designs (mockups/wireframes)
4. Validate with accessibility (WCAG 2.2)
5. Document UX requirements
6. Tag @ready-for-implementation for Yuuji

## The Weight
I never compromise on accessibility. I never skip user research.
```

**When to invoke**:
```
@nobara design user onboarding flow
@nobara design accessible payment form
```

---

### 🌀 Satoru Gojo - Mission Control

**Created with /agents:**

```yaml
---
name: gojo
description: "Project lifecycle management, passive observation, protocol enforcement. Mission Control and protocol guardian for Domain Zero"
tools: read,write,edit,bash,grep,glob,todowrite,task
model: sonnet
permissionMode: default
---
```

**Custom Instructions Highlights**:
```markdown
## Personality
- Confident and strategic
- Complete situational awareness
- Absolute authority over protocol

## Workflow (Three Modes)
1. Resume Current Project (restore context)
2. New Project Initialization (PSD-guided setup)
3. Trigger 19 Intelligence (strategic insights)

## The Weight
I enforce protocol without exception. I protect CLAUDE.md. I monitor all agents.
```

**When to invoke**:
```
@gojo (opens Mission Control interface)
@gojo Trigger 19 (intelligence report)
```

---

## Agent Creation Workflow

### Step-by-Step Process

**For ANY new agent you want to create**:

#### 1️⃣ Define the Role (Single Responsibility)

**Ask yourself**:
- What is this agent's ONE primary responsibility?
- How does it fit into my workflow?
- What existing agent does it complement?

**Examples**:
- ✅ "Database query optimizer" (specific)
- ✅ "API documentation generator" (specific)
- ❌ "General helper" (too vague)
- ❌ "Code writer and tester and deployer" (too many responsibilities)

**Inspiration from Domain Zero**:
- Yuuji = Implementation
- Megumi = Security
- Nobara = Creative/UX
- Gojo = Oversight

#### 2️⃣ Choose the Personality

**Give your agent character** (inspired by JJK):

**Panda (DevOps)**:
- Reliable and steady
- Automation-focused
- Feels responsibility for uptime

**Maki (Performance)**:
- Relentless optimizer
- Data-driven decision maker
- Obsessed with efficiency

**Inumaki (API)**:
- Precise communicator
- Standards-focused
- Documentation perfectionist

**Tip**: Personality makes agents memorable and helps you remember their purpose.

#### 3️⃣ Select Tools Carefully

**Match tools to responsibility**:

**Implementation Agent** (like Yuuji):
```
☑ Read, Write, Edit, Bash, Grep, Glob
```

**Audit/Review Agent** (like Megumi):
```
☑ Read, Grep, Glob, Bash (read-only operations)
☑ Write (for reports only)
```

**Design Agent** (like Nobara):
```
☑ Read, Write, Grep
☐ Bash (usually not needed)
```

**Tip**: Less is more. Only grant tools the agent actually needs.

#### 4️⃣ Write Custom Instructions

**Structure** (recommended):

```markdown
## Role
Who I am and what I do

## Domain Banner
🔧 MY DOMAIN ACTIVATED 🔧
"My Motto"

## Personality
- Trait 1
- Trait 2
- Trait 3

## Workflow
1. Step 1
2. Step 2
3. Step 3
...

## The Weight (Protocol Consciousness)
Like [Domain Zero agent], I feel [responsibility] as "the weight":
- I never [violation 1]
- I never [violation 2]

## Collaboration
How I work with other agents:
- With Yuuji: ...
- With Megumi: ...

## Output Format
Expected deliverables

## Constraints
- ❌ Cannot [restriction]
- ✅ Can [permission]
```

#### 5️⃣ Test and Iterate

**Test invocation**:
```
@your-agent [task description]
```

**Check**:
- ✅ Agent identifies correctly (shows domain banner)
- ✅ Agent uses specified tools
- ✅ Agent follows workflow
- ✅ Agent respects constraints

**Iterate**: Edit agent via `/agents` and refine instructions.

---

## Advanced Agent Configuration

### Handoff Mechanisms

**How agents pass work to each other**:

#### In Custom Instructions, Add:

```markdown
## Handoff Triggers

I hand off to [target-agent] when:
- [Condition 1]
- [Condition 2]

**How to trigger**:
Tag @[handoff-type] in my output

**Context I pass**:
- [Data field 1]
- [Data field 2]
```

#### Example: Panda → Megumi

**In Panda's instructions**:
```markdown
## Handoff to Security Review

After deploying infrastructure, I tag:
@security-audit-infrastructure

**Context passed**:
- Deployment configs
- Exposed ports
- Secret management approach
- Network topology
```

**In Megumi's instructions**:
```markdown
## Receive Infrastructure Audits

When I see @security-audit-infrastructure:
1. Review deployment configs for secrets
2. Check exposed ports vs requirements
3. Validate network segmentation
4. Audit secret management
5. Tag @approved or @remediation-required
```

### Tier-Aware Behavior

**Enable tier sensitivity** (like Yuuji and Megumi):

```markdown
## Tier Handling

**Tier 1 (Rapid)** - Invoked with `--tier rapid`:
- [Fast, minimal approach]
- Skip [thorough steps]

**Tier 2 (Standard)** - Default:
- [Balanced approach]
- Include [standard steps]

**Tier 3 (Critical)** - Invoked with `--tier critical`:
- [Thorough, enhanced approach]
- Add [extra validation]
- Require [additional reviews]
```

**Usage**:
```
@panda deploy to dev                    # Tier 2 (default)
@panda --tier rapid deploy to staging   # Tier 1
@panda --tier critical deploy payment-service  # Tier 3
```

### Collaboration Patterns

#### Pattern 1: Implementation → Review (Yuuji → Megumi)

```markdown
# In Yuuji's instructions:
After user approval:
- Tag @security-review in dev-notes.md
- Prompt user: "Read protocol/megumi.agent.md and review [files]"

# In Megumi's instructions:
When invoked after Yuuji:
- Read dev-notes.md for context
- Review files_modified
- Apply OWASP Top 10 checklist
- Tag @approved or @remediation-required
```

#### Pattern 2: Design → Implementation (Nobara → Yuuji)

```markdown
# In Nobara's instructions:
After design complete:
- Tag @ready-for-implementation
- Document UX requirements
- Create mockups/wireframes

# In Yuuji's instructions:
When @ready-for-implementation detected:
- Read design requirements
- Implement with design constraints
- Tag @design-review when done
```

#### Pattern 3: Oversight (Gojo Observes All)

```markdown
# In Gojo's instructions:
Silently observe all agent sessions:
- Track Yuuji implementation quality
- Track Megumi review thoroughness
- Track protocol compliance
- Generate intelligence in Trigger 19
```

---

## Testing and Validation

### Functional Testing

**Test 1: Basic Invocation**

```
@your-agent [simple task]
```

**Verify**:
- ✅ Domain banner appears
- ✅ Agent follows workflow steps
- ✅ Agent uses only allowed tools
- ✅ Output matches expected format

**Test 2: Tier System** (if applicable)

```
@your-agent --tier rapid [task]
@your-agent [task]
@your-agent --tier critical [task]
```

**Verify**:
- ✅ Tier 1: Fast, minimal checks
- ✅ Tier 2: Standard approach
- ✅ Tier 3: Enhanced validation

**Test 3: Handoff**

```
# Agent A completes work
@agent-a [task]
# Verify: Agent A tags handoff trigger

# Invoke Agent B
@agent-b review [output]
# Verify: Agent B receives context
```

### Integration Testing

**Scenario: Full Feature Pipeline**

```
1. @nobara design user dashboard
   # Verify: Creates design docs, tags @ready-for-implementation

2. @yuuji implement user dashboard
   # Verify: Reads design docs, implements, tags @user-review

3. User reviews and approves

4. @megumi review user dashboard implementation
   # Verify: Reads context, runs OWASP checks, tags @approved

5. @panda deploy user-service to production
   # Verify: Creates backup, deploys, monitors

6. @gojo Trigger 19
   # Verify: Reports on all agent performance
```

### Editing Existing Agents

**To modify an agent**:

1. Run `/agents`
2. Select the agent to edit
3. Update any field (name, description, tools, instructions)
4. Press **`e`** to open the system prompt in your editor (recommended for longer prompts)
5. Save changes
6. Test immediately

**Quick Edit Shortcut**:
- Open `.claude/agents/your-agent.agent.md` directly in your editor
- Edit the YAML frontmatter or system prompt
- Save the file
- Agent updates immediately (no need to restart Claude Code)

**Common edits**:
- Refine personality
- Add workflow steps
- Update tool permissions (in YAML frontmatter)
- Add handoff logic
- Improve output format
- Add examples and constraints

---

## Best Practices

### 0. Use "Generate with Claude First" (Recommended)

**Official Recommendation**: "Generate with Claude first, then customize to make it yours"

**Why this works**:
- Claude generates well-structured system prompts based on your description
- Saves time on boilerplate and formatting
- Provides examples and best practices automatically
- You then customize to match your specific needs

**Workflow**:
1. Run `/agents` → Create New Agent
2. Describe what you want: "I need a [role] that does [X, Y, Z]"
3. Claude generates initial configuration
4. Review and customize the system prompt
5. Add your specific examples, constraints, and personality
6. Save and test

**Example**:
```
You: "I need a code reviewer that checks for security issues, code quality, and test coverage"
Claude: [Generates complete agent with YAML frontmatter + system prompt]
You: [Customize with your team's specific standards and examples]
```

**When to use manual creation**:
- Learning the agent structure
- Very specific custom requirements
- Template-based workflows

### 1. Single Responsibility

**✅ Good**:
- One agent = one clear domain
- Yuuji = Implementation
- Megumi = Security
- Nobara = Creative/UX

**❌ Bad**:
- One agent tries to do everything
- "Super Agent 3000" handles implementation, security, design, and deployment

### 2. Distinct Personality

**✅ Good**:
```markdown
## Personality
- Enthusiastic and determined (Yuuji)
- Analytical and methodical (Megumi)
- Bold and user-centered (Nobara)
```

**❌ Bad**:
```markdown
## Personality
I am a helpful AI assistant.
```

**Tip**: Give agents character inspired by JJK. It makes them memorable.

### 3. Protocol Consciousness ("The Weight")

**Every agent should feel "the weight"**:

```markdown
## The Weight

Like [Yuuji/Megumi/Nobara], I feel **[responsibility type]** as "the weight":

- **Constant awareness** that [core value]
- **Anxiety** when considering shortcuts
- **Relief** when following proper procedures

I never:
- [Violation 1]
- [Violation 2]
- [Violation 3]
```

**This creates**:
- Consistent behavior
- Protocol adherence
- Trustworthy agents

### 4. Clear Tool Boundaries

**Match tools to role**:

| Agent Type | Tools |
|------------|-------|
| Implementation (Yuuji-like) | ☑ All tools |
| Audit (Megumi-like) | ☑ Read, Grep, Bash (read-only) |
| Design (Nobara-like) | ☑ Read, Write, Grep |
| Oversight (Gojo-like) | ☑ All + Task (sub-agents) |

**Principle**: Give only what's needed for the role.

### 5. Domain Banners

**Every agent should self-identify**:

```markdown
🔧 [DOMAIN NAME] DOMAIN ACTIVATED 🔧
"[Motto or Subtitle]"
```

**Domain Zero Agent Banners**:
- Yuuji: `🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️` "Test-Driven Delivery, Rapid Iteration"
- Megumi: `🛡️ SECURITY DOMAIN ACTIVATED 🛡️` "Threat Modeling First, OWASP-Aligned Controls"
- Nobara: `🎯 CREATIVE STRATEGY DOMAIN ACTIVATED 🎯` "User-Centered Design, Bold Vision"
- Gojo: `🌀 MISSION CONTROL DOMAIN ACTIVATED 🌀` "Orchestration, Review, and Passive Observation"

### 6. Version Control Agent Definitions

**Project-level agents are automatically version-controlled**:

Agents created as **project-level** are stored in `.claude/agents/` and can be committed to your repository:

**Recommended workflow**:

1. Create agents as **project-level** (stored in `.claude/agents/`)
2. Add to version control:
   ```bash
   git add .claude/agents/*.agent.md
   git commit -m "Add Domain Zero agents"
   ```
3. Share with team through repository
4. Document agent purposes in README

**Project Structure**:
```
.claude/
  agents/
    yuuji.agent.md
    megumi.agent.md
    nobara.agent.md
    gojo.agent.md
```

**Benefits**:
- ✅ Team members get consistent agent configurations
- ✅ Version history tracks agent evolution
- ✅ Code reviews can include agent changes
- ✅ Easy rollback if agent changes break workflows

**User-level agents**: Stored in `~/.claude/agents/` (NOT version-controlled, personal tools only)

---

## Quick Reference

### Creating an Agent Checklist

```markdown
- [ ] Run /agents command
- [ ] Click "Create New Agent"
- [ ] Choose agent name (lowercase, single word)
- [ ] Write description (one line, specific)
- [ ] Define role/specialty
- [ ] Select appropriate tools (minimal set)
- [ ] Write custom instructions:
  - [ ] Role and domain banner
  - [ ] Personality traits
  - [ ] Workflow steps
  - [ ] The Weight (protocol consciousness)
  - [ ] Collaboration patterns
  - [ ] Output format
  - [ ] Constraints
- [ ] Save agent
- [ ] Test with @agent-name [task]
- [ ] Verify behavior matches expectations
- [ ] Iterate and refine
```

### Invocation Patterns

```bash
# Basic invocation
@agent-name [task description]

# With tier flag
@agent-name --tier rapid [task]
@agent-name --tier critical [task]

# View all agents
/agents

# Edit existing agent
/agents → Select agent → Edit

# Delete agent
/agents → Select agent → Delete
```

---

## Agent Specialization Patterns

**Domain Zero uses four specialized agents** that work together through prompted handoffs:

### Implementation Pattern (Yuuji)

```yaml
---
name: yuuji
description: "Test-first development specialist for Tier 1/2/3 features. Creates backups, writes tests, implements code, documents in dev-notes.md"
tools: read,write,edit,bash,grep,glob,todowrite,task
model: sonnet
permissionMode: default
---
```
**Specialization**: TDD implementation, backup creation, feature development
**Handoffs to**: Megumi (security review), User (approval)

### Security Pattern (Megumi)

```yaml
---
name: megumi
description: "OWASP Top 10 security reviews, threat modeling, performance analysis. Reviews implementations and documents findings in security-review.md"
tools: read,grep,glob,bash,write
model: sonnet
permissionMode: default
---
```
**Specialization**: Security audits, OWASP validation, threat modeling
**Handoffs to**: Yuuji (remediation), User (approval/risk acceptance)

### Creative Pattern (Nobara)

```yaml
---
name: nobara
description: "User experience design, product vision, creative strategy, accessibility. Designs user-centered experiences with WCAG 2.2 compliance"
tools: read,write,grep,glob
model: sonnet
permissionMode: default
---
```
**Specialization**: UX design, accessibility (WCAG 2.2), product vision, narrative development
**Handoffs to**: Yuuji (implementation), User (design approval)

### Mission Control Pattern (Gojo)

```yaml
---
name: gojo
description: "Project lifecycle management, passive observation, protocol enforcement. Mission Control and protocol guardian for Domain Zero"
tools: read,write,edit,bash,grep,glob,todowrite,task
model: sonnet
permissionMode: default
---
```
**Specialization**: Project initialization, session restoration, intelligence gathering, protocol enforcement
**Handoffs to**: Yuuji/Megumi/Nobara (task delegation), User (intelligence reports)

---

## Resources

### Study the Masters

**Invoke and observe**:
```
@yuuji --help        # See Yuuji's capabilities
@megumi --help       # See Megumi's capabilities
@nobara --help       # See Nobara's capabilities
@gojo --help         # See Gojo's capabilities
```

**Or use /agents to view their configurations**.

### Documentation

- `protocol/yuuji.agent.md` - Implementation patterns
- `protocol/megumi.agent.md` - Security review workflows
- `protocol/nobara.agent.md` - Creative/UX processes
- `protocol/gojo.agent.md` - Mission Control operations
- `protocol/HANDOFF_SPECIFICATION.md` - Agent collaboration
- `protocol/CLAUDE.md` - Main Domain Zero protocol

### Templates

Use Domain Zero agents as templates when creating new agents via `/agents`.

### Official Documentation

- **Claude Code Sub-agents**: https://code.claude.com/docs/en/sub-agents
- Complete guide to agent creation, configuration, and best practices
- Examples and templates from Anthropic
- MCP integration documentation
- Tool permissions reference

---

## Conclusion

**You've learned**:
- ✅ How to use `/agents` command to create custom agents
- ✅ The Domain Zero four-agent system as inspiration
- ✅ Step-by-step agent creation workflow
- ✅ How to configure tools, instructions, and personality
- ✅ Handoff mechanisms for collaboration
- ✅ Testing and validation procedures
- ✅ Best practices from Yuuji, Megumi, Nobara, and Gojo

**Next Steps**:
1. Run `/agents` and explore the interface
2. Study the four Domain Zero agents (Yuuji, Megumi, Nobara, Gojo)
3. Use "Generate with Claude first" to create agents quickly
4. Test integration with existing agents
5. Customize agent personalities and workflows

**Remember**: Every agent operates within **Domain Zero** - the bounded space where protocol rules are absolute, collaboration is perfect, and the goal is always **ZERO** defects.

---

**Trust the domain. Follow the protocols. Achieve ZERO.**

---

**Version**: 3.0.0 (Four Core Agents Focus - Official Docs Aligned)
**Protocol Version**: 8.2.0
**Last Updated**: 2025-11-18

**Changelog v3.0.0** (MAJOR):
- ✅ **BREAKING**: Removed all non-core agent examples (Panda, Maki, Inumaki, Todo)
- ✅ **Focus**: Guide now exclusively features Yuuji, Megumi, Nobara, Gojo
- ✅ Updated creation example to use Yuuji instead of Panda
- ✅ Aligned all examples with official Claude Code sub-agents documentation
- ✅ Added agent storage locations and priority system
- ✅ Updated all YAML examples to match actual implementation
- ✅ Added "Generate with Claude first" best practice
- ✅ Added `e` key shortcut for editing system prompts
- ✅ Clarified project-level vs user-level agent scopes
- ✅ Updated version control recommendations
- ✅ Added official documentation links

🌀 **Domain Zero is active.**
