# 03. Session Pool Management - Connection Pooling

## What is Connection Pooling?

Connection pooling reuses database connections instead of creating new ones for every request. This dramatically improves performance by:
- Avoiding connection creation overhead
- Limiting concurrent connections
- Managing connection lifecycle

SQLAlchemy uses connection pools automatically through the `Engine`.

## Example Files

This directory contains paired examples showing problems and solutions:

1. **No Pooling Problem**
   - `bad_no_pooling.py` - Creating new connection every time (slow!)
   - `good_with_pooling.py` - Reusing connections from pool (fast!)

2. **Pool Exhaustion Problem**
   - `bad_pool_exhaustion.py` - Not closing connections properly
   - `good_proper_cleanup.py` - Using context managers correctly

**Run them to see the difference:**
```bash
# See the problem
uv run python -m src.examples.03_session_pool.bad_no_pooling
uv run python -m src.examples.03_session_pool.bad_pool_exhaustion

# See the solution
uv run python -m src.examples.03_session_pool.good_with_pooling
uv run python -m src.examples.03_session_pool.good_proper_cleanup
```

## The Problem Without Pooling

```python
# Without pooling (naive approach)
for _ in range(100):
    engine = create_engine("postgresql://...")  # New connection every time!
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine.dispose()  # Close connection
```

**Problems:**
- 100 connection creations (slow!)
- Database overhead for auth/setup each time
- Poor performance under load

## With Connection Pooling (Default)

```python
# With pooling (SQLAlchemy default)
engine = create_engine("postgresql://...")  # Create once

for _ in range(100):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))  # Reuses connections from pool
```

**Benefits:**
- ✅ Connections reused from pool
- ✅ Fast - no creation overhead
- ✅ Efficient resource usage

## Pool Configuration

### Default Pool Settings

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    # Default pool settings (QueuePool)
    pool_size=5,              # Keep 5 connections open
    max_overflow=10,          # Allow 10 more connections if needed
    pool_timeout=30,          # Wait 30s for connection before error
    pool_recycle=3600,        # Recycle connections after 1 hour
    pool_pre_ping=False,      # Don't test connections before use
)
```

### Pool Parameters Explained

**`pool_size`** (default: 5)
- Number of connections kept open permanently
- These connections are always available in the pool
- Choose based on expected concurrent load

```python
# Light load - small pool
engine = create_engine(url, pool_size=2)

# Heavy load - larger pool
engine = create_engine(url, pool_size=20)
```

**`max_overflow`** (default: 10)
- Additional connections beyond `pool_size`
- Created when pool is exhausted
- Closed when returned to pool
- Total max connections = `pool_size + max_overflow`

```python
# Max 5 permanent + 10 temporary = 15 total connections
engine = create_engine(url, pool_size=5, max_overflow=10)

# No overflow - strict limit
engine = create_engine(url, pool_size=10, max_overflow=0)
```

**`pool_timeout`** (default: 30 seconds)
- How long to wait for connection from pool
- Raises `TimeoutError` if exceeded
- Set higher for slow queries, lower for fast APIs

```python
# API - fail fast
engine = create_engine(url, pool_timeout=5)

# Batch job - wait longer
engine = create_engine(url, pool_timeout=60)
```

**`pool_recycle`** (default: -1 = never)
- Recycle connections after N seconds
- Prevents stale connections
- Important for databases that close idle connections

```python
# MySQL closes connections after 8 hours
engine = create_engine(url, pool_recycle=3600)  # Recycle after 1 hour
```

**`pool_pre_ping`** (default: False)
- Test connection with `SELECT 1` before using
- Catches stale connections
- Slight performance cost but safer

```python
# Production - enable pre-ping for reliability
engine = create_engine(url, pool_pre_ping=True)
```

## Pool Types

### QueuePool (Default)

Best for most applications. Maintains a fixed pool of connections.

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    url,
    poolclass=QueuePool,  # Explicit (but it's the default)
    pool_size=5,
    max_overflow=10
)
```

**Use for:** Web apps, APIs, most production use cases

### NullPool (No Pooling)

Creates new connection for each request, no reuse.

```python
from sqlalchemy.pool import NullPool

engine = create_engine(url, poolclass=NullPool)
```

**Use for:**
- Development/debugging
- Serverless functions (AWS Lambda)
- Short-lived processes

### StaticPool (Single Connection)

One connection shared by all threads. Only for SQLite.

```python
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///db.sqlite",
    poolclass=StaticPool
)
```

**Use for:** SQLite in-memory databases, single-threaded apps

## Common Patterns

### Web Application (FastAPI/Flask)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure for web app
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=20,           # Handle concurrent requests
    max_overflow=10,        # Extra capacity for spikes
    pool_timeout=10,        # Fail fast for web requests
    pool_recycle=3600,      # Prevent stale connections
    pool_pre_ping=True,     # Reliability over slight performance cost
    echo=False              # Disable SQL logging in production
)

SessionLocal = sessionmaker(bind=engine)

# Use in request handler
def get_users():
    with SessionLocal() as session:
        return session.execute(select(User)).scalars().all()
```

### Background Worker/Celery

```python
# Configure for long-running worker
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=5,            # Fewer concurrent tasks
    max_overflow=5,         # Some extra capacity
    pool_timeout=30,        # Tasks can wait
    pool_recycle=1800,      # Recycle more frequently
    pool_pre_ping=True      # Catch stale connections
)
```

### AWS Lambda/Serverless

```python
from sqlalchemy.pool import NullPool

# No pooling for serverless
engine = create_engine(
    "postgresql://user:pass@rds.amazonaws.com/db",
    poolclass=NullPool,     # No connection reuse
    connect_args={
        "connect_timeout": 5
    }
)
```

**Why NullPool?**
- Lambda containers are short-lived
- Can't maintain persistent pool
- New connection per invocation

### SQLite Development

```python
from sqlalchemy.pool import StaticPool

# Single connection for SQLite
engine = create_engine(
    "sqlite:///dev.db",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)
```

## Monitoring Pool Health

```python
# Check pool status
pool = engine.pool

print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
print(f"Checked in: {pool.checkedin()}")
```

## Common Issues

### Issue 1: Pool Exhaustion

**Symptom:** `TimeoutError: QueuePool limit exceeded`

**Cause:** All connections in use, none available

**Solutions:**
```python
# Increase pool size
engine = create_engine(url, pool_size=20, max_overflow=20)

# Ensure connections are properly closed
with Session() as session:
    # ... work
    pass  # Auto-closes connection

# Don't forget to commit/rollback
session.commit()  # Or session.rollback()
```

### Issue 2: Stale Connections

**Symptom:** `OperationalError: server closed the connection`

**Cause:** Database closed idle connections

**Solutions:**
```python
# Enable recycling
engine = create_engine(url, pool_recycle=3600)

# Enable pre-ping (tests before use)
engine = create_engine(url, pool_pre_ping=True)
```

### Issue 3: Connection Leaks

**Symptom:** Connections never returned to pool

**Cause:** Not closing sessions properly

**Solutions:**
```python
# Always use context managers
with Session() as session:
    # work here
    pass  # Auto-closes

# Or explicit close
session = Session()
try:
    # work
    session.commit()
finally:
    session.close()  # Always close!
```

## Best Practices

### 1. Set Appropriate Pool Size

```python
# Calculate based on load
# pool_size = (concurrent_requests * avg_query_time) / request_duration

# Example: 100 req/s, 50ms queries
# pool_size = 100 * 0.05 = 5
engine = create_engine(url, pool_size=5, max_overflow=10)
```

### 2. Always Use Context Managers

```python
# Good: Auto-closes connection
with engine.begin() as conn:
    conn.execute(stmt)

# Good: Auto-closes session
with Session() as session:
    session.execute(stmt)
    session.commit()
```

### 3. Configure for Your Database

```python
# PostgreSQL
engine = create_engine(
    postgresql_url,
    pool_size=20,
    pool_recycle=3600,
    pool_pre_ping=True
)

# MySQL (closes connections after 8h)
engine = create_engine(
    mysql_url,
    pool_size=10,
    pool_recycle=3600,  # Recycle before MySQL timeout
    pool_pre_ping=True
)

# SQLite (no pooling needed)
engine = create_engine(
    sqlite_url,
    poolclass=StaticPool
)
```

### 4. Monitor in Production

```python
import logging

# Enable pool logging
logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)

# Check pool stats periodically
def check_pool_health():
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin()
    }
```

## Conclusion - Which Pool Should You Use?

### TL;DR - Quick Answer

**99% of cases: Use the default (QueuePool) - it's already perfect!**

SQLAlchemy's default configuration works great:
```python
engine = create_engine("postgresql://...")  # That's it!
# QueuePool with pool_size=5, max_overflow=10 is already set
```

### Decision Tree

**1. Normal Application (Web API, Backend Service)?**
→ **Use QueuePool (default)** ✅

```python
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=20,          # Adjust based on load
    max_overflow=10,
    pool_pre_ping=True,    # Recommended for production
)
```

**2. AWS Lambda or Serverless?**
→ **Use NullPool** (no persistent connections)

```python
from sqlalchemy.pool import NullPool

engine = create_engine(
    "postgresql://...",
    poolclass=NullPool  # New connection per invocation
)
```

**3. SQLite Development?**
→ **Use StaticPool** (single connection)

```python
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///dev.db",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)
```

### Pool Comparison

| Pool Type | When to Use | Pros | Cons |
|-----------|------------|------|------|
| **QueuePool** (default) | ✅ **Most apps** | Fast, efficient, handles concurrency | Needs long-lived process |
| **NullPool** | Serverless only | Works in Lambda | Slow (new connection each time) |
| **StaticPool** | SQLite only | Simple | Single connection only |

### Production Recommendations

**For Web Applications (FastAPI, Flask, Django):**
```python
engine = create_engine(
    database_url,
    pool_size=20,           # Handle ~20 concurrent requests
    max_overflow=10,        # Allow bursts up to 30 connections
    pool_timeout=10,        # Fail fast (10s)
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Detect stale connections
)
```

**For Background Workers (Celery, RQ):**
```python
engine = create_engine(
    database_url,
    pool_size=5,            # Fewer concurrent tasks
    max_overflow=5,
    pool_timeout=30,        # Tasks can wait longer
    pool_recycle=1800,      # Recycle every 30 minutes
    pool_pre_ping=True,
)
```

**For AWS Lambda:**
```python
from sqlalchemy.pool import NullPool

engine = create_engine(
    database_url,
    poolclass=NullPool      # Don't pool in Lambda!
)
```

### Most Important Rules

1. **Always use `with` statement**
   ```python
   # Good ✅
   with Session() as session:
       session.execute(...)

   # Bad ❌
   session = Session()
   session.execute(...)
   # Forgot to close - connection leaked!
   ```

2. **Start with defaults, then tune**
   - Default pool_size=5 works for most apps
   - Only increase if you see pool exhaustion
   - Monitor `checked_out` in production

3. **Enable `pool_pre_ping` in production**
   ```python
   engine = create_engine(url, pool_pre_ping=True)
   ```
   - Slight performance cost
   - Prevents stale connection errors
   - Worth it for reliability

### Summary

**Connection Pooling Benefits:**
- ✅ Reuses connections (3-4x faster)
- ✅ Limits concurrent connections
- ✅ Automatic lifecycle management

**What to use:**
- **Normal app:** QueuePool (default) - don't change anything!
- **Serverless:** NullPool
- **SQLite:** StaticPool

**Key Settings:**
- `pool_size`: Start with 5, increase if needed
- `pool_pre_ping`: Enable in production
- `pool_recycle`: Set to 3600 (1 hour)

**Remember:**
- Always use `with Session() as session:`
- Default QueuePool works for 99% of cases
- Only tune if you have evidence of problems
