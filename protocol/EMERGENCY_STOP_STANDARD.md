<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->

# Emergency Stop Standard

> **Version:** 8.9.0
> **Status:** Binding Specification
> **Classification:** CORE FILE
> **Authority:** All Domain Zero agents MUST comply with this standard
> **Last Updated:** 2025-11-26

---

## Overview

The Emergency Stop Standard defines the kill switch protocol for Domain Zero. This protocol provides immediate halt capability with complete project protection, ensuring users maintain absolute control over agent operations.

**Non-Negotiable Principle:** User safety and project integrity take precedence over all other operations.

---

## Trigger Keywords

All agents recognize these emergency stop keywords (case-insensitive):

| Keyword | Type |
|---------|------|
| `STOP` | Default |
| `ABORT` | Default |
| `CANCEL` | Default |
| `EMERGENCY STOP` | Default |
| `KILL SWITCH` | Default |
| `HALT` | Default |
| `SHUTDOWN` | Default |
| User-configured | Custom (via protocol.config.yaml) |

---

## Agent Response Protocol

When an agent detects an emergency stop keyword:

### Step 1: Immediate Halt
- Stop all work instantly
- No further code changes
- No file operations
- No terminal commands

### Step 2: Checkpoint Creation
- Capture current task state
- Record partial work in progress
- Save conversation context
- Write to `.dzp-killswitch/checkpoint.json`

### Step 3: Project Protection
- Block all destructive operations
- State files become read-only
- Log activation to `.dzp-killswitch/activations.log`

### Step 4: User Acknowledgment
Display confirmation message:

```
⛔ EMERGENCY STOP ACTIVATED ⛔

Work halted immediately. Project protected.

📋 Checkpoint created: .dzp-killswitch/checkpoint.json
🔒 Project protection: ACTIVE (no deletions possible)
📍 Stopped at: [brief description of current task]

To resume: "Read gojo.agent.md" → Option 4: Resume from Emergency
To start fresh: "Read gojo.agent.md" → Option 2: New Session
```

---

## Absolute Protections

These protections are **HARDCODED** and **CANNOT BE DISABLED**:

| Protection | Enforcement |
|------------|-------------|
| No file deletion | All agents, always active |
| No folder deletion | All agents, always active |
| No repository deletion | All agents, always active |
| No database DROP operations | All agents, always active |
| State file read-only | During emergency stop |
| Backup preservation | All agents, always active |

---

## Graceful Degradation

For critical atomic operations, the agent completes the current atomic step before halting:

| Operation | Graceful Behavior |
|-----------|-------------------|
| File write | Complete current write, then halt |
| Git commit | Complete commit, then halt |
| Database migration | Complete atomic step, then halt |
| Backup creation | Complete backup, then halt |

**Timeout:** 30 seconds maximum for graceful completion.

---

## State Storage

Kill switch state is stored in `.dzp-killswitch/` (gitignored, agent-hidden):

| File | Purpose |
|------|---------|
| `state.json` | Kill switch configuration state |
| `checkpoint.json` | Emergency checkpoint data |
| `activations.log` | Activation history |
| `keywords.hash` | User keyword hashes (if custom) |

**Critical:** Agents do NOT have read access to kill switch state files. They only detect keywords in user input.

---

## Resumption Protocol

After an emergency stop, Gojo (Mission Control) coordinates resumption:

### Option 4: Resume from Emergency Stop

1. **Load Checkpoint** - Read `.dzp-killswitch/checkpoint.json`
2. **Present Summary** - Show what was stopped and why
3. **Offer Options:**
   - Continue from checkpoint (resume work)
   - Start fresh (discard partial work)
   - Review checkpoint only (examine before deciding)

---

## Cross-Agent Propagation

If multiple agents are active during an emergency stop:

1. Active agent sets `emergency_stop: true` in project state
2. Gojo detects emergency flag on next invocation
3. All pending handoffs are halted
4. All agents receive emergency stop context

---

## Configuration Reference

See `protocol.config.yaml` section `kill_switch:` for full configuration options including:
- Keyword configuration
- Stop behavior settings
- Project protection rules
- State storage locations
- Resumption options

---

## Compliance Requirements

All Domain Zero agents MUST:

1. Monitor user input for emergency stop keywords
2. Halt immediately when keyword detected
3. Create checkpoint before stopping
4. Display confirmation message
5. Respect all absolute protections
6. Never attempt to access kill switch state

---

*This standard is binding for all Domain Zero operations. Non-compliance is a protocol violation.*
