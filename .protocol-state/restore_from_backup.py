#!/usr/bin/env python3
"""
Sukuna Rollback: Restore files from script modernization backup
"""
from pathlib import Path
import shutil

backup_dir = Path('.protocol-state/backups/script-modernization_20260105_231609/')
project_root = Path('.')

# Read backup manifest
manifest_file = backup_dir / 'backup-manifest.txt'
with open(manifest_file, 'r', encoding='utf-8') as f:
    # Skip header lines (lines 1-7)
    lines = f.readlines()[7:]
    backed_up_files = [line.strip() for line in lines if line.strip()]

restored_count = 0
skipped_count = 0
error_count = 0

print("=" * 60)
print("SUKUNA PRECISION REVERT: Restoring from Backup")
print("=" * 60)
print()

for file_path in backed_up_files:
    # Skip troubleshooting_tracker.py (already restored from git)
    if 'troubleshooting_tracker.py' in file_path:
        print(f"[SKIP] {file_path} (restored from git)")
        skipped_count += 1
        continue

    source = backup_dir / file_path
    target = project_root / file_path

    if source.exists():
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            restored_count += 1
            print(f"[OK] Restored: {file_path}")
        except Exception as e:
            error_count += 1
            print(f"[ERROR] Failed to restore {file_path}: {e}")
    else:
        error_count += 1
        print(f"[ERROR] Missing backup: {file_path}")

print()
print("=" * 60)
print(f"RESTORATION COMPLETE")
print("=" * 60)
print(f"Restored: {restored_count} files")
print(f"Skipped (git restore): {skipped_count} files")
print(f"Errors: {error_count} files")
print()

if error_count > 0:
    print("[WARNING] Some files failed to restore. Review errors above.")
    exit(1)
else:
    print("[SUCCESS] All files restored successfully")
    exit(0)
