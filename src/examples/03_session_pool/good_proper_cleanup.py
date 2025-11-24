"""
GOOD: Proper connection cleanup with context managers.

This demonstrates the correct way to manage connections:
- Always use 'with' statement (context manager)
- Connections are automatically returned to pool
- No pool exhaustion
"""

import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, select
from sqlalchemy.pool import QueuePool

from src.models import User


def proper_cleanup_approach():
    """Good: Using context managers to ensure connections are returned."""
    print("\n" + "=" * 80)
    print("GOOD: Proper Connection Cleanup (Context Managers)")
    print("=" * 80)

    engine = create_engine(
        "sqlite:///./test_pool.db",
        poolclass=QueuePool,
        pool_size=3,
        max_overflow=0,
        pool_timeout=2,
        echo=False,
    )

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    pool = engine.pool  # type: ignore[attr-defined]

    print("\nPool configuration:")
    print("  pool_size: 3")
    print("  max_overflow: 0")
    print("  Total max connections: 3\n")

    print("Using 'with' statement - connections auto-returned...\n")

    for i in range(5):
        # Good practice: Use 'with' statement
        with Session() as session:
            session.execute(select(User)).scalars().all()
            checked_out = pool.checkedout()  # type: ignore[attr-defined]
            print(f"  Query {i+1}: Inside 'with' block (checked_out: {checked_out})")
        # Connection automatically returned here!

        checked_out_after = pool.checkedout()  # type: ignore[attr-defined]
        print(f"           After 'with' block (checked_out: {checked_out_after})")

    print("\n✅ All connections properly returned to pool!")
    print("✅ No pool exhaustion!")

    engine.dispose()


def concurrent_with_proper_cleanup():
    """Show proper cleanup under concurrent load."""
    print("\n" + "=" * 80)
    print("GOOD: Proper Cleanup Under Load")
    print("=" * 80)

    engine = create_engine(
        "sqlite:///./test_pool.db",
        poolclass=QueuePool,
        pool_size=2,
        max_overflow=1,  # Max 3 total
        pool_timeout=5,  # Reasonable timeout
        echo=False,
    )

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)

    print("\nRunning 10 workers with proper cleanup...")
    print("Even with only 3 max connections, all workers will succeed!\n")

    def worker(worker_id: int):
        """Worker that properly closes connection."""
        # Use 'with' statement - connection auto-returned
        with Session() as session:
            session.execute(select(User)).scalars().all()
            time.sleep(0.1)  # Simulate work
            # Connection returned automatically when 'with' block ends
        return f"Worker {worker_id}: ✓ Success"

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(10)]
        results = [future.result() for future in futures]

    end_time = time.time()

    print("Results:")
    for result in results:
        print(f"  {result}")

    success_count = sum(1 for r in results if "Success" in r)

    print(f"\n{'=' * 80}")
    print(f"Success: {success_count}/10")
    print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
    print("=" * 80)

    print("\n✅ All workers succeeded!")
    print("✅ Connections were reused efficiently")
    print("✅ No timeouts or errors")

    engine.dispose()


def comparison_demo():
    """Direct comparison of bad vs good approach."""
    print("\n" + "=" * 80)
    print("COMPARISON: Bad vs Good Cleanup")
    print("=" * 80)

    engine = create_engine(
        "sqlite:///./test_pool.db", poolclass=QueuePool, pool_size=2, max_overflow=0, echo=False
    )

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    pool = engine.pool  # type: ignore[attr-defined]

    # Bad approach
    print("\n❌ Bad approach (not closing):")
    sessions_bad = []
    for i in range(2):
        session = Session()
        session.execute(select(User)).scalars().all()
        sessions_bad.append(session)
        checked_out = pool.checkedout()  # type: ignore[attr-defined]
        print(f"  Connection {i+1}: checked_out = {checked_out}")

    print(f"  Result: Pool exhausted (checked_out = {pool.checkedout()})")  # type: ignore[attr-defined]

    # Clean up
    for session in sessions_bad:
        session.close()

    time.sleep(0.1)

    # Good approach
    print("\n✅ Good approach (with statement):")
    for i in range(2):
        with Session() as session:
            session.execute(select(User)).scalars().all()
            checked_out = pool.checkedout()  # type: ignore[attr-defined]
            print(f"  Connection {i+1}: checked_out = {checked_out}")
        checked_out_after = pool.checkedout()  # type: ignore[attr-defined]
        print(f"           After 'with': checked_out = {checked_out_after}")

    print(f"  Result: Pool available (checked_out = {pool.checkedout()})")  # type: ignore[attr-defined]

    engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLUTION: Proper Connection Cleanup")
    print("=" * 80)
    print("\nThis shows the correct way to manage connections.")
    print("Compare with bad_pool_exhaustion.py to see the difference!")
    print("=" * 80)

    proper_cleanup_approach()
    concurrent_with_proper_cleanup()
    comparison_demo()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAY")
    print("=" * 80)
    print("Always use:")
    print("  with Session() as session:")
    print("      # Your code here")
    print("      # Connection auto-returned when block ends")
    print("\nNEVER:")
    print("  session = Session()  # Without 'with'")
    print("  # Forgot to close - connection leaked!")
    print("=" * 80)
