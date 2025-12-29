#!/usr/bin/env python3
"""
Domain Zero Protocol - Session Monitoring Effectiveness Dashboard
Version: 8.12.0 (PATCH-SESSION-004 - Component 3)
Purpose: Analyze session monitoring effectiveness and detect alert undercount

This dashboard provides visibility into session monitoring health by:
- Verifying AUTO-INVOKED section integrity in gojo.agent.md
- Calculating expected vs actual alert count
- Detecting alert undercount (coverage gap indicator)
- Generating formatted dashboard report

Usage:
    python .protocol-state/session-monitoring-report.py
    python .protocol-state/session-monitoring-report.py --json
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional


class SessionMonitoringDashboard:
    """Analyze and report on session monitoring effectiveness."""

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)
        self.state_file = self.protocol_root / ".protocol-state" / "session-state.json"
        self.gojo_file = self.protocol_root / "protocol" / "gojo.agent.md"
        self.json_output = "--json" in sys.argv

        # AUTO-INVOKED section markers (PATCH-SESSION-004)
        self.opening_marker = "<!-- CRITICAL: DO NOT REMOVE - SAFETY SYSTEM"
        self.closing_marker = "<!-- END CRITICAL SAFETY SYSTEM SECTION -->"
        self.section_header = "### AUTO-INVOKED SESSION ALERT CHECK"

    def check_auto_invoked_integrity(self) -> Tuple[bool, str]:
        """
        Check if AUTO-INVOKED section exists and is intact.

        Returns:
            (is_intact, status_message)
        """
        if not self.gojo_file.exists():
            return False, "ERROR: gojo.agent.md not found"

        try:
            with open(self.gojo_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            return False, f"ERROR: Cannot read gojo.agent.md: {e}"

        # Check for all required markers
        has_opening = self.opening_marker in content
        has_closing = self.closing_marker in content
        has_header = self.section_header in content

        if has_opening and has_closing and has_header:
            return True, "INTACT"
        else:
            missing = []
            if not has_opening:
                missing.append("opening marker")
            if not has_closing:
                missing.append("closing marker")
            if not has_header:
                missing.append("section header")
            return False, f"MISSING: {', '.join(missing)}"

    def calculate_expected_alerts(self, duration_minutes: int) -> int:
        """
        Calculate expected number of alerts based on session duration.

        Alert schedule:
        - 4h (240 min): First alert
        - 4h 45min (285 min): Second alert if user chose "continue" (escalation every 45 min)
        - 5h 30min (330 min): Third alert
        - 6h 15min (375 min): Fourth alert
        - etc.

        Args:
            duration_minutes: Total session duration

        Returns:
            Expected alert count
        """
        if duration_minutes < 240:  # Less than 4 hours
            return 0

        # First alert at 4 hours
        expected_count = 1

        # Escalated alerts every 45 minutes after first alert
        # (assuming user always chooses "continue")
        remaining_minutes = duration_minutes - 240
        escalated_alerts = remaining_minutes // 45

        expected_count += escalated_alerts
        return expected_count

    def analyze_alert_effectiveness(self) -> Dict:
        """
        Analyze alert effectiveness by comparing actual vs expected alerts.

        Returns:
            Analysis results dictionary
        """
        # Load session state
        if not self.state_file.exists():
            return {
                "error": "session-state.json not found",
                "session_active": False
            }

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            return {
                "error": f"Cannot read session state: {e}",
                "session_active": False
            }

        # Check if session is active
        if not state.get('current_session', {}).get('session_active'):
            return {
                "error": None,
                "session_active": False,
                "message": "No active session"
            }

        # Extract session metrics
        current = state['current_session']
        metrics = state['session_metrics']

        start_time_str = current.get('start_time')
        if not start_time_str:
            return {
                "error": "Missing start_time in session state",
                "session_active": True
            }

        try:
            start_time = datetime.fromisoformat(start_time_str)
        except (ValueError, TypeError):
            return {
                "error": "Invalid start_time format",
                "session_active": True
            }

        # Calculate current duration
        now = datetime.now()
        duration_minutes = int((now - start_time).total_seconds() / 60)

        # Get actual alerts
        actual_alerts = current.get('alert_count', 0)

        # Calculate expected alerts
        expected_alerts = self.calculate_expected_alerts(duration_minutes)

        # Calculate effectiveness
        if expected_alerts > 0:
            effectiveness_pct = (actual_alerts / expected_alerts) * 100
        else:
            effectiveness_pct = 100.0  # No alerts expected yet

        # Determine status
        if actual_alerts < expected_alerts:
            status = "UNDERCOUNT"
        elif actual_alerts == expected_alerts:
            status = "OK"
        else:
            status = "OVERCOUNT"  # Shouldn't happen, but handle it

        return {
            "error": None,
            "session_active": True,
            "session_id": current.get('session_id'),
            "duration_minutes": duration_minutes,
            "duration_formatted": self._format_duration(duration_minutes),
            "actual_alerts": actual_alerts,
            "expected_alerts": expected_alerts,
            "effectiveness_pct": effectiveness_pct,
            "status": status,
            "alert_undercount": expected_alerts - actual_alerts,
            "escalation_level": current.get('escalation_level', 0),
            "last_alert_time": current.get('last_alert_time'),
            "total_breaks": metrics.get('total_breaks', 0)
        }

    def generate_report(self) -> str:
        """
        Generate formatted dashboard report.

        Returns:
            Formatted report string
        """
        # Check AUTO-INVOKED integrity
        auto_invoked_intact, auto_invoked_status = self.check_auto_invoked_integrity()

        # Analyze alert effectiveness
        analysis = self.analyze_alert_effectiveness()

        if self.json_output:
            # JSON output for programmatic consumption
            output = {
                "auto_invoked_section": {
                    "intact": auto_invoked_intact,
                    "status": auto_invoked_status
                },
                "session_analysis": analysis
            }
            return json.dumps(output, indent=2)

        # Text dashboard output
        lines = []
        lines.append("=" * 60)
        lines.append("SESSION MONITORING DASHBOARD (v8.12.0)")
        lines.append("=" * 60)
        lines.append("")

        # AUTO-INVOKED Section Status
        lines.append("AUTO-INVOKED Section:")
        if auto_invoked_intact:
            lines.append("  Status: [OK] INTACT")
        else:
            lines.append(f"  Status: [!] {auto_invoked_status}")
            lines.append("  Action: Run 'python scripts/verify-auto-invoked.py' for details")
        lines.append("")

        # Session Analysis
        if analysis.get("error"):
            lines.append(f"Session Analysis: [ERROR] {analysis['error']}")
        elif not analysis.get("session_active"):
            lines.append("Session Analysis: No active session")
        else:
            lines.append("Session Analysis:")
            lines.append(f"  Session ID: {analysis['session_id']}")
            lines.append(f"  Duration: {analysis['duration_formatted']} ({analysis['duration_minutes']} min)")
            lines.append(f"  Alerts Issued: {analysis['actual_alerts']}")
            lines.append(f"  Expected Alerts: {analysis['expected_alerts']}")
            lines.append(f"  Effectiveness: {analysis['effectiveness_pct']:.1f}%")
            lines.append("")

            # Status indicator
            if analysis['status'] == "OK":
                lines.append("  Status: [OK] Alert system functioning correctly")
            elif analysis['status'] == "UNDERCOUNT":
                lines.append(f"  Status: [!] UNDERCOUNT detected")
                lines.append(f"  Missing: {analysis['alert_undercount']} alert(s)")
                lines.append("")
                lines.append("  Possible causes:")
                lines.append("    - Debounce blocking alerts (check last_alert_time)")
                lines.append("    - AUTO-INVOKED section not being called")
                lines.append("    - Context compaction removed enforcement code")
            elif analysis['status'] == "OVERCOUNT":
                lines.append(f"  Status: [!] More alerts than expected (unusual)")
                lines.append(f"  Extra: {analysis['actual_alerts'] - analysis['expected_alerts']} alert(s)")

            lines.append("")
            lines.append(f"  Escalation Level: {analysis['escalation_level']}")
            lines.append(f"  Total Breaks: {analysis['total_breaks']}")
            if analysis['last_alert_time']:
                try:
                    last_alert = datetime.fromisoformat(analysis['last_alert_time'])
                    minutes_since = int((datetime.now() - last_alert).total_seconds() / 60)
                    lines.append(f"  Last Alert: {minutes_since} minutes ago")
                except (ValueError, TypeError):
                    lines.append(f"  Last Alert: Invalid timestamp")
            else:
                lines.append("  Last Alert: Never")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _format_duration(self, minutes: int) -> str:
        """Format duration in human-readable format."""
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            return f"{hours}h {mins}min"
        else:
            return f"{mins}min"


def main():
    """Command-line entry point."""
    protocol_root = Path.cwd()

    dashboard = SessionMonitoringDashboard(protocol_root)
    report = dashboard.generate_report()

    print(report)


if __name__ == "__main__":
    main()
