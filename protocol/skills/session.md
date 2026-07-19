<!-- [CORE FILE] - Domain Zero Protocol v9.10.0 -->
# Session Management Skill
## Unified Interface for Work Session Tracking

**Version**: 2.1.0
**Agent(s)**: Gojo (Mission Control)
**Category**: Session Management
**Risk Level**: Medium (code execution via Python)
**Token Efficiency**: High (replaces manual session_monitor.py commands)

---

## Purpose

Provides unified skill interface for session_monitor.py operations with integrated checkpoint file updates. Gojo-owned skill due to domain.record.md write access requirement.

**Use when:**
- Starting/ending work sessions
- Recording breaks during extended work
- Updating project checkpoints (session state, dev notes, domain record)
- Checking session status for alerting

---

## Prerequisites

- [ ] `.protocol-state/session_monitor.py` exists
- [ ] `.protocol-state/project-state.json` exists (consolidated state - auto-created if missing)
- [ ] **PATCH-STATE-001**: Uses consolidated `project-state.json::session_tracking` namespace (fallback to legacy `session-state.json` for backward compatibility)
- [ ] Python 3.8+ available
- [ ] Gojo agent context (domain.record.md write access)

**ESCAPE PATH**: If prerequisites fail:
1. If session_monitor.py missing: Error with path to installation docs
2. If Python unavailable: Suggest manual session tracking
3. Continue with available commands (graceful degradation)

---

## Commands

### /session start

**Action**: Start new work session and activate Domain Zero Protocol

**Implementation**:
```bash
# Step 1: Start session monitoring (safety/session state is first)
python .protocol-state/session_monitor.py start

# Step 2: Mandatory-attempt Cortex-first RECALL (v9.1.0, fail-soft — per Cortex Integration Contract)
#   scripts/brain.ps1 status          # POSIX: scripts/brain.sh status
#   if ok: scripts/brain.ps1 query "current open tasks, blockers, last decisions"
#   if unavailable: report "Cortex unavailable - proceeding without recall" and continue.
#   Surfaces prior context as cited evidence before reading large docs.

# Step 3: Activate Domain Zero Protocol
Read ./CLAUDE.md
```

**Output**:
- Session ID and start timestamp
- Full DZP protocol activation (all agent rules, restrictions, workflows)
- Cortex recall of recent open work (best-effort; omitted if Cortex unavailable)

**State Updates** (PATCH-STATE-001):
- `project-state.json::session_tracking`: Creates/updates current session (consolidated namespace)
- Backward compatible: Falls back to `session-state.json` if consolidated state unavailable
- `domain.record.md`: Logs session start (Gojo only)

**Workflow**:
1. Initialize session monitoring (Python script)
2. Attempt Cortex-first recall (status-gated, fail-soft)
3. Read ./CLAUDE.md to load complete DZP context
4. Agents now have full protocol awareness for the session

---

### /session status

**Action**: Display current session summary

**Implementation**:
```bash
python .protocol-state/session_monitor.py status
```

**Output**:
- Session duration
- Continuous work time
- Breaks taken
- Alert status
- High-risk operation blocking status

**State Updates**: None (read-only)

---

### /session update

**Action**: Core full-sync orchestrator — project documents + Cortex re-index + timestamp

**Role (v9.1.0)**: `/session update` is the CORE SYNC command. It does substantially more than a timestamp update: it runs the full project-document sync pipeline, then triggers a mandatory-attempt Cortex incremental re-index. Use `--time-only` to preserve the old fast-path for internal callers (e.g., session-check) that only need the timestamp refreshed.

**Implementation**:
```bash
# Standard full sync (recommended — runs all steps below)
DZP_AGENT=gojo python .protocol-state/session_monitor.py sync

# Sync without git operations
DZP_AGENT=gojo python .protocol-state/session_monitor.py sync --no-git

# Fast path: timestamp-only (for internal callers; skips document sync + Cortex)
DZP_AGENT=gojo python .protocol-state/session_monitor.py update --time-only
```

**Execution Order (full sync)**:
1. **Timestamp update** — refresh `session_tracking.last_interaction_time` in `project-state.json`
2. **Full project-document sync** — sync all protected docs (see below)
3. **Secret scan** — scan in-memory content before any write (prepare-scan-write pipeline)
4. **Backups** — timestamped backups created before writes (Protection Rule 4)
5. **Cortex incremental re-index** — mandatory-attempt, fail-soft (see below)
6. **Git commit/push** — APPROVAL-GATED: prompted, never automatic

**Project Documents Synced** (ALL CONTENT, NOT JUST METADATA):
1. **`.dzp-domain/domain.record.md`** - Strategic notes, session checkpoints, decisions log (Gojo permission required)
2. **`.protocol-state/project-state.json`** - Full project state via ProjectStateManager (atomic operations)
3. **`.protocol-state/dev-notes.md`** - Implementation log, completed features, pending tasks
4. **`.protocol-state/security-review.md`** - Security audit trail, findings, SEC-ID tracking

**Cortex Re-Index (v9.5.0 / WI-29) — ROUTED THROUGH COORDINATOR, FAIL-SOFT**:

Per Phase 5b (WI-29), `/session update` now routes its Cortex step through the coordinator rather than calling `brain.ps1/sh` directly. The coordinator fires the Cortex step exactly once:

```bash
# v9.5.0+ — full sync via coordinator (single Cortex trigger)
python dzp.py event session-update
```

The coordinator chains: `session_monitor.py sync` (DZP_AGENT=gojo) → `cortex-medium` (cortex_trigger.py --level medium --reason session-update) → `custom-agent-list` + `tier-status` + `tier-statistics` (all fail-soft).

- **Single-trigger**: coordinator owns the one Cortex path — no direct `brain.ps1/sh index` call
- **Fail-soft**: Cortex error never blocks the overall sync
- **Never writes protected docs**: Cortex is a derived index, never canonical

Reindex scope per invocation (BUG-CORTEX-008 R3, 2026-07-13):
- `/session update` → **incremental** (only changed/new chunks, via cortex_trigger.py --level medium)
- `/session end` → **incremental** (`--level medium`, no export — see /session end). The full rebuild + export no longer runs at session-end; it moved to the manual/periodic `cortex-rebuild-full` event to avoid the embedding-delta-bound timeout that used to fire chronically right after a session's largest content delta.

Reindex scope per invocation:
- `/session update` → **incremental** (only changed/new chunks)
- `/session end` → **incremental** (see /session end); full rebuild is now a separate manual/periodic step (`python dzp.py event cortex-rebuild-full`)

**Secret Patterns Detected**:
- API Keys (32+ characters)
- AWS Keys (AKIA...)
- GitHub Tokens (ghp_...)
- Connection Strings (mongodb://, postgres://, mysql://)
- Password Assignments

**Git Operations Workflow** (APPROVAL-GATED, not automatic):
1. Scan all documents for secrets
2. If high-confidence secrets found: abort commit with warning
3. If clean: prompt user for approval
4. On approval: commit with message `chore(session): Project documents checkpoint sync`
5. Push to remote: user choice (yes / local-only / skip)

**Use Cases**:
- Manual checkpoint during long work sessions
- Before taking break (preserve context)
- After completing significant milestone
- Before context compaction (save state)
- Ensure project documents are backed up to GitHub

**ESCAPE PATH**:
- If ProjectStateManager unavailable: Fall back to legacy file I/O
- If secret scanning fails: Log warning, continue without scan
- If Cortex unavailable/errors: Log "Cortex re-index skipped", continue — NEVER blocks sync
- If git operations fail: Log error, documents still synced locally
- Non-blocking operation (best-effort sync)

**Protection Rules** (NON-NEGOTIABLE):
- ❌ **NEVER OVERWRITE** - Project documents are append-only
- ✅ **BACKUP BEFORE EDIT** - Timestamped backups created automatically
- ✅ **NO TEMPLATE RESETS** - Never reset to template state
- ✅ **VERSION CONTROL** - Git commit/push recommended but approval-gated (never automatic)

---

### /session break [minutes]

**Action**: Record break duration

**Implementation**:
```bash
# Default: 15 minutes
python .protocol-state/session_monitor.py break 15

# Custom duration
python .protocol-state/session_monitor.py break 30
```

**Validation**: Duration must be 1-480 minutes (8 hours)

**State Updates** (PATCH-STATE-001):
- `project-state.json::session_tracking`: Adds break timestamp, resets escalation
- Backward compatible: Falls back to `session-state.json` if needed
- `domain.record.md`: Logs break (Gojo only)

---

### /session continue

**Action**: Resume work after break

**Implementation**:
```bash
python .protocol-state/session_monitor.py continue
```

**Output**: Resume timestamp and total session time

**State Updates** (PATCH-STATE-001):
- `project-state.json::session_tracking`: Updates last interaction timestamp
- Backward compatible: Falls back to `session-state.json` if needed

---

### /session end

**Action**: End current session, archive state, incremental Cortex re-index

**Implementation**:
```bash
# End session — v9.5.0+ routes through coordinator (WI-29)
# Coordinator chains: session_monitor.py end (DZP_AGENT=gojo)
#                     + end-snapshot + cortex-medium (incremental re-index, no export)
python dzp.py event session-end
```

**BUG-CORTEX-008 R3 (2026-07-13)**: `/session end`'s Cortex step is **incremental**
(`--level medium`, no `--export`, **90-second timeout**), not a full rebuild. The full `--level high` rebuild +
export snapshot moved to a separate, manually/periodically invoked event —
`python dzp.py event cortex-rebuild-full` — to keep session-end off a chronic
embedding-delta-bound timeout (the full rebuild's cost scales with how much NEW
content was just embedded, and session-end fires immediately after the session's
own largest content delta — the worst possible moment to run it synchronously).
See `internal-docs/Patch Report/Bug Report/BUG-CORTEX-008-sessionend-high-rebuild-timeout-2026-07-13.md`
§8/§10 for the full root-cause analysis and design. Run `cortex-rebuild-full`
weekly, or whenever a fresh exported snapshot matters (e.g. before a Toji audit),
or when `brain status` shows notable index drift.

**State Files Updated** (PATCH-SESSION-005 - Extensions 2 & 3, PATCH-STATE-001):
1. **project-state.json::session_tracking** - Archives session to history, resets current session (consolidated)
2. **project-state.json** - Updates total sessions count, total work minutes
3. **dev-notes.md** - Logs session end with metrics, security review event
4. **domain.record.md** - Logs session completion with wellbeing metrics (Gojo permission only via DZP_AGENT env var)

**Note (PATCH-STATE-001)**: Uses consolidated `project-state.json::session_tracking` namespace. Falls back to legacy `session-state.json` for backward compatibility.

**Output**: Session summary (duration, breaks, alerts)

**Note**: `DZP_AGENT=gojo` environment variable grants temporary Gojo permission for domain.record.md updates. All other state files are updated regardless of this variable.

**Cortex Incremental Re-Index (v9.5.0 / WI-29, revised by BUG-CORTEX-008 R3 2026-07-13) — ROUTED THROUGH COORDINATOR, FAIL-SOFT**:

Per Phase 5b (WI-29), `/session end` routes its Cortex step through the coordinator:

```bash
# v9.5.0+ — end session via coordinator (incremental re-index, R3)
python dzp.py event session-end
```

The coordinator chains: `session_monitor.py end` (DZP_AGENT=gojo, required) → `end-snapshot` (fail-soft) → `cortex-medium` (fail-soft, **incremental** re-index, no export, **90-second timeout** — BUG-CORTEX-008 R3).

**PARITY NOTE**: Session-tracking / wellbeing logging / domain.record.md write are NOT lost — the coordinator `session-end` step runs `session_monitor.py end` with `DZP_AGENT=gojo`.

**R3 NOTE (2026-07-13)**: `/session end` previously ran a full `--level high --export` rebuild here (WI-29, restoring a 2026-06-17 regression). That full rebuild is now a **separate** event — `python dzp.py event cortex-rebuild-full` — invoked manually or periodically, because running it synchronously at session-end collided with the session's own largest embedding delta and chronically timed out. See BUG-CORTEX-008 §8/§10 for the analysis. The exported snapshot is no longer refreshed automatically every session-end; run `cortex-rebuild-full` (or `scripts/brain.ps1 export --snapshot` after a manual `brain index`) to refresh it.

To store a distilled session-outcome fact before ending, run manually before the coordinator:
```bash
# Windows (POSIX: scripts/brain.sh) — optional, before python dzp.py event session-end
scripts/brain.ps1 remember "<session outcome: what shipped / decided>" --type decision --agent gojo
```

Best-effort: on any Cortex error, log and continue — session end is never blocked. Cortex never writes the protected docs.

**Toji snapshot** (`export --snapshot`) is **no longer** generated automatically at session-end (R3). To produce a fresh snapshot for Toji audits, **prefer** the lighter-weight `python dzp.py event toji-snapshot` (does `--level medium --export` — faster, sufficient for routine snapshot refresh); use the heavier `python dzp.py event cortex-rebuild-full` (full rebuild + export) or `scripts/brain.ps1 export --snapshot` / `scripts/brain.sh export --snapshot` directly (export only, against whatever is currently indexed) only when a full re-embed is actually needed.

---

## Checkpoint Update Workflow

When `/session update` is invoked, perform checkpoint sync:

### Step 1: Read Current State

```bash
# Read recent context from key files
tail -20 .protocol-state/dev-notes.md
cat .protocol-state/project-state.json
```

### Step 2: Generate Checkpoint Entry

**Format**:
```markdown
---
## {timestamp} - Session Checkpoint
**Session Duration**: {duration_formatted}
**Continuous Work**: {continuous_minutes} minutes
**Active Work**:
- {current_task_1}
- {current_task_2}
```

### Step 3: Update Checkpoint Files

**dev-notes.md**:
```bash
# Append checkpoint entry
echo "\n---\n## $(date -Iseconds) - Session Checkpoint\n**Session Duration**: ... \n" >> .protocol-state/dev-notes.md
```

**project-state.json::session_tracking** (PATCH-STATE-001 consolidated):
```json
{
  "session_tracking": {
    "current_session": {
      "last_interaction_time": "2025-12-28T20:00:00Z"
    },
    "last_updated": "2025-12-28T20:00:00Z"
  }
}
```

Note: Uses consolidated `session_tracking` namespace. Legacy `session-state.json` format supported for backward compatibility.

**domain.record.md** (Gojo only):
```markdown
---
## Session Checkpoint - {timestamp}
**Duration**: {duration} | **Continuous**: {continuous}
**Strategic Context**: {extract_from_recent_domain_record_entries}
```

**security-review.md** (if applicable):
```markdown
---
## {timestamp} - Security Checkpoint
**Status**: {active_security_work_summary}
```

**ESCAPE PATH**:
- If any file write fails: Log warning, continue with others
- If all files fail: Error with permission/path diagnostics
- Checkpoint sync is best-effort, not critical path

---

## Usage Examples

### Start Session
```bash
skill: "session"
args: "start"

# Or via slash command:
/session start
```

### Check Status Mid-Session
```bash
/session status
```

### Manual Checkpoint Before Break
```bash
/session update
/session break 15
```

### Resume After Break
```bash
/session continue
```

### End Session
```bash
/session end
```

---

## Integration with Session Monitoring

**Automatic Alerts**: Session monitor issues alerts at:
- 4 hours (initial alert)
- 6 hours (critical threshold - enables high-risk operation blocking)
- 8 hours (maximum - enforces read-only mode)

**Alert Workflow**:
1. Session monitor detects threshold
2. Gojo receives alert via `check_alert_needed()`
3. Gojo prompts user with `/session break` or `/session end`
4. If user continues: escalation level increases

**High-Risk Operation Blocking**:
- Blocks: `git push production`, `terraform destroy`, `npm publish`, etc.
- Triggered at 6+ hour sessions
- Cleared after sufficient break (15+ minutes)

---

## State File Schemas

### project-state.json::session_tracking (PATCH-STATE-001 Consolidated)
```json
{
  "session_tracking": {
    "current_session": {
      "session_id": "session_20251228_200000",
      "session_active": true,
      "start_time": "2025-12-28T20:00:00Z",
      "last_interaction_time": "2025-12-28T20:30:00Z",
      "alert_count": 0,
      "escalation_level": 0,
      "high_risk_operations_blocked": false
    },
    "session_metrics": {
      "total_duration_minutes": 30,
      "continuous_work_minutes": 30,
      "break_timestamps": [],
      "total_breaks": 0,
      "alerts_issued": 0
    },
    "thresholds": {
      "initial_alert_minutes": 240,
      "critical_session_minutes": 360,
      "max_continuous_minutes": 480
    },
    "last_updated": "2025-12-28T20:30:00Z"
  }
}
```

**Migration Note**: Legacy `session-state.json` supported for backward compatibility. Run `python .protocol-state/migrate_state_consolidation.py --execute` to consolidate.

---

## Error Handling

**Command Failures**:
- **session_monitor.py not found**: Provide installation instructions
- **Python not available**: Suggest manual tracking alternatives
- **Permission denied**: Check file permissions in `.protocol-state/`
- **Corrupted state file**: Auto-reset with backup creation

**Graceful Degradation**:
- If checkpoint file unreachable: Skip that file, continue with others
- If domain.record.md locked: Skip (non-critical for session ops)
- Session operations continue even if logging fails

---

## Changelog

### 2.2.0 (2026-07-13)
- BUG-CORTEX-008 R3 (durable fix): `/session end`'s Cortex step changed from a synchronous full `--level high --export` rebuild to an **incremental** `--level medium` re-index (no export) — removes the chronic embedding-delta-bound timeout that fired right after a session's own largest content delta
- Added the manual/periodic `cortex-rebuild-full` event (`python dzp.py event cortex-rebuild-full`) carrying the full rebuild + export that used to run at session-end; DZP remains no-daemon — this is a user-invoked maintenance step, not an automated scheduler
- Updated all "full rebuild" references in this doc to reflect the new incremental behavior and the export-freshness trade-off (snapshot no longer auto-refreshes every session-end)

### 2.1.0 (2026-06-14)
- `/session update` promoted to CORE FULL-SYNC orchestrator (v9.1.0)
- Added mandatory-attempt fail-soft Cortex incremental re-index step (per Cortex Integration Contract)
- Added `--time-only` flag for internal callers (timestamp-only fast path, skips sync + Cortex)
- Clarified git commit/push is APPROVAL-GATED, never automatic
- Documented execution order: timestamp → document sync → secret scan → backups → Cortex index → git (prompted)
- Full rebuild (`brain index`) deferred to `/session end`; incremental on `/session update`
- Added status-gate: only attempt full index if `brain status` exits 0

### 1.0.0 (2025-12-28)
- Initial release for v8.11.0
- Commands: start, status, update, break, continue, end
- Integrated checkpoint file updates (update command)
- Gojo-owned skill (domain.record.md access)
- Direct session_monitor.py invocation (no agent coordination overhead)

---

**Status**: Production-Ready
**Maintenance**: Update when session_monitor.py adds new commands or thresholds change
