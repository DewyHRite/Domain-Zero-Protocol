#!/usr/bin/env python3
"""
Domain Zero Protocol - Work Session Monitoring System
Version: 8.6.0
Purpose: Actual implementation of work session tracking and safety alerts

This module provides REAL enforcement of work session monitoring, replacing
the prompt-based theater identified by Sukuna's red team assessment.

Usage:
    From Gojo agent: Read and execute functions to track session state
    From verification scripts: Validate session health and issue alerts
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class SessionMonitor:
    """
    Work session monitoring with real time tracking and enforcement.
    """

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)
        self.state_file = self.protocol_root / ".protocol-state" / "session-state.json"
        self.template_file = self.protocol_root / ".protocol-state" / "work-session-alert.template.md"
        self.config_file = self.protocol_root / "protocol.config.yaml"

        # Load high-risk operation literals (no regex, safer and faster)
        self._high_risk_literals = self._load_high_risk_literals()

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

    def _is_safe_regex(self, pattern: str, max_length: int = 200, timeout_seconds: float = 0.1) -> bool:
        """
        Validate that a regex pattern is safe (not a ReDoS attack).

        Args:
            pattern: Regex pattern string to validate
            max_length: Maximum allowed pattern length
            timeout_seconds: Maximum time allowed for pattern compilation/test

        Returns:
            True if pattern is safe, False otherwise
        """
        # Length check (excessive length is suspicious)
        if len(pattern) > max_length:
            return False

        # Check for catastrophic backtracking patterns
        dangerous_constructs = [
            r'(\w+\*)+',  # Nested quantifiers
            r'(\w+)+\w+', # Overlapping quantifiers
            r'(\w*)*',    # Nested star quantifiers
            r'(\w+)+$',   # Greedy quantifier before anchor
        ]

        for dangerous in dangerous_constructs:
            if re.search(dangerous, pattern):
                return False

        # Try to compile the pattern with a timeout
        try:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Regex compilation timeout")

            # Set timeout (Unix only - Windows will skip this check)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.setitimer(signal.ITIMER_REAL, timeout_seconds)

            # Attempt to compile
            compiled = re.compile(pattern, re.IGNORECASE)

            # Test against a worst-case string
            test_string = 'a' * 100 + 'b'
            compiled.search(test_string)

            # Cancel timeout
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)

            return True

        except (re.error, TimeoutError, Exception):
            return False

    def _ensure_state_file(self):
        """Ensure session state file exists with proper schema."""
        if not self.state_file.exists():
            print(f"⚠️  Session state file not found at {self.state_file}")
            print("Creating default session state...")
            try:
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.state_file, 'w') as f:
                    json.dump(self._default_state(), f, indent=2)
            except (IOError, OSError) as e:
                raise RuntimeError(f"Failed to create session state file at {self.state_file}: {e}")

    def _default_state(self) -> Dict:
        """Return default session state structure."""
        return {
            "_comment": "Domain Zero Protocol - Work Session State Tracking (v8.6.0)",
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
                "initial_alert_minutes": 240,
                "escalated_alert_minutes": 45,
                "critical_session_minutes": 360,
                "max_continuous_minutes": 480,
                "late_night_hour": 22,
                "minimum_break_minutes": 15
            },
            "session_history": [],
            "last_updated": None,
            "protocol_version": "8.6.0"
        }

    def load_state(self) -> Dict:
        """Load current session state from JSON."""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Session state file not found. Returning default state.")
            return self._default_state()
        except json.JSONDecodeError as e:
            print(f"⚠️  Corrupted session state file: {e}. Returning default state.")
            return self._default_state()

    def save_state(self, state: Dict):
        """Save session state to JSON."""
        state['last_updated'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def start_session(self, session_id: Optional[str] = None) -> Dict:
        """
        Start a new work session or continue existing one.

        Returns:
            Updated state with session initialized
        """
        state = self.load_state()
        now = datetime.now()

        # Check if there's an active session from < 30 minutes ago
        if state['current_session']['session_active']:
            try:
                last_time = datetime.fromisoformat(state['current_session']['last_interaction_time'])
                gap_minutes = (now - last_time).total_seconds() / 60
            except (ValueError, TypeError):
                # Invalid timestamp format - treat as expired session
                print(f"⚠️  Invalid timestamp in session state. Starting new session.")
                gap_minutes = float('inf')

            if gap_minutes < 30:
                # Continue existing session
                print(f"📊 Continuing active session (gap: {gap_minutes:.1f} minutes)")
                state['current_session']['last_interaction_time'] = now.isoformat()
                self.save_state(state)
                return state
            else:
                # Session expired, archive it
                print(f"⏸️  Previous session expired ({gap_minutes:.1f} min gap). Starting new session.")
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

        print(f"✅ New session started: {session_id}")
        self.save_state(state)
        return state

    def update_interaction(self, _retry_count: int = 0, _max_retries: int = 1) -> Dict:
        """
        Record a new interaction in the current session.

        Args:
            _retry_count: Internal retry counter (do not set manually)
            _max_retries: Maximum retries for session reset (default: 1)

        Returns:
            Updated state with interaction timestamp

        Raises:
            RuntimeError: If session cannot be started/reset after max retries
        """
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
            print("⚠️  Session start_time is missing. Resetting session.")
            try:
                return self.update_interaction(_retry_count=_retry_count + 1, _max_retries=_max_retries)
            except Exception as e:
                raise RuntimeError(f"Failed to reset session (missing start_time): {e}")

        try:
            start = datetime.fromisoformat(start_time)
        except (ValueError, TypeError):
            print("⚠️  Invalid session start_time format. Resetting session.")
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

    def check_alert_needed(self) -> Tuple[bool, str, Dict]:
        """
        Check if a work session alert should be issued.

        Returns:
            (should_alert, alert_level, alert_context)
            alert_level: "standard", "escalated", "critical"
        """
        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, None, {}

        now = datetime.now()
        start_time = state['current_session'].get('start_time')
        if not start_time:
            print("⚠️  Session start_time is missing. Cannot check alert.")
            return False, None, {}

        try:
            start = datetime.fromisoformat(start_time)
        except (ValueError, TypeError):
            print("⚠️  Invalid session start_time format. Cannot check alert.")
            return False, None, {}

        duration_minutes = (now - start).total_seconds() / 60

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

        Args:
            context: Alert context from check_alert_needed()

        Returns:
            Rendered alert text with placeholders replaced
        """
        if not self.template_file.exists():
            # Return minimal fallback template
            return f"""
⚠️ Extended Work Session Detected

**Duration:** {context.get('duration_formatted', 'Unknown')}
**Project:** {self._get_project_name()}

You have been working for an extended period. Consider taking a break to maintain productivity and reduce errors.

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
            '{LATE_NIGHT_FLAG}': '🌙 YES - Late night work detected' if context.get('is_late_night') else '☀️ No',
            '{CONTINUOUS_FLAG}': f"⚠️ {context.get('continuous_minutes', 0)} minutes without break" if context.get('continuous_minutes', 0) > 120 else '✅ Recent breaks taken',
            '{BREAK_RECOMMENDATION}': self._get_break_recommendation(context),
            '{LATE_NIGHT_THRESHOLD}': f"{state['thresholds']['late_night_hour']}:00"
        }

        # Replace all placeholders
        rendered = template
        for placeholder, value in replacements.items():
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def record_user_choice(self, choice: str) -> Dict:
        """
        Record user's response to work session alert.

        Args:
            choice: "save_and_break" or "continue"

        Returns:
            Updated state
        """
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

        Args:
            duration_minutes: Reported break duration (optional)

        Returns:
            Updated state
        """
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

        print(f"✅ Break recorded at {now.strftime('%H:%M')}")
        self.save_state(state)
        return state

    def end_session(self) -> Dict:
        """
        End the current work session and archive it.

        Returns:
            Updated state with session ended
        """
        state = self.load_state()

        if state['current_session']['session_active']:
            self._archive_session(state)
            print("✅ Session ended and archived")

        self.save_state(state)
        return state

    def is_high_risk_operation(self, command: Optional[str]) -> bool:
        """
        Check if a command is considered high-risk using literal string matching.

        Non-string or empty commands are treated as not high-risk.

        Args:
            command: Command string to check (None or empty treated as non-high-risk)

        Returns:
            True if command is high-risk
        """
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
        state = self.load_state()

        if not state['current_session']['session_active']:
            return False, ""

        # Check if high-risk blocking is enabled
        if state['current_session']['high_risk_operations_blocked']:
            if self.is_high_risk_operation(operation):
                reason = f"🛑 High-risk operation blocked: Extended session ({state['session_metrics']['total_duration_minutes']} min). Take a break first."
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
            return "⚠️ Session state corrupted: start_time missing"

        try:
            start_formatted = datetime.fromisoformat(start_time).strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            start_formatted = "Invalid timestamp"

        summary = f"""
📊 **Work Session Summary**

**Duration:** {self._format_duration(metrics['total_duration_minutes'])}
**Continuous Work:** {self._format_duration(metrics['continuous_work_minutes'])} since last break
**Breaks Taken:** {metrics['total_breaks']}
**Alerts Issued:** {metrics['alerts_issued']}
**Escalation Level:** {current['escalation_level']}
**High-Risk Blocking:** {'🛑 ENABLED' if current['high_risk_operations_blocked'] else '✅ Disabled'}

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
        duration = context.get('duration_minutes', 0)
        is_late = context.get('is_late_night', False)

        if duration >= 360:  # 6+ hours
            return "🛑 STRONGLY RECOMMENDED - End session and rest"
        elif duration >= 300:  # 5 hours
            return "⚠️ Take 15-minute break minimum"
        elif duration >= 240:  # 4 hours
            return "💡 5-10 minute break suggested"
        elif is_late:
            return "🌙 Late night work - consider ending session"
        else:
            return "Continue with awareness"


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
        print(f"❌ Error: Failed to initialize SessionMonitor: {e}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python session_monitor.py <command>")
        print("Commands: start, update, check, summary, end, break, test")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        monitor.start_session()
    elif command == "update":
        state = monitor.update_interaction()
        print(f"Session updated: {state['session_metrics']['total_duration_minutes']} minutes")
    elif command == "check":
        needed, level, context = monitor.check_alert_needed()
        if needed:
            print(f"⚠️  Alert needed: {level}")
            print(monitor.render_alert(context))
        else:
            print("✅ No alert needed")
    elif command == "summary":
        print(monitor.get_session_summary())
    elif command == "end":
        monitor.end_session()
    elif command == "break":
        monitor.record_break(15)
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
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
