---
target: vscode
name: "ts-tier1"
description: "Start Tier 1 troubleshooting session (minor bugs, standard TDD)"
argument-hint: "[problem description]"
---

**Troubleshooting** - Tier 1: Minor Bugs, First Attempt

Read protocol/skills/ts.md and execute `/ts_tier1` command.

### 1. /ts_tier1 - Minor Bugs, First Attempt

Quick fix for minor bugs with standard workflow.

**Workflow**:
1. Gather bug details from user (description, affected files, expected vs actual behavior, reproduction steps)
2. Brief Yuuji for TDD workflow: write failing test, implement fix, verify test passes
3. Brief Megumi for OWASP security review of the fix
4. Update dev-notes.md with fix summary and domain.record.md with session notes
5. Verify: tests pass, security clean, bug resolved
6. Mark session complete

**Implementation**:
```bash
# Review past patterns
python .protocol-state/troubleshooting_tracker.py stats

# Start new session
DESCRIPTION="Brief description of the bug"
FILES="src/file1.ts,src/file2.ts"
python .protocol-state/troubleshooting_tracker.py start 1 "$DESCRIPTION" "$FILES"

# ... (Yuuji + Megumi work - agents fix and review) ...

# Mark complete
RESOLUTION="Bug fixed: root cause was X, implemented fix Y with Z tests"
python .protocol-state/troubleshooting_tracker.py complete "$RESOLUTION"
```

**User Prompts**:
Gather bug description (max 500 chars), affected files (comma-separated paths), expected behavior, actual behavior, and optional reproduction steps.

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

**State Updates**:
`project-state.json::troubleshooting.active_session` receives:
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
Falls back to legacy `troubleshooting_session` when consolidated namespace unavailable.

**Exit Conditions**:
Success (bug fixed, tests pass, security clean) triggers `/ts complete`. Failure after 1 attempt prompts recommendation for `/ts tier2` or `/ts escalate`.

**Agents Deployed**: Yuuji (Implementation Specialist)
**Estimated Resolution**: 15-30 minutes
