<!-- [CORE FILE] - Domain Zero Protocol v8.10.0 -->
# Memory Tool Configuration Guide
## Enabling Claude Memory Tool Beta for DZP v8.10.0

**Version**: 8.10.0
**Purpose**: Instructions for enabling Claude Memory Tool API (beta) for persistent cross-session memory
**Required For**: DZP v8.8.0 validation framework and agent memory persistence

---

## Overview

The Memory Tool enables DZP agents to persist information across conversations through client-side file operations. This provides:
- Persistent agent memory across sessions
- Context snapshots that survive context clears
- Learned patterns and successful strategies
- Validation metrics and state tracking

**API Status**: Beta (as of December 2025)
**Required Models**: Claude Sonnet 4.5, Opus 4.5, Haiku 4.5 (or newer)

---

## Configuration by Platform

### Claude Code (VS Code Extension)

Memory Tool is **automatically available** in Claude Code when using supported models.

**No additional configuration needed** - the Memory Tool is enabled by default in Claude Code for:
- Claude Sonnet 4.5 (claude-sonnet-4-5-20251022)
- Claude Opus 4.5 (claude-opus-4-5-20251101)
- Claude Haiku 4.5

**Verification**:
```javascript
// Check if Memory Tool is available
// In Claude Code, invoke any agent and it will automatically have access to:
// - view /memories/path
// - create /memories/path {content}
// - str_replace /memories/path old new
// - insert /memories/path line {text}
// - delete /memories/path
// - rename /memories/old /memories/new
```

---

### Claude.ai (Web Interface)

Memory Tool is **automatically available** in Claude.ai web interface when using supported models.

**No additional configuration needed** - Claude.ai automatically enables Memory Tool for supported models.

**Verification**:
- Start a conversation with Claude Sonnet 4.5 or Opus 4.5
- Invoke a DZP agent (e.g., "Read gojo.agent.md")
- The agent will automatically have access to Memory Tool operations

---

### Anthropic API (Direct Integration)

If you're using the Anthropic API directly (custom client, SDK integration), you need to enable the Memory Tool beta.

**Required Headers**:
```python
import anthropic

client = anthropic.Anthropic(
    api_key="your-api-key"
)

# Enable Memory Tool beta
headers = {
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "context-management-2025-06-27"  # Memory Tool beta
}

# Example API call with Memory Tool enabled
message = client.messages.create(
    model="claude-sonnet-4-5-20251022",
    max_tokens=4096,
    extra_headers=headers,  # Include beta header
    tools=[
        {
            "type": "memory_20250818",  # Memory Tool type
            "name": "memory"
        },
        # ... other tools (read, write, edit, bash, etc.)
    ],
    messages=[
        {
            "role": "user",
            "content": "Read gojo.agent.md"
        }
    ]
)
```

**TypeScript/JavaScript**:
```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const message = await client.messages.create({
  model: 'claude-sonnet-4-5-20251022',
  max_tokens: 4096,
  extra_headers: {
    'anthropic-version': '2023-06-01',
    'anthropic-beta': 'context-management-2025-06-27',
  },
  tools: [
    {
      type: 'memory_20250818',
      name: 'memory',
    },
    // ... other tools
  ],
  messages: [
    {
      role: 'user',
      content: 'Read gojo.agent.md',
    },
  ],
});
```

---

## Memory Tool Operations

Once enabled, DZP agents have access to six Memory Tool operations:

| Operation | Syntax | Description |
|-----------|--------|-------------|
| **view** | `view /memories/path` | Display directory or file contents |
| **create** | `create /memories/path {content}` | Create or overwrite file |
| **str_replace** | `str_replace /memories/path old new` | Replace specific text |
| **insert** | `insert /memories/path line {text}` | Insert text at line number |
| **delete** | `delete /memories/path` | Remove file or directory |
| **rename** | `rename /memories/old /memories/new` | Move or rename file |

---

## DZP Memory Directory Structure

DZP v8.8.0 uses this standardized memory structure:

```text
/memories/
├── agents/
│   ├── yuuji/
│   │   ├── implementation-patterns.json
│   │   ├── test-templates.yaml
│   │   └── session-context.json
│   ├── megumi/
│   │   ├── vulnerability-database.json
│   │   ├── remediation-patterns.yaml
│   │   └── review-history.json
│   ├── nobara/
│   │   ├── design-patterns.json
│   │   ├── accessibility-rules.yaml
│   │   └── user-research.json
│   ├── gojo/
│   │   ├── project-state.json
│   │   ├── session-state.json
│   │   └── trigger-19-observations.json
│   └── sukuna/
│       ├── validation-rules.yaml
│       ├── metrics.json
│       └── tuning-history.json
│
├── validation/
│   ├── snapshots/
│   │   └── snapshot-[ISO-8601].json
│   ├── validation-state.json
│   └── learned-rules.yaml
│
└── project/
    ├── tier-config.yaml
    └── protocol-config.yaml
```

---

## Security & Path Validation

**CRITICAL**: All Memory Tool operations are restricted to the `/memories/` directory for security.

**Built-in Security**:
- ✅ Paths must start with `/memories/`
- ✅ Directory traversal attacks prevented (no `..` sequences)
- ✅ Canonical path resolution enforced
- ✅ Whitelist-based directory access

**DZP automatically validates all paths** - no additional security configuration needed.

---

## Verification & Testing

### Test 1: Check Memory Tool Availability

Start a DZP agent and verify Memory Tool access:

```text
User: "Read gojo.agent.md"
Gojo: [Gojo should be able to view /memories/agents/gojo/]
```

If Memory Tool is working, Gojo will check `/memories/agents/gojo/` on startup.

### Test 2: Create Test Memory File

```text
User: "Create a test memory file at /memories/test.txt with content 'Hello DZP'"
```

Expected: File created successfully with no errors.

### Test 3: View Memory Directory

```text
User: "View /memories/ directory"
```

Expected: Should see directory listing with agents/, validation/, project/ subdirectories.

---

## Troubleshooting

### Error: "Memory Tool not available"

**Cause**: Model doesn't support Memory Tool or beta not enabled
**Solution**:
1. Verify using Claude Sonnet 4.5, Opus 4.5, or Haiku 4.5
2. If using Anthropic API directly, add beta header: `anthropic-beta: context-management-2025-06-27`
3. Check tool definition includes `type: "memory_20250818"`

### Error: "Path validation failed"

**Cause**: Path doesn't start with `/memories/`
**Solution**: All DZP memory operations must use paths starting with `/memories/`

**Correct**:
```text
view /memories/agents/yuuji/session-context.json
```

**Incorrect**:
```text
view /session-context.json  # Missing /memories/ prefix
view ../memories/  # Directory traversal not allowed
```

### Error: "Directory not found"

**Cause**: Memory directory structure not initialized
**Solution**: DZP v8.8.0 automatically initializes `/memories/` on first run. If seeing this error:
1. Invoke Gojo: "Read gojo.agent.md"
2. Enable validation when prompted
3. Gojo will initialize `/memories/` structure

---

## Performance Considerations

Memory Tool operations add minimal latency:
- `view`: ~50-100ms
- `create/str_replace`: ~100-200ms
- `delete/rename`: ~50ms

**DZP Optimization**:
- Lazy loading (only read when needed)
- Batch operations (combine multiple updates)
- Caching (keep frequently accessed data in-context)
- Selective persistence (only write changed fields)

**Target Performance** (DZP v8.8.0):
- Memory read on startup: <200ms
- Memory update on change: <300ms
- Session state persistence: <500ms total

---

## Context Management Integration

**Memory Tool + Context Editing**:

When context approaches limits, Claude automatically:
1. Preserves critical info to `/memories/`
2. Clears old tool results
3. Reads back from `/memories/` to restore context
4. Continues work indefinitely

**Configuration** (optional, for custom integrations):
```json
{
  "context_editing": {
    "enabled": true,
    "exclude_tools": ["memory"],
    "preserve_to_memory": [
      "/memories/agents/*/session-context.json",
      "/memories/validation/validation-state.json"
    ]
  }
}
```

---

## Advanced: Custom Memory Backends

For enterprise deployments, you can implement custom Memory Tool backends:

**Supported Backends**:
- Local filesystem (default)
- Amazon S3
- Google Cloud Storage
- Azure Blob Storage
- Encrypted storage

**Implementation**:
See Anthropic's Memory Tool documentation for subclassing `BetaAbstractMemoryTool` (Python) or `betaMemoryTool` (TypeScript).

**DZP Compatibility**: Custom backends must maintain `/memories/` directory structure for compatibility with DZP v8.8.0.

---

## Migration Guide: Local State → Memory Tool

**Purpose**: Migrate existing DZP state files from `.protocol-state/` to `/memories/` for cross-session persistence.

**Migration Status**: **OPTIONAL** - DZP v8.8.0 maintains backward compatibility with local `.protocol-state/` files.

**When to Migrate**:
- ✅ You want persistent memory across sessions
- ✅ You use context editing and need to preserve state
- ✅ You have Claude Sonnet 4.5+ / Opus 4.5+ / Haiku 4.5+
- ❌ Don't migrate if Memory Tool not available on your platform

---

### Migration Prerequisites

### Step 1: Verify Memory Tool Availability

Test Memory Tool access before migrating:
```text
User: "View /memories/ directory"
```

Expected: Directory listing or empty directory (no error).

If you get "Memory Tool not available", see troubleshooting section above.

### Step 2: Check Existing State Files

Identify files to migrate in `.protocol-state/`:
```bash
# Common DZP state files:
.protocol-state/project-state.json         # → /memories/project/project-state.json
.protocol-state/session-state.json         # → /memories/agents/gojo/session-state.json
.protocol-state/validation/validation-state.json # → /memories/validation/validation-state.json
.protocol-state/agents/gojo/observations.json    # → /memories/agents/gojo/observations.json
# ... and other agent state files
```

### Step 3: Create Backup

**CRITICAL**: Always backup before migration.

```bash
# Create timestamped backup
cp -r .protocol-state .protocol-state.backup-$(date +%Y%m%d-%H%M%S)
```

---

### Step-by-Step Migration

#### Platform: Claude Code / Claude.ai

**Migration Process** (via agent invocation):

1. **Invoke Gojo for Migration**:
```text
User: "Read gojo.agent.md and migrate my state files to Memory Tool"
```

2. **Gojo will**:
   - Check Memory Tool availability
   - Read existing `.protocol-state/` files
   - Create `/memories/` directory structure
   - Write state files to `/memories/`
   - Validate migration success
   - Rename old files to `.backup` (not deleted)

3. **Verify Migration**:
```text
User: "View /memories/ directory structure"
```

Expected output:
```text
/memories/
├── agents/
│   └── gojo/
│       ├── project-state.json
│       └── session-state.json
├── validation/
│   └── validation-state.json
└── project/
    └── tier-config.yaml
```

4. **Test Memory Persistence**:
```text
User: "Read gojo.agent.md and check if my project state persisted"
```

Gojo should read from `/memories/` and display current project state.

5. **Cleanup** (after verification):
```text
User: "Remove .protocol-state/ backup files after confirming migration successful"
```

---

#### Platform: Anthropic API (Python)

**Manual Migration Script**:

```python
import anthropic
import json
from pathlib import Path

client = anthropic.Anthropic(api_key="your-api-key")

# Enable Memory Tool beta
headers = {
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "context-management-2025-06-27"
}

def migrate_state_file(local_path: str, memory_path: str):
    """Migrate a single state file to Memory Tool"""

    # 1. Read existing state
    with open(local_path, 'r') as f:
        state_data = json.load(f)

    # 2. Create in Memory Tool
    message = client.messages.create(
        model="claude-sonnet-4-5-20251022",
        max_tokens=4096,
        extra_headers=headers,
        tools=[{"type": "memory_20250818", "name": "memory"}],
        messages=[{
            "role": "user",
            "content": f"create {memory_path} {json.dumps(state_data)}"
        }]
    )

    print(f"✓ Migrated: {local_path} → {memory_path}")
    return message

# Migration mapping
migrations = [
    (".protocol-state/project-state.json", "/memories/project/project-state.json"),
    (".protocol-state/session-state.json", "/memories/agents/gojo/session-state.json"),
    (".protocol-state/validation/validation-state.json", "/memories/validation/validation-state.json"),
]

# Execute migrations
for local_path, memory_path in migrations:
    if Path(local_path).exists():
        migrate_state_file(local_path, memory_path)

        # Backup (don't delete yet)
        backup_path = f"{local_path}.backup"
        Path(local_path).rename(backup_path)
        print(f"✓ Backed up: {local_path} → {backup_path}")

print("\n✓ Migration complete. Verify before removing backups.")
```

**Verification Script**:

```python
def verify_migration(memory_path: str, expected_keys: list):
    """Verify migrated file has expected structure"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20251022",
        max_tokens=4096,
        extra_headers=headers,
        tools=[{"type": "memory_20250818", "name": "memory"}],
        messages=[{
            "role": "user",
            "content": f"view {memory_path}"
        }]
    )

    # Parse response and check for expected keys
    content = message.content[0].text
    data = json.loads(content)

    for key in expected_keys:
        assert key in data, f"Missing key: {key}"

    print(f"✓ Verified: {memory_path}")

# Verify migrations
verify_migration("/memories/project/project-state.json",
                ["project_metadata", "protocol_version", "tier_settings"])
verify_migration("/memories/agents/gojo/session-state.json",
                ["session_id", "started_at", "active_tier"])
```

---

#### Platform: Anthropic API (TypeScript)

**Manual Migration Script**:

```typescript
import Anthropic from '@anthropic-ai/sdk';
import * as fs from 'fs/promises';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

interface Migration {
  localPath: string;
  memoryPath: string;
}

async function migrateStateFile(localPath: string, memoryPath: string): Promise<void> {
  // 1. Read existing state
  const stateData = await fs.readFile(localPath, 'utf-8');
  const state = JSON.parse(stateData);

  // 2. Create in Memory Tool
  const message = await client.messages.create({
    model: 'claude-sonnet-4-5-20251022',
    max_tokens: 4096,
    extra_headers: {
      'anthropic-version': '2023-06-01',
      'anthropic-beta': 'context-management-2025-06-27',
    },
    tools: [{ type: 'memory_20250818', name: 'memory' }],
    messages: [{
      role: 'user',
      content: `create ${memoryPath} ${JSON.stringify(state)}`,
    }],
  });

  console.log(`✓ Migrated: ${localPath} → ${memoryPath}`);
}

async function migrate() {
  const migrations: Migration[] = [
    {
      localPath: '.protocol-state/project-state.json',
      memoryPath: '/memories/project/project-state.json',
    },
    {
      localPath: '.protocol-state/session-state.json',
      memoryPath: '/memories/agents/gojo/session-state.json',
    },
    {
      localPath: '.protocol-state/validation/validation-state.json',
      memoryPath: '/memories/validation/validation-state.json',
    },
  ];

  for (const { localPath, memoryPath } of migrations) {
    try {
      await migrateStateFile(localPath, memoryPath);

      // Backup (don't delete yet)
      await fs.rename(localPath, `${localPath}.backup`);
      console.log(`✓ Backed up: ${localPath} → ${localPath}.backup`);
    } catch (error) {
      console.error(`✗ Failed to migrate ${localPath}:`, error);
    }
  }

  console.log('\n✓ Migration complete. Verify before removing backups.');
}

migrate();
```

---

### Rollback Procedures

If migration fails or causes issues, rollback to local `.protocol-state/`:

**Option 1: Restore from Backup** (if backups exist)

```bash
# Remove Memory Tool files (optional)
# DZP will fall back to local files automatically

# Restore from backup
mv .protocol-state/project-state.json.backup .protocol-state/project-state.json
mv .protocol-state/session-state.json.backup .protocol-state/session-state.json
mv .protocol-state/validation/validation-state.json.backup .protocol-state/validation/validation-state.json

# Verify restoration
ls -la .protocol-state/
```

**Option 2: Disable Memory Tool** (use local files only)

DZP v8.8.0 automatically falls back to `.protocol-state/` if Memory Tool is unavailable.

**No configuration needed** - just ensure `.protocol-state/` files exist.

**Option 3: Hybrid Mode** (keep both)

DZP v8.8.0 supports hybrid mode:
- If `/memories/` files exist → use Memory Tool
- If `/memories/` files missing → fall back to `.protocol-state/`

You can keep both for redundancy during transition period.

---

### Validation Steps

**After migration, verify success**:

### Test 1: Memory Tool Read
```text
User: "Read gojo.agent.md and show me my current project state"
```

Expected: Gojo reads from `/memories/project/project-state.json` and displays state.

### Test 2: Memory Tool Write
```text
User: "Read gojo.agent.md and update my project name to 'Test Migration'"
```

Expected: Gojo updates `/memories/project/project-state.json`.

### Test 3: Session Persistence
```text
# Session 1:
User: "Read gojo.agent.md and create test memory: /memories/test-migration.txt with content 'Session 1'"

# Close session, restart Claude

# Session 2:
User: "Read gojo.agent.md and read /memories/test-migration.txt"
```

Expected: Session 2 successfully reads content created in Session 1.

### Test 4: Data Integrity
```text
User: "Read gojo.agent.md and verify all my project metadata migrated correctly"
```

Expected: Gojo confirms all expected fields present in migrated files.

---

### Common Migration Issues

#### Issue: "Memory Tool path validation failed"

**Cause**: Attempted to access path outside `/memories/`

**Solution**: All migrated files MUST be under `/memories/` prefix.

**Correct**:
- `/memories/project/project-state.json` ✅
- `/memories/agents/gojo/session-state.json` ✅

**Incorrect**:
- `/project-state.json` ❌
- `/.protocol-state/project-state.json` ❌

#### Issue: "JSON parse error after migration"

**Cause**: Data format mismatch or corrupted during transfer

**Solution**:
1. Restore from `.backup` files
2. Verify local file is valid JSON: `cat .protocol-state/project-state.json | jq .`
3. Re-run migration with validated file

#### Issue: "Old state files still being used"

**Cause**: DZP falls back to local files if Memory Tool read fails

**Solution**:
1. Verify Memory Tool working: `view /memories/`
2. Check Memory Tool beta enabled (if using API directly)
3. Rename old files to force Memory Tool usage: `mv .protocol-state .protocol-state.OLD`

#### Issue: "Permission denied writing to /memories/"

**Cause**: Memory Tool not properly enabled or filesystem permissions

**Solution**:
- **Claude Code**: Verify using supported model (Sonnet 4.5+, Opus 4.5+, Haiku 4.5+)
- **Claude.ai**: Refresh session, re-invoke agent
- **Anthropic API**: Verify beta header: `anthropic-beta: context-management-2025-06-27`

#### Issue: "Data lost after session restart"

**Cause**: Files written to local `.protocol-state/` instead of `/memories/`

**Solution**:
1. Verify migration completed: `view /memories/project/`
2. Check for `.backup` files (may indicate incomplete migration)
3. Re-run migration procedure

---

### Post-Migration Checklist

After successful migration:

- [ ] All state files accessible via `/memories/` paths
- [ ] Memory Tool read/write operations working
- [ ] Session persistence verified (test across sessions)
- [ ] Data integrity confirmed (all fields present)
- [ ] Backups created (`.protocol-state.backup-*` exists)
- [ ] Old files renamed to `.backup` (safety net)
- [ ] Test rollback procedure (verify you can restore)
- [ ] Remove backups after 1-2 weeks of stable operation (optional)

---

### Migration Benefits

After migration to Memory Tool:

✅ **Cross-Session Persistence**: State survives session restarts, context clears, client crashes
✅ **Context Editing Support**: Critical state preserved during automatic context editing
✅ **Multi-Agent Coordination**: Agents share persistent state via `/memories/`
✅ **Reduced Setup Time**: No need to re-initialize state each session
✅ **Future-Proof**: Positioned for DZP v9.0+ features (cross-project memory, cloud sync)

---

## Additional Resources

**Official Documentation**:
- Anthropic Memory Tool Docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

**DZP Documentation**:
- Memory Tool Integration Reference: `docs/reference/MEMORY_TOOL_INTEGRATION.md`
- Validation Framework Guide: `docs/guides/VALIDATION_FRAMEWORK_GUIDE.md`
- Implementation Guide: `docs/installation/IMPLEMENTATION_GUIDE.md`

---

## Support

**Issues with Memory Tool**:
- Check model compatibility (Sonnet 4.5+, Opus 4.5+, Haiku 4.5+)
- Verify beta header if using Anthropic API directly
- Review Anthropic Memory Tool beta status/updates

**Issues with DZP Memory Integration**:
- Report at: https://github.com/DewyHRite/Domain-Zero-Protocol/issues
- Include: DZP version, Claude model, platform (Claude Code/Claude.ai/API)

---

**Last Updated**: 2025-12-05 (v8.8.0)
**Status**: Production-Ready
