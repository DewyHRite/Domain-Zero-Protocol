#!/usr/bin/env python3
"""
Domain Zero Protocol - Working Directory Verification Utility

Version: 1.0.0
Created: 2025-12-06
Part of: DZP v8.8.0 Phase 4 - Component 1 (Safety Enhancement)

This utility verifies that scripts are running from the correct project root
directory before making any modifications. Prevents accidental operations in
wrong directories.

Usage:
    from verify_working_directory import verify_project_root

    if not verify_project_root():
        sys.exit(1)
"""

import sys
from pathlib import Path
from typing import Optional, List


def get_project_root() -> Optional[Path]:
    """
    Attempt to find the project root directory

    Returns:
        Path to project root if found, None otherwise
    """
    current = Path.cwd()

    # Check current directory first
    if is_project_root(current):
        return current

    # Check parent directories (up to 3 levels)
    for parent in current.parents[:3]:
        if is_project_root(parent):
            return parent

    return None


def is_project_root(path: Path) -> bool:
    """
    Check if a directory is the DZP project root

    Args:
        path: Directory to check

    Returns:
        True if directory is project root, False otherwise
    """
    required_markers = [
        'protocol/CLAUDE.md',
        'protocol.config.yaml',
        '.protocol-state/project-state.json'
    ]

    # All markers must exist
    return all((path / marker).exists() for marker in required_markers)


def get_missing_markers(path: Path) -> List[str]:
    """
    Get list of missing project markers

    Args:
        path: Directory to check

    Returns:
        List of missing marker file paths
    """
    required_markers = [
        'protocol/CLAUDE.md',
        'protocol.config.yaml',
        '.protocol-state/project-state.json'
    ]

    return [marker for marker in required_markers if not (path / marker).exists()]


def verify_project_root(silent: bool = False, exit_on_failure: bool = False) -> bool:
    """
    Verify that script is running from the correct project root directory

    Args:
        silent: If True, suppress output (only return boolean)
        exit_on_failure: If True, exit with code 1 on failure

    Returns:
        True if in correct directory, False otherwise
    """
    current_dir = Path.cwd()

    # Check if current directory is project root
    if is_project_root(current_dir):
        if not silent:
            print(f"[OK] Working directory verified: {current_dir}")
        return True

    # Try to find project root
    project_root = get_project_root()

    if project_root:
        if not silent:
            print(f"[WARN] Not in project root, but found root at: {project_root}")
            print(f"  Current directory: {current_dir}")
            print(f"  Recommended: cd {project_root}")

        if exit_on_failure:
            sys.exit(1)

        return False

    # Project root not found
    if not silent:
        print(f"[ERROR] Not in Domain Zero Protocol project root")
        print(f"  Current directory: {current_dir}")
        print(f"  Missing required files:")

        for marker in get_missing_markers(current_dir):
            print(f"    - {marker}")

        print(f"\n  Ensure you are in the correct directory:")
        print(f"    cd /path/to/Domain_Zero")
        print(f"    python scripts/{Path(__file__).name}")

    if exit_on_failure:
        sys.exit(1)

    return False


def require_project_root(script_name: Optional[str] = None) -> Path:
    """
    Verify project root and exit if not found (strict mode)

    Args:
        script_name: Name of calling script (for error messages)

    Returns:
        Path to verified project root

    Raises:
        SystemExit: If not in project root
    """
    if script_name:
        print(f"\n[{script_name}] Verifying working directory...")

    if not verify_project_root(silent=False, exit_on_failure=False):
        print(f"\n[CRITICAL] SAFETY CHECK FAILED: Cannot proceed outside project root")
        sys.exit(1)

    return Path.cwd()


# Convenience function for scripts
def ensure_project_root() -> Path:
    """
    Ensure script is running from project root (exits on failure)

    Returns:
        Path to project root
    """
    return require_project_root()


if __name__ == '__main__':
    """Test the verification utility"""
    print("Domain Zero Protocol - Working Directory Verification Test")
    print("=" * 70)

    result = verify_project_root(silent=False, exit_on_failure=False)

    if result:
        print("\n[OK] Verification PASSED")
        print(f"  Project root: {Path.cwd()}")
        sys.exit(0)
    else:
        print("\n[ERROR] Verification FAILED")
        sys.exit(1)
