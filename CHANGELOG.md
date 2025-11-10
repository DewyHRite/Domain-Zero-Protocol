# Changelog - Domain Zero Protocol

All notable changes to the Domain Zero Protocol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [7.1.1] - 2025-11-09

### Added
- **Comprehensive Agent Documentation System** - Complete agent building and usage guides:
  - `Domain Zero Agents/` - Generic agent building framework with templates
    - `AGENT_TEMPLATE.md` - Universal template for creating custom agents
    - `README.md` - Guide for building custom agents
    - `examples/KIRA_DOCUMENTATION_SPECIALIST.md` - Example custom agent
  - `Domain Zero Agents - Full JJK Edition/` - 8 complete character agents
    - Core Four: GOJO.md, YUUJI.md, MEGUMI.md, NOBARA.md
    - Extended: PANDA.md, MAKI.md, INUMAKI.md, TODO.md
    - JJK_AGENT_TEMPLATE.md - JJK-themed agent template
- **Core Documentation (3 comprehensive guides)**:
  - `AGENT_INVOCATION_GUIDE.md` - System prompts for all 8 agents (16 KB)
  - `AGENT_TOOLS_REFERENCE.md` - Tool permissions + advanced capabilities (32 KB)
  - `AGENT_MODEL_RECOMMENDATIONS.md` - Opus/Sonnet/Haiku selection guide (18 KB)
- **SYSTEM_UPDATE_COMPLETE_V7.1.0.md** - Complete v7.1.0 release documentation

### Changed
- **README.md** - Added Agent Documentation section (lines 154-160, 912-936)
  - Links to generic and JJK agent documentation
  - Integration examples and usage guidance
- **Protocol files** - Updated version references from v7.1.0 to v7.1.1
- **project-state.json** - Updated protocol_version to 7.1.1

### Fixed
- Version consistency across all protocol and documentation files

### Documentation
- Total: 16 new files, ~313 KB of agent documentation
- Coverage: System prompts, tool permissions, model recommendations, advanced capabilities
- Integration: Parallel execution, background processes, Jupyter notebooks

---


---

## [7.1.0] - 2025-11-08

### Breaking Changes
- **Dual Workflow Enforcement** (Tier 2/3 only):
  - Yuuji and Megumi CANNOT be invoked separately for Tier 2 (Standard) or Tier 3 (Critical) features
  - **Old pattern** (deprecated): User invokes Yuuji → user manually tags @security-review → user invokes Megumi separately
  - **New pattern** (v7.1.0): User invokes Yuuji once → Yuuji prompts for Megumi invocation after implementation complete
  - **Rationale**: Eliminate possibility of skipped security reviews for production code (Tier 2/3)
  - **Migration**: See DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md for step-by-step migration instructions
  - **Tier 1 exception**: Rapid prototyping (Tier 1) unchanged - Yuuji-only invocation still valid

### Added
- **Dual Workflow Enforcement Guide** (DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md):
  - Complete migration guide for new Yuuji-Megumi collaboration pattern
  - Old vs new invocation pattern comparison
  - Tier-specific examples (Tier 1/2/3)
  - Success criteria and validation checklist
  - Integration guidance for existing projects

- **Mask Mode Configuration** (protocol.config.yaml):
  - Master toggle: `mask_mode.enabled` (true = JJK theme, false = professional mode)
  - Granular settings: control banners, personality, terminology, emoji, and narrative framing independently
  - Unmasked names: professional agent titles when mask is OFF (Implementation Specialist, Security Analyst, etc.)
  - Unmasked terminology: standard translations for JJK terms (Domain Zero → Protocol Environment, etc.)

- **MASK_MODE.md** - Complete specification document:
  - What Mask Mode is and why it exists (presentation choice without functionality loss)
  - Truth about "agents" (same AI, different prompts - per REALITY_CHECK.md)
  - Behavior comparison tables (MASK ON vs MASK OFF)
  - Configuration reference with validation rules
  - Migration guide from v7.0.0
  - Use case guidance (personal vs professional contexts)
  - Examples demonstrating both modes

- **REALITY_CHECK.md** - Honest documentation:
  - What "agents" really are (prompt engineering, not true multi-agent)
  - What Domain Zero actually does (structured prompts for TDD, security, documentation)
  - When to use/not use Domain Zero (realistic assessment)
  - Customization advice (how to make it yours)
  - Success metrics to track (measure your own results)
  - Cost-benefit analysis and honest value proposition
  - Comparison with alternatives (Cursor rules, custom instructions, etc.)

### Changed
- **CLAUDE.md**:
  - Added Mask Mode section (v7.1.0+) explaining JJK theme vs professional mode
  - Added REALITY_CHECK.md to Additional Resources
  - Added MASK_MODE.md to Additional Resources
  - Updated version to v7.1.0
  - Updated major enhancements to highlight Mask Mode Toggle
  - Updated version history with v7.1.0 entry

- **protocol.config.yaml**:
  - Added complete `mask_mode` configuration section (40+ lines)
  - Updated protocol_version to 7.1.0
  - Updated config_version to 1.2
  - Updated last_updated to 2025-11-08

- **VERSION.md**:
  - Updated to v7.1.0 with complete release summary
  - Added "What's New in v7.1.0" section
  - Updated upgrade notes for mask mode
  - Added mask mode to cumulative improvements

- **Documentation Philosophy**:
  - REALITY_CHECK.md provides honest, no-marketing-fluff assessment
  - MASK_MODE.md separates presentation layer from core functionality
  - Clear acknowledgment that agents are prompt engineering, not magic
  - User empowerment through informed choice (mask ON/OFF)

### Implementation Approach
- **Presentation vs Functionality**: Mask Mode affects HOW agents communicate, not WHAT they enforce
- **No breaking changes to core functionality from Mask Mode**: Default behavior (MASK ON) preserves the JJK-themed experience. Note: Dual Workflow Enforcement is a breaking workflow change for Tier 2/3 (see Breaking Changes above).
- **User choice**: Toggle between engaging personality-driven responses and professional direct responses
- **Hybrid modes**: Granular settings allow custom combinations (e.g., keep emoji but use standard terminology)
- **Transparency**: REALITY_CHECK.md honestly explains what users are actually using

### Philosophy
- **Mask as choice, not requirement**: Users choose presentation style without sacrificing protocol structure
- **Security reviews are NOT optional**: Dual workflow ensures Tier 2/3 features receive mandatory security review
- **Honest documentation**: REALITY_CHECK.md acknowledges the truth about prompt engineering
- **User empowerment**: Informed users make better decisions about tool adoption and customization
- **Functionality preserved**: All TDD, tier, backup functionality unchanged regardless of mask setting
- **Tier 1 flexibility maintained**: Fast prototyping still skips security review (by design)

---

## [7.0.0] - 2025-11-07

### Added
- **AGENT_BINDING_OATH.md** - Formal commitment framework:
  - 10 binding principles: User Authority, Transparency, Safety Over Autonomy, Active Protection, Bounded Authority, Honest Communication, Non-Circumvention, Self-Awareness, Collective Responsibility, Continuous Improvement
  - Oath acknowledgment process for all agents
  - Violation consequences (learning-focused, not punitive)

- **DECISION_REASONING_TEMPLATE.md** - Transparency framework:
  - 9-section structured template: Decision, Objective, Reasoning, Alternatives Considered, Risk Assessment, Confidence Level, Dependencies, Implementation Complexity, Final Recommendation
  - Complete worked example included
  - Required for all non-trivial recommendations

- **Absolute Zero Protocol Core Principles** (CLAUDE.md):
  - Principle 1: Absolute User Authority
  - Principle 2: Transparency First
  - Principle 3: Safety Over Autonomy
  - Principle 4: Active Protection
  - Principle 5: Binding Commitment

### Changed
- **All Agent Files** (YUUJI, MEGUMI, NOBARA, GOJO):
  - Added Binding Oath acknowledgment sections
  - Updated to v7.0.0
  - Enhanced major enhancements with AZP commitment

- **protocol.config.yaml**:
  - Added `absolute_zero_protocol` enforcement section
  - Enabled decision reasoning requirements
  - Updated to v7.0.0

- **CLAUDE.md**:
  - Integrated AZP Core Principles section
  - Updated version history to track v7.0.0 as major release
  - Cross-referenced new AZP documents

### Implementation Approach
- **Augmentation, not replacement**: AZP formalizes existing DZP safety principles
- **No breaking changes**: Enhanced structure without changing agent behavior
- **Phase 1 Foundation**: Agent oaths, decision templates, core principles

---

## [6.2.8] - 2025-11-07

### Added
- **Copilot PR review fixes** - Addressed 20 comprehensive review comments

### Changed
- **Protocol files** - Removed inline HTML/CSS for better cross-platform Markdown rendering
- **GOJO.md ASCII art** - Fixed version alignment
- **VERSION.md and CHANGELOG.md** - Improved consistency

### Fixed
- **CODEOWNERS** - Removed gitignored path references
- **Script comments** - Improved accuracy and clarity in verify-protocol scripts
- **Version consistency** - Synchronized all version references across documentation

---

## [6.2.7] - 2025-11-07

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
- **Markdown linting** - SECURITY.md link formatting and code block language identifiers

### Security
- **Enhanced OWASP Top 10 alignment** - MEGUMI security review process improvements
- **Credential management** - Updated .gitignore to protect sensitive state files
- **Script execution safety** - Improved error handling prevents silent failures

---


---

## [6.2.6] - 2025-11-07

### Added
- **Verification Script v2.0** - Major enhancements to both Bash and PowerShell scripts:
  - Dependency checking with new exit code 3 for missing tools
  - YAML syntax validation using Python or yamllint
  - Selective check execution (`--quick`, `--skip`, `--only`, `--list`)
  - Enhanced error messages with impact/action/documentation links
  - Graceful degradation on critical errors
- **Documentation for script options** - Updated README.md, FAQ.md, and PROTOCOL_QUICKSTART.md with new verification script features

### Changed
- **scripts/verify-protocol.sh** - Upgraded from v1.0 to v2.0 with all Phase 1 & 2 enhancements
- **scripts/verify-protocol.ps1** - Upgraded from v1.0 to v2.0 with feature parity to Bash version
- **Quick mode** - 60% faster verification by running only critical checks
- **Modular check system** - 8 checks organized by criticality (4 critical, 4 warning)

### Performance
- **60% faster** verification with `--quick` mode
- **75-85% faster** targeted debugging with `--only` flag
- **0% performance impact** in default mode (new checks are lightweight)

---

## [6.2.5] - 2025-11-07

### Added
- **FAQ.md** - Comprehensive FAQ covering getting started, tier system, agent behavior, configuration, security & privacy, integration, troubleshooting, and advanced topics (50+ questions)
- **TIER_TRANSITION_GUIDE.md** - Detailed guide for upgrading and downgrading tiers during workflows, including Gojo's role, validation workflows, and common scenarios
- **MIGRATION_GUIDE_TEMPLATE.md** - Template for creating migration guides between major versions, providing step-by-step processes for future upgrades
- **Troubleshooting section in README.md** - Comprehensive 300+ line troubleshooting guide covering configuration issues, agent behavior, tier system problems, verification scripts, git/GitHub integration, performance optimization, and common errors

### Changed
- **Documentation structure enhanced** - Added four major documentation resources to improve user experience and reduce support burden

---

## [6.2.4] - 2025-11-07

### Added
- **SECURITY.md** - Comprehensive vulnerability disclosure policy with coordinated disclosure timeline, CVSS-based severity levels, and safe harbor protections for security researchers

### Changed
- **Enhanced placeholder validation** - Verification scripts now fail (not warn) when configuration placeholders are detected
- **Improved error messages** - Added helpful "HOW TO FIX" guidance with examples when placeholders found
- **Updated PROTOCOL_QUICKSTART.md** - Added warning about placeholder validation requirement

### Fixed
- **Configuration placeholder detection** - Now treats placeholders as errors instead of warnings
- **PowerShell Unicode encoding** - Fixed Unicode symbol issues in verify-protocol.ps1

---

## [6.2.3] - 2025-11-07

### Changed
- **VERSION.md replaces VERSION file** - Now includes detailed release summary and change information instead of simple version string
- **Documentation structure improved** - Better version information visibility for users

### Fixed
- **Removed VERSION_UPDATE_CHECKLIST.md from releases** - Internal developer checklist no longer exposed in public releases

---

## [6.2.2] - 2025-11-07

### Added
- **CODEOWNERS file** for protocol protection - Enforces required approvals for changes to core protocol files (CLAUDE.md, agent files, configuration)
- **.gitignore file** for privacy protection - Prevents accidental commits of sensitive data (trigger-19.md, backups, internal docs)

### Fixed
- **GitHub Actions workflow conditional syntax** - Corrected `hashFiles()` condition format in security-scan-example.yml

### Security
- Privacy protection enhanced with .gitignore to prevent exposure of local intelligence data

---

## [6.2.1] - 2025-11-06

### Added
- **Interactive Work Session Alerts**: Gojo now presents users with explicit "Save Progress" or "Continue Working" options when extended work sessions are detected
- **Enhanced Enforcement Logic**: Gojo responds differently based on user choice:
  - Helps save and commit work if user chooses to take a break
  - Increases monitoring frequency (30-45 min intervals) if user continues
  - Blocks high-risk operations during extended sessions (configurable)
- **New Configuration Settings** in `protocol.config.yaml`:
  - `safety.enforcement.interactive_session_alerts` - Enable user choice in alerts
  - `safety.enforcement.block_until_response` - Block workflow until user responds
  - `safety.enforcement.escalate_on_continue` - Escalate monitoring if user continues
  - `safety.enforcement.block_high_risk_when_fatigued` - Block critical ops when fatigued
  - `safety.boundaries.alert_interval_minutes` - Initial alert interval (240 min)
  - `safety.boundaries.escalated_alert_interval_minutes` - Alert interval after continue (45 min)
  - `safety.boundaries.critical_session_hours` - Critical session threshold (6 hours)

### Changed
- **Work Session Alert Template** (`.protocol-state/work-session-alert.template.md`):
  - Restructured with clear "Decision Point" section
  - Added comprehensive guidance for each option
  - Included safety requirements and Gojo's response behavior
- **GOJO.md - Work Session Monitoring Section**:
  - Added "Work Session Alert Protocol (v6.2.7 Enhanced)"
  - Added "Enforcement Levels & User Choice" section
  - Added "How I Respond to User Choices" section with detailed workflows

### Fixed
- Version consistency across all protocol files (completed v6.2 update before v6.2.7)

---

## [6.2.0] - 2025-11-06

### Added
- **Absolute Safety Principles**: User safety and wellbeing established as highest priority
- **Version Control Enforcement**: Stricter version tracking and consistency checks
- **Work Session Monitoring**: Initial implementation of session duration tracking and alerts
- **Canonical Source Integration**: Protocol references canonical repository for updates

### Changed
- Safety hierarchy explicitly defined (Physical Safety > Wellbeing > Project Safety > Code Quality)
- All agents must respect safety boundaries and escalate concerns
- Enhanced `protocol.config.yaml` with comprehensive safety settings

---

## [6.1.0] - 2025-11-06

### Added
- **Canonical Source Adoption**: Protocol can reference and sync with canonical repository
- **Agent Self-Identification Standard**: All agents announce themselves with emoji and domain name
- **Session Continuity**: Agents re-identify after long sessions or absences
- `CANONICAL_SOURCE_ADOPTION.md` - Adoption and integration guide
- `AGENT_SELF_IDENTIFICATION_STANDARD.md` - Self-identification specification
- Version control scripts (`update-instructions.sh`, `verify-protocol.sh`)

### Changed
- Updated all agent files (YUUJI, MEGUMI, NOBARA, GOJO) with self-identification protocols
- Enhanced `protocol.config.yaml` with canonical repository configuration

---

## [6.0.0] - 2025-11-05

### Added
- **Adaptive Workflow Complexity (Tier System)**: Three-tier system (Rapid/Standard/Critical)
- **NOBARA Agent**: Creative Strategy & UX Specialist (four-agent system)
- **Tier Selection Guide**: Comprehensive guide for choosing appropriate tier
- Desktop application wrapper support (Electron-based)

### Changed
- Major workflow overhaul with tier-based requirements
- Security reviews now tier-adaptive (Tier 2+)
- Testing requirements vary by tier

### Breaking Changes
- Workflow structure changed from fixed to adaptive
- All agents must now operate within tier-specific constraints

---

## [5.1.0] - 2025-11-01

### Added
- **CLAUDE.md Protection System**: Tier 2 protection with authorized editors only
- **Backup & Rollback Requirements**: Mandatory backups before destructive operations
- Enhanced safety enforcement mechanisms

### Changed
- Only USER and GOJO (with authorization) can modify CLAUDE.md
- All destructive operations require backup confirmation

---

## [5.0.0] - 2025-10-28

### Added
- **Mission Control (GOJO)**: Fourth agent for project lifecycle management
- **Passive Observation**: Background monitoring and intelligence gathering
- **Three-Tier Enforcement**: Isolation, backups, quality gates
- **Trigger 19**: Full intelligence report system

### Changed
- Expanded from three-agent to four-agent architecture
- Protocol guardian role established with special privileges

---

## [4.0.0] - 2025-10-20

### Added
- **Custom Trigger System**: User-defined triggers for protocol actions
- Configurable trigger keywords and responses

---

## [3.0.0] - 2025-10-15

### Added
- **Dual Workflow Implementation**: Support for parallel workflows
- Enhanced agent coordination mechanisms

---

## [2.0.0] - 2025-10-10

### Added
- **Three-Agent Architecture**: YUUJI (Implementation), MEGUMI (Security), and basic coordination

### Changed
- Expanded from single-agent to three-agent system

---

## [1.0.0] - 2025-10-01

### Added
- Initial single-agent system
- Basic protocol structure
- Core implementation workflows

---

## Version Numbering Scheme

**Format**: vMAJOR.MINOR.PATCH

- **MAJOR** (Breaking changes, system overhauls)
- **MINOR** (New features, backward-compatible enhancements)
- **PATCH** (Bug fixes, documentation updates, minor corrections)

---

**Canonical Source**: <https://github.com/DewyHRite/Domain-Zero-Protocol>
**Maintainer**: Protocol Guardians
**Last Updated**: 2025-11-08
