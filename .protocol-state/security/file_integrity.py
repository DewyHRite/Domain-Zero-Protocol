#!/usr/bin/env python3
"""
File integrity monitoring for Domain Zero Protocol CORE files.
Implements SHA-256 hash verification (PATCH-SEC-002).

Version: 8.8.0
Purpose: Detect tampering with protocol files
OWASP: A08:2021 - Software and Data Integrity Failures
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

INTEGRITY_FILE = '.protocol-state/security/file-integrity.json'

PROTECTED_FILES = [
    'protocol/CLAUDE.md',
    'protocol/yuuji.agent.md',
    'protocol/megumi.agent.md',
    'protocol/nobara.agent.md',
    'protocol/gojo.agent.md',
    'protocol/sukuna.agent.md',
    'protocol/todo.agent.md',
    'protocol/maki.agent.md',
    'protocol/panda.agent.md',
    'protocol/inumaki.agent.md',
    'protocol/SUKUNA-REPORT.md',
]


def compute_file_hash(filepath: str) -> str:
    """
    Compute SHA-256 hash of file.

    Args:
        filepath: Path to file to hash

    Returns:
        Hexadecimal SHA-256 hash string

    Raises:
        RuntimeError: If file cannot be read (TOCTOU protection)

    Example:
        >>> hash_val = compute_file_hash('protocol/CLAUDE.md')
        >>> len(hash_val)
        64
    """
    try:
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                sha256.update(block)
        return sha256.hexdigest()
    except (FileNotFoundError, PermissionError, IOError, OSError) as e:
        raise RuntimeError(f"Failed to compute hash for {filepath}: {e}") from e


def initialize_integrity_baseline() -> Dict[str, str]:
    """
    Compute and store hashes for all protected files.

    Returns:
        Dictionary mapping filepath to SHA-256 hash

    Example:
        >>> baseline = initialize_integrity_baseline()
        >>> 'protocol/CLAUDE.md' in baseline
        True
    """
    baseline = {}

    for filepath in PROTECTED_FILES:
        if Path(filepath).exists():
            baseline[filepath] = compute_file_hash(filepath)
        else:
            print(f"[WARN] Protected file not found: {filepath}")

    # Store baseline using atomic write (temp file + rename)
    Path(INTEGRITY_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then rename
    temp_file = INTEGRITY_FILE + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump({
            'version': '8.8.0',
            'timestamp': int(time.time()),
            'hashes': baseline
        }, f, indent=2)
        f.write('\n')  # Add trailing newline

    # Atomic replace (os.replace is atomic on both Unix and Windows)
    Path(temp_file).replace(INTEGRITY_FILE)

    print(f"[INFO] Integrity baseline created with {len(baseline)} files")
    return baseline


def verify_file_integrity() -> Dict[str, str]:
    """
    Verify integrity of all protected files.

    Returns:
        Dict of filepath -> error message (empty dict if all valid)

    Example:
        >>> violations = verify_file_integrity()
        >>> len(violations) == 0  # Should be True if no tampering
        True
    """
    # Load baseline
    if not Path(INTEGRITY_FILE).exists():
        # SECURITY: Fail loudly if baseline is missing (may indicate tampering)
        # Only allow auto-creation in development mode via environment variable
        if os.environ.get('DZP_ALLOW_BASELINE_AUTOCREATE') == '1':
            print("[WARN] No integrity baseline found, creating one (dev mode)...")
            initialize_integrity_baseline()
            return {}  # Newly created baseline, no violations
        else:
            raise RuntimeError(
                f"CRITICAL: Integrity baseline missing at {INTEGRITY_FILE}. "
                "This may indicate tampering. Manual investigation required. "
                "Set DZP_ALLOW_BASELINE_AUTOCREATE=1 only in development/testing."
            )

    try:
        with open(INTEGRITY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            baseline = data.get('hashes', {})
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"CRITICAL: Baseline file corrupted at {INTEGRITY_FILE}: {e}. "
            "This may indicate tampering."
        ) from e

    violations = {}

    for filepath, expected_hash in baseline.items():
        if not Path(filepath).exists():
            violations[filepath] = "FILE MISSING"
            continue

        current_hash = compute_file_hash(filepath)
        if current_hash != expected_hash:
            violations[filepath] = f"TAMPERED (expected: {expected_hash[:8]}..., got: {current_hash[:8]}...)"

    return violations


def update_integrity_baseline(filepath: str) -> None:
    """
    Update baseline hash for a specific file after authorized modification.

    Args:
        filepath: Path to file whose hash should be updated

    Raises:
        ValueError: If filepath is not in PROTECTED_FILES
        RuntimeError: If baseline is missing or corrupted
        FileNotFoundError: If file doesn't exist

    Example:
        >>> # After authorized edit to CLAUDE.md
        >>> update_integrity_baseline('protocol/CLAUDE.md')
    """
    # SECURITY: Validate filepath is in protected list
    if filepath not in PROTECTED_FILES:
        raise ValueError(
            f"Cannot update baseline for unprotected file: {filepath}. "
            f"File must be in PROTECTED_FILES list."
        )

    # SECURITY: Fail if baseline is missing (don't auto-create)
    if not Path(INTEGRITY_FILE).exists():
        raise RuntimeError(
            f"CRITICAL: Cannot update baseline - file missing at {INTEGRITY_FILE}"
        )

    if not Path(filepath).exists():
        raise FileNotFoundError(f"Cannot update hash for non-existent file: {filepath}")

    # Load existing baseline with corruption handling
    try:
        with open(INTEGRITY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Baseline file corrupted: {e}") from e

    # Compute new hash
    new_hash = compute_file_hash(filepath)
    old_hash = data['hashes'].get(filepath, 'none')
    data['hashes'][filepath] = new_hash
    data['timestamp'] = int(time.time())

    # Atomic write: write to temp file, then rename
    temp_file = INTEGRITY_FILE + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')  # Add trailing newline

    # Atomic replace
    Path(temp_file).replace(INTEGRITY_FILE)

    print(f"[INFO] Updated integrity hash for: {filepath}")
    print(f"[INFO] Old hash: {old_hash[:16]}... -> New hash: {new_hash[:16]}...")


# Self-test on module import
if __name__ == "__main__":
    import sys

    print("[INFO] Running PATCH-SEC-002 self-tests...")

    # Enable auto-creation for testing only
    os.environ['DZP_ALLOW_BASELINE_AUTOCREATE'] = '1'

    # Test 1: Initialize baseline
    try:
        baseline = initialize_integrity_baseline()
        if len(baseline) == 0:
            print("[FAIL] No files found to protect")
            sys.exit(1)
        print(f"[PASS] Baseline created with {len(baseline)} files")
    except Exception as e:
        print(f"[FAIL] Baseline creation failed: {e}")
        sys.exit(1)

    # Test 2: Verify integrity (should pass immediately after creation)
    try:
        violations = verify_file_integrity()
        if len(violations) > 0:
            print(f"[FAIL] Unexpected violations: {violations}")
            sys.exit(1)
        print("[PASS] Integrity verification passed")
    except Exception as e:
        print(f"[FAIL] Integrity verification failed: {e}")
        sys.exit(1)

    # Test 3: Test update functionality
    try:
        if Path('protocol/CLAUDE.md').exists():
            update_integrity_baseline('protocol/CLAUDE.md')
            print("[PASS] Baseline update working")
        else:
            print("[SKIP] CLAUDE.md not found, skipping update test")
    except Exception as e:
        print(f"[FAIL] Baseline update failed: {e}")
        sys.exit(1)

    # Test 4: Test security validation (unprotected file should fail)
    try:
        update_integrity_baseline('unprotected-file.txt')
        print("[FAIL] Unprotected file update should have been rejected")
        sys.exit(1)
    except ValueError:
        print("[PASS] Unprotected file update rejected correctly")

    print("\n[PASS] All PATCH-SEC-002 tests passed")
