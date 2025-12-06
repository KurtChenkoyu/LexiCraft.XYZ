"""
Test script to diagnose authentication issues.
"""
import os
import sys
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

def test_token_decode(token: str):
    """Test decoding a JWT token."""
    print(f"\n{'='*60}")
    print("Testing JWT Token Decoding")
    print(f"{'='*60}")
    
    if not SUPABASE_JWT_SECRET:
        print("❌ SUPABASE_JWT_SECRET not set!")
        return
    
    print(f"✅ JWT Secret is set (length: {len(SUPABASE_JWT_SECRET)})")
    
    try:
        # Decode with verification
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_signature": True}
        )
        
        print("✅ Token verified successfully!")
        print(f"\nToken payload:")
        print(f"  - sub (user_id): {payload.get('sub')}")
        print(f"  - email: {payload.get('email')}")
        print(f"  - exp: {payload.get('exp')}")
        print(f"  - iat: {payload.get('iat')}")
        print(f"  - aud: {payload.get('aud')}")
        print(f"  - role: {payload.get('role')}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        print("❌ Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_auth.py <jwt_token>")
        print("\nTo get your token:")
        print("1. Open browser console on your app")
        print("2. Run: await supabase.auth.getSession()")
        print("3. Copy the access_token value")
        sys.exit(1)
    
    token = sys.argv[1]
    test_token_decode(token)

