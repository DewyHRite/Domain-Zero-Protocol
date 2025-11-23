# Agent Mode Indicators & Display Systems

## Overview

This document specifies visual and textual indicators used to communicate agent mode, tier, and operational state within the Domain Zero Protocol system.

---

## Self-Identification Banners

For complete specification of self-identification banners, see [`AGENT_SELF_IDENTIFICATION_STANDARD.md`](AGENT_SELF_IDENTIFICATION_STANDARD.md).

**Standard Banner Format**:
```text
[EMOJI] [DOMAIN NAME] ACTIVATED [EMOJI]
"[Domain Subtitle]"
```

---

## Agent Mode Indicators

Each agent has a distinct emoji indicator that appears in their self-identification banner and throughout protocol documentation:

| Agent | Emoji | Domain Name | Mode |
|-------|-------|-------------|------|
| **Yuuji Itadori** | 🛠️ | IMPLEMENTATION DOMAIN | Implementation Mode |
| **Megumi Fushiguro** | 🛡️ | SECURITY DOMAIN | Security Review Mode |
| **Satoru Gojo** | 🌀 | MISSION CONTROL DOMAIN | Mission Control Mode |
| **Nobara Kugisaki** | 🎯 | CREATIVE STRATEGY DOMAIN | Creative Strategy Mode |

---

## Workflow Tier Indicators

The Domain Zero Protocol uses three workflow tiers with distinct indicators:

| Tier | Indicator | Name | Time Estimate |
|------|-----------|------|---------------|
| **Tier 1** | 🚀 | Rapid | 10-15 minutes |
| **Tier 2** | ⚖️ | Standard | 30-45 minutes |
| **Tier 3** | 🔒 | Critical | 60-90 minutes |

**Usage in Documentation**:
- Tier headers: `## TIER 1: RAPID 🚀`
- Invocation examples: `--tier rapid` ← Associated with 🚀
- Output templates: `[Tier 3 - CRITICAL] 🔒`

---

## Status Indicators

Standard status indicators used across protocol state files and intelligence reports:

| Status | Indicator | Meaning | Used In |
|--------|-----------|---------|---------|
| **In Progress** | ⏳ | Work currently underway | dev-notes.md, Trigger 19 |
| **Completed** | ✅ | Task finished successfully | dev-notes.md, security-review.md |
| **Blocked** | ⛔ | Cannot proceed without intervention | dev-notes.md, Trigger 19 |
| **Review Required** | 🔍 | Awaiting review or approval | dev-notes.md |
| **Failed** | ❌ | Task failed or error encountered | security-review.md, scripts |
| **Warning** | ⚠️ | Caution or non-blocking issue | verify-protocol scripts |
| **Approved** | @approved | Security review passed | security-review.md |
| **Remediation Required** | @remediation-required | Issues found, fixes needed | security-review.md |

---

## Workflow Tag Indicators

Tags used in dev-notes.md and security-review.md to coordinate workflow:

| Tag | Meaning | Who Uses | Next Action |
|-----|---------|----------|-------------|
| `@user-review` | Ready for user review | Yuuji | User reviews implementation |
| `@security-review` | Ready for security audit (Tier 2) | Yuuji | Megumi conducts review |
| `@security-review-critical` | Ready for enhanced security audit (Tier 3) | Yuuji | Megumi conducts enhanced review |
| `@approved` | Security review passed | Megumi | Feature complete |
| `@remediation-required` | Issues found | Megumi | Yuuji fixes issues |
| `@re-review` | Fixes complete, ready for verification | Yuuji | Megumi verifies fixes |

---

## Integration Points

Mode indicators are displayed in:

### 1. Self-Identification Banners
- Agents display their emoji and domain name on invocation
- Configured via `protocol.config.yaml` under `self_identification.agents.<name>`
- Debounced to prevent spam (default: 15 minutes)

### 2. Dev Notes Headers
Example from `.protocol-state/dev-notes.md`:
```markdown
## ✅ Implementation Complete: User Authentication
**Agent**: Yuuji Itadori 🛠️
**Tier**: Standard ⚖️
**Status**: ⏳ In Progress → ✅ Completed
```

### 3. Security Review Reports
Example from `.protocol-state/security-review.md`:
```markdown
## 🛡️ Security Review: User Authentication
**Reviewer**: Megumi Fushiguro
**Tier**: Standard ⚖️
**Status**: ✅ @approved
```

### 4. Trigger 19 Intelligence Reports
Example from `.protocol-state/trigger-19.md`:
```markdown
## 🌀 Trigger 19 Intelligence Report
**Domain Controller**: Satoru Gojo
**Mission Status**: ACTIVE ⏳
**Protocol Health**: ✅ EXCELLENT
```

### 5. Output Templates
Agents include indicators in their structured outputs:
```markdown
## [Tier 3 - CRITICAL] 🔒 Implementation Complete: Payment Processing
...
```

---

## Configuration

Mode indicators can be customized in `protocol.config.yaml`:

```yaml
self_identification:
  enabled: true
  include_emoji: true  # Set to false to disable emoji in banners
  agents:
    yuuji:
      emoji: "🛠️"
      domain_name: "IMPLEMENTATION DOMAIN"
      subtitle: "Test-Driven Delivery, Rapid Iteration"
    megumi:
      emoji: "🛡️"
      domain_name: "SECURITY DOMAIN"
      subtitle: "Threat Modeling First, OWASP-Aligned Controls"
    gojo:
      emoji: "🌀"
      domain_name: "MISSION CONTROL DOMAIN"
      subtitle: "Orchestration, Review, and Passive Observation"
    nobara:
      emoji: "🎯"
      domain_name: "CREATIVE STRATEGY DOMAIN"
      subtitle: "User Insight, Narrative, and Delight"
```

---

## Accessibility Considerations

### Emoji Alternatives

For environments where emoji display is inconsistent or inaccessible:

| Emoji | Text Alternative | ASCII Alternative |
|-------|------------------|-------------------|
| 🛠️ | `[IMPL]` | `<IMPL>` |
| 🛡️ | `[SEC]` | `<SEC>` |
| 🌀 | `[MC]` | `<MC>` |
| 🎯 | `[UX]` | `<UX>` |
| 🚀 | `[T1-RAPID]` | `<T1>` |
| ⚖️ | `[T2-STD]` | `<T2>` |
| 🔒 | `[T3-CRIT]` | `<T3>` |
| ✅ | `[DONE]` | `<OK>` |
| ⏳ | `[PROG]` | `<WIP>` |
| ⛔ | `[BLOCK]` | `<X>` |
| ⚠️ | `[WARN]` | `<!>` |

**Implementation**: Set `include_emoji: false` in protocol.config.yaml to use text-based mode indicators.

---

## Version Information

**Document Version**: 1.0
**Protocol Version: 6.2.3
**Last Updated**: 2025-11-06
**Status**: Active

---

**See Also**:
- [`AGENT_SELF_IDENTIFICATION_STANDARD.md`](AGENT_SELF_IDENTIFICATION_STANDARD.md) - Complete self-ID specification
- [`CLAUDE.md`](CLAUDE.md) - Main protocol file
- [`protocol.config.yaml`](../protocol.config.yaml) - Configuration reference
