---
target: vscode
name: "ts-status"
description: "Display current troubleshooting session status"
argument-hint: "No arguments required"
---

**Troubleshooting** - Show Current Session Status

Read protocol/skills/ts.md and execute `/ts status` command.

# Mark complete
STATUS="Bug fixed: root cause was X, implemented fix Y with Z tests"
python .protocol-state/troubleshooting_tracker.py status "$STATUS"

**Displays**:
- Current troubleshooting tier
- Session ID
- Start time
- Problem description
- Agents deployed
- Escalation history
- Current status
