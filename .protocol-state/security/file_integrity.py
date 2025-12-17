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

    Example:
        >>> hash_val = compute_file_hash('protocol/CLAUDE.md')
        >>> len(hash_val)
        64
    """
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for block in iter(lambda: f.read(4096), b''):
            sha256.update(block)
    return sha256.hexdigest()


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

    # Store baseline
    Path(INTEGRITY_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(INTEGRITY_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'version': '8.8.0',
            'timestamp': int(time.time()),
            'hashes': baseline
        }, f, indent=2)

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
        print("[WARN] No integrity baseline found, creating one...")
        initialize_integrity_baseline()
        return {}  # Newly created baseline, no violations

    with open(INTEGRITY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        baseline = data.get('hashes', {})

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

    Example:
        >>> # After authorized edit to CLAUDE.md
        >>> update_integrity_baseline('protocol/CLAUDE.md')
    """
    if not Path(INTEGRITY_FILE).exists():
        print("[WARN] No baseline exists, creating new baseline...")
        initialize_integrity_baseline()
        return

    if not Path(filepath).exists():
        print(f"[ERROR] Cannot update hash for non-existent file: {filepath}")
        return

    with open(INTEGRITY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Compute new hash
    new_hash = compute_file_hash(filepath)
    data['hashes'][filepath] = new_hash
    data['timestamp'] = int(time.time())

    with open(INTEGRITY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"[INFO] Updated integrity hash for: {filepath}")


# Self-test on module import
if __name__ == "__main__":
    import sys

    print("[INFO] Running PATCH-SEC-002 self-tests...")

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

    print("\n[PASS] All PATCH-SEC-002 tests passed")
