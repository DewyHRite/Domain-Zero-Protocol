#!/usr/bin/env python3
"""
Domain Zero Protocol - Dependency Scanner & Impact Analysis

Version: 1.0.0
Created: 2025-12-06
Part of: DZP v8.8.0 Validation Framework - Phase 3

This script analyzes dependencies across the Domain Zero Protocol to detect:
- Agent → File dependencies (which agents read/write which files)
- File → File dependencies (which files reference other files)
- Circular dependencies (problematic dependency loops)
- Impact analysis (blast radius of changes)

Features:
- Comprehensive dependency graph construction
- Circular dependency detection with cycle visualization
- Impact analysis with blast radius calculation
- Agent dependency matrix
- Export to JSON for visualization tools
- CLI interface with multiple report formats

Usage:
    python scripts/dependency-scanner.py --scan                    # Full scan
    python scripts/dependency-scanner.py --analyze <file>          # Analyze specific file
    python scripts/dependency-scanner.py --check-cycles            # Detect circular deps
    python scripts/dependency-scanner.py --agent-matrix            # Agent dependency matrix
    python scripts/dependency-scanner.py --export <output.json>    # Export graph
"""

import ast
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
PROTOCOL_DIR = PROJECT_ROOT / "protocol"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
STATE_DIR = PROJECT_ROOT / ".protocol-state"

# Agent file patterns
AGENT_FILES = [
    "yuuji.agent.md",
    "megumi.agent.md",
    "nobara.agent.md",
    "gojo.agent.md",
    "todo.agent.md",
    "maki.agent.md",
    "panda.agent.md",
    "inumaki.agent.md",
    "sukuna.agent.md"
]

# Critical state files
CRITICAL_FILES = [
    ".protocol-state/project-state.json",
    ".protocol-state/session-state.json",
    ".protocol-state/validation/validation-state.json",
    "protocol.config.yaml"
]


# =============================================================================
# Dependency Graph
# =============================================================================

class DependencyGraph:
    """Represents the dependency graph for the entire DZP system."""

    def __init__(self):
        """Initialize empty dependency graph."""
        # File → Set[File] (direct dependencies)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)

        # File → Set[File] (reverse dependencies - who depends on me)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)

        # Agent → Set[File] (which files each agent uses)
        self.agent_dependencies: Dict[str, Set[str]] = defaultdict(set)

        # File metadata
        self.file_types: Dict[str, str] = {}
        self.file_sizes: Dict[str, int] = {}

    def add_dependency(self, source: str, target: str):
        """Add a dependency from source to target."""
        self.dependencies[source].add(target)
        self.reverse_dependencies[target].add(source)

    def add_agent_dependency(self, agent: str, file_path: str):
        """Add agent → file dependency."""
        self.agent_dependencies[agent].add(file_path)

    def get_direct_dependencies(self, file_path: str) -> Set[str]:
        """Get files that this file directly depends on."""
        return self.dependencies.get(file_path, set())

    def get_reverse_dependencies(self, file_path: str) -> Set[str]:
        """Get files that depend on this file."""
        return self.reverse_dependencies.get(file_path, set())

    def get_all_dependencies(self, file_path: str) -> Set[str]:
        """Get all dependencies (direct and indirect) recursively."""
        visited = set()
        queue = deque([file_path])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)

            # Add direct dependencies to queue
            for dep in self.dependencies.get(current, set()):
                if dep not in visited:
                    queue.append(dep)

        # Remove the original file from results
        visited.discard(file_path)
        return visited

    def get_all_reverse_dependencies(self, file_path: str) -> Set[str]:
        """Get all files that depend on this file (direct and indirect)."""
        visited = set()
        queue = deque([file_path])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)

            # Add reverse dependencies to queue
            for dep in self.reverse_dependencies.get(current, set()):
                if dep not in visited:
                    queue.append(dep)

        # Remove the original file from results
        visited.discard(file_path)
        return visited

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = []

        def dfs(node: str) -> None:
            """DFS helper to detect cycles."""
            if node in rec_stack:
                # Found a cycle
                cycle_start = rec_stack.index(node)
                cycle = rec_stack[cycle_start:] + [node]
                # Normalize cycle to avoid duplicates (start from smallest element)
                normalized = min(range(len(cycle)-1), key=lambda i: cycle[i])
                normalized_cycle = cycle[normalized:-1] + cycle[:normalized] + [cycle[normalized]]
                if normalized_cycle not in cycles:
                    cycles.append(normalized_cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.append(node)

            for neighbor in self.dependencies.get(node, set()):
                dfs(neighbor)

            rec_stack.pop()

        # Try DFS from each node
        for node in self.dependencies.keys():
            if node not in visited:
                dfs(node)

        return cycles


# =============================================================================
# File Scanners
# =============================================================================

class PythonFileScanner:
    """Scans Python files for dependencies."""

    @staticmethod
    def scan(file_path: Path) -> Set[str]:
        """
        Scan Python file for file path references.

        Returns:
            Set of referenced file paths (relative to project root)
        """
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse as AST
            try:
                tree = ast.parse(content)

                # Look for Path() calls and string literals that look like paths
                for node in ast.walk(tree):
                    # Path("...") or Path(...) / "..."
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == 'Path':
                            for arg in node.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    path_str = arg.value
                                    if '/' in path_str or '\\' in path_str:
                                        dependencies.add(path_str)

                    # String literals that look like paths
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        value = node.value
                        # Check for common patterns
                        if any(pattern in value for pattern in ['.json', '.yaml', '.md', '.py', '.protocol-state', 'protocol/']):
                            if '/' in value or '\\' in value:
                                dependencies.add(value)

            except SyntaxError:
                # If AST parsing fails, fall back to regex
                pass  # Intentional: regex fallback handles this case

            # Regex fallback for file patterns
            patterns = [
                r'["\']([^"\']*\.(?:json|yaml|yml|md|py))["\']',  # File extensions
                r'["\'](\./[^"\']+)["\']',  # Relative paths
                r'["\'](\.\./[^"\']+)["\']',  # Parent relative paths
                r'["\'](.protocol-state/[^"\']+)["\']',  # State directory
                r'["\'](protocol/[^"\']+)["\']',  # Protocol directory
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                dependencies.update(matches)

        except Exception as e:
            print(f"Warning: Failed to scan {file_path}: {e}", file=sys.stderr)

        return dependencies


class JSONFileScanner:
    """Scans JSON files for file references."""

    @staticmethod
    def scan(file_path: Path) -> Set[str]:
        """
        Scan JSON file for file path references.

        Returns:
            Set of referenced file paths
        """
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Recursively search for string values that look like paths
            # Note: Recursive extraction could hit recursion limit on deeply nested JSON.
            # This is unlikely for typical config files but could be problematic for
            # malformed/malicious input.
            def extract_paths(obj):
                if isinstance(obj, dict):
                    for value in obj.values():
                        extract_paths(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_paths(item)
                elif isinstance(obj, str):
                    # Check if string looks like a path
                    if any(pattern in obj for pattern in ['.json', '.yaml', '.md', '.py', 'protocol/', '.protocol-state/']):
                        if '/' in obj or '\\' in obj:
                            dependencies.add(obj)

            extract_paths(data)

        except Exception as e:
            print(f"Warning: Failed to scan {file_path}: {e}", file=sys.stderr)

        return dependencies


class MarkdownFileScanner:
    """Scans Markdown files for file references."""

    @staticmethod
    def scan(file_path: Path) -> Set[str]:
        """
        Scan Markdown file for file path references.

        Returns:
            Set of referenced file paths
        """
        dependencies = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for markdown links [text](path)
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.findall(link_pattern, content)
            for _, link in matches:
                if not link.startswith('http'):
                    dependencies.add(link)

            # Look for code blocks with file paths
            code_pattern = r'`([^`]*(?:\.json|\.yaml|\.md|\.py|protocol/|\.protocol-state/)[^`]*)`'
            matches = re.findall(code_pattern, content)
            dependencies.update(matches)

            # Look for quoted paths
            quote_pattern = r'["\']([^"\']*(?:\.json|\.yaml|\.md|\.py|protocol/|\.protocol-state/)[^"\']*)["\']'
            matches = re.findall(quote_pattern, content)
            dependencies.update(matches)

        except Exception as e:
            print(f"Warning: Failed to scan {file_path}: {e}", file=sys.stderr)

        return dependencies


# =============================================================================
# Dependency Scanner
# =============================================================================

class DependencyScanner:
    """Main dependency scanner for DZP."""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        """Initialize scanner."""
        self.project_root = project_root
        self.graph = DependencyGraph()
        self.python_scanner = PythonFileScanner()
        self.json_scanner = JSONFileScanner()
        self.md_scanner = MarkdownFileScanner()

    def normalize_path(self, path_str: str) -> str:
        """Normalize a path string to be relative to project root."""
        # Remove quotes
        path_str = path_str.strip('\'"')

        # Convert backslashes to forward slashes
        path_str = path_str.replace('\\', '/')

        # Remove leading ./
        if path_str.startswith('./'):
            path_str = path_str[2:]

        # Remove leading /
        if path_str.startswith('/'):
            path_str = path_str[1:]

        # Filter out invalid paths (too short, contain control chars, too long, etc.)
        if len(path_str) < 3 or len(path_str) > 200:
            return ""

        # Check for control characters or weird unicode
        if any(ord(c) < 32 or ord(c) > 126 for c in path_str):
            return ""

        # Must look like a valid file path
        if not any(c in path_str for c in ['.', '/']):
            return ""

        return path_str

    def scan_file(self, file_path: Path) -> Set[str]:
        """
        Scan a single file for dependencies.

        Returns:
            Set of dependency file paths
        """
        suffix = file_path.suffix.lower()

        if suffix == '.py':
            return self.python_scanner.scan(file_path)
        elif suffix in ['.json']:
            return self.json_scanner.scan(file_path)
        elif suffix in ['.md', '.yaml', '.yml']:
            return self.md_scanner.scan(file_path)

        return set()

    def scan_directory(self, directory: Path, pattern: str = "**/*") -> None:
        """Scan all files in a directory matching pattern."""
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                self.scan_and_add(file_path)

    def scan_and_add(self, file_path: Path) -> None:
        """Scan a file and add its dependencies to the graph."""
        # Get relative path from project root
        try:
            rel_path = file_path.relative_to(self.project_root)
        except ValueError:
            # File is outside project root
            return

        source = str(rel_path).replace('\\', '/')

        # Add file metadata
        self.graph.file_types[source] = file_path.suffix
        try:
            self.graph.file_sizes[source] = file_path.stat().st_size
        except OSError:
            pass

        # Scan for dependencies
        dependencies = self.scan_file(file_path)

        for dep in dependencies:
            normalized_dep = self.normalize_path(dep)
            # Only add if normalized path is valid and different from source
            if normalized_dep and normalized_dep != source and len(normalized_dep) >= 3:
                self.graph.add_dependency(source, normalized_dep)

        # Check if this is an agent file
        if file_path.name in AGENT_FILES:
            agent_name = file_path.stem.split('.')[0]  # Extract agent name (e.g., "yuuji" from "yuuji.agent.md")
            for dep in dependencies:
                normalized_dep = self.normalize_path(dep)
                # Only add valid, non-empty dependencies
                if normalized_dep and len(normalized_dep) >= 3:
                    self.graph.add_agent_dependency(agent_name, normalized_dep)

    def scan_full_project(self) -> None:
        """Scan the entire DZP project."""
        print("Scanning DZP project for dependencies...")

        # Scan protocol directory
        self.scan_directory(PROTOCOL_DIR, "**/*.md")
        self.scan_directory(PROTOCOL_DIR, "**/*.yaml")

        # Scan scripts directory
        self.scan_directory(SCRIPTS_DIR, "**/*.py")

        # Scan state directory
        self.scan_directory(STATE_DIR, "**/*.json")
        self.scan_directory(STATE_DIR, "**/*.py")
        self.scan_directory(STATE_DIR, "**/*.md")

        # Scan project root config files
        for file_path in self.project_root.glob("*.yaml"):
            self.scan_and_add(file_path)

        for file_path in self.project_root.glob("*.json"):
            self.scan_and_add(file_path)

        print(f"✅ Scan complete: {len(self.graph.dependencies)} files analyzed")


# =============================================================================
# Impact Analysis
# =============================================================================

class ImpactAnalyzer:
    """Analyzes the impact of changing files."""

    def __init__(self, graph: DependencyGraph):
        """Initialize with dependency graph."""
        self.graph = graph

    def analyze_impact(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze impact of changing a file.

        Returns:
            Dictionary with impact metrics
        """
        # Normalize path
        file_path = file_path.replace('\\', '/')

        # Get direct and indirect dependencies
        direct_deps = self.graph.get_direct_dependencies(file_path)
        all_deps = self.graph.get_all_dependencies(file_path)

        # Get reverse dependencies (who depends on this file)
        direct_reverse = self.graph.get_reverse_dependencies(file_path)
        all_reverse = self.graph.get_all_reverse_dependencies(file_path)

        # Calculate blast radius
        blast_radius = len(all_reverse)

        # Determine risk level
        if blast_radius == 0:
            risk_level = "MINIMAL"
        elif blast_radius <= 3:
            risk_level = "LOW"
        elif blast_radius <= 10:
            risk_level = "MEDIUM"
        elif blast_radius <= 20:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Check if file is critical
        is_critical = any(file_path.endswith(cf) for cf in CRITICAL_FILES)

        # Find affected agents
        affected_agents = []
        for agent, files in self.graph.agent_dependencies.items():
            if file_path in files or any(dep in files for dep in all_deps):
                affected_agents.append(agent)

        return {
            "file_path": file_path,
            "blast_radius": blast_radius,
            "risk_level": risk_level,
            "is_critical": is_critical,
            "direct_dependencies": len(direct_deps),
            "total_dependencies": len(all_deps),
            "direct_reverse_dependencies": len(direct_reverse),
            "total_reverse_dependencies": len(all_reverse),
            "affected_agents": affected_agents,
            "dependency_list": sorted(list(all_reverse))
        }


# =============================================================================
# Report Generators
# =============================================================================

class ReportGenerator:
    """Generates various dependency reports."""

    def __init__(self, graph: DependencyGraph, analyzer: ImpactAnalyzer):
        """Initialize with graph and analyzer."""
        self.graph = graph
        self.analyzer = analyzer

    def generate_impact_report(self, file_path: str) -> None:
        """Generate impact analysis report for a file."""
        impact = self.analyzer.analyze_impact(file_path)

        print("\n" + "═" * 80)
        print(f"DEPENDENCY ANALYSIS: {impact['file_path']}")
        print("═" * 80)

        # File type
        file_type = self.graph.file_types.get(file_path, "Unknown")
        print(f"\nFILE TYPE: {file_type}")
        print(f"BLAST RADIUS: {impact['risk_level']}")
        print(f"RISK LEVEL: {impact['risk_level']}")

        if impact['is_critical']:
            print("⚠️  CRITICAL FILE - Extra caution required")

        # Direct dependencies
        print(f"\nDIRECT DEPENDENCIES ({impact['direct_dependencies']}):")
        for dep in sorted(list(self.graph.get_direct_dependencies(file_path))):
            print(f"  → {dep}")

        # Reverse dependencies
        print(f"\nDIRECT REVERSE DEPENDENCIES ({impact['direct_reverse_dependencies']}):")
        reverse_deps = self.graph.get_reverse_dependencies(file_path)
        if reverse_deps:
            for dep in sorted(list(reverse_deps)):
                print(f"  ← {dep}")
        else:
            print("  (none)")

        # Affected agents
        if impact['affected_agents']:
            print(f"\nAFFECTED AGENTS ({len(impact['affected_agents'])}):")
            for agent in sorted(impact['affected_agents']):
                print(f"  ✓ {agent}")

        # Recommendations
        print("\nRECOMMENDATIONS:")
        if impact['risk_level'] in ['HIGH', 'CRITICAL']:
            print("  ⚠️  HIGH IMPACT - Create Tier 3 snapshot before modifying")
            print(f"  📸 Suggested: python scripts/create-snapshot.py --manual --tier 3 --description \"Before modifying {file_path}\"")
            print("  🔒 Suggested: Test changes in isolated branch first")
        elif impact['risk_level'] == 'MEDIUM':
            print("  ⚠️  MEDIUM IMPACT - Create Tier 2 snapshot recommended")
            print(f"  📸 Suggested: python scripts/create-snapshot.py --manual --tier 2")
        else:
            print("  ✅ LOW IMPACT - Safe to modify with normal backup procedures")

        print("\n" + "═" * 80)

    def generate_cycle_report(self) -> None:
        """Generate circular dependency report."""
        cycles = self.graph.detect_cycles()

        print("\n" + "═" * 80)
        print("CIRCULAR DEPENDENCY SCAN RESULTS")
        print("═" * 80)

        if not cycles:
            print("\n✅ NO CIRCULAR DEPENDENCIES DETECTED")
            print("\nYour dependency graph is acyclic. Well done!")
        else:
            print(f"\n❌ {len(cycles)} CIRCULAR DEPENDENC{'Y' if len(cycles) == 1 else 'IES'} DETECTED:")

            for i, cycle in enumerate(cycles, 1):
                print(f"\nCYCLE #{i} (LENGTH: {len(cycle) - 1}):")
                for j, node in enumerate(cycle):
                    if j < len(cycle) - 1:
                        print(f"  {node}")
                        print(f"    ↓")
                    else:
                        print(f"  {node} ← LOOP DETECTED")

                # Severity assessment
                cycle_length = len(cycle) - 1
                if cycle_length <= 2:
                    severity = "HIGH"
                elif cycle_length <= 4:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

                print(f"\nSEVERITY: {severity}")
                print("\nRECOMMENDATION:")
                print("  💡 Break cycle by extracting shared configuration")
                print("  💡 Use one-way dependency flow")
                print("  💡 Consider refactoring to remove circular reference")

        print("\n" + "═" * 80)

    def generate_agent_matrix(self) -> None:
        """Generate agent dependency matrix."""
        print("\n" + "═" * 80)
        print("AGENT DEPENDENCY MATRIX")
        print("═" * 80)

        if not self.graph.agent_dependencies:
            print("\n⚠️  No agent dependencies detected")
            return

        for agent in sorted(self.graph.agent_dependencies.keys()):
            files = self.graph.agent_dependencies[agent]
            print(f"\n{agent.upper()} ({len(files)} files):")
            for file_path in sorted(files):
                print(f"  → {file_path}")

        print("\n" + "═" * 80)

    def export_json(self, output_path: Path) -> None:
        """Export dependency graph to JSON."""
        data = {
            "dependencies": {k: list(v) for k, v in self.graph.dependencies.items()},
            "reverse_dependencies": {k: list(v) for k, v in self.graph.reverse_dependencies.items()},
            "agent_dependencies": {k: list(v) for k, v in self.graph.agent_dependencies.items()},
            "file_types": self.graph.file_types,
            "file_sizes": self.graph.file_sizes
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Dependency graph exported to {output_path}")


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Domain Zero Protocol - Dependency Scanner & Impact Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scan                                    Scan entire project
  %(prog)s --analyze .protocol-state/project-state.json   Analyze specific file
  %(prog)s --check-cycles                            Detect circular dependencies
  %(prog)s --agent-matrix                            Show agent dependency matrix
  %(prog)s --export dependency-graph.json            Export graph to JSON

Performance:
  Target scan time: <10 seconds for full project
  Circular dependency detection: DFS algorithm (O(V+E))
  Impact analysis: BFS traversal (O(V+E))
        """
    )

    parser.add_argument('--scan', action='store_true',
                        help='Scan entire DZP project')
    parser.add_argument('--analyze', type=str, metavar='FILE',
                        help='Analyze impact of specific file')
    parser.add_argument('--check-cycles', action='store_true',
                        help='Detect circular dependencies')
    parser.add_argument('--agent-matrix', action='store_true',
                        help='Show agent dependency matrix')
    parser.add_argument('--export', type=str, metavar='OUTPUT',
                        help='Export dependency graph to JSON')

    args = parser.parse_args()

    try:
        # Create scanner
        scanner = DependencyScanner()

        # Always scan first (required for all operations)
        if args.scan or args.analyze or args.check_cycles or args.agent_matrix or args.export:
            scanner.scan_full_project()

        # Create analyzer and reporter
        analyzer = ImpactAnalyzer(scanner.graph)
        reporter = ReportGenerator(scanner.graph, analyzer)

        # Execute requested operation
        if args.analyze:
            reporter.generate_impact_report(args.analyze)

        if args.check_cycles:
            reporter.generate_cycle_report()

        if args.agent_matrix:
            reporter.generate_agent_matrix()

        if args.export:
            output_path = Path(args.export)
            reporter.export_json(output_path)

        # If only --scan was requested, show summary
        if args.scan and not (args.analyze or args.check_cycles or args.agent_matrix or args.export):
            print(f"\n✅ Scan complete")
            print(f"   Files analyzed: {len(scanner.graph.dependencies)}")
            print(f"   Dependencies found: {sum(len(v) for v in scanner.graph.dependencies.values())}")
            print(f"   Agents tracked: {len(scanner.graph.agent_dependencies)}")
            print(f"\nUse --analyze, --check-cycles, --agent-matrix, or --export for detailed reports")

        # If no arguments, show help
        if not any([args.scan, args.analyze, args.check_cycles, args.agent_matrix, args.export]):
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
