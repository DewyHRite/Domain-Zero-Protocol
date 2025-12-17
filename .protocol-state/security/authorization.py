#!/usr/bin/env python3
"""
Cryptographic authorization system for Domain Zero Protocol.
Implements HMAC-SHA256 tokens with expiration (PATCH-SEC-001).

Version: 8.8.0
Purpose: Prevent agent impersonation attacks via prompt injection
OWASP: A07:2021 - Identification and Authentication Failures
"""

import hmac
import hashlib
import time
import os
from pathlib import Path
from typing import Optional, Tuple

# Generate secret key per session (store in .protocol-state/security/.auth_key)
AUTH_KEY_FILE = Path('.protocol-state/security/.auth_key')


def _get_or_create_secret_key() -> bytes:
    """Get existing secret key or generate new one."""
    os.makedirs('.protocol-state/security', exist_ok=True)

    if AUTH_KEY_FILE.exists():
        with open(AUTH_KEY_FILE, 'rb') as f:
            return f.read()

    # Generate new key
    secret_key = os.urandom(32)
    with open(AUTH_KEY_FILE, 'wb') as f:
        f.write(secret_key)

    # Ensure .gitignore includes this file
    gitignore_path = Path('.protocol-state/.gitignore')
    gitignore_content = gitignore_path.read_text() if gitignore_path.exists() else ''
    if 'security/.auth_key' not in gitignore_content:
        with open(gitignore_path, 'a') as f:
            f.write('\n# PATCH-SEC-001: Authorization secret key\nsecurity/.auth_key\n')

    return secret_key


SECRET_KEY = _get_or_create_secret_key()


def generate_auth_token(operation: str, agent_id: str, expires_in: int = 1800) -> str:
    """
    Generate cryptographic authorization token.

    Args:
        operation: Operation being authorized (e.g., "CLAUDE.md:edit", "sukuna:invoke")
        agent_id: Agent requesting authorization (e.g., "gojo", "user")
        expires_in: Token validity in seconds (default: 30 minutes)

    Returns:
        Token string in format: "operation:agent_id:timestamp:signature"

    Example:
        >>> token = generate_auth_token('CLAUDE.md:edit', 'gojo')
        >>> # Returns: "CLAUDE.md:edit:gojo:1234567890:abc123..."
    """
    timestamp = int(time.time()) + expires_in
    message = f"{operation}:{agent_id}:{timestamp}"
    signature = hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()
    return f"{message}:{signature}"


def verify_auth_token(token: str, operation: str) -> Tuple[bool, Optional[str]]:
    """
    Verify authorization token.

    Args:
        token: Token to verify
        operation: Expected operation

    Returns:
        (is_valid, error_message)
            - is_valid: True if token is valid, False otherwise
            - error_message: None if valid, error description if invalid

    Example:
        >>> token = generate_auth_token('CLAUDE.md:edit', 'gojo')
        >>> valid, error = verify_auth_token(token, 'CLAUDE.md:edit')
        >>> assert valid and error is None
    """
    try:
        parts = token.rsplit(':', 1)
        if len(parts) != 2:
            return False, "Invalid token format"

        message, signature = parts

        # Verify signature using constant-time comparison
        expected_sig = hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return False, "Invalid signature"

        # Parse message (operation can contain colons, so parse from right)
        message_parts = message.split(':')
        if len(message_parts) < 3:
            return False, "Invalid message format"

        # Last two parts are always agent and timestamp
        timestamp_str = message_parts[-1]
        agent = message_parts[-2]
        # Everything else is the operation
        op = ':'.join(message_parts[:-2])

        # Verify operation
        if op != operation:
            return False, f"Token for '{op}', expected '{operation}'"

        # Verify expiration
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return False, "Invalid timestamp"

        if timestamp < time.time():
            return False, "Token expired"

        return True, None

    except Exception as e:
        return False, f"Token verification failed: {e}"


def require_gojo_authorization(operation: str, token: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Check if current context has valid Gojo authorization.

    Args:
        operation: Operation requiring authorization
        token: Authorization token (if None, checks environment)

    Returns:
        (is_authorized, error_message)

    Example:
        >>> token = generate_auth_token('CLAUDE.md:edit', 'gojo')
        >>> authorized, error = require_gojo_authorization('CLAUDE.md:edit', token)
        >>> assert authorized
    """
    # Check explicit token parameter first
    if token:
        return verify_auth_token(token, operation)

    # Check AUTH_TOKEN environment variable
    env_token = os.environ.get('DZP_AUTH_TOKEN')
    if env_token:
        return verify_auth_token(env_token, operation)

    # No authorization found
    return False, "No authorization token provided"


# Self-test on module import
if __name__ == "__main__":
    # Test token generation and verification
    test_token = generate_auth_token('test:operation', 'test_agent', expires_in=60)
    valid, error = verify_auth_token(test_token, 'test:operation')

    if valid:
        print("[PASS] PATCH-SEC-001: Authorization system self-test passed")
    else:
        print(f"[FAIL] PATCH-SEC-001: Authorization system self-test failed: {error}")
        exit(1)

    # Test expiration
    expired_token = generate_auth_token('test:operation', 'test_agent', expires_in=-1)
    valid, error = verify_auth_token(expired_token, 'test:operation')

    if not valid and "expired" in error.lower():
        print("[PASS] PATCH-SEC-001: Token expiration working")
    else:
        print(f"[FAIL] PATCH-SEC-001: Token expiration test failed")
        exit(1)

    # Test signature tampering
    tampered_token = test_token[:-5] + "XXXXX"
    valid, error = verify_auth_token(tampered_token, 'test:operation')

    if not valid and "signature" in error.lower():
        print("[PASS] PATCH-SEC-001: Signature verification working")
    else:
        print(f"[FAIL] PATCH-SEC-001: Signature tampering test failed")
        exit(1)

    print("\n[PASS] All PATCH-SEC-001 tests passed")
