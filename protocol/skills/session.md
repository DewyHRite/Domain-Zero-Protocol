<!-- [CORE FILE] - Domain Zero Protocol v9.12.0 -->
# Session Management Skill
## Unified Interface for Work Session Tracking

**Version**: 2.5.2
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
- [ ] Python 3.9+ available (IMPL-002, 2026-08-06 Toji audit: `session_monitor.py` unconditionally imports the stdlib `zoneinfo` module, added in 3.9 -- this is this project's real floor, matching `requirements-clock.txt`)
- [ ] Gojo agent context (domain.record.md write access)

**ESCAPE PATH**: If prerequisites fail:
1. If session_monitor.py missing: Error with path to installation docs
2. If Python unavailable: Suggest manual session tracking
3. Continue with available commands (graceful degradation)

---

## Time envelope contract (v9.12.0 A4, ADR D5 — Toji gate 4)

`docs/superpowers/specs/2026-08-04-clock-authority-adr.md` decision D5 defines a single, versioned,
provider-neutral **time envelope** — closing `audits/2026-08-01-toji-session-time-authority-claude-codex.md`
finding AI-001 (HIGH): Claude/Codex previously had no authoritative, structured time context and
could misread a UTC-stamped session ID as local wall time (the 2026-07-30/31 incident this ADR
answers).

**Seven lifecycle boundaries emit it** — `start`, `status`, `check` (including the MANDATORY
auto-invoked `check-and-record`, which shares the `check` boundary), `resume`/`continue`,
`transfer-begin`, `transfer-finalize`, and `handoff` — via a `--json` flag on the corresponding
`session_monitor.py` command (documented per-command below). **`--json` replaces the normal prose
output entirely — it never appears alongside it** — one parseable JSON document on stdout, matching
the ADR's `envelope_schema: 1` field table exactly (`envelope_status`/`envelope_status_reasons`,
`session.session_id_is_opaque`, `user_zone`, `local_wall_time`, `gap`/`continuity`, `work_streak`,
`late_night`, `alert.reasons`, `clock_health`). **Omitting `--json` leaves every command's existing
prose output byte-for-byte unchanged** — this is deliberate backward compatibility for a human
reading a terminal directly, proven by `tests/test_session_monitor_envelope.py::TestCliJsonFlag`.

**`--json` is the DEFAULT/PRIMARY form for provider consumption, not an optional alternate (Toji audit
2026-08-06, AI-001 HIGH direct fix)**: prior to this remediation, `check-and-record` — the MANDATORY
auto-invoked path named by `protocol/skills/session-check.md`, run on EVERY Gojo Mission Control
activation — had NO `--json` branch at all, so a provider following the documented default command
could only ever receive prose, defeating the D5.3 relay rule below in the one place it is supposed to
be unconditionally enforced. `check-and-record --json` now exists and MUST be the command Gojo/Claude/
Codex actually invoke for this mandatory path; the plain-prose `check-and-record` (no `--json`) is a
legacy/human-readable rendering, never the primary implementation.

**Binding provider relay rule (ADR D5.3, direct AI-001 fix)**: Claude and Codex MUST invoke the
`--json` form of every named lifecycle command (`start`, `status`, `check-and-record`, `resume`/
`continue`, `transfer-begin`, `transfer-finalize`, `handoff`) and relay envelope fields verbatim in
any prose that makes a time-sensitive claim (`local_wall_time.display`, `gap.formatted`,
`continuity.class`, `late_night.is_late_night`, `alert.reasons`) — **never reconstruct, infer, or
restate time from a session ID, prior-turn prose, or the model's own training-time/runtime notion of
"now."** When `envelope_status` is `degraded` or `unavailable` — or `--json` fails to produce
parseable JSON at all — this is an explicit DEGRADED condition: prose MUST say timing information is
degraded/unavailable (citing `envelope_status_reasons` when present) rather than silently falling
back to the prose-only command's output as if it were an equivalent substitute. When
`user_zone.source == "os-fallback"`, local time MUST be qualified as unconfirmed. Session IDs remain
**opaque** identifiers under this contract (`session.session_id_is_opaque: true` is always present as
a standing reminder) — no consumer may parse wall time or elapsed time from one; the authoritative
instant is always `authoritative_instant_utc` / the appropriate `session_boundaries.*` field.

**Alert reason codes (ADR D6.4/D6.5, direct IMPL-001 fix)**: `check`'s alert result now carries a
combinable **list** of reason codes (`context['alert_reasons']` / envelope `alert.reasons`) —
`duration_initial`, `duration_escalated`, `duration_critical`, `duration_maximum`, `late_night` —
instead of a single `alert_level` string. Late night is now an **independent** trigger: a fresh
(0-minute) session starting at/after the configured late-night hour now produces a checkpoint on
its own, even with zero duration-threshold contribution (previously `is_late_night` was inert
context only — see `tests/test_alert_reason_codes.py` and the "FIXED (v9.12.0 A4)" note in
`tests/test_session_monitor_time_characterization.py`). `alert_level` (the pre-existing single-value
field) is retained unchanged for existing consumers.

---

## Commands

### /session start

**Action**: Start new work session and activate Domain Zero Protocol

**Implementation**:
```bash
# Step 0 (v9.11.0, FEAT-TRANSFER-9.11.0-001): if .protocol-state/session-handoff.md
# exists and postdates the last session start, READ IT FIRST - it is the cheapest
# high-value context in the tree (session_monitor.py start also warns loudly if a
# session-handoff.INCOMPLETE marker exists, and names the keyed retry command)

# Step 1 (PRIMARY, Toji audit 2026-08-06 AI-001 fix): Start session monitoring
# (safety/session state is first) -- structured envelope, per this file's
# "Time envelope contract" section above
python .protocol-state/session_monitor.py start --json

# Step 2: Mandatory-attempt Cortex-first RECALL (v9.1.0, fail-soft — per Cortex Integration Contract)
#   scripts/brain.ps1 status          # POSIX: scripts/brain.sh status
#   if ok: scripts/brain.ps1 query "current open tasks, blockers, last decisions"
#   if unavailable: report "Cortex unavailable - proceeding without recall" and continue.
#   Surfaces prior context as cited evidence before reading large docs.

# Step 3: Activate Domain Zero Protocol — read the REPOSITORY-ROOT CLAUDE.md
# (canonical; protocol/CLAUDE.md is a compatibility stub since v9.11.0)
Read CLAUDE.md
```

**Legacy/human-readable form (NOT the primary implementation)**: `python .protocol-state/session_monitor.py start`
(no `--json`) still produces the pre-A4 prose byte-for-byte unchanged, for a human reading a terminal
directly. A provider consuming output for its own time reasoning MUST still obtain the authoritative
fields via `--json` per the relay rule above.

**Output** (`--json` form): the ADR D5 envelope (`boundary: "start"`) — see "Time envelope contract"
section above. Relay per D5.3; never reconstruct time from the session ID. Envelope absence
(`envelope_status != "complete"`, or `--json` failing to produce parseable JSON) is an explicit
degraded condition, never silently treated as equivalent to the prose form.

**Output** (legacy prose form):
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
3. Read the repository-root CLAUDE.md to load complete DZP context
4. Agents now have full protocol awareness for the session

---

### /session status

**Action**: Display current session summary

**Structured time envelope is the DEFAULT/PRIMARY form (v9.12.0 A4, ADR D5 — Toji gate 4; Toji
audit 2026-08-06 `AI-001` HIGH direct fix, closing the "status still bypasses the envelope"
finding)**: `status --json` emits the ADR D5 envelope (`boundary: "status"`) — see "Time envelope
contract" section above. Providers (Claude, Codex) MUST invoke `status --json` and relay envelope
fields verbatim; never reconstruct local time, elapsed time, or session freshness from the session
ID. Envelope absence (`envelope_status` `degraded`/`unavailable`, or `--json` failing to produce
parseable JSON) is an explicit DEGRADED condition — state that timing information is
degraded/unavailable rather than silently falling back to the legacy prose form below as if it
were an equivalent substitute.

**Implementation**:
```bash
python .protocol-state/session_monitor.py status --json
```

**Legacy/human-readable form (NOT the primary implementation)**: omitting `--json` still produces
the pre-A4 prose byte-for-byte unchanged, for a human directly reading a terminal.
```bash
python .protocol-state/session_monitor.py status
```

**Output** (legacy prose form):
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

Reindex scope per invocation (BUG-CORTEX-008 R3 2026-07-13, DETACHED by R5 2026-07-18):
- `/session update` → **incremental** (only changed/new chunks, via cortex_trigger.py --level medium)
- `/session end` → **incremental** (`--level medium`, no export — see /session end). The full rebuild + export no longer runs at session-end; it moved to the manual/periodic `cortex-rebuild-full` event to avoid the embedding-delta-bound timeout that used to fire chronically right after a session's largest content delta.

Both Cortex steps run **detached** (`detach: true`, R5 2026-07-18): the
coordinator launches them off its critical path and they report `launched`, not
`succeeded`. A stalled or failed index is therefore reported by the
post-detach liveness assertion in `cortex_trigger.py`, not by an exit code.

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

**Action**: Record that a break STARTED (break INITIATION only)

**Toji audit 2026-08-06 (SEC-002, HIGH direct fix, ADR D3.1/D7.4/D7.5's lifecycle-event contract)**:
this command previously treated a caller-supplied `[minutes]` as sufficient, on its own, to
immediately clear both `current_session.high_risk_operations_blocked` and the durable `work_streak`
protection window — an unverified CLAIM, not a measured elapsed-time pair. It no longer does either.

`break [minutes]` is now purely the **break-initiation** half of a two-instant lifecycle pair ("the
existing break → continue lifecycle is the natural pair", ADR D7.4): it records
`current_session.pending_break_started_utc` (this call's own authoritative instant) plus bookkeeping
(break count/timestamp history, continuous-work-timer reset, escalation reset), but makes **no**
protection decision. `[minutes]` is recorded ONLY as an informational note
(`pending_break_reported_minutes`) — it is **never** used to authorize clearing protection.

The **completion** half — the actual qualification check, measured against two authoritative,
clock-health-gated instants (`pending_break_started_utc` and the later `continue`/interaction
instant) — happens the next time `update_interaction()` runs: `/session continue` (below), or any
other recorded interaction. Protection is preserved on missing, future, rollback-detected,
implausible, or incomplete break evidence.

**Implementation**:
```bash
# Default: 15 minutes (note-only -- does NOT by itself clear protection)
python .protocol-state/session_monitor.py break 15

# Custom duration (still note-only)
python .protocol-state/session_monitor.py break 30
```

**Validation**: Duration must be 1-480 minutes (8 hours) — validated as before; only its
AUTHORIZATION role changed (SEC-002).

**State Updates** (PATCH-STATE-001 + SEC-002):
- `project-state.json::session_tracking`: Adds break timestamp, resets escalation, resets continuous
  work timer, sets `current_session.pending_break_started_utc` + `pending_break_reported_minutes`
- Protection is **NOT** touched here — see `/session continue` below
- Backward compatible: Falls back to `session-state.json` if needed
- `domain.record.md`: Logs break (Gojo only)

---

### /session continue

**Action**: Resume work after break — this is also where a pending break is VERIFIED and protection
is actually cleared (SEC-002)

**Structured time envelope is the DEFAULT/PRIMARY form (v9.12.0 A4, ADR D5 — Toji gate 4; Toji
audit 2026-08-06 `AI-001` HIGH direct fix, closing the "resume still bypasses the envelope"
finding)**: `continue --json` (alias `resume --json`) emits the ADR D5 envelope (`boundary:
"resume"`) — see "Time envelope contract" section above. Providers (Claude, Codex) MUST invoke
`continue --json` and relay envelope fields verbatim; never reconstruct local time, elapsed time,
or session freshness from the session ID. Envelope absence is an explicit DEGRADED condition —
state that timing information is degraded/unavailable rather than silently falling back to the
legacy prose form below as if it were an equivalent substitute.

**Toji audit 2026-08-06 (SEC-002 completion half)**: if `current_session.pending_break_started_utc`
is set (from a prior `/session break`), this command measures the health-gated elapsed gap between
that instant and now. Only when that gap is clock-health `ok` AND meets `minimum_break_minutes` does
protection actually clear (`high_risk_operations_blocked = false`, the durable `work_streak` closes).
Otherwise the pending marker is cleared (resolved either way) but protection is **preserved** — a
break immediately followed by continue (near-zero real elapsed time, the exact SEC-002 exploit shape)
does NOT qualify, regardless of the `[minutes]` claimed at `break` time.

**Implementation**:
```bash
python .protocol-state/session_monitor.py continue --json
```

**Legacy/human-readable form (NOT the primary implementation)**: omitting `--json` still produces
the pre-A4 prose byte-for-byte unchanged, for a human directly reading a terminal.
```bash
python .protocol-state/session_monitor.py continue
```

**Output** (legacy prose form): Resume timestamp and total session time; if a pending break was
verified as qualifying, an additional `[OK] SEC-002: qualifying break verified (... min measured,
>= ... min required) -- protection cleared.` line; if a pending break did NOT qualify, a `[!]
SEC-002: break not verified as qualifying (...)` line to stderr (protection status unchanged).

**State Updates** (PATCH-STATE-001 + SEC-002/IMPL-001):
- `project-state.json::session_tracking`: Updates last interaction timestamp
- Resolves any pending break (see above) — clears `pending_break_started_utc`
- IMPL-001: on a VERIFIED qualifying break, advances
  `current_session.streak_contribution_start_time` to the verification instant, so subsequent work-
  streak accumulation measures only POST-break minutes — never re-accumulating the pre-break work
  the qualifying break just closed
- Backward compatible: Falls back to `session-state.json` if needed

---

### /session end

**Action**: End current session, archive state, incremental Cortex re-index

**Implementation**:
```bash
# End session — v9.5.0+ routes through coordinator (WI-29)
# Coordinator chains: session_monitor.py end (DZP_AGENT=gojo)
#                     + end-snapshot + cortex-medium (incremental re-index, no export)
#                     + cortex-distill (propose-only) + validation-refresh (ledger refresh, v9.10.2)
python dzp.py event session-end
```

**BUG-CORTEX-008 R5 (2026-07-18) - SUPERSEDES R3 BELOW**: the Cortex step is
**DETACHED** (`detach: true` in `.protocol-state/script_dependencies.yaml`).
It is launched fire-and-forget off the coordinator's critical path and returns
`launched` immediately. **There is no longer an effective timeout**: the
`timeout_seconds: 90` still present in that file is a *detach-disabled fallback
only*, consulted solely if `detach` is ever removed or set false. R3's premise
-- that switching to `--level medium` alone would fix the stall -- was
disproven by the same timeout class recurring on medium; Cortex re-index cost
is embedding-DELTA-bound, not corpus-size-bound, so the run immediately after a
session's largest content delta starves any budget. Detaching removes the step
from the critical path instead of racing a bigger budget.

**Consequence you must know about.** Removing the timeout also removed **the
only signal that the index failed**. A detached step reports `launched` and
nothing ever reports what happened next. Observed live in canonical: an
orphaned `index.lock` from an interrupted detached run caused every subsequent
run to log `index hook skipped; lock exists` and then go silent for hours -
nothing failed, nothing warned, and `brain status` still answered `ok`.

Mitigation (v9.11.0): `cortex_trigger.py` now performs a **post-detach liveness
assertion**. Each run records the `last_index` stamp it observed *before*
launching an index; the next run compares, and if `last_index` has not advanced
it prints a loud `[CORTEX-TRIGGER:index-liveness] WARNING`. It is **advisory
only** and never changes an exit code - a liveness probe that could break the
run would be worse than the silence it replaces. If you see that warning, check
for a stale `index.lock` beside `brain.db`.

**BUG-CORTEX-008 R3 (2026-07-13) - HISTORICAL, superseded by R5 above**: `/session end`'s Cortex step is **incremental**
(`--level medium`, no `--export`), not a full rebuild. The full `--level high` rebuild +
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

The coordinator chains: `session_monitor.py end` (DZP_AGENT=gojo, required) → `end-snapshot` (fail-soft) → `cortex-medium` (fail-soft, **incremental** re-index, no export, **DETACHED / no effective timeout** — BUG-CORTEX-008 R5 2026-07-18; the `timeout_seconds: 90` in script_dependencies.yaml is a detach-disabled fallback only, and a post-detach liveness assertion is what reports a stalled index) → `cortex-distill` (fail-soft, propose-only) → `validation-refresh` (fail-soft, `scripts/validate-protocol.py --check --ci-mode`, 60s timeout — added v9.10.2, Toji finding `IMPL-001`: refreshes `validation-state.json` AFTER session-end's own state mutations so the validation ledger describes the terminal state instead of a stale pre-session-end `passed`; a failing or absent validator degrades to a warning and never fails the event).

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

### /session transfer

**Action**: `/session transfer` = **update + end + a durable handoff brief**, so the next session starts warm instead of losing the "why" behind the state files (FEAT-TRANSFER-9.11.0-001, v9.11.0 Increment 2).

**Problem it solves**: `/session end` + `/session start` technically transfers state, but the next session gets the state FILES, not a BRIEF. Reconstructing "what was I doing and why" costs the first twenty minutes of every resume. A long session can also degrade before it hits any wellbeing threshold — the per-session duration counter resets to zero at every `/session start`, so it structurally cannot see cross-session continuity (e.g. a 5h05m session ending at 01:58 followed by a new session starting at 02:02 looks, to the counter, like two unrelated sessions rather than one continuous 5h09m stretch).

**Wellness alerts now point here (v9.11.0)**: every wellness checkpoint (4h initial, 6h critical, 8h maximum, and escalated re-alerts) additionally recommends `/session transfer` alongside the existing save-and-break / continue recommendations — see `render_alert()` / `{SESSION_TRANSFER_TIP}` in `.protocol-state/work-session-alert.template.md`.

**Structured time envelope (v9.12.0 A4)**: each of the three CLI steps directly reachable by name
below — `transfer-begin`, `handoff`, `transfer-finalize` — accepts its own `--json` flag, emitting
the ADR D5 envelope for that boundary (`transfer_begin`/`handoff`/`transfer_finalize` respectively)
instead of its normal `[OK]`/`[ERROR]` prose. The coordinator-driven `python dzp.py event
session-transfer` path (below) is unaffected — envelope emission is an additional manual/diagnostic
capability on the underlying commands, not wired into the coordinator event itself in this
increment.

**Implementation**:
```bash
# Fail-closed event chain — event-level fail_soft: false is the LOAD-BEARING
# line (see .protocol-state/script_dependencies.yaml § session-transfer).
python dzp.py event session-transfer
```

**Execution order — fail-closed state machine (nine steps)**:

| # | Step | Required | Notes |
|---|---|---|---|
| 0 | `transfer-begin` | yes | writes `.protocol-state/session-handoff.INCOMPLETE` marker with the currently active session's id, BEFORE anything mutates |
| 1 | `session-update` (full sync) | yes | documents + secret scan + backups |
| 2 | `session-end` | yes | `DZP_AGENT=gojo`; archives the current session |
| 3 | `handoff-write` | yes | identity-checked against the just-archived session, writes the brief + archive copy, records `handoff-write` complete in the marker — **does NOT clear the marker** (IMPL-001, 2026-07-29 remediation; only step 5 below does) |
| 4 | `end-snapshot` | **yes** | mandatory (`ISS-TRANSFER-9.11.0-001`, USER directive) — durable post-transfer state capture under `.protocol-state/snapshots/`, readable by Toji for post-session audit (standing read access, no CLI needed) |
| 5 | `transfer-finalize` | **yes** | **the sole marker-clearer.** Records `end-snapshot` complete in the marker and clears the marker ONLY once every required step (`handoff-write`, `end-snapshot`) is recorded. Because this event is fail-closed, a failing `end-snapshot` breaks the loop BEFORE this step ever runs, so the marker correctly survives with only `handoff-write` recorded — durable, visible evidence that the mandatory snapshot (not the handoff) is what remains outstanding |
| 6 | `cortex-medium` | no | detached, non_blocking — indexes the handoff brief for next-session recall |
| 7 | `cortex-distill` | no | non_blocking, propose-only |
| 8 | `validation-refresh` | no | non_blocking AND `terminal_validator: true` (IMPL-001, 2026-07-30) — runs strictly AFTER the coordinator's own event-result bookkeeping write, so its checksum/attested-seq describe the TRUE terminal `project-state.json`, not a state the coordinator's own next write would immediately supersede |

**Why event-level `fail_soft: false` (not just `required: true`)**: per Toji `DESIGN-001` (2026-07-27), `required: true` on a step only sets a failure flag — it does **not** stop `script_coordinator.py`'s step loop (`if fail_closed: break` is the only thing that does, and `fail_closed = strict or not event_fail_soft`). Without the event-level flag, a failed `session-end` would still be followed by `handoff-write`, which — reading `session_history[-1]` — would durably record the **previous** session as the one just ended. Four independent mechanisms close this instead of one flag:

- **M1 — event fail-closed**: `session-transfer` declares `fail_soft: false` at the event level.
- **M2 — positive identity predicate**: `handoff-write` asserts `session_history[-1].session_id` matches the expected id and **refuses to write** on any mismatch.
- **M3 — incomplete-transfer marker**: `transfer-begin` writes `.protocol-state/session-handoff.INCOMPLETE` (session id + start timestamp) before anything else mutates. This is also how the expected id reaches `handoff-write` at all — the coordinator has no mechanism to pass a value computed by one step into a later step's command, so `handoff-write` falls back to reading the marker when no explicit `--expect-session-id` is given.
- **M4 — retry paths, keyed to marker state**: the marker's `steps_completed` list tells you exactly what to retry — never a one-size-fits-all command (see `session_monitor.py`'s `_warn_if_transfer_incomplete()`, which implements exactly this matrix):
  - **Neither `handoff-write` nor `end-snapshot` recorded** (or no marker-derivable progress at all): `python .protocol-state/session_monitor.py handoff --session-id <id>` regenerates the brief from the archived history record for that id. Idempotent, keyed to the id — the correct response to "session-end succeeded but handoff-write failed."
  - **`handoff-write` recorded, `end-snapshot` is not**: the brief already exists; only the mandatory snapshot is missing. Retry with `python .protocol-state/create-snapshot.py --auto --tier 2 --trigger session-transfer` followed by `python .protocol-state/session_monitor.py transfer-finalize`. Re-running `handoff` alone here is a no-op that can never complete the transfer.
  - **Both `handoff-write` and `end-snapshot` recorded but the marker was never cleared** (e.g. a crash between marking `end-snapshot` complete and clearing the marker): every required step is already done — finish directly with `python .protocol-state/session_monitor.py transfer-finalize` (no `--session-id` needed; it reads the marker's own session id).

**If the transfer is interrupted**: `/session start` checks for the `.INCOMPLETE` marker and warns loudly — before anything else — naming the exact retry command for whichever of the three states above applies (see `_warn_if_transfer_incomplete()`). If `session-handoff.md` exists and postdates the last recorded session start, `/session start` also points to it first (cheapest high-value context in the tree).

**Artifact**:
- `.protocol-state/session-handoff.md` — current brief, overwritten each transfer
- `.protocol-state/archive/handoff/session-handoff-<session_id>.md` — immutable per-session copy

**Deliberately NOT a protected document.** The three protected records are append-only; a handoff must be *replaced* to stay current. It is derived state, like `trigger-19.md` — gitignored, never shipped. The header of the generated artifact itself states this contract.

**Content**: machine-generated (session identity, final duration, breaks, alerts, escalation, cross-session continuity gap, branch/HEAD/working-tree summary, protocol version, Cortex status, domain-record line count vs rotation threshold) plus one clearly marked freeform section sourced from an optional `.protocol-state/session-handoff-notes.md` staging file (Gojo-authored: blocking gates, next queue, known drift, traps hit, a `START HERE:` pointer). Handoff content passes the same secret scan the protected docs get before any write.

**Double-end guard**: running `session-end` (bare, or as this event's own step 2) with no active session degrades gracefully with a clear message — never a traceback.

**Toji availability (`ISS-TRANSFER-9.11.0-001`)**: the mandatory end-of-transfer snapshot (step 4) lands under `.protocol-state/snapshots/`, which is already within Toji's standing read access across all Domain Zero records — no CLI invocation needed on his part. This gives every `/session transfer` a durable, complete post-session state capture for audit, alongside the existing `toji-snapshot` event (`python dzp.py event toji-snapshot`) that refreshes the lighter-weight Cortex export used for the same purpose.

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

### 2.5.2 (2026-08-06)
- **Toji v9.12.0 release-train audit `AI-001` (HIGH) remediation**: `/session status` and `/session
  continue` were still prose-primary — the CLI already supported `--json` for both boundaries
  (`session_monitor.py` ~4727-4734, ~4835-4846), but this skill presented the bare command as each
  boundary's implementation and introduced `--json` only afterward as an optional alternative. Both
  sections now mirror the pattern already applied to `/session start`: `--json` is the PRIMARY
  provider-facing implementation, the bare command is relabeled "Legacy/human-readable form (NOT the
  primary implementation)", and each section restates the D5.3 relay rule (relay envelope fields
  verbatim; envelope absence is an explicit degraded condition, never silently equivalent to prose).
  `/session transfer`'s `transfer-begin`/`handoff`/`transfer-finalize` notes were reviewed and left
  unchanged — they already describe `--json` as an additional manual/diagnostic capability on the
  underlying commands, not a prose-primary default. Drafted by Yuuji under Gojo authorization

### 2.5.1 (2026-08-05)
- **SEC-CLOCKADR-9.12.0-019 (P3) remediation**: "Time envelope contract" section fixed a boundary
  miscount — "Six lifecycle boundaries emit it" listed seven (`transfer-begin`/`transfer-finalize`
  are two distinct boundaries, not one joined by a slash) — corrected to "Seven". Filed by Megumi's
  v9.12.0 A4 gate-4 review (`.protocol-state/security-review.md`); applied by Yuuji under Gojo
  authorization

### 2.5.0 (2026-08-05)
- **v9.12.0 A4 (`docs/superpowers/specs/2026-08-04-clock-authority-adr.md` decision D5/D6.4/D6.5, Toji gate 4)**: added the "Time envelope contract" section documenting the new ADR D5 structured time envelope (`--json` flag on `start`/`status`/`check`/`continue`(`resume`)/`transfer-begin`/`transfer-finalize`/`handoff`, replacing prose output entirely when passed, never alongside it) and the D6.4/D6.5 alert reason-code model (`alert_reasons` list; late night is now an independent trigger, direct fix for audit finding IMPL-001). Per-command `--json` notes added to `/session start`, `/session status`, `/session continue`, and `/session transfer`. Backward compatibility (no `--json`) is byte-for-byte unchanged — see `tests/test_session_monitor_envelope.py::TestCliJsonFlag`. Drafted by Yuuji under Gojo authorization

### 2.4.1 (2026-07-31)
- **IMPL-002 remediation (Toji audit `audits/2026-07-30-toji-main-v9-11-0-completed-work.md`, MEDIUM; tracked as `BUG-COORD-9.11.0-001`)**: the `/session transfer` contract section was resynced to the implemented nine-step state machine — `transfer-finalize` documented as the sole marker-clearer (`handoff-write` explicitly does NOT clear the marker), `validation-refresh` documented as step 8 with `terminal_validator: true` (runs strictly after the coordinator's own event-result write, per IMPL-001), and the single retry command replaced with the 3-way marker-state recovery matrix mirroring `session_monitor.py`'s `_warn_if_transfer_incomplete()`. Drafted by Yuuji, applied by Gojo under USER authorization; parity-guarded by `tests/test_session_transfer.py::TestIMPL002ContractParity`

### 2.4.0 (2026-07-28)
- **`FEAT-TRANSFER-9.11.0-001` (v9.11.0 Increment 2)**: added `/session transfer` — update + end + a durable handoff brief (`.protocol-state/session-handoff.md` + immutable per-session archive copy), so the next session resumes with full context instead of just state files
- New `session-transfer` coordinator event (event-level `fail_soft: false` — the load-bearing line) chaining `transfer-begin` (new) → `session-update` → `session-end` → `handoff-write` (new) → optional snapshot/Cortex/validation refresh
- Fail-closed state machine documented via four independent mechanisms (M1-M4: event fail-closed, positive identity predicate, incomplete-transfer marker, retry path) per Toji `DESIGN-001` (2026-07-27): `required: true` alone does not stop the coordinator's step loop
- `/session start` now checks for an incomplete-transfer marker (warns loudly, names the retry command) and points to a fresh `session-handoff.md` before reading the large protocol documents
- Wellness alerts (`render_alert()` / `work-session-alert.template.md`) now additionally recommend `/session transfer` at every alert level, alongside the existing save-and-break / continue recommendations
- `/session end` (and the transfer event's own session-end step) now prints a clear message and degrades gracefully when there is no active session, instead of silently no-op'ing
- Megumi Tier-3 remediation (`SEC-TRANSFER-9.11.0-001..006`, all closed): baseline-update authorization now cross-checks `DZP_AGENT`, transfer-marker reads degrade gracefully on any wrong-shape JSON, `transfer-begin` refuses to clobber a different incomplete transfer, and session ids are charset-validated before any path is built
- `ISS-TRANSFER-9.11.0-001` (first live run, 2026-07-29): `end-snapshot` mandatory (`required: true`) — durable post-transfer state capture readable by Toji for post-session audit, no CLI needed on his part. Fixed the root cause the live run surfaced: `create-snapshot.py`'s `--trigger` choices did not include `session-transfer` (dry-run cannot catch this — it only resolves step targets, never executes); mirrored into `protocol/validation-rules.yaml`'s two `reason` enums in the same change (same class as `BUG-SNAPSHOT-NULLFIELDS-001`/MF-1)
- `/session start`'s Step 0 (handoff-brief-first / incomplete-marker warning) now documented explicitly in this section, mirroring `.claude/commands/session-start.md`

### 2.3.0 (2026-07-28)
- **Doc sync to BUG-CORTEX-008 R5 (2026-07-18)**: this document still described R3 (`90-second timeout`) while `.protocol-state/script_dependencies.yaml` had carried `detach: true` since 2026-07-18, with its own comment stating the timeout is a "detach-DISABLED FALLBACK ONLY". The doc and the executable config disagreed for ten days
- Recorded the consequence R5 did not: detaching removed the timeout and with it the ONLY failure signal for the Cortex index. Confirmed live - an orphaned `index.lock` silenced indexing for hours with no warning and `brain status` still reporting `ok`
- Added a **post-detach liveness assertion** in `cortex_trigger.py`: records the observed `last_index` before launching, warns loudly on the next run if it never advanced. Advisory only, never affects exit codes

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
