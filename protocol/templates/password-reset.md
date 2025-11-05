# Template: Password Reset Flow

## Overview

**Feature**: Secure password reset functionality allowing users to reset forgotten passwords via email verification.

**Use Case**: Users who forgot their password can request a password reset link via email, verify their identity, and set a new password.

**Technology Stack**:
- Backend: Python (FastAPI), Node.js (Express), Django
- Email Service: SendGrid, AWS SES, Resend
- Token Storage: Database or Redis
- Security: Time-limited tokens, rate limiting

**Estimated Time**:
- Implementation: 2-3 hours
- Testing: 1-1.5 hours
- Security Review: 30-45 minutes
- **Total**: 3.5-5 hours

---

## Prerequisites

- ✅ User authentication system exists
- ✅ Email service configured
- ✅ Password reset tokens table created
- ✅ Password hashing library (bcrypt) installed
- ✅ Rate limiting library available
- ✅ Backup created

---

## Password Reset Flow

```
1. User clicks "Forgot Password"
   ↓
2. User enters email address
   ↓
3. Server validates email format
   ↓
4. Server checks if user exists (silently - no user enumeration)
   ↓
5. Generate secure reset token
   ↓
6. Store token with expiry (1 hour)
   ↓
7. Send password reset email with link
   ↓
8. Return generic success message (don't reveal if user exists)

[User clicks reset link in email]
   ↓
9. User lands on reset form with token in URL
   ↓
10. User enters new password (2x for confirmation)
   ↓
11. Server validates token (exists, not expired, not used)
   ↓
12. Validate new password strength
   ↓
13. Hash new password
   ↓
14. Update user password
   ↓
15. Invalidate reset token
   ↓
16. Send confirmation email (password changed)
   ↓
17. Return success / redirect to login
```

---

## Yuuji Implementation Checklist

### Phase 1: Database Setup (20 minutes)

- [ ] **Create password_reset_tokens table**

  **Required fields**:
  - `id` (Primary Key)
  - `user_id` (Foreign Key → users.id)
  - `token` (UUID, unique, indexed)
  - `expires_at` (Timestamp, 1 hour from creation)
  - `used_at` (Nullable timestamp, prevents token reuse)
  - `created_at` (Timestamp)

- [ ] **Run database migrations**
- [ ] **Create backup before proceeding**

### Phase 2: Write Tests First (TDD) (1-1.5 hours)

- [ ] **Test: POST /auth/forgot-password** (Request reset)
  - Success: Valid email → Returns generic success message
  - Success: Non-existent email → Returns same success message (prevent enumeration)
  - Creates reset token in database
  - Sends reset email
  - Error: Invalid email format → 400
  - Error: Missing email → 400
  - Rate limited: Max 3 requests per hour per IP

- [ ] **Test: POST /auth/reset-password** (Reset password)
  - Success: Valid token + strong password → Password updated
  - Returns 200 OK
  - Token marked as used
  - Confirmation email sent
  - Error: Invalid token → 400
  - Error: Expired token → 400 (> 1 hour old)
  - Error: Already used token → 400
  - Error: Weak password → 400
  - Error: Password confirmation mismatch → 400

- [ ] **Test: GET /auth/validate-reset-token?token={token}** (Check token validity)
  - Success: Valid token → Returns 200
  - Error: Invalid/expired token → 400

### Phase 3: Implement Forgot Password Endpoint (1 hour)

- [ ] **POST /auth/forgot-password** - Request password reset

  **Request validation**:
  - Email format validation
  - Rate limiting: 3 requests/hour per IP

  **Business logic**:
  - Look up user by email (case-insensitive)
  - If user doesn't exist: Still return success (prevent enumeration)
  - If user exists:
    - Generate secure reset token (UUID4)
    - Store token with 1-hour expiry
    - Send reset email with link
  - Return generic success message in both cases

### Phase 4: Implement Reset Password Endpoint (1 hour)

- [ ] **POST /auth/reset-password** - Reset password with token

  **Request validation**:
  - Token format validation
  - New password strength validation
  - Password confirmation match

  **Business logic**:
  - Validate token (exists, not expired, not used)
  - Find user associated with token
  - Hash new password
  - Update user password
  - Mark token as used (set used_at timestamp)
  - Send confirmation email
  - Return success message

- [ ] **GET /auth/validate-reset-token** - Check token validity (optional)
  - Validates token before showing reset form
  - Improves UX (user knows immediately if token is invalid)

### Phase 5: Email Templates (30 minutes)

- [ ] **Password reset email**
  - Subject: "Reset Your Password"
  - Include reset link with token
  - Mention 1-hour expiry
  - Security notice: "If you didn't request this, ignore it"

- [ ] **Password changed confirmation email**
  - Subject: "Your Password Was Changed"
  - Notify user of password change
  - Security notice: "If you didn't make this change, contact support"

### Phase 6: Documentation & Rollback (15 minutes)

- [ ] Document reset flow
- [ ] Document security measures
- [ ] Create rollback plan in dev-notes.md
- [ ] Tag @user-review when complete

---

## Code Template

### Python (FastAPI) Implementation

```python
# models/password_reset.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# schemas/password_reset.py
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator('new_password')
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

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


# utils/email.py (add to existing email utilities)
async def send_password_reset_email(email: str, token: str):
    """Send password reset link."""
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject="Reset Your Password",
        html_content=f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below to proceed:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p><strong>This link will expire in 1 hour.</strong></p>
            <p>If you didn't request this, please ignore this email. Your password will not be changed.</p>
            <p>For security, never share this link with anyone.</p>
        </body>
        </html>
        """
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Failed to send reset email: {e}")
        return False

async def send_password_changed_email(email: str):
    """Send confirmation that password was changed."""
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject="Your Password Was Changed",
        html_content="""
        <html>
        <body>
            <h2>Password Changed Successfully</h2>
            <p>Your password was recently changed.</p>
            <p><strong>If you made this change</strong>, you can safely ignore this email.</p>
            <p><strong>If you did NOT make this change</strong>, your account may be compromised.
               Please contact support immediately and secure your account.</p>
        </body>
        </html>
        """
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")
        return False


# routes/password_reset.py
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from utils.password import hash_password
from utils.email import send_password_reset_email, send_password_changed_email

router = APIRouter(prefix="/auth", tags=["password-reset"])

# Simple in-memory rate limiter (use Redis in production)
reset_requests = {}  # {ip: [(timestamp, count)]}

def check_rate_limit(ip: str, max_requests: int = 3, window_minutes: int = 60):
    """Check if IP has exceeded rate limit."""
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)

    if ip not in reset_requests:
        reset_requests[ip] = []

    # Remove old requests outside window
    reset_requests[ip] = [
        req_time for req_time in reset_requests[ip]
        if req_time > window_start
    ]

    # Check limit
    if len(reset_requests[ip]) >= max_requests:
        return False

    # Add current request
    reset_requests[ip].append(now)
    return True


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset. Returns success regardless of whether user exists (prevent enumeration)."""

    # Rate limiting
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later."
        )

    # Look up user (case-insensitive)
    user = db.query(User).filter(
        func.lower(User.email) == func.lower(data.email)
    ).first()

    # IMPORTANT: Return success even if user doesn't exist (prevent user enumeration)
    if user:
        # Delete old unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at == None
        ).delete()

        # Generate reset token
        token = str(uuid.uuid4())
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()

        # Send reset email (async)
        background_tasks.add_task(send_password_reset_email, user.email, token)

    # Always return the same message (security)
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Reset password using reset token."""

    # Find token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token expired
    if datetime.utcnow() > reset_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )

    # Check if token already used
    if reset_token.used_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used"
        )

    # Get user
    user = db.query(User).filter(User.id == reset_token.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    # Update password
    user.password_hash = hash_password(data.new_password)

    # Mark token as used
    reset_token.used_at = datetime.utcnow()

    db.commit()

    # Send confirmation email (async)
    background_tasks.add_task(send_password_changed_email, user.email)

    return {
        "message": "Password reset successfully. You can now log in with your new password."
    }


@router.get("/validate-reset-token")
async def validate_reset_token(token: str, db: Session = Depends(get_db)):
    """Check if reset token is valid (useful for frontend)."""

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    if datetime.utcnow() > reset_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    if reset_token.used_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used"
        )

    return {"message": "Token is valid"}
```

---

## Megumi Security Checklist

### Critical Security Requirements

- [ ] **User Enumeration Prevention**
  - ✅ Same response for existing and non-existing emails
  - ✅ Same response time for both cases (consider adding delay)
  - ❌ SEC-001: If reveals user existence → HIGH

- [ ] **Token Security**
  - ✅ Tokens are cryptographically random (UUID4)
  - ✅ Tokens expire after 1 hour
  - ✅ Tokens can only be used once (used_at timestamp)
  - ✅ Tokens indexed for fast lookup
  - ❌ SEC-002: If predictable tokens → CRITICAL
  - ❌ SEC-003: If no expiry → CRITICAL

- [ ] **Rate Limiting**
  - ✅ Forgot password: 3 requests/hour per IP
  - ✅ Reset password: Rate limit by token (prevent brute force)
  - ❌ SEC-004: If no rate limiting → HIGH

- [ ] **Password Validation**
  - ✅ Strong password requirements (8+ chars, mixed case, numbers)
  - ✅ Password confirmation required
  - ✅ Old password cannot be reused (optional but recommended)
  - ❌ SEC-005: If weak passwords allowed → HIGH

- [ ] **Email Security**
  - ✅ Reset links use HTTPS
  - ✅ Token not exposed in email body (only in link)
  - ✅ Confirmation email sent after password change
  - ❌ SEC-006: If HTTP links → HIGH

- [ ] **Token Cleanup**
  - ✅ Old unused tokens deleted before creating new one
  - ✅ Used tokens marked with used_at timestamp
  - ✅ Database cleanup job for expired tokens (recommended)
  - ❌ SEC-007: If token accumulation → LOW

- [ ] **Notification Security**
  - ✅ User notified when password changes
  - ✅ Email includes security warning if unauthorized
  - ❌ SEC-008: If no change notification → MEDIUM

### OWASP Top 10 Verification

| OWASP Category | Check | Status |
|----------------|-------|--------|
| A01: Broken Access Control | Token validates user identity | ✅ |
| A02: Cryptographic Failures | bcrypt for passwords, random tokens | ✅ |
| A04: Insecure Design | Token expiry, one-time use, rate limits | ✅ |
| A05: Security Misconfiguration | No user enumeration, HTTPS links | ✅ |
| A07: Identification/Auth Failures | Strong passwords, rate limiting | ✅ |

---

## Common Pitfalls

### ❌ Pitfall 1: User Enumeration
```python
# WRONG - Reveals if user exists
if not user:
    return {"error": "User not found"}
return {"message": "Reset email sent"}
```
**Fix**: Same response always
```python
# CORRECT
return {"message": "If an account exists, reset link has been sent"}
```

### ❌ Pitfall 2: No Token Expiry
```python
# WRONG - Token valid forever
reset_token = PasswordResetToken(user_id=user.id, token=token)
```
**Fix**: Set 1-hour expiry
```python
# CORRECT
expires_at = datetime.utcnow() + timedelta(hours=1)
reset_token = PasswordResetToken(..., expires_at=expires_at)
```

### ❌ Pitfall 3: Token Reuse
```python
# WRONG - Token can be used multiple times
if reset_token.expires_at < datetime.utcnow():
    raise HTTPException(...)
# No check if already used!
```
**Fix**: Mark as used
```python
# CORRECT
if reset_token.used_at:
    raise HTTPException(400, "Token already used")
reset_token.used_at = datetime.utcnow()
```

### ❌ Pitfall 4: No Rate Limiting
```python
# WRONG - Can spam reset requests
@router.post("/forgot-password")
def forgot_password(email: str):
    # No rate limiting!
```
**Fix**: Implement rate limits
```python
# CORRECT
if not check_rate_limit(request.client.host):
    raise HTTPException(429, "Too many requests")
```

---

## Testing Strategy

```python
def test_forgot_password_existing_user(client):
    response = client.post("/auth/forgot-password", json={
        "email": "existing@example.com"
    })
    assert response.status_code == 200
    assert "reset link" in response.json()["message"].lower()

def test_forgot_password_nonexistent_user(client):
    response = client.post("/auth/forgot-password", json={
        "email": "nonexistent@example.com"
    })
    # Same response as existing user (prevent enumeration)
    assert response.status_code == 200
    assert "reset link" in response.json()["message"].lower()

def test_reset_password_success(client, valid_reset_token):
    response = client.post("/auth/reset-password", json={
        "token": valid_reset_token,
        "new_password": "NewSecure123",
        "confirm_password": "NewSecure123"
    })
    assert response.status_code == 200

def test_reset_password_expired_token(client, expired_token):
    response = client.post("/auth/reset-password", json={
        "token": expired_token,
        "new_password": "NewSecure123",
        "confirm_password": "NewSecure123"
    })
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

def test_reset_password_reuse_token(client, used_token):
    response = client.post("/auth/reset-password", json={
        "token": used_token,
        "new_password": "NewSecure123",
        "confirm_password": "NewSecure123"
    })
    assert response.status_code == 400
    assert "already been used" in response.json()["detail"].lower()

def test_rate_limiting(client):
    for i in range(4):
        response = client.post("/auth/forgot-password", json={
            "email": "test@example.com"
        })
        if i < 3:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Too many requests
```

---

## Rollback Plan

**Rollback Steps**:
1. Backup location: `./backups/[timestamp]/`
2. Stop application
3. Restore code from backup
4. Rollback database migration (password_reset_tokens table)
5. Restart application
6. Verify old system works (if any)

**Rollback Time**: 5 minutes

---

## Tags for Domain Zero Workflow

- `@user-review` - Password reset implementation complete
- `@security-review` - Ready for Megumi
- `@approved` - Production-ready

---

**Template Version**: 1.0
**Last Updated**: 2025-11-05
**Domain Zero Protocol**: v5.1
