# Domain Zero Protocol - Session Monitor CLI Enhancement Patch

**Patch Version**: v8.8.0-session-monitor-cli
**Release Date**: 2025-12-11
**Applies To**: Domain Zero Protocol v8.8.0 installations
**Type**: Feature Enhancement + Operational Improvements

---

## 📋 What This Patch Adds

This patch enhances the session monitoring system with **complete CLI** and **updated operational procedures** for Gojo's orchestration workflow.

### Session Monitor CLI Enhancements (v8.8.0)

**Added 5 New Commands**:
1. **`new-session`** - Alias for `start` (matches user expectations)
2. **`reset`** - Clear session state with automatic backup
3. **`continue`** / **`resume`** - Resume work after break
4. **`help`** / **`--help`** / **`-h`** - Comprehensive help text
5. **Enhanced `break`** - Now accepts duration argument

**Improved User Experience**:
- Categorized help output (Session Management, Monitoring, Break Management, Utilities)
- Better error messages with helpful suggestions
- Complete command reference with examples
- All commands tested and verified working

---

## 📂 Files Modified

| File | Changes | Description |
|------|---------|-------------|
| **session_monitor.py** | +130 lines | Added 5 CLI commands, enhanced help |
| **gojo.agent.md** | +20 lines | Updated session command documentation |
| **gojo-session-monitoring-guide.md** | Version refs | Updated version to v8.8.0 |
| **work-session-alert.template.md** | Version refs | Updated version to v8.8.0 |
| **session-state.example.json** | Version refs | Updated version to v8.8.0 |
| **project-state.json** | Version refs | Updated protocol_version to v8.8.0 |
| **gojo.prompt.md** | +40 lines | Enhanced with full CLI command reference |

**Total**: ~210 lines added/modified across 7 files

---

## 🔧 Detailed Changes

### 1. session_monitor.py - Complete CLI

**New Commands Added**:

```python
# new-session (alias for start)
if command == "start" or command == "new-session":
    monitor.start_session()
    print(f"✅ New session started: {monitor.state['current_session']['session_id']}")

# reset (with automatic backup)
elif command == "reset":
    import shutil
    backup_path = monitor.state_file.parent / f"session-state.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy(monitor.state_file, backup_path)
    print(f"📦 Backup created: {backup_path}")
    monitor.state_file.unlink()
    monitor._ensure_state_file()
    print("✅ Session state reset successfully")

# continue/resume
elif command == "continue" or command == "resume":
    state = monitor.update_interaction()
    print(f"✅ Resumed work session")
    print(f"   Total duration: {state['session_metrics']['total_duration_minutes']} minutes")

# Enhanced break with duration argument
elif command == "break":
    duration = 15  # default
    if len(sys.argv) > 2:
        duration = int(sys.argv[2])
    monitor.record_break(duration)
    print(f"✅ Break recorded: {duration} minutes at {datetime.now().strftime('%H:%M')}")

# help command
elif command == "help" or command == "--help" or command == "-h":
    print("Domain Zero Protocol - Work Session Monitor v8.8.0")
    print("\nSession Management:")
    print("  start, new-session   Start a new work session")
    # ... full categorized help
```

**Enhanced Help Output**:
- Categorized by function (Session, Monitoring, Break, Utilities)
- Usage examples included
- Clear command aliases documented
- Professional formatting

### 2. gojo.agent.md - Updated Documentation

**Available Session Commands** section updated:

```markdown
**Available Session Commands** (v8.8.0+):
```bash
# Session Management
python .protocol-state/session_monitor.py start           # or new-session
python .protocol-state/session_monitor.py end
python .protocol-state/session_monitor.py reset

# Monitoring
python .protocol-state/session_monitor.py update
python .protocol-state/session_monitor.py check
python .protocol-state/session_monitor.py status          # or summary

# Break Management
python .protocol-state/session_monitor.py break [minutes] # default: 15
python .protocol-state/session_monitor.py continue        # or resume

# Utilities
python .protocol-state/session_monitor.py help
python .protocol-state/session_monitor.py test
```
```

### 3. gojo.prompt.md - Enhanced Orchestration Procedures

**Added comprehensive session management guidance**:

```markdown
### Session Health (`session_monitor.py`)

**Available Commands (v8.8.0)**:
```bash
# Session Management
python .protocol-state/session_monitor.py start           # or new-session
python .protocol-state/session_monitor.py update          # Record interaction
python .protocol-state/session_monitor.py end             # End session
python .protocol-state/session_monitor.py reset           # Clear state (creates backup)

# Monitoring
python .protocol-state/session_monitor.py check           # Check for alerts
python .protocol-state/session_monitor.py status          # or summary

# Break Management
python .protocol-state/session_monitor.py break [minutes] # default: 15
python .protocol-state/session_monitor.py continue        # or resume

# Utilities
python .protocol-state/session_monitor.py help            # Show all commands
python .protocol-state/session_monitor.py test            # Test alert rendering
```
```

**Updated "Save & Break" procedure**:
- Now uses `break [minutes]` command instead of manual state updates
- Resume protocol uses `continue` command

**Updated Pre-Execution Checks**:
- Includes session command reference for quick access
- Documents all available commands

---

## 🤖 AI Installation Instructions

### For AI Agents (Claude, GPT, etc.)

When applying this patch to a Domain Zero Protocol installation:

#### Step 1: Verify Prerequisites

```bash
# Check protocol version
grep "protocol_version" .protocol-state/project-state.json
# Must show: "8.8.0"

# Verify session_monitor.py exists
test -f .protocol-state/session_monitor.py && echo "EXISTS" || echo "MISSING"
```

#### Step 2: Create Backups (MANDATORY)

```bash
# Create timestamped backup directory
mkdir -p ".protocol-state/backups/session-cli-patch-$(date +%Y%m%d_%H%M%S)"

# Backup all files being modified
cp ".protocol-state/session_monitor.py" ".protocol-state/backups/session-cli-patch-$(date +%Y%m%d_%H%M%S)/"
cp "protocol/gojo.agent.md" ".protocol-state/backups/session-cli-patch-$(date +%Y%m%d_%H%M%S)/"
cp ".protocol-state/gojo-session-monitoring-guide.md" ".protocol-state/backups/session-cli-patch-$(date +%Y%m%d_%H%M%S)/"
cp "gojo.prompt.md" ".protocol-state/backups/session-cli-patch-$(date +%Y%m%d_%H%M%S)/"
cp ".protocol-state/session-state.example.json" ".protocol-state/backups/session-cli-patch-$(date +%Y%m%d_%H%M%S)/"

echo "✅ Backups created"
```

#### Step 3: Apply Code Changes

**File 1: `.protocol-state/session_monitor.py`**

Use the **Edit tool** to add the following command handlers to the CLI section (around line 681):

```python
# Add after existing command handlers:

if command == "start" or command == "new-session":
    monitor.start_session()
    session_id = monitor.state["current_session"]["session_id"]
    print(f"✅ New session started: {session_id}")

elif command == "reset":
    try:
        if monitor.state_file.exists():
            import shutil
            backup_path = monitor.state_file.parent / f"session-state.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy(monitor.state_file, backup_path)
            print(f"📦 Backup created: {backup_path}")
            monitor.state_file.unlink()
            print(f"🗑️  Removed: {monitor.state_file}")
        monitor._ensure_state_file()
        print("✅ Session state reset successfully")
    except Exception as e:
        print(f"❌ Error resetting session state: {e}", file=sys.stderr)
        sys.exit(1)

elif command == "continue" or command == "resume":
    state = monitor.update_interaction()
    print(f"✅ Resumed work session")
    print(f"   Total duration: {state['session_metrics']['total_duration_minutes']} minutes")

elif command == "break":
    duration = 15  # default
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
            if duration < 1:
                print("❌ Break duration must be at least 1 minute", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print(f"❌ Invalid duration: {sys.argv[2]} (must be a number)", file=sys.stderr)
            sys.exit(1)
    monitor.record_break(duration)
    timestamp = datetime.now().strftime('%H:%M')
    print(f"✅ Break recorded: {duration} minutes at {timestamp}")

elif command == "help" or command == "--help" or command == "-h":
    print("Domain Zero Protocol - Work Session Monitor v8.8.0")
    print("")
    print("Session Management:")
    print("  start, new-session   Start a new work session")
    print("  update               Record an interaction (updates duration)")
    print("  end                  End the current session")
    print("  reset                Reset session state (clear all data)")
    print("")
    print("Monitoring & Alerts:")
    print("  check                Check if alert is needed")
    print("  status, summary      Show current session summary")
    print("")
    print("Break Management:")
    print("  break [minutes]      Record a break (default: 15 minutes)")
    print("  continue, resume     Resume work after break")
    print("")
    print("Utilities:")
    print("  test                 Test alert rendering")
    print("  help                 Show this help message")
    print("")
    print("Examples:")
    print("  python session_monitor.py start              # Start new session")
    print("  python session_monitor.py status             # Check current status")
    print("  python session_monitor.py check              # Check for alerts")
    print("  python session_monitor.py break 15           # Take 15-min break")
    print("  python session_monitor.py continue           # Resume after break")
    print("  python session_monitor.py end                # End session")
```

**Also update version references**:
- Line 4 (module docstring): `Version: 8.8.0`
- Line 115 (state comment): `"_comment": "Domain Zero Protocol - Work Session State Tracking (v8.8.0)"`
- Line 148 (protocol_version): `"protocol_version": "8.8.0"`
- Line 751 (help text): `print("Domain Zero Protocol - Work Session Monitor v8.8.0")`

**Update unknown command error** (around line 779):
```python
else:
    print(f"Unknown command: {command}", file=sys.stderr)
    print("Run 'python session_monitor.py help' for usage information", file=sys.stderr)
    sys.exit(1)
```

**File 2: `protocol/gojo.agent.md`**

Update the "Available Session Commands" section (around line 422):

```markdown
**Available Session Commands** (v8.8.0+):
```bash
# Session Management
python .protocol-state/session_monitor.py start           # or new-session
python .protocol-state/session_monitor.py end
python .protocol-state/session_monitor.py reset

# Monitoring
python .protocol-state/session_monitor.py update
python .protocol-state/session_monitor.py check
python .protocol-state/session_monitor.py status          # or summary

# Break Management
python .protocol-state/session_monitor.py break [minutes] # default: 15
python .protocol-state/session_monitor.py continue        # or resume

# Utilities
python .protocol-state/session_monitor.py help
python .protocol-state/session_monitor.py test
```
```

**File 3: `gojo.prompt.md`**

Update Session Health section (around line 125) with complete command reference - see detailed changes above in "File Changes" section.

**File 4-6: Version References Only**

Update these files with version changes only:
- `.protocol-state/session-state.example.json`: Update `_comment` and `protocol_version` to v8.8.0
- `.protocol-state/gojo-session-monitoring-guide.md`: Already correct (keep historical v8.7.0 references)
- `.protocol-state/work-session-alert.template.md`: Update header/footer to v8.8.0

#### Step 4: Verify Installation

```bash
# Test help command
python .protocol-state/session_monitor.py help
# Should show: "Domain Zero Protocol - Work Session Monitor v8.8.0"

# Test new commands
python .protocol-state/session_monitor.py new-session
python .protocol-state/session_monitor.py status
python .protocol-state/session_monitor.py break 10
python .protocol-state/session_monitor.py continue
python .protocol-state/session_monitor.py reset

# All should work without "Unknown command" errors
```

#### Step 5: Document Changes

Add entry to project changelog or dev-notes:

```markdown
## Session Monitor CLI Enhancement (v8.8.0)

**Date**: 2025-12-11
**Changes Applied**:
- Added 5 new CLI commands (new-session, reset, continue/resume, help)
- Enhanced break command with duration argument
- Improved help output with categorization
- Updated gojo.agent.md with complete command reference
- Updated gojo.prompt.md orchestration procedures

**Verification**: All commands tested and working ✅
```

---

## 🧪 Testing Checklist

After applying the patch, verify:

### Functionality Tests

```bash
# Test 1: Help command
python .protocol-state/session_monitor.py help
# Expected: Displays categorized help with v8.8.0 version

# Test 2: New session
python .protocol-state/session_monitor.py new-session
# Expected: ✅ New session started: session_YYYYMMDD_HHMMSS

# Test 3: Session status
python .protocol-state/session_monitor.py status
# Expected: Displays current session metrics

# Test 4: Break with duration
python .protocol-state/session_monitor.py break 10
# Expected: ✅ Break recorded: 10 minutes at HH:MM

# Test 5: Continue/resume
python .protocol-state/session_monitor.py continue
# Expected: ✅ Resumed work session

# Test 6: Reset with backup
python .protocol-state/session_monitor.py reset
# Expected: 📦 Backup created + ✅ Session state reset successfully

# Test 7: Invalid command
python .protocol-state/session_monitor.py invalid-command
# Expected: Unknown command: invalid-command
#           Run 'python session_monitor.py help' for usage information
```

### Documentation Tests

- [ ] gojo.agent.md shows session commands with v8.8.0+ label
- [ ] gojo.prompt.md includes complete CLI reference
- [ ] All version references show v8.8.0
- [ ] Help text matches documented commands

### Integration Tests

- [ ] Gojo can invoke session_monitor.py commands
- [ ] Session state persists across invocations
- [ ] Backups are created correctly on reset
- [ ] Break/continue workflow functions properly

---

## 🔄 Rollback Procedure

If issues arise, restore from backup:

```bash
# Find your backup timestamp
ls -la .protocol-state/backups/

# Restore files
BACKUP_DIR=".protocol-state/backups/session-cli-patch-YYYYMMDD_HHMMSS"
cp "$BACKUP_DIR/session_monitor.py" ".protocol-state/"
cp "$BACKUP_DIR/gojo.agent.md" "protocol/"
cp "$BACKUP_DIR/gojo.prompt.md" "."
cp "$BACKUP_DIR/session-state.example.json" ".protocol-state/"

# Verify restoration
python .protocol-state/session_monitor.py help
# Should show older version or missing new commands
```

---

## 📊 Impact Assessment

### Benefits

✅ **User Experience**:
- Intuitive command names (`new-session`, `continue`)
- Comprehensive help system
- Better error messages

✅ **Safety**:
- Automatic backups on reset
- State validation
- Clear feedback messages

✅ **Maintainability**:
- Complete CLI interface
- Well-documented commands
- Consistent with protocol standards

### Risks

⚠️ **Low Risk Changes**:
- All changes are additive (no breaking changes)
- Backward compatible (existing commands unchanged)
- Tested on multiple operating systems

---

## 🤝 Compatibility

**Compatible With**:
- Domain Zero Protocol v8.8.0
- All 9 agents (Yuuji, Megumi, Nobara, Gojo, Todo, Maki, Panda, Inumaki, Sukuna)
- Windows, Linux, macOS
- Python 3.6+

**Not Compatible With**:
- v8.7.0 or earlier (missing session monitoring base implementation)
- v8.9.0 or later (future versions may have different CLI structure)

---

## 📚 Additional Documentation

**Related Files**:
- `SESSION_MONITOR_CLI_UPDATE_v8.8.0.md` - Complete feature documentation
- `.protocol-state/gojo-session-monitoring-guide.md` - Implementation guide for Gojo
- `protocol/gojo.agent.md` - Mission Control procedures
- `gojo.prompt.md` - Orchestration workflow reference

**Resources**:
- Canonical Source: https://github.com/DewyHRite/Domain-Zero-Protocol
- Issue Tracking: GitHub Issues
- Support: Repository discussions

---

## 🎯 Success Criteria

✅ **Patch Successfully Applied When**:
- All 10+ new commands work without errors
- Help command displays v8.8.0 and categorized output
- Gojo documentation reflects new CLI commands
- All tests pass
- No breaking changes to existing functionality

---

**Patch Created**: 2025-12-11
**Protocol Version**: 8.8.0
**Patch Type**: Feature Enhancement (CLI)
**Breaking Changes**: None
**Testing Status**: All commands verified ✅
