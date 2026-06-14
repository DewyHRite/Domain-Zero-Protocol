#!/usr/bin/env python3
"""
Domain Zero Protocol - Snapshot Integration Module

Version: 1.0.0
Created: 2025-12-06
Part of: DZP v8.8.0 Validation Framework - Gojo Integration

This module integrates automatic tier-based snapshot creation with Gojo's
session management system.

Features:
- Operation counting and tracking
- Tier-based automatic snapshot triggers
- Tier change detection and snapshots
- Integration with create-snapshot.py
- Session-aware snapshot management

Tier-Based Triggers:
- Tier 1: Manual only (no automatic snapshots)
- Tier 2: Every 10 operations
- Tier 3: After each operation
- All tiers: On tier changes

Usage:
    from snapshot_integration import SnapshotIntegration

    integration = SnapshotIntegration()
    integration.record_operation(description="User authentication implementation")
    integration.check_and_create_snapshot()
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / ".protocol-state"
SESSION_STATE_PATH = STATE_DIR / "session-state.json"
PROJECT_STATE_PATH = STATE_DIR / "project-state.json"
CREATE_SNAPSHOT_SCRIPT = PROJECT_ROOT / "scripts" / "create-snapshot.py"

# Tier-based snapshot triggers
TIER_SNAPSHOT_INTERVALS = {
    1: None,  # Manual only (no automatic snapshots)
    2: 10,    # Every 10 operations
    3: 1      # After each operation
}


# =============================================================================
# Snapshot Integration
# =============================================================================

class SnapshotIntegration:
    """Manages automatic tier-based snapshot creation for Gojo."""

    def __init__(self):
        """Initialize snapshot integration."""
        self.session_state = self._load_session_state()
        self.project_state = self._load_project_state()
        self.current_tier = self._get_current_tier()

    def _load_session_state(self) -> Dict[str, Any]:
        """Load session state from file."""
        if not SESSION_STATE_PATH.exists():
            # Initialize if missing
            return {
                "operation_count": 0,
                "last_snapshot_operation_count": 0,
                "snapshots_this_session": 0,
                "last_operation_time": None,
                "last_operation_description": None
            }

        with open(SESSION_STATE_PATH, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # Ensure operation tracking fields exist
        if "operation_count" not in state:
            state["operation_count"] = 0
        if "last_snapshot_operation_count" not in state:
            state["last_snapshot_operation_count"] = 0
        if "snapshots_this_session" not in state:
            state["snapshots_this_session"] = 0
        if "last_operation_time" not in state:
            state["last_operation_time"] = None
        if "last_operation_description" not in state:
            state["last_operation_description"] = None

        return state

    def _load_project_state(self) -> Dict[str, Any]:
        """Load project state from file."""
        if not PROJECT_STATE_PATH.exists():
            # Return default
            return {
                "tier_settings": {
                    "default_tier": 2
                }
            }

        with open(PROJECT_STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_session_state(self) -> None:
        """Save session state to file."""
        SESSION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.session_state, f, indent=2)

    def _get_current_tier(self) -> int:
        """Get current tier from project state."""
        tier_settings = self.project_state.get("tier_settings", {})
        return tier_settings.get("default_tier", 2)

    def record_operation(self, description: Optional[str] = None) -> None:
        """
        Record a significant operation.

        Args:
            description: Optional description of the operation
        """
        self.session_state["operation_count"] += 1
        self.session_state["last_operation_time"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        if description:
            self.session_state["last_operation_description"] = description

        self._save_session_state()

    def should_create_snapshot(self) -> Tuple[bool, str]:
        """
        Check if a snapshot should be created based on tier and operation count.

        Returns:
            Tuple of (should_create, reason)
        """
        current_count = self.session_state["operation_count"]
        last_snapshot_count = self.session_state["last_snapshot_operation_count"]
        operations_since_snapshot = current_count - last_snapshot_count

        # Tier 1: Manual only (never create automatically)
        if self.current_tier == 1:
            return False, "Tier 1 (Rapid) - manual snapshots only"

        # Tier 3: After each operation
        if self.current_tier == 3:
            if operations_since_snapshot >= 1:
                return True, f"Tier 3 (Critical) - automatic snapshot after operation {current_count}"
            return False, "Tier 3 - snapshot already created for this operation"

        # Tier 2: Every 10 operations
        if self.current_tier == 2:
            if operations_since_snapshot >= 10:
                return True, f"Tier 2 (Standard) - automatic snapshot every 10 operations (current: {current_count})"
            return False, f"Tier 2 - {10 - operations_since_snapshot} operations until next snapshot"

        return False, f"Unknown tier: {self.current_tier}"

    def create_snapshot(
        self,
        trigger: str = "operation_count",
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a snapshot using create-snapshot.py.

        Args:
            trigger: Snapshot trigger reason
            description: Optional description for the snapshot

        Returns:
            Snapshot metadata if successful, None otherwise
        """
        try:
            # Build command
            cmd = [
                sys.executable,
                str(CREATE_SNAPSHOT_SCRIPT),
                "--auto",
                "--tier", str(self.current_tier),
                "--trigger", trigger,
                "--operation-count", str(self.session_state["operation_count"])
            ]

            if description:
                cmd.extend(["--description", description])

            # Execute snapshot creation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"⚠️  Snapshot creation failed: {result.stderr}", file=sys.stderr)
                return None

            # Update session state
            self.session_state["last_snapshot_operation_count"] = self.session_state["operation_count"]
            self.session_state["snapshots_this_session"] += 1
            self._save_session_state()

            # Parse output for snapshot ID (optional)
            # The output contains "Snapshot ID: [uuid]"
            for line in result.stdout.split('\n'):
                if "Snapshot ID:" in line:
                    snapshot_id = line.split("Snapshot ID:")[1].strip()
                    return {
                        "snapshot_id": snapshot_id,
                        "operation_count": self.session_state["operation_count"],
                        "tier": self.current_tier,
                        "trigger": trigger
                    }

            return {
                "success": True,
                "operation_count": self.session_state["operation_count"],
                "tier": self.current_tier
            }

        except subprocess.TimeoutExpired:
            print("⚠️  Snapshot creation timed out after 60 seconds", file=sys.stderr)
            return None
        except Exception as e:
            print(f"⚠️  Snapshot creation error: {e}", file=sys.stderr)
            return None

    def check_and_create_snapshot(
        self,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if snapshot is needed and create if necessary.

        Args:
            description: Optional description for the snapshot

        Returns:
            Snapshot metadata if created, None otherwise
        """
        should_create, reason = self.should_create_snapshot()

        if should_create:
            print(f"📸 Creating automatic snapshot: {reason}")
            return self.create_snapshot(
                trigger="operation_count",
                description=description or self.session_state.get("last_operation_description")
            )

        return None

    def on_tier_change(self, old_tier: int, new_tier: int) -> Optional[Dict[str, Any]]:
        """
        Create a snapshot when tier changes.

        Args:
            old_tier: Previous tier
            new_tier: New tier

        Returns:
            Snapshot metadata if created, None otherwise
        """
        description = f"Tier change: {old_tier} → {new_tier}"
        print(f"📸 Creating snapshot due to tier change: {description}")

        result = self.create_snapshot(
            trigger="tier_change",
            description=description
        )

        # Update current tier
        self.current_tier = new_tier

        return result

    def get_status(self) -> Dict[str, Any]:
        """
        Get current snapshot integration status.

        Returns:
            Status dictionary
        """
        current_count = self.session_state["operation_count"]
        last_snapshot_count = self.session_state["last_snapshot_operation_count"]
        operations_since_snapshot = current_count - last_snapshot_count

        should_create, reason = self.should_create_snapshot()

        return {
            "current_tier": self.current_tier,
            "operation_count": current_count,
            "operations_since_snapshot": operations_since_snapshot,
            "snapshots_this_session": self.session_state["snapshots_this_session"],
            "should_create_snapshot": should_create,
            "reason": reason,
            "last_operation_time": self.session_state.get("last_operation_time"),
            "last_operation_description": self.session_state.get("last_operation_description")
        }


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - Snapshot Integration Module"
    )

    parser.add_argument('--record', action='store_true',
                        help='Record a new operation')
    parser.add_argument('--description', '-d', type=str,
                        help='Description of the operation')
    parser.add_argument('--check', action='store_true',
                        help='Check if snapshot is needed and create if necessary')
    parser.add_argument('--status', action='store_true',
                        help='Show current snapshot integration status')
    parser.add_argument('--tier-change', type=str, metavar='OLD:NEW',
                        help='Record tier change (format: 2:3)')

    args = parser.parse_args()

    integration = SnapshotIntegration()

    if args.record:
        integration.record_operation(description=args.description)
        print(f"✅ Operation recorded (count: {integration.session_state['operation_count']})")

        # Automatically check after recording
        integration.check_and_create_snapshot()

    elif args.check:
        result = integration.check_and_create_snapshot(description=args.description)
        if result:
            print(f"✅ Snapshot created: {result.get('snapshot_id', 'success')}")
        else:
            _, reason = integration.should_create_snapshot()
            print(f"ℹ️  No snapshot needed: {reason}")

    elif args.tier_change:
        try:
            old, new = args.tier_change.split(':')
            old_tier = int(old)
            new_tier = int(new)
            result = integration.on_tier_change(old_tier, new_tier)
            if result:
                print(f"✅ Tier change snapshot created: {result.get('snapshot_id', 'success')}")
        except ValueError:
            print("❌ Invalid tier change format. Use: OLD:NEW (e.g., 2:3)", file=sys.stderr)
            sys.exit(1)

    elif args.status:
        status = integration.get_status()
        print("\n" + "=" * 80)
        print("Snapshot Integration Status")
        print("=" * 80)
        print(f"Current Tier: {status['current_tier']}")
        print(f"Operation Count: {status['operation_count']}")
        print(f"Operations Since Last Snapshot: {status['operations_since_snapshot']}")
        print(f"Snapshots This Session: {status['snapshots_this_session']}")
        print(f"\nShould Create Snapshot: {status['should_create_snapshot']}")
        print(f"Reason: {status['reason']}")

        if status['last_operation_time']:
            print(f"\nLast Operation: {status['last_operation_time']}")
            if status['last_operation_description']:
                print(f"Description: {status['last_operation_description']}")

        print("=" * 80 + "\n")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
