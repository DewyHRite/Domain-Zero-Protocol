<!-- [CORE FILE] - Domain Zero Protocol v9.12.1 -->
# Memory Tool Configuration Guide
## Configuring Anthropic's Claude Memory Tool — and What DZP Actually Does With It

**Version**: 9.12.0
**Purpose**: Reference for enabling Anthropic's Claude Memory Tool API (beta) for persistent
cross-session memory, and an explicit statement of what Domain Zero Protocol does and does not do
with it.
**Status**: Reference document. DZP's own persistent cross-session memory system is
**[DZP Cortex](../guides/DZP_CORTEX.md)**, not the Memory Tool described below.

---

> **READ THIS FIRST.** DZP contains **no Memory Tool code path** and performs **no** integration
> with, or path validation for, the `/memories/` mechanism described in this document. Everything
> below `## Configuration by Platform` documents Anthropic's **generic** Memory Tool API/beta —
> useful if you are configuring the Memory Tool for your own use, or building an integration on top
> of DZP — but it is **not** a description of DZP's own current behavior. Historically (pre-v9.11.0)
> this document stated the opposite (that DZP automatically validated paths and orchestrated
> migrations); that was incorrect and is corrected throughout, not just in the security section
> below. If you are looking for DZP's actual persistent memory system, see
> **[docs/guides/DZP_CORTEX.md](../guides/DZP_CORTEX.md)** — DZP Cortex is a local, cited semantic
> recall layer with its own storage, CLI (`brain`), and session-lifecycle integration, and is
> unrelated to the Anthropic Memory Tool.

---

## Overview

The Memory Tool is a beta Anthropic API capability that lets a client persist information across
conversations through client-side file operations under a `/memories/` namespace. In general, this
can provide:
- Persistent memory across sessions, for whatever client wires it up
- Context snapshots that survive context clears
- Learned patterns and successful strategies
- Arbitrary state tracking, defined entirely by the integration that uses it

**None of the above is DZP's own behavior.** DZP does not call the Memory Tool, does not read or
write `/memories/`, and does not depend on it being available. DZP's actual state persistence is:
- **Session/project state**: `.protocol-state/project-state.json` (consolidated namespaces since
  PATCH-STATE-001, v8.13.0 — see root `CLAUDE.md`'s "State Consolidation" section), with automatic
  fallback to legacy per-purpose files if the consolidated state is unavailable.
- **Cross-session semantic memory**: [DZP Cortex](../guides/DZP_CORTEX.md), a separate, local,
  on-device system with its own storage layer, unrelated to the Memory Tool.

**API Status**: Beta (as of December 2025)
**Required Models**: Claude Sonnet 4.5, Opus 4.5, Haiku 4.5 (or newer)

---

## Configuration by Platform

*(This section describes Anthropic's Memory Tool generically. It is accurate as platform/API
documentation; it does not describe anything DZP itself invokes.)*

### Claude Code (VS Code Extension)

Memory Tool is **automatically available** in Claude Code when using supported models.

**No additional configuration needed** - the Memory Tool is enabled by default in Claude Code for:
- Claude Sonnet 4.5 (claude-sonnet-4-5-20251022)
- Claude Opus 4.5 (claude-opus-4-5-20251101)
- Claude Haiku 4.5

**Verification**:
```javascript
// Check if Memory Tool is available
// In Claude Code, any agent invoked with a supported model automatically has access to:
// - view /memories/path
// - create /memories/path {content}
// - str_replace /memories/path old new
// - insert /memories/path line {text}
// - delete /memories/path
// - rename /memories/old /memories/new
//
// DZP agents do NOT call any of these operations as part of their normal workflow —
// availability of the tool is not the same as DZP using it.
```

---

### Claude.ai (Web Interface)

Memory Tool is **automatically available** in Claude.ai web interface when using supported models.

**No additional configuration needed** - Claude.ai automatically enables Memory Tool for supported models.

**Verification**:
- Start a conversation with Claude Sonnet 4.5 or Opus 4.5
- The Memory Tool operations become available to the model generically
- DZP agent invocations (e.g., "Read gojo.agent.md") do not themselves use Memory Tool operations

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

Once enabled (by the *client*, not by DZP), the Memory Tool exposes six generic operations:

| Operation | Syntax | Description |
|-----------|--------|-------------|
| **view** | `view /memories/path` | Display directory or file contents |
| **create** | `create /memories/path {content}` | Create or overwrite file |
| **str_replace** | `str_replace /memories/path old new` | Replace specific text |
| **insert** | `insert /memories/path line {text}` | Insert text at line number |
| **delete** | `delete /memories/path` | Remove file or directory |
| **rename** | `rename /memories/old /memories/new` | Move or rename file |

---

## A Hypothetical Memory Directory Structure (Integrator Reference Only)

DZP does **not** create, read, or maintain any `/memories/` directory structure. The layout below
is an **illustrative example** of how an integrator building a Memory Tool bridge on top of DZP
*could* choose to organize agent-scoped memory, if they wanted to mirror DZP's own agent/namespace
boundaries. It has never been implemented by DZP itself, at any version:

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

> **CORRECTION (v9.11.0, `SEC-MEMPATH-PENDING-L`)**: this section previously
> stated that *"DZP automatically validates all paths - no additional security
> configuration needed."* **That was not true, and the claim has been removed.**
> DZP contains no Memory Tool code path and performs **no** path validation of
> its own. The statement is corrected here rather than quietly deleted, because
> anyone who read the previous version may have skipped validation work on the
> strength of it. (v9.12.0: this correction is no longer an isolated island in
> the document — the rest of this file has been rewritten to agree with it; see
> the banner at the top of this document.)

**What actually enforces the `/memories/` boundary**

Memory Tool path handling is performed by the **client/runtime that implements
the tool** (the Claude Code / API Memory Tool integration), not by Domain Zero
Protocol. Whatever sandboxing that runtime applies is the enforcement you
actually get. DZP neither adds to it nor verifies it.

**What DZP provides**

`scripts/memory_path_validator.py` is an **unwired reference library for
integrators** — a `MemoryPathValidator` class plus `validate_memory_path()` /
`get_validation_error()` / `sanitize_memory_path()` helpers implementing
`/memories/` prefix enforcement, `..` traversal rejection, canonical
resolution, and a directory/agent whitelist.

It has **zero callers anywhere in DZP**. Nothing calls it for you. It is
therefore no longer shipped in the published distribution (removed from
`scripts/distro/publish-manifest.yaml`), because a shipped module carrying a
"SECURITY CRITICAL" banner and no call site reads as protection that is not
there.

**If you are building a Memory Tool integration on top of DZP**

Take the module from the canonical dev repository and call it explicitly at
every point a path enters a filesystem operation — validation only protects the
call sites that invoke it:

```python
from memory_path_validator import validate_memory_path, get_validation_error

if not validate_memory_path(user_supplied_path):
    raise ValueError(f"unsafe memory path: {get_validation_error(user_supplied_path)}")
# ... only now touch the filesystem
```

Do not assume any layer beneath you has already done this.

---

## Verification & Testing (Generic Memory Tool, Not DZP-Specific)

The tests below verify that the **Memory Tool itself** is available and working for your client —
they are not DZP tests, and DZP does not perform any of these checks itself.

### Test 1: Check Memory Tool Availability

```text
User: "Create a test memory file at /memories/test.txt with content 'Hello'"
```

Expected: File created successfully with no errors. This confirms the Memory Tool is enabled and
working for your client/platform — it does not mean DZP has done anything with it, because DZP
never invokes this operation itself.

### Test 2: View Memory Directory

```text
User: "View /memories/ directory"
```

Expected: Should see whatever directory listing your own integration (if any) has created. A fresh
DZP installation with no integrator-built Memory Tool bridge will show nothing DZP-related here,
because DZP never wrote anything there.

---

## Troubleshooting

### Error: "Memory Tool not available"

**Cause**: Model doesn't support Memory Tool or beta not enabled
**Solution**:
1. Verify using Claude Sonnet 4.5, Opus 4.5, or Haiku 4.5
2. If using Anthropic API directly, add beta header: `anthropic-beta: context-management-2025-06-27`
3. Check tool definition includes `type: "memory_20250818"`

This affects only the generic Memory Tool availability — it has no bearing on DZP's own operation,
since DZP does not require or use the Memory Tool.

### Error: "Path validation failed"

**Cause**: Path doesn't start with `/memories/` (a constraint enforced by the Memory Tool's own
client/runtime, not by DZP — see the Security & Path Validation section above)
**Solution**: All Memory Tool operations must use paths starting with `/memories/`.

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

**Cause**: No `/memories/` directory structure exists yet for your client/integration.
**Solution**: DZP does **not** automatically initialize any `/memories/` structure — there is no
DZP-side "first run" behavior for this at all. If you are building your own Memory Tool
integration, your integration's own initialization code is responsible for creating whatever
structure it needs.

---

## Performance Considerations (Generic Memory Tool API, Illustrative Only)

These are illustrative, platform-level latency figures for the Memory Tool API itself — not
measurements of anything DZP does, since DZP does not call these operations:
- `view`: ~50-100ms
- `create/str_replace`: ~100-200ms
- `delete/rename`: ~50ms

If you build your own Memory Tool integration on top of DZP, general optimization advice applies:
- Lazy loading (only read when needed)
- Batch operations (combine multiple updates)
- Caching (keep frequently accessed data in-context)
- Selective persistence (only write changed fields)

DZP's own state I/O (`.protocol-state/project-state.json` reads/writes, and DZP Cortex's local
vector store) has its own independent performance characteristics, unrelated to the numbers above.

---

## Context Management Integration

**Memory Tool + Context Editing**:

When context approaches limits, a client that has wired up the Memory Tool can automatically:
1. Preserve critical info to `/memories/`
2. Clear old tool results
3. Read back from `/memories/` to restore context
4. Continue work indefinitely

This is a capability of the Memory Tool + context-editing combination generically — it is not
something DZP configures or relies on.

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

**Compatibility note**: this is entirely about the Memory Tool's own backend abstraction — it has no
DZP compatibility requirement, because DZP does not consume `/memories/` at all. If you build a
custom backend as part of your own Memory Tool integration on top of DZP, keep whatever
`/memories/` directory structure *your own integration* expects.

---

## A Hypothetical Migration Guide: Local State → A Memory Tool Integration

**This entire section is illustrative, for integrators only. DZP does not perform, orchestrate, or
support this migration in any form — there is no "migrate my state files to Memory Tool" command,
and Gojo does not have any code path that reads `.protocol-state/`, writes `/memories/`, or checks
Memory Tool availability.** It is retained here as a worked example of *how you would build such a
bridge yourself*, since the underlying operations (view/create/etc.) and DZP's real state file
layout are both accurate and may be useful reference material.

**If you actually want persistent, queryable cross-session memory for DZP today**, use
**[DZP Cortex](../guides/DZP_CORTEX.md)** instead — it already exists, is already wired into the
`/session` lifecycle, and requires no custom integration work.

### What you would need to build

- A migration script or agent instruction set that:
  1. Reads DZP's real, current state files (see below — not the pre-consolidation layout)
  2. Writes their content into `/memories/` using the Memory Tool's `create` operation
  3. Verifies the write succeeded
  4. Leaves DZP's own `.protocol-state/` files untouched (DZP always reads from there; it has no
     fallback-to-Memory-Tool logic, so removing `.protocol-state/` files would break DZP)

### DZP's actual current state file layout (as of PATCH-STATE-001, v8.13.0+)

Do **not** use the historical, pre-consolidation per-purpose files below as a migration *source* —
they no longer hold the canonical data:

```text
# Current, canonical source for a hypothetical migration:
.protocol-state/project-state.json   # consolidated: session_tracking, troubleshooting,
                                      # tier_tracking, agent_invocation_tracking namespaces
                                      # → e.g. /memories/project/project-state.json

# Legacy, pre-PATCH-STATE-001 per-purpose files (session-state.json,
# troubleshooting-history.json, agent-invocation-tracker.json) are preserved
# only as automatic FALLBACK files if the consolidated state is unavailable —
# they are not the live source of truth and should not be treated as such by
# a migration script written today.
```

### Illustrative Python sketch (untested, for reference only)

```python
import anthropic
import json
from pathlib import Path

client = anthropic.Anthropic(api_key="your-api-key")

headers = {
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "context-management-2025-06-27"
}

def migrate_state_file(local_path: str, memory_path: str):
    """Illustrative only — copies one local JSON file's content into the
    Memory Tool via `create`. Not part of DZP; you would run this yourself as
    part of your own integration, against DZP's real project-state.json."""
    with open(local_path, 'r') as f:
        state_data = json.load(f)

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
    print(f"Copied: {local_path} -> {memory_path}")
    return message

# Illustrative mapping against DZP's REAL, current (post-consolidation) state file:
migrations = [
    (".protocol-state/project-state.json", "/memories/project/project-state.json"),
]

for local_path, memory_path in migrations:
    if Path(local_path).exists():
        migrate_state_file(local_path, memory_path)
        # DZP's own .protocol-state/ files are NEVER renamed or removed by this
        # sketch -- DZP always reads from .protocol-state/ directly and has no
        # Memory Tool fallback logic.
```

### Rollback

There is nothing to roll back on DZP's side — DZP never stopped reading `.protocol-state/`, because
it never started reading `/memories/` in the first place. If you built your own integration on top
of this sketch, rolling back means simply stopping your integration's writes to `/memories/`; DZP's
behavior is completely unaffected either way.

---

## Additional Resources

**Official Documentation**:
- Anthropic Memory Tool Docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

**DZP Documentation**:
- **DZP's actual persistent memory system**: [docs/guides/DZP_CORTEX.md](../guides/DZP_CORTEX.md)
- Implementation Guide: `docs/installation/IMPLEMENTATION_GUIDE.md`

---

## Support

**Issues with the (generic) Memory Tool**:
- Check model compatibility (Sonnet 4.5+, Opus 4.5+, Haiku 4.5+)
- Verify beta header if using Anthropic API directly
- Review Anthropic Memory Tool beta status/updates

**Issues with DZP itself** (which does not use the Memory Tool):
- Report at: https://github.com/DewyHRite/Domain-Zero-Protocol/issues
- Include: DZP version, Claude model, platform (Claude Code/Claude.ai/API)

---

**Last Updated**: 2026-08-07 (v9.12.0) — full-document currency rewrite resolving the
self-contradiction between the v9.11.0 correction and the rest of this document
(`TOJI-DOCS-9.12.0-007`).
**Status**: Reference document (generic Memory Tool API) + explicit non-integration statement.
DZP's real memory system is [DZP Cortex](../guides/DZP_CORTEX.md).
