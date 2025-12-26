<!-- [CORE FILE] - Domain Zero Protocol v8.10.0 -->
# DZP Rules of Engagement (ROE) - Post-Compaction Recovery
## Reinforce DZP Protocol After Context Compaction

**Version**: 1.0.0
**Agent(s)**: ALL (gojo, yuuji, megumi, nobara, todo, maki, panda, inumaki, sukuna)
**Category**: Protocol Reinforcement
**Risk Level**: Low (no code execution)
**Token Efficiency**: High token savings (prevents repeated manual explanations)

---

## Purpose

After context compaction in Claude Code, agents lose critical DZP protocol context including agent roles, restrictions, tier workflows, and parallel patterns. Users waste time manually re-explaining these rules.

This skill provides a single-command recovery mechanism that:
- Outputs complete DZP protocol summary
- Updates state files to track compaction recoveries
- Runs protocol validation
- Presents actionable quick reference

**Use this skill immediately after context compaction to restore full DZP context.**

---

## Prerequisites

**BEFORE using this skill, ensure**:
- [ ] Context compaction has occurred (agent behavior shows confusion about DZP rules)
- [ ] `.protocol-state/project-state.json` exists
- [ ] User has confirmed need for ROE reinforcement

**ESCAPE PATH**: If prerequisites cannot be met:
1. If project-state.json is missing: Create minimal version with defaults
2. If user hasn't confirmed: Ask via AskUserQuestion whether to proceed
3. If no compaction detected: Output ROE anyway (no harm in refreshing)

---

## Quick Invocation

```bash
skill: "dzp-roe"

Context: Just recovered from compaction, need DZP rules refresher
```

Or via slash command:
```bash
/dzp-roe
```

---

## Workflow Steps

### Step 1: Read Current Project State

**Action**: Read `.protocol-state/project-state.json` to get current project context

**Tools**: Read

**ESCAPE PATH** if blocked:
- If file doesn't exist: Use defaults (project_name="Unknown", current_mission="Not Set")
- If file is corrupted: Ask user for project name and mission
- Continue with skill regardless (ROE output doesn't strictly require project state)

---

### Step 2: Output DZP Protocol Summary

**Action**: Output comprehensive DZP Rules of Engagement

**Tools**: None (direct output)

**Template**:
```markdown
## 🎯 DZP RULES OF ENGAGEMENT (v8.10.0)

### 9-Agent System

| Agent | Role | Specialization |
|-------|------|----------------|
| **Gojo** | Mission Control | Project lifecycle, protocol guardian, coordination |
| **Yuuji** | Implementation | Test-first development, ALL code changes |
| **Megumi** | Security | OWASP Top 10 reviews, threat modeling |
| **Nobara** | Creative/UX | User experience, product vision, accessibility |
| **Todo** | Database | Schema design, migrations, query optimization |
| **Maki** | Performance | Profiling, bundle analysis, zero-overhead optimization |
| **Panda** | Build/CI | CI/CD pipelines, Docker, GitHub Actions |
| **Inumaki** | API | REST/GraphQL/WebSocket design, OpenAPI |
| **Sukuna** | System Updates | Protocol updates, adversarial reviews |

### Critical Restrictions (MUST FOLLOW)

**Implementation Routing**:
- ❌ **Nobara, Todo, Maki, Panda, Inumaki CANNOT write code directly**
- ✅ **These 5 agents MUST route implementation through Yuuji** via @implementation handoff
- ✅ **Only Yuuji, Gojo, and Sukuna have Edit/Bash tools for code changes**

**Domain Record Access**:
- ✅ **Gojo + Sukuna ONLY** have full READ/WRITE access to `.dzp-domain/domain.record.md`
- ❌ **All other 7 agents** (yuuji, megumi, nobara, todo, maki, panda, inumaki) are DENIED

**Agent File Protection**:
- ❌ **No non-Gojo agent** may edit another agent's `.agent.md` file
- ✅ **READ-ONLY access** to all agent definition files for study
- ✅ **Changes require** User direct edit OR Gojo coordination with explicit permission

**Tier Validation**:
- ✅ **Tier 2 (Standard)** is DEFAULT for all features
- ✅ **Tier 3 (Critical)** required for auth, payments, sensitive data
- ✅ **Tier 1 (Rapid)** only for prototypes, explicitly requested by user

### Parallel Workflow Patterns

**When to use PARALLEL**:
- Independent agent tasks (e.g., Megumi review + Yuuji tests simultaneously)
- Multiple file reads/searches
- Non-dependent operations
- **How**: Single message with multiple Task calls

**When to use SEQUENTIAL**:
- Dependent operations (e.g., Write file BEFORE git commit)
- Operations where one requires output of another
- **How**: Chain with && (e.g., `git add . && git commit && git push`)

**State Update Rules**:
- ✅ **Always update** `project-state.json` after significant work
- ✅ **Gojo/Sukuna log** strategic decisions to `domain.record.md`
- ✅ **Yuuji logs** implementation notes to `dev-notes.md`
- ✅ **Megumi logs** security findings to `security-review.md`

### Current Project State

**Project**: {project_name}
**Current Mission**: {current_mission}
**Tech Stack**: {tech_stack}
**Active Tier**: {current_tier}
**Last Session**: {last_session_timestamp}

---

## ✅ Protocol Validation Results

{validation_results}

---

## 📚 Quick Reference

**Agent Invocation Patterns**:
```bash
# Mission Control
"Read protocol/gojo.agent.md and brief me on project status"

# Implementation (all code changes)
"Read protocol/yuuji.agent.md and implement [feature] with tier 2"

# Security Review
"Read protocol/megumi.agent.md and review [component] for OWASP Top 10"

# UX Design
"Read protocol/nobara.agent.md and design [flow] with WCAG 2.2 compliance"

# Database
"Read protocol/todo.agent.md and design schema for [feature]"

# Performance
"Read protocol/maki.agent.md and optimize [component]"

# Build/CI
"Read protocol/panda.agent.md and configure CI/CD for [project]"

# API Design
"Read protocol/inumaki.agent.md and design REST API for [feature]"
```

**Parallel Invocation Example**:
```bash
# Launch security review + implementation in parallel
[Single message with two Task calls]:
- Task 1: megumi review authentication
- Task 2: yuuji implement tests for authentication
```

**State Update Example**:
```bash
# After implementing feature
1. Yuuji updates dev-notes.md with implementation notes
2. Gojo updates project-state.json with mission progress
3. Megumi updates security-review.md if security-relevant
```

---

**Recovery complete. All DZP rules reinforced. Ready to resume work with full protocol context.**
```

**Fill Template Variables**:
- `{project_name}`: From project-state.json → project_metadata.name
- `{current_mission}`: From project-state.json → current_mission.description
- `{tech_stack}`: From project-state.json → project_metadata.tech_stack
- `{current_tier}`: From session state or default to "Tier 2 (Standard)"
- `{last_session_timestamp}`: From project-state.json → session_metadata.last_active
- `{validation_results}`: From Step 5 validation output

---

### Step 3: Update Project State (Compaction Recovery Tracking)

**Action**: Update `.protocol-state/project-state.json` with compaction recovery metadata

**Tools**: Read, Edit

**Schema Addition**:
```json
{
  "compaction_recovery": {
    "last_recovery_timestamp": "2025-12-25T00:00:00Z",
    "recovery_count": 1,
    "recovery_history": [
      {
        "timestamp": "2025-12-25T00:00:00Z",
        "invoked_by": "user|gojo|yuuji|megumi|nobara|todo|maki|panda|inumaki|sukuna",
        "context": "Optional context string from invocation"
      }
    ]
  }
}
```

**ESCAPE PATH** if blocked:
- If project-state.json doesn't exist: Create minimal version
- If JSON is corrupted: Skip this step, log warning
- If Edit fails: Use Write tool to overwrite (last resort)

---

### Step 4: Log to Domain Record (Gojo/Sukuna ONLY)

**Action**: IF current agent is Gojo or Sukuna, append ROE invocation to `.dzp-domain/domain.record.md`

**Tools**: Read, Edit (Gojo/Sukuna only)

**Log Format**:
```markdown
---
## DZP ROE Invocation - {timestamp}
**Invoked By**: {agent_name}
**Context**: {optional_context}
**Recovery Count**: {total_recoveries}

Post-compaction recovery initiated. DZP rules reinforced for all agents.
```

**ESCAPE PATH** if blocked:
- If agent is NOT Gojo or Sukuna: **SKIP THIS STEP** (access denied, this is expected)
- If domain.record.md doesn't exist: Create it (Gojo/Sukuna only)
- If file is too large: Trigger rotation via `scripts/domain-record-rotate.py --rotate`

---

### Step 5: Update Dev Notes (Continuity)

**Action**: Append compaction recovery note to `.protocol-state/dev-notes.md`

**Tools**: Read, Edit

**Note Format**:
```markdown
---
## {timestamp} - Context Compaction Recovery
**Tool**: `/dzp-roe` (DZP Rules of Engagement)
**Status**: DZP protocol rules reinforced

All agents restored to full DZP context. Ready to resume work.

**Active Work** (from before compaction):
{extract current tasks from recent dev-notes entries}
```

**ESCAPE PATH** if blocked:
- If dev-notes.md doesn't exist: Create it
- If file is too large (>25k chars): Trigger rotation via `scripts/file-rotate.py --file dev-notes --rotate`
- Continue regardless

---

### Step 6: Run Protocol Validation

**Action**: Execute `scripts/validate-protocol.py --check` to verify protocol integrity

**Tools**: Bash

**Command**:
```bash
python scripts/validate-protocol.py --check 2>&1
```

**Parse Output**:
- ✅ All checks passed: "Protocol validation: PASSED"
- ⚠️ Warnings detected: "Protocol validation: PASSED (with warnings)"
- ❌ Errors detected: "Protocol validation: FAILED - {error_count} errors"

**Validation Checks**:
1. tier-defaults.yaml integrity
2. file-classifications.json integrity
3. All 9 agent .agent.md files present
4. Domain record size (rotation needed if >25k chars)
5. REQUIRED_FILES manifest compliance

**ESCAPE PATH** if blocked:
- If script doesn't exist: Skip validation, output "Validation skipped (script not found)"
- If script fails: Output error but continue with ROE (non-blocking)
- If Python not available: Skip validation

---

### Step 7: Verify Agent Compliance

**Action**: Check that all 9 agent files are present and have correct version

**Tools**: Glob, Read

**Checks**:
```bash
# Verify all 9 agents exist
ls protocol/*.agent.md | wc -l  # Should be 9

# Verify Gojo/Sukuna domain record access documentation
grep -l "domain.record.md" protocol/gojo.agent.md protocol/sukuna.agent.md

# Verify implementation restrictions
grep -l "CANNOT use edit" protocol/nobara.agent.md protocol/todo.agent.md protocol/maki.agent.md protocol/panda.agent.md protocol/inumaki.agent.md
```

**Output**:
```markdown
### Agent Compliance Status
✅ 9 agent files present
✅ Gojo domain record access: DOCUMENTED
✅ Sukuna domain record access: DOCUMENTED
✅ Implementation restrictions (5 agents): DOCUMENTED
✅ Tier validation sections: PRESENT (all 9 agents)
```

**ESCAPE PATH** if blocked:
- If agents missing: List which ones, flag as WARNING
- If documentation missing: Flag as WARNING but continue
- Compliance check is informational, not blocking

---

### Step 8: Output Parallel Workflow Guidance

**Action**: Provide concrete examples of parallel vs sequential workflows

**Tools**: None (direct output)

**Output**:
```markdown
## 🚀 Parallel Workflow Guidance

### PARALLEL Pattern (Use for Independent Tasks)

**Example 1: Security Review + Testing**
```
[Single message with two Task calls]:

Task 1 - Megumi security review:
"Read protocol/megumi.agent.md and review authentication for OWASP Top 10"

Task 2 - Yuuji testing:
"Read protocol/yuuji.agent.md and write tests for authentication"
```

**Example 2: Multiple Agent Consultations**
```
[Single message with three Task calls]:

Task 1: "Read protocol/todo.agent.md and design database schema for user management"
Task 2: "Read protocol/inumaki.agent.md and design REST API for user CRUD"
Task 3: "Read protocol/nobara.agent.md and design user onboarding flow"
```

### SEQUENTIAL Pattern (Use for Dependent Tasks)

**Example 1: Git Workflow**
```bash
# CORRECT (sequential with &&)
git add . && git commit -m "feat: add authentication" && git push

# WRONG (parallel would fail)
git add . & git commit -m "..." & git push  # DON'T DO THIS
```

#### Example 2: File Creation Then Read
```text
Step 1: Write new file
Step 2: Read file to verify (depends on Step 1 completing)
```

### When to Use Each

**PARALLEL**:
- Agent tasks with no dependencies
- Multiple file reads/searches
- Independent analysis/reviews
- Saves time: 2 agents work simultaneously

**SEQUENTIAL**:
- Git operations (add → commit → push)
- File operations (write → read → verify)
- Dependent data (fetch → process → save)
- Maintains order: Step 2 needs Step 1 output
```

---

### Step 9: Prompt Agent to Continue Tasks with Proper DZP Workflow

**Action**: Remind agent to continue previous tasks using correct DZP patterns

**Tools**: None (direct output)

**Output**:
```markdown
## 🎯 Ready to Resume Work

**DZP protocol rules have been reinforced.** You can now continue your previous tasks using proper workflows:

### If You Are Implementing Code:
- ✅ **Route through Yuuji** if you are Nobara, Todo, Maki, Panda, or Inumaki
- ✅ Use `@implementation` handoff pattern:
  ```
  @implementation [detailed specification]

  Read protocol/yuuji.agent.md and implement [feature/fix] with:
  - [Requirement 1]
  - [Requirement 2]
  - Tier: [1/2/3]
  ```

### If You Are Analyzing/Designing:
- ✅ **Continue with your specialization** (Security, UX, Database, API, Performance)
- ✅ Update appropriate state files:
  - Megumi → `security-review.md`
  - Yuuji → `dev-notes.md`
  - Gojo/Sukuna → `domain.record.md`

### If Multiple Agents Are Needed:
- ✅ **Use parallel invocation** for independent tasks (single message, multiple Task calls)
- ✅ **Use sequential** for dependent operations (&&)

### Check Previous Context:
Review `dev-notes.md` (last 10 entries) for context on what was being worked on before compaction:

{extract_last_10_dev_notes_entries}

---

**What should you continue working on?**
{prompt_user_or_infer_from_context}
```

**Decision Logic**:
1. If `dev-notes.md` has recent entries: Extract last task and suggest continuing it
2. If user provided context in `/dzp-roe [context]`: Use that context to prompt next action
3. If no context available: Ask user "What would you like to work on now?"

**ESCAPE PATH** if blocked:
- If dev-notes.md doesn't exist or is empty: Skip extraction, ask user for next task
- If cannot infer task: Default to asking user "Ready to resume. What should we work on?"

---

## Output Summary

After completing all 9 steps, the skill provides:
1. ✅ Complete DZP protocol summary (9 agents, restrictions, patterns)
2. ✅ Updated project-state.json (compaction recovery tracking)
3. ✅ Logged to domain.record.md (Gojo/Sukuna only - learning patterns)
4. ✅ Updated dev-notes.md (continuity note for active work)
5. ✅ Protocol validation results (integrity checks)
6. ✅ Agent compliance verification (all 9 agents documented correctly)
7. ✅ Parallel workflow guidance (concrete examples)
8. ✅ Quick reference card (agent invocation patterns)
9. ✅ **Task continuation prompt** (reminds agent to continue previous work with proper DZP workflow)

**Result**: Agents fully restored to DZP context AND prompted to continue tasks using proper workflow patterns. User can resume work without repeating protocol explanations.

---

## Changelog

### 1.0.0 (2025-12-25)
- Initial release for v8.10.0
- 9-step workflow for post-compaction recovery
- State tracking (project-state.json, domain.record.md, dev-notes.md)
- Protocol validation integration
- Parallel workflow guidance
- Task continuation prompting (Step 9: guides agent to resume previous work with proper DZP patterns)

---

**Status**: Production-Ready
**Maintenance**: Update when DZP protocol changes (new agents, new restrictions, etc.)
