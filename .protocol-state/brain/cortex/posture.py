"""Phase-1 encryption posture advisory (PLAN-CORTEX-ENC-001).
Best-effort, never raises — pure reporting for `brain status`.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Reuse the cloud-sync token convention used by paths.py safety checks.
_SYNC_TOKENS = ("onedrive", "dropbox", "google drive", "googledrive", "icloud", "box sync")


def _on_cloud_sync_path(data_dir: Path) -> bool:
    p = str(data_dir).lower()
    return any(tok in p for tok in _SYNC_TOKENS)


def _disk_encryption_status() -> str:
    """Best-effort OS-disk-encryption probe. Returns 'on'|'off'|'unknown'.
    Never raises; 'unknown' is always an acceptable answer.

    SEC-STATE-9.12.0-001: platform detection deliberately does NOT use
    `platform.system()`/`platform.uname()` -- both share BUG-STATE-001's
    Class-1 exposure, a process-wide result CACHED on the first call
    anywhere in the process (`platform._uname_cache`) that a poisoned
    earlier caller can corrupt for every later caller, including this one,
    even in an unrelated file. Uses the same `os.name`/`sys.platform` idiom
    established as project-wide precedent by that fix
    (`project_state_manager.py`, `attestation.py`): `os.name == "nt"` for
    the Windows-only branch (immune to both the uname cache AND a live
    `sys.platform` monkeypatch), `sys.platform` prefix checks for the
    darwin/linux distinction (cheap, uncached, no I/O).
    """
    try:
        if sys.platform == "darwin" and shutil.which("fdesetup"):
            out = subprocess.run(["fdesetup", "status"], capture_output=True, text=True, timeout=5)
            if "On" in out.stdout:
                return "on"
            if "Off" in out.stdout:
                return "off"
        elif os.name == "nt" and shutil.which("manage-bde"):
            # BUG-CORTEXTRIGGER-9.12.0-001: this branch is already gated on
            # os.name == "nt", so subprocess.CREATE_NO_WINDOW (Windows-only
            # constant) is always safe to reference here. Without it,
            # manage-bde.exe -- a console-subsystem child -- pops a new
            # visible console when this runs under a console-less detached
            # parent (cortex_trigger.py via script_coordinator.py's
            # _spawn_detached).
            out = subprocess.run(
                ["manage-bde", "-status", "C:"],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            low = out.stdout.lower()
            if "percentage encrypted:  100" in low or "fully encrypted" in low:
                return "on"
            if "fully decrypted" in low or "percentage encrypted:  0" in low:
                return "off"
        elif sys.platform.startswith("linux") and shutil.which("lsblk"):
            out = subprocess.run(["lsblk", "-o", "TYPE"], capture_output=True, text=True, timeout=5)
            if "crypt" in out.stdout:
                return "on"
            # Absence of a 'crypt' row does NOT prove the disk is unencrypted —
            # the device tree may not be visible to lsblk in containers, VMs, or
            # non-root contexts.  Mirror the macOS/Windows fall-through: return
            # 'unknown' rather than 'off' to avoid a false advisory.
            return "unknown"
    except Exception:
        return "unknown"
    return "unknown"


def posture_advisory(data_dir: str | Path) -> dict:
    data_dir = Path(data_dir)
    on_sync = _on_cloud_sync_path(data_dir)
    disk = _disk_encryption_status()
    advice: list[str] = []
    if on_sync:
        advice.append(
            "Cortex data dir is on a cloud-sync path; OS-disk encryption does NOT protect "
            "synced copies. Enable Cortex encryption-at-rest (brain key set) or move data_dir off the synced folder."
        )
    if disk == "off":
        advice.append("OS-disk encryption appears OFF; enable BitLocker/FileVault/dm-crypt as a baseline.")
    return {
        "data_dir": str(data_dir),
        "on_cloud_sync_path": on_sync,
        "disk_encryption": disk,
        "advice": advice,
    }
