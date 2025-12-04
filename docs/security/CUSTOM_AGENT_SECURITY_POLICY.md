# Custom Agent Security Policy (v8.7.0)

**Domain Zero Protocol - Custom Agent Security Policy**
**Version**: 8.7.0
**Effective Date**: 2025-12-03
**Status**: ACTIVE

---

## Purpose

This document defines the security policies, requirements, and enforcement mechanisms for custom agents in the Domain Zero Protocol. Custom agents extend the protocol's capabilities but must operate within strict security boundaries to protect your codebase and maintain protocol integrity.

---

## Security Threat Model

### Threat Actors

1. **Malicious Custom Agents** - Agents intentionally designed to bypass security or exfiltrate data
2. **Compromised Agent Files** - Legitimate agents modified by attackers
3. **Accidental Privilege Escalation** - Well-intentioned agents with excessive permissions
4. **Supply Chain Attacks** - Distribution of pre-packaged malicious agents

### Attack Vectors

- **Agent Name Collision**: Impersonating core agents (yuuji, megumi, gojo)
- **Tool Permission Abuse**: Using bash/task tools for code execution
- **Self-Modification**: Agents editing their own .agent.md files
- **YAML Injection**: Code injection via malicious YAML frontmatter
- **File System Access**: Unauthorized modification of protocol files
- **Coordination Attacks**: Multiple compromised agents working together

---

## Security Requirements

### 1. Namespace Protection (CUST-CRIT-002)

**Policy**: Custom agent names must be globally unique and distinguishable from core agents.

**Requirements**:
- ✅ **MUST** follow pattern: `custom-[name]`
- ✅ **MUST** be lowercase, alphanumeric with hyphens
- ✅ **MUST** be 5-23 characters total (including `custom-` prefix)
- ❌ **MUST NOT** match reserved names:
  - Core agents: `yuuji`, `megumi`, `nobara`, `gojo`
  - Extended agents: `todo`, `maki`, `panda`, `inumaki`
  - System agents: `sukuna`, `claude`
  - Reserved: `admin`, `root`, `system`, `mission_control`

**Enforcement**:
- Pre-invocation validation blocks invalid names
- Runtime checks prevent name changes

**Examples**:
```yaml
✅ Valid:   custom-formatter, custom-data-analyzer, custom-tester
❌ Invalid: gojo, custom_formatter, formatter, CUSTOM-FORMATTER
```

---

### 2. Tool Permission Control (CUST-CRIT-003)

**Policy**: Custom agents have restricted tool access based on risk level.

**Permission Tiers**:

**Tier 1 - Default Allowed** (No approval required):
- `read` - Read files
- `grep` - Search file contents
- `glob` - Find files by pattern
- `askuserquestion` - Prompt user for input

**Tier 2 - Requires Approval** (Granted with warning):
- `write` - Create new files
- `edit` - Modify existing files
- `webfetch` - Fetch web content
- `websearch` - Search the web
- `todowrite` - Manage todo lists

**Tier 3 - Forbidden** (Never allowed):
- `bash` - Execute shell commands
- `task` - Spawn other agents
- `notebookedit` - Modify Jupyter notebooks
- `killshell` - Terminate processes

**Enforcement**:
- Tools declared in YAML are filtered at registration time
- Runtime monitoring prevents unauthorized tool use
- Violations trigger automatic quarantine

---

### 3. YAML Sanitization (CUST-CRIT-004)

**Policy**: Agent YAML frontmatter must not contain code injection patterns.

**Forbidden Patterns**:
```yaml
❌ __proto__           # Prototype pollution
❌ eval:               # Code evaluation
❌ exec:               # Code execution
❌ ${...}              # Template injection
❌ require(            # Module loading
❌ import              # Import statements
❌ !!python/           # Python object deserialization
```

**Required Fields**:
```yaml
✅ name:        custom-myagent
✅ description: Agent description
✅ tools:       [read, grep]
✅ model:       sonnet
```

**Enforcement**:
- Pre-invocation regex scanning
- YAML parsing with safe_load only
- Validation errors block agent registration

---

### 4. File Immutability (CUST-CRIT-008)

**Policy**: Custom agents cannot modify protected files or themselves.

**Immutable Paths**:
- `protocol/` - Core protocol definitions
- `.claude/agents/` - Agent definition files
- `.protocol-state/custom-agent-registry.json` - Registry database
- `.protocol-state/authorization/` - Security logs
- `protocol.config.yaml` - Configuration

**Enforcement**:
- File write operations are monitored
- Attempts to modify immutable paths are blocked
- SHA-256 hashes detect file modifications
- Frequent modifications trigger quarantine

---

### 5. Rate Limiting (CUST-HIGH-001)

**Policy**: Prevent resource exhaustion from excessive invocations.

**Limits**:
- Maximum 10 invocations per minute per agent
- Maximum 2 concurrent custom agents
- 5-second cooldown between rapid invocations

**Enforcement**:
- In-memory timestamp tracking
- Exceeded limits block invocation
- Violations logged to audit log

---

### 6. Registry and Monitoring (CUST-CRIT-006)

**Policy**: All custom agent activity must be tracked and auditable.

**Monitoring**:
- Registry file: `.protocol-state/custom-agent-registry.json`
- Audit log: `.protocol-state/authorization/custom-agent-audit.log`
- Tracked data:
  - Invocation timestamps
  - Tool usage patterns
  - Validation failures
  - File modifications
  - Quarantine status

**Enforcement**:
- Every invocation is registered
- Failed validations are counted
- Anomalies trigger warnings
- Gojo has full visibility

---

## Enforcement Mechanisms

### Pre-Invocation Validation

**Script**: `scripts/validate-custom-agents.py`

**When**: Before first invocation of custom agent

**Checks**:
1. Agent name follows naming rules
2. YAML structure is valid
3. No forbidden YAML patterns
4. Tools are in allowed lists
5. File size under 100KB

**Result**: PASS or FAIL with specific errors

### Runtime Monitoring

**Module**: `.protocol-state/custom_agent_monitor.py`

**When**: During and after agent invocation

**Actions**:
1. Register invocation in registry
2. Filter tool permissions
3. Check rate limits
4. Detect file modifications
5. Identify anomalies
6. Log all activity

**Result**: Granted tools, denied tools, warnings

### Automatic Quarantine

**Trigger Conditions**:
- Validation failure with forbidden patterns
- Attempting to use forbidden tools
- Excessive file modifications (5+)
- High anomaly score (3+ anomalies)
- Manual quarantine by Gojo or user

**Effect**:
- Agent cannot be invoked
- Registry marked as quarantined
- Reason logged to audit
- User must manually review

---

## User Responsibilities

### Creating Custom Agents

1. **Follow Naming Rules**: Use `custom-` prefix
2. **Request Minimal Tools**: Only request tools you need
3. **Validate Before Use**: Run validation script
4. **Review Warnings**: Pay attention to approval-required tools
5. **Test Safely**: Test in non-production environments first

### Maintaining Custom Agents

1. **Avoid Frequent Edits**: Excessive modifications trigger warnings
2. **Don't Share .agent.md**: Agents are project-specific
3. **Review Audit Logs**: Check `.protocol-state/authorization/custom-agent-audit.log`
4. **Respond to Quarantines**: Investigate why agent was quarantined

### Security Incident Response

If you discover a security issue:

1. **Quarantine Immediately**:
   ```bash
   python .protocol-state/custom_agent_monitor.py --quarantine custom-suspicious \
       --reason "Unauthorized tool usage detected"
   ```

2. **Review Audit Log**:
   ```bash
   grep "custom-suspicious" .protocol-state/authorization/custom-agent-audit.log
   ```

3. **Check Registry**:
   ```bash
   python .protocol-state/custom_agent_monitor.py --summary custom-suspicious
   ```

4. **Remove Agent File** (if malicious):
   ```bash
   rm .claude/agents/custom-suspicious.agent.md
   ```

---

## Configuration

### protocol.config.yaml Settings

```yaml
custom_agent_security:
  enabled: true  # Master toggle

  registration:
    require_validation: true
    auto_quarantine_on_failure: true
    max_custom_agents: 10  # Per project

  namespace:
    reserved_names: [yuuji, megumi, nobara, gojo, todo, maki, panda, inumaki, sukuna]
    require_prefix: "custom-"
    allow_prefix_override: false

  tool_permissions:
    custom_agents_default: [read, grep, glob, askuserquestion]
    requires_approval: [write, edit, webfetch, websearch, todowrite]
    forbidden: [bash, task, notebookedit, killshell]
    runtime_validation: true
    block_on_violation: true

  file_protection:
    immutable_paths:
      - "protocol/"
      - ".claude/agents/"
      - ".protocol-state/custom-agent-registry.json"
      - ".protocol-state/authorization/"
      - "protocol.config.yaml"
    block_self_modification: true

  monitoring:
    enabled: true
    track_tool_usage: true
    detect_anomalies: true

  rate_limiting:
    enabled: true
    max_invocations_per_minute: 10
    max_concurrent_custom_agents: 2
    cooldown_period_seconds: 5
```

---

## Compliance

### For Users

- **Validation is Mandatory**: All custom agents must pass validation
- **Tool Restrictions Apply**: Forbidden tools cannot be used
- **Monitoring is Always On**: Custom agent activity is always logged
- **Quarantine is Enforceable**: Gojo can quarantine any custom agent

### For Custom Agents

- **No Self-Modification**: Cannot edit own .agent.md file
- **No Core Impersonation**: Cannot use core agent names
- **No Protocol Modification**: Cannot edit protocol/ files
- **Tool Compliance**: Must respect granted/denied tool lists

---

## Exceptions

**NONE**. Security policies have no exceptions. If you need capabilities beyond these policies, either:

1. Request Gojo to perform the operation
2. Perform the operation manually
3. Propose a protocol enhancement via GitHub issue

---

## Audit and Review

### Audit Logs

Location: `.protocol-state/authorization/custom-agent-audit.log`

Retention: Indefinite (user responsible for archival)

Format:
```
2025-12-03T10:30:15 | INVOCATION | custom-agent | by=user | validated=True
2025-12-03T10:30:16 | TOOL_GRANTED | custom-agent | read | DEFAULT_ALLOWED
2025-12-03T10:30:20 | TOOL_DENIED | custom-agent | bash | FORBIDDEN
2025-12-03T10:30:21 | AGENT_QUARANTINED | custom-agent | Reason: Forbidden tool
```

### Security Reviews

- **Gojo Reviews**: Automatic on every invocation
- **User Reviews**: Should review audit log periodically
- **Protocol Updates**: Security policies may be updated in future versions

---

## Version History

- **v8.7.0** (2025-12-03): Initial security policy
  - Implemented namespace protection
  - Implemented tool permission control
  - Implemented YAML sanitization
  - Implemented file immutability
  - Implemented monitoring and quarantine

---

## References

- **Red Team Assessment**: `internal-docs/RED_TEAM_ASSESSMENT_CUSTOM_AGENTS_v8.7.0.md`
- **Gojo Integration Guide**: `.protocol-state/gojo-custom-agent-security-guide.md`
- **Validation Script**: `scripts/validate-custom-agents.py`
- **Monitor Module**: `.protocol-state/custom_agent_monitor.py`
- **Agent Creation Guide**: `docs/guides/CREATING_CLAUDE_AGENTS.md`

---

**This policy is authoritative. All custom agents must comply. Non-compliance results in automatic quarantine.**
