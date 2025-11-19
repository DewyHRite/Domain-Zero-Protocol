# Agent Model Recommendations - Domain Zero Protocol

**Version**: 1.0.0
**Created**: November 9, 2025
**Purpose**: Guide for selecting the optimal AI model for each agent based on task complexity

---

## 📋 Table of Contents

- [Overview](#overview)
- [Available Models](#available-models)
- [Model Selection Matrix](#model-selection-matrix)
- [Agent-Specific Recommendations](#agent-specific-recommendations)
- [Task-Based Model Selection](#task-based-model-selection)
- [Cost vs Performance Trade-offs](#cost-vs-performance-trade-offs)
- [Best Practices](#best-practices)

---

## Overview

Different Domain Zero agents benefit from different AI models based on their domain complexity, criticality, and performance requirements. This guide helps you choose the optimal model for each agent and task.

**Key Principle**: Match model capability to task complexity. Don't use Opus for simple tasks, don't use Haiku for critical security reviews.

---

## Available Models

### Model Comparison

| Model | Capability | Speed | Cost | Best For |
|-------|-----------|-------|------|----------|
| **Opus** | Highest | Slowest | Highest | Complex reasoning, critical tasks, thorough analysis |
| **Sonnet** | High | Balanced | Medium | Most development tasks, balanced speed/quality |
| **Haiku** | Good | Fastest | Lowest | Simple tasks, quick operations, straightforward work |

### Model Characteristics

**Claude Opus** (claude-opus-4-5):
- **Strengths**: Deep reasoning, complex problem-solving, thorough analysis
- **Use For**: Security reviews, architecture design, complex orchestration
- **Avoid For**: Simple file edits, basic CRUD operations, straightforward configs

**Claude Sonnet** (claude-sonnet-4-5):
- **Strengths**: Balanced capability and speed, excellent code quality
- **Use For**: Feature implementation, API design, performance optimization
- **Default**: Most agents should default to Sonnet

**Claude Haiku** (claude-haiku-4):
- **Strengths**: Fast responses, cost-effective, good for structured tasks
- **Use For**: Build configs, simple scripts, straightforward documentation
- **Limitations**: Not suitable for complex reasoning or critical security work

---

## Model Selection Matrix

| Agent | Default Model | Simple Tasks | Complex Tasks | Critical Tasks |
|-------|--------------|--------------|---------------|----------------|
| **Gojo** | Opus | Sonnet | Opus | Opus |
| **Yuuji** | Sonnet | Haiku | Sonnet | Opus |
| **Megumi** | Opus | Sonnet | Opus | Opus |
| **Nobara** | Sonnet | Haiku | Sonnet | Opus |
| **Panda** | Sonnet | Haiku | Sonnet | Sonnet |
| **Maki** | Sonnet | Haiku | Sonnet | Opus |
| **Inumaki** | Sonnet | Haiku | Sonnet | Opus |
| **Todo** | Sonnet | Haiku | Sonnet | Opus |

**Legend**:
- **Default Model**: Recommended for most tasks in this domain
- **Simple Tasks**: Basic, straightforward operations
- **Complex Tasks**: Multi-step reasoning, non-trivial implementations
- **Critical Tasks**: Security-sensitive, production deployments, irreversible operations

---

## Agent-Specific Recommendations

### 🌀 SATORU GOJO - Mission Control & Protocol Guardian

**Default Model**: **Opus**

**Why Opus**:
- Complex orchestration across multiple agents
- Protocol enforcement requires deep understanding
- Critical decision-making (CLAUDE.md modifications)
- Work session monitoring needs nuanced judgment

**When to Use Sonnet**:
- Simple status checks (`git status`, reading dev-notes.md)
- Routine protocol verification
- Basic task coordination

**When to Use Haiku**:
- Never recommended (Gojo's role is too critical)

**Example Invocations**:
```bash
# Default (Opus)
"Read GOJO.md and orchestrate v2.0 release"

# Explicit model selection
"Read GOJO.md [model:opus] and coordinate multi-agent security review"

# Sonnet for simple check
"Read GOJO.md [model:sonnet] and check project status"
```

---

### ⚡ YUUJI ITADORI - Implementation Specialist

**Default Model**: **Sonnet**

**Why Sonnet**:
- Balanced speed and code quality
- Most features are standard complexity
- Fast iteration for TDD workflow
- Good enough for 90% of implementations

**When to Use Haiku**:
- Simple CRUD operations
- Boilerplate code generation
- Basic file structure setup
- Straightforward refactoring

**When to Use Opus**:
- Complex algorithms (e.g., graph algorithms, data processing pipelines)
- Critical business logic (payment processing, auth systems)
- Multi-layered architectures
- Performance-critical code

**Example Invocations**:
```bash
# Default (Sonnet)
"Read YUUJI.md and implement user registration"

# Haiku for simple task
"Read YUUJI.md [model:haiku] and create basic Express route for /health endpoint"

# Opus for complex feature
"Read YUUJI.md [model:opus] --tier-3 and implement payment processing with Stripe"
```

---

### 🛡️ MEGUMI FUSHIGURO - Security Analyst

**Default Model**: **Opus**

**Why Opus**:
- Security reviews cannot miss vulnerabilities
- OWASP Top 10 requires thorough analysis
- Threat modeling needs deep reasoning
- False negatives are unacceptable

**When to Use Sonnet**:
- Initial quick scans (first pass)
- Code pattern searches
- Basic security checks (linting, dependency audit)

**When to Use Haiku**:
- Never recommended (security is too critical)

**Example Invocations**:
```bash
# Default (Opus) - ALWAYS for security reviews
"Read MEGUMI.md and review security of authentication system"

# Sonnet for initial scan only
"Read MEGUMI.md [model:sonnet] and run quick security scan for obvious issues"

# Opus for Tier 3 (mandatory)
"Read MEGUMI.md [model:opus] --tier-3 and perform comprehensive security audit"
```

**Critical**: Tier 2 and Tier 3 security reviews MUST use Opus. This is non-negotiable.

---

### 💅 NOBARA KUGISAKI - Creative Strategy & UX

**Default Model**: **Sonnet**

**Why Sonnet**:
- Creative work benefits from good reasoning
- UX design doesn't require maximum capability
- Fast iteration for design exploration
- Balance between quality and speed

**When to Use Haiku**:
- Simple wireframe descriptions
- Basic component specifications
- Straightforward design documentation

**When to Use Opus**:
- Complex user research synthesis
- Multi-stakeholder design strategy
- Accessibility compliance (WCAG AA/AAA)
- Design system architecture

**Example Invocations**:
```bash
# Default (Sonnet)
"Read NOBARA.md and design dashboard UI for analytics"

# Haiku for simple task
"Read NOBARA.md [model:haiku] and create component spec for basic button"

# Opus for complex UX
"Read NOBARA.md [model:opus] and design complete onboarding flow with A/B testing strategy"
```

---

### 🐼 PANDA - Build & Integration Specialist

**Default Model**: **Sonnet**

**Why Sonnet**:
- Build configs often need some reasoning
- CI/CD pipelines can be complex
- Balance between speed and correctness

**When to Use Haiku**:
- Simple build configurations (basic Vite/Webpack configs)
- Straightforward Dockerfile creation
- Basic CI/CD pipeline setup

**When to Use Opus**:
- Complex multi-stage builds
- Advanced optimization strategies
- Distributed build systems

**Example Invocations**:
```bash
# Default (Sonnet)
"Read PANDA.md and configure GitHub Actions CI/CD pipeline"

# Haiku for simple config
"Read PANDA.md [model:haiku] and create basic Dockerfile for Node app"

# Sonnet for production optimization
"Read PANDA.md [model:sonnet] --domain-expansion and optimize production build"
```

---

### ⚔️ MAKI ZENIN - Performance Optimization Specialist

**Default Model**: **Sonnet**

**Why Sonnet**:
- Performance analysis needs good reasoning
- Most optimizations are standard patterns
- Fast profiling and iteration

**When to Use Haiku**:
- Simple performance checks
- Basic Lighthouse audits
- Straightforward optimizations (image compression)

**When to Use Opus**:
- Deep algorithmic optimization (O(n²) → O(n log n))
- Complex rendering optimizations
- Memory leak analysis and resolution
- Critical performance bottlenecks

**Example Invocations**:
```bash
# Default (Sonnet)
"Read MAKI.md and optimize dashboard performance"

# Haiku for basic audit
"Read MAKI.md [model:haiku] and run Lighthouse audit"

# Opus for deep optimization
"Read MAKI.md [model:opus] --domain-expansion and eliminate all performance bottlenecks"
```

---

### 🍙 TOGE INUMAKI - API & Communication Specialist

**Default Model**: **Sonnet**

**Why Sonnet**:
- API design is structured but needs reasoning
- Type safety and validation require care
- Balance between speed and correctness

**When to Use Haiku**:
- Simple REST CRUD endpoints
- Basic OpenAPI spec generation
- Straightforward validation schemas

**When to Use Opus**:
- Complex distributed system APIs
- GraphQL schema design for large systems
- API versioning strategies
- WebSocket real-time architectures

**Example Invocations**:
```bash
# Default (Sonnet)
"Read INUMAKI.md and design REST API for blog system"

# Haiku for simple endpoint
"Read INUMAKI.md [model:haiku] and create basic GET /users/:id endpoint spec"

# Opus for complex API
"Read INUMAKI.md [model:opus] --domain-expansion and design complete microservices API architecture"
```

---

### 💪 AOI TODO - Database & Backend Specialist

**Default Model**: **Sonnet**

**Why Sonnet**:
- Schema design needs careful reasoning
- Migrations require correctness
- Query optimization needs analysis

**When to Use Haiku**:
- Simple table additions
- Basic CRUD model definitions
- Straightforward seed files

**When to Use Opus**:
- Complex data migrations (large-scale refactoring)
- Multi-tenant database architecture
- Advanced query optimization (complex joins, indexing strategy)
- Data integrity in distributed systems

**Example Invocations**:
```bash
# Default (Sonnet)
"Read TODO.md and design schema for e-commerce platform"

# Haiku for simple change
"Read TODO.md [model:haiku] and add 'status' column to posts table"

# Opus for complex migration
"Read TODO.md [model:opus] --domain-expansion and design multi-tenant database architecture with row-level security"
```

---

## Task-Based Model Selection

### By Task Complexity

**Use Haiku**:
- ✅ Simple file reads/edits
- ✅ Basic configuration files
- ✅ Boilerplate code generation
- ✅ Straightforward documentation
- ✅ Simple bash commands
- ✅ Basic CRUD operations

**Use Sonnet** (Default):
- ✅ Most feature implementations
- ✅ Standard API design
- ✅ Typical database schemas
- ✅ Performance optimizations
- ✅ Build pipeline configurations
- ✅ UX/UI design work

**Use Opus**:
- ✅ Security reviews (Tier 2/3)
- ✅ Complex algorithms
- ✅ Multi-agent orchestration
- ✅ Critical production deployments
- ✅ Advanced architecture design
- ✅ Complex data migrations

### By Tier System

**Tier 1 (Rapid Prototyping)**:
- **Model**: Haiku or Sonnet
- **Rationale**: Speed over perfection, no tests or security review

**Tier 2 (Standard - Production)** [DEFAULT]:
- **Model**: Sonnet
- **Security Review**: Opus (mandatory for Megumi)
- **Rationale**: Balance speed and quality, production-ready

**Tier 3 (Critical - Auth/Payments/PII)**:
- **Model**: Opus (for both implementation and security review)
- **Rationale**: No compromises on critical systems

---

## Cost vs Performance Trade-offs

### Cost Comparison (Approximate)

Assuming similar token usage:
- **Haiku**: ~1x cost (baseline)
- **Sonnet**: ~3-5x cost
- **Opus**: ~15-20x cost

### ROI by Agent

**High ROI for Opus**:
- ✅ **Gojo**: Critical orchestration, protocol guardian
- ✅ **Megumi**: Security vulnerabilities cost more than model usage
- ✅ **Yuuji** (Tier 3 only): Critical features justify cost

**Good ROI for Sonnet**:
- ✅ **Yuuji**: Most features (Tier 2)
- ✅ **Nobara**: Creative work
- ✅ **Maki**: Performance optimization
- ✅ **Inumaki**: API design
- ✅ **Todo**: Database design
- ✅ **Panda**: Build configs

**Good ROI for Haiku**:
- ✅ Simple, repetitive tasks across all agents
- ✅ Quick checks and validations
- ✅ Boilerplate generation

### Cost Optimization Strategies

**1. Start Haiku, Escalate if Needed**:
```bash
# Try Haiku first for simple task
"Read YUUJI.md [model:haiku] and add logging to function"

# If Haiku struggles, escalate to Sonnet
"Read YUUJI.md [model:sonnet] and add comprehensive logging with structured output"
```

**2. Use Sonnet for Exploration, Opus for Execution**:
```bash
# Sonnet explores options
"Read NOBARA.md [model:sonnet] and explore UX approaches for checkout flow"

# Opus finalizes complex design
"Read NOBARA.md [model:opus] and finalize comprehensive checkout UX with A/B testing"
```

**3. Haiku for Batch Operations**:
```bash
# Haiku for 50 similar files
"Read YUUJI.md [model:haiku] and add TypeScript types to all 50 utility functions"
```

---

## Best Practices

### 1. Default to Recommended Models

**Start with agent's default model**:
- Gojo → Opus
- Megumi → Opus
- Everyone else → Sonnet

### 2. Escalate Based on Complexity

**Use this decision tree**:
```
Is task simple and straightforward?
  Yes → Try Haiku
  No → Is task critical or complex?
    Yes → Use Opus
    No → Use Sonnet (default)
```

### 3. Never Downgrade Critical Tasks

**NEVER use Haiku for**:
- ❌ Security reviews
- ❌ Production deployments
- ❌ Data migrations (except trivial)
- ❌ Payment processing
- ❌ Authentication systems

### 4. Explicit Model Selection

**When in doubt, specify explicitly**:
```bash
# Explicit (good practice)
"Read MEGUMI.md [model:opus] and review authentication security"

# Implicit (relies on default)
"Read MEGUMI.md and review authentication security"
```

### 5. Document Model Choice for Critical Work

**In dev-notes.md or commit messages**:
```markdown
## Security Review (2025-11-09)
- Agent: Megumi Fushiguro
- Model: claude-opus-4-5 (required for Tier 2 security review)
- Scope: User authentication system
- Result: PASS (no critical vulnerabilities found)
```

### 6. Monitor Model Performance

**Track which models work best for your workflows**:
- Did Haiku successfully handle this task type?
- Did Sonnet miss something Opus would catch?
- Was Opus overkill for this simple task?

### 7. Budget Allocation

**Allocate model budget by agent priority**:
1. **Always Opus**: Megumi (security), Gojo (orchestration)
2. **Mostly Sonnet**: Yuuji, Nobara, Maki, Inumaki, Todo, Panda
3. **Haiku when possible**: Simple tasks across all agents

---

## Model Selection Quick Reference

| Task Type | Recommended Model | Agents |
|-----------|------------------|--------|
| **Security Review** | Opus (mandatory) | Megumi |
| **Orchestration** | Opus | Gojo |
| **Feature Implementation** | Sonnet | Yuuji |
| **API Design** | Sonnet | Inumaki |
| **Database Design** | Sonnet | Todo |
| **Performance Optimization** | Sonnet | Maki |
| **UX Design** | Sonnet | Nobara |
| **Build Configuration** | Sonnet or Haiku | Panda |
| **Simple CRUD** | Haiku | Yuuji |
| **Boilerplate** | Haiku | Any agent |
| **Critical Systems** | Opus | Any agent (Tier 3) |

---

## Example Workflows with Model Selection

### Workflow 1: New Feature (Tier 2)

```bash
# Step 1: Implementation (Sonnet)
"Read YUUJI.md [model:sonnet] and implement password reset feature"

# Step 2: Security Review (Opus - mandatory)
"Read MEGUMI.md [model:opus] and review password reset security"
```

**Cost**: ~4x vs using Sonnet for both
**Benefit**: Thorough security review catches vulnerabilities

---

### Workflow 2: Payment System (Tier 3)

```bash
# Step 1: Implementation (Opus - critical)
"Read YUUJI.md [model:opus] --tier-3 and implement Stripe payment integration"

# Step 2: Security Review (Opus - mandatory)
"Read MEGUMI.md [model:opus] --tier-3 and perform comprehensive security audit of payment flow"
```

**Cost**: ~16x vs using Haiku (never do this!)
**Benefit**: Critical system handled with maximum care

---

### Workflow 3: Simple Build Config (Cost-Optimized)

```bash
# Use Haiku for straightforward task
"Read PANDA.md [model:haiku] and create Dockerfile for basic Node.js app"
```

**Cost**: 1x (baseline)
**Benefit**: Fast, cheap, good enough for simple configs

---

### Workflow 4: Complex Architecture (Quality-Optimized)

```bash
# Step 1: Gojo orchestrates (Opus)
"Read GOJO.md [model:opus] and orchestrate microservices architecture design"

# Step 2: Inumaki designs APIs (Opus for complexity)
"Read INUMAKI.md [model:opus] and design inter-service communication APIs"

# Step 3: Todo designs databases (Opus for multi-tenant)
"Read TODO.md [model:opus] and design multi-tenant database architecture"
```

**Cost**: High (~48x for 3 Opus calls)
**Benefit**: Complex architecture designed correctly the first time

---

## Important Notes

1. **Security Always Uses Opus**: Megumi's Tier 2/3 reviews MUST use Opus
2. **Gojo Defaults to Opus**: Mission-critical orchestration needs best reasoning
3. **Most Work Uses Sonnet**: 80% of tasks work well with Sonnet
4. **Haiku is for Speed**: Simple, repetitive tasks benefit from Haiku
5. **Tier 3 Uses Opus**: Critical systems (auth, payments, PII) need maximum capability
6. **User Can Override**: User has final say on model selection
7. **Cost vs Quality**: Balance based on project budget and criticality

---

🌀 **Remember**: The right model for the right task. Security and critical systems deserve Opus. Most work thrives with Sonnet. Simple tasks fly with Haiku!
