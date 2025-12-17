#!/usr/bin/env python3
"""
Path validation and sanitization for Domain Zero Protocol.
Implements safe path joining to prevent directory traversal attacks (PATCH-SEC-004).

Version: 8.8.0
Purpose: Prevent path traversal via directory traversal sequences
OWASP: A01:2021 - Broken Access Control
"""

from pathlib import Path
from typing import Union


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


def safe_join(base_dir: Union[str, Path], user_path: Union[str, Path]) -> Path:
    """
    Safely join paths, preventing directory traversal attacks.

    Args:
        base_dir: Base directory that user_path must remain within
        user_path: User-supplied path component

    Returns:
        Resolved Path object within base_dir

    Raises:
        SecurityError: If user_path attempts to escape base_dir

    Examples:
        >>> safe_join('.protocol-state/backups', 'session-20251211.json')
        WindowsPath('.protocol-state/backups/session-20251211.json')

        >>> safe_join('.protocol-state', '../../etc/passwd')
        SecurityError: Path traversal detected
    """
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()

    # Use is_relative_to() to prevent path confusion attacks
    # (e.g., /home/user vs /home/username substring matching)
    try:
        # Python 3.9+ has is_relative_to()
        if not target.is_relative_to(base):
            raise SecurityError(
                f"Path traversal detected: {user_path}\n"
                f"Attempted to access: {target}\n"
                f"Must remain within: {base}"
            )
    except AttributeError:
        # Fallback for Python < 3.9: use relative_to()
        try:
            target.relative_to(base)
        except ValueError:
            raise SecurityError(
                f"Path traversal detected: {user_path}\n"
                f"Attempted to access: {target}\n"
                f"Must remain within: {base}"
            )

    return target


def validate_backup_path(backup_name: str) -> Path:
    """
    Validate backup filename and return safe path.

    Args:
        backup_name: User-supplied backup filename

    Returns:
        Safe path within .protocol-state/backups/

    Raises:
        SecurityError: If backup name contains invalid characters

    Example:
        >>> validate_backup_path('session-20251211.json')
        WindowsPath('.protocol-state/backups/session-20251211.json')

        >>> validate_backup_path('../../../etc/passwd')
        SecurityError: Invalid backup name
    """
    # Validate backup name is not empty
    if not backup_name or not backup_name.strip():
        raise SecurityError("Backup name cannot be empty")

    # Whitelist allowed characters
    if not all(c.isalnum() or c in '-_.' for c in backup_name):
        raise SecurityError(f"Invalid backup name: {backup_name}")

    return safe_join('.protocol-state/backups', backup_name)


# Self-test on module import
if __name__ == "__main__":
    import sys

    print("[INFO] Running PATCH-SEC-004 self-tests...")

    # Test 1: Valid path should be accepted
    try:
        result = safe_join('.protocol-state/backups', 'test.json')
        print("[PASS] Valid path accepted")
    except SecurityError:
        print("[FAIL] Valid path rejected (false positive)")
        sys.exit(1)

    # Test 2: Path traversal should be blocked
    try:
        result = safe_join('.protocol-state', '../../etc/passwd')
        print("[FAIL] Path traversal not blocked")
        sys.exit(1)
    except SecurityError:
        print("[PASS] Path traversal blocked")

    # Test 3: Absolute path traversal should be blocked
    try:
        result = safe_join('.protocol-state', '/etc/passwd')
        print("[FAIL] Absolute path traversal not blocked")
        sys.exit(1)
    except SecurityError:
        print("[PASS] Absolute path traversal blocked")

    # Test 4: Nested path traversal should be blocked
    try:
        result = safe_join('.protocol-state/backups', 'test/../../../../../../etc/passwd')
        print("[FAIL] Nested path traversal not blocked")
        sys.exit(1)
    except SecurityError:
        print("[PASS] Nested path traversal blocked")

    # Test 5: Valid backup name should be accepted
    try:
        result = validate_backup_path('session-20251211.json')
        print("[PASS] Valid backup name accepted")
    except SecurityError:
        print("[FAIL] Valid backup name rejected")
        sys.exit(1)

    # Test 6: Invalid backup name with path traversal should be rejected
    try:
        result = validate_backup_path('../../../etc/passwd')
        print("[FAIL] Invalid backup name not rejected")
        sys.exit(1)
    except SecurityError:
        print("[PASS] Invalid backup name rejected")

    # Test 7: Backup name with special characters should be rejected
    try:
        result = validate_backup_path('test;rm -rf /')
        print("[FAIL] Backup name with special characters not rejected")
        sys.exit(1)
    except SecurityError:
        print("[PASS] Backup name with special characters rejected")

    # Test 8: Valid nested path
    try:
        result = safe_join('.protocol-state', 'backups/test.json')
        expected_base = Path('.protocol-state').resolve()

        # Use is_relative_to() to match production code security (Python 3.9+)
        try:
            if not result.is_relative_to(expected_base):
                print(f"[FAIL] Valid nested path rejected: {result}")
                sys.exit(1)
        except AttributeError:
            # Fallback for Python < 3.9: use relative_to()
            try:
                result.relative_to(expected_base)
            except ValueError:
                print(f"[FAIL] Valid nested path rejected: {result}")
                sys.exit(1)

        print("[PASS] Valid nested path accepted")
    except SecurityError:
        print("[FAIL] Valid nested path rejected (false positive)")
        sys.exit(1)

    print("\n[PASS] All PATCH-SEC-004 tests passed")
