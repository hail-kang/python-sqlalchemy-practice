"""
Good Examples: Solving N+1 problem with eager loading.

This demonstrates various solutions to the N+1 problem:
1. joinedload() - Single query with JOIN
2. selectinload() - Separate query with IN clause (recommended)
3. subqueryload() - Separate query with subquery
4. Manual grouping - Fetch and group in Python
"""

import time
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload, subqueryload

from src.config.database import DatabaseConfig
from src.models import Comment, Post, User
from src.utils.db_init import reset_database
from src.utils.sample_data import create_all_sample_data


def setup_data():
    """Setup test data once."""
    db = DatabaseConfig()
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
    print("✓ Test data ready\n")
    return db


def demonstrate_joinedload(db):
    """Solution 1: Single query with JOIN."""
    print("\n" + "=" * 80)
    print("SOLUTION 1: joinedload() - Single Query with JOIN")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching users with posts using LEFT OUTER JOIN...")
        start_time = time.time()

        # Single query with JOIN
        stmt = select(User).options(joinedload(User.posts))
        users = session.execute(stmt).unique().scalars().all()

        print(f"\n✓ Fetched {len(users)} users with their posts")
        print("\nAccessing user.posts - NO additional queries:")

        for i, user in enumerate(users, 1):
            post_count = len(user.posts)  # No query!
            print(f"  {i}. {user.username}: {post_count} posts")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 1 (users + posts in single JOIN)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nPros: Single query, simple")
        print("Cons: Cartesian product with large datasets")
        print("-" * 80)


def demonstrate_selectinload(db):
    """Solution 2: Separate query with IN clause (RECOMMENDED)."""
    print("\n" + "=" * 80)
    print("SOLUTION 2: selectinload() - SELECT...IN Query (RECOMMENDED)")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching users, then posts with IN clause...")
        start_time = time.time()

        # Query 1: Users, Query 2: Posts with IN
        stmt = select(User).options(selectinload(User.posts))
        users = session.execute(stmt).scalars().all()

        print(f"\n✓ Fetched {len(users)} users with their posts")
        print("\nAccessing user.posts - NO additional queries:")

        for i, user in enumerate(users, 1):
            post_count = len(user.posts)  # No query!
            print(f"  {i}. {user.username}: {post_count} posts")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 2 (1 for users, 1 for posts with IN)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nPros: No cartesian product, efficient, clean")
        print("Cons: Two queries instead of one")
        print("✅ RECOMMENDED for most cases")
        print("-" * 80)


def demonstrate_subqueryload(db):
    """Solution 3: Separate query with subquery."""
    print("\n" + "=" * 80)
    print("SOLUTION 3: subqueryload() - Subquery Approach")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching users, then posts with subquery...")
        start_time = time.time()

        # Query 1: Users, Query 2: Posts with subquery
        stmt = select(User).options(subqueryload(User.posts))
        users = session.execute(stmt).scalars().all()

        print(f"\n✓ Fetched {len(users)} users with their posts")
        print("\nAccessing user.posts - NO additional queries:")

        for i, user in enumerate(users, 1):
            post_count = len(user.posts)  # No query!
            print(f"  {i}. {user.username}: {post_count} posts")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 2 (1 for users, 1 for posts with subquery)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nPros: Works with complex filtering")
        print("Cons: Generally selectinload() is preferred")
        print("-" * 80)


def demonstrate_manual_grouping(db):
    """Solution 4: Manual grouping in Python."""
    print("\n" + "=" * 80)
    print("SOLUTION 4: Manual Grouping in Python")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching users and posts separately, then grouping in Python...")
        start_time = time.time()

        # Query 1: Fetch all users
        users = session.execute(select(User)).scalars().all()
        print(f"\n✓ Fetched {len(users)} users")

        # Query 2: Fetch all posts at once
        user_ids = [user.id for user in users]
        posts = session.execute(select(Post).where(Post.author_id.in_(user_ids))).scalars().all()
        print(f"✓ Fetched {len(posts)} posts")

        # Group posts by user in Python
        print("\nGrouping posts by user in Python memory...")
        posts_by_user = defaultdict(list)
        for post in posts:
            posts_by_user[post.author_id].append(post)

        print("\nUsing grouped data:")
        for i, user in enumerate(users, 1):
            user_posts = posts_by_user[user.id]
            print(f"  {i}. {user.username}: {len(user_posts)} posts")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 2 (1 for users, 1 for all posts)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nPros: Full control, can add custom logic")
        print("Cons: Manual mapping, more verbose code")
        print("Use case: Custom grouping, complex aggregations")
        print("-" * 80)


def demonstrate_multiple_relationships(db):
    """Load multiple relationships efficiently."""
    print("\n" + "=" * 80)
    print("BONUS: Multiple Relationships with selectinload()")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching users with posts AND comments...")
        start_time = time.time()

        # Load multiple relationships
        stmt = select(User).options(
            selectinload(User.posts), selectinload(User.comments), selectinload(User.applications)
        )
        users = session.execute(stmt).scalars().all()

        print(f"\n✓ Fetched {len(users)} users with all their relationships")
        print("\nAccessing multiple relationships - NO additional queries:")

        for i, user in enumerate(users, 1):
            post_count = len(user.posts)
            comment_count = len(user.comments)
            app_count = len(user.applications)
            print(
                f"  {i}. {user.username}: {post_count} posts, {comment_count} comments, {app_count} applications"
            )

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 4 (1 users + 3 relationships)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nCompare to lazy loading: Would be 1 + 3N queries!")
        print("-" * 80)


def demonstrate_nested_relationships(db):
    """Load nested relationships efficiently."""
    print("\n" + "=" * 80)
    print("BONUS: Nested Relationships (Users -> Posts -> Comments)")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching users -> posts -> comments in 3 queries...")
        start_time = time.time()

        # Chain options for nested loading
        stmt = select(User).options(selectinload(User.posts).selectinload(Post.comments))
        users = session.execute(stmt).scalars().all()

        print(f"\n✓ Fetched {len(users)} users with posts and comments")
        print("\nAccessing nested relationships - NO additional queries:")

        total_posts = 0
        total_comments = 0
        for user in users:
            for post in user.posts:
                total_posts += 1
                total_comments += len(post.comments)

        print(f"  Processed {len(users)} users")
        print(f"  Processed {total_posts} posts")
        print(f"  Processed {total_comments} comments")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 3 (users, posts, comments)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print(
            f"\nCompare to lazy loading: Would be 1 + {len(users)} + {total_posts} = {1 + len(users) + total_posts} queries!"
        )
        print("-" * 80)


def demonstrate_manual_nested_grouping(db):
    """Manual grouping for nested relationships."""
    print("\n" + "=" * 80)
    print("BONUS: Manual Nested Grouping (Full Control)")
    print("=" * 80)

    with db.get_session() as session:
        print("\nFetching and grouping users -> posts -> comments manually...")
        start_time = time.time()

        # Query 1: Users
        users = session.execute(select(User)).scalars().all()
        user_ids = [user.id for user in users]

        # Query 2: Posts
        posts = session.execute(select(Post).where(Post.author_id.in_(user_ids))).scalars().all()
        post_ids = [post.id for post in posts]

        # Query 3: Comments
        comments = (
            session.execute(select(Comment).where(Comment.post_id.in_(post_ids))).scalars().all()
        )

        # Group in Python
        print("\nGrouping data in Python...")
        posts_by_user = defaultdict(list)
        for post in posts:
            posts_by_user[post.author_id].append(post)

        comments_by_post = defaultdict(list)
        for comment in comments:
            comments_by_post[comment.post_id].append(comment)

        # Use grouped data
        print("\nProcessing grouped data:")
        for user in users[:3]:  # Show first 3
            user_posts = posts_by_user[user.id]
            print(f"\n  {user.username}:")
            for post in user_posts[:2]:  # Show first 2 posts
                post_comments = comments_by_post[post.id]
                print(f"    - {post.title}: {len(post_comments)} comments")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 3 (users, posts, comments)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nPros: Full control over queries and grouping logic")
        print("Cons: More manual code, not using ORM relationships")
        print("-" * 80)


def demonstrate_without_foreign_keys(db):
    """Manual grouping when foreign key constraints don't exist."""
    print("\n" + "=" * 80)
    print("SPECIAL CASE: No Foreign Key Constraints (Startup Pattern)")
    print("=" * 80)
    print("\nMany startups don't use FK constraints for flexibility.")
    print("In this case, ORM features like selectinload() won't work!")
    print("Manual grouping is the ONLY solution.\n")

    with db.get_session() as session:
        print("Simulating queries without relationship() support...")
        start_time = time.time()

        # Query 1: Fetch users (no relationship loading possible)
        users = session.execute(select(User)).scalars().all()
        user_ids = [user.id for user in users]
        print(f"\n✓ Fetched {len(users)} users")

        # Query 2: Fetch posts manually with IN clause
        posts = session.execute(select(Post).where(Post.author_id.in_(user_ids))).scalars().all()
        print(f"✓ Fetched {len(posts)} posts with IN clause")

        # Query 3: Fetch comments manually
        post_ids = [post.id for post in posts]
        comments = (
            session.execute(select(Comment).where(Comment.post_id.in_(post_ids))).scalars().all()
        )
        print(f"✓ Fetched {len(comments)} comments with IN clause")

        # Group in Python (since ORM can't help)
        print("\nGrouping data in Python memory...")
        posts_by_user = defaultdict(list)
        for post in posts:
            posts_by_user[post.author_id].append(post)

        comments_by_post = defaultdict(list)
        for comment in comments:
            comments_by_post[comment.post_id].append(comment)

        # Use grouped data
        print("\nUsing grouped data (first 3 users):")
        for user in users[:3]:
            user_posts = posts_by_user[user.id]
            total_comments = sum(len(comments_by_post[post.id]) for post in user_posts)
            print(f"  {user.username}: {len(user_posts)} posts, {total_comments} comments")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 3 (users, posts, comments)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nThis is the ONLY way without FK constraints!")
        print("✅ Still much better than N+1 problem")
        print("\nKey points:")
        print("  • No relationship() needed")
        print("  • No selectinload()/joinedload() available")
        print("  • Direct SQL with IN clauses")
        print("  • Manual Python grouping")
        print("  • Same performance (3 queries)")
        print("-" * 80)


def demonstrate_startup_helper_function(db):
    """Real-world helper function for startups without FK constraints."""
    print("\n" + "=" * 80)
    print("PRACTICAL EXAMPLE: Reusable Helper Function")
    print("=" * 80)

    def get_users_with_posts_and_comments(session, user_ids: list[int]):
        """
        Fetch users with their posts and comments efficiently.
        Works without foreign key constraints.
        """
        # Fetch all data
        users = session.execute(select(User).where(User.id.in_(user_ids))).scalars().all()

        posts = (
            session.execute(select(Post).where(Post.author_id.in_(user_ids))).scalars().all()
        )

        post_ids = [post.id for post in posts]
        comments = (
            session.execute(select(Comment).where(Comment.post_id.in_(post_ids))).scalars().all()
        )

        # Group
        posts_by_user = defaultdict(list)
        for post in posts:
            posts_by_user[post.author_id].append(post)

        comments_by_post = defaultdict(list)
        for comment in comments:
            comments_by_post[comment.post_id].append(comment)

        # Return structured data
        return [
            {
                "user": user,
                "posts": [
                    {"post": post, "comments": comments_by_post[post.id]}
                    for post in posts_by_user[user.id]
                ],
            }
            for user in users
        ]

    with db.get_session() as session:
        print("\nUsing reusable helper function...")
        start_time = time.time()

        # Get first 5 users
        user_ids = list(range(1, 6))
        result = get_users_with_posts_and_comments(session, user_ids)

        print(f"\n✓ Fetched {len(result)} users with posts and comments")
        print("\nData structure (first 2 users):")
        for item in result[:2]:
            user = item["user"]
            posts = item["posts"]
            total_comments = sum(len(p["comments"]) for p in posts)
            print(f"\n  {user.username}:")
            print(f"    - {len(posts)} posts")
            print(f"    - {total_comments} total comments")
            for post_item in posts[:2]:  # Show first 2 posts
                post = post_item["post"]
                comments = post_item["comments"]
                print(f"      • {post.title}: {len(comments)} comments")

        end_time = time.time()

        print("\n" + "-" * 80)
        print("Total queries: 3 (users, posts, comments)")
        print(f"Time taken: {(end_time - start_time)*1000:.2f}ms")
        print("\nBenefits:")
        print("  ✅ Works without FK constraints")
        print("  ✅ Reusable across codebase")
        print("  ✅ Type-safe with proper typing")
        print("  ✅ Easy to test and debug")
        print("  ✅ Full control over queries")
        print("-" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLVING THE N+1 PROBLEM - GOOD EXAMPLES")
    print("=" * 80)
    print("\nThis script demonstrates various solutions to the N+1 problem.")
    print("Watch the SQL queries - you'll see efficient query patterns!")
    print("=" * 80)

    db = setup_data()

    # Basic solutions
    demonstrate_joinedload(db)
    demonstrate_selectinload(db)
    demonstrate_subqueryload(db)
    demonstrate_manual_grouping(db)

    # Advanced scenarios
    demonstrate_multiple_relationships(db)
    demonstrate_nested_relationships(db)
    demonstrate_manual_nested_grouping(db)

    # Without FK constraints
    demonstrate_without_foreign_keys(db)
    demonstrate_startup_helper_function(db)

    print("\n" + "=" * 80)
    print("SUMMARY - RECOMMENDATIONS")
    print("=" * 80)
    print("WITH Foreign Key Constraints:")
    print("  1. ✅ Use selectinload() as default (clean, efficient)")
    print("  2. Use joinedload() for one-to-one relationships")
    print("  3. Chain options for nested relationships")
    print("  4. Load multiple relationships in one query")
    print("\nWITHOUT Foreign Key Constraints:")
    print("  1. ✅ Manual grouping is the ONLY way")
    print("  2. Direct SQL with IN clauses")
    print("  3. Python defaultdict for grouping")
    print("  4. Create reusable helper functions")
    print("  5. Same performance (2-3 queries)")
    print("\nRemember: 2-4 optimized queries >> 100+ lazy queries!")
    print("=" * 80)
