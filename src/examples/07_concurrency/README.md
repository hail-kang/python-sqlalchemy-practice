# 07. Concurrency - Handling Race Conditions

## ⚠️ Important Note About SQLite

**SQLite has limited concurrency support** - it uses table-level locking, not row-level locking. This means:
- `SELECT FOR UPDATE` will lock the entire table, not just specific rows
- Concurrent writes are serialized at the table level
- Performance is significantly worse than PostgreSQL/MySQL for concurrent operations

**For production applications with high concurrency:**
- ✅ Use PostgreSQL or MySQL (they support true row-level locking)
- ✅ Implement database constraints as defense in depth
- ✅ Test concurrent scenarios with your actual database

**These examples demonstrate the concepts**, but results may vary due to SQLite's limitations.

## What is a Race Condition?

A race condition occurs when multiple processes/threads access shared data simultaneously, leading to:
- Lost updates
- Duplicate entries
- Incorrect calculations
- Data inconsistency

## Example Files

**Problem & Solution Pairs:**

1. **Race Condition Problem**
   - `bad_race_condition.py` - No protection against concurrent access (data loss!)
   - `good_pessimistic_lock.py` - Using SELECT FOR UPDATE (safe!)

2. **Real-World Example: Campaign Applications**
   - `bad_campaign_overflow.py` - Max participants exceeded due to race condition
   - `good_campaign_safe.py` - Proper locking to enforce limits

**Run examples:**
```bash
# See the race condition problem
uv run python -m src.examples.07_concurrency.bad_race_condition

# See the solution with locking
uv run python -m src.examples.07_concurrency.good_pessimistic_lock

# Campaign overflow problem
uv run python -m src.examples.07_concurrency.bad_campaign_overflow

# Campaign with proper protection
uv run python -m src.examples.07_concurrency.good_campaign_safe
```

## The Problem: Race Conditions

### Lost Updates
```python
# Thread 1: Read count = 10
# Thread 2: Read count = 10
# Thread 1: Write count = 11
# Thread 2: Write count = 11  # Lost Thread 1's update!
# Result: count = 11 (should be 12)
```

**Problems:**
- Multiple threads read same value
- Each calculates new value independently
- Last write wins, others lost
- Data inconsistency

### Real-World Example: Campaign Applications

```python
# Campaign has max_participants = 100
# Current applications = 99

# User A checks: 99 < 100 ✓ (can apply)
# User B checks: 99 < 100 ✓ (can apply)
# User A creates application → 100 total ✓
# User B creates application → 101 total ❌ OVERFLOW!
```

## Solutions

### Solution 1: Pessimistic Locking (SELECT FOR UPDATE)

```python
from sqlalchemy import select

# Lock the row for update
stmt = select(Campaign).where(Campaign.id == campaign_id).with_for_update()
campaign = session.execute(stmt).scalar_one()

# Now we have exclusive lock - safe to check and update
if campaign.max_participants is None or len(campaign.applications) < campaign.max_participants:
    application = Application(user_id=user_id, campaign_id=campaign_id)
    session.add(application)
    session.commit()  # Lock released
else:
    raise ValueError("Campaign is full")
```

**How it works:**
1. `SELECT ... FOR UPDATE` locks the row
2. Other transactions wait until lock is released
3. Only one transaction can proceed at a time
4. Prevents race conditions completely

**Benefits:**
- ✅ Guaranteed data consistency
- ✅ No lost updates
- ✅ Simple to implement
- ✅ Works across all databases

**Trade-offs:**
- ⚠️ Other transactions must wait
- ⚠️ Can cause deadlocks if not careful
- ⚠️ Reduced concurrency

### Solution 2: Optimistic Locking (Version Column)

```python
class Campaign(Base):
    # ... other columns
    version: Mapped[int] = mapped_column(default=1, nullable=False)

# Read with version
campaign = session.get(Campaign, campaign_id)
original_version = campaign.version

# Make changes
campaign.some_field = new_value

# Update only if version hasn't changed
stmt = (
    update(Campaign)
    .where(Campaign.id == campaign_id)
    .where(Campaign.version == original_version)
    .values(some_field=new_value, version=original_version + 1)
)
result = session.execute(stmt)

if result.rowcount == 0:
    raise ConcurrentModificationError("Data was modified by another transaction")
```

**Benefits:**
- ✅ Better concurrency (no locks)
- ✅ No deadlocks
- ✅ Good for read-heavy workloads

**Trade-offs:**
- ⚠️ Must handle retry logic
- ⚠️ More complex code
- ⚠️ Can fail under high contention

### Solution 3: Database Constraints

```python
# Add unique constraint at database level
class Application(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'campaign_id', name='uq_user_campaign'),
    )

# Now database prevents duplicate applications
try:
    application = Application(user_id=user_id, campaign_id=campaign_id)
    session.add(application)
    session.commit()
except IntegrityError:
    session.rollback()
    raise ValueError("Already applied to this campaign")
```

**Benefits:**
- ✅ Enforced at database level
- ✅ Cannot be bypassed
- ✅ Works across all application instances

## Locking Types

### FOR UPDATE (Exclusive Lock)

```python
# Exclusive lock - blocks other SELECT FOR UPDATE
stmt = select(Campaign).where(Campaign.id == id).with_for_update()
campaign = session.execute(stmt).scalar_one()
```

**Use when:**
- Need to modify the row
- Must prevent all concurrent access
- Ensuring sequential processing

### FOR UPDATE SKIP LOCKED

```python
# Skip locked rows instead of waiting
stmt = select(Campaign).where(Campaign.id == id).with_for_update(skip_locked=True)
campaign = session.execute(stmt).scalar_one_or_none()

if campaign is None:
    # Row is locked by another transaction, skip it
    return
```

**Use when:**
- Implementing job queues
- Processing tasks in parallel
- Don't want to wait for locks

### FOR UPDATE NOWAIT

```python
# Fail immediately if locked (don't wait)
stmt = select(Campaign).where(Campaign.id == id).with_for_update(nowait=True)
try:
    campaign = session.execute(stmt).scalar_one()
except DatabaseError:
    # Row is locked, handle it
    raise ResourceLockedError("Campaign is being processed")
```

**Use when:**
- Want immediate failure instead of waiting
- Implementing fail-fast behavior
- User-facing operations (don't make users wait)

### FOR SHARE (Shared Lock)

```python
# Shared lock - allows other reads but blocks writes
stmt = select(Campaign).where(Campaign.id == id).with_for_update(read=True)
campaign = session.execute(stmt).scalar_one()
```

**Use when:**
- Need consistent read
- Allow concurrent reads
- Block writes during calculation

## Common Patterns

### Pattern 1: Check and Insert with Lock

```python
def apply_to_campaign(session, user_id: int, campaign_id: int):
    """Safely apply to campaign with participant limit."""
    # Lock campaign row
    stmt = select(Campaign).where(Campaign.id == campaign_id).with_for_update()
    campaign = session.execute(stmt).scalar_one()

    # Check limit
    if campaign.max_participants is not None:
        current_count = len(campaign.applications)
        if current_count >= campaign.max_participants:
            raise ValueError(f"Campaign is full ({current_count}/{campaign.max_participants})")

    # Safe to insert
    application = Application(user_id=user_id, campaign_id=campaign_id)
    session.add(application)
    session.commit()
```

### Pattern 2: Atomic Counter Update

```python
def increment_counter(session, campaign_id: int):
    """Atomically increment counter without race condition."""
    from sqlalchemy import update

    # Direct UPDATE bypasses race condition
    stmt = (
        update(Campaign)
        .where(Campaign.id == campaign_id)
        .values(some_counter=Campaign.some_counter + 1)
    )
    session.execute(stmt)
    session.commit()
```

### Pattern 3: Conditional Update with Lock

```python
def approve_application_if_slots_available(session, application_id: int):
    """Approve application only if campaign has available slots."""
    # Lock both application and campaign
    stmt = (
        select(Application)
        .where(Application.id == application_id)
        .options(joinedload(Application.campaign))
        .with_for_update()
    )
    application = session.execute(stmt).scalar_one()

    campaign = application.campaign
    approved_count = sum(1 for app in campaign.applications if app.status == "approved")

    if campaign.max_participants is None or approved_count < campaign.max_participants:
        application.status = "approved"
        session.commit()
    else:
        raise ValueError("No available slots")
```

## When to Use Each Solution

### Use Pessimistic Locking (SELECT FOR UPDATE) when:
- ✅ High contention (many concurrent updates)
- ✅ Must guarantee no conflicts
- ✅ Simple logic (check → update)
- ✅ Critical operations (payments, inventory)

**Example:** Campaign applications with participant limits

### Use Optimistic Locking (Version) when:
- ✅ Low contention (rare conflicts)
- ✅ Read-heavy workload
- ✅ Long-running transactions
- ✅ Can handle retry logic

**Example:** Editing user profiles, article updates

### Use Database Constraints when:
- ✅ Enforcing uniqueness
- ✅ Data integrity rules
- ✅ Cross-application consistency

**Example:** No duplicate applications, unique usernames

## Performance Considerations

### Lock Duration
```python
# Bad ❌ - Long lock duration
with session.begin():
    campaign = session.execute(
        select(Campaign).with_for_update()
    ).scalar_one()

    # Expensive operation while holding lock
    send_email_notification()  # 2 seconds
    process_payment()          # 3 seconds

    session.commit()  # Lock held for 5+ seconds!

# Good ✅ - Minimize lock duration
with session.begin():
    campaign = session.execute(
        select(Campaign).with_for_update()
    ).scalar_one()

    # Quick check and update only
    if can_apply(campaign):
        create_application(campaign)

    session.commit()  # Lock released quickly

# Do expensive operations after
send_email_notification()
process_payment()
```

### Deadlock Prevention
```python
# Bad ❌ - Different lock order causes deadlocks
# Transaction 1: Lock Campaign A → Lock User X
# Transaction 2: Lock User X → Lock Campaign A
# DEADLOCK!

# Good ✅ - Consistent lock order
def apply_to_campaign(session, user_id: int, campaign_id: int):
    # Always lock in same order: User → Campaign
    user = session.execute(
        select(User).where(User.id == user_id).with_for_update()
    ).scalar_one()

    campaign = session.execute(
        select(Campaign).where(Campaign.id == campaign_id).with_for_update()
    ).scalar_one()

    # Process...
```

## Testing Concurrency Issues

```python
import threading
from concurrent.futures import ThreadPoolExecutor

def test_race_condition():
    """Test concurrent applications to same campaign."""
    campaign_id = 1
    max_participants = 10

    def apply(user_id: int):
        with Session() as session:
            apply_to_campaign(session, user_id, campaign_id)

    # Simulate 20 users applying simultaneously
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(apply, i) for i in range(20)]
        results = [f.result() for f in futures]

    # Verify only 10 applications created
    with Session() as session:
        count = session.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.campaign_id == campaign_id)
        )
        assert count == max_participants, f"Expected {max_participants}, got {count}"
```

## Best Practices

1. **Use SELECT FOR UPDATE for critical sections** - Simplest and safest
2. **Keep transactions short** - Release locks quickly
3. **Consistent lock order** - Prevent deadlocks
4. **Add database constraints** - Defense in depth
5. **Handle lock timeout** - Don't hang forever
6. **Use SKIP LOCKED for queues** - Better throughput
7. **Test under load** - Race conditions only appear under concurrency

## Summary

**Key Takeaways:**
- Race conditions cause data loss and inconsistency
- `SELECT FOR UPDATE` prevents race conditions
- Keep lock duration minimal
- Use consistent lock ordering
- Add database constraints as safety net

**Decision Guide:**
- **High contention + critical:** Pessimistic locking (SELECT FOR UPDATE) ✅
- **Low contention + retry ok:** Optimistic locking (version column)
- **Uniqueness rules:** Database constraints
- **Job queues:** SELECT FOR UPDATE SKIP LOCKED
- **User-facing:** SELECT FOR UPDATE NOWAIT (fail fast)

**Remember:** Always test concurrent scenarios - bugs only appear under load!
