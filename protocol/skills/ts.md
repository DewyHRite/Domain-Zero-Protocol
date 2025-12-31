<!-- [CORE FILE] - Domain Zero Protocol v8.12.0 -->
# TS (Tier Shift) - Troubleshooting Tier Management
## Context-Aware Bug Resolution with Hybrid Escalation

**Version**: 1.1.0 (PATCH-STATE-001)
**Agent(s)**: Gojo (Mission Control)
**Category**: Troubleshooting & Diagnostics
**Risk Level**: Medium (state writes, agent coordination)
**Token Efficiency**: High (prevents repeated debugging workflows)

---

## Purpose

5-tier hybrid troubleshooting system for systematic bug resolution with automatic escalation. User selects initial tier based on bug severity, with auto-escalation after failed attempts.

**Integrated Troubleshooting Tracker** (v1.0.0, PATCH-STATE-001):
- All /ts commands automatically track sessions in `project-state.json::troubleshooting` (consolidated)
- Uses nested structure: `troubleshooting.active_session`, `troubleshooting.statistics`, `troubleshooting.history`
- Backward compatible: Falls back to legacy `troubleshooting-history.json` when needed
- Historical stats inform tier selection and approach
- Pattern recognition from past resolutions
- Escalation tracking for learning

**Use when:**
- Debugging complex issues requiring multiple approaches
- Need structured troubleshooting workflow
- Escalating from simple fixes to full investigation
- Coordinating multiple DZP agents for bug resolution

---

## Prerequisites

- [ ] `.protocol-state/project-state.json` exists (consolidated state)
- [ ] **PATCH-STATE-001**: Uses `project-state.json::troubleshooting` namespace (fallback to legacy `troubleshooting-history.json`)
- [ ] Python 3.8+ available (for optional plan mode validation)
- [ ] Gojo agent context (domain.record.md write access)

**ESCAPE PATH**: If prerequisites fail:
1. If project-state.json missing: Create minimal version with troubleshooting schemas
2. If Python unavailable: Skip plan mode validation (proceed with user confirmation)
3. Continue with available troubleshooting features
4. **PATCH-STATE-001**: Automatic fallback to legacy files if consolidated state unavailable

---

## Tier System Overview

| Tier | Severity | Agents | Duration | Key Features |
|------|----------|--------|----------|--------------|
| **Tier 1** | Minor | Yuuji + Megumi | 30-45 min | Standard TDD + security review |
| **Tier 2** | Moderate | Yuuji + Megumi | 60-90 min | Investigation phase + root cause |
| **Tier 3** | Complex | Yuuji + Megumi + Support | 2-3 hours | User-selected specialists |
| **Tier 4** | Critical | Yuuji + Megumi + Support | 3-4 hours | Root cause diagram + multi-hypothesis |
| **Tier 5 (Codered)** | Catastrophic | ALL 9 agents | 4-6 hours | Mandatory plan mode, full doc sync |

**Hybrid Escalation**:
- **Initial tier**: User selects based on bug severity
- **Auto-escalation**: After 2 failed attempts per tier (configurable)
- **Manual escalation**: Available anytime via `/ts escalate`

---

## Commands

### 1. /ts_tier1 - Minor Bugs, First Attempt

**Purpose**: Quick fix for minor bugs with standard workflow

**Workflow**:
0. **Review troubleshooting history stats** (python troubleshooting_tracker.py stats)
- Check past Tier 1 success rate and avg duration
- Review frequently affected files for pattern recognition
- Inform tier selection with historical data
1. **Initialize troubleshooting session** (python troubleshooting_tracker.py start 1 "<description>" "<files>")
2. Prompt user for bug details (description, affected files, expected vs actual)
3. Brief Yuuji for TDD workflow (write failing test, implement fix, verify)
4. Brief Megumi for OWASP security review
5. Update dev-notes.md and domain.record.md
6. **Complete session tracking** (python troubleshooting_tracker.py complete "<resolution>")

**Implementation**:
```bash
# Step 0: Review past troubleshooting patterns
python .protocol-state/troubleshooting_tracker.py stats

# Step 1: Start new session
python .protocol-state/troubleshooting_tracker.py start 1 "<description>" "<files>"

# ... (Yuuji + Megumi work) ...

# Step 6: Mark complete
python .protocol-state/troubleshooting_tracker.py complete "<resolution>"
```

**User Prompts**:
- Bug description (max 500 chars)
- Affected files (comma-separated paths)
- Expected behavior
- Actual behavior
- Steps to reproduce (optional)

**Agent Briefing** (Yuuji):
```
Read protocol/yuuji.agent.md and fix bug with tier 2 workflow:

**Bug**: {description}
**Affected Files**: {files}
**Expected**: {expected}
**Actual**: {actual}

Workflow:
1. Write failing unit test demonstrating bug
2. Implement minimal fix
3. Verify test passes
4. Run full test suite
5. Update dev-notes.md with fix summary
```

**Agent Briefing** (Megumi):
```
Read protocol/megumi.agent.md and review fix for security implications:

**Bug**: {description}
**Files Modified**: {files}

Review for:
- Input validation bypassed by fix
- Authentication/authorization changes
- SQL injection, XSS, or other OWASP Top 10 risks
- Logging of sensitive data
```

**State Updates** (PATCH-STATE-001):
- `project-state.json::troubleshooting.active_session` (consolidated):
  ```json
  {
    "session_id": "TS-{timestamp}",
    "active": true,
    "current_tier": 1,
    "attempts_count": 1,
    "bug_description": "{description}",
    "affected_files": ["{file1}", "{file2}"],
    "started_at": "{timestamp}"
  }
  ```
- **Fallback**: Updates legacy `troubleshooting_session` if consolidated namespace unavailable

**Exit Conditions**:
- **Success**: Bug fixed, tests pass, security clean → `/ts complete`
- **Failure**: Bug persists after 1 attempt → Recommend `/ts tier2` or `/ts escalate`

---

### 2. /ts_tier2 - Moderate Bugs, Enhanced Investigation

**Enhancements over Tier1**:
- **Investigation phase** BEFORE fix (write to investigation.md)
- **Root cause hypothesis** with user review gate
- **Integration tests** in addition to unit tests
- **Git log analysis** for recent changes

**Workflow**:
1. Yuuji investigates and writes hypothesis to investigation.md
2. Present hypothesis to user for approval
3. Implement fix only after approval
4. Add integration tests
5. Analyze git history for related changes

**Investigation Template** (investigation.md):
```markdown
## Tier 2 Investigation - {session_id}
**Bug**: {description}
**Duration**: {minutes} minutes

### Root Cause Hypothesis
{hypothesis_text}

### Evidence
1. {evidence_1}
2. {evidence_2}

### Proposed Fix
{fix_approach}

### Test Strategy
- Unit tests: {test_plan_unit}
- Integration tests: {test_plan_integration}
```

**Agent Briefing** (Yuuji - Investigation Phase):
```
Read protocol/yuuji.agent.md and investigate bug:

**Bug**: {description}
**Affected Files**: {files}
**Tier**: 2 (Enhanced Investigation)

Investigation Steps:
1. Reproduce bug locally
2. Write root cause hypothesis to investigation.md
3. Present hypothesis for user approval
4. [WAIT FOR APPROVAL]
5. Implement fix with TDD
6. Add integration tests
7. Analyze git log for related changes
```

**State Updates** (PATCH-STATE-001):
- Increment `troubleshooting.active_session.attempts_count` (consolidated)
- Add investigation.md path to session metadata
- **Fallback**: Updates legacy `troubleshooting_session` if needed

---

### 3. /ts_tier3 - Complex Bugs, Support Agent Selection

**New Feature**: Context-dependent support agent selection

**Workflow**:
1. Prompt user to select support agents based on bug domain
2. Each selected support agent investigates and outputs recommendation
3. All recommendations route to Yuuji via @implementation handoff
4. Yuuji synthesizes and implements unified fix

**Support Agent Selection UI**:
```
Select support agents based on bug domain (multi-select):

[ ] Todo - Database issues (schema, queries, migrations, ORM)
[ ] Panda - CI/CD issues (build failures, deployment, Docker, GitHub Actions)
[ ] Maki - Performance issues (slow queries, memory leaks, bundle size)
[ ] Inumaki - API issues (REST, GraphQL, WebSocket, contracts)
[ ] Nobara - UX issues (accessibility, user flow, design system)

Examples:
- Database bug → select Todo
- API + performance → select Inumaki + Maki
- CI/CD + Docker → select Panda

Selected agents: _____________
```

**Agent Coordination**:
Each support agent provides specialized analysis:

**Todo** (Database):
```
Read protocol/todo.agent.md and analyze database-related bug:

**Bug**: {description}
**Schema Affected**: {schema}

Analysis:
- Schema integrity check
- Query performance analysis
- Migration history review
- Data corruption detection
- Recommendation document → .protocol-state/investigation.md
```

**Maki** (Performance):
```
Read protocol/maki.agent.md and profile performance issue:

**Bug**: {description}
**Performance Symptoms**: {symptoms}

Profiling:
- Bottleneck identification
- Memory leak detection
- CPU profiling
- Bundle analysis
- Recommendation → .protocol-state/investigation.md
```

**Inumaki** (API):
```
Read protocol/inumaki.agent.md and analyze API contract issue:

**Bug**: {description}
**Endpoints Affected**: {endpoints}

Analysis:
- Contract validation
- Breaking change detection
- Client compatibility
- Error handling review
- Recommendation → .protocol-state/investigation.md
```

**Yuuji Synthesis**:
```
Read protocol/yuuji.agent.md and synthesize all support agent recommendations:

**Support Agents Deployed**: {agent_list}
**Recommendations**:
- Todo: {todo_recommendation}
- Maki: {maki_recommendation}
- Inumaki: {inumaki_recommendation}

Synthesize unified fix:
1. Consolidate recommendations
2. Resolve conflicts between approaches
3. Implement holistic solution
4. Test across all domains (DB, API, performance)
```

**State Updates** (PATCH-STATE-001):
- `troubleshooting.active_session.selected_support_agents`: ["todo", "maki"] (consolidated)
- `troubleshooting.active_session.support_agent_deliverables`:
  ```json
  {
    "todo": {"status": "complete", "output_file": ".protocol-state/investigation.md#database-analysis"},
    "maki": {"status": "in_progress", "output_file": null}
  }
  ```
- **Fallback**: Updates legacy `troubleshooting_session` if needed

---

### 4. /ts_tier4 - Critical Bugs, Advanced Investigation

**Requirements**:
- **Root cause diagram/flowchart** (visual bug propagation)
- **Multi-hypothesis testing** (test at least 2 hypotheses before fixing)
- **Regression suite category addition** (prevent similar bugs)
- **Production telemetry analysis** (logs, metrics, traces)
- **User review gate before implementation**

**Enhanced Investigation Deliverable** (investigation.md):
```markdown
## Tier 4 Advanced Investigation - {session_id}

### Root Cause Diagram
[ASCII flowchart or link to visual diagram showing bug propagation path]

### Hypotheses Tested
1. **Hypothesis**: Redis cache not invalidating
   - **Test**: Manual cache clear + retry
   - **Result**: ✅ Confirmed (bug resolved)

2. **Hypothesis**: Database query race condition
   - **Test**: Added transaction isolation
   - **Result**: ❌ Ruled out (bug persists)

### Production Impact Analysis
- **Affected Users**: ~1,200 (12% of active user base)
- **Error Rate**: 3.4% of queries
- **Performance Degradation**: +450ms p95 latency
- **Revenue Impact**: $XXX estimated

### Regression Prevention
**New Test Category**: cache-invalidation-tests/
- Test 1: Cache invalidation on data mutation
- Test 2: TTL expiration verification
- Test 3: Multi-key invalidation consistency

### Proposed Fix
{detailed_fix_approach}

**User Approval Required**: [ ]
```

**Agent Briefing** (Yuuji - Tier 4):
```
Read protocol/yuuji.agent.md and conduct advanced investigation:

**Tier**: 4 (Critical Bug - Advanced Investigation)
**Bug**: {description}

Investigation Requirements:
1. Create root cause diagram (ASCII or visual)
2. Test at least 2 hypotheses before fixing
3. Analyze production telemetry (logs/metrics/traces)
4. Identify production impact metrics
5. Design regression suite category
6. Write comprehensive investigation.md
7. [WAIT FOR USER APPROVAL]
8. Implement fix with full test coverage
```

---

### 5. /ts_codered - All Hands, Mandatory Plan Mode

**Critical Protocol**: Codered activates ALL 9 agents with mandatory plan mode

**Step 1: Plan Mode Validation**

Check for plan mode activity. If NOT active, output recommendation:

```
⚠️ CODERED TROUBLESHOOTING REQUIRES PLAN MODE ⚠️

This catastrophic bug investigation requires comprehensive planning before execution.

**Please enable plan mode** in Claude Code:
Settings → Plans → Enable Plan Mode

Once enabled, reinvoke: /ts codered

Plan mode ensures:
- Full investigation before code changes
- Complete documentation of approach
- User review gate before implementation
- Rollback plan documented upfront

[If plan mode already active, proceed to Step 2]
```

**Step 2: All-Agent Briefing**

Output briefing templates for ALL 9 agents:

**Gojo** (Mission Control):
```
Read protocol/gojo.agent.md and coordinate codered investigation:

**Session**: {session_id}
**Bug**: {description}
**Severity**: CODERED (All Hands)

Coordination Tasks:
- Track all 8 agent findings in domain.record.md
- Synthesize unified recommendation after all agents complete
- Monitor progress, unblock agents
- Ensure full documentation sync (6 files)
- Present final recommendation to user
```

**Yuuji** (Implementation):
```
Read protocol/yuuji.agent.md with tier 3 (Critical) + plan mode:

**Tier**: CODERED (mandatory plan mode)
**Bug**: {description}

Plan Mode Requirements:
1. Investigation phase (no code changes)
2. Multi-hypothesis testing
3. Rollback plan documentation
4. User review gate before implementation
5. Test suite expansion
6. Implementation with TDD
```

**Megumi** (Security):
```
Read protocol/megumi.agent.md and conduct threat model analysis:

**Bug**: {description}
**Severity**: CODERED

Security Analysis:
- Is bug exploitable? (CVE assignment if yes)
- Multi-model security review (Claude + GPT-4)
- Incident response plan
- Post-mortem security recommendations
- Output: .protocol-state/security-review.md
```

**Nobara** (UX):
```
Read protocol/nobara.agent.md and assess user impact:

**Bug**: {description}

User Impact Assessment:
- Affected user workflows
- UX degradation analysis
- User communication strategy (email/in-app)
- Accessibility implications (WCAG 2.2)
- Output: User impact report
```

**Todo** (Database):
```
Read protocol/todo.agent.md and verify data integrity:

**Bug**: {description}

Database Analysis:
- Schema integrity verification
- Data corruption analysis
- Backup/restore plan validation
- Migration rollback procedure
- Output: Database integrity report
```

**Maki** (Performance):
```
Read protocol/maki.agent.md and conduct performance profiling:

**Bug**: {description}

Performance Analysis:
- Bottleneck identification
- Benchmark suite creation
- Performance regression detection
- Optimization recommendations
- Output: Performance profile report
```

**Panda** (Build/CI):
```
Read protocol/panda.agent.md and validate deployment safety:

**Bug**: {description}

CI/CD Analysis:
- Build system health check
- Deployment rollback procedure validation
- Environment consistency verification
- Canary deployment plan
- Output: Deployment safety report
```

**Inumaki** (API):
```
Read protocol/inumaki.agent.md and validate API contracts:

**Bug**: {description}

API Analysis:
- Contract validation (OpenAPI spec)
- Breaking change detection
- Client compatibility matrix
- Backward compatibility plan
- Output: API compatibility report
```

**Sukuna** (Adversarial Review):
```
Read protocol/sukuna.agent.md and challenge all findings:

**Bug**: {description}

Adversarial Review:
- Challenge each agent's findings
- Stress-test proposed fix
- Identify edge cases
- Alternative solution proposals
- Devil's advocate recommendations
```

**Step 3: Full Documentation Sync** (PATCH-STATE-001)

ALL 6 state files MUST be updated:

1. **project-state.json::troubleshooting.active_session** (consolidated):
   ```json
   {
     "troubleshooting": {
       "active_session": {
         "session_id": "{id}",
         "current_tier": 5,
         "codered_active": true,
         "plan_mode_active": true,
         "agent_completion_status": {
           "yuuji": "complete",
           "megumi": "in_progress",
           ...
         }
       }
     }
   }
   ```
   **Fallback**: Updates legacy `troubleshooting_session` if consolidated unavailable

2. **dev-notes.md**:
   ```markdown
   ## CODERED Session - {session_id}
   **Agents**: All 9 deployed
   **Assignments**:
   - Yuuji: Implementation with plan mode
   - Megumi: Threat model + multi-model review
   - [Full list]
   ```

3. **investigation.md**:
   Multi-agent findings consolidated by Gojo

4. **security-review.md**:
   Megumi threat model + OWASP review

5. **domain.record.md** (Gojo only):
   Strategic context, business impact, decision log

6. **project-state.json::troubleshooting.history** (PATCH-STATE-001):
   Session archive on completion (consolidated)
   **Fallback**: Legacy `troubleshooting-history.json` if consolidated unavailable

**Step 4: Gojo Unified Recommendation**

After all 9 agents complete, Gojo synthesizes:

```
✅ CODERED TROUBLESHOOTING COMPLETE

**Root Cause**: {identified_cause}
**Fix Implemented**: {description}
**Tests Added**: {count} ({types})
**Security Status**: ✅ Megumi sign-off
**Performance Impact**: ✅ Maki sign-off

**All-Agent Findings**:
- Yuuji: {finding}
- Megumi: {finding}
- Nobara: {finding}
- Todo: {finding}
- Maki: {finding}
- Panda: {finding}
- Inumaki: {finding}
- Sukuna: {adversarial_challenges}

**Recommendation**:
1. Deploy fix to staging
2. Run full regression suite
3. Monitor production telemetry for 24-48 hours
4. Schedule incident post-mortem
5. Update runbooks with learnings

**Documentation Updated**: All 6 files ✅

**Next Steps**: {user_decision_point}
```

---

### 6. /ts status - Show Current Session

**Read-only command** displaying active troubleshooting session.

**Output**:
```
📊 TROUBLESHOOTING SESSION STATUS

Session ID: TS-20251228-140000
Status: Active ✅
Current Tier: 3 (Complex Bugs + Support Agents)
Duration: 45 minutes
Attempts: 3

Bug Description:
{description}

Affected Files:
- {file1}
- {file2}

Agents Deployed:
- Yuuji (Implementation) ✅ Complete
- Megumi (Security) ⏳ In Progress
- Todo (Database) ✅ Complete
- Maki (Performance) ⏳ In Progress

Escalation History:
- tier1 → tier2 (auto-escalation, failed attempt after 30 min)
- tier2 → tier3 (manual, user reason: "Need DB + perf expertise")

Next Actions: Waiting for Megumi + Maki completion
```

**Implementation** (PATCH-STATE-001):
Read `project-state.json::troubleshooting.active_session` (consolidated), format output
**Fallback**: Reads legacy `troubleshooting_session` if consolidated unavailable

---

### 7. /ts history - Show Recent Sessions

**Read-only command** displaying last 10 troubleshooting sessions.

**Output**:
```
📜 TROUBLESHOOTING HISTORY (Last 10 Sessions)

1. TS-20251228-140000 (3 hours ago)
   tier1 → tier3 → ✅ Resolved
   Bug: Database cache invalidation
   Duration: 2h 15m | Agents: Yuuji, Megumi, Todo, Maki
   Tests Added: 8

2. TS-20251227-093000 (1 day ago)
   tier2 → ✅ Resolved
   Bug: Migration syntax error
   Duration: 1h 15m | Agents: Yuuji, Megumi, Todo
   Tests Added: 3

3. TS-20251226-150000 (2 days ago)
   tier1 → tier2 → tier4 → ✅ Resolved
   Bug: Race condition in payment processing
   Duration: 3h 45m | Agents: Yuuji, Megumi, Todo, Inumaki
   Tests Added: 12

Statistics:
- Total Sessions: 47
- Tier Distribution: tier1 (32%), tier2 (45%), tier3 (18%), tier4 (4%), codered (1%)
- Average Resolution Time: 1h 32m
- Most Common Escalation: tier1 → tier2 (auto, failed attempt)
```

**Implementation** (PATCH-STATE-001):
Read `project-state.json::troubleshooting.history` + `troubleshooting.statistics` (consolidated), format last 10 sessions + statistics
**Fallback**: Reads legacy `troubleshooting-history.json` if consolidated unavailable

---

### 8. /ts escalate - Manual Tier Escalation

**Purpose**: Manually escalate current session to next tier

**Workflow**:
1. Read current tier from project-state.json
2. Validate escalation path: tier1→tier2→tier3→tier4→codered
3. Prompt user for escalation reason
4. Log to escalation_history
5. Re-run workflow for new tier

**Tier Progression Rules**:
- Cannot skip tiers (tier1 → tier3 blocked)
- Codered requires explicit user confirmation
- De-escalation not supported (complete session, start new one)

**User Prompt**:
```
Manual Escalation: tier{N} → tier{N+1}

Reason for escalation (required):
_____________________________________________

[Confirm] [Cancel]
```

**State Update**:
```json
{
  "escalation_history": [
    {
      "from_tier": 2,
      "to_tier": 3,
      "reason": "manual",
      "user_reason": "Need database and performance expertise",
      "timestamp": "2025-12-28T15:00:00Z"
    }
  ]
}
```

---

### 9. /ts complete - Close and Archive Session

**Purpose**: Mark session complete and archive to consolidated state (PATCH-STATE-001)

**Workflow**:
1. Validate session is active
2. Prompt user for outcome and completion notes
3. Archive session to `project-state.json::troubleshooting.history` (consolidated)
4. Clear active session from `project-state.json::troubleshooting.active_session`
5. Log completion to dev-notes.md and domain.record.md
6. Update `troubleshooting.statistics`
7. **Fallback**: Updates legacy files if consolidated unavailable

**User Prompt**:
```
Close Troubleshooting Session

Outcome:
[ ] Resolved - Bug fixed and verified
[ ] Mitigated - Temporary workaround implemented
[ ] Deferred - Requires further analysis, scheduled for later
[ ] Cannot Reproduce - Unable to reproduce bug

Completion Notes (optional):
_____________________________________________

Tests Added: ___ (count)

[Complete Session] [Cancel]
```

**Archive Entry** (project-state.json::troubleshooting.history - PATCH-STATE-001):
```json
{
  "session_id": "TS-20251228-140000",
  "started_at": "2025-12-28T14:00:00Z",
  "completed_at": "2025-12-28T16:15:00Z",
  "duration_minutes": 135,
  "initial_tier": 1,
  "final_tier": 3,
  "attempts_count": 3,
  "bug_description": "Database query returns stale data intermittently",
  "affected_files": ["src/db/queries.ts", "src/cache/redis-client.ts"],
  "selected_support_agents": ["todo", "maki"],
  "escalation_history": [...],
  "outcome": "resolved",
  "completion_notes": "Fixed Redis cache invalidation bug with TTL adjustment",
  "tests_added": 8,
  "agents_deployed": ["yuuji", "megumi", "todo", "maki"]
}
```

**State Updates** (PATCH-STATE-001):
- Archive to `project-state.json::troubleshooting.history.sessions[]` (consolidated)
- Clear `troubleshooting.active_session`
- Increment `troubleshooting.statistics.total_sessions`
- Update tier distribution in `troubleshooting.statistics.sessions_by_tier`
- Log to dev-notes.md and domain.record.md
- **Fallback**: Updates legacy `troubleshooting-history.json` if consolidated unavailable

---

## Escalation Logic

### Automatic Escalation

**Trigger**: Failed attempt at current tier

**Detection Heuristics**:
1. **Test failures**: Yuuji reports tests still failing after implementation
2. **Security issues**: Megumi tags @remediation-required
3. **Time threshold exceeded**: tier1 (60min), tier2 (120min), tier3 (180min)
4. **User reports bug persists**: Manual feedback

**Escalation Threshold**: 2 failed attempts per tier (configurable in protocol.config.yaml)

**Workflow**:
```
1. Detect failure condition (tests fail, bug persists, time exceeded)
2. Increment attempts_count
3. If attempts_count >= threshold:
   - Log to escalation_history (reason: "auto", trigger: {condition})
   - Increment current_tier
   - Output: "Auto-escalating to tier{N} due to {reason}"
   - Re-run tier{N} workflow
4. Else:
   - Output: "Attempt {N} failed. Retry tier{current} or escalate manually?"
   - User decides: retry or `/ts escalate`
```

### Manual Escalation

Always available via `/ts escalate`, regardless of auto-escalation logic.

**Use Cases**:
- Bug more complex than initially assessed
- Need specialized agent expertise ("Need Maki for performance analysis")
- Security implications identified during investigation
- Production impact higher than expected

---

## State Schemas

### project-state.json::troubleshooting (PATCH-STATE-001 Consolidated)

```json
{
  "troubleshooting": {
    "_comment": "Troubleshooting session tracking - consolidated",
    "_schema_version": "2.0.0",
    "active_session": {
      "session_id": "TS-20251228-140000",
      "active": true,
      "current_tier": 3,
      "attempts_count": 3,
      "bug_description": "Database query returns stale data intermittently",
      "affected_files": ["src/db/queries.ts", "src/cache/redis-client.ts"],
      "expected_behavior": "Query returns fresh data every time",
      "actual_behavior": "Query returns stale data ~10% of requests",
      "reproduction_steps": ["1. Run query", "2. Update data", "3. Re-run query within 5 seconds"],
      "selected_support_agents": ["todo", "maki"],
      "support_agent_deliverables": {
        "todo": {"status": "complete", "output_file": ".protocol-state/investigation.md#database-analysis"},
        "maki": {"status": "in_progress", "output_file": null}
      },
      "escalation_history": [
        {"from_tier": 1, "to_tier": 2, "reason": "auto", "trigger": "failed_attempt", "timestamp": "2025-12-28T14:30:00Z"},
        {"from_tier": 2, "to_tier": 3, "reason": "manual", "user_reason": "Need DB + perf expertise", "timestamp": "2025-12-28T15:00:00Z"}
      ],
      "agent_completion_status": {
        "yuuji": "complete",
        "megumi": "in_progress",
        "todo": "complete",
        "maki": "in_progress"
      },
      "plan_mode_active": false,
      "codered_active": false,
      "started_at": "2025-12-28T14:00:00Z",
      "last_updated": "2025-12-28T15:30:00Z"
    },
    "statistics": {
      "total_sessions": 47,
      "sessions_by_tier": {
        "tier1": 15,
        "tier2": 21,
        "tier3": 8,
        "tier4": 2,
        "codered": 1
      },
      "sessions_by_outcome": {
        "resolved": 40,
        "mitigated": 4,
        "deferred": 2,
        "cannot_reproduce": 1
      },
      "average_resolution_minutes": {
        "tier1": 35,
        "tier2": 75,
        "tier3": 165,
        "tier4": 240,
        "codered": 263
      },
      "auto_escalation_count": 12,
      "manual_escalation_count": 5,
      "most_common_escalation_path": "tier1 → tier2",
      "total_tests_added": 387,
      "last_updated": "2025-12-28T16:00:00Z"
    },
    "history": {
      "sessions": [],
      "metadata": {
        "created": "2025-12-01T00:00:00Z",
        "total_sessions_all_time": 47,
        "last_updated": "2025-12-28T16:00:00Z"
      }
    }
  }
}
```

**Migration Note**: Legacy `troubleshooting-history.json` and `project-state.json::troubleshooting_session/troubleshooting_statistics` supported for backward compatibility.

### troubleshooting-history.json (Legacy - Deprecated)

```json
{
  "schema_version": "1.0.0",
  "sessions": [
    {
      "session_id": "TS-20251228-140000",
      "started_at": "2025-12-28T14:00:00Z",
      "completed_at": "2025-12-28T16:15:00Z",
      "duration_minutes": 135,
      "initial_tier": 1,
      "final_tier": 3,
      "attempts_count": 3,
      "bug_description": "Database query returns stale data intermittently",
      "affected_files": ["src/db/queries.ts", "src/cache/redis-client.ts"],
      "selected_support_agents": ["todo", "maki"],
      "escalation_history": [...],
      "outcome": "resolved",
      "completion_notes": "Fixed Redis cache invalidation bug with TTL adjustment",
      "tests_added": 8,
      "agents_deployed": ["yuuji", "megumi", "todo", "maki"]
    }
  ],
  "retention_policy": {
    "max_sessions": 100,
    "auto_archive_after_days": 90,
    "archive_location": ".protocol-state/archive/troubleshooting/"
  }
}
```

---

## Configuration (Optional)

### protocol.config.yaml Extension

```yaml
troubleshooting:
  auto_escalation:
    enabled: true
    attempts_per_tier: 2
    tier1_timeout_minutes: 60
    tier2_timeout_minutes: 120
    tier3_timeout_minutes: 180
    tier4_to_codered: "manual"  # Require user approval

  session_tracking:
    persist_history: true
    max_history_sessions: 100
    auto_archive_after_days: 90

  tier_time_estimates:
    tier1_minutes: "30-45"
    tier2_minutes: "60-90"
    tier3_minutes: "120-180"
    tier4_minutes: "180-240"
    codered_minutes: "240-360"

  support_agent_defaults:
    database: "todo"
    performance: "maki"
    api: "inumaki"
    ux: "nobara"
    cicd: "panda"
```

**Note**: All defaults hardcoded in skill for zero-config operation.

---

## Security Considerations

**Risk Level**: Medium

**Threat Model**:
1. **State injection** (malicious bug descriptions) → Sanitize input, truncate to 500 chars, remove control characters
2. **Path traversal** (affected files with `../`) → Validate paths, disallow `..` sequences
3. **Sensitive data leak** (bug descriptions with secrets) → Warn if patterns detected: "password", "secret", "token", "api_key"
4. **DoS via large sessions** → Limit troubleshooting-history.json to 100 sessions, auto-archive old ones

**Mitigations**:
- Input sanitization (remove control chars, limit length)
- Path validation (no `../`, must be within project root)
- Secret detection warnings (pattern matching for common secret keywords)
- Retention policy (max 100 sessions, auto-archive after 90 days)
- troubleshooting-history.json: 0644 permissions (read/write owner, read-only group/others)

---

## Escape Paths

### Prerequisites Failures (PATCH-STATE-001)
- **project-state.json::troubleshooting missing**: Auto-create with default troubleshooting namespace schema
- **Consolidated state unavailable**: Fallback to legacy `troubleshooting-history.json` (read/write)
- **Python unavailable**: Skip plan mode validation, trust user confirmation for codered
- **domain.record.md locked**: Skip strategic logging, log to dev-notes.md only
- **project-state.json corrupted**: Create minimal version with troubleshooting schemas

### Graceful Degradation Hierarchy
1. **CRITICAL** (must succeed): project-state.json::troubleshooting, dev-notes.md
2. **HIGH** (best effort): domain.record.md, legacy troubleshooting-history.json (fallback only)
3. **MEDIUM** (optional): security-review.md, investigation.md
4. **LOW** (nice-to-have): plan mode validation, statistics, tier time estimates

---

## Usage Examples

### Example 1: Quick Fix (Tier 1)
```bash
/ts tier1
Bug: Button onClick handler not firing
Affected files: src/components/Button.tsx
Expected: Click triggers submit
Actual: Nothing happens
```

### Example 2: Database Investigation (Tier 2 → Tier 3)
```bash
/ts tier2
Bug: Migration fails with foreign key constraint error
Affected files: migrations/20251228_add_user_settings.sql

[After investigation, user escalates manually]:

/ts escalate
Reason: Need Todo for schema validation + migration rollback plan

[System prompts for support agent selection]:
Selected agents: Todo

[Todo investigates, outputs recommendation, Yuuji implements]

/ts complete
Outcome: Resolved
Notes: Fixed foreign key order in migration, added rollback procedure
Tests Added: 5
```

### Example 3: Catastrophic Bug (Codered)
```bash
/ts codered
Bug: Payment processing silently failing, revenue loss detected

[System checks plan mode, outputs recommendation if not active]

[User enables plan mode, reinvokes]:

/ts codered

[System briefs ALL 9 agents]:
- Gojo: Coordinate investigation
- Yuuji: Plan mode investigation + fix
- Megumi: Threat model (exploitable?)
- Nobara: User impact assessment
- Todo: Data integrity verification
- Maki: Performance profiling
- Panda: Deployment rollback plan
- Inumaki: API contract validation
- Sukuna: Adversarial review

[After all agents complete, Gojo synthesizes unified recommendation]

/ts complete
Outcome: Resolved
Notes: Payment gateway timeout increased, circuit breaker added, full audit conducted
Tests Added: 23
```

---

## Changelog

### 1.1.0 (2025-12-29) - PATCH-STATE-001
- **BREAKING**: Migrated to consolidated state (`project-state.json::troubleshooting`)
- Nested structure: `troubleshooting.active_session`, `troubleshooting.statistics`, `troubleshooting.history`
- Backward compatibility: Fallback to legacy `troubleshooting-history.json` when consolidated unavailable
- Uses ProjectStateManager for all state operations
- All commands updated to reference consolidated namespaces
- Migration support via `migrate_state_consolidation.py`

### 1.0.0 (2025-12-28)
- Initial release for v8.11.0
- 9 commands: tier1-4, codered, status, history, escalate, complete
- Hybrid escalation (severity + attempts-based)
- Context-dependent support agent selection (tier3-4)
- Mandatory plan mode for codered
- Full state persistence (troubleshooting_session, troubleshooting_statistics, troubleshooting-history.json)
- Auto-escalation after 2 failed attempts per tier
- Gojo-owned skill (domain.record.md write access)

---

**Status**: Production-Ready
**Maintenance**: Update when DZP adds new agents or escalation logic changes
