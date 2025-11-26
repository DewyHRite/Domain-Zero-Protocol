<!-- [CORE FILE] - Domain Zero Protocol v8.5.0 -->
# Gojo Operational Procedures - Detailed Reference

**Version**: 8.5.0
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

**Step 2: Create Project Folder Structure**
```
Create the complete Domain Zero folder structure:

Root/
├── protocol/                    # Core protocol system
│   ├── CLAUDE.md               # Main protocol
│   ├── yuuji.agent.md          # Implementation agent
│   ├── megumi.agent.md         # Security agent
│   ├── nobara.agent.md         # Creative strategy agent
│   ├── gojo.agent.md           # Mission Control
│   └── [extended agents]       # Todo, Maki, Panda, Inumaki
│
├── .protocol-state/             # State management (hidden)
│   ├── project-state.json       # Initialize with defaults
│   ├── dev-notes.md             # Create empty
│   ├── security-review.md       # Create empty
│   └── trigger-19.md            # Create empty, mark private
│
├── src/                         # User's source code
├── tests/                       # User's tests
└── README.md                    # Project README
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
