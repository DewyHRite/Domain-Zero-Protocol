# Research Mode State Directory

This directory contains research session outputs from Domain Zero agents.

## Structure

```
.protocol-state/research/
├── research-index.json       # Global index tracking all research sessions
├── yuuji/                    # Yuuji (Implementation) research outputs
├── megumi/                   # Megumi (Security) research outputs
├── nobara/                   # Nobara (Creative Strategy/UX) research outputs
└── gojo/                     # Gojo (Mission Control) research outputs
```

## File Naming Convention

**Summary files** (tracked, optional):
- `{ISO-8601-timestamp}.summary.md`
- Example: `2025-11-09T14-30-00Z.summary.md`

**Raw notes** (gitignored):
- `{ISO-8601-timestamp}.raw.log`
- Example: `2025-11-09T14-30-00Z.raw.log`

## Privacy

- **Raw notes** (`.raw.log` files) are gitignored and never committed
- **Summary files** (`.summary.md`) are curated and can optionally be tracked
- PII is automatically redacted from all outputs
- Only source URLs and excerpts are stored, not full content

## Session Workflow

1. **Initiation** (`@research-start`): Agent validates research mode enabled
2. **Scoping**: Form 3-5 focused research questions
3. **Source Selection**: Build candidate list, filter by source policy
4. **Collection**: Retrieve summaries/excerpts with timestamps
5. **Triangulation**: Cross-check 2+ sources for each key claim
6. **Synthesis** (`@research-update`): Produce structured summary
7. **Validation**: Apply agent-specific verification gates
8. **Completion** (`@research-complete`): Persist summary, update index

## Configuration

See `protocol.config.yaml` → `research` section and `protocol/RESEARCH_MODE.md` for complete specification.

## Version

Research Mode introduced in Domain Zero Protocol v7.2.0
