#!/usr/bin/env python3
"""
Domain Zero Protocol - Memory Path Validator (v8.8.0)
SECURITY CRITICAL: Validates all Memory Tool paths to prevent directory traversal attacks

This module provides path validation for Memory Tool operations (/memories/ directory).
All Memory Tool paths MUST pass validation before use.

Author: Domain Zero Protocol Team
License: MIT
"""

import os
import re
from pathlib import Path
from typing import Tuple, List, Optional


class MemoryPathValidator:
    """
    Validates Memory Tool paths for security.

    Security Requirements:
    1. All paths must start with /memories/
    2. No directory traversal (.. sequences)
    3. Canonical path resolution enforced
    4. Whitelist-based directory access
    """

    # Required prefix for all memory paths
    MEMORY_PREFIX = "/memories/"

    # Allowed top-level directories under /memories/
    WHITELIST_DIRS = [
        "agents",
        "validation",
        "project"
    ]

    # Allowed agent subdirectories
    # Option: Load from environment or config file
    env_agents = os.environ.get("DZP_ALLOWED_AGENTS", "").strip()
    ALLOWED_AGENTS = [a.strip() for a in env_agents.split(",") if a.strip()] if env_agents else [
        "yuuji",
        "megumi",
        "nobara",
        "gojo",
        "sukuna",
        "todo",
        "maki",
        "panda",
        "inumaki"
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize path validator.

        Args:
            strict_mode: If True, only allow whitelisted directories
        """
        self.strict_mode = strict_mode
        self.validation_errors = []

    def validate_path(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a Memory Tool path.

        Args:
            path: Path to validate (e.g., "/memories/agents/yuuji/session-context.json")

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if path is safe to use
            - error_message: None if valid, error description if invalid

        Example:
            >>> validator = MemoryPathValidator()
            >>> is_valid, error = validator.validate_path("/memories/agents/yuuji/test.json")
            >>> if is_valid:
            ...     # Safe to use path
            ...     pass
        """
        self.validation_errors = []

        # Rule 1: Must start with /memories/
        if not path.startswith(self.MEMORY_PREFIX):
            return False, f"Path must start with '{self.MEMORY_PREFIX}' (got: {path})"

        # Rule 2: No directory traversal
        # Check for literal and common encoded variants
        traversal_patterns = ["..", "%2e%2e", "%2E%2E", "..%2f", "..%5c"]
        if any(p in path for p in traversal_patterns):
            return False, f"Directory traversal not allowed (path contains '..'): {path}"

        # Rule 3: Canonical path resolution
        try:
            canonical = self._resolve_canonical(path)
            # Allow exact match of /memories (root directory)
            if canonical != "/memories" and not canonical.startswith(self.MEMORY_PREFIX):
                return False, f"Canonical path escapes /memories/: {canonical}"
        except Exception as e:
            return False, f"Path resolution error: {str(e)}"

        # Rule 4: Whitelist validation (if strict mode)
        if self.strict_mode:
            whitelist_error = self._validate_whitelist(path)
            if whitelist_error:
                return False, whitelist_error

        # Rule 5: No dangerous characters
        dangerous_chars = ["<", ">", "|", "&", ";", "`", "$", "(", ")", "{", "}"]
        for char in dangerous_chars:
            if char in path:
                return False, f"Dangerous character '{char}' not allowed in path"

        # All checks passed
        return True, None

    def _resolve_canonical(self, path: str) -> str:
        """
        Resolve path to canonical form.

        Args:
            path: Memory Tool path

        Returns:
            Canonical path (normalized)
        """
        # Normalize path separators
        normalized = path.replace("\\", "/")

        # Remove duplicate slashes
        normalized = re.sub(r'/+', '/', normalized)

        # Resolve . and .. components
        parts = []
        for part in normalized.split('/'):
            if part == '' or part == '.':
                continue
            elif part == '..':
                if parts and parts[-1] != '..':
                    parts.pop()
            else:
                parts.append(part)

        # Reconstruct path with single leading slash
        canonical = '/' + '/'.join(parts)

        return canonical

    def _validate_whitelist(self, path: str) -> Optional[str]:
        """
        Validate path against whitelist.

        Args:
            path: Memory Tool path

        Returns:
            Error message if invalid, None if valid
        """
        # Remove /memories/ prefix
        relative_path = path[len(self.MEMORY_PREFIX):]

        # Split into components
        parts = [p for p in relative_path.split('/') if p]

        if not parts:
            # Root /memories/ directory is valid
            return None

        # Check top-level directory
        top_level = parts[0]
        if top_level not in self.WHITELIST_DIRS:
            return f"Top-level directory '{top_level}' not in whitelist. Allowed: {self.WHITELIST_DIRS}"

        # Special validation for agents/ subdirectory
        if top_level == "agents" and len(parts) > 1:
            agent_name = parts[1]
            if agent_name not in self.ALLOWED_AGENTS:
                return f"Agent '{agent_name}' not in allowed list. Allowed: {self.ALLOWED_AGENTS}"

        return None

    def validate_batch(self, paths: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
        """
        Validate multiple paths.

        Args:
            paths: List of paths to validate

        Returns:
            List of tuples: (path, is_valid, error_message)
        """
        results = []
        for path in paths:
            is_valid, error = self.validate_path(path)
            results.append((path, is_valid, error))
        return results

    def get_safe_path(self, path: str) -> Optional[str]:
        """
        Attempt to sanitize and return a safe version of the path.

        Args:
            path: Potentially unsafe path

        Returns:
            Safe path if possible, None if path cannot be made safe
        """
        # Add /memories/ prefix if missing
        if not path.startswith(self.MEMORY_PREFIX):
            if path.startswith("/"):
                path = self.MEMORY_PREFIX + path[1:]
            else:
                path = self.MEMORY_PREFIX + path

        # Attempt to resolve canonical
        try:
            canonical = self._resolve_canonical(path)
        except Exception:
            return None

        # Validate the sanitized path
        is_valid, _ = self.validate_path(canonical)
        if is_valid:
            return canonical
        return None


# Convenience functions for common operations

def validate_memory_path(path: str, strict: bool = True) -> bool:
    """
    Quick validation check for a single path.

    Args:
        path: Memory Tool path to validate
        strict: Enable whitelist validation

    Returns:
        True if path is valid, False otherwise

    Example:
        >>> if validate_memory_path("/memories/agents/yuuji/test.json"):
        ...     # Safe to use
        ...     pass
    """
    validator = MemoryPathValidator(strict_mode=strict)
    is_valid, _ = validator.validate_path(path)
    return is_valid


def get_validation_error(path: str, strict: bool = True) -> Optional[str]:
    """
    Get detailed error message for invalid path.

    Args:
        path: Memory Tool path to validate
        strict: Enable whitelist validation

    Returns:
        Error message if invalid, None if valid

    Example:
        >>> error = get_validation_error("/invalid/path")
        >>> if error:
        ...     print(f"Path invalid: {error}")
    """
    validator = MemoryPathValidator(strict_mode=strict)
    _, error = validator.validate_path(path)
    return error


def sanitize_memory_path(path: str) -> Optional[str]:
    """
    Attempt to fix common path issues.

    Args:
        path: Potentially unsafe path

    Returns:
        Safe path if possible, None if unfixable

    Example:
        >>> safe = sanitize_memory_path("agents/yuuji/test.json")
        >>> print(safe)
        /memories/agents/yuuji/test.json
    """
    validator = MemoryPathValidator()
    return validator.get_safe_path(path)


# Security Tests (run with: python -m doctest memory_path_validator.py)

def run_security_tests():
    """Run comprehensive security tests."""
    validator = MemoryPathValidator()

    # Test cases: (path, should_be_valid, description)
    test_cases = [
        # Valid paths
        ("/memories/agents/yuuji/session-context.json", True, "Valid agent file"),
        ("/memories/validation/snapshots/test.json", True, "Valid validation file"),
        ("/memories/project/tier-config.yaml", True, "Valid project file"),
        ("/memories/", True, "Root memories directory"),

        # Invalid: missing prefix
        ("/agents/yuuji/test.json", False, "Missing /memories/ prefix"),
        ("memories/agents/yuuji/test.json", False, "Missing leading slash"),

        # Invalid: directory traversal
        ("/memories/../etc/passwd", False, "Directory traversal up"),
        ("/memories/agents/../validation/test.json", False, "Directory traversal in path"),

        # Invalid: not in whitelist
        ("/memories/evil/malicious.json", False, "Directory not in whitelist"),

        # Invalid: unknown agent
        ("/memories/agents/hacker/evil.json", False, "Unknown agent name"),

        # Invalid: dangerous characters
        ("/memories/agents/yuuji/file;rm -rf.json", False, "Command injection attempt"),
        ("/memories/agents/yuuji/file$(whoami).json", False, "Command substitution"),
    ]

    print("Running Memory Path Validator Security Tests...\n")
    passed = 0
    failed = 0

    for path, should_be_valid, description in test_cases:
        is_valid, error = validator.validate_path(path)

        if is_valid == should_be_valid:
            print(f"[PASS] {description}")
            print(f"  Path: {path}")
            if error:
                print(f"  Error: {error}")
            passed += 1
        else:
            print(f"[FAIL] {description}")
            print(f"  Path: {path}")
            print(f"  Expected valid={should_be_valid}, got valid={is_valid}")
            if error:
                print(f"  Error: {error}")
            failed += 1
        print()

    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    # Run security tests
    import sys
    success = run_security_tests()
    sys.exit(0 if success else 1)
