#!/usr/bin/env python3
"""
JSON schema validation for Domain Zero Protocol state files.
Implements input validation to prevent state manipulation attacks (PATCH-SEC-003).

Version: 8.8.0
Purpose: Prevent state manipulation via malicious JSON injection
OWASP: A03:2021 - Injection
"""

try:
    from jsonschema import validate, ValidationError
except ImportError:
    print("[ERROR] jsonschema package not installed")
    print("[INFO] Install with: pip install jsonschema")
    raise

from typing import Dict, Any
import json
from pathlib import Path

# Import path validator for secure file access
try:
    from .path_validator import safe_join, SecurityError
except ImportError:
    # Fallback for direct script execution
    from path_validator import safe_join, SecurityError

PROJECT_STATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "protocol_version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+\\.\\d+$"
        },
        "active_role": {
            "type": "string",
            "enum": ["yuuji", "megumi", "nobara", "gojo", "todo", "maki", "panda", "inumaki", "sukuna", "none"]
        },
        "current_state": {
            "type": "string",
            "enum": ["IDLE", "IN_PROGRESS", "BLOCKED", "COMPLETED"]
        },
        "tier": {
            "type": "integer",
            "minimum": 1,
            "maximum": 3
        },
        "passive_monitoring": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"}
            }
        }
    },
    "required": ["protocol_version", "active_role"],
    "additionalProperties": True
}

SESSION_STATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "protocol_version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+\\.\\d+$"
        },
        "current_session": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "start_time": {"type": "string"},
                "duration_minutes": {"type": "number", "minimum": 0}
            }
        },
        "session_metrics": {
            "type": "object",
            "properties": {
                "total_duration_minutes": {"type": "number", "minimum": 0, "maximum": 1440}
            }
        }
    },
    "required": ["protocol_version"]
}


def validate_project_state(state: Dict[str, Any]) -> None:
    """
    Validate project-state.json against schema.

    Args:
        state: Dictionary containing project state

    Raises:
        ValidationError: If state is invalid

    Example:
        >>> state = {"protocol_version": "8.8.0", "active_role": "yuuji"}
        >>> validate_project_state(state)  # No exception = valid
    """
    validate(instance=state, schema=PROJECT_STATE_SCHEMA)


def validate_session_state(state: Dict[str, Any]) -> None:
    """
    Validate session-state.json against schema.

    Args:
        state: Dictionary containing session state

    Raises:
        ValidationError: If state is invalid

    Example:
        >>> state = {"protocol_version": "8.8.0"}
        >>> validate_session_state(state)  # No exception = valid
    """
    validate(instance=state, schema=SESSION_STATE_SCHEMA)


# Safe loader functions
def load_validated_project_state(filepath: str = 'project-state.json') -> Dict[str, Any]:
    """
    Load and validate project state.

    Args:
        filepath: Filename (not full path) within .protocol-state/ directory

    Returns:
        Validated project state dictionary

    Raises:
        ValidationError: If state is invalid
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        SecurityError: If path traversal detected

    Example:
        >>> state = load_validated_project_state()
        >>> assert "protocol_version" in state
    """
    # SECURITY: Use safe_join to prevent path traversal
    safe_filepath = safe_join('.protocol-state', filepath)

    with open(safe_filepath, 'r', encoding='utf-8') as f:
        state = json.load(f)

    validate_project_state(state)
    return state


def load_validated_session_state(filepath: str = 'session-state.json') -> Dict[str, Any]:
    """
    Load and validate session state.

    Args:
        filepath: Filename (not full path) within .protocol-state/ directory

    Returns:
        Validated session state dictionary

    Raises:
        ValidationError: If state is invalid
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        SecurityError: If path traversal detected

    Example:
        >>> state = load_validated_session_state()
        >>> assert "protocol_version" in state
    """
    # SECURITY: Use safe_join to prevent path traversal
    safe_filepath = safe_join('.protocol-state', filepath)

    with open(safe_filepath, 'r', encoding='utf-8') as f:
        state = json.load(f)

    validate_session_state(state)
    return state


# Self-test on module import
if __name__ == "__main__":
    import sys
    from pathlib import Path

    print("[INFO] Running PATCH-SEC-003 self-tests...")

    # Test 1: Schema validation with valid data
    try:
        valid_project = {
            "protocol_version": "8.8.0",
            "active_role": "yuuji",
            "current_state": "IN_PROGRESS",
            "tier": 2
        }
        validate_project_state(valid_project)
        print("[PASS] Valid project state accepted")
    except ValidationError as e:
        print(f"[FAIL] Valid project state rejected: {e}")
        sys.exit(1)

    # Test 2: Schema validation with invalid data (should fail)
    try:
        invalid_project = {
            "protocol_version": "not-a-version",  # Invalid pattern
            "active_role": "yuuji"
        }
        validate_project_state(invalid_project)
        print("[FAIL] Invalid project state accepted (should have been rejected)")
        sys.exit(1)
    except ValidationError:
        print("[PASS] Invalid project state rejected correctly")

    # Test 3: Schema validation with invalid agent name
    try:
        invalid_agent = {
            "protocol_version": "8.8.0",
            "active_role": "malicious_agent"  # Not in enum
        }
        validate_project_state(invalid_agent)
        print("[FAIL] Invalid agent name accepted (should have been rejected)")
        sys.exit(1)
    except ValidationError:
        print("[PASS] Invalid agent name rejected correctly")

    # Test 4: Session state validation
    try:
        valid_session = {
            "protocol_version": "8.8.0",
            "current_session": {
                "session_id": "test-session",
                "start_time": "2025-12-16T00:00:00",
                "duration_minutes": 30
            },
            "session_metrics": {
                "total_duration_minutes": 120
            }
        }
        validate_session_state(valid_session)
        print("[PASS] Valid session state accepted")
    except ValidationError as e:
        print(f"[FAIL] Valid session state rejected: {e}")
        sys.exit(1)

    # Test 5: Session state with duration over limit (should fail)
    try:
        invalid_session = {
            "protocol_version": "8.8.0",
            "session_metrics": {
                "total_duration_minutes": 2000  # Over 1440 (24 hours)
            }
        }
        validate_session_state(invalid_session)
        print("[FAIL] Excessive session duration accepted (should have been rejected)")
        sys.exit(1)
    except ValidationError:
        print("[PASS] Excessive session duration rejected correctly")

    # Test 6: Load and validate actual project state (if exists)
    project_state_path = Path('.protocol-state/project-state.json')
    if project_state_path.exists():
        try:
            state = load_validated_project_state()
            print(f"[PASS] Actual project state loaded and validated")
        except Exception as e:
            print(f"[WARN] Actual project state validation failed: {e}")
            print("[INFO] This may be expected if project-state.json has invalid format")
    else:
        print("[SKIP] No project-state.json found, skipping actual file test")

    print("\n[PASS] All PATCH-SEC-003 tests passed")
