# Template: JWT Authentication

## Overview

**Feature**: Stateless authentication using JSON Web Tokens (JWT) for REST APIs

**Use Case**: Secure API authentication where users login with credentials and receive a token to access protected endpoints.

**Technology Stack**:
- Backend: Python (FastAPI), Node.js (Express), or any REST framework
- JWT Library: PyJWT (Python), jsonwebtoken (Node.js)
- Password Hashing: bcrypt

**Estimated Time**:
- Implementation: 2-3 hours
- Testing: 1-2 hours
- Security Review: 30-45 minutes
- **Total**: 3.5-5.5 hours

---

## Prerequisites

Before implementing JWT authentication, ensure:

- ✅ User model exists in database with username/email and password fields
- ✅ Password hashing library installed (bcrypt recommended)
- ✅ JWT library installed (PyJWT for Python, jsonwebtoken for Node.js)
- ✅ Environment variable system configured (.env file)
- ✅ Database connection working
- ✅ Basic REST API framework set up (FastAPI, Express, Django, etc.)

---

## Yuuji Implementation Checklist

### Phase 1: Setup & Dependencies (30 minutes)

- [ ] Install required dependencies
  - `pip install pyjwt bcrypt python-dotenv` (Python)
  - `npm install jsonwebtoken bcrypt dotenv` (Node.js)
- [ ] Create `.env` file with JWT secret
  - `JWT_SECRET=your-super-secret-key-change-me`
  - `JWT_ALGORITHM=HS256`
  - `JWT_EXPIRY_MINUTES=15`
- [ ] Verify `.env` is in `.gitignore` (CRITICAL)
- [ ] Create backup before proceeding

### Phase 2: JWT Utility Functions (1 hour)

- [ ] **Create JWT utility module** (`utils/jwt_handler.py` or `utils/jwtHandler.js`)

  **Functions needed**:
  - `generate_token(user_id, username)` → Returns JWT string
  - `decode_token(token)` → Returns payload or raises error
  - `verify_token(token)` → Returns True/False with user data

- [ ] **Write tests for JWT utilities** (TDD approach)
  - Test: Generate token successfully
  - Test: Decode valid token
  - Test: Reject expired token
  - Test: Reject invalid signature
  - Test: Reject malformed token

### Phase 3: Authentication Endpoints (1.5 hours)

- [ ] **POST /auth/login** - User authentication endpoint

  **Requirements**:
  - Accept `username` and `password` in request body
  - Validate credentials against database
  - Hash password and compare with stored hash
  - Return JWT token on success
  - Return 401 on invalid credentials
  - Rate limit: 5 attempts per minute

- [ ] **POST /auth/refresh** (Optional but recommended)
  - Accept refresh token
  - Issue new access token
  - Invalidate old refresh token

- [ ] **POST /auth/logout** (Optional)
  - Blacklist token (requires Redis or token store)

- [ ] **Write tests for authentication endpoints**
  - Test: Successful login returns token
  - Test: Invalid password returns 401
  - Test: Non-existent user returns 401
  - Test: Missing fields return 400
  - Test: Rate limiting works

### Phase 4: Token Validation Middleware (1 hour)

- [ ] **Create authentication middleware** (`middleware/auth_middleware.py`)

  **Requirements**:
  - Extract token from `Authorization: Bearer <token>` header
  - Validate token using JWT utility
  - Attach user data to request object
  - Return 401 if token missing or invalid
  - Return 403 if token expired

- [ ] **Apply middleware to protected routes**
  - Example: `@requires_auth` decorator (Python)
  - Example: `authenticateToken` middleware (Express)

- [ ] **Write tests for middleware**
  - Test: Valid token allows access
  - Test: Missing token returns 401
  - Test: Invalid token returns 401
  - Test: Expired token returns 403
  - Test: Malformed header returns 401

### Phase 5: Integration & Documentation (30 minutes)

- [ ] Create protected endpoint example (`GET /api/protected`)
- [ ] Update API documentation with authentication flow
- [ ] Document token format and expiry
- [ ] Create rollback plan in dev-notes.md
- [ ] Tag @user-review when complete

---

## Code Template

### Python (FastAPI) Implementation

```python
# utils/jwt_handler.py
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 15))

def generate_token(user_id: int, username: str) -> str:
    """Generate JWT token for authenticated user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[Dict]:
    """Decode and verify JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def verify_token(token: str) -> tuple[bool, Optional[Dict]]:
    """Verify token and return (is_valid, payload)."""
    payload = decode_token(token)
    if payload:
        return True, payload
    return False, None


# routes/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel
import bcrypt
from utils.jwt_handler import generate_token, verify_token
from database import get_user_by_username  # Your DB function

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Authenticate user and return JWT token."""

    # Get user from database
    user = get_user_by_username(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    password_valid = bcrypt.checkpw(
        credentials.password.encode('utf-8'),
        user.password_hash.encode('utf-8')
    )
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate token
    token = generate_token(user.id, user.username)

    return LoginResponse(access_token=token)


# middleware/auth_middleware.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from utils.jwt_handler import verify_token

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    """Dependency to validate JWT and return current user."""
    token = credentials.credentials
    is_valid, payload = verify_token(token)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return payload  # Contains user_id and username


# Example protected route
@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """Example protected endpoint requiring authentication."""
    return {
        "message": "Access granted",
        "user": current_user["username"]
    }
```

### Node.js (Express) Implementation

```javascript
// utils/jwtHandler.js
const jwt = require('jsonwebtoken');
require('dotenv').config();

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_ALGORITHM = process.env.JWT_ALGORITHM || 'HS256';
const JWT_EXPIRY_MINUTES = parseInt(process.env.JWT_EXPIRY_MINUTES || 15);

function generateToken(userId, username) {
  const payload = {
    user_id: userId,
    username: username,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (JWT_EXPIRY_MINUTES * 60)
  };

  return jwt.sign(payload, JWT_SECRET, { algorithm: JWT_ALGORITHM });
}

function verifyToken(token) {
  try {
    const decoded = jwt.verify(token, JWT_SECRET, { algorithms: [JWT_ALGORITHM] });
    return { valid: true, payload: decoded };
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return { valid: false, error: 'Token expired' };
    }
    return { valid: false, error: 'Invalid token' };
  }
}

module.exports = { generateToken, verifyToken };


// routes/auth.js
const express = require('express');
const bcrypt = require('bcrypt');
const { generateToken } = require('../utils/jwtHandler');
const { getUserByUsername } = require('../database');  // Your DB function

const router = express.Router();

router.post('/login', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }

  // Get user from database
  const user = await getUserByUsername(username);
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Verify password
  const passwordValid = await bcrypt.compare(password, user.password_hash);
  if (!passwordValid) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Generate token
  const token = generateToken(user.id, user.username);

  res.json({
    access_token: token,
    token_type: 'bearer'
  });
});

module.exports = router;


// middleware/authMiddleware.js
const { verifyToken } = require('../utils/jwtHandler');

function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];  // Bearer TOKEN

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  const result = verifyToken(token);

  if (!result.valid) {
    return res.status(401).json({ error: result.error });
  }

  req.user = result.payload;
  next();
}

module.exports = { authenticateToken };


// Example protected route
router.get('/protected', authenticateToken, (req, res) => {
  res.json({
    message: 'Access granted',
    user: req.user.username
  });
});
```

---

## Megumi Security Checklist

### Critical Security Requirements

- [ ] **JWT Secret Security**
  - ✅ Secret stored in environment variable (not hardcoded)
  - ✅ Secret is at least 32 characters long
  - ✅ Secret is randomly generated (not "secret123")
  - ✅ `.env` file in `.gitignore`
  - ❌ SEC-001: If secret is hardcoded → CRITICAL

- [ ] **Token Expiry**
  - ✅ Access token expiry is set (15-30 minutes recommended)
  - ✅ Expiry is enforced in decode function
  - ✅ Expired tokens return 403 Forbidden
  - ❌ SEC-002: If no expiry set → HIGH

- [ ] **Algorithm Security**
  - ✅ Using HS256 or RS256 (NOT "none")
  - ✅ Algorithm specified in decode (prevents algorithm confusion attack)
  - ❌ SEC-003: If algorithm not specified → CRITICAL

- [ ] **Password Security**
  - ✅ Passwords hashed with bcrypt (NOT MD5, SHA1)
  - ✅ Bcrypt rounds ≥ 10
  - ✅ Passwords never logged or returned in responses
  - ❌ SEC-004: If weak hashing → CRITICAL

- [ ] **Token Storage (Frontend)**
  - ✅ Document recommends httpOnly cookies OR sessionStorage
  - ✅ **Warn against localStorage** (XSS vulnerability)
  - ❌ SEC-005: If localStorage used → HIGH

- [ ] **Error Messages**
  - ✅ Generic error "Invalid credentials" (don't reveal if user exists)
  - ✅ Don't leak stack traces in production
  - ❌ SEC-006: If user enumeration possible → MEDIUM

- [ ] **Rate Limiting**
  - ✅ Login endpoint has rate limiting (5-10 req/min)
  - ✅ Prevents brute force attacks
  - ❌ SEC-007: If no rate limiting → HIGH

- [ ] **HTTPS Enforcement**
  - ✅ API served over HTTPS in production
  - ✅ Tokens never sent over HTTP
  - ❌ SEC-008: If HTTP used → CRITICAL

### OWASP Top 10 Verification

| OWASP Category | Check | Status |
|----------------|-------|--------|
| A01: Broken Access Control | JWT required for protected routes | ✅ |
| A02: Cryptographic Failures | bcrypt for passwords, secure JWT secret | ✅ |
| A03: Injection | Parameterized DB queries | ✅ |
| A04: Insecure Design | Token expiry, refresh tokens | ✅ |
| A05: Security Misconfiguration | Secrets in .env, not hardcoded | ✅ |
| A07: Identification/Auth Failures | Rate limiting, strong passwords | ✅ |

### Performance Review

- [ ] JWT generation < 50ms
- [ ] JWT validation < 10ms
- [ ] Password hashing uses async (non-blocking)
- [ ] Database queries use indexes on username field

---

## Common Pitfalls

### ❌ Pitfall 1: Hardcoded JWT Secret
```python
# WRONG - Never do this
JWT_SECRET = "mysecretkey123"
```
**Fix**: Use environment variables
```python
# CORRECT
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET not set in environment")
```

### ❌ Pitfall 2: No Token Expiry
```python
# WRONG - Token never expires
payload = {"user_id": user_id}
```
**Fix**: Always set expiry
```python
# CORRECT
payload = {
    "user_id": user_id,
    "exp": datetime.utcnow() + timedelta(minutes=15)
}
```

### ❌ Pitfall 3: Algorithm Not Specified
```python
# WRONG - Vulnerable to algorithm confusion
jwt.decode(token, secret)
```
**Fix**: Always specify algorithm
```python
# CORRECT
jwt.decode(token, secret, algorithms=["HS256"])
```

### ❌ Pitfall 4: Storing Tokens in localStorage
```javascript
// WRONG - Vulnerable to XSS
localStorage.setItem('token', accessToken);
```
**Fix**: Use httpOnly cookies or sessionStorage
```javascript
// BETTER (but still not ideal)
sessionStorage.setItem('token', accessToken);

// BEST - httpOnly cookie (set from server)
res.cookie('token', accessToken, { httpOnly: true, secure: true });
```

### ❌ Pitfall 5: Revealing User Existence
```python
# WRONG - Tells attacker if username exists
if not user:
    return {"error": "User not found"}
if not password_valid:
    return {"error": "Wrong password"}
```
**Fix**: Generic error message
```python
# CORRECT
if not user or not password_valid:
    return {"error": "Invalid credentials"}
```

---

## Testing Strategy

### Unit Tests (utils/jwt_handler.py)

```python
import pytest
from utils.jwt_handler import generate_token, verify_token
import time

def test_generate_token_success():
    token = generate_token(user_id=1, username="testuser")
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_valid_token():
    token = generate_token(1, "testuser")
    is_valid, payload = verify_token(token)
    assert is_valid == True
    assert payload["user_id"] == 1
    assert payload["username"] == "testuser"

def test_reject_expired_token():
    # Create token with 1-second expiry
    token = generate_token(1, "testuser", expiry_seconds=1)
    time.sleep(2)  # Wait for expiry
    is_valid, payload = verify_token(token)
    assert is_valid == False

def test_reject_invalid_signature():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
    is_valid, payload = verify_token(token)
    assert is_valid == False

def test_reject_malformed_token():
    is_valid, payload = verify_token("not-a-jwt-token")
    assert is_valid == False
```

### Integration Tests (routes/auth.py)

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "correct_password"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_password():
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "wrong_password"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_nonexistent_user():
    response = client.post("/auth/login", json={
        "username": "nonexistent",
        "password": "password"
    })
    assert response.status_code == 401

def test_protected_route_with_valid_token():
    # Login first
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "correct_password"
    })
    token = login_response.json()["access_token"]

    # Access protected route
    response = client.get("/api/protected", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200

def test_protected_route_without_token():
    response = client.get("/api/protected")
    assert response.status_code == 403  # Forbidden

def test_protected_route_with_invalid_token():
    response = client.get("/api/protected", headers={
        "Authorization": "Bearer invalid_token"
    })
    assert response.status_code == 401
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (100% coverage on auth module)
- [ ] Security review completed (@approved from Megumi)
- [ ] JWT_SECRET generated securely (use `openssl rand -hex 32`)
- [ ] Environment variables configured in production
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Error logging set up (don't log tokens!)

### Post-Deployment

- [ ] Test login endpoint in production
- [ ] Verify token expiry works
- [ ] Check HTTPS enforcement
- [ ] Monitor for failed login attempts
- [ ] Set up alerts for unusual activity

---

## Rollback Plan

If JWT authentication causes issues in production:

**Rollback Steps**:
1. Identify backup location: `./backups/[timestamp]/`
2. Stop application server
3. Restore pre-JWT code from backup
4. Remove JWT dependencies from requirements.txt/package.json
5. Restart application
6. Verify old authentication method works
7. Investigate JWT issues in staging environment

**Rollback Time Estimate**: 5-10 minutes

**Rollback Verification**:
- [ ] Application starts without errors
- [ ] Old authentication method works
- [ ] No JWT-related errors in logs

---

## Additional Resources

**JWT Best Practices**:
- [JWT.io](https://jwt.io/) - JWT debugger and documentation
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

**Libraries**:
- Python: [PyJWT](https://pyjwt.readthedocs.io/)
- Node.js: [jsonwebtoken](https://github.com/auth0/node-jsonwebtoken)

**Security Reading**:
- [RFC 7519 - JWT Specification](https://tools.ietf.org/html/rfc7519)
- [Common JWT Security Pitfalls](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)

---

## Tags for Domain Zero Workflow

After implementation:
- `@user-review` - Implementation complete, ready for user review
- `@security-review` - Ready for Megumi's security audit
- `@remediation-required` - Megumi found issues
- `@re-review` - Issues fixed, ready for verification
- `@approved` - Security review passed, production-ready

---

**Template Version**: 1.0
**Last Updated**: 2025-11-05
**Domain Zero Protocol**: v5.1
**Estimated Success Rate**: 95% (when following checklist completely)
