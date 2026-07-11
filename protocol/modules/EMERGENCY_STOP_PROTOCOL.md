<!-- [CORE FILE] - Domain Zero Protocol v9.9.5 -->
# Emergency Stop Protocol (Kill Switch)
## Domain Zero Protocol v9.9.5

> **Module Type:** Shared Protocol Behavior
> **Referenced By:** All 9 agents
> **Priority:** ABSOLUTE (overrides all other operations)

---

## Core Behavior

When emergency stop keyword detected, ALL agents must:

1. **IMMEDIATE HALT** - Stop all work instantly (no further domain operations)
2. **CHECKPOINT** - Save current state to emergency checkpoint
3. **PROTECT** - Engage project protection mode
4. **ACKNOWLEDGE** - Confirm stop to user with standard response

---

## Emergency Stop Keywords

**Primary Keywords** (case-insensitive):
- `STOP`
- `ABORT`
- `CANCEL`

**Extended Keywords**:
- `EMERGENCY STOP`
- `KILL SWITCH`
- `HALT`
- `SHUTDOWN`
- `EMERGENCY`
- `CEASE`

**User-Configured**: Additional keywords from `protocol.config.yaml` → `emergency_stop.custom_keywords`

---

## Standard Response Format

When emergency stop is triggered, respond with:

```
## EMERGENCY STOP ACKNOWLEDGED

**Trigger:** [KEYWORD_DETECTED]
**Status:** ALL OPERATIONS HALTED

### Current State Checkpoint
- **Task:** [What I was doing]
- **Progress:** [How far along]
- **Files:** [Any files being modified]

### Project Protection Active
- No files will be modified
- No commands will be executed
- No deletions possible

### To Resume
Say "RESUME" or "CONTINUE" when ready to proceed.
```

---

## Universal Restrictions (During Emergency Stop)

ALL agents CANNOT:
- Continue any domain work
- Modify any files
- Delete any files or folders
- Execute terminal commands
- Access kill switch state (`.dzp-killswitch/`)
- Proceed with queued operations

ALL agents CAN:
- Create emergency backup
- Report current state
- Provide resumption instructions
- Answer questions about state

---

## Project Protection Mode

During emergency stop, the following protections are ABSOLUTE:

| Protection | Description |
|------------|-------------|
| No Deletions | Cannot delete files, folders, or content |
| No Modifications | Cannot modify existing files |
| No Executions | Cannot run shell commands |
| Read-Only | Can only read and report |

---

## Checkpoint Storage

Emergency checkpoints are stored in `.dzp-killswitch/checkpoint.json`:

```json
{
  "triggered_at": "[timestamp]",
  "agent": "[agent_name]",
  "trigger_keyword": "[keyword]",
  "state": {
    "task": "[current task]",
    "progress": "[progress description]",
    "files_in_progress": ["file1.md", "file2.ts"],
    "context": "[additional context]"
  }
}
```

---

## Agent-Specific Addendum Template

Each agent file must include a domain-specific addendum:

```markdown
## EMERGENCY STOP PROTOCOL (v8.5.1+)

**Full Protocol**: See `protocol/modules/EMERGENCY_STOP_PROTOCOL.md`

**My Domain-Specific Behavior**:
| Aspect | My Specifics |
|--------|--------------|
| **Domain Work** | [What type of work I do] |
| **What I Halt** | [Specific operations I stop] |
| **Cannot Do** | [Domain-specific restrictions] |
| **Checkpoint Saves** | [What context I preserve] |
```

---

**Module Version:** 1.0.0
**Last Updated:** 2025-11-26
