#!/usr/bin/env python3
"""
Tier Statistics Management Utility (v8.8.0)

PURPOSE: Automatic tracking and reporting of tier system usage across all agents.

CAPABILITIES:
  - Record tier events (selection, completion, bypass, violations)
  - Calculate statistics (distribution, averages, compliance rates)
  - Generate reports (CLI, markdown, JSON)
  - Integrate with project-state.json
  - Support Gojo Trigger 19 intelligence reports

USAGE:
  python tier-statistics.py --view                    # View current statistics
  python tier-statistics.py --record --event [event]  # Record tier event
  python tier-statistics.py --report --format markdown # Generate report
  python tier-statistics.py --reset --force           # Reset statistics

EVENTS:
  - tier_selected: User specifies tier for feature
  - tier_completed: Feature completes with tier compliance
  - tier_bypassed: User explicitly bypasses tier requirements
  - tier_violated: Agent detects tier compliance violation
  - tier_transitioned: Feature moves between tiers

INTEGRATION:
  - Reads/writes .protocol-state/project-state.json
  - Uses verify_working_directory.py for safety
  - Called automatically by agents (Yuuji, Megumi, Gojo)
  - Manual invocation for reporting/diagnostics

VERSION: 8.8.0
CREATED: 2025-12-06 (Phase 4 Week 2)
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import argparse

# F16: Insert scripts/ on sys.path before the import so this script can be
# invoked from the project root (python .protocol-state/tier-statistics.py).
# Without this, verify_working_directory.py (which lives in scripts/) is not
# on the path and the import fails with an unhandled ImportError.
import sys as _sys
from pathlib import Path as _Path
_scripts_dir = str(_Path(__file__).resolve().parent.parent / "scripts")
if _scripts_dir not in _sys.path:
    _sys.path.insert(0, _scripts_dir)

# Import working directory verification
try:
    from verify_working_directory import verify_project_root
except ImportError:
    print("[ERROR] Cannot import verify_working_directory.py")
    print("  Ensure verify_working_directory.py exists in scripts/")
    sys.exit(1)

# PATCH-STATE-001: Import centralized state manager
try:
    # Add .protocol-state to path for importing ProjectStateManager
    protocol_state_dir = Path(__file__).parent.parent / ".protocol-state"
    if str(protocol_state_dir) not in sys.path:
        sys.path.insert(0, str(protocol_state_dir))

    from project_state_manager import ProjectStateManager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False
    # Silent fallback to legacy file I/O for backward compatibility


class TierStatistics:
    """Tier statistics management and reporting"""

    def __init__(self, project_state_path: Path):
        """Initialize tier statistics manager

        Args:
            project_state_path: Path to project-state.json
        """
        self.project_state_path = project_state_path
        self.project_state = self._load_project_state()

        # PATCH-STATE-001: Initialize ProjectStateManager if available
        if STATE_MANAGER_AVAILABLE:
            protocol_root = project_state_path.parent.parent
            self.state_manager = ProjectStateManager(protocol_root)
        else:
            self.state_manager = None

    def _load_project_state(self) -> Dict[str, Any]:
        """Load project state from JSON file

        Returns:
            Project state dictionary
        """
        if not self.project_state_path.exists():
            print(f"[ERROR] project-state.json not found: {self.project_state_path}")
            sys.exit(1)

        try:
            with open(self.project_state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in project-state.json: {e}")
            sys.exit(1)

    def _save_project_state(self):
        """
        Save project state to JSON file

        PATCH-STATE-001: Uses ProjectStateManager when available for atomic writes.
        """
        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                self.state_manager.save_project_state(self.project_state)
                return
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy: {e}")

        # Legacy file I/O (backward compatibility)
        try:
            with open(self.project_state_path, 'w', encoding='utf-8') as f:
                json.dump(self.project_state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save project-state.json: {e}")
            sys.exit(1)

    def _init_statistics(self) -> Dict[str, Any]:
        """Initialize empty tier statistics structure

        Returns:
            Empty statistics dictionary
        """
        return {
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "total_features": 0,
            "tier_distribution": {
                "tier_1": 0,
                "tier_2": 0,
                "tier_3": 0
            },
            "average_time_per_tier": {
                "tier_1": 0.0,
                "tier_2": 0.0,
                "tier_3": 0.0
            },
            "compliance_rate": {
                "tier_1": 1.0,
                "tier_2": 1.0,
                "tier_3": 1.0
            },
            "bypass_count": 0,
            "violation_count": 0,
            "last_30_days": {
                "tier_1": 0,
                "tier_2": 0,
                "tier_3": 0
            },
            "events": []  # Rolling event log (last 100 events)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get current tier statistics

        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.
        Reads from "tier_tracking" namespace (consolidated from tier_statistics).

        Returns:
            Tier statistics dictionary
        """
        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                tier_data = self.state_manager.get_tier_tracking()
                # Ensure tier_data is not deprecated
                if not tier_data.get("_deprecated"):
                    return tier_data
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy: {e}")

        # Legacy file I/O (backward compatibility)
        # Check tier_tracking first (new consolidated name)
        if "tier_tracking" in self.project_state and not self.project_state["tier_tracking"].get("_deprecated"):
            return self.project_state["tier_tracking"]

        # Fallback to legacy tier_statistics name
        if "tier_statistics" not in self.project_state:
            self.project_state["tier_tracking"] = self._init_statistics()
            self._save_project_state()

        return self.project_state.get("tier_tracking", self._init_statistics())

    def _sanitize_input(self, text: str, field_name: str) -> str:
        """Sanitize user input to prevent data pollution

        Args:
            text: Input string to sanitize
            field_name: Name of field (for error reporting)

        Returns:
            Sanitized string (alphanumeric, spaces, hyphens, underscores only)
        """
        import re

        # Allow only alphanumeric, spaces, hyphens, underscores
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '', text)

        # Collapse multiple spaces
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Limit length to 100 characters
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        # Warn if input was modified
        if sanitized != text:
            print(f"[WARNING] {field_name} contained invalid characters and was sanitized")
            print(f"  Original: {text[:50]}...")
            print(f"  Sanitized: {sanitized[:50]}...")

        return sanitized

    def record_event(self, event_type: str, tier: int, agent: str,
                    feature: str, duration_minutes: Optional[int] = None,
                    compliance: Optional[bool] = None):
        """Record a tier event

        Args:
            event_type: Type of event (tier_selected, tier_completed, etc.)
            tier: Tier number (1, 2, or 3)
            agent: Agent name (yuuji, megumi, gojo, etc.)
            feature: Feature name or description
            duration_minutes: Feature duration in minutes (for tier_completed)
            compliance: Whether feature was compliant (for tier_completed)
        """
        stats = self.get_statistics()

        # Sanitize inputs to prevent data pollution
        agent_sanitized = self._sanitize_input(agent, "agent")
        feature_sanitized = self._sanitize_input(feature, "feature")

        # Create event record
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "tier": tier,
            "agent": agent_sanitized,
            "feature": feature_sanitized
        }

        if duration_minutes is not None:
            event["duration_minutes"] = duration_minutes

        if compliance is not None:
            event["compliance"] = compliance

        # Add event to rolling log (keep last 100)
        stats["events"].append(event)
        if len(stats["events"]) > 100:
            stats["events"] = stats["events"][-100:]

        # Update statistics based on event type
        tier_key = f"tier_{tier}"

        if event_type == "tier_selected":
            # Increment tier distribution
            stats["tier_distribution"][tier_key] += 1
            stats["total_features"] += 1

            # Update last 30 days (check if within window)
            stats["last_30_days"][tier_key] += 1

        elif event_type == "tier_completed":
            # Update average time per tier
            if duration_minutes is not None:
                current_avg = stats["average_time_per_tier"][tier_key]
                tier_count = stats["tier_distribution"][tier_key]

                if tier_count > 0:
                    # Calculate new rolling average
                    new_avg = ((current_avg * (tier_count - 1)) + duration_minutes) / tier_count
                    stats["average_time_per_tier"][tier_key] = round(new_avg, 1)

            # Update compliance rate
            if compliance is not None:
                tier_count = stats["tier_distribution"][tier_key]
                if tier_count > 0:
                    # Recalculate compliance rate
                    # This is simplified - in production, you'd track compliant/total separately
                    current_rate = stats["compliance_rate"][tier_key]
                    if compliance:
                        # Compliant - maintain or increase rate
                        new_rate = ((current_rate * (tier_count - 1)) + 1.0) / tier_count
                    else:
                        # Non-compliant - decrease rate
                        new_rate = ((current_rate * (tier_count - 1)) + 0.0) / tier_count
                        stats["violation_count"] += 1

                    stats["compliance_rate"][tier_key] = round(new_rate, 2)

        elif event_type == "tier_bypassed":
            stats["bypass_count"] += 1

        elif event_type == "tier_violated":
            stats["violation_count"] += 1

        # Update timestamp
        stats["last_updated"] = datetime.utcnow().isoformat() + "Z"

        # PATCH-STATE-001: Update self.project_state with modified tier_tracking data
        self.project_state["tier_tracking"] = stats

        # Save changes
        self._save_project_state()

    def generate_report(self, format: str = "text") -> str:
        """Generate tier statistics report

        Args:
            format: Output format (text, markdown, json)

        Returns:
            Formatted report string
        """
        stats = self.get_statistics()

        if format == "json":
            return json.dumps(stats, indent=2)

        elif format == "markdown":
            return self._generate_markdown_report(stats)

        else:  # text
            return self._generate_text_report(stats)

    def _generate_text_report(self, stats: Dict[str, Any]) -> str:
        """Generate plain text report

        Args:
            stats: Statistics dictionary

        Returns:
            Plain text report
        """
        total = stats["total_features"]

        lines = [
            "TIER STATISTICS SUMMARY",
            "=" * 50,
            "",
            f"Total Features: {total}",
            f"Last Updated: {stats['last_updated']}",
            "",
            "Tier Distribution:",
            f"  Tier 1 (Rapid):     {stats['tier_distribution']['tier_1']:3d} features ({self._percent(stats['tier_distribution']['tier_1'], total)})",
            f"  Tier 2 (Standard):  {stats['tier_distribution']['tier_2']:3d} features ({self._percent(stats['tier_distribution']['tier_2'], total)})",
            f"  Tier 3 (Critical):  {stats['tier_distribution']['tier_3']:3d} features ({self._percent(stats['tier_distribution']['tier_3'], total)})",
            "",
            "Compliance Rates:",
            f"  Tier 1: {stats['compliance_rate']['tier_1']*100:5.1f}% {self._check_mark(stats['compliance_rate']['tier_1'])}",
            f"  Tier 2: {stats['compliance_rate']['tier_2']*100:5.1f}% {self._check_mark(stats['compliance_rate']['tier_2'])}",
            f"  Tier 3: {stats['compliance_rate']['tier_3']*100:5.1f}% {self._check_mark(stats['compliance_rate']['tier_3'])}",
            "",
            "Average Time Per Tier:",
            f"  Tier 1: {stats['average_time_per_tier']['tier_1']:5.1f} min (target: 10-15)",
            f"  Tier 2: {stats['average_time_per_tier']['tier_2']:5.1f} min (target: 30-45)",
            f"  Tier 3: {stats['average_time_per_tier']['tier_3']:5.1f} min (target: 60-90)",
            "",
            f"Bypass Count: {stats['bypass_count']}",
            f"Violation Count: {stats['violation_count']}",
            "",
            "Last 30 Days:",
            f"  Tier 1: {stats['last_30_days']['tier_1']}",
            f"  Tier 2: {stats['last_30_days']['tier_2']}",
            f"  Tier 3: {stats['last_30_days']['tier_3']}",
        ]

        return "\n".join(lines)

    def _generate_markdown_report(self, stats: Dict[str, Any]) -> str:
        """Generate markdown report (for Trigger 19 integration)

        Args:
            stats: Statistics dictionary

        Returns:
            Markdown report
        """
        total = stats["total_features"]

        lines = [
            "### TIER USAGE ANALYSIS (v8.8.0)",
            "",
            "**Tier Distribution (Lifetime)**:",
            f"- Tier 1 (Rapid): {stats['tier_distribution']['tier_1']} features ({self._percent(stats['tier_distribution']['tier_1'], total)})",
            f"- Tier 2 (Standard): {stats['tier_distribution']['tier_2']} features ({self._percent(stats['tier_distribution']['tier_2'], total)})",
            f"- Tier 3 (Critical): {stats['tier_distribution']['tier_3']} features ({self._percent(stats['tier_distribution']['tier_3'], total)})",
            "",
            "**Compliance Rates**:",
            f"- Tier 1: {stats['compliance_rate']['tier_1']*100:.0f}% {self._check_mark(stats['compliance_rate']['tier_1'])}",
            f"- Tier 2: {stats['compliance_rate']['tier_2']*100:.0f}% {self._check_mark(stats['compliance_rate']['tier_2'])}",
            f"- Tier 3: {stats['compliance_rate']['tier_3']*100:.0f}% {self._check_mark(stats['compliance_rate']['tier_3'])}",
            "",
            "**Average Time Per Tier**:",
            f"- Tier 1: {stats['average_time_per_tier']['tier_1']:.0f} min {self._time_check(stats['average_time_per_tier']['tier_1'], 10, 15)}",
            f"- Tier 2: {stats['average_time_per_tier']['tier_2']:.0f} min {self._time_check(stats['average_time_per_tier']['tier_2'], 30, 45)}",
            f"- Tier 3: {stats['average_time_per_tier']['tier_3']:.0f} min {self._time_check(stats['average_time_per_tier']['tier_3'], 60, 90)}",
            "",
            f"**Tier Bypass Events**: {stats['bypass_count']} total",
            f"**Tier Violations**: {stats['violation_count']} total",
            "",
            "**Last 30 Days**:",
            f"- Tier 1: {stats['last_30_days']['tier_1']} features",
            f"- Tier 2: {stats['last_30_days']['tier_2']} features",
            f"- Tier 3: {stats['last_30_days']['tier_3']} features",
        ]

        return "\n".join(lines)

    def _percent(self, count: int, total: int) -> str:
        """Calculate percentage string

        Args:
            count: Count value
            total: Total value

        Returns:
            Percentage string (e.g., "25%")
        """
        if total == 0:
            return "0%"
        return f"{(count / total * 100):.0f}%"

    def _check_mark(self, compliance_rate: float) -> str:
        """Get check mark for compliance rate

        Args:
            compliance_rate: Compliance rate (0.0-1.0)

        Returns:
            Check mark or warning symbol
        """
        if compliance_rate >= 0.95:
            return "[OK]"
        elif compliance_rate >= 0.85:
            return "[WARN]"
        else:
            return "[FAIL]"

    def _time_check(self, avg_time: float, min_target: int, max_target: int) -> str:
        """Check if average time is within target range

        Args:
            avg_time: Average time in minutes
            min_target: Minimum target time
            max_target: Maximum target time

        Returns:
            Status indicator
        """
        if avg_time == 0:
            return ""
        elif min_target <= avg_time <= max_target:
            return "(within target)"
        elif avg_time < min_target:
            return "(faster than target)"
        else:
            return "(slower than target)"

    def reset_statistics(self):
        """
        Reset all tier statistics to zero

        PATCH-STATE-001: Resets tier_tracking namespace (consolidated from tier_statistics).
        """
        self.project_state["tier_tracking"] = self._init_statistics()
        self._save_project_state()
        print("[OK] Tier statistics reset to zero")


def main():
    """Main entry point for tier-statistics.py"""

    parser = argparse.ArgumentParser(
        description="Tier Statistics Management Utility (v8.8.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View current statistics
  python tier-statistics.py --view

  # Record tier selection
  python tier-statistics.py --record --event tier_selected --tier 2 --agent yuuji --feature "user auth"

  # Record tier completion
  python tier-statistics.py --record --event tier_completed --tier 2 --agent yuuji --feature "user auth" --duration 38 --compliance true

  # Generate markdown report (for Trigger 19)
  python tier-statistics.py --report --format markdown

  # Reset statistics (requires --force)
  python tier-statistics.py --reset --force
        """
    )

    parser.add_argument('--view', action='store_true',
                       help='View current tier statistics')
    parser.add_argument('--record', action='store_true',
                       help='Record a tier event')
    parser.add_argument('--report', action='store_true',
                       help='Generate tier statistics report')
    parser.add_argument('--reset', action='store_true',
                       help='Reset tier statistics (requires --force)')

    # Record event arguments
    parser.add_argument('--event', type=str,
                       choices=['tier_selected', 'tier_completed', 'tier_bypassed', 'tier_violated', 'tier_transitioned'],
                       help='Event type to record')
    parser.add_argument('--tier', type=int, choices=[1, 2, 3],
                       help='Tier number (1, 2, or 3)')
    parser.add_argument('--agent', type=str,
                       help='Agent name (yuuji, megumi, gojo, etc.)')
    parser.add_argument('--feature', type=str,
                       help='Feature name or description')
    parser.add_argument('--duration', type=int,
                       help='Feature duration in minutes (for tier_completed)')
    parser.add_argument('--compliance', type=str, choices=['true', 'false'],
                       help='Compliance status (for tier_completed)')

    # Report arguments
    parser.add_argument('--format', type=str, default='text',
                       choices=['text', 'markdown', 'json'],
                       help='Report format (default: text)')

    # Reset arguments
    parser.add_argument('--force', action='store_true',
                       help='Force reset without confirmation')

    args = parser.parse_args()

    # Verify working directory
    if not verify_project_root(silent=False, exit_on_failure=True):
        sys.exit(1)

    # Initialize tier statistics manager
    project_root = Path.cwd()
    project_state_path = project_root / ".protocol-state" / "project-state.json"

    tier_stats = TierStatistics(project_state_path)

    # Handle commands
    if args.view:
        # View current statistics
        report = tier_stats.generate_report(format='text')
        print(report)

    elif args.record:
        # Record tier event
        if not all([args.event, args.tier, args.agent, args.feature]):
            print("[ERROR] --record requires: --event, --tier, --agent, --feature")
            sys.exit(1)

        # Parse compliance
        compliance = None
        if args.compliance:
            compliance = args.compliance.lower() == 'true'

        tier_stats.record_event(
            event_type=args.event,
            tier=args.tier,
            agent=args.agent,
            feature=args.feature,
            duration_minutes=args.duration,
            compliance=compliance
        )

        print(f"[OK] Recorded {args.event} for Tier {args.tier} ({args.feature})")

    elif args.report:
        # Generate report
        report = tier_stats.generate_report(format=args.format)
        print(report)

    elif args.reset:
        # Reset statistics
        if not args.force:
            print("[ERROR] --reset requires --force flag for confirmation")
            print("  This will permanently delete all tier statistics")
            sys.exit(1)

        tier_stats.reset_statistics()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
