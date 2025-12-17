#!/usr/bin/env python3
"""
Domain Record Auto-Rotation Script
Domain Zero Protocol v8.8.0+

Purpose: Automatically archive domain.record.md when size threshold reached
Access: Gojo + Sukuna ONLY
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

# Configuration
DOMAIN_RECORD_PATH = Path(".dzp-domain/domain.record.md")
ARCHIVE_DIR = Path(".dzp-domain/archive")
METADATA_PATH = Path(".dzp-domain/.rotation-metadata.json")
DEFAULT_THRESHOLD = 5000

class DomainRecordRotator:
    def __init__(self):
        self.config = self._load_config()
        self.metadata = self._load_metadata()

    def _load_config(self):
        """Load rotation config from protocol.config.yaml"""
        # Simplified - in production, parse YAML
        return {
            "threshold_lines": DEFAULT_THRESHOLD,
            "enabled": True,
            "keep_archives": 10
        }

    def _load_metadata(self):
        """Load rotation metadata"""
        if METADATA_PATH.exists():
            with open(METADATA_PATH, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0.0",
            "rotation_threshold": DEFAULT_THRESHOLD,
            "rotation_enabled": True,
            "last_rotation": None,
            "total_rotations": 0,
            "archives": []
        }

    def _save_metadata(self):
        """Save rotation metadata"""
        METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(METADATA_PATH, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def check_rotation_needed(self):
        """Check if rotation threshold exceeded"""
        if not DOMAIN_RECORD_PATH.exists():
            return False, 0

        with open(DOMAIN_RECORD_PATH, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)

        threshold = self.config["threshold_lines"]
        needs_rotation = line_count >= threshold

        return needs_rotation, line_count

    def rotate(self, reason="threshold"):
        """Archive current domain.record.md and create fresh file"""
        if not DOMAIN_RECORD_PATH.exists():
            print("[ERROR] domain.record.md not found - nothing to rotate")
            return False

        # Create archive directory
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Generate archive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"domain.record_{timestamp}.md"
        archive_path = ARCHIVE_DIR / archive_name

        # Count lines before archiving
        with open(DOMAIN_RECORD_PATH, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)

        # Copy to archive
        shutil.copy2(DOMAIN_RECORD_PATH, archive_path)

        # Update metadata
        self.metadata["last_rotation"] = datetime.now().isoformat()
        self.metadata["total_rotations"] += 1
        self.metadata["archives"].append({
            "date": datetime.now().isoformat(),
            "lines": line_count,
            "archive_file": archive_name,
            "reason": reason
        })
        self._save_metadata()

        # Clean old archives
        self._cleanup_old_archives()

        # Create fresh domain.record.md
        self._create_fresh_record()

        print(f"[OK] Rotated domain.record.md ({line_count} lines) -> {archive_name}")
        return True

    def _cleanup_old_archives(self):
        """Keep only recent archives per config"""
        keep_count = self.config.get("keep_archives", 10)
        archives = sorted(ARCHIVE_DIR.glob("domain.record_*.md"), key=os.path.getmtime)

        if len(archives) > keep_count:
            for old_archive in archives[:-keep_count]:
                old_archive.unlink()
                print(f"[INFO] Deleted old archive: {old_archive.name}")

    def _create_fresh_record(self):
        """Create fresh domain.record.md with template"""
        template = '''# Domain Record - Mission Control & System Adversary Notes
<!-- [INTERNAL] - Domain Zero Protocol v8.8.0 -->
<!-- ACCESS: Gojo + Sukuna ONLY -->

**Rotation Date**: {date}
**Previous Archive**: See `.dzp-domain/archive/`

---

## 🎯 CURRENT SESSION

### Session Notes

[Append new session notes here]

---

## 📋 STRATEGIC DECISIONS LOG

### Recent Decisions

[Append strategic decisions here]

---

## 🔄 PROTOCOL UPDATE TRACKING

### Update History

[Append protocol updates here]

---

## 🧠 LEARNING PATTERNS & INSIGHTS

### Insights

[Append learning patterns here]

---

## 🚨 CRASH RECOVERY CHECKPOINT

### Recovery Context

[Update crash recovery context here]

---

**End of Domain Record**
'''.format(date=datetime.now().isoformat())

        with open(DOMAIN_RECORD_PATH, 'w', encoding='utf-8') as f:
            f.write(template)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Domain Record Rotation")
    parser.add_argument('--check', action='store_true', help="Check if rotation needed")
    parser.add_argument('--rotate', action='store_true', help="Force rotation now")
    args = parser.parse_args()

    rotator = DomainRecordRotator()

    if args.check:
        needs_rotation, line_count = rotator.check_rotation_needed()
        threshold = rotator.config["threshold_lines"]
        print(f"[INFO] Domain Record: {line_count} / {threshold} lines")
        if needs_rotation:
            print(f"[WARN] Rotation needed (threshold exceeded)")
            return 1
        else:
            print(f"[OK] No rotation needed")
            return 0

    elif args.rotate:
        rotator.rotate(reason="manual")
        return 0

    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    exit(main())
