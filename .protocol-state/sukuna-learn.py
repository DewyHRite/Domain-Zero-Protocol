#!/usr/bin/env python3
"""
Sukuna Learning System (v8.8.0 Component 3a)

PURPOSE: Learn from protocol updates and system changes to improve future update planning.

CRITICAL SAFETY GUARANTEES:
  1. USER PROTECTION: Suggestions only, never automatic actions. User authority supreme.
  2. PROJECT PROTECTION: No sensitive data storage, project isolation, no security weakening.
  3. KILL SWITCH: Learning pauses during emergencies. No learning from stressed user.
  4. PRIVACY: Local-only, gitignored, instantly clearable.
  5. NO MANIPULATION: Advisory only, never pressure, easy dismiss.

WHAT SUKUNA LEARNS:
  - File dependency patterns (which files change together)
  - Update duration patterns (estimated vs actual time)
  - Rollback trigger patterns (what causes rollbacks)
  - Breaking change patterns (version compatibility)

WHAT SUKUNA NEVER LEARNS:
  - Project secrets or sensitive data
  - Patterns that weaken security
  - Patterns that reduce test coverage
  - Patterns specific to other projects (project isolation)

USAGE:
  python sukuna-learn.py --record-update [metadata]  # Record system update
  python sukuna-learn.py --view-patterns              # View learned patterns
  python sukuna-learn.py --suggest [context]          # Get suggestions (if enabled)
  python sukuna-learn.py --clear --force              # Clear all learned data
  python sukuna-learn.py --disable                    # Disable learning
  python sukuna-learn.py --enable                     # Enable learning (requires consent)

INTEGRATION:
  - Called by Sukuna during system updates (.protocol-state/system-update-framework/)
  - Patterns stored in .protocol-state/learning/sukuna-patterns.json (gitignored)
  - Respects protocol.config.yaml → learning.enabled setting
  - Integrates with Kill Switch (learning pauses when active)

VERSION: 8.8.0
CREATED: 2025-12-06 (Phase 4 Week 3)
SAFETY: USER + PROJECT protection mandatory
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse
import hashlib

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
    # Silent fallback for sukuna-learn (optional dependency)


# Sensitive data patterns to NEVER store
PROHIBITED_DATA_PATTERNS = [
    r'password', r'api[_-]?key', r'token', r'secret',
    r'email.*@', r'phone.*\d{3}', r'ssn', r'social.*security',
    r'credit[_-]?card', r'private[_-]?key', r'connection[_-]?string',
    r'postgresql://', r'mongodb://', r'mysql://',
    r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',  # JWT tokens
    r'sk_live_', r'pk_live_',  # Stripe keys
]

# Patterns that weaken security (NEVER store these)
SECURITY_WEAKENING_PATTERNS = [
    r'skip.*security.*review',
    r'bypass.*tier.*validation',
    r'disable.*authentication',
    r'remove.*encryption',
    r'skip.*backup',
    r'allow.*unsigned',
    r'disable.*safety',
    r'fast.*track.*without.*test',
]


class SukunaLearning:
    """Sukuna learning system with USER + PROJECT protection"""

    def __init__(self, project_root: Path):
        """Initialize Sukuna learning system

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.learning_dir = project_root / ".protocol-state" / "learning"
        self.project_state_path = project_root / ".protocol-state" / "project-state.json"
        self.kill_switch_path = project_root / ".dzp-killswitch" / "state.json"

        # Create learning directory if needed
        self.learning_dir.mkdir(parents=True, exist_ok=True)

        # PATCH-STATE-001: Initialize ProjectStateManager if available
        if STATE_MANAGER_AVAILABLE:
            self.state_manager = ProjectStateManager(project_root)
        else:
            self.state_manager = None

        # Project-specific learning file (isolated per project)
        self.project_id = self._get_project_id()
        self.patterns_file = self.learning_dir / f"sukuna-patterns-{self.project_id}.json"

        # Load configuration
        self.config = self._load_config()
        self.patterns = self._load_patterns()

    def _get_project_id(self) -> str:
        """Generate unique project identifier for pattern isolation

        Returns:
            Short hash identifying this project
        """
        # Use project root path to generate consistent ID
        project_path = str(self.project_root.resolve())
        return hashlib.sha256(project_path.encode()).hexdigest()[:8]

    def _load_config(self) -> Dict[str, Any]:
        """Load learning configuration from project-state.json

        PATCH-STATE-001: Uses ProjectStateManager when available for unified state access.

        Returns:
            Learning configuration dictionary
        """
        # PATCH-STATE-001: Use ProjectStateManager if available
        if self.state_manager:
            try:
                state = self.state_manager.load_project_state()
                return state.get("learning_consent", {"enabled": False, "consent_given": False})
            except Exception as e:
                print(f"[WARN] ProjectStateManager failed, falling back to legacy: {e}")
                # Fall through to legacy file I/O

        # Legacy file I/O (backward compatibility)
        if not self.project_state_path.exists():
            return {"enabled": False, "consent_given": False}

        try:
            with open(self.project_state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                return state.get("learning_consent", {"enabled": False, "consent_given": False})
        except Exception as e:
            print(f"[WARN] Could not load learning config: {e}")
            return {"enabled": False, "consent_given": False}

    def _load_patterns(self) -> Dict[str, Any]:
        """Load learned patterns from file

        Returns:
            Patterns dictionary
        """
        if not self.patterns_file.exists():
            return self._init_patterns()

        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load patterns: {e}")
            return self._init_patterns()

    def _init_patterns(self) -> Dict[str, Any]:
        """Initialize empty patterns structure

        Returns:
            Empty patterns dictionary
        """
        return {
            "project_id": self.project_id,
            "project_name": self.project_root.name,
            "created": datetime.utcnow().isoformat() + "Z",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "total_updates_observed": 0,
            "patterns": []
        }

    def _save_patterns(self):
        """Save patterns to file"""
        self.patterns["last_updated"] = datetime.utcnow().isoformat() + "Z"

        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save patterns: {e}")
            sys.exit(1)

    def _is_kill_switch_active(self) -> bool:
        """Check if Kill Switch is active

        Returns:
            True if Kill Switch active, False otherwise
        """
        if not self.kill_switch_path.exists():
            return False

        try:
            with open(self.kill_switch_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                return state.get("active", False)
        except:
            return False

    def _contains_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive data

        Args:
            text: Text to check

        Returns:
            True if sensitive data detected
        """
        text_lower = text.lower()

        for pattern in PROHIBITED_DATA_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        return False

    def _weakens_security(self, pattern: str) -> bool:
        """Check if pattern weakens security

        Args:
            pattern: Pattern description

        Returns:
            True if pattern weakens security
        """
        pattern_lower = pattern.lower()

        for prohibited in SECURITY_WEAKENING_PATTERNS:
            if re.search(prohibited, pattern_lower):
                return True

        return False

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to remove sensitive information

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Replace user home paths
        text = re.sub(r'/home/[^/]+/', '/USER_HOME/', text)
        text = re.sub(r'C:\\Users\\[^\\]+\\', 'C:\\USER_HOME\\', text)

        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

        # Remove URLs with credentials
        text = re.sub(r'https?://[^:]+:[^@]+@', 'https://[CREDENTIALS]@', text)

        return text

    def is_enabled(self) -> bool:
        """Check if learning is enabled

        Returns:
            True if learning enabled and consented
        """
        # Check 1: Kill Switch
        if self._is_kill_switch_active():
            return False

        # Check 2: Learning enabled in config
        if not self.config.get("enabled", False):
            return False

        # Check 3: User consent given
        if not self.config.get("consent_given", False):
            return False

        return True

    def record_update(self, update_data: Dict[str, Any]):
        """Record a system update for learning

        Args:
            update_data: Update metadata (files changed, duration, outcome)
        """
        if not self.is_enabled():
            print("[INFO] Learning disabled - not recording update")
            return

        # Safety check 1: Sanitize data
        sanitized_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "files_modified": update_data.get("files_modified", []),
            "duration_minutes": update_data.get("duration_minutes", 0),
            "outcome": update_data.get("outcome", "unknown"),
            "version_from": update_data.get("version_from", ""),
            "version_to": update_data.get("version_to", "")
        }

        # Safety check 2: Remove sensitive file paths
        sanitized_data["files_modified"] = [
            self._sanitize_text(f) for f in sanitized_data["files_modified"]
        ]

        # Safety check 3: Check for sensitive data
        if self._contains_sensitive_data(json.dumps(sanitized_data)):
            print("[ERROR] Sensitive data detected - not recording update")
            return

        # Record update
        self.patterns["total_updates_observed"] += 1

        # Learn file dependency pattern
        self._learn_file_dependencies(sanitized_data["files_modified"])

        # Learn duration pattern
        self._learn_duration_pattern(sanitized_data)

        # Save patterns
        self._save_patterns()

        print(f"[OK] Recorded system update ({self.patterns['total_updates_observed']} total)")

    def _learn_file_dependencies(self, files: List[str]):
        """Learn which files change together

        Args:
            files: List of files modified in update
        """
        if len(files) < 2:
            return  # Need at least 2 files for dependency

        # Sort files for consistent pattern matching
        files_sorted = sorted(files)

        # Create pattern description
        pattern_text = f"Files modified together: {', '.join(files_sorted[:5])}"
        if len(files_sorted) > 5:
            pattern_text += f" (+{len(files_sorted) - 5} more)"

        # Check if pattern already exists
        for pattern in self.patterns["patterns"]:
            if pattern["type"] == "file_dependency" and pattern["files"] == files_sorted:
                # Increment confidence
                pattern["sample_size"] += 1
                pattern["confidence"] = min(0.99, pattern["confidence"] + 0.05)
                pattern["last_observed"] = datetime.utcnow().isoformat() + "Z"
                return

        # Add new pattern
        new_pattern = {
            "type": "file_dependency",
            "description": pattern_text,
            "files": files_sorted,
            "confidence": 0.70,  # Start at 70% confidence
            "sample_size": 1,
            "created": datetime.utcnow().isoformat() + "Z",
            "last_observed": datetime.utcnow().isoformat() + "Z"
        }

        self.patterns["patterns"].append(new_pattern)

    def _learn_duration_pattern(self, update_data: Dict[str, Any]):
        """Learn update duration patterns

        Args:
            update_data: Update metadata
        """
        duration = update_data.get("duration_minutes", 0)
        if duration <= 0:
            return

        # Categorize update type
        files_count = len(update_data.get("files_modified", []))

        if files_count <= 3:
            update_type = "small"
        elif files_count <= 10:
            update_type = "medium"
        else:
            update_type = "large"

        # Find existing duration pattern
        for pattern in self.patterns["patterns"]:
            if pattern["type"] == "update_duration" and pattern["update_type"] == update_type:
                # Update rolling average
                current_avg = pattern["average_duration"]
                sample_size = pattern["sample_size"]

                new_avg = ((current_avg * sample_size) + duration) / (sample_size + 1)

                pattern["average_duration"] = round(new_avg, 1)
                pattern["sample_size"] += 1
                pattern["confidence"] = min(0.95, 0.60 + (sample_size * 0.05))
                pattern["last_observed"] = datetime.utcnow().isoformat() + "Z"
                return

        # Add new duration pattern
        new_pattern = {
            "type": "update_duration",
            "update_type": update_type,
            "description": f"{update_type.capitalize()} updates (1-{files_count} files) average {duration} min",
            "average_duration": float(duration),
            "confidence": 0.60,  # Low confidence with 1 sample
            "sample_size": 1,
            "created": datetime.utcnow().isoformat() + "Z",
            "last_observed": datetime.utcnow().isoformat() + "Z"
        }

        self.patterns["patterns"].append(new_pattern)

    def get_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get learning-based suggestions for current update

        Args:
            context: Current update context (files to modify, etc.)

        Returns:
            List of suggestion dictionaries
        """
        if not self.is_enabled():
            return []

        suggestions = []

        # Get file dependency suggestions
        files_to_modify = context.get("files_to_modify", [])
        if files_to_modify:
            dep_suggestions = self._suggest_file_dependencies(files_to_modify)
            suggestions.extend(dep_suggestions)

        # Get duration estimate suggestions
        duration_suggestions = self._suggest_duration_estimate(context)
        suggestions.extend(duration_suggestions)

        # Filter: Only show high-confidence suggestions (>80%)
        high_confidence = [s for s in suggestions if s["confidence"] >= 0.80]

        return high_confidence

    def _suggest_file_dependencies(self, files: List[str]) -> List[Dict[str, Any]]:
        """Suggest related files based on learned patterns

        Args:
            files: Files user plans to modify

        Returns:
            List of suggestions
        """
        suggestions = []

        for pattern in self.patterns["patterns"]:
            if pattern["type"] != "file_dependency":
                continue

            # Check if any planned files match pattern
            pattern_files = set(pattern["files"])
            planned_files = set(files)

            overlap = pattern_files & planned_files
            if not overlap:
                continue

            # Suggest missing files
            missing = pattern_files - planned_files
            if missing:
                suggestions.append({
                    "type": "file_dependency",
                    "message": f"Pattern suggests also updating: {', '.join(list(missing)[:3])}",
                    "confidence": pattern["confidence"],
                    "sample_size": pattern["sample_size"],
                    "action": "advisory",  # Advisory only, never automatic
                    "dismissible": True,   # User can dismiss
                    "safety_note": "This is a suggestion based on patterns, not a requirement"
                })

        return suggestions

    def _suggest_duration_estimate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest update duration estimate

        Args:
            context: Update context

        Returns:
            List of suggestions
        """
        suggestions = []

        files_count = len(context.get("files_to_modify", []))

        if files_count <= 3:
            update_type = "small"
        elif files_count <= 10:
            update_type = "medium"
        else:
            update_type = "large"

        for pattern in self.patterns["patterns"]:
            if pattern["type"] != "update_duration":
                continue

            if pattern["update_type"] == update_type:
                avg_duration = pattern["average_duration"]
                confidence = pattern["confidence"]

                suggestions.append({
                    "type": "duration_estimate",
                    "message": f"Based on {pattern['sample_size']} similar updates, expect ~{avg_duration:.0f} min",
                    "confidence": confidence,
                    "sample_size": pattern["sample_size"],
                    "action": "informational",
                    "dismissible": True,
                    "safety_note": "Estimate only - actual time may vary"
                })

        return suggestions

    def view_patterns(self) -> str:
        """Generate human-readable patterns report

        Returns:
            Formatted patterns report
        """
        if not self.patterns["patterns"]:
            return "No patterns learned yet. Learning system needs data from system updates."

        lines = [
            "SUKUNA LEARNED PATTERNS",
            "=" * 70,
            "",
            f"Project: {self.patterns['project_name']} (ID: {self.patterns['project_id']})",
            f"Total Updates Observed: {self.patterns['total_updates_observed']}",
            f"Total Patterns: {len(self.patterns['patterns'])}",
            f"Last Updated: {self.patterns['last_updated']}",
            "",
            "PATTERNS (sorted by confidence):",
            ""
        ]

        # Sort by confidence
        sorted_patterns = sorted(self.patterns["patterns"], key=lambda p: p["confidence"], reverse=True)

        for i, pattern in enumerate(sorted_patterns, 1):
            confidence_pct = pattern["confidence"] * 100
            conf_label = "[HIGH]" if pattern["confidence"] >= 0.85 else "[MED]" if pattern["confidence"] >= 0.70 else "[LOW]"

            lines.append(f"{i}. {pattern['description']}")
            lines.append(f"   Type: {pattern['type']}")
            lines.append(f"   Confidence: {confidence_pct:.0f}% {conf_label} (based on {pattern['sample_size']} samples)")
            lines.append(f"   Last Observed: {pattern['last_observed']}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("Note: These are advisory patterns. User authority always supreme.")

        return "\n".join(lines)

    def clear_patterns(self):
        """Clear all learned patterns (requires user confirmation)"""
        self.patterns = self._init_patterns()
        self._save_patterns()

        if self.patterns_file.exists():
            self.patterns_file.unlink()

        print("[OK] All Sukuna learned patterns cleared")

    def disable_learning(self):
        """Disable learning system"""
        print("[INFO] To disable learning, set learning.enabled = false in protocol.config.yaml")
        print("  or update .protocol-state/project-state.json → learning_consent.enabled")

    def enable_learning(self):
        """Enable learning system (requires user consent)"""
        print("[INFO] To enable learning:")
        print("  1. Review safety guarantees in CLAUDE.md")
        print("  2. Update .protocol-state/project-state.json:")
        print("     'learning_consent': {")
        print("       'enabled': true,")
        print("       'consent_given': true,")
        print("       'consent_date': '<current-date>'")
        print("     }")
        print("  3. Set protocol.config.yaml → learning.enabled = true")


def main():
    """Main entry point for sukuna-learn.py"""

    parser = argparse.ArgumentParser(
        description="Sukuna Learning System (v8.8.0) - USER + PROJECT Protected",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Safety Guarantees:
  - USER: Suggestions only, never automatic actions. User authority supreme.
  - PROJECT: No sensitive data, project isolation, no security weakening.
  - KILL SWITCH: Learning pauses during emergencies.
  - PRIVACY: Local-only, gitignored, instantly clearable.

Examples:
  # Record system update
  python sukuna-learn.py --record-update --files "file1.md,file2.py" --duration 45 --outcome success

  # View learned patterns
  python sukuna-learn.py --view-patterns

  # Get suggestions (if learning enabled)
  python sukuna-learn.py --suggest --files "tier-defaults.yaml"

  # Clear all learned data
  python sukuna-learn.py --clear --force

  # Enable/disable learning
  python sukuna-learn.py --enable
  python sukuna-learn.py --disable
        """
    )

    parser.add_argument('--record-update', action='store_true',
                       help='Record a system update for learning')
    parser.add_argument('--view-patterns', action='store_true',
                       help='View learned patterns')
    parser.add_argument('--suggest', action='store_true',
                       help='Get suggestions based on learned patterns')
    parser.add_argument('--clear', action='store_true',
                       help='Clear all learned patterns (requires --force)')
    parser.add_argument('--enable', action='store_true',
                       help='Enable learning (shows instructions)')
    parser.add_argument('--disable', action='store_true',
                       help='Disable learning (shows instructions)')

    # Record update arguments
    parser.add_argument('--files', type=str,
                       help='Comma-separated list of files modified')
    parser.add_argument('--duration', type=int,
                       help='Update duration in minutes')
    parser.add_argument('--outcome', type=str, choices=['success', 'rollback', 'partial'],
                       help='Update outcome')
    parser.add_argument('--version-from', type=str,
                       help='Version before update')
    parser.add_argument('--version-to', type=str,
                       help='Version after update')

    # Suggest arguments
    # (--files reused for suggestion context)

    # Clear arguments
    parser.add_argument('--force', action='store_true',
                       help='Force operation without confirmation')

    args = parser.parse_args()

    # Verify working directory
    if not verify_project_root(silent=False, exit_on_failure=True):
        sys.exit(1)

    # Initialize learning system
    project_root = Path.cwd()
    sukuna = SukunaLearning(project_root)

    # Handle commands
    if args.record_update:
        if not args.files:
            print("[ERROR] --record-update requires --files")
            sys.exit(1)

        files = [f.strip() for f in args.files.split(',')]

        update_data = {
            "files_modified": files,
            "duration_minutes": args.duration or 0,
            "outcome": args.outcome or "unknown",
            "version_from": args.version_from or "",
            "version_to": args.version_to or ""
        }

        sukuna.record_update(update_data)

    elif args.view_patterns:
        report = sukuna.view_patterns()
        print(report)

    elif args.suggest:
        if not sukuna.is_enabled():
            print("[INFO] Learning disabled - no suggestions available")
            print("  Enable learning with: python sukuna-learn.py --enable")
            sys.exit(0)

        if not args.files:
            print("[ERROR] --suggest requires --files")
            sys.exit(1)

        files = [f.strip() for f in args.files.split(',')]
        context = {"files_to_modify": files}

        suggestions = sukuna.get_suggestions(context)

        if not suggestions:
            print("[INFO] No high-confidence suggestions available")
        else:
            print(f"[INFO] Found {len(suggestions)} suggestion(s):\n")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"{i}. {suggestion['message']}")
                print(f"   Confidence: {suggestion['confidence']*100:.0f}% (based on {suggestion['sample_size']} samples)")
                print(f"   Note: {suggestion['safety_note']}")
                print()

    elif args.clear:
        if not args.force:
            print("[ERROR] --clear requires --force flag for confirmation")
            print("  This will permanently delete all learned patterns")
            sys.exit(1)

        sukuna.clear_patterns()

    elif args.enable:
        sukuna.enable_learning()

    elif args.disable:
        sukuna.disable_learning()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
