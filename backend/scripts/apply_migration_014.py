#!/usr/bin/env python3
"""
Apply migration 014: Backfill learning_progress.learner_id

Usage:
    python3 scripts/apply_migration_014.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / '.env')

# Add parent directory to path
sys.path.insert(0, str(backend_dir))

from src.database.postgres_connection import PostgresConnection

def apply_migration_014():
    """Apply migration 014 to backfill learner_id in learning_progress."""
    migration_file = backend_dir / 'migrations' / '014_backfill_learning_progress_learner_id.sql'
    
    print("=" * 60)
    print("Applying Migration 014: Backfill learning_progress.learner_id")
    print("=" * 60)
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    conn = PostgresConnection()
    session = conn.get_session()
    
    try:
        print("🔌 Connected to database")
        print(f"📄 Reading migration file: {migration_file.name}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print("🚀 Executing migration...")
        print("   (This may take a moment...)")
        
        # Execute the SQL
        session.execute(text(sql))
        session.commit()
        
        print()
        print("✅ Migration applied successfully!")
        
        # Verify: Count remaining orphaned entries
        print()
        print("🔍 Verifying migration...")
        result = session.execute(text("""
            SELECT COUNT(*) FROM public.learning_progress WHERE learner_id IS NULL
        """))
        orphaned_count = result.scalar()
        
        if orphaned_count == 0:
            print(f"✅ Verified: All entries now have learner_id (0 orphaned entries)")
        else:
            print(f"⚠️  Warning: {orphaned_count} entries still have NULL learner_id")
            print("   (These may be for child profiles or need manual review)")
        
        # Count total updated
        result = session.execute(text("""
            SELECT COUNT(*) FROM public.learning_progress WHERE learner_id IS NOT NULL
        """))
        total_with_learner_id = result.scalar()
        print(f"📊 Total entries with learner_id: {total_with_learner_id}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()
        conn.close()

if __name__ == "__main__":
    success = apply_migration_014()
    sys.exit(0 if success else 1)

