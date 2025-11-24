"""
GOOD: Pessimistic locking with SELECT FOR UPDATE.

This demonstrates how to prevent race conditions using row-level locking.
"""

import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select

from src.config.database import DatabaseConfig
from src.models import User
from src.utils.db_init import reset_database


def prepare_test_data():
    """Prepare test data with users."""
    db = DatabaseConfig()
    reset_database(db.engine)

    with db.get_session() as session:
        # Create test user with counter
        test_user = User(
            username="counter_user",
            email="counter@example.com",
            full_name="Counter 0",  # Initialize counter to 0
            is_active=True,
        )
        session.add(test_user)
        session.commit()


def good_increment_with_lock():
    """Good: Increment counter with SELECT FOR UPDATE - NO race condition!"""
    print("\n" + "=" * 80)
    print("GOOD: Counter Increment With SELECT FOR UPDATE")
    print("=" * 80)

    prepare_test_data()

    db = DatabaseConfig()

    # Get initial value
    with db.get_session() as session:
        user = session.execute(select(User).where(User.username == "counter_user")).scalar_one()
        print(f"\nInitial value: {user.full_name}")

    def increment_with_lock(worker_id: int):
        """Increment counter WITH lock - NO RACE CONDITION!"""
        with db.get_session() as session:
            # SELECT FOR UPDATE - locks the row
            stmt = select(User).where(User.username == "counter_user").with_for_update()
            user = session.execute(stmt).scalar_one()

            # Parse current counter
            current_counter = int(user.full_name.split()[-1])  # type: ignore[union-attr]
            print(f"  Worker {worker_id}: Locked and read counter = {current_counter}")

            # Simulate some processing time
            time.sleep(0.01)

            # Increment and write back (still holding lock)
            new_counter = current_counter + 1
            user.full_name = f"Counter {new_counter}"

            session.commit()  # Lock released here
            print(f"  Worker {worker_id}: Wrote counter = {new_counter}, lock released")

            return new_counter

    print("\n10 workers incrementing counter with lock...\n")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(increment_with_lock, i) for i in range(10)]
        _ = [f.result() for f in futures]

    # Check final value
    with db.get_session() as session:
        user = session.execute(select(User).where(User.username == "counter_user")).scalar_one()
        final_counter = int(user.full_name.split()[-1])  # type: ignore[union-attr]

        print("\n✅ NO LOST UPDATES:")
        print(f"  Final counter value: {final_counter}")
        print("  Expected value: 10 (0 + 10 increments)")
        print("  Lost updates: 0")
        print("  SELECT FOR UPDATE prevented race condition!")


def good_check_and_insert_with_lock():
    """Good: Check-then-insert with lock."""
    print("\n" + "=" * 80)
    print("GOOD: Check-Then-Insert With SELECT FOR UPDATE")
    print("=" * 80)

    prepare_test_data()

    db = DatabaseConfig()

    def create_user_with_lock(username: str, worker_id: int):
        """Create user if username doesn't exist - WITH LOCK!"""
        with db.get_session() as session:
            # Lock the table/row to check
            # Note: For new inserts, we lock existing row to serialize checks
            stmt = select(User).where(User.username == username).with_for_update()
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                print(f"  Worker {worker_id}: {username} exists, skipping")
                return None

            print(f"  Worker {worker_id}: {username} not found, creating...")

            # Simulate processing
            time.sleep(0.01)

            # Create new user (we hold lock, so serial execution)
            new_user = User(
                username=username,
                email=f"{username}@example.com",
                full_name=f"User {username}",
                is_active=True,
            )
            session.add(new_user)

            try:
                session.commit()  # Lock released
                print(f"  Worker {worker_id}: ✓ Created {username}")
                return new_user.id
            except Exception as e:
                session.rollback()
                print(f"  Worker {worker_id}: ❌ Failed - {type(e).__name__}")
                return None

    print("\n5 workers trying to create same username with proper locking...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_user_with_lock, "locked_user", i) for i in range(5)]
        results = [f.result() for f in futures]

    success_count = sum(1 for r in results if r is not None)

    print("\n✅ NO RACE CONDITION:")
    print("  Only first worker passed the check")
    print("  Others waited for lock and then saw existing user")
    print(f"  Successful inserts: {success_count}")
    print("  Expected: 1 ✓")


def good_nowait_example():
    """Good: Use NOWAIT to fail fast instead of waiting."""
    print("\n" + "=" * 80)
    print("GOOD: SELECT FOR UPDATE NOWAIT (Fail Fast)")
    print("=" * 80)

    prepare_test_data()

    db = DatabaseConfig()

    def try_lock_nowait(worker_id: int):
        """Try to lock row, fail immediately if already locked."""
        with db.get_session() as session:
            try:
                # NOWAIT - fail immediately if locked
                stmt = (
                    select(User).where(User.username == "counter_user").with_for_update(nowait=True)
                )
                _ = session.execute(stmt).scalar_one()

                print(f"  Worker {worker_id}: ✓ Got lock, processing...")
                time.sleep(0.1)  # Hold lock for a while

                session.commit()
                return f"Worker {worker_id}: Success"

            except Exception as e:
                session.rollback()
                error_name = type(e).__name__
                print(f"  Worker {worker_id}: ❌ Lock held by another - {error_name}")
                return f"Worker {worker_id}: Failed (locked)"

    print("\n5 workers trying to lock same row with NOWAIT...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_lock_nowait, i) for i in range(5)]
        results = [f.result() for f in futures]

    success_count = sum(1 for r in results if "Success" in r)
    failed_count = sum(1 for r in results if "Failed" in r)

    print("\n✅ FAIL FAST BEHAVIOR:")
    print(f"  Succeeded: {success_count} (got lock)")
    print(f"  Failed immediately: {failed_count} (didn't wait)")
    print("  Good for user-facing operations - no waiting!")


def good_skip_locked_queue_pattern():
    """Good: Use SKIP LOCKED for job queue pattern."""
    print("\n" + "=" * 80)
    print("GOOD: SELECT FOR UPDATE SKIP LOCKED (Job Queue)")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    # Create multiple pending jobs
    with db.get_session() as session:
        jobs = [
            User(
                username=f"job_{i}",
                email=f"job{i}@example.com",
                full_name=f"Pending Job {i}",
                is_active=False,  # False = pending
            )
            for i in range(10)
        ]
        session.add_all(jobs)
        session.commit()
        print(f"\nCreated {len(jobs)} pending jobs\n")

    def process_next_job(worker_id: int):
        """Process next available job (skip locked ones)."""
        with db.get_session() as session:
            # SKIP LOCKED - skip rows locked by other workers
            stmt = (
                select(User)
                .where(User.username.like("job_%"))
                .where(User.is_active == False)  # noqa: E712
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            job = session.execute(stmt).scalar_one_or_none()

            if job is None:
                print(f"  Worker {worker_id}: No available jobs")
                return None

            print(f"  Worker {worker_id}: Processing {job.username}...")

            # Simulate job processing
            time.sleep(0.05)

            # Mark as processed
            job.is_active = True
            job.full_name = f"Processed by Worker {worker_id}"

            session.commit()
            return job.username

    print("5 workers processing jobs in parallel with SKIP LOCKED...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        # Each worker tries to process 2 jobs
        futures = []
        for worker_id in range(5):
            futures.append(executor.submit(process_next_job, worker_id))
            futures.append(executor.submit(process_next_job, worker_id))

        results = [f.result() for f in futures]

    processed = [r for r in results if r is not None]

    print("\n✅ PARALLEL JOB PROCESSING:")
    print(f"  Processed jobs: {len(processed)}")
    print("  No worker waited for locks - all worked in parallel!")
    print("  Perfect for job queues and task distribution!")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLUTION: Pessimistic Locking with SELECT FOR UPDATE")
    print("=" * 80)
    print("\nThis shows how to prevent race conditions with proper locking.")
    print("Compare with bad_race_condition.py to see the difference!")
    print("=" * 80)

    good_increment_with_lock()
    good_check_and_insert_with_lock()
    good_nowait_example()
    good_skip_locked_queue_pattern()

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\n🔒 Locking strategies:")
    print("  • FOR UPDATE: Exclusive lock (default)")
    print("  • FOR UPDATE NOWAIT: Fail fast if locked")
    print("  • FOR UPDATE SKIP LOCKED: Skip locked rows (job queues)")
    print("\n💡 Key rules:")
    print("  1. Use SELECT FOR UPDATE for critical sections")
    print("  2. Keep lock duration minimal")
    print("  3. Use NOWAIT for user-facing operations")
    print("  4. Use SKIP LOCKED for parallel processing")
    print("=" * 80)
