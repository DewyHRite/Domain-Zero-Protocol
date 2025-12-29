# Gojo Custom Agent Security Integration Guide
<!-- [CORE FILE] - Domain Zero Protocol v8.12.0 -->

**Purpose**: Guide for Gojo to enforce custom agent security policies
**Version**: 8.12.0
**Updated**: 2025-12-29

---

## Overview

This guide provides Gojo with the tools and procedures to enforce custom agent security policies, addressing vulnerabilities identified in Sukuna's red team assessment (CUST-CRIT-001 through CUST-CRIT-008).

### Security Components

1. **validate-custom-agents.py** - Pre-invocation validation
2. **custom_agent_monitor.py** - Runtime monitoring and enforcement
3. **protocol.config.yaml** - Security policy configuration
4. **Audit logs** - Tamper-evident activity tracking

---

## Quick Reference

### When User Invokes Custom Agent

```python
# Step 1: Validate agent file
validation_result = run_validation(agent_file_path)

# Step 2: Check quarantine status
is_quarantined, reason = monitor.is_quarantined(agent_name)
if is_quarantined:
    ❌ Block invocation

# Step 3: Check rate limits
is_valid, error = monitor.validate_rate_limit(agent_name)
if not is_valid:
    ❌ Block invocation

# Step 4: Register invocation
invocation = monitor.register_invocation(...)

# Step 5: Check for anomalies
anomalies = monitor.detect_anomalies(agent_name)
if anomalies:
    ⚠️  Warn user
```

---

## Component 1: Pre-Invocation Validation

### Validate Agent File

Before allowing custom agent invocation, run validation:

```python
import subprocess
import json
from pathlib import Path

def validate_custom_agent(agent_file_path: Path) -> dict:
    """
    Validate custom agent file against security policies.

    Returns:
        {
            'passed': bool,
            'errors': list[str],
            'warnings': list[str],
            'info': list[str]
        }
    """
    result = subprocess.run(
        ['python', 'scripts/validate-custom-agents.py', str(agent_file_path)],
        capture_output=True,
        text=True
    )

    # Parse validation output
    output = result.stdout
    passed = result.returncode == 0

    # Extract errors/warnings from output
    lines = output.split('\n')
    errors = [l for l in lines if l.startswith('❌ ERROR:')]
    warnings = [l for l in lines if l.startswith('⚠️  WARNING:')]
    info = [l for l in lines if l.startswith('ℹ️  INFO:')]

    return {
        'passed': passed,
        'errors': errors,
        'warnings': warnings,
        'info': info
    }
```

### Validation Checks

The validator checks:

1. **Namespace Protection** (CUST-CRIT-002)
   - Agent name follows `custom-[name]` pattern
   - Not in reserved_names list (yuuji, megumi, gojo, etc.)

2. **YAML Sanitization** (CUST-CRIT-004)
   - No forbidden patterns (__proto__, eval:, exec:)
   - Required fields present (name, description, tools, model)

3. **Tool Permissions** (CUST-CRIT-003)
   - Tools in allowed list
   - Forbidden tools (bash, task) blocked

4. **File Integrity**
   - File size under 100KB
   - Valid markdown format

### Response to Validation Failure

```python
if not validation_result['passed']:
    # Log failure
    print(f"🛑 Custom agent validation failed: {agent_name}")
    for error in validation_result['errors']:
        print(f"  {error}")

    # Auto-quarantine if critical
    if any('forbidden' in e.lower() for e in validation_result['errors']):
        monitor.quarantine_agent(
            agent_name,
            "Critical validation failure: forbidden pattern detected"
        )

    # Block invocation
    return "❌ Cannot invoke custom agent: validation failed"
```

---

## Component 2: Runtime Monitoring

### Initialize Monitor

```python
from pathlib import Path
import sys

# Import custom agent monitor
sys.path.append('.protocol-state')
from custom_agent_monitor import CustomAgentMonitor

# Initialize
protocol_root = Path.cwd()
monitor = CustomAgentMonitor(protocol_root)
```

### Check Quarantine Status

Before invocation, check if agent is quarantined:

```python
is_quarantined, reason = monitor.is_quarantined(agent_name)

if is_quarantined:
    print(f"🛑 Agent '{agent_name}' is quarantined")
    print(f"Reason: {reason}")
    print("Contact user to review and release from quarantine")
    return  # Block invocation
```

### Rate Limiting

Prevent excessive invocations:

```python
# Check rate limit (default: 10 invocations per minute)
is_valid, error_msg = monitor.validate_rate_limit(agent_name, max_per_minute=10)

if not is_valid:
    print(f"⚠️  {error_msg}")
    print("Wait 60 seconds before retrying")
    return  # Block invocation
```

### Register Invocation

After validation passes, register the invocation:

```python
# Load security config
import yaml
with open('protocol.config.yaml', 'r') as f:
    config = yaml.safe_load(f)

security_config = config['custom_agent_security']

# Register invocation
invocation = monitor.register_invocation(
    agent_name=agent_name,
    agent_file_path=agent_file_path,
    invoked_by='user',  # or 'gojo' if you invoke it
    requested_tools=agent_yaml['tools'],  # From agent YAML frontmatter
    validation_result=validation_result,
    config=security_config
)

# Check what tools were granted vs denied
if invocation.tools_denied:
    print(f"⚠️  Some tools were denied:")
    for tool in invocation.tools_denied:
        print(f"  - {tool}")
    print(f"Agent will only have access to: {', '.join(invocation.tools_granted)}")
```

### Anomaly Detection

After invocation, check for suspicious patterns:

```python
anomalies = monitor.detect_anomalies(agent_name)

if anomalies:
    print(f"⚠️  ANOMALIES DETECTED for '{agent_name}':")
    for anomaly in anomalies:
        print(f"  - {anomaly}")

    # Auto-quarantine if serious
    if len(anomalies) >= 3:
        monitor.quarantine_agent(
            agent_name,
            f"Multiple anomalies detected: {len(anomalies)}"
        )
        print(f"🛑 Agent '{agent_name}' has been auto-quarantined")
```

---

## Component 3: Tool Permission Enforcement

### How Tool Filtering Works

The monitor validates requested tools against three categories:

```yaml
# From protocol.config.yaml
custom_agent_security:
  tool_permissions:
    custom_agents_default:  # Always allowed
      - read
      - grep
      - glob
      - askuserquestion

    requires_approval:  # Allowed with warning
      - write
      - edit
      - webfetch
      - websearch
      - todowrite

    forbidden:  # Never allowed
      - bash
      - task
      - notebookedit
      - killshell
```

### Runtime Enforcement

```python
# Tools are filtered during register_invocation()
granted, denied, errors = monitor.validate_tool_permissions(
    agent_name,
    requested_tools=['read', 'write', 'bash'],
    config=security_config
)

# granted = ['read', 'write']  # write requires approval but is granted
# denied = ['bash']  # bash is forbidden
# errors = ["Tool 'bash' is forbidden for custom agents"]
```

### Enforcing Tool Access

When agent attempts to use a tool:

```python
def agent_can_use_tool(agent_name: str, tool: str) -> bool:
    """Check if agent has permission for tool."""
    # Load latest invocation record
    summary = monitor.get_agent_summary(agent_name)
    if not summary:
        return False

    # Get registry entry
    registry = monitor.load_registry()
    entry = registry[agent_name]

    # Check last invocation's granted tools
    if entry.invocation_history:
        last_invocation = entry.invocation_history[-1]
        granted_tools = last_invocation['tools_granted']
        return tool.lower() in [t.lower() for t in granted_tools]

    return False
```

---

## Component 4: File Immutability Protection

### Detect Self-Modification Attempts (CUST-CRIT-008)

The monitor tracks file hashes to detect modifications:

```python
# File hash is computed on each invocation
file_hash = monitor.compute_file_hash(agent_file_path)

# Compare with previous hash
registry = monitor.load_registry()
if agent_name in registry:
    entry = registry[agent_name]

    if entry.file_hash and file_hash != entry.file_hash:
        print(f"⚠️  WARNING: Agent file has been modified!")
        print(f"  Old hash: {entry.file_hash[:16]}...")
        print(f"  New hash: {file_hash[:16]}...")
        print(f"  Total modifications: {entry.hash_changed_count + 1}")

        # Auto-quarantine if excessive modifications
        if entry.hash_changed_count >= 5:
            monitor.quarantine_agent(
                agent_name,
                "Excessive file modifications detected (potential self-modification attack)"
            )
```

### Block Write Operations to Agent Files

Add to Gojo's tool monitoring:

```python
def check_write_operation(file_path: str, agent_name: str) -> bool:
    """
    Check if write operation should be blocked.

    Returns True if allowed, False if blocked.
    """
    immutable_paths = [
        'protocol/',
        '.claude/agents/',
        '.protocol-state/custom-agent-registry.json',
        '.protocol-state/authorization/',
        'protocol.config.yaml'
    ]

    # Check if path matches immutable patterns
    for pattern in immutable_paths:
        if file_path.startswith(pattern):
            print(f"🛑 BLOCKED: Agent '{agent_name}' attempted to modify protected file")
            print(f"  File: {file_path}")
            print(f"  Reason: File is in immutable path '{pattern}'")

            # Log to audit
            monitor.audit_logger.critical(
                f"IMMUTABILITY_VIOLATION | {agent_name} | Attempted write to {file_path}"
            )

            return False  # Block

    return True  # Allow
```

---

## Monitoring and Maintenance

### View All Custom Agents

```bash
python .protocol-state/custom_agent_monitor.py --list
```

Output:
```
================================================================================
Registered Custom Agents (3)
================================================================================

✅ Active | custom-data-analyzer
  Invocations: 15
  Last Used: 2025-12-03T10:30:00
  Tools: read, grep, glob

🔴 QUARANTINED | custom-deploy-helper
  Invocations: 3
  Last Used: 2025-12-03T09:15:00
  Tools: bash, write
  Quarantine Reason: Attempted to use forbidden tool 'bash'

✅ Active | custom-formatter
  Invocations: 8
  Last Used: 2025-12-03T11:00:00
  Tools: read, write, edit
```

### Agent Summary

```bash
python .protocol-state/custom_agent_monitor.py --summary custom-data-analyzer
```

### Check for Anomalies

```bash
python .protocol-state/custom_agent_monitor.py --check-anomalies custom-data-analyzer
```

### Manual Quarantine

```bash
python .protocol-state/custom_agent_monitor.py --quarantine custom-suspicious-agent \
    --reason "User reported unexpected behavior"
```

---

## Audit Log Review

### Audit Log Location

`.protocol-state/authorization/custom-agent-audit.log`

### Log Format

```
2025-12-03T10:30:15 | AGENT_REGISTERED | custom-data-analyzer | First invocation | Tools: read, grep
2025-12-03T10:30:15 | TOOL_GRANTED | custom-data-analyzer | read | DEFAULT_ALLOWED
2025-12-03T10:30:15 | TOOL_GRANTED | custom-data-analyzer | grep | DEFAULT_ALLOWED
2025-12-03T10:30:15 | INVOCATION | custom-data-analyzer | by=user | validated=True | tools_granted=2 | tools_denied=0
2025-12-03T10:45:20 | FILE_MODIFIED | custom-data-analyzer | Hash changed | Old: a3f5... | New: b7e2...
2025-12-03T11:00:00 | TOOL_DENIED | custom-evil-agent | bash | FORBIDDEN
2025-12-03T11:00:00 | AGENT_QUARANTINED | custom-evil-agent | Reason: Attempted to use forbidden tool
```

### Monitoring for Security Events

```bash
# Watch for critical events
tail -f .protocol-state/authorization/custom-agent-audit.log | grep -E "DENIED|QUARANTINED|VIOLATION|CRITICAL"
```

---

## Integration Workflow

### Complete Custom Agent Invocation Workflow

```python
def invoke_custom_agent_safely(agent_name: str, agent_file_path: Path):
    """
    Safely invoke a custom agent with full security checks.

    This implements all security layers:
    - Pre-invocation validation
    - Quarantine check
    - Rate limiting
    - Tool permission filtering
    - Anomaly detection
    - Audit logging
    """

    # Step 1: Pre-invocation validation
    print(f"🔍 Validating custom agent: {agent_name}")
    validation_result = validate_custom_agent(agent_file_path)

    if not validation_result['passed']:
        print(f"❌ Validation failed:")
        for error in validation_result['errors']:
            print(f"  {error}")
        return False

    print("✅ Validation passed")

    # Step 2: Check quarantine status
    is_quarantined, reason = monitor.is_quarantined(agent_name)
    if is_quarantined:
        print(f"🛑 Agent is quarantined: {reason}")
        return False

    # Step 3: Rate limiting
    is_valid, error_msg = monitor.validate_rate_limit(agent_name)
    if not is_valid:
        print(f"⚠️  {error_msg}")
        return False

    # Step 4: Parse agent YAML to get requested tools
    with open(agent_file_path, 'r') as f:
        content = f.read()

    import re
    import yaml
    yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not yaml_match:
        print("❌ No YAML frontmatter found")
        return False

    agent_yaml = yaml.safe_load(yaml_match.group(1))
    requested_tools = agent_yaml.get('tools', [])

    # Step 5: Register invocation (filters tools)
    print(f"📝 Registering invocation...")
    invocation = monitor.register_invocation(
        agent_name=agent_name,
        agent_file_path=agent_file_path,
        invoked_by='user',
        requested_tools=requested_tools,
        validation_result=validation_result,
        config=security_config
    )

    # Step 6: Check tool grants
    if invocation.tools_denied:
        print(f"⚠️  Some tools were denied:")
        for tool in invocation.tools_denied:
            print(f"  - {tool}")

    print(f"✅ Tools granted: {', '.join(invocation.tools_granted)}")

    # Step 7: Anomaly detection
    anomalies = monitor.detect_anomalies(agent_name)
    if anomalies:
        print(f"⚠️  Anomalies detected:")
        for anomaly in anomalies:
            print(f"  - {anomaly}")

    # Step 8: Proceed with invocation
    print(f"✅ Safe to invoke: {agent_name}")
    return True
```

---

## Emergency Procedures

### Quarantine All Custom Agents

```bash
# List all agents
python .protocol-state/custom_agent_monitor.py --list

# Quarantine each one
python .protocol-state/custom_agent_monitor.py --quarantine custom-agent-1 --reason "Emergency lockdown"
python .protocol-state/custom_agent_monitor.py --quarantine custom-agent-2 --reason "Emergency lockdown"
```

### Clear Registry (Nuclear Option)

```bash
# Backup first
cp .protocol-state/custom-agent-registry.json .protocol-state/custom-agent-registry.backup.json

# Clear
rm .protocol-state/custom-agent-registry.json
```

### Review Audit Log for Incidents

```bash
# Search for specific agent
grep "custom-suspicious-agent" .protocol-state/authorization/custom-agent-audit.log

# Find all denied operations
grep "DENIED" .protocol-state/authorization/custom-agent-audit.log

# Find all quarantine events
grep "QUARANTINED" .protocol-state/authorization/custom-agent-audit.log
```

---

## Configuration Reference

### Security Settings in protocol.config.yaml

```yaml
custom_agent_security:
  enabled: true

  registration:
    require_validation: true
    validation_script: "./scripts/validate-custom-agents.py"
    auto_quarantine_on_failure: true
    max_custom_agents: 10

  namespace:
    reserved_names: [yuuji, megumi, nobara, gojo, todo, maki, panda, inumaki, sukuna]
    require_prefix: "custom-"

  tool_permissions:
    custom_agents_default: [read, grep, glob, askuserquestion]
    requires_approval: [write, edit, webfetch, websearch, todowrite]
    forbidden: [bash, task, notebookedit, killshell]

  monitoring:
    enabled: true
    registry_file: ".protocol-state/custom-agent-registry.json"
    audit_log: ".protocol-state/authorization/custom-agent-audit.log"
```

---

## FAQ

**Q: What if user insists on using a quarantined agent?**
A: Explain the security risk. If they persist, they can manually remove quarantine status by editing the registry JSON, but warn them this bypasses safety checks.

**Q: Can custom agents invoke other custom agents?**
A: No. Custom agents cannot use the `task` tool, which is required for agent invocation. Only Gojo can coordinate agent handoffs.

**Q: What if validation script is missing or broken?**
A: Default to DENY. Do not allow custom agent invocation without validation. Log error to audit log.

**Q: How often should I review audit logs?**
A: Include custom agent activity in Trigger 19 intelligence reports. Review logs after any security incident.

---

## Version History

- **v8.10.0** (2025-12-25): Documentation updates
  - Updated version references
  - Enhanced security guidelines
  - Clarified tier enforcement

- **v8.7.0** (2025-12-03): Initial implementation
  - Created validation script
  - Created monitoring system
  - Integrated with Gojo workflows

---

**This guide is authoritative for custom agent security enforcement. Follow these procedures exactly.**
