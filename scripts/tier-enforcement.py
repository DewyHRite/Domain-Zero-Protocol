#!/usr/bin/env python3
"""
Domain Zero Protocol - Tier Bypass Tracking System (Statistics Only)

Version: 2.0.0
Created: 2025-12-05
Updated: 2025-12-06
Part of: DZP v8.8.0 Validation Framework

This script tracks tier bypass statistics for analytics and reporting:
- Records tier override attempts per month
- Provides usage statistics and patterns
- NO ENFORCEMENT - Always allows bypasses
- Automatically resets counter at month boundary

Original Plan Alignment:
- Original v8.8.0 plan: "Tier 2: Warns user, allows override"
- This implementation: Tracks for statistics, never blocks
- User feedback: 3-strike hard-block was too restrictive

Usage:
    python scripts/tier-enforcement.py --check             # Always returns OK
    python scripts/tier-enforcement.py --record            # Record a bypass
    python scripts/tier-enforcement.py --reset             # Reset counter
    python scripts/tier-enforcement.py --status            # Show statistics
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

# Statistics tracking (no enforcement limits)
BYPASS_TRACKING_ENABLED = True


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
    Check bypass tracking status (always allows bypass - statistics only)

    Returns:
        Tuple of (can_bypass: bool, reason: str, status: dict)
        - can_bypass: Always True (no enforcement, statistics only)
        - reason: Human-readable explanation with current statistics
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

        # Get bypass count (for statistics only, no enforcement)
        bypass_count = tracking.get("bypass_count", 0)

        status = {
            "current_month": tracking["current_month"],
            "bypass_count": bypass_count,
            "last_bypass": tracking.get("last_bypass"),
            "month_rolled_over": rolled_over
        }

        # Always allow bypass - this is statistics only
        reason = f"Bypass allowed (statistics only: {bypass_count} bypasses recorded this month)"
        return (True, reason, status)

    except FileNotFoundError as e:
        return (True, f"WARNING: {e} (allowing bypass)", {})
    except Exception as e:
        return (True, f"WARNING: Unexpected error: {e} (allowing bypass)", {})


def record_bypass(tier: int, reason: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Record a tier bypass for statistics tracking (no enforcement)

    Args:
        tier: Tier that was bypassed (1, 2, or 3)
        reason: Optional reason for bypass

    Returns:
        Tuple of (success: bool, message: str, status: dict)
        - Always succeeds (statistics only, no blocking)
    """
    try:
        state = load_project_state()
        initialize_bypass_tracking(state)

        # Check for month rollover
        check_month_rollover(state)

        tracking = state["tier_settings"]["bypass_tracking"]

        # Increment bypass counter (statistics only)
        tracking["bypass_count"] = tracking.get("bypass_count", 0) + 1
        tracking["last_bypass"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # Save state
        save_project_state(state)

        bypass_count = tracking["bypass_count"]
        message = f"Bypass recorded for Tier {tier}. Total this month: {bypass_count} (statistics only, no limits)"

        status = {
            "current_month": tracking["current_month"],
            "bypass_count": bypass_count,
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
    Get current bypass tracking status (statistics only)

    Returns:
        Dictionary with bypass tracking statistics
    """
    try:
        state = load_project_state()
        initialize_bypass_tracking(state)

        # Check for month rollover
        rolled_over = check_month_rollover(state)

        tracking = state["tier_settings"]["bypass_tracking"]
        bypass_count = tracking.get("bypass_count", 0)

        return {
            "enabled": tracking.get("enabled", True),
            "current_month": tracking["current_month"],
            "bypass_count": bypass_count,
            "can_bypass": True,  # Always true - statistics only
            "status": "TRACKING",
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
    print("║       Tier Bypass Tracking System (Statistics Only)         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\nStatus:        {status['status']}")
    print(f"Current Month: {status['current_month']}")
    print(f"Bypasses This Month: {status['bypass_count']}")

    if status['last_bypass']:
        last_bypass_dt = datetime.fromisoformat(status['last_bypass'].replace('Z', '+00:00'))
        print(f"Last Bypass:   {last_bypass_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    else:
        print("Last Bypass:   Never")

    print(f"Next Reset:    {status['next_reset']}-01")

    if status['month_rolled_over']:
        print("\n✅ Month rolled over - counter automatically reset")

    print("\nℹ️  Statistics only - bypasses are always allowed (no enforcement)")
    print()


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - Tier Bypass Tracking (Statistics Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check                Check bypass status (always returns OK)
  %(prog)s --record --tier 2      Record a Tier 2 bypass
  %(prog)s --status               Show bypass statistics
  %(prog)s --reset                Reset monthly counter

Statistics-Only Tracking:
  - Tracks tier bypasses for analytics and reporting
  - NO ENFORCEMENT - Bypasses are always allowed
  - Counter automatically resets at month boundary
  - Bypass = using Tier 1 workflow when Tier 2/3 is recommended

Original Plan Alignment:
  - Original v8.8.0 plan: "Tier 2: Warns user, allows override"
  - This implementation: Tracks for statistics, never blocks
  - User feedback: Hard-blocking was too restrictive
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
