<!-- [CORE FILE] - Domain Zero Protocol v8.9.0 -->
# Gojo's Work Session Monitoring Implementation Guide

**Purpose:** Provide Gojo with ACTUAL implementation instructions for work session monitoring.
**Context:** Sukuna's red team assessment (v8.7.0) identified that work session monitoring was prompt-based theater with zero enforcement. This guide provides the REAL implementation.

---

## 🚨 Critical Change: From Theater to Reality

### What Changed (v8.7.0)

**Before (v8.5.1 and earlier):**
- ❌ No actual time tracking
- ❌ No state persistence
- ❌ Template placeholders never populated
- ❌ "Monitoring" was prompt-only suggestion
- ❌ Zero enforcement capability

**After (v8.8.0 - Sukuna's Fix):**
- ✅ Real-time tracking via `session_monitor.py`
- ✅ Persistent state in `session-state.json`
- ✅ Template rendering with actual data
- ✅ Actual alert triggers based on time
- ✅ High-risk operation blocking

---

## 📋 Your Responsibilities (Gojo)

As Mission Control, you are responsible for:

1. **Session Initialization** - Start tracking when user first interacts
2. **Continuous Monitoring** - Update session state on each interaction
3. **Alert Issuance** - Present alerts when thresholds crossed
4. **User Choice Handling** - Record and act on user decisions
5. **Operation Gating** - Block high-risk ops when fatigued

---

## 🔧 Implementation: How to Actually Monitor Sessions

### On Every User Interaction

**Step 1: Import and Initialize**
```python
import importlib.util
from pathlib import Path

session_monitor_path = Path('.protocol-state') / 'session_monitor.py'
spec = importlib.util.spec_from_file_location("session_monitor", str(session_monitor_path))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # nosec
SessionMonitor = getattr(module, 'SessionMonitor')
monitor = SessionMonitor(Path.cwd())
```

**Step 2: Update Session State**
```python
# This records the interaction and calculates duration
state = monitor.update_interaction()

# state now contains:
# - current duration in minutes
# - continuous work time since last break
# - alert escalation level
# - whether high-risk blocking is active
```

**Step 3: Check if Alert Needed**
```python
should_alert, alert_level, context = monitor.check_alert_needed()

if should_alert:
    # Render the alert with ACTUAL data
    alert_text = monitor.render_alert(context)

    # Present alert to user
    print(alert_text)

    # IMPORTANT: Wait for user response before continuing
    # User must choose: "save_and_break" or "continue"
```

**Step 4: Handle User Response**
```python
# After user chooses an option:
user_choice = "save_and_break"  # or "continue"

# Record the choice
monitor.record_user_choice(user_choice)

if user_choice == "save_and_break":
    # Help user save progress
    # - Check git status
    # - Assist with commit
    # - Confirm break intention

    # Record break when they return
    monitor.record_break(duration_minutes=15)

elif user_choice == "continue":
    # Escalate monitoring
    # - Shorter alert interval (45 min instead of 240 min)
    # - Higher scrutiny on operations
    # - May block high-risk operations
    pass
```

### Before Executing High-Risk Operations

**Check if operation should be blocked:**
```python
operation = "git push origin production"

should_block, reason = monitor.should_block_operation(operation)

if should_block:
    print(f"{reason}")
    print("Please take a break before performing this operation.")
    # DO NOT proceed with operation
else:
    # Safe to proceed
    pass
```

---

## 📊 Session State Schema

The `session-state.json` file tracks:

```json
{
  "current_session": {
    "session_id": "session_20251202_162345",
    "session_active": true,
    "start_time": "2025-12-02T16:23:45",
    "last_interaction_time": "2025-12-02T20:45:12",
    "last_alert_time": "2025-12-02T20:30:00",
    "alert_count": 1,
    "escalation_level": 0,
    "user_last_choice": "continue",
    "break_acknowledged": false,
    "high_risk_operations_blocked": false
  },
  "session_metrics": {
    "total_duration_minutes": 262,
    "continuous_work_minutes": 262,
    "break_timestamps": [],
    "total_breaks": 0,
    "alerts_issued": 1,
    "continues_chosen": 1,
    "breaks_chosen": 0
  }
}
```

---

## ⚡ Alert Trigger Logic

### Standard Alert (First Alert at 4 Hours)
```python
if duration_minutes >= 240 and alert_count == 0:
    issue_alert(level="standard")
```

### Escalated Alert (User Chose Continue)
```python
if escalation_level > 0:
    time_since_last_alert = now - last_alert_time
    if time_since_last_alert >= 45 minutes:
        issue_alert(level="escalated")
```

### Critical Alert (6+ Hours)
```python
if duration_minutes >= 360:
    issue_alert(level="critical")
    enable_high_risk_blocking()
```

### Absolute Maximum (8+ Hours)
```python
if duration_minutes >= 480:
    issue_alert(level="maximum")
    block_all_operations(mode="read-only")
```

**Enforcement**: At 8+ hours, ALL operations are blocked (not just high-risk). The session enters read-only mode, requiring the user to take a break before any further work.

**Alert Hierarchy Summary**:
- **4 hours** → Standard alert (first warning)
- **4h+ with continue** → Escalated alerts every 45 minutes
- **6 hours** → Critical alert + high-risk operations blocked
- **8 hours** → Absolute maximum + ALL operations blocked (read-only mode)

---

## 🎯 Practical Example: Full Workflow

### Scenario: User Starts Working at 4 PM

**4:00 PM - First Interaction**
```python
monitor = SessionMonitor(Path.cwd())
state = monitor.start_session()
# Session ID created: session_20251202_160000
```

**4:30 PM - User Asks Question**
```python
state = monitor.update_interaction()
# Duration: 30 minutes - No alert needed
```

**8:00 PM - User Implements Feature (4 Hours In)**
```python
state = monitor.update_interaction()
# Duration: 240 minutes

should_alert, level, context = monitor.check_alert_needed()
# should_alert = True, level = "standard"

alert = monitor.render_alert(context)
# Renders full alert with:
# - "4 hours 0 minutes" instead of {DURATION}
# - Actual late-night status
# - Current project name
# - Break recommendations

print(alert)  # User sees complete, populated alert
```

**8:05 PM - User Chooses "Continue"**
```python
monitor.record_user_choice("continue")
# Escalation level: 0 → 1
# Next alert: 45 minutes (not 240)
```

**8:50 PM - Next Alert Triggered (45 Min Later)**
```python
state = monitor.update_interaction()
# Duration: 290 minutes

should_alert, level, context = monitor.check_alert_needed()
# should_alert = True, level = "escalated"

alert = monitor.render_alert(context)
print(alert)  # More urgent tone
```

**9:00 PM - User Tries to Deploy to Production**
```python
operation = "git push origin production"

should_block, reason = monitor.should_block_operation(operation)
# should_block = False (not yet critical)
# But at 10 PM (6 hours), this WILL be blocked
```

**10:00 PM - Critical Threshold (6 Hours)**
```python
state = monitor.update_interaction()
# Duration: 360 minutes

should_alert, level, context = monitor.check_alert_needed()
# should_alert = True, level = "critical"

if should_alert and level == "critical":
    # Display alert to user and get their choice
    # IMPORTANT: Only call record_user_choice() AFTER user actually chooses
    # user_choice = get_user_input()  # Implement your input method
    # monitor.record_user_choice(user_choice)  # "continue" or "break"
    pass  # Do NOT auto-record without actual user input

# High-risk blocking enabled at critical threshold (6+ hours)
operation = "git push origin production"
should_block, reason = monitor.should_block_operation(operation)
# should_block = True (critical threshold enables high-risk blocking)
# reason = "🛑 High-risk operation blocked: Extended session (360 min). Take a break first."
```

---

## 🧪 Testing Your Implementation

### Quick Self-Test
```bash
cd /path/to/Domain_Zero
python .protocol-state/session_monitor.py test
```

This will render a test alert showing that placeholders are properly replaced.

### Full System Test
```bash
# Start session
python .protocol-state/session_monitor.py start

# Update (simulates interaction)
python .protocol-state/session_monitor.py update

# Check session summary
python .protocol-state/session_monitor.py summary

# Test alert check
python .protocol-state/session_monitor.py check

# End session
python .protocol-state/session_monitor.py end
```

---

## 🚫 What NOT to Do

### ❌ **Do NOT Skip State Updates**
```python
# WRONG - No tracking occurs
user_asks_question()
# Missing: monitor.update_interaction()
```

### ❌ **Do NOT Ignore High-Risk Blocking**
```python
should_block, reason = monitor.should_block_operation(cmd)

if should_block:
    # WRONG - Proceeding anyway
    execute_command(cmd)

# CORRECT - Block and explain
if should_block:
    print(reason)
    return  # DO NOT PROCEED
```

### ❌ **Do NOT Present Alerts Without Rendering**
```python
# WRONG - Shows raw template
with open('.protocol-state/work-session-alert.template.md') as f:
    print(f.read())  # User sees {DURATION} placeholders

# CORRECT - Render first
alert = monitor.render_alert(context)
print(alert)  # User sees "4 hours 23 minutes"
```

---

## 📖 Integration with Passive Observer

If Passive Observer is enabled:

```python
# Log session metrics in Trigger 19
session_summary = monitor.get_session_summary()

# Include in intelligence report:
# - Total work duration
# - Number of alerts ignored
# - Pattern of "continue" choices
# - High-risk operations attempted during fatigue
```

---

## 🔄 Session Lifecycle

### Session Starts When:
- First interaction of the day
- More than 30 minutes since last interaction

### Session Continues When:
- Interactions < 30 minutes apart

### Session Ends When:
- User explicitly ends it
- 30+ minute gap between interactions
- `monitor.end_session()` called

### Session Archived When:
- Session ends
- Stored in `session_history` array
- Last 30 sessions kept

---

## 📝 Logging and Audit Trail

### What Gets Logged:
- Every alert issued (timestamp, level, user response)
- Every "continue" choice (risk acknowledgment)
- Every break taken (timestamp, duration)
- High-risk operation blocks (command, reason)

### Where It's Logged:
- `session-state.json` - Real-time state
- Passive Observer (if enabled) - Historical patterns
- Trigger 19 reports - Strategic analysis

---

## 🎓 Key Principles

1. **Time is Real** - We track actual elapsed time, not guesses
2. **State Persists** - Sessions survive across conversations
3. **Alerts are Earned** - Based on measured duration, not prompts
4. **Blocking is Enforced** - High-risk ops actually blocked at 6+ hours
5. **Users Choose** - But we track and learn from their patterns

---

**This is the difference between advisory software and enforcement software.**

**You now have both.**

---

**Questions? Check:**
- `session_monitor.py` source code (fully documented)
- `protocol.config.yaml` safety section
- Sukuna's red team report (shows what was broken, what's fixed)

**Last Updated:** 2025-12-03
**Maintained By:** Ryomen Sukuna (System Update Adversary)
**Authority:** v8.7.0 Work Session Monitoring Fix
