---
target: vscode
name: "session-start"
description: "Start new work session and activate Domain Zero Protocol"
argument-hint: "No arguments required"
---

**Session Management** - Start Work Session

Read protocol/skills/session.md and execute `/session start` command.

**Implementation**:
```bash
python .protocol-state/session_monitor.py start
```

Then read protocol/CLAUDE.md to activate full DZP context.
