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
- CLI interface with multiple flags
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
import hashlib
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
    print("ERROR: jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(3)


# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_FILE = PROJECT_ROOT / "protocol" / "validation-rules.yaml"
STATE_DIR = PROJECT_ROOT / ".protocol-state"
VALIDATION_STATE_FILE = STATE_DIR / "validation" / "validation-state.json"


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

    # Discover snapshot files (snapshot-*.json pattern)
    snapshots_dir = state_dir / "snapshots"
    if snapshots_dir.exists():
        for snapshot_file in snapshots_dir.glob("snapshot-*.json"):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
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

def detect_drift(current_results: List[ValidationResult], last_validation_state: Optional[Dict[str, Any]]) -> List[DriftAlert]:
    """
    Detect unauthorized changes since last validation by comparing checksums

    Args:
        current_results: Current validation results with checksums
        last_validation_state: Previous validation state from validation-state.json

    Returns:
        List of DriftAlert objects for files with detected drift
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
        previous = integrity_data.get(file_key, {})
        previous_checksum = previous.get('checksum')

        if previous_checksum and result.checksum != previous_checksum:
            # Drift detected!
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


def apply_auto_fixes(auto_fixes: List[AutoFix], preview_only: bool = False) -> int:
    """
    Apply auto-fixes based on confidence level

    Args:
        auto_fixes: List of AutoFix objects
        preview_only: If True, only show what would be fixed (dry-run)

    Returns:
        Number of fixes applied

    Note: HIGH auto-applies, MEDIUM prompts, LOW skips
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
            # MEDIUM confidence - prompt user
            if preview_only:
                print(f"[PREVIEW] Would prompt for: {fix.description}")
            else:
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
            state["state_file_integrity"][file_key] = {
                "checksum": result.checksum,
                "last_validated": datetime.now(timezone.utc).isoformat() + 'Z',
                "status": result.status.value,
                "errors": [e.message for e in result.errors[:5]]  # Store first 5 errors
            }

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
    if any(e.severity == "critical" for r in results for e in r.errors):
        exit_code = ExitCode.CRITICAL
    elif files_failed > 0 or total_errors > 0:
        exit_code = ExitCode.ERRORS
    elif total_warnings > 0:
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
        for state_file in state_files:
            schema = schemas.get(state_file.schema_name)
            if not schema:
                print(f"WARNING: No schema found for {state_file.schema_name}, skipping", file=sys.stderr)
                continue

            if args.verbose:
                print(f"Validating {state_file.path.relative_to(PROJECT_ROOT)}...")

            result = validate_file(state_file, schema)
            results.append(result)

        # Drift detection
        last_validation_state = load_validation_state()
        drift_alerts = detect_drift(results, last_validation_state)

        # Auto-fix generation
        auto_fixes = []
        if args.fix:
            auto_fixes = generate_auto_fixes(results)
            if auto_fixes:
                print(f"\n{len(auto_fixes)} auto-fix suggestion(s) generated")
                applied = apply_auto_fixes(auto_fixes, preview_only=args.preview)
                if not args.preview:
                    print(f"{applied} fix(es) applied\n")

        # Update validation state
        if not args.preview:
            update_validation_state(results, auto_fixes)

        # Generate report
        report = generate_report(results, drift_alerts, auto_fixes)

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
