# Engineering Practices & Project Management Guide
<!-- Domain Zero Protocol v9.12.1 - Offline Reference -->

**Agent**: Gojo (Mission Control & Protocol Guardian)
**Last Updated**: 2025-12-26
**Sources**: [Google Engineering Practices](https://google.github.io/eng-practices/), [Agile Manifesto](https://agilemanifesto.org/)

---

## Table of Contents

1. [Code Review Guidelines](#code-review-guidelines)
2. [Commit Standards](#commit-standards)
3. [Agile Principles](#agile-principles)
4. [Documentation Practices](#documentation-practices)
5. [Technical Decision Records](#technical-decision-records)
6. [Team Communication](#team-communication)
7. [Project Lifecycle](#project-lifecycle)

---

## Code Review Guidelines

### The Purpose of Code Review

1. **Improve code quality** - Catch bugs, improve design
2. **Share knowledge** - Spread understanding across team
3. **Ensure consistency** - Maintain coding standards
4. **Teach and learn** - Mentoring opportunity

### What to Look For

```
1. Design
   - Is the code well-designed?
   - Does it fit the architecture?
   - Is it the right abstraction level?

2. Functionality
   - Does the code do what it's supposed to?
   - Are edge cases handled?
   - Is it correct for users?

3. Complexity
   - Is the code more complex than necessary?
   - Will developers understand it later?
   - Is it over-engineered?

4. Tests
   - Are there appropriate tests?
   - Do tests actually test the functionality?
   - Are tests maintainable?

5. Naming
   - Are names clear and descriptive?
   - Do names follow conventions?

6. Comments
   - Are comments necessary and helpful?
   - Do comments explain WHY, not WHAT?

7. Style
   - Does it follow the style guide?
   - Is formatting consistent?

8. Documentation
   - Are public APIs documented?
   - Is README updated if needed?
```

### How to Write Review Comments

```
# Good comments are:
- Constructive - Suggest improvements
- Specific - Point to exact issues
- Actionable - Clear what to do
- Kind - Professional and respectful

# Examples:

# BAD
"This is wrong."
"Why did you do it this way?"

# GOOD
"Consider using a dictionary here for O(1) lookup instead of
searching the list, which is O(n). This matters because this
function is called frequently in the hot path."

"I think this could be simplified by extracting the validation
logic into a separate function. What do you think?"
```

### How to Handle Review Feedback

```
# As the author:
1. Assume good intent
2. Consider each comment carefully
3. Respond to every comment
4. If you disagree, explain why
5. Thank reviewers for their time

# As the reviewer:
1. Be prompt (aim for < 24 hours)
2. Distinguish blocking vs non-blocking feedback
3. Approve when code is good enough
4. Don't block on style preferences
```

### Review Speed

```
# Guidelines:
- Review within one business day
- If too busy, say so and suggest another reviewer
- Small CLs (< 100 lines) should be reviewed faster
- Don't let perfect be the enemy of good

# Prioritization:
1. Unblock others first
2. Review time-sensitive changes
3. Review based on impact
```

---

## Commit Standards

### Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting (no code change) |
| `refactor` | Code change (no feature/fix) |
| `perf` | Performance improvement |
| `test` | Adding tests |
| `chore` | Maintenance tasks |
| `ci` | CI/CD changes |
| `build` | Build system changes |

### Examples

```bash
# Feature
feat(auth): add OAuth2 login support

# Fix
fix(api): handle null response from external service

# Docs
docs(readme): update installation instructions

# Breaking change
feat(api)!: change response format for /users endpoint

BREAKING CHANGE: The response now returns an object with
`data` and `meta` keys instead of a bare array.

# With scope
fix(parser): correctly handle escaped quotes in strings

The parser was failing when strings contained \" sequences.
This fix properly tracks escape state during parsing.

Fixes #123
```

### Commit Message Guidelines

```
# Subject line:
- Use imperative mood ("Add feature" not "Added feature")
- Don't end with period
- Keep under 50 characters
- Capitalize first letter

# Body (when needed):
- Explain WHAT and WHY, not HOW
- Wrap at 72 characters
- Separate from subject with blank line

# Footer:
- Reference issues: "Fixes #123", "Closes #456"
- Co-authors: "Co-authored-by: Name <email>"
- Breaking changes: "BREAKING CHANGE: description"
```

---

## Agile Principles

### The Agile Manifesto

```
We value:
- Individuals and interactions    over processes and tools
- Working software               over comprehensive documentation
- Customer collaboration         over contract negotiation
- Responding to change           over following a plan
```

### Key Practices

#### 1. Iterative Development

```
Sprint/Iteration (1-2 weeks):
1. Plan - Select work from backlog
2. Build - Develop features
3. Review - Demo to stakeholders
4. Retrospect - Improve process
5. Repeat
```

#### 2. User Stories

```
# Format
As a [type of user]
I want [goal]
So that [benefit]

# Example
As a registered user
I want to reset my password
So that I can regain access to my account if I forget it

# Acceptance Criteria
- Email field validates format
- Sends reset link within 1 minute
- Link expires after 24 hours
- Shows confirmation message
```

#### 3. Definition of Done

```
A feature is "done" when:
- [ ] Code complete and reviewed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No critical bugs
- [ ] Deployed to staging
- [ ] Product owner approved
```

#### 4. Retrospectives

```
Format: Start/Stop/Continue

Start doing:
- Daily standups at 9am
- Writing ADRs for decisions

Stop doing:
- Long meetings without agendas
- Skipping code reviews

Continue doing:
- Pair programming on complex features
- Weekly demos to stakeholders
```

---

## Documentation Practices

### Types of Documentation

| Type | Audience | Examples |
|------|----------|----------|
| **API Docs** | Developers | OpenAPI, JSDoc |
| **User Guides** | End users | How-to guides |
| **Architecture** | Team | ADRs, diagrams |
| **README** | New developers | Setup, overview |
| **Runbooks** | Operations | Incident response |

### README Template

```markdown
# Project Name

Brief description of what this project does.

## Quick Start

\`\`\`bash
# Clone and install
git clone https://github.com/org/project
cd project
npm install

# Run
npm start
\`\`\`

## Features

- Feature 1
- Feature 2
- Feature 3

## Documentation

- [API Reference](./docs/api.md)
- [Architecture](./docs/architecture.md)
- [Contributing](./CONTRIBUTING.md)

## Development

### Prerequisites

- Node.js 20+
- PostgreSQL 16+

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Run `npm install`
4. Run `npm run db:migrate`
5. Run `npm run dev`

### Testing

\`\`\`bash
npm test        # Run tests
npm run lint    # Run linter
\`\`\`

## License

MIT
```

### Code Comments

```python
# GOOD: Explain WHY
# We use a 30-second timeout because the external API
# sometimes takes up to 25 seconds during peak hours
timeout = 30

# BAD: Explain WHAT (obvious from code)
# Set timeout to 30
timeout = 30

# GOOD: Document non-obvious behavior
def calculate_price(items):
    """Calculate total price including tax.

    Note: Returns 0 for empty cart rather than raising
    an exception to simplify checkout flow.
    """
    if not items:
        return 0
    return sum(item.price for item in items) * 1.08
```

---

## Technical Decision Records

### ADR Template

```markdown
# ADR-001: Use PostgreSQL for primary database

## Status

Accepted

## Context

We need to choose a primary database for our application.
Requirements:
- ACID compliance
- JSON support for flexible schemas
- Good performance at scale
- Team familiarity

## Decision

We will use PostgreSQL 16.

## Consequences

### Positive
- Strong ACID guarantees
- Excellent JSON/JSONB support
- Team has PostgreSQL experience
- Rich ecosystem of tools

### Negative
- Requires more operational expertise than managed NoSQL
- Horizontal scaling more complex than some alternatives

### Neutral
- Will need connection pooling (PgBouncer)

## Alternatives Considered

### MySQL
- Pros: Team familiarity, good performance
- Cons: Weaker JSON support, fewer advanced features

### MongoDB
- Pros: Flexible schema, easy scaling
- Cons: Weaker consistency guarantees, less team experience
```

### When to Write ADRs

```
Write an ADR when:
- Choosing between significant alternatives
- Making architectural decisions
- Decisions that affect multiple teams
- Decisions that are hard to reverse

Don't write an ADR for:
- Obvious choices
- Easily reversible decisions
- Implementation details
```

---

## Team Communication

### Standup Format

```
Each person shares:
1. What I did yesterday
2. What I'll do today
3. Any blockers

Rules:
- Keep it short (< 15 min total)
- Save discussions for after
- Focus on coordination, not reporting
```

### Async Communication

```
# Effective async messages:

Subject: [ACTION NEEDED] Review PR #123 for auth changes

Context:
- Working on OAuth2 integration (JIRA-456)
- Need this merged by Friday for demo

Request:
- Please review PR #123
- Focus on security aspects

Timeline:
- Review needed by Thursday EOD
- Happy to discuss async or sync

# Include:
- Clear subject with action type
- Context (why, link to ticket)
- Specific request
- Timeline/urgency
```

### Meeting Guidelines

```
# Before meeting:
- Share agenda 24h in advance
- Include relevant documents
- Set clear objective

# During meeting:
- Start on time
- Stick to agenda
- Document decisions

# After meeting:
- Send summary within 24h
- Include action items
- Assign owners and deadlines
```

---

## Project Lifecycle

### Phase 1: Discovery

```
Activities:
- Understand problem
- Research solutions
- Define requirements
- Identify constraints

Outputs:
- Problem statement
- Technical constraints
- Initial scope
```

### Phase 2: Design

```
Activities:
- Architecture design
- API design
- Database schema
- UI/UX mockups

Outputs:
- Design documents
- ADRs
- Prototypes (optional)
```

### Phase 3: Implementation

```
Activities:
- Iterative development
- Code reviews
- Testing
- Documentation

Practices:
- Small, frequent commits
- Feature branches
- CI/CD pipeline
- Regular demos
```

### Phase 4: Release

```
Pre-release:
- Feature freeze
- Testing (QA, UAT)
- Documentation review
- Runbook preparation

Release:
- Staged rollout
- Monitoring
- Rollback plan ready

Post-release:
- Monitor metrics
- Gather feedback
- Fix issues
```

### Phase 5: Maintenance

```
Ongoing:
- Bug fixes
- Security updates
- Dependency updates
- Performance monitoring

Regular:
- Retrospectives
- Technical debt review
- Documentation updates
```

---

## Quick Reference

### Code Review Checklist

```
[ ] Design is appropriate
[ ] Functionality is correct
[ ] Tests are adequate
[ ] Code is readable
[ ] No obvious bugs
[ ] Security considered
[ ] Performance acceptable
[ ] Documentation updated
```

### PR Template

```markdown
## Description
Brief description of changes

## Type
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing done

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed
- [ ] Comments added where needed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #123
```

### Decision Matrix

```
| Option | Effort | Impact | Risk | Score |
|--------|--------|--------|------|-------|
| A      | Low    | High   | Low  | 9     |
| B      | Medium | Medium | Low  | 6     |
| C      | High   | High   | High | 4     |

Scoring: Impact(1-3) + (4-Effort) + (4-Risk)
```

---

**Online References**:
- [Google Engineering Practices](https://google.github.io/eng-practices/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [ADR GitHub](https://adr.github.io/)
