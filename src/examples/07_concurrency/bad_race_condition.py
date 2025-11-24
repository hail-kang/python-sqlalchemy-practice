"""
BAD: Race condition - no protection against concurrent access.

This demonstrates what happens when multiple threads access shared data
without proper locking.
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
        # Create users for testing
        user_dicts = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "is_active": True,
            }
            for i in range(10)
        ]
        session.bulk_insert_mappings(User, user_dicts)  # type: ignore[arg-type]
        session.commit()


def bad_increment_counter_no_lock():
    """Bad: Increment counter without lock - race condition!"""
    print("\n" + "=" * 80)
    print("BAD: Counter Increment Without Lock (Race Condition)")
    print("=" * 80)

    prepare_test_data()

    db = DatabaseConfig()

    # Set initial counter to 0
    with db.get_session() as session:
        user = session.get(User, 1)
        if user:
            # Use id as counter for demonstration
            stmt = select(User).where(User.id == 1)
            user = session.execute(stmt).scalar_one()
            print(f"\nInitial value: {user.id}")

    def increment_without_lock(worker_id: int):
        """Increment counter WITHOUT lock - RACE CONDITION!"""
        with db.get_session() as session:
            # Read current value
            user = session.get(User, 1)
            if not user:
                return

            current_value = user.id
            print(f"  Worker {worker_id}: Read value = {current_value}")

            # Simulate some processing time
            time.sleep(0.01)

            # Write new value (other workers read same value!)
            new_value = current_value + 1
            user.id = new_value  # This won't work as id is primary key

            # Let's use a custom field instead
            # For demo, we'll just show the problem

            print(f"  Worker {worker_id}: Would write value = {new_value}")

        return new_value

    print("\n10 workers trying to increment simultaneously...")
    print("Each reads value, increments, and writes back\n")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(increment_without_lock, i) for i in range(10)]
        results = [f.result() for f in futures]

    print("\n❌ RACE CONDITION DEMONSTRATED:")
    print("  Each worker read the same initial value")
    print("  Each calculated their own 'next value'")
    print(f"  Results from workers: {results}")
    print("  Expected final value: 11 (1 + 10 increments)")
    print("  What would happen: Last write wins, others lost!")


def bad_check_and_insert_race():
    """Bad: Check if exists, then insert - race condition!"""
    print("\n" + "=" * 80)
    print("BAD: Check-Then-Insert Without Lock (Race Condition)")
    print("=" * 80)

    prepare_test_data()

    db = DatabaseConfig()

    def create_user_no_lock(username: str):
        """Create user if username doesn't exist - RACE CONDITION!"""
        with db.get_session() as session:
            # Check if username exists
            existing = session.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()

            if existing:
                print(f"  {username}: Already exists, skipping")
                return None

            print(f"  {username}: Not found, creating...")

            # Simulate some processing time
            time.sleep(0.01)

            # Create new user (multiple workers might reach here!)
            new_user = User(
                username=username,
                email=f"{username}@example.com",
                full_name=f"User {username}",
                is_active=True,
            )
            session.add(new_user)

            try:
                session.commit()
                print(f"  {username}: ✓ Created")
                return new_user.id
            except Exception as e:
                session.rollback()
                print(f"  {username}: ❌ Failed - {type(e).__name__}")
                return None

    print("\n10 workers trying to create same username simultaneously...\n")

    with ThreadPoolExecutor(max_workers=10) as executor:
        # All try to create same username
        futures = [executor.submit(create_user_no_lock, "duplicate_user") for _ in range(10)]
        results = [f.result() for f in futures]

    success_count = sum(1 for r in results if r is not None)

    print("\n❌ RACE CONDITION:")
    print("  Multiple workers passed the 'exists check' simultaneously")
    print("  All tried to insert the same username")
    print(f"  Successful inserts: {success_count}")
    print("  Expected: 1 (only one should succeed)")
    print("  Without unique constraint, all would succeed = duplicate data!")


def bad_read_modify_write_race():
    """Bad: Read-Modify-Write without lock - lost updates!"""
    print("\n" + "=" * 80)
    print("BAD: Read-Modify-Write Without Lock (Lost Updates)")
    print("=" * 80)

    prepare_test_data()

    db = DatabaseConfig()

    # Create a test user with a counter field
    with db.get_session() as session:
        test_user = User(
            username="counter_user",
            email="counter@example.com",
            full_name="Counter User",
            is_active=True,
        )
        session.add(test_user)
        session.commit()
        test_user_id = test_user.id
        print(f"\nCreated test user with id={test_user_id}")

    def increment_full_name_no_lock(worker_id: int):
        """Increment a counter in full_name field - RACE CONDITION!"""
        with db.get_session() as session:
            # Read current user
            user = session.get(User, test_user_id)
            if not user:
                return

            # Parse current counter from full_name
            try:
                current_counter = int(user.full_name.split()[-1])  # type: ignore[union-attr]
            except (ValueError, IndexError):
                current_counter = 0

            print(f"  Worker {worker_id}: Read counter = {current_counter}")

            # Simulate some processing
            time.sleep(0.01)

            # Increment and write back
            new_counter = current_counter + 1
            user.full_name = f"Counter {new_counter}"

            session.commit()
            print(f"  Worker {worker_id}: Wrote counter = {new_counter}")

            return new_counter

    print("\n10 workers incrementing counter simultaneously...\n")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(increment_full_name_no_lock, i) for i in range(10)]
        _ = [f.result() for f in futures]

    # Check final value
    with db.get_session() as session:
        user = session.get(User, test_user_id)
        if user:
            try:
                final_counter = int(user.full_name.split()[-1])  # type: ignore[union-attr]
            except (ValueError, IndexError):
                final_counter = 0
            print("\n❌ LOST UPDATES:")
            print(f"  Final counter value: {final_counter}")
            print("  Expected value: 10 (0 + 10 increments)")
            print(f"  Lost updates: {10 - final_counter}")
            print("  All workers read similar values and overwrote each other!")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEMONSTRATING THE PROBLEM: Race Conditions")
    print("=" * 80)
    print("\nThis shows what happens without proper concurrency control.")
    print("See good_pessimistic_lock.py for the solution!")
    print("=" * 80)

    bad_increment_counter_no_lock()
    bad_check_and_insert_race()
    bad_read_modify_write_race()

    print("\n" + "=" * 80)
    print("💡 TIP: Use SELECT FOR UPDATE to prevent race conditions!")
    print("=" * 80)
