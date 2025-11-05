# Template: Secure File Upload with Cloud Storage

## Overview

**Feature**: Secure file upload system with validation, virus scanning, cloud storage (S3/Azure/GCS), and presigned URL generation.

**Use Case**: Allow users to upload files (images, documents, videos) with security validation and store them in cloud storage.

**Technology Stack**:
- Backend: Python (FastAPI), Node.js (Express)
- Storage: AWS S3, Azure Blob Storage, Google Cloud Storage
- Validation: File type, size, content verification
- Optional: ClamAV (virus scanning)

**Estimated Time**:
- Implementation: 3-4 hours
- Testing: 1.5-2 hours
- Security Review: 45-60 minutes
- **Total**: 5-7 hours

---

## Prerequisites

- ✅ Cloud storage account (AWS S3, Azure, or GCS)
- ✅ Cloud storage SDK installed (boto3, @azure/storage-blob, @google-cloud/storage)
- ✅ Environment variables configured (bucket name, credentials)
- ✅ File validation library (python-magic, file-type)
- ✅ Database table for file metadata
- ✅ Backup created

---

## File Upload Flow

```
1. User selects file in frontend
   ↓
2. Frontend validates file size client-side (UX improvement)
   ↓
3. POST request to /api/upload with multipart/form-data
   ↓
4. Server validates:
   - File size (< 10MB for images, < 100MB for videos)
   - File type (whitelist: jpg, png, pdf, etc.)
   - MIME type matches extension
   - Content verification (magic bytes)
   ↓
5. Generate unique filename (UUID + original extension)
   ↓
6. (Optional) Virus scan with ClamAV
   ↓
7. Upload to cloud storage (S3/Azure/GCS)
   ↓
8. Store file metadata in database (filename, size, user_id, etc.)
   ↓
9. Return file ID and presigned URL
```

---

## Yuuji Implementation Checklist

### Phase 1: Database Setup (20 minutes)

- [ ] **Create uploads table**

  **Required fields**:
  - `id` (Primary Key, UUID)
  - `user_id` (Foreign Key → users.id, nullable if public uploads)
  - `filename` (Original filename)
  - `stored_filename` (UUID-based filename in cloud)
  - `file_size` (Bytes)
  - `mime_type` (e.g., image/jpeg)
  - `storage_provider` (s3, azure, gcs)
  - `storage_path` (Full path/key in cloud)
  - `status` (Enum: uploading, completed, failed)
  - `created_at` (Timestamp)

- [ ] **Run database migrations**
- [ ] **Create backup before proceeding**

### Phase 2: Write Tests First (TDD) (1.5-2 hours)

- [ ] **Test: POST /api/upload** (Upload file)
  - Success: Valid image file → Returns file ID and URL
  - Success: Valid PDF → Returns file ID
  - File stored in cloud storage
  - Metadata stored in database
  - Error: File too large → 413 Payload Too Large
  - Error: Invalid file type → 400 (e.g., .exe file)
  - Error: MIME type mismatch → 400 (file.jpg but actually .exe)
  - Error: No file provided → 400
  - Error: Corrupted file → 400

- [ ] **Test: GET /api/files/{id}** (Get file metadata)
  - Success: Returns filename, size, mime_type, URL
  - Error: File doesn't exist → 404
  - Error: Unauthorized access → 403 (if private files)

- [ ] **Test: GET /api/files/{id}/download** (Download file)
  - Success: Returns presigned URL (redirects)
  - Error: File doesn't exist → 404
  - Error: Unauthorized → 403

- [ ] **Test: DELETE /api/files/{id}** (Delete file)
  - Success: Deletes from cloud + database
  - Error: Unauthorized → 403

### Phase 3: Cloud Storage Setup (30-45 minutes)

- [ ] **Configure AWS S3 / Azure Blob / GCS**
  - Create bucket/container
  - Set up IAM credentials (access key + secret)
  - Configure CORS (if frontend needs direct access)
  - Set bucket policy (private by default)

- [ ] **Create storage utility module**
  - `upload_file(file, filename)` → Returns storage path
  - `generate_presigned_url(filename, expiry=3600)` → Returns URL
  - `delete_file(filename)` → Deletes from cloud
  - Error handling for network failures

### Phase 4: Implement Upload Endpoint (1.5-2 hours)

- [ ] **POST /api/upload** - Upload file

  **Validation**:
  - File size limits:
    - Images: 10 MB max
    - Documents (PDF): 20 MB max
    - Videos: 100 MB max
  - File type whitelist: jpg, jpeg, png, gif, pdf, doc, docx, mp4
  - MIME type verification (check magic bytes, not just extension)
  - Sanitize filename (remove path traversal attempts)

  **Business logic**:
  - Generate unique stored filename: `{UUID}.{extension}`
  - Upload to cloud storage
  - Store metadata in database
  - Return file ID and presigned URL (1-hour expiry)

### Phase 5: Implement Download & Delete (30 minutes)

- [ ] **GET /api/files/{id}** - Get file metadata
- [ ] **GET /api/files/{id}/download** - Get download URL (presigned)
- [ ] **DELETE /api/files/{id}** - Delete file (cloud + database)

### Phase 6: Documentation & Rollback (15 minutes)

- [ ] Document upload limits
- [ ] Document supported file types
- [ ] Create rollback plan in dev-notes.md
- [ ] Tag @user-review when complete

---

## Code Template

### Python (FastAPI + AWS S3) Implementation

```python
# models/upload.py
from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base
import enum
import uuid

class UploadStatus(str, enum.Enum):
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for public uploads
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # Bytes
    mime_type = Column(String(100), nullable=False)
    storage_provider = Column(String(20), default="s3")
    storage_path = Column(String(500), nullable=False)
    status = Column(Enum(UploadStatus), default=UploadStatus.UPLOADING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# utils/storage.py
import os
import boto3
from botocore.exceptions import ClientError
from datetime import timedelta

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def upload_to_s3(file_content: bytes, filename: str, mime_type: str) -> str:
    """Upload file to S3 and return storage path."""
    try:
        s3_client.put_object(
            Bucket=AWS_BUCKET_NAME,
            Key=filename,
            Body=file_content,
            ContentType=mime_type
        )
        return f"s3://{AWS_BUCKET_NAME}/{filename}"
    except ClientError as e:
        raise Exception(f"Failed to upload to S3: {e}")

def generate_presigned_url(filename: str, expiry_seconds: int = 3600) -> str:
    """Generate presigned URL for downloading file."""
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_BUCKET_NAME, 'Key': filename},
            ExpiresIn=expiry_seconds
        )
        return url
    except ClientError as e:
        raise Exception(f"Failed to generate presigned URL: {e}")

def delete_from_s3(filename: str) -> bool:
    """Delete file from S3."""
    try:
        s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=filename)
        return True
    except ClientError as e:
        print(f"Failed to delete from S3: {e}")
        return False


# utils/file_validation.py
import magic
import os
from typing import Optional

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg": {"extensions": [".jpg", ".jpeg"], "max_size": 10 * 1024 * 1024},  # 10 MB
    "image/png": {"extensions": [".png"], "max_size": 10 * 1024 * 1024},
    "image/gif": {"extensions": [".gif"], "max_size": 10 * 1024 * 1024},
    "application/pdf": {"extensions": [".pdf"], "max_size": 20 * 1024 * 1024},  # 20 MB
    "video/mp4": {"extensions": [".mp4"], "max_size": 100 * 1024 * 1024},  # 100 MB
}

def validate_file(file_content: bytes, filename: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Validate file content and name.
    Returns: (is_valid, mime_type, error_message)
    """
    # Get file extension
    _, ext = os.path.splitext(filename.lower())

    # Detect MIME type from content (magic bytes)
    mime = magic.Magic(mime=True)
    detected_mime_type = mime.from_buffer(file_content)

    # Check if MIME type is allowed
    if detected_mime_type not in ALLOWED_MIME_TYPES:
        return False, None, f"File type not allowed: {detected_mime_type}"

    # Check if extension matches MIME type
    allowed_extensions = ALLOWED_MIME_TYPES[detected_mime_type]["extensions"]
    if ext not in allowed_extensions:
        return False, None, f"File extension {ext} doesn't match content type {detected_mime_type}"

    # Check file size
    file_size = len(file_content)
    max_size = ALLOWED_MIME_TYPES[detected_mime_type]["max_size"]
    if file_size > max_size:
        return False, None, f"File too large. Maximum size: {max_size / (1024*1024):.1f} MB"

    return True, detected_mime_type, None


# routes/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session
import uuid
import os

router = APIRouter(prefix="/api", tags=["file-upload"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user),  # Optional auth
    db: Session = Depends(get_db)
):
    """Upload a file to cloud storage."""

    # Read file content
    file_content = await file.read()

    # Validate file
    is_valid, mime_type, error = validate_file(file_content, file.filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    stored_filename = f"{uuid.uuid4()}{file_ext}"

    try:
        # Upload to S3
        storage_path = upload_to_s3(file_content, stored_filename, mime_type)

        # Save metadata to database
        upload_record = Upload(
            user_id=current_user.id if current_user else None,
            filename=file.filename,
            stored_filename=stored_filename,
            file_size=len(file_content),
            mime_type=mime_type,
            storage_provider="s3",
            storage_path=storage_path,
            status=UploadStatus.COMPLETED
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        # Generate presigned URL for immediate access
        presigned_url = generate_presigned_url(stored_filename, expiry_seconds=3600)

        return {
            "id": upload_record.id,
            "filename": upload_record.filename,
            "size": upload_record.file_size,
            "mime_type": upload_record.mime_type,
            "url": presigned_url,
            "expires_in": 3600
        }

    except Exception as e:
        # Cleanup on failure
        if 'upload_record' in locals():
            upload_record.status = UploadStatus.FAILED
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/files/{file_id}")
async def get_file_metadata(
    file_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file metadata."""
    upload = db.query(Upload).filter(Upload.id == file_id).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check authorization (if file belongs to user)
    if upload.user_id and current_user and upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    return {
        "id": upload.id,
        "filename": upload.filename,
        "size": upload.file_size,
        "mime_type": upload.mime_type,
        "created_at": upload.created_at
    }


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get presigned download URL."""
    upload = db.query(Upload).filter(Upload.id == file_id).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check authorization
    if upload.user_id and current_user and upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Generate presigned URL
    try:
        presigned_url = generate_presigned_url(upload.stored_filename, expiry_seconds=3600)
        return {
            "url": presigned_url,
            "expires_in": 3600
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file."""
    upload = db.query(Upload).filter(Upload.id == file_id).first()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check authorization
    if upload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to delete this file"
        )

    # Delete from S3
    delete_from_s3(upload.stored_filename)

    # Delete from database
    db.delete(upload)
    db.commit()

    return {"message": "File deleted successfully"}
```

---

## Megumi Security Checklist

### Critical Security Requirements

- [ ] **File Type Validation**
  - ✅ Whitelist of allowed MIME types
  - ✅ Magic byte verification (not just extension)
  - ✅ Extension matches MIME type
  - ❌ SEC-001: If only extension checked → CRITICAL (can upload .exe as .jpg)

- [ ] **File Size Limits**
  - ✅ Maximum size enforced (10MB images, 100MB videos)
  - ✅ Size checked before processing
  - ✅ Prevents DoS via large files
  - ❌ SEC-002: If no size limit → HIGH

- [ ] **Filename Sanitization**
  - ✅ Original filename sanitized (remove path traversal)
  - ✅ Stored filename is UUID-based
  - ✅ No user input in storage path
  - ❌ SEC-003: If unsanitized filenames → HIGH

- [ ] **Access Control**
  - ✅ Private files require authentication
  - ✅ Users can only access their own files
  - ✅ Presigned URLs have expiry (1 hour)
  - ❌ SEC-004: If no access control → CRITICAL

- [ ] **Virus Scanning** (Optional but recommended)
  - ✅ ClamAV integration for file scanning
  - ✅ Quarantine suspicious files
  - ❌ SEC-005: If no virus scanning → MEDIUM

- [ ] **Storage Security**
  - ✅ S3 bucket is private (not public read)
  - ✅ IAM credentials not hardcoded
  - ✅ Presigned URLs used for access
  - ❌ SEC-006: If public bucket → CRITICAL

- [ ] **Metadata Validation**
  - ✅ Filename length limited (< 255 chars)
  - ✅ MIME type validated
  - ❌ SEC-007: If unlimited metadata → LOW

### OWASP Top 10 Verification

| OWASP Category | Check | Status |
|----------------|-------|--------|
| A01: Broken Access Control | File ownership, presigned URLs | ✅ |
| A03: Injection | Filename sanitization, no path traversal | ✅ |
| A04: Insecure Design | Size limits, type validation | ✅ |
| A05: Security Misconfiguration | Private bucket, IAM credentials | ✅ |
| A08: Software/Data Integrity | Magic byte verification | ✅ |

---

## Common Pitfalls

### ❌ Pitfall 1: Trusting File Extension
```python
# WRONG - Extension can be faked
if filename.endswith('.jpg'):
    # Assume it's an image
```
**Fix**: Check magic bytes
```python
# CORRECT
mime_type = magic.from_buffer(file_content, mime=True)
if mime_type == 'image/jpeg':
    ...
```

### ❌ Pitfall 2: No File Size Limit
```python
# WRONG - Can upload 10GB file (DoS)
file_content = await file.read()
```
**Fix**: Check size limits
```python
# CORRECT
if len(file_content) > 10 * 1024 * 1024:  # 10 MB
    raise HTTPException(413, "File too large")
```

### ❌ Pitfall 3: Using Original Filename
```python
# WRONG - Path traversal attack
upload_to_s3(content, file.filename)  # filename = "../../etc/passwd"
```
**Fix**: Generate safe filename
```python
# CORRECT
stored_filename = f"{uuid.uuid4()}{file_ext}"
```

### ❌ Pitfall 4: Public S3 Bucket
```python
# WRONG - Anyone can access files
# S3 bucket policy: Allow public read
```
**Fix**: Use presigned URLs
```python
# CORRECT - Private bucket + presigned URLs
url = generate_presigned_url(filename, expiry=3600)
```

---

## Testing Strategy

```python
def test_upload_valid_image(client, auth_headers):
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.jpg", f, "image/jpeg")},
            headers=auth_headers
        )
    assert response.status_code == 200
    assert "id" in response.json()
    assert "url" in response.json()

def test_upload_file_too_large(client, auth_headers):
    large_file = b"x" * (11 * 1024 * 1024)  # 11 MB
    response = client.post(
        "/api/upload",
        files={"file": ("large.jpg", large_file, "image/jpeg")},
        headers=auth_headers
    )
    assert response.status_code == 413  # Payload Too Large

def test_upload_invalid_type(client, auth_headers):
    response = client.post(
        "/api/upload",
        files={"file": ("malware.exe", b"MZ...", "application/x-msdownload")},
        headers=auth_headers
    )
    assert response.status_code == 400

def test_download_unauthorized(client, other_user_file):
    response = client.get(f"/api/files/{other_user_file.id}/download")
    assert response.status_code == 403

def test_delete_file(client, user_file, auth_headers):
    response = client.delete(
        f"/api/files/{user_file.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
```

---

## Rollback Plan

**Rollback Steps**:
1. Backup location: `./backups/[timestamp]/`
2. Stop application
3. Restore code from backup
4. Rollback database migration (uploads table)
5. S3 files remain (can be cleaned up later)
6. Restart application

**Rollback Time**: 5 minutes

---

## Tags for Domain Zero Workflow

- `@user-review` - File upload implementation complete
- `@security-review` - Ready for Megumi
- `@approved` - Production-ready

---

**Template Version**: 1.0
**Last Updated**: 2025-11-05
**Domain Zero Protocol**: v5.1
