# Claude Code Permissions Schema

This document explains the permission model used in `.claude/settings.local.json`.

## Overview

The permissions system controls which commands Claude Code can execute without asking for user confirmation. This file is **gitignored** and local-only, so each developer can set their own comfort level.

## Structure

```json
{
  "permissions": {
    "allow": [],   // Commands Claude can run automatically
    "deny": [],    // Commands Claude must never run
    "ask": []      // Commands that require explicit user confirmation
  }
}
```

## Permission Format

Permissions use the format: `Tool(action:pattern)`

- **Tool**: The tool name (e.g., `Bash`, `Edit`, `Write`)
- **action**: The command or operation
- **pattern**: Optional wildcard pattern using `*`

### Examples

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",           // Allow all git status commands
      "Bash(git commit -m:*)",        // Allow git commit with message
      "Bash(npm test:*)",             // Allow running tests
      "Bash(find:*)"                  // Allow all find commands
    ],
    "deny": [
      "Bash(git push --force:*)",     // Block force push
      "Bash(rm -rf:*)",               // Block recursive delete
      "Bash(git reset --hard:*)"      // Block hard reset
    ],
    "ask": [
      "Bash(npm install:*)",          // Ask before installing packages
      "Write(*)"                      // Ask before creating new files
    ]
  }
}
```

## Wildcard Patterns

The `*` wildcard matches any arguments:

- `git commit:*` → Matches `git commit -m "..."`, `git commit --amend`, etc.
- `npm:*` → Matches any npm command
- `Tool(*)` → Matches any use of that tool

## Evaluation Order

Permissions are evaluated in this priority order:

1. **deny** (highest priority) - Blocks commands even if allowed elsewhere
2. **ask** - Prompts for confirmation
3. **allow** - Executes without prompting
4. **default behavior** - If no rule matches, Claude will ask for permission

## Security Considerations

### Git Operations

Be careful with wildcards on git commands:

```json
// ❌ TOO BROAD - allows dangerous operations
"Bash(git:*)"

// ✅ SPECIFIC - safer approach
"Bash(git status:*)",
"Bash(git diff:*)",
"Bash(git log:*)",
"Bash(git add:*)",
"Bash(git commit -m:*)"

// ✅ EXPLICIT DENY for dangerous operations
"deny": [
  "Bash(git push --force:*)",
  "Bash(git reset --hard:*)",
  "Bash(git clean -fd:*)"
]
```

### File Operations

```json
// ❌ Allows unrestricted file creation
"Write(*)"

// ✅ Require confirmation for file operations
"ask": ["Write(*)"]
```

### Command Execution

```json
// ❌ Too permissive
"Bash(*)"

// ✅ Specific commands only
"allow": [
  "Bash(npm test:*)",
  "Bash(npm run build:*)",
  "Bash(git status:*)"
]
```

## Default Configuration

The current `.claude/settings.local.json` includes:

```json
{
  "permissions": {
    "allow": [
      "Bash(git commit:*)",  // Allows all git commit operations
      "Bash(find:*)",        // Allows all find operations
      "Bash(git add:*)"      // Allows staging files
    ]
  }
}
```

### Notes on Current Permissions

- **`git commit:*`** - This wildcard permits all commit operations, including:
  - `git commit -m "message"`
  - `git commit --amend`
  - `git commit --no-verify` (bypasses pre-commit hooks)

  If you want to restrict this, consider narrowing to specific flags:
  ```json
  "Bash(git commit -m:*)",     // Only allow commits with message
  "Bash(git commit --amend:*)" // Only allow amending
  ```

- **`find:*`** - Allows file system searches. Generally safe for read-only operations.

- **`git add:*`** - Allows staging any files. Generally safe, but be aware it can stage sensitive files if not careful.

## Recommended Configurations

### Conservative (High Security)

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)"
    ],
    "ask": [
      "Bash(git commit:*)",
      "Bash(git add:*)",
      "Write(*)",
      "Edit(*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)"
    ]
  }
}
```

### Balanced (Development Workflow)

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git add:*)",
      "Bash(git commit -m:*)",
      "Bash(npm test:*)",
      "Bash(find:*)"
    ],
    "ask": [
      "Bash(git push:*)",
      "Bash(npm install:*)",
      "Write(*)"
    ],
    "deny": [
      "Bash(git push --force:*)",
      "Bash(rm -rf:*)"
    ]
  }
}
```

### Permissive (Low Friction)

```json
{
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(npm:*)",
      "Edit(*)",
      "Read(*)"
    ],
    "deny": [
      "Bash(rm -rf /:*)",  // Still block system-wide deletion
      "Bash(git push --force main:*)"  // Still block force push to main
    ]
  }
}
```

## Troubleshooting

### Claude keeps asking for permission

If Claude is asking for permission on commands you've allowed, check:

1. Exact command match - permissions are case-sensitive and must match the exact command pattern
2. Wildcard placement - ensure `*` is in the right position
3. Tool name - verify you're using the correct tool name (`Bash` vs `bash`)

### Commands are being blocked

Check your `deny` rules first - they have highest priority. If a command matches both `allow` and `deny`, it will be blocked.

## Further Reading

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [GitHub Repository](https://github.com/anthropics/claude-code)
