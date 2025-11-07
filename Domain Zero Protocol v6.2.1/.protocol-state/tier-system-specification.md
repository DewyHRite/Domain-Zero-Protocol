# ADAPTIVE WORKFLOW COMPLEXITY - TIER SYSTEM SPECIFICATION
## Domain Zero v6.2.1 Enhancement

**Enhancement ID**: ENH-001
**Priority**: CRITICAL
**Status**: IMPLEMENTATION IN PROGRESS
**Version**: 6.2.1
**Date**: 2025-11-05

---

## OVERVIEW

The Adaptive Workflow Complexity system introduces three workflow tiers that allow users to match process rigor to feature criticality, eliminating the "one-size-fits-all" workflow overhead.

**Problem Solved**: Current workflow takes 30-45 minutes for ALL features, creating 3x overhead for simple tasks like renaming a function or fixing a typo.

**Solution**: Three-tier system allows users to choose appropriate workflow depth.

---

## TIER SYSTEM DESIGN

### **TIER 1: RAPID** 🚀
**Use Cases**: Prototypes, experiments, learning exercises, throwaway code, simple scripts

**Workflow**:
1. User specifies task with `--tier rapid` flag
2. Yuuji implements WITHOUT tests (fast iteration)
3. Skip Megumi security review entirely
4. Minimal documentation (1-2 sentence summary)
5. **MAINTAIN**: Backup requirements (always create backup)
6. User reviews and approves

**Time**: 10-15 minutes per feature

**Trade-Off**: Speed over quality (acceptable for non-production code)

**Success Criteria**:
- ✅ Code implements requested functionality
- ✅ Backup created before changes
- ⚠️ No tests written
- ⚠️ No security review
- ⚠️ Minimal documentation

**Example Invocation**:
```
User: "Read YUUJI.md --tier rapid and create a Python script to rename files in a folder"
```

**Yuuji Response Pattern**:
```markdown
## Tier 1 (RAPID) Implementation: File Renaming Script

### Implementation
[Creates file_renamer.py with straightforward implementation]

### Backup
✅ Backup created: ./backups/2025-11-05-14-30/

### Documentation
Simple Python script that renames files in a folder based on pattern matching.

@user-review
```

---

### **TIER 2: STANDARD** ⚖️
**Use Cases**: Production features, client deliverables, standard development work

**Workflow**: CURRENT DUAL WORKFLOW (unchanged from v5.1)
1. User specifies task (default tier if no flag specified)
2. Yuuji implements with test-first development
3. Create backup before changes
4. Document rollback plan
5. User reviews implementation
6. Tag @security-review → Megumi audits
7. Remediation loop if needed
8. @approved when zero issues

**Time**: 30-45 minutes per feature

**Trade-Off**: Balanced quality and speed (default for most work)

**Success Criteria**:
- ✅ Comprehensive test coverage
- ✅ OWASP security review passed
- ✅ Complete documentation
- ✅ Backup + rollback plan
- ✅ Zero security issues

**Example Invocation**:
```
User: "Read YUUJI.md and implement user authentication"
User: "Read YUUJI.md --tier standard and implement user authentication"  (explicit)
```

**This is the CURRENT workflow - no changes needed for Tier 2.**

---

### **TIER 3: CRITICAL** 🔒
**Use Cases**: Authentication, payment processing, data handling, medical/legal apps, compliance requirements

**Workflow**: ENHANCED SECURITY + COMPREHENSIVE TESTING
1. User specifies task with `--tier critical` flag
2. Yuuji implements with test-first development
3. **ENHANCED**: Integration tests + E2E tests required (not just unit)
4. **ENHANCED**: Performance benchmarking required
5. Create backup before changes
6. Document rollback plan (with extensive verification)
7. User reviews implementation
8. Tag @security-review-critical → Megumi conducts enhanced audit
9. **ENHANCED**: Multi-model security review (Claude + GPT-4o if available)
10. **ENHANCED**: Risk-based prioritization (P0/P1/P2/P3)
11. Remediation loop with verification at each step
12. **ENHANCED**: Final checklist before @approved

**Time**: 60-90 minutes per feature

**Trade-Off**: Maximum quality over speed (appropriate for sensitive code)

**Success Criteria**:
- ✅ Comprehensive unit tests
- ✅ Integration tests for workflows
- ✅ E2E tests for user scenarios
- ✅ Performance benchmarks established
- ✅ Dual-model security review (if available)
- ✅ Risk assessment with severity scores
- ✅ Extensive documentation
- ✅ Tested rollback procedure
- ✅ Zero critical/high security issues

**Example Invocation**:
```
User: "Read YUUJI.md --tier critical and implement payment processing with Stripe"
```

**Yuuji Response Pattern**:
```markdown
## Tier 3 (CRITICAL) Implementation: Stripe Payment Processing

### Unit Tests
✅ test_create_payment_intent()
✅ test_validate_payment_amount()
✅ test_handle_webhook_signature()
[... 15+ unit tests ...]

### Integration Tests
✅ test_stripe_api_integration()
✅ test_payment_flow_with_real_stripe_test_mode()
✅ test_webhook_handling_workflow()
[... 8+ integration tests ...]

### E2E Tests
✅ test_full_checkout_to_confirmation_flow()
✅ test_payment_failure_handling()
✅ test_refund_workflow()

### Performance Benchmarks
- Payment intent creation: 145ms (target: <200ms) ✅
- Webhook processing: 23ms (target: <50ms) ✅
- Database transaction commit: 8ms (target: <10ms) ✅

### Security Considerations (Enhanced)
🔒 PCI DSS compliance maintained (no card data stored)
🔒 Webhook signature verification implemented
🔒 Rate limiting on payment endpoints (10/min per user)
🔒 Amount validation with decimal precision handling
🔒 Idempotency keys for duplicate prevention

### Backup
✅ Backup created: ./backups/2025-11-05-14-30/
✅ Database backup: ./backups/2025-11-05-14-30/db-snapshot.sql

### Rollback Plan
1. Stop payment service (systemctl stop payment-service)
2. Restore code from backup
3. Rollback database migration (alembic downgrade -1)
4. Restart service
5. Verify: curl /health/payments should return 200
6. Test: Process test payment (should succeed)

Rollback Time Estimate: 3 minutes
Rollback Dependencies: payment-service, database

@user-review
```

---

## TIER SELECTION GUIDE

### Decision Tree for Users

**Question 1: Is this code going to production?**
- **NO** → Tier 1 (Rapid)
- **YES** → Continue to Question 2

**Question 2: Does this code handle sensitive data or operations?**
- **YES** (auth, payments, medical, legal, financial) → Tier 3 (Critical)
- **NO** → Continue to Question 3

**Question 3: Is this a standard feature?**
- **YES** (CRUD, API endpoints, UI components, utilities) → Tier 2 (Standard)
- **UNSURE** → Default to Tier 2 (Standard)

---

### Tier Selection Examples

| Feature | Recommended Tier | Rationale |
|---------|------------------|-----------|
| File renaming script | Tier 1 (Rapid) | Throwaway script, not production |
| User registration | Tier 2 (Standard) | Production feature, standard pattern |
| Password reset | Tier 2 (Standard) | Production, but well-understood pattern |
| JWT authentication | Tier 3 (Critical) | Security-critical, authentication |
| Stripe payment processing | Tier 3 (Critical) | Financial transactions, PCI compliance |
| Database CRUD endpoints | Tier 2 (Standard) | Production, standard patterns |
| Admin dashboard UI | Tier 2 (Standard) | Production, but UI-focused |
| Medical record handling | Tier 3 (Critical) | HIPAA compliance, sensitive data |
| Email notification service | Tier 2 (Standard) | Production utility, low risk |
| OAuth2 provider | Tier 3 (Critical) | Security-critical, complex auth |
| Simple HTML landing page | Tier 1 (Rapid) | Prototype, quick iteration |
| Data export to CSV | Tier 2 (Standard) | Production feature, data handling |
| Credit card tokenization | Tier 3 (Critical) | PCI compliance, financial data |
| Blog post CRUD | Tier 2 (Standard) | Standard content management |
| API rate limiting | Tier 3 (Critical) | Security mechanism, DoS prevention |

---

## IMPLEMENTATION DETAILS

### Invocation Syntax

**Format**: `Read [AGENT].md --tier [rapid|standard|critical] and [task]`

**Examples**:
```
"Read YUUJI.md --tier rapid and create hello world script"
"Read YUUJI.md --tier standard and implement user profile"
"Read YUUJI.md --tier critical and implement OAuth2 provider"
"Read MEGUMI.md --tier critical and review payment processing"
```

**Default**: If no `--tier` flag specified, **Tier 2 (Standard)** is assumed.

---

### Agent Behavior Modifications

#### **YUUJI Changes**

**Tier 1 (Rapid)**:
- Skip test writing entirely
- Implement solution directly
- Create backup before changes (non-negotiable)
- Write 1-2 sentence documentation
- Tag @user-review (no @security-review)

**Tier 2 (Standard)**:
- Current behavior (no changes)
- Test-first development
- Backup + rollback plan
- Tag @security-review after user approval

**Tier 3 (Critical)**:
- Test-first development (unit + integration + E2E)
- Performance benchmarking required
- Enhanced backup (code + database)
- Extensive rollback plan with verification
- Tag @security-review-critical

---

#### **MEGUMI Changes**

**Tier 1 (Rapid)**:
- Not invoked (skip security review)

**Tier 2 (Standard)**:
- Current behavior (no changes)
- OWASP Top 10 systematic review
- SEC-ID documentation
- @remediation-required or @approved

**Tier 3 (Critical)**:
- Enhanced OWASP review with deeper analysis
- Multi-model review if available (Claude + GPT-4o)
- Risk-based prioritization (P0/P1/P2/P3)
- Performance analysis
- Compliance considerations (PCI, HIPAA, SOC2)
- Integration test verification
- Final security checklist before @approved

---

### State Tracking

**project-state.json additions**:
```json
{
  "tier_usage_statistics": {
    "tier_1_rapid": {
      "total_features": 0,
      "avg_time_minutes": 0,
      "last_used": null
    },
    "tier_2_standard": {
      "total_features": 0,
      "avg_time_minutes": 0,
      "last_used": null
    },
    "tier_3_critical": {
      "total_features": 0,
      "avg_time_minutes": 0,
      "last_used": null
    }
  },
  "current_feature_tier": "none"
}
```

**dev-notes.md format update**:
```markdown
## [Tier 1 - RAPID] File Renaming Script
...

## [Tier 2 - STANDARD] User Profile Implementation
...

## [Tier 3 - CRITICAL] Payment Processing
...
```

---

## TIER SYSTEM BENEFITS

### Productivity Gains

**Before (v5.1)**:
- All features: 30-45 minutes
- Simple script: 30-45 minutes (OVERKILL)
- Standard feature: 30-45 minutes (APPROPRIATE)
- Critical feature: 30-45 minutes (INSUFFICIENT)

**After (v6.0)**:
- Simple script (Tier 1): 10-15 minutes (**70% faster**)
- Standard feature (Tier 2): 30-45 minutes (same)
- Critical feature (Tier 3): 60-90 minutes (**50% more thorough**)

**Net Result**:
- 70% speed increase for rapid prototyping
- Maintained quality for standard work
- Enhanced security for critical features
- Average productivity gain: **+50%** across mixed workload

---

### Quality Improvements

**Tier 1 (Rapid)**:
- Acceptable: No tests for throwaway code
- Maintained: Backups prevent data loss

**Tier 2 (Standard)**:
- Maintained: Current quality level (80% vulnerability detection)

**Tier 3 (Critical)**:
- Enhanced: 95% vulnerability detection (multi-model review)
- Enhanced: Integration + E2E tests catch workflow issues
- Enhanced: Performance benchmarks prevent regressions

---

### User Experience

**Flexibility**: Users choose appropriate rigor
**Efficiency**: No more overkill for simple tasks
**Safety**: Critical features get extra scrutiny
**Learning**: Users understand quality trade-offs

---

## MIGRATION FROM v5.1

### Backward Compatibility

**All existing workflows default to Tier 2 (Standard)**:
- No `--tier` flag = Tier 2 automatically
- Current dev-notes.md entries remain valid
- Existing security-review.md processes unchanged

**Migration Steps**:
1. Update protocol files (CLAUDE.md, YUUJI.md, MEGUMI.md, NOBARA.md, GOJO.md)
2. Update project-state.json with tier tracking
3. Add tier-system-specification.md to docs
4. Users can immediately use `--tier` flags
5. Existing workflows continue without modification

**Breaking Changes**: NONE (all changes are additive)

---

## SUCCESS METRICS

### Adoption Metrics
- **Target**: 60%+ of features use explicit tier selection within 30 days
- **Measure**: Track tier_usage_statistics in project-state.json

### Productivity Metrics
- **Target**: 70% reduction in Tier 1 feature time (30-45min → 10-15min)
- **Measure**: avg_time_minutes per tier

### Quality Metrics
- **Target**: 95% vulnerability detection for Tier 3 features
- **Measure**: Post-deployment security incidents

### User Satisfaction
- **Target**: 85%+ users report tier system improves workflow
- **Measure**: User survey after 30 days

---

## NEXT STEPS

1. ✅ Design tier system specification (COMPLETE - this document)
2. ⏭️ Update CLAUDE.md with tier documentation
3. ⏭️ Update YUUJI.md for tier-aware implementation
4. ⏭️ Update MEGUMI.md for tier-aware security review
5. ⏭️ Update GOJO.md to brief agents on tier selection
6. ⏭️ Update project-state.json schema
7. ⏭️ Create user-facing tier selection guide
8. ⏭️ Test tier system with example features
9. ⏭️ Document in GOJO-UPDATES-PATCH.md
10. ⏭️ Release as Domain Zero v6.0

---

**END OF TIER SYSTEM SPECIFICATION**

**Version**: 6.2.1
**Status**: Ready for Implementation
**Next Action**: Update protocol files with tier system
