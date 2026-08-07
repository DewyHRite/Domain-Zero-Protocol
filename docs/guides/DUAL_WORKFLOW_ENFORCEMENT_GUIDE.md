<!-- [CORE FILE] - Domain Zero Protocol v9.12.0 -->
# DUAL WORKFLOW ENFORCEMENT GUIDE
## Domain Zero Protocol v9.12.0 - Mandatory Yuuji-Megumi Collaboration

**Version**: 2.0.0
**Last Updated**: 2026-08-07
**Purpose**: Describe the mandatory dual workflow that governs how Yuuji (Implementation
Specialist) and Megumi (Security Analyst) work together on Tier 2/3 production code.

**History note**: this behavior shipped in v7.1.0 (November 2025) and has been the live, default
protocol behavior for every release since — over 40 versions. This guide originally documented it
as a pending migration checklist; it has been rewritten (2026-08-07) to describe the workflow as
it works **today**. If you're looking for the historical migration record, see `CHANGELOG.md`'s
`[7.1.0]` entry.

---

## 🎯 EXECUTIVE SUMMARY

Yuuji and Megumi work as an **integrated pair** for all Tier 2 (Standard) and Tier 3 (Critical)
features — this is baked directly into `protocol/yuuji.agent.md` and `protocol/megumi.agent.md`,
not an optional convention:

- ✅ Yuuji implements, then **prompts** for Megumi's invocation (outputs the exact instruction to
  run) — the User does not manually tag `@security-review`.
- ✅ Workflow bypass for Tier 2/3 is **strongly discouraged** and treated as a protocol violation
  if requested without switching to Tier 1.
- ✅ Tier 1 (Rapid) remains Yuuji-only — no security review, by design (prototypes only).
- ✅ Gojo and Nobara remain independently invokable, unaffected by this pairing.
- ✅ User retains final authority: the dual workflow is strongly recommended, not a technical hard
  block — see `protocol/skills/gojo/roe-and-tiers.md` for the current advisory + statistics-
  tracking enforcement model that governs this (and every) tier recommendation.

---

## 📋 HOW THE DUAL WORKFLOW WORKS TODAY

### Tier 2 (Standard) Implementation [DEFAULT]

**Invoke**: `"Read yuuji.agent.md and implement [feature]"`

**What Yuuji Does**:
- Full test-first development cycle
- Creates/modifies files as needed
- Writes comprehensive tests
- Creates backup + rollback plan
- Documents everything in dev-notes.md
- Tags `@user-review` for user approval
- **After approval, outputs the instruction to invoke Megumi** for security review
- Follows through remediation if needed, looping until Megumi tags `@approved`

**Time**: 30-45 minutes (implementation) + 30-45 minutes (security review) = **60-90 minutes total**

**Use For**: Production features, client deliverables, standard work

**Workflow Sequence**:
1. Yuuji implements with tests
2. Yuuji tags `@user-review`
3. User approves implementation
4. **Yuuji outputs the instruction to invoke Megumi** (prompting the User for handoff — the User
   still has to run it; Yuuji cannot invoke another agent directly)
5. Megumi reviews and tags `@remediation-required` OR `@approved`
6. If remediation needed: Yuuji fixes issues and loops back to step 4
7. If `@approved`: Feature complete ✓

---

### Tier 3 (Critical) Implementation

Same sequence as Tier 2, with Yuuji's enhanced test coverage (unit + integration + E2E) and
Megumi's enhanced review (multi-model when configured, threat modeling, P0-P3 risk
prioritization). Invocation: `"Read yuuji.agent.md --tier critical and implement [feature]"`,
with Yuuji's prompted handoff reading `"Read megumi.agent.md --tier critical and review
[feature]"`.

---

### Tier 1 (Rapid) Exception

Tier 1 remains the **only** exception to the dual workflow:

```text
User: "Read yuuji.agent.md --tier rapid and create prototype"

Yuuji:
1. Implements quickly (no tests)
2. Tags @user-review
3. Done! (No security review for prototypes)
```

---

## 🔗 MEGUMI'S SIDE: PROMPTED INVOCATION

Megumi is invoked in two ways:

- **PROMPTED** (the normal path): Yuuji outputs the instruction to invoke Megumi after the User
  approves his implementation. Megumi conducts the review, documents findings in
  `security-review.md` with SEC-IDs, and tags `@remediation-required` or `@approved`.
- **DIRECT** (standalone audit or consultation, NOT part of dual workflow): a User can invoke
  Megumi directly for an audit of *existing* code (`"Read megumi.agent.md and audit [module]"`)
  or a security question (`"Read megumi.agent.md - [question]"`) with no Yuuji implementation
  involved. These are valid, independent use cases — see root `CLAUDE.md`'s "Mode 2: Standalone
  Consultation" for the full restriction list on when standalone Megumi review is and isn't
  appropriate.

If a User invokes Megumi to review a Tier 2/3 feature that Yuuji has not yet implemented, Megumi's
correct response is to redirect to the sequence above rather than review nothing.

---

## What Happens If a User Tries to Skip the Security Review

**Scenario**: User says "Read yuuji.agent.md and implement feature X, but skip security review"

**Yuuji's Response**:
```text
I understand you want feature X quickly, but I won't skip the security review for a
Tier 2/3 production feature — that's a protocol violation by design.

Your options:
1. Proceed with the full dual workflow (recommended for production):
   - I implement with tests
   - You review my implementation
   - I prompt you to invoke Megumi for security review
   - Feature completes after @approved

2. Use Tier 1 (Rapid) if this is a prototype:
   - Fast implementation, no tests
   - NO security review (acceptable for non-production)
   - Invocation: "Read yuuji.agent.md --tier rapid and [task]"

3. Standalone consultation, if you just have questions:
   - No implementation, no security review
   - Invocation: "Read yuuji.agent.md - [question]"

4. Explicit skip, if you accept the risk for this Tier 2/3 feature:
   - Say exactly: "Skip security review for [feature]"
   - Gojo tracks the skip and sends periodic reminders until it's reviewed
     (every 24h for Tier 2, every 8h for Tier 3)
   - You can invoke Megumi anytime to close it out: "Read megumi.agent.md and review [feature]"

Which would you like?
```

Per `protocol/skills/gojo/roe-and-tiers.md`'s advisory enforcement model, this pushback is strong
but not a technical block — the User can still override it explicitly (e.g. by switching to Tier
1, or via the explicit skip in option 4), and Gojo logs the deviation in tier statistics for
transparency.

---

## Nobara and Gojo Are Unaffected

**Nobara** remains independently invokable, with no automatic handoff to other agents — creative
strategy and UX work does not require the security pairing that implementation does.

**Gojo** remains independently invokable for mission control functions, and separately briefs
Yuuji and Megumi on tier-aware dual-workflow expectations as part of onboarding a new session.

---

## 🚨 TROUBLESHOOTING

### User Wants to Skip Security Review

See "What Happens If a User Tries to Skip the Security Review" above — offer Tier 1 (Rapid) as
the legitimate fast path, or proceed with the full dual workflow.

### User Manually Tags `@security-review`

Manual `@security-review` tagging from the pre-v7.1.0 workflow is a no-op today; Yuuji already
prompts for Megumi's invocation automatically after approval. If a User tags it out of habit,
Yuuji should simply note that the prompted handoff already covers this and continue normally.

### User Invokes Megumi Before Yuuji Has Implemented Anything

```text
Megumi Response:
"I'm ready to review, but I need Yuuji's implementation first.

The correct workflow sequence:
1. 'Read yuuji.agent.md and implement X'
2. Review Yuuji's implementation
3. Yuuji outputs the instruction to invoke me for security review

Please start with Yuuji, and I'll be invoked through his prompt when ready. (Or, if you want an
audit of code that already exists, say so explicitly — that's a valid standalone use case.)"
```

---

## 📊 WHY THIS WORKFLOW EXISTS

**Security**: consistent OWASP Top 10 coverage for all Tier 2/3 features, with prompt-based
reminders that reduce the chance of a skipped review, and a compliance-ready audit trail once
reviews complete.

**Productivity**: a single invocation (the User invokes Yuuji only) with a prompted, low-friction
handoff to Megumi rather than a second manual step to remember.

**Quality**: test-first implementation and security validation are treated as one integrated unit,
consistent with Domain Zero's zero-defect philosophy — a remediation loop with Megumi verifying
fixes runs until `@approved`.

---

## ✅ CURRENT INVOCATION PATTERNS

### Correct

```text
Tier 1 (Rapid) - Yuuji only:
User: "Read yuuji.agent.md --tier rapid and create prototype"
→ Yuuji implements quickly (no tests), tags @user-review. Done.

Tier 2 (Standard) - dual workflow with prompted handoff:
User: "Read yuuji.agent.md and implement user registration"
→ Yuuji implements with tests, tags @user-review
→ User reviews and approves
→ Yuuji outputs: "Read megumi.agent.md and review user registration"
→ Megumi reviews, tags @remediation-required or @approved
→ If issues: Yuuji remediates, loop continues
→ If clean: Feature complete ✓

Tier 3 (Critical) - enhanced dual workflow with prompted handoff:
User: "Read yuuji.agent.md --tier critical and implement JWT authentication"
→ Yuuji implements with unit + integration + E2E tests, creates performance benchmarks
→ Yuuji tags @user-review; User approves
→ Yuuji outputs: "Read megumi.agent.md --tier critical and review JWT authentication"
→ Megumi conducts enhanced security review; remediation loop continues until @approved
```

### Discouraged (Gojo will push back; User authority still governs — see roe-and-tiers.md)

```text
"Read yuuji.agent.md and implement auth, but skip security review"
→ Yuuji explains the dual-workflow requirement and offers Tier 1/standalone alternatives instead
  of silently complying.

"Read megumi.agent.md and review auth module" (before Yuuji has implemented anything)
→ Megumi redirects to the correct sequence, or clarifies if a standalone audit of *existing* code
  was actually intended.
```

---

## 🎓 RELATED DOCUMENTATION

- **`CLAUDE.md`** (repository root) — "Mode 1: Dual Workflow" is the canonical, current summary
  of this behavior; this guide expands on it.
- **`protocol/skills/gojo/roe-and-tiers.md`** — the tier system's authoritative decision tree,
  characteristics table, and the advisory + statistics-tracking enforcement model referenced
  throughout this guide.
- **`protocol/yuuji.agent.md`** / **`protocol/megumi.agent.md`** — the agent files where this
  behavior is actually implemented.

---

**END OF DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md**

**Domain Zero Protocol v9.12.0** - Perfect Code Through Mandatory Collaboration

*Yuuji and Megumi are an integrated pair for production code. This is the way.*
