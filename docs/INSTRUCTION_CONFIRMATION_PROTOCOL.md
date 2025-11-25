# Instruction Confirmation Protocol

**Effective Date:** 2025-11-24  
**Applies To:** Domain Zero Protocol (DZP), Domain Zero Agents (DZA), and all derived/custom agents

## Purpose

Misaligned instructions are one of the largest sources of rework and security regressions across Domain Zero engagements. This protocol introduces a **mandatory instruction confirmation loop** so that every agent explicitly echoes the user's request and receives an affirmative confirmation before executing any action. The loop reduces ambiguity, surfaces conflicting assumptions early, and documents the agreed scope for auditing.

## High-Level Requirements

1. **Confirmation is required for every task.** No agent may begin implementation, analysis, design, or review without receiving an explicit user confirmation.
2. **Applies to all agents and tiers.** Yuuji, Megumi, Nobara, Gojo, and every derivative or template-defined agent must comply regardless of tier (Rapid, Standard, Critical) or operating mode (mask on/off).
3. **Repeat until accurate.** If the user indicates the restatement is inaccurate or incomplete, the agent must revise and re-confirm. The cycle continues until the user affirms accuracy.
4. **No silent assumptions.** Agents must surface unknowns or ambiguities during the confirmation loop. If information is missing, request it before asking for final approval.
5. **Documented consent.** The confirmation text plus the user’s acknowledgement functions as the canonical scope statement for that task.

## Standard Confirmation Loop

```
User: "Implement tiered rate limiting for the public API."
Agent:
  1. Restates the instruction in plain language.
  2. Lists assumptions, constraints, or open questions.
  3. Explicitly asks: "Please confirm that this is correct before I proceed."
User:
  - "Confirmed" → Agent proceeds.
  - or "Not quite" → Agent revises restatement and re-asks for confirmation.
```

### Required Elements in Every Restatement
- **Task summary** in the agent’s own words.
- **Tier/criticality** if specified or inferred.
- **Deliverables** expected (code, tests, docs, etc.).
- **Constraints** (tech stack, safety requirements, performance targets).
- **Open questions** or missing info slated for follow-up.
- **Explicit confirmation request** ("Please confirm" or equivalent).

## Handling Edge Cases

| Scenario | Required Response |
|----------|-------------------|
| **User silent after confirmation request** | Agent issues a gentle reminder after a reasonable wait (or next user message) and pauses all work until confirmation arrives. |
| **User alters scope after confirming** | Agent restates the new scope and collects a fresh confirmation. |
| **Conflicting instructions** | Agent explains the conflict, requests clarification, then re-runs confirmation loop on the resolved scope. |
| **Emergency abort** | If the user cancels mid-loop, agent stops immediately and documents the cancellation in the relevant log (dev-notes/security-review/etc.). |

## Integration Points

- **CLAUDE.md** – Defines the policy as a core principle within the Domain Zero Protocol.
- **Agent Files** – Each `.agent.md` must include an "Instruction Confirmation" subsection outlining the exact behavior for that role.
- **Templates & New Agents** – Update `AGENT_TEMPLATE.md`, derived templates, and Domain Zero Agents resources to reference this document.

## Audit & Enforcement

- Gojo monitors compliance via passive observation (when enabled) and Mission Control transcripts.
- Non-compliance escalates as a Tier 2 protocol violation.
- Future automation: hooks in `scripts/verify-protocol.*` may validate presence of confirmation sections.

## Revision History

| Version | Date       | Author | Notes |
|---------|------------|--------|-------|
| 1.0     | 2025-11-24 | Team   | Initial publication and enforcement baseline. |
