<!-- [CORE FILE] - Domain Zero Protocol v9.11.0 -->
# Slash Commands

Ready-to-use slash command files for Claude Code CLI.

## Installation

Copy this folder's contents to your project's `.claude/commands/` directory:

```bash
# From your project root (where protocol/ is located)
mkdir -p .claude/commands
cp -r slash-commands/* .claude/commands/
```

## Available Commands

| Command | Agent | Description |
|---------|-------|-------------|
| `/gojo` | Gojo Satoru | Mission Control - Project planning and protocol enforcement |
| `/yuuji` | Yuuji Itadori | Implementation Specialist - Test-first development |
| `/megumi` | Megumi Fushiguro | Security Analyst - OWASP Top 10 reviews |
| `/nobara` | Nobara Kugisaki | Creative Strategy & UX - User experience design |
| `/todo` | Aoi Todo | Database Specialist - Schema design and migrations |
| `/maki` | Maki Zenin | Performance Specialist - Profiling and optimization |
| `/panda` | Panda | Build Specialist - CI/CD and Docker |
| `/inumaki` | Toge Inumaki | API Specialist - REST/GraphQL design |
| `/sukuna` | Ryomen Sukuna | System Update Adversary - Protocol updates via Gojo |

## Session & Utility Commands

| Command | Description |
|---------|-------------|
| `/session-start` | Start work session + activate DZP context (reads fresh handoff brief first if present) |
| `/session-status` | Display current session summary |
| `/session-update` | Core full sync: project documents + Cortex re-index + timestamp |
| `/session-break` / `/session-continue` | Record a break / resume after break |
| `/session-end` | End session (coordinator event; incremental Cortex re-index, detached) |
| `/session-transfer` | Update + end + durable handoff brief in one fail-closed event (v9.11.0) |
| `/session-check` | Auto-invoked session monitoring enforcement (4h/6h/8h alerts) |
| `/dzp-roe` | Restore agent context after compaction |
| `/brain` / `/input` | Query or update DZP Cortex semantic memory |
| `/ts-tier1`..`/ts-tier4`, `/ts-codered` | Tiered troubleshooting sessions |
| `/ts-status`, `/ts-escalate`, `/ts-complete`, `/ts-history` | Troubleshooting session management |
| `/sys-update` | System update framework entry |

## Usage

```bash
# Project planning
/gojo brief me on project status

# Implement a feature
/yuuji implement user authentication with tier 2

# Security review
/megumi review the authentication implementation

# UX design
/nobara design the login flow with accessibility

# Database design
/todo create schema for user management

# Performance audit
/maki analyze bundle size and suggest optimizations

# CI/CD setup
/panda configure GitHub Actions workflow

# API design
/inumaki design REST endpoints for user CRUD

# System update (via Gojo -> Sukuna)
/gojo engage sukuna to plan v8.7.0 upgrade
# (blocked) Do not invoke directly:
# /sukuna update protocol   # Must go through Gojo
```

## Notes

- These commands require the Domain Zero Protocol agents in `protocol/`
- Commands pass `$ARGUMENTS` to the agent for context
- Customize or add project-specific commands as needed
