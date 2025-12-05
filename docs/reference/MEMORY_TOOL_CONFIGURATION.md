<!-- [CORE FILE] - Domain Zero Protocol v8.8.0 -->
# Memory Tool Configuration Guide
## Enabling Claude Memory Tool Beta for DZP v8.8.0

**Version**: 8.8.0
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

```
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

```
User: "Read gojo.agent.md"
Gojo: [Gojo should be able to view /memories/agents/gojo/]
```

If Memory Tool is working, Gojo will check `/memories/agents/gojo/` on startup.

### Test 2: Create Test Memory File

```
User: "Create a test memory file at /memories/test.txt with content 'Hello DZP'"
```

Expected: File created successfully with no errors.

### Test 3: View Memory Directory

```
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
```
view /memories/agents/yuuji/session-context.json
```

**Incorrect**:
```
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
