<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->
---
title: "Skill Registry"
version: "3.2.2"
protocol_version: "9.12.1"
last_updated: "2026-07-18"
status: "Production-Ready"
---

# Domain Zero Protocol - Skill Registry

**Version**: 3.2.2
**Protocol Version**: 9.12.1
**Last Updated**: 2026-07-18

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

> **Accuracy note (`SEC-SKILLREG-001`, v9.11.0).** This table previously listed every entry as an
> invocable skill with `Code Execution: Yes (Python)`. **Ten of them had no skill document**, so
> `skill: "<name>"` resolved to nothing. Nine are in fact **script-backed** — the capability is real
> and directly invocable, but it is a script, not a skill. One had lost its script entirely. The
> **Backing** column below now states what actually implements each row; a row must never again
> assert a resolution path that does not exist. Verified by direct inspection 2026-07-28.

| Skill Name | Version | Owner | Risk Level | Code Execution | Backing | Last Review | Target Agents |
|------------|---------|-------|------------|----------------|---------|-------------|---------------|
| skill-builder | 1.0.0 | gojo | Low | No | skill doc `skill-builder.md` | 2025-11-22 | gojo |
| dzp-roe | 2.0.0 | gojo | Low | No | skill doc `dzp-roe.md` | 2025-12-28 | gojo |
| trigger19r | 1.0.0 | sukuna | Medium | No (gate script runs via hooks/publish, not the skill) | skill doc `trigger19r.md` + **script** `scripts/check_trigger19r_sanitization.py` | 2026-07-29 | sukuna |
| session | 2.4.1 | gojo | Medium | Yes (Python) | skill doc `session.md` | 2026-07-31 | gojo |
| session-check | 1.0.0 | gojo | Low | Yes (Python) | skill doc `session-check.md` | 2025-12-29 | gojo |
| ts | 1.0.0 | gojo | Medium | No | skill doc `ts.md` | 2025-12-28 | gojo |
| validate-protocol | 1.0.0 | gojo | Low | Yes (Python) | **script** `scripts/validate-protocol.py` | 2026-07-28 | gojo |
| verify-installation | 1.0.0 | gojo | Low | Yes (Python) | **script** `scripts/verify-installation.py` | 2026-07-28 | gojo |
| dependency-scanner | 1.0.0 | gojo | Medium | Yes (Python) | **script** `scripts/dependency-scanner.py` | 2026-07-28 | gojo |
| file-rotate | 1.0.0 | gojo | Medium | Yes (Python) | **script** `scripts/file-rotate.py` | 2026-07-28 | gojo |
| verify-auto-invoked | 1.0.0 | gojo | Low | Yes (Python) | **script** `scripts/verify-auto-invoked.py` | 2026-07-28 | gojo |
| validate-custom-agents | 1.0.0 | gojo | Medium | Yes (Python) | **script** `scripts/validate-custom-agents.py` | 2026-07-28 | gojo |
| ⚠️ verify-working-directory | 1.0.0 | gojo | Low | Yes (Python, imported module — no skill doc) | **script** `scripts/verify_working_directory.py` (live, shipped; see below) | 2026-08-03 | gojo (imported by tier-statistics.py, gojo-learn.py, sukuna-learn.py) |
| create-snapshot | 1.0.0 | gojo | Medium | Yes (Python) | **script** `.protocol-state/create-snapshot.py` | 2026-07-28 | gojo |
| restore-snapshot | 1.0.0 | gojo | High | Yes (Python) | **script** `.protocol-state/restore-snapshot.py` | 2026-07-28 | gojo |
| domain-record-rotate | 1.0.0 | gojo | Low | Yes (Python) | **script** `scripts/domain-record-rotate.py` | 2026-07-28 | gojo |
| ~~memory-path-validator~~ **DEPRECATED v9.11.0** | 1.0.0 | gojo | n/a | **No — not executed, not shipped** | 2026-07-28 | none |
| megumi-secid | 1.0.0 | megumi | Medium | Yes (Python, mediated — Megumi has no Bash; a bash-capable resident executes `secid.{sh,ps1}` on her behalf per D9) | skill doc `megumi-secid.md` + wrapper `scripts/secid.{sh,ps1}` + engine `scripts/idgov/engine.py` | 2026-08-03 | megumi (mediated via gojo/yuuji) |
| resident-mint | 1.0.0 | gojo/sukuna/yuuji | Medium | Yes (Python) | skill doc `resident-mint.md` + wrappers `scripts/residentid-{sukuna,gojo,yuuji}.{sh,ps1}` | 2026-08-03 | sukuna, gojo, yuuji |

> **✅ CORRECTED — `verify-working-directory` (`SEC-SKILLREG-001`, v9.11.0; re-verified 2026-08-03
> per CodeRabbit PR #115 finding #25, independently re-confirmed before applying — not taken on
> the finding's word alone).**
> This row previously claimed **"NO — implementation MISSING"** / **"none in live tree."** That
> claim was **false** and is retracted here: `scripts/verify_working_directory.py` exists in the
> live tree right now (not only in backup trees), is git-tracked, ships via
> `publish-manifest.yaml` `include_scripts` (line 53), and is actively imported by
> `tier-statistics.py`, `gojo-learn.py`, and `sukuna-learn.py` (re-verified 2026-08-03 via direct
> `ls`/`grep` on the live tree). The prior partial correction (2026-07-29, Sukuna Inc-3 review §7)
> fixed the "no script in the live tree" phrasing but left this paragraph's overall framing —
> "existed and was shipped, then disappeared," "restore from the backup tree" — standing, and that
> framing was **itself incorrect**: the implementation never disappeared from the live tree.
>
> **The only artifact that is actually missing is a skill DOC.** There has never been a
> `verify-working-directory.md` skill file that would let this be invoked directly as
> `skill: "verify-working-directory"` — the underlying script exists solely as an imported module
> used by the three scripts above, never as a standalone invocable skill.
>
> **Status: no restoration or deregistration action required.** The row above is corrected to
> reflect the live, shipped script and its three real importers. Writing a
> `verify-working-directory.md` skill doc, if direct invocation is ever wanted, remains an open,
> low-priority backlog item — a documentation gap, not an implementation gap.
>
> *Method note (retained):* the original 2026-07-28 finding was produced by corroborating a
> negative — a single `Test-Path` reported simple absence, the `UPSTREAM-003` rule (a negative
> result is not self-verifying) required a second method, and `find` located backup copies. That
> earlier check evidently stopped at the backup trees without re-checking the live tree itself;
> this correction closes that gap by checking the live tree directly.

> **Deprecation note — `memory-path-validator` (v9.11.0).** `scripts/memory_path_validator.py`
> declared itself `SECURITY CRITICAL` and this registry listed it as an active
> `Code Execution: Yes (Python)` skill, but it had **zero callers anywhere in the repo** and no
> code outside the module even referenced the `/memories/` path space it claimed to guard. It was
> shipping to consumers alongside documentation stating that path validation happened
> automatically. It never ran.
>
> Found by the rescoped orphan-control guard (`tests/test_security_module_orphan_guard.py`) as the
> fourth instance of a control documented-as-existing but not wired.
> **Replacement: none — no live consumer exists.** The module is de-shipped
> (removed from `publish-manifest.yaml`), the false claim in
> `docs/reference/MEMORY_TOOL_CONFIGURATION.md` is retracted, and the entry is retained here per
> the Deprecation rule in § Review Requirements rather than deleted, so the record survives.
> If Memory Tool path validation is wanted later, it must be re-introduced **with a live call site
> and a test asserting it is reached** — not merely present.

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
| trigger19r | Decision-provenance report, Sukuna-exclusive (Trigger 19-R) | Active |

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

### 3.2.2 (2025-12-29) - v8.12.0 post-implementation version sync
- Version-sync pass only. No skill was added, removed, re-owned or re-scoped.
- Entry reconstructed from git history (`6aade7f`, "fix(version-sync): Complete
  v8.12.0 post-implementation cleanup") during the v9.11.0 batch-3 remediation:
  the header field was bumped 3.2.1 -> 3.2.2 without a corresponding changelog
  entry, and stayed that way for seven months because no linter covered a bare
  `**Version**:` field. This was the SIXTH logged occurrence of that class and
  the first found by a machine -- `check_version_stamps.py` Type 13
  (VERSION-VS-CHANGELOG) now compares this header against this section.

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
