"""
BAD: Slow update - updating one record at a time.

This demonstrates the performance problem of updating records one-by-one.
"""

import time

from sqlalchemy import select

from src.config.database import DatabaseConfig
from src.models import User
from src.utils.db_init import reset_database


def prepare_test_data(db: DatabaseConfig, count: int = 1000):
    """Prepare test data for update examples."""
    reset_database(db.engine)

    with db.get_session() as session:
        # Use bulk_insert_mappings for fast test data creation
        user_dicts = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "is_active": True,
            }
            for i in range(count)
        ]
        session.bulk_insert_mappings(User, user_dicts)  # type: ignore[arg-type]
        session.commit()


def slow_update_one_by_one():
    """Bad: Update and commit one at a time."""
    print("\n" + "=" * 80)
    print("BAD: Updating One-by-One with Individual Commits")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print(f"Updating {record_count} users ONE AT A TIME...")
    print("Each update has its own commit (very slow!)\n")

    start_time = time.time()

    with db.get_session() as session:
        # Load all users
        users = session.execute(select(User)).scalars().all()

        for i, user in enumerate(users):
            user.is_active = False
            user.full_name = f"Updated {user.username}"
            session.commit()  # Commit EACH update!

            if i < 5 or i % 200 == 0:
                print(f"  Updated user {i+1}/{record_count}")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print(f"  • {record_count} database round trips")
    print(f"  • {record_count} separate transactions")
    print("  • ORM overhead for each update")
    print("  • Very slow performance")
    print("  • Database connection overhead")


def slow_update_with_single_commit():
    """Slightly better: Update all, then commit once."""
    print("\n" + "=" * 80)
    print("SLIGHTLY BETTER: Update All, Then Single Commit")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print(f"Updating {record_count} users with single commit...")
    print("But still loading and modifying ORM objects\n")

    start_time = time.time()

    with db.get_session() as session:
        # Load all users
        users = session.execute(select(User)).scalars().all()

        for i, user in enumerate(users):
            user.is_active = False
            user.full_name = f"Updated {user.username}"

            if i < 5 or i % 200 == 0:
                print(f"  Modified user object {i+1}/{record_count}")

        print("\nCommitting all at once...")
        session.commit()  # Single commit

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n⚠️  STILL SLOW:")
    print(f"  • Loading {record_count} ORM objects (memory intensive)")
    print(f"  • Modifying {record_count} objects one-by-one")
    print("  • ORM overhead for object tracking")
    print("  • Better than one-by-one, but not optimal")


def slow_update_load_all_data():
    """Bad: Loading all data into memory for simple update."""
    print("\n" + "=" * 80)
    print("BAD: Loading All Data for Simple Update")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print(f"Loading {record_count} users just to set is_active=False...")
    print("Unnecessary data loading and ORM overhead!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Load ALL data just to set a flag
        users = session.execute(select(User)).scalars().all()
        print(f"  Loaded {len(users)} users into memory")

        for user in users:
            user.is_active = False  # Simple field update

        session.commit()
        print("  Updated all users")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print(f"  • Loaded {record_count} full records unnecessarily")
    print("  • High memory usage")
    print("  • ORM overhead for tracking changes")
    print("  • Could have been a simple UPDATE query")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEMONSTRATING THE PROBLEM: Slow Bulk Update")
    print("=" * 80)
    print("\nThis shows why updating records one-by-one is inefficient.")
    print("See good_bulk_update.py for the solution!")
    print("=" * 80)

    slow_update_one_by_one()
    slow_update_with_single_commit()
    slow_update_load_all_data()

    print("\n" + "=" * 80)
    print("💡 TIP: Use bulk_update_mappings() or direct UPDATE for efficient updates!")
    print("=" * 80)
