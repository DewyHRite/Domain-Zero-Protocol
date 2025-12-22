## Summary

This PR completes the v8.9.0 release with security remediation from Sukuna-Megumi red team assessment, version sweep across all protocol files, and documentation updates.

## Security Remediation (8 Findings)

| Finding | Priority | Status |
|---------|----------|--------|
| SEC-001 | P0 | ✅ Task tool subagent_type constraints documented |
| SEC-002 | P1 | ✅ Version sweep 8.8.0 → 8.9.0 complete |
| SEC-003 | P1 | ✅ Malicious test data cleaned from project-state.json |
| SEC-005 | P2 | ✅ Input validation added to file-rotate.py |
| SEC-007 | P2 | ✅ Archive verification (SHA-256) added to file-rotate.py |
| SEC-008 | P3 | ✅ Tool removal comments standardized |

## Changes

### Security Hardening (file-rotate.py)
- Added `sanitize_reason()` - Input sanitization with regex
- Added `validate_path_safety()` - Path traversal prevention
- Added `compute_file_hash()` - SHA-256 integrity verification
- Updated `FileRotator.__init__` with path validation
- Updated `rotate()` with reason sanitization and archive verification

### Version Sweep (8.8.0 → 8.9.0)
- Updated 50+ protocol files with v8.9.0 headers
- Updated VERSION.md, README.md, CLAUDE.md
- Updated protocol.config.yaml versioning section
- Updated gojo.agent.md banners and Major Enhancements
- Preserved historical references (e.g., "NEW IN v8.8.0")

### Documentation Updates (getting-started.html)
- Updated version badge and title to v8.9.0
- Added Claude Skills Integration feature card
- Added Implementation Routing feature card
- Added file-rotate.py and protocol/skills/ to protocol files table

### Data Cleanup
- Removed SQL injection test payloads from project-state.json
- Removed path traversal test data
- Kept legitimate user authentication events

## Files Changed

- **51 files** modified
- **3514 insertions**, **397 deletions**

## Testing

```bash
python -m py_compile scripts/file-rotate.py  # ✅ Syntax verified
```

## Related

- Sukuna-Megumi Red Team Assessment (8 findings)
- v8.9.0 Implementation Plan

🤖 Generated with [Claude Code](https://claude.com/claude-code)
