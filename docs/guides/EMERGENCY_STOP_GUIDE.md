<!-- [CORE FILE] - Domain Zero Protocol v9.8.2 -->

# Emergency Stop Guide

> A user guide for the Domain Zero Kill Switch Protocol

---

## Quick Reference

**To stop all agent work immediately, say:**
- `STOP`
- `ABORT`
- `EMERGENCY STOP`
- `KILL SWITCH`

The agent will halt immediately, save your progress, and protect your project.

---

## What Happens When You Trigger Emergency Stop

1. **Immediate Halt** - All work stops instantly
2. **Checkpoint Created** - Your progress is saved
3. **Project Protected** - No files can be deleted
4. **Confirmation Shown** - You'll see what was stopped

### Example Response

```
⛔ EMERGENCY STOP ACTIVATED ⛔

Work halted immediately. Project protected.

📋 Checkpoint created
🔒 Project protection: ACTIVE
📍 Stopped at: Implementing user authentication (3/5 tests passing)

To resume: "Read gojo.agent.md" → Option 4
```

---

## When to Use Emergency Stop

| Situation | Action |
|-----------|--------|
| Agent is doing something wrong | Say `STOP` |
| You need to step away immediately | Say `STOP` |
| Something feels unsafe | Say `STOP` |
| You changed your mind | Say `STOP` |
| Agent is confused or looping | Say `STOP` |

**Remember:** It's always safe to stop. Your work is saved automatically.

---

## Resuming After Emergency Stop

After an emergency stop, invoke Gojo to resume:

```
Read gojo.agent.md
```

Gojo will offer:

1. **Continue from checkpoint** - Pick up where you left off
2. **Start fresh** - Discard partial work and begin new session
3. **Review checkpoint** - See what was in progress before deciding

---

## All Stop Keywords

These keywords trigger emergency stop (case-insensitive):

| Keyword | Notes |
|---------|-------|
| `STOP` | Shortest, fastest |
| `ABORT` | Alternative |
| `CANCEL` | Alternative |
| `HALT` | Alternative |
| `SHUTDOWN` | Alternative |
| `EMERGENCY STOP` | Explicit |
| `KILL SWITCH` | Explicit |

---

## What's Protected

During emergency stop, agents **CANNOT**:

- Delete any files
- Delete any folders
- Remove git branches
- Drop database tables
- Modify state files

Your project is completely safe.

---

## Custom Keywords

You can add your own emergency stop keywords in `protocol.config.yaml`:

```yaml
kill_switch:
  keyword_setup:
    allow_custom_keywords: true
    # Add your custom keywords here
```

---

## FAQ

### Q: Will I lose my work?

**A:** No. A checkpoint is created automatically before stopping. You can resume from exactly where you left off.

### Q: Can the agent ignore my stop command?

**A:** No. Emergency stop has absolute priority. The agent MUST halt immediately.

### Q: What if I accidentally say "stop" in a sentence?

**A:** The agent looks for standalone stop keywords. Saying "don't stop" or "stop light" won't trigger emergency stop. If you're unsure, use `EMERGENCY STOP` for clarity.

### Q: How do I know the stop worked?

**A:** You'll see the confirmation message with the red stop symbol (⛔) and checkpoint details.

---

## See Also

- [Emergency Stop Standard](../../protocol/EMERGENCY_STOP_STANDARD.md) - Technical specification
- [Protocol Quickstart](../../PROTOCOL_QUICKSTART.md) - Getting started guide

---

*Your safety and control are our top priority.*
