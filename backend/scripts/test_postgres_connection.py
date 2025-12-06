"""
Test script for PostgreSQL connection and basic operations.

Usage:
    python scripts/test_postgres_connection.py
"""
import os
import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.postgres_connection import PostgresConnection
from src.database.models import Base
from src.database.postgres_crud import (
    create_user,
    get_user_by_email,
    create_child,
    get_children_by_parent,
    create_learning_progress,
    get_learning_progress_by_child,
    create_points_account,
    get_points_account_by_child,
    create_points_transaction,
    get_points_transactions_by_child,
    create_verification_schedule,
    get_upcoming_verifications,
    create_withdrawal_request,
    get_withdrawal_requests_by_child,
    create_relationship_discovery,
    get_relationship_discoveries_by_child,
)


def test_connection():
    """Test database connection."""
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    
    try:
        conn = PostgresConnection()
        if conn.verify_connectivity():
            print("✅ Connection successful!")
            return conn
        else:
            print("❌ Connection verification failed")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None


def test_create_tables(conn: PostgresConnection):
    """Create all tables."""
    print("\n" + "=" * 60)
    print("Creating Tables")
    print("=" * 60)
    
    try:
        Base.metadata.create_all(conn.engine)
        print("✅ All tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def test_user_crud(conn: PostgresConnection):
    """Test user CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing User CRUD")
    print("=" * 60)
    
    session = conn.get_session()
    
    try:
        # Create user
        user = create_user(
            session,
            email="test@example.com",
            password_hash="hashed_password_123",
            name="Test Parent",
            phone="+886912345678",
            country="TW"
        )
        print(f"✅ Created user: {user.id} - {user.email}")
        
        # Get user by email
        found_user = get_user_by_email(session, "test@example.com")
        if found_user and found_user.id == user.id:
            print(f"✅ Retrieved user by email: {found_user.email}")
        else:
            print("❌ Failed to retrieve user by email")
        
        return user
    except Exception as e:
        print(f"❌ User CRUD error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def test_child_crud(conn: PostgresConnection, parent_id):
    """Test child CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing Child CRUD")
    print("=" * 60)
    
    session = conn.get_session()
    
    try:
        # Create child
        child = create_child(
            session,
            parent_id=parent_id,
            name="Test Child",
            age=10
        )
        print(f"✅ Created child: {child.id} - {child.name}")
        
        # Get children by parent
        children = get_children_by_parent(session, parent_id)
        if len(children) > 0:
            print(f"✅ Retrieved {len(children)} child(ren) for parent")
        else:
            print("❌ Failed to retrieve children")
        
        return child
    except Exception as e:
        print(f"❌ Child CRUD error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def test_learning_progress_crud(conn: PostgresConnection, child_id):
    """Test learning progress CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing Learning Progress CRUD")
    print("=" * 60)
    
    session = conn.get_session()
    
    try:
        # Create learning progress
        progress = create_learning_progress(
            session,
            child_id=child_id,
            learning_point_id="test_word_123",
            tier=1,
            status="learning"
        )
        print(f"✅ Created learning progress: {progress.id} - {progress.learning_point_id}")
        
        # Get learning progress by child
        progress_list = get_learning_progress_by_child(session, child_id)
        if len(progress_list) > 0:
            print(f"✅ Retrieved {len(progress_list)} learning progress entry(ies)")
        else:
            print("❌ Failed to retrieve learning progress")
        
        return progress
    except Exception as e:
        print(f"❌ Learning progress CRUD error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def test_points_crud(conn: PostgresConnection, child_id):
    """Test points CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing Points CRUD")
    print("=" * 60)
    
    session = conn.get_session()
    
    try:
        # Create points account
        account = create_points_account(session, child_id)
        print(f"✅ Created points account: {account.id} - Available: {account.available_points}")
        
        # Create points transaction
        transaction = create_points_transaction(
            session,
            child_id=child_id,
            transaction_type="earned",
            points=100,
            tier=1,
            description="Test earning"
        )
        print(f"✅ Created points transaction: {transaction.id} - {transaction.points} points")
        
        # Get transactions
        transactions = get_points_transactions_by_child(session, child_id)
        if len(transactions) > 0:
            print(f"✅ Retrieved {len(transactions)} transaction(s)")
        else:
            print("❌ Failed to retrieve transactions")
        
        return account
    except Exception as e:
        print(f"❌ Points CRUD error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def test_verification_crud(conn: PostgresConnection, child_id, learning_progress_id):
    """Test verification schedule CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing Verification Schedule CRUD")
    print("=" * 60)
    
    session = conn.get_session()
    
    try:
        # Create verification schedule
        schedule = create_verification_schedule(
            session,
            child_id=child_id,
            learning_progress_id=learning_progress_id,
            test_day=1,
            scheduled_date=date.today()
        )
        print(f"✅ Created verification schedule: {schedule.id} - Day {schedule.test_day}")
        
        # Get upcoming verifications
        upcoming = get_upcoming_verifications(session, child_id)
        if len(upcoming) > 0:
            print(f"✅ Retrieved {len(upcoming)} upcoming verification(s)")
        else:
            print("❌ Failed to retrieve upcoming verifications")
        
        return schedule
    except Exception as e:
        print(f"❌ Verification CRUD error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def test_withdrawal_crud(conn: PostgresConnection, child_id, parent_id):
    """Test withdrawal request CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing Withdrawal Request CRUD")
    print("=" * 60)
    
    session = conn.get_session()
    
    try:
        # Create withdrawal request
        request = create_withdrawal_request(
            session,
            child_id=child_id,
            parent_id=parent_id,
            amount_ntd=Decimal("100.00"),
            points_amount=100,
            bank_account="1234567890"
        )
        print(f"✅ Created withdrawal request: {request.id} - {request.amount_ntd} NTD")
        
        # Get withdrawal requests
        requests = get_withdrawal_requests_by_child(session, child_id)
        if len(requests) > 0:
            print(f"✅ Retrieved {len(requests)} withdrawal request(s)")
        else:
            print("❌ Failed to retrieve withdrawal requests")
        
        return request
    except Exception as e:
        print(f"❌ Withdrawal CRUD error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def test_relationship_discovery_crud(conn: PostgresConnection, child_id):
    """Test relationship discovery CRUD operations."""
    print("\n" + "=" * 60)
    print("Testing Relationship Discovery CRUD")
    print("=" * 60)
    
    session = conn.get_session()
    
    try:
        # Create relationship discovery
        discovery = create_relationship_discovery(
            session,
            child_id=child_id,
            source_learning_point_id="test_word_123",
            target_learning_point_id="test_word_456",
            relationship_type="COLLOCATES_WITH",
            bonus_awarded=False
        )
        print(f"✅ Created relationship discovery: {discovery.id} - {discovery.relationship_type}")
        
        # Get relationship discoveries
        discoveries = get_relationship_discoveries_by_child(session, child_id)
        if len(discoveries) > 0:
            print(f"✅ Retrieved {len(discoveries)} relationship discovery(ies)")
        else:
            print("❌ Failed to retrieve relationship discoveries")
        
        return discovery
    except Exception as e:
        print(f"❌ Relationship discovery CRUD error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PostgreSQL Database Test Suite")
    print("=" * 60)
    
    # Test connection
    conn = test_connection()
    if not conn:
        print("\n❌ Cannot proceed without database connection")
        return
    
    # Create tables
    if not test_create_tables(conn):
        print("\n❌ Cannot proceed without tables")
        return
    
    # Test CRUD operations
    user = test_user_crud(conn)
    if not user:
        print("\n❌ User CRUD failed, skipping remaining tests")
        return
    
    child = test_child_crud(conn, user.id)
    if not child:
        print("\n❌ Child CRUD failed, skipping remaining tests")
        return
    
    progress = test_learning_progress_crud(conn, child.id)
    if not progress:
        print("\n⚠️  Learning progress CRUD failed, continuing...")
    
    account = test_points_crud(conn, child.id)
    if not account:
        print("\n⚠️  Points CRUD failed, continuing...")
    
    if progress:
        schedule = test_verification_crud(conn, child.id, progress.id)
        if not schedule:
            print("\n⚠️  Verification CRUD failed, continuing...")
    
    request = test_withdrawal_crud(conn, child.id, user.id)
    if not request:
        print("\n⚠️  Withdrawal CRUD failed, continuing...")
    
    discovery = test_relationship_discovery_crud(conn, child.id)
    if not discovery:
        print("\n⚠️  Relationship discovery CRUD failed, continuing...")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    
    conn.close()


if __name__ == "__main__":
    main()

