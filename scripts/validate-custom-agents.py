#!/usr/bin/env python3
"""
Domain Zero Protocol - Custom Agent Security Validator (v8.7.0)

Validates custom agent definitions against security policies defined in protocol.config.yaml.
Enforces namespace protection, tool permissions, YAML sanitization, and file integrity checks.

Exit Codes:
  0 - All validations passed
  1 - Validation failed (details in stderr)
  2 - Configuration error
  3 - File not found or access error

Usage:
  python validate-custom-agents.py <agent_file_path>
  python validate-custom-agents.py --validate-all
"""

import sys
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import argparse


@dataclass
class ValidationResult:
    """Stores validation results with categorized errors."""
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def add_error(self, message: str):
        """Add a critical error (blocks agent registration)."""
        self.errors.append(f"❌ ERROR: {message}")
        self.passed = False

    def add_warning(self, message: str):
        """Add a warning (logged but doesn't block)."""
        self.warnings.append(f"⚠️  WARNING: {message}")

    def add_info(self, message: str):
        """Add informational message."""
        self.info.append(f"ℹ️  INFO: {message}")

    def get_report(self) -> str:
        """Generate human-readable validation report."""
        lines = []

        if self.errors:
            lines.append("🔴 VALIDATION FAILED\n")
            lines.extend(self.errors)

        if self.warnings:
            lines.append("\n⚠️  WARNINGS:")
            lines.extend(self.warnings)

        if self.info:
            lines.append("\n📋 INFO:")
            lines.extend(self.info)

        if self.passed:
            lines.insert(0, "✅ VALIDATION PASSED\n")

        return "\n".join(lines)


class ConfigLoader:
    """Loads and parses protocol.config.yaml security settings."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            # Default: look for protocol.config.yaml in project root
            self.config_path = Path(__file__).parent.parent / "protocol.config.yaml"
        else:
            self.config_path = Path(config_path)

        self.config: Dict[str, Any] = {}
        self.security_config: Dict[str, Any] = {}

    def load(self) -> bool:
        """Load configuration file. Returns True on success."""
        if not self.config_path.exists():
            print(f"❌ Configuration file not found: {self.config_path}", file=sys.stderr)
            return False

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # Extract custom_agent_security section
            self.security_config = self.config.get('custom_agent_security', {})

            if not self.security_config:
                print("⚠️  WARNING: custom_agent_security section not found in config", file=sys.stderr)

            return True

        except yaml.YAMLError as e:
            print(f"❌ Failed to parse configuration YAML: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Unexpected error loading configuration: {e}", file=sys.stderr)
            return False

    def is_enabled(self) -> bool:
        """Check if custom agent security is enabled."""
        return self.security_config.get('enabled', False)


class CustomAgentValidator:
    """Main validator for custom agent definitions."""

    def __init__(self, config: ConfigLoader):
        self.config = config
        self.security = config.security_config

    def validate_agent_file(self, agent_path: Path) -> ValidationResult:
        """
        Validate a custom agent definition file against all security policies.

        Args:
            agent_path: Path to the .agent.md file to validate

        Returns:
            ValidationResult with all validation checks
        """
        result = ValidationResult()

        # Pre-flight checks
        if not agent_path.exists():
            result.add_error(f"Agent file not found: {agent_path}")
            return result

        if not agent_path.suffix == '.md' or not agent_path.name.endswith('.agent.md'):
            result.add_error(f"Agent file must have .agent.md extension, got: {agent_path.name}")
            return result

        # Path traversal protection: validate that resolved path is within expected directory
        try:
            resolved_path = agent_path.resolve()
            # Expected base directory: .claude/agents/ relative to current working directory
            expected_base = (Path.cwd() / ".claude" / "agents").resolve()

            # Check if resolved path is a subdirectory of expected base
            try:
                resolved_path.relative_to(expected_base)
            except ValueError:
                result.add_error(
                    f"Path traversal detected: Agent file must be in .claude/agents/ directory. "
                    f"Got: {agent_path} (resolves to: {resolved_path})"
                )
                return result
        except Exception as e:
            result.add_error(f"Failed to validate agent file path: {e}")
            return result

        # Read file content
        try:
            with open(agent_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            result.add_error(f"Failed to read agent file: {e}")
            return result

        # Extract agent name from filename
        agent_filename = agent_path.stem.replace('.agent', '')

        # Run validation checks
        self._validate_file_size(agent_path, result)
        self._validate_agent_name(agent_filename, result)

        # Extract and validate YAML frontmatter
        frontmatter = self._extract_yaml_frontmatter(content, result)
        if frontmatter:
            self._validate_yaml_structure(frontmatter, result)
            self._validate_yaml_content(frontmatter, result)
            self._validate_tool_permissions(frontmatter, result)

        return result

    def _validate_file_size(self, agent_path: Path, result: ValidationResult):
        """Check agent file size is within limits (max 100KB)."""
        max_size = 100 * 1024  # 100KB
        actual_size = agent_path.stat().st_size

        if actual_size > max_size:
            result.add_error(
                f"Agent file size ({actual_size} bytes) exceeds maximum allowed "
                f"({max_size} bytes). Reduce agent file size."
            )
        else:
            result.add_info(f"File size: {actual_size} bytes (within limit)")

    def _validate_agent_name(self, agent_name: str, result: ValidationResult):
        """
        Validate agent name against namespace protection rules.

        Checks:
        - Follows custom-[name] pattern (if require_prefix is True)
        - Not in reserved_names list
        - Matches allowed name pattern
        """
        namespace_config = self.security.get('namespace', {})
        reserved_names = namespace_config.get('reserved_names', [])
        require_prefix = namespace_config.get('require_prefix', 'custom-')
        name_pattern = self.security.get('yaml_validation', {}).get('name_pattern', r'^custom-[a-z][a-z0-9-]{2,20}$')

        # Check reserved names
        if agent_name.lower() in [name.lower() for name in reserved_names]:
            result.add_error(
                f"Agent name '{agent_name}' is reserved for core protocol agents. "
                f"Reserved names: {', '.join(reserved_names)}"
            )

        # Check prefix requirement
        if require_prefix:
            if not agent_name.startswith(require_prefix):
                result.add_error(
                    f"Agent name must start with '{require_prefix}'. "
                    f"Got: '{agent_name}'"
                )

        # Check name pattern
        if not re.match(name_pattern, agent_name):
            result.add_error(
                f"Agent name '{agent_name}' does not match required pattern: {name_pattern}. "
                f"Name must be lowercase, alphanumeric with hyphens, 5-23 characters total "
                f"(including 'custom-' prefix)."
            )
        else:
            result.add_info(f"Agent name '{agent_name}' is valid")

    def _extract_yaml_frontmatter(self, content: str, result: ValidationResult) -> Optional[Dict[str, Any]]:
        """
        Extract YAML frontmatter from agent markdown file.

        Expected format:
        ---
        name: custom-myagent
        description: My custom agent
        tools: [read, grep]
        model: sonnet
        ---
        """
        # Match YAML frontmatter between --- delimiters
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            result.add_error(
                "No YAML frontmatter found. Agent files must start with YAML frontmatter "
                "between '---' delimiters."
            )
            return None

        yaml_content = match.group(1)

        try:
            frontmatter = yaml.safe_load(yaml_content)
            if not isinstance(frontmatter, dict):
                result.add_error("YAML frontmatter must be a dictionary/object")
                return None
            return frontmatter
        except yaml.YAMLError as e:
            result.add_error(f"Failed to parse YAML frontmatter: {e}")
            return None

    def _validate_yaml_structure(self, frontmatter: Dict[str, Any], result: ValidationResult):
        """Validate YAML has required fields and correct structure."""
        yaml_config = self.security.get('yaml_validation', {})
        required_fields = yaml_config.get('required_fields', ['name', 'description', 'tools', 'model'])

        for field in required_fields:
            if field not in frontmatter:
                result.add_error(f"Missing required YAML field: '{field}'")
            elif not frontmatter[field]:
                result.add_error(f"Required field '{field}' cannot be empty")

        # Validate 'tools' is a list
        if 'tools' in frontmatter:
            if not isinstance(frontmatter['tools'], list):
                result.add_error("YAML field 'tools' must be a list")
            elif not frontmatter['tools']:
                result.add_warning("Agent has empty tools list (no tool access)")

    def _validate_yaml_content(self, frontmatter: Dict[str, Any], result: ValidationResult):
        """
        Scan YAML content for dangerous patterns (code injection attempts).

        Forbidden patterns:
        - __proto__ (prototype pollution)
        - eval:, exec: (code execution)
        - ${...} (template injection)
        - require(, import (module loading)
        - !!python/ (Python object deserialization)
        """
        yaml_config = self.security.get('yaml_validation', {})
        forbidden_patterns = yaml_config.get('forbidden_patterns', [])

        # Convert frontmatter back to string for pattern matching
        yaml_str = yaml.dump(frontmatter)

        for pattern in forbidden_patterns:
            if re.search(pattern, yaml_str, re.IGNORECASE):
                result.add_error(
                    f"Forbidden pattern detected in YAML: '{pattern}'. "
                    f"This may indicate a code injection attempt."
                )

    def _validate_tool_permissions(self, frontmatter: Dict[str, Any], result: ValidationResult):
        """
        Validate requested tools against permission policies.

        Categories:
        - custom_agents_default: Allowed by default
        - requires_approval: Needs user approval (future: prompt user)
        - forbidden: Never allowed
        """
        tool_config = self.security.get('tool_permissions', {})
        default_tools = [tool.lower() for tool in tool_config.get('custom_agents_default', [])]
        requires_approval = [tool.lower() for tool in tool_config.get('requires_approval', [])]
        forbidden_tools = [tool.lower() for tool in tool_config.get('forbidden', [])]

        requested_tools = frontmatter.get('tools', [])
        if not isinstance(requested_tools, list):
            return  # Already caught in _validate_yaml_structure

        for tool in requested_tools:
            tool_lower = tool.lower()

            # Check forbidden tools
            if tool_lower in forbidden_tools:
                result.add_error(
                    f"Tool '{tool}' is forbidden for custom agents. "
                    f"Forbidden tools: {', '.join(forbidden_tools)}"
                )

            # Check tools requiring approval
            elif tool_lower in requires_approval:
                result.add_warning(
                    f"Tool '{tool}' requires user approval before use. "
                    f"User will be prompted on first invocation."
                )

            # Check if tool is in default allowed list
            elif tool_lower not in default_tools:
                result.add_warning(
                    f"Tool '{tool}' is not in the default allowed list. "
                    f"This may require configuration update."
                )

            else:
                result.add_info(f"Tool '{tool}' is allowed")


def validate_all_custom_agents(config: ConfigLoader) -> Tuple[int, int, int]:
    """
    Validate all custom agents in .claude/agents/ directory.

    Returns:
        Tuple of (passed, failed, total) counts
    """
    agent_dir = Path.cwd() / ".claude" / "agents"

    if not agent_dir.exists():
        print(f"ℹ️  No custom agent directory found: {agent_dir}", file=sys.stderr)
        return (0, 0, 0)

    agent_files = list(agent_dir.glob("*.agent.md"))

    if not agent_files:
        print(f"ℹ️  No custom agents found in: {agent_dir}", file=sys.stderr)
        return (0, 0, 0)

    validator = CustomAgentValidator(config)
    passed = 0
    failed = 0

    print(f"🔍 Validating {len(agent_files)} custom agent(s)...\n")

    for agent_file in agent_files:
        print(f"{'=' * 80}")
        print(f"Validating: {agent_file.name}")
        print(f"{'=' * 80}")

        result = validator.validate_agent_file(agent_file)
        print(result.get_report())
        print()

        if result.passed:
            passed += 1
        else:
            failed += 1

    print(f"{'=' * 80}")
    print(f"📊 SUMMARY: {passed} passed, {failed} failed, {len(agent_files)} total")
    print(f"{'=' * 80}")

    return (passed, failed, len(agent_files))


def main():
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - Custom Agent Security Validator (v8.7.0)"
    )
    parser.add_argument(
        'agent_file',
        nargs='?',
        help="Path to the .agent.md file to validate"
    )
    parser.add_argument(
        '--validate-all',
        action='store_true',
        help="Validate all custom agents in .claude/agents/"
    )
    parser.add_argument(
        '--config',
        help="Path to protocol.config.yaml (default: auto-detect)"
    )

    args = parser.parse_args()

    # Load configuration
    config = ConfigLoader(Path(args.config) if args.config else None)
    if not config.load():
        sys.exit(2)

    # Check if custom agent security is enabled
    if not config.is_enabled():
        print("⚠️  WARNING: custom_agent_security is disabled in protocol.config.yaml", file=sys.stderr)
        print("ℹ️  Validation will run but results will not be enforced.", file=sys.stderr)

    # Validate all agents
    if args.validate_all:
        passed, failed, total = validate_all_custom_agents(config)
        sys.exit(0 if failed == 0 else 1)

    # Validate single agent
    if not args.agent_file:
        parser.print_help()
        sys.exit(2)

    agent_path = Path(args.agent_file)
    validator = CustomAgentValidator(config)
    result = validator.validate_agent_file(agent_path)

    # Handle Windows console encoding issues with Unicode
    report = result.get_report()
    try:
        print(report)
    except UnicodeEncodeError:
        # Fallback: print with ASCII-safe replacements
        print(report.encode('ascii', 'replace').decode('ascii'))

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
