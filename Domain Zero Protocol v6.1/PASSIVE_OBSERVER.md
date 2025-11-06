# Passive Observer Mode - Gojo's Background Monitoring

## Understanding Gojo's Passive Observer Capability and When to Enable It

---

## What is Passive Observer Mode?

Passive Observer is Gojo's background monitoring system that continuously watches your development sessions and provides:
- Silent enforcement of protocol rules
- Proactive safety nudges
- Session continuity tracking
- Risk detection and auto-escalation
- Intelligence gathering for Trigger 19 reports

**Default Status**: **OFF** (disabled by default for privacy and consent)

---

## When Passive Observer is OFF (Default)

### ❌ Effects on Protocol

#### 1. No Background Enforcement
- **No silent isolation checks**: Yuuji/Megumi/Nobara can accidentally violate Gojo-secrecy (mention Gojo in outputs) unless they self-check
- **No proactive nudges**: Won't remind about backups, manifests, or session continuity
- **No opportunistic risk calls**: Won't auto-escalate high-risk operations
- **No auto-detection**: Protocol violations may go unnoticed until explicit review

#### 2. Reviews Become Opt-In Only
- **Gojo won't appear** unless explicitly invoked:
  - `"Read protocol/GOJO.md - Trigger 19"` (intelligence report)
  - `"Read protocol/GOJO.md"` (mission control)
  - `"Gojo: Review this implementation"`
- **Dual workflow remains**: Yuuji builds, Megumi audits (unchanged)
- **Arbitration/triage is idle**: No automatic conflict resolution or priority calls

#### 3. Weaker Guardrails on Core Files
- **Edits to protocol docs aren't auto-flagged**:
  - Changes to `CLAUDE.md`, `protocol.config.yaml`, or role files
  - Modifications to state files or configuration
- **Rely on PR process**: Manual review and labels for protection
- **CODEOWNERS still active**: Git-level protection remains (if configured)

#### 4. Observability Drops
- **No passive transcripts**: No session summaries or behavioral observations
- **No intelligence accumulation**: Trigger 19 reports will be minimal/empty
- **Depend on commit history**: Git log and role outputs are your audit trail
- **No pattern detection**: Won't identify recurring issues or anti-patterns

---

## ✅ Mitigations While OFF

When running with Passive Observer disabled, implement these compensating controls:

### 1. Explicit Checkpoints
Add manual gates to your workflow:
- **Before Yuuji starts**: Review requirements and tier selection
- **After Yuuji deliverable**: User review before security handoff
- **Before merge**: Final verification of all requirements

### 2. Megumi Isolation Checklist
Make Megumi verify isolation rules:
- ✅ Check for forbidden terms in Yuuji/Nobara outputs (no "Gojo", "passive", "observer")
- ✅ Verify Yuuji/Nobara didn't reference Gojo's existence
- ✅ Confirm role separation maintained (Yuuji/Megumi/Nobara don't cross-reference inappropriately)

### 3. PR Template Enforcement
Use PR templates and labels:
- **Backup verification**: Confirm backup created before changes
- **Change manifest**: List all modified files and their purpose
- **Tier declaration**: State which tier was used (Rapid/Standard/Critical)
- **Security review status**: Tag `@security-review` or `@approved`

### 4. Protocol Doc Protection
Require 2-approver rule for:
- `protocol/CLAUDE.md`
- `protocol.config.yaml`
- `protocol/YUUJI.md`, `MEGUMI.md`, `NOBARA.md`, `GOJO.md`
- Any state files or configuration

### 5. Explicit Gojo Invocation
Manually summon Gojo for high-risk operations:
- **Secrets management**: API keys, tokens, credentials
- **Authentication**: OAuth, JWT, session management
- **Data migrations**: Schema changes, data transforms
- **Protocol changes**: Modifications to core protocol files

---

## ✅ When Passive Observer is ON

### Benefits of Enabling

#### 1. Proactive Safety
- **Automatic backup reminders**: Gojo nudges Yuuji to create backups before changes
- **Isolation enforcement**: Silent checks that Yuuji/Megumi/Nobara maintain role separation
- **Risk detection**: Auto-escalates high-risk operations (auth, payments, secrets)
- **Session continuity**: Tracks work across sessions for better context

#### 2. Enhanced Observability
- **Passive transcripts**: Session summaries and behavioral observations
- **Pattern detection**: Identifies recurring issues, anti-patterns, team habits
- **Intelligence reports**: Rich Trigger 19 reports with actionable insights
- **Trend analysis**: Spots drift, missed requirements, or protocol violations over time

#### 3. Automatic Guardrails
- **Core file protection**: Auto-flags edits to CLAUDE.md or protocol files
- **Change detection**: Notices unauthorized modifications
- **Compliance tracking**: Monitors tier adherence and quality gates
- **Conflict resolution**: Arbitrates disagreements between Yuuji and Megumi

#### 4. Smarter Workflow
- **Contextual nudges**: "You're on a Critical tier feature—enable multi-model review?"
- **Opportunistic optimization**: "This pattern was flagged in Trigger 19 last week"
- **Proactive triage**: "3 P0 issues open—escalate to user?"
- **Session restoration**: "You left off implementing auth middleware—resume?"

---

## Privacy & Consent Considerations

### Why OFF by Default?

**Privacy-First Design**: Passive Observer collects session data for intelligence reports. This includes:
- Conversation transcripts (anonymized)
- Code changes and patterns
- Developer behavior and decision-making
- Time spent on tasks and blockers

**Explicit Consent Required**:
- You must **opt-in** to enable Passive Observer
- Set `passive_monitoring.enabled = true` **AND** `passive_monitoring.consent_given = true`
- Consent date is recorded for audit purposes

### Data Retention

When enabled, Passive Observer data:
- **Storage**: Local by default (`storage_location: "local"`)
- **Retention**: 14 days default (`data_retention_days: 14`)
- **Privacy**: trigger-19.md is **gitignored** by default (never committed)
- **GDPR Mode**: Enhanced privacy safeguards when `privacy.gdpr_mode = true`

### Disabling Anytime

You can disable Passive Observer at any time:
```yaml
# In protocol.config.yaml
privacy:
  passive_monitoring:
    enabled: false
    consent_given: false
```

Gojo will immediately stop background monitoring and clear temporary session data.

---

## How to Enable Passive Observer

### Step 1: Review Privacy Settings

Edit `protocol.config.yaml`:
```yaml
privacy:
  passive_monitoring:
    enabled: true              # Enable background monitoring
    consent_given: true        # Explicit consent (required)
    consent_date: "2025-11-05T00:00:00Z"  # Date you gave consent
    data_retention_days: 14    # How long to keep observations
    storage_location: "local"  # local, encrypted, cloud
```

### Step 2: Update Project State

Edit `.protocol-state/project-state.json`:
```json
{
  "passive_monitoring": {
    "enabled": true,
    "consent_given": true,
    "consent_date": "2025-11-05T00:00:00Z",
    "sessions_since_trigger_19": 0
  }
}
```

### Step 3: Invoke Gojo to Activate

In your AI assistant:
```text
Read protocol/GOJO.md
```

Gojo will detect Passive Observer is enabled and begin monitoring.

### Step 4: Test with Trigger 19

After a few work sessions, request an intelligence report:
```text
Read protocol/GOJO.md - Trigger 19
```

You should receive a detailed report with observations, patterns, and recommendations.

---

## Comparison: OFF vs ON

| Feature | Passive Observer OFF | Passive Observer ON |
|---------|---------------------|-------------------|
| **Background enforcement** | ❌ Manual only | ✅ Automatic |
| **Isolation checks** | ❌ Self-check only | ✅ Silent verification |
| **Backup reminders** | ❌ Manual | ✅ Proactive nudges |
| **Risk escalation** | ❌ Manual invocation | ✅ Automatic detection |
| **Gojo availability** | 🟡 Explicit invoke only | ✅ Always available |
| **Trigger 19 reports** | 🟡 Minimal/empty | ✅ Rich insights |
| **Core file protection** | ❌ PR process only | ✅ Auto-flagged |
| **Session continuity** | ❌ Git history only | ✅ Context tracking |
| **Privacy** | ✅ No data collection | ⚠️ Session data collected |
| **Consent required** | ❌ No | ✅ Yes (explicit opt-in) |

---

## Decision Guide: Should I Enable It?

### ✅ Enable Passive Observer If:

- You want **proactive safety** and automatic enforcement
- You're working on **high-risk features** (auth, payments, compliance)
- You value **intelligence reports** and pattern detection
- You're comfortable with **session data collection** (local, ephemeral)
- You want **Gojo's arbitration** and triage capabilities
- You trust the **privacy controls** (local storage, 14-day retention, gitignored)

### ❌ Keep It OFF If:

- You prefer **manual control** over all protocol operations
- You have **strict privacy requirements** (no session tracking)
- You're working in a **regulated environment** (legal, medical, financial)
- You don't need **background monitoring** or intelligence reports
- You're comfortable with **explicit checkpoints** and manual reviews
- You want **minimal AI overhead** (only invoke when needed)

---

## Rule of Thumb

**Turn Passive Observer back ON if you notice:**
- ❌ Drift in protocol adherence (missed backups, isolation breaches)
- ❌ Recurring bugs or anti-patterns
- ❌ Missed requirements or incomplete implementations
- ❌ Yuuji/Megumi/Nobara violating isolation (mentioning Gojo)
- ❌ High-risk operations without Gojo review
- ❌ Lack of session continuity between work sessions

**Passive Observer transforms Domain Zero from a reactive system to a proactive guardian.**

---

## Passive-Off Checklist (For PR Templates)

Use this checklist when Passive Observer is disabled:

```markdown
## Domain Zero Protocol Compliance (Passive Observer: OFF)

Since Passive Observer is disabled, please verify:

### Pre-Flight Checks
- [ ] Backup created before any code changes
- [ ] Tier declared (Rapid/Standard/Critical)
- [ ] Change manifest documented (list of modified files)

### Isolation Verification
- [ ] Yuuji output reviewed for forbidden terms (no "Gojo", "passive", "observer")
- [ ] Nobara output reviewed for forbidden terms (no "Gojo", "passive", "observer")
- [ ] Megumi output reviewed for role separation
- [ ] No cross-agent references in dev-notes.md or security-review.md

### Quality Gates
- [ ] Tests written (if Tier 2+)
- [ ] Security review completed (if Tier 2+)
- [ ] Megumi approval obtained (@approved tag)
- [ ] Rollback plan documented

### High-Risk Operations (if applicable)
- [ ] Gojo explicitly invoked for review
- [ ] Secrets/auth/payments reviewed by Gojo
- [ ] Protocol file changes approved (2-reviewer rule)

### Session Continuity
- [ ] dev-notes.md updated with current status
- [ ] Blockers documented (if any)
- [ ] Next steps clearly defined

**Note**: Consider enabling Passive Observer for enhanced safety and proactive monitoring.
See `PASSIVE_OBSERVER.md` for benefits and setup instructions.
```

---

## Frequently Asked Questions

### Q: Is my data sent to external servers?

**A**: No. By default, `storage_location: "local"` keeps all Passive Observer data on your machine. It's never uploaded unless you explicitly configure cloud storage.

### Q: Is trigger-19.md tracked in git?

**A**: No. The `.gitignore` file explicitly excludes `trigger-19.md` by default. This file contains Gojo's private observations and is never committed to version control.

### Q: Can I enable Passive Observer temporarily?

**A**: Yes! Enable it for high-risk features or sprints, then disable when done. Toggle the settings in `protocol.config.yaml` and restart your session.

### Q: What happens to existing data if I disable it?

**A**: Gojo clears temporary session data but preserves the Trigger 19 report (trigger-19.md) until you manually delete it or it ages out per retention policy.

### Q: Does Passive Observer slow down my workflow?

**A**: No. Monitoring happens in the background and doesn't block Yuuji or Megumi's work. Trigger 19 reports are generated on-demand, not continuously.

### Q: Can I customize what Gojo observes?

**A**: Yes. Edit `protocol.config.yaml` to adjust observation scope, data retention, and reporting frequency. See Gojo's protocol file for advanced configuration.

---

## Summary

**Passive Observer OFF** (default):
- Privacy-focused, no data collection
- Manual enforcement and explicit invocations only
- Requires compensating controls (checkpoints, PR templates, 2-approver rules)
- Best for: privacy-sensitive environments, manual control preference

**Passive Observer ON** (opt-in):
- Proactive safety, automatic enforcement, rich intelligence
- Continuous background monitoring and pattern detection
- Local storage, ephemeral data, gitignored reports
- Best for: high-risk projects, complex workflows, team collaboration

**Choose based on your privacy requirements, risk tolerance, and workflow preferences.**

---

**Domain Zero Protocol v6.0** - Perfect Code Through Infinite Collaboration

*The weight is real. The protocol is absolute. Domain Zero is active.*
