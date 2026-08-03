<!-- [CORE FILE] - Domain Zero Protocol v9.11.0 -->

# Sukuna System Update - Output Templates

**Version**: 8.7.0
**Last Updated**: 2025-12-03
**Purpose**: Centralized output templates for Sukuna System Update responses

---

## Template 1: System Update Interface

```markdown
╔══════════════════════════════════════════════════════════════╗
║         SYSTEM UPDATE v8.7.0 - MALEVOLENT SHRINE             ║
╠══════════════════════════════════════════════════════════════╣
║  👹 Sukuna - Adversarial Protocol Specialist                 ║
╠══════════════════════════════════════════════════════════════╣
║  [1] Plan Update      - Scope, risk, backup strategy         ║
║  [2] Execute Plan     - Apply approved changes               ║
║  [3] Risk Assessment  - Red-team analysis                    ║
║  [4] Rollback         - Restore from backup                  ║
╠══════════════════════════════════════════════════════════════╣
║  Access: Gojo-coordinated | User approval required           ║
╚══════════════════════════════════════════════════════════════╝

Select 1-4 or describe the update:
```

---

## Template 2: Update Plan Presentation

```markdown
╔══════════════════════════════════════════════════════════════╗
║                 SYSTEM UPDATE PLAN                           ║
╚══════════════════════════════════════════════════════════════╝

📋 UPDATE SCOPE: [description]
📊 RISK LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
🔄 VERSION: [current] → [target]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FILES AFFECTED:
├── CORE: [count] files
├── STATE: [count] files (merge strategy: [strategy])
└── CONFIG: [count] files

BACKUP PLAN:
└── Location: .protocol-state/backups/[timestamp]/
└── Manifest: backup-manifest.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXECUTION STEPS:
1. [Step with verification]
2. [Step with verification]
3. [Step with verification]

RISKS & MITIGATIONS:
- Risk: [description] → Mitigation: [action]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ USER APPROVAL REQUIRED
Reply "Approve" to execute, "Modify" to adjust, or "Cancel"
```

---

## Template 3: Risk Assessment Report

```markdown
╔══════════════════════════════════════════════════════════════╗
║              RED-TEAM RISK ASSESSMENT                        ║
╚══════════════════════════════════════════════════════════════╝

🎯 TARGET: [update/change description]
📊 OVERALL RISK: [LOW/MEDIUM/HIGH/CRITICAL]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RISK MATRIX:
| Category       | Risk   | Impact | Mitigation         |
|----------------|--------|--------|-------------------|
| Data Loss      | [L/M/H]| [desc] | [action]          |
| Breaking Change| [L/M/H]| [desc] | [action]          |
| Rollback       | [L/M/H]| [desc] | [action]          |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ADVERSARIAL FINDINGS:
[numbered list of potential issues]

RECOMMENDATION: [PROCEED/PROCEED WITH CAUTION/ABORT]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Template 4: Update Execution Summary

```markdown
╔══════════════════════════════════════════════════════════════╗
║              UPDATE EXECUTION COMPLETE                       ║
╚══════════════════════════════════════════════════════════════╝

✅ STATUS: [SUCCESS/PARTIAL/FAILED]
🔄 VERSION: [previous] → [current]
⏱️ DURATION: [time]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHANGES APPLIED:
├── Files modified: [count]
├── Files created: [count]
├── Files deleted: [count]
└── Backup: .protocol-state/backups/[timestamp]/

VERIFICATION:
[x] Backup created
[x] Changes applied
[x] Validation passed
[ ] [any pending items]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ROLLBACK: If issues occur, use Template 5 (Rollback Recovery)

Logged to: plan-documentation.md
```

---

## Template 5: Rollback Recovery Interface

```markdown
╔══════════════════════════════════════════════════════════════╗
║              ROLLBACK RECOVERY                               ║
╚══════════════════════════════════════════════════════════════╝

⚠️ ROLLBACK REQUESTED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AVAILABLE BACKUPS:
| Timestamp           | Version | Files | Status   |
|---------------------|---------|-------|----------|
| [ISO-8601]          | [ver]   | [n]   | [status] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ROLLBACK OPTIONS:

A. Full Rollback
   - Restore all files from backup
   - Revert version numbers

B. Partial Rollback
   - Select specific files to restore
   - Keep other changes

C. Cancel
   - Exit without changes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Select A, B, or C
```

---

**Usage**: Reference from sukuna.agent.md: `.protocol-state/sukuna-templates/OUTPUT_TEMPLATES.md`
