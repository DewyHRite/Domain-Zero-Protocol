#!/usr/bin/env python3
"""
Domain Zero Protocol - 3-Strike Tier Bypass Enforcement System

Version: 1.0.0
Created: 2025-12-05
Part of: DZP v8.8.0 Validation Framework (Approved Enhancement)

This script implements the 3-strike tier bypass tracking system that:
- Tracks tier override attempts per month
- Allows up to 3 bypasses per calendar month
- Hard-blocks further bypasses after 3rd strike
- Automatically resets counter at month boundary

Original Plan Note:
- Original v8.8.0 plan specified "Tier 2: Warns user, allows override"
- Enhancement added via clarification: 3-strike bypass system per month
- User approval: Hybrid plan (keep this enhancement, revert others)

Usage:
    python scripts/tier-enforcement.py --check             # Check bypass status
    python scripts/tier-enforcement.py --record            # Record a bypass
    python scripts/tier-enforcement.py --reset             # Reset counter (admin)
    python scripts/tier-enforcement.py --status            # Show full status
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_STATE_FILE = PROJECT_ROOT / ".protocol-state" / "project-state.json"

# 3-strike system constants
MAX_BYPASSES_PER_MONTH = 3


# =============================================================================
# Project State Management
# =============================================================================

def load_project_state() -> Dict[str, Any]:
    """
    Load project-state.json

    Returns:
        Project state dictionary

    Raises:
        FileNotFoundError: If project-state.json doesn't exist
        json.JSONDecodeError: If file is malformed
    """
    if not PROJECT_STATE_FILE.exists():
        raise FileNotFoundError(f"Project state file not found: {PROJECT_STATE_FILE}")

    with open(PROJECT_STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_project_state(state: Dict[str, Any]) -> None:
    """
    Save project-state.json

    Args:
        state: Project state dictionary to save
    """
    with open(PROJECT_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def initialize_bypass_tracking(state: Dict[str, Any]) -> None:
    """
    Initialize bypass tracking in project-state.json if not present

    Args:
        state: Project state dictionary

    Modifies state in-place to add tier_settings.bypass_tracking structure
    """
    # Ensure tier_settings exists
    if "tier_settings" not in state:
        state["tier_settings"] = {
            "default_tier": 2  # Tier 2: Standard (default)
        }

    # Initialize bypass tracking if not present
    if "bypass_tracking" not in state["tier_settings"]:
        current_month = datetime.utcnow().strftime("%Y-%m")

        state["tier_settings"]["bypass_tracking"] = {
            "enabled": True,
            "current_month": current_month,
            "bypass_count": 0,
            "last_bypass": None
        }


# =============================================================================
# Bypass Tracking Functions
# =============================================================================

def get_current_month() -> str:
    """
    Get current month in YYYY-MM format

    Returns:
        Current month string (e.g., "2025-12")
    """
    return datetime.now(timezone.utc).strftime("%Y-%m")


def check_month_rollover(state: Dict[str, Any]) -> bool:
    """
    Check if month has rolled over and reset counter if needed

    Args:
        state: Project state dictionary

    Returns:
        True if month rolled over and counter was reset, False otherwise
    """
    initialize_bypass_tracking(state)

    tracking = state["tier_settings"]["bypass_tracking"]
    current_month = get_current_month()

    if tracking["current_month"] != current_month:
        # Month rollover - reset counter
        tracking["current_month"] = current_month
        tracking["bypass_count"] = 0
        save_project_state(state)
        return True

    return False


def can_bypass_tier_warning() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if user can bypass tier warning (has remaining strikes)

    Returns:
        Tuple of (can_bypass: bool, reason: str, status: dict)
        - can_bypass: True if user can bypass, False if hard-blocked
        - reason: Human-readable explanation
        - status: Current bypass tracking status
    """
    try:
        state = load_project_state()
        initialize_bypass_tracking(state)

        # Check for month rollover
        rolled_over = check_month_rollover(state)

        tracking = state["tier_settings"]["bypass_tracking"]

        # Check if tracking is disabled
        if not tracking.get("enabled", True):
            return (True, "Bypass tracking is disabled", tracking)

        # Check bypass count
        bypass_count = tracking.get("bypass_count", 0)
        remaining = MAX_BYPASSES_PER_MONTH - bypass_count

        status = {
            "current_month": tracking["current_month"],
            "bypass_count": bypass_count,
            "max_bypasses": MAX_BYPASSES_PER_MONTH,
            "remaining": remaining,
            "last_bypass": tracking.get("last_bypass"),
            "month_rolled_over": rolled_over
        }

        if bypass_count >= MAX_BYPASSES_PER_MONTH:
            # HARD-BLOCK: No more bypasses this month
            reason = f"HARD-BLOCKED: You've used all {MAX_BYPASSES_PER_MONTH} tier bypasses for {tracking['current_month']}. Next reset: {get_next_month()}"
            return (False, reason, status)
        else:
            # Can bypass
            reason = f"Bypass allowed ({remaining}/{MAX_BYPASSES_PER_MONTH} remaining for {tracking['current_month']})"
            return (True, reason, status)

    except FileNotFoundError as e:
        return (False, f"ERROR: {e}", {})
    except Exception as e:
        return (False, f"ERROR: Unexpected error: {e}", {})


def record_bypass(tier: int, reason: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Record a tier bypass (increment counter)

    Args:
        tier: Tier that was bypassed (1, 2, or 3)
        reason: Optional reason for bypass

    Returns:
        Tuple of (success: bool, message: str, status: dict)
    """
    try:
        state = load_project_state()
        initialize_bypass_tracking(state)

        # Check for month rollover
        check_month_rollover(state)

        tracking = state["tier_settings"]["bypass_tracking"]

        # Check if already at limit
        can_bypass, check_reason, status = can_bypass_tier_warning()
        if not can_bypass:
            return (False, check_reason, status)

        # Increment bypass counter
        tracking["bypass_count"] = tracking.get("bypass_count", 0) + 1
        tracking["last_bypass"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # Save state
        save_project_state(state)

        # Calculate remaining
        remaining = MAX_BYPASSES_PER_MONTH - tracking["bypass_count"]

        message = f"Bypass recorded for Tier {tier}. {remaining}/{MAX_BYPASSES_PER_MONTH} bypasses remaining for {tracking['current_month']}"

        if remaining == 0:
            message += f"\n⚠️ WARNING: You've used all bypasses for this month. Next bypass will be HARD-BLOCKED until {get_next_month()}."

        status = {
            "current_month": tracking["current_month"],
            "bypass_count": tracking["bypass_count"],
            "max_bypasses": MAX_BYPASSES_PER_MONTH,
            "remaining": remaining,
            "last_bypass": tracking["last_bypass"]
        }

        return (True, message, status)

    except FileNotFoundError as e:
        return (False, f"ERROR: {e}", {})
    except Exception as e:
        return (False, f"ERROR: Unexpected error: {e}", {})


def reset_bypass_counter(admin_override: bool = False) -> Tuple[bool, str]:
    """
    Reset bypass counter (admin function)

    Args:
        admin_override: If True, allows manual reset mid-month

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        state = load_project_state()
        initialize_bypass_tracking(state)

        tracking = state["tier_settings"]["bypass_tracking"]

        old_count = tracking.get("bypass_count", 0)
        old_month = tracking.get("current_month", "unknown")

        # Reset counter
        tracking["bypass_count"] = 0
        tracking["current_month"] = get_current_month()

        save_project_state(state)

        if admin_override:
            message = f"Admin override: Bypass counter reset from {old_count} to 0 (month: {old_month} → {tracking['current_month']})"
        else:
            message = f"Bypass counter reset: {old_count} → 0 (new month: {tracking['current_month']})"

        return (True, message)

    except FileNotFoundError as e:
        return (False, f"ERROR: {e}")
    except Exception as e:
        return (False, f"ERROR: Unexpected error: {e}")


def get_bypass_status() -> Dict[str, Any]:
    """
    Get current bypass tracking status

    Returns:
        Dictionary with bypass tracking status
    """
    try:
        state = load_project_state()
        initialize_bypass_tracking(state)

        # Check for month rollover
        rolled_over = check_month_rollover(state)

        tracking = state["tier_settings"]["bypass_tracking"]
        bypass_count = tracking.get("bypass_count", 0)
        remaining = MAX_BYPASSES_PER_MONTH - bypass_count

        can_bypass, reason, _ = can_bypass_tier_warning()

        return {
            "enabled": tracking.get("enabled", True),
            "current_month": tracking["current_month"],
            "bypass_count": bypass_count,
            "max_bypasses": MAX_BYPASSES_PER_MONTH,
            "remaining": remaining,
            "can_bypass": can_bypass,
            "status": "OK" if can_bypass else "BLOCKED",
            "last_bypass": tracking.get("last_bypass"),
            "next_reset": get_next_month(),
            "month_rolled_over": rolled_over
        }

    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Utility Functions
# =============================================================================

def get_next_month() -> str:
    """
    Get next month in YYYY-MM format

    Returns:
        Next month string (e.g., "2025-01")
    """
    current = datetime.now(timezone.utc)
    if current.month == 12:
        return f"{current.year + 1}-01"
    else:
        return f"{current.year}-{current.month + 1:02d}"


def print_status(status: Dict[str, Any]) -> None:
    """
    Print bypass tracking status in human-readable format

    Args:
        status: Status dictionary from get_bypass_status()
    """
    if "error" in status:
        print(f"ERROR: {status['error']}")
        return

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║         3-Strike Tier Bypass Tracking System                ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\nStatus:        {status['status']}")
    print(f"Current Month: {status['current_month']}")
    print(f"Bypasses Used: {status['bypass_count']}/{status['max_bypasses']}")
    print(f"Remaining:     {status['remaining']}")

    if status['last_bypass']:
        last_bypass_dt = datetime.fromisoformat(status['last_bypass'].replace('Z', '+00:00'))
        print(f"Last Bypass:   {last_bypass_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    else:
        print("Last Bypass:   Never")

    print(f"Next Reset:    {status['next_reset']}-01")

    if status['month_rolled_over']:
        print("\n✅ Month rolled over - counter automatically reset")

    if status['can_bypass']:
        if status['remaining'] == 1:
            print(f"\n⚠️  WARNING: Only {status['remaining']} bypass remaining this month!")
        elif status['remaining'] == 0:
            print("\n🚫 HARD-BLOCKED: No bypasses remaining this month!")
        else:
            print(f"\n✅ You can bypass tier warnings ({status['remaining']} remaining)")
    else:
        print("\n🚫 HARD-BLOCKED: No more bypasses allowed until next month")
        print(f"   Counter resets on {status['next_reset']}-01")

    print()


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - 3-Strike Tier Bypass Enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check                Check if bypass is allowed
  %(prog)s --record --tier 2      Record a Tier 2 bypass
  %(prog)s --status               Show full bypass tracking status
  %(prog)s --reset --admin        Reset counter (admin override)

3-Strike System:
  - Users can bypass tier warnings up to 3 times per month
  - 4th bypass attempt is HARD-BLOCKED
  - Counter automatically resets at month boundary
  - Bypass = using Tier 1 workflow when Tier 2/3 is recommended

Note: This is an APPROVED ENHANCEMENT to the original v8.8.0 plan.
      Original plan: "Tier 2: Warns user, allows override" (no mechanism)
      Enhancement: 3-strike bypass system per month
        """
    )

    parser.add_argument('--check', action='store_true',
                        help='Check if bypass is currently allowed')
    parser.add_argument('--record', action='store_true',
                        help='Record a tier bypass (increment counter)')
    parser.add_argument('--tier', type=int, choices=[1, 2, 3],
                        help='Tier that was bypassed (required with --record)')
    parser.add_argument('--reason', type=str, default="",
                        help='Optional reason for bypass')
    parser.add_argument('--status', action='store_true',
                        help='Show full bypass tracking status')
    parser.add_argument('--reset', action='store_true',
                        help='Reset bypass counter (use with --admin)')
    parser.add_argument('--admin', action='store_true',
                        help='Admin override flag (allows mid-month reset)')
    parser.add_argument('--init', action='store_true',
                        help='Initialize bypass tracking in project-state.json')

    args = parser.parse_args()

    # Validate arguments
    if args.record and not args.tier:
        print("ERROR: --tier is required with --record", file=sys.stderr)
        sys.exit(1)

    if args.admin and not args.reset:
        print("ERROR: --admin requires --reset", file=sys.stderr)
        sys.exit(1)

    # Execute commands
    try:
        if args.init:
            # Initialize bypass tracking
            state = load_project_state()
            initialize_bypass_tracking(state)
            save_project_state(state)
            print("✅ Bypass tracking initialized in project-state.json")
            status = get_bypass_status()
            print_status(status)

        elif args.check:
            # Check if bypass is allowed
            can_bypass, reason, status = can_bypass_tier_warning()
            print(f"\n{reason}\n")
            if can_bypass:
                print(f"✅ Status: {status['remaining']}/{status['max_bypasses']} bypasses remaining for {status['current_month']}")
                sys.exit(0)
            else:
                print(f"🚫 BLOCKED until {get_next_month()}-01")
                sys.exit(1)

        elif args.record:
            # Record a bypass
            success, message, status = record_bypass(args.tier, args.reason)
            print(f"\n{message}\n")
            if success:
                sys.exit(0)
            else:
                sys.exit(1)

        elif args.reset:
            # Reset counter
            success, message = reset_bypass_counter(admin_override=args.admin)
            print(f"\n{message}\n")
            if success:
                sys.exit(0)
            else:
                sys.exit(1)

        elif args.status:
            # Show full status
            status = get_bypass_status()
            print_status(status)
            sys.exit(0)

        else:
            # No command specified - show status by default
            status = get_bypass_status()
            print_status(status)
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
