#!/usr/bin/env python3
"""
Domain Zero Protocol - Custom Agent Validator Tests
Version: 8.7.0

Comprehensive test suite for custom agent definition validation.
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_custom_agents import (
    CustomAgentValidator,
    ConfigLoader
)


@pytest.fixture
def temp_protocol_root(tmp_path):
    """Create temporary protocol root with config."""
    # Create protocol.config.yaml
    config_content = """
custom_agent_security:
  enabled: true
  namespace:
    reserved_names:
      - yuuji
      - megumi
      - nobara
      - gojo
      - todo
      - maki
      - panda
      - inumaki
      - sukuna
    require_prefix: "custom-"
  yaml_validation:
    required_fields:
      - name
      - description
      - tools
      - model
    name_pattern: '^custom-[a-z][a-z0-9-]{2,20}$'
    forbidden_patterns:
      - '__proto__'
      - 'eval:'
      - 'exec:'
      - '\\$\\{.*\\}'
      - '!!python/'
  tool_permissions:
    custom_agents_default:
      - read
      - grep
      - glob
    requires_approval:
      - edit
      - write
    forbidden:
      - bash
      - task
"""
    config_file = tmp_path / "protocol.config.yaml"
    config_file.write_text(config_content)

    # Create agents directory
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True)

    return tmp_path


@pytest.fixture
def config_loader(temp_protocol_root):
    """Create ConfigLoader with temp config."""
    config_path = temp_protocol_root / "protocol.config.yaml"
    loader = ConfigLoader(config_path)
    loader.load()
    return loader


@pytest.fixture
def validator(config_loader):
    """Create CustomAgentValidator instance."""
    return CustomAgentValidator(config_loader)


@pytest.fixture
def valid_agent_content():
    """Valid agent file content."""
    return """---
name: custom-test
description: Test agent for validation
tools:
  - read
  - grep
model: sonnet
---

# Custom Test Agent

This is a test agent.
"""


@pytest.fixture
def create_agent_file(temp_protocol_root):
    """Helper to create agent file with given content."""
    def _create(filename, content):
        agent_path = temp_protocol_root / ".claude" / "agents" / filename
        agent_path.write_text(content)
        return agent_path
    return _create


class TestConfigLoader:
    """Test configuration loading."""

    def test_loads_config_successfully(self, temp_protocol_root):
        """Should load protocol.config.yaml."""
        config_path = temp_protocol_root / "protocol.config.yaml"
        loader = ConfigLoader(config_path)
        assert loader.load() is True
        assert loader.security_config is not None

    def test_handles_missing_config(self, tmp_path):
        """Should handle missing config file gracefully."""
        config_path = tmp_path / "nonexistent.yaml"
        loader = ConfigLoader(config_path)
        assert loader.load() is False

    def test_is_enabled_check(self, config_loader):
        """Should correctly check if security is enabled."""
        assert config_loader.is_enabled() is True


class TestFileSizeValidation:
    """Test file size validation."""

    def test_accepts_normal_file_size(self, validator, create_agent_file, valid_agent_content):
        """Should accept files under 100KB."""
        agent_path = create_agent_file("custom-small.agent.md", valid_agent_content)
        result = validator.validate_agent_file(agent_path)

        # Should have info message about file size
        info_messages = [msg for msg in result.info if "File size" in msg]
        assert len(info_messages) == 1

    def test_rejects_oversized_file(self, validator, create_agent_file):
        """Should reject files over 100KB."""
        # Create content > 100KB
        large_content = """---
name: custom-large
description: Large agent
tools: [read]
model: sonnet
---

# Large Agent

""" + ("x" * 110000)

        agent_path = create_agent_file("custom-large.agent.md", large_content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("exceeds maximum" in err for err in result.errors)


class TestAgentNameValidation:
    """Test agent name validation."""

    def test_accepts_valid_name(self, validator, create_agent_file, valid_agent_content):
        """Should accept name with custom- prefix."""
        agent_path = create_agent_file("custom-test.agent.md", valid_agent_content)
        result = validator.validate_agent_file(agent_path)

        # Check for successful name validation
        info_messages = [msg for msg in result.info if "valid" in msg.lower()]
        assert len(info_messages) > 0

    def test_rejects_reserved_name(self, validator, create_agent_file):
        """Should reject core protocol agent names."""
        content = """---
name: yuuji
description: Trying to impersonate core agent
tools: [read]
model: sonnet
---
"""
        agent_path = create_agent_file("yuuji.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("reserved" in err.lower() for err in result.errors)

    def test_rejects_missing_prefix(self, validator, create_agent_file):
        """Should reject names without custom- prefix."""
        content = """---
name: testagent
description: Missing prefix
tools: [read]
model: sonnet
---
"""
        agent_path = create_agent_file("testagent.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("must start with 'custom-'" in err for err in result.errors)

    def test_rejects_invalid_pattern(self, validator, create_agent_file):
        """Should reject names with invalid characters."""
        content = """---
name: custom-Test_Agent
description: Invalid characters
tools: [read]
model: sonnet
---
"""
        agent_path = create_agent_file("custom-Test_Agent.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("does not match required pattern" in err for err in result.errors)


class TestYAMLStructureValidation:
    """Test YAML structure validation."""

    def test_accepts_valid_yaml(self, validator, create_agent_file, valid_agent_content):
        """Should accept valid YAML frontmatter."""
        agent_path = create_agent_file("custom-valid.agent.md", valid_agent_content)
        result = validator.validate_agent_file(agent_path)

        # Should not have YAML-related errors
        yaml_errors = [err for err in result.errors if "YAML" in err or "frontmatter" in err]
        assert len(yaml_errors) == 0

    def test_rejects_missing_yaml(self, validator, create_agent_file):
        """Should reject files without YAML frontmatter."""
        content = "# Agent without frontmatter\n\nThis is invalid."
        agent_path = create_agent_file("custom-noyaml.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("No YAML frontmatter" in err for err in result.errors)

    def test_rejects_missing_required_field(self, validator, create_agent_file):
        """Should reject YAML missing required fields."""
        content = """---
name: custom-incomplete
description: Missing tools field
model: sonnet
---
"""
        agent_path = create_agent_file("custom-incomplete.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("Missing required YAML field: 'tools'" in err for err in result.errors)

    def test_rejects_empty_required_field(self, validator, create_agent_file):
        """Should reject empty required fields."""
        content = """---
name: custom-empty
description: ""
tools: [read]
model: sonnet
---
"""
        agent_path = create_agent_file("custom-empty.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("cannot be empty" in err for err in result.errors)

    def test_rejects_non_list_tools(self, validator, create_agent_file):
        """Should reject tools field that's not a list."""
        content = """---
name: custom-badtools
description: Tools not a list
tools: read
model: sonnet
---
"""
        agent_path = create_agent_file("custom-badtools.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("'tools' must be a list" in err for err in result.errors)


class TestYAMLContentValidation:
    """Test YAML content security validation."""

    def test_rejects_proto_pollution(self, validator, create_agent_file):
        """Should reject __proto__ pattern."""
        content = """---
name: custom-proto
description: Prototype pollution attempt
tools: [read]
model: sonnet
__proto__: malicious
---
"""
        agent_path = create_agent_file("custom-proto.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("Forbidden pattern" in err and "__proto__" in err for err in result.errors)

    def test_rejects_eval_pattern(self, validator, create_agent_file):
        """Should reject eval: pattern."""
        content = """---
name: custom-eval
description: Code execution attempt
tools: [read]
model: sonnet
config:
  eval: "malicious code"
---
"""
        agent_path = create_agent_file("custom-eval.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("Forbidden pattern" in err for err in result.errors)

    def test_rejects_python_deserialization(self, validator, create_agent_file):
        """Should reject !!python/ pattern."""
        content = """---
name: custom-python
description: Python deserialization attack
tools: [read]
model: !!python/name:os.system
---
"""
        agent_path = create_agent_file("custom-python.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("Forbidden pattern" in err for err in result.errors)


class TestToolPermissionsValidation:
    """Test tool permissions validation."""

    def test_accepts_default_tools(self, validator, create_agent_file):
        """Should accept tools in default allowed list."""
        content = """---
name: custom-defaulttools
description: Uses default tools
tools:
  - read
  - grep
  - glob
model: sonnet
---
"""
        agent_path = create_agent_file("custom-defaulttools.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        # Should have info messages for allowed tools
        tool_info = [msg for msg in result.info if "allowed" in msg.lower()]
        assert len(tool_info) >= 3

    def test_warns_approval_required_tools(self, validator, create_agent_file):
        """Should warn about tools requiring approval."""
        content = """---
name: custom-approval
description: Uses approval-required tools
tools:
  - edit
  - write
model: sonnet
---
"""
        agent_path = create_agent_file("custom-approval.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        # Should have warnings for approval-required tools
        approval_warnings = [warn for warn in result.warnings if "requires user approval" in warn]
        assert len(approval_warnings) == 2

    def test_rejects_forbidden_tools(self, validator, create_agent_file):
        """Should reject forbidden tools."""
        content = """---
name: custom-forbidden
description: Uses forbidden tools
tools:
  - bash
  - task
model: sonnet
---
"""
        agent_path = create_agent_file("custom-forbidden.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed
        assert any("bash" in err and "forbidden" in err.lower() for err in result.errors)
        assert any("task" in err and "forbidden" in err.lower() for err in result.errors)

    def test_handles_mixed_tools(self, validator, create_agent_file):
        """Should correctly classify mixed tool list."""
        content = """---
name: custom-mixed
description: Mixed tool permissions
tools:
  - read     # default
  - edit     # requires approval
  - bash     # forbidden
  - unknown  # not in list
model: sonnet
---
"""
        agent_path = create_agent_file("custom-mixed.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        assert not result.passed  # Should fail due to forbidden tool

        # Check all categories present
        assert any("allowed" in msg.lower() for msg in result.info)  # read
        assert any("requires user approval" in warn for warn in result.warnings)  # edit
        assert any("forbidden" in err.lower() for err in result.errors)  # bash


class TestPathTraversalValidation:
    """Test path traversal protection."""

    def test_accepts_file_in_agents_directory(self, validator, create_agent_file, valid_agent_content):
        """Should accept files in .claude/agents/."""
        agent_path = create_agent_file("custom-safe.agent.md", valid_agent_content)
        result = validator.validate_agent_file(agent_path)

        # Should not have path traversal errors
        path_errors = [err for err in result.errors if "Path traversal" in err]
        assert len(path_errors) == 0

    def test_rejects_file_outside_agents_directory(self, validator, temp_protocol_root):
        """Should reject files outside .claude/agents/."""
        # Create file in wrong location
        bad_path = temp_protocol_root / "custom-bad.agent.md"
        bad_path.write_text("""---
name: custom-bad
description: Outside agents directory
tools: [read]
model: sonnet
---
""")

        result = validator.validate_agent_file(bad_path)

        assert not result.passed
        assert any("Path traversal detected" in err for err in result.errors)


class TestFileExtensionValidation:
    """Test file extension validation."""

    def test_accepts_agent_md_extension(self, validator, create_agent_file, valid_agent_content):
        """Should accept .agent.md extension."""
        agent_path = create_agent_file("custom-valid.agent.md", valid_agent_content)
        result = validator.validate_agent_file(agent_path)

        # No extension errors
        ext_errors = [err for err in result.errors if "extension" in err.lower()]
        assert len(ext_errors) == 0

    def test_rejects_wrong_extension(self, validator, temp_protocol_root):
        """Should reject files without .agent.md extension."""
        agents_dir = temp_protocol_root / ".claude" / "agents"
        bad_file = agents_dir / "custom-bad.md"
        bad_file.write_text("content")

        result = validator.validate_agent_file(bad_file)

        assert not result.passed
        assert any(".agent.md extension" in err for err in result.errors)


class TestValidationResultReporting:
    """Test validation result reporting."""

    def test_passed_result_format(self, validator, create_agent_file, valid_agent_content):
        """Passed result should have proper format."""
        agent_path = create_agent_file("custom-pass.agent.md", valid_agent_content)
        result = validator.validate_agent_file(agent_path)

        report = result.get_report()
        assert "✅ VALIDATION PASSED" in report
        assert "❌ ERROR" not in report

    def test_failed_result_format(self, validator, create_agent_file):
        """Failed result should show errors prominently."""
        content = """---
name: yuuji
description: Reserved name
tools: [bash]
model: sonnet
---
"""
        agent_path = create_agent_file("yuuji.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        report = result.get_report()
        assert "🔴 VALIDATION FAILED" in report
        assert "❌ ERROR" in report
        assert not result.passed

    def test_includes_all_message_types(self, validator, create_agent_file):
        """Report should include errors, warnings, and info."""
        content = """---
name: custom-mixed
description: Mixed validation
tools:
  - read   # info
  - edit   # warning
  - bash   # error
model: sonnet
---
"""
        agent_path = create_agent_file("custom-mixed.agent.md", content)
        result = validator.validate_agent_file(agent_path)

        report = result.get_report()
        # Should have all three categories
        assert "ERROR" in report
        assert "WARNING" in report
        assert "INFO" in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
