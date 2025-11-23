# Agent Handoff Specification
## Domain Zero Protocol v8.0.0

**Version**: 1.0.0
**Created**: November 18, 2025
**Status**: Production-Ready
**Purpose**: Define agent-to-agent context transfer mechanisms for .agent.md format

---

## Table of Contents

- [Overview](#overview)
- [Handoff Architecture](#handoff-architecture)
- [YAML Frontmatter Structure](#yaml-frontmatter-structure)
- [Handoff Triggers](#handoff-triggers)
- [Context Transfer](#context-transfer)
- [Implementation Patterns](#implementation-patterns)
- [Agent-Specific Handoffs](#agent-specific-handoffs)
- [Security Considerations](#security-considerations)
- [Testing Handoffs](#testing-handoffs)

---

## Overview

**Agent handoffs** enable seamless context transfer between specialized agents in Domain Zero Protocol. When implemented correctly, handoffs:

- ✅ Preserve complete context across agent transitions
- ✅ Eliminate redundant information gathering
- ✅ Maintain workflow continuity
- ✅ Enable tier-aware processing
- ✅ Support security review orchestration

**Key Principle**: Handoffs are **declarative** and **context-rich** - the receiving agent gets everything needed to continue the workflow without manual context rebuilding.

---

## Handoff Architecture

### Flow Diagram

```
User Request
     ↓
┌────────────────┐
│  YUUJI (Impl)  │
│  Implements    │
│  feature       │
└────────┬───────┘
         │
         │ @user-review tag
         ↓
┌────────────────┐
│  USER REVIEW   │
│  Approves impl │
└────────┬───────┘
         │
         │ Handoff Trigger: @security-review
         ↓
┌────────────────┐
│ GOJO (Mission  │
│  Control)      │
│  Orchestrates  │
└────────┬───────┘
         │
         │ Context: files, tier, scope
         ↓
┌────────────────┐
│ MEGUMI (Sec)   │
│ Security audit │
└────────┬───────┘
         │
         │ @approved or @remediation-required
         ↓
    [Complete or loop back to Yuuji]
```

### Key Components

1. **Trigger Keywords**: `@agent-name` or `@action-keyword`
2. **Context Payload**: Structured data passed between agents
3. **Handoff Orchestrator**: GOJO coordinates all transitions
4. **State Tracking**: `.protocol-state/project-state.json` records handoffs

---

## YAML Frontmatter Structure

### Required Handoff Section

Every .agent.md file MUST include a `handoffs` section in YAML frontmatter:

```yaml
---
target: vscode
name: "Agent Name"
# ... other fields ...

handoffs:
  - agent: target_agent_name
    trigger: "@trigger-keyword"
    context:
      - context_field_1
      - context_field_2
      - context_field_3
  - agent: another_agent
    trigger: "@another-trigger"
    context:
      - different_context
---
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent` | string | ✅ | Target agent name (lowercase: yuuji, megumi, nobara, gojo) |
| `trigger` | string | ✅ | Keyword that initiates handoff (must start with @) |
| `context` | array | ✅ | List of context fields to pass to target agent |

### Example: Yuuji's Handoffs

```yaml
handoffs:
  - agent: megumi
    trigger: "@security-review"
    context:
      - files_modified
      - tier_level
      - implementation_scope
      - test_coverage
  - agent: gojo
    trigger: "@user-review"
    context:
      - implementation_complete
      - backup_location
      - rollback_plan
```

**Interpretation**:
- When Yuuji tags `@security-review`, Megumi receives context about what files changed, what tier this is, etc.
- When Yuuji tags `@user-review`, Gojo receives implementation status and backup details

---

## Handoff Triggers

### Standard Trigger Keywords

| Trigger | Source Agent | Target Agent | Purpose |
|---------|--------------|--------------|---------|
| `@security-review` | Yuuji | Megumi | Request security audit (Tier 2/3) |
| `@user-review` | Yuuji | Gojo | Request user approval before security review |
| `@remediation-required` | Megumi | Yuuji | Security issues found, fix required |
| `@re-review` | Yuuji | Megumi | Fixes applied, verification requested |
| `@approved` | Megumi | Gojo | Security review passed, feature complete |
| `@brief-implementation` | Gojo | Yuuji | Mission Control provides implementation briefing |
| `@brief-security` | Gojo | Megumi | Mission Control provides security briefing |
| `@brief-design` | Gojo | Nobara | Mission Control provides design briefing |
| `@implement-design` | Nobara | Yuuji | Design specs ready for implementation |
| `@security-ux-review` | Nobara | Megumi | Security review needed for UX flows |
| `@escalate` | Any | Gojo | Critical issue requiring Mission Control intervention |

### Custom Triggers

Projects can define custom triggers in `.protocol-state/custom-triggers.json`:

```json
{
  "custom_triggers": {
    "@performance-review": {
      "source": "yuuji",
      "target": "megumi",
      "context": ["benchmark_results", "profiling_data"],
      "description": "Request performance analysis"
    }
  }
}
```

---

## Context Transfer

### Context Field Types

#### 1. **File References**

```yaml
context:
  - files_modified     # Array of file paths changed
  - files_created      # Array of new files
  - files_deleted      # Array of removed files
```

**Example Payload**:
```json
{
  "files_modified": [
    "src/auth/login.ts",
    "src/auth/jwt.ts"
  ],
  "files_created": [
    "src/auth/__tests__/login.test.ts"
  ],
  "files_deleted": []
}
```

#### 2. **Tier Information**

```yaml
context:
  - tier_level         # "rapid", "standard", or "critical"
  - tier_requirements  # Specific requirements for this tier
```

**Example Payload**:
```json
{
  "tier_level": "critical",
  "tier_requirements": {
    "tests": ["unit", "integration", "e2e"],
    "security_review": "enhanced",
    "performance_benchmarks": true
  }
}
```

#### 3. **Implementation Scope**

```yaml
context:
  - implementation_scope   # High-level description
  - feature_requirements   # Detailed requirements
  - acceptance_criteria    # Success criteria
```

**Example Payload**:
```json
{
  "implementation_scope": "JWT-based authentication system",
  "feature_requirements": [
    "Access token generation (15min expiry)",
    "Refresh token handling (7d expiry)",
    "Token validation middleware",
    "Secure cookie storage"
  ],
  "acceptance_criteria": [
    "All tests pass",
    "No OWASP Top 10 violations",
    "Token expiry enforced",
    "Secure storage verified"
  ]
}
```

#### 4. **Test Coverage**

```yaml
context:
  - test_coverage       # Coverage percentage
  - test_types          # Which test types ran
  - test_results        # Pass/fail summary
```

**Example Payload**:
```json
{
  "test_coverage": {
    "statements": 95,
    "branches": 88,
    "functions": 100,
    "lines": 94
  },
  "test_types": ["unit", "integration"],
  "test_results": {
    "total": 24,
    "passed": 24,
    "failed": 0,
    "skipped": 0
  }
}
```

#### 5. **Security Findings**

```yaml
context:
  - security_findings   # Array of SEC-IDs
  - remediation_required # Fixes needed
  - sec_ids             # Security issue IDs
  - verification_criteria # How to verify fixes
```

**Example Payload**:
```json
{
  "security_findings": [
    {
      "sec_id": "SEC-001",
      "severity": "HIGH",
      "category": "A02:2021 - Cryptographic Failures",
      "description": "JWT secret stored in plaintext",
      "location": "src/auth/jwt.ts:12",
      "recommendation": "Use environment variables for secrets"
    }
  ],
  "remediation_required": true,
  "sec_ids": ["SEC-001"],
  "verification_criteria": [
    "Secret moved to .env file",
    "Hardcoded secret removed from source",
    "Environment variable validated at startup"
  ]
}
```

#### 6. **Project State**

```yaml
context:
  - project_state       # Current project status
  - current_tasks       # Active tasks
  - protocol_updates    # Recent protocol changes
```

**Example Payload**:
```json
{
  "project_state": {
    "status": "ACTIVE",
    "active_features": 2,
    "pending_reviews": 1,
    "open_security_issues": 0
  },
  "current_tasks": [
    "Implement password reset flow",
    "Add email verification"
  ],
  "protocol_updates": [
    "v8.0.0: Agent file format changed to .agent.md"
  ]
}
```

---

## Implementation Patterns

### Pattern 1: Sequential Handoff (Yuuji → Megumi)

**Use Case**: Standard Tier 2 implementation with security review

**Flow**:
```markdown
1. Yuuji implements feature
2. Yuuji tags @user-review in dev-notes.md
3. User reviews and approves
4. Yuuji outputs: "Ready for security review. Invoke Megumi..."
5. User manually invokes Megumi (prompted handoff)
6. Gojo passes context to Megumi
7. Megumi reviews with full context
8. Megumi tags @approved or @remediation-required
```

**Yuuji's .agent.md**:
```yaml
handoffs:
  - agent: megumi
    trigger: "@security-review"
    context:
      - files_modified
      - tier_level
      - implementation_scope
      - test_coverage
```

**Gojo's Orchestration**:
```markdown
When user invokes Megumi after Yuuji's @user-review:
1. Read dev-notes.md for implementation scope
2. Extract files_modified from git diff
3. Identify tier_level from Yuuji's tags
4. Calculate test_coverage from test results
5. Pass complete context to Megumi
```

### Pattern 2: Escalation Handoff (Any → Gojo)

**Use Case**: Critical issue requires Mission Control intervention

**Flow**:
```markdown
1. Agent encounters critical issue (e.g., CLAUDE.md violation attempt)
2. Agent tags @escalate
3. Gojo immediately receives alert
4. Gojo assesses situation
5. Gojo takes corrective action or notifies user
```

**Any Agent's .agent.md**:
```yaml
handoffs:
  - agent: gojo
    trigger: "@escalate"
    context:
      - violation_type
      - severity
      - agent_name
      - timestamp
```

### Pattern 3: Briefing Handoff (Gojo → Agents)

**Use Case**: Mission Control provides project context to agents

**Flow**:
```markdown
1. User invokes Gojo: "Read gojo.agent.md"
2. Gojo selects Option 1 (Resume Current Project)
3. Gojo loads project-state.json and dev-notes.md
4. Gojo creates individualized briefings for each agent
5. When user invokes agent, Gojo's brief is available
```

**Gojo's .agent.md**:
```yaml
handoffs:
  - agent: yuuji
    trigger: "@brief-implementation"
    context:
      - project_state
      - current_tasks
      - tier_guidance
      - protocol_updates
```

---

## Agent-Specific Handoffs

### Yuuji (Implementation Specialist)

**Receives handoffs from**:
- **Megumi**: `@remediation-required` (fix security issues)
- **Gojo**: `@brief-implementation` (project context)
- **Nobara**: `@implement-design` (design specs)

**Initiates handoffs to**:
- **Megumi**: `@security-review` (request audit)
- **Gojo**: `@user-review` (request approval)

**Context provided to Megumi**:
```yaml
context:
  - files_modified
  - tier_level
  - implementation_scope
  - test_coverage
```

### Megumi (Security Analyst)

**Receives handoffs from**:
- **Yuuji**: `@security-review` (audit request)
- **Yuuji**: `@re-review` (verify fixes)
- **Gojo**: `@brief-security` (project context)
- **Nobara**: `@security-ux-review` (security review for UX flows)

**Initiates handoffs to**:
- **Yuuji**: `@remediation-required` (issues found)
- **Gojo**: `@approved` (review passed)
- **Gojo**: `@escalate` (critical findings)

**Context provided to Yuuji**:
```yaml
context:
  - security_findings
  - remediation_required
  - sec_ids
  - verification_criteria
```

### Nobara (Creative Strategy & UX)

**Receives handoffs from**:
- **Gojo**: `@brief-design` (project vision)

**Initiates handoffs to**:
- **Yuuji**: `@implement-design` (specs ready)
- **Megumi**: `@security-ux-review` (sensitive data flows)

**Context provided to Yuuji**:
```yaml
context:
  - design_specifications
  - mockups
  - user_flows
  - accessibility_requirements
```

### Gojo (Mission Control)

**Receives handoffs from**:
- **Any agent**: `@escalate` (critical issues)
- **Yuuji**: `@user-review` (implementation complete)
- **Megumi**: `@approved` (security review passed)

**Initiates handoffs to**:
- **Yuuji**: `@brief-implementation`
- **Megumi**: `@brief-security`
- **Nobara**: `@brief-design`

**Context provided varies by target agent** (see individual agent sections above)

---

## Security Considerations

### 1. **Context Sanitization**

**Rule**: Never pass sensitive data in context payloads

**Prohibited**:
```json
{
  "user_password": "plaintextpassword123",  // ❌ NEVER
  "api_key": "sk_live_123456",              // ❌ NEVER
  "database_credentials": { ... }           // ❌ NEVER
}
```

**Correct**:
```json
{
  "files_modified": ["src/auth/password.ts"],
  "security_concerns": ["Password hashing implementation"],
  "sec_ids": ["SEC-001: Review hashing algorithm"]
}
```

### 2. **Authorization Hierarchy**

**Handoff permissions must respect agent authority levels**:

| Agent | Can Initiate Handoffs To | Cannot Initiate To |
|-------|---------------------------|---------------------|
| Yuuji | Megumi, Gojo | - |
| Megumi | Yuuji, Gojo | - |
| Nobara | Yuuji, Megumi | - |
| Gojo | All agents | - |

**Note**: All agents can escalate to Gojo, but only Gojo can modify CLAUDE.md (with user authorization).

### 3. **Context Integrity**

**Rule**: Context payloads must be immutable during transfer

- ✅ Context is read-only once generated
- ✅ Receiving agent cannot modify handoff context
- ✅ Context is logged in project-state.json for audit trail

---

## Testing Handoffs

### Unit Testing

**Test each handoff trigger individually**:

```yaml
# Test: Yuuji → Megumi security review handoff
Given: Yuuji completes Tier 2 implementation
When: Yuuji tags @security-review
Then: Megumi receives:
  - files_modified: ["src/auth/login.ts"]
  - tier_level: "standard"
  - implementation_scope: "User authentication"
  - test_coverage: { statements: 95 }
```

### Integration Testing

**Test complete workflow with handoffs**:

```markdown
Scenario: Full Tier 2 workflow
1. Gojo briefs Yuuji on project context
2. Yuuji implements feature
3. Yuuji tags @user-review
4. User approves
5. Yuuji outputs instruction for Megumi invocation
6. User invokes Megumi
7. Gojo passes context to Megumi
8. Megumi reviews and tags @approved
9. Workflow complete
```

**Success Criteria**:
- ✅ All context fields present at each handoff
- ✅ No manual context reconstruction required
- ✅ Workflow completes without errors
- ✅ All handoffs logged in project-state.json

### Validation Script

**Run handoff validation**:

```powershell
# Validate handoff configuration
./scripts/validate-agents.ps1

# Check:
# - All agents have handoffs defined in YAML
# - Trigger keywords follow @ convention
# - Context fields are documented
# - No circular handoff dependencies
```

---

## Example: Complete Handoff Flow

### Scenario: Tier 2 JWT Authentication Implementation

#### Step 1: Yuuji Implements

```markdown
## Yuuji's Actions:
1. Creates src/auth/jwt.ts
2. Writes tests in src/auth/__tests__/jwt.test.ts
3. All tests pass (24/24)
4. Documents in dev-notes.md
5. Tags @user-review
```

#### Step 2: User Review

```markdown
## User Actions:
1. Reviews implementation
2. Approves implementation
3. Yuuji outputs: "Ready for security review. Please invoke Megumi..."
```

#### Step 3: Handoff Context Preparation

```json
// Gojo prepares context
{
  "files_modified": [
    "src/auth/jwt.ts",
    "src/auth/middleware/validate-token.ts"
  ],
  "files_created": [
    "src/auth/__tests__/jwt.test.ts"
  ],
  "tier_level": "standard",
  "implementation_scope": "JWT-based authentication with access/refresh tokens",
  "test_coverage": {
    "statements": 95,
    "branches": 88,
    "functions": 100,
    "lines": 94
  },
  "test_results": {
    "total": 24,
    "passed": 24,
    "failed": 0
  }
}
```

#### Step 4: Megumi Reviews

```markdown
## Megumi's Actions:
1. Receives full context (no manual searching needed)
2. Reviews files_modified against OWASP Top 10
3. Finds SEC-001: JWT secret in plaintext
4. Documents in security-review.md
5. Tags @remediation-required
```

#### Step 5: Return Handoff to Yuuji

```json
// Megumi's context to Yuuji
{
  "security_findings": [
    {
      "sec_id": "SEC-001",
      "severity": "HIGH",
      "category": "A02:2021 - Cryptographic Failures",
      "description": "JWT secret stored in plaintext",
      "location": "src/auth/jwt.ts:12",
      "recommendation": "Use environment variables for secrets"
    }
  ],
  "remediation_required": true,
  "sec_ids": ["SEC-001"],
  "verification_criteria": [
    "Secret moved to .env file",
    "Hardcoded secret removed from source",
    "Environment variable validated at startup"
  ]
}
```

#### Step 6: Yuuji Fixes and Re-submits

```markdown
## Yuuji's Actions:
1. Receives context with SEC-001 details
2. Moves JWT secret to .env file
3. Updates code to use process.env.JWT_SECRET
4. Adds validation at startup
5. Tags @re-review
```

#### Step 7: Megumi Verifies

```markdown
## Megumi's Actions:
1. Receives verification_criteria from context
2. Verifies each criterion met
3. Confirms fix effective
4. Tags @approved
```

#### Step 8: Workflow Complete

```markdown
## Gojo's Actions:
1. Receives @approved from Megumi
2. Updates project-state.json:
   - feature status: "COMPLETE"
   - security_reviewed: true
   - open_security_issues: 0
3. Logs handoff history for Trigger 19 intelligence
```

---

## Appendix: Handoff Event Schema

### JSON Schema for Handoff Events

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Domain Zero Handoff Event",
  "type": "object",
  "required": ["event_id", "timestamp", "source_agent", "target_agent", "trigger", "context"],
  "properties": {
    "event_id": {
      "type": "string",
      "description": "Unique identifier for this handoff event"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO-8601 timestamp when handoff occurred"
    },
    "source_agent": {
      "type": "string",
      "enum": ["yuuji", "megumi", "nobara", "gojo"],
      "description": "Agent initiating the handoff"
    },
    "target_agent": {
      "type": "string",
      "enum": ["yuuji", "megumi", "nobara", "gojo"],
      "description": "Agent receiving the handoff"
    },
    "trigger": {
      "type": "string",
      "pattern": "^@[a-z-]+$",
      "description": "Trigger keyword (must start with @)"
    },
    "context": {
      "type": "object",
      "description": "Context payload (schema varies by handoff type)"
    },
    "status": {
      "type": "string",
      "enum": ["pending", "completed", "failed"],
      "description": "Handoff execution status"
    }
  }
}
```

---

## Version History

- **1.0.0** (2025-11-18): Initial specification for v8.0.0 .agent.md format

---

**END OF HANDOFF_SPECIFICATION.md**
