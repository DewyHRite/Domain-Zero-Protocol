---
target: vscode
name: "session-continue"
description: "Resume work after break"
argument-hint: "No arguments required"
---

**Session Management** - Resume After Break

Read protocol/skills/session.md and execute `/session continue` command.

### /session continue

**Action**: Resume work after break

**Implementation**:
```bash
python .protocol-state/session_monitor.py continue
```

**Output**: Resume timestamp and total session time

**State Updates** (PATCH-STATE-001):
- `project-state.json::session_tracking`: Updates last interaction timestamp
- Backward compatible: Falls back to `session-state.json` if needed


**Implementation**:
```bash
python .protocol-state/session_monitor.py continue
```

Updates interaction timestamp to resume work after break.
