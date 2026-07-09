"""Recovery-artifact metadata + key-generation record (PLAN-CORTEX-RECOVERY-001 §18.5;
DESIGN-001). The key_generation changes ONLY when key material changes (allocate),
never on export/read. Allocation is lock-guarded and fail-closed."""
from __future__ import annotations
import hashlib, json, os, sys, tempfile, time
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
            return allowed_count >= 1
        except Exception:
            return False
    import stat as _stat
    return (_stat.S_IMODE(path.stat().st_mode) & 0o077) == 0
