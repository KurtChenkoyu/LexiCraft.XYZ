#!/usr/bin/env python3
"""
Verify that SUPABASE_JWT_SECRET is set correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

def verify_jwt_secret():
    """Verify JWT secret is loaded."""
    print("🔍 Verifying SUPABASE_JWT_SECRET...")
    print("=" * 60)
    
    # Load .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env file from: {env_path}")
    else:
        print(f"⚠️  .env file not found at: {env_path}")
        print("   Trying to load from environment...")
        load_dotenv()
    
    # Check if secret is set
    secret = os.getenv("SUPABASE_JWT_SECRET")
    
    if not secret:
        print("\n❌ SUPABASE_JWT_SECRET is NOT set!")
        print("\n📝 To fix:")
        print("   1. Open backend/.env file")
        print("   2. Add: SUPABASE_JWT_SECRET=your-secret-here")
        print("   3. Get secret from Supabase Dashboard → Settings → API → Legacy JWT Secret")
        return False
    
    # Verify secret looks correct
    print(f"\n✅ SUPABASE_JWT_SECRET is set!")
    print(f"   Length: {len(secret)} characters")
    print(f"   First 20 chars: {secret[:20]}...")
    print(f"   Last 10 chars: ...{secret[-10:]}")
    
    # Check if it's a reasonable length (Supabase secrets are usually 80-200 chars)
    if len(secret) < 32:
        print("\n⚠️  WARNING: Secret seems too short. Make sure you copied the entire secret.")
        return False
    
    if len(secret) > 500:
        print("\n⚠️  WARNING: Secret seems too long. Make sure you didn't copy extra content.")
        return False
    
    print("\n✅ Secret length looks correct!")
    
    # Test if we can import the auth module (without actually using it)
    try:
        # Just check if the module can be imported
        import jwt
        print("✅ PyJWT library is installed")
    except ImportError:
        print("\n❌ PyJWT library is NOT installed!")
        print("   Run: pip install PyJWT>=2.8.0")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All checks passed! JWT secret is configured correctly.")
    print("\n💡 Next steps:")
    print("   1. Restart your backend server")
    print("   2. Test an authenticated API endpoint")
    print("   3. Check logs - you should NOT see warnings about missing JWT secret")
    
    return True

if __name__ == "__main__":
    success = verify_jwt_secret()
    sys.exit(0 if success else 1)

