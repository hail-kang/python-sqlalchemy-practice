# 05. Bulk Operations - Efficient Mass Data Processing

## What are Bulk Operations?

Bulk operations process large amounts of data efficiently by:
- Reducing database round trips
- Minimizing ORM overhead
- Using batch INSERT/UPDATE/DELETE
- Optimizing memory usage

## Example Files

**Problem & Solution Pairs:**

1. **Slow Insert Problem**
   - `bad_slow_insert.py` - Inserting one-by-one (slow!)
   - `good_bulk_insert.py` - Batch insert (fast!)

2. **Slow Update Problem**
   - `bad_slow_update.py` - Updating one-by-one (slow!)
   - `good_bulk_update.py` - Bulk update (fast!)

**Run examples:**
```bash
# See the problems
uv run python -m src.examples.05_bulk_operations.bad_slow_insert
uv run python -m src.examples.05_bulk_operations.bad_slow_update

# See the solutions
uv run python -m src.examples.05_bulk_operations.good_bulk_insert
uv run python -m src.examples.05_bulk_operations.good_bulk_update
```

## The Problem: One-by-One Operations

### Slow Insert
```python
# Bad: Insert one at a time
for i in range(1000):
    user = User(username=f"user{i}", email=f"user{i}@example.com")
    session.add(user)
    session.commit()  # 1000 commits!
```

**Problems:**
- 1000 database round trips
- 1000 transactions
- ORM overhead for each object
- Very slow!

### Slow Update
```python
# Bad: Update one at a time
users = session.query(User).all()
for user in users:
    user.is_active = False
    session.commit()  # Commit each one!
```

**Problems:**
- N queries to update N records
- N commits
- Slow with large datasets

## Solutions

### Bulk Insert Methods

#### Method 1: `session.add_all()` + Single Commit
```python
# Good: Batch insert with single commit
users = [
    User(username=f"user{i}", email=f"user{i}@example.com")
    for i in range(1000)
]
session.add_all(users)
session.commit()  # Single commit for all!
```

**Benefits:**
- Single database round trip
- Single transaction
- Much faster

#### Method 2: `bulk_insert_mappings()`
```python
# Better: Direct INSERT without ORM overhead
user_dicts = [
    {"username": f"user{i}", "email": f"user{i}@example.com"}
    for i in range(1000)
]
session.bulk_insert_mappings(User, user_dicts)
session.commit()
```

**Benefits:**
- No ORM object creation
- Lower memory usage
- Fastest insert method
- **Trade-off:** No validation, no defaults, no relationships

#### Method 3: Raw SQL with `execute()`
```python
# Fastest: Raw SQL INSERT
from sqlalchemy import insert

stmt = insert(User).values([
    {"username": f"user{i}", "email": f"user{i}@example.com"}
    for i in range(1000)
])
session.execute(stmt)
session.commit()
```

**Benefits:**
- Maximum performance
- Full SQL control
- **Trade-off:** Bypasses all ORM features

### Bulk Update Methods

#### Method 1: `bulk_update_mappings()`
```python
# Update many records efficiently
users = session.query(User).all()
user_updates = [
    {"id": user.id, "is_active": False}
    for user in users
]
session.bulk_update_mappings(User, user_updates)
session.commit()
```

**Benefits:**
- Single UPDATE statement
- No ORM overhead
- Fast

#### Method 2: Direct UPDATE Statement
```python
# Fastest: Single UPDATE for all matching records
from sqlalchemy import update

stmt = update(User).where(User.created_at < cutoff_date).values(is_active=False)
session.execute(stmt)
session.commit()
```

**Benefits:**
- Single database round trip
- Database does all the work
- Scales to millions of records

### Bulk Delete

```python
# Delete many records at once
from sqlalchemy import delete

stmt = delete(User).where(User.is_active == False)
result = session.execute(stmt)
session.commit()
print(f"Deleted {result.rowcount} users")
```

## Performance Comparison

| Method | 1000 Records | Memory | Features |
|--------|-------------|---------|----------|
| One-by-one insert | ~5000ms | High | Full ORM |
| `add_all()` | ~500ms | High | Full ORM |
| `bulk_insert_mappings()` | ~50ms | Low | ✅ **Best balance** |
| Raw SQL | ~30ms | Lowest | No ORM |

## When to Use Each Method

### Use `add_all()` when:
- Need ORM features (validation, defaults, events)
- Need relationships populated
- Inserting < 1000 records
- Code clarity matters more than performance

```python
users = [User(username=f"user{i}") for i in range(100)]
session.add_all(users)
session.commit()
```

### Use `bulk_insert_mappings()` when:
- Inserting 1000+ records
- Don't need ORM validation
- Memory efficiency matters
- **Recommended for most bulk operations** ✅

```python
user_dicts = [{"username": f"user{i}"} for i in range(10000)]
session.bulk_insert_mappings(User, user_dicts)
session.commit()
```

### Use Raw SQL when:
- Maximum performance needed
- Inserting millions of records
- Database-specific features needed
- Have complex SQL logic

```python
stmt = insert(User).values(user_dicts)
session.execute(stmt)
session.commit()
```

## Chunking Large Operations

For very large datasets, process in chunks to avoid memory issues:

```python
def bulk_insert_chunked(session, model, data, chunk_size=1000):
    """Insert data in chunks to manage memory."""
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        session.bulk_insert_mappings(model, chunk)
        session.commit()
        print(f"Inserted {i + len(chunk)}/{len(data)} records")
```

## Common Pitfalls

### Pitfall 1: Committing Inside Loop
```python
# Bad ❌
for user_data in data:
    session.add(User(**user_data))
    session.commit()  # Don't do this!

# Good ✅
for user_data in data:
    session.add(User(**user_data))
session.commit()  # Single commit
```

### Pitfall 2: Not Using Bulk Methods
```python
# Bad ❌ - Creating ORM objects unnecessarily
users = [User(**data) for data in large_dataset]
session.add_all(users)
session.commit()

# Good ✅ - Direct mappings
session.bulk_insert_mappings(User, large_dataset)
session.commit()
```

### Pitfall 3: Loading All Data for Update
```python
# Bad ❌ - Loads all data into memory
users = session.query(User).all()
for user in users:
    user.status = "inactive"
session.commit()

# Good ✅ - Direct UPDATE
session.execute(
    update(User).values(status="inactive")
)
session.commit()
```

## Best Practices

1. **Batch commits** - Commit once, not per record
2. **Use bulk methods** - `bulk_insert_mappings()` for 1000+ records
3. **Chunk large operations** - Process in batches to manage memory
4. **Use direct SQL for mass updates** - Don't load data unnecessarily
5. **Disable autoflush** - `session.autoflush = False` for better performance
6. **Consider COPY for PostgreSQL** - Use `COPY` for millions of records

## PostgreSQL COPY Example

For maximum performance with PostgreSQL:

```python
from io import StringIO
import csv

# Prepare CSV data
output = StringIO()
writer = csv.writer(output)
for i in range(100000):
    writer.writerow([f"user{i}", f"user{i}@example.com"])

output.seek(0)

# Use COPY command
from sqlalchemy import text

session.execute(text("""
    COPY users (username, email)
    FROM STDIN
    WITH (FORMAT CSV)
"""), output)
session.commit()
```

## Summary

**Key Takeaways:**
- Batch operations are 10-100x faster than one-by-one
- Use `bulk_insert_mappings()` for most bulk operations
- Use direct SQL for mass updates/deletes
- Chunk very large operations
- Profile and measure to find bottlenecks

**Decision Guide:**
- **< 100 records:** Use `add_all()` - ORM features are worth it
- **100-10,000 records:** Use `bulk_insert_mappings()` - best balance
- **10,000+ records:** Consider raw SQL or database-specific tools (COPY)
- **Mass updates:** Always use direct UPDATE/DELETE statements

**Remember:** Premature optimization is bad, but bulk operations are a known pattern for handling large datasets efficiently!
