#!/usr/bin/env python3
"""
Check the actual database schema for leaderboard-related tables.
This will show us what columns actually exist.
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

# Parse connection string
parsed = urlparse(db_url)
conn_params = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'database': parsed.path.lstrip('/'),
    'user': unquote(parsed.username) if parsed.username else None,
    'password': unquote(parsed.password) if parsed.password else None,
}

print("=" * 60)
print("Checking Leaderboard Database Schema")
print("=" * 60)
print(f"Database: {conn_params['database']}@{conn_params['host']}:{conn_params['port']}")
print()

try:
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # Check learners table
    print("=" * 60)
    print("1. public.learners table")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'learners'
        ORDER BY ordinal_position;
    """)
    learners_cols = cursor.fetchall()
    if learners_cols:
        for col in learners_cols:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  {col[0]:20} {col[1]:20} {nullable}{default}")
        # Check specifically for avatar_emoji
        has_avatar = any(col[0] == 'avatar_emoji' for col in learners_cols)
        print(f"\n  ✅ avatar_emoji exists: {has_avatar}")
    else:
        print("  ❌ Table does not exist")
    
    # Check xp_history table
    print("\n" + "=" * 60)
    print("2. xp_history table")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'xp_history'
        ORDER BY ordinal_position;
    """)
    xp_history_cols = cursor.fetchall()
    if xp_history_cols:
        for col in xp_history_cols:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  {col[0]:20} {col[1]:20} {nullable}{default}")
        # Check specifically for learner_id
        has_learner_id = any(col[0] == 'learner_id' for col in xp_history_cols)
        print(f"\n  ✅ learner_id exists: {has_learner_id}")
        if has_learner_id:
            # Check if it's nullable
            learner_id_col = next((col for col in xp_history_cols if col[0] == 'learner_id'), None)
            if learner_id_col:
                print(f"  📝 learner_id is nullable: {learner_id_col[2] == 'YES'}")
                # Check how many records have learner_id set
                cursor.execute("SELECT COUNT(*) FROM xp_history WHERE learner_id IS NOT NULL")
                with_learner_id = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM xp_history")
                total = cursor.fetchone()[0]
                print(f"  📊 Records with learner_id: {with_learner_id} / {total}")
    else:
        print("  ❌ Table does not exist")
    
    # Check user_xp table
    print("\n" + "=" * 60)
    print("3. user_xp table")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'user_xp'
        ORDER BY ordinal_position;
    """)
    user_xp_cols = cursor.fetchall()
    if user_xp_cols:
        for col in user_xp_cols:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  {col[0]:20} {col[1]:20} {nullable}{default}")
        # Check specifically for learner_id
        has_learner_id = any(col[0] == 'learner_id' for col in user_xp_cols)
        print(f"\n  ✅ learner_id exists: {has_learner_id}")
        if has_learner_id:
            # Check if it's nullable
            learner_id_col = next((col for col in user_xp_cols if col[0] == 'learner_id'), None)
            if learner_id_col:
                print(f"  📝 learner_id is nullable: {learner_id_col[2] == 'YES'}")
                # Check how many records have learner_id set
                cursor.execute("SELECT COUNT(*) FROM user_xp WHERE learner_id IS NOT NULL")
                with_learner_id = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM user_xp")
                total = cursor.fetchone()[0]
                print(f"  📊 Records with learner_id: {with_learner_id} / {total}")
    else:
        print("  ❌ Table does not exist")
    
    # Check learning_progress table for learner_id
    print("\n" + "=" * 60)
    print("4. learning_progress table (learner_id column)")
    print("=" * 60)
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
          AND table_name = 'learning_progress'
          AND column_name = 'learner_id';
    """)
    lp_learner_id = cursor.fetchone()
    if lp_learner_id:
        print(f"  ✅ learner_id exists: {lp_learner_id[0]} ({lp_learner_id[1]}, nullable: {lp_learner_id[2] == 'YES'})")
        cursor.execute("SELECT COUNT(*) FROM learning_progress WHERE learner_id IS NOT NULL")
        with_learner_id = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM learning_progress")
        total = cursor.fetchone()[0]
        print(f"  📊 Records with learner_id: {with_learner_id} / {total}")
    else:
        print("  ❌ learner_id column does not exist in learning_progress")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("This will help us understand what migration state we're in.")
    print("If learner_id columns are missing, we need to run migration Part 1.")
    print("If learner_id columns exist but are NULL, we need to run the backfill script.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

