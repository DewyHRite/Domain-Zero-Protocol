#!/usr/bin/env python3
"""
Domain Zero Protocol - Template Syncing
Syncs .template.* and .example.* files to working locations
"""

import shutil
from pathlib import Path

def sync_templates():
    """Sync .template.* and .example.* files to working locations"""

    templates = [
        # (source, destination, create_if_missing)
        ('.protocol-state/session-state.example.json',
         '.protocol-state/session-state.json', False),  # Created by session_monitor.py

        ('.protocol-state/custom-agent-registry.example.json',
         '.protocol-state/custom-agent-registry.json', True),

        ('.protocol-state/system-update-framework/backup-manifest.template.json',
         '.protocol-state/system-update-framework/backup-manifest.json', True),

        ('.protocol-state/system-update-framework/file-classifications.template.json',
         '.protocol-state/system-update-framework/file-classifications.json', True),

        ('.protocol-state/system-update-framework/version-registry.template.json',
         '.protocol-state/system-update-framework/version-registry.json', True),
    ]

    print("=" * 70)
    print("DOMAIN ZERO PROTOCOL - TEMPLATE SYNCING")
    print("=" * 70)
    print()

    synced_count = 0
    skipped_count = 0
    missing_count = 0
    intentionally_skipped = 0

    for src, dst, create in templates:
        src_path = Path(src)
        dst_path = Path(dst)

        # Check if source template exists
        if not src_path.exists():
            print(f"[WARN] Template missing: {src}")
            missing_count += 1
            continue

        # If destination already exists, skip (regardless of create flag)
        if dst_path.exists():
            print(f"[OK] Already exists (skipping): {dst}")
            skipped_count += 1
            continue

        # Destination doesn't exist
        if not create:
            # Intentionally not creating (e.g., session-state.json created by session_monitor.py)
            print(f"[INFO] Not created by design: {dst} (created by {Path(src).stem} process)")
            intentionally_skipped += 1
            continue

        # Create the destination file
        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)
        print(f"[OK] Synced: {src} -> {dst}")
        synced_count += 1

    print()
    print("=" * 70)
    print(f"SUMMARY: {synced_count} synced, {skipped_count} already exist, {intentionally_skipped} not created by design, {missing_count} missing")
    print("=" * 70)

    if missing_count > 0:
        print()
        print("[WARN] Some templates are missing. Check installation completeness.")
        print("Run: python scripts/verify-installation.py")
        return 1

    if synced_count == 0 and skipped_count > 0:
        print()
        print("[OK] All templates already synced - no action needed")
        return 0

    print()
    print("[OK] Template syncing complete")
    return 0

if __name__ == '__main__':
    import sys
    exit_code = sync_templates()
    sys.exit(exit_code)
