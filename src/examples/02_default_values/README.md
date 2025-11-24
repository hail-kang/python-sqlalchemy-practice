# 02. Default Values - Python-level vs Database-level

## What Are Default Values

Default values are automatically assigned to columns when no value is provided during insert. SQLAlchemy provides two approaches: Python-level (`default=`) and database-level (`server_default=`).

## Database-level Defaults (server_default)

```python
from sqlalchemy import func, String
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    username: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="active"  # Database sets this
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()  # Database function
    )
```

**How it works:**
- Default value is defined in database schema (DDL)
- Database engine applies the default during INSERT
- SQLAlchemy doesn't know the value until after commit/refresh

**Generated SQL:**
```sql
CREATE TABLE users (
    username VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Python-level Defaults (default)

```python
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    username: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(
        String(20),
        default="active"  # Python sets this
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)  # Python function
    )
```

**How it works:**
- Default value is computed in Python before INSERT
- SQLAlchemy sets the value on the object immediately
- Value is available without refresh

**Generated SQL:**
```sql
CREATE TABLE users (
    username VARCHAR(50),
    status VARCHAR(20),  -- No DEFAULT clause
    created_at TIMESTAMP
);

-- On insert, Python provides the values:
INSERT INTO users (username, status, created_at)
VALUES ('john', 'active', '2024-01-15 10:30:00+00:00');
```

## Key Differences

| Aspect | `server_default=` | `default=` |
|--------|------------------|------------|
| **Where computed** | Database | Python |
| **When computed** | During INSERT | Before INSERT |
| **Immediate access** | ❌ Need refresh | ✅ Available instantly |
| **Database independence** | ❌ DB-specific | ✅ Works anywhere |
| **Raw SQL inserts** | ✅ Works | ❌ Ignored |
| **Testing** | ❌ Need database | ✅ No database needed |
| **Complex logic** | ❌ Limited to SQL | ✅ Full Python |

## When to Use Each

### Use `server_default=` when:

✅ **Working with legacy databases**
```python
# Database already has DEFAULT constraint
legacy_column: Mapped[str] = mapped_column(
    String(20),
    server_default="pending"
)
```

✅ **Need defaults for raw SQL inserts**
```python
# Apps besides SQLAlchemy insert data
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now()
)
```

✅ **Database-enforced constraints**
```python
# Want database to guarantee default regardless of client
version: Mapped[int] = mapped_column(server_default="1")
```

### Use `default=` when:

✅ **Need immediate access to default value**
```python
user = User(username="john")
print(user.status)  # "active" - no database access needed
```

✅ **Complex Python logic**
```python
import uuid

# Database can't generate UUIDs this way
user_id: Mapped[str] = mapped_column(
    String(36),
    default=lambda: str(uuid.uuid4())
)
```

✅ **Database independence**
```python
# Works same on SQLite, PostgreSQL, MySQL
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc)
)
```

✅ **Easier testing**
```python
# Can test without database
def test_user_defaults():
    user = User(username="test")
    assert user.status == "active"  # Works without db
```

## Real Examples from Our Project

Our project uses **Python-level defaults** exclusively:

```python
# src/models/base.py
class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),  # Python-level
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

**Why Python-level?**
- ✅ Works on SQLite (dev), PostgreSQL (prod) identically
- ✅ Can test models without database
- ✅ Immediate access to timestamps
- ✅ Explicit UTC timezone handling
- ✅ No database-specific functions needed

## Common Patterns

### Static Defaults
```python
# Both work the same for static values
status: Mapped[str] = mapped_column(default="pending")
status: Mapped[str] = mapped_column(server_default="pending")
```

### Callable Defaults (Python-level only)
```python
# Use lambda for dynamic values
created_at: Mapped[datetime] = mapped_column(
    default=lambda: datetime.now(timezone.utc)
)

# Use regular function
def generate_api_key():
    return secrets.token_urlsafe(32)

api_key: Mapped[str] = mapped_column(String(50), default=generate_api_key)
```

### Database Functions (Database-level only)
```python
from sqlalchemy import func

# PostgreSQL
created_at: Mapped[datetime] = mapped_column(server_default=func.now())

# MySQL
created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

# Note: func.now() translates to different SQL per database
```

### Both Together
```python
# Can use both (Python default + database fallback)
status: Mapped[str] = mapped_column(
    String(20),
    default="active",           # SQLAlchemy ORM inserts
    server_default="active"     # Raw SQL inserts
)
```

## Migration Example

If converting database defaults to Python defaults:

```python
# Before: Database-level
class User(Base):
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="active"
    )

# After: Python-level
class User(Base):
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False
    )
```

**Migration steps:**
1. Add Python `default=` to model
2. Create migration to remove database `DEFAULT` constraint
3. Existing rows keep their values
4. New inserts use Python default

## Summary

**Use Python-level defaults (`default=`) when:**
- You control all inserts via SQLAlchemy ORM
- Need database independence
- Want immediate access to default values
- Require complex logic or external libraries
- Testing without database

**Use Database-level defaults (`server_default=`) when:**
- Working with legacy databases
- Multiple applications insert data
- Raw SQL inserts must work
- Database must enforce defaults

**Our recommendation:** Python-level defaults for new projects - better testability, database independence, and immediate value access.
