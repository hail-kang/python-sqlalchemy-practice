"""
GOOD: Efficient bulk update methods.

This demonstrates fast ways to update many records:
1. bulk_update_mappings()
2. Direct UPDATE statement (fastest)
"""

import time

from sqlalchemy import select, update

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


def fast_update_bulk_mappings():
    """Good: Use bulk_update_mappings() for multiple field updates."""
    print("\n" + "=" * 80)
    print("GOOD: bulk_update_mappings() - Multiple Fields")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print(f"Updating {record_count} users with bulk_update_mappings()...")
    print("Direct UPDATE without ORM objects\n")

    start_time = time.time()

    with db.get_session() as session:
        # Get IDs (lightweight query)
        users = session.execute(select(User.id, User.username)).all()
        print(f"  Fetched {len(users)} user IDs")

        # Create update dictionaries
        user_updates = [
            {
                "id": user_id,
                "is_active": False,
                "full_name": f"Updated {username}",
            }
            for user_id, username in users
        ]

        # Bulk update
        session.bulk_update_mappings(User, user_updates)  # type: ignore[arg-type]
        print(f"  Bulk updated {len(user_updates)} records")

        # Single commit
        session.commit()
        print("  Committed once")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • No full ORM object loading")
    print("  • Single bulk UPDATE operation")
    print("  • Low memory usage")
    print("  • 10-50x faster than one-by-one")

    print("\n⚠️  TRADE-OFFS:")
    print("  • Must fetch IDs first (if needed)")
    print("  • No validation or ORM events")
    print("  • Need to know which records to update")


def fastest_update_direct_statement():
    """Better: Direct UPDATE statement for simple updates."""
    print("\n" + "=" * 80)
    print("BETTER: Direct UPDATE Statement - Simple Field")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Updating all users with direct UPDATE statement...")
    print("Database does all the work - no data loading!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Direct UPDATE statement
        stmt = update(User).values(is_active=False)
        result = session.execute(stmt)

        print("  Executed UPDATE statement")
        print(f"  Rows affected: {result.rowcount}")  # type: ignore[attr-defined]

        # Single commit
        session.commit()
        print("  Committed once")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • No data loading at all")
    print("  • Single database operation")
    print("  • Scales to millions of records")
    print("  • 100-500x faster than one-by-one")
    print("  • Minimal memory usage")


def conditional_update_demo():
    """Demonstrate conditional bulk update."""
    print("\n" + "=" * 80)
    print("BONUS: Conditional Bulk Update")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Updating users with username starting with 'user1'...")
    print("Direct UPDATE with WHERE clause\n")

    start_time = time.time()

    with db.get_session() as session:
        # Conditional UPDATE
        stmt = update(User).where(User.username.like("user1%")).values(is_active=False)

        result = session.execute(stmt)
        print("  Executed conditional UPDATE")
        print(f"  Rows affected: {result.rowcount}")  # type: ignore[attr-defined]

        # Single commit
        session.commit()
        print("  Committed once")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Updates only matching records")
    print("  • Database-level filtering")
    print("  • No unnecessary data transfer")
    print("  • Extremely fast even with millions of records")


def multiple_field_update_demo():
    """Demonstrate updating multiple fields with conditions."""
    print("\n" + "=" * 80)
    print("BONUS: Multiple Field Update with Conditions")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Updating multiple fields for inactive users...")
    print("Direct UPDATE with complex logic\n")

    start_time = time.time()

    with db.get_session() as session:
        # Update multiple fields
        stmt = (
            update(User)
            .where(User.username.like("user2%"))
            .values(is_active=False, full_name="Bulk Updated User")
        )

        result = session.execute(stmt)
        print("  Executed UPDATE with multiple fields")
        print(f"  Rows affected: {result.rowcount}")  # type: ignore[attr-defined]

        # Single commit
        session.commit()
        print("  Committed once")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Update multiple fields at once")
    print("  • Complex WHERE conditions")
    print("  • Database-level computation")
    print("  • Single SQL statement")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLUTION: Efficient Bulk Update Methods")
    print("=" * 80)
    print("\nCompare these with bad_slow_update.py to see the difference!")
    print("=" * 80)

    fast_update_bulk_mappings()
    fastest_update_direct_statement()
    conditional_update_demo()
    multiple_field_update_demo()

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\nRecommended approach:")
    print("  • Simple field updates: Direct UPDATE statement ✅")
    print("  • Multiple field updates: bulk_update_mappings()")
    print("  • Complex logic per record: Load → Modify → Commit")
    print("\nKey rule: Don't load data unless you need complex per-record logic!")
    print("=" * 80)
