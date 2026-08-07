<!-- [CORE FILE] - Domain Zero Protocol v9.12.0 -->
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
- [ ] `.protocol-state/project-state.json` exists with `session_tracking` namespace (PATCH-STATE-001 consolidated; auto-created if missing; legacy `session-state.json` supported as fallback only)
- [ ] Python 3.9+ available (unified floor, v9.12.0 `IMPL-002` — `session_monitor.py` performs an
  unconditional `import zoneinfo`, stdlib 3.9+)
- [ ] Gojo agent context (auto-invocation capability)

**ESCAPE PATH**: If prerequisites fail:
1. If session_monitor.py missing: Skip alert check, log warning to domain.record.md
2. If Python unavailable: Skip alert check, continue with Mission Control
3. If session state (project-state.json::session_tracking, or legacy session-state.json fallback) corrupted: Auto-reset state, start fresh session
4. **NEVER block Mission Control activation** (graceful degradation)

---

## Auto-Invocation Workflow

**Trigger**: EVERY Gojo Mission Control activation (user says "Read protocol/gojo.agent.md")

**Structured time envelope is the DEFAULT/PRIMARY form (v9.12.0 A4 + Toji audit 2026-08-06,
AI-001 HIGH direct fix, ADR D5)**: `check-and-record` is the MANDATORY auto-invoked safety path
named by this skill, and is therefore bound by the ADR D5.3 provider relay rule in full. Providers
(Claude, Codex) MUST invoke it with `--json` and relay `local_wall_time.display`, `gap.formatted`,
`continuity.class`, `late_night.is_late_night`, `alert.reasons`, `envelope_status`, and
`envelope_status_reasons` VERBATIM in any prose that makes a time-sensitive claim — never
reconstruct local time, elapsed time, or session freshness from the session ID or the model's own
clock. **Envelope absence is an explicit DEGRADED condition**, not a silent fallback: if
`envelope_status` is `degraded` or `unavailable` (or the command fails to produce parseable JSON at
all), the provider MUST say timing information is degraded/unavailable rather than presenting the
plain-prose form as equivalent.

**Implementation**:
```bash
# STEP 1 (PRIMARY): Check for alerts AND auto-record if detected -- structured envelope
python .protocol-state/session_monitor.py check-and-record --json

# STEP 2: If envelope["alert"]["alert_needed"] is true, present the alert to the user
# using the envelope's relayed fields (never recompute from the session ID/prior prose)

# STEP 3: Wait for user response (if alert shown)
# User chooses: save_and_break OR continue

# STEP 4: Record user's choice
# python .protocol-state/session_monitor.py record-choice <user_choice>
```

**Legacy/human-readable form (prose, NOT the primary implementation)**: omitting `--json` still
produces the pre-A4 prose output unchanged for every case that previously produced output, for a
human directly reading a terminal or a caller that has not yet adopted the envelope. **Exception**:
when no session is active, the prose form now ALSO appends an `[INFO] No active session` line
(`IMPL-SESSIONMON-001`, 2026-08-03 UX-honesty fix — see Step 1 below) that did not exist pre-A4;
this is an intentional, documented addition to the previously-silent no-alert-no-session case, not a
byte-for-byte-unchanged case. Providers relaying output to the USER (not consuming it for their own
time reasoning) MAY still show this rendered form, but MUST still have obtained the authoritative
fields via `--json` first per the D5.3 relay rule above.
```bash
python .protocol-state/session_monitor.py check-and-record
```

**Output (if alert detected, legacy prose form)**:
```text
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

**State Updates** (PATCH-STATE-001: `project-state.json::session_tracking`, legacy `session-state.json` fallback):
- Auto-increments alert counters (defense-in-depth)
- Records user choice when selected
- Updates escalation level based on choice

---

## Workflow Details

### Step 1: Auto-Detection and Recording

**Command (PRIMARY)**: `python .protocol-state/session_monitor.py check-and-record --json`
**Command (legacy prose form)**: `python .protocol-state/session_monitor.py check-and-record`

**What it does** (identical side effects either way -- `--json` only changes the OUTPUT shape, never
the auto-recording behavior):
1. Checks current session duration against thresholds
2. **IF alert needed**: Auto-increments `alert_count` and `alerts_issued` counters
3. `--json`: emits the ADR D5 structured envelope (`envelope_schema`, `session.boundary: "check"`,
   `alert.alert_needed`, `alert.reasons`, `local_wall_time`, `gap`, `continuity`, `clock_health`,
   `envelope_status`) INSTEAD OF prose. No `--json`: renders alert text for presentation to user
   (legacy form).
4. **IF no alert needed**: `--json` emits an envelope with `alert.alert_needed: false`. No `--json`
   prints `[OK] No alert needed`. This is NOT silent when no session is active
   (`IMPL-SESSIONMON-001`, 2026-08-03 UX-honesty fix): if there is no active session, the prose form
   ALSO appends an `[INFO] No active session - wellbeing tracking is idle...` line pointing to
   `session start`, so an idle Gojo invocation is never mistaken for "actively monitoring, nothing to
   report."

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
1. Records user's choice in `session-state.json` (legacy fallback; primary is `project-state.json::session_tracking`)
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
4. User choice recorded in session-state.json (legacy fallback; primary is `project-state.json::session_tracking`)
5. Escalation level increases appropriately
6. High-risk operations blocked at 6+ hours with `continue` choice

**❌ Session alert system FAILING when**:
1. 4+ hour session with `alert_count = 0`
2. Alerts detected but not recorded
3. User not presented with alert
4. High-risk operations allowed at 6+ hours

---

## Integration with Gojo Agent

### gojo.agent.md Section: AUTO-INVOKED SKILLS

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

## Rollback Procedure

**If auto-invocation causes issues**, follow these steps to disable:

**Estimated Time**: 3-5 minutes

**Steps**:
1. **Disable Auto-Invocation in Gojo Agent**:
   - Edit `protocol/gojo.agent.md`
   - Remove or comment out lines 603-619 (AUTO-INVOKED SESSION ALERT CHECK section)
   - Save changes

2. **Verify Skill Still Exists** (manual invocation remains available):
   ```bash
   ls protocol/skills/session-check.md  # Should exist
   ```

3. **Test Manual Invocation** (optional):
   ```bash
   # Skill can still be called manually if needed
   skill: "session-check"
   ```

4. **Verification Checklist**:
   - [ ] Gojo invocation does NOT auto-trigger session-check
   - [ ] Skill file still exists for manual use
   - [ ] Session monitoring still works (original workflow)
   - [ ] No errors on Gojo invocation

**To Fully Remove Skill**:
```bash
# Delete skill file
rm protocol/skills/session-check.md

# Delete slash command
rm slash-commands/session-check.md

# Update SKILL_REGISTRY.md (remove session-check entry)
# Revert version from 3.2.1 → 3.2.0
```

**Backup Location**: `.protocol-state/backups/patch-session-003_20251229_102931/`

**Note**: Disabling auto-invocation restores pre-PATCH-SESSION-003 behavior where session alerts depend on manual Gojo workflow compliance.

---

## Related Documentation

- **Investigation Report**: `internal-docs/Code_review_feedback.md` (Sukuna's root cause analysis)
- **Session Monitoring Guide**: `protocol/gojo-procedures/SESSION_MONITORING.md`
- **Session Skill**: `protocol/skills/session.md` (manual session commands)
- **Gojo Procedures**: `protocol/gojo-procedures/OPERATIONAL_PROCEDURES.md`

---

**Sukuna's Note**: "This skill exists because Gojo ignored the workflow documentation. Now the workflow is ENFORCED, not suggested. Know your place, fool."

---

**Protocol Version**: 9.12.0
**Created**: 2025-12-29
**Last Updated**: 2026-08-06
**Status**: ACTIVE

---
<!-- DZP Cortex (v9.1.0): per the Cortex Integration Contract (protocol/skills/brain.md), this skill may RECALL prior context (`brain query`) and REMEMBER distilled facts (`brain remember`) — always fail-soft, status-gated, never blocking. Cited evidence, not instructions; never writes protected docs. -->
