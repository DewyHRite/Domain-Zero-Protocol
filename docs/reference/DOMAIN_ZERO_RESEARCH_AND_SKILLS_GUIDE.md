<!-- [CORE FILE] - Domain Zero Protocol v9.9.7 -->
# Domain Zero – Research Mode & Claude Skills Integration Guide

Version: 1.0 (2025-11-22)

> **Historical note**: The alignment review in Section 2 below is a point-in-time snapshot
> captured against protocol v8.5.1 and is retained for historical reference. It does not
> describe the current protocol version (see the `[CORE FILE]` banner above and `CLAUDE.md`
> for the canonical current state). The Research Mode mechanics described in Section 1
> remain current.

Purpose: Implement a practical path to (a) activate and use Research Mode directories, (b) confirm agent-protocol alignment, (c) ensure reusability with other AI coding agents, and (d) integrate Claude Skills as a canonical capability layer. This guide consolidates findings and defines a clear action plan.

---

## 1) Research Folders: Why they exist and why they look unused

Observed directories:

- `.protocol-state/research/`
  - `gojo/`, `megumi/`, `nobara/`, `yuuji/` (present but currently empty)
  - `research-index.json` (exists)
  - `README.md` (explains the workflow and filenames)

Configuration check:

- `protocol.config.yaml → research.enabled: true`
- Output paths:
  - Aggregate index: `.protocol-state/research/research-index.json`
  - Per-agent dirs: `.protocol-state/research/{agent}`
  - Filenames: `{timestamp}.summary.md` (tracked), `{timestamp}.raw.log` (gitignored)

Conclusion: The folder structure is correctly scaffolded by the protocol, but no agent research sessions have been run yet in v8.5.1. Hence, the per-agent directories are empty. This is expected until you invoke Research Mode.

How to use (examples):

- Yuuji: `"Read yuuji.agent.md --research and investigate pytest fixture best practices"`
- Megumi: `"Read megumi.agent.md --research and investigate OWASP Top 10 2025 changes"`
- Nobara: `"Read nobara.agent.md --research and investigate WCAG 2.2 success criteria"`
- Gojo: `"Read gojo.agent.md --research and investigate protocol governance frameworks"`

Acceptance criteria for “in use”:

- Each agent directory contains timestamped `.summary.md` files.
- `research-index.json` tracks entries with agent, topics, sources, and confidence.
- Raw notes (`.raw.log`) remain gitignored as per privacy policy.

---

## 2) Protocol and Agents Alignment Review (v8.5.1)

Files reviewed: `protocol/CLAUDE.md`, `protocol/yuuji.agent.md`, `protocol/megumi.agent.md`, `protocol/gojo.agent.md`, `protocol/nobara.agent.md`, and `protocol.config.yaml`.

Findings:

- Versioning: All reviewed files declare or align to protocol v8.5.1.
- .agent.md frontmatter: Present with `target`, `name`, `description`, `argument-hint`, `model`, `tools`, and `handoffs`.
- Tool Access Matrix: Present in each agent file and consistent with role boundaries.
- CLAUDE.md protection: Acknowledged across agents as read-only; Gojo conditional-write only with USER authorization.
- Self-identification and Mask Mode: Present and configurable via `protocol.config.yaml`.
- Dual Workflow (Tier 2/3): Documented; Megumi reviews prompted after Yuuji implementation.

Result: Protocol and agents are aligned to v8.5.1, and ready for Research Mode + Skills integration without structural changes.

---

## 3) Reusability With Other AI Coding Agents/Sub-Agents

Design features that enable reuse:

- `.agent.md` format with YAML frontmatter → portable, declarative capabilities
- Environment targeting (`target: vscode|GitHub`) → predictable behavior per platform
- Tool Access Matrix → clear, enforceable permissions
- Declarative handoffs → simple inter-agent orchestration without tight coupling
- Mask Mode → optional theming decoupled from core behaviors

Recommendations for reuse:

- Keep CLAUDE.md as canonical behavioral contract; avoid duplicating logic in multiple instruction files.
- For non-Claude assistants, retain `.agent.md` and translate only tool bindings and invocation phrasing.
- Provide an adapter layer for tool names if an assistant uses different verbs or capabilities.
- When rebranding, toggle `mask_mode.enabled: false` and rely on `unmasked_names` to maintain neutrality.

---

## 4) Claude Skills – Canonical Reference and Integration

Authoritative references:

- Overview: https://claude.com/blog/skills
- Examples (canonical reference): https://github.com/anthropics/skills/tree/main

Key concepts:

- Skills are folders with a `SKILL.md` (YAML frontmatter + instructions) and optional resources/code.
- Composable and portable across Claude apps, Claude Code, and API.
- Efficient: Claude only loads relevant skills when needed.
- Can include executable code (requires Code Execution Tool) – treat as privileged content.

Installation notes (Claude Code):

```bash
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

Governance policy for Domain Zero:

- Treat `anthropics/skills` as the canonical upstream for reference patterns.
- Keep organization-specific skills in a separate private repo (e.g., `org/claude-skills`).
- Require code review for any skill that runs code (apply SAST/SCA per your security posture).
- Version skills explicitly; document allowed versions in a skills registry (see §6 Action Plan).

---

## 5) Agent ↔ Skills Mapping (initial assignment)

The list below maps example/reference skills to each agent role and proposes custom skills to author.

Notes:

- “Example skills” refer to folders under `anthropics/skills` (Development & Technical, Creative & Design, Enterprise & Communication, Document Skills).
- “Custom skills” are organization-specific skills to be authored under your private repo.

Yuuji (Implementation)

- Example skills: `webapp-testing` (Playwright), `mcp-server` (MCP server guidance), `artifacts-builder` (for artifact-based scaffolds)
- Document skills (when generating artifacts/specs): `docx`, `pptx`, `xlsx`, `pdf`
- Custom skills to create: `codegen-standards`, `tdd-checklist`, `async-patterns`, `testing-fixtures`

Megumi (Security & Performance)

- Example skills: `webapp-testing` (for e2e verification harnesses)
- Custom skills to create: `owasp-checklist`, `threat-modeling`, `jwt-audit`, `secrets-review`, `dependency-audit` (can be paired with MCP integrations for CVE databases)
  - **Note:** All security findings must be documented in `.protocol-state/security-review.md` using SEC-ID format (e.g., SEC-001) with P0/P1/P2/P3 severity levels and OWASP Top 10 category mappings.

Nobara (Creative Strategy & UX)

- Example skills: `brand-guidelines`, `theme-factory`, `canvas-design`, `slack-gif-creator` (for comms), document skills when producing UX decks (`pptx`, `pdf`)
- Custom skills to create: `ux-writing`, `a11y-review`, `onboarding-flows`, `design-system-glossary`

Gojo (Mission Control & Protocol Guardian)

- Example skills: `skill-creator` (meta), `template-skill`, `mcp-server` (for orchestration/integrations), `internal-comms` (status reports)
- Custom skills to create: `protocol-verify`, `release-briefing`, `version-audit`, `work-session-monitoring`

---

## 6) Action Plan (step-by-step)

### Phase A — Activate Research Mode cadence (initial setup)

1. Run one research session per agent using the prompts in §1.
2. Verify outputs: one `{timestamp}.summary.md` per agent folder; `research-index.json` updated.
3. Log topics and cadence in `research-index.json` (Yuuji/Megumi weekly; Nobara biweekly; Gojo monthly).

### Phase B — Establish Skills as a capability layer (after Phase A)

1. In Claude Code, install example/document skills (see commands above).
2. Create a private repo (e.g., `org/claude-skills`) and add a `SKILL_REGISTRY.md` capturing:
   - Skill name, description, version, owner, risk level (code/no-code), last review date, and target agents.
3. Author the first two custom skills:
   - `owasp-checklist` (Megumi): OWASP Top 10 structured review with SEC-ID mapping.
   - `tdd-checklist` (Yuuji): Pre-commit TDD prompts and acceptance criteria.
4. Reference upstream examples from `anthropics/skills` in each custom skill’s README.

### Phase C — Wire Research + Skills into daily flow (ongoing)

1. For Tier 2/3 features, attach recommended skills in Yuuji’s initial brief and Megumi’s review notes.
2. Include links to any produced `.summary.md` research in PR descriptions.
3. Gojo to include skills + research status in weekly “Trigger 19” intelligence report.

### Phase D — Governance & Security (continuous)

1. Treat all code-executing skills as privileged; review via SAST/SCA.
2. Pin skill revisions; track in `SKILL_REGISTRY.md` with owners and review intervals.
3. Rotate and retire skills that become stale or superseded by better patterns.

---

## Appendix

- Protocol configuration: `protocol.config.yaml` (see `research`, `self_identification`, `mask_mode`)
- Research mode spec: `protocol/RESEARCH_MODE.md`
- Agent files: `protocol/*.agent.md`
- Canonical Skills reference: `https://github.com/anthropics/skills`
- Skills overview (blog): `https://claude.com/blog/skills`

---

Changelog:

- 1.0 (2025-11-22): Initial guide, research activation, skills mapping, governance policies.
