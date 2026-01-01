---
target: vscode
name: "session-status"
description: "Display current session summary"
argument-hint: "No arguments required"
---

**Session Management** - Show Session Status

Read protocol/skills/session.md and execute `/session status` command.

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

**Implementation**:
```bash
python .protocol-state/session_monitor.py status
```

Shows session duration, continuous work time, breaks taken, and alert status.
