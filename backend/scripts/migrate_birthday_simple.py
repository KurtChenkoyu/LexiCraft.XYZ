#!/usr/bin/env python3
"""
Simple migration script - uses psycopg2 directly.
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    print("\nGet it from Supabase:")
    print("  Settings → Database → Connection string → URI")
    print("\nThen run:")
    print("  export DATABASE_URL='postgresql://...'")
    print("  python3 scripts/migrate_birthday_simple.py")
    sys.exit(1)

print("🔌 Connecting...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    print("✅ Connected!\n")
    
    # Add columns
    for col in ['birth_month', 'birth_day', 'birthday_edit_count']:
        print(f"📝 Adding {col}...")
        if col == 'birthday_edit_count':
            cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} INTEGER DEFAULT 0")
        else:
            cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} INTEGER")
        print(f"✅ {col} added")
    
    # Set defaults
    print("\n📝 Setting defaults...")
    cur.execute("UPDATE users SET birthday_edit_count = 0 WHERE birthday_edit_count IS NULL")
    print(f"✅ Updated {cur.rowcount} rows")
    
    print("\n🎉 Migration complete!")
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

