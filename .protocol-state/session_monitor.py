#!/usr/bin/env python3
"""
Domain Zero Protocol - Work Session Monitoring System
Version: 8.8.0
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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Session duration limits (PATCH-SEC-005 - SEC-DZP-008 remediation)
MAX_BREAK_DURATION = 480  # 8 hours
MIN_BREAK_DURATION = 1    # 1 minute
MAX_SESSION_DURATION = 1440  # 24 hours


class SessionMonitor:
    """
    Work session monitoring with real time tracking and enforcement.
    """

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)
        self.state_file = self.protocol_root / ".protocol-state" / "session-state.json"
        self.template_file = self.protocol_root / ".protocol-state" / "work-session-alert.template.md"
        self.config_file = self.protocol_root / "protocol.config.yaml"
        self.invocation_tracker_file = self.protocol_root / ".protocol-state" / "agent-invocation-tracker.json"

        # Load high-risk operation literals (no regex, safer and faster)
        self._high_risk_literals = self._load_high_risk_literals()

        # Load configuration (v8.12.0 - Configuration Enhancements)
        self.enabled = self._load_enabled_flag()
        self.alert_thresholds = self._load_alert_thresholds()
        self.alert_customization = self._load_alert_customization()

        self._ensure_state_file()

    def _load_high_risk_literals(self) -> List[str]:
        """
        Load high-risk operation literal strings from config file.

        Uses literal string matching instead of regex to avoid ReDoS vulnerabilities.
        Matching is case-insensitive via .lower() comparison.

        Returns:
            List of lowercase literal strings to match
        """
        # Default fallback literals (safe, no regex)
        default_literals = [
            'git push origin production',
            'git push origin main',
            'git push origin master',
            'git push --force',
            'git push -f',
            'deploy production',
            'deploy --production',
            'rm -rf',
            'drop table',
            'drop database',
            'delete from',
            'alter table',
            'truncate table',
            'npm publish',
            'docker push',
            'docker production',
            'kubectl delete',
            'kubectl delete namespace',
            'kubectl production',
            'terraform destroy',
            'terraform apply -auto-approve',
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
        v8.12.0 - PATCH-SESSION-004

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

        v8.12.0 - Configuration Enhancement
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

        v8.12.0 - Configuration Enhancement
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

        v8.12.0 - Configuration Enhancement
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
        """Return default session state structure (v8.12.0 - uses loaded thresholds)."""
        return {
            "_comment": "Domain Zero Protocol - Work Session State Tracking (v8.12.0)",
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
            "protocol_version": "8.12.0"
        }

    def load_state(self) -> Dict:
        """Load current session state from JSON."""
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
        """Save session state to JSON with atomic write (SEC-002 FIX)."""
        state['last_updated'] = datetime.now().isoformat()

        # Atomic write pattern
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
            except:
                pass
            raise IOError(f"Failed to save session state: {e}")

    def start_session(self, session_id: Optional[str] = None) -> Dict:
        """
        Start a new work session or continue existing one.

        v8.12.0 - Respects enabled flag

        Returns:
            Updated state with session initialized, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.12.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()
        now = datetime.now()

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

        v8.12.0 - Respects enabled flag

        Args:
            _retry_count: Internal retry counter (do not set manually)
            _max_retries: Maximum retries for session reset (default: 1)

        Returns:
            Updated state with interaction timestamp, or default state if disabled

        Raises:
            RuntimeError: If session cannot be started/reset after max retries
        """
        # Early return if session monitoring is disabled (v8.12.0)
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

        now = datetime.now()
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

        duration_minutes = (now - start).total_seconds() / 60
        state['session_metrics']['total_duration_minutes'] = int(duration_minutes)

        # Update continuous work time (time since last break)
        if state['session_metrics']['break_timestamps']:
            last_break = datetime.fromisoformat(state['session_metrics']['break_timestamps'][-1])
            continuous_minutes = (now - last_break).total_seconds() / 60
        else:
            continuous_minutes = duration_minutes

        state['session_metrics']['continuous_work_minutes'] = int(continuous_minutes)

        self.save_state(state)
        return state

    def check_alert_needed(self, debounce_override: int = None) -> Tuple[bool, str, Dict]:
        """
        Check if a work session alert should be issued.

        v8.12.0 - Respects enabled flag

        Args:
            debounce_override: CLI --debounce argument (v8.12.0)

        Returns:
            (should_alert, alert_level, alert_context)
            alert_level: "standard", "escalated", "critical"
        """
        # Early return if session monitoring is disabled (v8.12.0)
        if not self.enabled:
            return False, None, {}

        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, None, {}

        now = datetime.now()
        start_time = state['current_session'].get('start_time')
        if not start_time:
            print("[!] Session start_time is missing. Cannot check alert.")
            return False, None, {}

        try:
            start = datetime.fromisoformat(start_time)
        except (ValueError, TypeError):
            print("[!] Invalid session start_time format. Cannot check alert.")
            return False, None, {}

        duration_minutes = (now - start).total_seconds() / 60

        # Debounce check (v8.12.0 - PATCH-SESSION-004)
        # Skip alert if last alert was too recent (prevents spam during rapid prototyping)
        debounce_threshold = self._load_debounce_config(cli_override=debounce_override)
        last_alert_time = state['current_session'].get('last_alert_time')

        if last_alert_time:
            try:
                last_alert = datetime.fromisoformat(last_alert_time)
                minutes_since_last_alert = (now - last_alert).total_seconds() / 60

                if minutes_since_last_alert < debounce_threshold:
                    # Alert debounced - too soon since last alert
                    return False, None, {}
            except (ValueError, TypeError):
                # Invalid timestamp format - proceed with alert check
                pass

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
            last_alert = state['current_session']['last_alert_time']
            if last_alert:
                last_alert_time = datetime.fromisoformat(last_alert)
                minutes_since_alert = (now - last_alert_time).total_seconds() / 60

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

        v8.12.0 - Enhanced with custom message injection

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

        now = datetime.now()
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

        # Inject custom messages (v8.12.0)
        custom_msg = self._inject_custom_messages(context)
        if custom_msg:
            # Append custom messages after the standard template
            rendered += f"\n\n---\n\n{custom_msg}"

        return rendered

    def record_user_choice(self, choice: str) -> Dict:
        """
        Record user's response to work session alert.

        v8.12.0 - Respects enabled flag

        Args:
            choice: "save_and_break" or "continue"

        Returns:
            Updated state, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.12.0)
        if not self.enabled:
            return self._default_state()

        # Validate input
        if choice not in ["save_and_break", "continue"]:
            raise ValueError(f"Invalid choice '{choice}'. Must be 'save_and_break' or 'continue'.")

        state = self.load_state()
        now = datetime.now()

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

        v8.12.0 - Respects enabled flag

        Args:
            duration_minutes: Reported break duration (optional)

        Returns:
            Updated state, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.12.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()
        now = datetime.now()

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

        v8.12.0 - Respects enabled flag

        Returns:
            Updated state with session ended, or default state if disabled
        """
        # Early return if session monitoring is disabled (v8.12.0)
        if not self.enabled:
            return self._default_state()

        state = self.load_state()

        if state['current_session']['session_active']:
            self._archive_session(state)
            print("[OK] Session ended and archived")

        self.save_state(state)
        return state

    def is_high_risk_operation(self, command: Optional[str]) -> bool:
        """
        Check if a command is considered high-risk using literal string matching.

        v8.12.0 - Respects enabled flag

        Non-string or empty commands are treated as not high-risk.

        Args:
            command: Command string to check (None or empty treated as non-high-risk)

        Returns:
            True if command is high-risk, False if disabled or non-high-risk
        """
        # Early return if session monitoring is disabled (v8.12.0)
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
        # Early return if session monitoring is disabled (v8.12.0)
        if not self.enabled:
            return False, ""

        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, ""

        duration_minutes = state['session_metrics']['total_duration_minutes']
        thresholds = state['thresholds']

        # Check if 8-hour maximum continuous work threshold reached - BLOCK ALL OPERATIONS
        if duration_minutes >= thresholds['max_continuous_minutes']:
            reason = f"[BLOCKED] MAXIMUM WORK LIMIT REACHED: {duration_minutes} minutes ({duration_minutes // 60}+ hours). You MUST take a break. Session is now read-only."
            return True, reason

        # Check if 6-hour critical threshold reached - block high-risk operations only
        if state['current_session']['high_risk_operations_blocked']:
            if self.is_high_risk_operation(operation):
                reason = f"[BLOCKED] High-risk operation blocked: Extended session ({duration_minutes} min). Take a break first."
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

        summary = f"""
[STATUS] **Work Session Summary**

**Duration:** {self._format_duration(metrics['total_duration_minutes'])}
**Continuous Work:** {self._format_duration(metrics['continuous_work_minutes'])} since last break
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
            archived = {
                "session_id": state['current_session']['session_id'],
                "start_time": state['current_session']['start_time'],
                "end_time": datetime.now().isoformat(),
                "total_duration_minutes": state['session_metrics']['total_duration_minutes'],
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

    def _get_project_name(self) -> str:
        """Get current project name from protocol root."""
        return self.protocol_root.name

    def _get_break_recommendation(self, context: Dict) -> str:
        """Generate break recommendation based on context."""
        # Use custom message if configured (v8.12.0)
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

        v8.12.0 - Configuration Enhancement

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

        v8.12.0 - PATCH-SESSION-004 Component 5

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

        # Load tracker state
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
        now = datetime.now().isoformat()
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
                        duration_minutes = int((datetime.now() - start_time).total_seconds() / 60)

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

        # Save updated tracker (SEC-001 FIX: atomic write)
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
        print("Agent Invocation Tracking (v8.12.0):")
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
        state = monitor.update_interaction()
        print(f"Session updated: {state['session_metrics']['total_duration_minutes']} minutes")
    elif command == "check":
        # v8.12.0 - PATCH-SESSION-004: Support --debounce CLI argument
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
            timestamp = datetime.now().strftime('%H:%M')
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
                backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
            state['current_session']['last_alert_time'] = datetime.now().isoformat()
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
        print("Domain Zero Protocol - Work Session Monitor v8.12.0")
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
        print("Agent Invocation Tracking (v8.12.0):")
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
