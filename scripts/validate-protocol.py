#!/usr/bin/env python3
"""
Domain Zero Protocol - State File Validation Engine

Version: 1.0.0
Created: 2025-12-05
Part of: DZP v8.8.0 Validation Framework

This script validates Domain Zero Protocol state files against JSON schemas
defined in protocol/validation-rules.yaml.

Features:
- JSON Schema validation for 5 state file types
- SHA-256 checksum verification for drift detection
- Confidence-based auto-fix engine (HIGH auto-applies, MEDIUM prompts, LOW skips)
- Detailed validation reporting (Markdown/JSON)
- CLI with multiple flags
- Exit codes: 0 (pass), 1 (warnings), 2 (errors), 3 (critical)

Usage:
    python scripts/validate-protocol.py --check               # Basic validation
    python scripts/validate-protocol.py --check --verbose     # Verbose output
    python scripts/validate-protocol.py --fix                # Apply auto-fixes
    python scripts/validate-protocol.py --fix --preview       # Preview fixes (dry-run)
    python scripts/validate-protocol.py --report              # Generate Markdown report
    python scripts/validate-protocol.py --file <path>         # Validate specific file
"""

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(3)

try:
    import jsonschema
    from jsonschema import Draft7Validator, validators
except ImportError:
    # BUG-VALIDATE-002 (v9.3.0): jsonschema (+PyYAML) are declared in requirements-dev.txt
    print("ERROR: jsonschema is required. Install with: pip install -r requirements-dev.txt "
          "(or: pip install jsonschema)", file=sys.stderr)
    sys.exit(3)


# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_FILE = PROJECT_ROOT / "protocol" / "validation-rules.yaml"
STATE_DIR = PROJECT_ROOT / ".protocol-state"
VALIDATION_STATE_FILE = STATE_DIR / "validation" / "validation-state.json"

# FEAT-IDGOV-001 Phase G3: issue-id registry JSONL (module constant, mirrors
# VALIDATION_STATE_FILE's shape so tests can monkeypatch it the same way --
# see tests/test_validate_protocol_issue_registry.py).
ISSUE_REGISTRY_FILE = STATE_DIR / "issue-registry.jsonl"

# ISS-083: local write-attestation (fail-soft; module lives in .protocol-state/,
# alongside project_state_manager.py / session_monitor.py, the sanctioned
# writers this check consults). Absence must never break --check.
#
# CodeRabbit PR#108: loaded directly from its known file path via
# importlib.util (rather than mutating sys.path + `import attestation`).
# A persistent `sys.path.insert(0, str(STATE_DIR))` puts the WHOLE
# .protocol-state/ directory on the import path for the rest of the
# process -- every other top-level module living there (session_monitor,
# project_state_manager, migrate_state_9x, etc.) becomes importable by bare
# name too, which is a broader and longer-lived surface than this file
# needs just to reach one sibling module. Mirrors the existing hyphenated-
# module load shim used elsewhere in this repo (e.g.
# .protocol-state/restore-snapshot.py's `create_snapshot` import,
# tests/test_state_write_attestation.py's `_load_create_snapshot_module`).
_attestation = None
_ATTESTATION_AVAILABLE = False
_ATTESTATION_MODULE_NAME = "dzp_attestation_module"
try:
    _attestation_spec = importlib.util.spec_from_file_location(
        _ATTESTATION_MODULE_NAME, STATE_DIR / "attestation.py"
    )
    if _attestation_spec is not None and _attestation_spec.loader is not None:
        _attestation = importlib.util.module_from_spec(_attestation_spec)
        # Register in sys.modules BEFORE exec: attestation.py's
        # AttestationCheck @dataclass needs `sys.modules[cls.__module__]` to
        # resolve during class creation (CPython 3.10+ dataclasses internals
        # look the defining module up there) -- executing an unregistered
        # module raises AttributeError on that lookup.
        sys.modules[_ATTESTATION_MODULE_NAME] = _attestation
        _attestation_spec.loader.exec_module(_attestation)
        _ATTESTATION_AVAILABLE = True
except (ImportError, OSError, SyntaxError):
    sys.modules.pop(_ATTESTATION_MODULE_NAME, None)
    _attestation = None
    _ATTESTATION_AVAILABLE = False


class ExitCode(Enum):
    """Exit codes for validation script"""
    SUCCESS = 0          # Validation passed (no errors)
    WARNINGS = 1         # Warnings only (usable but needs improvement)
    ERRORS = 2           # Errors detected (needs fixing)
    CRITICAL = 3         # Critical failure (cannot validate)


class FixConfidence(Enum):
    """Confidence levels for auto-fix suggestions"""
    HIGH = "HIGH"        # Auto-apply (safe fixes)
    MEDIUM = "MEDIUM"    # Prompt user
    LOW = "LOW"          # Skip (too risky)


class ValidationStatus(Enum):
    """Validation status for individual files"""
    VALID = "valid"
    INVALID = "invalid"
    DRIFT_DETECTED = "drift_detected"
    MISSING = "missing"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StateFile:
    """Represents a DZP state file to be validated"""
    path: Path
    schema_name: str
    exists: bool = True
    content: Optional[Dict[str, Any]] = None


@dataclass
class ValidationError:
    """Represents a validation error"""
    file: str
    error_type: str
    message: str
    path: str = ""
    severity: str = "error"  # error, warning, critical


@dataclass
class DriftAlert:
    """Represents a drift detection event"""
    file: str
    detected_at: str
    changes: List[str]
    severity: str = "medium"


@dataclass
class AutoFix:
    """Represents an auto-fix suggestion"""
    fix_id: str
    file: str
    fix_type: str
    description: str
    confidence: FixConfidence
    current_value: Any
    proposed_value: Any
    applied: bool = False
    user_approved: Optional[bool] = None


@dataclass
class ValidationResult:
    """Results from validating a single file"""
    file: str
    schema: str
    status: ValidationStatus
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    drift_detected: bool = False
    auto_fixes: List[AutoFix] = field(default_factory=list)
    # ISS-083: seq accepted this run via a valid write-attestation (None when
    # no attestation was consulted/accepted this run -- update_validation_state()
    # carries the prior persisted value forward in that case).
    attested_seq: Optional[int] = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    timestamp: str
    total_files: int
    files_validated: int
    files_passed: int
    files_failed: int
    files_missing: int
    total_errors: int
    total_warnings: int
    drift_alerts: List[DriftAlert]
    results: List[ValidationResult]
    exit_code: ExitCode


# =============================================================================
# File Discovery
# =============================================================================

def discover_state_files(root_dir: Path) -> List[StateFile]:
    """
    Find all DZP state files in .protocol-state/ directory

    Returns:
        List of StateFile objects to be validated
    """
    state_files = []
    state_dir = root_dir / ".protocol-state"

    # File-to-schema mappings from validation-rules.yaml metadata
    file_mappings = {
        "project-state.json": "project-state",
        "session-state.json": "session-state",
        "validation/validation-state.json": "validation-state",
        "snapshots/snapshot-manifest.json": "snapshot-manifest",
    }

    for file_path, schema_name in file_mappings.items():
        full_path = state_dir / file_path
        exists = full_path.exists()

        content = None
        if exists:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # File exists but can't be read - will be caught during validation
                pass

        state_files.append(StateFile(
            path=full_path,
            schema_name=schema_name,
            exists=exists,
            content=content
        ))

    # Discover snapshot files (snapshot-*.json.gz pattern)
    snapshots_dir = state_dir / "snapshots"
    if snapshots_dir.exists():
        for snapshot_file in snapshots_dir.glob("snapshot-*.json.gz"):
            try:
                with gzip.open(snapshot_file, 'rt', encoding='utf-8') as f:
                    content = json.load(f)
                state_files.append(StateFile(
                    path=snapshot_file,
                    schema_name="snapshot",
                    exists=True,
                    content=content
                ))
            except (json.JSONDecodeError, IOError):
                # Skip malformed snapshot files
                pass

    return state_files


# =============================================================================
# Schema Loading
# =============================================================================

def load_schemas(schema_file: Path) -> Dict[str, Any]:
    """
    Load validation-rules.yaml and parse JSON schemas

    Args:
        schema_file: Path to validation-rules.yaml

    Returns:
        Dictionary mapping schema names to JSON schema objects

    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If schema file is malformed
    """
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(schema_file, 'r', encoding='utf-8') as f:
        rules = yaml.safe_load(f)

    if 'schemas' not in rules:
        raise ValueError("Invalid schema file: missing 'schemas' key")

    return rules['schemas']


# =============================================================================
# Validation Engine
# =============================================================================

def validate_file(state_file: StateFile, schema: Any) -> ValidationResult:
    """
    Validate a single state file against its JSON schema

    Args:
        state_file: StateFile object containing path and content
        schema: JSON schema definition

    Returns:
        ValidationResult with errors, warnings, and status
    """
    result = ValidationResult(
        file=str(state_file.path.relative_to(PROJECT_ROOT)),
        schema=state_file.schema_name,
        status=ValidationStatus.VALID
    )

    # Check if file exists
    if not state_file.exists:
        result.status = ValidationStatus.MISSING
        result.errors.append(ValidationError(
            file=result.file,
            error_type="missing_file",
            message=f"State file does not exist: {state_file.path}",
            severity="critical"
        ))
        return result

    # Check if file is readable JSON
    if state_file.content is None:
        try:
            with open(state_file.path, 'r', encoding='utf-8') as f:
                state_file.content = json.load(f)
        except json.JSONDecodeError as e:
            result.status = ValidationStatus.INVALID
            result.errors.append(ValidationError(
                file=result.file,
                error_type="json_decode_error",
                message=f"Invalid JSON: {e}",
                severity="critical"
            ))
            return result
        except IOError as e:
            result.status = ValidationStatus.INVALID
            result.errors.append(ValidationError(
                file=result.file,
                error_type="read_error",
                message=f"Cannot read file: {e}",
                severity="critical"
            ))
            return result

    # Validate against JSON schema
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(state_file.content), key=lambda e: e.path)

    for error in errors:
        path = ".".join(str(p) for p in error.path) if error.path else "root"

        result.errors.append(ValidationError(
            file=result.file,
            error_type=error.validator,
            message=error.message,
            path=path,
            severity="error"
        ))

    # Calculate checksum for drift detection
    result.checksum = calculate_checksum(state_file.path)

    # Set status based on errors
    if result.errors:
        result.status = ValidationStatus.INVALID

    return result


def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of file contents

    Args:
        file_path: Path to file

    Returns:
        Hex string of SHA-256 checksum
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


# =============================================================================
# Drift Detection
# =============================================================================

def detect_drift(
    current_results: List[ValidationResult],
    last_validation_state: Optional[Dict[str, Any]],
    state_dir: Path = STATE_DIR,
) -> List[DriftAlert]:
    """
    Detect unauthorized changes since last validation by comparing checksums

    Args:
        current_results: Current validation results with checksums
        last_validation_state: Previous validation state from validation-state.json
        state_dir: The `.protocol-state` directory (attestation ledger + key
            location). Defaults to the real STATE_DIR; overridable for tests.

    Returns:
        List of DriftAlert objects for files with detected drift

    ISS-083 (authorized-writer attestation): before raising a drift alert for
    a checksum mismatch, consult the local attestation ledger. A valid,
    non-stale attestation for the file's CURRENT content -- with a seq
    strictly greater than the last seq this checker has already accepted for
    that file -- proves the change came from a sanctioned writer holding the
    local HMAC key, and the alert is suppressed for this run (the new
    checksum becomes the baseline via update_validation_state(), same as
    today). A missing/invalid/stale/replayed attestation still raises the
    alert exactly as before: this is fail-closed for anything that looks
    like tamper, and fail-soft (identical to pre-ISS-083 behavior) when the
    attestation infrastructure itself is absent.
    """
    drift_alerts = []

    if last_validation_state is None:
        return drift_alerts

    # Get previous file integrity data
    integrity_data = last_validation_state.get('state_file_integrity', {})

    for result in current_results:
        if result.status == ValidationStatus.MISSING:
            continue

        file_key = Path(result.file).name
        # The validation-state file IS the integrity baseline store. Its own checksum
        # is recorded by update_validation_state() *before* the new state is written,
        # so after the write the file no longer matches its stored hash — producing a
        # perpetual, unfixable self-drift alert. Exclude it from drift detection
        # (it cannot meaningfully checksum itself).
        if file_key == "validation-state.json":
            continue
        previous = integrity_data.get(file_key, {})
        previous_checksum = previous.get('checksum')

        if previous_checksum and result.checksum != previous_checksum:
            # Checksum changed since last run -- candidate drift. Consult the
            # attestation ledger before alerting.
            if _ATTESTATION_AVAILABLE:
                check = _attestation.verify_current_content(state_dir, file_key, result.checksum)
                if check.attested and check.seq is not None:
                    try:
                        previous_seq = int(previous.get('attested_seq', 0) or 0)
                    except (TypeError, ValueError):
                        previous_seq = 0
                    if check.seq > previous_seq:
                        # Authorized, non-replayed write: accept as the new
                        # baseline, suppress the alert, and remember the seq
                        # so a replay of this same (or older) attestation is
                        # rejected on a future run.
                        result.attested_seq = check.seq
                        continue
                    # else: seq did not advance -- replay. Fall through to alert.

            drift_alerts.append(DriftAlert(
                file=result.file,
                detected_at=datetime.now(timezone.utc).isoformat() + 'Z',
                changes=["checksum_mismatch"],
                severity="medium"
            ))
            result.drift_detected = True
            result.status = ValidationStatus.DRIFT_DETECTED

    return drift_alerts


# =============================================================================
# Auto-Fix Engine
# =============================================================================

def generate_auto_fixes(validation_results: List[ValidationResult]) -> List[AutoFix]:
    """
    Generate auto-fix suggestions for common validation errors

    Args:
        validation_results: List of validation results with errors

    Returns:
        List of AutoFix suggestions with confidence levels

    Note: Original plan specifies HIGH auto-applies, MEDIUM prompts, LOW skips
    """
    auto_fixes = []
    fix_id_counter = 0

    for result in validation_results:
        for error in result.errors:
            fix = None
            fix_id_counter += 1

            # HIGH confidence fixes - Safe, auto-apply
            if error.error_type == "required" and "tier_usage_statistics" in error.path:
                # Missing tier statistics - can safely initialize to 0
                fix = AutoFix(
                    fix_id=f"fix-{fix_id_counter:04d}",
                    file=result.file,
                    fix_type="add_missing_required_field",
                    description=f"Initialize missing field '{error.path}' with default value",
                    confidence=FixConfidence.HIGH,
                    current_value=None,
                    proposed_value={"tier_1_tasks": 0, "tier_2_tasks": 0, "tier_3_tasks": 0}
                )

            elif error.error_type == "type" and "timestamp" in error.path.lower():
                # Type mismatch on timestamp - can safely add current timestamp
                fix = AutoFix(
                    fix_id=f"fix-{fix_id_counter:04d}",
                    file=result.file,
                    fix_type="fix_type_mismatch",
                    description=f"Fix timestamp type mismatch at '{error.path}'",
                    confidence=FixConfidence.HIGH,
                    current_value="<invalid>",
                    proposed_value=datetime.now(timezone.utc).isoformat() + 'Z'
                )

            # MEDIUM confidence fixes - Require user approval
            elif error.error_type == "required":
                # Missing required field - but not sure what value to use
                fix = AutoFix(
                    fix_id=f"fix-{fix_id_counter:04d}",
                    file=result.file,
                    fix_type="add_missing_required_field",
                    description=f"Add missing required field '{error.path}'",
                    confidence=FixConfidence.MEDIUM,
                    current_value=None,
                    proposed_value="<user_must_provide>"
                )

            elif error.error_type == "enum":
                # Invalid enum value - might have valid alternatives
                fix = AutoFix(
                    fix_id=f"fix-{fix_id_counter:04d}",
                    file=result.file,
                    fix_type="fix_enum_violation",
                    description=f"Fix invalid enum value at '{error.path}'",
                    confidence=FixConfidence.MEDIUM,
                    current_value="<invalid>",
                    proposed_value="<needs_user_selection>"
                )

            # LOW confidence fixes - Too risky, skip
            elif error.error_type == "additionalProperties":
                # Extra properties - deleting data is risky
                fix = AutoFix(
                    fix_id=f"fix-{fix_id_counter:04d}",
                    file=result.file,
                    fix_type="remove_additional_property",
                    description=f"Remove unexpected property at '{error.path}'",
                    confidence=FixConfidence.LOW,
                    current_value="<unknown>",
                    proposed_value=None
                )

            if fix:
                auto_fixes.append(fix)
                result.auto_fixes.append(fix)

    return auto_fixes


def apply_auto_fixes(auto_fixes: List[AutoFix], preview_only: bool = False, ci_mode: bool = False) -> int:
    """
    Apply auto-fixes based on confidence level

    Args:
        auto_fixes: List of AutoFix objects
        preview_only: If True, only show what would be fixed (dry-run)
        ci_mode: If True, skip interactive prompts (auto-skip MEDIUM confidence)

    Returns:
        Number of fixes applied

    Note: HIGH auto-applies, MEDIUM prompts (or skips in CI mode), LOW skips
    """
    applied_count = 0

    for fix in auto_fixes:
        if fix.confidence == FixConfidence.HIGH:
            # HIGH confidence - auto-apply
            if preview_only:
                print(f"[PREVIEW] Would auto-apply: {fix.description}")
            else:
                print(f"[AUTO-FIX] Applying: {fix.description}")
                # TODO: Implement actual fix application
                fix.applied = True
                applied_count += 1

        elif fix.confidence == FixConfidence.MEDIUM:
            # MEDIUM confidence - prompt user (or skip in CI mode)
            if preview_only:
                print(f"[PREVIEW] Would prompt for: {fix.description}")
            elif ci_mode:
                # CI mode: auto-skip MEDIUM confidence fixes (no prompts)
                print(f"\n[MEDIUM CONFIDENCE FIX - SKIPPED IN CI MODE]")
                print(f"  File: {fix.file}")
                print(f"  Fix: {fix.description}")
                print(f"  [SKIPPED - run without --ci-mode to prompt]")
                fix.user_approved = False
            else:
                # Interactive mode: prompt user
                print(f"\n[MEDIUM CONFIDENCE FIX]")
                print(f"  File: {fix.file}")
                print(f"  Fix: {fix.description}")
                print(f"  Current: {fix.current_value}")
                print(f"  Proposed: {fix.proposed_value}")

                response = input("  Apply this fix? (y/N): ").strip().lower()
                if response == 'y':
                    print("  [APPLYING FIX]")
                    # TODO: Implement actual fix application
                    fix.applied = True
                    fix.user_approved = True
                    applied_count += 1
                else:
                    print("  [SKIPPED]")
                    fix.user_approved = False

        elif fix.confidence == FixConfidence.LOW:
            # LOW confidence - skip (too risky)
            if preview_only:
                print(f"[PREVIEW] Would skip (LOW confidence): {fix.description}")
            else:
                print(f"[SKIP] LOW confidence fix: {fix.description}")
            fix.applied = False

    return applied_count


# =============================================================================
# Validation State Management
# =============================================================================

def load_validation_state() -> Optional[Dict[str, Any]]:
    """
    Load existing validation state from validation-state.json

    Returns:
        Validation state dict, or None if file doesn't exist
    """
    if not VALIDATION_STATE_FILE.exists():
        return None

    try:
        with open(VALIDATION_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def update_validation_state(results: List[ValidationResult], auto_fixes: List[AutoFix]) -> None:
    """
    Update validation-state.json after validation run

    Args:
        results: Validation results
        auto_fixes: Auto-fixes that were applied
    """
    # Ensure validation directory exists
    VALIDATION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    state = load_validation_state() or {
        "validation_enabled": True,
        "last_full_validation": None,
        "last_validation_result": "not_run",
        "state_file_integrity": {},
        "drift_alerts": [],
        "auto_fix_history": []
    }

    # Update validation metadata
    state["last_full_validation"] = datetime.now(timezone.utc).isoformat() + 'Z'
    state["last_validation_result"] = "passed" if all(r.status == ValidationStatus.VALID for r in results) else "failed"

    # Update file integrity checksums
    for result in results:
        if result.checksum:
            file_key = Path(result.file).name
            entry = {
                "checksum": result.checksum,
                "last_validated": datetime.now(timezone.utc).isoformat() + 'Z',
                "status": result.status.value,
                "errors": [e.message for e in result.errors[:5]]  # Store first 5 errors
            }

            # ISS-083: persist the attested seq we've accepted for this file
            # (if any) so future runs can detect replay -- a stamp whose seq
            # does not exceed this value is rejected even if it is otherwise
            # a validly-signed, content-matching attestation. Carry the prior
            # value forward when this run didn't consult/accept a new one
            # (unchanged checksum, or an unattested/rejected mismatch).
            prior_entry = state["state_file_integrity"].get(file_key, {})
            if result.attested_seq is not None:
                entry["attested_seq"] = result.attested_seq
            elif "attested_seq" in prior_entry:
                entry["attested_seq"] = prior_entry["attested_seq"]

            state["state_file_integrity"][file_key] = entry

    # Add auto-fix history
    for fix in auto_fixes:
        if fix.applied:
            state["auto_fix_history"].append({
                "fix_id": fix.fix_id,
                "timestamp": datetime.now(timezone.utc).isoformat() + 'Z',
                "file": fix.file,
                "fix_type": fix.fix_type,
                "confidence": fix.confidence.value,
                "applied": fix.applied,
                "user_approved": fix.user_approved,
                "description": fix.description
            })

    # Save updated state
    with open(VALIDATION_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


# =============================================================================
# Reporting
# =============================================================================

def generate_report(results: List[ValidationResult], drift_alerts: List[DriftAlert], auto_fixes: List[AutoFix], output_format: str = "markdown") -> ValidationReport:
    """
    Generate comprehensive validation report

    Args:
        results: List of validation results
        drift_alerts: List of drift detection alerts
        auto_fixes: List of auto-fix suggestions
        output_format: "markdown" or "json"

    Returns:
        ValidationReport object
    """
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)

    files_passed = sum(1 for r in results if r.status == ValidationStatus.VALID)
    files_failed = sum(1 for r in results if r.status == ValidationStatus.INVALID)
    files_missing = sum(1 for r in results if r.status == ValidationStatus.MISSING)

    # Determine exit code
    # BUG-VALIDATE-001 (v9.3.0): never report SUCCESS when nothing was actually
    # validated - an empty result set means "couldn't check", not "passed".
    if any(e.severity == "critical" for r in results for e in r.errors):
        exit_code = ExitCode.CRITICAL
    elif files_failed > 0 or total_errors > 0:
        exit_code = ExitCode.ERRORS
    elif total_warnings > 0:
        exit_code = ExitCode.WARNINGS
    elif (len(results) - files_missing) == 0:
        # No files were validated (none discovered, or all skipped/missing)
        exit_code = ExitCode.WARNINGS
    else:
        exit_code = ExitCode.SUCCESS

    report = ValidationReport(
        timestamp=datetime.now(timezone.utc).isoformat() + 'Z',
        total_files=len(results),
        files_validated=len(results) - files_missing,
        files_passed=files_passed,
        files_failed=files_failed,
        files_missing=files_missing,
        total_errors=total_errors,
        total_warnings=total_warnings,
        drift_alerts=drift_alerts,
        results=results,
        exit_code=exit_code
    )

    return report


def print_report_markdown(report: ValidationReport) -> None:
    """Print validation report in Markdown format to stdout"""
    print("\n# Domain Zero Protocol - Validation Report")
    print(f"\n**Generated**: {report.timestamp}")
    print(f"**Status**: {report.exit_code.name}")
    print("\n## Summary")
    print(f"\n- **Total Files**: {report.total_files}")
    print(f"- **Files Validated**: {report.files_validated}")
    print(f"- **Passed**: {report.files_passed}")
    print(f"- **Failed**: {report.files_failed}")
    print(f"- **Missing**: {report.files_missing}")
    print(f"- **Total Errors**: {report.total_errors}")
    print(f"- **Total Warnings**: {report.total_warnings}")

    if report.drift_alerts:
        print("\n## Drift Alerts")
        for alert in report.drift_alerts:
            print(f"\n- **File**: `{alert.file}`")
            print(f"  - **Detected**: {alert.detected_at}")
            print(f"  - **Severity**: {alert.severity}")
            print(f"  - **Changes**: {', '.join(alert.changes)}")

    print("\n## Validation Details")
    for result in report.results:
        # Use ASCII-safe status indicators for cross-platform compatibility
        status_icon = {
            ValidationStatus.VALID: "[OK]",
            ValidationStatus.INVALID: "[ERROR]",
            ValidationStatus.DRIFT_DETECTED: "[DRIFT]",
            ValidationStatus.MISSING: "[MISSING]"
        }.get(result.status, "[?]")

        print(f"\n### {status_icon} `{result.file}`")
        print(f"**Schema**: {result.schema}")
        print(f"**Status**: {result.status.value}")

        if result.errors:
            print(f"\n**Errors**: {len(result.errors)}")
            for error in result.errors[:10]:  # Show first 10 errors
                path_info = f" at `{error.path}`" if error.path else ""
                print(f"- [{error.severity.upper()}] {error.error_type}{path_info}: {error.message}")

            if len(result.errors) > 10:
                print(f"- ... and {len(result.errors) - 10} more errors")

        if result.drift_detected:
            print("\n**[DRIFT] Drift Detected**: File changed since last validation")

    print("\n---\n")


def print_report_summary(report: ValidationReport) -> None:
    """Print brief validation summary to stdout"""
    # Use ASCII-safe status indicators for cross-platform compatibility
    status_icon = {
        ExitCode.SUCCESS: "[OK]",
        ExitCode.WARNINGS: "[WARN]",
        ExitCode.ERRORS: "[ERROR]",
        ExitCode.CRITICAL: "[CRITICAL]"
    }.get(report.exit_code, "[?]")

    print(f"\n{status_icon} Validation {report.exit_code.name}")
    print(f"   {report.files_passed}/{report.files_validated} files passed")

    if report.total_errors > 0:
        print(f"   {report.total_errors} error(s) found")
    if report.total_warnings > 0:
        print(f"   {report.total_warnings} warning(s) found")
    if report.drift_alerts:
        print(f"   {len(report.drift_alerts)} drift alert(s)")

    print()


# =============================================================================
# Domain Record Validation (v8.8.0+)
# =============================================================================

def validate_domain_record() -> bool:
    """Validate domain record integrity and size"""
    domain_record = PROJECT_ROOT / ".dzp-domain" / "domain.record.md"
    config_file = PROJECT_ROOT / "protocol.config.yaml"

    # Load threshold from config
    default_threshold = 5000
    threshold = default_threshold

    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                domain_config = config.get('domain_record', {})
                rotation_config = domain_config.get('rotation', {})
                threshold = rotation_config.get('threshold_lines', default_threshold)
    except (yaml.YAMLError, IOError) as e:
        print(f"[WARN] Failed to load config, using default threshold: {e}")
        threshold = default_threshold

    if not domain_record.exists():
        print("[WARN] domain.record.md not found - will be created on first rotation")
        # Domain record will be created by rotation script if needed
        return True

    # Check line count
    try:
        with open(domain_record, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)

        if line_count >= threshold:
            print(f"[WARN] domain.record.md exceeds threshold ({line_count} / {threshold} lines)")
            print("       Run: python scripts/domain-record-rotate.py --rotate")
            return False
        else:
            print(f"[OK] domain.record.md size OK ({line_count} / {threshold} lines)")
            return True

    except Exception as e:
        print(f"[WARN] Error checking domain.record.md: {e}")
        return False


# =============================================================================
# Issue-ID Registry Schema Check (FEAT-IDGOV-001 Phase G3, v9.10.0+)
# =============================================================================

def validate_issue_registry(registry_path: Path = ISSUE_REGISTRY_FILE) -> bool:
    """ADDITIVE per-line JSONL schema check for the issue-id registry
    (.protocol-state/issue-registry.jsonl).

    Deliberately LIGHT-WEIGHT: full semantic/content invariants (uniqueness
    of assign ids, grammar, monotonic seq, rev-continuity, transition-
    legality, writer-authority) are already fully owned by
    scripts/check_issue_ids.py (which reuses idgov.engine.validate() -- DRY,
    single source of truth) and are NOT duplicated here. This check only
    confirms each non-blank line is well-formed JSON with the minimal
    required event-shape keys, catching a corrupted/truncated/hand-edited
    line early, in the same --check pass as every other DZP state file --
    without adding a second, competing content validator.

    A MISSING or EMPTY registry is NOT an error: the registry does not exist
    until FEAT-IDGOV-001 goes live (backfill + Phase G1 hook/CI activation),
    and this must never block `validate-protocol.py --check` in the
    meantime (mirrors idgov.registry.read_events()'s own missing-file =
    empty-list behavior).

    Args:
        registry_path: overridable for tests (mirrors VALIDATION_STATE_FILE's
            monkeypatch pattern used elsewhere in this module).

    Returns:
        True if the registry is absent, empty, or every row is well-formed;
        False if any row fails the structural check (never raises).
    """
    if not registry_path.exists():
        print(f"[OK] {registry_path.name} not present (FEAT-IDGOV-001 not yet activated) - skipping")
        return True

    try:
        raw = registry_path.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        print(f"[WARN] Could not read {registry_path.name}: {e}")
        return False

    lines = raw.splitlines()
    non_blank = [line for line in lines if line.strip()]
    if not non_blank:
        print(f"[OK] {registry_path.name} is empty - skipping")
        return True

    errors = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as e:
            errors.append(f"line {i}: invalid JSON ({e})")
            continue

        if not isinstance(row, dict):
            errors.append(f"line {i}: row is not a JSON object")
            continue

        for key in ("schema", "event", "id", "rev"):
            if key not in row:
                errors.append(f"line {i}: missing required key '{key}'")

        event = row.get("event")
        if event not in ("assign", "transition"):
            errors.append(f"line {i}: unknown/missing event type '{event}'")
        elif event == "assign":
            for key in ("family", "subsystem", "seq", "state"):
                if key not in row:
                    errors.append(f"line {i}: assign event missing '{key}'")
        elif event == "transition":
            for key in ("state", "prev_state"):
                if key not in row:
                    errors.append(f"line {i}: transition event missing '{key}'")

    if errors:
        print(f"[ERROR] {registry_path.name} schema check found {len(errors)} issue(s):")
        for e in errors[:10]:
            print(f"  - {e}")
        if len(errors) > 10:
            print(f"  - ... and {len(errors) - 10} more")
        print("  Note: full content-invariant validation is scripts/check_issue_ids.py's job")
        print("  (uniqueness/grammar/seq/rev-continuity/transition-legality/writer-authority).")
        print("  This is only a structural per-line JSONL shape check.")
        return False

    print(f"[OK] {registry_path.name} schema OK ({len(non_blank)} row(s))")
    return True


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - State File Validation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check                    Basic validation check
  %(prog)s --check --verbose          Verbose validation output
  %(prog)s --fix                      Apply auto-fixes (HIGH auto, MEDIUM prompt, LOW skip)
  %(prog)s --fix --ci-mode            Apply auto-fixes in CI mode (no prompts, skip MEDIUM)
  %(prog)s --fix --preview            Preview fixes without applying (dry-run)
  %(prog)s --report                   Generate Markdown report
  %(prog)s --file <path>              Validate specific file only
  %(prog)s --scan-dependencies        Manually trigger dependency scan

Exit Codes:
  0 = Validation passed (no errors)
  1 = Warnings only (usable but needs improvement)
  2 = Errors detected (needs fixing)
  3 = Critical failure (cannot validate)
        """
    )

    parser.add_argument('--check', action='store_true',
                        help='Run validation check on all state files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output with detailed error messages')
    parser.add_argument('--fix', action='store_true',
                        help='Apply auto-fixes (HIGH auto, MEDIUM prompt, LOW skip)')
    parser.add_argument('--preview', action='store_true',
                        help='Preview fixes without applying (dry-run, requires --fix)')
    parser.add_argument('--report', action='store_true',
                        help='Generate detailed Markdown validation report')
    parser.add_argument('--file', type=str, metavar='PATH',
                        help='Validate specific file only')
    parser.add_argument('--scan-dependencies', action='store_true',
                        help='Manually trigger dependency scan (checks for circular dependencies)')
    parser.add_argument('--output', '-o', type=str, metavar='FILE',
                        help='Write report to file instead of stdout')
    parser.add_argument('--ci-mode', action='store_true',
                        help='CI/CD mode: skip interactive prompts, auto-skip MEDIUM confidence fixes')

    args = parser.parse_args()

    # Validate arguments
    if args.preview and not args.fix:
        print("ERROR: --preview requires --fix", file=sys.stderr)
        sys.exit(ExitCode.CRITICAL.value)

    if not any([args.check, args.fix, args.report, args.file, args.scan_dependencies]):
        parser.print_help()
        sys.exit(ExitCode.SUCCESS.value)

    # Check if schema file exists
    if not SCHEMA_FILE.exists():
        print(f"ERROR: Schema file not found: {SCHEMA_FILE}", file=sys.stderr)
        print("Run validation from project root directory.", file=sys.stderr)
        sys.exit(ExitCode.CRITICAL.value)

    try:
        # Load schemas
        if args.verbose:
            print(f"Loading schemas from {SCHEMA_FILE.relative_to(PROJECT_ROOT)}...")
        schemas = load_schemas(SCHEMA_FILE)

        # Discover state files
        if args.file:
            # Validate specific file
            file_path = Path(args.file).resolve()  # Convert to absolute path
            if not file_path.exists():
                print(f"ERROR: File not found: {file_path}", file=sys.stderr)
                sys.exit(ExitCode.CRITICAL.value)

            # Determine schema name (keep hyphens - matches validation-rules.yaml)
            schema_name = file_path.stem  # Keep original name with hyphens
            if schema_name.startswith('snapshot-'):
                schema_name = 'snapshot'

            state_files = [StateFile(path=file_path, schema_name=schema_name, exists=True)]
        else:
            # Discover all state files
            if args.verbose:
                print("Discovering state files...")
            state_files = discover_state_files(PROJECT_ROOT)

        if args.verbose:
            print(f"Found {len(state_files)} state file(s) to validate\n")

        # Run validation
        results = []
        unmatched_schemas = []
        for state_file in state_files:
            schema = schemas.get(state_file.schema_name)
            if not schema:
                print(f"WARNING: No schema found for {state_file.schema_name}, skipping", file=sys.stderr)
                unmatched_schemas.append(state_file.schema_name)
                continue

            if args.verbose:
                print(f"Validating {state_file.path.relative_to(PROJECT_ROOT)}...")

            result = validate_file(state_file, schema)
            results.append(result)

        # BUG-VALIDATE-001 (v9.3.0): an explicitly-requested --file that can't be
        # matched to a schema must NOT report SUCCESS/exit 0 - that is a false
        # negative (an unvalidatable file silently "passing"). Treat it as an error.
        if args.file and not results:
            print(
                f"ERROR: No schema matched for requested file "
                f"(schema_name='{unmatched_schemas[0] if unmatched_schemas else '?'}'). "
                f"Cannot validate; refusing to report success.",
                file=sys.stderr,
            )
            sys.exit(ExitCode.ERRORS.value)

        # Drift detection
        # ISS-083: informational note (never an error/warning) when the local
        # attestation ledger hasn't been initialized yet on this install --
        # drift detection runs exactly as it did before ISS-083 (every
        # checksum mismatch alerts) until the next sanctioned write creates
        # .protocol-state/.attestation.json. This is a benign, one-time
        # transition state, never a crash or hard failure.
        if not args.file and _ATTESTATION_AVAILABLE and not _attestation.ledger_exists(STATE_DIR):
            print(
                "[INFO] Attestation ledger not yet initialized "
                f"({STATE_DIR / _attestation.LEDGER_FILENAME}); drift detection is "
                "running unattested until the next sanctioned state write creates it "
                "(ISS-083)."
            )

        last_validation_state = load_validation_state()
        drift_alerts = detect_drift(results, last_validation_state)

        # Auto-fix generation
        auto_fixes = []
        if args.fix:
            auto_fixes = generate_auto_fixes(results)
            if auto_fixes:
                print(f"\n{len(auto_fixes)} auto-fix suggestion(s) generated")
                applied = apply_auto_fixes(auto_fixes, preview_only=args.preview, ci_mode=args.ci_mode)
                if not args.preview:
                    print(f"{applied} fix(es) applied\n")

        # Update validation state
        if not args.preview:
            update_validation_state(results, auto_fixes)

        # Generate report
        report = generate_report(results, drift_alerts, auto_fixes)

        # Domain record validation (v8.8.0+) - run before printing report
        if args.check or args.verbose:
            print("\nValidating domain record...")
            domain_record_ok = validate_domain_record()
            if not domain_record_ok and report.exit_code == ExitCode.SUCCESS:
                # Downgrade to warnings if domain record needs rotation
                report.exit_code = ExitCode.WARNINGS

            # FEAT-IDGOV-001 Phase G3: additive, non-fatal-unless-malformed
            # per-line JSONL schema check for the issue-id registry.
            print("\nValidating issue-id registry (FEAT-IDGOV-001)...")
            issue_registry_ok = validate_issue_registry()
            if not issue_registry_ok and report.exit_code == ExitCode.SUCCESS:
                report.exit_code = ExitCode.WARNINGS

        # Output report
        if args.report or args.verbose:
            if args.output:
                # Write to file
                with open(args.output, 'w', encoding='utf-8') as f:
                    stdout_backup = sys.stdout
                    sys.stdout = f
                    print_report_markdown(report)
                    sys.stdout = stdout_backup
                print(f"Report written to {args.output}")
            else:
                print_report_markdown(report)
        else:
            print_report_summary(report)

        # Dependency scan (manual trigger only - reverted from automatic)
        if args.scan_dependencies:
            print("Dependency scanning feature not yet implemented")
            print("Will scan for circular dependencies in future release")

        sys.exit(report.exit_code.value)

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(ExitCode.CRITICAL.value)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(ExitCode.CRITICAL.value)


if __name__ == '__main__':
    main()
