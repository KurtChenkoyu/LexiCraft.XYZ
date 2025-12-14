#!/usr/bin/env python3
"""
Migration script to add birthday fields to users table.
Run this directly to avoid Supabase SQL Editor timeout.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL environment variable not set")
    print("\nUsage:")
    print("  export DATABASE_URL='postgresql://...'")
    print("  python scripts/migrate_birthday_fields.py")
    print("\nOr from Supabase dashboard:")
    print("  Settings → Database → Connection string → URI")
    sys.exit(1)

print("🔌 Connecting to database...")
try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("✅ Connected!")
        
        # Add columns one by one (safer)
        print("\n📝 Adding birth_month column...")
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS birth_month INTEGER
        """))
        conn.commit()
        print("✅ birth_month added")
        
        print("\n📝 Adding birth_day column...")
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS birth_day INTEGER
        """))
        conn.commit()
        print("✅ birth_day added")
        
        print("\n📝 Adding birthday_edit_count column...")
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS birthday_edit_count INTEGER DEFAULT 0
        """))
        conn.commit()
        print("✅ birthday_edit_count added")
        
        # Set default for existing rows
        print("\n📝 Setting default values for existing rows...")
        result = conn.execute(text("""
            UPDATE users 
            SET birthday_edit_count = 0 
            WHERE birthday_edit_count IS NULL
        """))
        conn.commit()
        print(f"✅ Updated {result.rowcount} rows")
        
        # Add constraints
        print("\n📝 Adding constraints...")
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD CONSTRAINT check_birth_month 
                CHECK (birth_month IS NULL OR (birth_month >= 1 AND birth_month <= 12))
            """))
            conn.commit()
            print("✅ birth_month constraint added")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("⚠️  birth_month constraint already exists")
            else:
                raise
        
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD CONSTRAINT check_birth_day 
                CHECK (birth_day IS NULL OR (birth_day >= 1 AND birth_day <= 31))
            """))
            conn.commit()
            print("✅ birth_day constraint added")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("⚠️  birth_day constraint already exists")
            else:
                raise
        
        print("\n🎉 Migration completed successfully!")
        
except OperationalError as e:
    print(f"❌ Connection error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

