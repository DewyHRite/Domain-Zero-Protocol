"""Phase-1 encryption posture advisory (PLAN-CORTEX-ENC-001).
Best-effort, never raises — pure reporting for `brain status`.
"""
from __future__ import annotations
import platform
import shutil
import subprocess
from pathlib import Path

# Reuse the cloud-sync token convention used by paths.py safety checks.
_SYNC_TOKENS = ("onedrive", "dropbox", "google drive", "googledrive", "icloud", "box sync")


def _on_cloud_sync_path(data_dir: Path) -> bool:
    p = str(data_dir).lower()
    return any(tok in p for tok in _SYNC_TOKENS)


def _disk_encryption_status() -> str:
    """Best-effort OS-disk-encryption probe. Returns 'on'|'off'|'unknown'.
    Never raises; 'unknown' is always an acceptable answer."""
    system = platform.system()
    try:
        if system == "Darwin" and shutil.which("fdesetup"):
            out = subprocess.run(["fdesetup", "status"], capture_output=True, text=True, timeout=5)
            if "On" in out.stdout:
                return "on"
            if "Off" in out.stdout:
                return "off"
        elif system == "Windows" and shutil.which("manage-bde"):
            out = subprocess.run(["manage-bde", "-status", "C:"], capture_output=True, text=True, timeout=8)
            low = out.stdout.lower()
            if "percentage encrypted:  100" in low or "fully encrypted" in low:
                return "on"
            if "fully decrypted" in low or "percentage encrypted:  0" in low:
                return "off"
        elif system == "Linux" and shutil.which("lsblk"):
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
