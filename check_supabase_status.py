#!/usr/bin/env python3
"""
Check Current Supabase Integration Status

This script checks what's already configured vs what still needs to be done.
"""

import os
from pathlib import Path

def check_frontend_env():
    """Check if frontend environment variables are set."""
    print("🔍 Checking Frontend Environment Variables...")
    
    env_file = Path("landing-page/.env.local")
    if env_file.exists():
        print("   ✅ .env.local file exists")
        content = env_file.read_text()
        has_url = "NEXT_PUBLIC_SUPABASE_URL" in content
        has_key = "NEXT_PUBLIC_SUPABASE_ANON_KEY" in content
        
        if has_url and has_key:
            print("   ✅ Supabase environment variables found in .env.local")
            return True
        else:
            print("   ⚠️  .env.local exists but missing Supabase variables")
            return False
    else:
        print("   ❌ .env.local file not found")
        return False


def check_backend_env():
    """Check if backend environment variables are set."""
    print("\n🔍 Checking Backend Environment Variables...")
    
    env_file = Path("backend/.env")
    if env_file.exists():
        print("   ✅ .env file exists")
        content = env_file.read_text()
        has_db = "DATABASE_URL" in content
        has_url = "SUPABASE_URL" in content
        has_key = "SUPABASE_SERVICE_ROLE_KEY" in content
        
        if has_db and has_url and has_key:
            print("   ✅ All Supabase environment variables found in .env")
            return True
        else:
            print("   ⚠️  .env exists but missing some Supabase variables")
            missing = []
            if not has_db: missing.append("DATABASE_URL")
            if not has_url: missing.append("SUPABASE_URL")
            if not has_key: missing.append("SUPABASE_SERVICE_ROLE_KEY")
            print(f"      Missing: {', '.join(missing)}")
            return False
    else:
        print("   ❌ .env file not found")
        return False


def check_code_implementation():
    """Check if Supabase code is implemented."""
    print("\n🔍 Checking Code Implementation...")
    
    files_to_check = [
        ("Frontend Client", "landing-page/lib/supabase/client.ts"),
        ("Frontend Server", "landing-page/lib/supabase/server.ts"),
        ("Auth Context", "landing-page/contexts/AuthContext.tsx"),
        ("Login Page", "landing-page/app/[locale]/login/page.tsx"),
        ("Signup Page", "landing-page/app/[locale]/signup/page.tsx"),
        ("Backend Connection", "backend/src/database/postgres_connection.py"),
    ]
    
    all_exist = True
    for name, path in files_to_check:
        if Path(path).exists():
            print(f"   ✅ {name}: {path}")
        else:
            print(f"   ❌ {name}: {path} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_migrations():
    """Check if migrations exist."""
    print("\n🔍 Checking Database Migrations...")
    
    migrations = [
        ("Initial Schema", "backend/migrations/001_initial_schema.sql"),
        ("Auth Integration", "backend/migrations/004_supabase_auth_integration.sql"),
    ]
    
    all_exist = True
    for name, path in migrations:
        if Path(path).exists():
            print(f"   ✅ {name}: {path}")
        else:
            print(f"   ❌ {name}: {path} - NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """Run all checks."""
    print("=" * 60)
    print("Supabase Integration Status Check")
    print("=" * 60)
    print()
    
    results = {
        "Code Implementation": check_code_implementation(),
        "Database Migrations": check_migrations(),
        "Frontend Environment": check_frontend_env(),
        "Backend Environment": check_backend_env(),
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅ COMPLETE" if passed else "❌ NEEDS SETUP"
        print(f"{status}: {check}")
    
    print("\n" + "=" * 60)
    print("What This Means")
    print("=" * 60)
    
    if results["Code Implementation"]:
        print("✅ Code is already implemented - frontend and backend are ready")
    else:
        print("❌ Some code files are missing")
    
    if results["Database Migrations"]:
        print("✅ Migration files exist")
    else:
        print("❌ Migration files missing")
    
    if results["Frontend Environment"]:
        print("✅ Frontend environment variables are configured")
    else:
        print("❌ Frontend needs .env.local with Supabase keys")
        print("   See: SUPABASE_AUTH_SETUP.md or AUTH_SETUP_CHECKLIST.md")
    
    if results["Backend Environment"]:
        print("✅ Backend environment variables are configured")
    else:
        print("❌ Backend needs .env with DATABASE_URL and Supabase keys")
        print("   See: backend/scripts/setup_supabase.md")
    
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    
    if all(results.values()):
        print("🎉 Everything is configured! You can:")
        print("   1. Test authentication: python backend/scripts/test_auth_flow.py")
        print("   2. Test frontend: cd landing-page && npm run dev")
        print("   3. Visit /login or /signup to test auth flow")
    else:
        if not results["Frontend Environment"] or not results["Backend Environment"]:
            print("📝 You need to:")
            print("   1. Create Supabase project (if not done)")
            print("   2. Get API keys from Supabase dashboard")
            print("   3. Add environment variables to .env files")
            print("\n   See: AUTH_SETUP_CHECKLIST.md for quick steps")
            print("   Or: SUPABASE_SETUP_COMPLETE_GUIDE.md for detailed guide")


if __name__ == "__main__":
    main()

