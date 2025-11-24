"""
BAD: Pool exhaustion - not closing connections properly.

This demonstrates what happens when you don't close connections:
- Pool gets exhausted
- New requests wait or timeout
- Application becomes unresponsive
"""

import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, select
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.pool import QueuePool

from src.models import User


def pool_exhaustion_problem():
    """Bad: Not closing connections properly leads to pool exhaustion."""
    print("\n" + "=" * 80)
    print("BAD: Not Closing Connections = Pool Exhaustion")
    print("=" * 80)

    # Small pool to make problem obvious
    engine = create_engine(
        "sqlite:///./test_pool.db",
        poolclass=QueuePool,
        pool_size=3,  # Only 3 connections
        max_overflow=0,  # No overflow
        pool_timeout=2,  # Timeout after 2 seconds
        echo=False,
    )

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    pool = engine.pool  # type: ignore[attr-defined]

    print("\nPool configuration:")
    print("  pool_size: 3")
    print("  max_overflow: 0")
    print("  Total max connections: 3")
    print("  pool_timeout: 2 seconds\n")

    print("Opening connections but NOT closing them...\n")

    # Bad practice: Open connections but don't close
    sessions = []
    for i in range(3):
        session = Session()
        session.execute(select(User)).scalars().all()
        sessions.append(session)  # Not closing!
        checked_out = pool.checkedout()  # type: ignore[attr-defined]
        print(f"  Connection {i+1}: Opened (checked_out: {checked_out})")
        time.sleep(0.1)

    print("\n❌ All 3 connections are now checked out and NOT returned!")

    # Try to get another connection
    print("\nTrying to open 4th connection...")
    try:
        session4 = Session()
        session4.execute(select(User)).scalars().all()
        print("  ✓ Got connection")
    except SQLAlchemyTimeoutError:
        print("  ❌ TIMEOUT! No connections available!")
        print("  ⚠️  Application is stuck - pool exhausted!")

    # Clean up
    for session in sessions:
        session.close()
    engine.dispose()

    print("\n" + "=" * 80)
    print("PROBLEMS:")
    print("  • Connections not returned to pool")
    print("  • Pool becomes exhausted")
    print("  • New requests timeout")
    print("  • Application becomes unresponsive")
    print("=" * 80)


def concurrent_exhaustion_demo():
    """Show exhaustion under concurrent load."""
    print("\n" + "=" * 80)
    print("BAD: Pool Exhaustion Under Load")
    print("=" * 80)

    engine = create_engine(
        "sqlite:///./test_pool.db",
        poolclass=QueuePool,
        pool_size=2,
        max_overflow=1,  # Max 3 total
        pool_timeout=1,  # Short timeout
        echo=False,
    )

    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)

    print("\nRunning 10 workers but only 3 connections available...")

    def worker(worker_id: int):
        """Worker that holds connection."""
        try:
            session = Session()
            session.execute(select(User)).scalars().all()
            time.sleep(0.5)  # Hold connection
            session.close()  # Eventually close
            return f"Worker {worker_id}: Success"
        except SQLAlchemyTimeoutError:
            return f"Worker {worker_id}: ❌ TIMEOUT!"
        except Exception as e:
            return f"Worker {worker_id}: ❌ ERROR - {type(e).__name__}"

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(10)]
        results = [future.result() for future in futures]

    print("\nResults:")
    success_count = sum(1 for r in results if "Success" in r)
    timeout_count = sum(1 for r in results if "TIMEOUT" in r)

    for result in results:
        if "TIMEOUT" in result:
            print(f"  {result}")
        else:
            print(f"  {result}")

    print(f"\n{'=' * 80}")
    print(f"Success: {success_count}/10")
    print(f"Timeouts: {timeout_count}/10")
    print("=" * 80)

    print("\n⚠️  Some workers failed because pool was exhausted!")

    engine.dispose()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEMONSTRATING THE PROBLEM: Pool Exhaustion")
    print("=" * 80)
    print("\nThis shows what happens when connections aren't closed properly.")
    print("See good_proper_cleanup.py for the solution!")
    print("=" * 80)

    pool_exhaustion_problem()
    concurrent_exhaustion_demo()

    print("\n" + "=" * 80)
    print("💡 TIP: Always use 'with' statement or close() sessions!")
    print("=" * 80)
