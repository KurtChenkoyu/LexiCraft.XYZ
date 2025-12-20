#!/usr/bin/env python3
"""
Run Part 1 of XP migration (add learner_id columns).

This adds the columns without making them NOT NULL, allowing the backfill script
to populate them before Part 3 enforces the constraints.

Usage:
    python scripts/run_xp_migration_part1.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse, unquote

# Load .env file
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(env_path)

# Get DATABASE_URL
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

# Parse connection string (handle URL encoding)
parsed = urlparse(db_url)
# Use direct connection port (5432) for DDL operations like CREATE INDEX
# Pooler (6543) doesn't support DDL
port = 5432 if parsed.port == 6543 else (parsed.port or 5432)
conn_params = {
    'host': parsed.hostname,
    'port': port,
    'database': parsed.path.lstrip('/'),
    'user': unquote(parsed.username) if parsed.username else None,
    'password': unquote(parsed.password) if parsed.password else None,
}

print("=" * 60)
print("XP Migration Part 1: Add learner_id Columns")
print("=" * 60)
print(f"Database: {conn_params['database']}@{conn_params['host']}:{conn_params['port']}")
print()

# Part 1 SQL (only the column additions and indexes)
part1_sql = """
-- ============================================
-- PART 1: Add learner_id columns (nullable initially)
-- ============================================

-- Step 1: Add learner_id columns (nullable for now, will be populated by backfill script)
ALTER TABLE user_xp 
ADD COLUMN IF NOT EXISTS learner_id UUID REFERENCES public.learners(id) ON DELETE CASCADE;

ALTER TABLE xp_history 
ADD COLUMN IF NOT EXISTS learner_id UUID REFERENCES public.learners(id) ON DELETE CASCADE;

-- Step 2: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_xp_learner ON user_xp(learner_id);
CREATE INDEX IF NOT EXISTS idx_xp_history_learner ON xp_history(learner_id);
CREATE INDEX IF NOT EXISTS idx_xp_history_learner_date ON xp_history(learner_id, earned_at);
"""

try:
    # Connect and run migration
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Connected to database")
    print("🚀 Executing Part 1 migration...")
    print("   Adding learner_id columns and indexes...")
    
    # Execute the SQL
    cursor.execute(part1_sql)
    
    print()
    print("✅ Part 1 migration completed successfully!")
    print()
    print("Changes applied:")
    print("  ✓ Added learner_id column to user_xp table")
    print("  ✓ Added learner_id column to xp_history table")
    print("  ✓ Created indexes for performance")
    print()
    print("Next steps:")
    print("  1. Run backfill script: python scripts/backfill_xp_to_learners.py")
    print("  2. Run Part 3 migration: python scripts/run_xp_migration_part3.py")
    
    # Verify columns were added
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'user_xp' 
        AND column_name = 'learner_id';
    """)
    exists = cursor.fetchone()
    
    if exists:
        print()
        print("✅ Verified: learner_id column exists in user_xp")
    else:
        print()
        print("⚠️  Warning: Could not verify column creation")
    
    cursor.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ Connection error: {e}")
    print()
    print("💡 Tip: If using Supabase connection pooler (port 6543),")
    print("   try using the direct connection port (5432) instead.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

