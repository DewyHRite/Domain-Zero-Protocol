# Domain Zero Protocol - Version Information

**Version:** v8.2.0
**Release Date:** November 18, 2025
**Release Type:** Minor Release

---

## Release Summary

This minor release **enhances Research Mode** to make it actively usable by all agents. Research Mode (specification added in v7.2.0) now includes complete invocation guidance, structured output templates, and staleness monitoring integrated with Mission Control. All four agents (Yuuji, Megumi, Nobara, Gojo) can now conduct domain-specific research to stay current with evolving standards and best practices.

### Key Changes

- **✅ Research Mode Invocation** - All agents can now be invoked with `--research` flag
- **✅ Agent-Specific Research Sections** - Complete research guidance added to all 4 agent files
- **✅ Structured Output Templates** - Standardized summary format with citations and confidence indicators
- **✅ Staleness Monitoring** - Gojo enforces research currency with configurable thresholds
- **✅ Directory Structure** - `.protocol-state/research/` created for all agents

---

## What's New in v8.2.0

### Added

#### 1. **Research Mode Enhancement** - Active agent research implementation

**Agent Research Focus Areas:**
- **Yuuji**: Implementation patterns, TDD tooling, test isolation, async patterns (Weekly)
- **Megumi**: OWASP updates, emerging vulnerabilities, cryptographic standards (Weekly)
- **Nobara**: WCAG guidelines, usability heuristics, onboarding flows (Biweekly)
- **Gojo**: Meta trends, coordination tooling, risk landscape, protocol governance (Monthly)

**Invocation Pattern:**
```bash
"Read [agent].agent.md --research and investigate [topic]"
```

**Example Invocations:**
```bash
"Read yuuji.agent.md --research and investigate pytest fixture best practices"
"Read megumi.agent.md --research and investigate OWASP Top 10 2025 changes"
"Read nobara.agent.md --research and investigate WCAG 2.2 success criteria"
"Read gojo.agent.md --research and investigate multi-agent orchestration patterns"
```

#### 2. **Research Output Structure** - Standardized summaries with citations

**Directory Structure:**
```
.protocol-state/research/
├── research-index.json       # Global index with last session timestamps
├── yuuji/
│   ├── 2025-11-18T14-30-00Z.summary.md
│   └── 2025-11-18T14-30-00Z.raw.log    (gitignored)
├── megumi/
│   ├── 2025-11-18T15-00-00Z.summary.md
│   └── 2025-11-18T15-00-00Z.raw.log    (gitignored)
├── nobara/
│   └── (research outputs)
└── gojo/
    └── (research outputs)
```

**Summary Template Features:**
- Focus questions (3-5 specific research questions)
- Key findings table with sources and confidence indicators
- Actionable recommendations (experiments, not mandates)
- Source citations with OWASP/WCAG/RFC mappings
- Privacy protection (raw notes gitignored)

#### 3. **Quality Gates** - Research validation requirements

**Source Requirements:**
- Minimum 3 primary sources (OWASP, NIST, W3C, RFC, peer-reviewed)
- High confidence findings require 2+ source corroboration
- Security items mapped to OWASP/CVE/NIST (Megumi only)
- WCAG criterion mapping (Nobara only)

**Confidence Levels:**
- **High**: Primary sources + corroborated by 2+ independent sources
- **Medium**: Reputable documentation/framework guides + some corroboration
- **Low**: Single source or unverified (flagged for further research)

#### 4. **Staleness Monitoring** - Gojo enforces research currency

**Thresholds:**
- Standard warning: 14+ days without research
- Critical escalation: 7+ days for security/auth/crypto topics (Megumi)
- Reminders issued in Mission Control interface

**Research Cadence:**
- Yuuji: Weekly (implementation knowledge evolves rapidly)
- Megumi: Weekly (security threats require constant monitoring)
- Nobara: Biweekly (UX/accessibility standards update less frequently)
- Gojo: Monthly (strategic trends are slower-moving)

#### 5. **Integration with Workflows** - Research informs implementation

**Research → Implementation Flow:**
1. Research findings documented in structured summary
2. User reviews recommendations and approves approach
3. Standard tier workflows apply (Tier 1/2/3)
4. Implementation uses current best practices from research

**Example:**
```
Research: "JWT rotation best practices have changed"
→ Summary recommends 30-minute refresh token rotation
→ User approves recommendation
→ "Read yuuji.agent.md --tier critical and implement JWT refresh rotation"
→ Standard Tier 3 workflow applies
```

### Changed

#### 1. **protocol/CLAUDE.md** - Added Mode 4: Research Mode

**Operational Modes Section:**
- Added comprehensive Research Mode overview
- Documented research focus by agent
- Included quality gates and staleness monitoring
- Added invocation examples for all agents

**Agent Invocation Patterns:**
- Added research mode examples for Yuuji, Megumi, Nobara, Gojo
- Included research flag usage patterns

#### 2. **All Agent Files** - Research mode sections added

**yuuji.agent.md** (protocol/yuuji.agent.md:1318-1462):
- Research focus (implementation patterns, TDD tooling)
- Invocation guidance and examples
- Output template and integration with implementation work

**megumi.agent.md** (protocol/megumi.agent.md:2043-2229):
- Research focus (OWASP, vulnerabilities, cryptography)
- Security-specific source prioritization
- CVE/NIST cross-reference requirements

**nobara.agent.md** (protocol/nobara.agent.md:561-739):
- Research focus (WCAG, usability heuristics)
- User-centered research prioritization
- WCAG criterion mapping

**gojo.agent.md** (protocol/gojo.agent.md:1952-2148):
- Research focus (meta trends, coordination, governance)
- Strategic intelligence synthesis
- Agent research monitoring responsibilities

### Updated

- **protocol.config.yaml**: Version 8.2.0, config_version 2.2
- **protocol/CLAUDE.md**: Version 8.2.0, research mode operational mode added
- **.protocol-state/project-state.json**: protocol_version 8.2.0
- **All 4 agent files**: Research mode sections (145-195 lines each)

---

## Files Modified

**Core Protocol:**
- `protocol.config.yaml` - Version updated to 8.2.0, config_version to 2.2
- `protocol/CLAUDE.md` - Version 8.2.0, Mode 4: Research Mode added
- `.protocol-state/project-state.json` - protocol_version updated to 8.2.0

**Agent Files:**
- `protocol/yuuji.agent.md` - Research mode section added (lines 1318-1462)
- `protocol/megumi.agent.md` - Research mode section added (lines 2043-2229)
- `protocol/nobara.agent.md` - Research mode section added (lines 561-739)
- `protocol/gojo.agent.md` - Research mode section added (lines 1952-2148)

**State Management:**
- `.protocol-state/research/` - Directory structure created
- `.protocol-state/research/research-index.json` - Initial index created
- `.gitignore` - Already configured for research raw.log exclusions (v7.2.0)

---

## Configuration

Research mode is controlled via `protocol.config.yaml`:

```yaml
research:
  enabled: true
  allowed_agents: ["yuuji", "megumi", "nobara", "gojo"]
  cadence:
    yuuji: "weekly"
    megumi: "weekly"
    nobara: "biweekly"
    gojo: "monthly"
  max_session_minutes: 25
  source_policy:
    max_sources: 12
    min_primary_sources: 3
  escalation:
    stale_days_warning: 14
    critical_domain_stale_days: 7
```

---

## Upgrade Notes

### For Existing Users

**No Action Required:**
- Research mode is optional (agents function normally without it)
- All changes are backward compatible
- Existing workflows unaffected

**Optional Enhancements:**
```bash
# Use research mode before critical implementations
"Read megumi.agent.md --research and investigate OWASP Top 10 2025 changes"
# Then implement with current knowledge
"Read yuuji.agent.md --tier critical and implement JWT authentication"
```

### For New Users

Research mode provides a structured way to keep agent knowledge current:
1. Enable research in `protocol.config.yaml` (enabled by default)
2. Invoke agents with `--research` flag when needed
3. Review research summaries in `.protocol-state/research/[agent]/`
4. Approve recommendations before implementation

---

## Breaking Changes

**None.** This is a backward-compatible minor release.

---

## Documentation

**Research Mode Specification:**
- `protocol/RESEARCH_MODE.md` - Complete specification (v7.2.0)
- `protocol/CLAUDE.md` - Mode 4: Research Mode overview
- All agent files - Research mode sections with invocation guidance

**Configuration:**
- `protocol.config.yaml` - Research settings under `research:` section

---

## Known Issues

**None identified.**

---

## Contributors

- Domain Zero Protocol Team
- 🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

**Previous Version:** v8.1.0 (Playwright E2E Testing Infrastructure)
**Next Planned:** TBD (See roadmap in README.md)
