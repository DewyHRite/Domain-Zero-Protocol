#!/usr/bin/env python3
"""
Domain Zero Protocol - Custom Agent Monitor Tests
Version: 8.7.0

Comprehensive test suite for custom agent security monitoring and enforcement.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / ".protocol-state"))

from custom_agent_monitor import CustomAgentMonitor, AgentRegistryEntry, AgentInvocation


@pytest.fixture
def temp_protocol_root(tmp_path):
    """Create temporary protocol root directory structure."""
    protocol_state = tmp_path / ".protocol-state"
    protocol_state.mkdir()

    auth_dir = protocol_state / "authorization"
    auth_dir.mkdir()

    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)

    # Create a test agent file
    test_agent = agents_dir / "custom-test.agent.md"
    test_agent.write_text("""---
name: custom-test
description: Test agent
tools: [read, grep]
model: sonnet
---

# Test Agent
""")

    return tmp_path


@pytest.fixture
def monitor(temp_protocol_root):
    """Create CustomAgentMonitor instance."""
    return CustomAgentMonitor(temp_protocol_root)


@pytest.fixture
def sample_config():
    """Sample security configuration."""
    return {
        'tool_permissions': {
            'custom_agents_default': ['read', 'grep', 'glob'],
            'requires_approval': ['edit', 'write'],
            'forbidden': ['bash', 'task']
        }
    }


class TestRegistryOperations:
    """Test registry load/save operations."""

    def test_load_empty_registry(self, monitor):
        """Should return empty dict when registry doesn't exist."""
        registry = monitor.load_registry()
        assert registry == {}

    def test_save_and_load_registry(self, monitor):
        """Should correctly save and load registry."""
        entry = AgentRegistryEntry(
            agent_name='custom-test',
            agent_file_path='/path/to/agent.md',
            first_seen='2025-01-01T00:00:00',
            last_invoked='2025-01-01T00:00:00',
            total_invocations=5
        )

        registry = {'custom-test': entry}
        monitor.save_registry(registry)

        loaded = monitor.load_registry()
        assert 'custom-test' in loaded
        assert loaded['custom-test'].agent_name == 'custom-test'
        assert loaded['custom-test'].total_invocations == 5

    def test_registry_file_created(self, monitor):
        """Registry file should be created on first save."""
        entry = AgentRegistryEntry(
            agent_name='custom-test',
            agent_file_path='/path/to/agent.md',
            first_seen='2025-01-01T00:00:00',
            last_invoked='2025-01-01T00:00:00'
        )

        monitor.save_registry({'custom-test': entry})
        assert monitor.registry_file.exists()


class TestRateLimiting:
    """Test rate limiting with persistence."""

    def test_rate_limit_allows_first_invocation(self, monitor):
        """Should allow first invocation."""
        is_valid, error = monitor.validate_rate_limit('custom-test', max_per_minute=10)
        assert is_valid
        assert error is None

    def test_rate_limit_enforces_max(self, monitor):
        """Should block when max invocations exceeded."""
        agent_name = 'custom-test'
        max_per_minute = 3

        # First 3 should succeed
        for i in range(max_per_minute):
            is_valid, error = monitor.validate_rate_limit(agent_name, max_per_minute)
            assert is_valid, f"Invocation {i+1} should be allowed"

        # 4th should fail
        is_valid, error = monitor.validate_rate_limit(agent_name, max_per_minute)
        assert not is_valid
        assert "Rate limit exceeded" in error

    def test_rate_limit_persists_across_instances(self, temp_protocol_root):
        """Rate limits should persist across monitor instances."""
        agent_name = 'custom-test'

        # First instance - use up rate limit
        monitor1 = CustomAgentMonitor(temp_protocol_root)
        for _ in range(5):
            monitor1.validate_rate_limit(agent_name, max_per_minute=5)

        # Second instance - should still be rate limited
        monitor2 = CustomAgentMonitor(temp_protocol_root)
        is_valid, error = monitor2.validate_rate_limit(agent_name, max_per_minute=5)
        assert not is_valid
        assert "Rate limit exceeded" in error

    def test_rate_limit_clears_old_timestamps(self, monitor, temp_protocol_root):
        """Should remove timestamps older than 1 minute."""
        agent_name = 'custom-test'

        # Create registry entry with old timestamps
        old_time = (datetime.now() - timedelta(minutes=2)).isoformat()
        recent_time = datetime.now().isoformat()

        entry = AgentRegistryEntry(
            agent_name=agent_name,
            agent_file_path='/path/to/agent.md',
            first_seen=old_time,
            last_invoked=recent_time,
            rate_limit_timestamps=[old_time, old_time, recent_time]
        )

        monitor.save_registry({agent_name: entry})

        # Validate rate limit - should only count recent timestamp
        is_valid, error = monitor.validate_rate_limit(agent_name, max_per_minute=5)
        assert is_valid  # Only 1 recent timestamp, so should allow


class TestToolPermissions:
    """Test tool permission validation."""

    def test_grants_default_tools(self, monitor, sample_config):
        """Should grant tools in default allowed list."""
        granted, denied, errors = monitor.validate_tool_permissions(
            'custom-test',
            ['read', 'grep'],
            sample_config
        )

        assert granted == ['read', 'grep']
        assert denied == []
        assert errors == []

    def test_denies_forbidden_tools(self, monitor, sample_config):
        """Should deny forbidden tools."""
        granted, denied, errors = monitor.validate_tool_permissions(
            'custom-test',
            ['bash', 'task'],
            sample_config
        )

        assert granted == []
        assert denied == ['bash', 'task']
        assert len(errors) == 2
        assert "forbidden" in errors[0].lower()

    def test_grants_approval_required_tools(self, monitor, sample_config):
        """Should grant tools requiring approval (with warning)."""
        granted, denied, errors = monitor.validate_tool_permissions(
            'custom-test',
            ['edit', 'write'],
            sample_config
        )

        assert granted == ['edit', 'write']
        assert denied == []
        # No errors, but audit log should have approval warnings

    def test_mixed_tool_permissions(self, monitor, sample_config):
        """Should correctly classify mixed tool list."""
        granted, denied, errors = monitor.validate_tool_permissions(
            'custom-test',
            ['read', 'bash', 'edit', 'unknown'],
            sample_config
        )

        assert 'read' in granted  # default
        assert 'edit' in granted  # requires approval
        assert 'bash' in denied   # forbidden
        assert 'unknown' in denied  # not in allowed list


class TestAgentRegistration:
    """Test agent invocation registration."""

    def test_first_invocation_creates_entry(self, monitor, temp_protocol_root, sample_config):
        """Should create new registry entry for first invocation."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"

        invocation = monitor.register_invocation(
            agent_name='custom-test',
            agent_file_path=agent_path,
            invoked_by='user',
            requested_tools=['read', 'grep'],
            validation_result={'passed': True, 'errors': []},
            config=sample_config
        )

        registry = monitor.load_registry()
        assert 'custom-test' in registry
        assert registry['custom-test'].total_invocations == 1
        assert registry['custom-test'].tools_used == {'read': 1, 'grep': 1}

    def test_subsequent_invocations_increment_count(self, monitor, temp_protocol_root, sample_config):
        """Should increment invocation count."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"

        # First invocation
        monitor.register_invocation(
            agent_name='custom-test',
            agent_file_path=agent_path,
            invoked_by='user',
            requested_tools=['read'],
            validation_result={'passed': True, 'errors': []},
            config=sample_config
        )

        # Second invocation
        monitor.register_invocation(
            agent_name='custom-test',
            agent_file_path=agent_path,
            invoked_by='user',
            requested_tools=['grep'],
            validation_result={'passed': True, 'errors': []},
            config=sample_config
        )

        registry = monitor.load_registry()
        assert registry['custom-test'].total_invocations == 2
        assert registry['custom-test'].tools_used['read'] == 1
        assert registry['custom-test'].tools_used['grep'] == 1

    def test_tracks_validation_failures(self, monitor, temp_protocol_root, sample_config):
        """Should track validation failures."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"

        monitor.register_invocation(
            agent_name='custom-test',
            agent_file_path=agent_path,
            invoked_by='user',
            requested_tools=['read'],
            validation_result={'passed': False, 'errors': ['Name collision']},
            config=sample_config
        )

        registry = monitor.load_registry()
        assert registry['custom-test'].validation_failures == 1


class TestFileIntegrity:
    """Test file hash tracking and modification detection."""

    def test_computes_file_hash(self, monitor, temp_protocol_root):
        """Should compute SHA-256 hash of file."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"
        file_hash = monitor.compute_file_hash(agent_path)

        assert file_hash is not None
        assert len(file_hash) == 64  # SHA-256 hex digest

    def test_detects_file_modifications(self, monitor, temp_protocol_root, sample_config):
        """Should detect when agent file is modified."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"

        # First invocation
        monitor.register_invocation(
            agent_name='custom-test',
            agent_file_path=agent_path,
            invoked_by='user',
            requested_tools=['read'],
            validation_result={'passed': True, 'errors': []},
            config=sample_config
        )

        # Modify file
        agent_path.write_text("Modified content")

        # Second invocation
        monitor.register_invocation(
            agent_name='custom-test',
            agent_file_path=agent_path,
            invoked_by='user',
            requested_tools=['read'],
            validation_result={'passed': True, 'errors': []},
            config=sample_config
        )

        registry = monitor.load_registry()
        assert registry['custom-test'].hash_changed_count == 1


class TestQuarantine:
    """Test agent quarantine functionality."""

    def test_quarantine_marks_agent(self, monitor):
        """Should mark agent as quarantined."""
        # Create initial registry entry
        entry = AgentRegistryEntry(
            agent_name='custom-malicious',
            agent_file_path='/path/to/agent.md',
            first_seen='2025-01-01T00:00:00',
            last_invoked='2025-01-01T00:00:00'
        )
        monitor.save_registry({'custom-malicious': entry})

        # Quarantine
        monitor.quarantine_agent('custom-malicious', 'Suspicious activity detected')

        registry = monitor.load_registry()
        assert registry['custom-malicious'].quarantined is True
        assert 'Suspicious activity' in registry['custom-malicious'].quarantine_reason

    def test_is_quarantined_check(self, monitor):
        """Should correctly identify quarantined agents."""
        entry = AgentRegistryEntry(
            agent_name='custom-bad',
            agent_file_path='/path/to/agent.md',
            first_seen='2025-01-01T00:00:00',
            last_invoked='2025-01-01T00:00:00',
            quarantined=True
        )
        monitor.save_registry({'custom-bad': entry})

        assert monitor.is_quarantined('custom-bad') is True
        assert monitor.is_quarantined('custom-good') is False


class TestAnomalyDetection:
    """Test anomaly detection functionality."""

    def test_detects_rate_limit_anomaly(self, monitor):
        """Should detect rate limit violations as anomalies."""
        agent_name = 'custom-test'

        # Exceed rate limit
        for _ in range(15):
            monitor.validate_rate_limit(agent_name, max_per_minute=10)

        anomalies = monitor.detect_anomalies()

        # Should have anomaly for this agent
        assert len(anomalies) > 0

    def test_detects_validation_failure_anomaly(self, monitor, temp_protocol_root, sample_config):
        """Should detect multiple validation failures."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"

        # Register multiple failed validations
        for _ in range(5):
            monitor.register_invocation(
                agent_name='custom-test',
                agent_file_path=agent_path,
                invoked_by='user',
                requested_tools=['bash'],  # forbidden tool
                validation_result={'passed': False, 'errors': ['Forbidden tool']},
                config=sample_config
            )

        anomalies = monitor.detect_anomalies()
        assert len(anomalies) > 0

        # Check for validation failure anomaly
        validation_anomalies = [a for a in anomalies if 'validation' in a.lower()]
        assert len(validation_anomalies) > 0


class TestInvocationHistory:
    """Test invocation history tracking."""

    def test_keeps_last_10_invocations(self, monitor, temp_protocol_root, sample_config):
        """Should keep only last 10 invocations in history."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"

        # Register 15 invocations
        for i in range(15):
            monitor.register_invocation(
                agent_name='custom-test',
                agent_file_path=agent_path,
                invoked_by='user',
                requested_tools=['read'],
                validation_result={'passed': True, 'errors': []},
                config=sample_config
            )

        registry = monitor.load_registry()
        assert len(registry['custom-test'].invocation_history) == 10


class TestAuditLogging:
    """Test audit logging functionality."""

    def test_audit_log_created(self, monitor):
        """Audit log file should be created."""
        assert monitor.audit_log_file.exists()

    def test_logs_invocation(self, monitor, temp_protocol_root, sample_config):
        """Should log invocations to audit file."""
        agent_path = temp_protocol_root / ".claude" / "agents" / "custom-test.agent.md"

        monitor.register_invocation(
            agent_name='custom-test',
            agent_file_path=agent_path,
            invoked_by='user',
            requested_tools=['read'],
            validation_result={'passed': True, 'errors': []},
            config=sample_config
        )

        # Check audit log contains invocation
        log_content = monitor.audit_log_file.read_text()
        assert 'INVOCATION' in log_content
        assert 'custom-test' in log_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
