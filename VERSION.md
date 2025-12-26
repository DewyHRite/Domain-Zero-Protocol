<!-- [CORE FILE] - Domain Zero Protocol v8.10.0 -->
# Domain Zero Protocol - Version Information

**Version:** v8.10.0
**Release Date:** December 25, 2025
**Release Type:** Minor Release

---

## Release Summary

This release introduces **DZP Rules of Engagement (ROE)** - a post-compaction recovery system that restores full DZP protocol context with a single slash command (`/dzp-roe`). Solves the user pain point of repeatedly explaining protocol rules after context compaction.

### Key Changes in v8.10.0

- **Component 1: DZP ROE Skill** - 9-step workflow for post-compaction recovery: protocol summary, state tracking, validation, and task continuation prompting
- **Component 2: Slash Command** - `/dzp-roe` user-invocable command for instant DZP context restoration
- **Component 3: State Schema Update** - Added `compaction_recovery` tracking to project-state.json (recovery count, history, timestamps)
- **Component 4: Skill Registry Update** - SKILL_REGISTRY.md v3.0.0 and AGENT_SKILLS_MAP.yaml v4 with dzp-roe mapped to ALL 9 agents
- **Component 5: Task Continuation** - Skill prompts agents to resume previous work using proper DZP workflow patterns (implementation routing, parallel/sequential patterns)

### Previous Release (v8.9.0)

- **Component 1: Claude Skills Integration** - 16 Anthropic skills (pdf, docx, xlsx, pptx, frontend-design, web-artifacts-builder, webapp-testing, mcp-builder, skill-creator, brand-guidelines, canvas-design, doc-coauthoring, internal-comms, theme-factory, algorithmic-art, slack-gif-creator) mapped to all 9 agents
- **Component 2: Implementation Restrictions** - Nobara, Todo, Maki, Panda, Inumaki now route all code implementation through Yuuji; edit/bash tools removed from these agents
- **Component 3: File Rotation System** - scripts/file-rotate.py for dev-notes.md and security-review.md rotation at 25k character threshold
- **Component 4: OWASP Cheatsheet Integration** - Megumi updated with comprehensive OWASP Cheatsheet Series references (Tier 1/2/3 organization)
- **Updated Skill Registry** - SKILL_REGISTRY.md and AGENT_SKILLS_MAP.yaml v3 with complete skill mappings

### Previous Release (v8.8.0)

- **Component 1: Tier Validation System** - Active pwd verification, tier-defaults.yaml (18KB config), all 9 agents updated with tier validation sections, 30-day backward compatibility grace period
- **Component 2: Tier Statistics** - Automatic tier usage tracking, compliance monitoring, markdown/JSON reporting for Trigger 19 integration
- **Component 3: Dual Learning Systems** - Sukuna learns from protocol updates, Gojo learns from tier selections, comprehensive USER + PROJECT protection, opt-in by default
- **Comprehensive Safety** - Kill Switch integration, sanitized data, project isolation, confidence thresholds (80%+, 3+ samples), instant disable capability
- **Migration Guide** - 500+ line MIGRATION_v8.7_to_v8.8.md with step-by-step upgrade instructions

### Previous Release (v8.7.0)

- **Custom Agent Security Framework** - Pre-invocation validation (440 lines), runtime monitoring (650+ lines), audit logging, and registry system
- **8 Critical Vulnerabilities Fixed** - Agent name collision, self-declared tool permissions, YAML injection, agent self-modification, zero Gojo oversight, rate limiting, file immutability
- **Comprehensive Test Coverage** - 60+ test cases for session monitoring, 110+ tests total for security features
- **Agent Banner Compliance** - Fixed emoji consistency and added missing banner for Sukuna (protocol/AGENT_SELF_IDENTIFICATION_STANDARD.md compliance)

### Previous Release (v8.6.0)

- **Nine-Agent System** - Sukuna formalized as the 9th agent; all documentation updated from "eight-agent" to "nine-agent"
- **Full Documentation Update** - README, FAQ, PROTOCOL_QUICKSTART, VERSION, CLAUDE.md, gojo.agent.md all reflect 9-agent architecture
- **Distribution Update** - core-files-v8.5.1/ updated to core-files-v8.6.0/ standard

### Previous Release (v8.5.1)

- **Sukuna System Update Adversary** - Ryomen Sukuna integrated as adversarial-but-aligned system update specialist, invocable only via Gojo or User
- **Cross-Agent Edit Restrictions** - Non-Gojo agents now have READ-ONLY access to all `.agent.md` files; changes require User or Gojo authorization
- **JJK Character Reference** - Full Sukuna character reference added to `.protocol-state/jjk-character-reference/`
- **Slash Command Rename** - `/system-update` renamed to `/sukuna` with JJK character integration
- **Work Session Management** - Enhanced enforcement across all agents
- **Gojo Template Extraction** - Extracted OUTPUT TEMPLATES to `.protocol-state/gojo-templates/OUTPUT_TEMPLATES.md` (~9% size reduction)

### Previous Release (v8.5.0)

- **Kill Switch Protocol** - Emergency stop mechanism with immediate halt, checkpoint creation, and project protection
- **User Technical Level System** - Beginner/Intermediate/Expert modes that adapt agent communication style
- **Gojo Mission Control Option 4** - New "Resume from Emergency Stop" option for checkpoint recovery

### Previous Release (v8.4.1)

- **Agent File Cleanup** - Removed verbose Gojo Awareness sections for cleaner separation of concerns
- **JJK Character References** - Added character context sections to all 9 agent files
- **Research Mode Expansion** - Updated to support all 9 agents with role-specific research focus

---

## What's New in v8.4.1

### Changed

#### 1. **Agent File Cleanup**

Removed verbose "Gojo Awareness" sections from all non-Gojo agent files:
- `protocol/yuuji.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/megumi.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/nobara.agent.md` - Replaced with concise "Mission Control: Gojo" reference
- `protocol/todo.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/maki.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/panda.agent.md` - Added "Mission Control: Gojo" reference
- `protocol/inumaki.agent.md` - Added "Mission Control: Gojo" reference

#### 2. **JJK Character Reference Additions**

Added character context sections to all 9 agent files linking to:
- Canon series information (Jujutsu Kaisen)
- Character wiki references
- Cursed technique mappings to agent specializations
- Domain expansion parallels

#### 3. **Research Mode Expansion**

Updated `protocol/RESEARCH_MODE.md` to support all 9 agents:
- Added role-specific research focus for Extended Four agents
- Defined operational cadences per agent type
- Integrated staleness monitoring for all agents

#### 4. **Handoff Specification Updates**

Updated `protocol/HANDOFF_SPECIFICATION.md`:
- Changed example handoffs from `mission_control` to `gojo` for schema compliance
- Ensured all agent identifiers match JSON schema enum

---

## Files Modified

**Protocol Agent Files (8 files):**
- `protocol/gojo.agent.md` - JJK Character Reference added
- `protocol/yuuji.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/megumi.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/nobara.agent.md` - Gojo Awareness cleanup, JJK Character Reference added
- `protocol/todo.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/maki.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/panda.agent.md` - Mission Control reference, JJK Character Reference added
- `protocol/inumaki.agent.md` - Mission Control reference, JJK Character Reference added

**Core Protocol Files:**
- `protocol/CLAUDE.md` - Updated to 9-agent system, new invocations
- `protocol/gojo.agent.md` - Domain supervision for all 9 agents
- `protocol/yuuji.agent.md` - Version sync to 8.4.1
- `protocol/megumi.agent.md` - Version sync to 8.4.1
- `protocol/nobara.agent.md` - Version sync to 8.4.1

**Configuration:**
- `protocol.config.yaml` - Added 4 new agent configurations
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Extended with new agent skills

**State:**
- `.protocol-state/project-state.json` - Version 8.4.1

---

## Configuration

No new configuration required. All changes are backward compatible.

**New Agent Invocations:**
```bash
# Todo - Database & Backend
"Read protocol/todo.agent.md and design database schema for [feature]"

# Maki - Performance
"Read protocol/maki.agent.md and optimize [component/page]"

# Panda - Build & Integration
"Read protocol/panda.agent.md and configure CI/CD for [project]"

# Inumaki - API & Communication
"Read protocol/inumaki.agent.md and design API for [feature]"
```

---

## Upgrade Notes

### For Existing Users

**No Action Required:**
- All changes are backward compatible
- Existing four-agent workflows unchanged
- New agents are optional extensions

**Optional: Use Extended Agents:**
```bash
# Database design
"Read protocol/todo.agent.md and design schema for user management"

# Performance optimization
"Read protocol/maki.agent.md and run Lighthouse audit"

# CI/CD setup
"Read protocol/panda.agent.md and create GitHub Actions workflow"

# API design
"Read protocol/inumaki.agent.md and design REST API for orders"
```

### For New Users

1. Review `IMPLEMENTATION_GUIDE.md` for agent overview
2. Start with core four agents (Gojo, Yuuji, Megumi, Nobara)
3. Add extended agents as needed for specialized tasks

---

## Key Principles Established

1. **Nine-agent system** - Specialized expertise across all development domains
2. **Consistent format** - All agents use .agent.md with YAML frontmatter
3. **Domain supervision** - Gojo coordinates all agents with declarative handoffs
4. **Escape paths** - All agents have fallback patterns (never hang)
5. **Skill assignments** - Each agent has specialized skills in AGENT_SKILLS_MAP.yaml

---

## Breaking Changes

**None.** This is a backward-compatible patch release.

---

## Documentation

**Agent Files:**
- `protocol/todo.agent.md` - Database & Backend Specialist
- `protocol/maki.agent.md` - Performance Optimization Specialist
- `protocol/panda.agent.md` - Build & Integration Specialist
- `protocol/inumaki.agent.md` - API & Communication Specialist

**Updated Files:**
- `protocol/CLAUDE.md` - System overview with 9 agents
- `protocol/gojo.agent.md` - Domain supervision diagram

**Skills:**
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Agent-skill mapping

---

## Known Issues

**None identified.**

---

## Contributors

- Domain Zero Protocol Team
- Claude Code

---

**Previous Version:** v8.3.1 (Agent-Specific Escape Paths)
**Next Planned:** TBD (See roadmap in README.md)
