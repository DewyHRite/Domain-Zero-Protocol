<!-- [CORE FILE] - Domain Zero Protocol v8.4.0 -->
# Domain Zero Protocol - Version Information

**Version:** v8.4.0
**Release Date:** November 25, 2025
**Release Type:** Minor Release

---

## Release Summary

This minor release expands Domain Zero Protocol from a **four-agent** to an **eight-agent** system by fully integrating the second-year specialists: Todo, Maki, Panda, and Inumaki. All new agents follow the `.agent.md` format with YAML frontmatter, tool access matrices, and declarative handoffs.

### Key Changes in v8.4.0

- **Full 8-Agent Integration** - Four new agents added to core protocol
- **Todo (Database & Backend)** - Schema design, migrations, query optimization
- **Maki (Performance)** - Lighthouse audits, bundle analysis, profiling
- **Panda (Build & Integration)** - CI/CD, GitHub Actions, Docker, multi-core modes
- **Inumaki (API & Communication)** - REST, GraphQL, WebSocket, OpenAPI
- **Gojo Domain Supervision** - Updated to supervise all 8 agents
- **CLAUDE.md** - Updated to reflect complete 8-agent system

### Previous Release (v8.3.1)

- **Agent-Specific Escape Paths** - Each agent now has tailored escape path patterns
- **Instruction Confirmation Protocol** - Verified implementation across all agents
- **Updated Agent Headers** - All agent files now reference v8.3.1

---

## What's New in v8.4.0

### Added

#### 1. **Four New Agent Files** - Second-year specialists

**Files Created:**
- `protocol/todo.agent.md` - Database & Backend Specialist (Boogie Woogie)
- `protocol/maki.agent.md` - Performance Optimization Specialist (Heavenly Restriction)
- `protocol/panda.agent.md` - Build & Integration Specialist (Multi-Core System)
- `protocol/inumaki.agent.md` - API & Communication Specialist (Cursed Speech)

**Each Agent Includes:**
- YAML frontmatter with 7 required fields
- Tool Access Matrix with permissions
- Declarative handoff definitions
- Role-specific escape path patterns
- JJK-themed domain banners and terminology

#### 2. **Extended Agent Roster**

| Agent | Role | Domain |
|-------|------|--------|
| **Core Four** | | |
| Gojo | Mission Control | Protocol Guardian, Supervision |
| Yuuji | Implementation Specialist | TDD, Feature Development |
| Megumi | Security Analyst | OWASP, Vulnerability Detection |
| Nobara | Creative Strategy & UX | Design, Accessibility |
| **Extended Four** | | |
| Todo | Database & Backend | Schema, Migrations, Queries |
| Maki | Performance | Lighthouse, Bundle Analysis |
| Panda | Build & Integration | CI/CD, Docker, GitHub Actions |
| Inumaki | API & Communication | REST, GraphQL, WebSocket |

#### 3. **Gojo Domain Supervision Update**

**New Handoff Triggers:**
- `@brief-database` → Todo
- `@brief-performance` → Maki
- `@brief-build` → Panda
- `@brief-api` → Inumaki

**Updated Domain Diagram:**
```
                    ┌─────────────────┐
                    │     GOJO        │
                    │ Mission Control │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │ YUUJI   │         │ MEGUMI  │         │ NOBARA  │
   │  Impl   │◄───────►│Security │◄───────►│Creative │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │  TODO   │         │  MAKI   │         │ INUMAKI │
   │Database │         │  Perf   │         │   API   │
   └─────────┘         └─────────┘         └─────────┘
                            │
                       ┌────┴────┐
                       │  PANDA  │
                       │  Build  │
                       └─────────┘
```

---

## Files Modified

**New Files Created:**
- `protocol/todo.agent.md` - Database & Backend Specialist (~310 lines)
- `protocol/maki.agent.md` - Performance Optimization Specialist (~320 lines)
- `protocol/panda.agent.md` - Build & Integration Specialist (~315 lines)
- `protocol/inumaki.agent.md` - API & Communication Specialist (~330 lines)

**Core Protocol Files:**
- `protocol/CLAUDE.md` - Updated to 8-agent system, new invocations
- `protocol/gojo.agent.md` - Domain supervision for all 8 agents
- `protocol/yuuji.agent.md` - Version sync to 8.4.0
- `protocol/megumi.agent.md` - Version sync to 8.4.0
- `protocol/nobara.agent.md` - Version sync to 8.4.0

**Configuration:**
- `protocol.config.yaml` - Added 4 new agent configurations
- `protocol/skills/AGENT_SKILLS_MAP.yaml` - Extended with new agent skills

**State:**
- `.protocol-state/project-state.json` - Version 8.4.0

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

**None.** This is a backward-compatible minor release.

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
