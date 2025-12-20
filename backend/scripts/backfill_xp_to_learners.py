"""
Backfill XP from learning_progress to learner-scoped XP tables.

This script recalculates XP from the source of truth (learning_progress)
and assigns it to the correct learner_id. Uses LevelService logic to ensure
historical XP matches future XP calculations exactly.
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.database.postgres_connection import PostgresConnection
from src.services.levels import LevelService
from sqlalchemy import text
from uuid import UUID
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_xp_to_learners():
    """
    Recalculate XP from learning_progress and assign to learner_id.
    
    Strategy:
        1. Wipe existing XP data (it's "polluted" with shared XP)
        2. For each learner with progress:
            - Query ALL words (in progress + verified)
            - Award 5 XP for words in progress (effort reward)
            - Award rank-based XP for verified words (mastery reward)
            - Insert into xp_history with learner_id
            - Update user_xp for that learner_id
    """
    conn = PostgresConnection()
    db = conn.get_session()
    
    try:
        logger.info("🧹 Step 1: Wiping existing XP data (polluted with shared XP)")
        
        # Clear existing XP (will be recalculated from source of truth)
        db.execute(text("TRUNCATE TABLE xp_history"))
        db.execute(text("DELETE FROM user_xp"))
        db.commit()
        logger.info("✅ Cleared existing XP data")
        
        logger.info("📊 Step 2: Recalculating XP from learning_progress")
        
        # Get all learners with progress
        learners_result = db.execute(
            text("""
                SELECT DISTINCT learner_id
                FROM learning_progress
                WHERE learner_id IS NOT NULL
            """)
        )
        learners = [row[0] for row in learners_result.fetchall()]
        logger.info(f"Found {len(learners)} learners with progress")
        
        level_service = LevelService(db)
        
        for learner_id in learners:
            logger.info(f"Processing learner {learner_id}")
            
            # Get user_id for this learner (needed for xp_history.user_id constraint)
            learner_info = db.execute(
                text("""
                    SELECT COALESCE(user_id, guardian_id) as user_id
                    FROM public.learners
                    WHERE id = :learner_id
                """),
                {'learner_id': learner_id}
            ).fetchone()
            
            if not learner_info or not learner_info[0]:
                logger.warning(f"  ⚠️ Skipping learner {learner_id}: No user_id found")
                continue
            
            user_id = learner_info[0]
            
            # Constants (per design documentation)
            BASE_XP_WORD_IN_PROGRESS = 5  # Effort reward for words in progress
            
            # Get ALL words for this learner (in progress + verified)
            progress_result = db.execute(
                text("""
                    SELECT 
                        lp.learning_point_id,
                        lp.rank,
                        lp.status,
                        lp.learned_at,
                        lp.user_id
                    FROM learning_progress lp
                    WHERE lp.learner_id = :learner_id
                    ORDER BY lp.learned_at ASC
                """),
                {'learner_id': learner_id}
            )
            
            total_xp = 0
            xp_entries = []
            words_in_progress_count = 0
            words_verified_count = 0
            
            for row in progress_result.fetchall():
                sense_id = row[0]
                rank = row[1]  # Changed from tier to rank
                status = row[2]
                learned_at = row[3]
                progress_user_id = row[4] or user_id  # Use progress user_id if available, fallback to learner's user_id
                
                # Determine XP amount based on status (dual XP system: effort vs mastery)
                if status in ('pending', 'hollow', 'learning'):
                    # Effort-based XP: Reward engagement, not just mastery
                    xp_amount = BASE_XP_WORD_IN_PROGRESS
                    source = 'word_in_progress'
                    words_in_progress_count += 1
                elif status in ('verified', 'mastered', 'solid'):
                    # Mastery-based XP: Rank-based reward for verified words
                    base_xp = level_service.RANK_BASE_XP.get(rank, 100)  # Default to 100 if rank unknown
                    xp_amount = base_xp
                    source = 'word_learned'
                    words_verified_count += 1
                else:
                    # Unknown status - skip or log warning
                    logger.warning(f"  ⚠️ Unknown status '{status}' for word {sense_id}, skipping")
                    continue
                
                total_xp += xp_amount
                
                # Record in xp_history (include user_id for NOT NULL constraint)
                # Note: source_id is UUID type, but learning_point_id is a string, so we set it to NULL
                xp_entries.append({
                    'learner_id': learner_id,
                    'user_id': progress_user_id,  # Required for NOT NULL constraint
                    'xp_amount': xp_amount,
                    'source': source,
                    'source_id': None,  # learning_point_id is not a UUID, so we can't store it here
                    'earned_at': learned_at
                })
            
            # Insert XP history entries
            if xp_entries:
                for entry in xp_entries:
                    db.execute(
                        text("""
                            INSERT INTO xp_history (learner_id, user_id, xp_amount, source, source_id, earned_at)
                            VALUES (:learner_id, :user_id, :xp_amount, :source, :source_id, :earned_at)
                        """),
                        entry
                    )
                
                # Calculate level from total XP
                level_info = level_service.calculate_level(total_xp)
                
                # Initialize or update user_xp for this learner
                # During migration (before Part 3), learner_id is not yet the primary key
                # So we need to check existence first, then UPDATE or INSERT
                existing_check = db.execute(
                    text("SELECT learner_id FROM user_xp WHERE learner_id = :learner_id"),
                    {'learner_id': learner_id}
                ).fetchone()
                
                if existing_check:
                    # Update existing record
                    db.execute(
                        text("""
                            UPDATE user_xp
                            SET total_xp = :total_xp,
                                current_level = :level,
                                xp_to_next_level = :xp_to_next,
                                xp_in_current_level = :xp_in_level,
                                updated_at = NOW()
                            WHERE learner_id = :learner_id
                        """),
                        {
                            'learner_id': learner_id,
                            'total_xp': total_xp,
                            'level': level_info['level'],
                            'xp_to_next': level_info['xp_to_next'],
                            'xp_in_level': level_info['xp_in_level']
                        }
                    )
                else:
                    # Insert new record (include user_id for NOT NULL constraint during migration)
                    db.execute(
                        text("""
                            INSERT INTO user_xp (learner_id, user_id, total_xp, current_level, xp_to_next_level, xp_in_current_level, updated_at)
                            VALUES (:learner_id, :user_id, :total_xp, :level, :xp_to_next, :xp_in_level, NOW())
                        """),
                        {
                            'learner_id': learner_id,
                            'user_id': user_id,  # Required for NOT NULL constraint during migration
                            'total_xp': total_xp,
                            'level': level_info['level'],
                            'xp_to_next': level_info['xp_to_next'],
                            'xp_in_level': level_info['xp_in_level']
                        }
                    )
                
                logger.info(f"  ✅ Learner {learner_id}: {len(xp_entries)} words ({words_in_progress_count} in progress, {words_verified_count} verified), {total_xp} XP, Level {level_info['level']}")
            
            db.commit()
        
        logger.info("✅ Backfill complete!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Backfill failed: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    backfill_xp_to_learners()

