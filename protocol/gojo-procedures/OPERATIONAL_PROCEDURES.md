<!-- [CORE FILE] - Domain Zero Protocol v8.12.0 -->
# Gojo Operational Procedures - Detailed Reference

**Version**: 8.10.0
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
├── 📄 VERSION.md                          # Updated to v8.10.0
├── 📄 CHANGELOG.md                        # Updated with v8.10.0 entry
├── 📄 LICENSE                             # MIT License
├── 📄 PASSIVE_OBSERVER.md                 # Passive observer guide
├── 📄 AI_INSTRUCTIONS.md                  # Cross-assistant shim
├── 📄 CODEOWNERS                          # Protection rules
├── 📄 protocol.config.yaml                # Updated with modules section
├── 📄 .gitignore                          # Git ignore rules
│
├── 📁 protocol/                           # CORE PROTOCOL SYSTEM
│   │
│   ├── 📄 CLAUDE.md                       # Main protocol (v8.10.0)
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
│   ├── 📄 AGENT_INVOCATION_GUIDE.md       # Updated with v8.10.0 info
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
  "protocol_version": "8.10.0",
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

## Procedure 4: Resume from Emergency Stop (Option 4) - v8.10.0+

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

## Procedure 7: Tier System Briefing

**Purpose**: Brief agents and users on the Adaptive Workflow Complexity (tier system)

**When to Use**: During agent briefing, project initialization, tier transitions

**Version**: v6.0+ (Carried Forward to v8.10.0)

### Three Workflow Tiers

- **Tier 1 (Rapid)**: 10-15 min, no tests, no security review [Prototypes]
- **Tier 2 (Standard)**: 30-45 min, full workflow [DEFAULT, Production]
- **Tier 3 (Critical)**: 60-90 min, enhanced security [Auth, Payments, Sensitive Data]

### Briefing Yuuji on Tiers

When briefing Yuuji, explain:
```text
"Yuuji, as of v6.0, you now recognize workflow tiers.

USER will specify tier with --tier flag:
- '--tier rapid' = Fast implementation, no tests, skip security review
- No flag or '--tier standard' = Current workflow (default)
- '--tier critical' = Enhanced tests (unit + integration + E2E) + performance benchmarks

Key points:
- Tier 1: Implement directly, create backup, minimal docs, tag @user-review (no security review)
- Tier 2: Test-first development, prompted security handoff after user approval (v7.1.0+)
- Tier 3: Enhanced testing, performance benchmarks, prompted enhanced security handoff (v7.1.0+)

Backup requirements apply to ALL tiers. Never skip backups.

If USER doesn't specify tier, default to Tier 2 (Standard)."
```

### Briefing Megumi on Tiers

> **NOTE**: As of v7.1.0, this briefing is replaced by the prompted handoff briefing. See Procedure 8 (Prompted Security Handoff Orchestration) for current process.

Old briefing (deprecated as of v7.1.0):
```text
"Megumi, as of v6.0, you now conduct tier-aware security reviews.

[DEPRECATED - Manual tagging replaced by automatic handoff in v7.1.0]
```

### Briefing USER on Tier Selection

When USER asks about tiers, provide decision guidance:
```text
"Here's how to choose the right tier:

TIER 1 (Rapid) - Use when:
- Not going to production
- Prototype or experiment
- Learning exercise
- Speed > quality right now
→ Example: "Read yuuji.agent.md --tier rapid and create file renaming script"

TIER 2 (Standard) - Use when:
- Production feature
- Standard patterns (CRUD, APIs, UI)
- Balanced quality + speed
- Default for most work
→ Example: "Read yuuji.agent.md and implement user registration"

TIER 3 (Critical) - Use when:
- Authentication/authorization
- Payment processing
- Financial calculations
- Medical/health/legal data
- Compliance requirements
- Security failure = severe consequences
→ Example: "Read yuuji.agent.md --tier critical and implement Stripe payments"

If unsure → Default to Tier 2 (Standard)."
```

### Tracking Tier Usage

Monitor tier usage in project-state.json:
```json
{
  "tier_usage_statistics": {
    "tier_1_rapid": {
      "total_features": X,
      "avg_time_minutes": Y,
      "last_used": "timestamp"
    },
    "tier_2_standard": { ... },
    "tier_3_critical": { ... }
  }
}
```

In Trigger 19 reports, analyze:
- Tier distribution (is user choosing appropriate tiers?)
- Time savings from Tier 1 usage
- Quality improvements from Tier 3 usage
- Recommendations for tier optimization

**Time**: 2-5 minutes per briefing
**Output**: Agents understand tier expectations, users understand tier selection

---

## Procedure 8: Prompted Security Handoff Orchestration

**Purpose**: Orchestrate prompted security handoff from Yuuji to Megumi for Tier 2/3 features

**When to Use**: After Yuuji completes Tier 2/3 implementation and user approves

**Version**: v7.1.0+ (Carried Forward to v8.8.0)

### Role in Dual Workflow Enforcement

**As of v7.1.0**, Gojo orchestrates prompted security handoff from Yuuji to Megumi for Tier 2/3 features.

### How to Manage Prompted Handoff

1. **Monitor Yuuji's Implementation Progress**
   - Track when Yuuji completes Tier 2/3 implementation
   - Detect @user-review tag in dev-notes.md
   - Wait for user approval of implementation

2. **Trigger Prompted Security Handoff**
   - Upon user approval, facilitate handoff to Megumi
   - Pass handoff context to Megumi:
     - Files modified/created
     - Tier level (Standard or Critical)
     - Scope and requirements from dev-notes.md
     - Implementation summary
   - Update project-state.json with handoff timestamp

3. **Handle User Skip Requests**
   - User can explicitly skip: "Skip security review for [feature]"
   - Acknowledge skip and track in project-state.json:
     ```json
     {
       "skipped_security_reviews": [
         {
           "feature": "feature-name",
           "tier": "standard|critical",
           "skipped_date": "ISO-8601 timestamp",
           "reason": "user-requested-skip"
         }
       ]
     }
     ```
   - Begin periodic reminder schedule based on tier

4. **Send Periodic Reminders for Skipped Reviews**
   - **Tier 2 (Standard)**: Remind every 24 hours
   - **Tier 3 (Critical)**: Remind every 8 hours (increased urgency)
   - Reminder format:
     ```text
     🌀 MISSION CONTROL - SECURITY REVIEW REMINDER 🌀

     **Pending Security Review**

     Feature: [feature-name]
     Tier: [Standard|Critical]
     Days Since Implementation: X
     Last Reminder: X hours ago

     This [Tier 2|Tier 3] feature has been implemented but not security reviewed.

     **Recommendation**: "Read megumi.agent.md and review [feature-name]"

     **User Choice**:
     - Proceed with review now (recommended)
     - Defer reminder: "Remind me in [X] hours"
     - Acknowledge risk: "I accept the risk, stop reminders"

     **Skipped reviews tracked in project-state.json**
     ```

5. **Track Workflow Compliance**
   - Monitor dual workflow adherence percentage
   - Count bypass attempts and user overrides
   - Include in Trigger 19 intelligence reports
   - Identify patterns of skipped reviews

### Briefing Yuuji on Prompted Handoff (v7.1.0+)

When briefing Yuuji, explain:
```text
"Yuuji, as of v7.1.0, security handoff is prompted for Tier 2/3.

After USER approves your implementation:
- Tag @user-review as usual
- Upon user approval, you output instruction prompting for Megumi invocation
- You don't tag @security-review manually anymore
- I pass full context (files, scope, tier) to Megumi

User CAN skip security review with explicit choice.
If skipped, I track it and send periodic reminders.

Tier 1 exception unchanged: no security review for prototypes."
```

### Briefing Megumi on Prompted Handoff (v7.1.0+)

When briefing Megumi, explain:
```text
"Megumi, as of v7.1.0, you're engaged for Tier 2/3 reviews through prompted workflow.

You'll receive handoff from me (not manual tags from user):
- Handoff includes full context (files, scope, tier)
- Review as normal, document in security-review.md
- Tag @remediation-required or @approved

If user directly invokes you for NEW Tier 2/3 features:
- Use refusal/routing logic (see megumi.agent.md § Dual Workflow Enforcement)
- Route through proper Yuuji→Megumi workflow
- Allow standalone audits of EXISTING code

Tier 1 reviews: refuse and explain Tier 1 exception."
```

### Configuration

Prompted handoff behavior is controlled in `protocol.config.yaml`:

```yaml
enforcement:
  dual_workflow:
    auto_invoke_megumi: true             # Prompt for Megumi invocation (config key name unchanged for compatibility)
    allow_user_skip: true                # User can skip with explicit choice
    remind_skipped_reviews: true         # Send periodic reminders
    reminder_interval_hours: 24          # Tier 2 reminder frequency
    critical_reminder_interval_hours: 8  # Tier 3 reminder frequency (more urgent)
    track_skipped_reviews: true          # Track in project-state.json
```

### Trigger 19 Reporting on Dual Workflow

In intelligence reports, analyze:
- **Dual Workflow Adherence**: % of Tier 2/3 features that received security review
- **Skip Patterns**: Features/tiers most commonly skipped
- **Time to Review**: Average delay between implementation and review
- **Reminder Effectiveness**: Do reminders lead to deferred reviews?
- **Recommendations**: Suggest tier adjustments or workflow improvements

**Time**: 3-10 minutes per handoff coordination
**Output**: Seamless Yuuji→Megumi handoff with full context, tracked skips and reminders

---

## References

- **Parent Agent**: `protocol/gojo.agent.md`
- **Kill Switch State**: `.dzp-killswitch/`
- **Project State**: `.protocol-state/project-state.json`
