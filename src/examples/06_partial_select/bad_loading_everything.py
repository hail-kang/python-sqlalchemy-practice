"""
BAD: Loading entire objects when only need specific columns.

This demonstrates the performance problem of over-fetching data.
"""

import time

from sqlalchemy import select

from src.config.database import DatabaseConfig
from src.models import User
from src.utils.db_init import reset_database


def prepare_test_data(db: DatabaseConfig, count: int = 1000):
    """Prepare test data."""
    reset_database(db.engine)

    with db.get_session() as session:
        user_dicts = [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User Number {i}",
                "is_active": True,
            }
            for i in range(count)
        ]
        session.bulk_insert_mappings(User, user_dicts)  # type: ignore[arg-type]
        session.commit()


def bad_load_everything_for_username():
    """Bad: Load entire User objects just to get usernames."""
    print("\n" + "=" * 80)
    print("BAD: Loading Full Objects for Single Column")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading ENTIRE User objects just to get usernames...")
    print("Fetching all 7 columns unnecessarily!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Bad: Load everything
        users = session.execute(select(User)).scalars().all()
        print(f"  Loaded {len(users)} full User objects")

        # Only use username!
        usernames = [user.username for user in users]
        print(f"  Extracted {len(usernames)} usernames")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Data loaded: 7 columns × {record_count} rows = {record_count * 7} values")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print("  • Loaded ALL 7 columns (id, username, email, full_name, is_active, created_at, updated_at)")
    print("  • Only used 1 column (username)")
    print("  • Wasted 86% of data transfer (6/7 columns unused)")
    print("  • High memory usage for unused data")
    print("  • Slower query execution")

    # Show sample data
    print("\n📊 Sample of loaded data:")
    if users:
        user = users[0]
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Full Name: {user.full_name}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Created At: {user.created_at}")
        print(f"  Updated At: {user.updated_at}")
        print("  ⚠️  Only username was actually used!")


def bad_load_everything_for_display_list():
    """Bad: Load full objects for simple display list."""
    print("\n" + "=" * 80)
    print("BAD: Loading Full Objects for Display List")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading ENTIRE User objects for display list...")
    print("Only need username and email for display!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Bad: Load everything
        users = session.execute(select(User)).scalars().all()
        print(f"  Loaded {len(users)} full User objects")

        # Only display username and email
        display_list = [{"username": u.username, "email": u.email} for u in users]
        print(f"  Created {len(display_list)} display items")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Data loaded: 7 columns × {record_count} rows = {record_count * 7} values")
    print(f"Data used: 2 columns × {record_count} rows = {record_count * 2} values")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print("  • Loaded 7 columns, used only 2")
    print("  • Wasted 71% of data transfer (5/7 columns unused)")
    print("  • Created ORM objects unnecessarily")
    print("  • High memory overhead")

    # Show sample
    print("\n📊 What we actually needed:")
    for item in display_list[:3]:
        print(f"  {item}")
    print("  ...")


def bad_load_everything_for_existence_check():
    """Bad: Load entire record just to check existence."""
    print("\n" + "=" * 80)
    print("BAD: Loading Full Object for Existence Check")
    print("=" * 80)

    db = DatabaseConfig()

    print("\nPreparing test users...")
    prepare_test_data(db, 100)
    print("Test data ready\n")

    print("Loading ENTIRE User object just to check if username exists...")
    print("Only need to know TRUE/FALSE!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Bad: Load entire object
        user = session.execute(select(User).where(User.username == "user50")).scalar_one_or_none()

        exists = user is not None
        print(f"  Loaded full User object: {user is not None}")
        print(f"  Existence check result: {exists}")

        if user:
            print("\n  Loaded data (all unused except existence):")
            print(f"    ID: {user.id}")
            print(f"    Username: {user.username}")
            print(f"    Email: {user.email}")
            print(f"    Full Name: {user.full_name}")
            print(f"    Is Active: {user.is_active}")
            print(f"    Created At: {user.created_at}")
            print(f"    Updated At: {user.updated_at}")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print("  • Loaded all 7 columns")
    print("  • Only needed boolean (exists or not)")
    print("  • 100% of data was unnecessary")
    print("  • Could use COUNT or simple ID check")


def bad_load_everything_for_dropdown():
    """Bad: Load full objects for dropdown list."""
    print("\n" + "=" * 80)
    print("BAD: Loading Full Objects for Dropdown Menu")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading ENTIRE User objects for HTML <select> dropdown...")
    print("Dropdown only needs ID and username!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Bad: Load everything for dropdown
        users = session.execute(select(User).where(User.is_active == True)).scalars().all()  # noqa: E712
        print(f"  Loaded {len(users)} full User objects")

        # Create dropdown options (only need id + username)
        dropdown_options = [{"value": u.id, "label": u.username} for u in users]
        print(f"  Created {len(dropdown_options)} dropdown options")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n❌ PROBLEMS:")
    print("  • Loaded 7 columns per user")
    print("  • Dropdown only needs 2 columns (id, username)")
    print("  • Wasted 71% of data transfer")
    print("  • Common mistake in web applications")

    print("\n📊 Dropdown needs only:")
    for option in dropdown_options[:5]:
        print(f"  {option}")
    print("  ...")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEMONSTRATING THE PROBLEM: Over-fetching Data")
    print("=" * 80)
    print("\nThis shows why loading entire objects is inefficient.")
    print("See good_partial_select.py for the solution!")
    print("=" * 80)

    bad_load_everything_for_username()
    bad_load_everything_for_display_list()
    bad_load_everything_for_existence_check()
    bad_load_everything_for_dropdown()

    print("\n" + "=" * 80)
    print("💡 TIP: Use partial select to load only what you need!")
    print("=" * 80)
