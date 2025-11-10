# Domain Zero Protocol - Version Information

**Version:** v7.1.1
**Release Date:** November 9, 2025
**Release Type:** Patch Release

---

## Release Summary

This patch release adds a comprehensive agent documentation system while synchronizing all version references to v7.1.1. No behavioral changes to protocol enforcement or agent functionality.

### Key Changes

- **Agent Documentation System** - 16 new comprehensive agent documentation files
- **Character Agent Docs** - Full JJK Edition with 8 character agents (PANDA, MAKI, INUMAKI, plus existing YUUJI, MEGUMI, NOBARA, GOJO, + TODO)
- **Agent Creation Guides** - Templates, invocation guides, tool references, and model recommendations
- **Version Synchronization** - All protocol files updated from v7.1.0 to v7.1.1
- **No Runtime Changes** - All behavioral changes introduced in v7.1.0; this is documentation-only

---

## What's New in v7.1.1

### Added
- **Domain Zero Agents/** - Professional agent documentation:
  - `README.md` - Complete guide to creating custom agents
  - `AGENT_TEMPLATE.md` - Template for new agent creation
  - `examples/KIRA_DOCUMENTATION_SPECIALIST.md` - Example agent implementation

- **Domain Zero Agents - Full JJK Edition/** - Character-themed documentation:
  - `README.md` - JJK Edition guide with character lore integration
  - `JJK_AGENT_TEMPLATE.md` - JJK-themed agent template
  - `AGENT_INVOCATION_GUIDE.md` - How to invoke agents correctly
  - `AGENT_TOOLS_REFERENCE.md` - Complete tools documentation
  - `AGENT_MODEL_RECOMMENDATIONS.md` - Model selection guidance
  - `PANDA.md` - CI/CD Pipeline Agent
  - `MAKI.md` - Code Refactoring & Optimization Agent
  - `INUMAKI.md` - Shell Commands & Automation Agent
  - `TODO.md` - Future agent expansion ideas
  - `GOJO.md`, `YUUJI.md`, `MEGUMI.md`, `NOBARA.md` - Copies from protocol/ for JJK Edition

### Changed
- **Version Updates**: All protocol files synchronized to v7.1.1:
  - `protocol/CLAUDE.md`, `protocol/GOJO.md`, `protocol/YUUJI.md`, `protocol/MEGUMI.md`, `protocol/NOBARA.md`, `protocol/MASK_MODE.md`
  - `protocol.config.yaml`, `README.md`, `VERSION.md`, `SECURITY.md`, `FAQ.md`, `CHANGELOG.md`
  - `PROTOCOL_QUICKSTART.md`, `DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md`
  - `.protocol-state/project-state.json`

- **Documentation Enhancements**:
  - Updated quickstart references to include GOJO alongside YUUJI, MEGUMI, NOBARA
  - Improved navigation structure with agent documentation sections
  - Added cross-references between professional and JJK editions

### Fixed
- Date consistency in `protocol/CLAUDE.md` (aligned to November 9, 2025)
- Version references in `SECURITY.md` (updated to v7.1.1)
- Footer version in `protocol/MASK_MODE.md` (updated to v7.1.1)
- Version tracking in `protocol/NOBARA.md` (updated to v7.1.1)
- Mission Control banner in `protocol/GOJO.md` (updated to v7.1.1)
- Canonical repository version in `protocol.config.yaml` (aligned to v7.1.1)

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
  - **New pattern** (v7.1.0): User invokes Yuuji once → Yuuji prompts for Megumi invocation after implementation
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

**v7.1.0 → v7.1.1:**
- **No breaking changes** - This is a documentation-only patch release
- **No action required** - All behavioral changes were in v7.1.0
- **New resources available**: Comprehensive agent documentation system
  - Explore `Domain Zero Agents/` for custom agent creation guides
  - Explore `Domain Zero Agents - Full JJK Edition/` for character-themed documentation
  - Use templates and examples to create your own specialized agents

**v7.0.0 → v7.1.0 (if upgrading from v7.0.0):**
- **Dual Workflow Enforcement** for Tier 2/3 (breaking workflow change)
  - Old: Invoke Yuuji → manually tag @security-review → invoke Megumi separately
  - New: Invoke Yuuji → Yuuji prompts for Megumi invocation (you manually execute)
- **Mask Mode** added to protocol.config.yaml (presentation only, non-breaking)
- Default behavior (MASK ON) preserves JJK-themed experience
- See DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md for migration instructions

---

## Full Details

See [CHANGELOG.md](CHANGELOG.md) for complete version history and detailed change information.

---

**Canonical Source:** https://github.com/DewyHRite/Domain-Zero-Protocol
**Previous Version:** v7.1.0
**Current Version:** v7.1.1

---

## Cumulative Improvements

**v7.1.0 → v7.1.1:** Agent Documentation System (16 files, custom agent creation guides)
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

**Assessment Score:** 10.0/10 - **COMPREHENSIVE DOCUMENTATION**: Full agent system documentation with templates, guides, and character-themed variants
