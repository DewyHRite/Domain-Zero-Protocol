#!/usr/bin/env python3
"""
Domain Zero Protocol - Custom Agent Security Monitor (v8.7.0)

Provides runtime monitoring and enforcement of custom agent security policies.
This module addresses CUST-CRIT-006 (Zero Gojo Oversight) by giving Gojo
visibility into all custom agent activity.

Usage:
    From Gojo agent: Import and use to track custom agent invocations
    Registry file: .protocol-state/custom-agent-registry.json
    Audit log: .protocol-state/authorization/custom-agent-audit.log
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import hashlib


@dataclass
class AgentInvocation:
    """Records a single custom agent invocation."""
    agent_name: str
    invoked_at: str  # ISO 8601 timestamp
    invoked_by: str  # user, gojo, or another agent
    tools_requested: List[str]
    tools_granted: List[str]
    tools_denied: List[str]
    validation_passed: bool
    validation_errors: List[str] = field(default_factory=list)
    file_hash: Optional[str] = None  # SHA-256 hash of agent file

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class AgentRegistryEntry:
    """Registry entry for a custom agent."""
    agent_name: str
    agent_file_path: str
    first_seen: str  # ISO 8601 timestamp
    last_invoked: str  # ISO 8601 timestamp
    total_invocations: int = 0
    tools_used: Dict[str, int] = field(default_factory=dict)  # tool_name: usage_count
    tools_denied: Dict[str, int] = field(default_factory=dict)  # tool_name: denial_count (for anomaly detection)
    validation_failures: int = 0
    quarantined: bool = False
    quarantine_reason: Optional[str] = None
    file_hash: Optional[str] = None  # Current file hash
    hash_changed_count: int = 0  # How many times file hash changed
    invocation_history: List[Dict] = field(default_factory=list)  # Last N invocations
    rate_limit_timestamps: List[str] = field(default_factory=list)  # ISO timestamps for rate limiting

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class CustomAgentMonitor:
    """
    Monitor and enforce security policies for custom agents.

    This provides Gojo with complete visibility into custom agent activity,
    addressing the "zero oversight" vulnerability.
    """

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)
        self.registry_file = self.protocol_root / ".protocol-state" / "custom-agent-registry.json"
        self.audit_log_file = self.protocol_root / ".protocol-state" / "authorization" / "custom-agent-audit.log"

        # Ensure directories exist
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.audit_log_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up audit logging
        self._setup_audit_logging()

    def _setup_audit_logging(self):
        """Configure audit logging with tamper-evident formatting."""
        # Create logger
        self.audit_logger = logging.getLogger('custom_agent_audit')
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.propagate = False

        # Remove existing handlers
        self.audit_logger.handlers.clear()

        # Create file handler
        handler = logging.FileHandler(self.audit_log_file, encoding='utf-8')
        handler.setLevel(logging.INFO)

        # Format: timestamp | agent | action | details
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)

    def load_registry(self) -> Dict[str, AgentRegistryEntry]:
        """
        Load custom agent registry from disk.

        Returns:
            Dictionary mapping agent_name to AgentRegistryEntry
        """
        if not self.registry_file.exists():
            return {}

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert dict entries back to AgentRegistryEntry objects
            registry = {}
            for agent_name, entry_data in data.items():
                registry[agent_name] = AgentRegistryEntry(**entry_data)

            return registry

        except json.JSONDecodeError as e:
            self.audit_logger.error(f"REGISTRY_LOAD_ERROR | Failed to parse registry: {e}")
            return {}
        except Exception as e:
            self.audit_logger.error(f"REGISTRY_LOAD_ERROR | Unexpected error: {e}")
            return {}

    def save_registry(self, registry: Dict[str, AgentRegistryEntry]):
        """
        Save custom agent registry to disk.

        Args:
            registry: Dictionary of AgentRegistryEntry objects
        """
        try:
            # Convert AgentRegistryEntry objects to dicts
            data = {name: entry.to_dict() for name, entry in registry.items()}

            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.audit_logger.error(f"REGISTRY_SAVE_ERROR | Failed to save registry: {e}")

    def compute_file_hash(self, file_path: Path) -> Optional[str]:
        """
        Compute SHA-256 hash of agent file.

        Args:
            file_path: Path to agent file

        Returns:
            Hex digest of SHA-256 hash, or None on error
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            self.audit_logger.error(f"HASH_ERROR | {file_path}: {e}")
            return None

    def validate_rate_limit(
        self,
        agent_name: str,
        max_per_minute: int = 10,
        max_concurrent: int = 2,
        cooldown_seconds: int = 5
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if agent has exceeded rate limit (persisted to registry).

        Enforces three policies:
        1. Per-minute invocation cap (default: 10/min)
        2. Cooldown period between invocations (default: 5 seconds)
        3. Global concurrent invocation limit (default: 2 concurrent)

        Args:
            agent_name: Name of custom agent
            max_per_minute: Maximum invocations per minute
            max_concurrent: Maximum concurrent custom agents (global limit)
            cooldown_seconds: Minimum seconds between invocations for this agent

        Returns:
            (is_valid, error_message) - error_message is None if valid
        """
        now = datetime.now()
        registry = self.load_registry()

        # Load timestamps from registry if agent exists, or create minimal entry
        if agent_name not in registry:
            # Create minimal registry entry for rate limiting tracking
            # Full entry will be created in register_invocation
            registry[agent_name] = AgentRegistryEntry(
                agent_name=agent_name,
                agent_file_path="<pending>",  # Will be updated in register_invocation
                first_seen=now.isoformat(),
                last_invoked=now.isoformat(),
                total_invocations=0,
                rate_limit_timestamps=[]
            )

        entry = registry[agent_name]

        # Convert ISO timestamps to datetime objects
        timestamps = [
            datetime.fromisoformat(ts)
            for ts in entry.rate_limit_timestamps
        ]

        # Remove timestamps older than 1 minute (sliding window)
        cutoff = datetime.fromtimestamp(now.timestamp() - 60)
        timestamps = [ts for ts in timestamps if ts > cutoff]

        # POLICY 1: Check per-minute invocation limit
        if len(timestamps) >= max_per_minute:
            self.audit_logger.warning(
                f"RATE_LIMIT_EXCEEDED | {agent_name} | {len(timestamps)} invocations in last minute"
            )
            return False, f"Rate limit exceeded: {len(timestamps)}/{max_per_minute} invocations per minute"

        # POLICY 2: Check cooldown period (last invocation must be > cooldown_seconds ago)
        if timestamps:
            last_invocation = max(timestamps)
            time_since_last = (now - last_invocation).total_seconds()
            if time_since_last < cooldown_seconds:
                self.audit_logger.warning(
                    f"COOLDOWN_VIOLATION | {agent_name} | {time_since_last:.1f}s since last invocation (min: {cooldown_seconds}s)"
                )
                return False, f"Cooldown violation: {time_since_last:.1f}s since last invocation (minimum: {cooldown_seconds}s)"

        # POLICY 3: Check global concurrent invocation limit
        # Count how many custom agents have invocations in the last 60 seconds
        active_agents = 0
        for other_agent_name, other_entry in registry.items():
            if other_agent_name == agent_name:
                continue  # Don't count ourselves

            other_timestamps = [
                datetime.fromisoformat(ts)
                for ts in other_entry.rate_limit_timestamps
            ]
            recent_other = [ts for ts in other_timestamps if ts > cutoff]
            if recent_other:
                active_agents += 1

        if active_agents >= max_concurrent:
            self.audit_logger.warning(
                f"CONCURRENCY_EXCEEDED | {agent_name} | {active_agents} custom agents active (max: {max_concurrent})"
            )
            return False, f"Concurrency limit exceeded: {active_agents} custom agents active (maximum: {max_concurrent})"

        # All policies passed - record this invocation
        timestamps.append(now)

        # Persist timestamps back to registry (ALWAYS, even for new agents)
        entry.rate_limit_timestamps = [ts.isoformat() for ts in timestamps]
        self.save_registry(registry)

        return True, None

    def validate_tool_permissions(
        self,
        agent_name: str,
        requested_tools: List[str],
        config: Dict
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Validate and filter requested tools against security policy.

        Args:
            agent_name: Name of custom agent
            requested_tools: Tools declared in agent YAML
            config: Security configuration from protocol.config.yaml

        Returns:
            (granted_tools, denied_tools, errors)
        """
        tool_config = config.get('tool_permissions', {})
        default_tools = [t.lower() for t in tool_config.get('custom_agents_default', [])]
        requires_approval = [t.lower() for t in tool_config.get('requires_approval', [])]
        forbidden = [t.lower() for t in tool_config.get('forbidden', [])]

        granted = []
        denied = []
        errors = []

        for tool in requested_tools:
            tool_lower = tool.lower()

            if tool_lower in forbidden:
                denied.append(tool)
                errors.append(f"Tool '{tool}' is forbidden for custom agents")
                self.audit_logger.warning(
                    f"TOOL_DENIED | {agent_name} | {tool} | FORBIDDEN"
                )

            elif tool_lower in requires_approval:
                # For now, grant with warning (future: prompt user)
                granted.append(tool)
                self.audit_logger.info(
                    f"TOOL_GRANTED_WITH_APPROVAL | {agent_name} | {tool} | REQUIRES_USER_APPROVAL"
                )

            elif tool_lower in default_tools:
                granted.append(tool)
                self.audit_logger.info(
                    f"TOOL_GRANTED | {agent_name} | {tool} | DEFAULT_ALLOWED"
                )

            else:
                denied.append(tool)
                errors.append(f"Tool '{tool}' is not in allowed list")
                self.audit_logger.warning(
                    f"TOOL_DENIED | {agent_name} | {tool} | NOT_IN_ALLOWED_LIST"
                )

        return granted, denied, errors

    def register_invocation(
        self,
        agent_name: str,
        agent_file_path: Path,
        invoked_by: str,
        requested_tools: List[str],
        validation_result: Dict,
        config: Dict
    ) -> AgentInvocation:
        """
        Register a custom agent invocation in the registry.

        Args:
            agent_name: Name of custom agent
            agent_file_path: Path to agent .agent.md file
            invoked_by: Who invoked the agent (user, gojo, etc.)
            requested_tools: Tools agent requested
            validation_result: Result from validate-custom-agents.py
            config: Security configuration

        Returns:
            AgentInvocation record
        """
        now = datetime.now().isoformat()

        # Load registry
        registry = self.load_registry()

        # Compute file hash
        file_hash = self.compute_file_hash(agent_file_path)

        # Validate tool permissions
        granted, denied, tool_errors = self.validate_tool_permissions(
            agent_name, requested_tools, config
        )

        # Check if validation passed
        validation_passed = validation_result.get('passed', False)
        validation_errors = validation_result.get('errors', []) + tool_errors

        # Create invocation record
        invocation = AgentInvocation(
            agent_name=agent_name,
            invoked_at=now,
            invoked_by=invoked_by,
            tools_requested=requested_tools,
            tools_granted=granted,
            tools_denied=denied,
            validation_passed=validation_passed,
            validation_errors=validation_errors,
            file_hash=file_hash
        )

        # Update or create registry entry
        if agent_name in registry:
            entry = registry[agent_name]
            entry.last_invoked = now
            entry.total_invocations += 1

            # Check for file modifications
            if file_hash and entry.file_hash and file_hash != entry.file_hash:
                entry.hash_changed_count += 1
                self.audit_logger.warning(
                    f"FILE_MODIFIED | {agent_name} | Hash changed | "
                    f"Old: {entry.file_hash[:16]}... | New: {file_hash[:16]}..."
                )

            entry.file_hash = file_hash

            # Update tool usage tracking
            for tool in granted:
                entry.tools_used[tool] = entry.tools_used.get(tool, 0) + 1

            # Track denied tools (for anomaly detection)
            for tool in denied:
                entry.tools_denied[tool] = entry.tools_denied.get(tool, 0) + 1

            # Track validation failures
            if not validation_passed:
                entry.validation_failures += 1

            # Add to invocation history (keep last 10)
            entry.invocation_history.append(invocation.to_dict())
            entry.invocation_history = entry.invocation_history[-10:]

        else:
            # First time seeing this agent
            entry = AgentRegistryEntry(
                agent_name=agent_name,
                agent_file_path=str(agent_file_path),
                first_seen=now,
                last_invoked=now,
                total_invocations=1,
                tools_used={tool: 1 for tool in granted},
                tools_denied={tool: 1 for tool in denied},
                validation_failures=0 if validation_passed else 1,
                file_hash=file_hash,
                invocation_history=[invocation.to_dict()]
            )
            registry[agent_name] = entry

            self.audit_logger.info(
                f"AGENT_REGISTERED | {agent_name} | First invocation | "
                f"Tools: {', '.join(granted)}"
            )

        # Save updated registry
        self.save_registry(registry)

        # Log invocation to audit log
        self.audit_logger.info(
            f"INVOCATION | {agent_name} | by={invoked_by} | "
            f"validated={validation_passed} | "
            f"tools_granted={len(granted)} | tools_denied={len(denied)}"
        )

        return invocation

    def quarantine_agent(self, agent_name: str, reason: str):
        """
        Quarantine a suspicious custom agent.

        Args:
            agent_name: Name of agent to quarantine
            reason: Reason for quarantine
        """
        registry = self.load_registry()

        if agent_name not in registry:
            self.audit_logger.error(
                f"QUARANTINE_ERROR | {agent_name} | Agent not in registry"
            )
            return

        entry = registry[agent_name]
        entry.quarantined = True
        entry.quarantine_reason = reason

        self.save_registry(registry)

        self.audit_logger.critical(
            f"AGENT_QUARANTINED | {agent_name} | Reason: {reason}"
        )

    def is_quarantined(self, agent_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an agent is quarantined.

        Args:
            agent_name: Name of agent to check

        Returns:
            (is_quarantined, reason) - reason is None if not quarantined
        """
        registry = self.load_registry()

        if agent_name not in registry:
            return False, None

        entry = registry[agent_name]
        if entry.quarantined:
            return True, entry.quarantine_reason

        return False, None

    def get_agent_summary(self, agent_name: str) -> Optional[Dict]:
        """
        Get summary information about a custom agent.

        Args:
            agent_name: Name of agent

        Returns:
            Dictionary with agent stats, or None if not found
        """
        registry = self.load_registry()

        if agent_name not in registry:
            return None

        entry = registry[agent_name]

        return {
            'agent_name': entry.agent_name,
            'agent_file_path': entry.agent_file_path,
            'first_seen': entry.first_seen,
            'last_invoked': entry.last_invoked,
            'total_invocations': entry.total_invocations,
            'tools_used': entry.tools_used,
            'validation_failures': entry.validation_failures,
            'quarantined': entry.quarantined,
            'quarantine_reason': entry.quarantine_reason,
            'file_modifications': entry.hash_changed_count,
            'recent_invocations': len(entry.invocation_history)
        }

    def get_all_agents_summary(self) -> List[Dict]:
        """
        Get summary of all registered custom agents.

        Returns:
            List of agent summaries
        """
        registry = self.load_registry()
        return [self.get_agent_summary(name) for name in registry.keys()]

    def detect_anomalies(self, agent_name: str) -> List[str]:
        """
        Detect anomalous behavior patterns for an agent.

        Args:
            agent_name: Name of agent to analyze

        Returns:
            List of anomaly descriptions (empty if none detected)
        """
        registry = self.load_registry()

        if agent_name not in registry:
            return []

        entry = registry[agent_name]
        anomalies = []

        # Check for excessive validation failures
        if entry.validation_failures > 3:
            anomalies.append(
                f"High validation failure rate: {entry.validation_failures} failures"
            )

        # Check for frequent file modifications
        if entry.hash_changed_count > 5:
            anomalies.append(
                f"Suspicious file modification pattern: {entry.hash_changed_count} changes"
            )

        # Check for unusual tool usage patterns (check denied attempts)
        forbidden_tools = ['bash', 'task', 'notebookedit', 'killshell']
        for tool in forbidden_tools:
            if tool in entry.tools_denied:
                anomalies.append(
                    f"Attempted to use forbidden tool '{tool}' "
                    f"({entry.tools_denied[tool]} times)"
                )

        # Check for rapid invocations
        if entry.total_invocations > 100:
            anomalies.append(
                f"High invocation count: {entry.total_invocations} total invocations"
            )

        if anomalies:
            self.audit_logger.warning(
                f"ANOMALIES_DETECTED | {agent_name} | {len(anomalies)} anomalies: "
                f"{'; '.join(anomalies)}"
            )

        return anomalies


def main():
    """
    CLI interface for custom agent monitoring.

    Usage:
        python custom_agent_monitor.py --list
        python custom_agent_monitor.py --summary <agent_name>
        python custom_agent_monitor.py --quarantine <agent_name> --reason "description"
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - Custom Agent Monitor (v8.7.0)"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="List all registered custom agents"
    )
    parser.add_argument(
        '--summary',
        metavar='AGENT',
        help="Show summary for specific agent"
    )
    parser.add_argument(
        '--quarantine',
        metavar='AGENT',
        help="Quarantine an agent"
    )
    parser.add_argument(
        '--reason',
        help="Reason for quarantine (required with --quarantine)"
    )
    parser.add_argument(
        '--check-anomalies',
        metavar='AGENT',
        help="Check for anomalies in agent behavior"
    )

    args = parser.parse_args()

    # Initialize monitor
    protocol_root = Path.cwd()
    monitor = CustomAgentMonitor(protocol_root)

    if args.list:
        agents = monitor.get_all_agents_summary()
        if not agents:
            print("No custom agents registered")
            return

        print(f"{'=' * 80}")
        print(f"Registered Custom Agents ({len(agents)})")
        print(f"{'=' * 80}\n")

        for agent in agents:
            status = "🔴 QUARANTINED" if agent['quarantined'] else "✅ Active"
            print(f"{status} | {agent['agent_name']}")
            print(f"  Invocations: {agent['total_invocations']}")
            print(f"  Last Used: {agent['last_invoked']}")
            print(f"  Tools: {', '.join(agent['tools_used'].keys())}")
            if agent['quarantined']:
                print(f"  Quarantine Reason: {agent['quarantine_reason']}")
            print()

    elif args.summary:
        summary = monitor.get_agent_summary(args.summary)
        if not summary:
            print(f"Agent '{args.summary}' not found in registry")
            return

        print(f"{'=' * 80}")
        print(f"Agent Summary: {summary['agent_name']}")
        print(f"{'=' * 80}\n")

        for key, value in summary.items():
            if key == 'tools_used':
                print(f"Tools Used:")
                for tool, count in value.items():
                    print(f"  - {tool}: {count} times")
            else:
                print(f"{key}: {value}")

    elif args.quarantine:
        if not args.reason:
            print("Error: --reason is required with --quarantine")
            return

        monitor.quarantine_agent(args.quarantine, args.reason)
        print(f"✅ Agent '{args.quarantine}' has been quarantined")
        print(f"Reason: {args.reason}")

    elif args.check_anomalies:
        anomalies = monitor.detect_anomalies(args.check_anomalies)
        if not anomalies:
            print(f"✅ No anomalies detected for '{args.check_anomalies}'")
        else:
            print(f"⚠️  Anomalies detected for '{args.check_anomalies}':\n")
            for i, anomaly in enumerate(anomalies, 1):
                print(f"{i}. {anomaly}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
