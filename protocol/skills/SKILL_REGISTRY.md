<!-- [CORE FILE] - Domain Zero Protocol v8.4.0 -->
---
title: "Skill Registry"
version: "1.0.0"
protocol_version: "8.4.0"
last_updated: "2025-11-24"
status: "Production-Ready"
---

# Domain Zero Protocol - Skill Registry

**Version**: 1.0.0
**Protocol Version**: 8.4.0
**Last Updated**: 2025-11-24

---

## Purpose

This registry tracks all skills available in the Domain Zero Protocol, their versions, owners, risk levels, and review status. Skills with `code_execution: true` require SAST/SCA review before deployment.

---

## Registry Format

| Skill Name | Version | Owner | Risk Level | Code Execution | Last Review | Target Agents |
|------------|---------|-------|------------|----------------|-------------|---------------|
| skill-builder | 1.0.0 | gojo | Low | No | 2025-11-22 | gojo |

---

## Skill Categories

### Meta Skills (Protocol Management)
| Skill | Description | Status |
|-------|-------------|--------|
| skill-builder | Create new skills with proper structure | Active |

### Implementation Skills (Yuuji)
| Skill | Description | Status |
|-------|-------------|--------|
| codegen-standards | Code generation standards and patterns | Planned |
| tdd-checklist | Test-driven development checklist | Planned |
| async-patterns | Async/await patterns and best practices | Planned |
| testing-fixtures | Test fixture patterns and setup | Planned |

### Security Skills (Megumi)
| Skill | Description | Status |
|-------|-------------|--------|
| owasp-checklist | OWASP Top 10 security review checklist | Planned |
| threat-modeling | Threat modeling templates and guides | Planned |
| jwt-audit | JWT implementation audit checklist | Planned |
| secrets-review | Secrets and credentials review | Planned |
| dependency-audit | Dependency vulnerability audit | Planned |

### Creative/UX Skills (Nobara)
| Skill | Description | Status |
|-------|-------------|--------|
| ux-writing | UX writing guidelines and patterns | Planned |
| a11y-review | Accessibility (WCAG 2.2) review checklist | Planned |
| onboarding-flows | User onboarding flow patterns | Planned |
| design-system-glossary | Design system terminology and patterns | Planned |

### Mission Control Skills (Gojo)
| Skill | Description | Status |
|-------|-------------|--------|
| protocol-verify | Protocol compliance verification | Planned |
| release-briefing | Release preparation checklist | Planned |
| version-audit | Version consistency audit | Planned |
| work-session-monitoring | Work session tracking and alerts | Planned |

---

## Governance

### Risk Levels

- **Low**: No code execution, documentation/checklist only
- **Medium**: Reads code but doesn't execute
- **High**: Executes code, requires SAST/SCA review

### Review Requirements

1. **All new skills**: Must be reviewed by Gojo before registration
2. **Code-executing skills**: Require SAST/SCA scan results
3. **Version updates**: Document changes in this registry
4. **Deprecation**: Mark as "Deprecated" with replacement note

### Adding a New Skill

1. Create skill file in `protocol/skills/[skill-name].md`
2. Add entry to `AGENT_SKILLS_MAP.yaml`
3. Register in this file with version, owner, and risk level
4. If code execution: provide SAST/SCA scan results
5. Update agent-specific mappings if applicable

---

## Changelog

### 1.0.0 (2025-11-22)
- Initial registry creation
- Added skill-builder as first registered skill
- Documented planned skills for all agents
