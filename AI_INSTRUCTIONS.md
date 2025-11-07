# AI Instructions - Domain Zero Protocol

**⚠️ This is a redirect file. The canonical protocol is maintained in `protocol/CLAUDE.md`.**

---

## For AI Assistants

**Primary Instructions**: Read [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

This project uses the **Domain Zero Protocol** - a four-agent AI development framework with security-first approach, creative strategy, and adaptive workflow complexity.

---

## Quick Start

**For Mission Control** (Project initialization, lifecycle management):
```
Read protocol/GOJO.md
```

**For Implementation** (Feature development):
```
Read protocol/YUUJI.md and [your task]
```

**For Security Review** (Vulnerability assessment):
```
Read protocol/MEGUMI.md and review [module/feature]
```

**For Creative Strategy & UX** (Product design, user experience):
```
Read protocol/NOBARA.md and [design/strategy task]
```

---

## Protocol Files

All protocol specifications are in the `protocol/` directory:

- **`protocol/CLAUDE.md`** ← **START HERE** (Main protocol specification)
- `protocol/GOJO.md` - Mission Control & Protocol Guardian
- `protocol/YUUJI.md` - Implementation Specialist
- `protocol/MEGUMI.md` - Security Analyst
- `protocol/NOBARA.md` - Creative Strategy & UX
- `protocol/TIER-SELECTION-GUIDE.md` - Quick reference for workflow tiers

---

## Why This Structure?

**CLAUDE.md is the canonical source of truth**:
- ✅ Single source of truth (no duplication)
- ✅ Version controlled and protected (via CODEOWNERS)
- ✅ Auditable change history (GOJO-UPDATES-PATCH.md)
- ✅ Works across all AI assistants

**This file exists for discoverability**:
- Many AI tools look for `AI_INSTRUCTIONS.md`, `AI.md`, or `.github/copilot-instructions.md`
- This shim ensures they find the Domain Zero Protocol
- No protocol logic duplicated here - just a pointer

---

## Integration with Existing Instructions

If you have existing project-specific instructions (e.g., `.github/copilot-instructions.md`, `CONTRIBUTING.md`), you can append a pointer to Domain Zero Protocol without replacing your current content:

```markdown
## Domain Zero Protocol

This project follows the Domain Zero Protocol for AI-assisted development.

**Primary entrypoint**: [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

For workflow guidance:
- Mission Control: `protocol/GOJO.md`
- Implementation: `protocol/YUUJI.md`
- Security Review: `protocol/MEGUMI.md`
- Creative Strategy & UX: `protocol/NOBARA.md`
```

**Automated updater**: See `scripts/update-instructions.ps1` (Windows) or `scripts/update-instructions.sh` (macOS/Linux) for safe, opt-in appending of protocol pointers to existing instruction files.

---

## Cross-Assistant Compatibility

This approach works with:
- **Claude** (Anthropic) - via this file or direct protocol file reading
- **GitHub Copilot** - via `.github/copilot-instructions.md` (append pointer)
- **Cursor** - via `.cursorrules` or this file (append pointer)
- **Cody** (Sourcegraph) - via this file
- **Tabnine** - via this file
- **Any AI assistant** that reads markdown instruction files

---

## Need Help?

**Read the main protocol**: [`protocol/CLAUDE.md`](protocol/CLAUDE.md)

**Quick reference**: [`protocol/TIER-SELECTION-GUIDE.md`](protocol/TIER-SELECTION-GUIDE.md)

**Setup guide**: [`README.md`](README.md)

---

**Version**: 6.2.1
**Last Updated**: 2025-11-06
**Canonical Source**: `protocol/CLAUDE.md` (always refer to this for authoritative protocol)
**Repository**: https://github.com/DewyHRite/Domain-Zero-Protocol
