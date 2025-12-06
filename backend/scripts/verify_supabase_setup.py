#!/usr/bin/env python3
"""
Quick Verification Script for Supabase Setup

This script checks if your Supabase environment is configured correctly.
It doesn't create any users or modify data - just checks configuration.

Usage:
    python scripts/verify_supabase_setup.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def check_env_vars():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = {
        "Frontend": [
            "NEXT_PUBLIC_SUPABASE_URL",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        ],
        "Backend": [
            "DATABASE_URL",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
        ],
    }
    
    all_present = True
    
    for category, vars_list in required_vars.items():
        print(f"\n  {category}:")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "KEY" in var or "PASSWORD" in var or "SECRET" in var:
                    masked = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
                    print(f"    ✅ {var}: {masked}")
                else:
                    print(f"    ✅ {var}: {value}")
            else:
                print(f"    ❌ {var}: NOT SET")
                all_present = False
    
    return all_present


def check_database_url_format():
    """Check if DATABASE_URL is in correct format."""
    print("\n🔍 Checking DATABASE_URL format...")
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("    ❌ DATABASE_URL not set")
        return False
    
    if db_url.startswith("postgresql://"):
        print("    ✅ DATABASE_URL format looks correct (postgresql://)")
        
        # Check for password placeholder
        if "[YOUR-PASSWORD]" in db_url or "YOUR_PASSWORD" in db_url:
            print("    ⚠️  WARNING: DATABASE_URL contains password placeholder!")
            print("       Replace [YOUR-PASSWORD] with your actual database password")
            return False
        
        return True
    else:
        print(f"    ⚠️  DATABASE_URL doesn't start with postgresql://")
        print(f"       Current format: {db_url[:30]}...")
        return False


def check_supabase_url_format():
    """Check if Supabase URLs are in correct format."""
    print("\n🔍 Checking Supabase URL formats...")
    
    frontend_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    backend_url = os.getenv("SUPABASE_URL")
    
    all_good = True
    
    if frontend_url:
        if frontend_url.startswith("https://") and ".supabase.co" in frontend_url:
            print(f"    ✅ NEXT_PUBLIC_SUPABASE_URL format correct")
        else:
            print(f"    ⚠️  NEXT_PUBLIC_SUPABASE_URL format may be incorrect")
            print(f"       Should be: https://xxxxx.supabase.co")
            all_good = False
    else:
        all_good = False
    
    if backend_url:
        if backend_url.startswith("https://") and ".supabase.co" in backend_url:
            print(f"    ✅ SUPABASE_URL format correct")
        else:
            print(f"    ⚠️  SUPABASE_URL format may be incorrect")
            all_good = False
    else:
        all_good = False
    
    # Check if they match
    if frontend_url and backend_url and frontend_url != backend_url:
        print(f"    ⚠️  WARNING: Frontend and backend Supabase URLs don't match!")
        print(f"       Frontend: {frontend_url}")
        print(f"       Backend:  {backend_url}")
        print(f"       They should point to the same Supabase project")
    
    return all_good


def check_key_format():
    """Check if Supabase keys look like JWT tokens."""
    print("\n🔍 Checking Supabase key formats...")
    
    anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    all_good = True
    
    if anon_key:
        if anon_key.startswith("eyJ") and len(anon_key) > 100:
            print(f"    ✅ NEXT_PUBLIC_SUPABASE_ANON_KEY format looks correct (JWT)")
        else:
            print(f"    ⚠️  NEXT_PUBLIC_SUPABASE_ANON_KEY format may be incorrect")
            print(f"       Should be a JWT token starting with 'eyJ'")
            all_good = False
    else:
        all_good = False
    
    if service_key:
        if service_key.startswith("eyJ") and len(service_key) > 100:
            print(f"    ✅ SUPABASE_SERVICE_ROLE_KEY format looks correct (JWT)")
        else:
            print(f"    ⚠️  SUPABASE_SERVICE_ROLE_KEY format may be incorrect")
            all_good = False
    else:
        all_good = False
    
    return all_good


def main():
    """Run all checks."""
    print("=" * 60)
    print("Supabase Setup Verification")
    print("=" * 60)
    print("\nThis script checks your configuration without connecting to Supabase.")
    print("For full testing, run: python scripts/test_auth_flow.py\n")
    
    results = []
    
    # Check 1: Environment variables
    results.append(("Environment Variables", check_env_vars()))
    
    # Check 2: Database URL format
    results.append(("Database URL Format", check_database_url_format()))
    
    # Check 3: Supabase URL format
    results.append(("Supabase URL Format", check_supabase_url_format()))
    
    # Check 4: Key format
    results.append(("Supabase Key Format", check_key_format()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All configuration checks passed!")
        print("   Next step: Run 'python scripts/test_auth_flow.py' to test connections")
        return 0
    else:
        print("\n⚠️  Some configuration checks failed.")
        print("   Please fix the issues above before proceeding.")
        print("\n   See SUPABASE_SETUP_COMPLETE_GUIDE.md for detailed setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

