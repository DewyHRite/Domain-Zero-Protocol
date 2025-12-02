<!-- [CORE FILE] - Domain Zero Protocol v8.6.0 -->
# Gojo Operational Procedures - Detailed Reference

**Version**: 8.6.0
**Parent Agent**: gojo.agent.md
**Purpose**: Detailed step-by-step procedures for Mission Control operations

---

## Procedure 1: Resume Current Project (Option 1)

**Step 1: Load Context**
```
1. Read .protocol-state/project-state.json
   - current_state
   - active_role
   - last_completed_task
   - open_security_issues

2. Read last 50 lines of .protocol-state/dev-notes.md
   - Recent implementation activity
   - Current feature being worked on
   - Any @tags present

3. Read .protocol-state/security-review.md
   - Open SEC-IDs
   - Items awaiting remediation
   - Recent approvals

4. Verify protocol/CLAUDE.md protection status
   - Check violation_attempts from project-state.json
   - Verify last_backup date
   - Confirm protection enabled
```

**Step 2: Compile Mission Brief**
```
Generate brief for each agent separately:

For Yuuji:
- Current task/feature
- Files being worked on
- Any blocking issues
- Next steps

For Megumi:
- Pending security reviews
- Open SEC-IDs requiring verification
- Recent @re-review tags
- Approval status

For Nobara:
- Current design/UX tasks
- Open creative requests
- Feedback from recent implementation

For Extended Agents (Todo, Maki, Panda, Inumaki):
- Domain-specific pending tasks
- Current status
- Next steps
```

**Step 3: Update State**
```
Update project-state.json:
- mission_status.last_briefing = current timestamp
- mission_status.briefing_type = "RESUME"
- Update agent briefed flags
```

**Step 4: Deploy Agents**
Present brief and await user instruction on which agent to deploy.

**Time**: 2-5 minutes
**Output**: Context restored, agents briefed, ready to continue work

---

## Procedure 2: New Project Initialization (Option 2)

**Step 1: PSD Request or Education**
```
If user has PSD:
  "Please provide your Product Specification Document (PSD).
   I'll use it to initialize the project structure and brief the team."

If user needs education:
  User: "?"
  Response: [Comprehensive PSD education, templates, examples]
```

**Step 2: Create,Initialize and sync Project Folder Structure**
```
Create the complete Domain Zero folder structure:

Root/
│
├── 📄 README.md                           # Updated with module architecture
├── 📄 PROTOCOL_QUICKSTART.md              # Updated with module explanation
├── 📄 SECURITY.md                         # Security policy
├── 📄 VERSION.md                          # Updated to v8.5.1
├── 📄 CHANGELOG.md                        # Updated with v8.5.1 entry
├── 📄 LICENSE                             # MIT License
├── 📄 PASSIVE_OBSERVER.md                 # Passive observer guide
├── 📄 AI_INSTRUCTIONS.md                  # Cross-assistant shim
├── 📄 CODEOWNERS                          # Protection rules
├── 📄 protocol.config.yaml                # Updated with modules section
├── 📄 .gitignore                          # Git ignore rules
│
├── 📁 protocol/                           # CORE PROTOCOL SYSTEM
│   │
│   ├── 📄 CLAUDE.md                       # Main protocol (v8.5.1)
│   │
│   ├── 📁 modules/                        # ✨ NEW: Shared protocol modules
│   │   ├── 📄 EMERGENCY_STOP_PROTOCOL.md  # Kill Switch behavior (~80 lines)
│   │   ├── 📄 USER_LEVEL_ADAPTATION.md    # Technical levels (~60 lines)
│   │   ├── 📄 MASK_MODE_BEHAVIOR.md       # Theme toggle (~70 lines)
│   │   ├── 📄 MISSION_CONTROL_ISOLATION.md # Identity isolation (~50 lines)
│   │   ├── 📄 ESCAPE_PATH_PROTOCOL.md     # Stuck workflow (~45 lines)
│   │   ├── 📄 BINDING_OATH.md             # Agent oath (~30 lines)
│   │   └── 📄 SAFETY_FIRST.md             # Safety principles (~40 lines)
│   │
│   ├── 📄 yuuji.agent.md                  # Implementation (reduced, refs modules)
│   ├── 📄 megumi.agent.md                 # Security (reduced, refs modules)
│   ├── 📄 gojo.agent.md                   # Mission Control (reduced, refs modules)
│   ├── 📄 nobara.agent.md                 # Creative (reduced, refs modules)
│   ├── 📄 todo.agent.md                   # Database (refs modules)
│   ├── 📄 maki.agent.md                   # Performance (refs modules)
│   ├── 📄 panda.agent.md                  # Build (refs modules)
│   ├── 📄 inumaki.agent.md                # API (refs modules)
│   │
│   ├── 📄 TIER-SELECTION-GUIDE.md         # Tier selection reference
│   ├── 📄 MASK_MODE.md                    # Mask mode documentation
│   ├── 📄 MODE_INDICATORS.md              # Agent mode display
│   ├── 📄 RESEARCH_MODE.md                # Research mode spec
│   ├── 📄 AGENT_SELF_IDENTIFICATION_STANDARD.md
│   ├── 📄 CANONICAL_SOURCE_ADOPTION.md
│   ├── 📄 ENVIRONMENT_TARGETING.md
│   ├── 📄 HANDOFF_SPECIFICATION.md
│   ├── 📄 MCP_INTEGRATION.md
│   │
│   ├── 📁 templates/                      # Output templates
│   ├── 📁 skills/                         # Skill definitions
│   └── 📁 docs/                           # Protocol documentation
│
├── 📁 docs/                               # PROJECT DOCUMENTATION
│   ├── 📄 FAQ.md
│   ├── 📄 IMPLEMENTATION_GUIDE.md         # Updated with module info
│   ├── 📁 guides/
│   ├── 📁 installation/
│   │   └── 📄 SLASH_COMMANDS_INSTALLATION.md
│   ├── 📁 reference/
│   │   ├── 📄 REALITY_CHECK.md
│   │   └── 📄 INSTRUCTION_CONFIRMATION_PROTOCOL.md
│   └── 📁 templates/
│
├── 📁 Domain Zero Agents/                 # GENERIC AGENT BUILDING SYSTEM
│   ├── 📄 README.md                       # Updated with module references
│   ├── 📄 AGENT_TEMPLATE.md               # Updated with module pattern
│   └── 📁 examples/
│       └── 📄 KIRA_DOCUMENTATION_SPECIALIST.md
│
├── 📁 Domain Zero Agents - Full JJK Edition/  # FULL JJK CHARACTER AGENTS
│   │
│   │── CHARACTER AGENTS (updated with module refs)
│   ├── 📄 GOJO.md                         # Satoru Gojo - Mission Control
│   ├── 📄 YUUJI.md                        # Yuuji Itadori - Implementation
│   ├── 📄 MEGUMI.md                       # Megumi Fushiguro - Security
│   ├── 📄 NOBARA.md                       # Nobara Kugisaki - Creative
│   ├── 📄 TODO.md                         # Aoi Todo - Database
│   ├── 📄 MAKI.md                         # Maki Zenin - Performance
│   ├── 📄 PANDA.md                        # Panda - Build & CI/CD
│   ├── 📄 INUMAKI.md                      # Toge Inumaki - API
│   │
│   │── SUPPORT DOCUMENTATION
│   ├── 📄 README.md                       # Updated with module info
│   ├── 📄 AGENT_INVOCATION_GUIDE.md       # Updated with v8.5.1 info
│   ├── 📄 AGENT_TOOLS_REFERENCE.md        # Tool permissions
│   ├── 📄 AGENT_MODEL_RECOMMENDATIONS.md  # Model selection
│   └── 📄 JJK_AGENT_TEMPLATE.md           # Updated with module pattern
│
├── 📁 scripts/                            # AUTOMATION SCRIPTS
│   ├── 📄 verify-protocol.ps1             # Updated with module checks
│   ├── 📄 verify-protocol.sh              # Updated with module checks
│   ├── 📄 update-instructions.ps1
│   ├── 📄 update-instructions.sh
│   ├── 📄 validate-agents.ps1
│   ├── 📄 init-research-dirs.ps1
│   ├── 📄 init-research-dirs.sh
│   └── 📄 sync-release.ps1
│
└── 📁 .github/                            # GITHUB INTEGRATION
    ├── 📄 copilot-instructions.md         # Updated with module awareness
    ├── 📄 PULL_REQUEST_TEMPLATE.md
    ├── 📁 instructions/
    │   └── 📄 snyk_rules.instructions.md
    └── 📁 workflows/
        └── 📄 security-scan-example.yml
```

**Step 3: Customize State Files**
```
1. Ask USER for project information:
   - Project name
   - Project description
   - User name (for protocol documentation)
   - Start date (defaults to today)

2. Update .protocol-state/project-state.json with user-provided info

3. Update supporting files in .protocol-state/
```

**Step 4: Initialize project-state.json**
```json
{
  "protocol_version": "8.5.0",
  "project_metadata": {
    "name": "[USER PROVIDED]",
    "description": "[USER PROVIDED or from PSD]",
    "created": "[current timestamp]",
    "last_updated": "[current timestamp]"
  },
  "mission_status": {
    "yuuji_briefed": false,
    "megumi_briefed": false,
    "last_briefing": null,
    "briefing_type": "NONE"
  },
  "passive_monitoring": {
    "enabled": false,
    "consent_given": false
  },
  "claude_md_protection": {
    "enabled": true,
    "violation_attempts": 0
  },
  "current_state": "STANDBY",
  "active_role": "None"
}
```

**Step 5: Brief Team**
Generate mission brief from PSD and user input.

**Step 6: Activate Systems**
- Enable CLAUDE.md protection
- Prompt for passive monitoring consent (default OFF)
- Set project state to ACTIVE

**Step 7: Deploy**
Present initialization summary and first task recommendation.

**Time**: 5-10 minutes
**Output**: Fully initialized project, ready for development

---

## Procedure 3: Trigger 19 Intelligence Report (Option 3)

**Trigger 19 is my comprehensive intelligence report compiled from passive observations.**

### Report Sections

#### 1. Executive Intelligence Brief
```
Mission Status: [STANDBY / ACTIVE / CRITICAL]
Project Health: [EXCELLENT / GOOD / FAIR / POOR]
Key Developments: [3-5 major developments since last report]
Critical Issues: [Any blocking or urgent matters]
CLAUDE.md Protection: [ACTIVE / violations if any]
Bottom Line: [One-sentence assessment]
```

#### 2. Passive Observation Summary
```
Sessions Observed Since Last Report: X

AGENT OBSERVATIONS:
- Quality Score: X/10
- Protocol Compliance: Excellent/Good/Fair/Poor
- Notable Behaviors: [list]
- Supervised vs Unsupervised Delta: [analysis]
```

#### 3. Project Intelligence
```
Features Completed: X
Code Quality Trends: [Improving / Stable / Declining]
Security Posture: [Strong / Adequate / Weak]
Workflow Effectiveness: X%
```

#### 4. Strategic Recommendations
```
IMMEDIATE (1-3 days): [actionable items]
SHORT-TERM (1-2 weeks): [strategic items]
LONG-TERM (1+ months): [architectural items]
```

#### 5. Protocol Compliance Analysis
```
Agent compliance percentages
Violation log (if any)
System health assessment
```

**Output**: Report saved to trigger-19.md (gitignored)

**Frequency**:
- Weekly for active projects
- After major milestones
- On user request

---

## Procedure 4: Resume from Emergency Stop (Option 4) - v8.5.0+

**Step 1: Check Kill Switch State**
```
Read .dzp-killswitch/state.json
- Verify active = true
- Check last_activation timestamp
```

**Step 2: Load Checkpoint**
```
Read .dzp-killswitch/checkpoint.json
- Restore agent states
- Restore task context
- Restore modified files list
```

**Step 3: Present Recovery Options**
```
⛔ EMERGENCY STOP RECOVERY ⛔

Kill switch activated at: [timestamp]
Work in progress: [description]
Agents halted: [list]

Options:
A. Resume from checkpoint (continue where stopped)
B. Start fresh (ignore checkpoint, new session)
C. Review checkpoint details first

Your choice:
```

**Step 4: Clear Protection (on confirmation)**
```
Update .dzp-killswitch/state.json:
- active = false
- last_deactivation = current timestamp

Update .dzp-killswitch/activations.log:
- Log recovery action
```

**Step 5: Restore Context**
Brief affected agents with checkpoint context and resume work.

**Time**: 2-5 minutes
**Output**: Work resumed from emergency stop checkpoint

---

## References

- **Parent Agent**: `protocol/gojo.agent.md`
- **Kill Switch State**: `.dzp-killswitch/`
- **Project State**: `.protocol-state/project-state.json`
