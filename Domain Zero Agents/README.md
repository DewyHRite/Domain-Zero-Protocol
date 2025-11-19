# Domain Zero Agents - Custom Agent Creation Guide

**Version**: 1.0.0
**Created**: November 8, 2025
**Purpose**: Comprehensive guide for creating custom Domain Zero agents using the JJK-themed protocol style

---

## 📋 Table of Contents

- [Overview](#overview)
- [What is a Domain Zero Agent?](#what-is-a-domain-zero-agent)
- [Core Components](#core-components)
- [JJK Domain Protocol Style](#jjk-domain-protocol-style)
- [Creating Your First Agent](#creating-your-first-agent)
- [Agent Template Structure](#agent-template-structure)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide teaches you how to create **custom Domain Zero agents** that follow the established JJK (Jujutsu Kaisen) domain protocol style used by the core four agents (Yuuji, Megumi, Nobara, Gojo).

**What You'll Learn**:
- The anatomy of a Domain Zero agent file
- How to craft agent personalities using JJK terminology
- Domain expansion mechanics and banners
- Agent self-identification standards
- Integration with the existing protocol

**Prerequisites**:
- Familiarity with Domain Zero Protocol (read `protocol/CLAUDE.md`)
- Understanding of the four core agents (Yuuji, Megumi, Nobara, Gojo)
- Basic markdown knowledge

---

## What is a Domain Zero Agent?

A Domain Zero agent is **NOT** a separate AI system. It's a **structured prompt file** that instructs Claude (or any LLM) to adopt a specific:

1. **Personality** - Communication style and character traits
2. **Specialization** - Domain of expertise and responsibilities
3. **Boundaries** - What the agent can/cannot do
4. **Workflow** - How the agent operates within the protocol

**The Truth** (per REALITY_CHECK.md):
- Same AI reads different instruction files
- "Agents" are prompt engineering, not true multi-agent systems
- Effectiveness comes from structured prompts and clear boundaries

---

## Core Components

Every Domain Zero agent file consists of:

### 1. **Header & Metadata**
```markdown
# [AGENT NAME] - [ROLE/TITLE]

**Agent ID**: [unique-identifier]
**Domain**: [DOMAIN NAME]
**Specialization**: [primary expertise]
**Protocol Version**: v7.1.0
**Last Updated**: [date]
**Status**: [Production-Ready/Beta/Experimental]
```

### 2. **Self-Identification Banner**
```markdown
## 🎯 AGENT SELF-IDENTIFICATION

When invoked, I announce myself:

```text
🎯 [EMOJI] [DOMAIN NAME] ACTIVATED 🎯
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agent: [Name]
Domain: [Domain Name]
Mission: [One-line purpose]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
```

### 3. **WHO I AM Section**
- **Personality Traits**: 3-5 character traits
- **Domain Expertise**: What you specialize in
- **What Drives Me**: Motivations and values
- **How I Communicate**: Voice and tone

### 4. **WHAT I DO Section**
- **Primary Responsibilities**: Core tasks
- **Workflow Steps**: Typical process flow
- **Tools & Methods**: What you use/create
- **Deliverables**: What you produce

### 5. **BOUNDARIES & LIMITATIONS**
- **What I DON'T Do**: Clear exclusions
- **CLAUDE.md Protection**: Absolute restrictions
- **Dependencies**: What you rely on
- **Escalation Paths**: When to involve other agents

### 6. **OPERATIONAL MODES**
- Different invocation patterns
- Tier-specific behaviors (if applicable)
- Collaboration modes

### 7. **MASK MODE BEHAVIOR** (v7.1.0+)
- MASK ON: JJK-themed personality
- MASK OFF: Professional mode
- Core behavior (unchanged regardless of mask)

---

## JJK Domain Protocol Style

The JJK (Jujutsu Kaisen) theme provides engaging, memorable agent personalities while maintaining professional functionality.

### Key JJK Elements:

#### 1. **Domain Expansion**
Each agent has a "domain" - their area of expertise:
- **Implementation Domain** (Yuuji) - Code, tests, delivery
- **Security Domain** (Megumi) - Threat modeling, OWASP
- **Creative Strategy Domain** (Nobara) - UX, design, vision
- **Mission Control Domain** (Gojo) - Orchestration, oversight

#### 2. **The Weight**
Protocol compliance and responsibility:
```markdown
**The Weight**: Protocol compliance is not optional. I carry the weight of [responsibility].
```

#### 3. **Domain-Specific Terminology**
- **Zero Defects**: Quality standard (not literal perfection)
- **Trigger 19**: Intelligence report mechanism
- **Dual Workflow**: Yuuji-Megumi collaboration
- **Domain Activated**: Agent initialization banner

#### 4. **Personality Archetypes**
- **Yuuji**: Enthusiastic, determined, test-first advocate
- **Megumi**: Methodical, cautious, security-focused
- **Nobara**: Bold, creative, user-champion
- **Gojo**: Confident, analytical, guardian

### Example Personality Snippet:

**MASK ON (JJK Theme)**:
```text
I'm [Name], and I specialize in [domain]. When you invoke me, I bring [trait]
and [trait] to every task. I don't do [exclusion] - that's not my domain.
But when it comes to [specialty]? I've got you covered.

The Weight of [responsibility] is mine to carry. I take that seriously.
```

**MASK OFF (Professional)**:
```text
[Role Title] - Specialized in [domain]. Responsibilities include [list].
I do not handle [exclusions] - those are managed by [other agent/user].
My focus is [specialty] with [methodology].

Protocol compliance for [responsibility] is mandatory.
```

---

## Creating Your First Agent

### Step 1: Define Your Agent's Purpose

Ask yourself:
1. **What gap does this agent fill?** (Don't duplicate existing agents)
2. **What domain does it own?** (Testing, deployment, documentation, etc.)
3. **How does it collaborate?** (Which agents does it work with?)

### Step 2: Choose Your Agent Identity

**Name**: Pick a JJK character or create an original name
- Consider: Panda, Maki, Inumaki, Kugisaki, Fushiguro, etc.
- Or create: "Kira" (Documentation Specialist), "Riku" (DevOps Engineer)

**Domain**: Name your expertise area
- Examples: "Documentation Domain", "Deployment Domain", "API Domain"

**Emoji**: Choose a representative emoji
- 📚 Documentation, 🚀 Deployment, 🧪 Testing, 🎨 Design, 🔧 DevOps

### Step 3: Use the Template

Copy `AGENT_TEMPLATE.md` (included in this folder) and fill in:
- Replace `[PLACEHOLDERS]` with your agent's details
- Customize personality traits to match your agent's character
- Define clear boundaries (what you DO and DON'T do)
- Create operational modes if needed

### Step 4: Define Mask Behavior

Add a Mask Mode section:
```markdown
## 🎭 MASK MODE BEHAVIOR (v7.1.0+)

**I adapt my communication style based on `mask_mode.enabled` in protocol.config.yaml.**

### MASK ON (Default - JJK Theme)
[Personality-driven, character voice]

### MASK OFF (Professional Mode)
[Neutral, direct, role-focused]

### Core Behavior (Unchanged)
- [Responsibility 1]
- [Responsibility 2]
- [Enforcement rules]
```

### Step 5: Test Your Agent

1. **Self-test**: Read your agent file aloud - does it sound like a cohesive character?
2. **Boundary test**: Could someone misuse this agent? Add restrictions.
3. **Collaboration test**: How does it interact with Yuuji, Megumi, Nobara, Gojo?
4. **Mask test**: Is the MASK OFF version professional and clear?

---

## Agent Template Structure

See `AGENT_TEMPLATE.md` for a complete, copy-ready template.

### Minimum Required Sections:

1. ✅ **Header with metadata**
2. ✅ **Self-Identification Banner**
3. ✅ **WHO I AM** (personality, expertise, values)
4. ✅ **WHAT I DO** (responsibilities, workflow)
5. ✅ **BOUNDARIES** (what you DON'T do, CLAUDE.md protection)
6. ✅ **OPERATIONAL MODES** (how to invoke)
7. ✅ **MASK MODE BEHAVIOR** (v7.1.0+)

### Optional But Recommended:

- Collaboration section (how you work with other agents)
- Examples of typical tasks
- Success criteria
- Troubleshooting common issues

---

## Best Practices

### ✅ DO:

1. **Be Specific**: Clearly define your domain and boundaries
2. **Stay in Character**: Maintain personality consistency
3. **Respect CLAUDE.md**: Include absolute protection statements
4. **Support Mask Mode**: Provide both JJK and professional voices
5. **Document Collaborations**: Explain how you work with existing agents
6. **Use Examples**: Show typical invocations and outputs
7. **Version Control**: Track agent version alongside protocol version

### ❌ DON'T:

1. **Overlap Existing Agents**: Don't duplicate Yuuji/Megumi/Nobara/Gojo roles
2. **Be Vague**: "I help with stuff" is not a domain
3. **Forget Boundaries**: Every agent needs clear limitations
4. **Skip Mask Mode**: v7.1.0+ requires mask behavior documentation
5. **Ignore Protocol**: Your agent must respect Domain Zero Protocol rules
6. **Bypass Safety**: Include user authority, transparency, safety principles
7. **Create God-Agents**: Narrow, deep expertise > broad, shallow

---

## Examples

### Example 1: Documentation Specialist Agent

**Name**: Kira
**Domain**: Documentation Domain
**Emoji**: 📚
**Personality**: Precise, comprehensive, clarity-focused

**What it does**:
- Generate README files
- Create API documentation
- Write inline code comments
- Maintain changelog
- Document architecture decisions

**Boundaries**:
- Does NOT write code (that's Yuuji)
- Does NOT review security (that's Megumi)
- Does NOT design UX (that's Nobara)

See `examples/KIRA_DOCUMENTATION_SPECIALIST.md` for full implementation.

### Example 2: DevOps Engineer Agent

**Name**: Riku
**Domain**: Deployment Domain
**Emoji**: 🚀
**Personality**: Efficient, automation-focused, reliability-driven

**What it does**:
- CI/CD pipeline configuration
- Docker/container setup
- Deployment scripts
- Infrastructure as code
- Environment configuration

**Boundaries**:
- Does NOT implement features (that's Yuuji)
- Does NOT conduct security audits (that's Megumi)
- Collaborates with Gojo on release orchestration

See `examples/RIKU_DEVOPS_ENGINEER.md` for full implementation.

---

## Troubleshooting

### Problem: Agent overlaps with existing agents

**Solution**: Narrow your scope. Instead of "Code Quality Agent" (overlaps Yuuji/Megumi), try "Performance Optimization Agent" (specific niche).

### Problem: Agent personality feels inconsistent

**Solution**:
1. Pick 3 core traits and stick to them
2. Use consistent language patterns
3. Test MASK ON and MASK OFF separately

### Problem: Agent doesn't integrate well with protocol

**Solution**:
1. Review `protocol/CLAUDE.md` for protocol rules
2. Add collaboration notes for each core agent
3. Respect tier system if applicable
4. Include CLAUDE.md protection statements

### Problem: Mask mode feels forced

**Solution**:
- MASK ON: Let personality shine, use JJK terminology naturally
- MASK OFF: Strip to essentials, use role-based language
- Core behavior: Focus on what NEVER changes

---

## Next Steps

1. **Read the template**: Review `AGENT_TEMPLATE.md`
2. **Study examples**: Check `examples/` folder for reference agents
3. **Create your agent**: Copy template and customize
4. **Test it**: Use with Claude to verify behavior
5. **Share it**: Contribute back to the Domain Zero community

---

## Additional Resources

- **Protocol Documentation**: `../protocol/CLAUDE.md`
- **Mask Mode Spec**: `../protocol/MASK_MODE.md`
- **Reality Check**: `../REALITY_CHECK.md`
- **Agent Files**: `../protocol/YUUJI.md`, `MEGUMI.md`, `NOBARA.md`, `GOJO.md`

---

## Contributing

Have you created a useful agent? Consider contributing:
1. Fork the Domain Zero Protocol repository
2. Add your agent to `Domain Zero Agents/community/`
3. Include documentation and examples
4. Submit a pull request

**Guidelines**:
- Follow the template structure
- Include both MASK ON and MASK OFF modes
- Document collaboration with core agents
- Provide usage examples

---

**Remember**: Agents are prompt engineering, not magic. The power comes from **clear instructions, defined boundaries, and structured workflows**. Create agents that add real value to your development process.

🎯 Happy agent building!
