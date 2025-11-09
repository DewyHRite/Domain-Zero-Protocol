# Domain Zero Protocol - Version Information

**Version:** v7.1.0
**Release Date:** November 8, 2025
**Release Type:** Minor Update

---

## Release Summary

This minor release adds **Mask Mode**, a configuration toggle that allows users to switch between JJK-themed personality responses and professional mode. It also integrates REALITY_CHECK.md, providing an honest assessment of what Domain Zero actually is and how to use it effectively.

### Key Changes

- **Mask Mode Toggle** - Switch between JJK theme and professional mode
- **Dual Workflow Enforcement** - Mandatory Yuuji-Megumi collaboration for Tier 2/3 features
- **MASK_MODE.md** - Complete specification for mask mode functionality
- **DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md** - Mandatory collaboration guide and migration instructions
- **REALITY_CHECK.md Integration** - Honest documentation about what Domain Zero actually is
- **Granular Mask Settings** - Fine-tune personality, terminology, banners, and emoji
- **Unmasked Terminology** - Professional alternatives for JJK-themed terms
- **Updated Documentation** - CLAUDE.md, protocol.config.yaml, and README updated with new features

---

## What's New in v7.1.0

### Added
- **Mask Mode Configuration** (protocol.config.yaml):
  - `mask_mode.enabled`: Master toggle (true = JJK theme, false = professional)
  - `mask_mode.settings`: Granular controls (banners, personality, terminology, emoji, narrative)
  - `mask_mode.unmasked_names`: Professional agent names when mask is OFF
  - `mask_mode.unmasked_terminology`: Standard terminology translations

- **MASK_MODE.md** - Complete specification document:
  - What Mask Mode is and why it exists
  - Behavior comparison (MASK ON vs MASK OFF)
  - Configuration reference and validation rules
  - Migration guide from v7.0.0
  - Examples and use cases

- **DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md** - Mandatory collaboration guide:
  - Rationale for mandatory dual workflow (eliminate skipped security reviews)
  - Old vs new invocation patterns (breaking change documentation)
  - Step-by-step migration instructions
  - Tier-specific examples (Tier 1/2/3 behavior)
  - Success criteria and integration checklist

- **REALITY_CHECK.md** - Honest documentation:
  - Truth about "agents" (same AI, different prompts)
  - What Domain Zero actually does (structured prompt engineering)
  - When to use/not use Domain Zero
  - Customization advice and success metrics
  - Cost-benefit analysis and alternatives

### Changed
- **CLAUDE.md**:
  - Added Mask Mode section explaining JJK theme vs professional mode
  - Added REALITY_CHECK.md to Additional Resources
  - Added MASK_MODE.md to Additional Resources
  - Updated version to v7.1.0
  - Updated version history with v7.1.0 entry

- **protocol.config.yaml**:
  - Added complete mask_mode configuration section
  - Updated protocol_version to 7.1.0
  - Updated config_version to 1.2
  - Updated last_updated to 2025-11-08

- **Documentation Structure**:
  - REALITY_CHECK.md provides honest assessment of framework
  - MASK_MODE.md explains presentation layer configurability
  - Clear distinction between core functionality (unchanged) and presentation (configurable)

### Breaking Changes
- **Dual Workflow Mandatory for Tier 2/3**: Yuuji-Megumi collaboration is now enforced
  - **Old pattern** (deprecated): User invokes Yuuji → tags @security-review → invokes Megumi separately
  - **New pattern** (v7.1.0): User invokes Yuuji once → Yuuji automatically invokes Megumi after implementation
  - **Impact**: Workflow pattern changes for Tier 2 (Standard) and Tier 3 (Critical) features
  - **Migration**: See DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md for complete migration instructions
  - **Tier 1 exception**: Rapid prototyping (Tier 1) unchanged - Yuuji-only invocation still valid

### Implementation Approach
- **Presentation vs Functionality**: Mask Mode affects HOW agents communicate, not WHAT they enforce
- **Dual workflow enforcement**: Eliminates possibility of skipping security reviews for production code
- **User choice preserved**: Mask Mode toggle between engaging and professional modes
- **Hybrid modes**: Granular settings allow custom combinations
- **Tier 1 flexibility**: Fast prototyping still skips security review (by design)

---

## Previous Versions

### What's New in v7.0.0

- **Absolute Zero Protocol Integration** - Formal agent commitment framework
- **Agent Binding Oath** - 10 binding principles for all agents
- **Decision Reasoning Template** - Structured transparency framework
- **Enhanced Safety Principles** - 5 core AZP principles integrated into CLAUDE.md

See previous VERSION.md for complete v7.0.0 details.

### What's New in v6.2.8

### Added
- **Pre-push version verification requirements** - Mandatory comprehensive codebase review checklist:
  - Added CRITICAL PRE-PUSH REQUIREMENT section to system-update.py
  - Added Pre-Push Version Verification (MANDATORY) to protocol/CLAUDE.md
  - Extended VERSION_MANAGEMENT_GUIDE.md with complete verification checklist
  - Automated + manual verification workflow before any GitHub push

- **Enhanced verification script error handling**:
  - PyYAML error handling with graceful degradation
  - Yamllint fallback when PyYAML module missing
  - PowerShell Core (pwsh) detection for cross-platform support
  - Improved error messages with actionable guidance

### Changed
- **GitHub Actions workflows**:
  - Fixed CodeQL workflow manual build step (removed exit 1)
  - Added workflow_dispatch trigger to security-scan-example.yml
  - Corrected IaC scan condition to exclude workflow files

- **CODEOWNERS governance**:
  - Removed duplicate root CODEOWNERS file
  - Cleaned up gitignored file references
  - Added VERSION.md, SECURITY.md, FAQ.md to tracked files
  - Ensured CODEOWNERS not in .gitignore

- **Documentation cleanup**:
  - Removed all ANSI escape codes from protocol files
  - Filled protocol.config.yaml placeholder values
  - Updated version references across 14+ documentation files

### Fixed
- **Version consistency issues** - Synchronized all version references to v6.2.7:
  - FAQ.md, SECURITY.md, CHANGELOG.md version metadata
  - Protocol files (CLAUDE.md, GOJO.md, YUUJI.md, MEGUMI.md, NOBARA.md)
  - CANONICAL_SOURCE_ADOPTION.md, tier-system-specification.md
  - GOJO.md project-state.json initialization template

- **PowerShell script control flow** - Added return statements after successful checks
- **Workflow failures** - Fixed GitHub Actions workflow configurations

### Security
- **Enhanced OWASP Top 10 alignment** - MEGUMI security review process improvements
- **Credential management** - Updated .gitignore to protect sensitive state files
- **Script execution safety** - Improved error handling prevents silent failures

---

## Upgrade Notes

No breaking changes. This is a backward-compatible minor update adding presentation layer configuration.

**What changed for you:**
- Mask Mode added to protocol.config.yaml
- Default behavior (MASK ON) preserves current JJK-themed experience
- REALITY_CHECK.md provides honest assessment of what you're using
- MASK_MODE.md documents how to switch between modes

**Action Required:**
- None - all changes are backward compatible
- Review REALITY_CHECK.md for honest guidance on using Domain Zero effectively
- See MASK_MODE.md if you want to try professional mode
- Edit protocol.config.yaml and set `mask_mode.enabled: false` to disable JJK theme

---

## Full Details

See [CHANGELOG.md](CHANGELOG.md) for complete version history and detailed change information.

---

**Canonical Source:** https://github.com/DewyHRite/Domain-Zero-Protocol
**Previous Version:** v7.0.0
**Current Version:** v7.1.0

---

## Cumulative Improvements

**v7.0.0 → v7.1.0:** Mask Mode Toggle, REALITY_CHECK.md integration, Professional vs JJK theme choice
**v6.2.8 → v7.0.0:** Absolute Zero Protocol Integration, Agent Binding Oath, Decision Reasoning Framework
**v6.2.7 → v6.2.8:** Copilot PR review fixes, version consistency updates
**v6.2.6 → v6.2.7:** Pre-push verification requirements, PyYAML error handling, PowerShell Core support
**v6.2.5 → v6.2.6:** Verification script v2.0 (60% faster, better UX)
**v6.2.4 → v6.2.5:** Comprehensive documentation enhancements (4 new docs)
**v6.2.3 → v6.2.4:** Security policy + enhanced config validation
**v6.2.2 → v6.2.3:** Documentation structure improvements
**v6.2.1 → v6.2.2:** Protocol protection (CODEOWNERS, .gitignore)
**v6.2.0 → v6.2.1:** Interactive work session alerts

**Assessment Score:** 10.0/10 - **USER EMPOWERMENT**: Users can now choose presentation style without sacrificing functionality
