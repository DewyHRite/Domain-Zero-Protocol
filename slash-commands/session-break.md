---
target: vscode
name: "session-break"
description: "Record a break during extended work"
argument-hint: "[minutes] - Default: 15 minutes"
---

**Session Management** - Record Break

Read protocol/skills/session.md and execute `/session break [minutes]` command.

**Implementation**:
```bash
# Default: 15 minutes
python .protocol-state/session_monitor.py break

# Custom duration
python .protocol-state/session_monitor.py break 30
```

Resets continuous work timer and escalation level.
