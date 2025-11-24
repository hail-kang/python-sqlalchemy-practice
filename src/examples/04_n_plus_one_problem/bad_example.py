"""
Bad Example: Lazy Loading causing N+1 problem.

This demonstrates the performance issue when relationships are lazy-loaded.
"""

import time

from sqlalchemy import select

from src.config.database import DatabaseConfig
from src.models import User
from src.utils.db_init import reset_database
from src.utils.sample_data import create_all_sample_data


def demonstrate_n_plus_one_problem():
    """Show the N+1 problem with lazy loading."""
    db = DatabaseConfig()

    # Setup test data
    print("Setting up test data...")
    reset_database(db.engine)

    with db.get_session() as session:
        create_all_sample_data(
            session,
            user_count=10,
            posts_per_user=5,
            comments_per_post=3,
            campaign_count=5,
            applications_per_campaign=3,
        )

    print("\n" + "=" * 80)
    print("BAD EXAMPLE: Lazy Loading (N+1 Problem)")
    print("=" * 80)

    with db.get_session() as session:
        print("\nQuery 1: Fetching all users...")
        start_time = time.time()

        # This is ONE query
        users = session.execute(select(User)).scalars().all()

        print(f"\n✓ Fetched {len(users)} users")
        print("\nNow accessing user.posts for each user...")
        print("Watch the SQL queries below - each iteration triggers a new query!\n")

        # This triggers N additional queries (one per user)
        for i, user in enumerate(users, 1):
            # Accessing user.posts triggers a SELECT query
            post_count = len(user.posts)
            print(f"  {i}. {user.username}: {post_count} posts")

        end_time = time.time()

        print("\n" + "-" * 80)
        print(f"Total queries: 1 (users) + {len(users)} (posts) = {1 + len(users)} queries")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("-" * 80)


def demonstrate_multiple_relationships():
    """Show N+1 problem gets worse with multiple relationships."""
    db = DatabaseConfig()

    print("\n" + "=" * 80)
    print("WORSE: Multiple Relationships (N+1+1 Problem)")
    print("=" * 80)

    with db.get_session() as session:
        print("\nQuery 1: Fetching all users...")
        start_time = time.time()

        users = session.execute(select(User)).scalars().all()

        print(f"\n✓ Fetched {len(users)} users")
        print("\nNow accessing BOTH user.posts AND user.comments...")
        print("This will trigger 2N additional queries!\n")

        for i, user in enumerate(users, 1):
            post_count = len(user.posts)  # N queries
            comment_count = len(user.comments)  # N more queries
            print(f"  {i}. {user.username}: {post_count} posts, {comment_count} comments")

        end_time = time.time()

        print("\n" + "-" * 80)
        print(
            f"Total queries: 1 (users) + {len(users)} (posts) + {len(users)} (comments) = {1 + 2*len(users)} queries"
        )
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("-" * 80)


def demonstrate_nested_relationships():
    """Show N+1 problem with nested relationships."""
    db = DatabaseConfig()

    print("\n" + "=" * 80)
    print("NIGHTMARE: Nested Relationships (Exponential Queries)")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching users, then their posts, then post comments...")
        start_time = time.time()

        users = session.execute(select(User)).scalars().all()
        total_queries = 1  # Initial users query

        for user in users:
            posts = user.posts  # 1 query per user
            total_queries += 1

            for post in posts:
                _ = post.comments  # 1 query per post
                total_queries += 1

        end_time = time.time()

        print(f"\n✓ Processed {len(users)} users and their posts and comments")
        print("\n" + "-" * 80)
        print(f"Total queries: {total_queries} (exponential growth!)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("-" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("N+1 PROBLEM DEMONSTRATION")
    print("=" * 80)
    print("\nThis script demonstrates the N+1 query problem.")
    print("Watch the SQL queries in the output - you'll see many repeated queries!")
    print("\nNOTE: This is the BAD way. See good_example.py for solutions.")
    print("=" * 80)

    demonstrate_n_plus_one_problem()
    demonstrate_multiple_relationships()
    demonstrate_nested_relationships()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("The N+1 problem causes:")
    print("  • Excessive database queries")
    print("  • Poor performance")
    print("  • High database load")
    print("  • Slow response times")
    print("\nSolution: Use eager loading (see good_example.py)")
    print("=" * 80)
