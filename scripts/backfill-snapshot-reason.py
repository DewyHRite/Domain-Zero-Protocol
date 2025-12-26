#!/usr/bin/env python3
"""
Backfill 'reason' field in snapshot files for PATCH-COMP-001 compliance.
Domain Zero Protocol v8.10.0
"""

import gzip
import json
from pathlib import Path

# Snapshot directory
SNAPSHOT_DIR = Path('.protocol-state/snapshots')

# Find all snapshot files from 2025-12-06
snapshot_files = list(SNAPSHOT_DIR.glob('snapshot-2025-12-06T*.json.gz'))

print(f"Found {len(snapshot_files)} snapshot files to process\n")

updated_count = 0
error_count = 0

for snapshot_file in snapshot_files:
    try:
        # Read compressed snapshot
        with gzip.open(snapshot_file, 'rt', encoding='utf-8') as f:
            data = json.load(f)

        # Check if 'reason' field already exists
        if 'reason' in data:
            print(f"[OK] {snapshot_file.name}: Already has 'reason' field ({data['reason']})")
            continue

        # Get reason from 'trigger' field (all snapshots have 'trigger': 'manual')
        reason = data.get('trigger', 'manual')

        # Add 'reason' field
        data['reason'] = reason

        # Write back compressed
        with gzip.open(snapshot_file, 'wt', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"[UPDATED] {snapshot_file.name}: Added reason='{reason}'")
        updated_count += 1

    except Exception as e:
        print(f"[ERROR] {snapshot_file.name}: ERROR - {e}")
        error_count += 1

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Updated: {updated_count}")
print(f"  Errors: {error_count}")
print(f"  Total: {len(snapshot_files)}")
print(f"{'='*60}")

if updated_count > 0:
    print(f"\n[SUCCESS] Backfill complete! Run validation to verify:")
    print(f"   python scripts/validate-protocol.py --check")
