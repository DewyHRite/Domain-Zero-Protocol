# Template: User Registration with Email Verification

## Overview

**Feature**: Complete user registration system with email verification, password strength validation, and secure user account creation.

**Use Case**: Allow new users to create accounts with email verification to prevent spam and ensure valid email addresses.

**Technology Stack**:
- Backend: Python (FastAPI), Node.js (Express), Django
- Database: PostgreSQL, MySQL, MongoDB
- Email Service: SendGrid, AWS SES, SMTP, Resend
- Token Generation: Secrets library, UUID

**Estimated Time**:
- Implementation: 3-4 hours
- Testing: 1.5-2 hours
- Security Review: 45 minutes
- **Total**: 5-6.5 hours

---

## Prerequisites

Before implementing user registration, ensure:

- ✅ User model/table created in database
- ✅ Password hashing library installed (bcrypt)
- ✅ Email service configured (SMTP, SendGrid, etc.)
- ✅ Token storage mechanism (database table or Redis)
- ✅ Email templates ready (HTML/plain text)
- ✅ Environment variables configured
- ✅ Backup created

---

## User Registration Flow

```
1. User submits registration form (email, password, username)
   ↓
2. Server validates input (email format, password strength)
   ↓
3. Check if email already exists
   ↓
4. Hash password with bcrypt
   ↓
5. Create user in database (status: pending)
   ↓
6. Generate verification token
   ↓
7. Send verification email with link
   ↓
8. Return success message (201 Created)

[User clicks verification link in email]
   ↓
9. Server validates token
   ↓
10. Update user status to "active"
   ↓
11. Return success / redirect to login
```

---

## Yuuji Implementation Checklist

### Phase 1: Database Setup (30 minutes)

- [ ] **Create users table** (if not exists)

  **Required fields**:
  - `id` (Primary Key, Auto-increment)
  - `username` (Unique, 3-50 chars)
  - `email` (Unique, valid email format)
  - `password_hash` (NOT password!)
  - `status` (Enum: pending, active, suspended)
  - `created_at` (Timestamp)
  - `email_verified_at` (Nullable timestamp)

- [ ] **Create verification_tokens table**

  **Required fields**:
  - `id` (Primary Key)
  - `user_id` (Foreign Key → users.id)
  - `token` (UUID/random string, unique, indexed)
  - `expires_at` (Timestamp, e.g., 24 hours from creation)
  - `created_at` (Timestamp)

- [ ] **Run database migrations**

- [ ] **Create backup before proceeding**

### Phase 2: Write Tests First (TDD) (1-1.5 hours)

- [ ] **Test: POST /auth/register** (Create user)
  - Success: Valid email, strong password, unique username
  - Returns 201 Created with success message
  - Password is hashed (never stored plain text)
  - User status is "pending"
  - Verification email sent
  - Error: Email already exists → 400
  - Error: Username already taken → 400
  - Error: Weak password → 400 (< 8 chars, no uppercase, etc.)
  - Error: Invalid email format → 400
  - Error: Missing required fields → 400

- [ ] **Test: GET /auth/verify-email?token={token}** (Verify email)
  - Success: Valid token → User status = "active"
  - Returns 200 OK or redirects to login
  - Token is consumed (cannot reuse)
  - Error: Invalid token → 400
  - Error: Expired token → 400 (> 24 hours old)
  - Error: Already verified → 400

- [ ] **Test: POST /auth/resend-verification** (Resend email)
  - Success: Resend verification email if not verified
  - Error: User already verified → 400
  - Error: User doesn't exist → 404
  - Rate limited: Max 3 resends per hour

### Phase 3: Implement Registration Endpoint (1.5 hours)

- [ ] **POST /auth/register** - Create new user

  **Request validation**:
  - Email format validation (regex or library)
  - Password strength: min 8 chars, 1 uppercase, 1 lowercase, 1 number
  - Username: 3-50 chars, alphanumeric + underscore

  **Business logic**:
  - Check if email exists (case-insensitive)
  - Check if username exists (case-insensitive)
  - Hash password with bcrypt (rounds ≥ 10)
  - Create user with status="pending"
  - Generate verification token (UUID4 or secure random)
  - Store token with expiry (24 hours)
  - Send verification email asynchronously
  - Return success message (don't expose user ID)

### Phase 4: Implement Email Verification (1 hour)

- [ ] **GET /auth/verify-email?token={token}** - Verify email

  **Validation**:
  - Token format valid
  - Token exists in database
  - Token not expired
  - User not already verified

  **Business logic**:
  - Find user by token
  - Check token expiry (< 24 hours old)
  - Update user status to "active"
  - Set email_verified_at timestamp
  - Delete/invalidate token
  - Return success or redirect to login page

- [ ] **POST /auth/resend-verification** - Resend verification email

  **Validation**:
  - User exists
  - User not already verified
  - Rate limit: 3 requests per hour per email

  **Business logic**:
  - Generate new token
  - Invalidate old token
  - Send verification email
  - Return success message

### Phase 5: Email Service Integration (45 minutes)

- [ ] **Configure email service** (SendGrid, AWS SES, SMTP)
- [ ] **Create email templates**
  - HTML version (styled, branded)
  - Plain text version (fallback)
  - Include verification link with token
  - Include expiry notice (24 hours)

- [ ] **Implement email sending function**
  - Async/background job (don't block API)
  - Error handling (log failures, don't crash)
  - Retry logic (3 attempts)

### Phase 6: Documentation & Rollback (20 minutes)

- [ ] Document registration flow
- [ ] Document password requirements
- [ ] Create rollback plan in dev-notes.md
- [ ] Tag @user-review when complete

---

## Code Template

### Python (FastAPI) Implementation

```python
# models/user.py
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from database import Base
import enum

class UserStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    email_verified_at = Column(DateTime(timezone=True), nullable=True)


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# schemas/user.py
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric with underscores only')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserRegisterResponse(BaseModel):
    message: str
    email: str


# utils/password.py
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# utils/email.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

async def send_verification_email(email: str, token: str):
    """Send email verification link."""
    verification_link = f"{FRONTEND_URL}/verify-email?token={token}"

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject="Verify Your Email Address",
        html_content=f"""
        <html>
        <body>
            <h2>Welcome! Please verify your email</h2>
            <p>Click the link below to verify your email address:</p>
            <p><a href="{verification_link}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
        </html>
        """
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return True
    except Exception as e:
        # Log error but don't crash
        print(f"Failed to send email: {e}")
        return False


# routes/auth.py
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user and send verification email."""

    # Check if email already exists
    existing_email = db.query(User).filter(
        func.lower(User.email) == func.lower(user_data.email)
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(User).filter(
        func.lower(User.username) == func.lower(user_data.username)
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create user
    user = User(
        username=user_data.username.lower(),
        email=user_data.email.lower(),
        password_hash=password_hash,
        status=UserStatus.PENDING
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate verification token
    token = str(uuid.uuid4())
    verification_token = VerificationToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(verification_token)
    db.commit()

    # Send verification email (async)
    background_tasks.add_task(send_verification_email, user.email, token)

    return UserRegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
        email=user.email
    )


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email with token."""

    # Find token
    verification = db.query(VerificationToken).filter(
        VerificationToken.token == token
    ).first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    # Check if expired
    if datetime.utcnow() > verification.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )

    # Get user
    user = db.query(User).filter(User.id == verification.user_id).first()

    if user.status == UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    # Update user status
    user.status = UserStatus.ACTIVE
    user.email_verified_at = datetime.utcnow()

    # Delete token
    db.delete(verification)
    db.commit()

    return {
        "message": "Email verified successfully. You can now log in."
    }


@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend verification email."""

    # Find user
    user = db.query(User).filter(func.lower(User.email) == func.lower(email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.status == UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    # Delete old tokens
    db.query(VerificationToken).filter(VerificationToken.user_id == user.id).delete()

    # Generate new token
    token = str(uuid.uuid4())
    verification_token = VerificationToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(verification_token)
    db.commit()

    # Send email
    background_tasks.add_task(send_verification_email, user.email, token)

    return {
        "message": "Verification email sent. Please check your inbox."
    }
```

---

## Megumi Security Checklist

### Critical Security Requirements

- [ ] **Password Storage**
  - ✅ Passwords hashed with bcrypt (rounds ≥ 10)
  - ✅ Passwords NEVER stored in plain text
  - ✅ Passwords NEVER logged or returned in API
  - ❌ SEC-001: If plain text storage → CRITICAL

- [ ] **Password Strength Requirements**
  - ✅ Minimum 8 characters
  - ✅ At least 1 uppercase letter
  - ✅ At least 1 lowercase letter
  - ✅ At least 1 number
  - ❌ SEC-002: If weak passwords allowed → HIGH

- [ ] **Email Verification Security**
  - ✅ Tokens are random and unpredictable (UUID4 or crypto.randomBytes)
  - ✅ Tokens expire after 24 hours
  - ✅ Tokens cannot be reused after verification
  - ✅ Tokens stored with index for fast lookup
  - ❌ SEC-003: If predictable tokens → CRITICAL

- [ ] **User Enumeration Prevention**
  - ✅ Same error for "email exists" and "username exists"
  - ✅ Registration takes same time regardless of email existence
  - ❌ SEC-004: If user enumeration possible → MEDIUM

- [ ] **Rate Limiting**
  - ✅ Registration endpoint limited (5 per hour per IP)
  - ✅ Resend verification limited (3 per hour per email)
  - ❌ SEC-005: If no rate limiting → HIGH

- [ ] **Email Security**
  - ✅ Emails sent over TLS
  - ✅ SPF/DKIM configured (prevent spoofing)
  - ✅ Verification links use HTTPS
  - ❌ SEC-006: If HTTP links → HIGH

- [ ] **Database Security**
  - ✅ Email and username stored in lowercase (prevents case-sensitivity bypass)
  - ✅ Unique constraints on email and username
  - ✅ Parameterized queries (no SQL injection)
  - ❌ SEC-007: If case-sensitive checks → MEDIUM

### OWASP Top 10 Verification

| OWASP Category | Check | Status |
|----------------|-------|--------|
| A01: Broken Access Control | Email verification required before login | ✅ |
| A02: Cryptographic Failures | bcrypt for passwords, random tokens | ✅ |
| A04: Insecure Design | Token expiry, rate limiting | ✅ |
| A05: Security Misconfiguration | Strong password policy, HTTPS | ✅ |
| A07: Identification/Auth Failures | Prevent user enumeration, rate limits | ✅ |

---

## Common Pitfalls

### ❌ Pitfall 1: Storing Plain Text Passwords
```python
# WRONG - Never do this!
user.password = user_data.password
```
**Fix**: Always hash passwords
```python
# CORRECT
user.password_hash = hash_password(user_data.password)
```

### ❌ Pitfall 2: Predictable Verification Tokens
```python
# WRONG - Sequential tokens are guessable
token = str(user.id) + str(int(time.time()))
```
**Fix**: Use cryptographically secure random tokens
```python
# CORRECT
import uuid
token = str(uuid.uuid4())  # Random, unpredictable
```

### ❌ Pitfall 3: No Token Expiry
```python
# WRONG - Token valid forever
verification_token = VerificationToken(user_id=user.id, token=token)
```
**Fix**: Set expiry (24 hours recommended)
```python
# CORRECT
expires_at = datetime.utcnow() + timedelta(hours=24)
verification_token = VerificationToken(..., expires_at=expires_at)
```

### ❌ Pitfall 4: User Enumeration via Error Messages
```python
# WRONG - Reveals if email exists
if existing_email:
    return {"error": "Email already registered"}
if existing_username:
    return {"error": "Username already taken"}
```
**Fix**: Generic error or same response time
```python
# BETTER
if existing_email or existing_username:
    return {"error": "Registration failed. Please try different credentials."}
```

### ❌ Pitfall 5: Case-Sensitive Email Checks
```python
# WRONG - "User@Example.com" and "user@example.com" seen as different
User.email == user_data.email
```
**Fix**: Normalize to lowercase
```python
# CORRECT
func.lower(User.email) == func.lower(user_data.email)
```

---

## Testing Strategy

```python
def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 201
    assert "verification" in response.json()["message"].lower()

def test_register_duplicate_email(client, existing_user):
    response = client.post("/auth/register", json={
        "username": "newuser",
        "email": existing_user.email,
        "password": "SecurePass123"
    })
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()

def test_register_weak_password(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "weak"  # Too short, no uppercase
    })
    assert response.status_code == 400

def test_verify_email_success(client, pending_user_with_token):
    user, token = pending_user_with_token
    response = client.get(f"/auth/verify-email?token={token}")
    assert response.status_code == 200
    # Verify user is now active
    assert user.status == UserStatus.ACTIVE

def test_verify_email_expired_token(client, expired_token):
    response = client.get(f"/auth/verify-email?token={expired_token}")
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

def test_verify_email_invalid_token(client):
    response = client.get("/auth/verify-email?token=invalid-token")
    assert response.status_code == 400
```

---

## Rollback Plan

**Rollback Steps**:
1. Backup location: `./backups/[timestamp]/`
2. Stop application
3. Restore code from backup
4. Rollback database migrations:
   - `alembic downgrade -1` (users table)
   - `alembic downgrade -1` (verification_tokens table)
5. Restart application
6. Verify old registration flow works

**Rollback Time**: 5-10 minutes

---

## Tags for Domain Zero Workflow

- `@user-review` - Registration implementation complete
- `@security-review` - Ready for Megumi
- `@approved` - Production-ready

---

**Template Version**: 1.0
**Last Updated**: 2025-11-05
**Domain Zero Protocol**: v5.1
