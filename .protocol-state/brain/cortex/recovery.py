"""Recovery-artifact metadata + key-generation record (PLAN-CORTEX-RECOVERY-001 §18.5;
DESIGN-001). The key_generation changes ONLY when key material changes (allocate),
never on export/read. Allocation is lock-guarded and fail-closed."""
from __future__ import annotations
import hashlib, json, os, sys, tempfile, time, warnings
from dataclasses import dataclass, asdict
from pathlib import Path

_GEN_FILE = "key-generation.json"
_GEN_LOCK = "key-generation.lock"
_HIGH_WATER_FILE = "content-refs.highwater"
_LOCK_TTL = 900


@dataclass
class RecoveryManifest:
    artifact_version: int
    created: str
    key_generation: str
    schema_version: int
    encryption_state: str
    install_id: str
    db_identity: str
    integrity_digest: str
    provenance: str
    # CODE-001 (CWE-391, v9.9.2): optional per-table diagnostics (JSON string,
    # e.g. {"cortex_memories": {"present": true, "rows": 2}, ...}). Appended
    # LAST with a default so every pre-existing manifest producer/consumer
    # (encryption backups, key-escrow exports, etc.) is unaffected -- old
    # on-disk manifests lacking this key still reconstruct via read_manifest()
    # (RecoveryManifest(**json)) because the field defaults to "".
    table_meta: str = ""


def _manifest_path(t: Path) -> Path:
    t = Path(t); return t.with_suffix(t.suffix + ".manifest.json")


def _atomic_write(path: Path, text: str) -> None:
    # NOTE: must NOT be used for key-equivalent content; use write_owner_only for that.
    fd, tmp = tempfile.mkstemp(dir=str(Path(path).parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _reap_stale_gen_lock(lock: Path, ttl_seconds: int) -> None:
    """Remove a stale key-generation.lock ONLY if it is unchanged between observe and unlink.

    Re-stats immediately before unlink to guard against a concurrent acquirer refreshing
    the lock between the mtime check and the deletion (SEC-R1A-001 TOCTOU fix).
    """
    try:
        st = lock.stat()
    except FileNotFoundError:
        return
    if (time.time() - st.st_mtime) < ttl_seconds:
        return  # fresh — leave it
    observed = st.st_mtime
    try:
        if lock.stat().st_mtime != observed:  # re-stat immediately before unlink
            return  # replaced/refreshed by a concurrent acquirer — do NOT delete
        lock.unlink()
    except OSError:
        return


def write_manifest(target: Path, m: RecoveryManifest) -> Path:
    mp = _manifest_path(target)
    _atomic_write(mp, json.dumps(asdict(m), indent=2) + "\n")
    return mp


def read_manifest(target: Path) -> "RecoveryManifest | None":
    mp = _manifest_path(target)
    if not mp.exists():
        return None
    return RecoveryManifest(**json.loads(mp.read_text(encoding="utf-8")))


def sha256_digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def current_install_id(data_dir) -> str:
    return os.environ.get("DZP_CORTEX_INSTALL_ID") or Path(data_dir).name


def current_key_generation(data_dir) -> "str | None":
    p = Path(data_dir) / _GEN_FILE
    if not p.exists():
        return None
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
        return rec["generation"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"corrupt key-generation record at {p}: {exc}") from exc


def allocate_key_generation(data_dir, install_id) -> str:
    """Allocate a NEW generation (key material changed). Lock-guarded + fail-closed."""
    data_dir = Path(data_dir)
    lock = data_dir / _GEN_LOCK
    data_dir.mkdir(parents=True, exist_ok=True)
    # RISK-RECOVERY-R1-001 / SEC-R1A-001: reap a STALE lock left by a crash/kill (or an
    # OneDrive placeholder that blocked the prior unlink) so a single interrupted allocation
    # can NEVER permanently brick `brain key export`. Uses TOCTOU-safe helper that re-stats
    # immediately before unlink to avoid racing a concurrent fresh acquirer.
    _reap_stale_gen_lock(lock, _LOCK_TTL)
    # crude cross-process lock via O_EXCL (retry briefly); mode 0o600 = owner-read/write only
    for _ in range(50):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd); break
        except FileExistsError:
            time.sleep(0.05)
    else:
        raise RuntimeError(f"could not acquire key-generation lock at {lock}; "
                           f"if it is stale, delete it or run: brain recover --clear-key-gen-lock")
    try:
        p = data_dir / _GEN_FILE
        n = 0
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))   # corrupt -> raises -> fail-closed
            n = int(rec["counter"])
        n += 1
        gen = f"{install_id}:{n}"
        _atomic_write(p, json.dumps({"counter": n, "generation": gen}, indent=2) + "\n")
        return gen
    finally:
        lock.unlink(missing_ok=True)


def read_high_water(data_dir) -> int:
    p = Path(data_dir) / _HIGH_WATER_FILE
    if not p.exists():
        return 0
    try:
        return int(p.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        return 0


def bump_high_water(data_dir, count: int) -> None:
    cur = read_high_water(data_dir); new = max(cur, int(count))
    if new != cur:
        _atomic_write(Path(data_dir) / _HIGH_WATER_FILE, str(new))


def read_high_water_or_none(data_dir) -> "int | None":
    p = Path(data_dir) / _HIGH_WATER_FILE
    if not p.exists():
        return None
    try:
        return int(p.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        return None


def record_high_water(conn, data_dir) -> int:
    n = conn.execute("SELECT count(*) FROM content_refs").fetchone()[0]
    bump_high_water(data_dir, n)
    return n


def reset_high_water(conn, data_dir) -> int:
    """RISK-RECOVERY-R1-003: re-baseline the high-water DOWN to the current content_refs count.
    Called ONLY after an INTENTIONAL shrink (eviction / compact) or by the operator escape hatch
    (`brain recover --reset-high-water`). The non-decreasing `bump_high_water` detects truncation;
    this is the sanctioned way to lower it so a legitimate compaction can't permanently fail the
    data-intact gate. Writes the exact count (atomic)."""
    n = conn.execute("SELECT count(*) FROM content_refs").fetchone()[0]
    p = Path(data_dir) / _HIGH_WATER_FILE
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".hw.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(n))
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return n


def write_owner_only(path: Path, data: bytes) -> None:
    path = Path(path)
    # O_NOFOLLOW: refuse to follow a symlink swapped at the target path on POSIX
    # (defence-in-depth; no-op on Windows where the flag is absent — SEC-TASK4-002)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(path), flags, 0o600)
    try:
        # SEC-CORTEX-ENC-013 (Windows pre-hardening exposure window, v9.9.3
        # remediation): os.open()'s mode argument (0o600 above) is IGNORED on
        # Windows -- the file is created with the parent directory's
        # inherited/default ACLs. The old order wrote+fsynced+closed the full
        # secret payload FIRST and only hardened the ACL afterward, so a fully
        # populated secret sat with weak ACLs for the entire write duration.
        # O_EXCL above guarantees THIS process just created a new, EMPTY file,
        # so it is safe (and required) to harden the ACL now, before any
        # secret byte is written. Fail CLOSED: if hardening the still-empty
        # file fails, close the fd, best-effort unlink the (empty) artifact,
        # and re-raise -- never fall through to writing the secret payload
        # into a file whose ACL we failed to harden.
        if sys.platform == "win32":
            try:
                _set_windows_owner_only_dacl(path)
            except Exception:
                os.close(fd)
                fd = None
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass  # best-effort cleanup; do not mask the original exception
                raise
        # F5 (SEC-CR104-MAJOR): a single os.write() may short-write on some POSIX
        # systems (pipes, unusual filesystems).  Loop until all bytes are written so
        # large key-equivalent artifacts (escrow blobs, export files) are never
        # silently truncated.  fsync() before close for crash-safe durability.
        view = memoryview(data)
        total = len(data)
        written = 0
        while written < total:
            n = os.write(fd, view[written:])
            written += n
        os.fsync(fd)
    finally:
        if fd is not None:
            os.close(fd)
    # SEC-001 (CWE-732, Toji audit v9.8.0->v9.9.1, v9.9.2 remediation): fail CLOSED
    # on post-write permission verification failure. Previously, if
    # verify_owner_only() returned False, the exception propagated but the
    # just-written secret-bearing artifact was NEVER removed -- it was left on disk
    # with no owner-only guarantee. A caller catching the exception had no way to
    # know an unprotected artifact still existed. Now: the verify step is guarded;
    # on ANY failure, best-effort unlink the artifact before re-raising (bare
    # `raise` preserves the original exception type and traceback -- cleanup
    # failure is intentionally swallowed so it never masks the real error). The
    # Windows DACL hardening itself already happened pre-write (above, SEC-CORTEX-
    # ENC-013); this is the existing defence-in-depth double-check.
    try:
        if not verify_owner_only(path):
            raise PermissionError(f"failed to establish owner-only permissions on {path}")
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass  # best-effort cleanup; do not mask the original exception
        raise


def _set_windows_owner_only_dacl(path: Path) -> None:  # pragma: no cover - Windows only
    import win32security, ntsecuritycon, win32api
    user, _, _ = win32security.LookupAccountName("", win32api.GetUserName())
    sd = win32security.GetFileSecurity(str(path), win32security.DACL_SECURITY_INFORMATION)
    dacl = win32security.ACL()  # empty -> add only the owner
    dacl.AddAccessAllowedAce(win32security.ACL_REVISION, ntsecuritycon.FILE_ALL_ACCESS, user)
    # Mark the DACL protected so inherited ACEs from parent containers are dropped
    sd.SetSecurityDescriptorControl(win32security.SE_DACL_PROTECTED, win32security.SE_DACL_PROTECTED)
    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(str(path), win32security.DACL_SECURITY_INFORMATION, sd)


def verify_owner_only(path: Path) -> bool:
    path = Path(path)
    if sys.platform == "win32":  # pragma: no cover - Windows only
        try:
            import win32security, win32api
            user, _, _ = win32security.LookupAccountName("", win32api.GetUserName())
            sd = win32security.GetFileSecurity(str(path), win32security.DACL_SECURITY_INFORMATION)
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                return False
            allowed_count = 0
            for i in range(dacl.GetAceCount()):
                (ace_type, ace_flags), mask, sid = dacl.GetAce(i)
                # Only ALLOW ACEs are grants; DENY ACEs are restrictive — skip them
                if ace_type != win32security.ACCESS_ALLOWED_ACE_TYPE:
                    continue
                if sid != user:
                    return False
                allowed_count += 1
            # BUG-CORTEXREPAIR-9.12.0-001: `ace_flags` (inheritance bits --
            # OBJECT_INHERIT_ACE/CONTAINER_INHERIT_ACE/INHERITED_ACE etc.) is
            # deliberately NOT inspected above. An ALLOW ace for the current
            # user is owner-only-compliant whether it is explicit or carries
            # (OI)(CI) inheritance flags -- directories hardened via
            # crypto._harden_windows_acl(path, is_dir=True) publish an
            # inheritable grant, and this function must still accept them.
            return allowed_count >= 1
        except Exception:
            return False
    import stat as _stat
    return (_stat.S_IMODE(path.stat().st_mode) & 0o077) == 0


# ---------------------------------------------------------------------------
# SEC-001 (CWE-732, Toji audit 2026-08-03, v9.12.0 Wave B2): directory/file
# storage primitives for Cortex's PRIMARY (base, always-on) data locations --
# data_dir/memories_dir/model_cache (cortex/paths.py) and the brain.db PARENT
# directory (cortex/store.py). write_owner_only()/verify_owner_only() above
# already cover single-shot RECOVERY artifacts (key-generation lock, escrow);
# these two functions are the directory-shaped and umask-proof-new-file
# counterparts for the base storage path.
#
# WINDOWS PRIMITIVE CHOICE (deliberate divergence from the pattern above):
# write_owner_only() hardens via _set_windows_owner_only_dacl(), which
# hard-imports pywin32 (win32security/ntsecuritycon/win32api). pywin32 is an
# OPTIONAL, encryption-extras-only dependency (requirements-enc.txt, never
# requirements-brain.txt) -- fine for write_owner_only()'s existing callers
# (key-generation/escrow, already deep in an encryption/recovery flow that
# presumes the extras are installed), but data_dir()/memories_dir()/
# model_cache()/db_path.parent are on the BASE path every Store() touches,
# encrypted or not. Hard-requiring pywin32 there would break every
# unencrypted Windows install that never installed requirements-enc.txt.
# crypto._harden_windows_acl (cortex/crypto.py) is the SAME class of
# "existing primitive, reuse, don't invent new platform logic" (spec Sec
# 22.4) already used for exactly this reason -- it hardens the encryption
# salt sidecar file via subprocess+icacls.exe (bundled with every Windows
# install, no pywin32 needed) and is explicitly documented as safe to call
# "before the encryption extras... are installed." Reused here unchanged.
# ---------------------------------------------------------------------------

# NOISE CONTROL for the existing-path warning below: data_dir()/memories_dir()/
# model_cache()/db_path.parent are called on EVERY Cortex operation, and EVERY
# pre-v9.12.0 install's directories (created by the old bare mkdir, no
# restrictive mode) will fail verify_owner_only() forever until an operator or
# Wave B4's repair tooling fixes them. A per-CALL warnings.warn() was measured
# during this fix's own test development to fire dozens of times per pytest
# file (each test's tmp_path is a distinct never-before-seen "existing,
# non-owner-only" directory) -- the same shape of flood would hit every real
# command an upgrading user runs, forever. The repo's own standing rule
# ("a control that cannot cover a path must say so visibly, never silently",
# CLAUDE.md) requires VISIBLE, not requires REPEATED — this process-lifetime
# flag caps the warning to its first occurrence per process, still guaranteeing
# it is visible in the output of every run/session that hits the gap, without
# drowning that run's other output.
_unsafe_dir_warned_this_process = False


def ensure_owner_only_dir(path: Path) -> None:
    """Create `path` (and any missing parents) as an owner-only directory.

    POSIX: os.makedirs(path, mode=0o700) at CREATION time. 0o700 has zero
    group/other bits, so no umask value can leave the result broader than
    owner-only (umask only ever SUBTRACTS bits from the requested mode) --
    unlike write_owner_only()'s FILE case, no separate post-creation
    verify+correct step is needed here for the POSIX branch.

    Windows: delegates to crypto._harden_windows_acl(path, is_dir=True) (see
    module-level comment above for why NOT _set_windows_owner_only_dacl).
    The is_dir=True form grants an INHERITABLE owner-only ACE
    ((OI)(CI) — object-inherit + container-inherit) rather than a plain,
    non-inheritable grant, so files/subdirectories created inside `path`
    afterward also inherit owner-only automatically instead of the token
    default DACL (BUG-CORTEXREPAIR-9.12.0-001). Fail-soft by that function's
    own design -- never raises, never blocks Cortex operation; on any
    hardening failure it prints its own stderr warning.

    EXISTING-PATH GAP (spec Sec 18.2, v9.12.0 Wave B4): if `path` already
    exists, this function does NOT chmod/re-ACL it -- it only reports a
    non-owner-only mode via warnings.warn() and returns. Auto-remediating a
    live, possibly in-use data directory (deciding whether concurrent
    readers/writers are safe to interrupt, whether content written under the
    old mode also needs attention, etc.) is new machinery this function
    deliberately does not invent; B4 owns that repair decision. This mirrors
    validate_data_dir()'s existing warnings.warn() pattern in paths.py for
    the analogous "detected but not silently overridden" unsafe-path case.

    The warning fires at most ONCE per process (see the module-level
    _unsafe_dir_warned_this_process flag and its comment above) -- every
    Cortex operation calls this function, so an unrate-limited warning would
    repeat on every single call for the lifetime of an un-repaired install.
    """
    global _unsafe_dir_warned_this_process
    path = Path(path)
    if path.exists():
        if not verify_owner_only(path):
            if not _unsafe_dir_warned_this_process:
                _unsafe_dir_warned_this_process = True
                warnings.warn(
                    f"Cortex directory {path} (and possibly other Cortex "
                    "directories in this session) exist with a non-owner-only "
                    "mode; SEC-001 (CWE-732) hardening only applies at "
                    "directory creation time -- pre-existing directories were "
                    "NOT modified (v9.12.0 Wave B4 tracks the repair decision; "
                    "see recovery.ensure_owner_only_dir's docstring). Further "
                    "occurrences are not repeated this process."
                )
        return
    os.makedirs(str(path), mode=0o700, exist_ok=True)
    if sys.platform == "win32":  # pragma: no cover - Windows only
        from .crypto import _harden_windows_acl
        # BUG-CORTEXREPAIR-9.12.0-001: is_dir=True selects the inheritable
        # (OI)(CI) grant so files created inside `path` afterward inherit an
        # owner-only ACE instead of the token default DACL (owner +
        # Administrators + SYSTEM). See crypto._harden_windows_acl's
        # docstring for the full regression writeup.
        _harden_windows_acl(path, is_dir=True)


def ensure_owner_only_new_file(path: Path) -> None:
    """Pre-create an EMPTY file at `path` with owner-only permissions, IF AND
    ONLY IF `path` does not already exist. No-op (never chmods) when the path
    already exists -- same existing-path posture as ensure_owner_only_dir
    above (the repair decision for a pre-existing broader-mode file is
    likewise deferred to v9.12.0 Wave B4, not invented here).

    Companion for callers that must hand a FRESH, already-narrow-permission
    path to a third-party library (e.g. sqlite3.connect()/sqlcipher3.connect())
    that manages its own subsequent writes -- write_owner_only() above is
    unsuitable there because it requires the complete byte content up front
    and performs its own single O_EXCL-guarded write; this function only
    pre-creates an EMPTY placeholder with the SAME umask-proof 0o600-request
    reasoning, then hands control to the caller's own library.

    CALLER CONTRACT: nothing in this repository currently calls this
    function from a code path that also depends on the target path's
    absence as a signal (see cortex/store.py's Store.__init__, which
    deliberately does NOT call this for db_path -- see that file's own
    comment for why). Any future caller must independently confirm the
    target path's existence is not already a meaningful signal elsewhere.
    """
    path = Path(path)
    if path.exists():
        return
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    except FileExistsError:
        return  # lost a creation race to a concurrent process; leave it alone
    if sys.platform == "win32":  # pragma: no cover - Windows only
        from .crypto import _harden_windows_acl
        _harden_windows_acl(path)
