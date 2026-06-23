"""Cortex encryption-at-rest key management + connection factory (v9.8.0,
PLAN-CORTEX-ENC-001). Imported lazily by store.py only when encryption is enabled,
so the optional deps (sqlcipher3, argon2-cffi, keyring) are not required by default.
"""
from __future__ import annotations
import base64
import binascii
import os
import stat
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
    return salt


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
