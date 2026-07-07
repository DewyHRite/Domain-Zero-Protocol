# Gojo Snapshot Integration Guide
<!-- [CORE FILE] - Domain Zero Protocol v9.9.2 -->

**Version**: 1.0.0
**Created**: 2025-12-06
**Updated**: 2025-12-29
**Part of**: DZP v8.13.0 Validation Framework - Phase 2

## Purpose

This guide documents how Gojo (Mission Control) should integrate automatic tier-based snapshot creation into session management.

## Overview

The snapshot integration system enables automatic context snapshots based on:
- **Tier 1**: Manual only (no automatic snapshots)
- **Tier 2**: Every 10 operations
- **Tier 3**: After each operation
- **All Tiers**: On tier changes

## Architecture

**Module**: `.protocol-state/snapshot_integration.py`
**Session State**: `.protocol-state/session-state.json` (operation tracking)
**Project State**: `.protocol-state/project-state.json` (tier configuration)
**Snapshot Creation**: `.protocol-state/create-snapshot.py` (called automatically)

## When to Record Operations

Gojo should record an operation when ANY of the following occur:

### Implementation Work
- ✅ Yuuji completes a feature implementation
- ✅ Yuuji applies remediation fixes
- ✅ Yuuji creates backups before major changes

### Security Review
- ✅ Megumi completes security audit
- ✅ Megumi approves feature with `@approved`
- ✅ Megumi documents security findings

### Design Work
- ✅ Nobara completes UX design
- ✅ Nobara creates wireframes or mockups
- ✅ Nobara finalizes creative strategy

### Database Operations
- ✅ Todo completes schema design
- ✅ Todo creates migration
- ✅ Todo optimizes queries

### Performance Work
- ✅ Maki completes performance audit
- ✅ Maki applies optimization
- ✅ Maki achieves performance target

### Build & Integration
- ✅ Panda configures CI/CD pipeline
- ✅ Panda completes build optimization
- ✅ Panda sets up deployment

### API Work
- ✅ Inumaki designs API specification
- ✅ Inumaki creates OpenAPI schema
- ✅ Inumaki implements API endpoint

### User Actions
- ✅ User creates manual snapshot
- ✅ User completes major task
- ✅ User reaches milestone

## When NOT to Record Operations

Do NOT record operations for:
- ❌ Gojo's own coordination activities
- ❌ Passive observation monitoring
- ❌ Trigger 19 intelligence reports
- ❌ Reading files or checking status
- ❌ Asking questions or clarifications

## Integration Pattern (Python)

### Basic Usage

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.protocol-state')))

from snapshot_integration import SnapshotIntegration

# Initialize integration
integration = SnapshotIntegration()

# Record operation
integration.record_operation(description="User authentication implementation completed")

# Check and create snapshot if needed
result = integration.check_and_create_snapshot()

if result:
    print(f"✅ Snapshot created: {result['snapshot_id']}")
else:
    _, reason = integration.should_create_snapshot()
    print(f"ℹ️  No snapshot needed: {reason}")
```

### On Tier Change

```python
# When tier changes (e.g., user switches from Tier 2 to Tier 3)
old_tier = 2
new_tier = 3

result = integration.on_tier_change(old_tier, new_tier)
if result:
    print(f"✅ Tier change snapshot created: {result['snapshot_id']}")
```

### Check Status

```python
status = integration.get_status()

print(f"Current Tier: {status['current_tier']}")
print(f"Operation Count: {status['operation_count']}")
print(f"Operations Since Last Snapshot: {status['operations_since_snapshot']}")
print(f"Should Create Snapshot: {status['should_create_snapshot']}")
print(f"Reason: {status['reason']}")
```

## Integration Pattern (Bash)

### Record Operation

```bash
python .protocol-state/snapshot_integration.py --record --description "Feature X completed"
```

### Check and Create Snapshot

```bash
python .protocol-state/snapshot_integration.py --check --description "Manual check"
```

### Record Tier Change

```bash
python .protocol-state/snapshot_integration.py --tier-change 2:3
```

### Check Status

```bash
python .protocol-state/snapshot_integration.py --status
```

## Gojo's Session Management Integration

### On Mission Control Activation

```python
# 1. Update session state (existing session monitoring)
from session_monitor import update_interaction, check_alert_needed

state = update_interaction()
should_alert, alert_level, context = check_alert_needed()

# 2. Display work session alert if needed
if should_alert:
    # Display alert template
    pass

# 3. Check snapshot integration status (NEW)
from snapshot_integration import SnapshotIntegration

integration = SnapshotIntegration()
status = integration.get_status()

# Optional: Display snapshot status in Mission Control interface
print(f"📸 Snapshots: {status['snapshots_this_session']} this session")
print(f"🔢 Operations: {status['operation_count']} ({status['operations_since_snapshot']} since last snapshot)")
```

### After Agent Work Completion

```python
# When agent work completes (e.g., Yuuji finishes implementation)
from snapshot_integration import SnapshotIntegration

integration = SnapshotIntegration()

# Record the operation
integration.record_operation(description="User authentication implementation completed by Yuuji")

# Check if snapshot is needed and create automatically
result = integration.check_and_create_snapshot()

if result:
    # Notify user
    print(f"\n📸 Automatic snapshot created: {result['snapshot_id'][:16]}...")
    print(f"   Trigger: {result['trigger']}")
    print(f"   Tier: {result['tier']}")
    print(f"   Operation: {result['operation_count']}\n")
```

### On Tier Change

```python
# When user changes tier (e.g., via tier bypass or explicit tier change)
from snapshot_integration import SnapshotIntegration

integration = SnapshotIntegration()

old_tier = 2  # Get from previous state
new_tier = 3  # Get from new state

# Create tier change snapshot
result = integration.on_tier_change(old_tier, new_tier)

if result:
    print(f"\n📸 Tier change snapshot created: {result['snapshot_id'][:16]}...")
    print(f"   Tier change: {old_tier} → {new_tier}\n")
```

## Session State Schema

The following fields are tracked in `session-state.json`:

```json
{
  "operation_count": 0,
  "last_snapshot_operation_count": 0,
  "snapshots_this_session": 0,
  "last_operation_time": null,
  "last_operation_description": null
}
```

**Field Descriptions**:
- `operation_count`: Total operations recorded this session
- `last_snapshot_operation_count`: Operation count when last snapshot was created
- `snapshots_this_session`: Number of automatic snapshots created this session
- `last_operation_time`: ISO-8601 timestamp of last operation
- `last_operation_description`: Description of last operation recorded

## Tier-Based Behavior

### Tier 1 (Rapid)
- **Frequency**: Manual only
- **Trigger**: User explicitly creates snapshots
- **Automatic**: ❌ None

### Tier 2 (Standard)
- **Frequency**: Every 10 operations
- **Trigger**: `operation_count`
- **Automatic**: ✅ Yes

### Tier 3 (Critical)
- **Frequency**: After each operation
- **Trigger**: `operation_count`
- **Automatic**: ✅ Yes

### All Tiers
- **Tier Change**: Creates snapshot when tier changes
- **Trigger**: `tier_change`
- **Description**: "Tier change: {old_tier} → {new_tier}"

## Error Handling

The integration module handles errors gracefully:

```python
result = integration.check_and_create_snapshot()

if result is None:
    # Snapshot creation failed (logged to stderr)
    # Continue session without blocking user
    print("⚠️  Snapshot creation failed, continuing without snapshot")
```

**Common Failures**:
- Snapshot creation script not found
- Insufficient disk space
- Permission errors
- Timeout (>60 seconds)

All errors are logged to stderr but do not block session continuation.

## Testing

### Test Tier 2 Behavior (10 operations)

```bash
# Record 10 operations
for i in {1..10}; do
  python .protocol-state/snapshot_integration.py --record --description "Test operation $i"
done

# Expected: Snapshot created after operation 10
```

### Test Tier 3 Behavior (1 operation)

```bash
# Change to Tier 3
python .protocol-state/snapshot_integration.py --tier-change 2:3

# Record 1 operation
python .protocol-state/snapshot_integration.py --record --description "Tier 3 test"

# Expected: Snapshot created immediately
```

### Verify Snapshots

```bash
# List all snapshots
python .protocol-state/create-snapshot.py --list

# Preview specific snapshot
python .protocol-state/restore-snapshot.py --preview <snapshot-id>
```

## Best Practices

1. **Record operations immediately after agent work completes**
   - Don't wait until end of session
   - Ensures timely snapshots

2. **Use descriptive operation descriptions**
   - Good: "User authentication implementation completed by Yuuji"
   - Bad: "Operation"

3. **Don't block on snapshot creation**
   - Snapshots run asynchronously
   - Failures are logged but don't stop work

4. **Monitor snapshot storage**
   - Check storage warnings in snapshot creation output
   - Retention policy automatically cleans up old snapshots

5. **Respect tier settings**
   - Tier 1: No automatic snapshots (manual only)
   - Tier 2: Balanced (every 10 operations)
   - Tier 3: Continuous (every operation)

## Configuration

Snapshot integration respects settings in `project-state.json`:

```json
{
  "tier_settings": {
    "default_tier": 2
  }
}
```

Snapshot retention limits are configured in `create-snapshot.py`:

```python
RETENTION_LIMITS = {
    1: 10,   # Tier 1: Manual only
    2: 30,   # Tier 2: Every 10 operations
    3: 50    # Tier 3: Continuous
}
```

## Security

- ✅ File permissions checked before import
- ✅ File ownership verified
- ✅ File size validated (10KB - 1MB range)
- ✅ No arbitrary code execution
- ✅ Timeout protection (60s max)

## Performance

- **Snapshot creation**: ~0.5-2 seconds (gzip compression)
- **Operation recording**: <10ms (JSON write)
- **Status check**: <5ms (JSON read)
- **No blocking**: Runs synchronously but fast enough not to impact UX

## Future Enhancements

Potential improvements for future versions:

1. **Async snapshot creation** - Non-blocking background snapshots
2. **Differential snapshots** - Only save changed files
3. **Remote backup** - Upload snapshots to cloud storage
4. **Snapshot tagging** - Mark important snapshots for preservation
5. **Operation categories** - Different counters for different operation types

## Troubleshooting

### Snapshots Not Creating

**Check**:
1. Is tier set correctly? (`project-state.json` → `tier_settings.default_tier`)
2. Have enough operations occurred? (Tier 2 needs 10, Tier 3 needs 1)
3. Is `create-snapshot.py` executable?
4. Check stderr output for errors

**Fix**:
```bash
# Verify tier
cat .protocol-state/project-state.json | grep -A3 tier_settings

# Check status
python .protocol-state/snapshot_integration.py --status

# Test manually
python .protocol-state/snapshot_integration.py --check
```

### Operation Count Not Incrementing

**Check**:
1. Is `session-state.json` writable?
2. Are operations being recorded?
3. Check file permissions

**Fix**:
```bash
# Check permissions
ls -l .protocol-state/session-state.json

# Reset if needed
chmod 644 .protocol-state/session-state.json

# Verify fields exist
cat .protocol-state/session-state.json | grep operation_count
```

### Snapshots Creating Too Frequently

**Check**:
1. Current tier (might be set to Tier 3)
2. Operation recording frequency

**Fix**:
```bash
# Change tier if needed
# Edit .protocol-state/project-state.json
# Set "default_tier": 2  (or 1 for manual only)
```

## Support

For issues or questions about snapshot integration:

1. Check this guide first
2. Review `.protocol-state/snapshot_integration.py` source code
3. Review `.protocol-state/create-snapshot.py` for snapshot creation logic
4. Check session-state.json for operation tracking status
5. Review stderr logs for error messages

---

**Version History**:
- v1.0.0 (2025-12-06): Initial Gojo integration guide
