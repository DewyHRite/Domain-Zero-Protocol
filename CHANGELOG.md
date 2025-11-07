# Changelog - Domain Zero Protocol

All notable changes to the Domain Zero Protocol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  - Added "Work Session Alert Protocol (v6.2.2 Enhanced)"
  - Added "Enforcement Levels & User Choice" section
  - Added "How I Respond to User Choices" section with detailed workflows

### Fixed
- Version consistency across all protocol files (completed v6.2 update before v6.2.2)

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
**Last Updated**: 2025-11-06
