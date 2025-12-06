#!/usr/bin/env python3
"""
Test Supabase Authentication Flow

This script tests the authentication integration:
1. Verifies Supabase connection
2. Tests user creation via Supabase Auth
3. Verifies user record is created in users table
4. Tests user lookup

Usage:
    python scripts/test_auth_flow.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

load_dotenv()


def get_supabase_client() -> Client:
    """Create Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for admin operations
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
        )
    
    return create_client(supabase_url, supabase_key)


def get_db_session() -> Session:
    """Create database session."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Missing DATABASE_URL in .env")
    
    engine = create_engine(
        database_url,
        poolclass=NullPool,
        connect_args={"sslmode": "require"}
    )
    return Session(engine)


def test_supabase_connection():
    """Test basic Supabase connection."""
    print("🔍 Testing Supabase connection...")
    try:
        client = get_supabase_client()
        # Try to list users (admin operation)
        response = client.auth.admin.list_users()
        print(f"✅ Supabase connection successful! Found {len(response.users)} users.")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


def test_database_connection():
    """Test PostgreSQL database connection."""
    print("\n🔍 Testing PostgreSQL connection...")
    try:
        session = get_db_session()
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"✅ Database connection successful! Found {count} users in database.")
        session.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_user_creation_trigger():
    """Test that user creation trigger works."""
    print("\n🔍 Testing user creation trigger...")
    try:
        client = get_supabase_client()
        session = get_db_session()
        
        # Create a test user via Supabase Auth
        test_email = f"test_{os.urandom(4).hex()}@example.com"
        test_password = "TestPassword123!"
        
        print(f"   Creating test user: {test_email}")
        
        # Create user via Supabase Auth
        auth_response = client.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True  # Auto-confirm for testing
        })
        
        user_id = auth_response.user.id
        print(f"   ✅ User created in auth.users: {user_id}")
        
        # Wait a moment for trigger to execute
        import time
        time.sleep(1)
        
        # Check if user was created in public.users table
        result = session.execute(
            text("SELECT id, email, name FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        user_record = result.fetchone()
        
        if user_record:
            print(f"   ✅ User record created in public.users table!")
            print(f"      ID: {user_record[0]}")
            print(f"      Email: {user_record[1]}")
            print(f"      Name: {user_record[2]}")
            
            # Clean up: Delete test user
            print(f"\n   🧹 Cleaning up test user...")
            client.auth.admin.delete_user(user_id)
            session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            session.commit()
            print(f"   ✅ Test user deleted")
            
            session.close()
            return True
        else:
            print(f"   ❌ User record NOT found in public.users table!")
            print(f"   ⚠️  Trigger may not be working. Check migration 004_supabase_auth_integration.sql")
            
            # Clean up
            client.auth.admin.delete_user(user_id)
            session.close()
            return False
            
    except Exception as e:
        print(f"❌ User creation trigger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Supabase Authentication Flow Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Supabase connection
    results.append(("Supabase Connection", test_supabase_connection()))
    
    # Test 2: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 3: User creation trigger
    results.append(("User Creation Trigger", test_user_creation_trigger()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Authentication setup is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

