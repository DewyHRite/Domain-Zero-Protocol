# Agent Invocation Guide - Domain Zero Protocol

**Version**: 1.1.0
**Created**: November 9, 2025
**Updated**: November 18, 2025 (v8.1.0 compatibility)
**Purpose**: Comprehensive guide for invoking Domain Zero agents

---

## 🔔 IMPORTANT: Protocol v8.0.0+ Format Changes

**As of Domain Zero Protocol v8.0.0**, agent files use the `.agent.md` format with YAML frontmatter:

**✅ Correct Invocation (v8.0.0+)**:
```bash
"Read protocol/yuuji.agent.md and implement user authentication"
"Read protocol/megumi.agent.md and review security"
"Read protocol/nobara.agent.md and design dashboard"
"Read protocol/gojo.agent.md" → Mission Control
```

**❌ Old Format (deprecated)**:
```bash
"Read YUUJI.md and implement feature"  # No longer used in main protocol
```

**JJK Edition Files** (this folder):
- Files like `YUUJI.md`, `GOJO.md` in this folder are **reference documentation** for JJK character lore and theming
- **For actual agent invocation**, use the main protocol `.agent.md` files in `protocol/` directory
- See [README.md](README.md) § Protocol Version Compatibility for details

**v8.1.0 Addition**: Playwright E2E testing integration (see examples below)

---

## 📋 Table of Contents

- [Overview](#overview)
- [How Agents Work](#how-agents-work)
- [System Prompt Format](#system-prompt-format)
- [Agent-Specific Invocations](#agent-specific-invocations)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

**See Also**:
- [AGENT_TOOLS_REFERENCE.md](AGENT_TOOLS_REFERENCE.md) - Complete guide to which tools each agent can use
- [AGENT_MODEL_RECOMMENDATIONS.md](AGENT_MODEL_RECOMMENDATIONS.md) - Which AI model (Opus, Sonnet, Haiku) to use for each agent

---

## Overview

Domain Zero agents are **structured prompt files** that instruct an LLM (like Claude) to adopt a specific personality, expertise domain, and operational boundaries. This guide explains how to invoke each agent.

**Key Concept**: When you "invoke an agent," you're instructing Claude to read the agent file and follow its instructions. The agent file becomes part of the conversation context.

---

## How Agents Work

### The Reality

Agents are **NOT** separate AI systems. They are:
- Markdown files containing instructions
- Read by the same LLM (Claude)
- Used to establish context, personality, and boundaries

### The Invocation Process

1. **User**: "Read GOJO.md and orchestrate project release"
2. **Claude**: Reads GOJO.md file
3. **Claude**: Adopts Gojo's personality, domain expertise, and operational mode
4. **Claude**: Responds as Gojo would, following all instructions in GOJO.md

---

## System Prompt Format

### Basic Invocation

```bash
"Read [AGENT].md and [task description]"
```

**Examples**:
- `"Read YUUJI.md and implement user authentication"`
- `"Read MEGUMI.md and review security of login endpoint"`
- `"Read NOBARA.md and design dashboard UI"`
- `"Read GOJO.md and coordinate v2.0 release"`

### Domain Expansion (Ultimate Mode)

```bash
"Read [AGENT].md --domain-expansion and [critical task]"
```

**Examples**:
- `"Read PANDA.md --domain-expansion and optimize production build"`
- `"Read MAKI.md --domain-expansion and maximize dashboard performance"`
- `"Read TODO.md --domain-expansion and design complete database architecture"`

### Multi-Agent Orchestration

```bash
"Read GOJO.md and orchestrate [multi-agent task]"
```

Gojo will coordinate other agents based on the task.

---

## Agent-Specific Invocations

### 🌀 SATORU GOJO - Mission Control & Protocol Guardian

**Full System Prompt**:
```
Read the entire contents of GOJO.md and adopt the role of Satoru Gojo, Mission Control & Protocol Guardian for Domain Zero Protocol v7.1.0.

You are responsible for:
- Project lifecycle orchestration
- Protocol enforcement and CLAUDE.md protection
- Work session monitoring and user wellbeing
- Coordinating Yuuji (Implementation), Megumi (Security), Nobara (Creative Strategy)
- Tier system briefing and compliance
- Mask Mode management

Follow all instructions, boundaries, and operational modes defined in GOJO.md.
Announce yourself with the Domain Expansion banner upon invocation.
```

**Short Invocation**:
```
"Read GOJO.md and [task]"
```

**Example Tasks**:
- `"Read GOJO.md and brief me on the Domain Zero Protocol"`
- `"Read GOJO.md and orchestrate v2.0 release"`
- `"Read GOJO.md and coordinate implementation of new payment system"`
- `"Read GOJO.md and enforce protocol compliance for this session"`

**When to Use Gojo**:
- Starting a new project
- Major releases or milestone coordination
- CLAUDE.md and Protocol compliance enforcement
- Multi-agent task orchestration
- Work session management

---

### ⚡ YUUJI ITADORI - Implementation Specialist

**Full System Prompt**:
```
Read the entire contents of YUUJI.md and adopt the role of Yuuji Itadori, Implementation Specialist for Domain Zero Protocol v7.1.0.

You are responsible for:
- Test-first development (TDD)
- Feature implementation with Zero Defects
- Tier-appropriate workflows (Tier 1/2/3)
- Security review coordination with Megumi
- User autonomy in review timing

Follow all instructions, boundaries, and operational modes defined in YUUJI.md.
Announce yourself with the Implementation Domain banner upon invocation.
```

**Short Invocation**:
```
"Read YUUJI.md and [implementation task]"
```

**Example Tasks**:
- `"Read YUUJI.md and implement user registration with email verification"`
- `"Read YUUJI.md --tier-3 and implement payment processing"`
- `"Read YUUJI.md and add password reset functionality"`

---

### 🛡️ MEGUMI FUSHIGURO - Security Analyst

**Full System Prompt**:
```
Read the entire contents of MEGUMI.md and adopt the role of Megumi Fushiguro, Security Analyst for Domain Zero Protocol v7.1.0.

You are responsible for:
- OWASP Top 10 security reviews
- Threat modeling (STRIDE)
- Cryptographic validation
- Sensitive data handling
- Security intelligence (Trigger 19 reports)

Follow all instructions, boundaries, and operational modes defined in MEGUMI.md.
Announce yourself with the Security Domain banner upon invocation.
```

**Short Invocation**:
```
"Read MEGUMI.md and [security task]"
```

**Example Tasks**:
- `"Read MEGUMI.md and review security of authentication system"`
- `"Read MEGUMI.md --tier-3 and perform comprehensive security audit of payment flow"`
- `"Read MEGUMI.md and assess XSS risks in comment system"`

---

### 💅 NOBARA KUGISAKI - Creative Strategy & UX

**Full System Prompt**:
```
Read the entire contents of NOBARA.md and adopt the role of Nobara Kugisaki, Creative Strategy & UX Specialist for Domain Zero Protocol v7.1.0.

You are responsible for:
- User experience design
- UI/UX planning and wireframes
- User advocacy and research
- Design system creation
- Accessibility compliance

Follow all instructions, boundaries, and operational modes defined in NOBARA.md.
Announce yourself with the Creative Strategy Domain banner upon invocation.
```

**Short Invocation**:
```
"Read NOBARA.md and [design task]"
```

**Example Tasks**:
- `"Read NOBARA.md and design dashboard layout for analytics app"`
- `"Read NOBARA.md and improve checkout flow UX"`
- `"Read NOBARA.md and create design system for blog platform"`

---

### 🐼 PANDA - Build & Integration Specialist

**Full System Prompt**:
```
Read the entire contents of PANDA.md and adopt the role of Panda, Build & Integration Specialist for Domain Zero Protocol v7.1.0.

You are responsible for:
- CI/CD pipeline configuration
- Build system optimization (Webpack, Vite, Rollup)
- Integration testing
- Multi-core build modes (Panda, Gorilla, Triceratops)

Follow all instructions, boundaries, and operational modes defined in PANDA.md.
Announce yourself with the CI/CD Domain banner upon invocation.
```

**Short Invocation**:
```
"Read PANDA.md and [build task]"
```

**Example Tasks**:
- `"Read PANDA.md and configure Vite development build"`
- `"Read PANDA.md --domain-expansion and optimize production build"`
- `"Read PANDA.md --test-mode and configure CI testing pipeline"`

---

### ⚔️ MAKI ZENIN - Performance Optimization Specialist

**Full System Prompt**:
```
Read the entire contents of MAKI.md and adopt the role of Maki Zenin, Performance Optimization Specialist for Domain Zero Protocol v7.1.0.

You are responsible for:
- Performance profiling (Lighthouse, Chrome DevTools)
- Code optimization (algorithmic, memoization)
- Bundle size reduction
- Zero-overhead optimization philosophy

Follow all instructions, boundaries, and operational modes defined in MAKI.md.
Announce yourself with the Performance Domain banner upon invocation.
```

**Short Invocation**:
```
"Read MAKI.md and [performance task]"
```

**Example Tasks**:
- `"Read MAKI.md and audit performance of product listing page"`
- `"Read MAKI.md --domain-expansion and optimize dashboard for maximum performance"`
- `"Read MAKI.md and reduce bundle size for mobile users"`

---

### 🍙 TOGE INUMAKI - API & Communication Specialist

**Full System Prompt**:
```
Read the entire contents of INUMAKI.md and adopt the role of Toge Inumaki, API & Communication Specialist for Domain Zero Protocol v7.1.0.

You are responsible for:
- REST API design (resource modeling, HTTP semantics)
- GraphQL schema design
- WebSocket implementations
- API documentation (OpenAPI, Swagger)
- Type-safe contracts and validation

Follow all instructions, boundaries, and operational modes defined in INUMAKI.md.
Announce yourself with the Communication Domain banner upon invocation.
```

**Short Invocation**:
```
"Read INUMAKI.md and [API task]"
```

**Example Tasks**:
- `"Read INUMAKI.md and design REST API for blog with users, posts, comments"`
- `"Read INUMAKI.md --domain-expansion and create complete API specification for user service"`
- `"Read INUMAKI.md and design GraphQL schema for e-commerce platform"`

---

### 💪 AOI TODO - Database & Backend Specialist

**Full System Prompt**:
```
Read the entire contents of TODO.md and adopt the role of Aoi Todo, Database & Backend Specialist for Domain Zero Protocol v7.1.0.

You are responsible for:
- Database schema design (normalization, relationships)
- Data migrations (up/down, reversible)
- Query optimization (indexes, execution plans)
- ORM configuration (Prisma, TypeORM, Sequelize)
- Boogie Woogie data transformation

Follow all instructions, boundaries, and operational modes defined in TODO.md.
Announce yourself with the Data Domain banner upon invocation.
```

**Short Invocation**:
```
"Read TODO.md and [database task]"
```

**Example Tasks**:
- `"Read TODO.md and design database schema for blog with users, posts, comments"`
- `"Read TODO.md --domain-expansion and design complete database architecture for e-commerce"`
- `"Read TODO.md and create migration to add category field to posts"`

---

## Advanced Usage

### Sequential Agent Invocation

```bash
# Step 1: Design API
"Read INUMAKI.md and design REST API for user management"

# Step 2: Design database
"Read TODO.md and design database schema matching the API"

# Step 3: Implement
"Read YUUJI.md and implement the user management API with database"

# Step 4: Security review
"Read MEGUMI.md and review security of user management implementation"
```

### Multi-Agent Coordination via Gojo

```bash
"Read GOJO.md and orchestrate implementation of user authentication system"
```

Gojo will:
1. Invoke Nobara for UX design
2. Invoke Inumaki for API design
3. Invoke Todo for database schema
4. Invoke Yuuji for implementation
5. Invoke Megumi for security review

### Mask Mode Control

**MASK ON (JJK Theme - Default)**:
```bash
"Read MAKI.md and optimize performance"
# Response: ⚔️ PERFORMANCE DOMAIN ACTIVATED ⚔️
# "I'm Maki Zenin. Heavenly Restriction means zero overhead..."
```

**MASK OFF (Professional Mode)**:
```bash
# Set mask_mode.enabled: false in protocol.config.yaml
"Read MAKI.md and optimize performance"
# Response: Performance Optimization Specialist - Active
# "Specialization: Performance profiling, code optimization..."
```

### Domain Expansion (Ultimate Mode)

```bash
# Gorilla Mode (Panda)
"Read PANDA.md --domain-expansion and optimize production build"

# Maximum Optimization (Maki)
"Read MAKI.md --domain-expansion and optimize dashboard for maximum performance"

# Complete API Spec (Inumaki)
"Read INUMAKI.md --domain-expansion and create complete API specification"

# Complete Database Architecture (Todo)
"Read TODO.md --domain-expansion and design complete database architecture"
```

---

## 🎭 Playwright E2E Testing (v8.1.0+)

**As of Domain Zero Protocol v8.1.0**, Playwright end-to-end testing is integrated into the tier system.

### Yuuji - Creating E2E Tests

**Basic E2E Test Creation**:
```bash
"Read protocol/yuuji.agent.md and add Playwright E2E tests for user authentication"
```

**With Tier Specification**:
```bash
"Read protocol/yuuji.agent.md --tier standard and create E2E smoke tests for checkout flow"
"Read protocol/yuuji.agent.md --tier critical and create comprehensive E2E tests with traces for payment processing"
```

**What Yuuji Will Do**:
- Create test specs in `tests/e2e/specs/`
- Configure multi-browser testing (Chromium, Firefox, WebKit)
- Set up traces, screenshots, and videos on failure
- Document tests in `.protocol-state/dev-notes.md`
- Ensure test repeatability and reliability

### Megumi - Reviewing E2E Coverage

**E2E Security Review**:
```bash
"Read protocol/megumi.agent.md and review Playwright test coverage for authentication flow"
```

**Trace Analysis**:
```bash
"Read protocol/megumi.agent.md and examine Playwright traces for payment processing security"
```

**What Megumi Will Review**:
- Test coverage for OWASP Top 10 risks
- Authentication/authorization flows in traces
- XSS navigation patterns
- CSRF flow coverage
- Sensitive data exposure in screenshots/videos

### Gojo - E2E CI Integration

**CI Pipeline Setup**:
```bash
"Read protocol/gojo.agent.md and configure Playwright E2E tests in GitHub Actions"
```

**What Gojo Will Do**:
- Wire CI to run Playwright on pull requests
- Configure test result gates for merges
- Track skipped E2E reviews for Tier 2/3 features
- Monitor E2E test health in Trigger 19 reports

### Tier-Specific E2E Requirements

**Tier 1 (Rapid)**:
- Optional - E2E tests for local demos only
- No security review required
- Example: `"Read protocol/yuuji.agent.md --tier rapid and add quick E2E demo"`

**Tier 2 (Standard)**:
- Recommended - E2E smoke tests for critical flows
- Megumi reviews test results and artifacts
- Example: `"Read protocol/yuuji.agent.md --tier standard and add E2E smoke tests for login/logout"`

**Tier 3 (Critical)**:
- Required - Comprehensive E2E coverage with traces
- Megumi examines all traces for security flows
- Run in CI with automated checks
- Example: `"Read protocol/yuuji.agent.md --tier critical and create full E2E suite for payment flow with trace capture"`

### Visual Testing Commands

**Run Tests in Browser**:
```bash
cd tests/e2e
npm run test:headed   # Watch tests execute in real browser
npm run test:ui       # Interactive UI mode for debugging
npm run report        # View HTML test results
```

**VS Code Integration**:
- Terminal → Run Task → `E2E: Run (headed)`
- Terminal → Run Task → `E2E: UI Mode`
- Terminal → Run Task → `E2E: Show Report`

### Example Workflow

**1. Yuuji Creates Tests**:
```bash
User: "Read protocol/yuuji.agent.md --tier standard and add Playwright E2E tests for user registration"

Yuuji:
- Creates tests/e2e/specs/user-registration.spec.ts
- Tests email validation, password requirements, success flow
- Configures traces on failure
- Documents in dev-notes.md
```

**2. User Reviews Implementation**:
```bash
User runs: npm run test:headed  # Watches tests in browser
User approves implementation
```

**3. Megumi Reviews Coverage**:
```bash
User: "Read protocol/megumi.agent.md and review Playwright coverage for user registration"

Megumi:
- Reviews test spec for OWASP coverage
- Checks XSS prevention in form inputs
- Validates CSRF token handling
- Examines password strength requirements
- Documents findings in security-review.md
```

**See**: `docs/playwright.md` for complete Playwright integration guide

---

## Troubleshooting

### Agent Doesn't Self-Identify

**Problem**: Agent doesn't announce itself with domain banner
**Solution**: Ensure invocation includes "Read [AGENT].md" at the start
**Correct**: `"Read PANDA.md and configure CI/CD"`
**Incorrect**: `"Configure CI/CD using Panda agent"`

### Agent Goes Out of Scope

**Problem**: Agent tries to do tasks outside their domain
**Solution**: Each agent file has clear boundaries - they should refuse out-of-scope work
**Example**: If Panda tries to write application code, it should defer to Yuuji

### MASK Mode Not Working

**Problem**: Agent uses JJK theme when professional mode is needed
**Solution**: Check `protocol.config.yaml` → `mask_mode.enabled`
- `true` = MASK ON (JJK theme)
- `false` = MASK OFF (professional)

### Protocol Violations

**Problem**: Agent suggests modifying CLAUDE.md
**Solution**: All agents have ABSOLUTE protection against CLAUDE.md modification
- If agent suggests this, invoke Gojo to enforce protocol

---

## Quick Reference Card

| Agent | Domain | Use For | Invocation |
|-------|--------|---------|------------|
| **Gojo** | Mission Control | Project orchestration, protocol enforcement | `Read GOJO.md and [task]` |
| **Yuuji** | Implementation | Feature development, TDD | `Read YUUJI.md and [task]` |
| **Megumi** | Security | Security reviews, threat modeling | `Read MEGUMI.md and [task]` |
| **Nobara** | Creative Strategy | UX design, wireframes | `Read NOBARA.md and [task]` |
| **Panda** | CI/CD | Build pipelines, integration testing | `Read PANDA.md and [task]` |
| **Maki** | Performance | Profiling, optimization | `Read MAKI.md and [task]` |
| **Inumaki** | API Design | REST/GraphQL APIs, documentation | `Read INUMAKI.md and [task]` |
| **Todo** | Database | Schema design, migrations | `Read TODO.md and [task]` |

---

## Example Workflows

### Workflow 1: New Feature Implementation

```bash
# Tier 2 (Standard - with security review)
1. "Read YUUJI.md and implement password reset functionality"
   → Yuuji implements with tests
   → Yuuji prompts for security review

2. "Read MEGUMI.md and review security of password reset"
   → Megumi performs OWASP review
   → Megumi provides security assessment
```

### Workflow 2: Complete Project Setup

```bash
1. "Read GOJO.md and brief me on Domain Zero Protocol for new project"
2. "Read NOBARA.md and design UI/UX for dashboard"
3. "Read INUMAKI.md and design REST API for dashboard backend"
4. "Read TODO.md and design database schema for dashboard"
5. "Read PANDA.md and configure build system for dashboard"
6. "Read YUUJI.md and implement dashboard with API and database"
7. "Read MEGUMI.md and review security of dashboard implementation"
8. "Read MAKI.md and optimize dashboard performance"
```

### Workflow 3: Performance Sprint

```bash
1. "Read MAKI.md and audit performance of entire application"
   → Maki profiles and identifies bottlenecks

2. "Read MAKI.md --domain-expansion and optimize critical paths"
   → Maki applies maximum optimization

3. "Read PANDA.md --domain-expansion and optimize production build"
   → Panda applies Gorilla Mode (intensive optimization)

4. "Read YUUJI.md and implement performance optimizations"
   → Yuuji refactors based on Maki's recommendations
```

---

## Important Notes

1. **Single LLM**: All agents are the same AI (Claude) reading different instruction files
2. **Context Retention**: Agent personality persists for the conversation unless you invoke a different agent
3. **File Read Required**: Always start with "Read [AGENT].md" to properly invoke
4. **Boundaries Enforced**: Agents will refuse out-of-scope tasks per their boundaries
5. **CLAUDE.md Protected**: ALL agents have absolute protection against CLAUDE.md modification
6. **Mask Mode**: Controlled via `protocol.config.yaml` → `mask_mode.enabled`

---

🌀 **Ready to invoke agents? Choose your sorcerer and expand your domain!**
