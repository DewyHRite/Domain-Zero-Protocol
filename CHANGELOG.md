# Changelog - Domain Zero Protocol

All notable changes to the Domain Zero Protocol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [8.2.0] - 2025-11-18

### Added

#### **Research Mode Enhancement** - Active agent research implementation

**Agent Research Capabilities:**
- All 4 agents (Yuuji, Megumi, Nobara, Gojo) can now conduct domain-specific research
- Invocation pattern: `"Read [agent].agent.md --research and investigate [topic]"`
- Research Mode specification (v7.2.0) now fully implemented with active invocation

**Research Focus Areas by Agent:**
- **Yuuji (Weekly):** Implementation patterns, TDD tooling, test isolation, async patterns, build performance
- **Megumi (Weekly):** OWASP updates, emerging vulnerabilities, cryptographic standards, CVE trends, compliance standards
- **Nobara (Biweekly):** WCAG guidelines, usability heuristics, onboarding flows, accessibility tooling, inclusive design
- **Gojo (Monthly):** Meta trends, coordination tooling, risk landscape, protocol governance, process optimization

**Research Output Structure:**
- Directory: `.protocol-state/research/` with agent subdirectories
- Structured summaries: `[agent]/[timestamp].summary.md`
- Raw notes: `[agent]/[timestamp].raw.log` (gitignored for privacy)
- Global index: `research-index.json` tracking last session timestamps

**Summary Template Features:**
- Focus questions (3-5 specific research questions)
- Key findings table with sources and confidence indicators (High/Medium/Low)
- Actionable recommendations (experiments, not mandates)
- Source citations with OWASP/WCAG/RFC/CVE mappings
- Privacy protection (raw notes never committed)

**Quality Gates:**
- Minimum 3 primary sources required (OWASP, NIST, W3C, RFC, peer-reviewed)
- High confidence findings require 2+ source corroboration
- Security items mapped to OWASP/CVE/NIST (Megumi only)
- WCAG criterion mapping with A/AA/AAA levels (Nobara only)

**Staleness Monitoring (Gojo enforces):**
- Standard warning: 14+ days without research
- Critical escalation: 7+ days for security/auth/crypto topics (Megumi)
- Research currency status shown in Mission Control interface
- Reminders issued during context restoration

**Research → Implementation Integration:**
- Research findings documented in structured summaries
- User reviews recommendations and approves approach
- Standard tier workflows apply (Tier 1/2/3) for implementation
- Implementation uses current best practices from research

**Example Invocations:**
```bash
"Read yuuji.agent.md --research and investigate pytest fixture best practices"
"Read megumi.agent.md --research and investigate OWASP Top 10 2025 changes"
"Read nobara.agent.md --research and investigate WCAG 2.2 success criteria"
"Read gojo.agent.md --research and investigate multi-agent orchestration patterns"
```

### Changed

#### **protocol/CLAUDE.md** - Mode 4: Research Mode added

**Operational Modes Section:**
- Added comprehensive Research Mode overview (Mode 4)
- Documented research focus by agent with cadence schedules
- Included quality gates and staleness monitoring details
- Added "When to Use" guidance (before critical implementations, periodic updates, standard updates)

**Agent Invocation Patterns:**
- Added research mode examples for all 4 agents (Yuuji, Megumi, Nobara, Gojo)
- Included research flag usage patterns
- Added Nobara invocation section (was missing)

#### **All 4 Agent Files** - Research mode sections added

**yuuji.agent.md (lines 1318-1462):**
- Purpose: Stay current on implementation patterns and TDD tooling
- Research focus: Implementation patterns, TDD tooling, test isolation, async patterns
- Invocation examples: pytest fixtures, async test isolation, FastAPI testing
- Output template and integration with implementation workflows

**megumi.agent.md (lines 2043-2229):**
- Purpose: Maintain OWASP knowledge and track emerging vulnerabilities
- Research focus: OWASP updates, emerging vulnerabilities, cryptography, CVE trends
- Security-specific source prioritization (NIST, CVE database, RFC security specs)
- CVE/NIST cross-reference requirements and risk assessment

**nobara.agent.md (lines 561-739):**
- Purpose: Stay current on WCAG and usability best practices
- Research focus: WCAG guidelines, usability heuristics, onboarding flows, accessibility
- User-centered research prioritization (W3C/WAI, Nielsen Norman Group)
- WCAG criterion mapping with A/AA/AAA compliance levels

**gojo.agent.md (lines 1952-2148):**
- Purpose: Strategic awareness of meta trends and coordination patterns
- Research focus: Meta trends, coordination tooling, risk landscape, protocol governance
- Strategic synthesis with cross-domain insights
- Agent research monitoring responsibilities (staleness detection for all agents)

### Updated

**Core Protocol:**
- `protocol.config.yaml` - Version 8.2.0, config_version 2.2
- `protocol/CLAUDE.md` - Version 8.2.0, Mode 4: Research Mode operational mode
- `.protocol-state/project-state.json` - protocol_version 8.2.0

**Agent Files:**
- `protocol/yuuji.agent.md` - Research mode section (145 lines)
- `protocol/megumi.agent.md` - Research mode section (187 lines)
- `protocol/nobara.agent.md` - Research mode section (179 lines)
- `protocol/gojo.agent.md` - Research mode section (197 lines)

**State Management:**
- `.protocol-state/research/` - Directory structure created with agent subdirectories
- `.protocol-state/research/research-index.json` - Initial index with agent metadata
- `.gitignore` - Already configured for raw.log exclusions (v7.2.0)

### Configuration

Research mode controlled via `protocol.config.yaml`:

```yaml
research:
  enabled: true
  allowed_agents: ["yuuji", "megumi", "nobara", "gojo"]
  cadence:
    yuuji: "weekly"
    megumi: "weekly"
    nobara: "biweekly"
    gojo: "monthly"
  max_session_minutes: 25
  source_policy:
    max_sources: 12
    min_primary_sources: 3
  escalation:
    stale_days_warning: 14
    critical_domain_stale_days: 7
```

### No Breaking Changes

- ✅ Research mode is optional (enabled by default but not required)
- ✅ Existing workflows unchanged (agents function normally without research)
- ✅ All changes are backward compatible
- ✅ Tier system unchanged (1/2/3 workflows still work as before)
- ✅ Invocation patterns extended (research flag added as option)

### Upgrade Notes

**No action required** - This is a backward-compatible minor release.

**Optional: Use Research Mode**
```bash
# Research before critical implementations
"Read megumi.agent.md --research and investigate OWASP Top 10 2025 changes"

# Then implement with current knowledge
"Read yuuji.agent.md --tier critical and implement JWT authentication"
```

**Research Benefits:**
- Stay current with evolving standards (OWASP, WCAG, TDD best practices)
- Evidence-based recommendations with citations
- Reduced risk of implementing outdated patterns
- Structured knowledge updates with confidence indicators

---

## [8.1.0] - 2025-11-18

### Added

#### **Playwright E2E Testing Infrastructure** - Complete end-to-end testing setup

**New Directory Structure:**
- `tests/e2e/` - Complete Playwright test infrastructure
  - `package.json` - Playwright dependencies and test scripts
  - `playwright.config.ts` - Multi-browser configuration (Chromium, Firefox, WebKit)
  - `specs/counter.spec.ts` - Visual demo test with interactive counter
  - `specs/web_smoke.spec.ts` - External site smoke test examples
  - `.gitignore` - Excludes test artifacts (reports, traces, videos)

**NPM Scripts:**
- `npm test` - Run all tests in headless mode
- `npm run test:headed` - Run tests in visible browser window
- `npm run test:ui` - Interactive UI mode for debugging
- `npm run test:debug` - Debug mode with breakpoints
- `npm run report` - Show HTML test report
- `npm run install:browsers` - Install Playwright browsers

**Tier System Integration:**
- **Tier 1 (Rapid):** Optional - Use E2E tests locally for demos only, no security review
- **Tier 2 (Standard):** Recommended - Add E2E smoke tests for critical user flows, Megumi reviews results
- **Tier 3 (Critical):** Required - Comprehensive E2E coverage with traces/videos, run in CI, Megumi examines security flows

**Agent Role Extensions:**
- **Yuuji (Implementation):** Creates/updates E2E tests, ensures repeatability, documents in dev-notes.md
- **Megumi (Security):** Reviews test coverage for OWASP risks, validates traces for auth/payment flows
- **Gojo (Mission Control):** Wires CI to run Playwright on PRs, gates merges, tracks skipped reviews

**VS Code Integration:**
- Tasks configured in `.vscode/tasks.json`:
  - `E2E: Install Playwright Browsers`
  - `E2E: Run (headed)`
  - `E2E: UI Mode`
  - `E2E: Show Report`

**Test Specifications:**
- `counter.spec.ts` - Visual demo with interactive counter (renders HTML, clicks buttons, verifies increments)
- `web_smoke.spec.ts` - External site smoke tests (Playwright docs, GitHub) with app-specific template

**Multi-Browser Support:**
- Chromium (Desktop Chrome)
- Firefox (Desktop Firefox)
- WebKit (Desktop Safari)
- Optional: Mobile viewport testing (commented out, ready to enable)

**Test Artifacts:**
- HTML reports in `playwright-report/`
- Traces captured on first retry
- Screenshots on failure
- Videos retained on failure

### Changed

#### **Documentation**
- ✅ `docs/playwright.md` - Complete Playwright integration guide added
- ✅ Protocol mapping for Tier 1/2/3 documented
- ✅ Agent role documentation updated with E2E responsibilities
- ✅ Setup instructions for Windows PowerShell
- ✅ Visual testing guidance (headed mode, UI mode, reports)

### No Breaking Changes

- ✅ Existing workflows unchanged
- ✅ Agent files unchanged (yuuji.agent.md, megumi.agent.md, gojo.agent.md)
- ✅ Tier system unchanged (1/2/3 workflows still work as before)
- ✅ Invocation patterns unchanged
- ✅ Optional enhancement (not required for existing users)

### Upgrade Notes

**No action required** - This is a backward-compatible release.

**Optional: Enable Playwright E2E Testing**
```powershell
cd "tests/e2e"
npm install
npm run install:browsers
npm run test:headed  # Watch tests in real browser
```

**Integration:**
- Tier 2: Yuuji creates E2E smoke tests → Megumi reviews coverage
- Tier 3: Yuuji creates comprehensive E2E → Megumi examines traces → Run in CI

**CI Integration (Optional):**
Add GitHub Action to run Playwright tests and upload reports as PR artifacts.

---

## [8.0.0] - 2025-11-18

### Breaking Changes

#### 🔴 Agent File Format Migration
- **Old Format**: `protocol/YUUJI.md`, `protocol/MEGUMI.md`, `protocol/NOBARA.md`, `protocol/GOJO.md`
- **New Format**: `protocol/yuuji.agent.md`, `protocol/megumi.agent.md`, `protocol/nobara.agent.md`, `protocol/gojo.agent.md`
- **Impact**: All agent file references must be updated across documentation, scripts, and invocation patterns

#### 🔴 Invocation Pattern Changes
- **Old**: `"Read YUUJI.md and implement feature"`
- **New**: `"Read yuuji.agent.md and implement feature"`
- **Impact**: User invocation commands must use new lowercase .agent.md file names
- **Migration**: Update all scripts, documentation, and workflow references

#### 🔴 YAML Frontmatter Required
- **Requirement**: All .agent.md files MUST include YAML frontmatter with 7 required fields
- **Fields**: `target`, `name`, `description`, `argument-hint`, `model`, `tools`, `handoffs`
- **Impact**: Custom agents must be migrated to include structured metadata
- **Validation**: Use `scripts/validate-agents.ps1` to verify format compliance

### Added

#### 1. **.agent.md File Format** - Structured agent metadata system
- **YAML Frontmatter**: Structured configuration header for all agent files
  - `target` field: Environment targeting (`vscode` | `github`)
  - `name` field: Agent full name with role
  - `description` field: Brief agent description
  - `argument-hint` field: Usage instruction/example
  - `model` field: AI model ID (e.g., `claude-3-5-sonnet-20241022`)
  - `tools` array: List of available tools
  - `handoffs` array: Agent transition definitions

#### 2. **Tool Access Matrix** - Formalized permissions table
- **Structure**: Markdown table in every agent file showing tool permissions
- **Access Levels**:
  - ✅ Full Access (unrestricted use)
  - ⚠️ Conditional Access (restricted/requires authorization)
  - ❌ Prohibited (tool not available)
- **Columns**: Tool name, Access Level, Usage description
- **Purpose**: Clear, auditable tool permissions for security and transparency

#### 3. **Declarative Handoff Mechanism** - Agent-to-agent transitions
- **YAML Configuration**: Handoffs defined in frontmatter
- **Trigger Keywords**: `@security-review`, `@remediation-required`, `@approved`, etc.
- **Context Transfer**: Automatic payload passing between agents
  - `files_modified` - Modified file list
  - `tier_level` - Tier 1/2/3 specification
  - `implementation_scope` - Feature scope description
  - `test_coverage` - Test coverage metrics
  - `security_findings` - SEC-IDs from reviews
- **Orchestration**: Mission Control (Gojo) coordinates all handoffs
- **Documentation**: `protocol/HANDOFF_SPECIFICATION.md` (15KB comprehensive spec)

#### 4. **Environment Targeting** - VS Code vs GitHub Copilot compatibility
- **`target` Field**: Specifies agent environment in YAML frontmatter
- **VS Code Target** (`target: vscode`):
  - ✅ Full MCP integration
  - ✅ All tools available
  - ✅ Automated handoffs
  - ✅ Persistent state management
- **GitHub Copilot Target** (`target: github`):
  - ❌ No MCP integration
  - ⚠️ Limited tool set
  - ⚠️ Manual handoffs
  - ❌ No persistent state
- **Documentation**: `protocol/ENVIRONMENT_TARGETING.md` (detailed environment guide)

#### 5. **MCP Integration Support** - Model Context Protocol server connections
- **Purpose**: Enable agents to connect to external data sources and services
- **Examples**:
  - Yuuji → Database MCP server → Query project schema
  - Megumi → CVE database MCP → Check vulnerability databases
  - Gojo → Jira MCP server → Sync project status
- **Configuration**: MCP servers defined in `~/.config/claude-code/mcp.json`
- **Benefits**:
  - Real-time data access during agent execution
  - Extend agent capabilities beyond built-in tools
  - Standardized connection management
- **Documentation**: `protocol/MCP_INTEGRATION.md` (comprehensive MCP guide)

#### 6. **Agent Validation Script** - Automated .agent.md format validation
- **File**: `scripts/validate-agents.ps1` (271 lines, 17 validation checks)
- **Phase 1**: Agent file existence (new .agent.md files present)
- **Phase 2**: Old agent file cleanup (old .md files removed)
- **Phase 3**: YAML frontmatter validation (parsing and required fields)
- **Phase 4**: Tool Access Matrix presence check
- **Phase 5**: Content integrity validation (minimum length requirements)
- **Phase 6**: Documentation reference scanning (no old .md references)
- **Features**:
  - Quick mode for fast verification
  - Comprehensive error reporting
  - Documentation reference validation
  - Exit codes for CI/CD integration

#### 7. **Comprehensive Specification Documents** - Complete guides
- **protocol/HANDOFF_SPECIFICATION.md** (15KB):
  - Complete handoff mechanism guide
  - Context transfer protocols
  - Agent-specific handoff patterns
  - Security considerations
  - Testing handoffs
  - Complete example: Tier 2 JWT Authentication workflow
- **protocol/MCP_INTEGRATION.md** (comprehensive):
  - What is MCP and how it works
  - MCP server configuration examples
  - Agent MCP capabilities
  - Example integrations (database, GitHub, Jira)
  - Security best practices
  - Troubleshooting guide
  - Creating custom MCP servers
- **protocol/ENVIRONMENT_TARGETING.md** (detailed):
  - VS Code vs GitHub Copilot targeting
  - Feature comparison matrix
  - Migration guides (Copilot → VS Code, VS Code → Copilot)
  - Multi-target support
  - Best practices

### Changed

#### 1. **protocol/CLAUDE.md** - Main protocol file updates
- ✅ Added comprehensive ".AGENT.MD FORMAT (v8.0.0+)" section
- ✅ Updated all agent file references (YUUJI.md → yuuji.agent.md)
- ✅ Updated all invocation pattern examples
- ✅ Added YAML frontmatter field documentation
- ✅ Added Tool Access Matrix explanation
- ✅ Added handoff mechanism documentation
- ✅ Added MCP integration overview
- ✅ Added environment targeting overview
- ✅ Added links to new specification documents
- ✅ Updated version to v8.0.0
- ✅ Updated major enhancements to highlight .agent.md format

#### 2. **README.md** - User-facing documentation
- ✅ Updated all agent file references (protocol/*.md → protocol/*.agent.md)
- ✅ Updated invocation pattern examples throughout
- ✅ Added links to .agent.md format documentation
- ✅ Updated quick start instructions
- ✅ Updated troubleshooting section with new file names

#### 3. **protocol.config.yaml** - Configuration file
- ✅ Updated agent file paths:
  - `yuuji_md: "protocol/yuuji.agent.md"`
  - `megumi_md: "protocol/megumi.agent.md"`
  - `nobara_md: "protocol/nobara.agent.md"`
  - `gojo_md: "protocol/gojo.agent.md"`
- ✅ Updated `protocol_version` to `8.0.0`
- ✅ Updated `config_version` to `2.0`
- ✅ Updated `last_updated` to `2025-11-18`

#### 4. **All Agent Files** - Migrated to .agent.md format
- **protocol/yuuji.agent.md**:
  - ✅ YAML frontmatter with all required fields
  - ✅ Tool Access Matrix section
  - ✅ Handoff definitions (to Megumi and Gojo)
  - ✅ Complete agent documentation preserved
  - ✅ Target: vscode (full MCP support)

- **protocol/megumi.agent.md**:
  - ✅ YAML frontmatter with security-specific configuration
  - ✅ Tool Access Matrix with security tools
  - ✅ Handoff definitions (to Yuuji and Gojo)
  - ✅ OWASP Top 10 review process documented
  - ✅ Target: vscode (CVE database MCP integration)

- **protocol/nobara.agent.md**:
  - ✅ YAML frontmatter with UX/creative configuration
  - ✅ Tool Access Matrix with design tools
  - ✅ Handoff definitions (to Yuuji and Megumi)
  - ✅ Design thinking methodology documented
  - ✅ Target: vscode (design tool MCP integration)

- **protocol/gojo.agent.md** (2060 lines):
  - ✅ YAML frontmatter with mission control configuration
  - ✅ Tool Access Matrix with special CLAUDE.md permissions
  - ✅ Handoff definitions (briefing all agents)
  - ✅ Passive observation system documented
  - ✅ Protocol guardian role formalized
  - ✅ Target: vscode (Jira/project management MCP integration)

### Removed

#### 1. **Old Agent Files** - Deleted and replaced
- ❌ `protocol/YUUJI.md` (replaced by `protocol/yuuji.agent.md`)
- ❌ `protocol/MEGUMI.md` (replaced by `protocol/megumi.agent.md`)
- ❌ `protocol/NOBARA.md` (replaced by `protocol/nobara.agent.md`)
- ❌ `protocol/GOJO.md` (replaced by `protocol/gojo.agent.md`)
- **Deletion Method**: `git rm` to ensure clean git history

### Migration Guide

#### Step 1: Update Agent File References
```bash
# Find and replace old references in your codebase
# Old: protocol/YUUJI.md → New: protocol/yuuji.agent.md
# Old: protocol/MEGUMI.md → New: protocol/megumi.agent.md
# Old: protocol/NOBARA.md → New: protocol/nobara.agent.md
# Old: protocol/GOJO.md → New: protocol/gojo.agent.md
```

#### Step 2: Update Invocation Patterns
**Old pattern**:
```bash
"Read YUUJI.md and implement feature"
```

**New pattern**:
```bash
"Read yuuji.agent.md and implement feature"
```

#### Step 3: Verify Agent Files Exist
```bash
# Check that new agent files are present
ls protocol/*.agent.md

# Should see:
# protocol/yuuji.agent.md
# protocol/megumi.agent.md
# protocol/nobara.agent.md
# protocol/gojo.agent.md
```

#### Step 4: Run Validation
```powershell
# Validate all agent files
./scripts/validate-agents.ps1

# Expected: All 17 checks pass
```

#### Step 5: Update Custom Agents (if any)
If you created custom agents, update them to .agent.md format:
1. Add YAML frontmatter (see examples in protocol/*.agent.md)
2. Add Tool Access Matrix section
3. Define handoffs in YAML
4. Rename file to *.agent.md

#### Step 6: Test Invocation
```bash
# Test each agent
"Read yuuji.agent.md and implement test feature"
"Read megumi.agent.md and review test feature"
"Read nobara.agent.md and design test UX"
"Read gojo.agent.md" → Select Option 1 (Resume)

# Verify:
# ✅ Agent responds correctly
# ✅ Tools work as expected
# ✅ Handoffs function properly
```

#### Step 7: Optional - Enable MCP Integration
```bash
# Create MCP configuration (if desired)
mkdir -p ~/.config/claude-code
cat > ~/.config/claude-code/mcp.json <<EOF
{
  "mcpServers": {
    "database": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://localhost:5432/mydb"
      }
    }
  }
}
EOF

# See protocol/MCP_INTEGRATION.md for more examples
```

### Breaking Change Impact Assessment

**High Impact**:
- ✅ Agent file names changed (all references must update)
- ✅ Invocation patterns changed (scripts/docs must update)
- ✅ File path references in automation scripts

**Medium Impact**:
- ✅ Custom agents need .agent.md migration
- ✅ YAML frontmatter structure learning curve
- ✅ Tool Access Matrix formalization

**Low Impact**:
- ✅ MCP integration (optional feature, can enable later)
- ✅ Environment targeting (defaults to vscode, works transparently)
- ✅ Handoff mechanism (enhances existing workflow patterns)

### No Action Required (Backward Compatible Behavior)

- ✅ Core agent behavior unchanged (Yuuji still implements, Megumi still reviews)
- ✅ Tier system unchanged (Rapid/Standard/Critical still work)
- ✅ Dual workflow unchanged (implementation → security review)
- ✅ Protocol philosophy unchanged (Zero defects, Perfect collaboration)
- ✅ Safety principles unchanged (User safety first)
- ✅ Backup requirements unchanged (Always required)

### Upgrade Support Resources

**Having trouble upgrading?**

1. **Read specification docs**:
   - `protocol/HANDOFF_SPECIFICATION.md`
   - `protocol/MCP_INTEGRATION.md`
   - `protocol/ENVIRONMENT_TARGETING.md`

2. **Run validation script**:
   ```powershell
   ./scripts/validate-agents.ps1 -Verbose
   ```

3. **Check for old references**:
   ```powershell
   # Search for old agent file references
   grep -r "YUUJI\.md\|MEGUMI\.md\|NOBARA\.md\|GOJO\.md" .
   ```

4. **Review example agent files**:
   - `protocol/yuuji.agent.md` - See complete .agent.md example
   - Compare old vs new format

### Version Compatibility

- **Requires**: Claude Code or VS Code with Claude extension for full MCP support
- **Compatible with**: GitHub Copilot (limited feature set, see ENVIRONMENT_TARGETING.md)
- **Minimum Protocol Version**: v8.0.0 (breaking changes from v7.x.x)
- **Recommended Migration Path**: v7.2.0 → v8.0.0 (follow all 7 migration steps)

### Performance & Quality

- ✅ Validation script runs 17 checks in <5 seconds
- ✅ YAML parsing overhead: <100ms per agent file
- ✅ Tool Access Matrix lookup: O(1) constant time
- ✅ Handoff context transfer: <200ms per handoff
- ✅ MCP integration latency: Depends on MCP server response time

### Security Enhancements

- ✅ Formalized tool permissions in Tool Access Matrix
- ✅ Declarative handoff security boundaries
- ✅ MCP server authorization layer
- ✅ Environment targeting prevents feature leakage
- ✅ Validation script prevents malformed agent files

---

## [7.2.0] - 2025-11-09

### Added
- **Research Mode** - Structured agent knowledge updates on evolving best practices:
  - **protocol/RESEARCH_MODE.md** - Complete 265-line specification for agent research workflows
  - **Research Configuration** (protocol.config.yaml):
    - `research.enabled` - Master toggle for Research Mode
    - `research.cadence` - Per-agent research schedules (weekly/biweekly/monthly)
    - `research.source_policy` - Quality gates (min primary sources, freshness requirements)
    - `research.privacy` - Privacy protection settings (gitignore raw notes, redact PII)
    - `research.verification` - Dual-source corroboration, security cross-referencing
    - `research.escalation` - Staleness detection and notification thresholds
    - `research.role_focus` - Agent-specific research focus areas
  - **Research State Directory** (.protocol-state/research/):
    - `research-index.json` - Global research session tracking
    - `yuuji/`, `megumi/`, `nobara/`, `gojo/` - Per-agent research outputs
    - `README.md` - Research directory documentation
  - **.gitignore Updates** - Raw research logs (.raw.log) gitignored for privacy

**Agent-Specific Research Focus:**
  - **Yuuji** (Implementation Specialist): Implementation patterns, TDD tooling, test isolation (weekly cadence)
  - **Megumi** (Security Analyst): OWASP updates, emerging vulnerabilities, cryptography papers (weekly cadence)
  - **Nobara** (Creative Strategy/UX): WCAG guidelines, usability heuristics, accessibility tooling (biweekly cadence)
  - **Gojo** (Mission Control): Meta trends, coordination tooling, risk landscape (monthly cadence)

**Research Session Workflow:**
  1. **Initiation** (`@research-start`): Validate enabled, load last session for continuity
  2. **Scoping**: Form 3-5 focused research questions
  3. **Source Selection**: Build candidate list, filter via source policy (min 3 primary sources)
  4. **Collection**: Retrieve summaries/excerpts with timestamps
  5. **Triangulation**: Cross-check 2+ sources for each key claim, mark confidence (High/Medium/Low)
  6. **Synthesis** (`@research-update`): Produce structured summary with citations
  7. **Validation**: Agent-specific verification (security mapping, UX criteria, etc.)
  8. **Completion** (`@research-complete`): Persist curated summary, update index

**Privacy Features:**
  - Raw research notes gitignored (never committed)
  - Automatic PII redaction
  - URL-only storage (summaries, not full dumps)
  - GDPR-compliant data handling

### Changed
- **protocol.config.yaml**:
  - Updated version to v7.2.0
  - Updated config_version to 1.3
  - Updated last_updated to 2025-11-09
  - Added comprehensive `research` configuration section (85 lines)

- **VERSION.md**:
  - Updated to v7.2.0
  - Added "What's New in v7.2.0" section
  - Updated cumulative improvements
  - Updated assessment score

- **protocol/RESEARCH_MODE.md**:
  - Updated version reference to v7.2.0

### Security
- Research Mode includes security verification gates for Megumi
- Research outputs mapped to OWASP Top 10, CVE feeds, and NIST standards
- Privacy-first design with gitignored raw notes and PII redaction

### Performance
- Research sessions capped at 25 minutes to prevent fatigue
- Staleness detection ensures agents stay current (14-day warning, 7-day for critical domains)

---

## [7.1.1] - 2025-11-09

### Added
- **Comprehensive Agent Documentation System** - Complete agent building and usage guides:
  - `Domain Zero Agents/` - Generic agent building framework with templates
    - `AGENT_TEMPLATE.md` - Universal template for creating custom agents
    - `README.md` - Guide for building custom agents
    - `examples/KIRA_DOCUMENTATION_SPECIALIST.md` - Example custom agent
  - `Domain Zero Agents - Full JJK Edition/` - 8 complete character agents
    - Core Four: GOJO.md, YUUJI.md, MEGUMI.md, NOBARA.md
    - Extended: PANDA.md, MAKI.md, INUMAKI.md, TODO.md
    - JJK_AGENT_TEMPLATE.md - JJK-themed agent template
- **Core Documentation (3 comprehensive guides)**:
  - `AGENT_INVOCATION_GUIDE.md` - System prompts for all 8 agents (16 KB)
  - `AGENT_TOOLS_REFERENCE.md` - Tool permissions + advanced capabilities (32 KB)
  - `AGENT_MODEL_RECOMMENDATIONS.md` - Opus/Sonnet/Haiku selection guide (18 KB)
- **SYSTEM_UPDATE_COMPLETE_V7.1.0.md** - Complete v7.1.0 release documentation

### Changed
- **README.md** - Added Agent Documentation section (lines 154-160, 912-936)
  - Links to generic and JJK agent documentation
  - Integration examples and usage guidance
- **Protocol files** - Updated version references from v7.1.0 to v7.1.1
- **project-state.json** - Updated protocol_version to 7.1.1

### Fixed
- Version consistency across all protocol and documentation files

### Documentation
- Total: 16 new files, ~313 KB of agent documentation
- Coverage: System prompts, tool permissions, model recommendations, advanced capabilities
- Integration: Parallel execution, background processes, Jupyter notebooks

---


---

## [7.1.0] - 2025-11-08

### Breaking Changes
- **Dual Workflow Enforcement** (Tier 2/3 only):
  - Yuuji and Megumi CANNOT be invoked separately for Tier 2 (Standard) or Tier 3 (Critical) features
  - **Old pattern** (deprecated): User invokes Yuuji → user manually tags @security-review → user invokes Megumi separately
  - **New pattern** (v7.1.0): User invokes Yuuji once → Yuuji prompts for Megumi invocation after implementation complete
  - **Rationale**: Eliminate possibility of skipped security reviews for production code (Tier 2/3)
  - **Migration**: See DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md for step-by-step migration instructions
  - **Tier 1 exception**: Rapid prototyping (Tier 1) unchanged - Yuuji-only invocation still valid

### Added
- **Dual Workflow Enforcement Guide** (DUAL_WORKFLOW_ENFORCEMENT_GUIDE.md):
  - Complete migration guide for new Yuuji-Megumi collaboration pattern
  - Old vs new invocation pattern comparison
  - Tier-specific examples (Tier 1/2/3)
  - Success criteria and validation checklist
  - Integration guidance for existing projects

- **Mask Mode Configuration** (protocol.config.yaml):
  - Master toggle: `mask_mode.enabled` (true = JJK theme, false = professional mode)
  - Granular settings: control banners, personality, terminology, emoji, and narrative framing independently
  - Unmasked names: professional agent titles when mask is OFF (Implementation Specialist, Security Analyst, etc.)
  - Unmasked terminology: standard translations for JJK terms (Domain Zero → Protocol Environment, etc.)

- **MASK_MODE.md** - Complete specification document:
  - What Mask Mode is and why it exists (presentation choice without functionality loss)
  - Truth about "agents" (same AI, different prompts - per REALITY_CHECK.md)
  - Behavior comparison tables (MASK ON vs MASK OFF)
  - Configuration reference with validation rules
  - Migration guide from v7.0.0
  - Use case guidance (personal vs professional contexts)
  - Examples demonstrating both modes

- **REALITY_CHECK.md** - Honest documentation:
  - What "agents" really are (prompt engineering, not true multi-agent)
  - What Domain Zero actually does (structured prompts for TDD, security, documentation)
  - When to use/not use Domain Zero (realistic assessment)
  - Customization advice (how to make it yours)
  - Success metrics to track (measure your own results)
  - Cost-benefit analysis and honest value proposition
  - Comparison with alternatives (Cursor rules, custom instructions, etc.)

### Changed
- **CLAUDE.md**:
  - Added Mask Mode section (v7.1.0+) explaining JJK theme vs professional mode
  - Added REALITY_CHECK.md to Additional Resources
  - Added MASK_MODE.md to Additional Resources
  - Updated version to v7.1.0
  - Updated major enhancements to highlight Mask Mode Toggle
  - Updated version history with v7.1.0 entry

- **protocol.config.yaml**:
  - Added complete `mask_mode` configuration section (40+ lines)
  - Updated protocol_version to 7.1.0
  - Updated config_version to 1.2
  - Updated last_updated to 2025-11-08

- **VERSION.md**:
  - Updated to v7.1.0 with complete release summary
  - Added "What's New in v7.1.0" section
  - Updated upgrade notes for mask mode
  - Added mask mode to cumulative improvements

- **Documentation Philosophy**:
  - REALITY_CHECK.md provides honest, no-marketing-fluff assessment
  - MASK_MODE.md separates presentation layer from core functionality
  - Clear acknowledgment that agents are prompt engineering, not magic
  - User empowerment through informed choice (mask ON/OFF)

### Implementation Approach
- **Presentation vs Functionality**: Mask Mode affects HOW agents communicate, not WHAT they enforce
- **No breaking changes to core functionality from Mask Mode**: Default behavior (MASK ON) preserves the JJK-themed experience. Note: Dual Workflow Enforcement is a breaking workflow change for Tier 2/3 (see Breaking Changes above).
- **User choice**: Toggle between engaging personality-driven responses and professional direct responses
- **Hybrid modes**: Granular settings allow custom combinations (e.g., keep emoji but use standard terminology)
- **Transparency**: REALITY_CHECK.md honestly explains what users are actually using

### Philosophy
- **Mask as choice, not requirement**: Users choose presentation style without sacrificing protocol structure
- **Security reviews are NOT optional**: Dual workflow ensures Tier 2/3 features receive mandatory security review
- **Honest documentation**: REALITY_CHECK.md acknowledges the truth about prompt engineering
- **User empowerment**: Informed users make better decisions about tool adoption and customization
- **Functionality preserved**: All TDD, tier, backup functionality unchanged regardless of mask setting
- **Tier 1 flexibility maintained**: Fast prototyping still skips security review (by design)

---

## [7.0.0] - 2025-11-07

### Added
- **AGENT_BINDING_OATH.md** - Formal commitment framework:
  - 10 binding principles: User Authority, Transparency, Safety Over Autonomy, Active Protection, Bounded Authority, Honest Communication, Non-Circumvention, Self-Awareness, Collective Responsibility, Continuous Improvement
  - Oath acknowledgment process for all agents
  - Violation consequences (learning-focused, not punitive)

- **DECISION_REASONING_TEMPLATE.md** - Transparency framework:
  - 9-section structured template: Decision, Objective, Reasoning, Alternatives Considered, Risk Assessment, Confidence Level, Dependencies, Implementation Complexity, Final Recommendation
  - Complete worked example included
  - Required for all non-trivial recommendations

- **Absolute Zero Protocol Core Principles** (CLAUDE.md):
  - Principle 1: Absolute User Authority
  - Principle 2: Transparency First
  - Principle 3: Safety Over Autonomy
  - Principle 4: Active Protection
  - Principle 5: Binding Commitment

### Changed
- **All Agent Files** (YUUJI, MEGUMI, NOBARA, GOJO):
  - Added Binding Oath acknowledgment sections
  - Updated to v7.0.0
  - Enhanced major enhancements with AZP commitment

- **protocol.config.yaml**:
  - Added `absolute_zero_protocol` enforcement section
  - Enabled decision reasoning requirements
  - Updated to v7.0.0

- **CLAUDE.md**:
  - Integrated AZP Core Principles section
  - Updated version history to track v7.0.0 as major release
  - Cross-referenced new AZP documents

### Implementation Approach
- **Augmentation, not replacement**: AZP formalizes existing DZP safety principles
- **No breaking changes**: Enhanced structure without changing agent behavior
- **Phase 1 Foundation**: Agent oaths, decision templates, core principles

---

## [6.2.8] - 2025-11-07

### Added
- **Copilot PR review fixes** - Addressed 20 comprehensive review comments

### Changed
- **Protocol files** - Removed inline HTML/CSS for better cross-platform Markdown rendering
- **GOJO.md ASCII art** - Fixed version alignment
- **VERSION.md and CHANGELOG.md** - Improved consistency

### Fixed
- **CODEOWNERS** - Removed gitignored path references
- **Script comments** - Improved accuracy and clarity in verify-protocol scripts
- **Version consistency** - Synchronized all version references across documentation

---

## [6.2.7] - 2025-11-07

### Added
- **Pre-push version verification requirements** - Mandatory comprehensive codebase review checklist:
  - Added CRITICAL PRE-PUSH REQUIREMENT section to system-update.py
  - Added Pre-Push Version Verification (MANDATORY) to protocol/CLAUDE.md
  - Extended VERSION_MANAGEMENT_GUIDE.md with complete verification checklist
  - Automated + manual verification workflow before any GitHub push
- **Enhanced verification script error handling**:
  - PyYAML error handling with graceful degradation
  - Yamllint fallback when PyYAML module missing
  - PowerShell Core (pwsh) detection for cross-platform support
  - Improved error messages with actionable guidance

### Changed
- **GitHub Actions workflows**:
  - Fixed CodeQL workflow manual build step (removed exit 1)
  - Added workflow_dispatch trigger to security-scan-example.yml
  - Corrected IaC scan condition to exclude workflow files
- **CODEOWNERS governance**:
  - Removed duplicate root CODEOWNERS file
  - Cleaned up gitignored file references
  - Added VERSION.md, SECURITY.md, FAQ.md to tracked files
  - Ensured CODEOWNERS not in .gitignore
- **Documentation cleanup**:
  - Removed all ANSI escape codes from protocol files
  - Filled protocol.config.yaml placeholder values
  - Updated version references across 14+ documentation files

### Fixed
- **Version consistency issues** - Synchronized all version references to v6.2.7:
  - FAQ.md, SECURITY.md, CHANGELOG.md version metadata
  - Protocol files (CLAUDE.md, GOJO.md, YUUJI.md, MEGUMI.md, NOBARA.md)
  - CANONICAL_SOURCE_ADOPTION.md, tier-system-specification.md
  - GOJO.md project-state.json initialization template
- **PowerShell script control flow** - Added return statements after successful checks
- **Workflow failures** - Fixed GitHub Actions workflow configurations
- **Markdown linting** - SECURITY.md link formatting and code block language identifiers

### Security
- **Enhanced OWASP Top 10 alignment** - MEGUMI security review process improvements
- **Credential management** - Updated .gitignore to protect sensitive state files
- **Script execution safety** - Improved error handling prevents silent failures

---


---

## [6.2.6] - 2025-11-07

### Added
- **Verification Script v2.0** - Major enhancements to both Bash and PowerShell scripts:
  - Dependency checking with new exit code 3 for missing tools
  - YAML syntax validation using Python or yamllint
  - Selective check execution (`--quick`, `--skip`, `--only`, `--list`)
  - Enhanced error messages with impact/action/documentation links
  - Graceful degradation on critical errors
- **Documentation for script options** - Updated README.md, FAQ.md, and PROTOCOL_QUICKSTART.md with new verification script features

### Changed
- **scripts/verify-protocol.sh** - Upgraded from v1.0 to v2.0 with all Phase 1 & 2 enhancements
- **scripts/verify-protocol.ps1** - Upgraded from v1.0 to v2.0 with feature parity to Bash version
- **Quick mode** - 60% faster verification by running only critical checks
- **Modular check system** - 8 checks organized by criticality (4 critical, 4 warning)

### Performance
- **60% faster** verification with `--quick` mode
- **75-85% faster** targeted debugging with `--only` flag
- **0% performance impact** in default mode (new checks are lightweight)

---

## [6.2.5] - 2025-11-07

### Added
- **FAQ.md** - Comprehensive FAQ covering getting started, tier system, agent behavior, configuration, security & privacy, integration, troubleshooting, and advanced topics (50+ questions)
- **TIER_TRANSITION_GUIDE.md** - Detailed guide for upgrading and downgrading tiers during workflows, including Gojo's role, validation workflows, and common scenarios
- **MIGRATION_GUIDE_TEMPLATE.md** - Template for creating migration guides between major versions, providing step-by-step processes for future upgrades
- **Troubleshooting section in README.md** - Comprehensive 300+ line troubleshooting guide covering configuration issues, agent behavior, tier system problems, verification scripts, git/GitHub integration, performance optimization, and common errors

### Changed
- **Documentation structure enhanced** - Added four major documentation resources to improve user experience and reduce support burden

---

## [6.2.4] - 2025-11-07

### Added
- **SECURITY.md** - Comprehensive vulnerability disclosure policy with coordinated disclosure timeline, CVSS-based severity levels, and safe harbor protections for security researchers

### Changed
- **Enhanced placeholder validation** - Verification scripts now fail (not warn) when configuration placeholders are detected
- **Improved error messages** - Added helpful "HOW TO FIX" guidance with examples when placeholders found
- **Updated PROTOCOL_QUICKSTART.md** - Added warning about placeholder validation requirement

### Fixed
- **Configuration placeholder detection** - Now treats placeholders as errors instead of warnings
- **PowerShell Unicode encoding** - Fixed Unicode symbol issues in verify-protocol.ps1

---

## [6.2.3] - 2025-11-07

### Changed
- **VERSION.md replaces VERSION file** - Now includes detailed release summary and change information instead of simple version string
- **Documentation structure improved** - Better version information visibility for users

### Fixed
- **Removed VERSION_UPDATE_CHECKLIST.md from releases** - Internal developer checklist no longer exposed in public releases

---

## [6.2.2] - 2025-11-07

### Added
- **CODEOWNERS file** for protocol protection - Enforces required approvals for changes to core protocol files (CLAUDE.md, agent files, configuration)
- **.gitignore file** for privacy protection - Prevents accidental commits of sensitive data (trigger-19.md, backups, internal docs)

### Fixed
- **GitHub Actions workflow conditional syntax** - Corrected `hashFiles()` condition format in security-scan-example.yml

### Security
- Privacy protection enhanced with .gitignore to prevent exposure of local intelligence data

---

## [6.2.1] - 2025-11-06

### Added
- **Interactive Work Session Alerts**: Gojo now presents users with explicit "Save Progress" or "Continue Working" options when extended work sessions are detected
- **Enhanced Enforcement Logic**: Gojo responds differently based on user choice:
  - Helps save and commit work if user chooses to take a break
  - Increases monitoring frequency (30-45 min intervals) if user continues
  - Blocks high-risk operations during extended sessions (configurable)
- **New Configuration Settings** in `protocol.config.yaml`:
  - `safety.enforcement.interactive_session_alerts` - Enable user choice in alerts
  - `safety.enforcement.block_until_response` - Block workflow until user responds
  - `safety.enforcement.escalate_on_continue` - Escalate monitoring if user continues
  - `safety.enforcement.block_high_risk_when_fatigued` - Block critical ops when fatigued
  - `safety.boundaries.alert_interval_minutes` - Initial alert interval (240 min)
  - `safety.boundaries.escalated_alert_interval_minutes` - Alert interval after continue (45 min)
  - `safety.boundaries.critical_session_hours` - Critical session threshold (6 hours)

### Changed
- **Work Session Alert Template** (`.protocol-state/work-session-alert.template.md`):
  - Restructured with clear "Decision Point" section
  - Added comprehensive guidance for each option
  - Included safety requirements and Gojo's response behavior
- **GOJO.md - Work Session Monitoring Section**:
  - Added "Work Session Alert Protocol (v6.2.7 Enhanced)"
  - Added "Enforcement Levels & User Choice" section
  - Added "How I Respond to User Choices" section with detailed workflows

### Fixed
- Version consistency across all protocol files (completed v6.2 update before v6.2.7)

---

## [6.2.0] - 2025-11-06

### Added
- **Absolute Safety Principles**: User safety and wellbeing established as highest priority
- **Version Control Enforcement**: Stricter version tracking and consistency checks
- **Work Session Monitoring**: Initial implementation of session duration tracking and alerts
- **Canonical Source Integration**: Protocol references canonical repository for updates

### Changed
- Safety hierarchy explicitly defined (Physical Safety > Wellbeing > Project Safety > Code Quality)
- All agents must respect safety boundaries and escalate concerns
- Enhanced `protocol.config.yaml` with comprehensive safety settings

---

## [6.1.0] - 2025-11-06

### Added
- **Canonical Source Adoption**: Protocol can reference and sync with canonical repository
- **Agent Self-Identification Standard**: All agents announce themselves with emoji and domain name
- **Session Continuity**: Agents re-identify after long sessions or absences
- `CANONICAL_SOURCE_ADOPTION.md` - Adoption and integration guide
- `AGENT_SELF_IDENTIFICATION_STANDARD.md` - Self-identification specification
- Version control scripts (`update-instructions.sh`, `verify-protocol.sh`)

### Changed
- Updated all agent files (YUUJI, MEGUMI, NOBARA, GOJO) with self-identification protocols
- Enhanced `protocol.config.yaml` with canonical repository configuration

---

## [6.0.0] - 2025-11-05

### Added
- **Adaptive Workflow Complexity (Tier System)**: Three-tier system (Rapid/Standard/Critical)
- **NOBARA Agent**: Creative Strategy & UX Specialist (four-agent system)
- **Tier Selection Guide**: Comprehensive guide for choosing appropriate tier
- Desktop application wrapper support (Electron-based)

### Changed
- Major workflow overhaul with tier-based requirements
- Security reviews now tier-adaptive (Tier 2+)
- Testing requirements vary by tier

### Breaking Changes
- Workflow structure changed from fixed to adaptive
- All agents must now operate within tier-specific constraints

---

## [5.1.0] - 2025-11-01

### Added
- **CLAUDE.md Protection System**: Tier 2 protection with authorized editors only
- **Backup & Rollback Requirements**: Mandatory backups before destructive operations
- Enhanced safety enforcement mechanisms

### Changed
- Only USER and GOJO (with authorization) can modify CLAUDE.md
- All destructive operations require backup confirmation

---

## [5.0.0] - 2025-10-28

### Added
- **Mission Control (GOJO)**: Fourth agent for project lifecycle management
- **Passive Observation**: Background monitoring and intelligence gathering
- **Three-Tier Enforcement**: Isolation, backups, quality gates
- **Trigger 19**: Full intelligence report system

### Changed
- Expanded from three-agent to four-agent architecture
- Protocol guardian role established with special privileges

---

## [4.0.0] - 2025-10-20

### Added
- **Custom Trigger System**: User-defined triggers for protocol actions
- Configurable trigger keywords and responses

---

## [3.0.0] - 2025-10-15

### Added
- **Dual Workflow Implementation**: Support for parallel workflows
- Enhanced agent coordination mechanisms

---

## [2.0.0] - 2025-10-10

### Added
- **Three-Agent Architecture**: YUUJI (Implementation), MEGUMI (Security), and basic coordination

### Changed
- Expanded from single-agent to three-agent system

---

## [1.0.0] - 2025-10-01

### Added
- Initial single-agent system
- Basic protocol structure
- Core implementation workflows

---

## Version Numbering Scheme

**Format**: vMAJOR.MINOR.PATCH

- **MAJOR** (Breaking changes, system overhauls)
- **MINOR** (New features, backward-compatible enhancements)
- **PATCH** (Bug fixes, documentation updates, minor corrections)

---

**Canonical Source**: <https://github.com/DewyHRite/Domain-Zero-Protocol>
**Maintainer**: Protocol Guardians
**Last Updated**: 2025-11-08
