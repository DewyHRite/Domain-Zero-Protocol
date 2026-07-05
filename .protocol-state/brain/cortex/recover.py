"""Guided Cortex recovery orchestrator (PLAN-CORTEX-RECOVERY-001 R1b).
Capability probing (not classification), the §18.2 data-intact gate, a durable
idempotent recovery journal (§17.5), stale-lock reaping, and the guided ladder."""
from __future__ import annotations
import hashlib, importlib.util, json, os, tempfile, time
from pathlib import Path
from . import recovery

# Stable machine-readable exit codes (§17.5)
EXIT_OK = 0
EXIT_DIAGNOSTICS = 0
EXIT_USER_CANCEL = 1
EXIT_WRONG_FACTOR = 3
EXIT_CORRUPTION = 4
EXIT_UNSAFE_SCOPE = 5
EXIT_FAILED_MUTATION = 6


def canonical_smoke():
    """Return a callable wrapping the canonical vec0/fts5 smoke
    (`migrate_cortex_encrypt_9_8._smoke_test_virtual_tables`, raises on failure).
    RISK-RECOVERY-R1-010: try multiple candidate layouts (dev tree AND consumer distro
    layouts) and raise a NAMED FileNotFoundError if absent — never a cryptic import error
    that silently fails the data-intact gate forever."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "migrate_cortex_encrypt_9_8.py",   # .protocol-state/  (dev + standard distro)
        here.parents[1] / "migrate_cortex_encrypt_9_8.py",   # brain/            (flattened layout)
        here.parent / "migrate_cortex_encrypt_9_8.py",       # cortex/           (engine-colocated layout)
    ]
    mig = next((p for p in candidates if p.exists()), None)
    if mig is None:
        raise FileNotFoundError(
            "canonical vec0 smoke helper migrate_cortex_encrypt_9_8.py not found; looked in: "
            + ", ".join(str(c) for c in candidates))
    spec = importlib.util.spec_from_file_location("migrate_cortex_encrypt_9_8", str(mig))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def _smoke(conn) -> bool:
        mod._smoke_test_virtual_tables(conn)  # raises on failure
        return True
    return _smoke


def data_intact(conn, data_dir, *, smoke, valid_versions) -> tuple[bool, list[str]]:
    """Deterministic §18.2 predicate. ALL must hold; returns (ok, [failed reasons])."""
    reasons: list[str] = []
    try:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            reasons.append("integrity_check != ok")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            reasons.append("foreign_key_check reported violations")
    except Exception as exc:
        reasons.append(f"integrity/foreign_key check raised: {exc}")
    iid = recovery.current_install_id(data_dir)
    try:
        n = conn.execute("SELECT count(*) FROM cortex_installs WHERE install_id=?", (iid,)).fetchone()[0]
        if n < 1:
            reasons.append(f"cortex_installs has no row for the current install ({iid})")
    except Exception as exc:
        reasons.append(f"cortex_installs unreadable: {exc}")
    if smoke is None:
        reasons.append("vec0 virtual-table smoke check not provided (required)")
    else:
        try:
            if not smoke(conn):
                reasons.append("vec0 virtual-table smoke check failed")
        except Exception as exc:
            reasons.append(f"vec0 smoke raised: {exc}")
    try:
        refs = conn.execute("SELECT count(*) FROM content_refs").fetchone()[0]
        hw = recovery.read_high_water_or_none(data_dir)
        if hw is None:
            reasons.append("no high-water baseline recorded — cannot verify completeness")
        elif refs < hw:
            reasons.append(f"content_refs {refs} below high-water {hw} (possible truncation)")
    except Exception as exc:
        reasons.append(f"content_refs unreadable: {exc}")
    try:
        row = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        sv = int(row[0]) if row and str(row[0]).isdigit() else None
        if sv is None or sv not in set(valid_versions):
            reasons.append(f"metadata.schema_version {row[0] if row else None!r} is not a known-valid version")
    except Exception as exc:
        reasons.append(f"schema_version unreadable: {exc}")
    return (len(reasons) == 0, reasons)


# ---------------------------------------------------------------------------
# Task 3: Durable recovery journal — validated state machine + idempotent
# resume/abort + opaque tokens (DESIGN-002, SEC-003)
# ---------------------------------------------------------------------------

class CorruptJournalError(Exception):
    """Raised when a non-trailing journal line is malformed (possible tampering or mid-write
    corruption with valid records after it).  Callers should route to EXIT_CORRUPTION."""


def tokenize(data_dir, path) -> str:
    """Data-dir-relative token, else opaque external:<sha8>. Never leaks a raw path (SEC-003)."""
    p = Path(path)
    try:
        return str(p.resolve().relative_to(Path(data_dir).resolve())).replace("\\", "/")
    except Exception:
        digest = hashlib.sha256(str(p).encode("utf-8")).hexdigest()[:8]
        return f"external:{digest}"


class RecoveryJournal:
    """Durable, non-secret, validated-state-machine recovery journal (§17.5 / DESIGN-002).
    One JSON object per line; the latest object for an op_id is its current state (resumable)."""
    _TERMINAL = {"recovery-complete", "aborted", "rolled-back"}
    _TRANSITIONS = {
        "started": {"backup-created", "aborted"},
        "backup-created": {"mutation-started", "aborted"},
        "mutation-started": {"verification-failed", "recovery-complete", "aborted"},
        "verification-failed": {"rollback-pending", "aborted"},
        "rollback-pending": {"rolled-back", "aborted"},
        "recovery-complete": set(),
        "rolled-back": set(),
        "aborted": set(),
    }

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.path = self.data_dir / "recovery-journal.jsonl"

    def _now(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _append(self, obj: dict) -> None:
        if not self.path.exists():
            recovery.write_owner_only(self.path, b"")   # establish owner-only on first write
        line = json.dumps(obj, separators=(",", ":")) + "\n"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line); f.flush(); os.fsync(f.fileno())   # durable

    def begin(self, operation, *, source, target, key_generation, intent, rollback_pointer=None) -> str:
        op_id = f"{operation}-{self._now().replace(':','').replace('-','')}-{os.getpid()}"
        self._append({"op_id": op_id, "operation": operation,
                      "source": tokenize(self.data_dir, source),
                      "target": tokenize(self.data_dir, target),
                      "key_generation": key_generation, "intent": intent,
                      "stage": "started", "rollback_pointer": rollback_pointer,
                      "verification_result": None, "ts": self._now()})
        return op_id

    def _write_state(self, rec: dict, stage: str, **updates) -> dict:
        rec = dict(rec); rec["stage"] = stage; rec["ts"] = self._now()
        for k, v in updates.items():
            if v is not None:
                rec[k] = v
        self._append(rec)
        return rec

    def advance(self, op_id, stage, *, verification_result=None, rollback_pointer=None) -> dict:
        rec = self.read(op_id)
        if rec is None:
            raise ValueError(f"unknown op_id {op_id!r}")
        cur = rec["stage"]
        if stage == cur:
            return rec  # idempotent
        if stage not in self._TRANSITIONS.get(cur, set()):
            raise ValueError(f"illegal journal transition {cur!r} -> {stage!r}")
        return self._write_state(rec, stage, verification_result=verification_result,
                                 rollback_pointer=rollback_pointer)

    def set_verification(self, op_id, result) -> dict:
        rec = self.read(op_id)
        if rec is None:
            raise ValueError(f"unknown op_id {op_id!r}")
        return self._write_state(rec, rec["stage"], verification_result=result)

    def abort(self, op_id, reason) -> dict:
        rec = self.read(op_id)
        if rec is None:
            raise ValueError(f"unknown op_id {op_id!r}")
        if rec["stage"] in self._TERMINAL:
            return rec  # idempotent
        return self._write_state(rec, "aborted", verification_result=f"aborted: {reason}")

    def read(self, op_id) -> "dict | None":
        if not self.path.exists():
            return None
        lines = [l for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
        latest = None
        last_idx = len(lines) - 1
        for idx, raw in enumerate(lines):
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                if idx == last_idx:
                    # Trailing truncation (common power-loss case): tolerate and stop.
                    break
                # Malformed line with valid records after it — structural corruption.
                raise CorruptJournalError(
                    f"journal line {idx} is not valid JSON (mid-file corruption at {self.path})"
                ) from None
            if obj.get("op_id") == op_id:
                latest = obj
        return latest

    def resume(self, op_id) -> "dict | None":
        rec = self.read(op_id)
        if rec is None or rec["stage"] in self._TERMINAL:
            return None
        return rec


# ---------------------------------------------------------------------------
# Task 4: --clear-lock stale index.lock reaper (§6 F6)
# ---------------------------------------------------------------------------

def clear_stale_lock(data_dir, *, ttl_seconds: int = 900) -> tuple[bool, str]:
    """Remove <data_dir>/index.lock only if mtime age >= ttl. Returns (removed, message)."""
    lock = Path(data_dir) / "index.lock"
    if not lock.exists():
        return (False, "no index.lock present")
    age = time.time() - lock.stat().st_mtime
    if age < ttl_seconds:
        return (False, f"index.lock is fresh (age={age:.0f}s < {ttl_seconds}s) — NOT reaped")
    try:
        lock.unlink()
        return (True, f"reaped stale index.lock (age={age:.0f}s)")
    except OSError as exc:
        return (False, f"could not reap index.lock: {exc}")


# ---------------------------------------------------------------------------
# Task 8: probe_state — observed capability probe (DESIGN-003)
# ---------------------------------------------------------------------------

def probe_state(data_dir) -> dict:
    """Observed state ONLY — no F-classification (capability probing, not F1/F3 distinction).

    SEC-NEW-001 / R1-005: resolve the key ONCE and reuse it for the open — no TOCTOU
    re-resolve that could mislabel a key-not-found as a connection error.
    """
    from . import crypto
    dd = Path(data_dir)
    db = dd / "brain.db"
    st = {
        "db_present": db.exists(),
        "encrypted": None,
        "key_status": "disabled",
        "schema_markers_agree": None,
        "lock_present": (dd / "index.lock").exists(),
    }
    if not db.exists():
        return st
    with open(db, "rb") as f:
        st["encrypted"] = f.read(16) != b"SQLite format 3\x00"
    conn = None
    try:
        if st["encrypted"]:
            try:
                # SEC-NEW-001/R1-005: resolve ONCE, reuse — no TOCTOU re-resolve.
                # open_encrypted_connection does NOT raise on a wrong key; SQLCipher defers
                # HMAC verification to the first page read.  Mark "unlocked" tentatively
                # after the open succeeds; demote to "locked" in the outer except if the
                # first query fails (wrong key / corrupt data).
                key = crypto.resolve_key(data_dir, allow_prompt=False)
                conn = crypto.open_encrypted_connection(db, key)
                st["key_status"] = "unlocked"
            except Exception:
                st["key_status"] = "locked"
                return st
        else:
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(str(db))
        uv = conn.execute("PRAGMA user_version").fetchone()[0]
        row = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        mirror = int(row[0]) if row and str(row[0]).isdigit() else None
        st["schema_markers_agree"] = (mirror is not None and int(uv) == mirror)
    except Exception:
        # A query failure on an encrypted DB means the key cannot actually decrypt the data.
        if st["encrypted"] and st["key_status"] == "unlocked":
            st["key_status"] = "locked"
        st["schema_markers_agree"] = None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    return st


# ---------------------------------------------------------------------------
# Task 9: finalize — best-effort cleanup + salt-sidecar gating (§17.6/IMPL-005)
# ---------------------------------------------------------------------------

def finalize(data_dir, *, artifacts, escrow_verified) -> dict:
    """Best-effort cleanup contract (§17.6). NOT a purge guarantee.

    brain.db.salt is NEVER removed unless escrow_verified is True (§18.1).
    Always warns about external copies (filesystem history / cloud sync /
    volume snapshots / SSD over-provisioning).
    """
    res: dict = {"removed": [], "kept": [], "warnings": []}
    salt = (Path(data_dir) / "brain.db.salt").resolve()
    for a in artifacts:
        p = Path(a)
        if p.resolve() == salt and not escrow_verified:
            res["kept"].append(str(p))
            res["warnings"].append(
                "brain.db.salt kept: escrow self-containment not round-trip-verified (§18.1)"
            )
            continue
        try:
            p.unlink()
            res["removed"].append(str(p))
        except FileNotFoundError:
            res["warnings"].append(f"{p.name}: already absent")
        except OSError as exc:
            res["kept"].append(str(p))
            res["warnings"].append(f"{p.name}: could not remove ({exc})")
    res["warnings"].append(
        "best-effort only — external copies may persist: filesystem history, "
        "cloud sync, volume snapshots, SSD over-provisioning"
    )
    return res
