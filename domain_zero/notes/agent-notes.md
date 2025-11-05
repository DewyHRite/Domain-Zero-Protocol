# Agent Notes (Megumi)

Purpose: Central log for Megumi’s security findings, performance observations, and verification tracking.

Do not include implementation patches here. Use SEC-IDs for traceability and reference them in reviews.

---

## Log Index
- Date: YYYY-MM-DD — Summary (e.g., "DUAL_WORKFLOW review of feature X; 2 findings: SEC-2025-11-04-001, -002")

---

## Finding Template

```
SEC-ID: SEC-YYYY-MM-DD-###
Severity: [Critical | High | Medium | Low]
Category: [OWASP | Perf | Both]
Location: [file:line or component]

Description:
- What’s the issue? How is it exploitable or harmful?

Evidence:
- Repro steps, screenshots, logs, or code references

Risk Assessment:
- Probability: [H/M/L]
- Impact: [Critical/High/Medium/Low]
- Overall Risk: [Critical/High/Medium/Low]

Recommendation:
- Specific remediation guidance

Status:
- [Open | In Remediation (Yuuji) | Verified Fixed | Deferred]
Verification Notes:
- How was the fix verified? (tests, manual, telemetry)
```

---

## Notes
- Use this file to maintain continuity across sessions
- Keep entries concise and link to detailed reports when needed
