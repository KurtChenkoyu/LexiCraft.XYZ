#!/usr/bin/env python3
"""
Seed Test Accounts for Development and QA

Creates standardized test accounts with different user states for testing
various gamification scenarios. All accounts use the same password for easy testing.

Personas:
    - fresh: New user, no progress
    - active: Mid-progress learner, 7-day streak, Level 5
    - power: Power user, Level 15+, many achievements
    - churned: Was active, broken streak (tests re-engagement)
    - edge_levelup: 5 XP away from level up (tests level-up animation)
    - edge_achieve: 1 word away from "100 words" achievement

Usage:
    python scripts/seed_test_accounts.py           # Create/update all test accounts
    python scripts/seed_test_accounts.py --reset   # Delete and recreate all test accounts
    python scripts/seed_test_accounts.py --list    # List existing test accounts
    python scripts/seed_test_accounts.py --delete  # Delete all test accounts

Environment:
    Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
"""

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

# All test accounts use this password
TEST_PASSWORD = os.getenv("TEST_ACCOUNT_PASSWORD", "TestPassword123!")

# Email domain for test accounts
TEST_EMAIL_DOMAIN = "lexicraft.xyz"

# Test account personas
TEST_PERSONAS = {
    "fresh": {
        "name": "Fresh Tester",
        "description": "New user, no progress",
        "xp": 0,
        "level": 1,
        "streak": 0,
        "words_learned": 0,
        "achievements": [],
    },
    "active": {
        "name": "Active Learner",
        "description": "Mid-progress, 7-day streak, Level 5",
        "xp": 1000,
        "level": 5,
        "streak": 7,
        "words_learned": 50,
        "achievements": ["first_word", "week_streak", "vocabulary_10"],
    },
    "power": {
        "name": "Power User",
        "description": "High level, many achievements",
        "xp": 10000,
        "level": 15,
        "streak": 45,
        "words_learned": 500,
        "achievements": [
            "first_word", "week_streak", "month_streak",
            "vocabulary_10", "vocabulary_50", "vocabulary_100",
            "first_mastery", "mastery_10"
        ],
    },
    "churned": {
        "name": "Churned User",
        "description": "Was active, broken streak (no activity in 5 days)",
        "xp": 2500,
        "level": 8,
        "streak": 0,  # Broken
        "last_activity_days_ago": 5,
        "words_learned": 100,
        "achievements": ["first_word", "vocabulary_10", "vocabulary_50"],
    },
    "edge_levelup": {
        "name": "Almost Level Up",
        "description": "5 XP away from Level 6 (tests level-up animation)",
        "xp": 1495,  # Level 6 starts at 1500
        "level": 5,
        "streak": 3,
        "words_learned": 75,
        "achievements": ["first_word", "vocabulary_10", "vocabulary_50"],
    },
    "edge_achieve": {
        "name": "Almost Achievement",
        "description": "99 words learned (1 away from 100-word achievement)",
        "xp": 3000,
        "level": 9,
        "streak": 14,
        "words_learned": 99,
        "achievements": ["first_word", "vocabulary_10", "vocabulary_50"],
    },
}


# ============================================
# DATABASE CONNECTIONS
# ============================================

def get_supabase_client() -> Client:
    """Create Supabase client with admin privileges."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
        )
    
    return create_client(supabase_url, supabase_key)


def get_db_session() -> Session:
    """Create database session."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Missing DATABASE_URL in .env")
    
    engine = create_engine(
        database_url,
        poolclass=NullPool,
        connect_args={"sslmode": "require"}
    )
    return Session(engine)


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_test_email(persona: str) -> str:
    """Generate test email for a persona."""
    return f"test+{persona}@{TEST_EMAIL_DOMAIN}"


def calculate_level_xp_boundaries(level: int) -> tuple:
    """Calculate XP boundaries for a level."""
    # Level N: XP needed = 100 + (N-1) * 50
    total_xp_for_level = 0
    for l in range(1, level):
        total_xp_for_level += 100 + (l - 1) * 50
    xp_needed_for_next = 100 + (level - 1) * 50
    return total_xp_for_level, xp_needed_for_next


def get_auth_users(client: Client) -> list:
    """Get all users from Supabase Auth (handles different API response formats)."""
    response = client.auth.admin.list_users()
    # Handle both old format (object with .users) and new format (list directly)
    if hasattr(response, 'users'):
        return response.users
    elif isinstance(response, list):
        return response
    else:
        return []


def create_auth_user(client: Client, email: str, name: str) -> Optional[str]:
    """Create a user in Supabase Auth. Returns user_id or None if exists."""
    try:
        response = client.auth.admin.create_user({
            "email": email,
            "password": TEST_PASSWORD,
            "email_confirm": True,
            "user_metadata": {"name": name, "is_test_account": True}
        })
        return response.user.id
    except Exception as e:
        if "already registered" in str(e).lower() or "already been registered" in str(e).lower():
            # User exists, get their ID
            users = get_auth_users(client)
            for user in users:
                if user.email == email:
                    return user.id
            return None
        raise


def delete_auth_user(client: Client, email: str) -> bool:
    """Delete a user from Supabase Auth."""
    try:
        users = get_auth_users(client)
        for user in users:
            if user.email == email:
                client.auth.admin.delete_user(user.id)
                return True
        return False
    except Exception as e:
        print(f"  ⚠️  Error deleting auth user: {e}")
        return False


def setup_user_xp(db: Session, user_id: str, xp: int, level: int):
    """Set up user XP record."""
    # Calculate XP in current level
    level_start, xp_needed = calculate_level_xp_boundaries(level)
    xp_in_level = xp - level_start
    
    # Upsert user_xp
    db.execute(
        text("""
            INSERT INTO user_xp (user_id, total_xp, current_level, xp_to_next_level, xp_in_current_level, updated_at)
            VALUES (:user_id, :total_xp, :level, :xp_to_next, :xp_in_level, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                total_xp = :total_xp,
                current_level = :level,
                xp_to_next_level = :xp_to_next,
                xp_in_current_level = :xp_in_level,
                updated_at = NOW()
        """),
        {
            "user_id": user_id,
            "total_xp": xp,
            "level": level,
            "xp_to_next": xp_needed,
            "xp_in_level": xp_in_level
        }
    )


def setup_achievements(db: Session, user_id: str, achievement_codes: List[str]):
    """Set up user achievements."""
    for code in achievement_codes:
        # Get achievement ID
        result = db.execute(
            text("SELECT id FROM achievements WHERE code = :code"),
            {"code": code}
        )
        row = result.fetchone()
        if row:
            achievement_id = row[0]
            # Upsert achievement
            db.execute(
                text("""
                    INSERT INTO user_achievements (user_id, achievement_id, unlocked_at, progress)
                    VALUES (:user_id, :achievement_id, NOW(), 100)
                    ON CONFLICT (user_id, achievement_id) DO UPDATE SET
                        unlocked_at = NOW(),
                        progress = 100
                """),
                {"user_id": user_id, "achievement_id": achievement_id}
            )
        else:
            print(f"    ⚠️  Achievement '{code}' not found in database")


def setup_learning_activity(db: Session, user_id: str, streak_days: int, words_learned: int, last_activity_days_ago: int = 0):
    """Create learning activity history to establish streak."""
    today = date.today()
    
    # Create activity for each streak day
    sample_sense_ids = [
        "be.v.01", "have.v.01", "do.v.01", "say.v.01", "go.v.01",
        "get.v.01", "make.v.01", "know.v.01", "think.v.01", "take.v.01",
        "see.v.01", "come.v.01", "want.v.01", "look.v.01", "use.v.01",
        "find.v.01", "give.v.01", "tell.v.01", "work.v.01", "call.v.01"
    ]
    
    # Calculate start date based on streak and last activity
    if last_activity_days_ago > 0:
        # Churned user - activity ended some days ago
        end_date = today - timedelta(days=last_activity_days_ago)
    else:
        end_date = today
    
    start_date = end_date - timedelta(days=streak_days)
    
    word_idx = 0
    for day_offset in range(streak_days):
        activity_date = start_date + timedelta(days=day_offset)
        
        # Add 2-5 words per day
        words_per_day = min(5, max(2, (words_learned - word_idx) // max(1, streak_days - day_offset)))
        
        for _ in range(words_per_day):
            if word_idx >= len(sample_sense_ids) * 5:
                break
                
            sense_id = sample_sense_ids[word_idx % len(sample_sense_ids)]
            unique_sense_id = f"{sense_id}_{word_idx}"
            
            # Create learning progress
            try:
                db.execute(
                    text("""
                        INSERT INTO learning_progress (user_id, learning_point_id, tier, status, learned_at)
                        VALUES (:user_id, :sense_id, 1, 'verified', :learned_at)
                        ON CONFLICT (user_id, learning_point_id, tier) DO NOTHING
                    """),
                    {
                        "user_id": user_id,
                        "sense_id": unique_sense_id,
                        "learned_at": datetime.combine(activity_date, datetime.min.time())
                    }
                )
            except Exception:
                pass
            
            word_idx += 1
            if word_idx >= words_learned:
                break
        
        if word_idx >= words_learned:
            break


def delete_user_data(db: Session, user_id: str):
    """Delete all user data from database."""
    tables = [
        "xp_history",
        "user_achievements",
        "user_xp",
        "verification_schedule",
        "learning_progress",
        "user_roles",
        "users"
    ]
    
    for table in tables:
        try:
            db.execute(
                text(f"DELETE FROM {table} WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
        except Exception:
            pass  # Table might not exist or have different column name


# ============================================
# MAIN OPERATIONS
# ============================================

def create_test_account(persona: str, config: Dict, client: Client, db: Session, reset: bool = False) -> bool:
    """Create or update a single test account."""
    email = get_test_email(persona)
    print(f"\n📦 {persona}: {config['description']}")
    print(f"   Email: {email}")
    
    try:
        # Delete existing if reset
        if reset:
            print("   🗑️  Deleting existing account...")
            all_users = get_auth_users(client)
            for user in all_users:
                if user.email == email:
                    delete_user_data(db, str(user.id))
                    db.commit()
                    delete_auth_user(client, email)
                    time.sleep(0.5)  # Rate limiting
                    break
        
        # Create auth user
        print(f"   👤 Creating auth user...")
        user_id = create_auth_user(client, email, config["name"])
        
        if not user_id:
            print(f"   ❌ Failed to create auth user")
            return False
        
        print(f"   ✅ User ID: {user_id}")
        
        # Wait for trigger to create user record
        time.sleep(1)
        
        # Ensure user record exists
        db.execute(
            text("""
                INSERT INTO users (id, email, name, country, created_at, updated_at)
                VALUES (:user_id, :email, :name, 'TW', NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    email = :email,
                    name = :name,
                    updated_at = NOW()
            """),
            {"user_id": user_id, "email": email, "name": config["name"]}
        )
        
        # Add learner role
        db.execute(
            text("""
                INSERT INTO user_roles (user_id, role)
                VALUES (:user_id, 'learner')
                ON CONFLICT (user_id, role) DO NOTHING
            """),
            {"user_id": user_id}
        )
        
        # Set up XP
        print(f"   📊 Setting XP: {config['xp']} (Level {config['level']})")
        setup_user_xp(db, user_id, config["xp"], config["level"])
        
        # Set up achievements
        if config.get("achievements"):
            print(f"   🏆 Setting achievements: {len(config['achievements'])} unlocked")
            setup_achievements(db, user_id, config["achievements"])
        
        # Set up learning activity
        if config.get("streak", 0) > 0 or config.get("words_learned", 0) > 0:
            last_activity = config.get("last_activity_days_ago", 0)
            print(f"   📚 Creating activity: {config.get('words_learned', 0)} words, {config.get('streak', 0)}-day streak")
            setup_learning_activity(
                db, user_id,
                config.get("streak", 0),
                config.get("words_learned", 0),
                last_activity
            )
        
        db.commit()
        print(f"   ✅ Account ready!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False


def list_test_accounts(client: Client, db: Session):
    """List all existing test accounts."""
    print("\n📋 Existing Test Accounts")
    print("=" * 60)
    
    all_users = get_auth_users(client)
    test_users = [u for u in all_users if u.email and f"@{TEST_EMAIL_DOMAIN}" in u.email and "test+" in u.email]
    
    if not test_users:
        print("No test accounts found.")
        return
    
    for user in test_users:
        email = user.email
        persona = email.split("+")[1].split("@")[0] if "+" in email else "unknown"
        
        # Get XP info
        result = db.execute(
            text("SELECT total_xp, current_level FROM user_xp WHERE user_id = :user_id"),
            {"user_id": user.id}
        )
        xp_row = result.fetchone()
        
        # Get word count
        result = db.execute(
            text("SELECT COUNT(*) FROM learning_progress WHERE user_id = :user_id"),
            {"user_id": user.id}
        )
        word_count = result.scalar() or 0
        
        print(f"\n  {persona}")
        print(f"    Email: {email}")
        print(f"    ID: {user.id}")
        if xp_row:
            print(f"    Level: {xp_row[1]} | XP: {xp_row[0]}")
        print(f"    Words: {word_count}")


def delete_all_test_accounts(client: Client, db: Session):
    """Delete all test accounts."""
    print("\n🗑️  Deleting All Test Accounts")
    print("=" * 60)
    
    all_users = get_auth_users(client)
    test_users = [u for u in all_users if u.email and f"@{TEST_EMAIL_DOMAIN}" in u.email and "test+" in u.email]
    
    if not test_users:
        print("No test accounts found.")
        return
    
    for user in test_users:
        print(f"  Deleting {user.email}...")
        delete_user_data(db, str(user.id))
        db.commit()
        delete_auth_user(client, user.email)
        time.sleep(0.5)
    
    print(f"\n✅ Deleted {len(test_users)} test accounts")


# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Seed test accounts for development")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate all test accounts")
    parser.add_argument("--list", action="store_true", help="List existing test accounts")
    parser.add_argument("--delete", action="store_true", help="Delete all test accounts")
    parser.add_argument("--persona", type=str, help="Create only specific persona")
    args = parser.parse_args()
    
    print("=" * 60)
    print("LexiCraft Test Account Seeder")
    print("=" * 60)
    
    try:
        client = get_supabase_client()
        db = get_db_session()
        
        print("✅ Connected to Supabase and Database")
        
        if args.list:
            list_test_accounts(client, db)
            return 0
        
        if args.delete:
            delete_all_test_accounts(client, db)
            return 0
        
        # Create accounts
        personas_to_create = {args.persona: TEST_PERSONAS[args.persona]} if args.persona else TEST_PERSONAS
        
        print(f"\n🚀 Creating {len(personas_to_create)} test account(s)...")
        print(f"   Password: {TEST_PASSWORD}")
        
        success_count = 0
        for persona, config in personas_to_create.items():
            if create_test_account(persona, config, client, db, reset=args.reset):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ Created {success_count}/{len(personas_to_create)} test accounts")
        print("\nQuick Login:")
        for persona in personas_to_create:
            print(f"  {persona}: {get_test_email(persona)} / {TEST_PASSWORD}")
        
        db.close()
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

