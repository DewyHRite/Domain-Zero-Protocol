# DZP Validation Framework - Local State Directory

**Version**: 8.8.0
**Purpose**: Local validation state storage (pre-Memory Tool migration)

---

## Directory Purpose

This directory stores validation framework state files **locally** until Memory Tool is enabled.

Once Memory Tool is enabled, these files will migrate to `/memories/validation/` for persistent cross-session storage.

---

## Directory Structure

```
.protocol-state/validation/
├── README.md                  # This file
├── snapshots/                 # Context snapshots
│   ├── snapshot-[ISO-8601].json
│   └── snapshot-manifest.json
├── validation-state.json      # Central validation tracking
├── validation-config.yaml     # User overrides (optional)
├── validation-report.md       # Latest validation report
├── metrics.json               # Validation metrics (Sukuna)
├── tuning-history.json        # Threshold adjustments (Sukuna)
└── learned-rules.yaml         # Auto-discovered patterns (Sukuna)
```

---

## Memory Tool Migration

When validation is enabled in DZP v8.8.0, these files will automatically migrate to:

**Local** → **Memory Tool**:
- `.protocol-state/validation/validation-state.json` → `/memories/validation/validation-state.json`
- `.protocol-state/validation/snapshots/` → `/memories/validation/snapshots/`
- `.protocol-state/validation/metrics.json` → `/memories/agents/sukuna/metrics.json`
- `.protocol-state/validation/tuning-history.json` → `/memories/agents/sukuna/tuning-history.json`
- `.protocol-state/validation/learned-rules.yaml` → `/memories/validation/learned-rules.yaml`

**Migration Process**:
1. Gojo detects existing `.protocol-state/validation/` files
2. Reads content from each file
3. Creates corresponding files in `/memories/` (Memory Tool)
4. Renames original files to `.backup` (not deleted)
5. Validates migration success
6. Continues using Memory Tool paths

---

## Backward Compatibility

If Memory Tool is not available or disabled:
- Validation framework falls back to local `.protocol-state/validation/` files
- Full functionality maintained (snapshots, validation, metrics)
- Performance slightly reduced (no cross-session persistence across context clears)

---

## File Descriptions

### validation-state.json
Central validation tracking file containing:
- State file integrity checksums
- Tier validation statistics
- Agent coordination tracking
- Drift detection results

**Schema**: See `protocol/validation-rules.yaml`

### snapshots/
Context snapshot storage directory:
- Tier 1: Max 10 snapshots (manual only)
- Tier 2: Max 30 snapshots (every 10 operations)
- Tier 3: Max 50 snapshots (continuous)
- Compressed with gzip (~70% size reduction)

### validation-config.yaml
User overrides for validation settings (optional):
- Auto-fix confidence thresholds
- Snapshot frequency overrides
- Per-agent validation customization
- Performance tuning parameters

### validation-report.md
Human-readable validation report:
- Latest validation results
- Auto-fix summary
- Drift detection alerts
- Tier compliance status

### metrics.json (Sukuna)
Validation effectiveness metrics:
- Context recall accuracy
- Recovery time statistics
- Self-healing rate by issue type
- Tier compliance rates

### tuning-history.json (Sukuna)
Automatic tuning log:
- Threshold adjustments (with user approval timestamps)
- Performance optimizations applied
- Learned rule additions
- Metrics improvement tracking

### learned-rules.yaml (Sukuna)
Auto-discovered fix patterns:
- Pattern detection from manual fixes
- Confidence scores per rule
- Success rates
- User approval status

---

## Gitignore Rules

**This directory should be GITIGNORED**:
```gitignore
# .gitignore
.protocol-state/validation/
```

**Rationale**:
- Contains session-specific state (not project artifacts)
- Snapshots are user-specific (context recovery)
- Metrics are installation-specific (not shared)

**Exception**: `validation-config.yaml` may be committed if team wants shared configuration.

---

## Storage Considerations

**Typical Storage Usage**:
- validation-state.json: ~50-100KB
- validation-report.md: ~10-20KB
- metrics.json: ~200-500KB (30 sessions of history)
- tuning-history.json: ~100KB
- learned-rules.yaml: ~50KB
- snapshots/: 1-5MB per snapshot

**Total Expected**: 50-200MB for active development project

**Cleanup**:
- Old snapshots auto-deleted when max count exceeded
- Metrics history truncated to last 100 sessions
- Tuning history kept indefinitely (valuable for analysis)

---

## Troubleshooting

**Issue**: Validation state corrupted
**Solution**: Rollback to snapshot or delete `.protocol-state/validation/` (will reinitialize)

**Issue**: Snapshots consuming too much storage
**Solution**: Reduce max snapshots in `validation-config.yaml`

**Issue**: Memory Tool migration failed
**Solution**: Check `.protocol-state/validation/*.backup` files for recovery

---

**Last Updated**: 2025-12-05 (v8.8.0)
