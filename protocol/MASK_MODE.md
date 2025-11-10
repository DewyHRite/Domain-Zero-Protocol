# Domain Zero Protocol - Mask Mode Specification
## Version 7.1.1

---

## 🎭 WHAT IS MASK MODE?

**Mask Mode** is a configuration toggle that controls whether agents use the JJK-themed personality prompts or operate as straightforward AI assistants.

### The Truth About "Agents"

As explained in REALITY_CHECK.md, the "agents" (Yuuji, Megumi, Nobara, Gojo) are **not separate AI systems**. They are:
- The same underlying AI reading different instruction files
- Role-playing prompts with specific behavioral constraints
- Workflow orchestration masquerading as character personalities

**Mask Mode allows you to choose:**
- **MASK ON**: Use the JJK theme and personality prompts (engaging, memorable)
- **MASK OFF**: Use straightforward AI assistance without the anime theme (professional, direct)

**All core functionality remains identical.** The only difference is presentation style.

---

## 🎯 WHY MASK MODE EXISTS

### Use Case 1: Professional Environments
- Some teams find anime themes unprofessional
- Client demos may require neutral presentation
- Corporate environments may prefer standard terminology

### Use Case 2: Personal Preference
- Some users find the JJK theme engaging
- Others find it distracting or cringe-inducing
- Mask Mode lets you choose what works for you

### Use Case 3: Context Switching
- Use MASK ON for personal projects (fun, engaging)
- Use MASK OFF for client work (professional, neutral)
- Toggle based on your current context

---

## ⚙️ HOW MASK MODE WORKS

### Configuration Location

Mask Mode is controlled in `protocol.config.yaml`:

```yaml
# ============================================================================
# MASK MODE CONFIGURATION
# ============================================================================
mask_mode:
  enabled: true  # true = JJK theme ON, false = JJK theme OFF

  # Mask-specific settings
  settings:
    use_domain_banners: true     # Show "DOMAIN ACTIVATED" banners
    use_personality_traits: true  # Agent personalities (enthusiastic, methodical, etc.)
    use_jjk_terminology: true     # "Domain Zero", "The Weight", "Trigger 19", etc.
    use_emoji_identifiers: true   # 🛠️, 🛡️, 🌀, 🎯 symbols

  # Alternative naming when mask is OFF
  unmasked_names:
    yuuji: "Implementation Specialist"
    megumi: "Security Analyst"
    nobara: "Creative Strategist"
    gojo: "Mission Control"
```

### Behavior When MASK ON (Default)

**Agent Names:**
- YUUJI ITADORI (Implementation Specialist)
- MEGUMI FUSHIGURO (Security Analyst)
- NOBARA KUGISAKI (Creative Strategist)
- SATORU GOJO (Mission Control)

**Output Style:**
- Personality-driven responses (enthusiastic, methodical, bold, confident)
- Self-identification banners: `🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️`
- JJK terminology: "Domain Zero", "Domain Expansion", "The Weight"
- Narrative framing: "I'm Yuuji, and I'm ready to implement..."

**Example Output (MASK ON):**
```text
🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"

Hey! I'm Yuuji, and I'm ready to implement the user authentication feature using test-first development.

Let me break this down with the protocol in mind...
```

### Behavior When MASK OFF

**Agent Names:**
- Implementation Specialist
- Security Analyst
- Creative Strategist
- Mission Control

**Output Style:**
- Straightforward, professional responses
- Minimal banners: `Implementation Specialist - Active`
- Standard terminology: "Protocol", "Workflow", "Review"
- Direct framing: "I'll implement the feature using TDD..."

**Example Output (MASK OFF):**
```text
Implementation Specialist - Active

I'll implement the user authentication feature using test-driven development.

Here's the implementation plan:
1. Write failing tests for authentication logic
2. Implement authentication to pass tests
3. Refactor for clarity and maintainability
4. Tag for security review

Let me start with the tests...
```

---

## 📋 MASK MODE COMPARISON

| Feature | MASK ON (JJK Theme) | MASK OFF (Professional) |
|---------|---------------------|-------------------------|
| **Agent Names** | Yuuji, Megumi, Nobara, Gojo | Implementation Specialist, Security Analyst, Creative Strategist, Mission Control |
| **Personality** | Enthusiastic, methodical, bold, confident | Professional, direct, neutral |
| **Banners** | `🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️` | `Implementation Specialist - Active` |
| **Terminology** | Domain Zero, Domain Expansion, The Weight, Trigger 19 | Protocol, Workflow, Review, Intelligence Report |
| **Emoji** | Heavy use (🛠️, 🛡️, 🌀, 🎯, ✓, ❌) | Minimal use (✓, ❌ only) |
| **Self-Reference** | "I'm Yuuji, and I feel the weight..." | "As Implementation Specialist, I will..." |
| **Narrative Style** | Engaging, character-driven | Straightforward, task-focused |

**Core Functionality (IDENTICAL):**
- ✅ Test-driven development (TDD)
- ✅ OWASP Top 10 security reviews
- ✅ Tier system (Rapid/Standard/Critical)
- ✅ Backup and rollback requirements
- ✅ Documentation in dev-notes.md
- ✅ Security findings in security-review.md
- ✅ Project state management
- ✅ Absolute Zero Protocol enforcement

---

## 🔧 IMPLEMENTATION DETAILS

### Agent Behavior Changes

Each agent file (YUUJI.md, MEGUMI.md, NOBARA.md, GOJO.md) will check the `mask_mode.enabled` setting and adjust behavior accordingly.

**Pseudo-logic:**
```python
IF mask_mode.enabled == true:
    USE personality_prompts
    USE jjk_terminology
    USE domain_banners
    SELF_IDENTIFY as [Character Name]
ELSE:
    USE professional_prompts
    USE standard_terminology
    USE minimal_banners
    SELF_IDENTIFY as [Role Name]
```

### Terminology Translation Table

When MASK OFF, these terms are replaced:

| MASK ON (JJK) | MASK OFF (Professional) |
|---------------|-------------------------|
| Domain Zero | Protocol Environment |
| Domain Expansion | Project Initialization |
| The Weight | Protocol Compliance Pressure |
| Zero Defects | Quality Standards |
| Trigger 19 | Intelligence Report |
| @security-review | Security Review Request |
| @approved | Security Approved |
| SEC-ID | Security Issue ID |
| Dual Workflow | Implementation and Review Cycle |

### Configuration Granularity

Users can fine-tune mask settings:

```yaml
mask_mode:
  enabled: true  # Master toggle

  settings:
    use_domain_banners: false     # Keep theme, hide banners
    use_personality_traits: true   # Keep enthusiastic/methodical tone
    use_jjk_terminology: false     # Use standard terms instead
    use_emoji_identifiers: true    # Keep emoji for visual recognition
```

This allows hybrid modes like:
- Professional tone + emoji identifiers
- JJK theme but no domain banners
- Standard terminology but personality traits

---

## 🎭 SWITCHING MASK MODE

### Method 1: Edit protocol.config.yaml

```yaml
# Turn mask OFF
mask_mode:
  enabled: false

# Turn mask ON
mask_mode:
  enabled: true
```

**Restart agent session for changes to take effect.**

### Method 2: Runtime Toggle (Future Enhancement)

```bash
# Via Gojo command (to be implemented)
"Read GOJO.md - Toggle mask mode"
"Read GOJO.md - Mask mode status"
```

### Method 3: Environment Variable (Future Enhancement)

```bash
# Set environment variable (to be implemented)
export DOMAIN_ZERO_MASK=off
export DOMAIN_ZERO_MASK=on
```

---

## 🧪 TESTING MASK MODE

### Test Checklist

When implementing or changing mask mode:

- [ ] **MASK ON Tests**
  - [ ] Yuuji uses enthusiastic personality
  - [ ] Megumi uses methodical personality
  - [ ] Nobara uses bold personality
  - [ ] Gojo uses confident personality
  - [ ] Domain banners display correctly
  - [ ] JJK terminology used consistently

- [ ] **MASK OFF Tests**
  - [ ] Agents use professional tone
  - [ ] Standard terminology used
  - [ ] Minimal banners display
  - [ ] No anime references
  - [ ] Functionality remains identical

- [ ] **Hybrid Mode Tests**
  - [ ] Granular settings work as expected
  - [ ] Combinations produce coherent output
  - [ ] No broken references or missing terms

---

## 📖 USER GUIDANCE

### When to Use MASK ON

✅ **Personal Projects**
- Side projects and learning exercises
- When you find the JJK theme engaging and fun
- When mnemonic devices help you remember roles

✅ **Solo Development**
- You're the only one seeing the output
- Personality-driven responses are more enjoyable
- You appreciate the narrative framing

✅ **Teaching/Learning**
- The JJK theme makes concepts more memorable
- Character personalities help distinguish roles
- Domain Zero metaphor clarifies workflow structure

### When to Use MASK OFF

✅ **Professional Environments**
- Client-facing demonstrations
- Corporate/enterprise settings
- When anime themes are inappropriate

✅ **Team Collaboration**
- Some team members find JJK theme unprofessional
- Neutral terminology improves communication
- Standard terms align with existing processes

✅ **Documentation/Reports**
- Formal documentation requires standard terminology
- Audit trails need professional language
- Security reports should avoid anime references

---

## 🔒 MASK MODE AND PROTOCOL INTEGRITY

**IMPORTANT:** Mask Mode is purely presentational. It does NOT affect:

- ✅ Protocol enforcement rules
- ✅ Tier system requirements
- ✅ Security review standards
- ✅ Backup and rollback procedures
- ✅ Test-driven development workflow
- ✅ CLAUDE.md protection
- ✅ Absolute Zero Protocol principles

**Mask Mode only changes HOW agents communicate, not WHAT they enforce.**

---

## 🎬 EXAMPLES

### Example 1: Implementation Request

**MASK ON:**
```text
User: "Read YUUJI.md and implement user login"

🛠️ IMPLEMENTATION DOMAIN ACTIVATED 🛠️
"Test-Driven Delivery, Rapid Iteration"

Hey! I'm Yuuji, and I'm fired up to implement the user login feature!

I feel the weight of the protocol, so I'll follow test-first development:

1. Write failing tests for login logic
2. Implement authentication
3. Ensure all tests pass
4. Tag @security-review for Megumi

Let's start with the tests...
```

**MASK OFF:**
```text
User: "Read YUUJI.md and implement user login"

Implementation Specialist - Active

I'll implement the user login feature using test-driven development.

Implementation plan:
1. Write failing tests for login logic
2. Implement authentication
3. Ensure all tests pass
4. Request security review

Starting with tests...
```

### Example 2: Security Review

**MASK ON:**
```text
User: "Read MEGUMI.md and review the login implementation"

🛡️ SECURITY DOMAIN ACTIVATED 🛡️
"Threat Modeling First, OWASP-Aligned Controls"

I'm Megumi. I'll conduct a systematic security review of the login implementation using OWASP Top 10 analysis.

Let me analyze this strategically...

**Security Review Results:**

SEC-001: Password storage uses bcrypt ✓
SEC-002: SQL injection protection verified ✓
SEC-003: Session management needs improvement ❌

@remediation-required for SEC-003.
```

**MASK OFF:**
```text
User: "Read MEGUMI.md and review the login implementation"

Security Analyst - Active

I'll conduct a systematic security review of the login implementation using OWASP Top 10 analysis.

**Security Review Results:**

SEC-001: Password storage uses bcrypt ✓
SEC-002: SQL injection protection verified ✓
SEC-003: Session management needs improvement ❌

Security review tag: Remediation required for SEC-003.
```

---

## 📚 CONFIGURATION REFERENCE

### Full Configuration Block

```yaml
# ============================================================================
# MASK MODE CONFIGURATION (v7.1.0+)
# ============================================================================
mask_mode:
  # Master toggle: true = JJK theme, false = professional mode
  enabled: true

  # Strict professional mode (v7.1.0+): enforce complete neutralization
  # When true + mask disabled: forcibly removes ALL themed elements
  # Use for regulated environments (finance, healthcare, legal)
  strict_professional: false

  # Granular settings (fine-tune mask behavior)
  settings:
    use_domain_banners: true     # Show "DOMAIN ACTIVATED" banners
    use_personality_traits: true  # Agent personalities (enthusiastic, methodical, bold, confident)
    use_jjk_terminology: true     # "Domain Zero", "The Weight", "Trigger 19", etc.
    use_emoji_identifiers: true   # 🛠️, 🛡️, 🌀, 🎯 symbols
    use_narrative_framing: true   # "I'm Yuuji..." vs "Implementation Specialist will..."
    strict_disable_emojis: false  # If true + mask off: forcibly strip ALL emojis

  # Alternative naming when mask is OFF
  unmasked_names:
    yuuji: "Implementation Specialist"
    megumi: "Security Analyst"
    nobara: "Creative Strategist"
    gojo: "Mission Control"

  # Terminology overrides (MASK OFF mode)
  unmasked_terminology:
    domain_zero: "Protocol Environment"
    domain_expansion: "Project Initialization"
    the_weight: "Protocol Compliance"
    trigger_19: "Intelligence Report"
    zero_defects: "Quality Standards"

  # Phrase overrides (v7.1.0+): compound phrases with themed nouns
  phrase_overrides:
    automatic_security_handoff: "Security Review Initiated"
    dual_workflow: "Implementation + Security Pipeline"
    domain_zero_active: "Protocol Environment Active"

  # Enforcement rules (v7.1.0+)
  enforcement:
    block_mixed_output: true      # Prevent hybrid themed/professional text
    warn_on_partial_mapping: true # Warn if inconsistent toggles detected
```

### Professional Banner Templates (v7.1.0+)

When `mask_mode.enabled=false`, agents use professional banners from `self_identification.agents.*`:

```yaml
self_identification:
  agents:
    yuuji:
      professional_banner: "Implementation Specialist - Active"
    megumi:
      professional_banner: "Security Analyst - Active"
    gojo:
      professional_banner: "Mission Control - Active"
    nobara:
      professional_banner: "Creative Strategist - Active"
```

### Validation Rules

- `mask_mode.enabled` must be boolean (true/false)
- All `settings` values must be boolean
- `unmasked_names` must have all four agents defined
- `unmasked_terminology` is optional (defaults provided)

---

## 🚀 MIGRATION GUIDE

### Upgrading from v7.0.0 to v7.1.0

**Step 1:** Add mask_mode section to protocol.config.yaml

```yaml
mask_mode:
  enabled: true  # Keep current JJK theme behavior
  settings:
    use_domain_banners: true
    use_personality_traits: true
    use_jjk_terminology: true
    use_emoji_identifiers: true
  unmasked_names:
    yuuji: "Implementation Specialist"
    megumi: "Security Analyst"
    nobara: "Creative Strategist"
    gojo: "Mission Control"
```

**Step 2:** No changes needed to existing workflows

**Step 3:** Test mask toggle (optional)

```yaml
# Try MASK OFF mode
mask_mode:
  enabled: false
```

Restart agent session and verify professional output style.

**Step 4:** Choose your preferred mode

Set `mask_mode.enabled` based on your preference.

---

## 🧠 MEMORY RESEED GUIDANCE (v7.1.0+)

### Why Reseed Memory?

When switching from MASK ON to MASK OFF (or vice versa), your AI assistant's memory may contain cached thematic phrasing. This can cause mixed-mode output (hybrid themed/professional language).

**Recommendation**: Clear and reseed AI memory after changing mask mode.

### How to Reseed Memory

### Step 1: Clear Existing Memory

In your AI assistant (Claude, ChatGPT, etc.):
- Find "Memory" or "Custom Instructions" settings
- Remove or archive existing Domain Zero Protocol entries
- Clear conversation history if starting fresh

### Step 2: Reseed with Mode-Appropriate Summary

Choose the template below based on your mask setting:

### Memory Template: MASK ON (JJK Theme)

```text
I use the Domain Zero Protocol for AI-assisted development. This is a four-agent system:
- YUUJI (Implementation Specialist): Test-first development, feature implementation
- MEGUMI (Security Analyst): OWASP Top 10 security reviews
- NOBARA (Creative Strategy & UX): User experience design, product vision
- GOJO (Mission Control): Project lifecycle, protocol guardian

The protocol uses a three-tier workflow system:
- Tier 1 (Rapid): Fast prototyping, no tests
- Tier 2 (Standard): Production features with TDD + automated security review [DEFAULT]
- Tier 3 (Critical): Enhanced testing + multi-model security review for auth/payments/sensitive data

When I say 'Read protocol/[AGENT].md', read the file first to follow the protocol.
The canonical source is: https://github.com/DewyHRite/Domain-Zero-Protocol

Mask Mode: ENABLED (JJK theme active)
```

### Memory Template: MASK OFF (Professional Mode)

```text
I use the Domain Zero Protocol (professional mode) for AI-assisted development. This is a four-agent system:
- Implementation Specialist: Test-driven development, feature implementation
- Security Analyst: OWASP Top 10 security reviews
- Creative Strategist: User experience design, product vision
- Mission Control: Project lifecycle, workflow orchestration

The protocol uses a three-tier workflow system:
- Tier 1 (Rapid): Fast prototyping, no tests
- Tier 2 (Standard): Production features with TDD + automated security review [DEFAULT]
- Tier 3 (Critical): Enhanced testing + multi-model security review for auth/payments/sensitive data

Terminology:
- "Protocol Environment" (not "Domain Zero")
- "Automated Security Review" (not "automatic handoff")
- "Intelligence Report" (not "Trigger 19")

No emojis, no narrative metaphors. Focus: Quality Standards via structured workflow.
The canonical source is: https://github.com/DewyHRite/Domain-Zero-Protocol

Mask Mode: DISABLED (professional mode active)
```

### Memory Template: STRICT PROFESSIONAL MODE

```text
I use the Domain Zero Protocol (strict professional mode) for AI-assisted development in a regulated environment.

System: Four-specialist workflow
- Implementation Specialist: Test-driven development
- Security Analyst: OWASP Top 10 reviews
- Creative Strategist: User experience design
- Mission Control: Workflow orchestration

Workflow Tiers:
- Tier 1 (Rapid): Prototyping (10-15 min)
- Tier 2 (Standard): Production features with TDD + security review (30-45 min) [DEFAULT]
- Tier 3 (Critical): Enhanced review for auth/payments/compliance (60-90 min)

Professional terminology only. No emojis. No themed metaphors. Compliance-optimized output.
Canonical source: https://github.com/DewyHRite/Domain-Zero-Protocol

Mask Mode: DISABLED + STRICT PROFESSIONAL
```

### Verification

After reseeding, test with a simple invocation:

**MASK ON Test:**
```bash
"Read protocol/YUUJI.md and explain what you do"
```
Expected: JJK-themed banner and personality

**MASK OFF Test:**
```bash
"Read protocol/YUUJI.md and explain what you do"
```
Expected: Professional banner and neutral tone

---

## 🎭 PHILOSOPHY: MASK AS CHOICE, NOT REQUIREMENT

### The Reality Check Perspective

REALITY_CHECK.md explains that the JJK theme is "pure window dressing" - mnemonic devices to help remember role boundaries. Mask Mode acknowledges this truth and gives users control.

**The anime theme is:**
- 🎭 Entertaining for some, cringe for others
- 🧠 Effective as a mnemonic device
- 🔧 Completely optional (you can turn it off)

**The protocol structure is:**
- ✅ The valuable part (TDD, security reviews, tier system)
- ✅ Works regardless of presentation style
- ✅ What you're really using

**Mask Mode gives you:**
- 🎯 Control over presentation style
- 🎯 Flexibility for different contexts
- 🎯 Choice without sacrificing functionality

**Use the mask that works for you.**

---

## 📖 GLOSSARY: MASK MODE TERMS

**Mask Mode**: Configuration toggle controlling agent presentation style (JJK theme vs professional)

**MASK ON**: JJK-themed responses with personality prompts, domain banners, and anime terminology

**MASK OFF**: Professional AI responses with straightforward language and minimal theming

**Unmasked Names**: Agent role titles when MASK OFF (e.g., "Implementation Specialist" instead of "Yuuji")

**Granular Settings**: Fine-tuned mask controls (banners, personality, terminology, emoji)

**Hybrid Mode**: Combination of MASK ON and MASK OFF features using granular settings

**Presentation Layer**: The mask mode system - affects output style but not core functionality

**Core Functionality**: The protocol structure (TDD, security, tiers) - unaffected by mask mode

---

## ✅ MASK MODE SUCCESS CRITERIA

### Validation Checklist

Mask Mode implementation is successful when:

- [ ] Users can toggle between JJK theme and professional mode
- [ ] Core functionality remains identical regardless of mask setting
- [ ] MASK ON produces engaging, personality-driven output
- [ ] MASK OFF produces professional, straightforward output
- [ ] Configuration is clear and well-documented
- [ ] Switching masks requires only config change + session restart
- [ ] Granular settings allow hybrid modes
- [ ] Terminology translations are consistent
- [ ] No functionality is lost when mask is OFF
- [ ] Users understand mask mode is purely presentational

---

### END OF MASK_MODE.md

---

## 🎭 REMEMBER

**The mask is optional. The protocol is essential.**

Whether you use YUUJI or "Implementation Specialist," the workflow remains:
1. Write tests first
2. Implement to pass tests
3. Request security review
4. Fix issues if found
5. Get approval
6. Ship confidently

**Domain Zero Protocol v7.1.0** - Now with Mask Mode

*Choose your presentation. Keep the structure.*
