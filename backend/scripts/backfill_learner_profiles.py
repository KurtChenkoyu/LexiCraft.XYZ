#!/usr/bin/env python3
"""
Backfill Learner Profiles for Existing Children

This script creates Learner profiles for existing children that don't have them.
Run this after migrating to the new multi-profile system.

Usage:
    python scripts/backfill_learner_profiles.py [user_email]
    
If user_email is not provided, it will backfill for all parents.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from uuid import UUID
from database.postgres_connection import get_db_session
from database.postgres_crud import users as user_crud
from database.postgres_crud.users import get_user_by_email, get_user_children

def backfill_for_user(session: Session, user_id: UUID) -> int:
    """Backfill learner profiles for a specific user."""
    try:
        count = user_crud.backfill_learner_profiles_for_children(session, user_id)
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        raise

def backfill_all_parents(session: Session) -> dict:
    """Backfill learner profiles for all parents."""
    from sqlalchemy import text
    
    # Get all users with parent role
    result = session.execute(
        text("""
            SELECT DISTINCT u.id, u.email, u.name
            FROM public.users u
            JOIN public.user_roles ur ON u.id = ur.user_id
            WHERE ur.role = 'parent'
        """)
    )
    
    parents = result.fetchall()
    results = {}
    
    for parent_id, email, name in parents:
        try:
            count = backfill_for_user(session, parent_id)
            results[email] = {
                'name': name,
                'created_count': count,
                'status': 'success'
            }
            print(f"✅ {email} ({name}): Created {count} learner profile(s)")
        except Exception as e:
            results[email] = {
                'name': name,
                'created_count': 0,
                'status': 'error',
                'error': str(e)
            }
            print(f"❌ {email} ({name}): Error - {e}")
    
    return results

def main():
    if len(sys.argv) > 1:
        # Backfill for specific user
        user_email = sys.argv[1]
        
        with get_db_session() as db:
            user = get_user_by_email(db, user_email)
            if not user:
                print(f"❌ User not found: {user_email}")
                sys.exit(1)
            
            # Check if user is a parent
            if not user_crud.user_has_role(db, user.id, 'parent'):
                print(f"❌ User {user_email} is not a parent")
                sys.exit(1)
            
            # Check if user has children
            children = get_user_children(db, user.id)
            if not children:
                print(f"ℹ️  User {user_email} has no children to backfill")
                sys.exit(0)
            
            print(f"📦 Backfilling learner profiles for {user_email}...")
            print(f"   Found {len(children)} child(ren)")
            
            count = backfill_for_user(db, user.id)
            
            print(f"✅ Created {count} learner profile(s) for {user_email}")
    else:
        # Backfill for all parents
        print("📦 Backfilling learner profiles for all parents...")
        
        with get_db_session() as db:
            results = backfill_all_parents(db)
            
            total_created = sum(r['created_count'] for r in results.values())
            total_parents = len(results)
            successful = sum(1 for r in results.values() if r['status'] == 'success')
            
            print(f"\n📊 Summary:")
            print(f"   Total parents: {total_parents}")
            print(f"   Successful: {successful}")
            print(f"   Total profiles created: {total_created}")

if __name__ == "__main__":
    main()

