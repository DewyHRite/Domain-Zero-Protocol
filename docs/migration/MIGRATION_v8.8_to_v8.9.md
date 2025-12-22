# Migration Guide: v8.8.0 to v8.9.0

**Migration Date**: December 22, 2025
**From Version**: 8.8.0
**To Version**: 8.9.0
**Breaking Changes**: Yes (Tool Restrictions)
**Estimated Time**: 15-30 minutes

---

## Summary of Changes

### New Features
1. **Claude Skills Integration** - 16 Anthropic skills mapped to all 9 agents
2. **Implementation Restrictions** - 5 agents now route code through Yuuji
3. **File Rotation System** - Generalized rotation for dev-notes.md and security-review.md
4. **OWASP Cheatsheet Integration** - Megumi enhanced with security references

### Breaking Changes
- **Nobara, Todo, Maki, Panda, Inumaki** can no longer use `edit` or `bash` tools
- These agents must invoke Yuuji via `@implementation` handoff for code changes

---

## Pre-Migration Checklist

- [ ] Backup your current installation
- [ ] Review current agent workflows for edit/bash usage
- [ ] Ensure Python 3.8+ is available (for file-rotate.py)
- [ ] Note any custom modifications to agent files

---

## Migration Steps

### Step 1: Update Protocol Files

Replace all protocol files with v8.9.0 versions:

```bash
# From canonical source
git pull origin main

# Or manual replacement
# Copy all files from core-files-v8.9.0/ to your project
```

### Step 2: Verify Agent File Updates

All 9 agent files should now have:
- `protocol_version: "8.9.0"`
- `agent_file_version: "1.3.0"` (or higher)
- `skill` added to tools list
- Nobara, Todo, Maki, Panda, Inumaki: `edit` and `bash` removed

### Step 3: Update Skill Configuration

Verify these files are updated:
- `protocol/skills/AGENT_SKILLS_MAP.yaml` (v3)
- `protocol/skills/SKILL_REGISTRY.md` (v2.0.0)

### Step 4: Install File Rotation Script

The new `scripts/file-rotate.py` supports:
- dev-notes.md rotation at 25k characters
- security-review.md rotation at 25k characters

Test the script:
```bash
python scripts/file-rotate.py --list
python scripts/file-rotate.py --file dev-notes --check
```

### Step 5: Update Workflow for Restricted Agents

If you have existing workflows using Nobara, Todo, Maki, Panda, or Inumaki for code editing:

**Before (v8.8.0)**:
```
"Read protocol/nobara.agent.md and implement this design"
```

**After (v8.9.0)**:
```
"Read protocol/nobara.agent.md and design this feature, then invoke Yuuji for implementation"
```

Or use the handoff:
```
"Read protocol/nobara.agent.md and design [feature]"
# Nobara designs, then triggers @implementation handoff to Yuuji
```

---

## Affected Files

### Agent Files (9 files)
| File | Changes |
|------|---------|
| gojo.agent.md | Version bump, skill tool added |
| yuuji.agent.md | Version bump, skill tool added |
| megumi.agent.md | Version bump, skill tool added, OWASP section |
| nobara.agent.md | Version bump, skill tool, edit removed |
| todo.agent.md | Version bump, skill tool, edit/bash removed |
| maki.agent.md | Version bump, skill tool, edit/bash removed |
| panda.agent.md | Version bump, skill tool, edit/bash removed |
| inumaki.agent.md | Version bump, skill tool, edit/bash removed |
| sukuna.agent.md | Version bump, skill tool added |

### Configuration Files
| File | Changes |
|------|---------|
| protocol.config.yaml | Version 8.9.0 |
| AGENT_SKILLS_MAP.yaml | v3 with 16 Anthropic skills |
| SKILL_REGISTRY.md | v2.0.0 with skill tables |

### New Files
| File | Purpose |
|------|---------|
| scripts/file-rotate.py | Generalized file rotation |

### Documentation Updates
| File | Changes |
|------|---------|
| VERSION.md | 8.9.0 release notes |
| README.md | New feature highlights |
| CHANGELOG.md | 8.9.0 section |
| protocol/CLAUDE.md | Version bump, feature list |

---

## Rollback Procedure

If issues occur, rollback to v8.8.0:

1. Restore agent files from backup
2. Restore configuration files
3. Remove scripts/file-rotate.py
4. Verify protocol.config.yaml shows v8.8.0

---

## Post-Migration Verification

### 1. Version Check
```bash
grep "protocol_version" protocol/*.agent.md
# All should show 8.9.0
```

### 2. Tool Restriction Check
```bash
grep -A 15 "^tools:" protocol/nobara.agent.md
# Should NOT include edit
```

### 3. Skill Integration Check
```bash
grep "skill" protocol/skills/AGENT_SKILLS_MAP.yaml | head -20
# Should show anthropic_skills_index
```

### 4. File Rotation Check
```bash
python scripts/file-rotate.py --list
# Should show dev-notes and security-review as supported
```

---

## FAQ

### Q: Why were edit/bash removed from 5 agents?
Implementation restrictions ensure code quality by centralizing all code changes through Yuuji, who follows test-first development practices.

### Q: Can restricted agents still create files?
Yes. They retain the `write` tool for documentation, designs, and specifications. Only code editing/execution is restricted.

### Q: How do I use the new skills?
Invoke with `skill: "skill-name"` in your prompts. See AGENT_SKILLS_MAP.yaml for agent-specific skills.

### Q: What happens when dev-notes.md exceeds 25k characters?
Yuuji should notify Gojo to run `python scripts/file-rotate.py --file dev-notes --rotate`, which archives the current file and creates a fresh one with the header preserved.

---

## Support

For migration issues:
- Check [FAQ.md](../FAQ.md)
- Review [CHANGELOG.md](../../CHANGELOG.md)
- Open issue at: https://github.com/DewyHRite/Domain-Zero-Protocol/issues
