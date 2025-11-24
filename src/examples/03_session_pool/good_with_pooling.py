"""
GOOD: Using connection pooling (default QueuePool).

This demonstrates the performance improvement with connection pooling.
Connections are reused instead of created every time.
"""

import time

from sqlalchemy import create_engine, select
from sqlalchemy.pool import QueuePool

from src.models import User
from src.utils.db_init import reset_database
from src.utils.sample_data import create_all_sample_data


def with_pooling_approach():
    """Good approach: Reuse connections from pool."""
    print("\n" + "=" * 80)
    print("GOOD APPROACH: With Connection Pooling (QueuePool)")
    print("=" * 80)
    print("\nREUSING connections from pool...\n")

    # Create engine ONCE - it maintains a connection pool
    engine = create_engine(
        "sqlite:///./test_pool.db",
        poolclass=QueuePool,  # Default
        pool_size=5,  # Keep 5 connections ready
        max_overflow=10,  # Allow 10 more if needed
        echo=False,
    )
    reset_database(engine)

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    with Session() as session:
        create_all_sample_data(session, user_count=10, posts_per_user=2)

    pool = engine.pool  # type: ignore[attr-defined]
    print(f"Pool configuration: size={pool.size()}, max_overflow=10")  # type: ignore[attr-defined]
    print("Connections will be REUSED from this pool\n")

    print("Running 50 queries with connection REUSE...")
    start_time = time.time()

    for i in range(50):
        # Reuse connection from pool
        with Session() as session:
            users = session.execute(select(User)).scalars().all()
            if i < 5:  # Show first 5
                checked_out = pool.checkedout()  # type: ignore[attr-defined]
                print(f"  Query {i+1}: {len(users)} users (reused, checked_out: {checked_out})")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'.' * 80}")
    print(f"Total time for 50 queries: {total_time*1000:.2f}ms")
    print(f"Average per query: {total_time*1000/50:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Only 5 connections created (in pool)")
    print("  • All 50 queries REUSE these connections")
    print("  • No connection creation overhead")
    print("  • Much faster performance")
    print("  • Efficient resource usage")

    engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLUTION: Using Connection Pooling")
    print("=" * 80)
    print("\nThis is the GOOD way - reusing connections from a pool.")
    print("Compare with bad_no_pooling.py to see the difference!")
    print("=" * 80)

    with_pooling_approach()

    print("\n" + "=" * 80)
    print("💡 TIP: Connection pooling is SQLAlchemy's default behavior!")
    print("=" * 80)
