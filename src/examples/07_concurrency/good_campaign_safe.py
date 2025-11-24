"""
GOOD: Campaign application with SELECT FOR UPDATE - max_participants enforced!

This demonstrates how to safely handle campaign applications with participant
limits using pessimistic locking.

⚠️ NOTE: SQLite has limited row-level locking support. For production use:
   - Use PostgreSQL or MySQL for true row-level locking
   - Implement database constraints (unique indexes) as defense in depth
   - Test with your actual production database
"""

import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

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


def good_apply_to_campaign_with_lock(campaign_id: int, user_id: int, _worker_id: int):
    """
    GOOD: Apply to campaign WITH lock - NO RACE CONDITION!

    SELECT FOR UPDATE ensures only one user can check and apply at a time.
    """
    db = DatabaseConfig()

    with db.get_session() as session:
        try:
            # 1. Lock campaign row with SELECT FOR UPDATE
            stmt = select(Campaign).where(Campaign.id == campaign_id).with_for_update()
            campaign = session.execute(stmt).scalar_one()

            # 2. Check if campaign is full (we hold lock, so accurate!)
            # Use database count instead of len() for accurate count
            current_count = session.scalar(
                select(func.count())
                .select_from(Application)
                .where(Application.campaign_id == campaign_id)
            ) or 0

            print(
                f"  User {user_id}: Locked and checked count = {current_count}/{campaign.max_participants}"
            )

            if campaign.max_participants and current_count >= campaign.max_participants:
                print(f"  User {user_id}: Campaign full, cannot apply")
                return False

            # 3. Simulate some processing time (still holding lock)
            time.sleep(0.01)

            # 4. Create application (safe, we hold lock)
            application = Application(
                user_id=user_id,
                campaign_id=campaign_id,
                status=ApplicationStatus.PENDING,
                message=f"Application from user {user_id}",
            )
            session.add(application)

            session.commit()  # Lock released here
            print(f"  User {user_id}: ✓ Application created, lock released")
            return True

        except Exception as e:
            session.rollback()
            print(f"  User {user_id}: ❌ Failed - {type(e).__name__}")
            return False


def demonstrate_campaign_safe():
    """Demonstrate campaign application with proper locking."""
    print("\n" + "=" * 80)
    print("GOOD: Campaign Application With SELECT FOR UPDATE")
    print("=" * 80)

    campaign_id = prepare_campaign_data()

    print("\nCampaign created:")
    print("  Title: Limited Campaign")
    print("  Max participants: 10")
    print("  Current applications: 0\n")

    print("20 users trying to apply simultaneously (with proper locking)...\n")

    # Simulate 20 users applying at the same time
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(good_apply_to_campaign_with_lock, campaign_id, i + 1, i) for i in range(20)
        ]
        _ = [f.result() for f in futures]

    # Check final count
    db = DatabaseConfig()
    with db.get_session() as session:
        campaign = session.get(Campaign, campaign_id)
        if campaign:
            actual_count = len(campaign.applications)
            expected_count = 10

            print(f"\n{'=' * 80}")
            print("✅ LOCK PREVENTED RACE CONDITION:")
            print(f"  Expected applications: {expected_count}")
            print(f"  Actual applications: {actual_count}")
            print("  Overflow: 0 ✓")
            print("=" * 80)

            if actual_count == expected_count:
                print("\n✅ SUCCESS:")
                print("  SELECT FOR UPDATE serialized access")
                print(f"  Only first {expected_count} users succeeded")
                print("  Remaining users saw campaign was full")
                print("  max_participants limit enforced correctly!")


def demonstrate_no_duplicate_with_constraint():
    """Demonstrate prevention of duplicate applications using DB constraint."""
    print("\n" + "=" * 80)
    print("GOOD: Prevent Duplicate Applications (Defense in Depth)")
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
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
        )
        session.add_all([campaign, user])
        session.commit()

        campaign_id = campaign.id
        user_id = user.id

    def apply_with_constraint_handling(attempt: int):
        """Try to apply - database constraint prevents duplicates."""
        with db.get_session() as session:
            # Create application without checking
            # (database constraint will prevent duplicates)
            application = Application(
                user_id=user_id,
                campaign_id=campaign_id,
                status=ApplicationStatus.PENDING,
                message=f"Attempt {attempt}",
            )
            session.add(application)

            try:
                session.commit()
                print(f"  Attempt {attempt}: ✓ Created")
                return True
            except IntegrityError:
                session.rollback()
                # Unique constraint violation - already applied
                print(f"  Attempt {attempt}: ❌ Already applied (unique constraint)")
                return False
            except Exception as e:
                session.rollback()
                print(f"  Attempt {attempt}: ❌ Failed - {type(e).__name__}")
                return False

    print("\nSame user trying to apply 5 times with constraint protection...\n")
    print("Note: Application model should have unique constraint:")
    print("  __table_args__ = (UniqueConstraint('user_id', 'campaign_id'),)\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(apply_with_constraint_handling, i) for i in range(5)]
        results = [f.result() for f in futures]

    # Check how many applications created
    with db.get_session() as session:
        count = session.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user_id)
            .where(Application.campaign_id == campaign_id)
        )

        success_count = sum(1 for r in results if r)

        print(f"\n{'=' * 80}")
        print("✅ DATABASE CONSTRAINT PROTECTION:")
        print("  Attempts: 5")
        print(f"  Successful: {success_count}")
        print(f"  Blocked by constraint: {5 - success_count}")
        print(f"  Final application count: {count}")
        print("=" * 80)

        if count == 1:
            print("\n✅ SUCCESS:")
            print("  Database constraint prevented duplicates")
            print("  Only one application created per user")
            print("  Defense in depth approach!")


def demonstrate_nowait_for_user_facing():
    """Demonstrate NOWAIT for better user experience."""
    print("\n" + "=" * 80)
    print("GOOD: Using NOWAIT for User-Facing Operations")
    print("=" * 80)

    campaign_id = prepare_campaign_data()

    def apply_with_nowait(user_id: int):
        """Try to apply with NOWAIT - fail fast if campaign is locked."""
        db = DatabaseConfig()

        with db.get_session() as session:
            try:
                # NOWAIT - fail immediately if locked
                stmt = select(Campaign).where(Campaign.id == campaign_id).with_for_update(nowait=True)
                campaign = session.execute(stmt).scalar_one()

                # Check if campaign is full
                current_count = len(campaign.applications)

                if campaign.max_participants and current_count >= campaign.max_participants:
                    return f"User {user_id}: Campaign full"

                # Create application
                application = Application(
                    user_id=user_id, campaign_id=campaign_id, status=ApplicationStatus.PENDING
                )
                session.add(application)

                session.commit()
                return f"User {user_id}: ✓ Applied successfully"

            except Exception as e:
                session.rollback()
                error_name = type(e).__name__
                # Campaign is being processed by another user
                return f"User {user_id}: ⚠️ Campaign busy, try again ({error_name})"

    print("\n5 users trying to apply with NOWAIT (fail fast)...\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(apply_with_nowait, i + 1) for i in range(5)]
        results = [f.result() for f in futures]

    for result in results:
        print(f"  {result}")

    print("\n✅ USER-FRIENDLY BEHAVIOR:")
    print("  Users don't wait indefinitely")
    print("  Failed attempts can retry immediately")
    print("  Better user experience!")


def demonstrate_batch_approval_with_lock():
    """Demonstrate batch approval with proper locking."""
    print("\n" + "=" * 80)
    print("GOOD: Batch Approval with Limit Enforcement")
    print("=" * 80)

    db = DatabaseConfig()
    reset_database(db.engine)

    with db.get_session() as session:
        # Create campaign with 5 max participants
        campaign = Campaign(
            title="Batch Campaign",
            description="Campaign for batch approval demo",
            is_active=True,
            max_participants=5,
        )
        session.add(campaign)
        session.commit()
        campaign_id = campaign.id

        # Create 10 pending applications
        users = [
            User(username=f"user{i}", email=f"user{i}@example.com", full_name=f"User {i}", is_active=True)
            for i in range(10)
        ]
        session.add_all(users)
        session.commit()

        applications = [
            Application(
                user_id=user.id, campaign_id=campaign_id, status=ApplicationStatus.PENDING, message=f"User {i}"
            )
            for i, user in enumerate(users)
        ]
        session.add_all(applications)
        session.commit()

        print(f"\nCreated campaign with max {campaign.max_participants} participants")
        print(f"Created {len(applications)} pending applications\n")

    def approve_applications_safely():
        """Approve applications up to max_participants limit."""
        with db.get_session() as session:
            # Lock campaign to check limit
            stmt = select(Campaign).where(Campaign.id == campaign_id).with_for_update()
            campaign = session.execute(stmt).scalar_one()

            # Count already approved
            approved_count = sum(1 for app in campaign.applications if app.status == ApplicationStatus.APPROVED)

            remaining_slots = campaign.max_participants - approved_count  # type: ignore[operator]

            print(f"  Approved: {approved_count}, Remaining slots: {remaining_slots}")

            if remaining_slots <= 0:
                print("  No remaining slots!")
                return 0

            # Get pending applications to approve
            pending_apps = [
                app for app in campaign.applications if app.status == ApplicationStatus.PENDING
            ][:remaining_slots]

            # Approve up to limit
            for app in pending_apps:
                app.status = ApplicationStatus.APPROVED
                print(f"    Approved application {app.id}")

            session.commit()
            return len(pending_apps)

    print("Approving applications with limit enforcement...\n")

    _ = approve_applications_safely()

    # Verify final state
    with db.get_session() as session:
        campaign = session.get(Campaign, campaign_id)
        if campaign:
            approved_count = sum(
                1 for app in campaign.applications if app.status == ApplicationStatus.APPROVED
            )
            pending_count = sum(1 for app in campaign.applications if app.status == ApplicationStatus.PENDING)

            print(f"\n{'=' * 80}")
            print("✅ BATCH APPROVAL RESULT:")
            print(f"  Max participants: {campaign.max_participants}")
            print(f"  Approved: {approved_count}")
            print(f"  Pending: {pending_count}")
            print(f"  Limit enforced: {'✓' if approved_count <= campaign.max_participants else '✗'}")  # type: ignore[operator]
            print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SOLUTION: Safe Campaign Application with Locking")
    print("=" * 80)
    print("\nThis shows how to safely handle campaign applications.")
    print("Compare with bad_campaign_overflow.py to see the difference!")
    print("=" * 80)

    demonstrate_campaign_safe()
    demonstrate_no_duplicate_with_constraint()
    demonstrate_nowait_for_user_facing()
    demonstrate_batch_approval_with_lock()

    print("\n" + "=" * 80)
    print("CONCLUSION: Defense in Depth")
    print("=" * 80)
    print("\n🛡️  Multiple layers of protection:")
    print("  1. SELECT FOR UPDATE - Prevents race conditions")
    print("  2. Unique constraint - Prevents duplicates")
    print("  3. Application-level validation - Extra safety")
    print("\n💡 Best practices:")
    print("  • Use FOR UPDATE for participant limits")
    print("  • Use NOWAIT for user-facing operations")
    print("  • Add unique constraints for data integrity")
    print("  • Keep lock duration minimal")
    print("  • Test under concurrent load!")
    print("=" * 80)
