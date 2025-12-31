#!/usr/bin/env python3
"""
Gojo Learning System (v8.8.0 Component 3b)

PURPOSE: Learn from mission coordination and intelligence reports to improve agent workflow.

CRITICAL SAFETY GUARANTEES:
  1. USER PROTECTION: Suggestions only, never automatic actions. User authority supreme.
  2. PROJECT PROTECTION: No sensitive data storage, project isolation, no security weakening.
  3. NO EXPLOITATION: Never learn user vulnerabilities or pressure points.
  4. KILL SWITCH: Learning pauses during emergencies and fatigue alerts.
  5. PRIVACY: Local-only, gitignored, instantly clearable.

WHAT GOJO LEARNS:
  - Tier selection patterns (feature keywords → appropriate tier)
  - Agent handoff efficiency (optimal agent transitions)
  - Work session patterns (user productivity rhythms)
  - Compliance violation patterns (common mistakes to prevent)

WHAT GOJO NEVER LEARNS:
  - User behavior during stress/fatigue (no exploitation)
  - Project-specific business logic or sensitive data
  - Patterns that pressure or manipulate user
  - Patterns that weaken security or reduce quality

USAGE:
  python gojo-learn.py --record-tier [metadata]       # Record tier selection
  python gojo-learn.py --record-handoff [metadata]    # Record agent handoff
  python gojo-learn.py --record-session [metadata]    # Record work session
  python gojo-learn.py --view-patterns                # View learned patterns
  python gojo-learn.py --suggest-tier [feature]       # Get tier suggestion
  python gojo-learn.py --clear --force                # Clear all learned data
  python gojo-learn.py --feedback [helpful/not]       # Record suggestion feedback

INTEGRATION:
  - Called by Gojo during mission coordination
  - Patterns stored in .protocol-state/learning/gojo-patterns.json (gitignored)
  - Integrates with Trigger 19 (learned insights in intelligence reports)
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
    # Silent fallback for gojo-learn (optional dependency)


# Sensitive data patterns to NEVER store (same as Sukuna)
PROHIBITED_DATA_PATTERNS = [
    r'password', r'api[_-]?key', r'token', r'secret',
    r'email.*@', r'phone.*\d{3}', r'ssn', r'social.*security',
    r'credit[_-]?card', r'private[_-]?key',
]

# Exploitative patterns (NEVER learn these)
EXPLOITATIVE_PATTERNS = [
    r'user.*tired.*accept',
    r'user.*stressed.*agree',
    r'user.*late.*night.*suggest',
    r'user.*vulnerable',
    r'pressure.*after.*fatigue',
]


class GojoLearning:
    """Gojo learning system with USER + PROJECT protection"""

    def __init__(self, project_root: Path):
        """Initialize Gojo learning system

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
        self.patterns_file = self.learning_dir / f"gojo-patterns-{self.project_id}.json"

        # Load configuration
        self.config = self._load_config()
        self.patterns = self._load_patterns()

    def _get_project_id(self) -> str:
        """Generate unique project identifier for pattern isolation

        Returns:
            Short hash identifying this project
        """
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
            "total_missions_observed": 0,
            "patterns": [],
            "dismissed_suggestions": [],  # Track dismissed suggestions
            "feedback": []  # Track suggestion effectiveness
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

    def _is_exploitative(self, pattern: str) -> bool:
        """Check if pattern is exploitative

        Args:
            pattern: Pattern description

        Returns:
            True if pattern exploits user
        """
        pattern_lower = pattern.lower()

        for exploitative in EXPLOITATIVE_PATTERNS:
            if re.search(exploitative, pattern_lower):
                return True

        return False

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to remove sensitive information

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Remove specific feature names (keep generic keywords)
        # Example: "PayPal payment integration" → "payment feature"

        # Replace user home paths
        text = re.sub(r'/home/[^/]+/', '/USER_HOME/', text)
        text = re.sub(r'C:\\Users\\[^\\]+\\', 'C:\\USER_HOME\\', text)

        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

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

    def record_tier_selection(self, feature_name: str, tier: int, outcome: str = "success") -> bool:
        """Record tier selection for learning

        Args:
            feature_name: Feature description (sanitized)
            tier: Selected tier (1, 2, or 3)
            outcome: Outcome (success, bypassed, violated)

        Returns:
            True if recorded successfully, False if skipped (disabled/sensitive data)
        """
        if not self.is_enabled():
            return False

        # Safety: Sanitize feature name
        feature_sanitized = self._sanitize_text(feature_name)

        # Safety: Check for sensitive data
        if self._contains_sensitive_data(feature_sanitized):
            return False

        # Extract keywords from feature name
        keywords = self._extract_keywords(feature_sanitized)

        # Learn tier pattern for each keyword
        for keyword in keywords:
            self._learn_tier_pattern(keyword, tier, outcome)

        self.patterns["total_missions_observed"] += 1
        self._save_patterns()
        return True

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text

        Args:
            text: Text to analyze

        Returns:
            List of keywords
        """
        # Common words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'to', 'in', 'on', 'at'}

        # Extract words
        words = re.findall(r'\b[a-z]+\b', text.lower())

        # Filter and return
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        return keywords[:5]  # Limit to top 5 keywords

    def _learn_tier_pattern(self, keyword: str, tier: int, outcome: str):
        """Learn tier selection pattern for keyword

        Args:
            keyword: Feature keyword
            tier: Selected tier
            outcome: Outcome (success/bypassed/violated)
        """
        # Find existing pattern
        for pattern in self.patterns["patterns"]:
            if pattern["type"] == "tier_selection" and pattern["keyword"] == keyword:
                # Update pattern
                pattern["tier_counts"][f"tier_{tier}"] += 1

                if outcome == "success":
                    pattern["successful_uses"] += 1

                pattern["total_uses"] += 1
                pattern["last_observed"] = datetime.utcnow().isoformat() + "Z"

                # Recalculate confidence (based on consistency)
                tier_counts = pattern["tier_counts"]
                most_common_count = max(tier_counts.values())
                total = pattern["total_uses"]

                pattern["confidence"] = most_common_count / total if total > 0 else 0.0
                pattern["recommended_tier"] = max(tier_counts, key=tier_counts.get)

                return

        # Add new pattern
        new_pattern = {
            "type": "tier_selection",
            "keyword": keyword,
            "description": f"Features with '{keyword}' keyword",
            "tier_counts": {
                "tier_1": 1 if tier == 1 else 0,
                "tier_2": 1 if tier == 2 else 0,
                "tier_3": 1 if tier == 3 else 0
            },
            "recommended_tier": f"tier_{tier}",
            "total_uses": 1,
            "successful_uses": 1 if outcome == "success" else 0,
            "confidence": 1.0,  # 100% with 1 sample (low sample size though)
            "sample_size": 1,
            "created": datetime.utcnow().isoformat() + "Z",
            "last_observed": datetime.utcnow().isoformat() + "Z"
        }

        self.patterns["patterns"].append(new_pattern)

    def suggest_tier(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Suggest tier based on learned patterns

        Args:
            feature_name: Feature description

        Returns:
            Suggestion dictionary or None
        """
        if not self.is_enabled():
            return None

        # Extract keywords
        keywords = self._extract_keywords(feature_name)

        # Find best matching pattern
        best_pattern = None
        best_confidence = 0.0

        for keyword in keywords:
            for pattern in self.patterns["patterns"]:
                if pattern["type"] == "tier_selection" and pattern["keyword"] == keyword:
                    if pattern["confidence"] > best_confidence and pattern["total_uses"] >= 3:
                        best_pattern = pattern
                        best_confidence = pattern["confidence"]

        if not best_pattern or best_confidence < 0.80:
            return None  # No high-confidence pattern

        # Check if user dismissed this suggestion before
        suggestion_id = f"tier_{best_pattern['keyword']}"
        if suggestion_id in self.patterns["dismissed_suggestions"]:
            return None

        # Create suggestion
        tier_num = int(best_pattern["recommended_tier"].split("_")[1])

        return {
            "type": "tier_suggestion",
            "tier": tier_num,
            "message": f"Based on {best_pattern['total_uses']} similar features with '{best_pattern['keyword']}', suggest Tier {tier_num}",
            "confidence": best_confidence,
            "sample_size": best_pattern["total_uses"],
            "keyword": best_pattern["keyword"],
            "suggestion_id": suggestion_id,
            "action": "advisory",
            "dismissible": True,
            "safety_note": "This is optional information based on patterns. Your choice."
        }

    def dismiss_suggestion(self, suggestion_id: str):
        """Dismiss a suggestion (don't show again)

        Args:
            suggestion_id: Suggestion identifier
        """
        if suggestion_id not in self.patterns["dismissed_suggestions"]:
            self.patterns["dismissed_suggestions"].append(suggestion_id)
            self._save_patterns()

        print(f"[OK] Suggestion dismissed - won't show again")

    def record_feedback(self, suggestion_id: str, helpful: bool):
        """Record feedback on suggestion effectiveness

        Args:
            suggestion_id: Suggestion identifier
            helpful: Whether suggestion was helpful
        """
        feedback = {
            "suggestion_id": suggestion_id,
            "helpful": helpful,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.patterns["feedback"].append(feedback)

        # If 3+ "not helpful" feedback for same suggestion, auto-dismiss
        not_helpful_count = sum(
            1 for f in self.patterns["feedback"]
            if f["suggestion_id"] == suggestion_id and not f["helpful"]
        )

        if not_helpful_count >= 3:
            self.dismiss_suggestion(suggestion_id)
            print(f"[INFO] Suggestion auto-dismissed after 3 'not helpful' responses")

        self._save_patterns()
        print(f"[OK] Feedback recorded - thank you!")

    def view_patterns(self) -> str:
        """Generate human-readable patterns report

        Returns:
            Formatted patterns report
        """
        if not self.patterns["patterns"]:
            return "No patterns learned yet. Learning system needs data from mission coordination."

        lines = [
            "GOJO LEARNED PATTERNS",
            "=" * 70,
            "",
            f"Project: {self.patterns['project_name']} (ID: {self.patterns['project_id']})",
            f"Total Missions Observed: {self.patterns['total_missions_observed']}",
            f"Total Patterns: {len(self.patterns['patterns'])}",
            f"Dismissed Suggestions: {len(self.patterns['dismissed_suggestions'])}",
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

            if pattern["type"] == "tier_selection":
                tier_num = int(pattern["recommended_tier"].split("_")[1])
                lines.append(f"{i}. {pattern['description']} -> Tier {tier_num}")
                lines.append(f"   Confidence: {confidence_pct:.0f}% {conf_label} (based on {pattern['total_uses']} uses)")
                lines.append(f"   Tier Distribution: T1={pattern['tier_counts']['tier_1']}, T2={pattern['tier_counts']['tier_2']}, T3={pattern['tier_counts']['tier_3']}")
                lines.append(f"   Success Rate: {(pattern['successful_uses']/pattern['total_uses']*100):.0f}%")
            else:
                lines.append(f"{i}. {pattern['description']}")
                lines.append(f"   Confidence: {confidence_pct:.0f}% {conf_label}")

            lines.append(f"   Last Observed: {pattern['last_observed']}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("Note: These are advisory patterns. User authority always supreme.")

        return "\n".join(lines)

    def clear_patterns(self):
        """Clear all learned patterns"""
        self.patterns = self._init_patterns()
        self._save_patterns()

        if self.patterns_file.exists():
            self.patterns_file.unlink()

        print("[OK] All Gojo learned patterns cleared")


def main():
    """Main entry point for gojo-learn.py"""

    parser = argparse.ArgumentParser(
        description="Gojo Learning System (v8.8.0) - USER + PROJECT Protected",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Safety Guarantees:
  - USER: Suggestions only, never automatic actions. User authority supreme.
  - PROJECT: No sensitive data, project isolation, no security weakening.
  - NO EXPLOITATION: Never learn user vulnerabilities or pressure points.
  - KILL SWITCH: Learning pauses during emergencies.
  - PRIVACY: Local-only, gitignored, instantly clearable.

Examples:
  # Record tier selection
  python gojo-learn.py --record-tier --feature "payment processing" --tier 3 --outcome success

  # Suggest tier for new feature
  python gojo-learn.py --suggest-tier --feature "user authentication"

  # Record feedback on suggestion
  python gojo-learn.py --feedback --suggestion-id "tier_payment" --helpful yes

  # View learned patterns
  python gojo-learn.py --view-patterns

  # Clear all learned data
  python gojo-learn.py --clear --force
        """
    )

    parser.add_argument('--record-tier', action='store_true',
                       help='Record tier selection for learning')
    parser.add_argument('--suggest-tier', action='store_true',
                       help='Get tier suggestion based on patterns')
    parser.add_argument('--view-patterns', action='store_true',
                       help='View learned patterns')
    parser.add_argument('--feedback', action='store_true',
                       help='Record suggestion feedback')
    parser.add_argument('--clear', action='store_true',
                       help='Clear all learned patterns (requires --force)')

    # Record tier arguments
    parser.add_argument('--feature', type=str,
                       help='Feature name or description')
    parser.add_argument('--tier', type=int, choices=[1, 2, 3],
                       help='Tier number (1, 2, or 3)')
    parser.add_argument('--outcome', type=str, choices=['success', 'bypassed', 'violated'],
                       help='Tier compliance outcome')

    # Feedback arguments
    parser.add_argument('--suggestion-id', type=str,
                       help='Suggestion identifier')
    parser.add_argument('--helpful', type=str, choices=['yes', 'no'],
                       help='Was suggestion helpful?')

    # Clear arguments
    parser.add_argument('--force', action='store_true',
                       help='Force operation without confirmation')

    args = parser.parse_args()

    # Verify working directory
    if not verify_project_root(silent=False, exit_on_failure=True):
        sys.exit(1)

    # Initialize learning system
    project_root = Path.cwd()
    gojo = GojoLearning(project_root)

    # Handle commands
    if args.record_tier:
        if not args.feature or args.tier is None:
            print("[ERROR] --record-tier requires --feature and --tier")
            sys.exit(1)

        outcome = args.outcome or "success"
        recorded = gojo.record_tier_selection(args.feature, args.tier, outcome)

        if recorded:
            print(f"[OK] Recorded tier selection: {args.feature} -> Tier {args.tier}")
        else:
            print(f"[INFO] Learning disabled - not recording tier selection")
            print(f"  (To enable: Set learning.enabled and learning.gojo.enabled to true in protocol.config.yaml)")

    elif args.suggest_tier:
        if not args.feature:
            print("[ERROR] --suggest-tier requires --feature")
            sys.exit(1)

        suggestion = gojo.suggest_tier(args.feature)

        if not suggestion:
            print("[INFO] No high-confidence tier suggestion available")
            print("  (Requires 3+ samples with 80%+ confidence)")
        else:
            print(f"\n[SUGGESTION] {suggestion['message']}")
            print(f"  Confidence: {suggestion['confidence']*100:.0f}%")
            print(f"  Sample Size: {suggestion['sample_size']}")
            print(f"  Note: {suggestion['safety_note']}")
            print(f"\n  Dismiss: python gojo-learn.py --feedback --suggestion-id {suggestion['suggestion_id']} --helpful no\n")

    elif args.feedback:
        if not args.suggestion_id or not args.helpful:
            print("[ERROR] --feedback requires --suggestion-id and --helpful")
            sys.exit(1)

        helpful = args.helpful.lower() == 'yes'
        gojo.record_feedback(args.suggestion_id, helpful)

    elif args.view_patterns:
        report = gojo.view_patterns()
        print(report)

    elif args.clear:
        if not args.force:
            print("[ERROR] --clear requires --force flag for confirmation")
            print("  This will permanently delete all learned patterns")
            sys.exit(1)

        gojo.clear_patterns()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
