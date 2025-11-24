"""
BAD: Slow insert - adding and committing one record at a time.

This demonstrates the performance problem of inserting records one-by-one.
"""

import time

from src.config.database import DatabaseConfig
from src.models import User
from src.utils.db_init import reset_database


def slow_insert_one_by_one():
    """Bad: Insert and commit one at a time."""
    print("\n" + "=" * 80)
    print("BAD: Inserting One-by-One with Individual Commits")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    record_count = 1000
    print(f"\nInserting {record_count} users ONE AT A TIME...")
    print("Each insert has its own commit (very slow!)\n")

    start_time = time.time()

    with db.get_session() as session:
        for i in range(record_count):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                is_active=True,
            )
            session.add(user)
            session.commit()  # Commit EACH record!

            if i < 5 or i % 200 == 0:  # Show progress
                print(f"  Inserted user {i+1}/{record_count}")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print(f"  • {record_count} database round trips")
    print(f"  • {record_count} separate transactions")
    print("  • ORM overhead for each individual insert")
    print("  • Very slow performance")
    print("  • Database connection overhead")


def slow_insert_with_single_commit():
    """Slightly better: Add all, then commit once."""
    print("\n" + "=" * 80)
    print("SLIGHTLY BETTER: Add All, Then Single Commit")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    record_count = 1000
    print(f"\nInserting {record_count} users with single commit...")
    print("But still creating ORM objects one-by-one\n")

    start_time = time.time()

    with db.get_session() as session:
        for i in range(record_count):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                is_active=True,
            )
            session.add(user)

            if i < 5 or i % 200 == 0:
                print(f"  Created user object {i+1}/{record_count}")

        print("\nCommitting all at once...")
        session.commit()  # Single commit

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n⚠️  STILL SLOW:")
    print("  • Creating 1000 ORM objects (memory intensive)")
    print("  • ORM overhead for object creation")
    print("  • Better than one-by-one, but not optimal")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEMONSTRATING THE PROBLEM: Slow Bulk Insert")
    print("=" * 80)
    print("\nThis shows why inserting records one-by-one is inefficient.")
    print("See good_bulk_insert.py for the solution!")
    print("=" * 80)

    slow_insert_one_by_one()
    slow_insert_with_single_commit()

    print("\n" + "=" * 80)
    print("💡 TIP: Use bulk_insert_mappings() for efficient batch inserts!")
    print("=" * 80)
