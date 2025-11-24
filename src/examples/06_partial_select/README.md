# 06. Partial Select - Loading Only What You Need

## What is Partial Select?

Partial select loads only specific columns instead of entire rows, improving:
- Query performance (less data transfer)
- Memory usage (smaller objects)
- Network bandwidth (reduced payload)
- Application speed (faster processing)

## Example Files

**Problem & Solution:**

- `bad_loading_everything.py` - Loading full objects unnecessarily (slow!)
- `good_partial_select.py` - Efficient partial select + type-safe patterns (fast!)

**Run examples:**
```bash
# See the problem
uv run python -m src.examples.06_partial_select.bad_loading_everything

# See the solution (includes type-safe patterns)
uv run python -m src.examples.06_partial_select.good_partial_select
```

## The Problem: Loading Everything

### Over-fetching Data
```python
# Bad: Load entire User objects just to get usernames
users = session.execute(select(User)).scalars().all()
usernames = [user.username for user in users]
```

**Problems:**
- Loads ALL columns (id, username, email, full_name, is_active, created_at, updated_at)
- Wastes memory on unused data
- Slower query execution
- Unnecessary data transfer

## Solutions

### Method 1: Select Specific Columns

```python
# Good: Load only username column
from sqlalchemy import select

stmt = select(User.username)
usernames = session.execute(stmt).scalars().all()
# Returns: ['user1', 'user2', 'user3']
```

**Benefits:**
- Only requested columns loaded
- Much faster queries
- Lower memory usage
- Reduced data transfer

### Method 2: Select Multiple Columns

```python
# Load multiple specific columns
stmt = select(User.username, User.email)
results = session.execute(stmt).all()

for username, email in results:
    print(f"{username}: {email}")
```

**Benefits:**
- Still loads only needed data
- Returns tuples for easy unpacking
- Clean, readable code

### Method 3: Named Tuples with `mappings()`

```python
# Get dictionary-like results
stmt = select(User.username, User.email)
results = session.execute(stmt).mappings().all()

for row in results:
    print(f"{row['username']}: {row['email']}")
```

**Benefits:**
- Dictionary-like access
- Self-documenting code
- Easy to work with

### ~~Method 4: Load Subset with `load_only()`~~ (Not Recommended)

```python
# ⚠️ AVOID: Breaks type safety!
stmt = select(User).options(load_only(User.username, User.email))
users = session.execute(stmt).scalars().all()  # Type: list[User]

# Type checker thinks all User fields are available, but they're not!
print(users[0].username)   # ✅ Loaded
print(users[0].full_name)  # ⚠️ NOT loaded, but no type error!
```

**Problems:**
- ❌ Breaks type safety (type is `User`, but not all fields loaded)
- ❌ Type checker can't catch unloaded field access
- ❌ Runtime confusion (None or lazy load)
- ❌ Use TypedDict/Dataclass instead!

## Performance Comparison

| Method | 1000 Records | Memory | Type Safety | Recommended |
|--------|-------------|---------|-------------|-------------|
| Load full objects | ~3-4ms | High | ✅ | Updating records |
| Select 1 column | ~1.5ms | Very low | ✅ (with TypedDict) | ✅ Most cases |
| Select 2-3 columns | ~1ms | Low | ✅ (with TypedDict) | ✅ Display lists |
| `load_only()` | ~4.8ms | Medium | ❌ Breaks | ❌ Avoid |

## When to Use Each Method

### Use Full Object Loading when:
- Need most/all columns
- Need ORM relationships
- Need ORM methods and behavior
- Updating records

```python
# Full loading makes sense here
users = session.execute(select(User)).scalars().all()
for user in users:
    user.is_active = False  # Modifying
    session.add(user)
```

### Use Partial Select when:
- Only need 1-3 columns
- Display lists or dropdowns
- Generating reports
- Aggregating data
- **Most read-only queries** ✅

```python
from typing import TypedDict

class UserDropdown(TypedDict):
    id: int
    username: str

# Type-safe partial select
stmt = select(User.id, User.username)
users: list[UserDropdown] = [
    {"id": row["id"], "username": row["username"]}
    for row in session.execute(stmt).mappings()
]
```

## Common Patterns

### Pattern 1: Dropdown/Select Lists

```python
# Perfect for HTML <select> dropdowns
stmt = select(User.id, User.username).where(User.is_active == True)
users = session.execute(stmt).all()

# Returns: [(1, 'alice'), (2, 'bob'), ...]
```

### Pattern 2: Display Tables

```python
# Load only columns shown in table
stmt = select(
    User.username,
    User.email,
    User.created_at
).order_by(User.created_at.desc())

users = session.execute(stmt).mappings().all()
```

### Pattern 3: Aggregation/Reports

```python
# Load minimal data for processing
stmt = select(Post.author_id, Post.created_at)
posts = session.execute(stmt).all()

# Group by author
from collections import defaultdict
posts_by_author = defaultdict(list)
for author_id, created_at in posts:
    posts_by_author[author_id].append(created_at)
```

### Pattern 4: Existence Checks

```python
# Check if username exists (don't load everything)
stmt = select(User.id).where(User.username == "alice").limit(1)
exists = session.execute(stmt).scalar() is not None
```

## Advanced Techniques

### Combining with Joins

```python
# Partial select from multiple tables
from sqlalchemy import select

stmt = select(
    User.username,
    Post.title,
    Post.created_at
).join(Post.author).where(User.is_active == True)

results = session.execute(stmt).all()
```

### Using Aliases for Complex Queries

```python
# Subqueries with partial selects
subq = select(User.id).where(User.is_active == True).subquery()

stmt = select(Post.title).where(Post.author_id.in_(subq))
titles = session.execute(stmt).scalars().all()
```

### Counting Efficiently

```python
from sqlalchemy import func

# Don't load data for counting
stmt = select(func.count()).select_from(User).where(User.is_active == True)
count = session.execute(stmt).scalar()
```

## Common Pitfalls

### Pitfall 1: Over-fetching for Simple Queries

```python
# Bad ❌ - Loading everything just for usernames
users = session.execute(select(User)).scalars().all()
usernames = [user.username for user in users]

# Good ✅ - Load only username
stmt = select(User.username)
usernames = session.execute(stmt).scalars().all()
```

### Pitfall 2: Not Using `mappings()` for Readability

```python
# Hard to read ❌
stmt = select(User.username, User.email, User.created_at)
results = session.execute(stmt).all()
for row in results:
    print(row[0], row[1], row[2])  # What are these?

# Self-documenting ✅
results = session.execute(stmt).mappings().all()
for row in results:
    print(row['username'], row['email'], row['created_at'])
```

### Pitfall 3: Using `load_only()` When Don't Need ORM

```python
# Unnecessary ORM overhead ❌
stmt = select(User).options(load_only(User.username))
users = session.execute(stmt).scalars().all()
names = [user.username for user in users]

# Simpler and faster ✅
stmt = select(User.username)
names = session.execute(stmt).scalars().all()
```

### Pitfall 4: Loading Data for Existence Checks

```python
# Bad ❌ - Loads entire record
user = session.execute(
    select(User).where(User.username == "alice")
).scalar_one_or_none()
exists = user is not None

# Good ✅ - Only check existence
stmt = select(User.id).where(User.username == "alice").limit(1)
exists = session.execute(stmt).scalar() is not None
```

## Best Practices

1. **Default to Partial Select** - Only load what you need
2. **Use Full Loading When Modifying** - Need ORM for updates
3. **Use `mappings()` for Readability** - Self-documenting code
4. **Count Without Loading** - Use `func.count()` for counts
5. **Profile Your Queries** - Measure to find bottlenecks

## Real-World Impact

### Example: User List API Endpoint

**Before (Full Loading):**
```python
# Loads all 7 columns × 1000 users = 7000 values
users = session.execute(select(User)).scalars().all()
return [{"id": u.id, "username": u.username} for u in users]
# Time: ~50ms, Memory: ~2MB
```

**After (Partial Select):**
```python
# Loads only 2 columns × 1000 users = 2000 values
stmt = select(User.id, User.username)
users = session.execute(stmt).mappings().all()
return list(users)
# Time: ~5ms, Memory: ~0.6MB
# Result: 10x faster, 70% less memory ✅
```

## Summary

**Key Takeaways:**
- Partial select is 5-10x faster for read-only queries
- Load only columns you actually use
- Use `mappings()` for readable code
- Reserve full loading for updates and complex ORM needs

**Decision Guide:**
- **Read-only, 1-3 columns:** `select(Model.col1, Model.col2).mappings()` + TypedDict ✅
- **Complex data:** Dataclass
- **APIs:** Pydantic with `model_validate()`
- **Updating records:** `select(Model)` - full loading
- **AVOID:** `load_only()` - breaks type safety ❌

**Remember:**
1. Most queries don't need all columns. Load only what you need!
2. Always use type-safe patterns (TypedDict/Dataclass/Pydantic)
3. Never use `load_only()` - use explicit column selection instead

## Type Safety with Partial Select

### ⚠️ The Problem with `load_only()`

`load_only()` breaks type safety because the type is still `User` but not all fields are loaded:

```python
from sqlalchemy.orm import load_only

stmt = select(User).options(load_only(User.username, User.email))
users: list[User] = session.execute(stmt).scalars().all()

print(users[0].username)   # ✅ Loaded
print(users[0].full_name)  # ⚠️ NOT loaded, but no type error!
```

**Problem:** Type checker can't catch unloaded field access!

### Solution 1: TypedDict with `select()` (Recommended)

```python
from typing import TypedDict

class UserBasicInfo(TypedDict):
    username: str
    email: str

# Select only needed columns
stmt = select(User.username, User.email)
results = session.execute(stmt).mappings().all()

# Type-safe conversion
users: list[UserBasicInfo] = [
    {"username": row["username"], "email": row["email"]}
    for row in results
]

# Type-safe access
print(users[0]["username"])  # ✅ OK
print(users[0]["email"])     # ✅ OK
print(users[0]["full_name"]) # ❌ Type error - field not in TypedDict!
```

**Benefits:**
- ✅ Type checker catches invalid field access
- ✅ Clear which fields are available
- ✅ Fastest performance (no ORM overhead)
- ✅ Great for most use cases

### Solution 2: Dataclass

```python
from dataclasses import dataclass

@dataclass
class UserBasic:
    username: str
    email: str

stmt = select(User.username, User.email)
results = session.execute(stmt).all()

users = [UserBasic(username=u, email=e) for u, e in results]

print(users[0].username)    # ✅ OK
print(users[0].full_name)   # ❌ Attribute error - caught by type checker!
```

**Benefits:**
- ✅ Type-safe with attribute access
- ✅ Dataclass benefits (__repr__, __eq__, etc.)
- ✅ Can add methods
- ✅ Good for complex data structures

### Solution 3: Pydantic (for APIs)

```python
from pydantic import BaseModel, EmailStr

class UserBasicSchema(BaseModel):
    username: str
    email: EmailStr  # Email validation!

stmt = select(User.username, User.email)
results = session.execute(stmt).mappings().all()

# Method 1: model_validate() - explicit validation (Pydantic v2 recommended)
users_v1 = [UserBasicSchema.model_validate(row) for row in results]

# Method 2: **row unpacking - also works
users_v2 = [UserBasicSchema(**row) for row in results]

print(users_v1[0].username)    # ✅ OK
print(users_v1[0].full_name)   # ❌ Attribute error
```

**Benefits:**
- ✅ Type-safe
- ✅ Runtime validation
- ✅ JSON serialization
- ✅ Perfect for FastAPI/APIs
- ✅ `model_validate()` is more explicit in Pydantic v2

**Note:** Install with `uv add pydantic`

### Comparison

| Solution | Type Safety | Performance | Complexity | Best For |
|----------|------------|-------------|------------|----------|
| TypedDict + select() | ✅ Excellent | ⚡ Fastest | ⭐ Simple | Most cases |
| Dataclass | ✅ Excellent | ⚡ Fast | ⭐⭐ Medium | Complex data |
| Pydantic | ✅ Excellent | ⚡ Fast | ⭐⭐⭐ Complex | APIs |
| load_only() | ❌ Poor | 🐌 Slower | ⭐ Simple | **Avoid** |

### Recommendation

**Default choice: TypedDict + `select()`**

```python
from typing import TypedDict

class UserDisplay(TypedDict):
    username: str
    email: str

stmt = select(User.username, User.email)
users: list[UserDisplay] = [
    {"username": row["username"], "email": row["email"]}
    for row in session.execute(stmt).mappings()
]
```

**Key Rule:** Don't use `load_only()` - use explicit column selection with TypedDict/Dataclass for type safety!
