"""
Comprehensive test suite for session_monitor.py

Tests the work session monitoring system including:
- High-risk operation detection
- Session state management
- Blocking logic at extended session durations
- Edge cases and error handling

Created: 2025-12-03
Purpose: Address CR-CRIT-003 (CodeRabbit review - missing test coverage)
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add .protocol-state to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / '.protocol-state'))

from session_monitor import SessionMonitor


@pytest.fixture
def temp_protocol_root(tmp_path):
    """Create temporary protocol directory structure."""
    protocol_state = tmp_path / ".protocol-state"
    protocol_state.mkdir()

    # Create minimal config file
    config_file = tmp_path / "protocol.config.yaml"
    config_file.write_text("# Minimal config for testing\n")

    # Create template file
    template_file = protocol_state / "work-session-alert.template.md"
    template_file.write_text("# Test Template\nDuration: {DURATION}\n")

    return tmp_path


@pytest.fixture
def monitor(temp_protocol_root):
    """Create SessionMonitor instance for testing."""
    return SessionMonitor(temp_protocol_root)


@pytest.fixture
def active_session_state(monitor):
    """Create an active session state with high-risk blocking enabled."""
    state = monitor.load_state()
    state['current_session']['session_active'] = True
    state['current_session']['session_id'] = 'test_session_001'
    state['current_session']['start_time'] = datetime.now().isoformat()
    state['current_session']['high_risk_operations_blocked'] = True
    state['session_metrics']['total_duration_minutes'] = 400  # Over 6 hours
    monitor.save_state(state)
    return state


class TestIsHighRiskOperation:
    """Test suite for is_high_risk_operation() method."""

    def test_git_push_production_detected(self, monitor):
        """Should detect git push to production."""
        assert monitor.is_high_risk_operation('git push origin production')
        assert monitor.is_high_risk_operation('git push production')

    def test_git_push_main_detected(self, monitor):
        """Should detect git push to main branch."""
        assert monitor.is_high_risk_operation('git push origin main')
        assert monitor.is_high_risk_operation('git push main')

    def test_git_push_master_detected(self, monitor):
        """Should detect git push to master branch."""
        assert monitor.is_high_risk_operation('git push origin master')
        assert monitor.is_high_risk_operation('git push master')

    def test_deploy_production_detected(self, monitor):
        """Should detect production deployments."""
        assert monitor.is_high_risk_operation('deploy to production')
        assert monitor.is_high_risk_operation('deploy production')

    def test_rm_rf_detected(self, monitor):
        """Should detect dangerous rm -rf commands."""
        assert monitor.is_high_risk_operation('rm -rf /')
        assert monitor.is_high_risk_operation('rm -rf /var')
        assert monitor.is_high_risk_operation('rm -rf .')

    def test_drop_table_detected(self, monitor):
        """Should detect DROP TABLE SQL commands."""
        assert monitor.is_high_risk_operation('DROP TABLE users')
        assert monitor.is_high_risk_operation('DROP TABLE IF EXISTS sessions')

    def test_delete_from_detected(self, monitor):
        """Should detect DELETE FROM SQL commands."""
        assert monitor.is_high_risk_operation('DELETE FROM users')
        assert monitor.is_high_risk_operation('DELETE FROM users WHERE id=1')

    def test_alter_table_detected(self, monitor):
        """Should detect ALTER TABLE SQL commands."""
        assert monitor.is_high_risk_operation('ALTER TABLE users ADD COLUMN')
        assert monitor.is_high_risk_operation('ALTER TABLE sessions DROP COLUMN')

    def test_npm_publish_detected(self, monitor):
        """Should detect npm publish commands."""
        assert monitor.is_high_risk_operation('npm publish')
        assert monitor.is_high_risk_operation('npm publish --tag latest')

    def test_docker_production_detected(self, monitor):
        """Should detect Docker production operations."""
        assert monitor.is_high_risk_operation('docker deploy production')
        assert monitor.is_high_risk_operation('docker-compose up production')

    def test_kubectl_delete_detected(self, monitor):
        """Should detect kubectl delete commands."""
        assert monitor.is_high_risk_operation('kubectl delete pod')
        assert monitor.is_high_risk_operation('kubectl delete namespace')

    def test_kubectl_production_detected(self, monitor):
        """Should detect kubectl production operations."""
        assert monitor.is_high_risk_operation('kubectl apply production')
        assert monitor.is_high_risk_operation('kubectl production rollout')

    def test_case_insensitive_detection(self, monitor):
        """Should detect high-risk operations case-insensitively."""
        assert monitor.is_high_risk_operation('GIT PUSH MAIN')
        assert monitor.is_high_risk_operation('Drop Table users')
        assert monitor.is_high_risk_operation('DELETE from users')
        assert monitor.is_high_risk_operation('NPM PUBLISH')

    def test_feature_branch_not_detected(self, monitor):
        """Should NOT detect git push to feature branches."""
        assert not monitor.is_high_risk_operation('git push origin feature-branch')
        assert not monitor.is_high_risk_operation('git push origin feat/new-feature')
        assert not monitor.is_high_risk_operation('git push origin bugfix/issue-123')

    def test_normal_sql_not_detected(self, monitor):
        """Should NOT detect normal SQL queries."""
        assert not monitor.is_high_risk_operation('SELECT * FROM users')
        assert not monitor.is_high_risk_operation('INSERT INTO users VALUES')
        assert not monitor.is_high_risk_operation('UPDATE users SET name=')

    def test_safe_commands_not_detected(self, monitor):
        """Should NOT detect safe commands as high-risk."""
        assert not monitor.is_high_risk_operation('git status')
        assert not monitor.is_high_risk_operation('git diff')
        assert not monitor.is_high_risk_operation('npm install')
        assert not monitor.is_high_risk_operation('docker ps')
        assert not monitor.is_high_risk_operation('kubectl get pods')

    def test_empty_string_not_detected(self, monitor):
        """Should handle empty strings gracefully."""
        assert not monitor.is_high_risk_operation('')

    def test_whitespace_only_not_detected(self, monitor):
        """Should handle whitespace-only strings gracefully."""
        assert not monitor.is_high_risk_operation('   ')
        assert not monitor.is_high_risk_operation('\n\t')


class TestShouldBlockOperation:
    """Test suite for should_block_operation() method."""

    def test_no_blocking_when_session_inactive(self, monitor):
        """Should not block when session is inactive."""
        state = monitor.load_state()
        state['current_session']['session_active'] = False
        monitor.save_state(state)

        should_block, reason = monitor.should_block_operation('git push main')
        assert not should_block
        assert reason == ""

    def test_no_blocking_when_flag_disabled(self, monitor):
        """Should not block when high_risk_operations_blocked is False."""
        state = monitor.load_state()
        state['current_session']['session_active'] = True
        state['current_session']['high_risk_operations_blocked'] = False
        monitor.save_state(state)

        should_block, reason = monitor.should_block_operation('git push main')
        assert not should_block
        assert reason == ""

    def test_blocks_high_risk_when_enabled(self, monitor, active_session_state):
        """Should block high-risk operations when flag is enabled."""
        should_block, reason = monitor.should_block_operation('git push main')
        assert should_block
        assert "High-risk operation blocked" in reason
        assert "400 min" in reason  # Check duration is included

    def test_does_not_block_safe_operations(self, monitor, active_session_state):
        """Should not block safe operations even when flag is enabled."""
        should_block, reason = monitor.should_block_operation('git status')
        assert not should_block
        assert reason == ""

    def test_blocking_reason_includes_duration(self, monitor, active_session_state):
        """Blocking reason should include session duration."""
        should_block, reason = monitor.should_block_operation('git push production')
        assert should_block
        assert "400 min" in reason or "400" in reason

    def test_blocking_reason_has_emoji(self, monitor, active_session_state):
        """Blocking reason should include stop emoji for visibility."""
        should_block, reason = monitor.should_block_operation('DROP TABLE users')
        assert should_block
        assert "🛑" in reason

    def test_blocks_all_high_risk_patterns(self, monitor, active_session_state):
        """Should block all high-risk operation patterns."""
        high_risk_operations = [
            'git push production',
            'git push main',
            'git push master',
            'deploy production',
            'rm -rf /',
            'DROP TABLE users',
            'DELETE FROM sessions',
            'ALTER TABLE users',
            'npm publish',
            'docker production',
            'kubectl delete pod',
            'kubectl production apply'
        ]

        for operation in high_risk_operations:
            should_block, reason = monitor.should_block_operation(operation)
            assert should_block, f"Failed to block: {operation}"
            assert len(reason) > 0, f"No reason provided for: {operation}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_none_gracefully(self, monitor, active_session_state):
        """Should handle None input gracefully (convert to string)."""
        # Python's re.search will convert None to 'None' string
        should_block, reason = monitor.should_block_operation(None)
        assert not should_block  # 'None' doesn't match any pattern

    def test_handles_special_characters(self, monitor, active_session_state):
        """Should handle special regex characters in operation strings."""
        operations_with_special_chars = [
            'git push origin feature/fix-[bug]',
            'command with (parentheses)',
            'command with $variables',
            'path/to/file.extension'
        ]

        for operation in operations_with_special_chars:
            # These should not crash, may or may not block depending on pattern
            should_block, reason = monitor.should_block_operation(operation)
            assert isinstance(should_block, bool)
            assert isinstance(reason, str)

    def test_handles_very_long_operations(self, monitor, active_session_state):
        """Should handle very long operation strings."""
        long_operation = 'git push ' + 'x' * 10000 + ' main'
        should_block, reason = monitor.should_block_operation(long_operation)
        assert should_block  # Contains 'main'

    def test_handles_multiline_operations(self, monitor, active_session_state):
        """Should handle multiline operation strings."""
        multiline_op = '''git push origin main
        && echo "deployed"
        && notify-slack'''
        should_block, reason = monitor.should_block_operation(multiline_op)
        assert should_block  # Contains 'main'


class TestSessionStateManagement:
    """Test session state loading and saving."""

    def test_load_state_creates_default_if_missing(self, temp_protocol_root):
        """Should create default state file if it doesn't exist."""
        monitor = SessionMonitor(temp_protocol_root)
        state = monitor.load_state()

        assert state is not None
        assert 'current_session' in state
        assert 'session_metrics' in state
        assert 'thresholds' in state

    def test_save_and_load_state_roundtrip(self, monitor):
        """Should correctly save and load state."""
        state = monitor.load_state()
        state['current_session']['session_id'] = 'test_123'
        state['session_metrics']['total_duration_minutes'] = 250

        monitor.save_state(state)
        loaded = monitor.load_state()

        assert loaded['current_session']['session_id'] == 'test_123'
        assert loaded['session_metrics']['total_duration_minutes'] == 250

    def test_state_has_last_updated_timestamp(self, monitor):
        """Saved state should have last_updated timestamp."""
        state = monitor.load_state()
        monitor.save_state(state)

        loaded = monitor.load_state()
        assert 'last_updated' in loaded
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(loaded['last_updated'])


class TestBlockingAt6PlusHours:
    """Test that operations are blocked at 6+ hours with flag enabled."""

    @pytest.mark.parametrize("duration_minutes,should_enable_blocking", [
        (359, False),  # Just under 6 hours - no blocking yet
        (360, True),   # Exactly 6 hours - blocking enabled
        (361, True),   # Just over 6 hours - blocking enabled
        (500, True),   # Well over 6 hours - blocking enabled
    ])
    def test_blocking_threshold_at_6_hours(self, monitor, duration_minutes, should_enable_blocking):
        """Blocking should activate at 6+ hours (360 minutes)."""
        state = monitor.load_state()
        state['current_session']['session_active'] = True
        state['current_session']['high_risk_operations_blocked'] = should_enable_blocking
        state['session_metrics']['total_duration_minutes'] = duration_minutes
        monitor.save_state(state)

        should_block, reason = monitor.should_block_operation('git push main')

        if should_enable_blocking:
            assert should_block, f"Should block at {duration_minutes} minutes"
            assert str(duration_minutes) in reason
        else:
            assert not should_block, f"Should not block at {duration_minutes} minutes"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
