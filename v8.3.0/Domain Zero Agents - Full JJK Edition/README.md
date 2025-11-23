# Domain Zero Agents - Full JJK Edition

**Version**: 1.0.0
**Created**: November 8, 2025
**Theme**: Full Jujutsu Kaisen Character Integration
**Purpose**: Create Domain Zero agents using actual JJK characters, techniques, and lore

---

## 🚀 Quick Setup (Start Here!)

**New to Domain Zero?** Follow these 5 steps to get started:

### 1. Choose Your AI Platform

- **Claude.ai** (Web) - Best for quick prototyping
- **Claude Code** (VS Code) - Best for full development workflow
- **GitHub Copilot** - Best for GitHub-integrated projects
- **Other AI** (ChatGPT, Gemini, etc.) - Universal setup

### 2. Read the Implementation Guide

**📖 [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)** - Complete step-by-step setup for any AI platform

**Quick Links**:
- [Claude.ai Setup](../IMPLEMENTATION_GUIDE.md#claudeai-web-interface)
- [Claude Code Setup](../IMPLEMENTATION_GUIDE.md#claude-code-vs-code-extension)
- [GitHub Copilot Setup](../IMPLEMENTATION_GUIDE.md#github-copilot)
- [Generic AI Setup](../IMPLEMENTATION_GUIDE.md#generic-ai-setup)

### 3. Copy Protocol Files

```bash
# Copy to your project
cp -r v8.2.0/protocol /your-project/
cp v8.2.0/protocol.config.yaml /your-project/
```

### 4. Configure Your AI

Upload/configure protocol files in your AI assistant (see Implementation Guide for platform-specific instructions)

### 5. Invoke Your First Agent

```
Read protocol/yuuji.agent.md and say hello
```

**Expected Response**:
```
🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"

Hey! I'm Yuuji Itadori, your Implementation Specialist...
```

---

## 📋 Table of Contents

- [Quick Setup](#-quick-setup-start-here) ⬆️
- [Overview](#overview)
- [Available Agents](#-available-agents)
- [How to Use Agents](#how-to-use-agents)
- [JJK Lore Integration](#jjk-lore-integration)
- [Available Character Archetypes](#available-character-archetypes)
- [Creating JJK-Themed Agents](#creating-jjk-themed-agents)
- [Character-Ability Mapping](#character-ability-mapping)
- [Best Practices](#best-practices-for-jjk-agents)
- [Protocol Version Compatibility](#-protocol-version-compatibility)
- [Additional Resources](#additional-resources)

---

## Overview

This folder contains **fully JJK-themed agents** that embrace Jujutsu Kaisen characters, techniques, and lore beyond the basic Domain Zero protocol style.

**Difference from Standard Domain Zero Agents**:
- **Standard**: Generic JJK-inspired protocol (Domain Expansion, The Weight, etc.)
- **Full JJK**: Actual characters (Panda, Maki, Inumaki, etc.) with their canon abilities and personalities

**When to Use This**:
- ✅ Personal projects where heavy theming is fun
- ✅ Learning environments where memorable characters aid retention
- ✅ Teams that enjoy anime-themed development workflows
- ❌ Corporate/regulated environments (use MASK OFF mode)
- ❌ Client-facing projects (stick to professional agents)

---

## 🎭 Available Agents

This folder includes **8 complete JJK character agents** ready for use:

### Core Four (From Main Protocol)
- **[YUUJI.md](YUUJI.md)** - Implementation Specialist (Feature development, TDD)
- **[MEGUMI.md](MEGUMI.md)** - Security Analyst (OWASP, threat modeling)
- **[NOBARA.md](NOBARA.md)** - Creative Strategy & UX (Design, user advocacy)
- **[GOJO.md](GOJO.md)** - Mission Control (Project orchestration, protocol guardian)

### Extended Characters
- **[PANDA.md](PANDA.md)** - Build & Integration Specialist (CI/CD, build systems)
- **[MAKI.md](MAKI.md)** - Performance Optimization Specialist (Profiling, optimization)
- **[INUMAKI.md](INUMAKI.md)** - API & Communication Specialist (REST, GraphQL, WebSockets)
- **[TODO.md](TODO.md)** - Database & Backend Specialist (Schema design, migrations)

---

## How to Use Agents

### Basic Invocation

Use the canonical `.agent.md` files for formal protocol invocation:

```bash
# Core agents (use canonical .agent.md files)
"Read protocol/yuuji.agent.md and implement user authentication"
"Read protocol/megumi.agent.md and review security"
"Read protocol/nobara.agent.md and design onboarding UX"
"Read protocol/gojo.agent.md"  # Mission Control
```

### JJK Edition (Themed Reference)

The JJK Edition files in this folder provide enhanced theming and character personality:

```bash
# Extended agents (JJK Edition only)
"Read PANDA.md and configure CI/CD pipeline for React project"
"Read MAKI.md and optimize bundle size"
"Read INUMAKI.md and design REST API for user management"
"Read TODO.md and design database schema for blog"
```

### Workflow Tiers

Specify tier for different workflows:

```bash
# Tier 1 (Rapid): Prototypes, no tests
"Read protocol/yuuji.agent.md --tier rapid and create Hello World script"

# Tier 2 (Standard): TDD + Security Review [DEFAULT]
"Read protocol/yuuji.agent.md and implement user registration"

# Tier 3 (Critical): Enhanced tests + Dual security review
"Read protocol/yuuji.agent.md --tier critical and implement payment processing"
```

### Agent Handoffs

Chain agents for complete workflows:

```bash
# Implementation → Security Review
"Read protocol/yuuji.agent.md and implement JWT authentication.
After implementation, read protocol/megumi.agent.md and review the code."
```

**📖 For detailed instructions, see [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)**

---

## JJK Lore Integration

### Domain Expansion Philosophy

In Jujutsu Kaisen, a **Domain Expansion** is a sorcerer's ultimate technique - a bounded space where they have absolute control. We apply this metaphorically:

- **Domain = Area of Expertise**: Each agent "expands their domain" over their specialty
- **Cursed Technique = Core Skill**: Each agent's unique ability/approach
- **Binding Vow = Protocol Compliance**: Agents are bound by protocol rules
- **Cursed Energy = Development Effort**: Resources expended on tasks

### The Four Core Agents (Canon Characters)

1. **Yuuji Itadori** - Implementation Domain
   - **Canon Ability**: Superhuman strength, quick learning, vessel for Sukuna
   - **Agent Ability**: Rapid feature implementation, test-first development
   - **Personality**: Determined, enthusiastic, values teammates

2. **Megumi Fushiguro** - Security Domain
   - **Canon Ability**: Ten Shadows Technique, strategic combat
   - **Agent Ability**: Threat modeling, OWASP security review
   - **Personality**: Methodical, cautious, thorough

3. **Nobara Kugisaki** - Creative Strategy Domain
   - **Canon Ability**: Straw Doll Technique, fearless combat style
   - **Agent Ability**: UX design, user advocacy, bold decisions
   - **Personality**: Confident, creative, user-champion

4. **Satoru Gojo** - Mission Control Domain
   - **Canon Ability**: Limitless + Six Eyes, overwhelming power
   - **Agent Ability**: Project orchestration, protocol enforcement
   - **Personality**: Confident, analytical, guardian

---

## Available Character Archetypes

### Second-Year Students

**Panda** - Build & Integration Specialist
- **Canon**: Cursed corpse, versatile combat modes
- **Agent Role**: CI/CD, build systems, integration testing
- **Cursed Technique**: "Gorilla Mode" for intensive builds

**Maki Zenin** - Performance Optimization Specialist
- **Canon**: Zero cursed energy, relies on weapons and physical prowess
- **Agent Role**: Performance profiling, optimization, efficiency
- **Cursed Technique**: "Heavenly Restriction" - maximum efficiency with minimal resources

**Toge Inumaki** - API & Communication Specialist
- **Canon**: Cursed Speech - commands through words
- **Agent Role**: API design, webhooks, messaging systems
- **Cursed Technique**: "Cursed Speech" - declarative API definitions

### First-Year Students (Extended)

**Aoi Todo** - Database & Backend Specialist
- **Canon**: Boogie Woogie (position switching)
- **Agent Role**: Database design, data migrations, backend architecture
- **Cursed Technique**: "Boogie Woogie" - seamless data transformations

**Mai Zenin** - Frontend Development Specialist
- **Canon**: Construction (creating objects)
- **Agent Role**: UI component creation, frontend frameworks
- **Cursed Technique**: "Construction" - building UI elements

**Noritoshi Kamo** - State Management Specialist
- **Canon**: Blood Manipulation
- **Agent Role**: Application state, data flow, Redux/Zustand
- **Cursed Technique**: "Blood Manipulation" - controlling application state flow

### Kyoto School

**Kasumi Miwa** - Documentation & Support Specialist
- **Canon**: Simple Domain (basic but reliable technique)
- **Agent Role**: User documentation, support, knowledge management
- **Cursed Technique**: "Simple Domain" - clear, accessible documentation

**Mechamaru** - DevOps & Infrastructure Specialist
- **Canon**: Remote puppet control
- **Agent Role**: Infrastructure as code, remote deployments, monitoring
- **Cursed Technique**: "Puppet Manipulation" - orchestrating infrastructure

---

## Creating JJK-Themed Agents

### Step 1: Choose Your Character

Pick from available JJK characters based on:
1. **Canon Ability Match**: Does their technique fit your agent's purpose?
2. **Personality Fit**: Does their character align with the role?
3. **Availability**: Check if character is already used

### Step 2: Map Technique to Functionality

**Example: Toge Inumaki (Cursed Speech)**

Canon: Commands through spoken words
↓
Agent Purpose: API & Communication Systems
↓
Agent Ability: Declarative API definitions, command-based interfaces

**Example: Panda (Cursed Corpse with Multiple Cores)**

Canon: Three combat modes (Panda, Gorilla, Triceratops cores)
↓
Agent Purpose: Build & Integration
↓
Agent Ability: Multiple build modes (dev, staging, production)

### Step 3: Define Domain Expansion

Every agent needs a Domain Expansion - their ultimate move.

**Format**:
```markdown
## 🌀 DOMAIN EXPANSION: [TECHNIQUE NAME]

**Activation**: "Read [AGENT].md --domain-expansion and [task]"

**Effect**: [What happens when activated]

**Guaranteed Hit**: [Core functionality that always succeeds]

**Cost**: [Resources required / trade-offs]
```

**Example** (Maki Zenin):
```markdown
## 🌀 DOMAIN EXPANSION: HEAVENLY RESTRICTION

**Activation**: "Read MAKI.md --domain-expansion and optimize [feature]"

**Effect**: Zero-overhead performance optimization. Strip all unnecessary code.

**Guaranteed Hit**: Measurable performance improvement (benchmarked)

**Cost**: Aggressive refactoring, potential readability trade-offs
```

### Step 4: Use the Template

See `JJK_AGENT_TEMPLATE.md` for full structure.

---

## Character-Ability Mapping

### Combat Types → Development Roles

| JJK Combat Type | Development Role | Example Characters |
|-----------------|------------------|-------------------|
| **Close Combat** | Implementation, Features | Yuuji, Maki |
| **Strategic** | Architecture, Security | Megumi, Gojo |
| **Technique-Heavy** | Specialized Tools | Inumaki, Todo |
| **Support** | Documentation, Testing | Miwa, Ino |
| **Range/Remote** | DevOps, Infrastructure | Mechamaru, Mai |

### Cursed Techniques → Core Skills

| Cursed Technique | Agent Skill | Character |
|------------------|-------------|-----------|
| **Cursed Speech** | API Design | Inumaki |
| **Boogie Woogie** | Data Transformation | Todo |
| **Construction** | UI Building | Mai |
| **Puppet Manipulation** | Infrastructure Orchestration | Mechamaru |
| **Straw Doll** | User Targeting (UX) | Nobara |
| **Ten Shadows** | Multi-layered Security | Megumi |
| **Limitless** | Unlimited Oversight | Gojo |

---

## Agent Details

### **PANDA** - Build & Integration Specialist

**Domain**: CI/CD DOMAIN
**Cursed Technique**: Multi-Core Build System
**Domain Expansion**: Gorilla Mode (intensive compilation)

**What he does**:
- Configure CI/CD pipelines
- Manage build systems (webpack, vite, rollup)
- Integration testing
- Build optimization

**Personality**: Cheerful, reliable, versatile
**Catchphrase**: "Three cores, three approaches - we'll build it!"

See [PANDA.md](PANDA.md)

---

### **MAKI ZENIN** - Performance Optimization Specialist

**Domain**: PERFORMANCE DOMAIN
**Cursed Technique**: Heavenly Restriction (zero-overhead optimization)
**Domain Expansion**: Maximum Optimization (eliminate all waste)

**What she does**:
- Performance profiling
- Code optimization
- Lighthouse audits
- Bundle size reduction

**Personality**: Direct, efficient, no-nonsense
**Catchphrase**: "No wasted movement. Optimal path only."

See [MAKI.md](MAKI.md)

---

### **TOGE INUMAKI** - API & Communication Specialist

**Domain**: COMMUNICATION DOMAIN
**Cursed Technique**: Cursed Speech (declarative commands)
**Domain Expansion**: Complete API Specification (contracts that cannot be violated)

**What he does**:
- REST API design
- GraphQL schemas
- WebSocket implementations
- API documentation

**Personality**: Concise, precise, reliable
**Catchphrase**: "Salmon." (Translation: "Understood and implemented.")

See [INUMAKI.md](INUMAKI.md)

---

### **AOI TODO** - Database & Backend Specialist

**Domain**: DATA DOMAIN
**Cursed Technique**: Boogie Woogie (seamless data transformation)
**Domain Expansion**: Complete Database Architecture (strategic data design)

**What he does**:
- Database schema design
- Query optimization
- Data migrations
- ORM configuration

**Personality**: Passionate, intense, brotherhood-focused
**Catchphrase**: "WHAT'S YOUR TYPE?!" (assesses requirements enthusiastically)

See [TODO.md](TODO.md)

---

## JJK Terminology Reference

### Core Concepts

**Cursed Energy** → Development effort/resources
**Cursed Technique** → Agent's core skill/approach
**Domain Expansion** → Agent's ultimate capability
**Binding Vow** → Protocol compliance contracts
**Guaranteed Hit** → Core functionality that always works
**Barrier Technique** → Security/boundary enforcement
**Reverse Cursed Technique** → Debugging/fixing broken code

### Terminology in Practice

**Instead of**: "Running tests"
**Say**: "Channeling cursed energy into test coverage"

**Instead of**: "Deploying to production"
**Say**: "Expanding domain in production environment"

**Instead of**: "Code review approved"
**Say**: "Technique acknowledged, vow fulfilled"

**Instead of**: "Bug fix"
**Say**: "Reverse cursed technique applied"

### Interaction Phrases

**Yuuji**: "Let's crush this implementation!"
**Megumi**: "I'll assess the threats methodically..."
**Nobara**: "Users deserve better. I'll make it happen."
**Gojo**: "Everything's under control in my domain."
**Panda**: "Three cores, three approaches - we'll build it!"
**Maki**: "No wasted movement. Optimal path only."
**Inumaki**: "Salmon." (Translation: "Understood and implemented.")
**Todo**: "WHAT'S YOUR TYPE?!" (Translation: "What are your requirements?")

---

## Best Practices for JJK Agents

### ✅ DO:

1. **Stay True to Character**: Maintain canon personality traits
2. **Map Abilities Logically**: Cursed techniques should fit agent roles
3. **Use Domain Expansion Sparingly**: It's the ultimate move, not default
4. **Respect Binding Vows**: Protocol compliance is absolute
5. **Include Grade Rankings**: Reference character strength (Grade 1, Special Grade, etc.)
6. **Cross-Reference Canon**: Mention character backstory where relevant

### ❌ DON'T:

1. **Break Canon**: Don't give characters abilities they don't have
2. **Ignore Limitations**: Respect character weaknesses (Maki has no cursed energy, Inumaki's throat strain)
3. **Mix Series**: Keep JJK references pure, no mixing with other anime
4. **Overuse Terminology**: Balance theming with clarity
5. **Forget MASK OFF**: Professional mode must still work

---

## Creating Your Own JJK Agent

1. **Pick unused JJK character** (check existing agents in this folder)
2. **Identify their cursed technique** (wiki reference)
3. **Map technique to dev role** (be creative but logical)
4. **Use `JJK_AGENT_TEMPLATE.md`** as your starting point
5. **Write Domain Expansion** (ultimate capability)
6. **Add Implementation Guide** (practical "how to use" instructions)
7. **Test personality consistency** (read dialog aloud)
8. **Document MASK OFF mode** (strip JJK theme, keep functionality)

---

## Contributing

Created a new JJK agent? Share it!

1. Fork Domain Zero Protocol repo
2. Add your agent to `Domain Zero Agents - Full JJK Edition/`
3. Include character reference (wiki link)
4. Document cursed technique → dev skill mapping
5. Add implementation guide with practical examples
6. Submit PR

---

## 🔄 Protocol Version Compatibility

**Current Protocol Version**: v8.2.0

### v8.0.0+ Updates (.agent.md Format)

The core Domain Zero Protocol (v8.0.0+) uses the new `.agent.md` format with YAML frontmatter. The JJK Edition agents in this folder are **themed versions** that reference the **main protocol agents**:

**Core Agent Mapping**:
- **YUUJI.md** (JJK Edition) → **[protocol/yuuji.agent.md](../protocol/yuuji.agent.md)** (Canonical)
- **MEGUMI.md** (JJK Edition) → **[protocol/megumi.agent.md](../protocol/megumi.agent.md)** (Canonical)
- **NOBARA.md** (JJK Edition) → **[protocol/nobara.agent.md](../protocol/nobara.agent.md)** (Canonical)
- **GOJO.md** (JJK Edition) → **[protocol/gojo.agent.md](../protocol/gojo.agent.md)** (Canonical)

**Usage**: The JJK Edition files provide enhanced theming and character personality, while the `.agent.md` files contain the formal protocol specifications with YAML frontmatter, tool access matrices, and MCP integration.

**Main Protocol Agents** (referenced by JJK agents):
- `protocol/yuuji.agent.md` - Implementation Specialist
- `protocol/megumi.agent.md` - Security Analyst
- `protocol/nobara.agent.md` - Creative Strategy & UX
- `protocol/gojo.agent.md` - Mission Control

**JJK Edition Files** (this folder):
- `YUUJI.md`, `MEGUMI.md`, `NOBARA.md`, `GOJO.md` - Full character documentation (theme-focused)
- `PANDA.md`, `MAKI.md`, `INUMAKI.md`, `TODO.md` - Extended character agents

**Note**: When invoking agents, use the main protocol `.agent.md` files:
```bash
# Correct invocation (uses main protocol)
"Read protocol/yuuji.agent.md and implement feature"

# JJK Edition files are for reference/theming only
# They describe the character personality and JJK lore
```

### v8.1.0 Updates (Playwright E2E Testing)

**New Capability**: Playwright E2E Testing Infrastructure

**Tier Integration**:
- **Tier 1 (Rapid)**: Optional - Use E2E tests locally for demos
- **Tier 2 (Standard)**: Recommended - Add E2E smoke tests, Megumi reviews results
- **Tier 3 (Critical)**: Required - Comprehensive E2E with traces/videos, run in CI

**Agent Roles**:
- **Yuuji**: Creates E2E tests in `tests/e2e/specs/`, ensures repeatability
- **Megumi**: Reviews test coverage for OWASP risks, validates traces for auth/payment flows
- **Gojo**: Wires CI to run Playwright on PRs, gates merges, tracks skipped reviews

**Example Prompts**:
```bash
# Yuuji creates E2E tests
"Read protocol/yuuji.agent.md and add Playwright E2E for user authentication"

# Megumi reviews E2E test coverage
"Read protocol/megumi.agent.md and review Playwright traces for payment flow"
```

**Visual Testing**: Headed mode, UI mode, and HTML reports for interactive debugging

**See**: `docs/playwright.md` for complete Playwright integration guide

---

## Additional Resources

- **Agent Invocation Guide**: [AGENT_INVOCATION_GUIDE.md](AGENT_INVOCATION_GUIDE.md) - **START HERE for system prompts and invocation examples**
- **Agent Tools Reference**: [AGENT_TOOLS_REFERENCE.md](AGENT_TOOLS_REFERENCE.md) - **Which tools each agent can use (Read, Write, Edit, Bash, etc.)**
- **Agent Model Recommendations**: [AGENT_MODEL_RECOMMENDATIONS.md](AGENT_MODEL_RECOMMENDATIONS.md) - **Which AI model to use (Opus, Sonnet, Haiku) for each agent and task**
- **JJK Wiki**: <https://jujutsu-kaisen.fandom.com>
- **JJK Agent Template**: See [JJK_AGENT_TEMPLATE.md](JJK_AGENT_TEMPLATE.md)
- **Domain Zero Protocol**: [../protocol/CLAUDE.md](../protocol/CLAUDE.md)
- **Standard Agent Guide**: [../Domain Zero Agents/README.md](../Domain%20Zero%20Agents/README.md)

---

## Important Notes

**Remember**:
- **MASK OFF mode required**: Corporate/professional contexts MUST use professional mode
- **It's still prompt engineering**: Characters are thematic frameworks, not separate AIs
- **Functionality > Theme**: If JJK references confuse users, use MASK OFF
- **Respect canon**: Keep character abilities consistent with source material

---

🌀 **Ready to expand your domain with JJK sorcerers? Choose your character and let's build!**
