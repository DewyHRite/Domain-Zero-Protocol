# TIER SELECTION QUICK REFERENCE
## Domain Zero v6.0 - Adaptive Workflow Complexity

**Choose the right workflow tier for your feature**

---

## 🚀 TIER 1: RAPID (10-15 minutes)

**When to Use**:
- ✅ Prototypes and experiments
- ✅ Throwaway code
- ✅ Learning exercises
- ✅ HTML/CSS mockups
- ✅ Quick scripts

**What You Get**:
- Fast implementation
- No tests
- No security review
- Backup still created
- Minimal documentation

**Invocation**:
```bash
"Read yuuji.agent.md --tier rapid and create a file renaming script"
"Read yuuji.agent.md --tier rapid and build HTML landing page mockup"
```

**Trade-Off**: Speed over quality (acceptable for non-production code)

---

## ⚖️ TIER 2: STANDARD (30-45 minutes) [DEFAULT]

**When to Use**:
- ✅ Production features
- ✅ CRUD operations
- ✅ API endpoints
- ✅ UI components
- ✅ Database operations
- ✅ Email services
- ✅ Standard business logic
- ✅ **When unsure, use this**

**What You Get**:
- Test-first development
- Full OWASP security review
- Comprehensive documentation
- Backup + rollback plan
- 80% vulnerability detection

**Invocation**:
```bash
"Read yuuji.agent.md and implement user authentication"
"Read yuuji.agent.md --tier standard and implement user profile"
```

**Trade-Off**: Balanced quality and speed (default for most work)

---

## 🔒 TIER 3: CRITICAL (60-90 minutes)

**When to Use**:
- ✅ JWT/OAuth authentication
- ✅ Payment processing (Stripe, PayPal)
- ✅ Financial calculations
- ✅ Medical record handling (HIPAA)
- ✅ Legal document processing
- ✅ Admin privilege systems
- ✅ Credit card tokenization
- ✅ Database encryption
- ✅ API rate limiting (security)

**What You Get**:
- Test-first development
- Unit + Integration + E2E tests
- Enhanced OWASP security review
- Multi-model review (Claude + GPT-4o)
- Risk-based prioritization (P0/P1/P2/P3)
- Compliance analysis (PCI/HIPAA/SOC2)
- Performance benchmarking
- Enhanced backup (code + database)
- 95% vulnerability detection

**Invocation**:
```bash
"Read yuuji.agent.md --tier critical and implement Stripe payment processing"
"Read yuuji.agent.md --tier critical and implement JWT authentication"
```

**Trade-Off**: Maximum quality over speed (appropriate for sensitive features)

---

## DECISION TREE

```text
┌─────────────────────────────────────┐
│ Is this code going to production?   │
└─────────────┬───────────────────────┘
              │
              ├─ NO → TIER 1 (Rapid)
              │
              └─ YES → ┌──────────────────────────────────────────┐
                       │ Does this handle sensitive data/ops?     │
                       └─────────────┬────────────────────────────┘
                                     │
                                     ├─ YES → TIER 3 (Critical)
                                     │       (auth, payments, medical,
                                     │        legal, financial data)
                                     │
                                     └─ NO → TIER 2 (Standard)
                                             (standard production work)
```

---

## EXAMPLES BY FEATURE TYPE

| Feature | Recommended Tier | Rationale |
|---------|------------------|-----------|
| File renaming script | Tier 1 (Rapid) | Not production, throwaway code |
| User registration | Tier 2 (Standard) | Production, well-understood pattern |
| Password reset | Tier 2 (Standard) | Production, standard pattern |
| JWT authentication | Tier 3 (Critical) | Security-critical, auth system |
| Stripe payments | Tier 3 (Critical) | Financial, PCI compliance |
| CRUD API endpoints | Tier 2 (Standard) | Production, standard patterns |
| Admin dashboard UI | Tier 2 (Standard) | Production UI, low risk |
| Medical records | Tier 3 (Critical) | HIPAA compliance, sensitive data |
| Email notifications | Tier 2 (Standard) | Production utility, low risk |
| OAuth2 provider | Tier 3 (Critical) | Security-critical, complex auth |
| Blog post CRUD | Tier 2 (Standard) | Standard content management |
| Credit card token | Tier 3 (Critical) | PCI compliance, financial data |
| Rate limiting | Tier 3 (Critical) | Security mechanism, DoS prevention |

---

## QUICK TIPS

### Default Behavior
- **No --tier flag** = Tier 2 (Standard) automatically
- All existing workflows continue unchanged

### Backup Requirements
- **ALL tiers require backups** (even Tier 1 Rapid)
- Never skip backup creation

### When Unsure
- **Default to Tier 2 (Standard)**
- You can always upgrade to Tier 3 later if needed

### Switching Tiers
- Start with Tier 1 for prototype
- Upgrade to Tier 2 when moving to production
- Upgrade to Tier 3 when handling sensitive data

---

## PRODUCTIVITY GAINS

**Tier 1 vs v5.1**: +70% speed (30-45min → 10-15min)
**Tier 2 vs v5.1**: Same speed (30-45min unchanged)
**Tier 3 vs v5.1**: 50% more thorough security (30-45min → 60-90min)

**Overall**: +50% average productivity across mixed workload

---

## GETTING STARTED

### Your First Tier 1 Feature
```text
You: "Read yuuji.agent.md --tier rapid and create a Python script to rename files"
Yuuji: [Implements in 10-15 minutes, no tests, minimal docs]
You: Review and done!
```

### Your First Tier 2 Feature
```text
You: "Read yuuji.agent.md and implement user profile"
Yuuji: [Test-first implementation, 30-45 minutes]
You: Review → Approve
Megumi: [Prompted handoff engages; OWASP security review]
```

### Your First Tier 3 Feature
```text
You: "Read yuuji.agent.md --tier critical and implement Stripe payment processing"
Yuuji: [Enhanced tests + performance benchmarks, 60-90 minutes]
You: Review → Approve
Megumi: [Prompted handoff (Tier 3) with enhanced security review + multi-model analysis]
```

---

## NEED MORE HELP?

- **Full Documentation**: Read protocol/CLAUDE.md
- **Tier System Spec**: Read .protocol-state/tier-system-specification.md
- **Ask Gojo**: "Read gojo.agent.md - explain tier system"

---

**Version**: 6.0
**Last Updated**: 2025-11-05
**Domain Zero**: Adaptive Workflow Complexity System
