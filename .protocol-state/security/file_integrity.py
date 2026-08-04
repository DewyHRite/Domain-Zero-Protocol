#!/usr/bin/env python3
"""
File integrity monitoring for Domain Zero Protocol CORE files.
Implements SHA-256 hash verification (PATCH-SEC-002).

Version: 9.11.0 (P1 remediation: CWD-independence, honest compensating-control
docs, consumer-shippable, wired into scripts/verify-installation.py)
Purpose: Detect tampering with protocol files
OWASP: A08:2021 - Software and Data Integrity Failures

SHIPPING NOTE (v9.11.0): this module is the ONLY file under
.protocol-state/security/ that ships to consumers (see
scripts/distro/publish-manifest.yaml include_state + forbid_tokens). Its
siblings (authorization.py, json_validator.py, path_validator.py) remain
dev-only and are NOT importable at runtime in a consumer install -- this
module therefore has ZERO imports from those siblings and must never grow one.

The shipped baseline data file (file-integrity.json) is intentionally NEVER
shipped -- see initialize_integrity_baseline()'s docstring for why a
dev-computed baseline would be wrong by construction post-publish-scrub, and
scripts/verify-installation.py's --init-integrity flag for how a consumer
establishes their own trusted baseline after installing.
"""

import hashlib
import json
import os
import platform
import time
from pathlib import Path
from typing import Dict, List, Optional

# Platform-specific file locking imports
try:
    import fcntl  # Unix/Linux/Mac
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import msvcrt  # Windows
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

# ---------------------------------------------------------------------------
# CWD-INDEPENDENCE FIX (P1 item 2): all paths below are anchored to the repo
# root, derived from this file's OWN location on disk, rather than being
# CWD-relative strings. Before this fix, INTEGRITY_FILE / AUDIT_LOG (and every
# PROTECTED_FILES entry, checked via bare Path(filepath)) silently resolved
# against whatever directory the CALLER happened to be running from -- e.g.
# invoking this module (or anything that imports it) from a subdirectory, or
# from a different cwd inside an editor/IDE terminal, made the entire control
# a silent no-op: verify_file_integrity() would report "baseline missing" (or
# worse, "0 violations" against an empty/wrong baseline) instead of actually
# checking the protected files.
#
# This file lives at <repo_root>/.protocol-state/security/file_integrity.py,
# a FIXED two levels below repo root, so repo root is derived structurally
# rather than guessed via cwd or environment variables.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]

INTEGRITY_FILE = str(REPO_ROOT / '.protocol-state' / 'security' / 'file-integrity.json')
AUDIT_LOG = str(REPO_ROOT / '.protocol-state' / 'security' / 'integrity-audit.log')

# Consumer-facing protected files. Every entry here MUST actually ship to
# consumers (see scripts/distro/publish-manifest.yaml) -- otherwise a clean
# install permanently reports "FILE MISSING" for a file that was never
# supposed to exist there (this is exactly what happened with the two
# gate-validate-*.py entries removed below; see DEV_ONLY_PROTECTED_FILES).
PROTECTED_FILES = [
    'CLAUDE.md',              # P1 item 3: root CLAUDE.md ships (publish-manifest.yaml
                               # include_files) and is precisely what the P1 finding
                               # named -- it was previously uncovered; only the
                               # protocol/CLAUDE.md compatibility copy was checked
                               # (a full mirror then; a pointer/stub since v9.11.0).
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
    'protocol.config.yaml',
    # SEC-ORCH-004: registry file added so SHA-256 is verified at startup
    '.protocol-state/script_dependencies.yaml',
    # SEC-COORD-005: gate delegate scripts added to integrity coverage
    # gate-validate-protocol.py and gate-validate-agents.py delegate to these;
    # without coverage here, a tampered validate-protocol.py bypasses the gate.
    'scripts/validate-protocol.py',
    'scripts/validate-custom-agents.py',
]

# P1 item 4: DEV-ONLY gate delegate scripts. These files exist in the
# canonical dev repo (used by ScriptCoordinator's gate wiring) but are NEVER
# part of scripts/distro/publish-manifest.yaml's include_state/include_scripts
# -- they do not ship. Checking them via the default PROTECTED_FILES list
# produced a permanent, unfixable "FILE MISSING" violation on every clean
# consumer install (the file was never supposed to exist there in the first
# place). Callers that specifically want dev-repo gate-script coverage must
# opt in via include_dev_only=True; consumer-facing callers (e.g.
# scripts/verify-installation.py) MUST NOT set it.
DEV_ONLY_PROTECTED_FILES = [
    # SEC-COORD-005-EXT: gate WRAPPER scripts, dev-repo only. These are the
    # actual executables the coordinator runs at gate time in the canonical
    # dev tree. Without this coverage, a tampered validate-protocol.py could
    # be bypassed by replacing the local gate-*.py wrapper with sys.exit(0).
    '.protocol-state/gate-validate-protocol.py',
    '.protocol-state/gate-validate-agents.py',
]


def _protected_files(include_dev_only: bool = False) -> List[str]:
    """Return the list of files this module protects.

    Args:
        include_dev_only: also include DEV_ONLY_PROTECTED_FILES (canonical dev
            repo only -- never set this True from a consumer-facing call site).
    """
    files = list(PROTECTED_FILES)
    if include_dev_only:
        files = files + DEV_ONLY_PROTECTED_FILES
    return files


def _repo_path(rel_or_abs: str) -> Path:
    """Resolve a PROTECTED_FILES-style relative path against REPO_ROOT.

    Absolute paths are returned as-is (defensive; PROTECTED_FILES entries are
    always relative in practice, but this keeps the helper safe if a caller
    ever passes one).
    """
    p = Path(rel_or_abs)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def compute_file_hash(filepath: str) -> str:
    """
    Compute SHA-256 hash of file.

    Args:
        filepath: Path to file to hash (absolute, or resolved by the caller)

    Returns:
        Hexadecimal SHA-256 hash string

    Raises:
        RuntimeError: If file cannot be read (TOCTOU protection)

    Example:
        >>> hash_val = compute_file_hash(str(REPO_ROOT / 'protocol' / 'CLAUDE.md'))
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


def initialize_integrity_baseline(include_dev_only: bool = False) -> Dict[str, str]:
    """
    Compute and store hashes for all protected files, establishing them as the
    trusted baseline.

    P1 item 5 (shipping note): this function must be run POST-INSTALL, not
    pre-publish. The publish pipeline (scripts/distro/dzp_publish_core.py)
    rewrites shipped files in place via identity_scrub() and content_scrub()
    (PII/identity replacement), so any hash computed in the DEV tree before
    publish would already be wrong for the files a consumer actually receives
    -- the baseline would be self-contradicting from the moment it shipped.
    For that reason file-integrity.json is intentionally excluded from
    publish-manifest.yaml (both by omission from include_state and by an
    explicit forbid_tokens entry) and is NEVER shipped; consumers generate
    their own baseline after installing via
    `python scripts/verify-installation.py --init-integrity`.

    Args:
        include_dev_only: also baseline DEV_ONLY_PROTECTED_FILES (canonical
            dev repo only).

    Returns:
        Dictionary mapping filepath to SHA-256 hash

    Example:
        >>> baseline = initialize_integrity_baseline()
        >>> 'protocol/CLAUDE.md' in baseline
        True
    """
    baseline = {}
    absent = []

    for filepath in _protected_files(include_dev_only):
        target = _repo_path(filepath)
        if target.exists():
            baseline[filepath] = compute_file_hash(str(target))
        else:
            absent.append(filepath)
            print(f"[WARN] Protected file not found: {filepath}")

    # SEC-FILEINTEG-PENDING-A (P1), manufacture path: REFUSE to write a baseline
    # that declares zero hashes. Previously, running --init-integrity from a
    # broken/empty tree (interrupted install, wrong directory, partially-restored
    # snapshot) legitimately produced {"hashes": {}} on disk -- a file that then
    # "verified clean" forever while checking nothing. The per-file [WARN] lines
    # above were the only signal, and a scripted install surfaces none of them.
    # Fail closed here so the invalid artifact is never created in the first
    # place, in addition to verify_file_integrity() refusing to consume one.
    if not baseline:
        raise RuntimeError(
            f"CRITICAL: refusing to create an EMPTY integrity baseline at "
            f"{INTEGRITY_FILE} -- none of the {len(_protected_files(include_dev_only))} "
            "protected files could be found on disk. This almost always means "
            "--init-integrity was run against a broken, incomplete, or wrong "
            "directory tree. An empty baseline verifies nothing while reporting "
            "success, so it is never written. Missing: "
            + ", ".join(absent[:10])
            + (" ..." if len(absent) > 10 else "")
        )

    # CodeRabbit PR #115 REAL-FIX #1 (SEC-FILEINTEG-UNDERCOVER-001): extend the
    # SEC-FILEINTEG-PENDING-A refusal above from "zero protected files found"
    # to "ANY protected file missing at baseline-initialization time". The
    # prior behavior here was warn-and-write: it wrote an under-covering
    # baseline to disk and returned success to the caller.
    # scripts/verify-installation.py --init-integrity then reported success
    # (exit 0) -- but every SUBSEQUENT verify_file_integrity() call raises the
    # "does not cover" RuntimeError from load_baseline_document() for the
    # missing entries, permanently. A success signal immediately followed by
    # permanent hard failures is exactly the defect class the empty-baseline
    # refusal above already closed for total absence; this closes it for
    # partial absence too. The caller (verify_file_integrity_gate() in
    # scripts/verify-installation.py) already wraps this call in a
    # try/except RuntimeError that prints [FAIL] and returns exit 1 -- no
    # caller-side change is required for this fix to take effect.
    if absent:
        raise RuntimeError(
            f"CRITICAL: refusing to create an UNDER-COVERING integrity "
            f"baseline at {INTEGRITY_FILE} -- {len(absent)} of "
            f"{len(_protected_files(include_dev_only))} protected files could "
            "not be found on disk. An under-covering baseline would report "
            "success (exit 0) at creation time, then FAIL CLOSED on every "
            "subsequent verification forever -- this almost always means "
            "--init-integrity was run against a broken, incomplete, or wrong "
            "directory tree. Repair the install (or correct "
            "PROTECTED_FILES/DEV_ONLY_PROTECTED_FILES, if a listed file "
            "legitimately does not ship here) before re-running "
            "--init-integrity. Missing: "
            + ", ".join(absent[:10])
            + (" ..." if len(absent) > 10 else "")
        )

    # Store baseline using atomic write (temp file + rename)
    Path(INTEGRITY_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then rename
    temp_file = INTEGRITY_FILE + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump({
            'version': '9.11.0',
            'timestamp': int(time.time()),
            'hashes': baseline
        }, f, indent=2)
        f.write('\n')  # Add trailing newline

    # Atomic replace (os.replace is atomic on both Unix and Windows)
    Path(temp_file).replace(INTEGRITY_FILE)

    print(f"[INFO] Integrity baseline created with {len(baseline)} files")
    return baseline


def load_baseline_document() -> Dict[str, object]:
    """Load, parse and STRUCTURALLY VALIDATE the whole baseline DOCUMENT.

    Single source of truth for "is this baseline usable at all", shared by
    load_baseline() (and through it verify_file_integrity() and
    scripts/verify-installation.py) AND by update_integrity_baseline(), which
    needs the non-hash metadata (`version`) it must preserve on rewrite.

    SEC-FILEINTEG-003 -- WHY THIS FUNCTION EXISTS AS A SEPARATE ENTRY POINT:

    load_baseline()'s docstring claimed to be the single source of truth for
    baseline usability. That was true for TWO of this module's THREE baseline
    readers. update_integrity_baseline() opened INTEGRITY_FILE itself, guarded
    only json.JSONDecodeError, and then subscripted data['hashes'] unguarded.
    Most bad shapes crashed there, so they failed CLOSED -- but `{"hashes": {}}`
    SUCCEEDED and wrote back a one-entry, UNDER-COVERING baseline: exactly the
    artifact initialize_integrity_baseline() had just been hardened to refuse
    to manufacture. It was rejected downstream by the coverage rule here, so
    the system still failed closed end to end; the defect was the inconsistency
    plus a single-source-of-truth claim that a future reviewer would rely on.

    Splitting document-level validation out (rather than having the update path
    re-read the file after calling load_baseline()) keeps ONE read and ONE set
    of guards. A pin in tests/test_file_integrity.py fails if a second raw
    json.load of the baseline reappears below this function.

    Returns:
        The validated baseline document. 'hashes' is always a non-empty dict
        covering at least every entry in PROTECTED_FILES.

    Raises:
        RuntimeError: if the baseline is missing, unparseable, or structurally
        invalid in ANY way.

    SEC-FILEINTEG-PENDING-A (P1) -- WHY THIS IS FAIL-CLOSED ON EVERY BRANCH:

    The prior implementation guarded only json.JSONDecodeError and then did
    `baseline = data.get('hashes', {})`. A baseline of `{}`, or
    `{"version": ..., "timestamp": ...}`, or `{"hashes": {}}` is perfectly
    valid JSON -- so nothing raised, `baseline` became `{}`, the comparison
    loop never executed, and the function returned an EMPTY violations dict.
    Empty violations is the caller's SUCCESS signal, so the shipped gate then
    printed:

        [OK] File integrity verified: 16 protected files checked, 0 violations

    having opened none of those 16 files. That is a false attestation in the
    release's headline integrity control, and it is reachable WITHOUT an
    attacker: an interrupted write, a full disk, a bad merge, a partially
    restored snapshot, or a hand-edit that drops the 'hashes' key all produce
    it.

    The governing rule, applied uniformly below: **a structurally invalid
    baseline must be indistinguishable from tampering, and must NEVER be
    indistinguishable from success.** This mirrors the fail-closed-on-empty
    precedent this same release already establishes correctly in
    scripts/distro/dzp_publish_core.py::_load_internal_identifiers(), where a
    silently-emptied denylist is treated exactly like a missing one.

    Note the deliberate asymmetry in the coverage check: a baseline covering
    MORE files than PROTECTED_FILES is fine (that is what
    initialize_integrity_baseline(include_dev_only=True) produces), but a
    baseline covering FEWER is not -- under-coverage is the same false
    attestation in partial form.
    """
    if not Path(INTEGRITY_FILE).exists():
        raise RuntimeError(
            f"CRITICAL: Integrity baseline missing at {INTEGRITY_FILE}. "
            "This may indicate tampering (the baseline was deleted), OR simply "
            "that no baseline has been established yet (e.g. immediately after "
            "a fresh install). There is no environment-variable bypass for this "
            "check. To establish the initial trusted baseline, run: "
            "python scripts/verify-installation.py --init-integrity"
        )

    try:
        with open(INTEGRITY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"CRITICAL: Baseline file corrupted at {INTEGRITY_FILE}: {e}. "
            "This may indicate tampering."
        ) from e
    except OSError as e:
        raise RuntimeError(
            f"CRITICAL: Baseline file at {INTEGRITY_FILE} could not be read: {e}. "
            "Refusing to report success on an unreadable baseline (fail-closed)."
        ) from e

    if not isinstance(data, dict):
        raise RuntimeError(
            f"CRITICAL: Baseline file corrupted at {INTEGRITY_FILE}: expected a "
            f"JSON object at the top level, got {type(data).__name__}. "
            "This may indicate tampering."
        )

    if 'hashes' not in data:
        raise RuntimeError(
            f"CRITICAL: Baseline file corrupted at {INTEGRITY_FILE}: no 'hashes' "
            "key. A baseline with no hashes section verifies NOTHING while "
            "reporting zero violations, so it is rejected rather than treated as "
            "a clean result. This may indicate tampering or an interrupted "
            "write. Re-establish it with: "
            "python scripts/verify-installation.py --init-integrity"
        )

    baseline = data['hashes']
    if not isinstance(baseline, dict):
        raise RuntimeError(
            f"CRITICAL: Baseline file corrupted at {INTEGRITY_FILE}: 'hashes' must "
            f"be a JSON object, got {type(baseline).__name__}. "
            "This may indicate tampering."
        )

    if not baseline:
        raise RuntimeError(
            f"CRITICAL: Baseline at {INTEGRITY_FILE} declares ZERO hashes. "
            "Refusing a no-op verification that would report success without "
            "checking a single file (fail-closed). This may indicate tampering, "
            "an interrupted write, or an --init-integrity run against a broken "
            "tree. Re-establish it with: "
            "python scripts/verify-installation.py --init-integrity"
        )

    uncovered = [f for f in PROTECTED_FILES if f not in baseline]
    if uncovered:
        raise RuntimeError(
            f"CRITICAL: Baseline at {INTEGRITY_FILE} does not cover "
            f"{len(uncovered)} of the {len(PROTECTED_FILES)} protected files, so "
            "those files would be silently reported as verified without ever "
            "being checked (fail-closed). Missing coverage for: "
            + ", ".join(uncovered)
            + ". Re-establish the baseline with: "
            "python scripts/verify-installation.py --init-integrity"
        )

    return data


def load_baseline() -> Dict[str, str]:
    """The validated filepath -> expected-SHA-256 mapping.

    Thin projection of load_baseline_document(); every structural guarantee and
    every fail-closed branch is documented there. Kept as a separate name
    because it is the published entry point used by verify_file_integrity() and
    by scripts/verify-installation.py's verified-count attestation.

    Returns:
        Dict of protected filepath -> expected SHA-256 hash. Never empty.

    Raises:
        RuntimeError: if the baseline is missing, unparseable, or structurally
        invalid in ANY way (delegated to load_baseline_document()).
    """
    return load_baseline_document()['hashes']


def verify_file_integrity() -> Dict[str, str]:
    """
    Verify integrity of all protected files against the stored baseline.

    Returns:
        Dict of filepath -> error message (empty dict if all valid)

    Raises:
        RuntimeError: If the baseline is missing, unparseable, or structurally
        invalid -- ALL delegated to load_baseline(), which is fail-closed on
        every branch (see SEC-FILEINTEG-PENDING-A in its docstring). An empty
        return value from this function therefore means "a valid, complete
        baseline was compared against every protected file and nothing
        differed", never "there was nothing to compare".

        SECURITY (SEC-COORD-005-EXT / P3, corrected in v9.11.0): there is NO
        environment-variable bypass here. The prior DZP_ALLOW_BASELINE_AUTOCREATE
        flag has been REMOVED entirely -- it silently blessed whatever bytes
        were on disk as the trusted baseline whenever the baseline file was
        absent, on the strength of a compensating-control claim
        ("ScriptCoordinator's _verify_registry_integrity() covers the gate
        path") that was FALSE: no such method exists anywhere in
        script_coordinator.py (confirmed by source scan -- the module contains
        no "integrity"/"sha256"/"hashlib" token). The accepted P3 risk was
        therefore unmitigated the entire time this comment claimed otherwise.
        A tampered file on a fresh/reset install would have been silently
        enrolled as "known good" by that bypass, and worse, an attacker who
        deletes file-integrity.json specifically (to force re-trust of files
        they just tampered with) would have had the env var do exactly what
        they wanted if it was ever set anywhere the process could see it (CI,
        shared shell profile, container image, etc.).

        The single intentional, auditable path for establishing initial trust
        is now `python scripts/verify-installation.py --init-integrity` -- a
        human-invoked, explicitly-named action with loud console output (see
        that script). This still carries residual trust-on-first-use risk
        inherent to any local integrity baseline (whoever runs
        --init-integrity first defines "known good"), but that risk is now
        scoped to one deliberate call site instead of an ambient environment
        variable that silently blinds every future verification run,
        including ones after a real tampering event.

    Example:
        >>> violations = verify_file_integrity()
        >>> len(violations) == 0  # Should be True if no tampering
        True
    """
    # Missing / unparseable / structurally-invalid baselines ALL raise here.
    # Deliberately one call: any future validation rule added to load_baseline()
    # is automatically enforced on this path too, so the two can never drift.
    baseline = load_baseline()

    violations = {}

    for filepath, expected_hash in baseline.items():
        target = _repo_path(filepath)
        if not target.exists():
            violations[filepath] = "FILE MISSING"
            continue

        current_hash = compute_file_hash(str(target))
        if current_hash != expected_hash:
            violations[filepath] = f"TAMPERED (expected: {expected_hash[:8]}..., got: {current_hash[:8]}...)"

    return violations


def _is_authorized_for_baseline_update(authorized_by: Optional[str]) -> bool:
    """
    Verify authorization for baseline updates.

    SEC-TRANSFER-9.11.0-001 (P1, CWE-863): this previously accepted ANY
    caller-asserted string ('GOJO', 'SYSTEM', 'USER' -- case-insensitively)
    with ZERO corroborating verification. A bare Python keyword argument
    `authorized_by="GOJO"` was believed unconditionally -- this increment's
    OWN implementation tooling exercised exactly that gap (see
    `.protocol-state/security/integrity-audit.log`, actor "GOJO",
    2026-07-29, with no DZP_AGENT set at all).

    Fixed to cross-check a corroborating signal per claim:

    - **GOJO**: cross-checked against `os.environ.get('DZP_AGENT', '').lower()
      == 'gojo'` -- the EXACT same signal `session_monitor.py`'s own
      `_check_gojo_invocation()` already trusts for the identical "is this
      actually Gojo" question elsewhere in this codebase. Not new trust
      infrastructure, just consistency with what is already relied upon.
    - **SYSTEM**: no comparable non-forgeable signal exists anywhere in this
      codebase today (no CI/service-identity token, no signed process
      attestation). Per the finding's explicit instruction ("require a
      comparable non-forgeable signal if one exists; else reject"), SYSTEM
      claims are now ALWAYS REJECTED rather than trusted on a bare string.
    - **USER**: the interactive-operator path. Permitted ONLY when
      `DZP_AGENT` is NOT set at all -- i.e., no agent identity is being
      asserted over this call. If `DZP_AGENT` is set to anything (including
      'gojo'), the caller is running inside an agent-driven invocation and a
      bare 'USER' claim from inside it is not credible.

    Honest limitation, stated plainly: `DZP_AGENT` is a plain environment
    variable, not cryptographic identity -- any local process can set it.
    This closes "any string is believed unconditionally" down to "the same
    already-trusted env-var signal every other Gojo-permission check in this
    codebase relies on," consistent with DZP's assessed threat model (a
    single local operator, not a multi-tenant trust boundary). It is a real
    improvement over zero verification, not a claim of unforgeable identity.

    Args:
        authorized_by: Identity of the entity requesting the update

    Returns:
        True if authorized, False otherwise
    """
    if authorized_by is None:
        return False

    claim = authorized_by.upper()
    dzp_agent = os.environ.get('DZP_AGENT', '').lower()

    if claim == 'GOJO':
        return dzp_agent == 'gojo'
    if claim == 'SYSTEM':
        # No comparable non-forgeable signal exists yet -- reject rather than
        # trust a bare string (SEC-TRANSFER-9.11.0-001).
        return False
    if claim == 'USER':
        # Interactive-operator path: credible only when no agent identity is
        # asserted over this call at all.
        return dzp_agent == ''

    return False


def _append_audit_entry(filepath: str, old_hash: str, new_hash: str, actor: str) -> None:
    """
    Append tamper-evident audit entry for baseline updates.

    Args:
        filepath: File that was updated
        old_hash: Previous hash value
        new_hash: New hash value
        actor: Entity that performed the update
    """
    entry = {
        'timestamp': int(time.time()),
        'actor': actor,
        'filepath': filepath,
        'old_hash': old_hash,
        'new_hash': new_hash
    }

    # Ensure audit log directory exists
    Path(AUDIT_LOG).parent.mkdir(parents=True, exist_ok=True)

    # Append to audit log with fsync for durability
    with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
        f.flush()
        os.fsync(f.fileno())  # Ensure written to disk


def update_integrity_baseline(
    filepath: str,
    authorized_by: Optional[str] = None,
    include_dev_only: bool = False,
) -> None:
    """
    Update baseline hash for a specific file after authorized modification.

    Args:
        filepath: Path to file whose hash should be updated
        authorized_by: Identity of authorizing entity (USER, GOJO, or SYSTEM)
        include_dev_only: allow updating a DEV_ONLY_PROTECTED_FILES entry
            (canonical dev repo only).

    Raises:
        ValueError: If filepath is not in the protected file list
        PermissionError: If not authorized for baseline updates
        RuntimeError: If baseline is missing or corrupted
        FileNotFoundError: If file doesn't exist

    Example:
        >>> # After authorized edit to CLAUDE.md
        >>> update_integrity_baseline('CLAUDE.md', authorized_by='USER')
    """
    # SECURITY: Verify authorization first
    if not _is_authorized_for_baseline_update(authorized_by):
        raise PermissionError(
            f"Unauthorized baseline update attempt by {authorized_by or 'unknown'}. "
            "Only USER, GOJO, or SYSTEM can update the integrity baseline."
        )

    # SECURITY: Validate filepath is in the protected list
    if filepath not in _protected_files(include_dev_only):
        raise ValueError(
            f"Cannot update baseline for unprotected file: {filepath}. "
            f"File must be in PROTECTED_FILES (or DEV_ONLY_PROTECTED_FILES with "
            f"include_dev_only=True)."
        )

    # SECURITY: Fail if baseline is missing (don't auto-create)
    if not Path(INTEGRITY_FILE).exists():
        raise RuntimeError(
            f"CRITICAL: Cannot update baseline - file missing at {INTEGRITY_FILE}"
        )

    target = _repo_path(filepath)
    if not target.exists():
        raise FileNotFoundError(f"Cannot update hash for non-existent file: {filepath}")

    # Use a dedicated lockfile to protect the entire critical section
    lockfile = INTEGRITY_FILE + '.lock'

    with open(lockfile, 'w', encoding='utf-8') as lock_f:
        # Acquire exclusive lock on dedicated lockfile (fail-fast if unavailable)
        if HAS_FCNTL:
            # Unix/Linux/Mac: acquire exclusive lock
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        elif HAS_MSVCRT:
            # Windows: acquire exclusive lock
            msvcrt.locking(lock_f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # SECURITY: File locking is required for integrity guarantee
            raise RuntimeError(
                "File locking not available on this platform. "
                "Cannot safely update integrity baseline."
            )

        # SEC-FILEINTEG-003: read through the SHARED validated reader rather
        # than re-opening the file with a JSONDecodeError-only guard. Every
        # structurally-invalid shape is now rejected here identically to the
        # verify path -- including {"hashes": {}}, which previously succeeded
        # and let this function write back an under-covering baseline.
        data = load_baseline_document()

        # Compute new hash
        new_hash = compute_file_hash(str(target))
        old_hash = data['hashes'].get(filepath, 'none')
        data['hashes'][filepath] = new_hash
        data['timestamp'] = int(time.time())

        # Atomic write: write to temp file, then rename (all within lock)
        temp_file = INTEGRITY_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as tmp:
            json.dump(data, tmp, indent=2)
            tmp.write('\n')  # Add trailing newline

        # Atomic replace while still holding lock (prevents race window)
        Path(temp_file).replace(INTEGRITY_FILE)

        # AUDIT: Log baseline update for forensics and compliance
        _append_audit_entry(filepath, old_hash, new_hash, authorized_by or 'unknown')

        # Lock released automatically when context exits

    print(f"[INFO] Updated integrity hash for: {filepath}")
    print(f"[INFO] Old hash: {old_hash[:16]}... -> New hash: {new_hash[:16]}...")


# Self-test on module import
if __name__ == "__main__":
    import sys

    print("[INFO] Running PATCH-SEC-002 self-tests...")

    # SECURITY: Use test-specific baseline (still REPO_ROOT-anchored) to avoid
    # modifying the production baseline.
    original_integrity_file = INTEGRITY_FILE
    original_audit_log = AUDIT_LOG
    INTEGRITY_FILE = str(REPO_ROOT / '.protocol-state' / 'security' / 'file-integrity.test.json')
    AUDIT_LOG = str(REPO_ROOT / '.protocol-state' / 'security' / 'integrity-audit.test.log')

    try:
        # Test 1: Initialize baseline (no bypass needed -- baseline genuinely
        # doesn't exist yet at the test-specific path).
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

        # Test 3: Test authorized update functionality
        # SEC-TRANSFER-9.11.0-006: authorized_by='SYSTEM' is now ALWAYS
        # rejected (SEC-TRANSFER-9.11.0-001 fix -- no comparable non-forgeable
        # signal exists for SYSTEM claims). Use a GOJO claim with the
        # corroborating DZP_AGENT=gojo environment variable it now requires,
        # restoring the environment immediately after (in a finally) so Test
        # 4/5 below still run under the default no-agent-asserted state they
        # themselves expect.
        _prior_dzp_agent = os.environ.get('DZP_AGENT')
        try:
            os.environ['DZP_AGENT'] = 'gojo'
            if (REPO_ROOT / 'CLAUDE.md').exists():
                update_integrity_baseline('CLAUDE.md', authorized_by='GOJO')
                print("[PASS] Baseline update working")
            else:
                print("[SKIP] CLAUDE.md not found, skipping update test")
        except Exception as e:
            print(f"[FAIL] Baseline update failed: {e}")
            sys.exit(1)
        finally:
            if _prior_dzp_agent is None:
                os.environ.pop('DZP_AGENT', None)
            else:
                os.environ['DZP_AGENT'] = _prior_dzp_agent

        # Test 4: Test unauthorized update (should fail)
        try:
            update_integrity_baseline('CLAUDE.md', authorized_by=None)
            print("[FAIL] Unauthorized update should have been rejected")
            sys.exit(1)
        except PermissionError:
            print("[PASS] Unauthorized update rejected correctly")

        # Test 5: Test security validation (unprotected file should fail)
        # SEC-TRANSFER-9.11.0-006: same fix as Test 3 -- an unauthorized
        # SYSTEM claim would now raise PermissionError (authorization) before
        # this call ever reaches the unprotected-file ValueError it exists to
        # prove. Authorize the call the same way (GOJO + DZP_AGENT=gojo) so it
        # actually exercises the intended validation path; any PermissionError
        # here would propagate uncaught (not silently pass) as a loud signal
        # the authorization fix regressed.
        _prior_dzp_agent = os.environ.get('DZP_AGENT')
        try:
            os.environ['DZP_AGENT'] = 'gojo'
            update_integrity_baseline('unprotected-file.txt', authorized_by='GOJO')
            print("[FAIL] Unprotected file update should have been rejected")
            sys.exit(1)
        except ValueError:
            print("[PASS] Unprotected file update rejected correctly")
        finally:
            if _prior_dzp_agent is None:
                os.environ.pop('DZP_AGENT', None)
            else:
                os.environ['DZP_AGENT'] = _prior_dzp_agent

        # Test 6: Missing baseline raises with no bypass available
        try:
            missing_path = str(REPO_ROOT / '.protocol-state' / 'security' / 'file-integrity.doesnotexist.json')
            INTEGRITY_FILE = missing_path
            try:
                verify_file_integrity()
                print("[FAIL] Missing baseline should have raised RuntimeError")
                sys.exit(1)
            except RuntimeError:
                print("[PASS] Missing baseline raises RuntimeError with no bypass")
        finally:
            INTEGRITY_FILE = str(REPO_ROOT / '.protocol-state' / 'security' / 'file-integrity.test.json')

        print("\n[PASS] All PATCH-SEC-002 tests passed")

    finally:
        # Clean up test files
        test_files = [INTEGRITY_FILE, AUDIT_LOG, INTEGRITY_FILE + '.lock']
        for test_file in test_files:
            if Path(test_file).exists():
                Path(test_file).unlink()

        # Restore original paths
        INTEGRITY_FILE = original_integrity_file
        AUDIT_LOG = original_audit_log
