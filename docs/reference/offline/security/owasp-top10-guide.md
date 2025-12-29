# OWASP Top 10 Security Guide
<!-- Domain Zero Protocol v8.11.0 - Offline Reference -->

**Agent**: Megumi (Security Analyst)
**Last Updated**: 2025-12-26
**Source**: [OWASP Top 10](https://owasp.org/Top10/)

---

## Table of Contents

1. [A01: Broken Access Control](#a01-broken-access-control)
2. [A02: Cryptographic Failures](#a02-cryptographic-failures)
3. [A03: Injection](#a03-injection)
4. [A04: Insecure Design](#a04-insecure-design)
5. [A05: Security Misconfiguration](#a05-security-misconfiguration)
6. [A06: Vulnerable Components](#a06-vulnerable-and-outdated-components)
7. [A07: Authentication Failures](#a07-identification-and-authentication-failures)
8. [A08: Software and Data Integrity Failures](#a08-software-and-data-integrity-failures)
9. [A09: Security Logging Failures](#a09-security-logging-and-monitoring-failures)
10. [A10: Server-Side Request Forgery](#a10-server-side-request-forgery-ssrf)

---

## A01: Broken Access Control

**Risk**: Unauthorized users access restricted functionality or data.

### Common Vulnerabilities

1. **Insecure Direct Object References (IDOR)**
   ```python
   # VULNERABLE
   @app.get("/api/users/{user_id}")
   def get_user(user_id: int):
       return db.get_user(user_id)  # No authorization check

   # SECURE
   @app.get("/api/users/{user_id}")
   def get_user(user_id: int, current_user: User = Depends(get_current_user)):
       if current_user.id != user_id and not current_user.is_admin:
           raise HTTPException(403, "Access denied")
       return db.get_user(user_id)
   ```

2. **Missing Function-Level Access Control**
   ```python
   # VULNERABLE - no role check
   @app.post("/api/admin/users")
   def create_user(user_data: UserCreate):
       return db.create_user(user_data)

   # SECURE
   @app.post("/api/admin/users")
   @require_role("admin")
   def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
       return db.create_user(user_data)
   ```

3. **Path Traversal**
   ```python
   # VULNERABLE
   @app.get("/files/{filename}")
   def get_file(filename: str):
       return open(f"/uploads/{filename}")  # ../../etc/passwd

   # SECURE
   @app.get("/files/{filename}")
   def get_file(filename: str):
       safe_path = os.path.realpath(os.path.join("/uploads", filename))
       if not safe_path.startswith("/uploads/"):
           raise HTTPException(400, "Invalid path")
       return open(safe_path)
   ```

### Prevention

- Deny by default (except public resources)
- Implement access control once, reuse everywhere
- Enforce record ownership
- Disable directory listing
- Log access control failures
- Rate limit API access

---

## A02: Cryptographic Failures

**Risk**: Sensitive data exposed due to weak or missing encryption.

### Common Vulnerabilities

1. **Transmitting Data in Clear Text**
   ```python
   # VULNERABLE - HTTP
   requests.post("http://api.example.com/login", data=credentials)

   # SECURE - HTTPS with certificate verification
   requests.post("https://api.example.com/login", data=credentials, verify=True)
   ```

2. **Weak Hashing Algorithms**
   ```python
   # VULNERABLE
   import hashlib
   password_hash = hashlib.md5(password.encode()).hexdigest()

   # SECURE
   import bcrypt
   password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
   ```

3. **Hardcoded Secrets**
   ```python
   # VULNERABLE
   API_KEY = "sk-1234567890abcdef"

   # SECURE
   import os
   API_KEY = os.environ.get("API_KEY")
   ```

### Prevention

- Use TLS 1.2+ for all data transmission
- Encrypt sensitive data at rest (AES-256)
- Use strong password hashing (bcrypt, Argon2, scrypt)
- Use authenticated encryption (AES-GCM)
- Never store secrets in code
- Rotate keys regularly
- Disable caching for sensitive responses

### Secure Encryption Example

```python
from cryptography.fernet import Fernet

# Generate and store key securely
key = Fernet.generate_key()

def encrypt_data(data: str) -> bytes:
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted).decode()
```

---

## A03: Injection

**Risk**: Untrusted data sent to interpreter as part of a command or query.

### SQL Injection

```python
# VULNERABLE
def get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)  # ' OR '1'='1' --

# SECURE - Parameterized queries
def get_user(username):
    query = "SELECT * FROM users WHERE username = ?"
    return db.execute(query, (username,))

# SECURE - ORM
def get_user(username):
    return User.query.filter_by(username=username).first()
```

### Command Injection

```python
# VULNERABLE
def ping_host(host):
    os.system(f"ping -c 1 {host}")  # ; rm -rf /

# SECURE - Avoid shell
import subprocess
def ping_host(host):
    # Validate input
    if not re.match(r'^[\w.-]+$', host):
        raise ValueError("Invalid host")
    subprocess.run(["ping", "-c", "1", host], capture_output=True)
```

### XSS (Cross-Site Scripting)

```javascript
// VULNERABLE
element.innerHTML = userInput;

// SECURE
element.textContent = userInput;

// OR use sanitization library
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### Prevention

- Use parameterized queries/prepared statements
- Use ORMs with care (still validate input)
- Validate and sanitize all input
- Escape output based on context
- Use Content Security Policy (CSP)
- Apply principle of least privilege

---

## A04: Insecure Design

**Risk**: Missing or ineffective security controls due to design flaws.

### Threat Modeling

Use STRIDE methodology:
- **S**poofing - Can someone impersonate a user?
- **T**ampering - Can data be modified?
- **R**epudiation - Can actions be denied?
- **I**nformation Disclosure - Can data leak?
- **D**enial of Service - Can the system be overwhelmed?
- **E**levation of Privilege - Can users gain unauthorized access?

### Secure Design Patterns

```python
# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/login")
@limiter.limit("5/minute")
def login(credentials: LoginRequest):
    pass

# Input validation with schemas
from pydantic import BaseModel, validator, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        return v
```

### Prevention

- Integrate security in design phase
- Use threat modeling
- Implement defense in depth
- Limit resource consumption
- Segregate tenants/users
- Use secure design patterns

---

## A05: Security Misconfiguration

**Risk**: Insecure default configurations, incomplete setups, or exposed sensitive data.

### Common Issues

1. **Debug Mode in Production**
   ```python
   # VULNERABLE
   app.run(debug=True)  # Exposes stack traces

   # SECURE
   app.run(debug=os.environ.get("DEBUG", "false").lower() == "true")
   ```

2. **Missing Security Headers**
   ```python
   # Add security headers
   @app.after_request
   def add_security_headers(response):
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
       response.headers['Content-Security-Policy'] = "default-src 'self'"
       return response
   ```

3. **Default Credentials**
   ```yaml
   # Check and change defaults
   database:
     user: admin          # CHANGE
     password: admin123   # CHANGE
   ```

### Prevention

- Automate hardening process
- Remove unused features/frameworks
- Review and update configurations
- Implement security headers
- Use infrastructure as code
- Regular security audits

---

## A06: Vulnerable and Outdated Components

**Risk**: Using components with known vulnerabilities.

### Detection

```bash
# Python
pip-audit
safety check

# JavaScript
npm audit
yarn audit

# Check specific CVEs
pip-audit --vulnerability-service osv

# Automated in CI
name: Security Scan
on: [push, pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip-audit
```

### Prevention

- Maintain inventory of dependencies
- Monitor CVE databases
- Use automated scanning in CI/CD
- Update dependencies regularly
- Remove unused dependencies
- Only use official sources

### Dependency Management

```toml
# pyproject.toml - Pin versions
[tool.poetry.dependencies]
django = "^4.2.0"  # Allow minor updates
requests = "2.31.0"  # Pin exact version for critical deps
```

---

## A07: Identification and Authentication Failures

**Risk**: Weak authentication mechanisms allowing unauthorized access.

### Secure Authentication

```python
# Password hashing
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Session management
from flask import session
import secrets

app.secret_key = secrets.token_hex(32)

@app.route('/login', methods=['POST'])
def login():
    if authenticate_user(request.form):
        session.regenerate()  # Prevent session fixation
        session['user_id'] = user.id
        session.permanent = True
        return redirect('/dashboard')
```

### Multi-Factor Authentication

```python
import pyotp

# Generate TOTP secret
secret = pyotp.random_base32()

# Verify TOTP code
def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
```

### Prevention

- Use MFA for sensitive operations
- Implement account lockout
- Use secure session management
- Hash passwords with bcrypt/Argon2
- Avoid default credentials
- Implement secure password recovery
- Log authentication failures

---

## A08: Software and Data Integrity Failures

**Risk**: Code and infrastructure without integrity verification.

### Secure CI/CD

```yaml
# GitHub Actions with signed commits
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # Verify commit signatures
      - name: Verify commits
        run: |
          git log --show-signature HEAD~5..HEAD

      # Use pinned action versions
      - uses: actions/setup-python@v5.0.0
        with:
          python-version: '3.12'
```

### Subresource Integrity

```html
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
        crossorigin="anonymous"></script>
```

### Prevention

- Use digital signatures for updates
- Verify dependency integrity
- Implement code review process
- Use signed commits
- Secure CI/CD pipeline
- Separate build and deploy permissions

---

## A09: Security Logging and Monitoring Failures

**Risk**: Insufficient logging prevents detection of attacks.

### Comprehensive Logging

```python
import logging
import json
from datetime import datetime

# Structured logging
class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)

    def log_event(self, event_type: str, user_id: str, details: dict):
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string,
            **details
        }
        self.logger.info(json.dumps(event))

security_log = SecurityLogger()

# Log authentication events
@app.route('/login', methods=['POST'])
def login():
    result = authenticate(request.form)
    security_log.log_event(
        'LOGIN_ATTEMPT',
        request.form.get('username'),
        {'success': result.success, 'method': 'password'}
    )
```

### What to Log

- Authentication successes and failures
- Authorization failures
- Input validation failures
- Application errors and exceptions
- Admin activities
- Data access patterns
- Security configuration changes

### Prevention

- Log all security-relevant events
- Use structured logging (JSON)
- Protect logs from tampering
- Set up real-time alerting
- Implement log retention policy
- Regular log review

---

## A10: Server-Side Request Forgery (SSRF)

**Risk**: Application fetches a URL without validating user input.

### SSRF Example

```python
# VULNERABLE
@app.get("/fetch")
def fetch_url(url: str):
    return requests.get(url).text  # http://localhost:8080/admin

# SECURE
import ipaddress
from urllib.parse import urlparse

ALLOWED_HOSTS = {'api.example.com', 'cdn.example.com'}

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)

    # Only allow HTTPS
    if parsed.scheme != 'https':
        return False

    # Check against allowlist
    if parsed.hostname not in ALLOWED_HOSTS:
        return False

    # Block internal IPs
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback:
            return False
    except ValueError:
        pass  # Not an IP address

    return True

@app.get("/fetch")
def fetch_url(url: str):
    if not is_safe_url(url):
        raise HTTPException(400, "URL not allowed")
    return requests.get(url, timeout=5).text
```

### Prevention

- Validate and sanitize all URLs
- Use allowlists for remote resources
- Block requests to internal networks
- Disable HTTP redirects or validate destinations
- Don't expose raw responses to users

---

## Quick Reference

### Security Headers Checklist

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=()
```

### Input Validation Rules

| Data Type | Validation |
|-----------|------------|
| Email | RFC 5322 format |
| URL | Allowlist domains |
| Integer | Range check |
| String | Length + allowlist chars |
| File | Extension + MIME + size |
| HTML | Sanitize with DOMPurify |

### Password Requirements

- Minimum 12 characters
- No maximum length (within reason)
- Allow all characters including Unicode
- Check against breached password lists
- No composition rules (uppercase, numbers, etc.)

---

**Online References**:
- [OWASP Top 10](https://owasp.org/Top10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
