---
target: vscode
name: "ts-complete"
description: "Mark troubleshooting session as complete and archive"
argument-hint: "No arguments required"
---

**Troubleshooting** - Close and Archive Session

Read protocol/skills/ts.md and execute `/ts complete` command.

**Action**: Closes current troubleshooting session and archives to history

# Mark complete

RESOLUTION="Bug fixed: root cause was X, implemented fix Y with Z tests"
python .protocol-state/troubleshooting_tracker.py complete "$RESOLUTION"


**Completion Checklist**:
1. Problem resolved and verified
2. Tests passing
3. Root cause documented (if Tier 4+)
4. Resolution committed to git
5. Session notes updated

**Archives**:
- Session moved to troubleshooting-history.json
- Session metrics calculated
- Investigation notes preserved
- Lessons learned documented
