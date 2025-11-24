"""
GOOD: Loading only specific columns needed.

This demonstrates efficient partial select patterns.
"""

import time

from sqlalchemy import func, select
from sqlalchemy.orm import load_only

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


def good_select_single_column():
    """Good: Select only username column."""
    print("\n" + "=" * 80)
    print("GOOD: Select Single Column")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading ONLY username column...")
    print("No unnecessary data!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Good: Select only username
        stmt = select(User.username)
        usernames = session.execute(stmt).scalars().all()
        print(f"  Loaded {len(usernames)} usernames")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Data loaded: 1 column × {record_count} rows = {record_count} values")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Loaded only 1 column (username)")
    print("  • 86% less data transfer (1/7 columns)")
    print("  • Much faster query")
    print("  • Minimal memory usage")
    print("  • Simple, clean code")

    print("\n📊 Sample data:")
    for username in usernames[:5]:
        print(f"  {username}")
    print("  ...")


def good_select_multiple_columns():
    """Good: Select multiple specific columns."""
    print("\n" + "=" * 80)
    print("GOOD: Select Multiple Columns")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading only username and email columns...")
    print("Perfect for display lists!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Good: Select only needed columns
        stmt = select(User.username, User.email)
        results = session.execute(stmt).all()
        print(f"  Loaded {len(results)} tuples (username, email)")

        # Easy to unpack
        display_list = [{"username": username, "email": email} for username, email in results]
        print(f"  Created {len(display_list)} display items")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Data loaded: 2 columns × {record_count} rows = {record_count * 2} values")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Loaded only 2 columns (username, email)")
    print("  • 71% less data transfer (2/7 columns)")
    print("  • Fast query execution")
    print("  • Returns clean tuples")

    print("\n📊 Sample data:")
    for item in display_list[:5]:
        print(f"  {item}")
    print("  ...")


def good_select_with_mappings():
    """Good: Use mappings() for dictionary-like access."""
    print("\n" + "=" * 80)
    print("GOOD: Select with mappings() - Dictionary Access")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading with mappings() for readable code...")
    print("Returns dictionary-like objects!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Good: Use mappings() for readability
        stmt = select(User.username, User.email, User.is_active)
        results = session.execute(stmt).mappings().all()
        print(f"  Loaded {len(results)} row mappings")

        # Self-documenting access
        for row in results[:3]:
            print(f"  {row['username']}: {row['email']} (active: {row['is_active']})")
        print("  ...")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Dictionary-like access with row['column']")
    print("  • Self-documenting code")
    print("  • Easy to work with")
    print("  • Great for JSON serialization")


def good_load_only_with_orm():
    """Good: Use load_only() when need ORM instances."""
    print("\n" + "=" * 80)
    print("GOOD: load_only() for Partial ORM Loading")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading ORM instances with only specific columns...")
    print("Still get User objects, but only loaded fields!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Good: Load only specific columns into ORM instances
        stmt = select(User).options(load_only(User.username, User.email))
        users = session.execute(stmt).scalars().all()
        print(f"  Loaded {len(users)} User instances (partial)")

        for user in users[:3]:
            print(f"  User: {user.username} ({user.email})")
        print("  ...")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Get ORM model instances")
    print("  • Only specified columns loaded")
    print("  • Other attributes lazy-load if accessed")
    print("  • Useful when need ORM features")

    print("\n⚠️  TRADE-OFFS:")
    print("  • Slightly slower than plain select()")
    print("  • ORM overhead still present")
    print("  • Use plain select() if don't need ORM")


def good_existence_check():
    """Good: Efficient existence check."""
    print("\n" + "=" * 80)
    print("GOOD: Efficient Existence Check")
    print("=" * 80)

    db = DatabaseConfig()

    print("\nPreparing test users...")
    prepare_test_data(db, 100)
    print("Test data ready\n")

    print("Checking existence without loading data...")
    print("Only query for ID!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Good: Only select ID to check existence
        stmt = select(User.id).where(User.username == "user50").limit(1)
        exists = session.execute(stmt).scalar() is not None

        print(f"  Existence check result: {exists}")
        print("  No data loaded, just TRUE/FALSE")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Only loads 1 value (ID)")
    print("  • Minimal data transfer")
    print("  • Fast existence check")
    print("  • Can also use func.count() for similar check")


def good_dropdown_list():
    """Good: Efficient dropdown data."""
    print("\n" + "=" * 80)
    print("GOOD: Efficient Dropdown List")
    print("=" * 80)

    db = DatabaseConfig()
    record_count = 1000

    print(f"\nPreparing {record_count} test users...")
    prepare_test_data(db, record_count)
    print("Test data ready\n")

    print("Loading only ID and username for dropdown...")
    print("Perfect for HTML <select> elements!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Good: Select only columns needed for dropdown
        stmt = select(User.id, User.username).where(User.is_active == True).order_by(User.username)  # noqa: E712
        results = session.execute(stmt).all()
        print(f"  Loaded {len(results)} (id, username) tuples")

        # Create dropdown options
        dropdown_options = [{"value": user_id, "label": username} for user_id, username in results]
        print(f"  Created {len(dropdown_options)} dropdown options")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print(f"Data loaded: 2 columns × {record_count} rows = {record_count * 2} values")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Only 2 columns loaded (id, username)")
    print("  • 71% less data transfer")
    print("  • Fast query for large lists")
    print("  • Common pattern in web apps")

    print("\n📊 Dropdown options:")
    for option in dropdown_options[:5]:
        print(f"  {option}")
    print("  ...")


def good_count_without_loading():
    """Good: Count records without loading data."""
    print("\n" + "=" * 80)
    print("GOOD: Count Without Loading Data")
    print("=" * 80)

    db = DatabaseConfig()

    print("\nPreparing test users...")
    prepare_test_data(db, 1000)
    print("Test data ready\n")

    print("Counting records without loading any data...")
    print("Using func.count()!\n")

    start_time = time.time()

    with db.get_session() as session:
        # Good: Count without loading
        stmt = select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
        count = session.execute(stmt).scalar()

        print(f"  Active users count: {count}")
        print("  No data loaded!")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'=' * 80}")
    print(f"Total time: {total_time*1000:.2f}ms")
    print("=" * 80)

    print("\n✅ BENEFITS:")
    print("  • Database does the counting")
    print("  • Zero data transfer")
    print("  • Extremely fast")
    print("  • Scales to millions of records")


# ============================================================================
# Type-Safe Partial Select Patterns
# ============================================================================
def type_safe_with_typeddict():
    """Type-safe partial select with TypedDict (RECOMMENDED)."""
    print("\n" + "=" * 80)
    print("TYPE-SAFE: TypedDict with select() (RECOMMENDED)")
    print("=" * 80)

    from typing import TypedDict

    class UserBasicInfo(TypedDict):
        """Type-safe partial user data."""

        username: str
        email: str

    db = DatabaseConfig()
    prepare_test_data(db, 10)

    with db.get_session() as session:
        # Select only needed columns
        stmt = select(User.username, User.email)
        results = session.execute(stmt).mappings().all()

        # Type-safe conversion
        users: list[UserBasicInfo] = [
            {"username": row["username"], "email": row["email"]} for row in results
        ]

        print("\n✅ Type-safe access:")
        print(f"  users[0]['username'] = {users[0]['username']}")
        print(f"  users[0]['email'] = {users[0]['email']}")

        print("\n❌ This would be a TYPE ERROR:")
        print("  users[0]['full_name']  # Type checker catches this!")

        print("\n✅ BENEFITS:")
        print("  • Type checker catches invalid field access")
        print("  • Clear which fields are available")
        print("  • Fastest performance (no ORM overhead)")
        print("  • Great for most use cases")


def type_safe_with_dataclass():
    """Type-safe partial select with dataclass."""
    print("\n" + "=" * 80)
    print("TYPE-SAFE: Dataclass for Partial Data")
    print("=" * 80)

    from dataclasses import dataclass

    @dataclass
    class UserBasic:
        """Partial user data with only username and email."""

        username: str
        email: str

    db = DatabaseConfig()
    prepare_test_data(db, 10)

    with db.get_session() as session:
        # Select specific columns
        stmt = select(User.username, User.email)
        results = session.execute(stmt).all()

        # Type-safe conversion
        users = [UserBasic(username=username, email=email) for username, email in results]

        print("\n✅ Type-safe access:")
        print(f"  users[0].username = {users[0].username}")
        print(f"  users[0].email = {users[0].email}")

        print("\n❌ This would be an ATTRIBUTE ERROR:")
        print("  users[0].full_name  # Type checker catches this!")

        print("\n✅ BENEFITS:")
        print("  • Type-safe with attribute access")
        print("  • Dataclass benefits (__repr__, __eq__, etc.)")
        print("  • Can add methods")
        print("  • Good for complex data structures")


def type_safe_with_pydantic():
    """Type-safe partial select with Pydantic (for APIs)."""
    print("\n" + "=" * 80)
    print("TYPE-SAFE: Pydantic Model (with validation)")
    print("=" * 80)

    try:
        from pydantic import BaseModel, EmailStr  # type: ignore[import-not-found]

        class UserBasicSchema(BaseModel):
            """Validated partial user data."""

            username: str
            email: EmailStr  # Email validation!

        db = DatabaseConfig()
        prepare_test_data(db, 10)

        with db.get_session() as session:
            # Select specific columns
            stmt = select(User.username, User.email)
            results = session.execute(stmt).mappings().all()

            # Type-safe + validated conversion
            # Method 1: model_validate() - recommended for Pydantic v2
            users = [UserBasicSchema.model_validate(row) for row in results]

            print("\n✅ Type-safe access:")
            print(f"  users[0].username = {users[0].username}")
            print(f"  users[0].email = {users[0].email}")

            print("\n❌ This would be an ATTRIBUTE ERROR:")
            print("  users[0].full_name  # Type checker catches this!")

            print("\n✅ BENEFITS:")
            print("  • Type-safe")
            print("  • Email validation at runtime")
            print("  • JSON serialization built-in")
            print("  • Perfect for FastAPI/APIs")
            print("  • model_validate() is explicit and preferred in Pydantic v2")

    except ImportError:
        print("\n⚠️  Pydantic not installed")
        print("Install: uv add pydantic")
        print("\n📝 Example usage:")
        print("  users = [UserBasicSchema.model_validate(row) for row in results]")
        print("  # or")
        print("  users = [UserBasicSchema(**row) for row in results]")


def why_avoid_load_only():
    """Show why load_only() breaks type safety."""
    print("\n" + "=" * 80)
    print("⚠️  WHY AVOID load_only()?")
    print("=" * 80)

    db = DatabaseConfig()
    prepare_test_data(db, 10)

    with db.get_session() as session:
        # Load only username and email
        stmt = select(User).options(load_only(User.username, User.email))
        users = session.execute(stmt).scalars().all()

        print("\n❌ PROBLEM: Type is list[User], but not all fields loaded!")
        print(f"  users[0].username = {users[0].username}  # ✅ Loaded")
        print(f"  users[0].email = {users[0].email}  # ✅ Loaded")
        print(f"  users[0].full_name = {users[0].full_name}  # ⚠️  NOT loaded but no type error!")
        print(f"  users[0].is_active = {users[0].is_active}  # ⚠️  NOT loaded but no type error!")

        print("\n❌ PROBLEMS:")
        print("  • Type checker doesn't catch unloaded field access")
        print("  • Runtime returns loaded values or triggers lazy load")
        print("  • Hard to know which fields are actually available")
        print("  • Breaks type safety!")

        print("\n✅ SOLUTION: Use select() with TypedDict/Dataclass instead")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLUTION: Efficient Partial Select")
    print("=" * 80)
    print("\nCompare these with bad_loading_everything.py to see the difference!")
    print("=" * 80)

    # Part 1: Efficient partial select patterns
    good_select_single_column()
    good_select_multiple_columns()
    good_select_with_mappings()
    good_load_only_with_orm()
    good_existence_check()
    good_dropdown_list()
    good_count_without_loading()

    # Part 2: Type-safe patterns
    print("\n" + "=" * 80)
    print("PART 2: TYPE-SAFE PATTERNS")
    print("=" * 80)

    type_safe_with_typeddict()
    type_safe_with_dataclass()
    type_safe_with_pydantic()
    why_avoid_load_only()

    # Final conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\n📊 Recommended approaches:")
    print("  • Single column: select(Model.column) ✅")
    print("  • Multiple columns: select(Model.col1, Model.col2)")
    print("  • Readable code: select(...).mappings()")
    print("  • Existence check: select(Model.id).limit(1)")
    print("  • Counting: select(func.count()).select_from(Model)")

    print("\n🛡️  Type-safe patterns:")
    print("  • Default: TypedDict + select(...).mappings() ✅")
    print("  • Complex data: Dataclass")
    print("  • APIs: Pydantic with model_validate()")
    print("  • AVOID: load_only() - breaks type safety!")

    print("\n💡 Key rules:")
    print("  1. Load only what you need")
    print("  2. Use type-safe patterns (TypedDict/Dataclass/Pydantic)")
    print("  3. Avoid load_only() - use explicit column selection")
    print("=" * 80)
