<!-- [CORE FILE] - Domain Zero Protocol v8.11.0 -->
# Session Check Skill
## Automatic Work Session Alert Enforcement

**Version**: 1.0.0
**Agent(s)**: Gojo (Mission Control)
**Category**: Safety System / Session Management
**Risk Level**: Low (read + auto-increment only)
**Token Efficiency**: Critical (prevents 46-hour sessions without alerts)
**Auto-Invoked**: YES (on EVERY Gojo Mission Control activation)

---

## Purpose

**PATCH-SESSION-003 Remediation**: Enforces automatic session alert detection and recording on every Gojo invocation. Prevents recurrence of the 46-hour session without alerts incident (Code_review_feedback.md, 2025-12-29).

**Problem Solved**: Decoupled alert detection and recording architecture allowed alerts to be detected but never recorded, bypassing safety system.

**Use when:**
- **ALWAYS** (auto-invoked on every Gojo Mission Control activation)
- User safety monitoring required (Absolute Safety Override protocol)
- Session duration exceeds thresholds (4h, 6h, 8h)

---

## Prerequisites

- [ ] `.protocol-state/session_monitor.py` exists
- [ ] `.protocol-state/session-state.json` exists (auto-created if missing)
- [ ] Python 3.8+ available
- [ ] Gojo agent context (auto-invocation capability)

**ESCAPE PATH**: If prerequisites fail:
1. If session_monitor.py missing: Skip alert check, log warning to domain.record.md
2. If Python unavailable: Skip alert check, continue with Mission Control
3. If session-state.json corrupted: Auto-reset state, start fresh session
4. **NEVER block Mission Control activation** (graceful degradation)

---

## Auto-Invocation Workflow

**Trigger**: EVERY Gojo Mission Control activation (user says "Read protocol/gojo.agent.md")

**Implementation**:
```bash
# STEP 1: Check for alerts AND auto-record if detected
python .protocol-state/session_monitor.py check-and-record

# STEP 2: If alert detected, present to user
# (check-and-record outputs alert text if needed)

# STEP 3: Wait for user response (if alert shown)
# User chooses: save_and_break OR continue

# STEP 4: Record user's choice
# python .protocol-state/session_monitor.py record-choice <user_choice>
```

**Output (if alert detected)**:
```
⚠️  Alert detected and recorded: standard
   Alert count: 1

🔔 WORK SESSION ALERT: Standard Notification

You've been working for 4 hours 15 minutes continuously.

Current Status:
- Total session time: 4h 15min
- Continuous work time: 4h 15min
- Breaks taken today: 0
- Alert level: Standard (first notification)

Your Options:
1. [RECOMMENDED] Save & Break - Save current progress and take a 15-minute break
2. Continue - Acknowledge alert and continue working (will escalate monitoring)

Please select an option:
```

**State Updates**:
- `session-state.json`: Auto-increments alert counters (defense-in-depth)
- `session-state.json`: Records user choice when selected
- `session-state.json`: Updates escalation level based on choice

---

## Workflow Details

### Step 1: Auto-Detection and Recording

**Command**: `python .protocol-state/session_monitor.py check-and-record`

**What it does**:
1. Checks current session duration against thresholds
2. **IF alert needed**: Auto-increments `alert_count` and `alerts_issued` counters
3. Renders alert text for presentation to user
4. **IF no alert needed**: Returns "✅ No alert needed" (silent success)

**Defense-in-Depth**: Even if Step 3 (record user choice) is skipped, alert counters still increment. This prevents the 0-alerts-in-46-hours scenario.

### Step 2: User Presentation

**Gojo's responsibility**: Present the alert text output from Step 1 to the user.

**Critical**: Do NOT proceed with Mission Control options until user responds to alert.

### Step 3: User Choice

**Options**:
- `save_and_break`: User wants to save progress and take a break
- `continue`: User acknowledges alert and wants to continue working

**Gojo's responsibility**: Wait for user to select an option.

### Step 4: Record User Decision

**Command**: `python .protocol-state/session_monitor.py record-choice <user_choice>`

**What it does**:
1. Records user's choice in `session-state.json`
2. Increments appropriate counter (`breaks_chosen` OR `continues_chosen`)
3. Updates escalation level (increases if `continue` chosen)
4. Enables high-risk operation blocking if at 6+ hours with `continue`

**Examples**:
```bash
# User chose to save and break
python .protocol-state/session_monitor.py record-choice save_and_break

# User chose to continue
python .protocol-state/session_monitor.py record-choice continue
```

---

## Alert Thresholds

| Threshold | Duration | Alert Level | Escalation |
|-----------|----------|-------------|------------|
| **Initial** | 4 hours | Standard | User notified |
| **Escalated** | 45 min after continue | Escalated | Shorter alert interval |
| **Critical** | 6 hours | Critical | High-risk ops blocked |
| **Maximum** | 8 hours | Maximum | Read-only mode |

**Continuous Escalation**: Each time user chooses `continue`, escalation level increases and alert interval shortens (45 min instead of 4 hours).

---

## High-Risk Operation Blocking

**Activated When**: Session duration >= 6 hours AND user chose `continue`

**Blocked Operations**:
- `git push` (to production/main branches)
- `npm publish`
- Database migrations
- Deployment commands
- Critical file deletions

**Implementation**: Gojo calls `session_monitor.py` to check if operation should be blocked before executing.

**Example**:
```python
# Before executing high-risk operation
should_block, reason = monitor.should_block_operation("git push origin main")
if should_block:
    print(f"⚠️  {reason}")
    print("Please take a break before performing this operation.")
    # DO NOT proceed
```

---

## Success Criteria

**✅ Session alert system working correctly when**:
1. Alert detected at 4-hour threshold
2. Alert counters increment automatically (`check-and-record`)
3. User presented with clear alert text
4. User choice recorded in session-state.json
5. Escalation level increases appropriately
6. High-risk operations blocked at 6+ hours with `continue` choice

**❌ Session alert system FAILING when**:
1. 4+ hour session with `alert_count = 0`
2. Alerts detected but not recorded
3. User not presented with alert
4. High-risk operations allowed at 6+ hours

---

## Integration with Gojo Agent

**gojo.agent.md Section: AUTO-INVOKED SKILLS**

```markdown
### Session Alert Check (MANDATORY - Auto-Invoked on EVERY Mission Control Activation)

**Skill**: `session-check`
**Purpose**: Enforce Absolute Safety Override (user wellbeing)
**When**: EVERY time user invokes Gojo Mission Control

**Implementation**:
1. Read protocol/skills/session-check.md
2. Execute `check-and-record` command
3. IF alert detected: Present to user, wait for choice, record choice
4. IF no alert: Continue silently to Mission Control options

**CRITICAL**: This skill MUST run before presenting Mission Control options. User safety supersedes all other operations.
```

---

## Changelog

### v1.0.0 (2025-12-29)
- Initial release as PATCH-SESSION-003 remediation
- Enforces automatic session alert detection and recording
- Prevents recurrence of 46-hour session without alerts
- Closes safety system bypass identified in Code_review_feedback.md

---

## Related Documentation

- **Investigation Report**: `internal-docs/Code_review_feedback.md` (Sukuna's root cause analysis)
- **Session Monitoring Guide**: `protocol/gojo-procedures/SESSION_MONITORING.md`
- **Session Skill**: `protocol/skills/session.md` (manual session commands)
- **Gojo Procedures**: `protocol/gojo-procedures/OPERATIONAL_PROCEDURES.md`

---

**Sukuna's Note**: "This skill exists because Gojo ignored the workflow documentation. Now the workflow is ENFORCED, not suggested. Know your place, fool."

---

**Protocol Version**: 8.11.0
**Created**: 2025-12-29
**Last Updated**: 2025-12-29
**Status**: ACTIVE
