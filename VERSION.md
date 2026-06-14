<!-- [CORE FILE] - Domain Zero Protocol v9.1.0 -->
# Domain Zero Protocol - Version Information

**Version:** v9.1.0
**Release Date:** 2026-06-14
**Release Type:** MINOR Release (DZP Cortex — Local Semantic Memory)

---

## Release Summary — v9.1.0 (MINOR)

v9.1.0 ships the **DZP Cortex** feature (PLAN-BRAIN-002): a local semantic-memory "separate brain" that was built and tested during the v9.0.0 cycle but deliberately held back from distribution until ready.

### Headline changes
- **DZP Cortex (PLAN-BRAIN-002)** — sqlite-vec + fastembed local embedding index, `/brain` slash command + skill (`protocol/skills/brain.md`, `.claude/commands/brain.md`), brain-index-hook scripts (`scripts/brain-index-hook.{sh,ps1}`), and `scripts/brain.{sh,ps1}` CLI wrappers. The **engine** (`.protocol-state/brain/`) is tracked + shipped; only the runtime **data** (DB, memories, model cache, snapshots) lives in the external dir `%LOCALAPPDATA%/dzp-cortex/<install-id>/` and is never committed or shipped.
- **Cortex distro shipping + workflow integration (PATCH-BRAIN-002)** — engine added to the distro allowlist (Megumi-cleared); SEC-BRAIN-012 forbid-token tripwire; `dzp-publish.ps1` audit-gate hardening; Cortex Integration Contract + RECALL/REMEMBER/INDEX hooks across `ts.md`/`session.md`/`dzp-roe.md` + all slash-command launchers (54 files); DZP↔Cortex gap closures (README onboarding incl. auto-index hook setup, Toji snapshot via `/session end` export). The `SessionEnd` auto-index hook is documented in README and installed locally; `.claude/settings.json` is gitignored, so the hook is not committed/shipped — it is per-install setup.
- **Security remediation** — SEC-BRAIN-007 (.gitignore backstops for model cache + sqlite index) and SEC-BRAIN-008 (AWS `access_key_id`/`secret_access_key` patterns in `cortex/ingest.py`; GCP/Azure coverage logged as future sweep, not yet implemented) both @approved by Megumi. SEC-BRAIN-012 @approved. No P0/P1 findings unresolved.
- **Performance gate** — no-daemon CLI targets: `query`/`remember` <3s, full index ≤5min, incremental no-op <5s; all pass. (No "sub-500ms" gate — that earlier figure was a documentation error; sub-1s warm latency is deferred to a future daemon.)
- **Phase 10 agent doc blocks** — all 10 `protocol/*.agent.md` files received Cortex context blocks (Phase 10 of PLAN-BRAIN-002) explaining when/how to hand off to the brain.
- **Distro publication + public release**: GATED — remaining on user testing; `DZP-v9.1.0` publish branch NOT yet created. Distro dry-run passes all gates.

### Why MINOR
New feature addition (Cortex) with full backward compatibility; no breaking protocol changes; existing installations unaffected unless they opt in.

---

## Previous Release — v9.0.0 (MAJOR)

**Version:** v9.0.0
**Release Date:** 2026-06-13
**Release Type:** MAJOR Release (Distribution Architecture + Version Reconciliation)

---

## Release Summary — v9.0.0 (MAJOR)

v9.0.0 is a **structural release and version reconciliation**. It introduces the **Distro Publish Architecture** (a fundamental change to how DZP is distributed) and consolidates a backlog of un-versioned / under-documented work accumulated since v8.12.0.

### Headline changes
- **Distro Publish Architecture (PATCH-DISTRO-001)** — clean dev/distribution split: production files publish to the canonical GitHub repo via an orphan `release` branch checked out as a `distro/` git worktree, driven by an allowlist `dzp-publish` script. The dev workspace never reaches canonical. Includes identity scrub, **content-level PII scrub + audit** (personal email/name/local-path removal, fail-loud), a forbidden-path audit, and a hard version-consistency assertion now covering `project-state.json` (closes report ISSUE-DZP-006/007).
- **PATCH-TOJI-001 (CRITICAL)** — fixed the Toji External Auditor fabrication defect (ISSUE-DZP-001): rebound Toji from the non-binding `vscode/*` toolset to real Claude Code tools (report-only), added anti-fabrication constraints + tripwire, and registered Toji in the runtime `agent_registry` (ISSUE-DZP-003). Toji file → v1.2.1.
- **Version reconciliation** — re-stamped all version-bearing files + all 10 agent definitions to v9.0.0; caught the `project-state.json` straggler (was lagging at 8.12.0); folded in the previously under-documented **v8.13.0** body (Toji 10th agent, Session Monitoring Enhancement PATCH-SESSION-004/005/006, State Consolidation PATCH-STATE-001).

### Why MAJOR
The distribution-model change (repo↔canonical relationship, dev/distro separation, orphan `release` branch) is a fundamental protocol restructuring under the semver policy. v9.0.0 establishes a clean, fully-stamped baseline after version/tag drift (git tags had stopped at v8.3.0; `project-state.json` had lagged two minors).

> Deferred to **v9.1.0**: DZP Cortex (local semantic-memory "separate brain") — built and tested in dev, excluded from distribution until shipped.

---

## Previous Releases (v8.12.0 – v8.13.0)

This release closes a critical session monitoring coverage gap (70-85% → 85-90%) identified through adversarial analysis. PATCH-SESSION-004 implements 5 defensive layers to prevent context compaction and agent bypass from disabling safety systems.

**Additional Patches (2025-12-31):**
- **PATCH-SESSION-005-v2**: Critical bug fix restoring user safety systems (3 stale timestamp bugs) + state management extensions + Gojo permission system
- **PATCH-TS-001**: Unified troubleshooting session tracker with permanent historical analytics and tier effectiveness analysis

### Key Changes in v8.12.0

#### PATCH-SESSION-004 (Original Release - 2025-12-29)

- **Component 1: Configurable Debounce** - Adjustable alert frequency (15-60 min range) via protocol.config.yaml + CLI `--debounce` flag to prevent alert spam during rapid prototyping
- **Component 2: Compaction-Resistant Markers** - HTML comments protect AUTO-INVOKED section in gojo.agent.md from context compaction removal (5-10% coverage gap closed)
- **Component 3: Alert Tracking Dashboard** - `.protocol-state/session-monitoring-report.py` detects alert undercount and verifies AUTO-INVOKED section integrity
- **Component 4: Verification Script** - `scripts/verify-auto-invoked.py` for CI/CD validation (exit code 0/1) to prevent safety system removal
- **Component 5: Invocation Tracking** - Tracks agent bypass patterns (direct vs routed invocations) to detect 10-15% coverage gap from agent invocation without Gojo
- **Bug Fix: Windows Compatibility** - Replaced Unicode emojis with ASCII equivalents in session_monitor.py (20+ instances) for full Windows cmd support

#### PATCH-SESSION-005-v2 (2025-12-31) - P0-Critical User Safety Restoration

- **3 Critical Bugs Fixed** - All causing user safety system failures:
  1. `get_session_summary()` always displayed "0 minutes" for 15+ hour sessions (visibility failure)
  2. `_archive_session()` permanently stored "0 minutes" in historical data (data corruption)
  3. `should_block_operation()` NEVER blocked high-risk operations, even after 47+ hours (safety system complete failure)
- **Root Cause** - Methods read stale `metrics['total_duration_minutes']` from JSON instead of calculating live from timestamps
- **Fix** - Added `_calculate_current_duration()` and `_calculate_current_continuous_work()` helper methods (lines 942-995)
- **Extension 2: State Management** - 4 new methods to update project-state.json, dev-notes.md, domain.record.md on session events
- **Extension 3: Permission System** - Gojo-only access to domain.record.md via `DZP_AGENT=gojo` environment variable check
- **Files Modified** - session_monitor.py (+180 lines), session.md (updated with DZP_AGENT=gojo syntax)

#### PATCH-TS-001 (2025-12-31) - Unified Troubleshooting Tracker

- **Purpose** - Centralized tracking for all /ts tier commands with permanent historical analytics
- **Created** - troubleshooting_tracker.py (585 lines) with 6 commands: start, update, complete, escalate, status, stats
- **Key Features**:
  - Tier analysis: Success rates, average durations, escalation patterns per tier (1-5)
  - File frequency tracking: Identifies most commonly problematic files across sessions
  - Pattern recognition: Statistical analysis of tier effectiveness and escalation triggers
  - Permanent retention: All sessions kept indefinitely in troubleshooting-history.json
- **Integration** - Updated protocol/skills/ts.md with Step 0: Review historical stats before tier selection
- **Impact** - Data-driven tier selection, pattern learning, troubleshooting effectiveness tracking

#### PATCH-STATE-001 (2025-12-31) - State File Consolidation

- **Purpose** - Consolidate 4 fragmented state files into unified project-state.json with nested namespaces
- **Problem Solved** - Eliminated state fragmentation, tier statistics duplication, and race conditions across separate JSON files
- **Created** - ProjectStateManager class (788 lines) + migration script (494 lines) with automatic backups and rollback
- **Key Features**:
  - Nested namespace architecture: session_tracking, troubleshooting, tier_tracking, agent_invocation_tracking
  - Centralized state management with cross-platform file locking (Windows msvcrt + Unix fcntl)
  - Non-destructive migration with SHA-256 integrity verification and automatic rollback on failure
  - Backward compatibility via fallback to legacy files if consolidated state unavailable
  - Atomic write operations using tempfile pattern to prevent partial state corruption
- **Files Consolidated**:
  - session-state.json -> project-state.json::session_tracking
  - troubleshooting-history.json -> project-state.json::troubleshooting
  - agent-invocation-tracker.json -> project-state.json::agent_invocation_tracking
  - Deduplicated tier_usage_statistics + tier_statistics -> project-state.json::tier_tracking
- **Security** - 24 security issues identified by Megumi, 16 resolved by Sukuna including 3 P0 critical race conditions (SEC-016, SEC-019, SEC-024)
- **Performance** - P95 latency 8.44ms (23.7x better than 200ms target), 125 ops/sec throughput (12.5x better than target), 99%+ capacity headroom
- **UX** - 78/100 initial score improved to 85/100 after Priority 1 fixes (rollback documentation, actionable error messages, clear success output)
- **Testing** - 5-phase comprehensive testing (Unit, Integration, Edge Cases, E2E Workflows, Final Validation) with unanimous @approved from Megumi, Maki, and Nobara
- **Updated Scripts (8)** - session_monitor.py, troubleshooting_tracker.py, tier-statistics.py, tier-enforcement.py, gojo-learn.py, sukuna-learn.py, restore-snapshot.py, create-snapshot.py
- **Updated Documentation (5)** - session.md, ts.md, gojo.agent.md, AI_INSTRUCTIONS.md, CHANGELOG.md
- **Impact** - Single source of truth for all DZP state, eliminated data inconsistency, improved reliability with proper locking mechanisms

### Previous Release (v8.11.0)

- **Component 1: Session Management Skill** - 6 commands (`/session start|status|update|break|continue|end`) for unified work session lifecycle with checkpoint file syncing (dev-notes, project-state, domain.record, security-review, session-state)
- **Component 2: TS Troubleshooting Tier System** - 9 commands across 5-tier hybrid bug resolution workflow with auto-escalation (`/ts_tier1|tier2|tier3|tier4|codered|status|history|escalate|complete`)
- **Component 3: DZP ROE v2.0.0** - 40% size reduction (510→306 lines), streamlined to 5-step workflow with parallel enforcement, anti-pattern examples
- **Component 4: State Schema Updates** - Added troubleshooting_session and troubleshooting_statistics to project-state.json, new troubleshooting-history.json for session archival
- **Component 5: Skill Registry Update** - SKILL_REGISTRY.md v3.0.0 → v3.2.0 with session and ts skills (both Gojo-owned with domain.record.md write access)

### Previous Release (v8.9.0)

- **Component 1: Claude Skills Integration** - 16 Anthropic skills (pdf, docx, xlsx, pptx, frontend-design, web-artifacts-builder, webapp-testing, mcp-builder, skill-creator, brand-guidelines, canvas-design, doc-coauthoring, internal-comms, theme-factory, algorithmic-art, slack-gif-creator) mapped to all 9 agents
- **Component 2: Implementation Restrictions** - Nobara, Todo, Maki, Panda, Inumaki now route all code implementation through Yuuji; edit/bash tools removed from these agents
- **Component 3: File Rotation System** - scripts/file-rotate.py for dev-notes.md and security-review.md rotation at 25k character threshold
- **Component 4: OWASP Cheatsheet Integration** - Megumi updated with comprehensive OWASP Cheatsheet Series references (Tier 1/2/3 organization)
- **Updated Skill Registry** - SKILL_REGISTRY.md and AGENT_SKILLS_MAP.yaml v3 with complete skill mappings

### Previous Release (v8.8.0)

- **Component 1: Tier Validation System** - Active pwd verification, tier-defaults.yaml (18KB config), all 9 agents updated with tier validation sections, 30-day backward compatibility grace period
- **Component 2: Tier Statistics** - Automatic tier usage tracking, compliance monitoring, markdown/JSON reporting for Trigger 19 integration
- **Component 3: Dual Learning Systems** - Sukuna learns from protocol updates, Gojo learns from tier selections, comprehensive USER + PROJECT protection, opt-in by default
- **Comprehensive Safety** - Kill Switch integration, sanitized data, project isolation, confidence thresholds (80%+, 3+ samples), instant disable capability
- **Migration Guide** - 500+ line MIGRATION_v8.7_to_v8.8.md with step-by-step upgrade instructions

### Previous Release (v8.7.0)

- **Custom Agent Security Framework** - Pre-invocation validation (440 lines), runtime monitoring (650+ lines), audit logging, and registry system
- **8 Critical Vulnerabilities Fixed** - Agent name collision, self-declared tool permissions, YAML injection, agent self-modification, zero Gojo oversight, rate limiting, file immutability
- **Comprehensive Test Coverage** - 60+ test cases for session monitoring, 110+ tests total for security features
- **Agent Banner Compliance** - Fixed emoji consistency and added missing banner for Sukuna (protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md compliance)

### Previous Release (v8.6.0)

- **Nine-Agent System** - Sukuna formalized as the 9th agent; all documentation updated from "eight-agent" to "nine-agent"
- **Full Documentation Update** - README, FAQ, PROTOCOL_QUICKSTART, VERSION, CLAUDE.md, gojo.agent.md all reflect 9-agent architecture
- **Distribution Update** - core-files-v8.5.1/ updated to core-files-v8.6.0/ standard

### Previous Release (v8.5.1)

- **Sukuna System Update Adversary** - Ryomen Sukuna integrated as adversarial-but-aligned system update specialist, invocable only via Gojo or User
- **Cross-Agent Edit Restrictions** - Non-Gojo agents now have READ-ONLY access to all `.agent.md` files; changes require User or Gojo authorization
- **JJK Character Reference** - Full Sukuna character reference added to `.protocol-state/jjk-character-reference/`
- **Slash Command Rename** - `/system-update` renamed to `/sukuna` with JJK character integration
- **Work Session Management** - Enhanced enforcement across all agents
- **Gojo Template Extraction** - Extracted OUTPUT TEMPLATES to `.protocol-state/gojo-templates/OUTPUT_TEMPLATES.md` (~9% size reduction)

### Previous Release (v8.5.0)

- **Kill Switch Protocol** - Emergency stop mechanism with immediate halt, checkpoint creation, and project protection
- **User Technical Level System** - Beginner/Intermediate/Expert modes that adapt agent communication style
- **Gojo Mission Control Option 4** - New "Resume from Emergency Stop" option for checkpoint recovery

### Previous Release (v8.4.1)

- **Agent File Cleanup** - Removed verbose Gojo Awareness sections for cleaner separation of concerns
- **JJK Character References** - Added character context sections to all 9 agent files
- **Research Mode Expansion** - Updated to support all 9 agents with role-specific research focus

---

## What's New in v8.4.1

### Changed

#### 1. **Agent File Cleanup**

Removed verbose "Gojo Awareness" sections from all non-Gojo agent files:
- `protocol/yuuji.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/megumi.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/nobara.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/todo.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/maki.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/panda.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/inumaki.agent.md` - Added "Mission Control: Gojo" reference

#### 2. **JJK Character Reference Additions**

Added character context sections to all 9 agent files linking to:
- Canon series information (Jujutsu Kaisen)
- Character wiki references
- Cursed technique mappings to agent specializations
- Domain expansion parallels

#### 3. **Research Mode Expansion**

Updated `protocol/RESEARCH_MODE.md` to support all 9 agents:
- Added role-specific research focus for Extended Four agents
- Defined operational cadences per agent type
- Integrated staleness monitoring for all agents

#### 4. **Handoff Specification Updates**

Updated `protocol/HANDOFF_SPECIFICATION.md`:
- Changed example handoffs from `mission_control` to `gojo` for schema compliance
- Ensured all agent identifiers match JSON schema enum

---

## Files Modified

**Protocol Agent Files (8 files):**
- `protocol/gojo.agent.md` - JJK Character Reference added
- `protocol/yuuji.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/megumi.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/nobara.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/todo.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/maki.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/panda.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/inumaki.agent.md` - Mission Control reference, JJK Character Reference added

**Core Protocol Files:**
- `protocol/CLAUDE.md` - Updated to 9-agent system, new invocations
- `protocol/gojo.agent.md` - Domain supervision for all 9 agents
- `protocol/yuuji.agent.md` - Version sync to 8.4.1
- `protocol/megumi.agent.md` - Version sync to 8.4.1
- `protocol/nobara.agent.md` - Version sync to 8.4.1

**Configuration:**
- `protocol.config.yaml` - Added 4 new agent configurations
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Extended with new agent skills

**State:**
- `.protocol-state/project-state.json` - Version 8.4.1

---

## Configuration

No new configuration required. All changes are backward compatible.

**New Agent Invocations:**
```bash
# Todo - Database & Backend
"Read protocol/todo.agent.md and design database schema for [feature]"

# Maki - Performance
"Read protocol/maki.agent.md and optimize [component/page]"

# Panda - Build & Integration
"Read protocol/panda.agent.md and configure CI/CD for [project]"

# Inumaki - API & Communication
"Read protocol/inumaki.agent.md and design API for [feature]"
```

---

## Upgrade Notes

### For Existing Users

**No Action Required:**
- All changes are backward compatible
- Existing four-agent workflows unchanged
- New agents are optional extensions

**Optional: Use Extended Agents:**
```bash
# Database design
"Read protocol/todo.agent.md and design schema for user management"

# Performance optimization
"Read protocol/maki.agent.md and run Lighthouse audit"

# CI/CD setup
"Read protocol/panda.agent.md and create GitHub Actions workflow"

# API design
"Read protocol/inumaki.agent.md and design REST API for orders"
```

### For New Users

1. Review `IMPLEMENTATION_GUIDE.md` for agent overview
2. Start with core four agents (Gojo, Yuuji, Megumi, Nobara)
3. Add extended agents as needed for specialized tasks

---

## Key Principles Established

1. **Nine-agent system** - Specialized expertise across all development domains
2. **Consistent format** - All agents use .agent.md with YAML frontmatter
3. **Domain supervision** - Gojo coordinates all agents with declarative handoffs
4. **Escape paths** - All agents have fallback patterns (never hang)
5. **Skill assignments** - Each agent has specialized skills in AGENT_SKILLS_MAP.yaml

---

## Breaking Changes

**None.** This is a backward-compatible patch release.

---

## Documentation

**Agent Files:**
- `protocol/todo.agent.md` - Database & Backend Specialist
- `protocol/maki.agent.md` - Performance Optimization Specialist
- `protocol/panda.agent.md` - Build & Integration Specialist
- `protocol/inumaki.agent.md` - API & Communication Specialist

**Updated Files:**
- `protocol/CLAUDE.md` - System overview with 9 agents
- `protocol/gojo.agent.md` - Domain supervision diagram

**Skills:**
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Agent-skill mapping

---

## Known Issues

**None identified.**

---

## Contributors

- Domain Zero Protocol Team
- Claude Code

---

**Previous Version:** v8.3.1 (Agent-Specific Escape Paths)
**Next Planned:** TBD (See roadmap in README.md)
