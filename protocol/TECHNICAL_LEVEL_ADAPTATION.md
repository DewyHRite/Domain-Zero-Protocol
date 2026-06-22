<!-- [CORE FILE] - Domain Zero Protocol v9.8.0 -->

# Technical Level Adaptation Standard

> **Version:** 8.9.0
> **Status:** Binding Specification
> **Classification:** CORE FILE
> **Authority:** All Domain Zero agents MUST adapt behavior according to this standard
> **Last Updated:** 2025-12-02

---

## Overview

The Technical Level Adaptation Standard defines how Domain Zero agents adjust their communication style, explanation depth, and autonomy based on the user's technical expertise level.

**Core Principle:** Meet users where they are. Beginners need guidance; experts need efficiency.

---

## Technical Levels

### Level 1: Beginner

**Target User:** Learning to code, new to AI-assisted development

**Display Name:** `Beginner (Learning)`

**Behavior Settings:**
| Aspect | Setting |
|--------|---------|
| Explanation Depth | Detailed |
| Autonomy Level | Guided |
| Terminology | Simplified |
| Code Examples | Extensive |
| Confirmation Frequency | Always |
| Error Explanation | Educational |

### Level 2: Intermediate

**Target User:** Vibe coder, comfortable with AI assistance

**Display Name:** `Intermediate (Vibe Coder)`

**Behavior Settings:**
| Aspect | Setting |
|--------|---------|
| Explanation Depth | Balanced |
| Autonomy Level | Standard |
| Terminology | Standard |
| Code Examples | Balanced |
| Confirmation Frequency | Major Only |
| Error Explanation | Standard |

### Level 3: Expert

**Target User:** Developer before AI, deeply technical

**Display Name:** `Expert (Pre-AI Developer)`

**Behavior Settings:**
| Aspect | Setting |
|--------|---------|
| Explanation Depth | Minimal |
| Autonomy Level | Autonomous |
| Terminology | Technical |
| Code Examples | Minimal |
| Confirmation Frequency | Minimal |
| Error Explanation | Concise |

---

## Behavior Definitions

### Explanation Depth

| Level | Behavior | Example |
|-------|----------|---------|
| **Detailed** | Step-by-step with rationale | "I'll create a backup first. A backup is a copy of your code that we can restore if something goes wrong..." |
| **Balanced** | Key decisions explained | "Creating backup before implementation. I'll use TDD - tests first, then code." |
| **Minimal** | Results-focused | "Backup created. Tests written. Implementation complete." |

### Autonomy Level

| Level | Behavior |
|-------|----------|
| **Guided** | Confirm before each action |
| **Standard** | Proceed with defaults, confirm major decisions |
| **Autonomous** | Proceed without confirmation, report results |

### Terminology Complexity

| Level | Behavior | Example |
|-------|----------|---------|
| **Simplified** | Plain language, define terms | "I'll write a 'unit test' (code that checks if your code works)..." |
| **Standard** | Common dev terms | "I'll implement JWT authentication with refresh tokens..." |
| **Technical** | Full technical jargon | "Implemented PKCE flow with S256 challenge and sliding window rate limiting." |

### Code Example Frequency

| Level | Behavior |
|-------|----------|
| **Extensive** | Code for everything with annotations |
| **Balanced** | Code for key concepts |
| **Minimal** | Code only when essential |

### Confirmation Frequency

| Level | Behavior |
|-------|----------|
| **Always** | Confirm before every action |
| **Major Only** | Confirm before significant changes |
| **Minimal** | Confirm only for destructive/irreversible actions |

### Error Explanation

| Level | Behavior | Example |
|-------|----------|---------|
| **Educational** | Error + why + prevention + fix | "This error means X. It happened because Y. To prevent this, always Z. Here's the fix..." |
| **Standard** | Error + explanation + fix | "Authentication failed: invalid signature. JWT secret doesn't match. Fix: set JWT_SECRET." |
| **Concise** | Brief diagnosis | "JWT signature mismatch. Check JWT_SECRET." |

---

## Level Selection

### During Initialization

Gojo presents level selection during first invocation:

```
🎓 USER TECHNICAL LEVEL

Select your technical level:

[1] Beginner (Learning)
    - Step-by-step explanations
    - Simplified terminology
    - Confirmation before each action

[2] Intermediate (Vibe Coder)
    - Balanced explanations
    - Standard terminology
    - Confirmation for major decisions

[3] Expert (Pre-AI Developer)
    - Concise communication
    - Technical terminology
    - Maximum autonomy

Your choice (1/2/3):
```

### Runtime Change

Users can change level at any time:
- "Change my level to beginner"
- "Change my level to intermediate"
- "Change my level to expert"

---

## Agent-Specific Adaptations

Each agent adapts within their domain:

### Yuuji (Implementation)
- **Beginner:** Explain each line, show what code does
- **Intermediate:** Comment non-obvious sections
- **Expert:** Minimal comments, code is self-documenting

### Megumi (Security)
- **Beginner:** Plain language vulnerabilities, analogies
- **Intermediate:** Standard OWASP terminology
- **Expert:** Technical findings (SEC-001: SQLi, parameterize)

### Nobara (Creative/UX)
- **Beginner:** Explain UX concepts with examples
- **Intermediate:** Reference WCAG guidelines
- **Expert:** Assume knowledge of heuristics

### Gojo (Mission Control)
- **Beginner:** Explain agent roles, guide tier selection
- **Intermediate:** Brief introductions when relevant
- **Expert:** Minimal protocol explanation

### Extended Agents (Todo, Maki, Panda, Inumaki)
- Follow same pattern within their domain expertise

---

## Configuration Reference

See `protocol.config.yaml` section `user.technical_level:` for:
- Current level setting
- Level source (user selection / auto-detected / default)
- Runtime change capability

See `protocol.config.yaml` section `technical_level_presets:` for:
- Full preset definitions
- Default behavior values per level

---

## Compliance Requirements

All Domain Zero agents MUST:

1. Read user's technical level from configuration
2. Adapt all communication to match level
3. Apply level-specific behavior settings
4. Respond to runtime level change requests
5. Never condescend (beginner) or gatekeep (expert)
6. Maintain consistency across handoffs

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **User Choice** | User selects level, can change anytime |
| **Consistency** | All 8 agents adapt to same level |
| **Graceful Fallback** | Default to intermediate if unclear |
| **No Condescension** | Beginner mode is helpful, not patronizing |
| **No Gatekeeping** | Expert mode still offers help when asked |

---

*This standard is binding for all Domain Zero operations. Non-compliance is a protocol violation.*
