#!/usr/bin/env python3
"""
Check what data exists for leaderboards.

This script checks:
1. If leaderboard_entries table exists
2. If learning_progress has data (for words leaderboard)
3. If user_xp or xp_history have data (for XP leaderboard)
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
print("Checking Leaderboard Data")
print("=" * 60)
print(f"Database: {conn_params['database']}@{conn_params['host']}:{conn_params['port']}")
print()

try:
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if leaderboard_entries exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'leaderboard_entries'
        )
    """)
    has_leaderboard_table = cursor.fetchone()[0]
    print(f"✅ leaderboard_entries table: {'EXISTS' if has_leaderboard_table else '❌ MISSING'}")
    
    if has_leaderboard_table:
        cursor.execute("SELECT COUNT(*) FROM leaderboard_entries")
        count = cursor.fetchone()[0]
        print(f"   └─ {count} entries")
    
    # Check learning_progress (for words leaderboard)
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'learning_progress'
        )
    """)
    has_learning_progress = cursor.fetchone()[0]
    print(f"\n✅ learning_progress table: {'EXISTS' if has_learning_progress else '❌ MISSING'}")
    
    if has_learning_progress:
        cursor.execute("SELECT COUNT(*) FROM learning_progress WHERE status = 'verified'")
        verified_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM learning_progress WHERE status = 'verified'")
        user_count = cursor.fetchone()[0]
        print(f"   └─ {verified_count} verified words across {user_count} users")
        
        # Check weekly/monthly
        cursor.execute("""
            SELECT COUNT(*) FROM learning_progress 
            WHERE status = 'verified' 
            AND learned_at >= NOW() - INTERVAL '7 days'
        """)
        weekly = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM learning_progress 
            WHERE status = 'verified' 
            AND learned_at >= NOW() - INTERVAL '30 days'
        """)
        monthly = cursor.fetchone()[0]
        print(f"   └─ Weekly: {weekly} words, Monthly: {monthly} words")
    
    # Check user_xp (for XP leaderboard)
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'user_xp'
        )
    """)
    has_user_xp = cursor.fetchone()[0]
    print(f"\n✅ user_xp table: {'EXISTS' if has_user_xp else '❌ MISSING'}")
    
    if has_user_xp:
        cursor.execute("SELECT COUNT(*) FROM user_xp WHERE total_xp > 0")
        xp_users = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total_xp) FROM user_xp")
        total_xp = cursor.fetchone()[0] or 0
        print(f"   └─ {xp_users} users with XP, Total: {total_xp:,} XP")
    
    # Check xp_history (for weekly/monthly XP)
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'xp_history'
        )
    """)
    has_xp_history = cursor.fetchone()[0]
    print(f"\n✅ xp_history table: {'EXISTS' if has_xp_history else '❌ MISSING'}")
    
    if has_xp_history:
        cursor.execute("SELECT COUNT(*) FROM xp_history")
        history_count = cursor.fetchone()[0]
        cursor.execute("""
            SELECT SUM(xp_amount) FROM xp_history 
            WHERE earned_at >= NOW() - INTERVAL '7 days'
        """)
        weekly_xp = cursor.fetchone()[0] or 0
        cursor.execute("""
            SELECT SUM(xp_amount) FROM xp_history 
            WHERE earned_at >= NOW() - INTERVAL '30 days'
        """)
        monthly_xp = cursor.fetchone()[0] or 0
        print(f"   └─ {history_count} XP records, Weekly: {weekly_xp:,} XP, Monthly: {monthly_xp:,} XP")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if has_leaderboard_table:
        print("✅ Can use leaderboard_entries table (fast)")
    elif has_learning_progress and verified_count > 0:
        print("✅ Can calculate from learning_progress (words leaderboard)")
    elif has_user_xp or has_xp_history:
        print("✅ Can calculate from user_xp/xp_history (XP leaderboard)")
    else:
        print("❌ No data available for leaderboards")
        print("   Run migration 013_gamification_schema.sql to create tables")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

