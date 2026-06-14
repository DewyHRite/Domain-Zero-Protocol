#!/usr/bin/env python3
"""
Domain Zero Protocol - AUTO-INVOKED Section Integrity Verification
Version: 8.12.0 (PATCH-SESSION-004)
Purpose: CI/CD validation to prevent context compaction from disabling safety systems

This script verifies that the AUTO-INVOKED startup checks in gojo.agent.md
remain intact and functional. Context compaction can strip critical enforcement
code, creating a 5-10% coverage gap.

Exit Codes:
    0: All checks passed (section intact)
    1: One or more checks failed (section compromised)

Usage:
    python scripts/verify-auto-invoked.py
    python scripts/verify-auto-invoked.py --verbose
"""

import sys
from pathlib import Path
from typing import Tuple, List


class AutoInvokedVerifier:
    """Verify AUTO-INVOKED section integrity in gojo.agent.md."""

    def __init__(self, protocol_root: Path):
        self.protocol_root = Path(protocol_root)
        self.gojo_file = self.protocol_root / "protocol" / "gojo.agent.md"
        self.verbose = "--verbose" in sys.argv or "-v" in sys.argv

        # Validate protocol root
        if not (self.protocol_root / "protocol").is_dir():
            raise FileNotFoundError(
                f"Protocol root validation failed: {self.protocol_root}\n"
                f"Expected 'protocol/' directory not found.\n"
                f"Please run this script from the Domain Zero Protocol root directory."
            )

        # Expected markers and keywords (PATCH-SESSION-004)
        self.opening_marker = "<!-- CRITICAL: DO NOT REMOVE - SAFETY SYSTEM"
        self.closing_marker = "<!-- END CRITICAL SAFETY SYSTEM SECTION -->"
        self.section_header = "### AUTO-INVOKED SESSION ALERT CHECK"
        self.cortex_section_header = "### AUTO-INVOKED CORTEX-FIRST RECALL"

        self.required_keywords = [
            "PATCH-SESSION-003",
            "session-check",
            "check-and-record",
            "PATCH-BRAIN-002",
            "CORTEX-FIRST",
            "brain.ps1 status",
            "mandatory to attempt",
            "MANDATORY",
            "CRITICAL",
        ]

        # Minimum section length (raised from 1000 to 1136 per CodeRabbit review)
        # Actual section is ~2200 chars as of v8.12.0
        self.min_section_length = 1136

    def verify(self) -> Tuple[bool, List[str]]:
        """
        Run all verification checks.

        Returns:
            (all_passed, error_messages)
        """
        errors = []

        # Check 1: File exists
        if not self.gojo_file.exists():
            errors.append(f"ERROR: gojo.agent.md not found at {self.gojo_file}")
            return False, errors

        # Read file content
        try:
            with open(self.gojo_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            errors.append(f"ERROR: Failed to read gojo.agent.md: {e}")
            return False, errors

        # Check 2: Opening HTML marker present
        if self.opening_marker not in content:
            errors.append(f"ERROR: Opening HTML marker missing: {self.opening_marker}")
        else:
            if self.verbose:
                print(f"[OK] Opening HTML marker found")

        # Check 3: Closing HTML marker present
        if self.closing_marker not in content:
            errors.append(f"ERROR: Closing HTML marker missing: {self.closing_marker}")
        else:
            if self.verbose:
                print(f"[OK] Closing HTML marker found")

        # Check 4: Section header present
        if self.section_header not in content:
            errors.append(f"ERROR: Section header missing: {self.section_header}")
        else:
            if self.verbose:
                print(f"[OK] Section header found")

        if self.cortex_section_header not in content:
            errors.append(f"ERROR: Cortex section header missing: {self.cortex_section_header}")
        else:
            if self.verbose:
                print(f"[OK] Cortex section header found")

        # Check 5: Extract protected section and validate length
        # Improved error handling for marker extraction edge cases
        if self.opening_marker in content and self.closing_marker in content:
            try:
                opening_idx = content.index(self.opening_marker)
                closing_idx = content.index(self.closing_marker) + len(self.closing_marker)

                # Validate marker order
                if opening_idx >= closing_idx:
                    errors.append(
                        f"ERROR: Marker order invalid (opening at {opening_idx}, closing at {closing_idx})"
                    )
                else:
                    protected_section = content[opening_idx:closing_idx]

                    section_length = len(protected_section)
                    if section_length < self.min_section_length:
                        errors.append(
                            f"ERROR: Protected section too short ({section_length} chars, minimum {self.min_section_length})"
                        )
                    else:
                        if self.verbose:
                            print(f"[OK] Protected section length: {section_length} chars (>= {self.min_section_length})")

                    # Check 6: All required keywords present in protected section
                    missing_keywords = []
                    for keyword in self.required_keywords:
                        if keyword not in protected_section:
                            missing_keywords.append(keyword)

                    if missing_keywords:
                        errors.append(f"ERROR: Missing required keywords in protected section: {', '.join(missing_keywords)}")
                    else:
                        if self.verbose:
                            print(f"[OK] All required keywords present: {', '.join(self.required_keywords)}")

            except ValueError as e:
                errors.append(f"ERROR: Unexpected error extracting protected section: {e}")
        elif self.opening_marker not in content and self.closing_marker not in content:
            # Both markers missing (already reported in checks 2-3)
            pass
        elif self.opening_marker in content:
            # Only opening marker present (closing already reported missing in check 3)
            if self.verbose:
                print("[WARN] Opening marker found but closing marker missing - cannot extract section")
        else:
            # Only closing marker present (opening already reported missing in check 2)
            if self.verbose:
                print("[WARN] Closing marker found but opening marker missing - cannot extract section")

        # Summary
        all_passed = len(errors) == 0
        return all_passed, errors

    def run(self) -> int:
        """
        Run verification and print results.

        Returns:
            Exit code (0 = pass, 1 = fail)
        """
        print("=" * 60)
        print("AUTO-INVOKED Startup Checks Integrity Verification")
        print("Domain Zero Protocol v9.1.0 (PATCH-SESSION-004 + PATCH-BRAIN-002)")
        print("=" * 60)
        print()

        all_passed, errors = self.verify()

        if all_passed:
            print("[PASS] All verification checks passed")
            print()
            print("Protected section integrity: OK")
            print("Safety system enforcement: FUNCTIONAL")
            print("Cortex-first enforcement: FUNCTIONAL")
            return 0
        else:
            print("[FAIL] Verification checks failed")
            print()
            for error in errors:
                print(f"  {error}")
            print()
            print("CRITICAL: AUTO-INVOKED section compromised!")
            print("Safety or Cortex-first enforcement may be non-functional.")
            print()
            print("Action Required:")
            print("  1. Restore gojo.agent.md from backup:")
            print(f"     cp .protocol-state/backups/v8.12.0-pre-implementation_*/gojo.agent.md protocol/")
            print("  2. OR apply PATCH-SESSION-004 HTML markers manually")
            print("  3. Run this script again to verify")
            return 1


def main():
    """Command-line entry point."""
    protocol_root = Path.cwd()

    try:
        verifier = AutoInvokedVerifier(protocol_root)
        exit_code = verifier.run()
        sys.exit(exit_code)
    except FileNotFoundError as e:
        print("=" * 60)
        print("AUTO-INVOKED Startup Checks Integrity Verification")
        print("Domain Zero Protocol v9.1.0 (PATCH-SESSION-004 + PATCH-BRAIN-002)")
        print("=" * 60)
        print()
        print("[ERROR] Protocol root validation failed")
        print()
        print(str(e))
        print()
        print("Current directory:", protocol_root)
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
