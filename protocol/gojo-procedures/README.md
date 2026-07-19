# Gojo Operational Procedures Index
<!-- [CORE FILE] - Domain Zero Protocol v9.10.1 -->

**Purpose**: Central index of all Gojo (Mission Control) operational procedures and implementation guides.
**Version**: 8.10.0
**Updated**: 2025-12-25

---

## 📚 Available Procedures

| Procedure | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Core Workflows** | [OPERATIONAL_PROCEDURES.md](./OPERATIONAL_PROCEDURES.md) | ~500 | Mission Control interface options and step-by-step procedures |
| **Session Monitoring** | [SESSION_MONITORING.md](./SESSION_MONITORING.md) | ~430 | Work session tracking, alerts, and enforcement implementation |
| **Custom Agent Security** | [CUSTOM_AGENT_SECURITY.md](./CUSTOM_AGENT_SECURITY.md) | ~640 | Security validation and monitoring for custom agents |
| **Snapshot Integration** | [SNAPSHOT_INTEGRATION.md](./SNAPSHOT_INTEGRATION.md) | ~200 | Tier-based automatic snapshot creation |

---

## 🔄 Core Workflows (OPERATIONAL_PROCEDURES.md)

### Procedure 1: Resume Current Project
- Load context from project-state.json
- Compile mission briefs for all agents
- Deploy agents based on current status
- **When to use**: Daily startup, returning to work

### Procedure 2: New Project Initialization
- PSD-guided setup
- Create complete folder structure
- Initialize state management
- Brief team on mission
- **When to use**: Starting new projects

### Procedure 3: Trigger 19 Intelligence Report
- Compile passive observations
- Agent performance analysis
- Strategic recommendations
- Protocol compliance status
- **When to use**: Weekly reviews, effectiveness assessment

### Procedure 4: Resume from Emergency Stop
- Load checkpoint from kill switch
- Show what was in progress
- Clear protection mode after confirmation
- **When to use**: After kill switch activation

### Procedure 5: Save & Break Protocol
- Create session snapshot
- Update dev-notes.md with checkpoint
- Commit partial work (WIP commit)
- Record break in session state
- **When to use**: Extended sessions, before risky operations

### Procedure 6: Resume Protocol
- Resume session and check status
- Show last checkpoint
- Present continuation options
- **When to use**: Returning after break

---

## ⏰ Session Monitoring (SESSION_MONITORING.md)

### Implementation Guide
Complete technical guide for integrating `session_monitor.py` with real-time tracking:
- Session initialization and state management
- Alert trigger logic (4h, 6h, 8h thresholds)
- User choice handling (save & break vs continue)
- High-risk operation blocking
- Session lifecycle management

### Key Features
- ✅ Real-time tracking via `session_monitor.py`
- ✅ Persistent state in `session-state.json`
- ✅ Template rendering with actual data
- ✅ High-risk operation blocking enforcement
- ✅ Integration with Passive Observer

### When to Reference
- On every Gojo invocation (mandatory session check)
- Before high-risk operations
- When extended sessions detected
- For Trigger 19 session metrics

---

## 🛡️ Custom Agent Security (CUSTOM_AGENT_SECURITY.md)

### Security Components
1. **validate-custom-agents.py** - Pre-invocation validation
2. **custom_agent_monitor.py** - Runtime monitoring and enforcement
3. **protocol.config.yaml** - Security policy configuration
4. **Audit logs** - Tamper-evident activity tracking

### Validation Checks
- Namespace protection (custom-* pattern)
- YAML sanitization (forbidden patterns)
- Tool permissions (allowed tools only)
- File integrity (size, format)

### Monitoring Features
- Quarantine status checks
- Rate limiting (10 invocations/minute)
- Invocation registration
- Anomaly detection

### When to Reference
- Before custom agent invocation
- When validation fails
- For security policy enforcement
- During quarantine operations

---

## 📸 Snapshot Integration (SNAPSHOT_INTEGRATION.md)

### Tier-Based Automation
- **Tier 1**: Manual snapshots only
- **Tier 2**: Automatic snapshot every 10 operations
- **Tier 3**: Automatic snapshot after EACH operation
- **All Tiers**: Automatic snapshot on tier changes

### Integration Pattern
Uses `snapshot_integration.py` to:
1. Record operations
2. Check snapshot thresholds
3. Create snapshots automatically
4. Track operation counts

### When Operations Should Be Recorded
- ✅ Feature implementation complete
- ✅ Security review complete
- ✅ Design work finished
- ✅ Database operations done
- ✅ Major milestones reached

### When to Reference
- After agent task completion
- When tier changes
- For snapshot policy enforcement
- During feature delivery

---

## 🔗 Cross-References

### Related Files
- **gojo.agent.md** - Main agent file (references procedures)
- **protocol/skills/gojo/** - Optional/complex Gojo skills
- **protocol.config.yaml** - Configuration for all procedures
- **.protocol-state/session-state.json** - Session tracking state
- **.protocol-state/project-state.json** - Project and tier state

### Integration Points
- Procedures → Called from gojo.agent.md operational modes
- Session Monitoring → Mandatory first invoke on Gojo activation
- Custom Agent Security → Referenced during custom agent invocation
- Snapshot Integration → Triggered after agent task completion

---

## 📖 Usage Guidelines

### For Gojo (Mission Control)
1. **Always reference** SESSION_MONITORING.md on first invoke
2. **Consult** OPERATIONAL_PROCEDURES.md for workflow steps
3. **Enforce** CUSTOM_AGENT_SECURITY.md for custom agents
4. **Apply** SNAPSHOT_INTEGRATION.md after task completion

### For Other Agents
- ❌ **READ-ONLY** access to all procedures
- ✅ Can reference procedures for context
- ✅ Cannot modify procedures
- ✅ Escalate to Gojo for procedural guidance

### For Users
- ✅ Read procedures to understand Gojo's behavior
- ✅ Reference procedures for troubleshooting
- ✅ Modify with explicit authorization (USER authority)
- ✅ Suggest improvements via protocol updates

---

## 🔄 Maintenance

**Last Updated**: 2025-12-17
**Maintained By**: Ryomen Sukuna (System Update Adversary)
**Review Cycle**: With each protocol version update

**Update Triggers**:
- Protocol version increment
- Sukuna security review findings
- Gojo workflow enhancements
- User feedback integration

---

## 📝 Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-22 | 8.9.0 | Version alignment with v8.9.0 release |
| 2025-12-17 | 8.8.0 | Created README index, moved INTERNAL guides to CORE |
| 2025-12-06 | 8.8.0 | Added SNAPSHOT_INTEGRATION.md |
| 2025-12-03 | 8.7.0 | Added CUSTOM_AGENT_SECURITY.md |
| 2025-12-03 | 8.7.0 | Added SESSION_MONITORING.md (Sukuna's fix) |
| 2025-12-02 | 8.6.0 | Created OPERATIONAL_PROCEDURES.md |

---

**For detailed implementation, see individual procedure files.**
