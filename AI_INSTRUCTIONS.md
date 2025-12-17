<!-- [CORE FILE] - Domain Zero Protocol v8.8.0 -->
# AI Instructions - Domain Zero Protocol

**Version**: 8.8.0 | **Last Updated**: 2025-12-17
**Purpose**: Complete installation and verification guide for AI assistants

---

## 🚨 CRITICAL: COMPLETE INSTALLATION REQUIRED

**Problem**: Partial installations cause protocol misconfiguration, missing files, and broken functionality.

**Solution**: This guide provides **COMPLETE** file-by-file checklists for AI assistants to verify and install Domain Zero Protocol correctly.

---

## For AI Assistants: READ THIS FIRST

**Primary Instructions**: Read [`protocol/CLAUDE.md`](protocol/CLAUDE.md) AFTER completing installation verification below.

**MANDATORY STEPS** (Run these before reading protocol/CLAUDE.md):
1. ✅ Complete file structure verification (Section 3)
2. ✅ Sync templates to implementation folders (Section 4)
3. ✅ Verify all subfolders and their contents (Section 5)
4. ✅ Run automated verification script (Section 6)

**Why This Matters**:
- Missing files → Broken protocol functionality
- Unsynced templates → Agents cannot function
- Missing subfolders → Configuration errors
- Incomplete installation → User frustration and wasted time

---

## Table of Contents

1. [Quick Start (First-Time Users)](#1-quick-start-first-time-users)
2. [Installation Types](#2-installation-types)
3. [Complete File Structure Checklist](#3-complete-file-structure-checklist)
4. [Template Syncing Procedures](#4-template-syncing-procedures)
5. [Subfolder Verification](#5-subfolder-verification)
6. [Automated Verification](#6-automated-verification)
7. [In-Place Upgrade Procedure](#7-in-place-upgrade-procedure)
8. [New Installation Procedure](#8-new-installation-procedure)
9. [Troubleshooting Missing Files](#9-troubleshooting-missing-files)
10. [Agent Invocation](#10-agent-invocation)

---

## 1. Quick Start (First-Time Users)

### Step 1: Verify Installation Completeness

**BEFORE reading any protocol files**, run this verification:

```bash
# Windows PowerShell
python scripts/verify-installation.py

# Expected output: "✅ Installation complete (X/X files present)"
# If ANY files missing: Follow Section 9 (Troubleshooting)
```

### Step 2: Sync Templates

```bash
# Copy .template.* and .example.* files to working locations
python scripts/sync-templates.py

# Expected output: "✅ All templates synced"
```

### Step 3: Read Protocol

```bash
# NOW safe to read protocol
Read protocol/CLAUDE.md
```

---

## 2. Installation Types

### Type A: New Installation (Fresh Project)
- **Goal**: Install complete DZP from scratch
- **Source**: `core-files-vX.Y.Z/` directory
- **Procedure**: Section 8

### Type B: In-Place Upgrade (Existing DZP Project)
- **Goal**: Upgrade existing installation to newer version
- **Source**: `core-files-vX.Y.Z/` directory
- **Procedure**: Section 7
- **⚠️ WARNING**: Do NOT overwrite `.protocol-state/*.json` (user data)

### Type C: Verification Only (Already Installed)
- **Goal**: Check existing installation for missing files
- **Source**: Current directory
- **Procedure**: Section 6

---

## 3. Complete File Structure Checklist

**MANDATORY**: Every file and folder listed below MUST exist for DZP to function.

### 3.1 Root Files (REQUIRED)

- [ ] `AI_INSTRUCTIONS.md` (this file)
- [ ] `CHANGELOG.md`
- [ ] `LICENSE`
- [ ] `PASSIVE_OBSERVER.md`
- [ ] `protocol.config.yaml`
- [ ] `PROTOCOL_QUICKSTART.md`
- [ ] `README.md`
- [ ] `SECURITY.md`
- [ ] `VERSION.md`

### 3.2 Protocol Directory (`protocol/`) - CORE FILES

**Agent Files** (9 agents):
- [ ] `protocol/gojo.agent.md` (Mission Control)
- [ ] `protocol/yuuji.agent.md` (Implementation)
- [ ] `protocol/megumi.agent.md` (Security)
- [ ] `protocol/nobara.agent.md` (Creative/UX)
- [ ] `protocol/todo.agent.md` (Database & Backend)
- [ ] `protocol/maki.agent.md` (Performance)
- [ ] `protocol/panda.agent.md` (Build & Integration)
- [ ] `protocol/inumaki.agent.md` (API & Communication)
- [ ] `protocol/sukuna.agent.md` (System Update)

**Main Protocol**:
- [ ] `protocol/CLAUDE.md` (PRIMARY PROTOCOL FILE)

**Reference Files**:
- [ ] `protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md`
- [ ] `protocol/CANONICAL_SOURCE_ADOPTION.md`
- [ ] `protocol/EMERGENCY_STOP_STANDARD.md`
- [ ] `protocol/ENVIRONMENT_TARGETING.md`
- [ ] `protocol/HANDOFF_SPECIFICATION.md`
- [ ] `protocol/MASK_MODE.md`
- [ ] `protocol/MCP_INTEGRATION.md`
- [ ] `protocol/MODE_INDICATORS.md`
- [ ] `protocol/RESEARCH_MODE.md`
- [ ] `protocol/TECHNICAL_LEVEL_ADAPTATION.md`
- [ ] `protocol/TIER-SELECTION-GUIDE.md`

### 3.3 Protocol Modules (`protocol/modules/`) - SHARED MODULES

- [ ] `protocol/modules/BINDING_OATH.md`
- [ ] `protocol/modules/EMERGENCY_STOP_PROTOCOL.md`
- [ ] `protocol/modules/ESCAPE_PATH_PROTOCOL.md`
- [ ] `protocol/modules/MASK_MODE_BEHAVIOR.md`
- [ ] `protocol/modules/MISSION_CONTROL_ISOLATION.md`
- [ ] `protocol/modules/SAFETY_FIRST.md`
- [ ] `protocol/modules/USER_LEVEL_ADAPTATION.md`

### 3.4 Gojo Procedures (`protocol/gojo-procedures/`)

- [ ] `protocol/gojo-procedures/OPERATIONAL_PROCEDURES.md`

### 3.5 Skills System (`protocol/skills/`)

- [ ] `protocol/skills/AGENT_SKILLS_MAP.yaml`
- [ ] `protocol/skills/SKILL_REGISTRY.md`
- [ ] `protocol/skills/skill-builder.md`

### 3.6 Documentation Directory (`docs/`)

**Guides** (`docs/guides/`):
- [ ] `docs/guides/AGENT_BINDING_OATH.md`
- [ ] `docs/guides/CREATING_CLAUDE_AGENTS.md`
- [ ] `docs/guides/DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md`
- [ ] `docs/guides/EMERGENCY_STOP_GUIDE.md`
- [ ] `docs/guides/TIER_TRANSITION_GUIDE.md`
- [ ] `docs/guides/USER_LEVEL_GUIDE.md`

**Installation** (`docs/installation/`):
- [ ] `docs/installation/IMPLEMENTATION_GUIDE.md`
- [ ] `docs/installation/MCP_SERVER_SETUP.md`
- [ ] `docs/installation/SLASH_COMMANDS_INSTALLATION.md`

**Reference** (`docs/reference/`):
- [ ] `docs/reference/AUTHORIZATION_PROTOCOL.md`
- [ ] `docs/reference/DOMAIN_ZERO_RESEARCH_AND_SKILLS_GUIDE.md`
- [ ] `docs/reference/INSTRUCTION_CONFIRMATION_PROTOCOL.md`
- [ ] `docs/reference/MIGRATION_GUIDE_TEMPLATE.md`
- [ ] `docs/reference/playwright.md`
- [ ] `docs/reference/REALITY_CHECK.md`

**Templates** (`docs/templates/`):
- [ ] `docs/templates/DECISION_REASONING_TEMPLATE.md`

**Root Documentation**:
- [ ] `docs/FAQ.md`
- [ ] `docs/DZP_DZA_INSTALLATION_REVIEW.md`
- [ ] `docs/SYSTEM_UPDATE_IMPLEMENTATION_GUIDE.md`
- [ ] `docs/TOKEN_EFFICIENCY_RECOMMENDATIONS.md`

### 3.7 Domain Record Directory (`.dzp-domain/`) - NEW IN v8.8.0

**Domain Record Files** (Gojo + Sukuna ONLY):
- [ ] `.dzp-domain/domain.record.md` (shared notes repository)
- [ ] `.dzp-domain/.rotation-metadata.json` (rotation tracking)
- [ ] `.dzp-domain/archive/` (directory for rotated archives)

**Purpose**: Shared notes repository for Gojo and Sukuna to prevent agent file bloat, enable crash recovery, and track strategic decisions. Auto-rotates at 5,000 lines.

### 3.8 State Directory (`.protocol-state/`) - CRITICAL

**Root State Files**:
- [ ] `.protocol-state/custom-agent-registry.example.json` (template)
- [ ] `.protocol-state/custom_agent_monitor.py`
- [ ] `.protocol-state/gojo-session-monitoring-guide.md`
- [ ] `.protocol-state/project-state.json` (may not exist on fresh install)
- [ ] `.protocol-state/session_monitor.py`
- [ ] `.protocol-state/session-state.example.json` (template)
- [ ] `.protocol-state/session-state.json` (created by session_monitor.py)
- [ ] `.protocol-state/work-session-alert.template.md`
- [ ] `.protocol-state/WORK_SESSION_STATUS.md`

**System Update Framework** (`.protocol-state/system-update-framework/`):
- [ ] `.protocol-state/system-update-framework/backup-manifest.template.json`
- [ ] `.protocol-state/system-update-framework/file-classifications.template.json`
- [ ] `.protocol-state/system-update-framework/plan-documentation.md`
- [ ] `.protocol-state/system-update-framework/plan-documentation.template.md`
- [ ] `.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.md`
- [ ] `.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.template.md`
- [ ] `.protocol-state/system-update-framework/version-registry.template.json`

**Authorization** (`.protocol-state/authorization/`):
- [ ] `.protocol-state/authorization/session-state.json`

**JJK Character Reference** (`.protocol-state/jjk-character-reference/`):
- [ ] `.protocol-state/jjk-character-reference/ryomen-sukuna.md`
- [ ] `.protocol-state/jjk-character-reference/satoru-gojo.md`

### 3.9 Scripts Directory (`scripts/`)

- [ ] `scripts/verify-protocol.ps1` (Windows)
- [ ] `scripts/verify-protocol.sh` (Linux/Mac)
- [ ] `scripts/validate-protocol.py` (Python - cross-platform validation)
- [ ] `scripts/domain-record-rotate.py` (Python - domain record rotation, v8.8.0+)
- [ ] `scripts/verify-installation.py` (Python - cross-platform)
- [ ] `scripts/sync-templates.py` (Python - cross-platform)

### 3.10 Domain Zero Agents Templates

**Generic Templates** (`Domain Zero Agents/`):
- [ ] `Domain Zero Agents/DOMAIN_ZERO_AGENT.md`
- [ ] `Domain Zero Agents/EXAMPLE_TODO_AGENT.md`
- [ ] `Domain Zero Agents/EXTENDED_FOUR_INTRO.md`
- [ ] `Domain Zero Agents/README.md`

**JJK Edition** (`Domain Zero Agents - Full JJK Edition/`):
- [ ] `Domain Zero Agents - Full JJK Edition/AGENT_INVOCATION_GUIDE.md`
- [ ] `Domain Zero Agents - Full JJK Edition/AGENT_MODEL_RECOMMENDATIONS.md`
- [ ] `Domain Zero Agents - Full JJK Edition/AGENT_TOOLS_REFERENCE.md`
- [ ] `Domain Zero Agents - Full JJK Edition/GOJO.md`
- [ ] `Domain Zero Agents - Full JJK Edition/INUMAKI.md`
- [ ] `Domain Zero Agents - Full JJK Edition/JJK_AGENT_TEMPLATE.md`
- [ ] `Domain Zero Agents - Full JJK Edition/MAKI.md`
- [ ] `Domain Zero Agents - Full JJK Edition/MEGUMI.md`
- [ ] `Domain Zero Agents - Full JJK Edition/NOBARA.md`
- [ ] `Domain Zero Agents - Full JJK Edition/PANDA.md`
- [ ] `Domain Zero Agents - Full JJK Edition/README.md`
- [ ] `Domain Zero Agents - Full JJK Edition/TODO.md`
- [ ] `Domain Zero Agents - Full JJK Edition/YUUJI.md`

### 3.11 Slash Commands (`.claude/commands/`) - OPTIONAL

If using Claude Code CLI:
- [ ] `.claude/commands/gojo.md`
- [ ] `.claude/commands/yuuji.md`
- [ ] `.claude/commands/megumi.md`
- [ ] `.claude/commands/nobara.md`
- [ ] `.claude/commands/todo.md`
- [ ] `.claude/commands/maki.md`
- [ ] `.claude/commands/panda.md`
- [ ] `.claude/commands/inumaki.md`
- [ ] `.claude/commands/sukuna.md`

**If missing**: See `docs/installation/SLASH_COMMANDS_INSTALLATION.md`

---

## 4. Template Syncing Procedures

**Problem**: Template files (`.template.*` and `.example.*`) are **NOT** automatically used. They must be copied to working locations.

### 4.1 Templates That Need Syncing

| Template File | → | Working File | Status |
|---------------|---|--------------|--------|
| `.protocol-state/session-state.example.json` | → | `.protocol-state/session-state.json` | Auto-created by session_monitor.py |
| `.protocol-state/custom-agent-registry.example.json` | → | `.protocol-state/custom-agent-registry.json` | User must create if using custom agents |
| `.protocol-state/system-update-framework/backup-manifest.template.json` | → | `.protocol-state/system-update-framework/backup-manifest.json` | Created on first Sukuna invocation |
| `.protocol-state/system-update-framework/file-classifications.template.json` | → | `.protocol-state/system-update-framework/file-classifications.json` | Created on first Sukuna invocation |
| `.protocol-state/system-update-framework/version-registry.template.json` | → | `.protocol-state/system-update-framework/version-registry.json` | Created on first Sukuna invocation |
| `.protocol-state/system-update-framework/plan-documentation.template.md` | → | `.protocol-state/system-update-framework/plan-documentation.md` | Already exists (not template) |
| `.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.template.md` | → | `.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.md` | Already exists (not template) |

### 4.2 Automated Template Syncing

**Run this Python script** to sync all templates:

```python
# scripts/sync-templates.py
import shutil
from pathlib import Path

def sync_templates():
    """Sync .template.* and .example.* files to working locations"""

    templates = [
        # (source, destination, create_if_missing)
        ('.protocol-state/session-state.example.json',
         '.protocol-state/session-state.json', False),  # Created by session_monitor.py

        ('.protocol-state/custom-agent-registry.example.json',
         '.protocol-state/custom-agent-registry.json', True),

        ('.protocol-state/system-update-framework/backup-manifest.template.json',
         '.protocol-state/system-update-framework/backup-manifest.json', True),

        ('.protocol-state/system-update-framework/file-classifications.template.json',
         '.protocol-state/system-update-framework/file-classifications.json', True),

        ('.protocol-state/system-update-framework/version-registry.template.json',
         '.protocol-state/system-update-framework/version-registry.json', True),
    ]

    for src, dst, create in templates:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            print(f"⚠️  Template missing: {src}")
            continue

        if dst_path.exists() and not create:
            print(f"✅ Already exists (skipping): {dst}")
            continue

        if create:
            shutil.copy2(src, dst)
            print(f"✅ Synced: {src} → {dst}")

if __name__ == '__main__':
    sync_templates()
```

**Run it**:
```bash
python scripts/sync-templates.py
```

**Expected Output**:
```text
✅ Synced: .protocol-state/custom-agent-registry.example.json → ...
✅ Synced: .protocol-state/system-update-framework/backup-manifest.template.json → ...
✅ Synced: .protocol-state/system-update-framework/file-classifications.template.json → ...
✅ Synced: .protocol-state/system-update-framework/version-registry.template.json → ...
```

---

## 5. Subfolder Verification

**Problem**: Missing subfolders cause import errors and broken references.

### 5.1 Required Subfolders

Run this check to verify ALL subfolders exist:

```bash
# Windows PowerShell
$folders = @(
    "protocol",
    "protocol/modules",
    "protocol/gojo-procedures",
    "protocol/skills",
    "docs",
    "docs/guides",
    "docs/installation",
    "docs/reference",
    "docs/templates",
    ".dzp-domain",
    ".dzp-domain/archive",
    ".protocol-state",
    ".protocol-state/system-update-framework",
    ".protocol-state/authorization",
    ".protocol-state/jjk-character-reference",
    ".protocol-state/backups",
    "scripts",
    "Domain Zero Agents",
    "Domain Zero Agents - Full JJK Edition",
    ".claude",
    ".claude/commands"
)

foreach ($folder in $folders) {
    if (Test-Path $folder) {
        Write-Host "✅ $folder"
    } else {
        Write-Host "❌ MISSING: $folder"
        New-Item -ItemType Directory -Path $folder -Force
        Write-Host "  → Created: $folder"
    }
}
```

**Linux/Mac**:
```bash
folders=(
    "protocol"
    "protocol/modules"
    "protocol/gojo-procedures"
    "protocol/skills"
    "docs"
    "docs/guides"
    "docs/installation"
    "docs/reference"
    "docs/templates"
    ".dzp-domain"
    ".dzp-domain/archive"
    ".protocol-state"
    ".protocol-state/system-update-framework"
    ".protocol-state/authorization"
    ".protocol-state/jjk-character-reference"
    ".protocol-state/backups"
    "scripts"
    "Domain Zero Agents"
    "Domain Zero Agents - Full JJK Edition"
    ".claude"
    ".claude/commands"
)

for folder in "${folders[@]}"; do
    if [ -d "$folder" ]; then
        echo "✅ $folder"
    else
        echo "❌ MISSING: $folder"
        mkdir -p "$folder"
        echo "  → Created: $folder"
    fi
done
```

---

## 6. Automated Verification

**MANDATORY**: Run this script after ANY installation/upgrade.

### 6.1 Complete Verification Script

**Create**: `scripts/verify-installation.py`

```python
#!/usr/bin/env python3
"""
Domain Zero Protocol - Installation Verification
Verifies complete file structure and identifies missing components
"""

from pathlib import Path
import sys

# Complete file manifest (based on Section 3)
REQUIRED_FILES = {
    # Root files
    'AI_INSTRUCTIONS.md': 'Root',
    'CHANGELOG.md': 'Root',
    'LICENSE': 'Root',
    'PASSIVE_OBSERVER.md': 'Root',
    'protocol.config.yaml': 'Root',
    'PROTOCOL_QUICKSTART.md': 'Root',
    'README.md': 'Root',
    'SECURITY.md': 'Root',
    'VERSION.md': 'Root',

    # Protocol agents
    'protocol/gojo.agent.md': 'Agent',
    'protocol/yuuji.agent.md': 'Agent',
    'protocol/megumi.agent.md': 'Agent',
    'protocol/nobara.agent.md': 'Agent',
    'protocol/todo.agent.md': 'Agent',
    'protocol/maki.agent.md': 'Agent',
    'protocol/panda.agent.md': 'Agent',
    'protocol/inumaki.agent.md': 'Agent',
    'protocol/sukuna.agent.md': 'Agent',

    # Protocol main
    'protocol/CLAUDE.md': 'Protocol',

    # Protocol reference
    'protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md': 'Reference',
    'protocol/CANONICAL_SOURCE_ADOPTION.md': 'Reference',
    'protocol/EMERGENCY_STOP_STANDARD.md': 'Reference',
    'protocol/ENVIRONMENT_TARGETING.md': 'Reference',
    'protocol/HANDOFF_SPECIFICATION.md': 'Reference',
    'protocol/MASK_MODE.md': 'Reference',
    'protocol/MCP_INTEGRATION.md': 'Reference',
    'protocol/MODE_INDICATORS.md': 'Reference',
    'protocol/RESEARCH_MODE.md': 'Reference',
    'protocol/TECHNICAL_LEVEL_ADAPTATION.md': 'Reference',
    'protocol/TIER-SELECTION-GUIDE.md': 'Reference',

    # Protocol modules
    'protocol/modules/BINDING_OATH.md': 'Module',
    'protocol/modules/EMERGENCY_STOP_PROTOCOL.md': 'Module',
    'protocol/modules/ESCAPE_PATH_PROTOCOL.md': 'Module',
    'protocol/modules/MASK_MODE_BEHAVIOR.md': 'Module',
    'protocol/modules/MISSION_CONTROL_ISOLATION.md': 'Module',
    'protocol/modules/SAFETY_FIRST.md': 'Module',
    'protocol/modules/USER_LEVEL_ADAPTATION.md': 'Module',

    # Gojo procedures
    'protocol/gojo-procedures/OPERATIONAL_PROCEDURES.md': 'Procedures',

    # Skills
    'protocol/skills/AGENT_SKILLS_MAP.yaml': 'Skills',
    'protocol/skills/SKILL_REGISTRY.md': 'Skills',
    'protocol/skills/skill-builder.md': 'Skills',

    # Documentation
    'docs/FAQ.md': 'Docs',
    'docs/DZP_DZA_INSTALLATION_REVIEW.md': 'Docs',
    'docs/SYSTEM_UPDATE_IMPLEMENTATION_GUIDE.md': 'Docs',
    'docs/TOKEN_EFFICIENCY_RECOMMENDATIONS.md': 'Docs',

    # Docs - Guides
    'docs/guides/AGENT_BINDING_OATH.md': 'Guides',
    'docs/guides/CREATING_CLAUDE_AGENTS.md': 'Guides',
    'docs/guides/DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md': 'Guides',
    'docs/guides/EMERGENCY_STOP_GUIDE.md': 'Guides',
    'docs/guides/TIER_TRANSITION_GUIDE.md': 'Guides',
    'docs/guides/USER_LEVEL_GUIDE.md': 'Guides',

    # Docs - Installation
    'docs/installation/IMPLEMENTATION_GUIDE.md': 'Installation',
    'docs/installation/MCP_SERVER_SETUP.md': 'Installation',
    'docs/installation/SLASH_COMMANDS_INSTALLATION.md': 'Installation',

    # Docs - Reference
    'docs/reference/AUTHORIZATION_PROTOCOL.md': 'Reference',
    'docs/reference/DOMAIN_ZERO_RESEARCH_AND_SKILLS_GUIDE.md': 'Reference',
    'docs/reference/INSTRUCTION_CONFIRMATION_PROTOCOL.md': 'Reference',
    'docs/reference/MIGRATION_GUIDE_TEMPLATE.md': 'Reference',
    'docs/reference/playwright.md': 'Reference',
    'docs/reference/REALITY_CHECK.md': 'Reference',

    # Docs - Templates
    'docs/templates/DECISION_REASONING_TEMPLATE.md': 'Templates',

    # State files
    '.protocol-state/custom-agent-registry.example.json': 'State',
    '.protocol-state/custom_agent_monitor.py': 'State',
    '.protocol-state/gojo-session-monitoring-guide.md': 'State',
    '.protocol-state/session_monitor.py': 'State',
    '.protocol-state/session-state.example.json': 'State',
    '.protocol-state/work-session-alert.template.md': 'State',
    '.protocol-state/WORK_SESSION_STATUS.md': 'State',

    # System Update Framework
    '.protocol-state/system-update-framework/backup-manifest.template.json': 'SUF',
    '.protocol-state/system-update-framework/file-classifications.template.json': 'SUF',
    '.protocol-state/system-update-framework/plan-documentation.md': 'SUF',
    '.protocol-state/system-update-framework/plan-documentation.template.md': 'SUF',
    '.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.md': 'SUF',
    '.protocol-state/system-update-framework/SYSTEM_UPDATE_FRAMEWORK.template.md': 'SUF',
    '.protocol-state/system-update-framework/version-registry.template.json': 'SUF',

    # JJK Character Reference
    '.protocol-state/jjk-character-reference/ryomen-sukuna.md': 'JJK',
    '.protocol-state/jjk-character-reference/satoru-gojo.md': 'JJK',

    # Scripts
    'scripts/verify-protocol.ps1': 'Scripts',
    'scripts/verify-protocol.sh': 'Scripts',
}

# Optional files (won't fail if missing)
OPTIONAL_FILES = {
    '.protocol-state/project-state.json': 'State (created on first use)',
    '.protocol-state/session-state.json': 'State (created by session_monitor.py)',
    '.protocol-state/authorization/session-state.json': 'Auth (created on first use)',
}

def verify_installation():
    """Verify complete DZP installation"""

    missing_files = []
    present_files = []

    print("=" * 70)
    print("DOMAIN ZERO PROTOCOL - INSTALLATION VERIFICATION")
    print("=" * 70)
    print()

    # Check required files
    for file_path, category in REQUIRED_FILES.items():
        path = Path(file_path)
        if path.exists():
            present_files.append((file_path, category))
        else:
            missing_files.append((file_path, category))

    # Report results
    total = len(REQUIRED_FILES)
    present_count = len(present_files)
    missing_count = len(missing_files)

    print(f"📊 RESULTS: {present_count}/{total} files present")
    print()

    if missing_count == 0:
        print("✅ INSTALLATION COMPLETE - All required files present")
        print()
        print("Next steps:")
        print("1. Run: python scripts/sync-templates.py")
        print("2. Read: protocol/CLAUDE.md")
        return 0

    else:
        print(f"❌ INSTALLATION INCOMPLETE - {missing_count} files missing")
        print()
        print("MISSING FILES:")
        print()

        # Group by category
        by_category = {}
        for file_path, category in missing_files:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(file_path)

        for category, files in sorted(by_category.items()):
            print(f"  {category} ({len(files)} missing):")
            for file_path in sorted(files):
                print(f"    ❌ {file_path}")
            print()

        print("RECOVERY STEPS:")
        print("1. Identify source: core-files-vX.Y.Z/ directory")
        print("2. Copy missing files from source to current directory")
        print("3. Re-run this verification script")
        print("4. See Section 9 in AI_INSTRUCTIONS.md for detailed recovery")
        print()

        return 1

if __name__ == '__main__':
    exit_code = verify_installation()
    sys.exit(exit_code)
```

### 6.2 Running Verification

```bash
# Make executable (Linux/Mac)
chmod +x scripts/verify-installation.py

# Run verification
python scripts/verify-installation.py

# Expected output if complete:
# ✅ INSTALLATION COMPLETE - All required files present (X/X files present)

# Expected output if incomplete:
# ❌ INSTALLATION INCOMPLETE - Y files missing
# [List of missing files by category]
```

---

## 7. In-Place Upgrade Procedure

**Goal**: Upgrade existing DZP installation without losing user data.

### 7.1 Pre-Upgrade Checklist

- [ ] Current version noted: `_____`
- [ ] Target version identified: `_____`
- [ ] Backup created: `_____`
- [ ] User data identified (`.protocol-state/*.json`)

### 7.2 Critical Files to PRESERVE

**⚠️ DO NOT OVERWRITE THESE**:
- `.protocol-state/project-state.json` (user project configuration)
- `.protocol-state/session-state.json` (current work session)
- `.protocol-state/custom-agent-registry.json` (custom agents)
- `.protocol-state/dev-notes.md` (implementation log)
- `.protocol-state/security-review.md` (security findings)
- `.protocol-state/trigger-19.md` (intelligence reports)
- Any `.protocol-state/backups/*` (user backups)
- `src/` (user source code)
- `tests/` (user tests)

### 7.3 Upgrade Steps

#### Step 1: Backup Current Installation

```bash
# Windows PowerShell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Path ".protocol-state/backups/pre-upgrade_$timestamp" -Force
Copy-Item -Path ".protocol-state/*.json" -Destination ".protocol-state/backups/pre-upgrade_$timestamp/" -ErrorAction SilentlyContinue

# Linux/Mac
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p .protocol-state/backups/pre-upgrade_$timestamp
cp .protocol-state/*.json .protocol-state/backups/pre-upgrade_$timestamp/ 2>/dev/null || true
```

#### Step 2: Extract New Core Files

```bash
# Identify source directory
ls core-files-v8.8.0/  # Example for v8.8.0

# Verify it exists
# If not, download from: https://github.com/DewyHRite/Domain-Zero-Protocol/releases
```

#### Step 3: Selective Copy (Preserve User Data)

```bash
# Copy CORE files only (NOT .protocol-state/*.json)
# Windows PowerShell
Copy-Item -Path "core-files-v8.8.0/protocol/*" -Destination "protocol/" -Recurse -Force
Copy-Item -Path "core-files-v8.8.0/docs/*" -Destination "docs/" -Recurse -Force
Copy-Item -Path "core-files-v8.8.0/*.md" -Destination "." -Force
Copy-Item -Path "core-files-v8.8.0/protocol.config.yaml" -Destination "." -Force

# Copy state TEMPLATES only (NOT actual state files)
Copy-Item -Path "core-files-v8.8.0/.protocol-state/*.template.*" -Destination ".protocol-state/" -Force
Copy-Item -Path "core-files-v8.8.0/.protocol-state/*.example.*" -Destination ".protocol-state/" -Force
Copy-Item -Path "core-files-v8.8.0/.protocol-state/*.py" -Destination ".protocol-state/" -Force
# Copy .md files EXCEPT user-maintained artifacts (dev-notes.md, security-review.md, trigger-19.md)
Get-ChildItem -Path "core-files-v8.8.0/.protocol-state/*.md" | Where-Object { $_.Name -notin @("dev-notes.md","security-review.md","trigger-19.md") } | Copy-Item -Destination ".protocol-state/" -Force

# Linux/Mac
cp -r core-files-v8.8.0/protocol/* protocol/
cp -r core-files-v8.8.0/docs/* docs/
cp core-files-v8.8.0/*.md .
cp core-files-v8.8.0/protocol.config.yaml .

# Copy templates only
cp core-files-v8.8.0/.protocol-state/*.template.* .protocol-state/
cp core-files-v8.8.0/.protocol-state/*.example.* .protocol-state/
cp core-files-v8.8.0/.protocol-state/*.py .protocol-state/
# Copy .md files EXCEPT user-maintained artifacts
for file in core-files-v8.8.0/.protocol-state/*.md; do
  filename=$(basename "$file")
  if [[ "$filename" != "dev-notes.md" && "$filename" != "security-review.md" && "$filename" != "trigger-19.md" ]]; then
    cp "$file" .protocol-state/
  fi
done
```

#### Step 4: Verify Upgrade

```bash
python scripts/verify-installation.py
```

#### Step 5: Sync Templates

```bash
python scripts/sync-templates.py
```

#### Step 6: Update Version

Edit `protocol.config.yaml`:
```yaml
versioning:
  protocol_version: "8.8.0"  # Update to new version
```

#### Step 7: Apply Patches from SUKUNA-REPORT.md (v8.8.0+)

**NEW IN v8.8.0**: Check for applicable patches in the self-service patch manifest.

```bash
# Read the patch manifest
Read protocol/SUKUNA-REPORT.md

# Filter patches applicable to this upgrade
# Check patch "Applies To" version range
# Example: If upgrading from v8.7.0 to v8.8.0, apply patches marked "v8.8.0+"

# For each ACTIVE patch with matching version:
# 1. Check "Required For" field (Upgrades vs New Installations)
# 2. Copy implementation code from patch entry
# 3. Apply to specified file
# 4. Run validation commands
# 5. Update patch status to APPLIED in local tracking

# Example patch application:
# If PATCH-SEC-005 (Session Monitor Duration Limits) is applicable:
# - Copy code from SUKUNA-REPORT.md Implementation section
# - Apply to .protocol-state/session_monitor.py
# - Run validation: python .protocol-state/session_monitor.py break 481 (should fail)
# - Mark as applied
```

**What to Apply**:
- Patches marked "Required For: Upgrades" with current version < patch version
- P0-Critical and P1-High patches (always recommended)
- P2-Medium and P3-Low patches (optional, user choice)

**Rollback Available**: Each patch includes rollback procedure if needed.

---

## 8. New Installation Procedure

**Goal**: Install complete DZP from scratch.

### 8.1 Installation Steps

#### Step 1: Verify Source Files

```bash
# Check core files directory exists
ls core-files-v8.8.0/

# If missing, download from:
# https://github.com/DewyHRite/Domain-Zero-Protocol/releases
```

#### Step 2: Copy All Files

```bash
# Windows PowerShell
Copy-Item -Path "core-files-v8.8.0/*" -Destination "." -Recurse -Force

# Linux/Mac
cp -r core-files-v8.8.0/* .
```

#### Step 3: Create Required Directories

```bash
# Windows PowerShell
New-Item -ItemType Directory -Path ".claude/commands" -Force
New-Item -ItemType Directory -Path ".protocol-state/backups" -Force
New-Item -ItemType Directory -Path "src" -Force
New-Item -ItemType Directory -Path "tests" -Force

# Linux/Mac
mkdir -p .claude/commands
mkdir -p .protocol-state/backups
mkdir -p src
mkdir -p tests
```

#### Step 4: Verify Installation

```bash
python scripts/verify-installation.py

# Expected: ✅ INSTALLATION COMPLETE
```

#### Step 5: Sync Templates

```bash
python scripts/sync-templates.py

# Expected: ✅ All templates synced
```

#### Step 6: Initialize Project State

```bash
# Run Gojo Mission Control to create project-state.json
Read protocol/gojo.agent.md

# Select Option 2: New Project Initialization
```

#### Step 7: Apply Required Patches from SUKUNA-REPORT.md (v8.8.0+)

**NEW IN v8.8.0**: Fresh installations should apply all patches marked "Required For: New Installations".

```bash
# Read the patch manifest
Read protocol/SUKUNA-REPORT.md

# Apply patches marked "Required For: New Installations"
# These are typically:
# - P0-Critical security patches
# - P1-High security patches
# - Essential functionality improvements

# For each required patch:
# 1. Verify patch applies to current version (check "Applies To" field)
# 2. Copy implementation code from patch entry
# 3. Apply to specified file
# 4. Run validation commands
# 5. Document in installation log

# Example: Apply PATCH-SEC-005 (Session Monitor Duration Limits)
# 1. Check: "Applies To: v8.8.0+" ✓
# 2. Copy duration limit code from Implementation section
# 3. Edit .protocol-state/session_monitor.py
# 4. Validate: python .protocol-state/session_monitor.py break 481
# 5. Expected: ❌ Error (duration limit enforced) = SUCCESS
```

**Why This Matters**:
- Security patches protect from known vulnerabilities
- Functionality patches ensure complete feature set
- Self-service model means no waiting for manual updates

**Optional Patches**: P2-Medium and P3-Low patches can be applied based on user preference.

---

## 9. Troubleshooting Missing Files

### 9.1 Identify Missing Files

#### Run verification

```bash
python scripts/verify-installation.py > missing-files-report.txt
cat missing-files-report.txt
```

### 9.2 Common Missing Files Issues

#### Issue 1: Missing Agent Files

```text
❌ protocol/yuuji.agent.md
❌ protocol/megumi.agent.md
```

#### Solution

```bash
cp core-files-v8.8.0/protocol/yuuji.agent.md protocol/
cp core-files-v8.8.0/protocol/megumi.agent.md protocol/
```

#### Issue 2: Missing Protocol Modules

```text
❌ protocol/modules/SAFETY_FIRST.md
❌ protocol/modules/BINDING_OATH.md
```

#### Solution for Issue 2

```bash
mkdir -p protocol/modules
cp core-files-v8.8.0/protocol/modules/* protocol/modules/
```

#### Issue 3: Missing State Files

```text
❌ .protocol-state/session_monitor.py
❌ .protocol-state/work-session-alert.template.md
```

#### Solution for Issue 3

```bash
cp core-files-v8.8.0/.protocol-state/session_monitor.py .protocol-state/
cp core-files-v8.8.0/.protocol-state/work-session-alert.template.md .protocol-state/
```

#### Issue 4: Missing Subfolders

```text
Directory not found: protocol/skills
```

#### Solution for Issue 4

```bash
mkdir -p protocol/skills
cp core-files-v8.8.0/protocol/skills/* protocol/skills/
```

### 9.3 Mass Recovery (Copy Everything)

**If many files missing**, use complete copy:

```bash
# Windows PowerShell
Copy-Item -Path "core-files-v8.8.0/*" -Destination "." -Recurse -Force -Exclude "*.json"

# Linux/Mac
rsync -av --exclude='*.json' core-files-v8.8.0/ ./
```

**Then verify**:
```bash
python scripts/verify-installation.py
```

---

## 10. Agent Invocation

**After completing installation verification**, you can now invoke agents:

### Core Four Agents

**Mission Control** (Project initialization):
```text
Read protocol/gojo.agent.md
```

**Implementation** (Test-first development):
```text
Read protocol/yuuji.agent.md and [your task]
```

**Security Review** (OWASP Top 10):
```text
Read protocol/megumi.agent.md and review [module/feature]
```

**Creative Strategy & UX** (Design, accessibility):
```text
Read protocol/nobara.agent.md and [design/strategy task]
```

### Extended Four Agents

**Database & Backend**:
```text
Read protocol/todo.agent.md and [database task]
```

**Performance & Infrastructure**:
```text
Read protocol/maki.agent.md and [performance task]
```

**Build & Integration**:
```text
Read protocol/panda.agent.md and [build task]
```

**API & Communication**:
```text
Read protocol/inumaki.agent.md and [API task]
```

### Slash Commands (If Installed)

| Command | Agent | Purpose |
|---------|-------|---------|
| `/gojo` | Mission Control | Project lifecycle |
| `/yuuji` | Implementation | TDD |
| `/megumi` | Security | OWASP reviews |
| `/nobara` | Creative/UX | Design |
| `/todo` | Orchestration | Task coordination |
| `/maki` | Performance | Optimization |
| `/panda` | QA | Testing |
| `/inumaki` | Documentation | Technical writing |
| `/sukuna` | System Update | Protocol updates (Gojo only) |

---

## Protocol Files

**After installation is verified**, read these files in order:

1. **[`protocol/CLAUDE.md`](protocol/CLAUDE.md)** - **START HERE** (Main protocol)
2. [`protocol.config.yaml`](protocol.config.yaml) - Configuration
3. Agent-specific `.agent.md` files as needed

---

## Canonical Source

> **Repository**: <https://github.com/DewyHRite/Domain-Zero-Protocol>
> **Version**: 8.8.0
> **Canonical File**: `protocol/CLAUDE.md`

All protocol updates originate from the canonical source.

---

## Summary Checklist for AI Assistants

**BEFORE reading protocol/CLAUDE.md, complete these steps**:

- [ ] Run `python scripts/verify-installation.py` → ✅ All files present
- [ ] Run `python scripts/sync-templates.py` → ✅ Templates synced
- [ ] Verify all subfolders exist (Section 5)
- [ ] Check `.protocol-state/session_monitor.py` exists
- [ ] Check `protocol/gojo.agent.md` exists
- [ ] Check `protocol/CLAUDE.md` exists

**If ANY checklist item fails**: Follow Section 9 (Troubleshooting) to recover missing files.

**Once complete**: Read `protocol/CLAUDE.md` and begin work.

---

## END OF AI_INSTRUCTIONS.md

---

**Domain Zero Protocol v8.8.0 - Complete Installation Guide**
**Updated**: 2025-12-17 (Domain Record System + Code Review Fixes)
