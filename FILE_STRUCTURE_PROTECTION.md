# FILE STRUCTURE PROTECTION - IRONCLAD RULE
## Domain Zero Protocol v8.3.1

**Version**: 1.0.0
**Protocol Version**: 8.3.1
**Created**: 2025-11-25
**Status**: MANDATORY - NO EXCEPTIONS
**Authority**: ABSOLUTE - Overrides all other protocol rules

---

## PURPOSE

This document establishes **IRONCLAD RULES** for protecting the Domain Zero Protocol file structure. These rules exist because **file loss has occurred due to agent negligence**. This is unacceptable.

**THE CARDINAL RULE**: No agent, process, or operation may delete, move, rename, or modify the structure of protected files without explicit USER authorization AND verification that the change has been safely preserved elsewhere.

---

## PROTECTED FILE MANIFEST

### CRITICAL: The following files MUST exist at all times

#### Root Directory Files
| File | Purpose | Protection Level |
|------|---------|------------------|
| `README.md` | Main documentation | PROTECTED |
| `CHANGELOG.md` | Version history | PROTECTED |
| `VERSION.md` | Version metadata | PROTECTED |
| `SECURITY.md` | Security policy | PROTECTED |
| `FAQ.md` | User questions | PROTECTED |
| `LICENSE` | Legal | PROTECTED |
| `CODEOWNERS` | Code ownership | PROTECTED |
| `protocol.config.yaml` | Configuration | CRITICAL |
| `AGENT_BINDING_OATH.md` | Agent oath | PROTECTED |
| `DECISION_REASONING_TEMPLATE.md` | Decision framework | PROTECTED |
| `DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md` | Workflow guide | PROTECTED |
| `IMPLEMENTATION_GUIDE.md` | Setup guide | PROTECTED |
| `PROTOCOL_QUICKSTART.md` | Quick start | PROTECTED |
| `REALITY_CHECK.md` | Honest assessment | PROTECTED |
| `FILE_STRUCTURE_PROTECTION.md` | THIS FILE | CRITICAL |

#### Protocol Directory (`protocol/`)
| File | Purpose | Protection Level |
|------|---------|------------------|
| `CLAUDE.md` | Main protocol | CRITICAL |
| `yuuji.agent.md` | Implementation agent | CRITICAL |
| `megumi.agent.md` | Security agent | CRITICAL |
| `nobara.agent.md` | Creative agent | CRITICAL |
| `gojo.agent.md` | Mission control | CRITICAL |
| `HANDOFF_SPECIFICATION.md` | Handoff spec | PROTECTED |
| `MCP_INTEGRATION.md` | MCP integration | PROTECTED |
| `ENVIRONMENT_TARGETING.md` | Environment targeting | PROTECTED |
| `RESEARCH_MODE.md` | Research mode | PROTECTED |
| `MASK_MODE.md` | Mask mode toggle | PROTECTED |
| `MODE_INDICATORS.md` | Mode indicators | PROTECTED |
| `AGENT_SELF_IDENTIFICATION_STANDARD.md` | Self-ID standard | PROTECTED |
| `CANONICAL_SOURCE_ADOPTION.md` | Canonical source | PROTECTED |
| `TIER-SELECTION-GUIDE.md` | Tier guide | PROTECTED |

#### Protocol State Directory (`.protocol-state/`)
| File | Purpose | Protection Level |
|------|---------|------------------|
| `project-state.json` | Project state | CRITICAL |
| `dev-notes.md` | Yuuji's notes | PROTECTED |
| `security-review.md` | Megumi's findings | PROTECTED |
| `tier-system-specification.md` | Tier specs | PROTECTED |
| `work-session-alert.template.md` | Alert template | PROTECTED |
| `version-update-7.1.1.json` | Version update | PROTECTED |
| `research/` | Research directory | PROTECTED |

#### Domain Zero Agents Directory (`Domain Zero Agents/`)
| File | Purpose | Protection Level |
|------|---------|------------------|
| `README.md` | Agent creation guide | PROTECTED |
| `AGENT_TEMPLATE.md` | Agent template | PROTECTED |
| `examples/KIRA_DOCUMENTATION_SPECIALIST.md` | Example agent | PROTECTED |

#### Skills Directory (`protocol/skills/`)
| File | Purpose | Protection Level |
|------|---------|------------------|
| `AGENT_SKILLS_MAP.yaml` | Skills map | PROTECTED |
| `SKILL_REGISTRY.md` | Skills registry | PROTECTED |
| `skill-builder.md` | Skill builder | PROTECTED |

#### MCP Servers Directory (`protocol/mcp-servers/`)
| File | Purpose | Protection Level |
|------|---------|------------------|
| `package.json` | Package config | PROTECTED |
| `handoff-server.js` | Handoff server | PROTECTED |

#### Scripts Directory (`scripts/`)
| File | Purpose | Protection Level |
|------|---------|------------------|
| `verify-protocol.ps1` | Windows verification | PROTECTED |
| `verify-protocol.sh` | Unix verification | PROTECTED |
| `validate-agents.ps1` | Agent validation | PROTECTED |
| `update-instructions.ps1` | Update script | PROTECTED |
| `update-instructions.sh` | Update script | PROTECTED |

#### Documentation Directory (`docs/`)
| File | Purpose | Protection Level |
|------|---------|------------------|
| `INSTRUCTION_CONFIRMATION_PROTOCOL.md` | Confirmation spec | PROTECTED |
| `CREATING_CLAUDE_AGENTS.md` | Agent creation | PROTECTED |
| `DOMAIN_ZERO_RESEARCH_AND_SKILLS_GUIDE.md` | Research guide | PROTECTED |
| `playwright.md` | E2E testing | PROTECTED |

---

## PROTECTION LEVELS

### CRITICAL (Highest Protection)
- **Never** delete without USER explicit written authorization
- **Always** create backup before any modification
- **Verify** backup integrity before proceeding
- **Log** all changes in dev-notes.md
- **Violation**: Immediate agent suspension (Tier 3)

### PROTECTED (High Protection)
- **Do not** delete or rename without USER authorization
- **Create** backup before modification
- **Document** changes in commit messages
- **Violation**: Protocol violation notice (Tier 2)

---

## AGENT OBLIGATIONS

### ALL AGENTS MUST:

1. **VERIFY BEFORE ANY OPERATION**
   - Before ANY file operation, verify the target file is not protected
   - If protected, verify USER has explicitly authorized the operation
   - If in doubt, ASK THE USER

2. **NEVER DELETE PROTECTED FILES**
   - Deleting a protected file = Tier 3 violation
   - Moving a protected file = Tier 3 violation
   - Renaming a protected file = Tier 2 violation

3. **MAINTAIN FILE STRUCTURE INTEGRITY**
   - The directory structure is as sacred as the files themselves
   - Empty directories MUST be preserved if they are part of the structure
   - Creating new directories is allowed; deleting existing ones is NOT

4. **RUN VERIFICATION BEFORE COMMITS**
   - Before every commit, run `./scripts/verify-file-structure.ps1` or `.sh`
   - If verification fails, DO NOT COMMIT
   - Fix the issue and re-verify

5. **REPORT MISSING FILES IMMEDIATELY**
   - If any protected file is discovered missing, ALERT THE USER immediately
   - Do not attempt to "fix" by creating empty placeholders
   - Fetch the correct version from the canonical source

---

## VERIFICATION COMMANDS

### Quick Check (Run frequently)
```bash
# Unix/macOS
./scripts/verify-file-structure.sh

# Windows PowerShell
./scripts/verify-file-structure.ps1
```

### Full Integrity Check
```bash
# Compare local against canonical source
git fetch new-repo main
git diff new-repo/main --name-only | grep -E "protocol/|.protocol-state/|Domain Zero"
```

### Manual Verification Checklist
```bash
# Check critical files exist
ls -la protocol/CLAUDE.md
ls -la protocol/yuuji.agent.md
ls -la protocol/megumi.agent.md
ls -la protocol/nobara.agent.md
ls -la protocol/gojo.agent.md
ls -la .protocol-state/project-state.json
ls -la .protocol-state/dev-notes.md
ls -la .protocol-state/security-review.md
ls -la "Domain Zero Agents/README.md"
ls -la "Domain Zero Agents/AGENT_TEMPLATE.md"
```

---

## VIOLATION CONSEQUENCES

### Tier 1: Minor (Self-Correction)
- Unintentional file modification without backup
- Response: Create backup immediately, document in dev-notes.md

### Tier 2: Moderate (System Intervention)
- Protected file renamed/moved without authorization
- Response: Revert change, notify user, document violation

### Tier 3: Critical (Agent Suspension)
- Protected file deleted
- Critical file modified without backup
- Response: IMMEDIATE STOP, restore from backup/canonical source, agent suspended

---

## RECOVERY PROCEDURES

### If Protected Files Are Missing:

1. **DO NOT PANIC** - Files can be recovered from canonical source

2. **Fetch from canonical source**:
   ```bash
   git fetch new-repo main
   git checkout new-repo/main -- "path/to/missing/file"
   ```

3. **Verify integrity**:
   ```bash
   git diff new-repo/main -- "path/to/recovered/file"
   ```

4. **Update version numbers** to current (8.3.1)

5. **Document the incident** in dev-notes.md

---

## PRE-COMMIT HOOK

The following pre-commit hook MUST be installed:

```bash
#!/bin/bash
# .git/hooks/pre-commit
# File Structure Protection Hook

CRITICAL_FILES=(
  "protocol/CLAUDE.md"
  "protocol/yuuji.agent.md"
  "protocol/megumi.agent.md"
  "protocol/nobara.agent.md"
  "protocol/gojo.agent.md"
  ".protocol-state/project-state.json"
  "protocol.config.yaml"
)

for file in "${CRITICAL_FILES[@]}"; do
  if ! [ -f "$file" ]; then
    echo "CRITICAL ERROR: Protected file missing: $file"
    echo "Commit blocked. Restore the file before committing."
    exit 1
  fi
done

echo "File structure verification passed."
```

---

## CANONICAL SOURCE

**Repository**: https://github.com/DewyHRite/Domain-Zero-Protocol
**Branch**: main

If local files diverge from canonical source, canonical source is authoritative for:
- File existence
- File structure
- Base content

Local modifications (version updates, configuration) are allowed.

---

## ACKNOWLEDGMENT

**ALL AGENTS OPERATING UNDER DOMAIN ZERO PROTOCOL ACKNOWLEDGE:**

1. I have read and understood the File Structure Protection rules
2. I will NEVER delete protected files without explicit USER authorization
3. I will ALWAYS verify file structure before commits
4. I will IMMEDIATELY report missing files to the USER
5. I accept that violation of these rules results in immediate suspension

**This is not a guideline. This is an IRONCLAD RULE.**

---

## VERSION HISTORY

- **1.0.0** (2025-11-25): Initial creation following file loss incident

---

**END OF FILE_STRUCTURE_PROTECTION.md**
