# 01. Why mapped_column() - Legacy vs Modern Approach

## What Changed in SQLAlchemy 2.0

SQLAlchemy 2.0 introduced `mapped_column()` with `Mapped[T]` type annotations to replace the legacy `Column()` approach.

## Legacy Approach (SQLAlchemy 1.x)

```python
from sqlalchemy import Column, Integer, String, Boolean

class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False)
    full_name = Column(String(100))  # No type hint - is this nullable?
    is_active = Column(Boolean, default=True)
```

**Problems:**
- ❌ No type hints - IDE can't help with autocomplete
- ❌ Type checkers (pyright, mypy) can't verify types
- ❌ Unclear nullability - is `full_name` nullable or not?
- ❌ No compile-time type safety

## Modern Approach (SQLAlchemy 2.0+)

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))  # Clearly nullable
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
```

**Benefits:**
- ✅ Full type hints - `Mapped[str]`, `Mapped[int]`, `Mapped[str | None]`
- ✅ IDE autocomplete and inline documentation
- ✅ Type checkers verify types at compile time
- ✅ Explicit nullability - `str | None` makes it obvious
- ✅ Better error messages from type checkers

## Key Differences

### 1. Type Safety

**Legacy:**
```python
user.username  # IDE doesn't know this is a string
user.age       # Typo! But no error until runtime
```

**Modern:**
```python
user.username  # Type checker knows this is str
user.age       # Type checker error: 'User' has no attribute 'age'
```

### 2. Nullability

**Legacy:**
```python
full_name = Column(String(100))           # Nullable? Who knows!
middle_name = Column(String(50), nullable=True)  # Must check parameter
```

**Modern:**
```python
full_name: Mapped[str | None] = mapped_column(String(100))  # Obviously nullable
middle_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Not nullable
```

### 3. Type Inference

**Legacy:**
```python
# Type checker sees this as 'Any' - no help
username = Column(String(50))
```

**Modern:**
```python
# Type checker knows username: str
username: Mapped[str] = mapped_column(String(50))
```

### 4. Foreign Keys

**Legacy:**
```python
author_id = Column(Integer, ForeignKey('users.id'))
# What does author_id contain? Integer? User object?
```

**Modern:**
```python
author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
# Clear: author_id is an integer

author: Mapped["User"] = relationship(back_populates="posts")
# Clear: author is a User object
```

## Why This Matters

### 1. Catch Errors Early

```python
# Legacy - runtime error
user = User()
user.usernam = "john"  # Typo! Only discovered when code runs
session.add(user)

# Modern - type checker catches it
user = User()
user.usernam = "john"  # Type checker: Property 'usernam' does not exist
```

### 2. Better IDE Support

```python
# Legacy - IDE shows generic object
user.  # IDE: Shows all possible SQLAlchemy methods

# Modern - IDE knows exact structure
user.  # IDE: username, email, full_name, is_active, created_at, updated_at
```

### 3. Clearer Code Intent

```python
# Legacy - unclear
description = Column(Text)  # Nullable? Required?

# Modern - crystal clear
description: Mapped[str | None] = mapped_column(Text)  # Obviously optional
title: Mapped[str] = mapped_column(String(200), nullable=False)  # Required
```

## Real Example from Our Project

```python
# src/models/user.py
class User(Base):
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
```

**What this shows:**
- Clear type hints for each field
- Explicit nullability with `str | None`
- IDE knows `username` is `str`, `full_name` is `str | None`
- Type checker verifies all attribute access

## Migration Guide

If you have legacy code:

```python
# Old
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100))
```

Convert to:

```python
# New
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))
```

Steps:
1. Add `Mapped[type]` annotation before `=`
2. Change `Column()` to `mapped_column()`
3. Remove first argument if it matches type annotation
4. Make nullability explicit with `type | None`

## Summary

**Why use `mapped_column()` over `Column()`:**

| Aspect | Legacy `Column()` | Modern `mapped_column()` |
|--------|------------------|-------------------------|
| Type Safety | ❌ No type hints | ✅ Full type annotations |
| IDE Support | ❌ Limited autocomplete | ✅ Full autocomplete |
| Type Checking | ❌ Runtime only | ✅ Compile-time checking |
| Nullability | ❌ Implicit/unclear | ✅ Explicit `T \| None` |
| Error Detection | ❌ Runtime errors | ✅ Catch before running |
| Code Clarity | ❌ Must check parameters | ✅ Type tells the story |

**Bottom line:** `mapped_column()` with `Mapped[T]` provides the same functionality as `Column()` but with modern Python type safety, better tooling support, and clearer code intent.
