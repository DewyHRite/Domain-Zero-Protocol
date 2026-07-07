<!-- [CORE FILE] - Domain Zero Protocol v9.9.2 -->
# Security Policy

## Scope

The Domain Zero Protocol security policy covers:

### In Scope
- **Protocol Specifications**: Security flaws in agent protocols (`CLAUDE.md` and `protocol/*.agent.md` — the 9 resident agents Gojo/Yuuji/Megumi/Nobara/Todo/Maki/Panda/Inumaki/Sukuna plus the Toji external auditor)
- **DZP Cortex (local semantic memory)**: Flaws in the on-device brain index (`.protocol-state/brain/cortex/`), its trust boundaries, secret-detection, access guards, or storage handling
- **Configuration Files**: Vulnerabilities in `protocol.config.yaml`, state templates, or AI instructions
- **Security Agent Logic**: Flaws in MEGUMI's OWASP Top 10 review process or security standards
- **Tier System**: Security bypasses or privilege escalation in tier enforcement
- **Authentication & Authorization**: Issues in agent identity verification or protocol authority enforcement
- **Workflow Automation**: Security risks in scripts (`scripts/verify-protocol.sh`, `scripts/verify-protocol.ps1`)
- **Documentation**: Security guidance errors or misleading security recommendations
- **State Management**: Information disclosure or tampering risks in `.protocol-state/`

### Out of Scope
- **Third-Party Integrations**: Security issues in Claude Code, GitHub Copilot, or other AI assistants (report to respective vendors)
- **User Projects**: Vulnerabilities in code generated using the protocol (user responsibility)
- **Infrastructure**: GitHub repository hosting, Actions, or Pages security (report to GitHub)
- **Theoretical Attacks**: Attacks requiring physical access, social engineering, or unpatched dependencies
- **AI Model Behavior**: Hallucinations, bias, or quality issues in AI responses (report to Anthropic/OpenAI)

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 9.8.x   | :white_check_mark: | Current stable release (security + bug fixes) |
| < 9.8.0 | :x:                | End of life (EOL) — upgrade to the latest 9.8.x release |

**Support Policy**: Only the **latest minor release line (currently 9.8.x)** receives security updates. All earlier versions are end-of-life.

**Upgrade Recommendation**: Users on any version below the current 9.8.x line should upgrade to the latest release immediately. See `VERSION.md` for the current version.

---

## Reporting a Vulnerability

### Preferred Method: Private Security Advisory (Recommended)

For sensitive security issues, use GitHub's private vulnerability reporting:

1. Navigate to: [GitHub Security Advisories](https://github.com/DewyHRite/Domain-Zero-Protocol/security/advisories)
2. Click "Report a vulnerability"
3. Fill out the advisory form with:
   - **Title**: Brief, non-sensational description (e.g., "Tier bypass in agent handoff logic")
   - **Description**: Detailed explanation of the vulnerability
   - **Impact**: Potential security consequences (confidentiality/integrity/availability)
   - **Affected Components**: Specific files, agents, or workflow steps
   - **Reproduction Steps**: Clear steps to reproduce the issue
   - **Suggested Fix** (optional): Proposed remediation approach

**Response Timeline**:
- **Initial Response**: Best effort (typically within 7 days)
- **Triage & Assessment**: Best effort (typically within 14 days)
- **Patch Development**: Depends on severity and complexity
- **Public Disclosure**: 90 days after initial report (or upon patch release, whichever is sooner)

### Alternative Method: GitHub Issues (Public Disclosure)

For low-severity issues or general security improvements:

1. Create a new issue: [New Issue](https://github.com/DewyHRite/Domain-Zero-Protocol/issues/new)
2. Use the `[SECURITY]` prefix in the title
3. Label the issue with `security` tag
4. Provide:
   - Affected component/file
   - Security concern description
   - Proposed improvement (if applicable)

**Use this method for**:
- Documentation clarifications
- Non-exploitable security hardening suggestions
- Best practice recommendations
- Security feature requests

**Response Timeline**:
- **Initial Response**: Best effort (typically within 14 days)
- **Resolution**: Included in next minor/patch release when available

### Emergency Contact

For critical vulnerabilities requiring immediate attention (e.g., active exploitation, data breach risk):

- **Email**: [GitHub Security Advisories](https://github.com/DewyHRite/Domain-Zero-Protocol/security/advisories)
- **GitHub**: Open an issue with `[SECURITY - URGENT]` prefix
- **Expected Response**: Best effort (prioritized over non-critical issues)
- **Definition of Critical**:
  - Remote code execution (RCE) in protocol scripts
  - Authentication bypass allowing unauthorized agent impersonation
  - Privilege escalation from Tier 1 to Tier 3 without proper authorization
  - Information disclosure of sensitive credentials or API keys

---

## Vulnerability Disclosure Timeline

We follow **coordinated disclosure** principles:

```text
Day 0:   Vulnerability reported via private advisory
Day 7:   Initial response & acknowledgment (best effort)
Day 14:  Triage completed, severity assigned (best effort)
Day 7-90: Patch development (based on severity and maintainer availability)
Day 90:  Public disclosure (CVE published, advisory made public)
```

**Early Disclosure**: We may disclose earlier if:
- A patch is available and tested
- The vulnerability is being actively exploited
- The reporter agrees to early disclosure

**Extended Timeline**: We may request extended timeline (up to 120 days) for:
- Complex vulnerabilities requiring architectural changes
- Issues affecting multiple versions
- Coordination with third-party dependencies
- Maintainer availability constraints

---

## Security Severity Levels

We use the following severity classification (based on CVSS 3.1):

| Severity | CVSS Score | Response Priority | Example |
|----------|-----------|-------------------|---------|
| **Critical** | 9.0-10.0 | Highest priority | RCE in protocol scripts, agent impersonation |
| **High** | 7.0-8.9 | High priority | Tier bypass, authentication weakness |
| **Medium** | 4.0-6.9 | Medium priority | Information disclosure, insecure defaults |
| **Low** | 0.1-3.9 | Low priority | Documentation errors, hardening opportunities |

**Note**: Response times are best effort and depend on maintainer availability. Critical issues will be prioritized.

---

## Safe Harbor

Domain Zero Protocol supports responsible security research under the following safe harbor guidelines:

### Protected Activities

You may:
- ✅ Test the Domain Zero Protocol against your own local installations
- ✅ Analyze protocol specifications, scripts, and configuration files for vulnerabilities
- ✅ Reverse-engineer protocol logic to understand security mechanisms
- ✅ Share findings privately via the reporting channels above

### Prohibited Activities

You must NOT:
- ❌ Access, modify, or delete data in third-party GitHub repositories using the protocol
- ❌ Conduct attacks against infrastructure hosting the protocol (GitHub, CDNs, etc.)
- ❌ Publicly disclose vulnerabilities before the 90-day disclosure window
- ❌ Extort, threaten, or demand compensation for vulnerability reports
- ❌ Test against production systems you do not own or have explicit permission to test

### Legal Protections

**If you comply with this policy**:
- We will not pursue legal action against you for security research activities
- We will work with you in good faith to understand and address the issue
- We will publicly acknowledge your contribution (if you wish) in release notes and advisories

**We reserve the right to**:
- Involve law enforcement for malicious or harmful activities
- Revoke safe harbor protections for policy violations

---

## Security Best Practices for Users

### Deployment Recommendations

1. **Credential Management**:
   - Never commit API keys, tokens, or credentials to version control
   - Use `.gitignore` to exclude `.protocol-state/trigger-19.md` and sensitive files
   - Rotate credentials regularly (every 90 days minimum)

2. **Tier System Enforcement**:
   - Always use Tier 3 for authentication, payment processing, or sensitive data handling
   - Never downgrade tier mid-workflow without explicit security review
   - Document tier selection rationale in `project-state.json`

3. **Agent Identity Verification**:
   - Verify agent self-identification using the canonical verification prompts
   - Use GOJO's Trigger 19 intelligence reports for security-critical decisions
   - Maintain audit logs of agent interactions in `dev-notes.md`

4. **Script Execution**:
   - Review `scripts/verify-protocol.sh` and `scripts/verify-protocol.ps1` before execution
   - Run protocol verification scripts in sandboxed environments
   - Use principle of least privilege for script permissions

5. **State File Protection**:
   - Restrict file permissions on `.protocol-state/` directory (0700 on Unix, ACLs on Windows)
   - Encrypt `trigger-19.md` if it contains sensitive threat intelligence
   - Backup state files before major protocol updates

### OWASP Top 10 Alignment

Domain Zero Protocol's security design addresses OWASP Top 10 (2021):

- **A01:2021 – Broken Access Control**: Tier system enforces least privilege
- **A02:2021 – Cryptographic Failures**: Megumi reviews crypto in Tier 3; DZP Cortex stores data on-device only (no cloud inference), with opt-in AES-256 encryption-at-rest available since v9.8.0 (SQLCipher + Argon2id/OS-keyring; disabled by default — see `brain encrypt` to enable)
- **A03:2021 – Injection**: YUUJI's TDD approach includes injection test cases
- **A04:2021 – Insecure Design**: NOBARA integrates security into UX design
- **A05:2021 – Security Misconfiguration**: `protocol.config.yaml` provides secure defaults
- **A06:2021 – Vulnerable Components**: Protocol encourages dependency scanning
- **A07:2021 – Authentication Failures**: Tier 3 mandates multi-model security review for auth
- **A08:2021 – Software Integrity Failures**: GOJO verifies protocol integrity
- **A09:2021 – Logging Failures**: `dev-notes.md` and `security-review.md` maintain audit trails
- **A10:2021 – SSRF**: MEGUMI's security checklist includes SSRF prevention

### Accepted Security Boundaries (Cortex Encryption-at-Rest)

Two residuals of DZP Cortex's opt-in encryption-at-rest (v9.8.0+) are **permanent, structural
boundaries** of the architecture, not open bugs or deferred work — no future patch closes them
without changing the underlying implementation:

- **Same-user malware can read the OS keystore.** The encryption key is cached in the per-user OS
  keystore (Windows Credential Manager / macOS Keychain / Linux Secret Service). Any process
  running as the *same OS user* has the same keystore access Cortex does — identical to the
  boundary every credential-manager-backed tool (browsers, git credential helpers, cloud CLIs)
  accepts. The mitigation is OS/endpoint hygiene, not a product control.
- **No in-memory key zeroization.** The resolved key is held in ordinary Python objects; CPython
  gives no guarantee that backing memory is wiped before garbage collection. True zeroization
  requires a language with manual memory control, which is out of scope for a cross-platform
  Python CLI.

Full threat-model rationale: `docs/superpowers/specs/2026-06-19-cortex-encryption-at-rest-design.md`
§12. Tracking: `.protocol-state/security-review.md:1922-1923` (Megumi @approved, non-blocking).

---

## Security Changelog

> Full version history is in `VERSION.md` and `CHANGELOG.md`; per-finding SEC-ID detail lives in
> `.protocol-state/security-review.md`. Below are the recent **security-relevant** releases.

### Recent security-relevant releases (9.x)
- **v9.8.1** — Cortex encryption migration user_version preservation (BUG-CORTEX-ENC-UV-001): `encrypt_brain()`/`decrypt_brain()` now capture + restore `PRAGMA user_version`; smoke-verify aborts on mismatch. Fixes silent `availability: unavailable` on any v9.8.0 encrypted brain.
- **v9.8.0** — Cortex encryption-at-rest (PLAN-CORTEX-ENC-001): opt-in SQLCipher AES-256 with Argon2id/OS-keyring key management; reversible backup-first migration; SEC-CORTEX-ENC-001..009 CLOSED
- **v9.7.2** — Cortex memory-keying silent data-loss fix (SEC-CORTEX-MEM-001) + content-addressed migration hardening
- **v9.7.1** — Cortex Access Hardening (CIA-triad): anti-destruction guard on shared brains, pre-op backups + `PRAGMA integrity_check`, graceful degradation (SEC-CORTEX-ACCESS-008/009/010)
- **v9.4.1** — Protected-document append-only enforcement (FEAT-GUARD-001): pre-commit byte-prefix guard on `dev-notes.md` / `security-review.md` / `domain.record.md`
- **v9.3.2 – v9.3.4** — Cortex trust-boundary default-deny, placeholder-aware secret detection, and a fail-closed schema-version guard
- **v9.1.0** — DZP Cortex local semantic memory introduced (on-device only; no cloud inference)
- **v9.0.0** — Distro publish architecture: identity/PII scrub + content-PII audit + version-consistency gate for every published release

### Earlier history
- **8.x** — Nine-agent system, Kill Switch protocol, Custom Agent Security Framework, Tier Validation, Toji external auditor
- **6.x – 7.x** — Initial public release, coordinated-disclosure policy, CVSS severity levels, safe-harbor protections, Tier-3 security review (EOL)

---

## Attribution & Recognition

We believe in recognizing security researchers who help improve Domain Zero Protocol.

### Hall of Fame

Security researchers who responsibly disclose vulnerabilities will be acknowledged here (with permission):

- *No vulnerabilities reported yet*

### Acknowledgment Preferences

When reporting, please indicate:
- [ ] I want public acknowledgment (name/handle listed in Hall of Fame)
- [ ] I want anonymous acknowledgment ("Anonymous researcher")
- [ ] I do not want acknowledgment

---

## Contact Information

- **Security Email**: [GitHub Security Advisories](https://github.com/DewyHRite/Domain-Zero-Protocol/security/advisories) (for critical/private reports)
- **Security Advisories**: [GitHub Security Advisories](https://github.com/DewyHRite/Domain-Zero-Protocol/security/advisories)
- **Public Issues**: [GitHub Issues](https://github.com/DewyHRite/Domain-Zero-Protocol/issues)
- **Project Repository**: [Domain Zero Protocol Repository](https://github.com/DewyHRite/Domain-Zero-Protocol)
- **Documentation**: See `README.md` and `PROTOCOL_QUICKSTART.md`

---

## Policy Updates

This security policy is versioned alongside the Domain Zero Protocol:

- **Current Version**: 1.5.0 (matches Domain Zero Protocol v9.9.2)
- **Last Updated**: July 4, 2026
- **Next Review**: Upon the next minor/major protocol update

Changes to this policy will be documented in `CHANGELOG.md` and announced via GitHub releases.

---

**Thank you for helping keep Domain Zero Protocol secure!**

We deeply appreciate the security research community's contributions to making AI-assisted development safer and more reliable.
