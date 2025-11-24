"""Sample data generation utilities."""

from sqlalchemy.orm import Session

from ..models import Application, ApplicationStatus, Campaign, Comment, Post, User


def create_sample_users(session: Session, count: int = 10) -> list[User]:
    """
    Create sample users.

    Args:
        session: SQLAlchemy session
        count: Number of users to create

    Returns:
        List of created User instances
    """
    users = []
    for i in range(1, count + 1):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            is_active=True,
        )
        users.append(user)

    session.add_all(users)
    session.commit()
    print(f"✓ Created {count} sample users")
    return users


def create_sample_posts(session: Session, users: list[User], posts_per_user: int = 5) -> list[Post]:
    """
    Create sample posts for given users.

    Args:
        session: SQLAlchemy session
        users: List of User instances
        posts_per_user: Number of posts per user

    Returns:
        List of created Post instances
    """
    posts = []
    post_id = 1

    for user in users:
        for i in range(1, posts_per_user + 1):
            post = Post(
                title=f"Post {post_id}: {user.username}'s article {i}",
                content=f"This is the content of post {post_id} by {user.username}. "
                f"Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                author_id=user.id,
                is_published=i % 2 == 0,  # Publish every other post
                view_count=i * 10,
            )
            posts.append(post)
            post_id += 1

    session.add_all(posts)
    session.commit()
    print(f"✓ Created {len(posts)} sample posts")
    return posts


def create_sample_comments(
    session: Session, posts: list[Post], users: list[User], comments_per_post: int = 3
) -> list[Comment]:
    """
    Create sample comments for given posts.

    Args:
        session: SQLAlchemy session
        posts: List of Post instances
        users: List of User instances
        comments_per_post: Number of comments per post

    Returns:
        List of created Comment instances
    """
    comments = []
    comment_id = 1

    for post in posts:
        for i in range(comments_per_post):
            # Round-robin assignment of users to comments
            user = users[i % len(users)]
            comment = Comment(
                content=f"Comment {comment_id}: This is a comment by {user.username} on post '{post.title}'",
                author_id=user.id,
                post_id=post.id,
            )
            comments.append(comment)
            comment_id += 1

    session.add_all(comments)
    session.commit()
    print(f"✓ Created {len(comments)} sample comments")
    return comments


def create_sample_campaigns(session: Session, count: int = 5) -> list[Campaign]:
    """
    Create sample campaigns.

    Args:
        session: SQLAlchemy session
        count: Number of campaigns to create

    Returns:
        List of created Campaign instances
    """
    campaigns = []
    for i in range(1, count + 1):
        campaign = Campaign(
            title=f"Campaign {i}: Marketing Initiative",
            description=f"This is campaign {i} for product promotion. "
            f"Join us to get exclusive rewards and benefits!",
            is_active=i % 3 != 0,  # Make some inactive
            max_participants=i * 10 if i % 2 == 0 else None,
        )
        campaigns.append(campaign)

    session.add_all(campaigns)
    session.commit()
    print(f"✓ Created {count} sample campaigns")
    return campaigns


def create_sample_applications(
    session: Session,
    users: list[User],
    campaigns: list[Campaign],
    applications_per_campaign: int = 3,
) -> list[Application]:
    """
    Create sample applications for campaigns.

    Args:
        session: SQLAlchemy session
        users: List of User instances
        campaigns: List of Campaign instances
        applications_per_campaign: Number of applications per campaign

    Returns:
        List of created Application instances
    """
    applications = []
    application_id = 1

    statuses = [
        ApplicationStatus.PENDING,
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    ]

    for campaign in campaigns:
        for i in range(applications_per_campaign):
            user = users[i % len(users)]
            status = statuses[i % len(statuses)]

            application = Application(
                user_id=user.id,
                campaign_id=campaign.id,
                status=status,
                message=f"Application {application_id}: I would like to participate in this campaign!",
                admin_note=(
                    f"Admin note for application {application_id}"
                    if status != ApplicationStatus.PENDING
                    else None
                ),
            )
            applications.append(application)
            application_id += 1

    session.add_all(applications)
    session.commit()
    print(f"✓ Created {len(applications)} sample applications")
    return applications


def create_all_sample_data(
    session: Session,
    user_count: int = 10,
    posts_per_user: int = 5,
    comments_per_post: int = 3,
    campaign_count: int = 5,
    applications_per_campaign: int = 3,
) -> tuple[list[User], list[Post], list[Comment], list[Campaign], list[Application]]:
    """
    Create all sample data at once.

    Args:
        session: SQLAlchemy session
        user_count: Number of users to create
        posts_per_user: Number of posts per user
        comments_per_post: Number of comments per post
        campaign_count: Number of campaigns to create
        applications_per_campaign: Number of applications per campaign

    Returns:
        Tuple of (users, posts, comments, campaigns, applications)
    """
    print("Creating sample data...")
    users = create_sample_users(session, user_count)
    posts = create_sample_posts(session, users, posts_per_user)
    comments = create_sample_comments(session, posts, users, comments_per_post)
    campaigns = create_sample_campaigns(session, campaign_count)
    applications = create_sample_applications(session, users, campaigns, applications_per_campaign)
    print("✓ All sample data created successfully")
    return users, posts, comments, campaigns, applications
