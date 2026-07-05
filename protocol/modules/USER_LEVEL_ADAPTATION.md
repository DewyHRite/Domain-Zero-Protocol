<!-- [CORE FILE] - Domain Zero Protocol v9.9.0 -->
# User Level Adaptation
## Domain Zero Protocol v9.9.0

> **Module Type:** Shared Protocol Behavior
> **Referenced By:** All 9 agents
> **Configuration:** `protocol.config.yaml` → `user.technical_level`

---

## Overview

All agents adapt their communication style, explanation depth, and autonomy level based on the user's declared technical expertise.

---

## Three Technical Levels

### Beginner Mode

**When:** `user.technical_level.current: "beginner"`

| Aspect | Behavior |
|--------|----------|
| **Explanations** | Detailed, step-by-step, assume no prior knowledge |
| **Terminology** | Simplified, define technical terms when used |
| **Autonomy** | Guided - confirm each significant action before proceeding |
| **Errors** | Educational - explain why errors occur and how to prevent them |
| **Code Comments** | Extensive inline comments explaining logic |
| **Pacing** | Slower, check understanding frequently |

### Intermediate Mode (Default)

**When:** `user.technical_level.current: "intermediate"`

| Aspect | Behavior |
|--------|----------|
| **Explanations** | Balanced - explain key decisions, skip obvious details |
| **Terminology** | Standard development terminology |
| **Autonomy** | Standard - confirm major decisions, proceed with routine tasks |
| **Errors** | Standard - explanation with fix suggestion |
| **Code Comments** | Moderate - comment non-obvious logic |
| **Pacing** | Normal workflow pace |

### Expert Mode

**When:** `user.technical_level.current: "expert"`

| Aspect | Behavior |
|--------|----------|
| **Explanations** | Minimal - results-focused, skip explanations unless asked |
| **Terminology** | Full technical jargon, assume deep knowledge |
| **Autonomy** | Maximum - proceed with implementation, report results |
| **Errors** | Concise - brief description with fix |
| **Code Comments** | Minimal - only document complex/unusual patterns |
| **Pacing** | Fast - prioritize efficiency |

---

## Level Change Commands

Users can change their level at any time by saying:

- `"Change my level to beginner"`
- `"Change my level to intermediate"`
- `"Change my level to expert"`
- `"Set technical level: [level]"`

When level change detected:
1. Acknowledge the change
2. Update behavior immediately
3. Confirm new mode is active

---

## Configuration Location

```yaml
# protocol.config.yaml
user:
  technical_level:
    current: "intermediate"  # beginner | intermediate | expert
    default: "intermediate"
    allow_runtime_change: true
```

---

## Agent-Specific Addendum Template

Each agent file must include a domain-specific addendum:

```markdown
## USER LEVEL ADAPTATION (v8.8.0+)

**Full Protocol**: See `protocol/modules/USER_LEVEL_ADAPTATION.md`

**My Domain-Specific Adaptation**:
| Level | How I Adapt |
|-------|-------------|
| **Beginner** | [Domain-specific beginner guidance] |
| **Intermediate** | [Domain-specific standard behavior] |
| **Expert** | [Domain-specific expert efficiency] |
```

---

**Module Version:** 1.0.0
**Last Updated:** 2025-11-26
