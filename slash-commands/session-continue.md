---
target: vscode
name: "session-continue"
description: "Resume work after break"
argument-hint: "No arguments required"
---

**Session Management** - Resume After Break

Read protocol/skills/session.md and execute `/session continue` command.

**Implementation**:
```bash
python .protocol-state/session_monitor.py continue
```

Updates interaction timestamp to resume work after break.
