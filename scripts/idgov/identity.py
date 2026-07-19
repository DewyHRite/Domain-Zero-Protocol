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
        _harden_owner_only(tf)  # Windows ACL (best-effort, now warns on failure)
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

def _harden_owner_only(path):
    try:
        if os.name == "nt":
            import subprocess, getpass
            subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r",
                            f"{getpass.getuser()}:F"], check=True, capture_output=True)
        else:
            os.chmod(path, 0o600)
    except Exception as e:
        import sys
        print(f"[idgov:identity] WARNING: could not harden {path} owner-only perms: {e}",
              file=sys.stderr)
