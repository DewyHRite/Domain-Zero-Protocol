<!-- [CORE FILE] - Domain Zero Protocol v8.5.1 -->
# Domain Zero Protocol - Version Information

**Version:** v8.5.1
**Release Date:** December 1, 2025
**Release Type:** Patch Release

---

## Release Summary

This patch release formalizes the Sukuna System Update Adversary as a Gojo-invoked agent for protocol modifications, adds Cross-Agent Edit Restrictions for enhanced security, and improves Work Session Management enforcement.

### Key Changes in v8.5.1

- **Sukuna System Update Adversary** - Ryomen Sukuna integrated as adversarial-but-aligned system update specialist, invocable only via Gojo or User
- **Cross-Agent Edit Restrictions** - Non-Gojo agents now have READ-ONLY access to all `.agent.md` files; changes require User or Gojo authorization
- **JJK Character Reference** - Full Sukuna character reference added to `.protocol-state/jjk-character-reference/`
- **Slash Command Rename** - `/system-update` renamed to `/sukuna` with JJK character integration
- **Work Session Management** - Enhanced enforcement across all agents
- **Token Optimization via Modular Architecture** - Extracted shared protocol sections (~1,755 lines) into 7 reusable module files
- **Module Reference System** - All 8 agents now reference shared modules in `protocol/modules/` instead of duplicating content
- **Agent Token Reduction** - Reduced agent file sizes by ~40-60% while preserving all functionality
- **Standardized Protocol Behaviors** - Emergency Stop, User Level Adaptation, Mask Mode, Binding Oath, and more as single-source-of-truth modules

### Previous Release (v8.5.0)

- **Kill Switch Protocol** - Emergency stop mechanism with immediate halt, checkpoint creation, and project protection
- **User Technical Level System** - Beginner/Intermediate/Expert modes that adapt agent communication style
- **Gojo Mission Control Option 4** - New "Resume from Emergency Stop" option for checkpoint recovery

### Previous Release (v8.4.1)

- **Agent File Cleanup** - Removed verbose Gojo Awareness sections for cleaner separation of concerns
- **JJK Character References** - Added character context sections to all 8 agent files
- **Research Mode Expansion** - Updated to support all 8 agents with role-specific research focus

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

Added character context sections to all 8 agent files linking to:
- Canon series information (Jujutsu Kaisen)
- Character wiki references
- Cursed technique mappings to agent specializations
- Domain expansion parallels

#### 3. **Research Mode Expansion**

Updated `protocol/RESEARCH_MODE.md` to support all 8 agents:
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
- `protocol/CLAUDE.md` - Updated to 8-agent system, new invocations
- `protocol/gojo.agent.md` - Domain supervision for all 8 agents
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

1. **Eight-agent system** - Specialized expertise across all development domains
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
- `protocol/CLAUDE.md` - System overview with 8 agents
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
