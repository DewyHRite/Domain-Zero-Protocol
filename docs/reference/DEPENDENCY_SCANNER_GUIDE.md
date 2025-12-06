# Dependency Scanner Guide

**Version**: 1.0.0
**Created**: 2025-12-06
**Part of**: DZP v8.8.0 Validation Framework - Phase 3

## Overview

The Dependency Scanner analyzes relationships between files, agents, and tasks in the Domain Zero Protocol to help you understand the impact of changes and detect potential problems.

## Quick Start

```bash
# Scan entire project
python scripts/dependency-scanner.py --scan

# Analyze specific file
python scripts/dependency-scanner.py --scan --analyze .protocol-state/project-state.json

# Detect circular dependencies
python scripts/dependency-scanner.py --scan --check-cycles

# View agent dependency matrix
python scripts/dependency-scanner.py --scan --agent-matrix

# Export to JSON for external tools
python scripts/dependency-scanner.py --scan --export dependency-graph.json
```

## Features

### 1. Dependency Graph Construction

The scanner builds a comprehensive dependency graph by analyzing:

- **Python files** (`.py`): Import statements, Path() calls, file path strings
- **JSON files** (`.json`): File path references in values
- **Markdown files** (`.md`): Links, code blocks, quoted paths
- **YAML files** (`.yaml`, `.yml`): File path references

**Supported Dependency Types**:
- Agent → File (which agents read/write which files)
- File → File (which files reference other files)
- Task → Task (which tasks depend on other tasks)

### 2. Impact Analysis

Answers the question: **"If I change this file, what breaks?"**

```bash
python scripts/dependency-scanner.py --scan --analyze <file-path>
```

**Output**:
- File type and classification
- Blast radius (MINIMAL/LOW/MEDIUM/HIGH/CRITICAL)
- Risk level assessment
- Direct dependencies (files this file depends on)
- Reverse dependencies (files that depend on this file)
- Affected agents
- Actionable recommendations

**Example Output**:
```
═══════════════════════════════════════════════════════════════
DEPENDENCY ANALYSIS: .protocol-state/project-state.json
═══════════════════════════════════════════════════════════════

FILE TYPE: .json
BLAST RADIUS: CRITICAL
RISK LEVEL: CRITICAL
⚠️  CRITICAL FILE - Extra caution required

DIRECT DEPENDENCIES (1):
  → .protocol-state/system-update-framework/

DIRECT REVERSE DEPENDENCIES (54):
  ← protocol/CLAUDE.md
  ← protocol/gojo.agent.md
  ← scripts/verify-installation.py
  ... (51 more)

AFFECTED AGENTS (2):
  ✓ gojo
  ✓ sukuna

RECOMMENDATIONS:
  ⚠️  HIGH IMPACT - Create Tier 3 snapshot before modifying
  📸 Suggested: python scripts/create-snapshot.py --manual --tier 3
  🔒 Suggested: Test changes in isolated branch first

═══════════════════════════════════════════════════════════════
```

### 3. Circular Dependency Detection

Detects problematic dependency loops using DFS (Depth-First Search) algorithm.

```bash
python scripts/dependency-scanner.py --scan --check-cycles
```

**Circular Dependencies**:
```
project-state.json → tier-enforcement.py → validation-state.json → project-state.json
└────────────────────────── CIRCULAR LOOP ──────────────────────────┘
```

**Output**:
- Number of cycles detected
- Each cycle visualized step-by-step
- Severity assessment (HIGH/MEDIUM/LOW based on cycle length)
- Recommendations to break the cycle

**Severity Levels**:
- **HIGH**: 2-node cycles (A → B → A)
- **MEDIUM**: 3-4 node cycles
- **LOW**: 5+ node cycles

### 4. Agent Dependency Matrix

Shows which files each agent depends on.

```bash
python scripts/dependency-scanner.py --scan --agent-matrix
```

**Output**:
```
═══════════════════════════════════════════════════════════════
AGENT DEPENDENCY MATRIX
═══════════════════════════════════════════════════════════════

YUUJI (42 files):
  → protocol/CLAUDE.md
  → protocol.config.yaml
  → .protocol-state/project-state.json
  → .protocol-state/session-state.json
  ... (38 more)

MEGUMI (38 files):
  → protocol/CLAUDE.md
  → protocol.config.yaml
  ... (36 more)

... (7 more agents)

═══════════════════════════════════════════════════════════════
```

### 5. Export to JSON

Export the entire dependency graph for visualization tools or custom analysis.

```bash
python scripts/dependency-scanner.py --scan --export dependency-graph.json
```

**JSON Structure**:
```json
{
  "dependencies": {
    "file.py": ["dependency1.json", "dependency2.yaml"]
  },
  "reverse_dependencies": {
    "dependency1.json": ["file.py", "other.py"]
  },
  "agent_dependencies": {
    "yuuji": ["protocol/CLAUDE.md", "project-state.json"],
    "megumi": ["protocol/CLAUDE.md", "validation-rules.yaml"]
  },
  "file_types": {
    "file.py": ".py",
    "dependency1.json": ".json"
  },
  "file_sizes": {
    "file.py": 15234,
    "dependency1.json": 2048
  }
}
```

## Use Cases

### Before Major Refactoring

```bash
# Check impact before changing session-state.json
python scripts/dependency-scanner.py --scan --analyze .protocol-state/session-state.json
```

**Decision**: If blast radius is HIGH or CRITICAL, create Tier 3 snapshot first.

### During Protocol Updates

```bash
# Check for new circular dependencies after changes
python scripts/dependency-scanner.py --scan --check-cycles
```

**Decision**: If new cycles detected, refactor to break them before committing.

### Planning Parallel Work

```bash
# View agent dependencies to identify independent work
python scripts/dependency-scanner.py --scan --agent-matrix
```

**Decision**: Tasks affecting different agents with no shared files can run in parallel.

### Code Review

```bash
# Analyze blast radius of files in a pull request
python scripts/dependency-scanner.py --scan --analyze <changed-file>
```

**Decision**: High-impact changes require extra scrutiny and testing.

## Risk Levels

The scanner assesses risk based on **blast radius** (number of reverse dependencies):

| Blast Radius | Risk Level | Recommendation |
|--------------|-----------|----------------|
| 0 files | MINIMAL | Safe to modify with normal backups |
| 1-3 files | LOW | Create Tier 1 snapshot recommended |
| 4-10 files | MEDIUM | Create Tier 2 snapshot recommended |
| 11-20 files | HIGH | Create Tier 3 snapshot + branch testing |
| 21+ files | CRITICAL | Tier 3 snapshot + thorough testing + gradual rollout |

## Performance

- **Full scan**: <10 seconds for ~300 files
- **Circular dependency detection**: O(V+E) using DFS
- **Impact analysis**: O(V+E) using BFS
- **Memory usage**: ~50MB for typical DZP installation

## Algorithms

### Dependency Graph Construction

1. **File Discovery**: Glob pattern matching for all `.py`, `.json`, `.md`, `.yaml` files
2. **Content Scanning**:
   - Python: AST parsing + regex fallback
   - JSON: Recursive value extraction
   - Markdown: Link extraction + code block scanning
   - YAML: String value extraction
3. **Path Normalization**: Convert to relative paths from project root
4. **Graph Building**: Add edges to dependency graph

### Circular Dependency Detection (DFS)

```
function detect_cycles(graph):
    visited = empty_set
    rec_stack = empty_list
    cycles = empty_list

    for each node in graph:
        if node not in visited:
            dfs(node, visited, rec_stack, cycles)

    return cycles

function dfs(node, visited, rec_stack, cycles):
    if node in rec_stack:
        # Found a cycle
        cycle = rec_stack[rec_stack.index(node):] + [node]
        cycles.append(cycle)
        return

    if node in visited:
        return

    visited.add(node)
    rec_stack.append(node)

    for each neighbor of node:
        dfs(neighbor, visited, rec_stack, cycles)

    rec_stack.pop()
```

### Impact Analysis (BFS)

```
function analyze_impact(file, graph):
    # Get all files that depend on this file (reverse dependencies)
    reverse_deps = bfs_traversal(file, graph.reverse_dependencies)

    blast_radius = len(reverse_deps)
    risk_level = calculate_risk(blast_radius)

    # Find affected agents
    affected_agents = []
    for agent, files in agent_dependencies:
        if file in files or any(dep in files for dep in reverse_deps):
            affected_agents.append(agent)

    return {
        blast_radius,
        risk_level,
        affected_agents,
        reverse_deps
    }

function bfs_traversal(start_node, graph):
    visited = empty_set
    queue = [start_node]

    while queue is not empty:
        node = queue.pop_front()

        if node in visited:
            continue

        visited.add(node)

        for each neighbor of node:
            if neighbor not in visited:
                queue.append(neighbor)

    return visited - {start_node}
```

## Troubleshooting

### Scanner Running Slowly

**Symptoms**: Scan takes >30 seconds

**Causes**:
- Very large files (>1MB)
- Many files in project (>1000)
- Slow disk I/O

**Solutions**:
- Exclude large files (modify glob patterns)
- Use SSD instead of HDD
- Run on files changed recently only

### False Positive Dependencies

**Symptoms**: Unrelated files shown as dependencies

**Causes**:
- Markdown content contains file-like strings
- Code examples include path strings
- Comments reference files

**Solutions**:
- These are filtered automatically (path normalization)
- Check that extracted paths are valid (>= 3 chars, contain `.` or `/`)
- If issue persists, adjust regex patterns in scanners

### Missing Dependencies

**Symptoms**: Known dependencies not detected

**Causes**:
- Dynamic path construction (e.g., `Path(var1 + var2)`)
- Non-standard file references
- Obfuscated paths

**Solutions**:
- Scanner detects static references only
- Add manual documentation for dynamic dependencies
- Consider refactoring to use static paths

### Circular Dependencies in Documentation

**Symptoms**: Many cycles detected, all involving `.md` files

**Causes**:
- Documentation files cross-reference each other
- This is normal and usually harmless

**Impact**:
- **Code files**: Fix immediately (can cause runtime issues)
- **Documentation files**: Usually safe (just cross-references)

**Decision**: Focus on fixing cycles involving `.py`, `.json`, or `.yaml` files first.

## Integration with Other Tools

### With Validation Engine

```bash
# Validate all dependencies of a file
python scripts/dependency-scanner.py --scan --analyze <file> > deps.txt
cat deps.txt | grep "→" | while read line; do
    file=$(echo $line | cut -d' ' -f2)
    python scripts/validate-protocol.py --check --file "$file"
done
```

### With Snapshot System

```bash
# Create snapshot before modifying high-impact file
impact=$(python scripts/dependency-scanner.py --scan --analyze <file> | grep "RISK LEVEL:")

if [[ "$impact" == *"CRITICAL"* ]] || [[ "$impact" == *"HIGH"* ]]; then
    python scripts/create-snapshot.py --manual --tier 3 --description "Before modifying <file>"
fi
```

### With Git

```bash
# Analyze files in current PR
git diff --name-only main | while read file; do
    python scripts/dependency-scanner.py --scan --analyze "$file"
done
```

## Best Practices

### 1. Run Before Major Changes

Always analyze impact before modifying core files:

```bash
python scripts/dependency-scanner.py --scan --analyze <file-to-modify>
```

### 2. Check for New Cycles Regularly

Run cycle detection after protocol updates:

```bash
python scripts/dependency-scanner.py --scan --check-cycles
```

### 3. Document High-Impact Files

If a file has CRITICAL blast radius, add a comment/docstring warning:

```python
"""
⚠️  CRITICAL FILE - 50+ dependencies
Run impact analysis before modifying:
  python scripts/dependency-scanner.py --scan --analyze <this-file>
"""
```

### 4. Export for Team Review

Share dependency graph with team for architectural discussions:

```bash
python scripts/dependency-scanner.py --scan --export team-review-deps.json
```

### 5. Integrate into CI/CD

Add dependency analysis to your CI pipeline:

```yaml
# GitHub Actions example
- name: Check Dependencies
  run: |
    python scripts/dependency-scanner.py --scan --check-cycles
    if [ $? -ne 0 ]; then
      echo "Circular dependencies detected!"
      exit 1
    fi
```

## Limitations

### Dynamic Dependencies Not Detected

The scanner can only detect **static** file references. Dynamic paths constructed at runtime are not detected:

```python
# ✅ Detected
file_path = Path(".protocol-state/project-state.json")

# ❌ Not detected
dir_name = ".protocol-state"
file_name = "project-state.json"
file_path = Path(dir_name) / file_name
```

**Workaround**: Document dynamic dependencies manually or refactor to static paths.

### External Dependencies Not Tracked

The scanner only analyzes files within the project root. External dependencies (pip packages, system libraries) are not tracked.

### Markdown Content May Create Noise

Documentation files often contain code examples and file references that aren't actual dependencies. The scanner filters aggressively but some noise may remain.

## Future Enhancements

Potential improvements for future versions:

1. **Visual Dependency Graph**: Generate interactive HTML visualization
2. **Diff Mode**: Compare dependency graphs between commits
3. **Watch Mode**: Continuous monitoring for dependency changes
4. **Plugin System**: Custom scanners for additional file types
5. **Performance Optimization**: Incremental scanning (only changed files)
6. **Dependency Metrics**: Calculate coupling scores, stability metrics

## Support

For issues or questions:

1. Check this guide first
2. Review `scripts/dependency-scanner.py` source code
3. Run with `--help` flag for CLI options
4. Check Phase 3 documentation in plan-documentation.md

---

**Remember**: The dependency scanner is **analysis only** - it never modifies files. It's safe to run at any time.
