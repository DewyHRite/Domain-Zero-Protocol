"""Cortex encryption-at-rest key management + connection factory (v9.8.0,
PLAN-CORTEX-ENC-001). Imported lazily by store.py only when encryption is enabled,
so the optional deps (sqlcipher3, argon2-cffi, keyring) are not required by default.
"""
from __future__ import annotations
import base64
import binascii
import os
import stat
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from .errors import CortexKeyUnavailableError, DependencyError  # re-exported + raised by resolve_key

ARGON2_PARAMS = {"memory_cost": 65536, "time_cost": 3, "parallelism": 1, "hash_len": 32}
SALT_FILENAME = "brain.db.salt"
KEYRING_SERVICE = "dzp-cortex"


def load_or_create_salt(data_dir: str | Path) -> bytes:
    """Return the 16-byte KDF salt, creating it once as a 0600 sidecar.
    Stored OUTSIDE the encrypted DB (needed before the DB can be opened).

    SEC-CORTEX-ENC-001 (v9.8.0): atomic creation via O_EXCL so the file is
    never visible to other OS users with less-restrictive permissions between
    creation and chmod.  If a concurrent process wins the race (FileExistsError),
    fall back to reading the existing salt.

    C2-2 (v9.9.1, RISK-ENC-003 P3 residual #2): on Windows, 0o600 (passed to
    os.open above) sets no NTFS ACL — the salt file remains readable by any
    account with filesystem access to the containing directory.  Immediately
    after creating the file, ``_harden_windows_acl`` restricts the ACL to the
    current user only (fail-soft; never blocks brain operation).
    """
    path = Path(data_dir) / SALT_FILENAME
    if path.exists():
        return path.read_bytes()
    salt = os.urandom(16)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(str(path), flags, 0o600)
        try:
            os.write(fd, salt)
        finally:
            os.close(fd)
    except FileExistsError:
        # Another process created the salt file between our exists() check and
        # our O_EXCL open — read the winner's salt instead.
        return path.read_bytes()
    _harden_windows_acl(path)
    return salt


def _harden_windows_acl(path: Path, *, is_dir: bool = False) -> None:
    """Best-effort Windows ACL hardening for a just-created key-equivalent
    file, OR (BUG-CORTEXREPAIR-9.12.0-001, v9.12.0 Wave B4 regression fix)
    for an owner-only-intended DIRECTORY.

    C2-2 (v9.9.1): POSIX-style 0o600 bits (set via os.open above) have no effect
    on Windows NTFS ACLs, so the salt sidecar remains readable by any account
    with filesystem access to the containing directory unless the ACL is
    explicitly restricted.  Uses the built-in ``icacls`` CLI via subprocess
    (no new dependency) rather than pywin32: this salt-creation path can run
    before the encryption extras (which bundle pywin32 on Windows, per
    requirements-enc.txt) are installed, so we avoid taking on a hard pywin32
    import here.

    Fail-soft by design: never raises and never blocks brain operation. On any
    failure (icacls missing, non-NTFS volume, permission denied, etc.) prints a
    single stderr warning and continues — the file still has the 0o600-style
    bits set by the caller. No-op on non-Windows platforms.

    CodeRabbit PR#105 (v9.9.1, closes accepted-P3 edge on SEC-CORTEX-ENC-010/
    RISK-ENC-003): a bare username passed to ``icacls /grant:r <user>:F`` is
    ambiguous/unreliable on domain-joined machines (local vs. domain account
    resolution). When ``USERDOMAIN`` is present and non-empty, the grant
    target is qualified as ``DOMAIN\\user``; otherwise the bare
    ``USERNAME``/``USER``/``getpass.getuser()`` fallback is used unchanged.

    BUG-CORTEXREPAIR-9.12.0-001 (v9.12.0 Wave B4 regression, discovered
    during the same wave's `brain repair-perms` rollout and confirmed on the
    live brain by Gojo investigation 2026-08-05): this primitive originated
    for a FILE (the salt sidecar) and its grant — plain ``<principal>:F``,
    with no ``(OI)(CI)`` object/container-inherit flags — is correct there.
    `repair.py::_harden_existing` and `recovery.ensure_owner_only_dir` later
    reused it UNCHANGED for DIRECTORIES that already have children relying
    on inherited ACEs. Replacing a directory's DACL with a non-inheritable
    grant (``/inheritance:r /grant:r principal:F``) triggers Windows'
    automatic-inheritance propagation on every child whose ACE is marked
    "inherited from this parent": the parent now publishes nothing
    inheritable, so those children lose their inherited ACE and — if they
    have no ACE of their own — end up with an EMPTY DACL, i.e. deny
    everyone, including the object's own owner. `is_dir=True` selects the
    directory-appropriate inheritable grant instead — ``principal:(OI)(CI)F``
    (object-inherit + container-inherit, Full Control) — so existing
    children keep receiving an equivalent owner-only ACE via inheritance
    instead of losing theirs, and NEW children created after hardening also
    inherit owner-only automatically. `is_dir` defaults to `False` so every
    pre-existing FILE call site (the salt sidecar here, and
    `recovery.write_owner_only`'s Windows branch which uses a different
    primitive entirely) is unaffected.
    """
    # SEC-STATE-9.12.0-001/-002 (idiom fold-in, v9.12.1 Batch B): project-wide
    # Windows-detection idiom is os.name == "nt" (immune to the
    # platform.system()/platform._uname_cache poisoning class AND to a live
    # sys.platform monkeypatch around real work -- BUG-STATE-001). This
    # guard never called platform.system()/uname() to begin with (sys.platform
    # itself is not the poisoning-prone API), so this is consistency
    # hardening, not a vulnerability fix -- os.name != "nt" is behaviorally
    # equivalent to sys.platform != "win32" on every platform this codebase
    # runs on.
    if os.name != "nt":
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
            "skipping ACL hardening (fail-soft, C2-2). The salt file relies on 0o600-style "
            "bits only, which NTFS does not enforce.",
            file=sys.stderr,
        )
        return
    userdomain = os.environ.get("USERDOMAIN", "").strip()
    principal = f"{userdomain}\\{current_user}" if userdomain else current_user
    # CodeRabbit PR#105 round-2 (ruff S607): fully-qualified icacls path so a
    # writable dir earlier in PATH can't shadow the system binary. Fail-soft:
    # if the resolved path is absent the FileNotFoundError below warns+continues.
    icacls_exe = os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"), "System32", "icacls.exe"
    )
    # BUG-CORTEXREPAIR-9.12.0-001: directories need an INHERITABLE grant
    # ((OI)(CI) = object-inherit + container-inherit) so existing/future
    # children keep an equivalent owner-only ACE via inheritance; a plain
    # grant is correct only for files (unchanged default behavior).
    grant_rights = "(OI)(CI)F" if is_dir else "F"
    try:
        result = subprocess.run(
            [icacls_exe, str(path), "/inheritance:r", "/grant:r", f"{principal}:{grant_rights}"],
            capture_output=True,
            text=True,
            timeout=10,
            # BUG-CORTEXTRIGGER-9.12.0-001: this function already early-returns
            # above on any non-Windows platform, so `subprocess.CREATE_NO_WINDOW`
            # (a Windows-only constant) is always safe to reference here.
            # Without it, icacls.exe -- a console-subsystem child -- pops a new
            # visible console when this runs under a console-less detached
            # parent (cortex_trigger.py via script_coordinator.py's
            # _spawn_detached).
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            print(
                f"WARNING: failed to harden Windows ACL on {path} "
                f"(icacls exit {result.returncode}): {result.stderr.strip()}. "
                "Continuing without ACL hardening (fail-soft, C2-2) — the salt file "
                "relies on 0o600-style bits only, which NTFS does not enforce.",
                file=sys.stderr,
            )
    except Exception as exc:
        print(
            f"WARNING: failed to harden Windows ACL on {path}: {exc}. "
            "Continuing without ACL hardening (fail-soft, C2-2) — the salt file "
            "relies on 0o600-style bits only, which NTFS does not enforce.",
            file=sys.stderr,
        )


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 32-byte AES-256 key from a passphrase via Argon2id.

    ENC-003 (v9.8.0): salt must be at least 16 bytes to prevent trivially weak
    KDF inputs.
    """
    if len(salt) < 16:
        raise ValueError("salt must be at least 16 bytes")
    try:
        from argon2.low_level import hash_secret_raw, Type
    except Exception as exc:  # pragma: no cover - optional dep
        raise DependencyError("argon2-cffi not installed; install requirements-enc.txt") from exc
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_PARAMS["time_cost"],
        memory_cost=ARGON2_PARAMS["memory_cost"],
        parallelism=ARGON2_PARAMS["parallelism"],
        hash_len=ARGON2_PARAMS["hash_len"],
        type=Type.ID,
    )


# ---------------------------------------------------------------------------
# Hybrid key-resolution layer (Task 4)
# ---------------------------------------------------------------------------

def _keyring_get(account: str) -> str | None:
    """Return the cached base64 key from the OS keystore, or None on any failure."""
    try:
        import keyring
        return keyring.get_password(KEYRING_SERVICE, account)
    except Exception:
        return None


def _keyring_set(account: str, value_b64: str) -> None:
    """Store a base64 key in the OS keystore. Raises if keyring is absent."""
    import keyring  # raises ImportError if absent (intentional — caller must handle)
    keyring.set_password(KEYRING_SERVICE, account, value_b64)


def _decode_key_value(value: str) -> bytes:
    """Accept a 'file:<path>' reference or a raw base64 key. Returns 32 raw bytes.

    ENC-002 (v9.8.0): parse file: URIs robustly via urlparse so that
    ``file://host/path`` (non-localhost host) is rejected with a clear error
    instead of silently becoming a relative path or leaking a UNC access.
    Accepted forms: ``file:/abs``, ``file:///abs``, ``file://localhost/abs``.

    Raises CortexKeyUnavailableError if the decoded length is not exactly 32.
    """
    if value.startswith("file:"):
        parsed = urlparse(value)
        netloc = parsed.netloc
        if netloc and netloc.lower() not in ("", "localhost"):
            raise CortexKeyUnavailableError(
                f"file: URI with a host is not supported; use file:///absolute/path "
                f"(got host={netloc!r})"
            )
        # Use the path component from urlparse; handles file:///abs and file:/abs forms.
        path = parsed.path
        value = Path(path).read_text(encoding="ascii", errors="strict").strip()
    try:
        raw = base64.b64decode(value, validate=True)
    except binascii.Error:
        raise CortexKeyUnavailableError("env/key value is not valid base64")
    if len(raw) != 32:
        raise CortexKeyUnavailableError(
            f"resolved key is {len(raw)} bytes, expected 32"
        )
    return raw


def resolve_key(
    data_dir,
    *,
    key_env: str = "DZP_CORTEX_KEY",
    account: str = "default",
    allow_prompt: bool = True,
) -> bytes:
    """Return the 32-byte encryption key using the following priority order:

    1. Environment variable ``key_env`` — value is ``file:<path>`` (base64 file)
       or a raw base64-encoded 32-byte key.
    2. OS keyring via ``_keyring_get(account)``.
    3. Interactive passphrase prompt (TTY only, gated on ``allow_prompt``).

    Raises ``CortexKeyUnavailableError`` if no source is available.
    """
    # 1. env (file: ref or raw base64) — suitable for CI / non-interactive
    env_val = os.environ.get(key_env)
    if env_val:
        return _decode_key_value(env_val)
    # 2. OS keystore (cached base64 key written by store_passphrase)
    cached = _keyring_get(account)
    if cached:
        return _decode_key_value(cached)
    # 3. interactive passphrase (TTY only)
    if allow_prompt and sys.stdin is not None and sys.stdin.isatty():
        import getpass
        passphrase = getpass.getpass("Cortex passphrase: ")
        salt = load_or_create_salt(data_dir)
        return derive_key(passphrase, salt)
    raise CortexKeyUnavailableError(
        f"No Cortex key available: set {key_env} (file:<path> or base64), "
        "run `brain key set`, or provide a passphrase on an interactive terminal."
    )


def store_passphrase(data_dir, passphrase: str, account: str = "default") -> None:
    """Derive the 32-byte key from *passphrase* and cache it (base64) in the OS keystore."""
    salt = load_or_create_salt(data_dir)
    key = derive_key(passphrase, salt)
    _keyring_set(account, base64.b64encode(key).decode())


# ---------------------------------------------------------------------------
# Task 5: encrypted-connection factory
# ---------------------------------------------------------------------------

def sqlcipher_available() -> bool:
    """Return True if sqlcipher3 is installed and importable."""
    try:
        import sqlcipher3  # noqa: F401
        return True
    except Exception:
        return False


def open_encrypted_connection(db_path, key: bytes):
    """Open a SQLCipher connection, apply the key, load sqlite_vec, and mirror the
    plaintext Store.connect() setup. ``key`` is 32 raw bytes — SQLCipher raw-key hex.

    Key handling: PRAGMA key = "x'<hexchars>'" built from key.hex() (the key is 32
    validated raw bytes; the hex is built ONLY from those bytes, never user text —
    there is no injection surface here).

    SEC-CORTEX-ENC-004 (v9.8.0): key must be exactly 32 bytes.  A shorter key
    (e.g. 16 bytes for AES-128) or a longer key would silently produce a different
    cipher configuration; reject early with a clear error.
    """
    # SEC-CORTEX-ENC-004: validate key length before opening any connection.
    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        raise CortexKeyUnavailableError("encryption key must be exactly 32 bytes")
    try:
        import sqlcipher3
    except Exception as exc:  # pragma: no cover - optional dep
        raise DependencyError("sqlcipher3 not installed; install requirements-enc.txt") from exc
    conn = sqlcipher3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlcipher3.Row
    # Raw key (no KDF inside SQLCipher): PRAGMA key = "x'<hex>'". Parameterized form
    # is not supported for PRAGMA key in SQLCipher, so we build the hex literal from
    # validated raw bytes (never user text) — there is no injection surface here.
    # MUST be the first DB operation (SQLCipher requires the key before any read)
    conn.execute("PRAGMA key = \"x'%s'\"" % key.hex())
    # SEC-CORTEX-ENC-005 (v9.8.0): pin SQLCipher v4 cipher parameters so every
    # encrypted DB — migrations included — stays readable across sqlcipher3
    # upgrades that might change the default cipher suite.
    conn.execute("PRAGMA cipher_compatibility = 4")
    conn.execute("PRAGMA busy_timeout = 10000")
    # load sqlite_vec on the encrypted connection (spike-verified: enable_load_extension works)
    try:
        import sqlite_vec
    except Exception as exc:
        raise DependencyError("sqlite-vec is not installed; install requirements-brain.txt") from exc
    conn.enable_load_extension(True)
    try:
        sqlite_vec.load(conn)
    finally:
        conn.enable_load_extension(False)
    return conn


# ---------------------------------------------------------------------------
# Task 1 (R1a): Version/KDF-authenticated self-contained wrapped escrow
# (CODE-001, CODE-002, §18.1) — PLAN-CORTEX-RECOVERY-001
# ---------------------------------------------------------------------------

import json as _json

_WRAP_MAGIC = "DZPC-ESCROW-1"
_WRAP_VERSION = 1
_WRAP_NONCE_LEN = 12
# Accepted Argon2id bounds (parameter-agility guardrails, CODE-001)
_KDF_BOUNDS = {"memory_cost": (8192, 1 << 21), "time_cost": (1, 10), "parallelism": (1, 16), "hash_len": (32, 32)}


def _wrap_aad(version, kdf, salt_b64, nonce_b64, binding) -> bytes:
    return _json.dumps(
        {"version": version, "kdf": kdf, "salt": salt_b64, "nonce": nonce_b64, "binding": binding},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def export_wrapped(key: bytes, passphrase: str, *, binding: dict) -> bytes:
    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        raise ValueError("wrapped-escrow key must be exactly 32 bytes")
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as exc:  # pragma: no cover
        raise DependencyError("cryptography not installed; install requirements-enc.txt") from exc
    salt = os.urandom(16)
    kdf = {"algorithm": "argon2id", **{k: ARGON2_PARAMS[k] for k in ("memory_cost", "time_cost", "parallelism", "hash_len")}}
    wrap_key = derive_key(passphrase, salt)
    nonce = os.urandom(_WRAP_NONCE_LEN)
    salt_b64, nonce_b64 = base64.b64encode(salt).decode(), base64.b64encode(nonce).decode()
    aad = _wrap_aad(_WRAP_VERSION, kdf, salt_b64, nonce_b64, binding)
    ct = AESGCM(wrap_key).encrypt(nonce, bytes(key), aad)
    doc = {"magic": _WRAP_MAGIC, "version": _WRAP_VERSION, "kdf": kdf,
           "salt": salt_b64, "nonce": nonce_b64,
           "ciphertext": base64.b64encode(ct).decode(), "binding": binding}
    return _json.dumps(doc, indent=2).encode("utf-8")


def _derive_from_artifact_kdf(passphrase: str, salt: bytes, kdf: dict) -> bytes:
    if kdf.get("algorithm") != "argon2id":
        raise CortexKeyUnavailableError(f"unsupported escrow KDF algorithm: {kdf.get('algorithm')!r}")
    for name, (lo, hi) in _KDF_BOUNDS.items():
        v = kdf.get(name)
        if not isinstance(v, int) or not (lo <= v <= hi):
            raise CortexKeyUnavailableError(f"escrow KDF param {name}={v!r} out of accepted bounds [{lo},{hi}]")
    try:
        from argon2.low_level import hash_secret_raw, Type
    except Exception as exc:  # pragma: no cover
        raise DependencyError("argon2-cffi not installed") from exc
    return hash_secret_raw(secret=passphrase.encode("utf-8"), salt=salt,
                           time_cost=kdf["time_cost"], memory_cost=kdf["memory_cost"],
                           parallelism=kdf["parallelism"], hash_len=kdf["hash_len"], type=Type.ID)


# ---------------------------------------------------------------------------
# Task 5 (R1b): Generic payload wrap/unwrap — self-contained AEAD for arbitrary bytes
# (§18.3, PLAN-CORTEX-RECOVERY-001). Wrapped under the ESCROW passphrase (NOT the DB
# key) so memory exports survive total DB-key loss.
# ---------------------------------------------------------------------------

_PAYLOAD_MAGIC = "DZPC-PAYLOAD-1"
_PAYLOAD_VERSION = 1


def wrap_payload(data: bytes, passphrase: str, *, meta: dict) -> bytes:
    """AEAD-wrap arbitrary bytes under passphrase (escrow path). Self-contained:
    salt + nonce embedded, version+kdf+meta are authenticated (bound in AAD).
    Returns a JSON envelope as bytes (owner-only write is the caller's responsibility)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception as exc:  # pragma: no cover
        raise DependencyError("cryptography not installed; install requirements-enc.txt") from exc
    salt = os.urandom(16)
    kdf = {"algorithm": "argon2id", **{k: ARGON2_PARAMS[k] for k in ("memory_cost", "time_cost", "parallelism", "hash_len")}}
    wrap_key = derive_key(passphrase, salt)
    nonce = os.urandom(_WRAP_NONCE_LEN)
    salt_b64, nonce_b64 = base64.b64encode(salt).decode(), base64.b64encode(nonce).decode()
    aad = _wrap_aad(_PAYLOAD_VERSION, kdf, salt_b64, nonce_b64, meta)
    ct = AESGCM(wrap_key).encrypt(nonce, bytes(data), aad)
    return _json.dumps({"magic": _PAYLOAD_MAGIC, "version": _PAYLOAD_VERSION, "kdf": kdf,
                        "salt": salt_b64, "nonce": nonce_b64,
                        "ciphertext": base64.b64encode(ct).decode(), "meta": meta}, indent=2).encode("utf-8")


def unwrap_payload(blob: bytes, passphrase: str) -> tuple[bytes, dict]:
    """Unwrap a DZPC-PAYLOAD-1 envelope. Raises CortexKeyUnavailableError on tamper
    or wrong passphrase (matches the escrow error surface so callers have one catch)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.exceptions import InvalidTag
    except Exception as exc:  # pragma: no cover
        raise DependencyError("cryptography not installed") from exc
    try:
        doc = _json.loads(blob.decode("utf-8"))
        if doc.get("magic") != _PAYLOAD_MAGIC:
            raise CortexKeyUnavailableError("not a DZPC payload artifact")
        if doc.get("version") != _PAYLOAD_VERSION:
            raise CortexKeyUnavailableError(f"unsupported payload version {doc.get('version')!r}")
        kdf, meta = doc["kdf"], doc["meta"]
        salt = base64.b64decode(doc["salt"], validate=True)
        nonce = base64.b64decode(doc["nonce"], validate=True)
        ct = base64.b64decode(doc["ciphertext"], validate=True)
    except (ValueError, KeyError, binascii.Error) as exc:
        raise CortexKeyUnavailableError(f"malformed payload artifact: {exc}")
    wrap_key = _derive_from_artifact_kdf(passphrase, salt, kdf)
    aad = _wrap_aad(doc["version"], kdf, doc["salt"], doc["nonce"], meta)
    try:
        data = AESGCM(wrap_key).decrypt(nonce, ct, aad)
    except InvalidTag:
        raise CortexKeyUnavailableError("payload unwrap failed — wrong passphrase or tampered artifact")
    return data, meta


def import_wrapped(blob: bytes, passphrase: str) -> tuple[bytes, dict]:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.exceptions import InvalidTag
    except Exception as exc:  # pragma: no cover
        raise DependencyError("cryptography not installed") from exc
    try:
        doc = _json.loads(blob.decode("utf-8"))
        if doc.get("magic") != _WRAP_MAGIC:
            raise CortexKeyUnavailableError("not a DZPC escrow artifact")
        if doc.get("version") != _WRAP_VERSION:
            raise CortexKeyUnavailableError(f"unsupported escrow artifact version {doc.get('version')!r}")
        kdf = doc["kdf"]; binding = doc["binding"]
        salt = base64.b64decode(doc["salt"], validate=True)
        nonce = base64.b64decode(doc["nonce"], validate=True)
        ct = base64.b64decode(doc["ciphertext"], validate=True)
    except (ValueError, KeyError, binascii.Error) as exc:
        raise CortexKeyUnavailableError(f"malformed escrow artifact: {exc}")
    wrap_key = _derive_from_artifact_kdf(passphrase, salt, kdf)
    aad = _wrap_aad(doc["version"], kdf, doc["salt"], doc["nonce"], binding)
    try:
        key = AESGCM(wrap_key).decrypt(nonce, ct, aad)
    except InvalidTag:
        raise CortexKeyUnavailableError("escrow unwrap failed — wrong passphrase or tampered artifact")
    if len(key) != 32:
        raise CortexKeyUnavailableError(f"unwrapped key is {len(key)} bytes, expected 32")
    return key, binding
