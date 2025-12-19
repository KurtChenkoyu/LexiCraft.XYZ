#!/usr/bin/env python3
"""
Run a SQL migration file directly against the database.

Usage:
    python scripts/run_sql_migration.py migrations/011_fsrs_support.sql
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

# Get migration file from command line or default
if len(sys.argv) > 1:
    migration_file = Path(sys.argv[1])
    if not migration_file.is_absolute():
        migration_file = backend_dir / migration_file
else:
    migration_file = backend_dir / 'migrations' / '011_fsrs_support.sql'

if not migration_file.exists():
    print(f"❌ Migration file not found: {migration_file}")
    sys.exit(1)

print("=" * 60)
print(f"Running Migration: {migration_file.name}")
print("=" * 60)
print(f"Database: {conn_params['database']}@{conn_params['host']}:{conn_params['port']}")
print()

try:
    # Connect and run migration
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Connected to database")
    print(f"📄 Reading migration file: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print("🚀 Executing migration...")
    print("   (This may take a moment...)")
    
    # Execute the SQL
    cursor.execute(sql)
    
    print()
    print("✅ Migration completed successfully!")
    print()
    print("Created/Updated tables:")
    print("  ✓ user_algorithm_assignment")
    print("  ✓ fsrs_review_history")
    print("  ✓ word_global_difficulty")
    print("  ✓ algorithm_comparison_metrics")
    print("  ✓ Updated verification_schedule with FSRS columns")
    
    # Verify table was created
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'user_algorithm_assignment'
        );
    """)
    exists = cursor.fetchone()[0]
    
    if exists:
        print()
        print("✅ Verified: user_algorithm_assignment table exists")
    else:
        print()
        print("⚠️  Warning: Could not verify table creation")
    
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

