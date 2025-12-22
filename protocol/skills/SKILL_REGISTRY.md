<!-- [CORE FILE] - Domain Zero Protocol v8.9.0 -->
---
title: "Skill Registry"
version: "2.0.0"
protocol_version: "8.9.0"
last_updated: "2025-12-22"
status: "Production-Ready"
---

# Domain Zero Protocol - Skill Registry

**Version**: 2.0.0
**Protocol Version**: 8.9.0
**Last Updated**: 2025-12-22

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

---

## Skill Categories

### Meta Skills (Protocol Management)
| Skill | Description | Status |
|-------|-------------|--------|
| skill-builder | Create new skills with proper structure | Active |
| skill-creator | Anthropic skill for creating skills | Active |

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
