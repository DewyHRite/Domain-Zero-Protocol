---
target: vscode
name: "session-end"
description: "End current work session"
argument-hint: "No arguments required"
---

**Session Management** - End Session

Read protocol/skills/session.md and execute `/session end` command.

**Implementation**:
```bash
python .protocol-state/session_monitor.py end
```

Archives current session to session_history and clears active session state.
