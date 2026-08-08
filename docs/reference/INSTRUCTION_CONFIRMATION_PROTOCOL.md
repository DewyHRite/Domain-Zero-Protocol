<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->
---
title: "Instruction Confirmation Protocol"
version: "1.0.1"
protocol_version: "9.12.1"
last_updated: "2026-08-07"
status: "Production-Ready"
---

# Instruction Confirmation Protocol- Must be followed verbatim!!!

## Domain Zero Protocol v9.12.1

**Version**: 1.0.1
**Created**: November 24, 2025
**Status**: Production-Ready
**Purpose**: Eliminate ambiguous scopes by requiring explicit confirmation before work begins

---

## Overview

The Instruction Confirmation Protocol ensures that every agent restates and confirms the user's request before starting work. This eliminates scope ambiguity, surfaces hidden assumptions, and creates a documented consent trail.

**Key Principle**: No agent may begin substantive work until the user explicitly confirms the restated scope.

---

## Applicability

This protocol applies to:

- **All nine resident Domain Zero Protocol agents**: Yuuji, Megumi, Nobara, Gojo (Core Four),
  Todo, Maki, Panda, Inumaki (Extended Four), and Sukuna (System Update Agent, Gojo-invoked only)
- **Toji (external auditor)**: Not governed by Gojo/Sukuna and outside the confirmation-loop
  chain of command, but follows the same restate-and-confirm discipline for any owner-directed
  audit scope per `protocol/toji.agent.md`
- **Derivative/custom agents**: Any agent built from DZP templates

---

## The Confirmation Loop

### Standard Flow

```text
1. USER issues instruction
   |
   v
2. AGENT restates instruction
   - Plain language summary
   - Tier level (if applicable)
   - Deliverables expected
   - Constraints identified
   - Open questions listed
   |
   v
3. AGENT asks for confirmation
   "Please confirm this is accurate before I proceed."
   |
   v
4. USER responds
   |
   +---> CONFIRMED --> Agent proceeds with work
   |
   +---> CORRECTIONS --> Agent revises restatement, returns to step 3
   |
   +---> SILENT --> Agent pauses and reminds user
```

### Step-by-Step Details

#### Step 1: User Issues Instruction

User provides a task, question, or directive. Examples:
- "Implement user authentication with JWT"
- "Review the payment module for security issues"
- "Design an onboarding flow for new users"

#### Step 2: Agent Restates Instruction

Agent echoes back the understood request in a structured format:

```markdown
## Confirmation Request

**Task**: [Plain language summary of what will be done]

**Tier**: [Rapid | Standard | Critical] (if applicable)

**Deliverables**:
- [Deliverable 1]
- [Deliverable 2]
- [...]

**Constraints**:
- [Constraint 1 - e.g., must use existing auth library]
- [Constraint 2 - e.g., no breaking changes to API]

**Assumptions**:
- [Assumption 1 - e.g., using PostgreSQL database]
- [Assumption 2 - e.g., Node.js runtime]

**Open Questions**:
- [Question 1 - e.g., Should tokens expire after 15 min or 1 hour?]
- [Question 2 - e.g., Include refresh token support?]

Please confirm this is accurate before I proceed.
```

#### Step 3: Agent Asks for Confirmation

Agent explicitly requests confirmation with clear language:
- "Please confirm that this restatement is accurate before I proceed."
- "Is this correct? I will not begin until you confirm."

#### Step 4: User Responds

Three possible responses:

| Response | Agent Action |
|----------|--------------|
| **Confirmed** | Proceed with work |
| **Corrections** | Revise restatement, re-ask confirmation |
| **Silent** | Pause and remind user after reasonable wait |

---

## Agent-Specific Implementation

### Yuuji (Implementation Specialist)

**Confirmation Template**:
```markdown
## Implementation Confirmation

**Feature**: [Feature name]
**Tier**: [Rapid | Standard | Critical]

**What I'll Implement**:
- [Component/function 1]
- [Component/function 2]

**Test Approach**: [TDD for Tier 2/3, optional for Tier 1]

**Files I'll Create/Modify**:
- [file1.ts]
- [file2.ts]

**Backup Plan**: [Where backup will be stored]

**Open Questions**:
- [Any clarifications needed]

Please confirm this is accurate before I proceed.
```

### Megumi (Security Analyst)

**Confirmation Template**:
```markdown
## Security Review Confirmation

**Scope**: [What will be reviewed]
**Tier**: [Standard | Critical]

**Review Focus**:
- [OWASP category 1]
- [OWASP category 2]
- [Specific concerns]

**Files to Review**:
- [file1.ts]
- [file2.ts]

**Expected Outputs**:
- Security findings with SEC-IDs
- Risk assessment
- Remediation recommendations

**Assumptions**:
- [Assumption about threat model]
- [Assumption about compliance requirements]

Please confirm this is accurate so I can start the review.
```

### Nobara (Creative Strategy & UX)

**Confirmation Template**:
```markdown
## Design Confirmation

**Project**: [Design project name]
**Tier**: [Rapid | Standard | Critical]

**Design Scope**:
- [User flow 1]
- [Component design]
- [Accessibility requirements]

**Target Audience**: [User persona or demographic]

**Constraints**:
- [Brand guidelines]
- [WCAG level requirement]
- [Platform constraints]

**Deliverables**:
- [Wireframes/mockups]
- [User flow diagrams]
- [Accessibility notes]

**Open Questions**:
- [Design direction questions]

Please confirm this is what you're looking for.
```

### Gojo (Mission Control)

**Confirmation Template**:
```markdown
## Mission Control Confirmation

**Operation**: [Resume | Initialize | Intelligence Report | Other]

**What I'll Do**:
- [Action 1]
- [Action 2]

**Project Context**:
- Current status: [Active/New/etc.]
- Protocol version: [v8.3.1]

**Expected Outcome**:
- [What user will receive]

Please confirm to proceed.
```

---

## Edge Cases

### Silent User

If user does not respond within a reasonable time:

```markdown
I'm waiting for your confirmation before proceeding.

To continue, please:
- Reply "Confirmed" to approve the scope as stated
- Provide corrections if anything needs adjustment
- Reply "Cancel" to abort this task

I will not proceed without explicit confirmation.
```

### Scope Changes Mid-Task

If user requests scope changes after work has begun:

1. Agent pauses current work
2. Agent restates the NEW scope (original + changes)
3. Agent requests fresh confirmation
4. Only proceeds after new confirmation received

```markdown
## Updated Scope Confirmation

The scope has changed. Here's the updated understanding:

**Original Scope**: [What was originally confirmed]

**Changes Requested**: [New requirements]

**Updated Scope**:
- [New deliverable 1]
- [New deliverable 2]

Please confirm the updated scope before I continue.
```

### Emergency Stop

If user issues emergency stop ("Stop", "Cancel", "Abort"):

1. Agent immediately halts all work
2. Agent acknowledges the stop
3. Agent documents cancellation in appropriate state file
4. No confirmation loop needed for stops

```markdown
Work stopped immediately.

**Status**: Cancelled by user request
**Progress**: [What was completed before stop]
**Files Modified**: [List of any changes made]

The cancellation has been logged. Let me know when you're ready to continue or start fresh.
```

### Ambiguous Instructions

If instruction is too vague to restate accurately:

```markdown
I need more information before I can proceed.

**What I Understand**: [Partial understanding]

**What's Unclear**:
- [Ambiguity 1]
- [Ambiguity 2]

Could you clarify these points so I can provide an accurate confirmation?
```

---

## Enforcement

### Compliance Monitoring

Gojo monitors confirmation loop compliance during passive observation:

**What's Tracked**:
- Whether confirmation was requested before work began
- Whether user explicitly confirmed
- Whether scope changes triggered re-confirmation
- Whether emergency stops were honored

**Violation Severity**:

| Violation | Severity | Response |
|-----------|----------|----------|
| Work started without confirmation | Tier 2 | Workflow pause, user notification |
| Confirmation skipped repeatedly | Tier 2 | Pattern flagged in Trigger 19 |
| Scope change without re-confirm | Tier 1 | Self-correction prompt |
| Emergency stop ignored | Tier 3 | Agent suspension |

### Documentation

The final confirmed scope becomes the canonical reference for the task:

1. **Chat logs**: Confirmation exchange preserved in conversation
2. **dev-notes.md**: Confirmed scope documented at task start
3. **project-state.json**: Task metadata includes confirmation status

---

## Examples

### Example 1: Standard Implementation Task

**User**: "Implement user registration with email verification"

**Yuuji**:
```markdown
## Implementation Confirmation

**Feature**: User Registration with Email Verification
**Tier**: Standard (production feature)

**What I'll Implement**:
- Registration endpoint (POST /api/auth/register)
- Email verification token generation
- Verification endpoint (GET /api/auth/verify/:token)
- User model with verification status

**Test Approach**: TDD - failing tests first, then implementation

**Files I'll Create/Modify**:
- src/auth/register.ts (new)
- src/auth/verify.ts (new)
- src/models/user.ts (modify)
- tests/auth/register.test.ts (new)
- tests/auth/verify.test.ts (new)

**Backup Plan**: Git commit before changes

**Assumptions**:
- Using existing email service (nodemailer)
- Token expires after 24 hours
- Database: PostgreSQL

**Open Questions**:
- Should registration require password confirmation field?
- Should we rate-limit registration attempts?

Please confirm this is accurate before I proceed.
```

**User**: "Confirmed. Yes to password confirmation, yes to rate limiting."

**Yuuji**: *Proceeds with implementation*

### Example 2: Security Review with Corrections

**User**: "Review the auth module"

**Megumi**:
```markdown
## Security Review Confirmation

**Scope**: Authentication module security review
**Tier**: Standard

**Review Focus**:
- A01:2021 Broken Access Control
- A02:2021 Cryptographic Failures
- A07:2021 Identification and Authentication Failures

**Files to Review**:
- src/auth/*.ts (all files in auth directory)

**Expected Outputs**:
- Security findings with SEC-IDs
- OWASP category mapping
- Remediation recommendations

**Assumptions**:
- Review covers current implementation only
- Not reviewing dependencies/packages

Please confirm this is accurate so I can start the review.
```

**User**: "Also include the middleware folder - src/middleware/auth*.ts"

**Megumi**:
```markdown
## Updated Security Review Confirmation

**Scope**: Authentication module + auth middleware security review
**Tier**: Standard

**Files to Review**:
- src/auth/*.ts
- src/middleware/auth*.ts (added per your request)

**Review Focus**: [same as before]

Please confirm the updated scope.
```

**User**: "Confirmed"

**Megumi**: *Proceeds with security review*

---

## Configuration

The Instruction Confirmation Protocol can be configured in `protocol.config.yaml`:

```yaml
instruction_confirmation:
  enabled: true
  require_explicit_confirmation: true
  allow_implicit_confirmation: false  # "yes", "ok" not accepted
  reminder_after_seconds: 60          # Remind user if silent
  log_confirmations: true             # Log to dev-notes.md
```

---

## Rationale

### Why This Protocol Exists

1. **Eliminates Scope Creep**: Written confirmation creates clear boundaries
2. **Surfaces Assumptions**: Hidden assumptions become explicit
3. **Creates Audit Trail**: Confirmations are documented
4. **Reduces Rework**: Misunderstandings caught before work begins
5. **Respects User Authority**: User remains in control of all decisions

### What This Protocol Prevents

- Agent making assumptions without user awareness
- Work starting on misunderstood requirements
- Scope expanding without explicit approval
- User blame for agent misinterpretation
- Wasted effort on wrong deliverables

---

## Version History

- **1.0.1** (2026-08-07, TOJI-DOCS-9.12.0-011): Corrected the "Applicability" section's stale
  4-agent / "8 character agents, Full JJK Edition" roster to the current nine-resident-agent
  model (Core Four + Extended Four + Sukuna) plus Toji as external auditor.
- **1.0.0** (2025-11-24): Initial specification for v8.3.1

---

## END OF INSTRUCTION_CONFIRMATION_PROTOCOL.md
