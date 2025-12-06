"""
Progressive Survey Model: Warm-Start Functions

Implements warm-start capability for LexiSurvey by leveraging prior knowledge
from learning_progress to reduce questions needed and increase confidence.

Key Functions:
- extract_prior_knowledge(): Get verified words by frequency band
- calculate_warm_start_confidence(): Initial confidence from prior data
- warm_start_band_performance(): Pre-populate band performance
- select_priority_bands(): Focus on uncertain areas
- auto_detect_survey_mode(): Choose appropriate survey mode

Research Basis:
- Bayesian updating: Prior (learning_progress) + Likelihood (survey) = Posterior
- Adaptive testing: Focus questions where uncertainty is highest
- Spaced repetition: Weight recent verifications higher
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Constants
FREQUENCY_BANDS = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
BAND_SIZE = 1000

# Configuration
PRIOR_CONFIG = {
    # Trust levels
    "verified_word_weight": 0.90,     # Verified = 90% reliable
    "recency_full_weight_days": 30,   # Data within 30 days = full weight
    "recency_decay_days": 180,        # Full decay after 6 months
    "min_recency_weight": 0.5,        # Oldest data = 50% weight
    
    # Confidence calculation
    "max_initial_confidence": 0.60,   # Never start above 60%
    "coverage_weight": 0.40,          # Band coverage importance
    "volume_weight": 0.40,            # Total verified words importance
    "recency_weight": 0.20,           # Data freshness importance
    "volume_saturation": 500,         # Verified words for max confidence
    
    # Survey mode thresholds
    "warm_start_min_verified": 20,    # Min verified words for warm-start
    "quick_validation_min_verified": 100,  # Min for quick validation
}

# Stopping thresholds by mode
STOPPING_CONFIG = {
    "cold_start": {
        "min_questions": 15,
        "confidence_threshold": 0.80,
        "max_questions": 35,
    },
    "warm_start": {
        "min_questions": 8,
        "confidence_threshold": 0.85,
        "max_questions": 20,
    },
    "quick_validation": {
        "min_questions": 5,
        "confidence_threshold": 0.90,
        "max_questions": 10,
    },
    "deep_dive": {
        "min_questions": 25,
        "confidence_threshold": 0.90,
        "max_questions": 50,
    },
}


@dataclass
class PriorKnowledge:
    """Prior knowledge extracted from learning_progress."""
    
    bands: Dict[int, Dict[str, Any]]  # {1000: {"verified_count": 10, "last_learned": datetime, "pass_rate": 0.9}}
    total_verified: int
    oldest_verification: Optional[datetime]
    newest_verification: Optional[datetime]
    
    @property
    def bands_with_data(self) -> int:
        """Count bands with verified words."""
        return sum(1 for b in self.bands.values() if b.get("verified_count", 0) > 0)
    
    @property
    def coverage(self) -> float:
        """Coverage ratio: bands with data / total bands."""
        return self.bands_with_data / len(FREQUENCY_BANDS)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "bands": {
                str(k): {
                    **v,
                    "last_learned": v.get("last_learned").isoformat() if v.get("last_learned") else None
                }
                for k, v in self.bands.items()
            },
            "total_verified": self.total_verified,
            "bands_with_data": self.bands_with_data,
            "coverage": round(self.coverage, 2),
            "oldest_verification": self.oldest_verification.isoformat() if self.oldest_verification else None,
            "newest_verification": self.newest_verification.isoformat() if self.newest_verification else None,
        }


def tier_to_frequency_band(tier: int) -> int:
    """
    Map learning_progress tier to frequency band.
    
    Tiers 1-7 map to bands 1000-7000.
    Tier 8+ maps to band 8000.
    """
    return min(tier, 8) * 1000


def extract_prior_knowledge(db: Session, user_id: UUID) -> PriorKnowledge:
    """
    Extract prior knowledge from learning_progress for warm-start.
    
    Queries verified learning points and aggregates by frequency band.
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        PriorKnowledge with band performance from verified words
    """
    try:
        result = db.execute(text("""
            SELECT 
                lp.tier,
                COUNT(*) as count,
                AVG(CASE WHEN vs.passed = true THEN 1 ELSE 0 END) as avg_pass_rate,
                MIN(lp.learned_at) as oldest,
                MAX(lp.learned_at) as newest
            FROM learning_progress lp
            LEFT JOIN verification_schedule vs ON vs.learning_progress_id = lp.id AND vs.completed = true
            WHERE lp.user_id = :user_id
            AND lp.status = 'verified'
            GROUP BY lp.tier
            ORDER BY lp.tier
        """), {"user_id": user_id})
        
        rows = result.fetchall()
        
        bands = {band: {"verified_count": 0, "last_learned": None, "pass_rate": 1.0} for band in FREQUENCY_BANDS}
        total_verified = 0
        oldest_verification = None
        newest_verification = None
        
        for tier, count, pass_rate, oldest, newest in rows:
            band = tier_to_frequency_band(tier)
            if band in bands:
                bands[band]["verified_count"] += count
                bands[band]["pass_rate"] = pass_rate if pass_rate is not None else 1.0
                bands[band]["last_learned"] = newest
                total_verified += count
                
                if oldest:
                    if oldest_verification is None or oldest < oldest_verification:
                        oldest_verification = oldest
                if newest:
                    if newest_verification is None or newest > newest_verification:
                        newest_verification = newest
        
        return PriorKnowledge(
            bands=bands,
            total_verified=total_verified,
            oldest_verification=oldest_verification,
            newest_verification=newest_verification,
        )
        
    except Exception as e:
        logger.error(f"Failed to extract prior knowledge: {e}")
        # Return empty prior knowledge on error
        return PriorKnowledge(
            bands={band: {"verified_count": 0, "last_learned": None, "pass_rate": 1.0} for band in FREQUENCY_BANDS},
            total_verified=0,
            oldest_verification=None,
            newest_verification=None,
        )


def calculate_recency_factor(prior: PriorKnowledge) -> float:
    """
    Calculate recency factor for prior knowledge.
    
    Recent data (< 30 days) = 1.0
    Old data (> 180 days) = 0.5
    Linear decay between
    """
    if prior.newest_verification is None:
        return 0.5
    
    now = datetime.now()
    days_since = (now - prior.newest_verification).days
    
    full_weight_days = PRIOR_CONFIG["recency_full_weight_days"]
    decay_days = PRIOR_CONFIG["recency_decay_days"]
    min_weight = PRIOR_CONFIG["min_recency_weight"]
    
    if days_since <= full_weight_days:
        return 1.0
    elif days_since >= decay_days:
        return min_weight
    else:
        # Linear decay
        decay_range = decay_days - full_weight_days
        days_in_decay = days_since - full_weight_days
        decay_factor = 1.0 - (days_in_decay / decay_range) * (1.0 - min_weight)
        return decay_factor


def calculate_warm_start_confidence(prior: PriorKnowledge) -> float:
    """
    Calculate initial confidence from prior knowledge.
    
    More verified words across more bands = higher initial confidence.
    Maximum initial confidence is capped at 60% - always need questions to validate.
    
    Formula:
        confidence = 0.4 * coverage + 0.4 * volume_factor + 0.2 * recency
    """
    # Factor 1: Coverage (how many bands have data)
    coverage = prior.coverage
    
    # Factor 2: Volume (total verified words)
    # Saturates around 500 words
    volume_saturation = PRIOR_CONFIG["volume_saturation"]
    volume_factor = min(prior.total_verified / volume_saturation, 1.0)
    
    # Factor 3: Recency (how recent is the data)
    recency_factor = calculate_recency_factor(prior)
    
    # Combine factors
    confidence = (
        PRIOR_CONFIG["coverage_weight"] * coverage +
        PRIOR_CONFIG["volume_weight"] * volume_factor +
        PRIOR_CONFIG["recency_weight"] * recency_factor
    )
    
    # Cap at max initial confidence
    return min(PRIOR_CONFIG["max_initial_confidence"], confidence)


def warm_start_band_performance(prior: PriorKnowledge) -> Dict[int, Dict[str, int]]:
    """
    Pre-populate band_performance with prior knowledge.
    
    Prior knowledge is treated as "pre-tested" with accuracy based on pass_rate.
    
    Returns:
        band_performance dict compatible with LexiSurveyEngine
    """
    band_performance = {}
    
    for band in FREQUENCY_BANDS:
        prior_data = prior.bands.get(band, {"verified_count": 0, "pass_rate": 1.0})
        verified = prior_data.get("verified_count", 0)
        pass_rate = prior_data.get("pass_rate", 1.0)
        
        # Apply recency decay to prior reliability
        recency = calculate_recency_factor(prior)
        effective_weight = PRIOR_CONFIG["verified_word_weight"] * recency
        
        # Calculate effective correct count
        # verified * pass_rate * weight gives us the effective "correct" answers
        effective_correct = int(verified * pass_rate * effective_weight)
        effective_tested = int(verified * effective_weight)
        
        band_performance[band] = {
            "tested": effective_tested,
            "correct": effective_correct,
            "prior": verified,  # Track original prior count
            "source": "learning_progress" if verified > 0 else None,
        }
    
    return band_performance


def estimate_reach_from_prior(prior: PriorKnowledge) -> int:
    """
    Estimate vocabulary reach from prior knowledge.
    
    Reach = highest band where we have verified words with good pass rate.
    """
    for band in reversed(FREQUENCY_BANDS):
        data = prior.bands.get(band)
        if data and data.get("verified_count", 0) >= 5:  # At least 5 verified words
            pass_rate = data.get("pass_rate", 0)
            if pass_rate >= 0.5:  # At least 50% pass rate
                return band
    
    return FREQUENCY_BANDS[0]  # Default to lowest band


def select_priority_bands(
    prior: PriorKnowledge,
    band_performance: Dict[int, Dict[str, int]]
) -> List[Tuple[int, str, int]]:
    """
    Identify bands to prioritize for testing.
    
    Priority:
    1. Bands with NO data (complete uncertainty) - priority 3
    2. Bands near the estimated boundary (high information) - priority 2
    3. Bands with stale data (old verifications) - priority 1
    
    Returns:
        List of (band, reason, priority) sorted by priority descending
    """
    priority_bands = []
    now = datetime.now()
    estimated_reach = estimate_reach_from_prior(prior)
    
    for band in FREQUENCY_BANDS:
        prior_data = prior.bands.get(band, {})
        verified = prior_data.get("verified_count", 0)
        last_learned = prior_data.get("last_learned")
        
        # Priority 3: No prior data
        if verified == 0:
            priority_bands.append((band, "no_data", 3))
            continue
        
        # Priority 2: Near boundary (high information value)
        if abs(band - estimated_reach) <= 1000:
            priority_bands.append((band, "boundary", 2))
            continue
        
        # Priority 1: Stale data (> 60 days old)
        if last_learned:
            days_since = (now - last_learned).days
            if days_since > 60:
                priority_bands.append((band, "stale", 1))
                continue
        
        # Priority 0: Has recent data, not near boundary
        priority_bands.append((band, "covered", 0))
    
    # Sort by priority (highest first)
    priority_bands.sort(key=lambda x: x[2], reverse=True)
    
    return priority_bands


def auto_detect_survey_mode(prior: PriorKnowledge, force_mode: Optional[str] = None) -> str:
    """
    Automatically detect appropriate survey mode based on prior knowledge.
    
    Rules:
    - cold_start: No or minimal prior data (< 20 verified words)
    - warm_start: Has meaningful prior data (20-100 verified words)
    - quick_validation: Substantial prior data (100+ verified words)
    - deep_dive: Only if explicitly requested
    
    Args:
        prior: Prior knowledge extracted from learning_progress
        force_mode: Override auto-detection (must be valid mode)
        
    Returns:
        Survey mode string
    """
    valid_modes = ["cold_start", "warm_start", "quick_validation", "deep_dive"]
    
    # Allow forcing a specific mode
    if force_mode and force_mode in valid_modes:
        return force_mode
    
    # Auto-detect based on prior knowledge
    if prior.total_verified >= PRIOR_CONFIG["quick_validation_min_verified"]:
        return "quick_validation"
    elif prior.total_verified >= PRIOR_CONFIG["warm_start_min_verified"]:
        return "warm_start"
    else:
        return "cold_start"


def get_stopping_config(survey_mode: str) -> Dict[str, Any]:
    """
    Get stopping criteria configuration for survey mode.
    
    Returns:
        Dict with min_questions, confidence_threshold, max_questions
    """
    return STOPPING_CONFIG.get(survey_mode, STOPPING_CONFIG["cold_start"])


def get_previous_survey(db: Session, user_id: UUID, current_session_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get the most recent completed survey for comparison.
    
    Returns:
        Dict with previous survey results, or None if no previous survey
    """
    try:
        result = db.execute(text("""
            SELECT 
                ss.id as session_id,
                ss.start_time,
                sr.volume,
                sr.reach,
                sr.density
            FROM survey_sessions ss
            JOIN survey_results sr ON sr.session_id = ss.id
            WHERE ss.user_id = :user_id
            AND ss.status = 'completed'
            AND ss.id != :current_session_id
            ORDER BY ss.start_time DESC
            LIMIT 1
        """), {"user_id": user_id, "current_session_id": current_session_id})
        
        row = result.fetchone()
        
        if row:
            return {
                "session_id": str(row[0]),
                "date": row[1],
                "volume": row[2],
                "reach": row[3],
                "density": float(row[4]) if row[4] else 0.0,
            }
        return None
        
    except Exception as e:
        logger.error(f"Failed to get previous survey: {e}")
        return None


def count_verified_between_surveys(
    db: Session, 
    user_id: UUID, 
    start_date: datetime, 
    end_date: datetime
) -> int:
    """
    Count verified words between two survey dates.
    
    Used for calculating learning efficiency between surveys.
    """
    try:
        result = db.execute(text("""
            SELECT COUNT(*)
            FROM learning_progress lp
            WHERE lp.user_id = :user_id
            AND lp.status = 'verified'
            AND lp.learned_at >= :start_date
            AND lp.learned_at < :end_date
        """), {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        return result.scalar() or 0
        
    except Exception as e:
        logger.error(f"Failed to count verified words: {e}")
        return 0


def calculate_efficiency_score(
    vocabulary_improvement: int,
    verified_between: int,
    days_between: int
) -> Optional[float]:
    """
    Calculate learning efficiency score.
    
    Higher score = more efficient learning.
    
    Formula: (vocabulary_improvement / verified_between) * (30 / days_between)
    
    - Numerator: How much vocabulary grew per verified word
    - Denominator: Normalized to 30-day periods
    
    A score of 1.0 means vocabulary grew by 1 word per verified word per 30 days.
    Score > 1.0 = better than expected (survey shows more growth than verified)
    Score < 1.0 = less efficient (verified more than survey shows)
    """
    if verified_between <= 0 or days_between <= 0:
        return None
    
    # Vocabulary improvement per verified word
    improvement_per_verified = vocabulary_improvement / verified_between
    
    # Normalize to 30-day periods
    time_factor = 30 / days_between
    
    efficiency = improvement_per_verified * time_factor
    
    return round(efficiency, 3)


def generate_efficiency_message(
    efficiency_score: Optional[float],
    vocabulary_improvement: int,
    days_between: int
) -> str:
    """
    Generate human-readable efficiency message for testimonials.
    """
    if efficiency_score is None:
        return "Keep learning to see your progress!"
    
    if vocabulary_improvement <= 0:
        return "Review your learning strategy to maximize vocabulary growth."
    
    daily_growth = vocabulary_improvement / max(days_between, 1)
    
    if efficiency_score >= 1.5:
        return f"Excellent! Your vocabulary is growing {efficiency_score:.1f}x faster with LexiCraft! (+{int(daily_growth)} words/day)"
    elif efficiency_score >= 1.0:
        return f"Great progress! +{vocabulary_improvement} words in {days_between} days ({int(daily_growth)} words/day)"
    elif efficiency_score >= 0.5:
        return f"Good progress! +{vocabulary_improvement} words. Try more focused practice to accelerate growth."
    else:
        return f"+{vocabulary_improvement} words. Consider reviewing your learning schedule for better retention."


class WarmStartResult:
    """Result of warm-start initialization."""
    
    def __init__(
        self,
        survey_mode: str,
        prior_knowledge: PriorKnowledge,
        band_performance: Dict[int, Dict[str, int]],
        initial_confidence: float,
        priority_bands: List[Tuple[int, str, int]],
        stopping_config: Dict[str, Any],
        previous_survey: Optional[Dict[str, Any]] = None,
    ):
        self.survey_mode = survey_mode
        self.prior_knowledge = prior_knowledge
        self.band_performance = band_performance
        self.initial_confidence = initial_confidence
        self.priority_bands = priority_bands
        self.stopping_config = stopping_config
        self.previous_survey = previous_survey
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "survey_mode": self.survey_mode,
            "prior_knowledge": self.prior_knowledge.to_dict(),
            "initial_confidence": round(self.initial_confidence, 3),
            "priority_bands": [
                {"band": band, "reason": reason, "priority": priority}
                for band, reason, priority in self.priority_bands
            ],
            "stopping_config": self.stopping_config,
            "previous_survey": self.previous_survey,
        }


def initialize_warm_start(
    db: Session,
    user_id: UUID,
    current_session_id: UUID,
    force_mode: Optional[str] = None,
) -> WarmStartResult:
    """
    Initialize warm-start survey with all necessary data.
    
    This is the main entry point for Progressive Survey Model.
    
    Args:
        db: Database session
        user_id: User UUID
        current_session_id: Current survey session UUID
        force_mode: Optional forced survey mode
        
    Returns:
        WarmStartResult with all warm-start data
    """
    # 1. Extract prior knowledge
    prior = extract_prior_knowledge(db, user_id)
    
    # 2. Auto-detect or use forced survey mode
    survey_mode = auto_detect_survey_mode(prior, force_mode)
    
    # 3. Calculate initial confidence
    initial_confidence = calculate_warm_start_confidence(prior) if survey_mode != "cold_start" else 0.0
    
    # 4. Pre-populate band performance
    band_performance = warm_start_band_performance(prior) if survey_mode != "cold_start" else None
    
    # 5. Select priority bands
    priority_bands = select_priority_bands(prior, band_performance or {})
    
    # 6. Get stopping config
    stopping_config = get_stopping_config(survey_mode)
    
    # 7. Get previous survey for comparison
    previous_survey = get_previous_survey(db, user_id, current_session_id)
    
    logger.info(
        f"Warm-start initialized: mode={survey_mode}, "
        f"prior_verified={prior.total_verified}, "
        f"initial_confidence={initial_confidence:.2f}"
    )
    
    return WarmStartResult(
        survey_mode=survey_mode,
        prior_knowledge=prior,
        band_performance=band_performance or {band: {"tested": 0, "correct": 0} for band in FREQUENCY_BANDS},
        initial_confidence=initial_confidence,
        priority_bands=priority_bands,
        stopping_config=stopping_config,
        previous_survey=previous_survey,
    )

