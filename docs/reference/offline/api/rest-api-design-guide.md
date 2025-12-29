# REST API Design Guide
<!-- Domain Zero Protocol v8.11.0 - Offline Reference -->

**Agent**: Inumaki (API & Communication Specialist)
**Last Updated**: 2025-12-26
**Sources**: [Zalando Guidelines](https://opensource.zalando.com/restful-api-guidelines/), [Microsoft API Guidelines](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Resource Design](#resource-design)
3. [HTTP Methods](#http-methods)
4. [Status Codes](#status-codes)
5. [Request/Response Design](#requestresponse-design)
6. [Error Handling](#error-handling)
7. [Pagination](#pagination)
8. [Filtering and Sorting](#filtering-and-sorting)
9. [Versioning](#versioning)
10. [Security](#security)
11. [OpenAPI Specification](#openapi-specification)

---

## Core Principles

### API First Design

1. **Design API before implementation**
2. **Use OpenAPI specification**
3. **Get peer review on API design**
4. **Consider API as a product**

### REST Constraints

| Constraint | Description |
|------------|-------------|
| **Client-Server** | Separation of concerns |
| **Stateless** | No session state on server |
| **Cacheable** | Responses indicate cacheability |
| **Uniform Interface** | Consistent resource identification |
| **Layered System** | Client doesn't know intermediaries |

---

## Resource Design

### Naming Conventions

```
# Use plural nouns for collections
GET /users
GET /orders
GET /products

# Use singular for singletons
GET /users/123
GET /me (current user)

# Use kebab-case for multi-word
GET /user-profiles
GET /order-items

# Avoid verbs in paths (use HTTP methods)
# Bad:
GET /getUsers
POST /createOrder

# Good:
GET /users
POST /orders
```

### Resource Hierarchy

```
# Sub-resources for clear relationships
GET /users/123/orders          # Orders for user 123
GET /users/123/orders/456      # Order 456 for user 123

# Keep hierarchy shallow (max 3 levels)
# Bad:
GET /organizations/1/departments/2/teams/3/members/4

# Good:
GET /teams/3/members
GET /members/4
```

### Resource Relationships

```
# Embedding related resources
GET /orders/123?expand=items,customer

# Response:
{
  "id": 123,
  "customer": {
    "id": 456,
    "name": "John Doe"
  },
  "items": [
    { "id": 1, "product_id": 789, "quantity": 2 }
  ]
}

# Linking to related resources
{
  "id": 123,
  "_links": {
    "self": { "href": "/orders/123" },
    "customer": { "href": "/customers/456" },
    "items": { "href": "/orders/123/items" }
  }
}
```

---

## HTTP Methods

### Method Semantics

| Method | Usage | Idempotent | Safe |
|--------|-------|------------|------|
| `GET` | Retrieve resource | Yes | Yes |
| `POST` | Create resource | No | No |
| `PUT` | Replace resource | Yes | No |
| `PATCH` | Partial update | No | No |
| `DELETE` | Remove resource | Yes | No |

### Method Examples

```
# GET - Retrieve
GET /users/123
GET /users?status=active

# POST - Create
POST /users
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com"
}

# PUT - Full replacement
PUT /users/123
Content-Type: application/json

{
  "id": 123,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "status": "active"
}

# PATCH - Partial update
PATCH /users/123
Content-Type: application/json

{
  "email": "newemail@example.com"
}

# DELETE - Remove
DELETE /users/123
```

### Special Actions

```
# Use POST for non-CRUD actions
POST /orders/123/cancel
POST /users/123/verify-email
POST /documents/123/publish

# Batch operations
POST /users/batch
Content-Type: application/json

{
  "operations": [
    { "method": "create", "data": { "name": "User 1" } },
    { "method": "update", "id": 123, "data": { "name": "Updated" } }
  ]
}
```

---

## Status Codes

### Success Codes (2xx)

| Code | Meaning | Usage |
|------|---------|-------|
| `200` | OK | General success |
| `201` | Created | Resource created |
| `202` | Accepted | Async processing started |
| `204` | No Content | Success with no body |

```
# 200 OK - GET success
GET /users/123
HTTP/1.1 200 OK

# 201 Created - POST success
POST /users
HTTP/1.1 201 Created
Location: /users/456

# 202 Accepted - Async operation
POST /reports/generate
HTTP/1.1 202 Accepted
Location: /jobs/789

# 204 No Content - DELETE success
DELETE /users/123
HTTP/1.1 204 No Content
```

### Client Error Codes (4xx)

| Code | Meaning | Usage |
|------|---------|-------|
| `400` | Bad Request | Invalid request body/params |
| `401` | Unauthorized | Missing/invalid authentication |
| `403` | Forbidden | Authenticated but not authorized |
| `404` | Not Found | Resource doesn't exist |
| `405` | Method Not Allowed | HTTP method not supported |
| `409` | Conflict | Resource state conflict |
| `422` | Unprocessable Entity | Validation failed |
| `429` | Too Many Requests | Rate limit exceeded |

### Server Error Codes (5xx)

| Code | Meaning | Usage |
|------|---------|-------|
| `500` | Internal Server Error | Unexpected server error |
| `502` | Bad Gateway | Upstream service error |
| `503` | Service Unavailable | Server overloaded/maintenance |
| `504` | Gateway Timeout | Upstream timeout |

---

## Request/Response Design

### Request Headers

```
# Required headers
Content-Type: application/json
Accept: application/json

# Authentication
Authorization: Bearer <token>

# Idempotency (for POST/PATCH)
Idempotency-Key: unique-request-id

# Request tracing
X-Request-ID: uuid-for-tracing
```

### Response Headers

```
# Content info
Content-Type: application/json; charset=utf-8

# Caching
Cache-Control: max-age=3600
ETag: "abc123"

# Rate limiting
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000

# CORS
Access-Control-Allow-Origin: https://example.com
```

### Response Body Structure

```json
// Single resource
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}

// Collection
{
  "data": [
    { "id": 1, "name": "Item 1" },
    { "id": 2, "name": "Item 2" }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  },
  "links": {
    "self": "/items?page=1",
    "next": "/items?page=2",
    "last": "/items?page=5"
  }
}
```

### Data Formats

```json
// Dates: ISO 8601
"created_at": "2024-01-15T10:30:00Z"

// Money: String with currency
"price": {
  "amount": "99.99",
  "currency": "USD"
}

// Enums: SCREAMING_SNAKE_CASE
"status": "PENDING_APPROVAL"

// Booleans: Never null
"is_active": true

// Null: Omit field or explicit null
"middle_name": null
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request body contains invalid data",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Email must be a valid email address"
      },
      {
        "field": "age",
        "code": "OUT_OF_RANGE",
        "message": "Age must be between 18 and 120"
      }
    ],
    "request_id": "req_abc123",
    "documentation_url": "https://api.example.com/docs/errors#VALIDATION_ERROR"
  }
}
```

### Common Error Codes

```json
// 400 Bad Request - Malformed request
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Request body is not valid JSON"
  }
}

// 401 Unauthorized - Missing/invalid auth
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired access token"
  }
}

// 403 Forbidden - Not authorized
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to access this resource"
  }
}

// 404 Not Found
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User with ID 123 not found"
  }
}

// 409 Conflict
{
  "error": {
    "code": "CONFLICT",
    "message": "Email address already registered"
  }
}

// 422 Validation Error
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [...]
  }
}

// 429 Rate Limited
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Try again in 60 seconds",
    "retry_after": 60
  }
}
```

---

## Pagination

### Offset-Based Pagination

```
# Request
GET /users?page=2&per_page=20

# Response
{
  "data": [...],
  "meta": {
    "total": 95,
    "page": 2,
    "per_page": 20,
    "total_pages": 5
  },
  "links": {
    "first": "/users?page=1&per_page=20",
    "prev": "/users?page=1&per_page=20",
    "self": "/users?page=2&per_page=20",
    "next": "/users?page=3&per_page=20",
    "last": "/users?page=5&per_page=20"
  }
}
```

### Cursor-Based Pagination (Preferred)

```
# Request
GET /users?limit=20&cursor=eyJpZCI6MTIzfQ

# Response
{
  "data": [...],
  "meta": {
    "has_more": true,
    "next_cursor": "eyJpZCI6MTQzfQ"
  },
  "links": {
    "next": "/users?limit=20&cursor=eyJpZCI6MTQzfQ"
  }
}
```

### Why Cursor > Offset

| Aspect | Offset | Cursor |
|--------|--------|--------|
| Performance | Degrades with large offsets | Consistent |
| Data changes | May skip/duplicate items | Stable |
| Scalability | Poor | Good |
| Use case | Small datasets | Large/real-time datasets |

---

## Filtering and Sorting

### Filtering

```
# Simple equality
GET /users?status=active

# Multiple values (OR)
GET /users?status=active,pending

# Comparison operators
GET /orders?created_at[gte]=2024-01-01
GET /products?price[lt]=100

# Text search
GET /users?q=john

# Combined filters (AND)
GET /orders?status=pending&customer_id=123
```

### Sorting

```
# Single field
GET /users?sort=created_at

# Descending
GET /users?sort=-created_at

# Multiple fields
GET /users?sort=-created_at,name

# Response should reflect sort
{
  "data": [...],
  "meta": {
    "sort": [
      { "field": "created_at", "direction": "desc" },
      { "field": "name", "direction": "asc" }
    ]
  }
}
```

### Field Selection

```
# Select specific fields
GET /users?fields=id,name,email

# Nested fields
GET /orders?fields=id,total,customer.name

# Response only includes requested fields
{
  "data": [
    {
      "id": 123,
      "name": "John",
      "email": "john@example.com"
    }
  ]
}
```

---

## Versioning

### URI Versioning (Recommended)

```
GET /v1/users
GET /v2/users
```

### Header Versioning

```
GET /users
Accept: application/vnd.api+json; version=2
```

### Version Lifecycle

```
# Deprecation header
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2025 00:00:00 GMT
Link: </v2/users>; rel="successor-version"
```

### Breaking vs Non-Breaking Changes

**Non-Breaking (OK)**:
- Adding new endpoints
- Adding new optional fields
- Adding new enum values
- Making required field optional

**Breaking (Requires new version)**:
- Removing endpoints
- Removing fields
- Renaming fields
- Changing field types
- Making optional field required

---

## Security

### Authentication

```
# Bearer token (JWT)
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# API key (for server-to-server)
X-API-Key: sk_live_abc123
```

### Authorization

```json
// Include scopes in token
{
  "sub": "user_123",
  "scopes": ["read:users", "write:orders"]
}

// Check scope on each request
// 403 if scope missing
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Token missing required scope: write:orders"
  }
}
```

### Rate Limiting

```
# Response headers
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000

# 429 when exceeded
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after": 60
  }
}
```

### Input Validation

```python
# Always validate
from pydantic import BaseModel, EmailStr, conint

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    age: conint(ge=18, le=120)

# Sanitize output
def serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        # Don't expose internal fields
        # "password_hash": user.password_hash  # NEVER
    }
```

---

## OpenAPI Specification

### Basic Structure

```yaml
openapi: 3.1.0
info:
  title: User API
  version: 1.0.0
  description: API for managing users

servers:
  - url: https://api.example.com/v1
    description: Production

paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      tags: [Users]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: per_page
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'

    post:
      summary: Create user
      operationId: createUser
      tags: [Users]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '422':
          $ref: '#/components/responses/ValidationError'

components:
  schemas:
    User:
      type: object
      required: [id, email, name]
      properties:
        id:
          type: integer
        email:
          type: string
          format: email
        name:
          type: string

    CreateUser:
      type: object
      required: [email, name]
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 1
          maxLength: 100

    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string

  responses:
    ValidationError:
      description: Validation error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

---

## Quick Reference

### URL Design

```
# Collections
GET    /resources          # List
POST   /resources          # Create

# Items
GET    /resources/{id}     # Read
PUT    /resources/{id}     # Replace
PATCH  /resources/{id}     # Update
DELETE /resources/{id}     # Delete

# Sub-resources
GET    /resources/{id}/sub # List sub-resources
POST   /resources/{id}/sub # Create sub-resource

# Actions
POST   /resources/{id}/action
```

### Headers Checklist

```
# Request
Content-Type: application/json
Accept: application/json
Authorization: Bearer <token>
Idempotency-Key: <unique-id>  (POST/PATCH)

# Response
Content-Type: application/json
Cache-Control: <policy>
X-RateLimit-*: <values>
```

### Status Code Decision Tree

```
Success?
├── Yes
│   ├── Body? → 200 OK
│   ├── Created? → 201 Created
│   ├── Async? → 202 Accepted
│   └── No body? → 204 No Content
└── No
    ├── Client error?
    │   ├── Bad syntax? → 400
    │   ├── Auth missing? → 401
    │   ├── Forbidden? → 403
    │   ├── Not found? → 404
    │   ├── Conflict? → 409
    │   ├── Validation? → 422
    │   └── Rate limit? → 429
    └── Server error?
        └── 500, 502, 503, 504
```

---

**Online References**:
- [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/)
- [Microsoft REST API Guidelines](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
