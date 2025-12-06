"""
Verify FSRS Setup

Quick script to verify FSRS implementation is correctly set up.

Checks:
1. Database migration applied
2. FSRS library installed
3. Algorithm services importable
4. Database tables exist
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def check_imports():
    """Check if all required modules can be imported."""
    print("Checking imports...")
    
    try:
        from src.spaced_repetition import (
            SM2PlusService,
            FSRSService,
            AssignmentService,
            get_algorithm_for_user,
        )
        print("✅ All spaced repetition modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def check_fsrs_library():
    """Check if FSRS library is installed."""
    print("\nChecking FSRS library...")
    
    try:
        from fsrs import FSRS, Card, Rating
        print("✅ FSRS library installed")
        return True
    except ImportError:
        print("❌ FSRS library not installed")
        print("   Run: pip install fsrs")
        return False


def check_database_tables():
    """Check if required database tables exist."""
    print("\nChecking database tables...")
    
    try:
        from src.database.postgres_connection import PostgresConnection
        from sqlalchemy import text
        
        conn = PostgresConnection()
        db = conn.get_session()
        
        tables_to_check = [
            'verification_schedule',
            'user_algorithm_assignment',
            'fsrs_review_history',
            'word_global_difficulty',
            'algorithm_comparison_metrics',
        ]
        
        all_exist = True
        for table in tables_to_check:
            result = db.execute(
                text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
            )
            exists = result.scalar()
            
            if exists:
                print(f"  ✅ {table} exists")
            else:
                print(f"  ❌ {table} missing")
                all_exist = False
        
        # Check for FSRS columns in verification_schedule
        result = db.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'verification_schedule'
                AND column_name IN ('algorithm_type', 'stability', 'difficulty', 'fsrs_state')
            """)
        )
        columns = [row[0] for row in result.fetchall()]
        
        if len(columns) >= 4:
            print(f"  ✅ verification_schedule has FSRS columns: {', '.join(columns)}")
        else:
            print(f"  ❌ verification_schedule missing FSRS columns")
            print(f"     Found: {columns}")
            print(f"     Expected: algorithm_type, stability, difficulty, fsrs_state")
            all_exist = False
        
        db.close()
        return all_exist
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False


def check_algorithm_services():
    """Check if algorithm services can be instantiated."""
    print("\nChecking algorithm services...")
    
    try:
        from src.spaced_repetition import SM2PlusService, FSRSService
        
        # Test SM-2+ service
        sm2 = SM2PlusService()
        assert sm2.algorithm_type == 'sm2_plus'
        print("  ✅ SM2PlusService works")
        
        # Test FSRS service (may fail if library not installed)
        try:
            fsrs = FSRSService()
            assert fsrs.algorithm_type == 'fsrs'
            print("  ✅ FSRSService works")
        except RuntimeError as e:
            print(f"  ⚠️  FSRSService not available: {e}")
            print("     (This is OK if fsrs library is not installed yet)")
        
        return True
        
    except Exception as e:
        print(f"❌ Service check failed: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("FSRS Setup Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", check_imports()))
    results.append(("FSRS Library", check_fsrs_library()))
    results.append(("Algorithm Services", check_algorithm_services()))
    results.append(("Database Tables", check_database_tables()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All checks passed! FSRS implementation is ready.")
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
        print("\nNext steps:")
        print("1. Run database migration: psql -d your_db -f migrations/011_fsrs_support.sql")
        print("2. Install FSRS library: pip install fsrs")
        print("3. Run this script again to verify")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

