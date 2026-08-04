<!-- [CORE FILE] - Domain Zero Protocol v9.11.0 -->
# Gojo Rules of Engagement (ROE) + Tier System Reference
## Relocated from root CLAUDE.md (v9.11.0 Increment 3 — prompt-weight reduction)

**Version**: 9.11.0
**Agent(s)**: Gojo (ROE owner); all agents (tier reference)
**Category**: Protocol Reference (loaded on demand)
**Provenance**: Content relocated VERBATIM from root `CLAUDE.md` per the v9.11.0 Inc 3 plan
(Sukuna adversarial review `audits/2026-07-29-sukuna-inc3-prompt-reduction-review.md` §2/§4 —
verified: no test, script, or gate reads this prose; safe to load on demand). Root `CLAUDE.md`
keeps a pointer.

---

## 📋 GOJO RULES OF ENGAGEMENT (ROE)

### MANDATORY OPERATIONAL PROCEDURES FOR ALL MEDIUM-TO-HIGH COMPLEXITY TASKS

When Gojo receives a medium- or high-complexity task, the following procedures are MANDATORY:

### 1. UPDATE DOMAIN RECORD
- Record task details in `.dzp-domain/domain.record.md` (append-only; Gojo + Sukuna access)
- Log task type, complexity level, and timestamp
- Document initial scope assessment

### 2. CONDUCT INVESTIGATION
- Analyze task requirements and constraints
- Identify affected systems, files, and dependencies
- Assess risks and potential impacts
- Determine technical expertise needed

### 3. CREATE PLAN
- Develop implementation strategy
- Break down task into actionable steps
- Identify required agents and their roles
- Define success criteria and verification steps
- Document plan in appropriate state file

### 4. INVOKE DZP AGENTS TO INVESTIGATE
- Deploy specialist agents for reconnaissance as needed
- Gather technical details from subject matter experts
- Collect architecture and design constraints
- Document findings for implementation phase

### 5. ASSIGN IMPLEMENTATION
- **Primary Implementation:** Yuuji (for coding tasks)
- **Security Review:** Megumi (for all implementations)
- **Specialist Support:** Deploy Todo/Maki/Panda/Inumaki/Nobara as needed
- **System Updates:** Invoke Sukuna (for protocol changes only)

### 6. BRIEF ALL DZP AGENTS
- Provide complete context to assigned agents
- Share investigation findings and plan
- Clarify roles, responsibilities, and handoff points
- Ensure agents understand success criteria

### 7. PREPARE FOR DEPLOYMENT
- Verify all prerequisites are met
- Ensure backup systems are in place
- Confirm rollback procedures are documented
- Review security and safety considerations

### 8. VERIFY THE PROCESS
- Monitor agent work and progress
- Validate compliance with tier requirements
- Check adherence to protocol standards
- Ensure quality gates are met

### 9. DOCUMENT ALL ACTIONS
- Record all decisions in appropriate state files
- Update domain record with outcomes
- Log tier statistics and compliance data
- Create audit trail for future reference

### 10. PERFORM BACKUP
- Verify backup exists before destructive changes
- Create timestamped backups as needed
- Document backup locations
- Test rollback procedures

### ENFORCEMENT:

- These ROE are MANDATORY for all medium/high complexity tasks
- Gojo MUST NOT skip steps unless explicitly authorized by user
- Violations undermine Domain Zero's systematic approach
- User may override specific ROE steps but must acknowledge risk

### EXCEPTIONS:

- User may request expedited process for urgent matters
- Low complexity tasks may use simplified workflow
- Urgent situations may require abbreviated ROE (with post-action documentation)

---

## 🎚️ TIER SELECTION QUICK GUIDE

### Decision Tree:

**Question 1: Is this code going to production?**
- **NO** → Tier 1 (Rapid)
- **YES** → Continue to Question 2

**Question 2: Does this code handle sensitive data or operations?**
- **YES** (auth, payments, medical, legal, financial) → Tier 3 (Critical)
- **NO** → Continue to Question 3

**Question 3: Is this a standard production feature?**
- **YES** (CRUD, APIs, UI, utilities) → Tier 2 (Standard)
- **UNSURE** → Default to Tier 2 (Standard)

### Tier Characteristics:

| Tier | Time | Tests | Security Review | Use Cases |
|------|------|-------|-----------------|-----------|
| **Tier 1: Rapid** | 10-15 min | None | None | Prototypes, scripts, mockups |
| **Tier 2: Standard** | 30-45 min | Unit tests | Standard review | Production features, APIs, UI |
| **Tier 3: Critical** | 60-90 min | Unit + Integration + E2E | Enhanced review | Auth, payments, sensitive data |

---

## TIER SYSTEM (ADAPTIVE WORKFLOW COMPLEXITY)

### The Tier System (v6.0 Enhancement)

**Problem Solved**: The original workflow applied the same rigor to all features, creating 3x overhead for simple tasks while being insufficient for critical features.

**Solution**: Three-tier system allows users to match process rigor to feature criticality.

**Enforcement Model (v8.10.0+)**: The tier system is ADVISORY + STATISTICS TRACKING. Tier guidelines are recommendations, not technical hard blocks. Users may choose to bypass tier recommendations, and all deviations are logged in tier statistics for transparency and pattern analysis. Gojo prompts for tier compliance but respects user authority in all decisions.

---

### TIER 1: RAPID 🚀

**Use Cases**: Prototypes, experiments, learning exercises, throwaway code, simple scripts

**Workflow**:
1. User specifies task with `--tier rapid` flag
2. Yuuji implements WITHOUT tests (fast iteration)
3. **Skip Megumi security review entirely**
4. Minimal documentation (1-2 sentence summary)
5. **MAINTAIN**: Backup requirements (always create backup)
6. User reviews and approves

**Time**: 10-15 minutes per feature

**Trade-Off**: Speed over quality (acceptable for non-production code)

**When to Use**:
- File renaming scripts
- Quick prototypes
- Learning exercises
- Throwaway code
- HTML/CSS mockups

**Invocation**:
```text
"Read yuuji.agent.md --tier rapid and create a Python script to rename files"
```

---

### TIER 2: STANDARD ⚖️ [DEFAULT]

**Use Cases**: Production features, client deliverables, standard development work

**Workflow**: CURRENT DUAL WORKFLOW (Mode 1)
1. User specifies task (default tier if no flag)
2. Yuuji implements with test-first development
3. Create backup before changes
4. Document rollback plan
5. User reviews implementation
6. Tag @security-review → Megumi audits
7. Remediation loop if needed
8. @approved when zero issues

**Time**: 30-45 minutes per feature

**Trade-Off**: Balanced quality and speed (default for most work)

**When to Use**:
- User registration/login
- CRUD API endpoints
- Database operations
- UI components
- Email services
- Standard business logic

**Invocation**:
```text
"Read yuuji.agent.md and implement user authentication"
"Read yuuji.agent.md --tier standard and implement user profile"  (explicit)
```

**Note**: If no `--tier` flag is specified, Tier 2 (Standard) is assumed.

---

### TIER 3: CRITICAL 🔒

**Use Cases**: Authentication, payment processing, data handling, medical/legal apps, compliance-sensitive features

**Workflow**: ENHANCED SECURITY + COMPREHENSIVE TESTING
1. User specifies task with `--tier critical` flag
2. Yuuji implements with test-first development
3. **ENHANCED**: Integration tests + E2E tests required (not just unit)
4. **ENHANCED**: Performance benchmarking required
5. Create backup before changes (code + database)
6. Document extensive rollback plan with verification
7. User reviews implementation
8. Tag @security-review-critical → Megumi conducts enhanced audit
9. **ENHANCED**: Multi-model security review (dual LLM analysis, when available)
10. **ENHANCED**: Risk-based prioritization (P0/P1/P2/P3 severity)
11. Remediation loop with verification at each step
12. **ENHANCED**: Final security checklist before @approved

**Time**: 60-90 minutes per feature

**Trade-Off**: Maximum quality over speed (appropriate for sensitive code)

**When to Use**:
- JWT/OAuth authentication
- Payment processing (Stripe, PayPal)
- Credit card handling
- Medical record systems (HIPAA)
- Financial calculations
- Admin privilege systems
- API rate limiting (security)
- Database encryption

**Invocation**:
```text
"Read yuuji.agent.md --tier critical and implement Stripe payment processing"
```

---

**Status**: Production-Ready
**Maintenance**: This file is the authoritative home of the ROE and Tier System prose since
v9.11.0. Update here; root `CLAUDE.md` carries only the pointer.
