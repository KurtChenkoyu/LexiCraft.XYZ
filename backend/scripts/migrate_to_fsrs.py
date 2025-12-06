"""
Migration Script: Convert SM-2+ Users to FSRS

This script migrates existing users from SM-2+ to FSRS algorithm.
It converts SM-2+ state (ease_factor, intervals) to FSRS state (stability, difficulty).

Usage:
    python -m scripts.migrate_to_fsrs [--user-id USER_ID] [--force] [--dry-run]
"""

import argparse
import logging
import sys
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.database.postgres_connection import PostgresConnection
from src.spaced_repetition import AssignmentService, FSRSService, SM2PlusService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def estimate_fsrs_from_sm2(
    ease_factor: float,
    current_interval: int,
    total_reviews: int,
    total_correct: int,
) -> Dict[str, Any]:
    """
    Estimate FSRS parameters from SM-2+ state.
    
    This is a heuristic conversion since FSRS and SM-2+ use different models.
    The actual FSRS state will be refined as the user continues reviewing.
    """
    # Estimate stability from current interval
    # FSRS stability roughly corresponds to how long until forgetting
    # We use current_interval as a proxy
    estimated_stability = max(1.0, current_interval * 0.8)
    
    # Estimate difficulty from ease factor
    # Lower ease_factor = harder word
    # FSRS difficulty is 0-1, where 1 = hardest
    # SM-2+ ease_factor is 1.3-3.0, where 1.3 = hardest
    if ease_factor <= 1.3:
        estimated_difficulty = 1.0
    elif ease_factor >= 3.0:
        estimated_difficulty = 0.0
    else:
        # Linear mapping: 1.3 -> 1.0, 2.5 -> 0.5, 3.0 -> 0.0
        estimated_difficulty = 1.0 - ((ease_factor - 1.3) / (3.0 - 1.3))
    
    # Estimate reps and lapses from review history
    reps = total_reviews
    lapses = total_reviews - total_correct
    
    # Create initial FSRS card state
    # Note: This is a simplified conversion. Real FSRS would need
    # the full state object from the fsrs library.
    fsrs_state = {
        'stability': estimated_stability,
        'difficulty': estimated_difficulty,
        'reps': reps,
        'lapses': lapses,
        'elapsed_days': 0,
        'scheduled_days': current_interval,
        'state': 2,  # 2 = Review state
    }
    
    return {
        'stability': estimated_stability,
        'difficulty': estimated_difficulty,
        'fsrs_state': fsrs_state,
    }


def migrate_user_to_fsrs(
    db: Session,
    user_id: UUID,
    force: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Migrate a single user from SM-2+ to FSRS.
    
    Args:
        db: Database session
        user_id: User UUID
        force: Force migration even if under 100 reviews
        dry_run: If True, don't actually migrate, just report
        
    Returns:
        True if migration successful
    """
    assignment_service = AssignmentService(db)
    
    # Check current algorithm
    current_algo = assignment_service.get_assignment(user_id, db)
    if current_algo and current_algo.value == 'fsrs':
        logger.info(f"User {user_id} already using FSRS")
        return True
    
    # Check eligibility
    if not force:
        can_migrate, review_count = assignment_service.can_migrate_to_fsrs(user_id, db)
        if not can_migrate:
            logger.warning(
                f"User {user_id} cannot migrate yet "
                f"({review_count}/{assignment_service.MIN_REVIEWS_FOR_MIGRATION} reviews)"
            )
            return False
    
    # Get all verification schedules for this user
    result = db.execute(
        text("""
            SELECT 
                id,
                learning_progress_id,
                ease_factor,
                current_interval,
                total_reviews,
                total_correct,
                algorithm_type
            FROM verification_schedule
            WHERE user_id = :user_id
            AND algorithm_type = 'sm2_plus'
        """),
        {'user_id': user_id}
    )
    
    schedules = result.fetchall()
    logger.info(f"Found {len(schedules)} SM-2+ schedules for user {user_id}")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would migrate {len(schedules)} schedules")
        return True
    
    # Migrate each schedule
    migrated_count = 0
    for schedule in schedules:
        schedule_id = schedule[0]
        ease_factor = schedule[2] or 2.5
        current_interval = schedule[3] or 1
        total_reviews = schedule[4] or 0
        total_correct = schedule[5] or 0
        
        # Estimate FSRS parameters
        fsrs_params = estimate_fsrs_from_sm2(
            ease_factor, current_interval, total_reviews, total_correct
        )
        
        # Update schedule
        try:
            db.execute(
                text("""
                    UPDATE verification_schedule
                    SET 
                        algorithm_type = 'fsrs',
                        stability = :stability,
                        difficulty = :difficulty,
                        fsrs_state = CAST(:fsrs_state AS jsonb),
                        updated_at = NOW()
                    WHERE id = :schedule_id
                """),
                {
                    'schedule_id': schedule_id,
                    'stability': fsrs_params['stability'],
                    'difficulty': fsrs_params['difficulty'],
                    'fsrs_state': str(fsrs_params['fsrs_state']).replace("'", '"'),
                }
            )
            migrated_count += 1
        except Exception as e:
            logger.error(f"Failed to migrate schedule {schedule_id}: {e}")
            db.rollback()
            continue
    
    # Update user assignment
    success = assignment_service.migrate_to_fsrs(user_id, db, force=force)
    
    if success:
        logger.info(
            f"Successfully migrated user {user_id}: "
            f"{migrated_count}/{len(schedules)} schedules converted"
        )
        db.commit()
        return True
    else:
        logger.error(f"Failed to update user assignment for {user_id}")
        db.rollback()
        return False


def migrate_all_eligible_users(
    db: Session,
    force: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Migrate all eligible users to FSRS.
    
    Returns:
        Dict with migration statistics
    """
    assignment_service = AssignmentService(db)
    
    # Get all SM-2+ users
    result = db.execute(
        text("""
            SELECT user_id
            FROM user_algorithm_assignment
            WHERE algorithm = 'sm2_plus'
        """)
    )
    
    users = [row[0] for row in result.fetchall()]
    logger.info(f"Found {len(users)} SM-2+ users")
    
    stats = {
        'total_users': len(users),
        'migrated': 0,
        'skipped': 0,
        'failed': 0,
    }
    
    for user_id in users:
        try:
            success = migrate_user_to_fsrs(db, user_id, force=force, dry_run=dry_run)
            if success:
                stats['migrated'] += 1
            else:
                stats['skipped'] += 1
        except Exception as e:
            logger.error(f"Failed to migrate user {user_id}: {e}")
            stats['failed'] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Migrate users from SM-2+ to FSRS')
    parser.add_argument('--user-id', type=str, help='Migrate specific user ID')
    parser.add_argument('--force', action='store_true', help='Force migration even if under 100 reviews')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually migrating')
    parser.add_argument('--all', action='store_true', help='Migrate all eligible users')
    
    args = parser.parse_args()
    
    conn = PostgresConnection()
    db = conn.get_session()
    
    try:
        if args.user_id:
            # Migrate specific user
            user_id = UUID(args.user_id)
            success = migrate_user_to_fsrs(db, user_id, force=args.force, dry_run=args.dry_run)
            sys.exit(0 if success else 1)
        elif args.all:
            # Migrate all users
            stats = migrate_all_eligible_users(db, force=args.force, dry_run=args.dry_run)
            logger.info(f"Migration complete: {stats}")
            sys.exit(0 if stats['failed'] == 0 else 1)
        else:
            parser.print_help()
            sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()

