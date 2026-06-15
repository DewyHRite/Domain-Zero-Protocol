#!/usr/bin/env python3
"""
Domain Zero Protocol - Work Session Monitoring System
Version: 9.3.0
Purpose: Actual implementation of work session tracking and safety alerts

This module provides REAL enforcement of work session monitoring, replacing
the prompt-based theater identified by Sukuna's red team assessment.

Usage:
    From Gojo agent: Read and execute functions to track session state
    From verification scripts: Validate session health and issue alerts
"""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# PATCH-STATE-001: Import centralized state manager
try:
    from project_state_manager import ProjectStateManager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False
    # Silent fallback to legacy file I/O for backward compatibility

# Session duration limits (PATCH-SEC-005 - SEC-DZP-008 remediation)
MAX_BREAK_DURATION = 480  # 8 hours
MIN_BREAK_DURATION = 1    # 1 minute
MAX_SESSION_DURATION = 1440  # 24 hours


def _parse_utc(timestamp: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO-8601 timestamp string and return a timezone-AWARE datetime in UTC.

    BUG-SESSION-001 (v9.3.0): Centralized timestamp parsing for the safety path.
    Legacy / pre-9.x state files (and externally edited state) can carry naive
    timestamps with no UTC offset (e.g. "2026-02-14T21:51:18.445590"). Subtracting
    a naive datetime from an aware `datetime.now(timezone.utc)` raises
    `TypeError: can't subtract offset-naive and offset-aware datetimes`, which used
    to crash `check_alert_needed()` and silently DISABLE the wellbeing safety check.

    This helper normalizes every parse: naive -> assume UTC; aware -> convert to UTC.
    Returns None if the string is missing or unparseable (callers treat None as
    "no usable timestamp" rather than crashing).

    Note: `datetime.fromisoformat()` on Python 3.11+ accepts a trailing 'Z'; on
    older versions it does not, so we normalize 'Z' to '+00:00' defensively.
    """
    if not timestamp:
        return None
    try:
        normalized = timestamp.strip()
        if normalized.endswith('Z'):
            normalized = normalized[:-1] + '+00:00'
        dt = datetime.fromisoformat(normalized)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


class SessionMonitor:
    """
    Work session monitoring with real time tracking and enforcement.
    """

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)

        # PATCH-STATE-001: Initialize centralized state manager
        if STATE_MANAGER_AVAILABLE:
            self.state_manager = ProjectStateManager(protocol_root)
        else:
            self.state_manager = None

        # Legacy file paths (kept for backward compatibility)
        self.state_file = self.protocol_root / ".protocol-state" / "session-state.json"
        self.template_file = self.protocol_root / ".protocol-state" / "work-session-alert.template.md"
        self.config_file = self.protocol_root / "protocol.config.yaml"
        self.invocation_tracker_file = self.protocol_root / ".protocol-state" / "agent-invocation-tracker.json"

        # Load high-risk operation literals (no regex, safer and faster)
        self._high_risk_literals = self._load_high_risk_literals()

        # Load configuration (v8.13.0 - Configuration Enhancements)
        self.enabled = self._load_enabled_flag()
        self.alert_thresholds = self._load_alert_thresholds()
        self.alert_customization = self._load_alert_customization()

        self._ensure_state_file()

    def _check_gojo_invocation(self) -> bool:
        """
        Check if current invocation is from Gojo agent.

        EXTENSION 3: Permission System (PATCH-SESSION-005)
        Domain.record.md should only be updated when invoked by Gojo to maintain
        strategic protocol integrity. Other agents/users can update other state files.

        Returns:
            True if invoked by Gojo (DZP_AGENT=gojo env var), False otherwise
        """
        return os.environ.get('DZP_AGENT', '').lower() == 'gojo'

    def _load_high_risk_literals(self) -> List[str]:
        """
        Load high-risk operation literal strings from config file.

        Uses literal string matching instead of regex to avoid ReDoS vulnerabilities.
        Matching is case-insensitive via .lower() comparison.

        Returns:
            List of lowercase literal strings to match
        """
        # Default fallback literals (safe, no regex)
        # Each entry is a substring; if it appears anywhere in the command (case-insensitive)
        # the command is classified as high-risk.  Short-form variants (without 'origin')
        # are intentionally included alongside the long-form equivalents so that both
        # 'git push main' and 'git push origin main' are caught.
        default_literals = [
            # git push — long form (with remote name)
            'git push origin production',
            'git push origin main',
            'git push origin master',
            # git push — short form (without remote name, still high-risk)
            'git push production',
            'git push main',
            'git push master',
            # git push — force flags
            'git push --force',
            'git push -f',
            # deploy variants
            'deploy to production',
            'deploy production',
            'deploy --production',
            # destructive filesystem
            'rm -rf',
            # SQL DDL / DML
            'drop table',
            'drop database',
            'delete from',
            'alter table',
            'truncate table',
            # package publishing
            'npm publish',
            # container / orchestration
            'docker push',
            'docker production',
            'docker-compose up production',
            'docker-compose production',
            'kubectl delete',
            'kubectl delete namespace',
            'kubectl production',
            'kubectl apply production',
            # infrastructure-as-code
            'terraform destroy',
            'terraform apply -auto-approve',
            # cloud platform destructive ops
            'heroku destroy',
            'firebase delete',
            'aws s3 rm',
            'gcloud delete',
        ]

        # Try to load literals from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Extract literals from config
                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                high_risk_ops = session_tracking.get('high_risk_operations', {})
                configured_literals = high_risk_ops.get('literals', [])

                if configured_literals:
                    # Return configured literals (lowercase for case-insensitive matching)
                    return [lit.lower() for lit in configured_literals]

            except Exception as e:
                # Silent fallback to defaults (no warning spam)
                pass

        # Fall back to defaults if config unavailable or empty
        return default_literals

    def _load_debounce_config(self, cli_override: int = None) -> int:
        """
        Load debounce threshold from config file or CLI argument.

        Debounce prevents alert spam by skipping alerts if last alert was < threshold ago.
        v8.13.0 - PATCH-SESSION-004

        Args:
            cli_override: CLI --debounce argument (takes precedence)

        Returns:
            Debounce threshold in minutes (default: 30, range: 15-60)
        """
        # CLI argument takes precedence
        if cli_override is not None:
            # Validate range
            if 15 <= cli_override <= 60:
                return cli_override
            else:
                print(f"[!] Invalid debounce value {cli_override}. Must be 15-60 minutes.")
                print(f"    Falling back to default: 30 minutes")
                return 30

        # Try to load from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                debounce_threshold = session_tracking.get('debounce_threshold_minutes')

                if debounce_threshold is not None:
                    # Validate range
                    if 15 <= debounce_threshold <= 60:
                        return debounce_threshold
                    else:
                        print(f"[!] Invalid debounce_threshold_minutes in config: {debounce_threshold}")
                        print(f"    Must be 15-60. Falling back to default: 30 minutes")
                        return 30

            except Exception as e:
                # Silent fallback to default
                pass

        # Default fallback
        return 30

    def _load_enabled_flag(self) -> bool:
        """
        Load session monitoring enabled flag from protocol.config.yaml.

        v8.13.0 - Configuration Enhancement
        Master toggle for session monitoring system.

        Returns:
            True if session monitoring is enabled, False otherwise (default: True)
        """
        # Default: enabled
        default = True

        # Try to load from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                enabled = session_tracking.get('enabled')

                if enabled is not None:
                    return bool(enabled)

            except Exception as e:
                # Silent fallback to default
                pass

        # Default fallback
        return default

    def _load_alert_thresholds(self) -> Dict:
        """
        Load alert threshold configuration from protocol.config.yaml.

        v8.13.0 - Configuration Enhancement
        Allows customization of when session alerts are issued.

        Returns:
            Dict with threshold values in minutes:
            {
                'initial_alert_minutes': 240,      # 4 hours
                'critical_session_minutes': 360,   # 6 hours
                'max_continuous_minutes': 480,     # 8 hours
                'escalated_alert_minutes': 45      # 45 minutes
            }
        """
        # Default thresholds (fallback if config unavailable)
        defaults = {
            'initial_alert_minutes': 240,      # 4 hours
            'critical_session_minutes': 360,   # 6 hours
            'max_continuous_minutes': 480,     # 8 hours
            'escalated_alert_minutes': 45      # 45 minutes
        }

        # Try to load from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                alert_thresholds = session_tracking.get('alert_thresholds', {})

                if alert_thresholds:
                    # Extract and validate each threshold
                    result = {}

                    # initial_alert_hours (2-12 range)
                    initial_hours = alert_thresholds.get('initial_alert_hours', 4)
                    if 2 <= initial_hours <= 12:
                        result['initial_alert_minutes'] = initial_hours * 60
                    else:
                        print(f"[!] Invalid initial_alert_hours: {initial_hours}. Must be 2-12. Using default: 4")
                        result['initial_alert_minutes'] = 240

                    # critical_session_hours (4-16 range)
                    critical_hours = alert_thresholds.get('critical_session_hours', 6)
                    if 4 <= critical_hours <= 16:
                        result['critical_session_minutes'] = critical_hours * 60
                    else:
                        print(f"[!] Invalid critical_session_hours: {critical_hours}. Must be 4-16. Using default: 6")
                        result['critical_session_minutes'] = 360

                    # max_continuous_hours (6-24 range)
                    max_hours = alert_thresholds.get('max_continuous_hours', 8)
                    if 6 <= max_hours <= 24:
                        result['max_continuous_minutes'] = max_hours * 60
                    else:
                        print(f"[!] Invalid max_continuous_hours: {max_hours}. Must be 6-24. Using default: 8")
                        result['max_continuous_minutes'] = 480

                    # escalated_alert_minutes (15-120 range)
                    escalated_mins = alert_thresholds.get('escalated_alert_minutes', 45)
                    if 15 <= escalated_mins <= 120:
                        result['escalated_alert_minutes'] = escalated_mins
                    else:
                        print(f"[!] Invalid escalated_alert_minutes: {escalated_mins}. Must be 15-120. Using default: 45")
                        result['escalated_alert_minutes'] = 45

                    return result

            except Exception as e:
                # Silent fallback to defaults
                pass

        # Default fallback
        return defaults

    def _load_alert_customization(self) -> Dict:
        """
        Load custom alert messages from protocol.config.yaml.

        v8.13.0 - Configuration Enhancement
        Allows customization of alert messages for company/team context.

        Returns:
            Dict with custom messages (None values mean use defaults):
            {
                'company_policy': str or None,
                'break_recommendation': str or None,
                'late_night_warning': str or None,
                'critical_warning': str or None
            }
        """
        # Default: all None (use built-in messages)
        defaults = {
            'company_policy': None,
            'break_recommendation': None,
            'late_night_warning': None,
            'critical_warning': None
        }

        # Try to load from config file
        if self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                safety_config = config.get('safety', {})
                session_tracking = safety_config.get('session_tracking', {})
                customization = session_tracking.get('alert_customization', {})

                if customization:
                    # Extract custom messages (preserving None for unset values)
                    return {
                        'company_policy': customization.get('company_policy'),
                        'break_recommendation': customization.get('break_recommendation'),
                        'late_night_warning': customization.get('late_night_warning'),
                        'critical_warning': customization.get('critical_warning')
                    }

            except Exception as e:
                # Silent fallback to defaults
                pass

        # Default fallback
        return defaults

    def _ensure_state_file(self):
        """Ensure session state file exists with proper schema."""
        if not self.state_file.exists():
            print(f"[!] Session state file not found at {self.state_file}")
            print("    Creating default session state...")
            try:
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.state_file, 'w') as f:
                    json.dump(self._default_state(), f, indent=2)
            except (IOError, OSError) as e:
                raise RuntimeError(f"Failed to create session state file at {self.state_file}: {e}")

    def _default_state(self) -> Dict:
        """Return default session state structure (v8.13.0 - uses loaded thresholds)."""
        return {
            "_comment": "Domain Zero Protocol - Work Session State Tracking (v8.13.0)",
            "current_session": {
                "session_id": None,
                "session_active": False,
                "start_time": None,
                "last_interaction_time": None,
                "last_alert_time": None,
                "alert_count": 0,
                "escalation_level": 0,
                "user_last_choice": None,
                "break_acknowledged": False,
                "high_risk_operations_blocked": False
            },
            "session_metrics": {
                "total_duration_minutes": 0,
                "continuous_work_minutes": 0,
                "break_timestamps": [],
                "total_breaks": 0,
                "alerts_issued": 0,
                "alerts_ignored": 0,
                "continues_chosen": 0,
                "breaks_chosen": 0
            },
            "thresholds": {
                "initial_alert_minutes": self.alert_thresholds['initial_alert_minutes'],
                "escalated_alert_minutes": self.alert_thresholds['escalated_alert_minutes'],
                "critical_session_minutes": self.alert_thresholds['critical_session_minutes'],
                "max_continuous_minutes": self.alert_thresholds['max_continuous_minutes'],
                "late_night_hour": 22,
                "minimum_break_minutes": 15
            },
            "session_history": [],
            "last_updated": None,
            "protocol_version": "8.13.0"
        }

    def load_state(self) -> Dict:
        """
        Load current session state from JSON.

        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.
        Falls back to legacy file I/O for backward compatibility.
        """
        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                return self.state_manager.get_session_tracking()
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy file I/O (backward compatibility)
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[!] Session state file not found. Returning default state.")
            return self._default_state()
        except json.JSONDecodeError as e:
            print(f"[!] Corrupted session state file: {e}. Returning default state.")
            return self._default_state()

    def save_state(self, state: Dict):
        """
        Save session state to JSON with atomic write (SEC-002 FIX).

        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.
        Falls back to legacy file I/O for backward compatibility.
        """
        state['last_updated'] = datetime.now(timezone.utc).isoformat()

        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                self.state_manager.update_session_tracking(state)
                return
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy atomic write pattern (backward compatibility)
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                              dir=self.state_file.parent,
                                              suffix='.tmp') as tmp_file:
                json.dump(state, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic replace (POSIX rename guarantees atomicity)
            os.replace(tmp_path, self.state_file)
        except (IOError, OSError) as e:
            # If atomic write fails, try cleanup and re-raise
            try:
                if 'tmp_path' in locals() and Path(tmp_path).exists():
                    os.unlink(tmp_path)
            except OSError:
                pass  # Cleanup failure is non-critical
            raise IOError(f"Failed to save session state: {e}")

    def start_session(self, session_id: Optional[str] = None) -> Dict:
        """
        Start a new work session or continue existing one.

        v8.13.0 - Respects enabled flag

        Returns:
            Updated state with session initialized, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()
        now = datetime.now(timezone.utc)

        # Check if there's an active session from < 30 minutes ago
        if state['current_session']['session_active']:
            try:
                last_time = datetime.fromisoformat(state['current_session']['last_interaction_time'])
                gap_minutes = (now - last_time).total_seconds() / 60
            except (ValueError, TypeError):
                # Invalid timestamp format - treat as expired session
                print(f"[!] Invalid timestamp in session state. Starting new session.")
                gap_minutes = float('inf')

            if gap_minutes < 30:
                # Continue existing session
                print(f"[STATUS] Continuing active session (gap: {gap_minutes:.1f} minutes)")
                state['current_session']['last_interaction_time'] = now.isoformat()
                self.save_state(state)
                return state
            else:
                # Session expired, archive it
                print(f"[PAUSED] Previous session expired ({gap_minutes:.1f} min gap). Starting new session.")
                self._archive_session(state)

        # Start new session
        session_id = session_id or f"session_{now.strftime('%Y%m%d_%H%M%S')}"

        state['current_session'] = {
            "session_id": session_id,
            "session_active": True,
            "start_time": now.isoformat(),
            "last_interaction_time": now.isoformat(),
            "last_alert_time": None,
            "alert_count": 0,
            "escalation_level": 0,
            "user_last_choice": None,
            "break_acknowledged": False,
            "high_risk_operations_blocked": False
        }

        state['session_metrics'] = self._default_state()['session_metrics']

        print(f"[OK] New session started: {session_id}")
        self.save_state(state)
        return state

    def update_interaction(self, _retry_count: int = 0, _max_retries: int = 1) -> Dict:
        """
        Record a new interaction in the current session.

        v8.13.0 - Respects enabled flag

        Args:
            _retry_count: Internal retry counter (do not set manually)
            _max_retries: Maximum retries for session reset (default: 1)

        Returns:
            Updated state with interaction timestamp, or default state if disabled

        Raises:
            RuntimeError: If session cannot be started/reset after max retries
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        if _retry_count > _max_retries:
            raise RuntimeError("Exceeded maximum retries to reset session. Session state may be corrupted.")

        state = self.load_state()

        if not state['current_session']['session_active']:
            # Auto-start session if not active
            try:
                return self.start_session()
            except Exception as e:
                raise RuntimeError(f"Failed to start session: {e}")

        now = datetime.now(timezone.utc)
        state['current_session']['last_interaction_time'] = now.isoformat()

        # Calculate duration
        start_time = state['current_session'].get('start_time')
        if not start_time:
            print("[!] Session start_time is missing. Resetting session.")
            try:
                return self.update_interaction(_retry_count=_retry_count + 1, _max_retries=_max_retries)
            except Exception as e:
                raise RuntimeError(f"Failed to reset session (missing start_time): {e}")

        try:
            start = datetime.fromisoformat(start_time)
        except (ValueError, TypeError):
            print("[!] Invalid session start_time format. Resetting session.")
            try:
                return self.update_interaction(_retry_count=_retry_count + 1, _max_retries=_max_retries)
            except Exception as e:
                raise RuntimeError(f"Failed to reset session (invalid start_time format): {e}")

        # BUG FIX: Ensure timezone awareness (PATCH-SESSION-006)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        duration_minutes = (now - start).total_seconds() / 60
        state['session_metrics']['total_duration_minutes'] = int(duration_minutes)

        # Update continuous work time (time since last break)
        if state['session_metrics']['break_timestamps']:
            last_break = datetime.fromisoformat(state['session_metrics']['break_timestamps'][-1])
            # BUG FIX: Ensure timezone awareness (PATCH-SESSION-006)
            if last_break.tzinfo is None:
                last_break = last_break.replace(tzinfo=timezone.utc)
            continuous_minutes = (now - last_break).total_seconds() / 60
        else:
            continuous_minutes = duration_minutes

        state['session_metrics']['continuous_work_minutes'] = int(continuous_minutes)

        # Log to security review (EXTENSION 3: PATCH-SESSION-005)
        self._log_session_to_security_review('session_update', state)

        self.save_state(state)
        return state

    def check_alert_needed(self, debounce_override: int = None) -> Tuple[bool, str, Dict]:
        """
        Check if a work session alert should be issued.

        v8.13.0 - Respects enabled flag

        Args:
            debounce_override: CLI --debounce argument (v8.13.0)

        Returns:
            (should_alert, alert_level, alert_context)
            alert_level: "standard", "escalated", "critical"
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return False, None, {}

        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, None, {}

        now = datetime.now(timezone.utc)
        start_time = state['current_session'].get('start_time')
        if not start_time:
            print("[!] Session start_time is missing. Cannot check alert.")
            return False, None, {}

        # BUG-SESSION-001 (v9.3.0): normalize naive->aware via _parse_utc so the
        # aware/naive subtraction below can never raise (safety-critical path).
        start = _parse_utc(start_time)
        if start is None:
            print("[!] Invalid session start_time format. Cannot check alert.")
            return False, None, {}

        duration_minutes = (now - start).total_seconds() / 60

        # Debounce check (v8.13.0 - PATCH-SESSION-004)
        # Skip alert if last alert was too recent (prevents spam during rapid prototyping)
        debounce_threshold = self._load_debounce_config(cli_override=debounce_override)
        last_alert_time = state['current_session'].get('last_alert_time')

        last_alert_dt = _parse_utc(last_alert_time)
        if last_alert_dt is not None:
            minutes_since_last_alert = (now - last_alert_dt).total_seconds() / 60
            if minutes_since_last_alert < debounce_threshold:
                # Alert debounced - too soon since last alert
                return False, None, {}

        thresholds = state['thresholds']
        escalation_level = state['current_session']['escalation_level']

        # Determine if alert is needed
        alert_needed = False
        alert_level = "standard"

        # Check if first alert threshold reached (4 hours)
        if duration_minutes >= thresholds['initial_alert_minutes'] and state['current_session']['alert_count'] == 0:
            alert_needed = True
            alert_level = "standard"

        # Check if escalated alert needed (user chose continue + time passed)
        elif escalation_level > 0:
            # BUG-SESSION-001 (v9.3.0): this branch previously parsed last_alert_time
            # with a bare datetime.fromisoformat() and NO naive->aware guard (and no
            # try/except), so a naive legacy timestamp here crashed the entire
            # check-and-record path, silently disabling the wellbeing safety alerts.
            escalation_last_alert = _parse_utc(state['current_session'].get('last_alert_time'))
            if escalation_last_alert is not None:
                minutes_since_alert = (now - escalation_last_alert).total_seconds() / 60

                if minutes_since_alert >= thresholds['escalated_alert_minutes']:
                    alert_needed = True
                    alert_level = "escalated"

        # Check if critical threshold reached (6+ hours)
        if duration_minutes >= thresholds['critical_session_minutes']:
            alert_needed = True
            alert_level = "critical"

        # Check if maximum continuous work threshold reached (8+ hours)
        # This is the absolute maximum - enforce stricter read-only mode
        if duration_minutes >= thresholds['max_continuous_minutes']:
            alert_needed = True
            alert_level = "maximum"  # Highest severity level

        # Build alert context
        context = {
            "duration_minutes": int(duration_minutes),
            "duration_formatted": self._format_duration(duration_minutes),
            "alert_level": alert_level,
            "is_late_night": now.hour >= thresholds['late_night_hour'],
            "continuous_minutes": state['session_metrics']['continuous_work_minutes'],
            "alert_count": state['current_session']['alert_count']
        }

        return alert_needed, alert_level, context

    def render_alert(self, context: Dict) -> str:
        """
        Render work session alert with actual data.

        v8.13.0 - Enhanced with custom message injection

        Args:
            context: Alert context from check_alert_needed()

        Returns:
            Rendered alert text with placeholders replaced and custom messages injected
        """
        if not self.template_file.exists():
            # Return minimal fallback template with custom messages
            custom_msg = self._inject_custom_messages(context)

            return f"""
[!] Extended Work Session Detected

**Duration:** {context.get('duration_formatted', 'Unknown')}
**Project:** {self._get_project_name()}

{custom_msg if custom_msg else 'You have been working for an extended period. Consider taking a break to maintain productivity and reduce errors.'}

**Options:**
1. Save progress and take a break (recommended)
2. Continue working (proceed with caution)

Template file not found at: {self.template_file}
"""

        with open(self.template_file, 'r', encoding='utf-8') as f:
            template = f.read()

        now = datetime.now(timezone.utc)
        state = self.load_state()

        # Build replacement values
        replacements = {
            '{DATE}': now.strftime('%Y-%m-%d %H:%M'),
            '{DURATION}': context.get('duration_formatted', 'Unknown'),
            '{PROJECT_NAME}': self._get_project_name(),
            '{LATE_NIGHT_FLAG}': '[LATE] YES - Late night work detected' if context.get('is_late_night') else '[DAY] No',
            '{CONTINUOUS_FLAG}': f"[!] {context.get('continuous_minutes', 0)} minutes without break" if context.get('continuous_minutes', 0) > 120 else '[OK] Recent breaks taken',
            '{BREAK_RECOMMENDATION}': self._get_break_recommendation(context),
            '{LATE_NIGHT_THRESHOLD}': f"{state['thresholds']['late_night_hour']}:00"
        }

        # Replace all placeholders
        rendered = template
        for placeholder, value in replacements.items():
            rendered = rendered.replace(placeholder, str(value))

        # Inject custom messages (v8.13.0)
        custom_msg = self._inject_custom_messages(context)
        if custom_msg:
            # Append custom messages after the standard template
            rendered += f"\n\n---\n\n{custom_msg}"

        return rendered

    def record_user_choice(self, choice: str) -> Dict:
        """
        Record user's response to work session alert.

        v8.13.0 - Respects enabled flag

        Args:
            choice: "save_and_break" or "continue"

        Returns:
            Updated state, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        # Validate input
        if choice not in ["save_and_break", "continue"]:
            raise ValueError(f"Invalid choice '{choice}'. Must be 'save_and_break' or 'continue'.")

        state = self.load_state()
        now = datetime.now(timezone.utc)

        state['current_session']['user_last_choice'] = choice
        state['current_session']['last_alert_time'] = now.isoformat()
        state['current_session']['alert_count'] += 1
        state['session_metrics']['alerts_issued'] += 1

        if choice == "save_and_break":
            state['session_metrics']['breaks_chosen'] += 1
            state['current_session']['break_acknowledged'] = True
        elif choice == "continue":
            state['session_metrics']['continues_chosen'] += 1
            state['current_session']['escalation_level'] += 1

            # Enable high-risk blocking if in critical session
            duration_minutes = state['session_metrics']['total_duration_minutes']
            if duration_minutes >= state['thresholds']['critical_session_minutes']:
                state['current_session']['high_risk_operations_blocked'] = True

        self.save_state(state)
        return state

    def record_break(self, duration_minutes: Optional[int] = None) -> Dict:
        """
        Record that user took a break.

        v8.13.0 - Respects enabled flag

        Args:
            duration_minutes: Reported break duration (optional)

        Returns:
            Updated state, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()
        now = datetime.now(timezone.utc)

        state['session_metrics']['break_timestamps'].append(now.isoformat())
        state['session_metrics']['total_breaks'] += 1
        state['current_session']['escalation_level'] = 0  # Reset escalation
        state['current_session']['break_acknowledged'] = False

        # Reset continuous work timer
        state['session_metrics']['continuous_work_minutes'] = 0

        # If break was sufficient, downgrade high-risk blocking
        if duration_minutes and duration_minutes >= state['thresholds']['minimum_break_minutes']:
            state['current_session']['high_risk_operations_blocked'] = False

        print(f"[OK] Break recorded at {now.strftime('%H:%M')}")
        self.save_state(state)
        return state

    def end_session(self) -> Dict:
        """
        End the current work session and archive it.

        v8.13.0 - Respects enabled flag

        Returns:
            Updated state with session ended, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()

        if state['current_session']['session_active']:
            self._archive_session(state)
            print("[OK] Session ended and archived")

            # Get archived session data (last entry in history)
            if state['session_history']:
                archived_session = state['session_history'][-1]

                # EXTENSION 2: State Management (PATCH-SESSION-005)
                # Update all protocol state files with session completion data
                self._update_project_state_on_session_end(archived_session)
                self._log_session_end_to_dev_notes(archived_session)
                self._log_session_end_to_domain_record(archived_session)

                # EXTENSION 3: Security Review (PATCH-SESSION-005)
                self._log_session_to_security_review('session_end', archived_session)

        self.save_state(state)

        # Workstream B: full Cortex rebuild on session end (periodic re-index).
        # Fail-soft: any exception or non-zero exit is logged, never re-raised.
        try:
            cortex_result = self._sync_cortex_index(full=True)
            if cortex_result.get('skipped'):
                print(f"[CORTEX] end-of-session rebuild skipped ({cortex_result.get('status', 'unknown')})")
            else:
                print(f"[CORTEX] end-of-session rebuild complete ({cortex_result.get('status', 'unknown')})")
        except Exception as exc:
            print(f"[CORTEX] end-of-session rebuild failed (non-fatal): {exc}")

        return state

    def is_high_risk_operation(self, command: Optional[str]) -> bool:
        """
        Check if a command is considered high-risk using literal string matching.

        v8.13.0 - Respects enabled flag

        Non-string or empty commands are treated as not high-risk.

        Args:
            command: Command string to check (None or empty treated as non-high-risk)

        Returns:
            True if command is high-risk, False if disabled or non-high-risk
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return False

        # Guard: Treat None, non-string, or empty/whitespace as non-high-risk
        if not isinstance(command, str) or not command.strip():
            return False

        # Normalize command for case-insensitive matching
        command_lower = command.lower()

        # Use literal string matching (faster and safer than regex)
        for literal in self._high_risk_literals:
            if literal in command_lower:
                return True

        return False

    def should_block_operation(self, operation: Optional[str]) -> Tuple[bool, str]:
        """
        Check if an operation should be blocked due to session state.

        Args:
            operation: Operation description or command (None or empty treated as non-high-risk)

        Returns:
            (should_block, reason) - reason is empty string if not blocked
        """
        # Early return if session monitoring is disabled (v8.13.0)
        if not self.enabled:
            return False, ""

        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, ""

        # Calculate live duration (BUG FIX: PATCH-SESSION-005 - SESSION-003)
        # Fixes CRITICAL bug where high-risk blocking never activated due to stale duration.
        # live_duration: computed from wall-clock start_time (accurate for running sessions).
        # stored_duration: total_duration_minutes recorded in state metrics — used in reason
        #   strings because it represents the duration that caused the blocking flag to be set
        #   (e.g. via record_user_choice) and is the value tests and humans expect to see.
        live_duration = self._calculate_current_duration(state)
        stored_duration = state['session_metrics'].get('total_duration_minutes', live_duration)
        # Use whichever is larger: live clock or stored metric (guards against clock skew in tests)
        duration_minutes = max(live_duration, stored_duration)
        thresholds = state['thresholds']

        # Check if 8-hour maximum continuous work threshold reached - BLOCK ALL OPERATIONS
        if duration_minutes >= thresholds['max_continuous_minutes']:
            reason = (
                f"🛑 [BLOCKED] MAXIMUM WORK LIMIT REACHED: {duration_minutes} minutes "
                f"({duration_minutes // 60}+ hours). You MUST take a break. "
                f"Session is now read-only."
            )
            return True, reason

        # Check if 6-hour critical threshold reached - block high-risk operations only
        if state['current_session']['high_risk_operations_blocked']:
            if self.is_high_risk_operation(operation):
                reason = (
                    f"🛑 High-risk operation blocked: Extended session "
                    f"({duration_minutes} min). Take a break first."
                )
                return True, reason

        return False, ""

    def get_session_summary(self) -> str:
        """
        Get human-readable session summary.

        Returns:
            Formatted session summary
        """
        state = self.load_state()

        if not state['current_session']['session_active']:
            return "No active session"

        metrics = state['session_metrics']
        current = state['current_session']

        # Validate start_time exists
        start_time = current.get('start_time')
        if not start_time:
            return "[!] Session state corrupted: start_time missing"

        try:
            start_formatted = datetime.fromisoformat(start_time).strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            start_formatted = "Invalid timestamp"

        # Calculate live duration (BUG FIX: PATCH-SESSION-005 - SESSION-001)
        # Fixes bug where status command showed 0 minutes for long-running sessions
        current_duration = self._calculate_current_duration(state)
        current_continuous = self._calculate_current_continuous_work(state)
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        summary = f"""
[STATUS] **Work Session Summary**

**Current Time:** {current_time}
**Duration:** {self._format_duration(current_duration)}
**Continuous Work:** {self._format_duration(current_continuous)} since last break
**Breaks Taken:** {metrics['total_breaks']}
**Alerts Issued:** {metrics['alerts_issued']}
**Escalation Level:** {current['escalation_level']}
**High-Risk Blocking:** {'[BLOCKED] ENABLED' if current['high_risk_operations_blocked'] else '[OK] Disabled'}

**Session ID:** {current['session_id']}
**Started:** {start_formatted}
"""
        return summary.strip()

    def _archive_session(self, state: Dict):
        """Archive current session to history."""
        if state['current_session']['session_active']:
            # Calculate final duration from start to end (BUG FIX: PATCH-SESSION-005 - SESSION-002)
            # Fixes bug where archived sessions showed 0 minutes duration
            try:
                start = datetime.fromisoformat(state['current_session']['start_time'])
                end = datetime.now(timezone.utc)
                actual_duration = int((end - start).total_seconds() / 60)
            except (ValueError, TypeError):
                # Fallback to stored value if timestamp invalid (shouldn't happen)
                actual_duration = state['session_metrics']['total_duration_minutes']

            archived = {
                "session_id": state['current_session']['session_id'],
                "start_time": state['current_session']['start_time'],
                "end_time": datetime.now(timezone.utc).isoformat(),
                "total_duration_minutes": actual_duration,
                "total_breaks": state['session_metrics']['total_breaks'],
                "alerts_issued": state['session_metrics']['alerts_issued'],
                "continues_chosen": state['session_metrics']['continues_chosen']
            }

            state['session_history'].append(archived)

            # Keep only last 30 sessions
            if len(state['session_history']) > 30:
                state['session_history'] = state['session_history'][-30:]

            # Reset current session
            state['current_session'] = self._default_state()['current_session']

    def _format_duration(self, minutes: float) -> str:
        """Format duration in human-readable format."""
        hours = int(minutes // 60)
        mins = int(minutes % 60)

        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
        else:
            return f"{mins} minutes"

    def _calculate_current_duration(self, state: Dict) -> int:
        """
        Calculate current session duration without updating state.

        PATCH-SESSION-005 (BUG FIX: SESSION-001)
        Calculates duration on-the-fly from start_time instead of reading stale metrics.

        Args:
            state: Session state dictionary

        Returns:
            Current session duration in minutes (0 if not active or invalid)
        """
        if not state['current_session']['session_active']:
            return 0

        start_time = state['current_session'].get('start_time')
        if not start_time:
            return 0

        try:
            start = datetime.fromisoformat(start_time)
            now = datetime.now(timezone.utc)
            return int((now - start).total_seconds() / 60)
        except (ValueError, TypeError):
            return 0  # Fallback on error

    def _calculate_current_continuous_work(self, state: Dict) -> int:
        """
        Calculate continuous work duration without updating state.

        PATCH-SESSION-005 (BUG FIX: SESSION-001)
        Calculates time since last break on-the-fly.

        Args:
            state: Session state dictionary

        Returns:
            Continuous work duration in minutes (0 if not active or invalid)
        """
        if not state['current_session']['session_active']:
            return 0

        if state['session_metrics']['break_timestamps']:
            try:
                last_break = datetime.fromisoformat(
                    state['session_metrics']['break_timestamps'][-1]
                )
                now = datetime.now(timezone.utc)
                return int((now - last_break).total_seconds() / 60)
            except (ValueError, TypeError, IndexError):
                return self._calculate_current_duration(state)
        else:
            return self._calculate_current_duration(state)

    def _get_project_name(self) -> str:
        """Get current project name from protocol root."""
        return self.protocol_root.name

    def _get_break_recommendation(self, context: Dict) -> str:
        """Generate break recommendation based on context."""
        # Use custom message if configured (v8.13.0)
        if self.alert_customization['break_recommendation']:
            return self.alert_customization['break_recommendation']

        # Default recommendations
        duration = context.get('duration_minutes', 0)
        is_late = context.get('is_late_night', False)

        if duration >= 360:  # 6+ hours
            return "[STOP] STRONGLY RECOMMENDED - End session and rest"
        elif duration >= 300:  # 5 hours
            return "[!] Take 15-minute break minimum"
        elif duration >= 240:  # 4 hours
            return "[TIP] 5-10 minute break suggested"
        elif is_late:
            return "[LATE] Late night work - consider ending session"
        else:
            return "Continue with awareness"

    def _inject_custom_messages(self, context: Dict) -> str:
        """
        Inject custom alert messages from configuration.

        v8.13.0 - Configuration Enhancement

        Args:
            context: Alert context with duration_minutes, is_late_night, etc.

        Returns:
            Formatted custom message string, or empty string if no custom messages
        """
        messages = []
        duration_hours = context.get('duration_minutes', 0) / 60
        is_late = context.get('is_late_night', False)
        is_critical = duration_hours >= (self.alert_thresholds['critical_session_minutes'] / 60)

        # Company policy message
        if self.alert_customization['company_policy']:
            messages.append(f"**Company Policy:** {self.alert_customization['company_policy']}")

        # Late night warning
        if is_late and self.alert_customization['late_night_warning']:
            messages.append(f"**Late Night Alert:** {self.alert_customization['late_night_warning']}")

        # Critical warning (overrides break recommendation if critical)
        if is_critical and self.alert_customization['critical_warning']:
            # Replace {hours} placeholder
            critical_msg = self.alert_customization['critical_warning'].replace('{hours}', f"{duration_hours:.1f}")
            messages.append(f"**CRITICAL:** {critical_msg}")

        return "\n\n".join(messages) if messages else ""

    def record_agent_invocation(self, agent_name: str, is_direct: bool = True) -> Dict:
        """
        Record an agent invocation for bypass detection.

        v8.13.0 - PATCH-SESSION-004 Component 5

        Args:
            agent_name: Name of agent invoked (gojo, yuuji, megumi, etc.)
            is_direct: True if direct invocation, False if routed via Gojo

        Returns:
            Updated invocation tracker state
        """
        # Validate agent name
        valid_agents = ['gojo', 'yuuji', 'megumi', 'nobara', 'todo', 'maki', 'panda', 'inumaki', 'sukuna']
        agent_name_lower = agent_name.lower()

        if agent_name_lower not in valid_agents:
            raise ValueError(f"Invalid agent name: {agent_name}. Must be one of: {', '.join(valid_agents)}")

        # PATCH-STATE-001: Load tracker state using ProjectStateManager
        if self.state_manager:
            try:
                tracker = self.state_manager.get_agent_invocation_tracking()
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O
                tracker = None

        if not self.state_manager or tracker is None:
            # Legacy file I/O (backward compatibility)
            if not self.invocation_tracker_file.exists():
                print(f"[!] Agent invocation tracker not found at {self.invocation_tracker_file}")
                print("    Using default schema")
                # File should exist from PATCH-SESSION-004, but handle gracefully
                return {}

            try:
                with open(self.invocation_tracker_file, 'r', encoding='utf-8') as f:
                    tracker = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"[ERROR] Cannot read invocation tracker: {e}")
                return {}

        if not tracker.get('tracking_enabled', True):
            # Tracking disabled, silently skip
            return tracker

        # Update invocation counts
        now = datetime.now(timezone.utc).isoformat()
        agent_data = tracker['invocations'].get(agent_name_lower, {})

        agent_data['total_count'] = agent_data.get('total_count', 0) + 1
        agent_data['last_invocation'] = now

        if agent_name_lower != 'gojo':
            # Track direct vs routed for non-Gojo agents
            if is_direct:
                agent_data['direct_invocations'] = agent_data.get('direct_invocations', 0) + 1
            else:
                agent_data['routed_invocations'] = agent_data.get('routed_invocations', 0) + 1

        tracker['invocations'][agent_name_lower] = agent_data
        tracker['_last_updated'] = now

        # Bypass detection (direct invocations of non-Gojo agents)
        if agent_name_lower != 'gojo' and is_direct and tracker.get('bypass_detection', {}).get('enabled', True):
            # Get current session duration
            session_state = self.load_state()
            if session_state.get('current_session', {}).get('session_active'):
                start_time_str = session_state['current_session'].get('start_time')
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str)
                        duration_minutes = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)

                        # Detect bypass if session is long-running (>= threshold)
                        threshold = tracker.get('bypass_detection', {}).get('threshold_minutes', 30)
                        if duration_minutes >= threshold:
                            bypass_alert = {
                                "timestamp": now,
                                "agent": agent_name_lower,
                                "session_duration_minutes": duration_minutes,
                                "message": f"Direct {agent_name_lower} invocation during {duration_minutes}-minute session (bypasses Gojo monitoring)"
                            }
                            tracker['bypass_detection']['bypass_alerts'].append(bypass_alert)
                    except (ValueError, TypeError):
                        pass  # Invalid timestamp, skip bypass detection

        # PATCH-STATE-001: Save updated tracker using ProjectStateManager
        if self.state_manager:
            try:
                self.state_manager.update_agent_invocation_tracking(tracker)
                return tracker
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy save (SEC-001 FIX: atomic write)
        try:
            # Atomic write pattern
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                              dir=self.invocation_tracker_file.parent,
                                              suffix='.tmp') as tmp_file:
                json.dump(tracker, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic replace (POSIX rename guarantees atomicity)
            os.replace(tmp_path, self.invocation_tracker_file)
        except (IOError, OSError) as e:
            print(f"[ERROR] Cannot save invocation tracker: {e}")

        return tracker

    def _update_project_state_on_session_end(self, session_data: Dict):
        """
        Update project-state.json with session completion data.

        EXTENSION 2: State Management (PATCH-SESSION-005)
        Logs session metrics to project-state for aggregate tracking.

        Args:
            session_data: Archived session data with duration, breaks, alerts, etc.
        """
        project_state_file = self.protocol_root / ".protocol-state" / "project-state.json"

        if not project_state_file.exists():
            print(f"[WARN] project-state.json not found at {project_state_file}")
            return

        try:
            with open(project_state_file, 'r', encoding='utf-8') as f:
                project_state = json.load(f)

            # Update session tracking metrics
            tracking = project_state.setdefault('session_tracking', {})
            tracking['last_session_end'] = session_data['end_time']
            tracking['total_sessions'] = tracking.get('total_sessions', 0) + 1
            tracking['total_work_minutes'] = tracking.get('total_work_minutes', 0) + session_data['total_duration_minutes']

            # Atomic write
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                              dir=project_state_file.parent,
                                              suffix='.tmp') as tmp_file:
                json.dump(project_state, tmp_file, indent=2)
                tmp_path = tmp_file.name

            os.replace(tmp_path, project_state_file)
            print(f"[OK] Updated project-state.json with session metrics")

        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"[ERROR] Failed to update project-state.json: {e}")

    def _log_session_end_to_dev_notes(self, session_data: Dict):
        """
        Log session end to dev-notes.md.

        EXTENSION 2: State Management (PATCH-SESSION-005)
        Provides human-readable development log of work sessions.

        Args:
            session_data: Archived session data
        """
        dev_notes_file = self.protocol_root / ".protocol-state" / "dev-notes.md"

        if not dev_notes_file.exists():
            print(f"[WARN] dev-notes.md not found at {dev_notes_file}")
            return

        try:
            entry = f"""
## Work Session Ended - {session_data['end_time']}

**Session ID:** {session_data['session_id']}
**Duration:** {self._format_duration(session_data['total_duration_minutes'])}
**Breaks Taken:** {session_data['total_breaks']}
**Alerts Issued:** {session_data['alerts_issued']}
**Continues Chosen:** {session_data['continues_chosen']}

"""
            with open(dev_notes_file, 'a', encoding='utf-8') as f:
                f.write(entry)

            print(f"[OK] Logged session end to dev-notes.md")

        except (IOError, OSError) as e:
            print(f"[ERROR] Failed to write to dev-notes.md: {e}")

    def _log_session_end_to_domain_record(self, session_data: Dict):
        """
        Log session end to domain.record.md (Gojo permission only).

        EXTENSION 3: Permission System (PATCH-SESSION-005)
        Strategic protocol tracking - only accessible when invoked by Gojo.

        Args:
            session_data: Archived session data
        """
        # Permission check: Only Gojo can update domain.record.md
        if not self._check_gojo_invocation():
            print(f"[SKIP] domain.record.md update skipped (requires Gojo invocation)")
            return

        domain_record_file = self.protocol_root / ".dzp-domain" / "domain.record.md"

        if not domain_record_file.exists():
            print(f"[WARN] domain.record.md not found at {domain_record_file}")
            return

        try:
            entry = f"""
### Session Completed - {session_data['end_time']}

- **Session ID:** {session_data['session_id']}
- **Duration:** {self._format_duration(session_data['total_duration_minutes'])}
- **Wellbeing Metrics:** {session_data['total_breaks']} breaks, {session_data['alerts_issued']} alerts, {session_data['continues_chosen']} continues
- **Session Pattern:** {'Extended session' if session_data['total_duration_minutes'] > 360 else 'Standard session'}

"""
            with open(domain_record_file, 'a', encoding='utf-8') as f:
                f.write(entry)

            print(f"[OK] Logged session end to domain.record.md (Gojo permission)")

        except (IOError, OSError) as e:
            print(f"[ERROR] Failed to write to domain.record.md: {e}")

    def _log_session_to_security_review(self, event_type: str, session_data: Dict):
        """
        Log session events to security-review.md for audit trail.

        EXTENSION 3: Permission System (PATCH-SESSION-005)
        Tracks session lifecycle events for security monitoring and protocol compliance.

        Args:
            event_type: "session_update" or "session_end"
            session_data: Session state or archived session data
        """
        security_review_file = self.protocol_root / ".protocol-state" / "security-review.md"

        if not security_review_file.exists():
            print(f"[WARN] security review file not found at {security_review_file}")
            return

        try:
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            if event_type == "session_update":
                duration = self._calculate_current_duration(session_data)
                entry = f"""
## Security Review - Session Update - {now}

**Event:** User interaction recorded
**Session Duration:** {self._format_duration(duration)}
**Safety Status:** {'[ALERT] Extended session' if duration > 360 else '[OK] Normal'}

"""
            elif event_type == "session_end":
                entry = f"""
## Security Review - Session End - {now}

**Event:** Work session ended
**Session ID:** {session_data['session_id']}
**Total Duration:** {self._format_duration(session_data['total_duration_minutes'])}
**Wellbeing Compliance:** {session_data['total_breaks']} breaks taken, {session_data['alerts_issued']} alerts acknowledged

"""
            else:
                return

            with open(security_review_file, 'a', encoding='utf-8') as f:
                f.write(entry)

            print(f"[OK] Logged {event_type} to security review")

        except (IOError, OSError) as e:
            print(f"[ERROR] Failed to write security review: {e}")

    def sync_all_project_documents(self, include_git_operations: bool = True) -> Dict[str, any]:
        """
        Comprehensive sync of all project documents with secret scanning and git operations.

        This method performs a full checkpoint of all project documentation:
        1. Updates project-state.json via ProjectStateManager
        2. Prepares checkpoint content for domain.record.md, dev-notes.md,
           security-review.md in memory (SEC-SU-002: no TOCTOU gap)
        3. Scans prepared content for production secrets BEFORE writing
        4. Writes content to files only if scan passes (with backups per SEC-SU-003)
        5. Commits and pushes with user approval

        Args:
            include_git_operations: If True, performs git commit/push with approval

        Returns:
            Dict with sync results and status
        """
        results = {
            'success': False,
            'documents_updated': [],
            'secrets_found': [],
            'git_operations': {'attempted': False, 'success': False},
            'errors': []
        }

        print("[SYNC] Starting comprehensive project document sync...")

        # Step 1: Update project-state.json using ProjectStateManager
        try:
            if self.state_manager:
                state = self.state_manager.load_project_state()
                # Update last_updated timestamp
                state['project_metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()
                self.state_manager.save_project_state(state)
                results['documents_updated'].append('project-state.json')
                print("[OK] project-state.json synced via ProjectStateManager")
            else:
                results['errors'].append("ProjectStateManager not available")
                print("[WARN] ProjectStateManager not available, skipping project-state.json sync")
        except Exception as e:
            results['errors'].append(f"project-state.json sync failed: {e}")
            print(f"[ERROR] Failed to sync project-state.json: {e}")

        # SEC-SU-002 REMEDIATION: Prepare content in memory FIRST, scan BEFORE writing.
        # This eliminates the TOCTOU gap where files could be modified between
        # write and scan. Content is generated, scanned, then written only if clean.

        # Step 2: Prepare checkpoint content for all documents (in-memory)
        pending_writes = []  # List of (filepath, content, doc_name) tuples
        content_map = {}     # filename -> content for in-memory scanning

        # Prepare domain.record.md content
        if self._check_gojo_invocation():
            try:
                result = self._prepare_domain_record_content()
                if result:
                    pending_writes.append((result[0], result[1], 'domain.record.md'))
                    content_map['domain.record.md'] = result[1]
                    print("[PREP] domain.record.md content prepared (Gojo permission)")
            except Exception as e:
                results['errors'].append(f"domain.record.md prep failed: {e}")
                print(f"[ERROR] Failed to prepare domain.record.md: {e}")
        else:
            print("[SKIP] domain.record.md sync skipped (requires Gojo permission)")

        # Prepare dev-notes.md content
        try:
            result = self._prepare_dev_notes_content()
            if result:
                pending_writes.append((result[0], result[1], 'dev-notes.md'))
                content_map['dev-notes.md'] = result[1]
                print("[PREP] dev-notes.md content prepared")
        except Exception as e:
            results['errors'].append(f"dev-notes.md prep failed: {e}")
            print(f"[ERROR] Failed to prepare dev-notes.md: {e}")

        # Prepare security-review.md content
        try:
            result = self._prepare_security_review_content()
            if result:
                pending_writes.append((result[0], result[1], 'security-review.md'))
                content_map['security-review.md'] = result[1]
                print("[PREP] security-review.md content prepared")
        except Exception as e:
            results['errors'].append(f"security-review.md prep failed: {e}")
            print(f"[ERROR] Failed to prepare security-review.md: {e}")

        # Step 3: Scan prepared content for secrets BEFORE writing
        doc_names = [name for _, _, name in pending_writes]
        if doc_names:
            print("[SCAN] Scanning prepared content for production secrets (pre-write)...")
            secrets_found = self._scan_for_secrets(doc_names, content_map=content_map)
            results['secrets_found'] = secrets_found

            # Filter to high-confidence findings that should block writes
            high_confidence_secrets = [s for s in secrets_found if s.get('confidence') == 'high']

            if high_confidence_secrets:
                print(f"[WARNING] Found {len(high_confidence_secrets)} HIGH confidence secrets in prepared content!")
                for secret in high_confidence_secrets:
                    print(f"  - {secret['file']}: {secret['type']} at line {secret['line']} [{secret['confidence']}]")
                print("[ABORT] Blocking file writes due to high-confidence secret detection")
                results['errors'].append(f"Write blocked: {len(high_confidence_secrets)} high-confidence secrets detected in content")
            else:
                if secrets_found:
                    print(f"[INFO] Found {len(secrets_found)} potential findings (none high-confidence)")
                    for secret in secrets_found:
                        print(f"  - {secret['file']}: {secret['type']} at line {secret['line']} [{secret.get('confidence', 'unknown')}]")
                else:
                    print("[OK] No secrets detected in prepared content")

                # Step 4: Write content to files (scan passed)
                for filepath, content, doc_name in pending_writes:
                    try:
                        self._write_checkpoint(filepath, content)
                        results['documents_updated'].append(doc_name)
                        print(f"[OK] {doc_name} synced")
                    except Exception as e:
                        results['errors'].append(f"{doc_name} write failed: {e}")
                        print(f"[ERROR] Failed to write {doc_name}: {e}")

        # Step 5: Git operations with user approval
        if include_git_operations and results['documents_updated']:
            try:
                git_result = self._git_commit_and_push_with_approval(
                    files=results['documents_updated'],
                    secrets_found=results['secrets_found']
                )
                results['git_operations'] = git_result
            except Exception as e:
                results['errors'].append(f"Git operations failed: {e}")
                print(f"[ERROR] Git operations failed: {e}")

        results['success'] = len(results['documents_updated']) > 0 and len(results['errors']) == 0

        # Workstream B: Cortex-in-sync — call AFTER doc writes + git, fail-soft.
        cortex_result = self._sync_cortex_index(full=False)
        results['cortex_index'] = cortex_result
        status_label = cortex_result.get('status', 'unknown')
        if cortex_result.get('skipped'):
            print(f"[CORTEX] index skipped ({status_label})")
        else:
            print(f"[CORTEX] index complete ({status_label})")

        print(f"[SYNC] Sync completed. {len(results['documents_updated'])} documents updated.")
        return results

    # -----------------------------------------------------------------------
    # Workstream B helpers
    # -----------------------------------------------------------------------

    def _cortex_index_lock_exists(self) -> bool:
        """Return True if the brain index.lock file exists (another indexer is running).

        Lock path mirrors brain-index-hook.ps1: <data_dir>/index.lock.
        Computed dynamically so we don't hard-code the install-id hash.
        Fail-soft: any error resolving the path → return False (let indexer try).
        """
        try:
            import subprocess as _sp
            brain_py = self.protocol_root / ".protocol-state" / "brain" / "brain.py"
            if not brain_py.exists():
                return False
            # Ask brain.py for its data_dir via a status --json call
            result = _sp.run(
                [sys.executable, str(brain_py), "--repo", str(self.protocol_root), "status", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return False
            import json as _json
            data = _json.loads(result.stdout)
            db_path = Path(data.get("db", ""))
            lock_path = db_path.parent / "index.lock"
            return lock_path.exists()
        except Exception:
            return False

    def _sync_cortex_index(self, full: bool = False) -> Dict:
        """Incrementally (or fully) re-index DZP Cortex after a document sync.

        Workstream B implementation — always fail-soft (never raises).

        Args:
            full: If True, perform a full rebuild (no --incremental flag).
                  If False (default), add --incremental for faster updates.

        Returns:
            dict with keys: attempted, skipped, status, [error], [exit_code]
        """
        import subprocess as _sp

        result: Dict = {"attempted": True, "skipped": False, "status": "unknown"}

        brain_py = self.protocol_root / ".protocol-state" / "brain" / "brain.py"
        if not brain_py.exists():
            result.update({"skipped": True, "status": "unavailable",
                           "reason": "brain.py not found"})
            return result

        try:
            # Status gate: verify Cortex is operational before indexing.
            status_proc = _sp.run(
                [sys.executable, str(brain_py), "--repo", str(self.protocol_root), "status"],
                capture_output=True, text=True, timeout=30,
            )
            if status_proc.returncode != 0:
                result.update({"skipped": True, "status": "status_failed",
                               "reason": (status_proc.stderr or "status non-zero")[:200]})
                return result

            # Lock check: another indexer may be running.
            if self._cortex_index_lock_exists():
                result.update({"skipped": True, "status": "locked",
                               "reason": "index.lock exists; another indexer is running"})
                return result

            # Build index command.
            index_cmd = [sys.executable, str(brain_py), "--repo", str(self.protocol_root), "index"]
            if not full:
                index_cmd.append("--incremental")

            index_proc = _sp.run(
                index_cmd,
                capture_output=True, text=True, timeout=120,
            )
            result.update({
                "skipped": False,
                "status": "ok" if index_proc.returncode == 0 else "error",
                "exit_code": index_proc.returncode,
                "summary": (index_proc.stdout or "")[:400],
            })
            return result

        except _sp.TimeoutExpired as exc:
            result.update({"skipped": True, "status": "timeout",
                           "error": f"indexer timed out after {exc.timeout}s"})
            return result
        except Exception as exc:
            result.update({"skipped": True, "status": "error",
                           "error": str(exc)[:200]})
            return result

    def _cli_update(self, time_only: bool = False) -> None:
        """Shared logic for the 'update' CLI command.

        Workstream B: rewires 'update' to be the full-sync orchestrator.

        Args:
            time_only: If True, only record the interaction timestamp (fast,
                       for internal/automated callers). If False (default),
                       run full sync (timestamp + doc sync + cortex index).
        """
        state = self.update_interaction()
        print(f"[OK] Session updated: {state['session_metrics']['total_duration_minutes']} minutes")

        if not time_only:
            include_git = True  # git remains approval-gated inside sync
            results = self.sync_all_project_documents(include_git_operations=include_git)

            print("\n[SYNC RESULTS]")
            print(f"Documents updated: {len(results['documents_updated'])}")
            for doc in results['documents_updated']:
                print(f"  + {doc}")

            cortex_info = results.get('cortex_index', {})
            if cortex_info.get('skipped'):
                print(f"[CORTEX] skipped ({cortex_info.get('status', 'unknown')})")
            else:
                print(f"[CORTEX] indexed ({cortex_info.get('status', 'unknown')})")

            if results['errors']:
                print(f"[WARN] {len(results['errors'])} sync error(s):")
                for err in results['errors']:
                    print(f"  - {err}")

    def _backup_before_append(self, filepath: Path) -> Optional[Path]:
        """
        SEC-SU-003 REMEDIATION: Create timestamped backup before append operations.

        Satisfies Protection Rule 4: BACKUP BEFORE EDIT for all project documents.

        Args:
            filepath: Path to the file being appended to

        Returns:
            Path to backup file, or None if backup failed
        """
        if not filepath.exists():
            return None

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = self.protocol_root / ".protocol-state" / "backups" / f"session-sync_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / filepath.name

        try:
            shutil.copy2(filepath, backup_file)
            return backup_file
        except (IOError, OSError) as e:
            print(f"[WARN] Failed to create backup of {filepath.name}: {e}")
            return None

    def _prepare_domain_record_content(self) -> Optional[Tuple[Path, str]]:
        """
        Generate domain.record.md checkpoint content without writing.

        SEC-SU-002 REMEDIATION: Content is generated in memory for
        pre-write secret scanning (eliminates TOCTOU gap).

        Returns:
            Tuple of (filepath, content_string) or None if file not found
        """
        domain_record_file = self.protocol_root / ".dzp-domain" / "domain.record.md"

        if not domain_record_file.exists():
            print(f"[WARN] domain.record.md not found at {domain_record_file}")
            return None

        state = self.load_state()
        now = datetime.now(timezone.utc)

        # Calculate session duration
        start_time = state['current_session'].get('start_time')
        start = _parse_utc(start_time)  # BUG-SESSION-001 (v9.3.0): naive->aware guard
        if start is not None:
            duration_minutes = (now - start).total_seconds() / 60
            duration_formatted = f"{int(duration_minutes // 60)}h {int(duration_minutes % 60)}m"
        else:
            duration_formatted = "Unknown"

        # Read recent entries from dev-notes for strategic context
        dev_notes_file = self.protocol_root / ".protocol-state" / "dev-notes.md"
        strategic_context = "No recent implementation notes"
        if dev_notes_file.exists():
            try:
                with open(dev_notes_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Get last 5 non-empty lines
                    recent_lines = [l.strip() for l in lines[-10:] if l.strip() and not l.startswith('#')]
                    if recent_lines:
                        strategic_context = ' | '.join(recent_lines[:3])
            except Exception:
                pass

        checkpoint_entry = f"""
---
## Session Checkpoint - {now.strftime('%Y-%m-%d %H:%M:%S')} UTC

**Session Duration**: {duration_formatted}
**Alert Status**: {state['current_session'].get('alert_count', 0)} alerts | Escalation Level {state['current_session'].get('escalation_level', 0)}
**Strategic Context**: {strategic_context}

"""
        return (domain_record_file, checkpoint_entry)

    def _prepare_dev_notes_content(self) -> Optional[Tuple[Path, str]]:
        """
        Generate dev-notes.md checkpoint content without writing.

        SEC-SU-002 REMEDIATION: Content is generated in memory for
        pre-write secret scanning (eliminates TOCTOU gap).

        Returns:
            Tuple of (filepath, content_string) or None if file not found
        """
        dev_notes_file = self.protocol_root / ".protocol-state" / "dev-notes.md"

        if not dev_notes_file.exists():
            print(f"[WARN] dev-notes.md not found at {dev_notes_file}")
            return None

        state = self.load_state()
        now = datetime.now(timezone.utc)

        # Calculate session duration
        start_time = state['current_session'].get('start_time')
        start = _parse_utc(start_time)  # BUG-SESSION-001 (v9.3.0): naive->aware guard
        if start is not None:
            duration_minutes = (now - start).total_seconds() / 60
            duration_formatted = f"{int(duration_minutes // 60)}h {int(duration_minutes % 60)}m"
        else:
            duration_formatted = "Unknown"

        checkpoint_entry = f"""
---
## {now.strftime('%Y-%m-%d %H:%M:%S')} - Session Checkpoint

**Session Duration**: {duration_formatted}
**Continuous Work**: {state['session_metrics'].get('continuous_work_minutes', 0)} minutes
**Breaks Taken**: {state['session_metrics'].get('total_breaks', 0)}

### Active Work
- Session checkpoint sync completed
- All project documents updated

"""
        return (dev_notes_file, checkpoint_entry)

    def _prepare_security_review_content(self) -> Optional[Tuple[Path, str]]:
        """
        Generate security-review.md checkpoint content without writing.

        SEC-SU-002 REMEDIATION: Content is generated in memory for
        pre-write secret scanning (eliminates TOCTOU gap).

        Returns:
            Tuple of (filepath, content_string) or None if file not found
        """
        security_review_file = self.protocol_root / ".protocol-state" / "security-review.md"

        if not security_review_file.exists():
            print(f"[WARN] security-review.md not found at {security_review_file}")
            return None

        now = datetime.now(timezone.utc)

        checkpoint_entry = f"""
---
## {now.strftime('%Y-%m-%d %H:%M:%S')} - Security Checkpoint

**Event**: Session checkpoint sync
**Status**: Project documents synced and secret scan completed

"""
        return (security_review_file, checkpoint_entry)

    def _write_checkpoint(self, filepath: Path, content: str):
        """
        Write checkpoint content to file with backup.

        SEC-SU-003: Creates timestamped backup before append.
        SEC-SU-002: Called only AFTER content passes secret scan.

        Args:
            filepath: Target file path
            content: Checkpoint content string to append
        """
        # SEC-SU-003: Create timestamped backup before append
        self._backup_before_append(filepath)

        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
        except (IOError, OSError) as e:
            raise Exception(f"Failed to write to {filepath.name}: {e}")

    # Legacy wrappers for backward compatibility (used by external callers)
    def _sync_domain_record(self):
        """Sync domain.record.md - legacy wrapper."""
        result = self._prepare_domain_record_content()
        if result:
            self._write_checkpoint(result[0], result[1])

    def _sync_dev_notes(self):
        """Sync dev-notes.md - legacy wrapper."""
        result = self._prepare_dev_notes_content()
        if result:
            self._write_checkpoint(result[0], result[1])

    def _sync_security_review(self):
        """Sync security-review.md - legacy wrapper."""
        result = self._prepare_security_review_content()
        if result:
            self._write_checkpoint(result[0], result[1])

    def _scan_for_secrets(self, files: List[str], content_map: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        Scan project documents for production secrets.

        SEC-SU-001 REMEDIATION: Reports ALL findings with confidence levels
        instead of silently skipping suspected false positives.

        SEC-SU-002 REMEDIATION: Accepts optional content_map for in-memory
        scanning before files are written (eliminates TOCTOU gap).

        SEC-SU-004 REMEDIATION: Secret previews are redacted to prevent
        leaking secret material to stdout/logs.

        SEC-SU-005 REMEDIATION: CONNECTION_STRING regex uses [^@\\s]+ before
        the @ to prevent quadratic backtracking. Lines > 500 chars are
        skipped to mitigate ReDoS on adversarial input.

        Detects:
        - AWS keys (AKIA...)
        - GitHub tokens (ghp_...)
        - Connection strings (mongodb://, postgres://, mysql://)
        - Password assignments
        - Generic API key patterns (high-entropy 32+ char strings)

        Args:
            files: List of filenames to scan
            content_map: Optional dict mapping filename -> content string
                         for in-memory pre-write scanning

        Returns:
            List of detected secrets with file, line, type, and confidence
        """
        import re

        secrets_found = []

        # SEC-SU-005: Narrowed API_KEY pattern and fixed CONNECTION_STRING
        # to prevent ReDoS via [^@\s]+ before the @ separator
        patterns = {
            'AWS_KEY': re.compile(r'AKIA[0-9A-Z]{16}'),
            'GITHUB_TOKEN': re.compile(r'ghp_[A-Za-z0-9]{36}'),
            'CONNECTION_STRING': re.compile(r'(mongodb|postgres|mysql|redis)://[^@\s]+@[^\s]+'),
            'PASSWORD_ASSIGNMENT': re.compile(r'password\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
            'API_KEY': re.compile(r'(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{32,}', re.IGNORECASE),
        }

        # Low-confidence indicator words (SEC-SU-001: still report, just lower confidence)
        low_confidence_indicators = ['example', 'placeholder', 'test', 'sample', 'dummy', 'fake', 'mock']

        for filename in files:
            # Determine content source: in-memory map or file on disk
            lines_to_scan = None

            if content_map and filename in content_map:
                # SEC-SU-002: Scan from in-memory content before write
                lines_to_scan = content_map[filename].splitlines(keepends=True)
            else:
                # Fall back to reading file from disk
                if filename == 'project-state.json':
                    filepath = self.protocol_root / ".protocol-state" / "project-state.json"
                elif filename == 'domain.record.md':
                    filepath = self.protocol_root / ".dzp-domain" / "domain.record.md"
                elif filename == 'dev-notes.md':
                    filepath = self.protocol_root / ".protocol-state" / "dev-notes.md"
                elif filename == 'security-review.md':
                    filepath = self.protocol_root / ".protocol-state" / "security-review.md"
                else:
                    continue

                if not filepath.exists():
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines_to_scan = f.readlines()
                except Exception as e:
                    print(f"[WARN] Failed to read {filepath} for scanning: {e}")
                    continue

            # Scan lines
            for line_num, line in enumerate(lines_to_scan, 1):
                # SEC-SU-005: Skip very long lines to prevent ReDoS
                if len(line) > 500:
                    secrets_found.append({
                        'file': filename,
                        'line': line_num,
                        'type': 'LONG_LINE_SKIPPED',
                        'confidence': 'info',
                        'preview': f'[SKIPPED - line length {len(line)} exceeds 500 char limit]'
                    })
                    continue

                for secret_type, pattern in patterns.items():
                    if pattern.search(line):
                        # SEC-SU-001: Determine confidence level instead of
                        # silently skipping. ALL matches are reported.
                        line_lower = line.lower()
                        confidence = 'high'

                        if any(indicator in line_lower for indicator in low_confidence_indicators):
                            confidence = 'low'
                        elif secret_type == 'API_KEY':
                            # Generic API key pattern is inherently medium confidence
                            confidence = 'medium'

                        # SEC-SU-004: Redact preview to prevent secret leakage
                        secrets_found.append({
                            'file': filename,
                            'line': line_num,
                            'type': secret_type,
                            'confidence': confidence,
                            'preview': f'[REDACTED {secret_type}]'
                        })

        return secrets_found

    def _git_commit_and_push_with_approval(self, files: List[str], secrets_found: List[Dict]) -> Dict:
        """
        Commit and push project documents with user approval.

        Args:
            files: List of filenames to commit
            secrets_found: List of detected secrets

        Returns:
            Dict with operation results
        """
        result = {
            'attempted': True,
            'success': False,
            'committed': False,
            'pushed': False,
            'user_approved': False,
            'secrets_override': False
        }

        # Map short filenames to full paths
        file_paths = []
        for filename in files:
            if filename == 'project-state.json':
                file_paths.append('.protocol-state/project-state.json')
            elif filename == 'domain.record.md':
                file_paths.append('.dzp-domain/domain.record.md')
            elif filename == 'dev-notes.md':
                file_paths.append('.protocol-state/dev-notes.md')
            elif filename == 'security-review.md':
                file_paths.append('.protocol-state/security-review.md')

        if not file_paths:
            print("[WARN] No files to commit")
            return result

        # Check for secrets
        if secrets_found:
            print(f"\n[WARNING] {len(secrets_found)} potential secrets detected!")
            print("Secrets should not be committed to git.")
            print("\nOptions:")
            print("  1) Abort commit (recommended)")
            print("  2) Review and clean secrets manually, then commit")
            print("  3) Override and commit anyway (NOT RECOMMENDED)")

            # For now, abort if secrets found (can enhance with user input later)
            print("\n[ABORT] Aborting commit due to detected secrets")
            return result

        # User approval for commit
        print(f"\n[GIT] Ready to commit {len(file_paths)} files:")
        for fp in file_paths:
            print(f"  - {fp}")

        print("\nCommit message: 'chore(session): Project documents checkpoint sync'")
        print("\nOptions:")
        print("  1) Commit and push to remote (default)")
        print("  2) Commit locally only")
        print("  3) Skip git operations")

        # For now, return with 'user_approved': False
        # In production, this would prompt for user input
        print("\n[INFO] Git operations require explicit user approval")
        print("[INFO] Run '/session commit' to complete git operations")

        return result


def main():
    """Command-line interface for session monitoring."""
    import sys
    import io

    # Fix Windows console encoding for emojis
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    protocol_root = Path.cwd()

    try:
        monitor = SessionMonitor(protocol_root)
    except Exception as e:
        print(f"[ERROR] Failed to initialize SessionMonitor: {e}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python session_monitor.py <command>")
        print("")
        print("Session Management:")
        print("  start, new-session         Start a new work session")
        print("  update                     Full sync: timestamp + doc sync + Cortex index")
        print("  update --time-only         Timestamp only (fast, for internal callers)")
        print("  sync                       Comprehensive project documents sync (domain.record, dev-notes, security-review, project-state)")
        print("  sync --no-git              Sync documents without git operations")
        print("  end                        End the current session")
        print("  reset                      Reset session state (clear all data)")
        print("")
        print("Monitoring & Alerts:")
        print("  check                      Check if alert is needed")
        print("  check --debounce=N         Check with custom debounce threshold (15-60 min)")
        print("  check-and-record           Check for alert AND auto-record if detected")
        print("  record-choice <choice>     Record user's alert response (save_and_break|continue)")
        print("  status, summary            Show current session summary")
        print("")
        print("Break Management:")
        print("  break [minutes]            Record a break (default: 15 minutes)")
        print("  continue, resume           Resume work after break")
        print("")
        print("Agent Invocation Tracking (v8.13.0):")
        print("  record-invocation <agent>  Record agent invocation for bypass detection")
        print("                             Use --routed flag if invocation was routed via Gojo")
        print("")
        print("Utilities:")
        print("  test                       Test alert rendering")
        print("  help                       Show this help message")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start" or command == "new-session":
        monitor.start_session()
    elif command == "update":
        # Workstream B: 'update' is now the full-sync orchestrator.
        # --time-only flag preserves the OLD timestamp-only behaviour for fast/internal callers.
        # check-and-record / continue / resume are unaffected (they call update_interaction directly).
        time_only = "--time-only" in sys.argv
        monitor._cli_update(time_only=time_only)
    elif command == "sync":
        # PATCH-SESSION-UPDATE: Comprehensive project documents sync
        include_git = "--no-git" not in sys.argv
        results = monitor.sync_all_project_documents(include_git_operations=include_git)

        print("\n[SYNC RESULTS]")
        print(f"Documents updated: {len(results['documents_updated'])}")
        for doc in results['documents_updated']:
            print(f"  ✅ {doc}")

        if results['secrets_found']:
            print(f"\n⚠️  Secrets found: {len(results['secrets_found'])}")
            for secret in results['secrets_found']:
                print(f"  - {secret['file']}:{secret['line']} ({secret['type']})")

        if results['errors']:
            print(f"\n❌ Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")

        if results['success']:
            print("\n✅ Sync completed successfully")
        else:
            print("\n⚠️  Sync completed with errors")
            sys.exit(1)
    elif command == "check":
        # v8.13.0 - PATCH-SESSION-004: Support --debounce CLI argument
        debounce_override = None
        if len(sys.argv) > 2 and sys.argv[2].startswith('--debounce'):
            try:
                # Parse --debounce=15 or --debounce 15
                if '=' in sys.argv[2]:
                    debounce_override = int(sys.argv[2].split('=')[1])
                elif len(sys.argv) > 3:
                    debounce_override = int(sys.argv[3])
            except (ValueError, IndexError):
                print("[!] Invalid --debounce format. Use: --debounce=15 or --debounce 15")

        needed, level, context = monitor.check_alert_needed(debounce_override=debounce_override)
        if needed:
            print(f"[!] Alert needed: {level}")
            print(monitor.render_alert(context))
        else:
            print("[OK] No alert needed")
    elif command == "summary" or command == "status":
        # 'status' is an alias for 'summary' (industry standard expectation)
        print(monitor.get_session_summary())
    elif command == "end":
        monitor.end_session()
    elif command == "break":
        # Record break with optional duration argument
        # PATCH-SEC-005: Validate duration to prevent DoS via infinite loops
        duration = 15  # default
        if len(sys.argv) > 2:
            try:
                duration = int(sys.argv[2])
                if duration < MIN_BREAK_DURATION or duration > MAX_BREAK_DURATION:
                    print(
                        f"[ERROR] Break duration must be between {MIN_BREAK_DURATION}-{MAX_BREAK_DURATION} minutes",
                        file=sys.stderr
                    )
                    print(f"        You requested: {duration} minutes", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"[ERROR] Invalid duration: {sys.argv[2]} (must be a number)", file=sys.stderr)
                sys.exit(1)
        monitor.record_break(duration)
    elif command == "continue" or command == "resume":
        # Resume work after break (just update interaction timestamp)
        # PATCH-SEC-007 (SEC-004): Add error handling
        try:
            state = monitor.update_interaction()
            timestamp = datetime.now(timezone.utc).strftime('%H:%M')
            print(f"[OK] Work resumed at {timestamp}")
            print(f"    Total session time: {state['session_metrics']['total_duration_minutes']} minutes")
        except Exception as e:
            print(f"[ERROR] Failed to resume session: {e}", file=sys.stderr)
            print(f"        Try starting a new session with 'start' or 'new-session'", file=sys.stderr)
            sys.exit(1)
    elif command == "reset":
        # Reset session state completely
        # PATCH-SEC-007: Atomic reset with backup verification
        if monitor.state_file.exists():
            try:
                # Create timestamped backup
                backup_timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                backup_filename = f"session-state.backup.{backup_timestamp}.json"
                backup_path = monitor.state_file.parent / backup_filename

                # Copy to backup location
                shutil.copy2(monitor.state_file, backup_path)

                # CRITICAL: Verify backup integrity before deletion
                if not backup_path.exists() or backup_path.stat().st_size == 0:
                    raise IOError("Backup verification failed: file missing or empty")

                # Verify backup is valid JSON
                with open(backup_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Will raise exception if corrupted

                print(f"[OK] Backup created and verified: {backup_filename}")

                # PATCH-SEC-007 (SEC-003): Clean up old backups (keep last 10)
                backup_pattern = monitor.state_file.parent.glob('session-state.backup.*.json')
                backups = sorted(backup_pattern, key=lambda p: p.stat().st_mtime)
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                    print(f"[INFO] Cleaned up {len(backups) - 10} old backup(s)")

                # Only delete after verified backup exists
                monitor.state_file.unlink()
                print(f"[DELETE] Removed: {monitor.state_file.name}")

                # Recreate with default state
                monitor._ensure_state_file()
                print("[OK] Session state reset successfully")
                print(f"     New state file created at: {monitor.state_file}")

            except (IOError, OSError, PermissionError) as e:
                print(f"[ERROR] Backup failed: {e}", file=sys.stderr)
                print(f"        Session state NOT reset (original preserved)", file=sys.stderr)
                sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Backup verification failed: Invalid JSON ({e})", file=sys.stderr)
                print(f"        Session state NOT reset (original preserved)", file=sys.stderr)
                # Clean up corrupted backup
                if backup_path.exists():
                    backup_path.unlink()
                sys.exit(1)
        else:
            print("[INFO] No session state file found (already reset)")
            print("       Use 'start' or 'new-session' to begin a new work session")
    elif command == "record-choice":
        # PATCH-SESSION-003: Record user's alert response choice
        # Enables Gojo to record user decisions via CLI
        if len(sys.argv) < 3:
            print("Usage: python session_monitor.py record-choice <save_and_break|continue>", file=sys.stderr)
            print("", file=sys.stderr)
            print("This command records the user's response to a work session alert.", file=sys.stderr)
            print("It increments alert counters and updates escalation state.", file=sys.stderr)
            sys.exit(1)

        choice = sys.argv[2]
        try:
            state = monitor.record_user_choice(choice)
            print(f"[OK] User choice '{choice}' recorded successfully")
            print(f"    Alert count: {state['current_session']['alert_count']}")
            print(f"    Escalation level: {state['current_session']['escalation_level']}")
            if state['current_session']['high_risk_operations_blocked']:
                print("[!] High-risk operations now blocked (6+ hours with 'continue')")
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
    elif command == "check-and-record":
        # PATCH-SESSION-003: Check for alert AND auto-record if detected
        # Provides defense-in-depth (alerts recorded even if user choice workflow fails)
        needed, level, context = monitor.check_alert_needed()
        if needed:
            # Auto-increment alert counters when alert detected
            state = monitor.load_state()
            state['current_session']['alert_count'] += 1
            state['current_session']['last_alert_time'] = datetime.now(timezone.utc).isoformat()
            state['session_metrics']['alerts_issued'] += 1
            monitor.save_state(state)

            print(f"[!] Alert detected and recorded: {level}")
            print(f"    Alert count: {state['current_session']['alert_count']}")
            print("")
            print(monitor.render_alert(context))
        else:
            print("[OK] No alert needed")
    elif command == "record-invocation":
        # PATCH-SESSION-004 Component 5: Record agent invocation for bypass detection
        if len(sys.argv) < 3:
            print("Usage: python session_monitor.py record-invocation <agent_name> [--routed]", file=sys.stderr)
            print("", file=sys.stderr)
            print("This command records agent invocations for bypass detection.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Arguments:", file=sys.stderr)
            print("  agent_name    Name of agent (gojo, yuuji, megumi, nobara, todo, maki, panda, inumaki, sukuna)", file=sys.stderr)
            print("  --routed      Flag to indicate invocation was routed via Gojo (default: direct)", file=sys.stderr)
            print("", file=sys.stderr)
            print("Examples:", file=sys.stderr)
            print("  python session_monitor.py record-invocation yuuji", file=sys.stderr)
            print("  python session_monitor.py record-invocation yuuji --routed", file=sys.stderr)
            sys.exit(1)

        agent_name = sys.argv[2]
        is_direct = "--routed" not in sys.argv

        try:
            tracker = monitor.record_agent_invocation(agent_name, is_direct=is_direct)
            invocation_type = "direct" if is_direct else "routed"
            print(f"[OK] Recorded {invocation_type} invocation of {agent_name}")

            # Show current stats
            agent_data = tracker.get('invocations', {}).get(agent_name.lower(), {})
            print(f"    Total invocations: {agent_data.get('total_count', 0)}")
            if agent_name.lower() != 'gojo':
                print(f"    Direct: {agent_data.get('direct_invocations', 0)}, Routed: {agent_data.get('routed_invocations', 0)}")

            # Check for bypass alerts
            bypass_alerts = tracker.get('bypass_detection', {}).get('bypass_alerts', [])
            if bypass_alerts:
                recent_alerts = [a for a in bypass_alerts if a.get('agent') == agent_name.lower()][-3:]
                if recent_alerts:
                    print(f"    [!] Recent bypass alerts: {len(recent_alerts)}")
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
    elif command == "test":
        # Test alert rendering
        test_context = {
            "duration_minutes": 250,
            "duration_formatted": "4 hours 10 minutes",
            "alert_level": "standard",
            "is_late_night": False,
            "continuous_minutes": 250,
            "alert_count": 1
        }
        print(monitor.render_alert(test_context))
    elif command == "help" or command == "--help" or command == "-h":
        # Show help
        print("Domain Zero Protocol - Work Session Monitor v8.13.0")
        print("")
        print("Usage: python session_monitor.py <command>")
        print("")
        print("Session Management:")
        print("  start, new-session         Start a new work session")
        print("  update                     Record an interaction (updates duration)")
        print("  end                        End the current session")
        print("  reset                      Reset session state (clear all data)")
        print("")
        print("Monitoring & Alerts:")
        print("  check                      Check if alert is needed")
        print("  check --debounce=N         Check with custom debounce threshold (15-60 min)")
        print("  check-and-record           Check for alert AND auto-record if detected")
        print("  record-choice <choice>     Record user's alert response (save_and_break|continue)")
        print("  status, summary            Show current session summary")
        print("")
        print("Break Management:")
        print("  break [minutes]            Record a break (default: 15 minutes)")
        print("  continue, resume           Resume work after break")
        print("")
        print("Agent Invocation Tracking (v8.13.0):")
        print("  record-invocation <agent>  Record agent invocation for bypass detection")
        print("                             Use --routed flag if invocation was routed via Gojo")
        print("")
        print("Utilities:")
        print("  test                       Test alert rendering")
        print("  help                       Show this help message")
        print("")
        print("Examples:")
        print("  python session_monitor.py start              # Start new session")
        print("  python session_monitor.py status             # Check current status")
        print("  python session_monitor.py check              # Check for alerts")
        print("  python session_monitor.py check --debounce=20  # Check with 20-min debounce")
        print("  python session_monitor.py break 15           # Take 15-min break")
        print("  python session_monitor.py continue           # Resume after break")
        print("  python session_monitor.py record-invocation yuuji  # Record Yuuji invocation")
        print("  python session_monitor.py end                # End session")
    else:
        print(f"Unknown command: {command}")
        print(f"Run 'python session_monitor.py help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
