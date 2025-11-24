# 03. N+1 Query Problem - The Performance Killer

## What is the N+1 Problem?

The N+1 problem occurs when:
1. You fetch N records with **1 query**
2. For each record, you fetch related data with **N additional queries**
3. Total: **1 + N queries** instead of 1-2 queries

This is one of the most common performance issues in ORMs.

## The Problem (Lazy Loading)

```python
# Query 1: Fetch all users
users = session.query(User).all()  # SELECT * FROM users

# Query 2-N: Fetch posts for EACH user (lazy loading)
for user in users:  # 10 users
    print(f"{user.username}: {len(user.posts)} posts")
    # SELECT * FROM posts WHERE author_id = 1
    # SELECT * FROM posts WHERE author_id = 2
    # SELECT * FROM posts WHERE author_id = 3
    # ... 10 queries!
```

**Result:** 1 + 10 = **11 queries** for 10 users!

With 100 users: **101 queries**
With 1000 users: **1001 queries** 🔥

## Solution 1: Eager Loading with joinedload()

Load related data with a JOIN in a single query:

```python
from sqlalchemy.orm import joinedload

# Single query with JOIN
users = session.query(User).options(joinedload(User.posts)).all()
# SELECT users.*, posts.*
# FROM users LEFT OUTER JOIN posts ON users.id = posts.author_id

for user in users:
    print(f"{user.username}: {len(user.posts)} posts")  # No additional queries!
```

**Result:** **1 query** regardless of number of users ✅

**When to use:**
- One-to-one relationships
- One-to-many with small number of related records
- Need data immediately in single query

**Drawback:**
- Cartesian product with large related data (lots of duplicates)
- Can be slow with many-to-many relationships

## Solution 2: Eager Loading with selectinload()

Load related data with a separate SELECT...IN query:

```python
from sqlalchemy.orm import selectinload

# Query 1: Fetch users
# Query 2: Fetch all related posts with IN clause
users = session.query(User).options(selectinload(User.posts)).all()
# Query 1: SELECT * FROM users
# Query 2: SELECT * FROM posts WHERE author_id IN (1, 2, 3, 4, 5, ...)

for user in users:
    print(f"{user.username}: {len(user.posts)} posts")  # No additional queries!
```

**Result:** **2 queries** regardless of number of users ✅

**When to use:**
- One-to-many with many related records
- Many-to-many relationships
- Want to avoid JOIN overhead

**Advantages:**
- No cartesian product
- More efficient with large related datasets
- **Recommended for most cases**

## Solution 3: Eager Loading with subqueryload()

Load related data with a subquery:

```python
from sqlalchemy.orm import subqueryload

users = session.query(User).options(subqueryload(User.posts)).all()
# Query 1: SELECT * FROM users
# Query 2: SELECT * FROM posts WHERE author_id IN (
#            SELECT users.id FROM users
#          )
```

**Result:** **2 queries** regardless of number of users ✅

**When to use:**
- Complex filtering on parent query
- Need to maintain query structure

**Note:** Generally `selectinload()` is preferred over `subqueryload()` in SQLAlchemy 2.0+

## Solution 4: Manual Grouping (Python-level)

Fetch data separately and group in Python:

```python
# Query 1: Fetch users
users = session.query(User).all()

# Query 2: Fetch all posts at once
user_ids = [user.id for user in users]
posts = session.query(Post).filter(Post.author_id.in_(user_ids)).all()

# Group in Python memory
from collections import defaultdict
posts_by_user = defaultdict(list)
for post in posts:
    posts_by_user[post.author_id].append(post)

# Use grouped data
for user in users:
    user_posts = posts_by_user[user.id]
    print(f"{user.username}: {len(user_posts)} posts")
```

**Result:** **2 queries** + Python grouping ✅

**When to use:**
- Need custom grouping logic
- Want full control over queries
- Already have data in memory
- Complex aggregations

**Advantages:**
- Full control over SQL
- Can optimize queries separately
- Easy to understand and debug
- No ORM "magic"

**Drawbacks:**
- Manual mapping code
- Objects not attached to session relationships
- More verbose

## Comparison

| Method | Queries | When to Use |
|--------|---------|-------------|
| **Lazy Loading** | 1 + N | ❌ Never for lists |
| **joinedload()** | 1 | One-to-one, small one-to-many |
| **selectinload()** | 2 | ✅ **Most cases** - one-to-many, many-to-many |
| **subqueryload()** | 2 | Complex parent filtering |
| **Manual Grouping** | 2 | Custom logic, full control |

## Nested Relationships

You can chain options for nested relationships:

```python
from sqlalchemy.orm import selectinload

# Load users -> posts -> comments in 3 queries
users = session.query(User).options(
    selectinload(User.posts).selectinload(Post.comments)
).all()

# Query 1: SELECT * FROM users
# Query 2: SELECT * FROM posts WHERE author_id IN (...)
# Query 3: SELECT * FROM comments WHERE post_id IN (...)

for user in users:
    for post in user.posts:
        print(f"{post.title}: {len(post.comments)} comments")
```

**Result:** **3 queries** for users -> posts -> comments ✅

## Multiple Relationships

Load multiple relationships at once:

```python
from sqlalchemy.orm import selectinload

users = session.query(User).options(
    selectinload(User.posts),
    selectinload(User.comments),
    selectinload(User.applications)
).all()

# Query 1: SELECT * FROM users
# Query 2: SELECT * FROM posts WHERE author_id IN (...)
# Query 3: SELECT * FROM comments WHERE author_id IN (...)
# Query 4: SELECT * FROM applications WHERE user_id IN (...)
```

**Result:** **4 queries** for all relationships ✅

## Real Example from Our Project

```python
# Bad: Lazy loading (1 + N + N queries)
users = session.query(User).all()
for user in users:
    print(f"Posts: {len(user.posts)}")      # N queries
    print(f"Comments: {len(user.comments)}") # N queries

# Good: Eager loading (3 queries total)
from sqlalchemy.orm import selectinload

users = session.query(User).options(
    selectinload(User.posts),
    selectinload(User.comments)
).all()

for user in users:
    print(f"Posts: {len(user.posts)}")      # No query!
    print(f"Comments: {len(user.comments)}") # No query!
```

## What If There's No Foreign Key Constraint?

Many startups and fast-moving teams **don't use foreign key constraints** in the database for flexibility. In this case:

**ORM features DON'T work:**
- ❌ `relationship()` won't work properly
- ❌ `selectinload()`, `joinedload()`, `subqueryload()` won't work
- ❌ No automatic relationship loading

**Solution: Manual Grouping (The ONLY Way)**

```python
from collections import defaultdict

# Query 1: Fetch all users
users = session.execute(select(User)).scalars().all()

# Query 2: Fetch all related posts with IN clause
user_ids = [user.id for user in users]
posts = session.execute(
    select(Post).where(Post.author_id.in_(user_ids))
).scalars().all()

# Group in Python memory
posts_by_user = defaultdict(list)
for post in posts:
    posts_by_user[post.author_id].append(post)

# Use grouped data
for user in users:
    user_posts = posts_by_user[user.id]
    print(f"{user.username}: {len(user_posts)} posts")
```

**Result:** **2 queries** (1 for users, 1 for posts) ✅

### Why This Works Without Foreign Keys

1. **Direct SQL queries** - No ORM relationship magic needed
2. **IN clause** - Fetch all related records at once
3. **Python grouping** - `defaultdict` maps posts to users in memory
4. **Index still required** - Make sure `author_id` has an index!

### Important: Still Need Index

```python
# Even without FK constraint, you MUST have index
author_id: Mapped[int] = mapped_column(nullable=False, index=True)  # Index is critical!
```

Without an index, the `WHERE author_id IN (...)` query will be slow.

### Nested Relationships Without FK

```python
# Query 1: Users
users = session.execute(select(User)).scalars().all()
user_ids = [user.id for user in users]

# Query 2: Posts
posts = session.execute(select(Post).where(Post.author_id.in_(user_ids))).scalars().all()
post_ids = [post.id for post in posts]

# Query 3: Comments
comments = session.execute(select(Comment).where(Comment.post_id.in_(post_ids))).scalars().all()

# Group in Python
posts_by_user = defaultdict(list)
for post in posts:
    posts_by_user[post.author_id].append(post)

comments_by_post = defaultdict(list)
for comment in comments:
    comments_by_post[comment.post_id].append(comment)

# Use grouped data
for user in users:
    user_posts = posts_by_user[user.id]
    for post in user_posts:
        post_comments = comments_by_post[post.id]
        print(f"{user.username} -> {post.title}: {len(post_comments)} comments")
```

**Result:** **3 queries** instead of 1 + N + M queries ✅

### When You Can't Use ORM Features

| Feature | With FK Constraints | Without FK Constraints |
|---------|-------------------|----------------------|
| `relationship()` | ✅ Works | ❌ Won't work reliably |
| `selectinload()` | ✅ Works | ❌ Won't work |
| `joinedload()` | ✅ Works | ❌ Won't work |
| Manual grouping | ✅ Works | ✅ **ONLY option** |
| Performance | Same (2 queries) | Same (2 queries) |

### Real-World Startup Pattern

```python
def get_users_with_posts(session, user_ids: list[int]):
    """Fetch users and their posts without FK constraints."""
    # Fetch data
    users = session.execute(
        select(User).where(User.id.in_(user_ids))
    ).scalars().all()

    posts = session.execute(
        select(Post).where(Post.author_id.in_(user_ids))
    ).scalars().all()

    # Group
    posts_by_user = defaultdict(list)
    for post in posts:
        posts_by_user[post.author_id].append(post)

    # Return structured data
    return [
        {
            "user": user,
            "posts": posts_by_user[user.id]
        }
        for user in users
    ]
```

**Benefits of this approach:**
- ✅ Works with or without FK constraints
- ✅ Full control over queries
- ✅ Easy to optimize
- ✅ Easy to understand and debug
- ✅ No ORM "magic"

**Trade-offs:**
- More verbose code
- Manual mapping required
- No automatic cascade behavior

## Detection and Debugging

Enable SQL logging to detect N+1 problems:

```python
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Now you'll see all SQL queries in console
users = session.query(User).all()
for user in users:
    print(user.posts)  # Watch the query spam!
```

## Summary

**The N+1 Problem:**
- Lazy loading triggers 1 + N queries
- Major performance killer
- Easy to accidentally introduce

**Solutions (in order of preference):**
1. **`selectinload()`** - Best for most cases (with FK constraints)
2. **`joinedload()`** - Single query (with FK constraints)
3. **Manual grouping** - Works with or without FK constraints ✅
4. **`subqueryload()`** - Specific edge cases (with FK constraints)

**Best Practice:**
- **With FK constraints:** Use `selectinload()` for collections
- **Without FK constraints:** Use manual grouping (ONLY option)
- Always use indexes on foreign key columns
- Profile with SQL logging enabled
- Always eager load when iterating relationships

**Remember:**
- 2 optimized queries >> 1001 unoptimized queries!
- Manual grouping works everywhere, even without FK constraints!
