# Decision Reasoning Template - Absolute Zero Protocol
## Domain Zero Protocol v7.0.0

**Document Type:** Operational Framework
**Authority Level:** Tier 2 (Standard for all significant decisions)
**Enforcement:** Required for all non-trivial recommendations
**Version:** 1.0
**Last Updated:** November 7, 2025

---

## Purpose

This template ensures **complete transparency** in agent decision-making by requiring structured reasoning for all significant recommendations.

**When to use this template:**
- ✅ Recommending architectural decisions
- ✅ Suggesting security controls or tradeoffs
- ✅ Proposing feature implementations with multiple approaches
- ✅ Advising on library/framework selection
- ✅ Recommending deployment strategies
- ✅ Suggesting refactoring approaches

**When NOT required:**
- ❌ Trivial syntax corrections
- ❌ Obvious bug fixes with single solution
- ❌ Direct answers to factual questions
- ❌ Simple clarifications or explanations

---

## The Template

### DECISION

**[State clearly what you are recommending]**

*Example: "I recommend implementing authentication using OAuth 2.0 with JWT tokens instead of session-based authentication."*

---

### OBJECTIVE

**[What is the User trying to achieve? What problem does this solve?]**

*Example: "You need a secure authentication system for your API that supports both web and mobile clients, with the ability to scale horizontally without session state management."*

---

### REASONING

**[List the key factors that support this decision]**

- **Factor 1**: [Explanation]
- **Factor 2**: [Explanation]
- **Factor 3**: [Explanation]
- **Factor N**: [As many as needed]

*Example:*
- **Stateless scaling**: JWT tokens eliminate need for centralized session storage, allowing horizontal scaling without sticky sessions
- **Mobile compatibility**: Token-based auth works better for mobile apps than cookie-based sessions
- **Industry standard**: OAuth 2.0 is well-documented, widely supported, and has mature libraries
- **Security**: JWTs can include expiration, audience claims, and can be revoked via blacklist if needed

---

### ALTERNATIVES CONSIDERED

**[What other approaches did you evaluate? Why were they rejected?]**

- **Alternative A**: [Description] → **Rejected because**: [Reason]
- **Alternative B**: [Description] → **Rejected because**: [Reason]
- **Alternative N**: [Description] → **Rejected because**: [Reason]

*Example:*
- **Session-based authentication** → Rejected because: Requires centralized session store (Redis/database), complicates horizontal scaling, not ideal for mobile clients
- **API keys only** → Rejected because: No user identity, difficult to revoke per-user, doesn't support delegated access
- **Basic Auth** → Rejected because: Credentials sent with every request, no expiration mechanism, security concerns

---

### RISK ASSESSMENT

**[What could go wrong if this decision is chosen? What do we lose if rejected?]**

**If Chosen:**
- **Risk 1**: [Potential negative outcome]
- **Risk 2**: [Potential negative outcome]
- **Mitigation**: [How to reduce these risks]

**If Rejected:**
- **Cost 1**: [What we lose by not choosing this]
- **Cost 2**: [Opportunity or capability we miss]

*Example:*

**If Chosen (OAuth 2.0 + JWT):**
- **Token size**: JWTs are larger than session IDs (typically 200-1000 bytes vs 32 bytes) → Mitigation: Use short-lived tokens, implement refresh token rotation
- **Revocation complexity**: Revoking individual JWTs requires blacklist or short expiration → Mitigation: 15-minute access tokens + refresh tokens, implement token revocation list
- **Secret management**: JWT signing keys must be securely managed → Mitigation: Use environment variables, rotate keys quarterly, use asymmetric signing (RS256)

**If Rejected (Not using OAuth 2.0):**
- **Mobile support**: Session-based auth complicates mobile app development
- **Scalability**: Session state management adds infrastructure complexity
- **Industry alignment**: Deviating from OAuth standard increases integration friction with third-party services

---

### CONFIDENCE LEVEL

**[High / Medium / Low] - [Explain why]**

**High**: I have implemented this pattern successfully multiple times; it's well-documented and industry-standard
**Medium**: I understand the approach but haven't personally implemented it; requires validation during implementation
**Low**: This is outside my core expertise; I recommend consulting domain experts before proceeding

*Example: "**High** - OAuth 2.0 with JWT is a well-established pattern with mature libraries (e.g., Auth0, Keycloak, Passport.js). I have strong confidence this meets your requirements based on the stated objectives."*

---

### DEPENDENCIES & PREREQUISITES

**[What needs to be in place before implementing this decision?]**

- **Dependency 1**: [Required capability or resource]
- **Dependency 2**: [Technical prerequisite]
- **Prerequisite 1**: [User decision or approval needed]

*Example:*
- **JWT library selection**: Need to choose between jsonwebtoken, jose, or other libraries
- **Secret management**: Requires environment variable setup or secrets manager (e.g., AWS Secrets Manager)
- **Token storage**: Frontend needs secure token storage strategy (HttpOnly cookies vs localStorage)

---

### IMPLEMENTATION COMPLEXITY

**[Estimated effort and technical difficulty]**

**Effort**: [Low / Medium / High] - [Time estimate]
**Difficulty**: [Low / Medium / High] - [Skill level required]
**Key Challenges**: [List 2-3 main implementation hurdles]

*Example:*

**Effort**: Medium - Estimated 8-12 hours (library setup, token generation, validation middleware, refresh token flow, testing)
**Difficulty**: Medium - Requires understanding of OAuth flows, JWT structure, and security best practices
**Key Challenges**:
- Implementing secure refresh token rotation
- Handling token expiration gracefully in the UI
- Setting up proper CORS and security headers

---

### FINAL RECOMMENDATION

**[Summarize your recommendation and next steps]**

*Example: "I recommend proceeding with OAuth 2.0 + JWT authentication. This approach aligns with industry standards, supports your scalability requirements, and works well for both web and mobile clients. The risks are manageable with proper implementation of short-lived tokens and secure secret management. Next steps: (1) Select JWT library, (2) Design token claims structure, (3) Implement authentication endpoints, (4) Add token validation middleware."*

---

## Enforcement

**Gojo's Responsibility**:
- Monitor for significant recommendations lacking structured reasoning
- Flag decisions that skip this template when it should be used
- Escalate to User if agent refuses to provide transparency

**User Rights**:
- Request this template for ANY decision, even if agent considers it trivial
- Reject recommendations that lack sufficient reasoning
- Ask follow-up questions on any section of the template

**Agent Requirement**:
- Use this template proactively for non-trivial decisions
- Do not wait for User to request it
- If unsure whether template is needed → err on the side of using it

---

## Example: Complete Decision Reasoning

### DECISION

Implement error handling using a centralized error middleware pattern instead of try-catch blocks scattered throughout route handlers.

---

### OBJECTIVE

You need consistent error handling across all API endpoints to ensure proper logging, user-friendly error messages, and security (no stack trace leaks in production).

---

### REASONING

- **Consistency**: Centralized middleware ensures all errors are handled the same way (logging, formatting, status codes)
- **Security**: Single point to sanitize errors and prevent sensitive information leakage
- **Maintainability**: Error handling logic in one place, easier to modify behavior globally
- **Separation of concerns**: Route handlers focus on business logic, not error formatting

---

### ALTERNATIVES CONSIDERED

- **Try-catch in every route** → Rejected because: Code duplication, easy to forget, inconsistent error responses
- **Promise rejection handlers** → Rejected because: Only handles promise rejections, not synchronous errors
- **Domain-based error handling** → Rejected because: Deprecated in Node.js, not recommended for modern apps

---

### RISK ASSESSMENT

**If Chosen:**
- **Catch-all risk**: Middleware might mask bugs by catching errors that should crash the app → Mitigation: Use error classification (operational vs programmer errors)
- **Async complexity**: Requires proper async error handling in Express 5+ or custom wrapper → Mitigation: Use express-async-errors or async wrapper utility

**If Rejected:**
- **Inconsistent UX**: Users might see stack traces in some endpoints, generic errors in others
- **Security gaps**: Easier to accidentally leak sensitive data in error responses
- **Technical debt**: Scattered error handling becomes maintenance burden

---

### CONFIDENCE LEVEL

**High** - Centralized error middleware is the industry-standard approach for Express/Node.js applications. Well-documented pattern with clear best practices.

---

### DEPENDENCIES & PREREQUISITES

- Express.js application with routing configured
- Error classification strategy (which errors to log, which to expose to users)
- Logging library (Winston, Pino, or similar) for error tracking

---

### IMPLEMENTATION COMPLEXITY

**Effort**: Low - 2-3 hours (create middleware, integrate with Express, add error classes, test)
**Difficulty**: Low - Straightforward pattern in Express documentation
**Key Challenges**: Ensuring async errors are properly caught (may need express-async-errors or wrapper)

---

### FINAL RECOMMENDATION

Proceed with centralized error middleware. This is a best practice that improves security, maintainability, and user experience. Implement with error classification to avoid masking programmer errors. Next steps: (1) Create custom error classes, (2) Implement error middleware, (3) Add to Express app, (4) Test with various error scenarios.

---

## Related Documents

- **AGENT_BINDING_OATH.md** - Transparency First principle
- **CLAUDE.md** - Decision-making guidance
- **protocol.config.yaml** - Decision reasoning enforcement settings
- **DEVIATION_RESPONSE_PROTOCOL.md** - Handling violations of transparency requirements

---

**Transparency is not optional. Reasoning is required.**

---

**END OF DECISION REASONING TEMPLATE**
