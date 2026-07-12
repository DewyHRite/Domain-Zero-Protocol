<!-- [CORE FILE] - Domain Zero Protocol v9.9.6 -->
---
title: "Skill Registry"
version: "3.2.2"
protocol_version: "9.9.6"
last_updated: "2026-07-07"
status: "Production-Ready"
---

# Domain Zero Protocol - Skill Registry

**Version**: 3.2.2
**Protocol Version**: 9.9.6
**Last Updated**: 2026-07-07

---

## Purpose

This registry tracks all skills available in the Domain Zero Protocol, their versions, owners, risk levels, and review status. Skills with `code_execution: true` require SAST/SCA review before deployment.

---

## Anthropic Skills (Official)

These skills are from the official Anthropic repository: https://github.com/anthropics/skills

| Skill Name | Version | Risk Level | Code Execution | Target Agents |
|------------|---------|------------|----------------|---------------|
| pdf | 1.0.0 | Low | No | megumi, nobara, inumaki |
| docx | 1.0.0 | Low | No | nobara, inumaki, yuuji |
| xlsx | 1.0.0 | Low | No | todo, maki, panda |
| pptx | 1.0.0 | Low | No | nobara, gojo |
| frontend-design | 1.0.0 | Low | No | nobara |
| web-artifacts-builder | 1.0.0 | Medium | Yes | nobara, yuuji |
| webapp-testing | 1.0.0 | Medium | Yes | yuuji, megumi |
| mcp-builder | 1.0.0 | High | Yes | yuuji, panda |
| skill-creator | 1.0.0 | Medium | No | gojo, yuuji, sukuna |
| brand-guidelines | 1.0.0 | Low | No | nobara |
| canvas-design | 1.0.0 | Low | No | nobara |
| doc-coauthoring | 1.0.0 | Low | No | ALL |
| internal-comms | 1.0.0 | Low | No | gojo, inumaki |
| theme-factory | 1.0.0 | Low | No | nobara, maki |
| algorithmic-art | 1.0.0 | Low | No | nobara |
| slack-gif-creator | 1.0.0 | Low | No | nobara |

---

## Custom Skills Registry

| Skill Name | Version | Owner | Risk Level | Code Execution | Last Review | Target Agents |
|------------|---------|-------|------------|----------------|-------------|---------------|
| skill-builder | 1.0.0 | gojo | Low | No | 2025-11-22 | gojo |
| dzp-roe | 2.0.0 | gojo | Low | No | 2025-12-28 | gojo |
| session | 1.0.0 | gojo | Medium | Yes (Python) | 2025-12-28 | gojo |
| session-check | 1.0.0 | gojo | Low | Yes (Python) | 2025-12-29 | gojo |
| ts | 1.0.0 | gojo | Medium | No | 2025-12-28 | gojo |
| validate-protocol | 1.0.0 | gojo | Low | Yes (Python) | 2025-12-29 | gojo |
| verify-installation | 1.0.0 | gojo | Low | Yes (Python) | 2025-12-29 | gojo |
| dependency-scanner | 1.0.0 | gojo | Medium | Yes (Python) | 2025-12-29 | gojo |
| file-rotate | 1.0.0 | gojo | Medium | Yes (Python) | 2025-12-29 | gojo |
| verify-auto-invoked | 1.0.0 | gojo | Low | Yes (Python) | 2025-12-29 | gojo |
| validate-custom-agents | 1.0.0 | gojo | Medium | Yes (Python) | 2025-12-29 | gojo |
| verify-working-directory | 1.0.0 | gojo | Low | Yes (Python) | 2025-12-29 | gojo |
| create-snapshot | 1.0.0 | gojo | Medium | Yes (Python) | 2025-12-29 | gojo |
| restore-snapshot | 1.0.0 | gojo | High | Yes (Python) | 2025-12-29 | gojo |
| domain-record-rotate | 1.0.0 | gojo | Low | Yes (Python) | 2025-12-29 | gojo |
| memory-path-validator | 1.0.0 | gojo | Low | Yes (Python) | 2025-12-29 | gojo |

---

## Skill Categories

### Meta Skills (Protocol Management)
| Skill | Description | Status |
|-------|-------------|--------|
| skill-builder | Create new skills with proper structure | Active |
| skill-creator | Anthropic skill for creating skills | Active |
| dzp-roe | Post-compaction recovery: Reinforce DZP rules (Gojo) | Active |

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
| session | Unified session management (start/status/update/break/continue/end) | Active |
| session-check | AUTO-INVOKED: Session alert enforcement (PATCH-SESSION-003) | Active |
| ts | Troubleshooting tier system (tier1-4/codered/status/history/escalate/complete) | Active |
| protocol-verify | Protocol compliance verification | Planned |
| release-briefing | Release preparation checklist | Planned |
| version-audit | Version consistency audit | Planned |

### Database & Backend Skills (Todo)

| Skill | Description | Status |
|-------|-------------|--------|
| schema-design | Database schema design patterns | Planned |
| migration-templates | Database migration templates | Planned |
| query-optimization | Query optimization checklist | Planned |
| orm-patterns | ORM configuration and patterns | Planned |

### Performance Skills (Maki)

| Skill | Description | Status |
|-------|-------------|--------|
| lighthouse-audit | Lighthouse performance audit guide | Planned |
| bundle-analysis | Bundle size analysis and optimization | Planned |
| performance-profiling | Performance profiling techniques | Planned |
| code-optimization | Code optimization patterns | Planned |

### Build & Integration Skills (Panda)

| Skill | Description | Status |
|-------|-------------|--------|
| ci-cd-templates | CI/CD pipeline templates | Planned |
| build-optimization | Build system optimization | Planned |
| docker-patterns | Docker and containerization patterns | Planned |
| deployment-checklist | Deployment verification checklist | Planned |

### API & Communication Skills (Inumaki)

| Skill | Description | Status |
|-------|-------------|--------|
| rest-design | REST API design patterns | Planned |
| graphql-schemas | GraphQL schema design | Planned |
| websocket-patterns | WebSocket implementation patterns | Planned |
| api-documentation | API documentation templates | Planned |

### System Update Skills (Sukuna)

| Skill | Description | Status |
|-------|-------------|--------|
| adversarial-review | Challenge and stress-test protocol changes | Active |
| update-validation | Validate system updates before deployment | Active |
| protocol-stress-test | Test protocol under adversarial conditions | Active |

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

### 3.2.1 (2025-12-29) - PATCH-SESSION-003
- **NEW**: **session-check** skill (Auto-Invoked Session Alert Enforcement) - Gojo-owned
- **Purpose**: Prevents recurrence of 46-hour session without alerts incident
- **Auto-Invoked**: YES (on EVERY Gojo Mission Control activation)
- **Remediation**: Enforces check-and-record + record-choice workflow
- Version bump: 3.2.0 → 3.2.1

### 3.2.0 (2025-12-28) - v8.11.0 Release
- **NEW**: **session** skill (Session Management) - Unified interface for work session tracking (Gojo-owned)
- **NEW**: **ts** skill (Troubleshooting Tier System) - 5-tier hybrid bug resolution (Gojo-owned)
- **UPDATED**: **dzp-roe** 1.0.0 → 2.0.0 - 50% size reduction, parallel workflow enforcement, Gojo-owned
- Updated protocol version to 8.11.0
- Added session and ts skills to Mission Control Skills category
- Changed dzp-roe owner from ALL agents → Gojo (domain.record.md write access)
- ts commands: tier1-4, codered, status, history, escalate, complete
- Hybrid escalation with context-dependent support agent selection
- Version bump: 3.0.0 → 3.2.0

### 3.0.0 (2025-12-25)
- Added **dzp-roe** skill (DZP Rules of Engagement) for post-compaction recovery
- Skill available to ALL agents for context restoration after compaction
- Updated protocol version to 8.10.0
- Added Meta Skills category entry for dzp-roe

### 2.0.0 (2025-12-22)
- Integrated 16 Anthropic official skills from GitHub repository
- Added Sukuna skills section (adversarial-review, update-validation, protocol-stress-test)
- Updated protocol version to 8.9.0
- Added Anthropic Skills table with all 16 skills mapped to agents
- Added skill-creator as active skill for gojo, yuuji, sukuna

### 1.0.0 (2025-11-22)
- Initial registry creation
- Added skill-builder as first registered skill
- Documented planned skills for all agents
