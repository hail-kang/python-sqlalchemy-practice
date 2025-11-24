"""
GOOD: Efficient bulk insert methods.

This demonstrates fast ways to insert many records:
1. add_all() with single commit
2. bulk_insert_mappings() (fastest)
3. Raw SQL insert
"""

import time

from sqlalchemy import insert

from src.config.database import DatabaseConfig
from src.models import User
from src.utils.db_init import reset_database


def fast_insert_add_all():
    """Good: Create objects in bulk, single commit."""
    print("\n" + "=" * 80)
    print("GOOD: add_all() with Single Commit")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    record_count = 1000
    print(f"\nInserting {record_count} users with add_all()...")
    print("Creating ORM objects but committing once\n")

    start_time = time.time()

    with db.get_session() as session:
        # Create all objects at once
        users = [
            User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                is_active=True,
            )
            for i in range(record_count)
        ]

        print(f"  Created {len(users)} user objects in memory")

        # Add all at once
        session.add_all(users)
        print("  Added all to session")

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
    print("  • Single database round trip")
    print("  • Single transaction")
    print("  • ORM features available (validation, defaults)")
    print("  • Much faster than one-by-one")

    print("\n⚠️  TRADE-OFFS:")
    print("  • Still creates ORM objects (memory usage)")
    print("  • ORM overhead for object creation")


def fastest_insert_bulk_mappings():
    """Better: Use bulk_insert_mappings() for maximum speed."""
    print("\n" + "=" * 80)
    print("BETTER: bulk_insert_mappings() - Direct Insert")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    record_count = 1000
    print(f"\nInserting {record_count} users with bulk_insert_mappings()...")
    print("No ORM objects created - direct SQL INSERT\n")

    start_time = time.time()

    with db.get_session() as session:
        # Create dictionaries (no ORM objects)
        user_dicts = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "is_active": True,
            }
            for i in range(record_count)
        ]

        print(f"  Created {len(user_dicts)} dictionaries")

        # Bulk insert directly
        session.bulk_insert_mappings(User, user_dicts)  # type: ignore[arg-type]
        print("  Bulk inserted all records")

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
    print("  • No ORM object creation (low memory)")
    print("  • Minimal overhead")
    print("  • Fastest method with SQLAlchemy")
    print("  • 10-100x faster than one-by-one")

    print("\n⚠️  TRADE-OFFS:")
    print("  • No validation or defaults")
    print("  • No relationships populated")
    print("  • Bypasses ORM events")


def raw_sql_insert():
    """Fastest: Raw SQL INSERT statement."""
    print("\n" + "=" * 80)
    print("FASTEST: Raw SQL INSERT")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    record_count = 1000
    print(f"\nInserting {record_count} users with raw SQL...")
    print("Direct SQL execution - maximum performance\n")

    start_time = time.time()

    with db.get_session() as session:
        # Create dictionaries
        user_dicts = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "is_active": True,
            }
            for i in range(record_count)
        ]

        print(f"  Created {len(user_dicts)} dictionaries")

        # Raw SQL insert
        stmt = insert(User).values(user_dicts)
        session.execute(stmt)
        print("  Executed raw SQL INSERT")

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
    print("  • Maximum performance")
    print("  • Full SQL control")
    print("  • Minimal overhead")

    print("\n⚠️  TRADE-OFFS:")
    print("  • Bypasses ALL ORM features")
    print("  • No validation, defaults, or events")
    print("  • Less portable across databases")


def chunked_insert_demo():
    """Demonstrate chunking for very large datasets."""
    print("\n" + "=" * 80)
    print("BONUS: Chunked Insert for Large Datasets")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    record_count = 5000
    chunk_size = 1000
    print(f"\nInserting {record_count} users in chunks of {chunk_size}...")
    print("Prevents memory issues with large datasets\n")

    start_time = time.time()

    with db.get_session() as session:
        # Create all data
        user_dicts = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "is_active": True,
            }
            for i in range(record_count)
        ]

        # Insert in chunks
        for i in range(0, len(user_dicts), chunk_size):
            chunk = user_dicts[i : i + chunk_size]
            session.bulk_insert_mappings(User, chunk)  # type: ignore[arg-type]
            session.commit()
            print(f"  Inserted chunk: {i + len(chunk)}/{record_count} records")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Average per record: {total_time*1000/record_count:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Controlled memory usage")
    print("  • Progress tracking")
    print("  • Partial success on failure")
    print("  • Works with millions of records")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLUTION: Efficient Bulk Insert Methods")
    print("=" * 80)
    print("\nCompare these with bad_slow_insert.py to see the difference!")
    print("=" * 80)

    fast_insert_add_all()
    fastest_insert_bulk_mappings()
    raw_sql_insert()
    chunked_insert_demo()

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\nRecommended approach:")
    print("  • < 100 records: add_all() - ORM features worth it")
    print("  • 100-10,000 records: bulk_insert_mappings() - best balance ✅")
    print("  • 10,000+ records: Consider raw SQL or COPY")
    print("=" * 80)
