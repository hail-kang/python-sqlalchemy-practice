"""
BAD: Creating new connection for every request (No Pooling).

This demonstrates the performance problem when not using connection pooling.
Every request creates a new database connection.
"""

import time

from sqlalchemy import create_engine, select
from sqlalchemy.pool import NullPool

from src.models import User
from src.utils.db_init import reset_database
from src.utils.sample_data import create_all_sample_data


def no_pooling_approach():
    """Bad approach: Create new engine (new connection) for every request."""
    print("\n" + "=" * 80)
    print("BAD APPROACH: No Connection Pooling (NullPool)")
    print("=" * 80)
    print("\nCreating NEW connection for EVERY query...\n")

    # Setup database once
    engine = create_engine("sqlite:///./test_pool.db", poolclass=NullPool, echo=False)
    reset_database(engine)

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    with Session() as session:
        create_all_sample_data(session, user_count=10, posts_per_user=2)

    print("Running 50 queries with NEW connection each time...")
    start_time = time.time()

    for i in range(50):
        # Create new engine = new connection every time!
        query_engine = create_engine("sqlite:///./test_pool.db", poolclass=NullPool, echo=False)
        QuerySession = sessionmaker(bind=query_engine)

        with QuerySession() as session:
            users = session.execute(select(User)).scalars().all()
            if i < 5:  # Show first 5
                print(f"  Query {i+1}: {len(users)} users (NEW connection created)")

        # Close connection
        query_engine.dispose()

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'.' * 80}")
    print(f"Total time for 50 queries: {total_time*1000:.2f}ms")
    print(f"Average per query: {total_time*1000/50:.2f}ms")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print("  • 50 connection creations (slow!)")
    print("  • Connection overhead for EVERY query")
    print("  • Database has to authenticate/setup 50 times")
    print("  • Waste of resources")
    print("  • Poor performance")

    engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEMONSTRATING THE PROBLEM: No Connection Pooling")
    print("=" * 80)
    print("\nThis is the BAD way - creating new connections for every request.")
    print("See good_with_pooling.py for the solution!")
    print("=" * 80)

    no_pooling_approach()

    print("\n" + "=" * 80)
    print("💡 TIP: Run good_with_pooling.py to see the difference!")
    print("=" * 80)
