#!/usr/bin/env python3
"""
Domain Zero Protocol - Troubleshooting Session Tracker
Version: 1.0.0
Purpose: Unified tracking for all /ts tier commands

This module provides centralized troubleshooting session tracking for the
Domain Zero Protocol tier system (Tier 1-5).

Usage:
    python troubleshooting_tracker.py start <tier> "<description>"
    python troubleshooting_tracker.py update "<progress note>"
    python troubleshooting_tracker.py complete "<resolution>"
    python troubleshooting_tracker.py escalate <new_tier>
    python troubleshooting_tracker.py status
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Import path_validator for input validation (security enhancement)
try:
    sys.path.insert(0, str(Path(__file__).parent / "security"))
    from path_validator import validate_file_path
    PATH_VALIDATOR_AVAILABLE = True
except ImportError:
    PATH_VALIDATOR_AVAILABLE = False
    def validate_file_path(path: str) -> bool:
        """Fallback validator if path_validator not available"""
        return True  # No validation if module missing

# PATCH-STATE-001: Import centralized state manager
try:
    from project_state_manager import ProjectStateManager
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False
    # Silent fallback to legacy file I/O for backward compatibility


class TroubleshootingTracker:
    """
    Troubleshooting session tracking with state management.

    Tracks all troubleshooting sessions across all tiers (1-5) with
    permanent history retention for pattern analysis.
    """

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)

        # PATCH-STATE-001: Initialize centralized state manager
        if STATE_MANAGER_AVAILABLE:
            self.state_manager = ProjectStateManager(protocol_root)
        else:
            self.state_manager = None

        # Legacy file path (kept for backward compatibility)
        self.history_file = self.protocol_root / ".protocol-state" / "troubleshooting-history.json"
        self._ensure_history_file()

    def _ensure_history_file(self):
        """Ensure troubleshooting history file exists with proper schema."""
        if not self.history_file.exists():
            print(f"[!] Troubleshooting history file not found at {self.history_file}")
            print("    Creating default history file...")
            try:
                self.history_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self._default_history(), f, indent=2)
            except (IOError, OSError) as e:
                raise RuntimeError(f"Failed to create history file at {self.history_file}: {e}")

    def _default_history(self) -> Dict:
        """Return default troubleshooting history structure."""
        return {
            "schema_version": "1.0.0",
            "sessions": [],
            "metadata": {
                "created": datetime.now().isoformat(),
                "protocol_version": "8.12.0",
                "last_updated": None,
                "total_sessions_all_time": 0
            }
        }

    def load_history(self) -> Dict:
        """
        Load troubleshooting history from JSON.

        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.
        Falls back to legacy file I/O for backward compatibility.
        """
        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                troubleshooting_data = self.state_manager.get_troubleshooting()
                return troubleshooting_data.get("history", self._default_history())
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy file I/O (backward compatibility)
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[!] History file not found. Returning default history.")
            return self._default_history()
        except json.JSONDecodeError as e:
            print(f"[!] Corrupted history file: {e}. Returning default history.")
            return self._default_history()

    def save_history(self, history: Dict):
        """
        Save troubleshooting history to JSON with atomic write.
        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.
        """
        history['metadata']['last_updated'] = datetime.now().isoformat()

        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                # Get current troubleshooting data and update history section
                troubleshooting_data = self.state_manager.get_troubleshooting()
                troubleshooting_data["history"] = history
                self.state_manager.update_troubleshooting(troubleshooting_data)
                return
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy file: {e}")
                # Fall through to legacy file I/O

        # Legacy atomic write pattern (backward compatibility)
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False,
                                              dir=self.history_file.parent,
                                              suffix='.tmp') as tmp_file:
                json.dump(history, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Atomic replace
            os.replace(tmp_path, self.history_file)
        except (IOError, OSError) as e:
            # Cleanup and re-raise
            try:
                if 'tmp_path' in locals() and Path(tmp_path).exists():
                    os.unlink(tmp_path)
            except OSError:
                pass  # Cleanup failure is non-critical
            raise IOError(f"Failed to save troubleshooting history: {e}")

    def start_session(self, tier: int, description: str, affected_files: Optional[str] = None) -> Dict:
        """
        Start a new troubleshooting session.

        Args:
            tier: Tier level (1-5)
            description: Bug description
            affected_files: Comma-separated file paths (optional)

        Returns:
            Created session data
        """
        # Validate tier
        if not (1 <= tier <= 5):
            raise ValueError(f"Invalid tier: {tier}. Must be 1-5.")

        # Validate description
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        if len(description) > 5000:
            raise ValueError("Description exceeds maximum length (5000 characters)")

        # Validate affected_files if provided
        if affected_files:
            file_list = [f.strip() for f in affected_files.split(',')]
            for file_path in file_list:
                if file_path and PATH_VALIDATOR_AVAILABLE:
                    if not validate_file_path(file_path):
                        raise ValueError(f"Invalid file path: {file_path}")

        history = self.load_history()
        now = datetime.now()

        # Check for active session
        active_sessions = [s for s in history['sessions'] if s.get('active', False)]
        if active_sessions:
            active = active_sessions[0]
            print(f"[WARN] Active session already exists: {active['session_id']}")
            print(f"      Use 'complete' to finish current session first, or 'escalate' to change tier")
            return active

        # Create new session
        session_id = f"TS-{now.strftime('%Y%m%d_%H%M%S')}"

        session = {
            "session_id": session_id,
            "tier": tier,
            "tier_name": self._get_tier_name(tier),
            "active": True,
            "bug_description": description,
            "affected_files": [f.strip() for f in affected_files.split(',')] if affected_files else [],
            "started_at": now.isoformat(),
            "completed_at": None,
            "resolution": None,
            "attempts_count": 1,
            "escalations": [],
            "progress_notes": [],
            "agents_deployed": self._get_tier_agents(tier)
        }

        history['sessions'].append(session)
        history['metadata']['total_sessions_all_time'] += 1

        self.save_history(history)
        print(f"[OK] Troubleshooting session started: {session_id}")
        print(f"    Tier: {tier} ({session['tier_name']})")
        print(f"    Bug: {description}")
        print(f"    Agents: {', '.join(session['agents_deployed'])}")

        return session

    def update_session(self, progress_note: str):
        """
        Update current active session with progress note.

        Args:
            progress_note: Progress update text
        """
        # Validate progress_note
        if not progress_note or not progress_note.strip():
            raise ValueError("Progress note cannot be empty")
        if len(progress_note) > 5000:
            raise ValueError("Progress note exceeds maximum length (5000 characters)")

        history = self.load_history()

        # Find active session
        active_sessions = [s for s in history['sessions'] if s.get('active', False)]
        if not active_sessions:
            print(f"[ERROR] No active troubleshooting session found")
            print(f"       Start a new session with: python troubleshooting_tracker.py start <tier> \"<description>\"")
            sys.exit(1)

        session = active_sessions[0]
        session['progress_notes'].append({
            "timestamp": datetime.now().isoformat(),
            "note": progress_note
        })

        self.save_history(history)
        print(f"[OK] Progress note added to {session['session_id']}")

    def complete_session(self, resolution: str):
        """
        Mark current session as complete.

        Args:
            resolution: Resolution description
        """
        # Validate resolution
        if not resolution or not resolution.strip():
            raise ValueError("Resolution cannot be empty")
        if len(resolution) > 5000:
            raise ValueError("Resolution exceeds maximum length (5000 characters)")

        history = self.load_history()

        # Find active session
        active_sessions = [s for s in history['sessions'] if s.get('active', False)]
        if not active_sessions:
            print(f"[ERROR] No active troubleshooting session found")
            sys.exit(1)

        session = active_sessions[0]
        session['active'] = False
        session['completed_at'] = datetime.now().isoformat()
        session['resolution'] = resolution

        # Calculate duration
        start = datetime.fromisoformat(session['started_at'])
        end = datetime.fromisoformat(session['completed_at'])
        duration_minutes = int((end - start).total_seconds() / 60)

        self.save_history(history)
        print(f"[OK] Session completed: {session['session_id']}")
        print(f"    Duration: {self._format_duration(duration_minutes)}")
        print(f"    Resolution: {resolution}")

    def escalate_session(self, new_tier: int):
        """
        Escalate current session to higher tier.

        Args:
            new_tier: New tier level (must be higher than current)
        """
        # Validate tier
        if not (1 <= new_tier <= 5):
            raise ValueError(f"Invalid tier: {new_tier}. Must be 1-5.")

        history = self.load_history()

        # Find active session
        active_sessions = [s for s in history['sessions'] if s.get('active', False)]
        if not active_sessions:
            print(f"[ERROR] No active troubleshooting session found")
            sys.exit(1)

        session = active_sessions[0]
        old_tier = session['tier']

        if new_tier <= old_tier:
            print(f"[ERROR] New tier ({new_tier}) must be higher than current tier ({old_tier})")
            sys.exit(1)

        # Record escalation
        session['escalations'].append({
            "timestamp": datetime.now().isoformat(),
            "from_tier": old_tier,
            "to_tier": new_tier,
            "reason": "Manual escalation"
        })

        session['tier'] = new_tier
        session['tier_name'] = self._get_tier_name(new_tier)
        session['agents_deployed'] = self._get_tier_agents(new_tier)

        # Increment attempts counter (escalation = failed attempt)
        session['attempts_count'] = session.get('attempts_count', 1) + 1

        self.save_history(history)
        print(f"[OK] Session escalated: Tier {old_tier} → Tier {new_tier}")
        print(f"    New agents: {', '.join(session['agents_deployed'])}")

    def get_status(self) -> str:
        """Get current troubleshooting session status."""
        history = self.load_history()

        # Find active session
        active_sessions = [s for s in history['sessions'] if s.get('active', False)]
        if not active_sessions:
            return "[STATUS] No active troubleshooting session"

        session = active_sessions[0]

        # Calculate duration
        start = datetime.fromisoformat(session['started_at'])
        now = datetime.now()
        duration_minutes = int((now - start).total_seconds() / 60)

        status = f"""
[STATUS] **Troubleshooting Session**

**Session ID:** {session['session_id']}
**Tier:** {session['tier']} ({session['tier_name']})
**Duration:** {self._format_duration(duration_minutes)}
**Attempts:** {session['attempts_count']}
**Escalations:** {len(session['escalations'])}

**Bug Description:** {session['bug_description']}
**Affected Files:** {', '.join(session['affected_files']) if session['affected_files'] else 'None specified'}
**Agents Deployed:** {', '.join(session['agents_deployed'])}

**Progress Notes:** {len(session['progress_notes'])} updates
**Started:** {session['started_at']}
"""
        return status.strip()

    def get_stats(self) -> str:
        """
        Get troubleshooting statistics from historical data.

        Analyzes past sessions to provide insights on:
        - Success rates by tier
        - Average duration by tier
        - Common file patterns
        - Escalation patterns
        - Resolution themes

        Returns:
            Formatted statistics report
        """
        history = self.load_history()
        sessions = history['sessions']

        if not sessions:
            return "[STATS] No troubleshooting sessions found in history"

        # Overall stats
        total_sessions = len(sessions)
        completed_sessions = [s for s in sessions if not s.get('active', False)]
        active_sessions = [s for s in sessions if s.get('active', False)]

        # Tier breakdown
        tier_stats = {}
        for tier in range(1, 6):
            tier_sessions = [s for s in completed_sessions if s['tier'] == tier]
            if tier_sessions:
                durations = []
                for s in tier_sessions:
                    try:
                        start = datetime.fromisoformat(s['started_at'])
                        end = datetime.fromisoformat(s['completed_at'])
                        duration = int((end - start).total_seconds() / 60)
                        durations.append(duration)
                    except (ValueError, KeyError):
                        pass  # Skip sessions with invalid timestamps

                avg_duration = sum(durations) / len(durations) if durations else 0
                escalations = sum(len(s.get('escalations', [])) for s in tier_sessions)

                tier_stats[tier] = {
                    'count': len(tier_sessions),
                    'avg_duration': avg_duration,
                    'escalations': escalations,
                    'escalation_rate': (escalations / len(tier_sessions) * 100) if tier_sessions else 0
                }

        # Most common files
        file_counts = {}
        for session in sessions:
            for file in session.get('affected_files', []):
                file_counts[file] = file_counts.get(file, 0) + 1

        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Recent sessions
        recent = sorted(completed_sessions, key=lambda x: x.get('completed_at', ''), reverse=True)[:5]

        # Build stats report
        stats = f"""
[STATS] **Troubleshooting History Analysis**

## Overview
**Total Sessions:** {total_sessions} ({len(completed_sessions)} completed, {len(active_sessions)} active)
**Historical Data Since:** {history['metadata'].get('created', 'Unknown')}

## Success Rate by Tier
"""

        for tier in range(1, 6):
            if tier in tier_stats:
                stats_data = tier_stats[tier]
                stats += f"""
**Tier {tier} ({self._get_tier_name(tier)})**:
- Sessions: {stats_data['count']}
- Avg Duration: {self._format_duration(stats_data['avg_duration'])}
- Escalations: {stats_data['escalations']} ({stats_data['escalation_rate']:.1f}% of sessions)
"""

        if top_files:
            stats += "\n## Most Frequently Affected Files\n"
            for file, count in top_files:
                stats += f"- {file}: {count} session(s)\n"

        if recent:
            stats += "\n## Recent Completions (Last 5)\n"
            for session in recent:
                try:
                    start = datetime.fromisoformat(session['started_at'])
                    end = datetime.fromisoformat(session['completed_at'])
                    duration = int((end - start).total_seconds() / 60)
                    stats += f"""
- **{session['session_id']}** (Tier {session['tier']})
  Duration: {self._format_duration(duration)} | Resolution: {session.get('resolution', 'Unknown')[:50]}...
"""
                except (ValueError, KeyError):
                    pass  # Skip sessions with invalid timestamps

        # Insights
        stats += "\n## Insights\n"

        # Escalation patterns
        total_escalations = sum(len(s.get('escalations', [])) for s in completed_sessions)
        if total_escalations > 0:
            escalation_rate = (total_escalations / len(completed_sessions) * 100) if completed_sessions else 0
            stats += f"- **Escalation Rate:** {escalation_rate:.1f}% of sessions required tier escalation\n"

        # Tier distribution
        if tier_stats:
            most_common_tier = max(tier_stats.items(), key=lambda x: x[1]['count'])
            stats += f"- **Most Common Tier:** Tier {most_common_tier[0]} ({most_common_tier[1]['count']} sessions)\n"

        # Average resolution time
        all_durations = []
        for session in completed_sessions:
            try:
                start = datetime.fromisoformat(session['started_at'])
                end = datetime.fromisoformat(session['completed_at'])
                duration = int((end - start).total_seconds() / 60)
                all_durations.append(duration)
            except (ValueError, KeyError):
                pass  # Skip sessions with invalid timestamps

        if all_durations:
            avg_overall = sum(all_durations) / len(all_durations)
            stats += f"- **Average Resolution Time:** {self._format_duration(avg_overall)}\n"

        return stats.strip()

    def _get_tier_name(self, tier: int) -> str:
        """Get tier name from tier number."""
        tier_names = {
            1: "Minor Bugs",
            2: "Moderate Bugs",
            3: "Complex Bugs",
            4: "Critical Bugs",
            5: "Code Red (Catastrophic)"
        }
        return tier_names.get(tier, "Unknown")

    def _get_tier_agents(self, tier: int) -> list:
        """Get agents deployed for tier."""
        tier_agents = {
            1: ["Yuuji"],
            2: ["Yuuji", "Megumi"],
            3: ["Yuuji", "Megumi", "Support Agent (User Selected)"],
            4: ["Yuuji", "Megumi", "Support Agent", "Gojo"],
            5: ["All 9 Agents"]
        }
        return tier_agents.get(tier, [])

    def _format_duration(self, minutes: float) -> str:
        """Format duration in human-readable format."""
        hours = int(minutes // 60)
        mins = int(minutes % 60)

        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
        else:
            return f"{mins} minutes"


def main():
    """Command-line interface for troubleshooting tracker."""
    import sys
    import io

    # Fix Windows console encoding
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # Derive protocol root from script location (not CWD - fixes path resolution bug)
    protocol_root = Path(__file__).resolve().parent.parent

    try:
        tracker = TroubleshootingTracker(protocol_root)
    except Exception as e:
        print(f"[ERROR] Failed to initialize TroubleshootingTracker: {e}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python troubleshooting_tracker.py <command> [args]")
        print("")
        print("Commands:")
        print("  start <tier> \"<description>\" [affected_files]")
        print("    Start new troubleshooting session")
        print("    Example: python troubleshooting_tracker.py start 2 \"Login fails with 500 error\" \"auth.py,login.py\"")
        print("")
        print("  update \"<progress note>\"")
        print("    Add progress note to active session")
        print("    Example: python troubleshooting_tracker.py update \"Found root cause in JWT validation\"")
        print("")
        print("  complete \"<resolution>\"")
        print("    Mark active session as complete")
        print("    Example: python troubleshooting_tracker.py complete \"Fixed JWT expiration check\"")
        print("")
        print("  escalate <new_tier>")
        print("    Escalate to higher tier")
        print("    Example: python troubleshooting_tracker.py escalate 3")
        print("")
        print("  status")
        print("    Show active session status")
        print("")
        print("  stats")
        print("    Show troubleshooting history statistics")
        print("")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python troubleshooting_tracker.py start <tier> \"<description>\" [affected_files]", file=sys.stderr)
            sys.exit(1)

        try:
            tier = int(sys.argv[2])
            description = sys.argv[3]
            affected_files = sys.argv[4] if len(sys.argv) > 4 else None

            tracker.start_session(tier, description, affected_files)
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "update":
        if len(sys.argv) < 3:
            print("[ERROR] Usage: python troubleshooting_tracker.py update \"<progress note>\"", file=sys.stderr)
            sys.exit(1)

        progress_note = sys.argv[2]
        tracker.update_session(progress_note)

    elif command == "complete":
        if len(sys.argv) < 3:
            print("[ERROR] Usage: python troubleshooting_tracker.py complete \"<resolution>\"", file=sys.stderr)
            sys.exit(1)

        resolution = sys.argv[2]
        tracker.complete_session(resolution)

    elif command == "escalate":
        if len(sys.argv) < 3:
            print("[ERROR] Usage: python troubleshooting_tracker.py escalate <new_tier>", file=sys.stderr)
            sys.exit(1)

        try:
            new_tier = int(sys.argv[2])
            tracker.escalate_session(new_tier)
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "status":
        print(tracker.get_status())

    elif command == "stats":
        print(tracker.get_stats())

    elif command == "help" or command == "--help" or command == "-h":
        print("Domain Zero Protocol - Troubleshooting Session Tracker v1.0.0")
        print("")
        print("Usage: python troubleshooting_tracker.py <command> [args]")
        print("")
        print("Commands:")
        print("  start <tier> \"<description>\" [affected_files]  Start new troubleshooting session")
        print("  update \"<progress note>\"                        Add progress note to active session")
        print("  complete \"<resolution>\"                         Mark active session as complete")
        print("  escalate <new_tier>                             Escalate to higher tier")
        print("  status                                          Show active session status")
        print("  stats                                           Show troubleshooting history statistics")
        print("  help                                            Show this help message")
        print("")
        print("Tiers:")
        print("  1 - Minor Bugs (Yuuji)")
        print("  2 - Moderate Bugs (Yuuji + Megumi)")
        print("  3 - Complex Bugs (Yuuji + Megumi + Support Agent)")
        print("  4 - Critical Bugs (Yuuji + Megumi + Support + Gojo)")
        print("  5 - Code Red / Catastrophic (All 9 Agents)")
        print("")
        print("Examples:")
        print("  python troubleshooting_tracker.py start 2 \"Login fails\" \"auth.py\"")
        print("  python troubleshooting_tracker.py update \"Found JWT bug\"")
        print("  python troubleshooting_tracker.py escalate 3")
        print("  python troubleshooting_tracker.py complete \"Fixed validation\"")
        print("  python troubleshooting_tracker.py status")
        print("  python troubleshooting_tracker.py stats")

    else:
        print(f"Unknown command: {command}")
        print(f"Run 'python troubleshooting_tracker.py help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
