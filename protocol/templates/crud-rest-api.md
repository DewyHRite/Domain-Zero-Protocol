# Template: RESTful CRUD API

## Overview

**Feature**: Complete Create, Read, Update, Delete (CRUD) REST API for a database entity

**Use Case**: Build production-ready REST API endpoints with full CRUD operations, validation, error handling, and security.

**Technology Stack**:
- Backend: Python (FastAPI), Node.js (Express), Django REST, or any REST framework
- Database: PostgreSQL, MySQL, MongoDB, SQLite
- ORM: SQLAlchemy (Python), Sequelize (Node.js), Mongoose (MongoDB)

**Estimated Time**:
- Implementation: 2-4 hours
- Testing: 1-2 hours
- Security Review: 30-45 minutes
- **Total**: 3.5-6.5 hours

---

## Prerequisites

Before implementing CRUD API, ensure:

- ✅ Database connection configured
- ✅ Database table/model created
- ✅ ORM/database library installed
- ✅ REST framework set up (FastAPI, Express, Django)
- ✅ Validation library available (Pydantic, Joi, Zod)
- ✅ Authentication middleware ready (if needed)
- ✅ Backup created

---

## Example Entity: "Task" CRUD API

This template uses a **Task** entity as an example. Replace "Task" with your entity name.

**Task Schema**:
```json
{
  "id": 1,
  "title": "Implement user authentication",
  "description": "Add JWT-based auth to API",
  "status": "in_progress",  // pending, in_progress, completed
  "priority": "high",        // low, medium, high
  "created_at": "2025-11-05T10:30:00Z",
  "updated_at": "2025-11-05T12:45:00Z"
}
```

---

## Yuuji Implementation Checklist

### Phase 1: Database Model & Setup (30-45 minutes)

- [ ] **Create database model/schema**

  **Fields to include**:
  - `id` (Primary Key, Auto-increment)
  - Business logic fields (title, description, status, etc.)
  - `created_at` (Timestamp, auto-generated)
  - `updated_at` (Timestamp, auto-updated)

- [ ] **Create migration** (if using migrations)
  - `alembic revision --autogenerate -m "Add tasks table"` (Python/SQLAlchemy)
  - `npx sequelize-cli db:migrate` (Node.js/Sequelize)

- [ ] **Create validation schemas** (Pydantic, Joi)
  - `TaskCreate` schema (for POST requests)
  - `TaskUpdate` schema (for PUT/PATCH requests)
  - `TaskResponse` schema (for responses)

- [ ] **Create backup before proceeding**

### Phase 2: Write Tests First (TDD) (1-1.5 hours)

- [ ] **Test: GET /tasks** (List all tasks)
  - Returns empty array when no tasks exist
  - Returns array of tasks when tasks exist
  - Supports pagination (limit, offset)
  - Supports filtering by status
  - Returns 200 OK

- [ ] **Test: GET /tasks/{id}** (Get single task)
  - Returns task when ID exists
  - Returns 404 when ID doesn't exist
  - Returns correct task structure

- [ ] **Test: POST /tasks** (Create task)
  - Creates task with valid data
  - Returns 201 Created with task object
  - Generates ID automatically
  - Sets created_at automatically
  - Returns 400 on missing required fields
  - Returns 400 on invalid data types

- [ ] **Test: PUT /tasks/{id}** (Full update)
  - Updates task when ID exists
  - Returns 200 OK with updated task
  - Returns 404 when ID doesn't exist
  - Updates updated_at timestamp
  - Returns 400 on invalid data

- [ ] **Test: PATCH /tasks/{id}** (Partial update)
  - Updates only provided fields
  - Doesn't require all fields
  - Returns 200 OK

- [ ] **Test: DELETE /tasks/{id}** (Delete task)
  - Deletes task when ID exists
  - Returns 204 No Content
  - Returns 404 when ID doesn't exist
  - Task is actually removed from database

### Phase 3: Implement Endpoints (1.5-2 hours)

- [ ] **GET /tasks** - List all tasks
  ```
  Query params: ?limit=10&offset=0&status=pending
  Response: 200 OK
  Body: { "tasks": [...], "total": 100, "limit": 10, "offset": 0 }
  ```

- [ ] **GET /tasks/{id}** - Get single task
  ```
  Response: 200 OK | 404 Not Found
  Body: { "id": 1, "title": "...", ... }
  ```

- [ ] **POST /tasks** - Create task
  ```
  Request: { "title": "...", "description": "...", "status": "pending" }
  Response: 201 Created
  Body: { "id": 1, "title": "...", "created_at": "..." }
  ```

- [ ] **PUT /tasks/{id}** - Full update task
  ```
  Request: { "title": "...", "description": "...", "status": "completed" }
  Response: 200 OK | 404 Not Found
  Body: { "id": 1, "title": "...", "updated_at": "..." }
  ```

- [ ] **PATCH /tasks/{id}** - Partial update task
  ```
  Request: { "status": "completed" }
  Response: 200 OK | 404 Not Found
  ```

- [ ] **DELETE /tasks/{id}** - Delete task
  ```
  Response: 204 No Content | 404 Not Found
  ```

### Phase 4: Validation & Error Handling (30 minutes)

- [ ] Validate required fields (title, etc.)
- [ ] Validate data types (string, int, enum)
- [ ] Validate string lengths (title max 200 chars)
- [ ] Validate enum values (status: pending/in_progress/completed)
- [ ] Return 400 Bad Request with clear error messages
- [ ] Return 404 Not Found for non-existent IDs
- [ ] Return 500 Internal Server Error with logging (no stack traces to client)

### Phase 5: Documentation & Rollback (20 minutes)

- [ ] Document API endpoints in OpenAPI/Swagger
- [ ] Create rollback plan in dev-notes.md
- [ ] Document database schema
- [ ] Tag @user-review when complete

---

## Code Template

### Python (FastAPI) Implementation

```python
# models/task.py
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from database import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# schemas/task.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from models.task import TaskStatus, TaskPriority

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # For SQLAlchemy models


# routes/tasks.py
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.task import Task, TaskStatus
from schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", response_model=dict)
async def list_tasks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[TaskStatus] = None,
    db: Session = Depends(get_db)
):
    """List all tasks with pagination and optional filtering."""
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)

    total = query.count()
    tasks = query.offset(offset).limit(limit).all()

    return {
        "tasks": tasks,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a single task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )

    return task

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    task = Task(**task_data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task (full update - all fields required)."""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )

    # Update all provided fields
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task

@router.patch("/{task_id}", response_model=TaskResponse)
async def partial_update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Partially update a task (only provided fields)."""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )

    # Update only provided fields
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )

    db.delete(task)
    db.commit()

    return None  # 204 No Content
```

### Node.js (Express + Sequelize) Implementation

```javascript
// models/Task.js
const { DataTypes } = require('sequelize');
const sequelize = require('../database');

const Task = sequelize.define('Task', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  title: {
    type: DataTypes.STRING(200),
    allowNull: false,
    validate: {
      notEmpty: true,
      len: [1, 200]
    }
  },
  description: {
    type: DataTypes.STRING(1000),
    allowNull: true
  },
  status: {
    type: DataTypes.ENUM('pending', 'in_progress', 'completed'),
    defaultValue: 'pending'
  },
  priority: {
    type: DataTypes.ENUM('low', 'medium', 'high'),
    defaultValue: 'medium'
  }
}, {
  timestamps: true,  // Adds createdAt and updatedAt
  tableName: 'tasks'
});

module.exports = Task;


// routes/tasks.js
const express = require('express');
const { body, param, query, validationResult } = require('express-validator');
const Task = require('../models/Task');

const router = express.Router();

// Validation middleware
const validateTask = [
  body('title').isString().isLength({ min: 1, max: 200 }),
  body('description').optional().isString().isLength({ max: 1000 }),
  body('status').optional().isIn(['pending', 'in_progress', 'completed']),
  body('priority').optional().isIn(['low', 'medium', 'high'])
];

const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

// GET /tasks - List all tasks
router.get('/', [
  query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
  query('offset').optional().isInt({ min: 0 }).toInt(),
  query('status').optional().isIn(['pending', 'in_progress', 'completed'])
], async (req, res) => {
  try {
    const limit = req.query.limit || 10;
    const offset = req.query.offset || 0;
    const status = req.query.status;

    const where = status ? { status } : {};

    const { count, rows } = await Task.findAndCountAll({
      where,
      limit,
      offset,
      order: [['created_at', 'DESC']]
    });

    res.json({
      tasks: rows,
      total: count,
      limit,
      offset
    });
  } catch (error) {
    console.error('Error listing tasks:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /tasks/:id - Get single task
router.get('/:id', [
  param('id').isInt().toInt()
], async (req, res) => {
  try {
    const task = await Task.findByPk(req.params.id);

    if (!task) {
      return res.status(404).json({ error: `Task with ID ${req.params.id} not found` });
    }

    res.json(task);
  } catch (error) {
    console.error('Error getting task:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /tasks - Create task
router.post('/', validateTask, handleValidationErrors, async (req, res) => {
  try {
    const task = await Task.create(req.body);
    res.status(201).json(task);
  } catch (error) {
    console.error('Error creating task:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// PUT /tasks/:id - Update task (full)
router.put('/:id', [
  param('id').isInt().toInt(),
  ...validateTask
], handleValidationErrors, async (req, res) => {
  try {
    const task = await Task.findByPk(req.params.id);

    if (!task) {
      return res.status(404).json({ error: `Task with ID ${req.params.id} not found` });
    }

    await task.update(req.body);
    res.json(task);
  } catch (error) {
    console.error('Error updating task:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// PATCH /tasks/:id - Partial update
router.patch('/:id', [
  param('id').isInt().toInt(),
  body('title').optional().isString().isLength({ min: 1, max: 200 }),
  body('description').optional().isString().isLength({ max: 1000 }),
  body('status').optional().isIn(['pending', 'in_progress', 'completed']),
  body('priority').optional().isIn(['low', 'medium', 'high'])
], handleValidationErrors, async (req, res) => {
  try {
    const task = await Task.findByPk(req.params.id);

    if (!task) {
      return res.status(404).json({ error: `Task with ID ${req.params.id} not found` });
    }

    await task.update(req.body);
    res.json(task);
  } catch (error) {
    console.error('Error updating task:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// DELETE /tasks/:id - Delete task
router.delete('/:id', [
  param('id').isInt().toInt()
], async (req, res) => {
  try {
    const task = await Task.findByPk(req.params.id);

    if (!task) {
      return res.status(404).json({ error: `Task with ID ${req.params.id} not found` });
    }

    await task.destroy();
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting task:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
```

---

## Megumi Security Checklist

### Critical Security Requirements

- [ ] **SQL Injection Protection**
  - ✅ Using parameterized queries (ORM)
  - ✅ Never concatenating user input into SQL strings
  - ✅ Input validation on all fields
  - ❌ SEC-001: If raw SQL with concatenation → CRITICAL

- [ ] **Input Validation**
  - ✅ All fields validated (type, length, format)
  - ✅ Enum values validated (status, priority)
  - ✅ String length limits enforced
  - ✅ Reject unexpected fields
  - ❌ SEC-002: If no validation → HIGH

- [ ] **Authorization** (if authentication required)
  - ✅ Users can only access their own tasks
  - ✅ Cannot modify other users' tasks
  - ✅ Admin role for unrestricted access (if applicable)
  - ❌ SEC-003: If no authorization checks → CRITICAL

- [ ] **Rate Limiting**
  - ✅ POST /tasks limited (prevent spam)
  - ✅ GET /tasks limited (prevent DoS)
  - ❌ SEC-004: If no rate limiting → MEDIUM

- [ ] **Mass Assignment Protection**
  - ✅ Only allowed fields can be set (Pydantic, Joi)
  - ✅ Cannot set `id`, `created_at` via API
  - ❌ SEC-005: If all fields settable → HIGH

- [ ] **Error Handling**
  - ✅ No stack traces in responses (production)
  - ✅ Generic error messages (don't leak DB structure)
  - ✅ Errors logged server-side
  - ❌ SEC-006: If stack traces exposed → MEDIUM

- [ ] **Pagination Limits**
  - ✅ Maximum limit enforced (e.g., 100)
  - ✅ Prevents fetching entire table
  - ❌ SEC-007: If unlimited pagination → LOW

### OWASP Top 10 Verification

| OWASP Category | Check | Status |
|----------------|-------|--------|
| A01: Broken Access Control | Authorization for task ownership | ✅ |
| A03: Injection | Parameterized queries, input validation | ✅ |
| A04: Insecure Design | Pagination, rate limiting | ✅ |
| A05: Security Misconfiguration | Error handling, no debug mode | ✅ |
| A08: Software/Data Integrity | Input validation, schema enforcement | ✅ |

### Performance Review

- [ ] Database indexes on frequently queried fields (id, status)
- [ ] Pagination implemented (not fetching all records)
- [ ] Query optimization (SELECT only needed fields)
- [ ] Connection pooling configured
- [ ] N+1 query problem avoided

---

## Common Pitfalls

### ❌ Pitfall 1: No Input Validation
```python
# WRONG - No validation
@router.post("/tasks")
def create_task(task: dict):
    task = Task(**task)  # Dangerous!
```
**Fix**: Use validation schemas
```python
# CORRECT
@router.post("/tasks")
def create_task(task: TaskCreate):  # Pydantic validates
    ...
```

### ❌ Pitfall 2: SQL Injection via Raw Queries
```python
# WRONG - SQL injection vulnerability
@router.get("/tasks")
def list_tasks(status: str):
    query = f"SELECT * FROM tasks WHERE status = '{status}'"
    # If status = "'; DROP TABLE tasks; --", you're hacked!
```
**Fix**: Use ORM or parameterized queries
```python
# CORRECT
query = db.query(Task).filter(Task.status == status)
```

### ❌ Pitfall 3: No Authorization Checks
```python
# WRONG - Any user can delete any task
@router.delete("/tasks/{id}")
def delete_task(id: int):
    task = get_task(id)
    task.delete()
```
**Fix**: Check ownership
```python
# CORRECT
@router.delete("/tasks/{id}")
def delete_task(id: int, current_user: User = Depends(get_current_user)):
    task = get_task(id)
    if task.user_id != current_user.id:
        raise HTTPException(403, "Forbidden")
    task.delete()
```

### ❌ Pitfall 4: Unlimited Pagination
```python
# WRONG - Can fetch 1 million records
@router.get("/tasks")
def list_tasks(limit: int):
    return db.query(Task).limit(limit).all()
```
**Fix**: Enforce maximum limit
```python
# CORRECT
@router.get("/tasks")
def list_tasks(limit: int = Query(10, ge=1, le=100)):  # Max 100
    ...
```

### ❌ Pitfall 5: Exposing Stack Traces
```python
# WRONG - Leaks internal details
try:
    task = get_task(id)
except Exception as e:
    return {"error": str(e)}  # Exposes DB structure!
```
**Fix**: Generic errors in production
```python
# CORRECT
try:
    task = get_task(id)
except Exception as e:
    logger.error(f"Error: {e}")  # Log internally
    return {"error": "Internal server error"}  # Generic to client
```

---

## Testing Strategy

### Test Coverage Goals
- **Unit Tests**: 100% (models, schemas)
- **Integration Tests**: 100% (all endpoints)
- **Edge Cases**: All error scenarios

### Example Tests (pytest)

```python
def test_list_tasks_empty(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json()["tasks"] == []
    assert response.json()["total"] == 0

def test_create_task_success(client):
    response = client.post("/tasks", json={
        "title": "Test task",
        "description": "Testing CRUD",
        "status": "pending"
    })
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["title"] == "Test task"

def test_create_task_missing_title(client):
    response = client.post("/tasks", json={
        "description": "No title provided"
    })
    assert response.status_code == 400

def test_get_task_success(client, sample_task):
    response = client.get(f"/tasks/{sample_task.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_task.id

def test_get_task_not_found(client):
    response = client.get("/tasks/99999")
    assert response.status_code == 404

def test_update_task_success(client, sample_task):
    response = client.put(f"/tasks/{sample_task.id}", json={
        "title": "Updated title",
        "status": "completed"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    assert response.json()["status"] == "completed"

def test_delete_task_success(client, sample_task):
    response = client.delete(f"/tasks/{sample_task.id}")
    assert response.status_code == 204

    # Verify it's actually deleted
    response = client.get(f"/tasks/{sample_task.id}")
    assert response.status_code == 404

def test_pagination(client, ten_tasks):
    response = client.get("/tasks?limit=5&offset=0")
    assert len(response.json()["tasks"]) == 5
    assert response.json()["total"] == 10

def test_filter_by_status(client, tasks_with_different_statuses):
    response = client.get("/tasks?status=completed")
    tasks = response.json()["tasks"]
    assert all(task["status"] == "completed" for task in tasks)
```

---

## Rollback Plan

If CRUD API causes issues:

**Rollback Steps**:
1. Locate backup: `./backups/[timestamp]/`
2. Stop application
3. Restore code from backup
4. Rollback database migration: `alembic downgrade -1`
5. Restart application
6. Verify old endpoints work
7. Check database integrity

**Rollback Time Estimate**: 5-10 minutes

**Rollback Verification**:
- [ ] Application starts successfully
- [ ] Database schema reverted
- [ ] Existing data intact
- [ ] No CRUD-related errors

---

## API Documentation Example (OpenAPI/Swagger)

```yaml
paths:
  /tasks:
    get:
      summary: List all tasks
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 10
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, in_progress, completed]
      responses:
        200:
          description: Success
    post:
      summary: Create a new task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskCreate'
      responses:
        201:
          description: Task created
        400:
          description: Invalid input
```

---

## Tags for Domain Zero Workflow

- `@user-review` - CRUD implementation complete
- `@security-review` - Ready for Megumi
- `@approved` - Production-ready

---

**Template Version**: 1.0
**Last Updated**: 2025-11-05
**Domain Zero Protocol**: v5.1
**Estimated Success Rate**: 95%
