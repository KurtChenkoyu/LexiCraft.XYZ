"""
Backfill FSRS Review History

Converts existing verification history to FSRS review history format.
This allows FSRS to learn from past reviews for better personalization.

Usage:
    python -m scripts.backfill_fsrs_history [--user-id USER_ID] [--all]
"""

import argparse
import logging
import sys
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from src.database.postgres_connection import PostgresConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_rating_to_fsrs(passed: bool, score: Optional[float]) -> int:
    """
    Convert verification result to FSRS rating (0-4).
    
    FSRS scale:
    - 0 (Again): Failed
    - 1 (Hard): Barely passed
    - 2 (Good): Passed
    - 3 (Easy): Passed easily
    """
    if not passed:
        return 0  # Again
    elif score is None:
        return 2  # Good (default for passed)
    elif score >= 90:
        return 3  # Easy
    elif score >= 70:
        return 2  # Good
    else:
        return 1  # Hard


def backfill_user_history(
    db: Session,
    user_id: UUID,
) -> int:
    """
    Backfill FSRS review history for a user.
    
    Converts existing verification_schedule completed records to fsrs_review_history.
    
    Returns:
        Number of records backfilled
    """
    # Get algorithm type
    algo_result = db.execute(
        text("""
            SELECT algorithm
            FROM user_algorithm_assignment
            WHERE user_id = :user_id
        """),
        {'user_id': user_id}
    )
    algo_row = algo_result.fetchone()
    if not algo_row:
        logger.warning(f"User {user_id} has no algorithm assignment")
        return 0
    
    algorithm_type = algo_row[0]
    
    # Get completed verifications
    result = db.execute(
        text("""
            SELECT 
                id,
                learning_progress_id,
                scheduled_date,
                completed_at,
                passed,
                score,
                ease_factor,
                current_interval,
                total_reviews,
                total_correct
            FROM verification_schedule
            WHERE user_id = :user_id
            AND completed = TRUE
            AND completed_at IS NOT NULL
            ORDER BY completed_at ASC
        """),
        {'user_id': user_id}
    )
    
    verifications = result.fetchall()
    logger.info(f"Found {len(verifications)} completed verifications for user {user_id}")
    
    backfilled = 0
    
    for i, verification in enumerate(verifications):
        schedule_id = verification[0]
        learning_progress_id = verification[1]
        scheduled_date = verification[2]
        completed_at = verification[3]
        passed = verification[4]
        score = verification[5]
        ease_factor = verification[6] or 2.5
        current_interval = verification[7] or 1
        total_reviews = verification[8] or 0
        total_correct = verification[9] or 0
        
        # Check if already backfilled
        existing = db.execute(
            text("""
                SELECT id
                FROM fsrs_review_history
                WHERE user_id = :user_id
                AND learning_progress_id = :learning_progress_id
                AND review_date = :review_date
            """),
            {
                'user_id': user_id,
                'learning_progress_id': learning_progress_id,
                'review_date': completed_at,
            }
        ).fetchone()
        
        if existing:
            continue  # Already backfilled
        
        # Convert to FSRS rating
        rating = convert_rating_to_fsrs(passed, score)
        
        # Estimate stability and difficulty from SM-2+ state
        # (This is a simplified conversion)
        stability_before = current_interval * 0.8 if current_interval > 0 else 1.0
        difficulty_before = 1.0 - ((ease_factor - 1.3) / (3.0 - 1.3)) if ease_factor else 0.5
        difficulty_before = max(0.0, min(1.0, difficulty_before))
        
        # After review, stability increases if passed
        if passed:
            stability_after = stability_before * 1.5
            difficulty_after = max(0.0, difficulty_before - 0.1)
        else:
            stability_after = stability_before * 0.5
            difficulty_after = min(1.0, difficulty_before + 0.1)
        
        # Calculate elapsed days (from previous review)
        # For first review, assume 0 days
        elapsed_days = 0.0
        if i > 0:
            prev_verification = verifications[i - 1]
            prev_date = prev_verification[3]  # completed_at
            if prev_date and completed_at:
                elapsed_days = (completed_at - prev_date).days
        
        # Insert into fsrs_review_history
        try:
            db.execute(
                text("""
                    INSERT INTO fsrs_review_history (
                        user_id,
                        learning_progress_id,
                        review_date,
                        performance_rating,
                        stability_before,
                        difficulty_before,
                        retention_predicted,
                        elapsed_days,
                        stability_after,
                        difficulty_after,
                        interval_after,
                        retention_actual,
                        algorithm_type
                    ) VALUES (
                        :user_id,
                        :learning_progress_id,
                        :review_date,
                        :performance_rating,
                        :stability_before,
                        :difficulty_before,
                        :retention_predicted,
                        :elapsed_days,
                        :stability_after,
                        :difficulty_after,
                        :interval_after,
                        :retention_actual,
                        :algorithm_type
                    )
                """),
                {
                    'user_id': user_id,
                    'learning_progress_id': learning_progress_id,
                    'review_date': completed_at,
                    'performance_rating': rating,
                    'stability_before': stability_before,
                    'difficulty_before': difficulty_before,
                    'retention_predicted': 0.9 if passed else 0.3,  # Estimate
                    'elapsed_days': elapsed_days,
                    'stability_after': stability_after,
                    'difficulty_after': difficulty_after,
                    'interval_after': current_interval,
                    'retention_actual': passed,
                    'algorithm_type': algorithm_type,
                }
            )
            backfilled += 1
        except Exception as e:
            logger.error(f"Failed to backfill verification {schedule_id}: {e}")
            db.rollback()
            continue
    
    if backfilled > 0:
        db.commit()
        logger.info(f"Backfilled {backfilled} review records for user {user_id}")
    
    return backfilled


def backfill_all_users(db: Session) -> dict:
    """Backfill history for all users."""
    result = db.execute(
        text("""
            SELECT DISTINCT user_id
            FROM verification_schedule
            WHERE completed = TRUE
        """)
    )
    
    users = [row[0] for row in result.fetchall()]
    logger.info(f"Found {len(users)} users with completed verifications")
    
    stats = {
        'total_users': len(users),
        'backfilled': 0,
        'failed': 0,
    }
    
    for user_id in users:
        try:
            count = backfill_user_history(db, user_id)
            stats['backfilled'] += count
        except Exception as e:
            logger.error(f"Failed to backfill user {user_id}: {e}")
            stats['failed'] += 1
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Backfill FSRS review history')
    parser.add_argument('--user-id', type=str, help='Backfill specific user ID')
    parser.add_argument('--all', action='store_true', help='Backfill all users')
    
    args = parser.parse_args()
    
    conn = PostgresConnection()
    db = conn.get_session()
    
    try:
        if args.user_id:
            user_id = UUID(args.user_id)
            count = backfill_user_history(db, user_id)
            logger.info(f"Backfilled {count} records")
            sys.exit(0)
        elif args.all:
            stats = backfill_all_users(db)
            logger.info(f"Backfill complete: {stats}")
            sys.exit(0)
        else:
            parser.print_help()
            sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()

