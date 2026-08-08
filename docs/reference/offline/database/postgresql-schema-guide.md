# PostgreSQL & Schema Design Guide
<!-- Domain Zero Protocol v9.12.1 - Offline Reference -->

**Agent**: Todo (Database & Backend Specialist)
**Last Updated**: 2025-12-26
**Sources**: [PostgreSQL Docs](https://www.postgresql.org/docs/), [Bytebase](https://www.bytebase.com/)

---

## Table of Contents

1. [Schema Design Principles](#schema-design-principles)
2. [Naming Conventions](#naming-conventions)
3. [Data Types](#data-types)
4. [Constraints](#constraints)
5. [Indexing Strategies](#indexing-strategies)
6. [Normalization](#normalization)
7. [Query Optimization](#query-optimization)
8. [Migrations](#migrations)
9. [Common Patterns](#common-patterns)
10. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## Schema Design Principles

### Core Principles

1. **Start Normalized, Denormalize When Necessary**
   - Begin with 3NF (Third Normal Form)
   - Denormalize only with measured performance need

2. **Design for Queries, Not Storage**
   - Understand access patterns before designing
   - Optimize for common queries

3. **Use Constraints for Data Integrity**
   - Database-level constraints are more reliable than application code
   - Constraints document business rules

4. **Plan for Change**
   - Design schemas that can evolve
   - Use migrations for all changes

---

## Naming Conventions

### Tables

```sql
-- Use plural, snake_case
CREATE TABLE users (...)
CREATE TABLE order_items (...)
CREATE TABLE user_preferences (...)

-- Junction tables: alphabetical order
CREATE TABLE products_tags (...)  -- Not tags_products
```

### Columns

```sql
-- Primary keys: id
id SERIAL PRIMARY KEY

-- Foreign keys: singular_table_id
user_id INTEGER REFERENCES users(id)
order_id INTEGER REFERENCES orders(id)

-- Timestamps: verb_at
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP
deleted_at TIMESTAMP  -- Soft delete

-- Booleans: is_/has_/can_
is_active BOOLEAN DEFAULT true
has_verified_email BOOLEAN DEFAULT false
can_edit BOOLEAN DEFAULT false

-- Status columns: descriptive
status VARCHAR(20) CHECK (status IN ('pending', 'active', 'completed'))
```

### Indexes

```sql
-- idx_table_column(s)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id_created_at ON orders(user_id, created_at);

-- Unique indexes: uniq_
CREATE UNIQUE INDEX uniq_users_email ON users(email);
```

### Constraints

```sql
-- Primary key: pk_table
CONSTRAINT pk_users PRIMARY KEY (id)

-- Foreign key: fk_table_referenced
CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)

-- Unique: uniq_table_column(s)
CONSTRAINT uniq_users_email UNIQUE (email)

-- Check: chk_table_description
CONSTRAINT chk_users_age_positive CHECK (age > 0)
```

---

## Data Types

### Choosing the Right Type

| Use Case | Type | Notes |
|----------|------|-------|
| Primary Key | `SERIAL` / `BIGSERIAL` | Auto-increment |
| UUID Key | `UUID` | Use `gen_random_uuid()` |
| Short text | `VARCHAR(n)` | Known max length |
| Long text | `TEXT` | Unlimited length |
| Integer | `INTEGER` | -2B to 2B |
| Big integer | `BIGINT` | Larger range |
| Decimal | `NUMERIC(p,s)` | Exact precision (money) |
| Float | `DOUBLE PRECISION` | Approximate (science) |
| Boolean | `BOOLEAN` | true/false |
| Date | `DATE` | Date only |
| Time | `TIME` | Time only |
| Timestamp | `TIMESTAMPTZ` | Always use with timezone |
| JSON | `JSONB` | Binary, indexed, preferred |
| Array | `type[]` | Native arrays |
| IP Address | `INET` | IPv4/IPv6 |
| UUID | `UUID` | 128-bit identifier |

### Type Best Practices

```sql
-- Money: Use NUMERIC, not FLOAT
price NUMERIC(10, 2)  -- Up to 99,999,999.99

-- Timestamps: Always use TIMESTAMPTZ
created_at TIMESTAMPTZ DEFAULT NOW()

-- JSON: Prefer JSONB over JSON
metadata JSONB DEFAULT '{}'::jsonb

-- Enums: Consider VARCHAR with CHECK
status VARCHAR(20) CHECK (status IN ('draft', 'published', 'archived'))
-- OR
CREATE TYPE article_status AS ENUM ('draft', 'published', 'archived');
status article_status DEFAULT 'draft'
```

---

## Constraints

### Primary Keys

```sql
-- Auto-increment
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

-- UUID
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL
);

-- Composite
CREATE TABLE order_items (
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

### Foreign Keys

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- With explicit constraint name and actions
    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ON DELETE options:
-- CASCADE: Delete child rows
-- SET NULL: Set FK to NULL
-- SET DEFAULT: Set FK to default value
-- RESTRICT: Prevent deletion (default)
-- NO ACTION: Check at end of transaction
```

### Unique Constraints

```sql
-- Single column
email VARCHAR(255) UNIQUE

-- Multiple columns
CONSTRAINT uniq_user_org UNIQUE (user_id, organization_id)

-- Partial unique (unique among active)
CREATE UNIQUE INDEX uniq_active_email
    ON users(email)
    WHERE deleted_at IS NULL;
```

### Check Constraints

```sql
-- Single condition
age INTEGER CHECK (age >= 0 AND age <= 150)

-- Named constraint
CONSTRAINT chk_positive_price CHECK (price > 0)

-- Multiple conditions
CONSTRAINT chk_valid_date_range
    CHECK (start_date < end_date)

-- Enum-like
status VARCHAR(20) CHECK (status IN ('active', 'inactive', 'pending'))
```

### Not Null

```sql
-- Required fields
email VARCHAR(255) NOT NULL,
name VARCHAR(100) NOT NULL,

-- With default
is_active BOOLEAN NOT NULL DEFAULT true,
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

---

## Indexing Strategies

### When to Create Indexes

1. **Primary keys** (automatic)
2. **Foreign keys** (create manually)
3. **Columns in WHERE clauses**
4. **Columns in JOIN conditions**
5. **Columns in ORDER BY**
6. **Columns with high selectivity**

### Index Types

```sql
-- B-tree (default, most common)
CREATE INDEX idx_users_email ON users(email);

-- Hash (equality only)
CREATE INDEX idx_users_email_hash ON users USING hash(email);

-- GIN (arrays, JSONB, full-text)
CREATE INDEX idx_posts_tags ON posts USING gin(tags);
CREATE INDEX idx_users_metadata ON users USING gin(metadata);

-- GiST (geometric, full-text)
CREATE INDEX idx_locations_point ON locations USING gist(point);

-- BRIN (large tables, sorted data)
CREATE INDEX idx_logs_created_at ON logs USING brin(created_at);
```

### Composite Indexes

```sql
-- Order matters! Left-to-right
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);

-- Supports queries:
-- WHERE user_id = 1
-- WHERE user_id = 1 AND created_at > '2024-01-01'

-- Does NOT support:
-- WHERE created_at > '2024-01-01'  (without user_id)
```

### Partial Indexes

```sql
-- Index only relevant rows
CREATE INDEX idx_active_users_email
    ON users(email)
    WHERE is_active = true;

-- Index only non-null values
CREATE INDEX idx_orders_shipped
    ON orders(shipped_at)
    WHERE shipped_at IS NOT NULL;
```

### Expression Indexes

```sql
-- Index on function result
CREATE INDEX idx_users_lower_email
    ON users(LOWER(email));

-- Use in query
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';
```

---

## Normalization

### First Normal Form (1NF)

- Atomic values (no arrays in columns)
- No repeating groups

```sql
-- Bad (not 1NF)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    product_names VARCHAR(1000)  -- "Shirt, Pants, Shoes"
);

-- Good (1NF)
CREATE TABLE order_items (
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    PRIMARY KEY (order_id, product_id)
);
```

### Second Normal Form (2NF)

- In 1NF
- No partial dependencies on composite key

```sql
-- Bad (not 2NF) - product_name depends only on product_id
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    product_name VARCHAR(100),  -- Partial dependency
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);

-- Good (2NF)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE order_items (
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);
```

### Third Normal Form (3NF)

- In 2NF
- No transitive dependencies

```sql
-- Bad (not 3NF) - city depends on zip_code, not user
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    zip_code VARCHAR(10),
    city VARCHAR(100)  -- Transitive dependency
);

-- Good (3NF)
CREATE TABLE zip_codes (
    code VARCHAR(10) PRIMARY KEY,
    city VARCHAR(100)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    zip_code VARCHAR(10) REFERENCES zip_codes(code)
);
```

---

## Query Optimization

### Using EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'test@example.com';

-- Output interpretation:
-- Seq Scan: Full table scan (bad for large tables)
-- Index Scan: Using index (good)
-- Bitmap Index Scan: Using index for multiple rows
-- Hash Join: Join using hash table
-- Nested Loop: Join comparing each row
```

### Common Optimizations

```sql
-- Use specific columns instead of *
SELECT id, name, email FROM users;  -- Good
SELECT * FROM users;                 -- Avoid

-- Use LIMIT for pagination
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- Use EXISTS instead of COUNT for existence check
-- Bad
SELECT COUNT(*) FROM orders WHERE user_id = 1;
-- Good
SELECT EXISTS(SELECT 1 FROM orders WHERE user_id = 1);

-- Use IN instead of multiple ORs
-- Bad
WHERE status = 'a' OR status = 'b' OR status = 'c'
-- Good
WHERE status IN ('a', 'b', 'c')

-- Avoid functions on indexed columns in WHERE
-- Bad (can't use index)
WHERE LOWER(email) = 'test@example.com'
-- Good (with expression index)
CREATE INDEX idx_users_lower_email ON users(LOWER(email));
WHERE LOWER(email) = 'test@example.com'
```

### Query Analysis Checklist

1. Check for missing indexes on WHERE/JOIN columns
2. Verify statistics are current: `ANALYZE table_name`
3. Look for sequential scans on large tables
4. Check for expensive sorts
5. Review join strategies

---

## Migrations

### Migration Best Practices

1. **One change per migration**
2. **Make migrations reversible**
3. **Test migrations on production-like data**
4. **Use transactions where possible**

### Alembic (Python/SQLAlchemy)

```python
# alembic/versions/001_create_users.py
"""Create users table"""

from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

### Safe Migration Patterns

```sql
-- Adding column (safe)
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Adding NOT NULL column (use default)
ALTER TABLE users ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active';

-- Renaming column (use new + copy + drop)
ALTER TABLE users ADD COLUMN full_name VARCHAR(200);
UPDATE users SET full_name = name;
ALTER TABLE users DROP COLUMN name;

-- Creating index concurrently (no lock)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Dropping column (make nullable first)
ALTER TABLE users ALTER COLUMN old_column DROP NOT NULL;
-- Later migration
ALTER TABLE users DROP COLUMN old_column;
```

---

## Common Patterns

### Soft Delete

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT uniq_active_email UNIQUE (email)
        WHERE deleted_at IS NULL
);

-- Soft delete
UPDATE users SET deleted_at = NOW() WHERE id = 1;

-- Query active only
SELECT * FROM users WHERE deleted_at IS NULL;
```

### Audit Trail

```sql
CREATE TABLE users_audit (
    audit_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by INTEGER
);

-- Trigger function
CREATE OR REPLACE FUNCTION audit_users()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO users_audit (user_id, action, new_data)
        VALUES (NEW.id, 'INSERT', to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO users_audit (user_id, action, old_data, new_data)
        VALUES (NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO users_audit (user_id, action, old_data)
        VALUES (OLD.id, 'DELETE', to_jsonb(OLD));
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_users();
```

### Timestamps

```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_update_timestamp
    BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
```

### Full-Text Search

```sql
-- Add search vector column
ALTER TABLE posts ADD COLUMN search_vector tsvector;

-- Create index
CREATE INDEX idx_posts_search ON posts USING gin(search_vector);

-- Update search vector
UPDATE posts SET search_vector =
    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(body, ''));

-- Search query
SELECT * FROM posts
WHERE search_vector @@ plainto_tsquery('english', 'search term')
ORDER BY ts_rank(search_vector, plainto_tsquery('english', 'search term')) DESC;
```

---

## Anti-Patterns to Avoid

### 1. Entity-Attribute-Value (EAV)

```sql
-- BAD: EAV pattern
CREATE TABLE attributes (
    entity_id INTEGER,
    attribute_name VARCHAR(100),
    attribute_value TEXT
);

-- GOOD: Proper schema or JSONB
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    attributes JSONB
);
```

### 2. Storing Lists in Strings

```sql
-- BAD
tags VARCHAR(1000)  -- "tag1,tag2,tag3"

-- GOOD
tags TEXT[]  -- ARRAY['tag1', 'tag2', 'tag3']
-- OR junction table
```

### 3. Missing Foreign Keys

```sql
-- BAD: No referential integrity
user_id INTEGER

-- GOOD: With foreign key
user_id INTEGER REFERENCES users(id)
```

### 4. Over-Denormalization

```sql
-- BAD: Redundant data
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    user_name VARCHAR(100),  -- Redundant!
    user_email VARCHAR(255)  -- Redundant!
);

-- GOOD: Normalized with JOIN
SELECT o.*, u.name, u.email
FROM orders o
JOIN users u ON o.user_id = u.id;
```

### 5. Using FLOAT for Money

```sql
-- BAD
price FLOAT

-- GOOD
price NUMERIC(10, 2)
```

---

**Online References**:
- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/)
- [Use The Index, Luke](https://use-the-index-luke.com/)
- [Bytebase Schema Design](https://www.bytebase.com/blog/top-database-schema-design-best-practices/)
