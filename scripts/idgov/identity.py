#!/usr/bin/env python3
"""FEAT-IDGOV-001 writer identity (Sukuna F3 / D11). attested_writer is derived from
WHICH per-wrapper token signed the call, never from a caller-supplied --agent string.
Honest residual: a process running as the same OS user CAN read a token file and forge
that writer. Local integrity, NOT cross-agent non-repudiation (mirrors attestation.py's
documented boundary)."""
import hmac, hashlib, os, secrets, pathlib

TOKENS_DIR = pathlib.Path(__file__).resolve().parents[2] / ".protocol-state" / ".idgov-tokens"

def _token_file(writer):
    return TOKENS_DIR / f"{writer}.token"

_HARDEN_OVERRIDE_ENV = "DZP_ALLOW_UNHARDENED_IDGOV_TOKEN"


def provision(writer: str) -> str:
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(TOKENS_DIR, 0o700)  # mkdir mode is umask-masked; enforce explicitly
    except OSError:
        pass  # best-effort (Windows ignores POSIX mode; ACL handled per-file below)
    tf = _token_file(writer)
    if not tf.exists():
        # O_EXCL create at 0600 BEFORE the secret payload hits disk (mirrors
        # cortex/recovery.py SEC-CORTEX-ENC-013 + attestation.py owner-only pattern)
        fd = os.open(str(tf), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, secrets.token_hex(32).encode())
            os.fsync(fd)
        finally:
            os.close(fd)
    # Finding 12 (CodeRabbit PR#112, P2): re-assert owner-only hardening on
    # EVERY provision() call -- new AND pre-existing tokens (a token that
    # already existed on disk previously skipped this entirely, so a
    # first-run hardening failure would stick forever, silently, since
    # tf.exists() would be True on every later call). This token file is the
    # HMAC signing secret behind writer authority (a materially different
    # risk than attestation.py's advisory-only, already-accepted ISS-083 P3
    # boundary), so a hardening failure now fails CLOSED by default instead
    # of warning-then-continuing with a possibly world-readable secret. A
    # named, loud, opt-in override exists for the SAME genuine non-NTFS/
    # no-icacls platform gap attestation.py documents, so a real platform
    # constraint doesn't hard-brick minting -- it just requires an explicit,
    # visible acknowledgement instead of a silent continue.
    if not _harden_owner_only(tf):
        if os.environ.get(_HARDEN_OVERRIDE_ENV) == "1":
            import sys
            print(
                f"[idgov:identity] {_HARDEN_OVERRIDE_ENV}=1 override ACTIVE -- "
                f"continuing with an unhardened token at {tf} (writer-authority "
                "signing key may be readable beyond the intended OS user).",
                file=sys.stderr,
            )
        else:
            raise PermissionError(
                f"could not secure {tf} to owner-only access; refusing to use it as "
                f"a writer-authority signing key. Set {_HARDEN_OVERRIDE_ENV}=1 to "
                "proceed anyway (loud, non-default -- e.g. for a documented "
                "non-NTFS/no-icacls platform gap)."
            )
    return f"{writer}-wrapper-v1"

def sign(writer_token_id: str, nonce: str) -> str:
    writer = writer_token_id.rsplit("-wrapper-", 1)[0]
    key = _token_file(writer).read_text(encoding="utf-8").strip().encode()
    return hmac.new(key, nonce.encode(), hashlib.sha256).hexdigest()

def derive_writer(signature: str, nonce: str):
    if not TOKENS_DIR.exists():
        return None
    for tf in sorted(TOKENS_DIR.glob("*.token")):
        writer = tf.stem
        key = tf.read_text(encoding="utf-8").strip().encode()
        expected = hmac.new(key, nonce.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, signature):
            return writer, f"{writer}-wrapper-v1"
    return None

def _harden_owner_only(path) -> bool:
    """Returns True on success, False on failure (still prints the WARNING
    either way -- callers decide whether a failure is fatal)."""
    try:
        if os.name == "nt":
            import subprocess, getpass
            # BUG-CORTEXTRIGGER-9.12.0-001 consistency follow-up (Megumi
            # out-of-scope awareness note, security-review.md ~line 7246):
            # this branch is already gated on os.name == "nt", so
            # subprocess.CREATE_NO_WINDOW (a Windows-only constant) is
            # always safe to reference here. Without it, icacls.exe -- a
            # console-subsystem child -- would pop a new visible console if
            # this ever ran under a console-less detached parent (not
            # reachable today: secid/pre-commit run in the foreground only).
            #
            # CodeRabbit PR#117 round-1 nitpick (verified valid): the bare
            # "icacls" argv[0] let a writable directory earlier in PATH
            # shadow the real system binary. Fully-qualified via SystemRoot,
            # mirroring the identical fix already applied to
            # cortex/crypto.py:134-139 (CodeRabbit PR#105 round-2, ruff
            # S607) -- same rationale, same resolution pattern.
            icacls_exe = os.path.join(
                os.environ.get("SystemRoot", r"C:\Windows"), "System32", "icacls.exe"
            )
            subprocess.run([icacls_exe, str(path), "/inheritance:r", "/grant:r",
                            f"{getpass.getuser()}:F"], check=True, capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            os.chmod(path, 0o600)
        return True
    except Exception as e:
        import sys
        print(f"[idgov:identity] WARNING: could not harden {path} owner-only perms: {e}",
              file=sys.stderr)
        return False
