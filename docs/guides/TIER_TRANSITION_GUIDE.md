# Tier Transition Guide

**Version:** v6.2.4
**Last Updated:** November 7, 2025

---

## Overview

This guide explains **how and when to change tiers** during a Domain Zero Protocol workflow. Tier transitions allow you to adjust the rigor and oversight level based on evolving requirements.

---

## Table of Contents

- [When to Transition](#when-to-transition)
- [Upgrading Tiers](#upgrading-tiers-increasing-rigor)
- [Downgrading Tiers](#downgrading-tiers-decreasing-rigor)
- [Transition Workflows](#transition-workflows)
- [Common Scenarios](#common-scenarios)
- [Best Practices](#best-practices)
- [Gojo's Role](#gojos-role-in-transitions)

---

## When to Transition

### Valid Reasons to Upgrade (↑ Increase Rigor)

✅ **Discovery of Security Implications:**
- Started as Tier 1 prototype, now handling user data
- Feature expanded to include authentication
- Realized code processes sensitive information

✅ **Production Deployment:**
- Prototype (Tier 1) worked, now making it production-ready (Tier 2)
- Production feature (Tier 2) now critical to business (Tier 3)

✅ **Compliance Requirements:**
- Legal team requires security review
- Audit trail needed for changes
- Regulatory requirements discovered (HIPAA, PCI-DSS, etc.)

✅ **Risk Mitigation:**
- User request for security review
- Bug found in similar code elsewhere
- Increased user base or exposure

---

### Valid Reasons to Downgrade (↓ Decrease Rigor)

⚠️ **Scope Reduction:**
- Feature removed sensitive data handling
- Authentication requirement eliminated
- Feature demoted to internal-only tool

⚠️ **Throwaway Code:**
- Prototype confirmed as dead-end
- Experimental feature rejected
- One-time data migration script

⚠️ **Non-Production:**
- Development/staging environment only
- Temporary workaround
- Documentation or example code

---

### Invalid Reasons (Do NOT Transition)

❌ **Time Pressure:**
- "Deadline is tomorrow, skip security review"
- "Just get it working, we'll fix it later"
- **Gojo will reject these requests**

❌ **Inconvenience:**
- "Tests take too long"
- "Security review is annoying"
- **Protocol exists for a reason**

❌ **Overconfidence:**
- "I'm sure it's secure"
- "This is simple, no need for tests"
- **Confidence ≠ Correctness**

---

## Upgrading Tiers (Increasing Rigor)

### Tier 1 → Tier 2 (Rapid to Standard)

**When:** Prototype becomes production feature

**Requirements Added:**
- ✅ Test-Driven Development (TDD)
- ✅ Security review (OWASP Top 10)
- ✅ Code review standards
- ✅ Documentation requirements

**Process:**
1. Say: **"Upgrade to Tier 2"** or **"I need tests and security review"**
2. Gojo acknowledges upgrade
3. Yuuji writes tests for existing code (backfill)
4. Yuuji refactors if needed to make testable
5. Megumi performs security review
6. Continue with Tier 2 standards

**Example:**
```
User: "This prototype is working well. Let's upgrade to Tier 2 for production."
Gojo: "Acknowledged. Upgrading from Tier 1 to Tier 2. Yuuji will now backfill tests
       and Megumi will perform security review before approval."
```

**Time Impact:** +30-45 minutes (test writing + security review)

---

### Tier 2 → Tier 3 (Standard to Critical)

**When:** Feature handles authentication, payments, or sensitive data

**Requirements Added:**
- ✅ Enhanced test coverage (edge cases, negative tests)
- ✅ Multi-model security review (if configured)
- ✅ Threat modeling
- ✅ Security-specific documentation
- ✅ Principle of least privilege enforcement

**Process:**
1. Say: **"Upgrade to Tier 3 - this handles user authentication"**
2. Gojo acknowledges upgrade and explains new requirements
3. Yuuji enhances test suite
4. Megumi performs deep security review
5. Optional: Second AI model reviews (if configured)
6. Gojo validates all requirements met

**Example:**
```
User: "Actually, this feature will handle user passwords. Upgrade to Tier 3."
Gojo: "Acknowledged. Upgrading to Tier 3 (Critical). This tier requires:
       - Enhanced test coverage including security edge cases
       - Deep security review with threat modeling
       - Principle of least privilege enforcement
       Proceeding with enhanced workflow."
```

**Time Impact:** +60-90 minutes total (enhanced testing + deep review)

---

### Tier 1 → Tier 3 (Direct Jump)

**When:** Discovered critical requirements mid-workflow

**Requirements Added:**
- All Tier 2 requirements
- All Tier 3 requirements

**Process:**
1. Say: **"Upgrade directly to Tier 3 - this handles payment processing"**
2. Gojo acknowledges major upgrade
3. Yuuji implements full TDD approach
4. Yuuji adds enhanced test coverage
5. Megumi performs comprehensive security review
6. Gojo validates all critical requirements met

**Example:**
```
User: "Wait, this needs to process credit card data. Jump to Tier 3 immediately."
Gojo: "Acknowledged. Direct upgrade Tier 1 → Tier 3. This is a major increase in
       requirements. Yuuji will implement full TDD with enhanced coverage, and
       Megumi will perform comprehensive security review including PCI-DSS
       considerations."
```

**Time Impact:** +90-120 minutes (full workflow from scratch)

---

## Downgrading Tiers (Decreasing Rigor)

### Tier 3 → Tier 2 (Critical to Standard)

**When:** Feature no longer handles critical data

**Requirements Removed:**
- Enhanced test coverage (standard coverage remains)
- Multi-model security review (standard OWASP remains)
- Threat modeling (basic security review remains)

**Process:**
1. Say: **"Downgrade to Tier 2 - we removed password handling"**
2. Gojo **assesses risk** and **challenges** your reasoning
3. Gojo asks: "Why is Tier 3 no longer needed?"
4. YOU provide justification
5. Gojo **approves or denies**
6. If approved: Continue with Tier 2 standards

**Example:**
```
User: "We're removing the authentication module. Can we downgrade to Tier 2?"
Gojo: "Request to downgrade Tier 3 → Tier 2 received. Please confirm:
       - Authentication logic completely removed?
       - No handling of user credentials or sessions?
       - No access to sensitive user data?"
User: "Confirmed. Feature now only displays public data."
Gojo: "Downgrade approved. Continuing with Tier 2 (Standard) requirements.
       Note: Security review still required per Tier 2."
```

**Time Saved:** ~30-45 minutes (no enhanced requirements)

---

### Tier 2 → Tier 1 (Standard to Rapid)

**When:** Code becomes throwaway or prototype

**Requirements Removed:**
- Test-Driven Development (tests optional)
- Security review (skipped)
- Code review standards (relaxed)

**Process:**
1. Say: **"Downgrade to Tier 1 - this is now a prototype only"**
2. Gojo **heavily challenges** this request
3. Gojo warns about risks
4. YOU must provide strong justification
5. Gojo **rarely approves** (high bar)
6. If approved: Continue with Tier 1 (no review)

**Example:**
```
User: "This approach isn't working. Downgrade to Tier 1 while I experiment."
Gojo: "⚠️ WARNING: Downgrade Tier 2 → Tier 1 removes security review and tests.
       This is ONLY acceptable for:
       - Throwaway code that will be deleted
       - Experiments not going to production
       - Internal tools with no user exposure

       Confirm this code will NOT go to production?"
User: "Confirmed. This is experimental only, will be deleted."
Gojo: "Downgrade approved with conditions:
       - Code marked as experimental in dev-notes.md
       - Separate branch created (not main)
       - Clear deletion timeline documented
       Proceeding with Tier 1 (Rapid) - no security review."
```

**Time Saved:** ~30-45 minutes (no tests or review)

---

### Tier 3 → Tier 1 (Direct Drop - RARE)

**When:** Almost never. Gojo will strongly resist.

**Process:**
1. Say: **"Drop to Tier 1 - abandoning this feature"**
2. Gojo **interrogates** your reasoning
3. Gojo requires **proof** feature is being abandoned
4. Gojo may require **deletion** instead of downgrade
5. If approved: Mark as abandoned, no further work

**Example:**
```
User: "This authentication approach failed. Drop to Tier 1."
Gojo: "❌ DENIED. Tier 3 → Tier 1 direct drop is not recommended.

       Alternative options:
       1. ABANDON: Delete code entirely and document decision
       2. RESTART: Begin new Tier 1 prototype with different approach
       3. CONTINUE: Stay Tier 3 and try different implementation

       Which do you prefer?"
User: "Let's abandon and restart with a new approach."
Gojo: "Recommended. Creating abandonment record in dev-notes.md.
       Ready to begin new Tier 1 prototype when you are."
```

---

## Transition Workflows

### Backfilling Requirements (Upgrade)

When upgrading, Gojo ensures previous tier requirements are met:

**Tier 1 → Tier 2 Backfill:**
```
1. Gojo: "Inventorying existing code..."
2. Yuuji: "Writing tests for existing functions..."
   - function_a: 3 tests added
   - function_b: 5 tests added
   - Total coverage: 87%
3. Megumi: "Performing security review on existing code..."
   - No OWASP Top 10 issues found
   - 2 recommendations for hardening
4. Gojo: "Tier 2 backfill complete. Proceeding with Tier 2 workflow."
```

**Tier 2 → Tier 3 Backfill:**
```
1. Gojo: "Enhancing existing tests for Tier 3..."
2. Yuuji: "Adding edge case and negative tests..."
   - Added 12 edge case tests
   - Added 7 negative/error condition tests
   - Total coverage: 95%
3. Megumi: "Performing deep security review..."
   - Threat modeling completed
   - Attack surface analysis done
   - 1 medium-severity finding (addressed)
4. Gojo: "Tier 3 enhanced requirements met. Proceeding."
```

---

### Validating Downgrade (Downgrade)

When downgrading, Gojo validates the justification:

**Gojo's Validation Questions:**
1. "Why is the higher tier no longer needed?"
2. "What changed in requirements or scope?"
3. "Are you certain this code won't handle [sensitive data/auth/payments]?"
4. "Will this code remain in a non-production environment?"
5. "Have you documented this decision in dev-notes.md?"

**Approval Criteria:**
- ✅ Legitimate scope reduction
- ✅ Removal of sensitive data handling
- ✅ Demotion to internal-only tool
- ✅ Code marked as experimental/throwaway

**Rejection Criteria:**
- ❌ Time pressure
- ❌ Convenience
- ❌ "We'll fix it later"
- ❌ Unclear justification

---

## Common Scenarios

### Scenario 1: Prototype Success → Production

**Initial State:** Tier 1 prototype
**Discovery:** Users love it, want it in production
**Action:** Upgrade to Tier 2

```
User: "Prototype works great. Let's productionize it - upgrade to Tier 2."
Gojo: "Acknowledged. Tier 1 → Tier 2 upgrade initiated."
Yuuji: "Backfilling tests for production readiness..."
Megumi: "Security review commencing..."
Gojo: "Tier 2 requirements met. Feature ready for production deployment."
```

---

### Scenario 2: Feature Creep → Security Critical

**Initial State:** Tier 2 standard feature
**Discovery:** PM wants to add user data storage
**Action:** Upgrade to Tier 3

```
User: "New requirement: Feature must store user preferences. Upgrade to Tier 3."
Gojo: "Acknowledged. User data storage detected. Tier 2 → Tier 3 upgrade required."
Megumi: "Performing enhanced security review for data storage..."
       - Encryption at rest: Required
       - Access controls: Validated
       - Data retention policy: Needs documentation
Gojo: "Tier 3 requirements validated. Proceed with implementation."
```

---

### Scenario 3: Abandoned Experiment

**Initial State:** Tier 2 feature in progress
**Discovery:** Approach isn't viable
**Action:** Downgrade to Tier 1 or abandon

```
User: "This approach won't work. Can we downgrade to Tier 1 and try a new direction?"
Gojo: "Downgrade request Tier 2 → Tier 1. Recommend: ABANDON current approach,
       START new Tier 1 prototype with different strategy. This provides:
       - Clean slate
       - No baggage from failed approach
       - Clear decision trail in dev-notes.md
       Proceed with abandonment?"
User: "Yes, let's abandon and start fresh."
Gojo: "Abandonment recorded. Ready for new Tier 1 prototype when you are."
```

---

### Scenario 4: Temporary Fix → Permanent Solution

**Initial State:** Tier 1 quick workaround
**Discovery:** Workaround still in use 6 months later
**Action:** Upgrade to Tier 2 (should have been done earlier!)

```
User: "This 'temporary' fix from 6 months ago is still running. We should
       probably upgrade to Tier 2 and make it official."
Gojo: "⚠️ ALERT: Code running in production for 6 months without Tier 2 review.

       IMMEDIATE ACTIONS REQUIRED:
       1. Upgrade to Tier 2 NOW
       2. Backfill tests immediately
       3. Security review ASAP
       4. Document as technical debt in dev-notes.md

       Proceeding with emergency Tier 2 upgrade..."
Yuuji: "Writing tests for production code (should have been done 6 months ago)..."
Megumi: "Performing overdue security review..."
Gojo: "Tier 2 requirements now met. Recommend preventing this in future:
       - All production code must start at Tier 2 minimum
       - 'Temporary' fixes require sunset dates
       - Monthly audit of Tier 1 code in production"
```

---

## Best Practices

### Do's ✅

1. **Upgrade Early:** If in doubt, upgrade to higher tier
2. **Document Decisions:** Record tier changes in dev-notes.md
3. **Trust Gojo's Judgment:** Gojo is trained to assess risk
4. **Be Transparent:** Explain why you're requesting downgrade
5. **Plan Ahead:** Consider tier when starting feature

### Don'ts ❌

1. **Don't Skip Tiers:** Don't jump Tier 3 → Tier 1 without excellent reason
2. **Don't Downgrade Under Pressure:** Deadlines are not justification
3. **Don't Override Gojo Without Reason:** Gojo's rejections are protective
4. **Don't Hide Requirements:** Tell Gojo if you discover auth/payment needs
5. **Don't Assume Lower is Faster:** Bugs from skipped reviews cost more time

---

## Gojo's Role in Transitions

### Upgrade Requests
- **Always Approves:** Increasing rigor is always allowed
- **Facilitates Backfill:** Ensures previous requirements met
- **Updates State:** Records tier change in project-state.json

### Downgrade Requests
- **Challenges Reasoning:** Acts as safety check
- **Asks Questions:** Validates justification
- **May Deny:** Rejects unsafe downgrades
- **Proposes Alternatives:** Suggests better approaches

### Gojo's Decision Framework

```python
def assess_downgrade_request(current_tier, requested_tier, justification):
    if "deadline" in justification or "time pressure" in justification:
        return "DENIED - Time pressure not valid reason"

    if handles_sensitive_data():
        return "DENIED - Security requirements unchanged"

    if production_code() and requested_tier == 1:
        return "DENIED - Production code requires minimum Tier 2"

    if justification_unclear():
        return "REQUEST CLARIFICATION"

    if legitimate_scope_reduction():
        return "APPROVED with conditions"

    return "DENIED - Insufficient justification"
```

---

## Tier Transition Checklist

### Before Requesting Upgrade

- [ ] Identified new requirements (auth, data, payments)
- [ ] Understand time impact of upgrade
- [ ] Ready to implement additional requirements
- [ ] Documented reason for upgrade in dev-notes.md

### Before Requesting Downgrade

- [ ] Verified scope reduction is real
- [ ] No sensitive data handling remains
- [ ] Prepared justification for Gojo
- [ ] Considered alternatives (abandon, restart)
- [ ] Ready to defend decision if challenged

### After Transition (Either Direction)

- [ ] Tier change recorded in project-state.json
- [ ] Dev-notes.md updated with decision rationale
- [ ] All requirements of new tier met
- [ ] Team/stakeholders informed (if applicable)

---

## Summary

**Tier transitions are safety mechanisms, not obstacles.**

- **Upgrades:** Always welcome, ensure quality and security
- **Downgrades:** Rarely needed, require strong justification
- **Gojo:** Acts as guardrail, not gatekeeper
- **Goal:** Right level of rigor for each feature

**When in doubt: Upgrade. Better safe than sorry.**

---

**Version:** v6.2.4
**Last Updated:** November 7, 2025
**Canonical Source:** https://github.com/DewyHRite/Domain-Zero-Protocol
