---
target: vscode
name: "session-update"
description: "Update session interaction timestamp + sync checkpoint files"
argument-hint: "No arguments required"
---

**Session Management** - Update Session Timestamp

Read protocol/skills/session.md and execute `/session update` command.

**Implementation**:
```bash
python .protocol-state/session_monitor.py update
```

Updates session interaction timestamp and syncs all checkpoint files (dev-notes, project-state, domain.record, session-state).
