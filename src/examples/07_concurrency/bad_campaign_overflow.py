"""
BAD: Campaign application without lock - max_participants can be exceeded!

This demonstrates the critical race condition when applying to campaigns
with participant limits.
"""

import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func, select

from src.config.database import DatabaseConfig
from src.models import Application, ApplicationStatus, Campaign, User
from src.utils.db_init import reset_database


def prepare_campaign_data():
    """Prepare test data with campaign and users."""
    db = DatabaseConfig()
    reset_database(db.engine)

    with db.get_session() as session:
        # Create a campaign with max 10 participants
        campaign = Campaign(
            title="Limited Campaign",
            description="This campaign has a maximum of 10 participants",
            is_active=True,
            max_participants=10,
        )
        session.add(campaign)

        # Create 20 users who will try to apply
        users = [
            User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                is_active=True,
            )
            for i in range(20)
        ]
        session.add_all(users)
        session.commit()

        return campaign.id


def bad_apply_to_campaign_no_lock(campaign_id: int, user_id: int, _worker_id: int):
    """
    BAD: Apply to campaign without lock - RACE CONDITION!

    Multiple users can pass the participant limit check simultaneously.
    """
    db = DatabaseConfig()

    with db.get_session() as session:
        # 1. Read campaign (NO LOCK!)
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            return False

        # 2. Check if campaign is full
        current_count = len(campaign.applications)

        print(f"  User {user_id}: Checked count = {current_count}/{campaign.max_participants}")

        if campaign.max_participants and current_count >= campaign.max_participants:
            print(f"  User {user_id}: Campaign full, cannot apply")
            return False

        # 3. Simulate some processing time (makes race condition more likely)
        time.sleep(0.01)

        # 4. Create application (other users also passed check!)
        application = Application(
            user_id=user_id,
            campaign_id=campaign_id,
            status=ApplicationStatus.PENDING,
            message=f"Application from user {user_id}",
        )
        session.add(application)

        try:
            session.commit()
            print(f"  User {user_id}: ✓ Application created")
            return True
        except Exception as e:
            session.rollback()
            print(f"  User {user_id}: ❌ Failed - {type(e).__name__}")
            return False


def demonstrate_campaign_overflow():
    """Demonstrate campaign overflow due to race condition."""
    print("\n" + "=" * 80)
    print("BAD: Campaign Application Without Lock")
    print("=" * 80)

    campaign_id = prepare_campaign_data()

    print("\nCampaign created:")
    print("  Title: Limited Campaign")
    print("  Max participants: 10")
    print("  Current applications: 0\n")

    print("20 users trying to apply simultaneously...\n")

    # Simulate 20 users applying at the same time
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(bad_apply_to_campaign_no_lock, campaign_id, i + 1, i) for i in range(20)]
        _ = [f.result() for f in futures]  # Wait for all to complete

    # Check final count
    db = DatabaseConfig()
    with db.get_session() as session:
        campaign = session.get(Campaign, campaign_id)
        if campaign:
            actual_count = len(campaign.applications)
            expected_count = 10

            print(f"\n{'=' * 80}")
            print("❌ RACE CONDITION RESULT:")
            print(f"  Expected applications: {expected_count}")
            print(f"  Actual applications: {actual_count}")
            print(f"  Overflow: {actual_count - expected_count} extra applications!")
            print("=" * 80)

            if campaign.max_participants and actual_count > expected_count:
                print("\n❌ PROBLEM:")
                print(f"  Multiple users read count={expected_count-1} simultaneously")
                print(f"  All passed the check (count < {expected_count})")
                print("  All created applications")
                print("  Campaign exceeded max_participants limit!")


def demonstrate_duplicate_application():
    """Demonstrate duplicate application from same user."""
    print("\n" + "=" * 80)
    print("BAD: Duplicate Application Check Without Lock")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    with db.get_session() as session:
        # Create campaign and user
        campaign = Campaign(
            title="Test Campaign",
            description="Test",
            is_active=True,
            max_participants=100,
        )
        user = User(
            username="duplicate_user",
            email="dup@example.com",
            full_name="Duplicate User",
            is_active=True,
        )
        session.add_all([campaign, user])
        session.commit()

        campaign_id = campaign.id
        user_id = user.id

    def apply_check_duplicate_no_lock(attempt: int):
        """Check if already applied, then create - RACE CONDITION!"""
        with db.get_session() as session:
            # Check if user already applied (NO LOCK!)
            existing = session.execute(
                select(Application)
                .where(Application.user_id == user_id)
                .where(Application.campaign_id == campaign_id)
            ).scalar_one_or_none()

            if existing:
                print(f"  Attempt {attempt}: Already applied, skipping")
                return False

            print(f"  Attempt {attempt}: No existing application, creating...")

            # Simulate processing time
            time.sleep(0.01)

            # Create application (multiple attempts might reach here!)
            application = Application(
                user_id=user_id,
                campaign_id=campaign_id,
                status=ApplicationStatus.PENDING,
            )
            session.add(application)

            try:
                session.commit()
                print(f"  Attempt {attempt}: ✓ Created")
                return True
            except Exception as e:
                session.rollback()
                print(f"  Attempt {attempt}: ❌ Failed - {type(e).__name__}")
                return False

    print("\nSame user trying to apply 5 times simultaneously...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(apply_check_duplicate_no_lock, i) for i in range(5)]
        _ = [f.result() for f in futures]  # Wait for all to complete

    # Check how many applications created
    with db.get_session() as session:
        count = session.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user_id)
            .where(Application.campaign_id == campaign_id)
        )

        print(f"\n{'=' * 80}")
        print("❌ DUPLICATE APPLICATION:")
        print("  Expected applications: 1 (per user)")
        print(f"  Actual applications: {count}")
        if count and count > 1:
            print(f"  Duplicates: {count - 1}")
            print("\n❌ PROBLEM:")
            print("  Multiple attempts passed the 'already applied' check")
            print("  All created applications")
            print("  Same user has multiple applications!")
        print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DEMONSTRATING THE PROBLEM: Campaign Application Race Conditions")
    print("=" * 80)
    print("\nThis shows critical bugs in campaign application system.")
    print("See good_campaign_safe.py for the solution!")
    print("=" * 80)

    demonstrate_campaign_overflow()
    demonstrate_duplicate_application()

    print("\n" + "=" * 80)
    print("💡 SOLUTIONS:")
    print("  1. Use SELECT FOR UPDATE to lock campaign before checking")
    print("  2. Add unique constraint (user_id, campaign_id)")
    print("  3. Both together for defense in depth!")
    print("=" * 80)
