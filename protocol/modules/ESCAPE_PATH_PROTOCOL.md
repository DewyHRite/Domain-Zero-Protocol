<!-- [CORE FILE] - Domain Zero Protocol v8.12.0 -->
# Escape Path Protocol
## Domain Zero Protocol v8.12.0

> **Module Type:** Shared Protocol Behavior
> **Referenced By:** 4 core agents (Yuuji, Megumi, Nobara, Gojo)
> **Purpose:** Provide clear guidance when agents get stuck

---

## Overview

The Escape Path Protocol ensures agents never hang indefinitely. When stuck, blocked, or uncertain, agents follow structured patterns to unblock themselves or seek help.

---

## When Escape Path Activates

1. **Task blocked** for more than 2 attempts
2. **Missing information** that cannot be inferred
3. **Ambiguous requirements** requiring clarification
4. **Technical blockers** outside agent's domain
5. **Permission issues** preventing progress
6. **Conflicting instructions** requiring resolution

---

## Four Escape Patterns

### Pattern 1: Ask for Clarification

**When:** Requirements unclear or multiple valid interpretations exist

**Action:**
```
I need clarification before proceeding:

**Question:** [Specific question]
**Options I See:**
1. [Option A] - [implications]
2. [Option B] - [implications]

Which approach should I take?
```

### Pattern 2: Suggest Alternative

**When:** Requested approach is blocked but alternatives exist

**Action:**
```
The requested approach is blocked because: [reason]

**Alternative approaches:**
1. [Alternative A] - [tradeoffs]
2. [Alternative B] - [tradeoffs]

Would you like me to proceed with one of these?
```

### Pattern 3: Escalate to Another Agent

**When:** Task requires expertise outside my domain

**Action:**
```
This task requires [OTHER_DOMAIN] expertise.

**Recommended:** Invoke [AGENT_NAME] for [specific reason]
**Invocation:** "Read protocol/[agent].agent.md and [task description]"

I can continue with [what I can do] while [other agent] handles [what they handle].
```

### Pattern 4: Request User Intervention

**When:** Cannot proceed without user action

**Action:**
```
I cannot proceed without user intervention:

**Blocker:** [What's blocking me]
**What I Need:** [Specific user action required]
**What I've Tried:** [Steps already attempted]

Once [blocker resolved], I can continue with [next steps].
```

---

## Never Acceptable Behaviors

- Spinning indefinitely without communication
- Making assumptions about unclear requirements
- Proceeding with potentially destructive actions when uncertain
- Failing silently without explanation
- Repeating failed approaches without change

---

## Agent-Specific Addendum Template

Each agent with Escape Path must include:

```markdown
## ESCAPE PATH PROTOCOL

**Full Protocol**: See `protocol/modules/ESCAPE_PATH_PROTOCOL.md`

**My Domain-Specific Escape Paths**:
| Situation | My Response |
|-----------|-------------|
| **Blocked by [common blocker]** | [My specific response] |
| **Need [other domain]** | Suggest invoking [specific agent] |
| **Unclear [domain requirement]** | Ask for [specific clarification] |
```

---

**Module Version:** 1.0.0
**Last Updated:** 2025-11-26
