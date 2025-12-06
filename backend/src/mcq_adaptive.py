"""
MCQ Adaptive Selection Service

Provides intelligent MCQ selection based on:
1. Learner ability estimation (from FSRS/SM2+ data + attempt history)
2. MCQ difficulty matching (select optimal difficulty for learner)
3. Quality-aware selection (prefer high-quality MCQs)

Integrates with:
- FSRS/SM-2+ spaced repetition (uses their difficulty/stability data)
- MCQ Assembler (stores generated MCQs)
- Verification Schedule (provides MCQs for scheduled tests)

Usage:
    from src.mcq_adaptive import MCQAdaptiveService
    
    service = MCQAdaptiveService(postgres_session, neo4j_conn)
    
    # Get MCQ for a verification test
    mcq = service.get_mcq_for_verification(user_id, sense_id)
    
    # Record answer and update stats
    result = service.process_answer(user_id, mcq_id, selected_index, response_time_ms)
"""

import json
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from src.database.models import (
    MCQPool, MCQStatistics, MCQAttempt, 
    VerificationSchedule, LearningProgress
)
from src.database.postgres_crud import mcq_stats


class AbilitySource(Enum):
    """Source of ability estimate."""
    FSRS = "fsrs"           # From FSRS stability/difficulty
    SM2_PLUS = "sm2_plus"   # From SM-2+ ease factor
    HISTORY = "history"     # From MCQ attempt history
    DEFAULT = "default"     # No data available


@dataclass
class AbilityEstimate:
    """User's estimated ability for a sense."""
    ability: float          # 0.0 = beginner, 1.0 = expert
    confidence: float       # How confident we are (0.0-1.0)
    source: AbilitySource   # Where estimate came from
    data_points: int        # Number of data points used


@dataclass
class MCQSelection:
    """Selected MCQ with metadata."""
    mcq: MCQPool
    user_ability: float
    mcq_difficulty: Optional[float]
    selection_reason: str


@dataclass
class AnswerResult:
    """Result of processing an answer."""
    is_correct: bool
    ability_before: float
    ability_after: float
    mcq_difficulty: Optional[float]
    explanation: str
    feedback: str


class MCQAdaptiveService:
    """
    Service for adaptive MCQ selection and tracking.
    
    Integrates with existing FSRS/SM-2+ data for ability estimation.
    """
    
    def __init__(self, db_session: Session, neo4j_conn=None):
        """
        Initialize the service.
        
        Args:
            db_session: SQLAlchemy session for PostgreSQL
            neo4j_conn: Optional Neo4j connection for content lookup
        """
        self.db = db_session
        self.neo4j = neo4j_conn
    
    # =========================================================================
    # ABILITY ESTIMATION
    # =========================================================================
    
    def estimate_ability(
        self, 
        user_id: UUID, 
        sense_id: str,
        use_fsrs_data: bool = True
    ) -> AbilityEstimate:
        """
        Estimate user's ability for a specific sense.
        
        Uses multiple sources in priority order:
        1. FSRS stability/difficulty (if available)
        2. SM-2+ ease factor (if available)
        3. MCQ attempt history
        4. Default (0.5)
        
        Args:
            user_id: User to estimate for
            sense_id: Sense being tested
            use_fsrs_data: Whether to use FSRS/SM2+ data
        
        Returns:
            AbilityEstimate with ability, confidence, and source
        """
        # Try to get FSRS/SM2+ data from verification schedule
        if use_fsrs_data:
            schedule_ability = self._estimate_from_schedule(user_id, sense_id)
            if schedule_ability:
                return schedule_ability
        
        # Fall back to MCQ attempt history
        history_ability = self._estimate_from_history(user_id, sense_id)
        if history_ability.data_points > 0:
            return history_ability
        
        # Default
        return AbilityEstimate(
            ability=0.5,
            confidence=0.0,
            source=AbilitySource.DEFAULT,
            data_points=0
        )
    
    def _estimate_from_schedule(
        self, 
        user_id: UUID, 
        sense_id: str
    ) -> Optional[AbilityEstimate]:
        """
        Estimate ability from FSRS/SM2+ verification schedule data.
        
        Uses:
        - FSRS: stability, difficulty, retention_probability
        - SM2+: ease_factor, consecutive_correct
        """
        # Get learning progress for this sense
        progress = self.db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.learning_point_id.like(f"%{sense_id}%")
        ).first()
        
        if not progress:
            return None
        
        # Get most recent verification schedule with FSRS/SM2+ data
        schedule = self.db.query(VerificationSchedule).filter(
            VerificationSchedule.learning_progress_id == progress.id
        ).order_by(desc(VerificationSchedule.created_at)).first()
        
        if not schedule:
            return None
        
        # Check for FSRS data (from migration 011)
        stability = getattr(schedule, 'stability', None)
        difficulty = getattr(schedule, 'difficulty', None)
        retention_prob = getattr(schedule, 'retention_probability', None)
        
        if stability is not None and difficulty is not None:
            # FSRS estimate: ability = (1 - difficulty) * retention_weight
            # Higher stability + lower difficulty = higher ability
            ability = (1 - difficulty) * 0.6 + (retention_prob or 0.5) * 0.4
            return AbilityEstimate(
                ability=max(0.0, min(1.0, ability)),
                confidence=0.8,  # FSRS data is reliable
                source=AbilitySource.FSRS,
                data_points=schedule.total_reviews if hasattr(schedule, 'total_reviews') else 1
            )
        
        # Check for SM-2+ data
        ease_factor = getattr(schedule, 'ease_factor', None)
        consecutive_correct = getattr(schedule, 'consecutive_correct', None)
        
        if ease_factor is not None:
            # SM-2+ estimate: normalize ease factor to 0-1
            # EF range is 1.3 - 3.0, so normalize
            normalized_ef = (ease_factor - 1.3) / (3.0 - 1.3)
            
            # Add bonus for consecutive correct
            consecutive_bonus = min(0.2, (consecutive_correct or 0) * 0.04)
            
            ability = normalized_ef * 0.8 + consecutive_bonus
            return AbilityEstimate(
                ability=max(0.0, min(1.0, ability)),
                confidence=0.6,  # SM-2+ is less precise than FSRS
                source=AbilitySource.SM2_PLUS,
                data_points=schedule.total_reviews if hasattr(schedule, 'total_reviews') else 1
            )
        
        return None
    
    def _estimate_from_history(
        self, 
        user_id: UUID, 
        sense_id: str,
        recent_limit: int = 30
    ) -> AbilityEstimate:
        """Estimate ability from MCQ attempt history."""
        ability = mcq_stats.estimate_user_ability_from_history(
            self.db, user_id, sense_id, recent_limit
        )
        
        # Count data points
        total, correct = mcq_stats.count_user_attempts(self.db, user_id, sense_id)
        
        # Confidence based on number of attempts
        confidence = min(0.9, total * 0.05) if total > 0 else 0.0
        
        return AbilityEstimate(
            ability=ability,
            confidence=confidence,
            source=AbilitySource.HISTORY,
            data_points=total
        )
    
    # =========================================================================
    # MCQ SELECTION
    # =========================================================================
    
    def get_mcq_for_verification(
        self,
        user_id: UUID,
        sense_id: str,
        mcq_type: Optional[str] = None,
        verification_schedule_id: Optional[int] = None
    ) -> Optional[MCQSelection]:
        """
        Get an MCQ for a verification test.
        
        Selects MCQ matching user's ability level.
        
        Args:
            user_id: User being tested
            sense_id: Sense being verified
            mcq_type: Optional filter ('meaning', 'usage', 'discrimination')
            verification_schedule_id: Optional link to spaced rep schedule
        
        Returns:
            MCQSelection with MCQ and metadata, or None if no MCQ available
        """
        # 1. Estimate user ability
        ability_estimate = self.estimate_ability(user_id, sense_id)
        
        # 2. Get recently shown MCQs to avoid
        recent_mcq_ids = self._get_recent_mcq_ids(user_id, sense_id, limit=5)
        
        # 3. Select adaptive MCQ
        mcq = mcq_stats.select_adaptive_mcq(
            self.db,
            sense_id=sense_id,
            user_ability=ability_estimate.ability,
            exclude_mcq_ids=recent_mcq_ids,
            mcq_type=mcq_type
        )
        
        if not mcq:
            return None
        
        # 4. Get MCQ difficulty
        stats = mcq_stats.get_mcq_statistics(self.db, mcq.id)
        mcq_difficulty = float(stats.difficulty_index) if stats and stats.difficulty_index else None
        
        # 5. Build selection reason
        if mcq_difficulty is not None:
            diff_match = abs(ability_estimate.ability - mcq_difficulty)
            if diff_match < 0.1:
                reason = "Optimal difficulty match"
            elif diff_match < 0.2:
                reason = "Good difficulty match"
            else:
                reason = "Best available (limited pool)"
        else:
            reason = "New MCQ (no difficulty data yet)"
        
        return MCQSelection(
            mcq=mcq,
            user_ability=ability_estimate.ability,
            mcq_difficulty=mcq_difficulty,
            selection_reason=reason
        )
    
    def get_mcqs_for_session(
        self,
        user_id: UUID,
        sense_id: str,
        count: int = 3,
        mcq_types: Optional[List[str]] = None
    ) -> List[MCQSelection]:
        """
        Get multiple MCQs for a verification session.
        
        Args:
            user_id: User being tested
            sense_id: Sense being verified
            count: Number of MCQs to return
            mcq_types: Optional list of types to include
        
        Returns:
            List of MCQSelection instances
        """
        # Default types: one of each
        if mcq_types is None:
            mcq_types = ['meaning', 'usage', 'discrimination']
        
        ability_estimate = self.estimate_ability(user_id, sense_id)
        recent_mcq_ids = self._get_recent_mcq_ids(user_id, sense_id, limit=10)
        
        selections = []
        used_ids = list(recent_mcq_ids)
        
        for mcq_type in mcq_types[:count]:
            mcq = mcq_stats.select_adaptive_mcq(
                self.db,
                sense_id=sense_id,
                user_ability=ability_estimate.ability,
                exclude_mcq_ids=used_ids,
                mcq_type=mcq_type
            )
            
            if mcq:
                stats = mcq_stats.get_mcq_statistics(self.db, mcq.id)
                selections.append(MCQSelection(
                    mcq=mcq,
                    user_ability=ability_estimate.ability,
                    mcq_difficulty=float(stats.difficulty_index) if stats and stats.difficulty_index else None,
                    selection_reason=f"Selected for {mcq_type} test"
                ))
                used_ids.append(mcq.id)
        
        return selections
    
    def _get_recent_mcq_ids(
        self, 
        user_id: UUID, 
        sense_id: str, 
        limit: int = 5
    ) -> List[UUID]:
        """Get IDs of recently shown MCQs for this user/sense."""
        recent = self.db.query(MCQAttempt.mcq_id).filter(
            MCQAttempt.user_id == user_id,
            MCQAttempt.sense_id == sense_id
        ).order_by(desc(MCQAttempt.created_at)).limit(limit).all()
        
        return [r.mcq_id for r in recent]
    
    # =========================================================================
    # ANSWER PROCESSING
    # =========================================================================
    
    def process_answer(
        self,
        user_id: UUID,
        mcq_id: UUID,
        selected_index: int,
        response_time_ms: Optional[int] = None,
        verification_schedule_id: Optional[int] = None,
        context: str = 'verification'
    ) -> AnswerResult:
        """
        Process a user's answer to an MCQ.
        
        1. Records the attempt
        2. Updates MCQ statistics (via trigger)
        3. Returns result with feedback
        
        Args:
            user_id: User who answered
            mcq_id: MCQ answered
            selected_index: Index of selected option (0-based)
            response_time_ms: Time taken to answer
            verification_schedule_id: Optional link to spaced rep
            context: Context of attempt ('verification', 'practice', 'survey')
        
        Returns:
            AnswerResult with correctness, ability changes, and feedback
        """
        # Get MCQ
        mcq = mcq_stats.get_mcq_by_id(self.db, mcq_id)
        if not mcq:
            raise ValueError(f"MCQ {mcq_id} not found")
        
        # Check correctness
        is_correct = (selected_index == mcq.correct_index)
        
        # Get selected option details
        options = mcq.options  # JSONB field
        selected_option = options[selected_index] if selected_index < len(options) else {}
        selected_source = selected_option.get('source', 'unknown')
        
        # Estimate ability before
        ability_before = self.estimate_ability(user_id, mcq.sense_id).ability
        
        # Record attempt (triggers stats update)
        mcq_stats.record_attempt(
            self.db,
            user_id=user_id,
            mcq_id=mcq_id,
            sense_id=mcq.sense_id,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            selected_option_index=selected_index,
            selected_option_source=selected_source,
            user_ability_estimate=ability_before,
            verification_schedule_id=verification_schedule_id,
            attempt_context=context
        )
        
        # Get ability after (will be slightly updated due to new data point)
        ability_after = self.estimate_ability(user_id, mcq.sense_id).ability
        
        # Get MCQ stats
        stats = mcq_stats.get_mcq_statistics(self.db, mcq_id)
        mcq_difficulty = float(stats.difficulty_index) if stats and stats.difficulty_index else None
        
        # Generate feedback
        if is_correct:
            if mcq_difficulty and mcq_difficulty < 0.4:
                feedback = "Excellent! That was a challenging one."
            elif mcq_difficulty and mcq_difficulty > 0.7:
                feedback = "Correct! Keep going."
            else:
                feedback = "Well done!"
        else:
            correct_option = options[mcq.correct_index]
            feedback = f"The correct answer was: {correct_option.get('text', 'N/A')}"
        
        return AnswerResult(
            is_correct=is_correct,
            ability_before=ability_before,
            ability_after=ability_after,
            mcq_difficulty=mcq_difficulty,
            explanation=mcq.explanation or "",
            feedback=feedback
        )
    
    # =========================================================================
    # QUALITY MANAGEMENT
    # =========================================================================
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get MCQ quality summary report."""
        return mcq_stats.get_quality_summary(self.db)
    
    def get_mcqs_needing_attention(self, limit: int = 20) -> List[Dict]:
        """
        Get MCQs that need attention (low quality or flagged).
        
        Returns:
            List of dicts with MCQ details and issues
        """
        # Get flagged MCQs
        flagged = mcq_stats.get_mcqs_needing_review(self.db, limit=limit)
        
        # Get low quality MCQs
        low_quality = mcq_stats.get_low_quality_mcqs(self.db, limit=limit)
        
        results = []
        
        for mcq in flagged:
            results.append({
                'mcq_id': str(mcq.id),
                'word': mcq.word,
                'sense_id': mcq.sense_id,
                'mcq_type': mcq.mcq_type,
                'issue': 'flagged_for_review',
                'reason': mcq.review_reason,
                'quality_score': float(mcq.quality_score) if mcq.quality_score else None
            })
        
        for mcq, stats in low_quality:
            if not any(r['mcq_id'] == str(mcq.id) for r in results):
                results.append({
                    'mcq_id': str(mcq.id),
                    'word': mcq.word,
                    'sense_id': mcq.sense_id,
                    'mcq_type': mcq.mcq_type,
                    'issue': 'low_quality',
                    'reason': f"Quality score: {stats.quality_score:.2f}" if stats.quality_score else "No stats",
                    'quality_score': float(stats.quality_score) if stats.quality_score else None,
                    'total_attempts': stats.total_attempts,
                    'difficulty': float(stats.difficulty_index) if stats.difficulty_index else None,
                    'discrimination': float(stats.discrimination_index) if stats.discrimination_index else None
                })
        
        return results[:limit]
    
    def trigger_quality_recalculation(self) -> int:
        """
        Trigger recalculation of all MCQ quality metrics.
        
        Uses Python-side calculation (DB functions may not exist).
        
        Returns:
            Number of MCQs recalculated
        """
        # Python-side calculation
        stats_needing_recalc = self.db.query(MCQStatistics).filter(
            MCQStatistics.needs_recalculation == True
        ).all()
        
        if not stats_needing_recalc:
            return 0
        
        count = 0
        for stats in stats_needing_recalc:
            if stats.total_attempts >= 5:
                # Calculate difficulty
                difficulty = stats.correct_attempts / stats.total_attempts
                
                # Calculate discrimination (simplified)
                discrimination = None
                if stats.ability_count_correct > 0 and stats.ability_count_wrong > 0:
                    mean_correct = float(stats.ability_sum_correct) / stats.ability_count_correct
                    mean_wrong = float(stats.ability_sum_wrong) / stats.ability_count_wrong
                    discrimination = max(0, min(1, mean_correct - mean_wrong))
                
                # Calculate quality
                if discrimination is not None:
                    quality = 0.5 * discrimination + 0.5 * (1 - abs(difficulty - 0.5) * 2)
                else:
                    quality = 1 - abs(difficulty - 0.5) * 2
                
                # Update stats
                stats.difficulty_index = Decimal(str(difficulty))
                stats.discrimination_index = Decimal(str(discrimination)) if discrimination else None
                stats.quality_score = Decimal(str(quality))
                stats.needs_recalculation = False
                
                # Update mcq_pool as well
                mcq = mcq_stats.get_mcq_by_id(self.db, stats.mcq_id)
                if mcq:
                    mcq.difficulty_index = stats.difficulty_index
                    mcq.discrimination_index = stats.discrimination_index
                    mcq.quality_score = stats.quality_score
                    mcq.needs_review = (discrimination and discrimination < 0.2) or difficulty < 0.2 or difficulty > 0.9
                    if mcq.needs_review:
                        if discrimination and discrimination < 0.2:
                            mcq.review_reason = 'Low discrimination'
                        elif difficulty < 0.2:
                            mcq.review_reason = 'Too difficult'
                        else:
                            mcq.review_reason = 'Too easy'
                
                count += 1
        
        self.db.commit()
        return count


# ============================================
# Helper Functions
# ============================================

def create_adaptive_service(db_session: Session, neo4j_conn=None) -> MCQAdaptiveService:
    """Factory function to create MCQAdaptiveService."""
    return MCQAdaptiveService(db_session, neo4j_conn)


# ============================================
# CLI for Testing
# ============================================

if __name__ == "__main__":
    import argparse
    from src.database.postgres_connection import PostgresConnection
    
    parser = argparse.ArgumentParser(description="MCQ Adaptive Selection Service")
    parser.add_argument("--quality-report", action="store_true", help="Show quality report")
    parser.add_argument("--recalculate", action="store_true", help="Recalculate quality metrics")
    parser.add_argument("--needs-attention", action="store_true", help="Show MCQs needing attention")
    
    args = parser.parse_args()
    
    pg_conn = PostgresConnection()
    db = pg_conn.get_session()
    service = MCQAdaptiveService(db)
    
    if args.quality_report:
        report = service.get_quality_report()
        print("\n📊 MCQ Quality Report")
        print("=" * 50)
        print(f"Total MCQs: {report['total_mcqs']}")
        print(f"Active MCQs: {report['active_mcqs']}")
        print(f"Needs Review: {report['needs_review']}")
        print(f"\nQuality Distribution:")
        for level, count in report['quality_distribution'].items():
            print(f"  {level.capitalize()}: {count}")
        print(f"\nAvg Quality Score: {report['avg_quality_score']:.3f}" if report['avg_quality_score'] else "No quality data")
        print(f"Total Attempts: {report['total_attempts']}")
    
    elif args.recalculate:
        count = service.trigger_quality_recalculation()
        print(f"✅ Recalculated quality for {count} MCQs")
    
    elif args.needs_attention:
        issues = service.get_mcqs_needing_attention()
        print("\n⚠️ MCQs Needing Attention")
        print("=" * 50)
        for item in issues:
            print(f"\n{item['word']} ({item['mcq_type']})")
            print(f"  Issue: {item['issue']}")
            print(f"  Reason: {item['reason']}")
            if item.get('quality_score'):
                print(f"  Quality: {item['quality_score']:.2f}")
    
    else:
        parser.print_help()

