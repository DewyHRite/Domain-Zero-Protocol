<!-- [CORE FILE] - Domain Zero Protocol v8.12.0 -->
# Session Management Skill
## Unified Interface for Work Session Tracking

**Version**: 1.0.0
**Agent(s)**: Gojo (Mission Control)
**Category**: Session Management
**Risk Level**: Medium (code execution via Python)
**Token Efficiency**: High (replaces manual session_monitor.py commands)

---

## Purpose

Provides unified skill interface for session_monitor.py operations with integrated checkpoint file updates. Gojo-owned skill due to domain.record.md write access requirement.

**Use when:**
- Starting/ending work sessions
- Recording breaks during extended work
- Updating project checkpoints (session state, dev notes, domain record)
- Checking session status for alerting

---

## Prerequisites

- [ ] `.protocol-state/session_monitor.py` exists
- [ ] `.protocol-state/session-state.json` exists (auto-created if missing)
- [ ] Python 3.8+ available
- [ ] Gojo agent context (domain.record.md write access)

**ESCAPE PATH**: If prerequisites fail:
1. If session_monitor.py missing: Error with path to installation docs
2. If Python unavailable: Suggest manual session tracking
3. Continue with available commands (graceful degradation)

---

## Commands

### /session start

**Action**: Start new work session and activate Domain Zero Protocol

**Implementation**:
```bash
# Step 1: Start session monitoring
python .protocol-state/session_monitor.py start

# Step 2: Activate Domain Zero Protocol
Read protocol/CLAUDE.md
```

**Output**:
- Session ID and start timestamp
- Full DZP protocol activation (all agent rules, restrictions, workflows)

**State Updates**:
- `session-state.json`: Creates/updates current session
- `domain.record.md`: Logs session start (Gojo only)

**Workflow**:
1. Initialize session monitoring (Python script)
2. Read protocol/CLAUDE.md to load complete DZP context
3. Agents now have full protocol awareness for the session

---

### /session status

**Action**: Display current session summary

**Implementation**:
```bash
python .protocol-state/session_monitor.py status
```

**Output**:
- Session duration
- Continuous work time
- Breaks taken
- Alert status
- High-risk operation blocking status

**State Updates**: None (read-only)

---

### /session update

**Action**: Update session interaction timestamp + sync all checkpoint files

**Implementation**:
```bash
# Step 1: Update session timestamp
python .protocol-state/session_monitor.py update

# Step 2: Sync checkpoint files
# (See Checkpoint Update Workflow below)
```

**Checkpoint Files Updated**:
1. **session-state.json** - Session duration, alert counts
2. **dev-notes.md** - Append checkpoint entry with current tasks
3. **project-state.json** - Update last_active timestamp, mission progress
4. **security-review.md** - Append checkpoint (if security work active)
5. **domain.record.md** - Log checkpoint with strategic context (Gojo only)

**Use Cases**:
- Manual checkpoint during long work sessions
- Before taking break (preserve context)
- After completing significant milestone
- Before context compaction (save state)

**ESCAPE PATH**:
- If checkpoint file missing: Create with minimal schema
- If write fails: Log warning, continue with available files
- Non-blocking operation (best-effort sync)

---

### /session break [minutes]

**Action**: Record break duration

**Implementation**:
```bash
# Default: 15 minutes
python .protocol-state/session_monitor.py break 15

# Custom duration
python .protocol-state/session_monitor.py break 30
```

**Validation**: Duration must be 1-480 minutes (8 hours)

**State Updates**:
- `session-state.json`: Adds break timestamp, resets escalation
- `domain.record.md`: Logs break (Gojo only)

---

### /session continue

**Action**: Resume work after break

**Implementation**:
```bash
python .protocol-state/session_monitor.py continue
```

**Output**: Resume timestamp and total session time

**State Updates**:
- `session-state.json`: Updates last interaction timestamp

---

### /session end

**Action**: End current session and archive

**Implementation**:
```bash
python .protocol-state/session_monitor.py end
```

**State Updates**:
- `session-state.json`: Archives session to history, resets current
- `domain.record.md`: Logs session end with metrics (Gojo only)

**Output**: Session summary (duration, breaks, alerts)

---

## Checkpoint Update Workflow

When `/session update` is invoked, perform checkpoint sync:

### Step 1: Read Current State

```bash
# Read recent context from key files
tail -20 .protocol-state/dev-notes.md
cat .protocol-state/project-state.json
```

### Step 2: Generate Checkpoint Entry

**Format**:
```markdown
---
## {timestamp} - Session Checkpoint
**Session Duration**: {duration_formatted}
**Continuous Work**: {continuous_minutes} minutes
**Active Work**:
- {current_task_1}
- {current_task_2}
```

### Step 3: Update Checkpoint Files

**dev-notes.md**:
```bash
# Append checkpoint entry
echo "\n---\n## $(date -Iseconds) - Session Checkpoint\n**Session Duration**: ... \n" >> .protocol-state/dev-notes.md
```

**project-state.json**:
```json
{
  "session_metadata": {
    "last_active": "2025-12-28T20:00:00Z",
    "last_checkpoint": "2025-12-28T20:00:00Z"
  }
}
```

**domain.record.md** (Gojo only):
```markdown
---
## Session Checkpoint - {timestamp}
**Duration**: {duration} | **Continuous**: {continuous}
**Strategic Context**: {extract_from_recent_domain_record_entries}
```

**security-review.md** (if applicable):
```markdown
---
## {timestamp} - Security Checkpoint
**Status**: {active_security_work_summary}
```

**ESCAPE PATH**:
- If any file write fails: Log warning, continue with others
- If all files fail: Error with permission/path diagnostics
- Checkpoint sync is best-effort, not critical path

---

## Usage Examples

### Start Session
```bash
skill: "session"
args: "start"

# Or via slash command:
/session start
```

### Check Status Mid-Session
```bash
/session status
```

### Manual Checkpoint Before Break
```bash
/session update
/session break 15
```

### Resume After Break
```bash
/session continue
```

### End Session
```bash
/session end
```

---

## Integration with Session Monitoring

**Automatic Alerts**: Session monitor issues alerts at:
- 4 hours (initial alert)
- 6 hours (critical threshold - enables high-risk operation blocking)
- 8 hours (maximum - enforces read-only mode)

**Alert Workflow**:
1. Session monitor detects threshold
2. Gojo receives alert via `check_alert_needed()`
3. Gojo prompts user with `/session break` or `/session end`
4. If user continues: escalation level increases

**High-Risk Operation Blocking**:
- Blocks: `git push production`, `terraform destroy`, `npm publish`, etc.
- Triggered at 6+ hour sessions
- Cleared after sufficient break (15+ minutes)

---

## State File Schemas

### session-state.json
```json
{
  "current_session": {
    "session_id": "session_20251228_200000",
    "session_active": true,
    "start_time": "2025-12-28T20:00:00Z",
    "last_interaction_time": "2025-12-28T20:30:00Z",
    "alert_count": 0,
    "escalation_level": 0,
    "high_risk_operations_blocked": false
  },
  "session_metrics": {
    "total_duration_minutes": 30,
    "continuous_work_minutes": 30,
    "break_timestamps": [],
    "total_breaks": 0,
    "alerts_issued": 0
  },
  "thresholds": {
    "initial_alert_minutes": 240,
    "critical_session_minutes": 360,
    "max_continuous_minutes": 480
  }
}
```

---

## Error Handling

**Command Failures**:
- **session_monitor.py not found**: Provide installation instructions
- **Python not available**: Suggest manual tracking alternatives
- **Permission denied**: Check file permissions in `.protocol-state/`
- **Corrupted state file**: Auto-reset with backup creation

**Graceful Degradation**:
- If checkpoint file unreachable: Skip that file, continue with others
- If domain.record.md locked: Skip (non-critical for session ops)
- Session operations continue even if logging fails

---

## Changelog

### 1.0.0 (2025-12-28)
- Initial release for v8.11.0
- Commands: start, status, update, break, continue, end
- Integrated checkpoint file updates (update command)
- Gojo-owned skill (domain.record.md access)
- Direct session_monitor.py invocation (no agent coordination overhead)

---

**Status**: Production-Ready
**Maintenance**: Update when session_monitor.py adds new commands or thresholds change
