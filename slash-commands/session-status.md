---
target: vscode
name: "session-status"
description: "Display current session summary"
argument-hint: "No arguments required"
---

**Session Management** - Show Session Status

Read protocol/skills/session.md and execute `/session status` command.

**Implementation**:
```bash
python .protocol-state/session_monitor.py status
```

Shows session duration, continuous work time, breaks taken, and alert status.
