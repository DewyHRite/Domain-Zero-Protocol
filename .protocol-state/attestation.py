#!/usr/bin/env python3
"""
Domain Zero Protocol - Local Write Attestation (ISS-083)
Version: 1.0.0

Purpose
-------
`scripts/validate-protocol.py --check` schema-validates DZP state files and
compares each against a SHA-256 baseline from the previous run. Sanctioned
writers (ProjectStateManager, session_monitor.py, create-snapshot.py)
LEGITIMATELY rewrite these files as part of normal operation. Every such
authorized write previously showed up as a checksum mismatch -> a "drift
alert" -> alert fatigue -> operators learning to commit through tamper
alerts as routine, which is the exact channel a genuine out-of-band tamper
would use to pass unremarked.

This module lets a sanctioned writer stamp a signed attestation for a file
it just wrote (`record_write`), and lets a checker (validate-protocol.py)
verify that a file's CURRENT content is backed by a valid, non-replayed
attestation (`verify_current_content`) before deciding whether a checksum
mismatch is genuine drift or an authorized change.

Design
------
- Side-channel ledger (`.protocol-state/.attestation.json`, gitignored) maps
  file_key -> {writer, seq, content_sha256, ts, hmac}. A side-channel is
  preferred over embedding the stamp into each JSON state file: it avoids
  mutating every state schema, and avoids the "hash includes its own stamp"
  self-reference problem.
- Local HMAC-SHA256 key (`.protocol-state/.attestation.key`, gitignored, 32
  random bytes, generated on first use, owner-only permissions where the
  platform supports it -- POSIX `chmod 0600` plus, on Windows (the primary
  platform for this control, where chmod bits are a documented no-op), an
  owner-only NTFS ACL via `icacls` -- see `_harden_windows_acl()` below).
  This provides LOCAL integrity (detect edits made by processes that don't
  hold the key) -- it is NOT cross-machine non-repudiation and does NOT
  distinguish between DZP components running under the same local user
  account.
- Per-file monotonic `seq`, incremented on every sanctioned write. A stamp
  whose seq does not exceed the last-accepted seq for that file is treated
  as a replay and is rejected (the caller falls back to raising a drift
  alert). The anchor for "last-accepted seq" lives in the checker's own
  baseline store (validation-state.json), not in this ledger, so an
  attacker who replays an old (file + ledger-entry) pair together still
  cannot roll back the accepted seq.

  Composition note: restoring an OLDER `validation-state.json` backup can
  only ever make drift-suppression MORE LENIENT, never forge an
  attestation. Rolling back the checker's remembered `attested_seq` just
  re-opens the door to re-accepting an already-issued (still validly
  signed, content-matching) attestation a second time -- it can never
  manufacture a match for content nobody holding the key ever actually
  wrote, because `verify_current_content()` independently re-checks the
  ledger's `content_sha256` against the file's real current bytes and
  re-verifies the HMAC under the local key on every call, regardless of
  what the checker's own baseline says.

Fail-soft contract
-------------------
Every public function in this module is fail-soft: on any error (missing
key, unreadable/corrupt ledger, permission failure, disk error) it returns a
safe "attestation unavailable" result rather than raising. Callers MUST NOT
depend on this module to enforce anything -- it only ever *suppresses* an
otherwise-identical drift alert when a valid attestation is present. Absence
of the key/ledger reproduces the exact pre-ISS-083 behavior (always alert on
checksum mismatch), so environments without this infrastructure degrade
gracefully rather than crash or silently stop checking.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

LEDGER_FILENAME = ".attestation.json"
KEY_FILENAME = ".attestation.key"
LOCK_FILENAME = ".attestation.lock"
KEY_SIZE_BYTES = 32
SCHEMA_VERSION = "1.0.0"

# CodeRabbit PR#108: cross-process lock timing for the key-gen + ledger
# read-modify-write critical sections below. Short and best-effort by
# design -- see `_cross_process_lock()` docstring for the fail-soft
# rationale (a lock that can never be acquired must never block a
# sanctioned writer from completing its real state write).
_LOCK_TIMEOUT_SECONDS = 5.0
_LOCK_RETRY_DELAY_SECONDS = 0.05


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _key_path(state_dir: Path) -> Path:
    return Path(state_dir) / KEY_FILENAME


def _ledger_path(state_dir: Path) -> Path:
    return Path(state_dir) / LEDGER_FILENAME


def ledger_exists(state_dir: Path) -> bool:
    """True if the attestation ledger has been initialized for *state_dir*."""
    try:
        return _ledger_path(state_dir).exists()
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

def _harden_windows_acl(path: Path) -> None:
    """Best-effort Windows ACL hardening for the just-created attestation key.

    P3 (Megumi, post-Tier-3-approval residual): POSIX-style 0o600 bits (set
    via os.chmod in get_or_create_key()) have NO effect on Windows NTFS
    ACLs -- the key file otherwise inherits the parent directory's ACL, so
    another local account on a shared machine could read it and forge
    attestation entries. Windows is the primary platform for this control,
    so this matters.

    This is a deliberate MIRROR (with attribution) of
    `.protocol-state/brain/cortex/crypto.py::_harden_windows_acl()`
    (added under SEC-CORTEX-ENC-010 / C2-2 for the Cortex salt sidecar),
    not an import of it: that function lives inside the `cortex` package,
    which uses relative imports (`from .errors import ...`) and pulls in
    the wider Cortex package-import surface (its `__init__.py` + sibling
    modules) just to reach one small, dependency-free stdlib helper.
    `attestation.py` is intentionally standalone (imported by
    project_state_manager.py, session_monitor.py, create-snapshot.py, and
    scripts/validate-protocol.py, several of which are NOT part of the
    Cortex/brain subsystem), so a duplicated, self-contained copy is
    preferable to a cross-package import here. Keep both copies in sync if
    either is revised.

    Uses the built-in ``icacls`` CLI via subprocess (no new dependency,
    same approach as crypto.py) rather than pywin32, since callers of this
    module must not acquire a hard pywin32 dependency just for key
    hardening.

    Fail-soft by design: never raises and never blocks key generation. On
    any failure (icacls missing, non-NTFS volume, permission denied,
    inability to resolve the current user, etc.) prints a single stderr
    warning and continues -- the key file still has the 0o600-style bits
    set by the caller. No-op on non-Windows platforms.
    """
    if sys.platform != "win32":
        return
    current_user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if not current_user:
        try:
            import getpass
            current_user = getpass.getuser()
        except Exception:
            current_user = ""
    if not current_user:
        print(
            f"WARNING: could not determine current user to harden Windows ACL on {path}; "
            "skipping ACL hardening (fail-soft, ISS-083 P3). The attestation key relies on "
            "0o600-style bits only, which NTFS does not enforce.",
            file=sys.stderr,
        )
        return
    userdomain = os.environ.get("USERDOMAIN", "").strip()
    principal = f"{userdomain}\\{current_user}" if userdomain else current_user
    # Fully-qualified icacls path so a writable dir earlier in PATH can't
    # shadow the system binary (mirrors crypto.py's hardening, ruff S607).
    icacls_exe = os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"), "System32", "icacls.exe"
    )
    try:
        result = subprocess.run(
            [icacls_exe, str(path), "/inheritance:r", "/grant:r", f"{principal}:F"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(
                f"WARNING: failed to harden Windows ACL on {path} "
                f"(icacls exit {result.returncode}): {result.stderr.strip()}. "
                "Continuing without ACL hardening (fail-soft, ISS-083 P3) -- the "
                "attestation key relies on 0o600-style bits only, which NTFS does not enforce.",
                file=sys.stderr,
            )
    except Exception as exc:
        print(
            f"WARNING: failed to harden Windows ACL on {path}: {exc}. "
            "Continuing without ACL hardening (fail-soft, ISS-083 P3) -- the "
            "attestation key relies on 0o600-style bits only, which NTFS does not enforce.",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Cross-process locking (CodeRabbit PR#108)
# ---------------------------------------------------------------------------
#
# Both the key-gen critical section (`get_or_create_key`) and the ledger
# read-modify-write critical section (`record_write`) were previously
# unprotected against concurrent DZP writers (e.g. two `/session update`
# invocations, or a hook + a manual script, racing). For key-gen this could
# leave two processes momentarily holding two DIFFERENT in-memory keys
# before `os.replace()` settles on one; for the ledger, two concurrent
# `record_write()` calls for two DIFFERENT `file_key`s each load the WHOLE
# ledger, mutate only their own entry, and write back the WHOLE ledger --
# so a naive interleaving can silently lose one of the two updates (the
# second writer's save clobbers the first writer's added entry).
#
# `_cross_process_lock()` is a small, dependency-free, standalone lock
# (msvcrt on win32 -- the primary platform for this control -- fcntl
# elsewhere) local to this module. It is deliberately NOT borrowed from
# `ProjectStateManager._file_lock()` (project_state_manager.py): that class
# already imports `record_write` FROM this module (see its module
# docstring / callers), so importing `ProjectStateManager` back into
# `attestation.py` would create an import cycle. `ProjectStateManager`'s
# lock is also a bound *method* requiring a fully constructed instance
# (protocol_root, namespaced lock files, etc.), not a standalone function
# attestation.py's simpler procedural style can reuse cleanly.


@contextmanager
def _cross_process_lock(state_dir: Path) -> Iterator[bool]:
    """Best-effort cross-process exclusive lock guarding attestation state.

    Yields True if the lock was actually acquired, False if it was not
    (lock file could not be opened/created, or another holder did not
    release it within `_LOCK_TIMEOUT_SECONDS`). The caller's `with` block
    always runs either way -- this is advisory, best-effort serialization,
    not a hard mutex: per the module's fail-soft contract, attestation must
    NEVER block or fail a sanctioned writer's real state write just because
    a lock could not be taken. On a platform/filesystem where locking is
    unavailable, the pre-existing (unlocked) behavior is reproduced exactly,
    which is only ever a benign, spurious drift-alert risk under a genuine
    race -- never data corruption of the caller's actual state file (that
    file's own write path, e.g. ProjectStateManager, has its own locking).

    Any exception raised INSIDE the `with` block propagates normally (only
    lock acquisition itself is wrapped in fail-soft handling) so existing
    `except OSError` handling in `get_or_create_key()`/`record_write()`
    is unaffected.
    """
    state_dir = Path(state_dir)
    lock_path = state_dir / LOCK_FILENAME
    handle = None
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        handle = open(lock_path, "a+b")
    except OSError:
        handle = None

    locked = False
    if handle is not None:
        deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                break
            except OSError:
                if time.monotonic() >= deadline:
                    break
                time.sleep(_LOCK_RETRY_DELAY_SECONDS)

    try:
        yield locked
    finally:
        if handle is not None:
            if locked:
                try:
                    if sys.platform == "win32":
                        import msvcrt

                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
            try:
                handle.close()
            except OSError:
                pass


def _get_or_create_key_locked(state_dir: Path) -> Optional[bytes]:
    """Body of `get_or_create_key()`, assumed to run inside `_cross_process_lock()`."""
    path = _key_path(state_dir)
    if path.exists():
        data = path.read_bytes()
        if data:
            return data
        # Empty/corrupt key file -- fall through and regenerate.

    key = secrets.token_bytes(KEY_SIZE_BYTES)
    state_dir.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_name = tempfile.mkstemp(
        dir=str(state_dir), prefix=".attestation.key.", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(key)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass

    # Best-effort owner-only permissions (POSIX only; no-op/ignored on
    # platforms -- e.g. Windows -- where chmod bits don't apply the same
    # way). Never fail the key creation over a permissions warning.
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass

    # P3 (Megumi): chmod alone is a no-op on Windows NTFS ACLs. Harden
    # with an owner-only DACL via icacls there too (fail-soft; never
    # blocks key creation -- see _harden_windows_acl() docstring).
    try:
        _harden_windows_acl(path)
    except Exception:
        pass

    return key


def get_or_create_key(state_dir: Path) -> Optional[bytes]:
    """
    Load the local HMAC attestation key for *state_dir*, generating it on
    first use.

    Fail-soft: returns None (never raises) if the key cannot be read or
    created (read-only filesystem, permission errors, etc.). Callers MUST
    treat None as "attestation unavailable" and skip stamping/verifying.

    CodeRabbit PR#108: the read-check-generate-write sequence below runs
    under `_cross_process_lock()` so two concurrent first-use callers
    cannot race to generate (and briefly disagree on) the key -- see that
    function's docstring for why a local lock is used here rather than
    `ProjectStateManager`'s.
    """
    state_dir = Path(state_dir)
    try:
        with _cross_process_lock(state_dir):
            return _get_or_create_key_locked(state_dir)
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Ledger I/O
# ---------------------------------------------------------------------------

def _empty_ledger() -> Dict[str, Any]:
    return {"_schema_version": SCHEMA_VERSION, "files": {}}


def _load_ledger(state_dir: Path) -> Dict[str, Any]:
    path = _ledger_path(state_dir)
    if not path.exists():
        return _empty_ledger()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
            return _empty_ledger()
        return data
    except (OSError, json.JSONDecodeError, ValueError):
        return _empty_ledger()


def _save_ledger(state_dir: Path, ledger: Dict[str, Any]) -> bool:
    state_dir = Path(state_dir)
    path = _ledger_path(state_dir)
    tmp_name = None
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(
            dir=str(state_dir), prefix=".attestation.", suffix=".tmp"
        )
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
        tmp_name = None
        return True
    except OSError:
        return False
    finally:
        if tmp_name and os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# HMAC helpers
# ---------------------------------------------------------------------------

def _message(writer: str, seq: int, content_sha256: str, ts: str) -> bytes:
    return f"{writer}|{seq}|{content_sha256}|{ts}".encode("utf-8")


def _sign(key: bytes, writer: str, seq: int, content_sha256: str, ts: str) -> str:
    return hmac.new(key, _message(writer, seq, content_sha256, ts), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Public API: record (writer side)
# ---------------------------------------------------------------------------

def record_write(state_dir: Path, file_key: str, content: bytes, writer: str) -> bool:
    """
    Stamp an attestation for a sanctioned write that has ALREADY completed.

    Args:
        state_dir: The `.protocol-state` directory (ledger + key location).
        file_key: Basename used by validate-protocol.py's drift detection
            (e.g. "project-state.json", "session-state.json",
            "snapshot-manifest.json").
        content: The exact bytes now on disk for this file (the caller
            should read this back from disk post-write rather than
            re-serialize, so the recorded hash always matches reality).
        writer: Human-readable component identity (e.g.
            "ProjectStateManager", "SessionMonitor", "create-snapshot").
            This is NOT an authorization boundary -- any process holding the
            local key can claim any writer label; it is provenance metadata
            included in what gets signed, not a multi-party access control.

    Returns:
        True if the attestation was recorded, False on any failure
        (fail-soft -- never raises, never blocks the caller's real write,
        which has already succeeded by the time this is called).

    CodeRabbit PR#108: the whole key-gen-if-needed + ledger
    load-modify-save sequence below runs under ONE `_cross_process_lock()`
    acquisition (never two nested acquisitions -- that would deadlock a
    same-process caller under `msvcrt`/`fcntl`, which treat independent
    file handles to the same lock file independently). This closes a
    lost-update race: without the lock, two concurrent `record_write()`
    calls for two DIFFERENT `file_key`s could each load the same prior
    ledger, mutate only their own key, and save the whole ledger back --
    the second save would silently discard the first call's new entry.
    """
    try:
        state_dir = Path(state_dir)
        with _cross_process_lock(state_dir):
            key = _get_or_create_key_locked(state_dir)
            if key is None:
                return False

            ledger = _load_ledger(state_dir)
            files = ledger.setdefault("files", {})
            prev_entry = (
                files.get(file_key, {}) if isinstance(files.get(file_key), dict) else {}
            )
            try:
                prev_seq = int(prev_entry.get("seq", 0))
            except (TypeError, ValueError):
                prev_seq = 0

            seq = prev_seq + 1
            content_sha256 = hashlib.sha256(content).hexdigest()
            ts = datetime.now(timezone.utc).isoformat()
            digest = _sign(key, writer, seq, content_sha256, ts)

            files[file_key] = {
                "writer": writer,
                "seq": seq,
                "content_sha256": content_sha256,
                "ts": ts,
                "hmac": digest,
            }

            return _save_ledger(state_dir, ledger)
    except Exception:
        # Defense in depth: attestation must NEVER raise into a caller's
        # write path -- it is best-effort metadata, not a correctness gate.
        return False


# ---------------------------------------------------------------------------
# Public API: verify (checker side)
# ---------------------------------------------------------------------------

@dataclass
class AttestationCheck:
    """Result of consulting the attestation ledger for one file."""

    attested: bool
    reason: str
    seq: Optional[int] = None
    writer: Optional[str] = None


def verify_current_content(
    state_dir: Path, file_key: str, current_sha256: str
) -> AttestationCheck:
    """
    Check whether *current_sha256* (the file's ACTUAL current content hash)
    is backed by a valid attestation entry for *file_key*.

    This checks: a ledger entry exists, its recorded content_sha256 matches
    what's on disk RIGHT NOW (so a stale attestation for old content, or a
    ledger with no matching entry, never vouches for different content),
    and the HMAC over the entry is valid under the local key. It does NOT
    by itself enforce monotonicity across runs -- callers that need replay
    protection must additionally compare the returned `seq` against their
    own persisted "last accepted seq" for this file (see
    scripts/validate-protocol.py's detect_drift()).

    Fail-soft: any missing key/ledger/entry/parsing problem results in
    attested=False rather than raising, so the caller falls back to
    treating the change as an ordinary (unattested) drift candidate.
    """
    try:
        state_dir = Path(state_dir)
        key = get_or_create_key(state_dir)
        if key is None:
            return AttestationCheck(False, "attestation_key_unavailable")

        ledger = _load_ledger(state_dir)
        entry = ledger.get("files", {}).get(file_key)
        if not isinstance(entry, dict):
            return AttestationCheck(False, "no_attestation_entry")

        writer = entry.get("writer")
        seq_raw = entry.get("seq")
        content_sha256 = entry.get("content_sha256")
        ts = entry.get("ts")
        stored_hmac = entry.get("hmac")

        if not all([writer, content_sha256, ts, stored_hmac]) or seq_raw is None:
            return AttestationCheck(False, "malformed_attestation_entry")

        try:
            seq = int(seq_raw)
        except (TypeError, ValueError):
            return AttestationCheck(False, "malformed_attestation_entry")

        # The attestation must describe the file's CURRENT content. If the
        # ledger's recorded hash doesn't match what's on disk right now, the
        # ledger entry is stale (content changed again after the attested
        # write) or simply describes different content -- it cannot vouch
        # for this particular checksum mismatch.
        if content_sha256 != current_sha256:
            return AttestationCheck(False, "content_hash_mismatch")

        expected_hmac = _sign(key, writer, seq, content_sha256, ts)
        if not hmac.compare_digest(expected_hmac, stored_hmac):
            return AttestationCheck(False, "hmac_invalid")

        return AttestationCheck(True, "authorized_write", seq=seq, writer=writer)
    except Exception:
        return AttestationCheck(False, "attestation_verification_error")
