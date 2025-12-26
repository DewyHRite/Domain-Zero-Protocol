# Offline Reference Documentation
<!-- Domain Zero Protocol v8.10.0 -->

**Purpose**: Comprehensive offline documentation for DZP agents to reference authoritative best practices without requiring internet access.

**Version**: 8.10.0
**Last Updated**: 2025-12-26

---

## Document Index

### Testing (Yuuji - Implementation Specialist)

| Document | Description | Lines |
|----------|-------------|-------|
| [pytest-complete-guide.md](testing/pytest-complete-guide.md) | Python testing with pytest: fixtures, markers, mocking, async | ~500 |
| [jest-vitest-guide.md](testing/jest-vitest-guide.md) | JavaScript testing with Jest/Vitest: matchers, mocking, snapshots | ~450 |

**Online References**: [pytest](https://docs.pytest.org/), [Jest](https://jestjs.io/), [Vitest](https://vitest.dev/)

---

### Accessibility (Nobara - Creative Strategy & UX)

| Document | Description | Lines |
|----------|-------------|-------|
| [wcag-22-complete-guide.md](accessibility/wcag-22-complete-guide.md) | WCAG 2.2 guidelines: POUR principles, success criteria, ARIA | ~550 |

**Online References**: [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/), [WebAIM](https://webaim.org/)

---

### Security (Megumi - Security Analyst)

| Document | Description | Lines |
|----------|-------------|-------|
| [owasp-top10-guide.md](security/owasp-top10-guide.md) | OWASP Top 10: vulnerabilities, prevention, code examples | ~600 |

**Online References**: [OWASP Top 10](https://owasp.org/Top10/), [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)

---

### Database (Todo - Database & Backend Specialist)

| Document | Description | Lines |
|----------|-------------|-------|
| [postgresql-schema-guide.md](database/postgresql-schema-guide.md) | PostgreSQL: schema design, indexing, migrations, optimization | ~600 |

**Online References**: [PostgreSQL Docs](https://www.postgresql.org/docs/), [Use The Index, Luke](https://use-the-index-luke.com/)

---

### Performance (Maki - Performance Optimization Specialist)

| Document | Description | Lines |
|----------|-------------|-------|
| [core-web-vitals-guide.md](performance/core-web-vitals-guide.md) | Core Web Vitals: LCP, INP, CLS optimization, profiling | ~550 |

**Online References**: [web.dev](https://web.dev/), [Chrome DevTools](https://developer.chrome.com/docs/devtools/)

---

### CI/CD (Panda - Build & Integration Specialist)

| Document | Description | Lines |
|----------|-------------|-------|
| [github-actions-docker-guide.md](cicd/github-actions-docker-guide.md) | GitHub Actions & Docker: workflows, Dockerfile best practices | ~650 |

**Online References**: [GitHub Actions](https://docs.github.com/en/actions), [Docker Docs](https://docs.docker.com/)

---

### API Design (Inumaki - API & Communication Specialist)

| Document | Description | Lines |
|----------|-------------|-------|
| [rest-api-design-guide.md](api/rest-api-design-guide.md) | REST API design: resources, HTTP methods, status codes, OpenAPI | ~600 |

**Online References**: [Zalando Guidelines](https://opensource.zalando.com/restful-api-guidelines/), [OpenAPI](https://spec.openapis.org/)

---

### Project Management (Gojo - Mission Control)

| Document | Description | Lines |
|----------|-------------|-------|
| [engineering-practices-guide.md](project-management/engineering-practices-guide.md) | Code review, commits, agile, ADRs, team communication | ~500 |

**Online References**: [Google Engineering Practices](https://google.github.io/eng-practices/), [Conventional Commits](https://www.conventionalcommits.org/)

---

## Directory Structure

```
docs/reference/offline/
├── README.md                          # This index
├── testing/
│   ├── pytest-complete-guide.md       # Python testing
│   └── jest-vitest-guide.md           # JavaScript testing
├── accessibility/
│   └── wcag-22-complete-guide.md      # WCAG 2.2 guidelines
├── security/
│   └── owasp-top10-guide.md           # OWASP Top 10
├── database/
│   └── postgresql-schema-guide.md     # PostgreSQL & schema design
├── performance/
│   └── core-web-vitals-guide.md       # Core Web Vitals
├── cicd/
│   └── github-actions-docker-guide.md # GitHub Actions & Docker
├── api/
│   └── rest-api-design-guide.md       # REST API design
└── project-management/
    └── engineering-practices-guide.md # Engineering practices
```

---

## Usage

### For Agents

Each agent can reference these documents for authoritative guidance:

```
Yuuji → testing/*.md
Nobara → accessibility/*.md
Megumi → security/*.md
Todo → database/*.md
Maki → performance/*.md
Panda → cicd/*.md
Inumaki → api/*.md
Gojo → project-management/*.md
```

### For Users

These documents can be read directly for quick reference without needing to search online documentation.

---

## Document Standards

All offline documents follow this structure:

1. **Header**: Protocol version, agent, last updated, sources
2. **Table of Contents**: Navigable sections
3. **Content**: Comprehensive coverage with code examples
4. **Quick Reference**: Cheatsheet-style summary
5. **Online References**: Links to authoritative sources

---

## Maintenance

**Updated By**: Sukuna (System Update Adversary)
**Review Cycle**: With each protocol version update

**Update Triggers**:
- Major version changes in referenced technologies
- New best practices published by authoritative sources
- Agent specialization changes
- User feedback

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-26 | 8.10.0 | Initial creation of comprehensive offline documentation |

---

**Total Documents**: 9
**Total Lines**: ~4,800
**Coverage**: All 8 agent specializations (excluding Sukuna system updates)
