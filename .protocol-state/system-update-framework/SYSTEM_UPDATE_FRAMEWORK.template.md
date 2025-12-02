[CORE DOCUMENT]

# Domain Zero: System Update Framework Protocol

> **Version:** 1.2.0
> **Status:** Production-Ready
> **Classification:** INTERNAL DOCUMENT
> **Authority:** Internal development framework - guides maintenance operations
> **Last Updated:** 2025-11-27

---

## Overview

This protocol serves as the authoritative guide for all Domain Zero system updates, modifications, and maintenance operations. Every action taken within Domain Zero must follow this framework without exception.

All subsequent agents, automated processes, and protocol expansions operating within Domain Zero inherit and comply with this framework.

---

## Core Principles

### Non-Negotiable Requirements

Before executing ANY system update, bug fix, feature addition, or structural modification:

1. **Backup and Rollback Verification Phase** - MUST complete before changes proceed
2. **File Classification Verification** - MUST identify and respect INTERNAL vs CORE classifications
3. **Version Checklist Sweep** - MUST verify all version identifiers update appropriately
4. **Plan Documentation** - MUST create or update with proposed changes

> **CRITICAL:** No changes proceed until confirmed rollback capability exists. This is non-negotiable.

---

## File Classification System

All files within Domain Zero operate under a binary classification system. Identify and respect these classifications at all times.

### INTERNAL Documents

**Markers:**

- Header tag: `[INTERNAL DOCUMENT]` or `[INTERNAL]`
- Storage in designated internal directories

**Characteristics:**

- Sensitive operational data
- Planning documents
- Version logs
- Framework records
- Research raw logs

**Git Policy: EXCLUDED FROM ALL GITHUB OPERATIONS**

| Blocked Action | Enforcement |
|----------------|-------------|
| `git add` | Block and warn |
| `git stage` | Block and warn |
| `git commit` | Block and warn |
| `git push` | Block and warn |

**Verification Procedure:** MUST follow before ANY git operation - MUST BE FOLLOWED VERBATIM

1. Check for `[INTERNAL DOCUMENT]` or `[INTERNAL]` header marker
2. Verify file is not in internal directories
3. Match against internal filename patterns
4. If classified as INTERNAL: block git operations and report

### CORE Files

**Markers:**

- Header tag: `[CORE FILE]` or `[CORE]`
- Residence in designated core directories

**Characteristics:**

- Production codebase
- Public repository content
- Version-controlled files

**Git Policy: STANDARD WORKFLOW**

| Requirement | Details |
|-------------|---------|
| Version verification | Must pass version number check before commit |
| Backup requirement | Backup must exist before modification |
| Classification verification | Must confirm as CORE before git operations |

### Internal Directories

```text
.protocol-state/system-update-framework/
.protocol-state/backups/
.protocol-state/research/**/*.raw.log
.protocol-state/trigger-19.md
notes/
conversion/
```

### Internal File Patterns

```text
*_INTERNAL.*
*_ACTIONABLE.md
*_REMEDIATION.md
*_DRAFT.md
*_WIP.md
*_PROGRESS.md
*_COMPLETE.md
*_ACTION_PLAN.md
*_DESIGN.md
*_REVIEW.md
SYSTEM_UPDATE_*.md (except this file)
P0_*.md, P1_*.md, P2_*.md, P3_*.md
SESSION_SUMMARY_*.md
RELEASE_NOTES_*.md
```

### Core Directories

```text
protocol/
docs/
scripts/
release/
Domain Zero Agents/
.github/
```

---

## Project State Preservation (CRITICAL)

When performing in-place upgrades on existing projects, certain files must NEVER be overwritten. This section defines the hard rules for project state preservation.

### Protected Files (NEVER Overwrite)

These files contain project-specific data that would be lost if overwritten:

| File | Reason | Update Behavior |
|------|--------|-----------------|
| `.protocol-state/dev-notes.md` | Project implementation history | NEVER_OVERWRITE |
| `.protocol-state/security-review.md` | Project security findings | NEVER_OVERWRITE |
| `.protocol-state/trigger-19.md` | Private intelligence reports | NEVER_OVERWRITE |

**Enforcement Rule:** Before ANY copy operation to `.protocol-state/`, check if these files exist. If they exist, SKIP the copy.

### Merge-Only Files

These files require schema merging, not wholesale replacement:

| File | Merge Behavior |
|------|----------------|
| `.protocol-state/project-state.json` | Merge new schema fields while preserving project data |

**Merge Algorithm for project-state.json:**

```text
1. LOAD     → Read local project-state.json
2. LOAD     → Read template project-state.json from core-files archive
3. SET      → protocol_version = new version (e.g., "8.5.1")
4. FOR EACH → new field in template missing locally
             → Add field with default value
5. PRESERVE → Existing project-specific fields:
             - project_metadata.name
             - project_metadata.description
             - project_metadata.created
             - project_metadata.tech_stack
             - git_metadata (all fields)
             - current_mission (all fields)
6. UPDATE   → Protocol-only fields:
             - protocol_version
             - system_update_framework.version
7. WRITE    → Merged JSON back to project-state.json
```

**On Merge Failure:**

```text
1. ABORT    → Do not write any changes
2. LOG      → Record error details
3. REQUEST  → Manual intervention
4. ROLLBACK → Restore from backup if needed
```

### Template File Rules

Template files (`.template.md`, `.template.json`) are initializers, not overwrites.

| File Status | Action |
|-------------|--------|
| `.md` exists | **KEEP** existing file, ignore template |
| `.md` does NOT exist | Copy `.template.md` → `.md` |

**Example:**

```text
# If upgrading project with existing dev-notes.md:
core-files/.protocol-state/dev-notes.template.md  →  SKIP (dev-notes.md exists)

# If fresh install (no dev-notes.md):
core-files/.protocol-state/dev-notes.template.md  →  COPY to dev-notes.md
```

---

## Installation Flow Classification

### Fresh Install Flow

**Definition:** Installing DZP into a project with NO existing protocol/state.

**Safe Operations:**

```text
✓ Copy entire protocol/ directory
✓ Copy entire .protocol-state/ template directory
✓ Initialize project-state.json from template
✓ Customize project-state.json with project metadata
```

**Detection:** No existing `protocol/` OR `.protocol-state/` directory.

### In-Place Upgrade Flow

**Definition:** Upgrading DZP in an existing project with existing state.

**Safe Operations:**

```text
✓ Sync protocol/ directory (overwrite protocol files)
✓ Sync docs/ directory
✓ Sync Domain Zero Agents/
✓ Sync .claude/commands/
✓ Sync .dzp-killswitch/
✓ Merge project-state.json (schema only)
```

**Forbidden Operations:**

```text
✗ Copy .protocol-state/ wholesale
✗ Overwrite dev-notes.md
✗ Overwrite security-review.md
✗ Overwrite trigger-19.md
✗ Replace project-state.json without merge
```

**Pre-requisites:**

```text
1. Backup ALL existing files including .protocol-state/
2. Verify rollback capability before proceeding
3. Document what will change in plan-documentation.md
```

---

## Directory Structure Enforcement

Maintain awareness of the canonical folder structure at all times.

### Verification Procedure

Before creating files or folders:

1. Reference the master structure document
2. Verify proposed location aligns with established architecture
3. If violation detected: flag discrepancy and request clarification
4. Do NOT proceed until location verification completes

### Canonical Structure

```text
Domain Zero/
├── protocol/                    # Core protocol files (CORE)
│   ├── CLAUDE.md               # Main protocol definition
│   ├── *.agent.md              # Agent definitions
│   ├── skills/                 # Agent skills
│   └── mcp-servers/            # MCP integration
├── docs/                        # Documentation (CORE)
├── scripts/                     # Verification scripts (CORE)
├── release/                     # Release packages (CORE)
├── Domain Zero Agents/          # Agent templates (CORE)
├── .protocol-state/             # State management (INTERNAL)
│   ├── system-update-framework/ # This framework's state
│   ├── backups/                 # Backup storage
│   └── research/                # Research data
├── .github/                     # GitHub workflows (CORE)
└── [root files]                 # README, VERSION, etc. (CORE)
```

---

## Version Number Management

### Centralized Version Registry

Location: `.protocol-state/system-update-framework/version-registry.json`

The registry tracks:

- File path
- Current version number
- Version format pattern
- Version locations within file
- Last update timestamp
- File classification

### Registered Version Files

| File | Version Locations |
|------|-------------------|
| `protocol/CLAUDE.md` | Header metadata, canonical section, version section |
| `protocol/gojo.agent.md` | Header metadata |
| `protocol/yuuji.agent.md` | Header metadata |
| `protocol/megumi.agent.md` | Header metadata |
| `protocol/nobara.agent.md` | Header metadata |
| `protocol.config.yaml` | canonical_repository.version |
| `VERSION.md` | Title, release information |
| `CHANGELOG.md` | Version headers |
| `README.md` | Version badge, installation section |
| `.protocol-state/project-state.json` | protocol_version field |

### Version Checklist Procedure

#### Pre-Update Sweep

The Pre-Update Sweep is the initial checklist performed before any system update. Its purpose is to verify the integrity and readiness of all registered version files, ensure backup and rollback capabilities, and confirm that all prerequisites for a safe update are met.

1. Verify all registered files exist
2. Record current versions from each file
3. Identify files requiring version update
4. Generate backup manifest
5. Present checklist to user for confirmation
6. Mark each item as VERIFIED or PENDING
7. Determine target versions based on update type
8. Communicate target versions to implementation phase
9. Maintain version integrity throughout update process
10. Document all findings in plan documentation
11. Ensure user approval before implementation
12. Prepare for post-update verification

#### Post-Update Sweep

The Post-Update Sweep, performed after the update, validates that all changes apply correctly and that the system remains stable.

1. Verify all version numbers update correctly
2. Check version format compliance (MAJOR.MINOR.PATCH)
3. Validate cross-file version consistency
4. Update registry with new versions
5. Mark each item as VERIFIED or PENDING

> **IMPORTANT:** No update is considered complete until all version numbers pass verification.

---

## Plan Documentation Protocol

### Location

`.protocol-state/system-update-framework/plan-documentation.md`

### Document Lifecycle

#### Phase 1: Planning

Document the following:

- Proposed changes
- Affected files with classifications
- Rationale for changes
- Expected outcomes
- Rollback procedure

#### Phase 2: Implementation

Log each action with:

- Timestamp
- Action description
- Result (SUCCESS/FAILED)
- Notes

#### Phase 3: Completion

Record:

- Final outcomes
- Deviations from original plan
- Lessons learned
- Version impact

### Classification

- **Document Type:** INTERNAL DOCUMENT
- **Persistence:** Indefinite (accumulates historical records)
- **Git Status:** NEVER delete, NEVER push to GitHub

---

## Backup and Rollback Procedure

### Mandatory Backup Scope

**CRITICAL:** Any pre-update backup MUST include ALL of the following:

| Directory/File | Reason | Required |
|----------------|--------|----------|
| `protocol/` | Protocol code | YES |
| `docs/` | Protocol documentation | YES |
| `.claude/commands/` | Slash commands | YES |
| `Domain Zero Agents/` | Generic agent templates | YES |
| `Domain Zero Agents - Full JJK Edition/` | JJK character agents | YES |
| `protocol.config.yaml` | Protocol configuration | YES |
| `AI_INSTRUCTIONS.md` | Discovery shim | YES |
| `PASSIVE_OBSERVER.md` | Observer mode guide | YES |
| `.dzp-killswitch/` | Kill switch state | YES |
| **`.protocol-state/`** | **Project-specific state (CRITICAL)** | **YES** |

**Rationale:** The JamWatHQ v8.5.1 incident demonstrated that omitting `.protocol-state/` from backup makes recovery require searching older backups or git history. Always backup `.protocol-state/` to ensure complete recovery capability.

### Pre-Modification Sequence

Execute this sequence before ANY modification begins:

```text
1. IDENTIFY    → List all files targeted for modification
2. BACKUP      → Create timestamped backup of each file (including .protocol-state/)
3. VERIFY      → Verify backup integrity (content comparison)
4. DOCUMENT    → Record rollback procedure for planned changes
5. CONFIRM     → Ensure restore paths are accessible
6. PROCEED     → Only after steps 1-5 verify successfully
```

### Backup Naming Convention

```text
{filename}_{YYYY-MM-DD_HH-MM-SS}.backup
```

### Backup Storage

```text
.protocol-state/backups/
```

### Backup Manifest

Location: `.protocol-state/system-update-framework/backup-manifest.json`

Tracks:

- Backup ID
- Creation timestamp
- Associated update ID
- File paths (original and backup)
- Checksum for integrity verification
- Verification status

### Rollback Execution

If any operation fails or rollback is required:

```text
1. HALT        → Stop all current operations
2. LOCATE      → Find backup files from manifest
3. VERIFY      → Check backup file integrity
4. RESTORE     → Restore original files from backups
5. CONFIRM     → Verify restoration success
6. UPDATE      → Record rollback in manifest
```

### Failure Handling

If ANY backup step fails:

- **HALT** all operations immediately
- **REPORT** the failure with details
- **DO NOT** proceed with modifications

---

## Operational Workflow

### Complete Update Sequence

When receiving an update request, follow this 10-step sequence:

| Step | Phase | Action |
|------|-------|--------|
| 1 | ACKNOWLEDGE | Receive request and classify as UPDATE, FIX, or STRUCTURAL_CHANGE |
| 2 | IDENTIFY | List all affected files and their classifications |
| 3 | BACKUP | Execute backup and rollback preparation |
| 4 | DOCUMENT | Create or update plan documentation with proposed changes |
| 5 | PRE-SCAN | Run version checklist pre-scan |
| 6 | IMPLEMENT | Make changes incrementally with logging |
| 7 | POST-SCAN | Run version checklist post-scan, verify all numbers update |
| 8 | COMPLETE | Update plan documentation with completion status |
| 9 | PRESENT | Show summary for user approval before git operations |
| 10 | EXECUTE | Execute git operations only for verified CORE files |

### Response Format

When executing framework operations, structure responses to include:

```markdown
## Current Phase

[Phase name and step number]

## Files Affected

| File | Classification | Status |
|------|----------------|--------|
| [path] | [CORE/INTERNAL] | [status] |

## Version Status

| File | Current | Target | Verified |
|------|---------|--------|----------|
| [path] | [ver] | [ver] | [YES/NO] |

## Blockers/Verification Failures

[Any issues requiring attention]
```

---

## Universal Framework Status

### Authority Level

This protocol serves as the **parent authority** for all Domain Zero operations including:

- Protocol expansions
- Agent file development
- Automated processes
- Future system additions

### Inheritance Requirements

When creating new protocols or agent definitions:

1. Reference this framework as parent authority
2. Ensure compatibility with file classifications
3. Implement backup verification procedures
4. Follow version management requirements
5. Integrate with plan documentation lifecycle

### Compliance Verification

All agents and processes must:

- [ ] Respect file classification system
- [ ] Execute backup before modifications
- [ ] Verify rollback capability
- [ ] Update version numbers appropriately
- [ ] Document changes in plan documentation
- [ ] Block INTERNAL documents from git operations

---

## State Files Reference

### Framework State Files

| File | Purpose | Classification |
|------|---------|----------------|
| `version-registry.json` | Version tracking | INTERNAL |
| `plan-documentation.md` | Update history | INTERNAL |
| `backup-manifest.json` | Backup tracking | INTERNAL |
| `file-classifications.json` | Classification registry | INTERNAL |

### Integration with Project State

The framework integrates with `.protocol-state/project-state.json`:

- Tracks protocol version
- Records backup count
- Monitors file protection status

---

## Quick Reference

### Before ANY Modification

- [ ] Backup created and verified
- [ ] Rollback procedure documented
- [ ] File classification confirmed
- [ ] Plan documentation updated

### Before ANY Git Operation

- [ ] File classifies as CORE
- [ ] Version numbers updated
- [ ] Version checklist passed
- [ ] User approval obtained

### After ANY Update

- [ ] Implementation logged with timestamps
- [ ] Version registry updated
- [ ] Plan documentation completed
- [ ] Backup manifest updated

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-25 | Initial framework implementation |
| 1.1.0 | 2025-11-27 | Applied Markdown best practices (heading hierarchy, code block languages, active voice, focused paragraphs) |
| 1.2.0 | 2025-11-27 | Added Project State Preservation rules (4.1), Merge-Only behavior (4.2), Mandatory backup scope (4.3), Template file rules (4.4), Installation flow classification (4.5), based on JamWatHQ v8.5.1 incident review |

---

*This document is the authoritative guide for all Domain Zero maintenance operations. Compliance is mandatory.*
