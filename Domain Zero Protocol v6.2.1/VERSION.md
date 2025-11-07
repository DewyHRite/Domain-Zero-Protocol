# Domain Zero Protocol - Version Information

**Version:** v6.2.1
**Release Date:** November 6, 2025
**Release Type:** Minor Update

---

## Release Summary

This version introduces **Interactive Work Session Alerts**, allowing users to make explicit choices when extended work sessions are detected. Gojo now presents "Save Progress" or "Continue Working" options with appropriate enforcement responses.

### Key Changes

- **Interactive session alerts** with user choice
- **Enhanced enforcement logic** based on user response
- **New configuration settings** for session monitoring
- **Improved work session alert template**

---

## What's New in v6.2.1

### Added
- Interactive Work Session Alerts with explicit user choices
- Enhanced enforcement logic based on user decisions
- New configuration settings in `protocol.config.yaml`:
  - `interactive_session_alerts`
  - `block_until_response`
  - `escalate_on_continue`
  - `block_high_risk_when_fatigued`

### Changed
- Work session alert template restructured
- GOJO.md work session monitoring section enhanced
- Alert response workflow improved

### Fixed
- Version consistency across all protocol files

---

## Upgrade Notes

No breaking changes. This is a backward-compatible minor update.

Configuration updates are optional - defaults provide sensible behavior.

---

## Full Details

See [CHANGELOG.md](CHANGELOG.md) for complete version history and detailed change information.

---

**Canonical Source:** https://github.com/DewyHRite/Domain-Zero-Protocol
**Previous Version:** v6.2.0
**Next Version:** v6.2.2 (planned)
