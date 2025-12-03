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
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
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

        self._ensure_state_file()

    def _ensure_state_file(self):
        """Ensure session state file exists with proper schema."""
        if not self.state_file.exists():
            print(f"⚠️  Session state file not found at {self.state_file}")
            print("Creating default session state...")
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self._default_state(), f, indent=2)

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
        with open(self.state_file, 'r') as f:
            return json.load(f)

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
            last_time = datetime.fromisoformat(state['current_session']['last_interaction_time'])
            gap_minutes = (now - last_time).total_seconds() / 60

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

    def update_interaction(self) -> Dict:
        """
        Record a new interaction in the current session.

        Returns:
            Updated state with interaction timestamp
        """
        state = self.load_state()

        if not state['current_session']['session_active']:
            # Auto-start session if not active
            return self.start_session()

        now = datetime.now()
        state['current_session']['last_interaction_time'] = now.isoformat()

        # Calculate duration
        start = datetime.fromisoformat(state['current_session']['start_time'])
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
        start = datetime.fromisoformat(state['current_session']['start_time'])
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
            return "⚠️ Work session alert template not found!"

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

    def is_high_risk_operation(self, command: str) -> bool:
        """
        Check if a command is considered high-risk.

        Args:
            command: Command string to check

        Returns:
            True if command is high-risk
        """
        high_risk_patterns = [
            r'git push.*production',
            r'git push.*main',
            r'git push.*master',
            r'deploy.*production',
            r'rm\s+-rf',
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'ALTER\s+TABLE',
            r'npm publish',
            r'docker.*production',
            r'kubectl.*delete',
            r'kubectl.*production'
        ]

        for pattern in high_risk_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        return False

    def should_block_operation(self, operation: str) -> Tuple[bool, str]:
        """
        Check if an operation should be blocked due to session state.

        Args:
            operation: Operation description or command

        Returns:
            (should_block, reason)
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

        summary = f"""
📊 **Work Session Summary**

**Duration:** {self._format_duration(metrics['total_duration_minutes'])}
**Continuous Work:** {self._format_duration(metrics['continuous_work_minutes'])} since last break
**Breaks Taken:** {metrics['total_breaks']}
**Alerts Issued:** {metrics['alerts_issued']}
**Escalation Level:** {current['escalation_level']}
**High-Risk Blocking:** {'🛑 ENABLED' if current['high_risk_operations_blocked'] else '✅ Disabled'}

**Session ID:** {current['session_id']}
**Started:** {datetime.fromisoformat(current['start_time']).strftime('%Y-%m-%d %H:%M')}
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
    monitor = SessionMonitor(protocol_root)

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
