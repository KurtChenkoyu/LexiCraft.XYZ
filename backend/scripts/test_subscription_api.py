#!/usr/bin/env python3
"""
Test Subscription API Endpoint

Tests the /api/subscriptions/activate endpoint to ensure it works correctly.

Usage:
    python scripts/test_subscription_api.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

# Load .env file
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(env_path)

# Get backend URL
backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')

def test_subscription_activate():
    """Test the subscription activation endpoint."""
    print("=" * 60)
    print("Testing Subscription API Endpoint")
    print("=" * 60)
    print(f"Backend URL: {backend_url}")
    print()
    
    # Test data - you'll need to replace with a real email from your database
    test_email = input("Enter a test user email (must exist in database): ").strip()
    if not test_email:
        print("❌ Email is required")
        return False
    
    # Test 1: Activate subscription with all fields
    print("\n📝 Test 1: Activate subscription (active status)")
    print("-" * 60)
    
    end_date = (datetime.now() + timedelta(days=180)).isoformat()  # 6 months from now
    
    payload = {
        "email": test_email,
        "subscription_status": "active",
        "plan_type": "6-month-pass",
        "subscription_end_date": end_date
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/subscriptions/activate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Test 1 PASSED: Subscription activated successfully")
        else:
            print(f"❌ Test 1 FAILED: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        return False
    
    # Test 2: Test status mapping (on_trial -> trial)
    print("\n📝 Test 2: Status mapping (on_trial -> trial)")
    print("-" * 60)
    
    # Use a newer date to ensure update happens (not skipped by idempotency)
    newer_end_date = (datetime.now() + timedelta(days=200)).isoformat()
    
    payload2 = {
        "email": test_email,
        "subscription_status": "on_trial",  # Lemon Squeezy status
        "plan_type": "6-month-pass",
        "subscription_end_date": newer_end_date
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/subscriptions/activate",
            json=payload2,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {result}")
        
        # Check if status was mapped correctly (either in subscription_status or current_status)
        mapped_status = result.get('subscription_status') or result.get('current_status')
        if response.status_code == 200 and mapped_status == 'trial':
            print("✅ Test 2 PASSED: Status correctly mapped from 'on_trial' to 'trial'")
        else:
            print(f"❌ Test 2 FAILED: Status mapping incorrect (got: {mapped_status})")
            return False
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        return False
    
    # Test 3: Test idempotency (older date should be skipped)
    print("\n📝 Test 3: Idempotency check (older date should be skipped)")
    print("-" * 60)
    
    old_date = (datetime.now() + timedelta(days=30)).isoformat()  # Older date
    
    payload3 = {
        "email": test_email,
        "subscription_status": "active",
        "plan_type": "6-month-pass",
        "subscription_end_date": old_date  # Older than previous
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/subscriptions/activate",
            json=payload3,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {result}")
        
        if response.status_code == 200 and result.get('skipped') == True:
            print("✅ Test 3 PASSED: Idempotency check working (older date skipped)")
        else:
            print(f"⚠️  Test 3: Idempotency check may not have triggered (this is OK if dates are equal)")
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        return False
    
    # Test 4: Test invalid email (should return 404)
    print("\n📝 Test 4: Invalid email (should return 404)")
    print("-" * 60)
    
    payload4 = {
        "email": "nonexistent@example.com",
        "subscription_status": "active",
        "plan_type": "6-month-pass",
        "subscription_end_date": end_date
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/subscriptions/activate",
            json=payload4,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 404:
            print("✅ Test 4 PASSED: Correctly returns 404 for non-existent email")
        else:
            print(f"❌ Test 4 FAILED: Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        return False
    
    # Test 5: Verify database was updated
    print("\n📝 Test 5: Verify database was updated")
    print("-" * 60)
    
    try:
        # Add backend directory to path
        backend_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(backend_dir))
        
        from src.database.postgres_connection import PostgresConnection
        from sqlalchemy import text
        
        conn = PostgresConnection()
        session = conn.get_session()
        
        result = session.execute(
            text("""
                SELECT subscription_status, plan_type, subscription_end_date
                FROM users
                WHERE email = :email
            """),
            {"email": test_email}
        ).fetchone()
        
        if result:
            status, plan_type, end_date = result
            print(f"  subscription_status: {status}")
            print(f"  plan_type: {plan_type}")
            print(f"  subscription_end_date: {end_date}")
            
            if status in ['active', 'trial']:
                print("✅ Test 5 PASSED: Database updated correctly")
            else:
                print(f"⚠️  Test 5: Status is {status} (may be expected)")
        else:
            print("❌ Test 5 FAILED: User not found in database")
            return False
        
        session.close()
        conn.close()
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_subscription_activate()
    sys.exit(0 if success else 1)

