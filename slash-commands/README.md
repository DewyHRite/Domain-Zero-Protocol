<!-- [CORE FILE] - Domain Zero Protocol v9.8.2 -->
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
