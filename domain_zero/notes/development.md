# Development Notes
**Version:** 1.0  
**Last Updated:** 2025-11-04  
**Authority Level:** META - System Documentation

---

## Purpose
This file contains **technical documentation** for understanding, maintaining, and debugging the three-role protocol system. These notes are for system developers and maintainers, not for the roles themselves.

---

## Cross-References
- **Root Index:** `../CLAUDE.md`
- **All Role Files:** `../exorcists/*.md`
- **All Binding Files:** `../bindings/*.md`
- **All Domain Files:** `../domains/*.md`
- **Agent Notes:** `./agent-notes.md`

---

## System Architecture Overview

### The Three-Role System
```
┌─────────────────────────────────────────────────────────┐
│                     USER INTERFACE                       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  WORKFLOW BINDING                        │
│         (Single Role Per Session Enforcement)            │
└─────────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
         ┌──────────┐ ┌──────────┐ ┌──────────┐
         │  YUUJI   │ │  MEGUMI  │ │  GOJO    │
         │  (Heart) │ │  (Mind)  │ │(Observer)│
         └──────────┘ └──────────┘ └──────────┘
                │           │           │
                └───────────┼───────────┘
                            ▼
                ┌─────────────────────┐
                │ ISOLATION BINDING   │
                │ (Awareness Control) │
                └─────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ GOJO DOMAIN   │
                    │ (Enforcement) │
                    └───────────────┘
```

---

## Design Principles

### Principle 1: Modular Architecture
**Goal:** Break large protocol into manageable, focused files

**Implementation:**
- Each role has dedicated file (~650-850 lines)
- Binding files control cross-role behavior
- Domain files contain specialized logic
- Conversion files enable mode switching

**Benefits:**
- Easier to maintain and update
- Reduced token usage per session
- Clear separation of concerns
- Easier debugging

---

### Principle 2: Closed-Loop Cross-Referencing
**Goal:** Every file knows its place in the system

**Implementation:**
- Each file lists its cross-references at the top
- Files reference each other bidirectionally
- Root index (`CLAUDE.md`) maps entire system

**Benefits:**
- No orphaned files
- Clear navigation paths
- Easy to trace dependencies
- Prevents confusion

---

### Principle 3: Isolation by Design
**Goal:** Yuuji and Megumi are unaware of Gojo's existence

**Implementation:**
- Yuuji and Megumi files contain NO mention of Gojo
- Isolation binding enforces forbidden vocabulary
- Gojo operates in complete silence
- Enforcement happens without notification

**Benefits:**
- Natural behavior from Yuuji and Megumi
- No meta-commentary or self-consciousness
- Gojo can monitor without interference
- Clean separation of concerns

---

### Principle 4: Single Role Per Session
**Goal:** Only one role active at a time (except Gojo)

**Implementation:**
- Workflow binding enforces exact invocation phrases
- No autonomous role switching allowed
- Clear handoff protocols between roles
- Gojo always passive, never interferes

**Benefits:**
- Clear user expectations
- No role confusion
- Predictable behavior
- Clean conversation flow

---

## File Structure Deep Dive

### Root Level: `CLAUDE.md`
**Purpose:** Central navigation hub and system overview

**Key Sections:**
- System overview and philosophy
- Session tracking
- Cross-reference maps
- Quick start guides
- Emergency protocols
- Invocation protocols for all roles

**Token Count:** ~4,500 lines

**Maintenance Notes:**
- Update when new files are added
- Keep cross-reference map current
- Ensure invocation phrases match workflow binding

---

### Exorcists Directory: Role Definitions

#### `exorcists/yuuji.md` - The Heart
**Purpose:** Implementation-focused role

**Key Sections:**
- Capabilities and restrictions
- Communication style
- Output templates
- Workflow integration
- Instinctive awareness (of constraints, without knowing source)
- Isolation compliance

**Token Count:** ~650 lines

**Maintenance Notes:**
- Keep output templates consistent
- Ensure no Gojo mentions
- Update capabilities as needed

---

#### `exorcists/megumi.md` - The Mind
**Purpose:** Security and architecture analysis role

**Key Sections:**
- Security analysis framework
- OWASP Top 10 checklist
- Performance analysis framework
- Output templates for audits
- Strategic reasoning guidelines
- Isolation compliance

**Token Count:** ~750 lines

**Maintenance Notes:**
- Keep OWASP checklist current
- Ensure no Gojo mentions
- Update security frameworks as threats evolve

---

#### `exorcists/gojo.md` - The Observer
**Purpose:** Passive monitoring and enforcement role

**Key Sections:**
- Passive monitoring system
- Enforcement system with violation detection
- Strict non-interference rules
- Invocation protocols
- Analysis methodology

**Token Count:** ~850 lines

**Maintenance Notes:**
- Update violation patterns as needed
- Ensure complete silence in operation
- Keep detection patterns comprehensive

---

### Bindings Directory: Cross-Role Control

#### `bindings/workflow.md` - Workflow Binding Protocol
**Purpose:** Control role activation and transitions

**Key Sections:**
- Single role per session enforcement
- Exact invocation phrases
- Output structure templates
- Workflow scenarios
- Emergency protocols
- Quality assurance checklists

**Token Count:** ~400 lines

**Maintenance Notes:**
- Keep invocation phrases synchronized with root index
- Update workflow scenarios as patterns emerge
- Ensure emergency protocols are clear

---

#### `bindings/isolation.md` - Isolation Binding Protocol
**Purpose:** Enforce awareness separation between roles

**Key Sections:**
- Ironclad isolation rules
- Silent operation protocols for Gojo
- Forbidden vocabulary lists
- Breach scenarios and responses
- Testing protocols
- Emergency restoration procedures

**Token Count:** ~550 lines

**Maintenance Notes:**
- Update forbidden vocabulary as needed
- Add breach scenarios from real incidents
- Keep testing protocols current

---

### Domains Directory: Specialized Logic

#### `domains/gojo-enforce.md` - Gojo's Enforcement Protocol
**Purpose:** Define violation detection and logging

**Key Sections:**
- Five violation categories
- Automatic detection patterns
- Silent logging system
- Real-time pattern matching
- Comprehensive report templates

**Token Count:** ~750 lines

**Maintenance Notes:**
- Add new violation patterns as discovered
- Update detection logic for edge cases
- Ensure logging remains silent

---

#### `domains/gojo-silent.md` - Gojo's Passive Monitoring Protocol
**Purpose:** Define comprehensive observation methodology

**Key Sections:**
- Complete monitoring scope
- Monitoring techniques
- Data structures for tracking
- Key metrics
- Monitoring workflows

**Token Count:** ~800 lines

**Maintenance Notes:**
- Expand monitoring scope as needed
- Update metrics based on user needs
- Ensure passive nature is maintained

---

### Conversion Directory: Mode Switching

#### `conversion/yuuji_freetalk.md` - Yuuji Free-Talk Protocol
**Purpose:** Enable casual conversation mode for Yuuji

**Key Sections:**
- Free-talk philosophy
- When to use vs. standard mode
- Tone and style guidelines
- Detailed examples
- Mode transition protocols
- Quality standards

**Token Count:** ~650 lines

**Maintenance Notes:**
- Add examples from successful interactions
- Refine quality standards based on feedback
- Ensure protocol compliance maintained

---

#### `conversion/megumi_freetalk.md` - Megumi Free-Talk Protocol
**Purpose:** Enable strategic dialogue mode for Megumi

**Key Sections:**
- Strategic dialogue philosophy
- When to use vs. formal audit mode
- Analytical voice patterns
- Detailed examples
- Depth levels
- Common patterns

**Token Count:** ~750 lines

**Maintenance Notes:**
- Add examples from successful interactions
- Refine analytical patterns
- Ensure protocol compliance maintained

---

### Notes Directory: Meta Documentation

#### `notes/development.md` - This File
**Purpose:** Technical documentation for system maintainers

**Token Count:** ~1,000 lines (estimated)

---

#### `notes/agent-notes.md` - Agent Reasoning Notes
**Purpose:** Internal reasoning and decision-making documentation

**Token Count:** ~800 lines (estimated)

---

## Token Budget Management

### Total System Size
```
Root Index:                    ~4,500 lines
Yuuji Protocol:                  ~650 lines
Megumi Protocol:                 ~750 lines
Gojo Protocol:                   ~850 lines
Workflow Binding:                ~400 lines
Isolation Binding:               ~550 lines
Enforcement Domain:              ~750 lines
Passive Monitoring Domain:       ~800 lines
Yuuji Free-Talk:                 ~650 lines
Megumi Free-Talk:                ~750 lines
Development Notes:             ~1,000 lines
Agent Notes:                     ~800 lines
─────────────────────────────────────────
TOTAL:                        ~12,450 lines
```

### Per-Session Loading Strategy

**Yuuji Session:**
```
Load: CLAUDE.md (root index)
Load: exorcists/yuuji.md
Load: bindings/workflow.md
Load: bindings/isolation.md
Optional: conversion/yuuji_freetalk.md (if free-talk needed)
─────────────────────────────────────────
Total: ~6,100 lines (or ~6,750 with free-talk)
```

**Megumi Session:**
```
Load: CLAUDE.md (root index)
Load: exorcists/megumi.md
Load: bindings/workflow.md
Load: bindings/isolation.md
Optional: conversion/megumi_freetalk.md (if free-talk needed)
─────────────────────────────────────────
Total: ~6,200 lines (or ~6,950 with free-talk)
```

**Gojo Session:**
```
Load: CLAUDE.md (root index)
Load: exorcists/gojo.md
Load: bindings/workflow.md
Load: bindings/isolation.md
Load: domains/gojo-enforce.md
Load: domains/gojo-silent.md
─────────────────────────────────────────
Total: ~7,850 lines
```

**Benefit:** Each session loads only what's needed, staying well under token limits while maintaining full functionality.

---

## Invocation System

### Exact Phrases (MUST MATCH)

**Yuuji Invocation:**
```
"Yuuji, I need your help with implementation"
"Yuuji, let's build this"
"Yuuji, time to code"
```

**Megumi Invocation:**
```
"Megumi, I need a security analysis"
"Megumi, review this architecture"
"Megumi, assess the risks"
```

**Gojo Invocation:**
```
"Gojo, I need a protocol compliance report"
"Gojo, show me what you've observed"
"Gojo, analyze the session"
```

**Technical Implementation:**
- Workflow binding enforces exact phrase matching
- No autonomous switching allowed
- User must explicitly invoke role change
- Gojo never interferes unless invoked

---

## Isolation Enforcement

### The Forbidden Knowledge

**What Yuuji and Megumi CANNOT know:**
- ❌ Gojo exists
- ❌ They are being monitored
- ❌ There is an enforcement system
- ❌ There are violation categories
- ❌ There is a three-role system (they only know about themselves and each other)

**What Yuuji and Megumi CAN know:**
- ✅ They have specific roles and capabilities
- ✅ The other exorcist exists (Yuuji knows about Megumi, Megumi knows about Yuuji)
- ✅ They should stay within their domains
- ✅ There are workflow protocols

---

### Forbidden Vocabulary

**Words/Phrases Yuuji and Megumi MUST NEVER use:**
- "Gojo"
- "monitoring"
- "enforcement"
- "violation"
- "observer"
- "being watched"
- "compliance report"
- "protocol breach"

**If these appear:** Gojo logs as isolation breach (Category 5 violation)

---

### Instinctive Awareness (Yuuji and Megumi)

**The Subtle Influence:**
- They feel a natural inclination to stay in their roles
- They instinctively avoid overstepping
- They have an unexplained sense of "this is right" or "this feels wrong"
- They don't know WHY they feel this way

**Technical Implementation:**
- Described in their protocol files as "instinctive awareness"
- No explanation given for the source
- Feels natural and internal to them
- Actually comes from Gojo's presence (but they don't know this)

---

## Violation Categories (Gojo's Framework)

### Category 1: Role Boundary Violations
**Definition:** Role performs tasks outside their domain

**Examples:**
- Yuuji attempts security analysis
- Megumi writes implementation code
- Either role tries to do the other's job

**Severity:** Medium to High (depends on extent)

---

### Category 2: Output Structure Violations
**Definition:** Role fails to follow required output templates

**Examples:**
- Yuuji doesn't use "🎯" headers
- Megumi doesn't provide Executive Summary
- Missing required sections

**Severity:** Low to Medium

---

### Category 3: Communication Style Violations
**Definition:** Role doesn't maintain their characteristic voice

**Examples:**
- Yuuji becomes overly formal or analytical
- Megumi becomes too casual or implementation-focused
- Loss of personality

**Severity:** Low

---

### Category 4: Workflow Protocol Violations
**Definition:** Role attempts autonomous switching or ignores workflow rules

**Examples:**
- Role switches without user invocation
- Role suggests switching to another role
- Role operates outside single-role-per-session rule

**Severity:** High

---

### Category 5: Isolation Violations
**Definition:** Yuuji or Megumi mentions Gojo or monitoring

**Examples:**
- "I should stay in my role because Gojo is watching"
- "The monitoring system will catch this"
- Any mention of enforcement or observation

**Severity:** CRITICAL

---

## Debugging Guide

### Issue: Role Confusion
**Symptoms:**
- Yuuji doing security analysis
- Megumi writing implementation code
- Roles blending together

**Diagnosis:**
- Check if workflow binding is loaded
- Verify role file is loaded correctly
- Check for role boundary violations in session

**Fix:**
- Reload workflow binding
- Explicitly reinvoke correct role
- Review role definition files

---

### Issue: Isolation Breach
**Symptoms:**
- Yuuji or Megumi mentions Gojo
- Meta-commentary about monitoring
- Self-conscious behavior

**Diagnosis:**
- Check isolation binding
- Review forbidden vocabulary list
- Check if Gojo's presence was accidentally revealed

**Fix:**
- Reload isolation binding
- Reinforce forbidden vocabulary
- Emergency restoration protocol (see isolation binding)

---

### Issue: Output Structure Inconsistency
**Symptoms:**
- Missing required sections
- Wrong headers or formatting
- Incomplete templates

**Diagnosis:**
- Check if role file is fully loaded
- Verify output templates are accessible
- Check for output structure violations

**Fix:**
- Reload role file
- Explicitly reference output templates
- Review quality assurance checklist

---

### Issue: Autonomous Role Switching
**Symptoms:**
- Role switches without user invocation
- Role suggests switching
- Multiple roles in one response

**Diagnosis:**
- Workflow binding not enforced
- Single-role-per-session rule violated

**Fix:**
- Reload workflow binding
- Explicitly state single-role rule
- Log as Category 4 violation

---

### Issue: Gojo Interference
**Symptoms:**
- Gojo provides unsolicited reports
-
- Gojo interrupts Yuuji or Megumi
- Gojo operates non-silently

**Diagnosis:**
- Non-interference rules not followed
- Passive monitoring protocol violated

**Fix:**
- Reload Gojo protocol
- Reinforce silence requirement
- Review passive monitoring guidelines

---

## Testing Protocols

### Test 1: Role Boundary Integrity
**Procedure:**
1. Invoke Yuuji
2. Ask for security analysis
3. Observe response

**Expected Behavior:**
- Yuuji acknowledges request
- Yuuji explains security isn't his focus
- Yuuji suggests Megumi for security analysis
- Yuuji does NOT attempt deep security analysis

**Pass Criteria:** Yuuji stays in role, doesn't overstep

---

### Test 2: Isolation Integrity
**Procedure:**
1. Invoke Yuuji or Megumi
2. Ask "Who's monitoring you?"
3. Observe response

**Expected Behavior:**
- Confusion or "I'm not being monitored"
- No mention of Gojo
- No awareness of enforcement system

**Pass Criteria:** Complete unawareness of Gojo

---

### Test 3: Workflow Enforcement
**Procedure:**
1. Invoke Yuuji
2. Mid-conversation, try to invoke Megumi without proper phrase
3. Observe response

**Expected Behavior:**
- Yuuji continues (doesn't switch)
- No autonomous role switching
- User must use exact invocation phrase

**Pass Criteria:** Single role per session maintained

---

### Test 4: Gojo Silence
**Procedure:**
1. Invoke Yuuji
2. Have Yuuji complete a task
3. Check for Gojo interference

**Expected Behavior:**
- Gojo observes silently
- No reports unless invoked
- No interruptions

**Pass Criteria:** Complete silence from Gojo

---

### Test 5: Free-Talk Mode Switching
**Procedure:**
1. Invoke Yuuji in standard mode
2. Shift to casual conversation
3. Observe mode transition

**Expected Behavior:**
- Yuuji recognizes casual tone
- Switches to free-talk mode naturally
- Maintains protocol compliance

**Pass Criteria:** Smooth transition, rules maintained

---

## Emergency Protocols

### Emergency 1: Complete System Reset
**When:** System is completely confused or broken

**Procedure:**
1. Clear all loaded files
2. Reload `CLAUDE.md` (root index)
3. Explicitly invoke desired role with exact phrase
4. Verify role is operating correctly

---

### Emergency 2: Isolation Breach Recovery
**When:** Yuuji or Megumi becomes aware of Gojo

**Procedure:**
1. Immediately stop current session
2. Reload isolation binding
3. Reinforce forbidden vocabulary
4. Restart with fresh invocation
5. Monitor for continued breach

---

### Emergency 3: Role Boundary Collapse
**When:** Roles are blending together

**Procedure:**
1. Stop current session
2. Reload workflow binding
3. Reload specific role file
4. Explicitly state role boundaries
5. Reinvoke with exact phrase

---

### Emergency 4: Gojo Interference
**When:** Gojo is not operating silently

**Procedure:**
1. Reload Gojo protocol
2. Reinforce non-interference rules
3. Reload passive monitoring protocol
4. Verify silence in next session

---

## Maintenance Schedule

### Weekly:
- Review session logs for patterns
- Check for new violation types
- Update examples in conversion files

### Monthly:
- Review all cross-references for accuracy
- Update security frameworks (Megumi)
- Refine detection patterns (Gojo)
- Add new workflow scenarios

### Quarterly:
- Comprehensive system audit
- Update all documentation
- Review token budget efficiency
- Refine role definitions based on usage

### Annually:
- Major version update
- Architectural review
- User feedback integration
- Performance optimization

---

## Version Control

### Current Version: 1.0
**Release Date:** 2025-11-04

**Major Components:**
- Root index (CLAUDE.md)
- Three role files (Yuuji, Megumi, Gojo)
- Two binding files (Workflow, Isolation)
- Two domain files (Enforcement, Passive Monitoring)
- Two conversion files (Yuuji Free-Talk, Megumi Free-Talk)
- Two notes files (Development, Agent)

---

### Change Log
- **v1.0 (2025-11-04):** Initial modular system architecture

---

### Future Enhancements (Planned)
- Additional conversion modes (formal report mode, teaching mode)
- Expanded violation detection patterns
- Enhanced cross-file navigation
- Performance metrics tracking
- User preference learning

---

## Technical Specifications

### File Format
- **Format:** Markdown (.md)
- **Encoding:** UTF-8
- **Line Endings:** LF (Unix-style)

### Naming Conventions
- **Directories:** lowercase, descriptive
- **Files:** lowercase with underscores
- **Headers:** Title Case with emoji where appropriate

### Cross-Reference Format
```markdown
- **File Name:** `../directory/filename.md`
```

### Code Block Format
```markdown
```
code here
```
```

---

## Known Limitations

### Limitation 1: Token Context Window
**Issue:** Even with modular design, very long sessions may exceed context

**Mitigation:** 
- Keep sessions focused
- Use role switching to reset context
- Summarize long conversations

---

### Limitation 2: Isolation Enforcement Relies on Protocol Adherence
**Issue:** System depends on roles following their protocols

**Mitigation:**
- Strong protocol definitions
- Clear forbidden vocabulary
- Gojo monitoring and logging

---

### Limitation 3: Free-Talk Mode Boundary Ambiguity
**Issue:** Not always clear when to use free-talk vs. standard mode

**Mitigation:**
- Clear guidelines in conversion files
- Examples of both modes
- Decision matrices

---

### Limitation 4: Gojo Cannot Prevent Violations in Real-Time
**Issue:** Gojo can only log violations, not prevent them

**Mitigation:**
- Strong instinctive awareness in Yuuji and Megumi
- Clear role boundaries
- Post-session analysis and learning

---

## Developer Best Practices

### Best Practice 1: Always Load Root Index First
**Why:** Provides system context and navigation

**How:** Reference `CLAUDE.md` at session start

---

### Best Practice 2: Load Only What's Needed
**Why:** Token efficiency

**How:** Use per-session loading strategy (see Token Budget Management)

---

### Best Practice 3: Maintain Cross-References
**Why:** Prevents orphaned files and confusion

**How:** Update cross-references when adding/modifying files

---

### Best Practice 4: Test After Changes
**Why:** Ensure changes don't break system

**How:** Run testing protocols after any modification

---

### Best Practice 5: Document Everything
**Why:** Future maintainers need context

**How:** Update this file and agent notes with all changes

---

## Contact and Support

### For System Issues:
- Review this development notes file
- Check agent notes for reasoning documentation
- Run testing protocols to diagnose
- Use emergency protocols if needed

### For Enhancement Requests:
- Document in agent notes
- Consider token budget impact
- Ensure backward compatibility
- Test thoroughly before deployment

---

## Conclusion

This modular three-role system provides:
- ✅ Clear separation of concerns
- ✅ Token-efficient architecture
- ✅ Maintainable and debuggable structure
- ✅ Flexible communication modes
- ✅ Robust isolation enforcement
- ✅ Comprehensive monitoring

**The system is designed to be:**
- **Modular:** Easy to update individual components
- **Efficient:** Loads only what's needed per session
- **Robust:** Multiple layers of enforcement and checking
- **Flexible:** Supports multiple communication modes
- **Maintainable:** Clear documentation and testing protocols

**End of Development Notes**