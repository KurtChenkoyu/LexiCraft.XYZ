#!/usr/bin/env python3
"""
Check what words a user is actually learning.

Usage:
    python3 scripts/check_learning_words.py [user_email]
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

def check_learning_words(user_email: str = None):
    """Check learning words for a user."""
    conn = PostgresConnection()
    session = conn.get_session()
    
    try:
        # Step 1: Get user_id and learner_id
        if user_email:
            user_result = session.execute(
                text("""
                    SELECT id, email FROM users WHERE email = :email
                """),
                {'email': user_email}
            ).fetchone()
            
            if not user_result:
                print(f"❌ User not found: {user_email}")
                return
            
            user_id = user_result[0]
            print(f"✅ Found user: {user_result[1]} (ID: {user_id})")
        else:
            # Get first parent user
            user_result = session.execute(
                text("""
                    SELECT id, email FROM users 
                    WHERE id IN (SELECT user_id FROM public.learners WHERE is_parent_profile = true)
                    LIMIT 1
                """)
            ).fetchone()
            
            if not user_result:
                print("❌ No parent user found")
                return
            
            user_id = user_result[0]
            print(f"✅ Using user: {user_result[1]} (ID: {user_id})")
        
        # Step 2: Get learner_id
        learner_result = session.execute(
            text("""
                SELECT id, display_name, user_id 
                FROM public.learners 
                WHERE user_id = :user_id AND is_parent_profile = true
            """),
            {'user_id': user_id}
        ).fetchone()
        
        if not learner_result:
            print("❌ No learner profile found for this user")
            return
        
        learner_id = learner_result[0]
        learner_name = learner_result[1]
        print(f"✅ Found learner profile: {learner_name} (ID: {learner_id})")
        print()
        
        # Step 3: Get all learning progress for this learner
        progress_result = session.execute(
            text("""
                SELECT 
                    lp.learning_point_id as sense_id,
                    lp.status,
                    lp.tier,
                    lp.learned_at,
                    CASE 
                        WHEN lp.status IN ('learning', 'pending', 'hollow') THEN 'LEARNING'
                        WHEN lp.status IN ('verified', 'mastered', 'solid') THEN 'MASTERED'
                        ELSE 'OTHER'
                    END as category
                FROM learning_progress lp
                WHERE lp.learner_id = :learner_id
                ORDER BY lp.learned_at DESC
            """),
            {'learner_id': learner_id}
        ).fetchall()
        
        if not progress_result:
            print("⚠️  No learning progress found for this learner")
            return
        
        # Step 4: Load emoji pack to filter emoji words
        emoji_sense_ids = set()
        try:
            # Try multiple possible locations
            possible_paths = [
                backend_dir / 'data' / 'emoji_core.json',
                backend_dir.parent / 'landing-page' / 'data' / 'emoji_core.json',
                backend_dir.parent / 'landing-page' / 'public' / 'data' / 'emoji_core.json',
            ]
            
            emoji_pack_path = None
            for path in possible_paths:
                if path.exists():
                    emoji_pack_path = path
                    break
            
            if emoji_pack_path:
                import json
                with open(emoji_pack_path, 'r', encoding='utf-8') as f:
                    emoji_pack = json.load(f)
                emoji_sense_ids = set(word['sense_id'] for word in emoji_pack.get('vocabulary', []))
                print(f"📦 Loaded emoji pack from {emoji_pack_path.name}: {len(emoji_sense_ids)} emoji words")
            else:
                # Fallback: Check sense_ids that match emoji pattern
                emoji_pattern_words = [w for w in progress_result if '.emoji.' in w[0]]
                if emoji_pattern_words:
                    emoji_sense_ids = set(w[0] for w in emoji_pattern_words)
                    print(f"📦 Detected {len(emoji_sense_ids)} emoji words by pattern matching (.emoji.)")
                else:
                    print("⚠️  Emoji pack not found, using pattern matching")
        except Exception as e:
            # Fallback: Check sense_ids that match emoji pattern
            emoji_pattern_words = [w for w in progress_result if '.emoji.' in w[0]]
            if emoji_pattern_words:
                emoji_sense_ids = set(w[0] for w in emoji_pattern_words)
                print(f"📦 Detected {len(emoji_sense_ids)} emoji words by pattern matching (.emoji.)")
            else:
                print(f"⚠️  Could not load emoji pack: {e}")
        
        print()
        print("=" * 80)
        print(f"Learning Progress for: {learner_name}")
        print("=" * 80)
        print()
        
        # Categorize words
        learning_words = []
        mastered_words = []
        other_words = []
        emoji_learning = []
        emoji_mastered = []
        legacy_learning = []
        legacy_mastered = []
        
        for row in progress_result:
            sense_id = row[0]
            status = row[1]
            tier = row[2]
            learned_at = row[3]
            category = row[4]
            
            is_emoji = sense_id in emoji_sense_ids if emoji_sense_ids else False
            
            word_info = {
                'sense_id': sense_id,
                'status': status,
                'tier': tier,
                'learned_at': learned_at,
                'is_emoji': is_emoji
            }
            
            if category == 'LEARNING':
                learning_words.append(word_info)
                if is_emoji:
                    emoji_learning.append(word_info)
                else:
                    legacy_learning.append(word_info)
            elif category == 'MASTERED':
                mastered_words.append(word_info)
                if is_emoji:
                    emoji_mastered.append(word_info)
                else:
                    legacy_mastered.append(word_info)
            else:
                other_words.append(word_info)
        
        # Print summary
        print(f"📊 Summary:")
        print(f"   Total entries: {len(progress_result)}")
        print(f"   Learning: {len(learning_words)} (Emoji: {len(emoji_learning)}, Legacy: {len(legacy_learning)})")
        print(f"   Mastered: {len(mastered_words)} (Emoji: {len(emoji_mastered)}, Legacy: {len(legacy_mastered)})")
        print(f"   Other: {len(other_words)}")
        print()
        
        # Print learning words (emoji first, then legacy)
        if learning_words:
            print("=" * 80)
            print(f"🔥 LEARNING WORDS ({len(learning_words)} total)")
            print("=" * 80)
            print()
            
            if emoji_learning:
                print(f"📦 Emoji Words ({len(emoji_learning)}):")
                for i, word in enumerate(emoji_learning, 1):
                    print(f"   {i}. {word['sense_id']} | Status: {word['status']} | Tier: {word['tier']} | Learned: {word['learned_at']}")
                print()
            
            if legacy_learning:
                print(f"📚 Legacy Words ({len(legacy_learning)}):")
                for i, word in enumerate(legacy_learning, 1):
                    print(f"   {i}. {word['sense_id']} | Status: {word['status']} | Tier: {word['tier']} | Learned: {word['learned_at']}")
                print()
        else:
            print("ℹ️  No words in learning status")
            print()
        
        # Print mastered words summary
        if mastered_words:
            print("=" * 80)
            print(f"💎 MASTERED WORDS ({len(mastered_words)} total)")
            print("=" * 80)
            print(f"   Emoji: {len(emoji_mastered)}, Legacy: {len(legacy_mastered)}")
            print()
        
        # Print status breakdown
        print("=" * 80)
        print("Status Breakdown:")
        print("=" * 80)
        status_counts = {}
        for row in progress_result:
            status = row[1] or 'null'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            print(f"   {status}: {count}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        conn.close()

if __name__ == "__main__":
    user_email = sys.argv[1] if len(sys.argv) > 1 else None
    check_learning_words(user_email)

