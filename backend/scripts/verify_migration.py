#!/usr/bin/env python3
"""
Verify Migration Script
Checks that the unified user model migration was applied correctly.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.postgres_connection import PostgresConnection


def check_table_exists(session, table_name):
    """Check if a table exists."""
    result = session.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """),
        {"table_name": table_name}
    )
    return result.scalar()


def check_column_exists(session, table_name, column_name):
    """Check if a column exists in a table."""
    result = session.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND column_name = :column_name
            )
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.scalar()


def check_trigger_exists(session, trigger_name):
    """Check if a trigger exists."""
    result = session.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.triggers 
                WHERE trigger_name = :trigger_name
            )
        """),
        {"trigger_name": trigger_name}
    )
    return result.scalar()


def check_function_exists(session, function_name):
    """Check if a function exists."""
    result = session.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.routines 
                WHERE routine_name = :function_name
                AND routine_type = 'FUNCTION'
            )
        """),
        {"function_name": function_name}
    )
    return result.scalar()


def verify_migration():
    """Verify that migration 007 and 008 were applied correctly."""
    print("🔍 Verifying Unified User Model Migration...")
    print("=" * 60)
    
    conn = PostgresConnection()
    session = conn.get_session()
    
    errors = []
    warnings = []
    
    # Check tables
    print("\n📊 Checking Tables...")
    required_tables = [
        'users',
        'user_roles',
        'user_relationships',
        'learning_progress',
        'points_accounts',
        'points_transactions',
        'withdrawal_requests',
        'relationship_discoveries'
    ]
    
    for table in required_tables:
        exists = check_table_exists(session, table)
        if exists:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - MISSING")
            errors.append(f"Table {table} does not exist")
    
    # Check users table columns
    print("\n📋 Checking Users Table Columns...")
    required_columns = [
        ('users', 'id'),
        ('users', 'email'),
        ('users', 'name'),
        ('users', 'age'),
        ('users', 'country'),
        ('users', 'email_confirmed'),
        ('users', 'created_at'),
        ('users', 'updated_at')
    ]
    
    for table, column in required_columns:
        exists = check_column_exists(session, table, column)
        if exists:
            print(f"  ✅ {table}.{column}")
        else:
            print(f"  ❌ {table}.{column} - MISSING")
            errors.append(f"Column {table}.{column} does not exist")
    
    # Check user_relationships table columns
    print("\n🔗 Checking User Relationships Table...")
    relationship_columns = [
        ('user_relationships', 'from_user_id'),
        ('user_relationships', 'to_user_id'),
        ('user_relationships', 'relationship_type'),
        ('user_relationships', 'status'),
        ('user_relationships', 'permissions'),
        ('user_relationships', 'metadata')
    ]
    
    for table, column in relationship_columns:
        exists = check_column_exists(session, table, column)
        if exists:
            print(f"  ✅ {table}.{column}")
        else:
            print(f"  ❌ {table}.{column} - MISSING")
            errors.append(f"Column {table}.{column} does not exist")
    
    # Check that old tables are gone
    print("\n🗑️  Checking Old Tables Are Removed...")
    old_tables = ['children']
    for table in old_tables:
        exists = check_table_exists(session, table)
        if not exists:
            print(f"  ✅ {table} - Removed (good)")
        else:
            print(f"  ⚠️  {table} - Still exists (should be removed)")
            warnings.append(f"Old table {table} still exists")
    
    # Check triggers
    print("\n⚙️  Checking Triggers...")
    required_triggers = ['on_auth_user_created']
    for trigger in required_triggers:
        exists = check_trigger_exists(session, trigger)
        if exists:
            print(f"  ✅ {trigger}")
        else:
            print(f"  ❌ {trigger} - MISSING")
            errors.append(f"Trigger {trigger} does not exist")
    
    # Check functions
    print("\n🔧 Checking Functions...")
    required_functions = [
        'handle_new_user',
        'is_parent_of',
        'get_user_roles'
    ]
    for func in required_functions:
        exists = check_function_exists(session, func)
        if exists:
            print(f"  ✅ {func}()")
        else:
            print(f"  ❌ {func}() - MISSING")
            errors.append(f"Function {func} does not exist")
    
    # Check indexes
    print("\n📇 Checking Indexes...")
    # This is a simplified check - you could make it more comprehensive
    result = session.execute(
        text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'users' 
            AND indexname LIKE 'idx_users%'
        """)
    )
    indexes = [row[0] for row in result.fetchall()]
    if indexes:
        print(f"  ✅ Found {len(indexes)} user indexes")
    else:
        warnings.append("No user indexes found")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ Errors Found: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
        print("\n⚠️  Migration verification FAILED")
        print("Please run migrations 007 and 008 in Supabase SQL Editor")
        return False
    else:
        print("\n✅ No errors found!")
    
    if warnings:
        print(f"\n⚠️  Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors:
        print("\n🎉 Migration verification PASSED!")
        print("Your database is ready for the unified user model.")
        return True
    
    session.close()
    return False


if __name__ == "__main__":
    try:
        success = verify_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

