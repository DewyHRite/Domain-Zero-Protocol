#!/usr/bin/env python3
"""
Generalized File Rotation Script
Domain Zero Protocol v8.9.0+

Purpose: Automatically archive files when character threshold reached
Supports: dev-notes.md, security-review.md, and other rotating files
Access: All agents (invoke via Gojo for rotation)
"""

import os
import sys
import json
import shutil
import yaml
import argparse
import hashlib
import re
from datetime import datetime
from pathlib import Path

# Default configuration
DEFAULT_CHAR_THRESHOLD = 25000  # 25k characters
DEFAULT_KEEP_ARCHIVES = 10

# Supported files and their configurations
SUPPORTED_FILES = {
    "dev-notes": {
        "path": Path(".protocol-state/dev-notes.md"),
        "archive_dir": Path(".protocol-state/archive/dev-notes"),
        "header_lines": 15,  # Lines to preserve as header
        "access": ["yuuji", "gojo"]
    },
    "security-review": {
        "path": Path(".protocol-state/security-review.md"),
        "archive_dir": Path(".protocol-state/archive/security-review"),
        "header_lines": 12,
        "access": ["megumi", "gojo"]
    }
}


def sanitize_reason(reason: str) -> str:
    """Sanitize reason string to prevent injection attacks (SEC-005)"""
    if not reason or not isinstance(reason, str):
        return "unspecified"
    # Allow only alphanumeric, spaces, underscores, hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9\s_\-]', '', reason)
    # Limit length
    return sanitized[:50] if sanitized else "unspecified"


def validate_path_safety(path: Path, expected_base: Path) -> bool:
    """Validate path doesn't escape expected directory (SEC-005)"""
    try:
        resolved = path.resolve()
        base_resolved = expected_base.resolve()
        return str(resolved).startswith(str(base_resolved))
    except (OSError, ValueError):
        return False


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file for integrity verification (SEC-007)"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError:
        return ""


class FileRotator:
    def __init__(self, file_key: str):
        if file_key not in SUPPORTED_FILES:
            raise ValueError(f"Unsupported file: {file_key}. Supported: {list(SUPPORTED_FILES.keys())}")

        self.file_key = file_key
        self.file_config = SUPPORTED_FILES[file_key]
        self.file_path = self.file_config["path"]
        self.archive_dir = self.file_config["archive_dir"]
        self.metadata_path = self.archive_dir / ".rotation-metadata.json"

        # Security validation (SEC-005): Ensure paths are within expected boundaries
        project_root = Path.cwd()
        if not validate_path_safety(self.file_path, project_root):
            raise ValueError(f"Invalid file path: {self.file_path} - path traversal detected")
        if not validate_path_safety(self.archive_dir, project_root):
            raise ValueError(f"Invalid archive path: {self.archive_dir} - path traversal detected")

        self.config = self._load_config()
        self.metadata = self._load_metadata()

    def _load_config(self):
        """Load rotation config from protocol.config.yaml"""
        config_path = Path("protocol.config.yaml")
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    file_rotation = config.get('file_rotation', {})
                    file_specific = file_rotation.get(self.file_key, {})
                    return {
                        "threshold_chars": file_specific.get('threshold_chars', DEFAULT_CHAR_THRESHOLD),
                        "enabled": file_specific.get('enabled', True),
                        "keep_archives": file_specific.get('keep_archives', DEFAULT_KEEP_ARCHIVES)
                    }
        except (yaml.YAMLError, IOError) as e:
            print(f"[WARN] Failed to load config: {e}")
            print(f"[INFO] Using default configuration")

        return {
            "threshold_chars": DEFAULT_CHAR_THRESHOLD,
            "enabled": True,
            "keep_archives": DEFAULT_KEEP_ARCHIVES
        }

    def _load_metadata(self):
        """Load rotation metadata"""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARN] Failed to load metadata: {e}")

        return {
            "version": "1.0.0",
            "file_key": self.file_key,
            "threshold_chars": DEFAULT_CHAR_THRESHOLD,
            "rotation_enabled": True,
            "last_rotation": None,
            "total_rotations": 0,
            "archives": []
        }

    def _save_metadata(self):
        """Save rotation metadata"""
        try:
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            return True
        except IOError as e:
            print(f"[ERROR] Failed to save metadata: {e}")
            return False

    def check_rotation_needed(self):
        """Check if rotation threshold exceeded"""
        if not self.file_path.exists():
            return False, 0

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                char_count = len(content)
        except IOError as e:
            print(f"[ERROR] Failed to read {self.file_key}: {e}")
            return False, 0

        threshold = self.config["threshold_chars"]
        needs_rotation = char_count >= threshold

        return needs_rotation, char_count

    def _extract_header(self, content: str) -> str:
        """Extract header section to preserve after rotation"""
        lines = content.split('\n')
        header_line_count = self.file_config.get("header_lines", 10)
        header_lines = lines[:header_line_count]
        return '\n'.join(header_lines)

    def rotate(self, reason="threshold"):
        """Archive current file and create fresh file with header preserved"""
        # SEC-005: Sanitize reason input
        safe_reason = sanitize_reason(reason)

        if not self.file_path.exists():
            print(f"[ERROR] {self.file_path} not found - nothing to rotate")
            return False

        # Create archive directory
        try:
            self.archive_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[ERROR] Failed to create archive directory: {e}")
            return False

        # Read current content
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                char_count = len(content)
        except IOError as e:
            print(f"[ERROR] Failed to read file: {e}")
            return False

        # SEC-007: Compute source hash before archiving
        source_hash = compute_file_hash(self.file_path)
        if not source_hash:
            print("[WARN] Could not compute source file hash - proceeding without verification")

        # Extract header for new file
        header = self._extract_header(content)

        # Generate archive filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_name = f"{self.file_key}-{timestamp}.md"
        archive_path = self.archive_dir / archive_name

        # Copy to archive
        try:
            shutil.copy2(self.file_path, archive_path)
        except (IOError, OSError) as e:
            print(f"[ERROR] Failed to create archive: {e}")
            return False

        # SEC-007: Verify archive integrity
        if source_hash:
            archive_hash = compute_file_hash(archive_path)
            if archive_hash != source_hash:
                print(f"[ERROR] Archive integrity check failed!")
                print(f"  Source hash:  {source_hash}")
                print(f"  Archive hash: {archive_hash}")
                try:
                    archive_path.unlink()  # Remove corrupted archive
                except OSError:
                    pass
                return False
            print(f"[OK] Archive integrity verified (SHA-256: {archive_hash[:16]}...)")

        # Update metadata
        self.metadata["last_rotation"] = datetime.now().isoformat()
        self.metadata["total_rotations"] += 1
        self.metadata["archives"].append({
            "date": datetime.now().isoformat(),
            "chars": char_count,
            "archive_file": archive_name,
            "reason": safe_reason,
            "sha256": source_hash if source_hash else "not_computed"
        })

        if not self._save_metadata():
            print("[WARN] Rotation completed but metadata save failed")

        # Clean old archives
        self._cleanup_old_archives()

        # Create fresh file with header + rotation marker
        if not self._create_fresh_file(header):
            print("[ERROR] Failed to create fresh file")
            return False

        print(f"[OK] Rotated {self.file_key} ({char_count} chars) -> {archive_name}")
        return True

    def _cleanup_old_archives(self):
        """Keep only recent archives per config"""
        keep_count = self.config.get("keep_archives", DEFAULT_KEEP_ARCHIVES)

        try:
            pattern = f"{self.file_key}-*.md"
            archives = sorted(self.archive_dir.glob(pattern), key=os.path.getmtime)
        except OSError as e:
            print(f"[WARN] Failed to list archives: {e}")
            return

        if len(archives) > keep_count:
            for old_archive in archives[:-keep_count]:
                try:
                    old_archive.unlink()
                    print(f"[INFO] Deleted old archive: {old_archive.name}")
                except OSError as e:
                    print(f"[WARN] Failed to delete archive {old_archive.name}: {e}")

    def _create_fresh_file(self, header: str):
        """Create fresh file with preserved header + rotation marker"""
        rotation_marker = f"""

---

## ROTATION NOTICE

**File rotated on**: {datetime.now().isoformat()}
**Previous content archived to**: `{self.archive_dir}/`
**Rotation reason**: Threshold exceeded ({self.config['threshold_chars']} chars)

---

## CONTINUE BELOW

"""
        fresh_content = header + rotation_marker

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(fresh_content)
            return True
        except IOError as e:
            print(f"[ERROR] Failed to create fresh file: {e}")
            return False


def list_supported_files():
    """List all supported files for rotation"""
    print("\nSupported files for rotation:")
    print("-" * 50)
    for key, config in SUPPORTED_FILES.items():
        print(f"  {key}:")
        print(f"    Path: {config['path']}")
        print(f"    Archive: {config['archive_dir']}")
        print(f"    Access: {', '.join(config['access'])}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generalized File Rotation for Domain Zero Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python file-rotate.py --list                    # List supported files
  python file-rotate.py --file dev-notes --check  # Check if rotation needed
  python file-rotate.py --file dev-notes --rotate # Force rotation
  python file-rotate.py --file security-review --check
        """
    )
    parser.add_argument('--list', action='store_true', help="List supported files")
    parser.add_argument('--file', type=str, help="File key to rotate (e.g., dev-notes, security-review)")
    parser.add_argument('--check', action='store_true', help="Check if rotation needed")
    parser.add_argument('--rotate', action='store_true', help="Force rotation now")

    args = parser.parse_args()

    if args.list:
        list_supported_files()
        return 0

    if not args.file:
        parser.print_help()
        print("\n[ERROR] --file is required for --check or --rotate")
        return 1

    if args.file not in SUPPORTED_FILES:
        print(f"[ERROR] Unknown file: {args.file}")
        list_supported_files()
        return 1

    try:
        rotator = FileRotator(args.file)
    except ValueError as e:
        print(f"[ERROR] {e}")
        return 1

    if args.check:
        needs_rotation, char_count = rotator.check_rotation_needed()
        threshold = rotator.config["threshold_chars"]
        print(f"[INFO] {args.file}: {char_count:,} / {threshold:,} chars")
        if needs_rotation:
            print(f"[WARN] Rotation needed (threshold exceeded)")
            return 1
        else:
            print(f"[OK] No rotation needed")
            return 0

    elif args.rotate:
        success = rotator.rotate(reason="manual")
        return 0 if success else 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
