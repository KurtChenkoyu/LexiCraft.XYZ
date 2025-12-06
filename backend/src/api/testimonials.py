"""
Testimonial API Endpoints

Provides endpoints for extracting testimonial data from survey history,
demonstrating the Progressive Survey Model's effectiveness.

Endpoints:
- GET /api/v1/testimonials/user/{user_id}: Individual user progress story
- GET /api/v1/testimonials/platform: Aggregate platform statistics
- GET /api/v1/testimonials/efficiency: Learning efficiency metrics
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.postgres_connection import PostgresConnection

router = APIRouter(prefix="/api/v1/testimonials", tags=["Testimonials"])

# Singleton
_postgres_conn: Optional[PostgresConnection] = None


def get_postgres_conn() -> PostgresConnection:
    """Get or create the PostgresConnection instance."""
    global _postgres_conn
    if _postgres_conn is None:
        _postgres_conn = PostgresConnection()
    return _postgres_conn


def get_db_session():
    """Get a database session."""
    conn = get_postgres_conn()
    session = conn.get_session()
    try:
        yield session
    finally:
        session.close()


# --- Response Models ---

class SurveyMilestone(BaseModel):
    """A milestone in user's survey journey."""
    date: datetime
    survey_number: int
    volume: int
    reach: int
    questions_asked: Optional[int]
    improvement_from_previous: Optional[int]
    cumulative_growth: int


class UserProgressStory(BaseModel):
    """User's complete progress story for testimonials."""
    user_id: str
    
    # Journey stats
    total_surveys: int
    first_survey_date: Optional[datetime]
    latest_survey_date: Optional[datetime]
    days_on_platform: int
    
    # Vocabulary growth
    starting_volume: int
    current_volume: int
    total_growth: int
    growth_percentage: float
    
    # Reach growth
    starting_reach: int
    current_reach: int
    reach_growth: int
    
    # Efficiency
    avg_questions_per_survey: Optional[float]
    questions_saved_by_warmstart: int
    avg_efficiency_score: Optional[float]
    
    # Learning
    total_verified_words: int
    
    # Milestones
    milestones: List[SurveyMilestone]
    
    # Testimonial text
    headline: str
    story: str


class PlatformStats(BaseModel):
    """Aggregate platform statistics for testimonials."""
    
    # User stats
    total_users_with_surveys: int
    users_with_multiple_surveys: int
    
    # Survey stats
    total_surveys: int
    avg_surveys_per_user: float
    
    # Growth stats
    avg_vocabulary_growth: float
    median_vocabulary_growth: int
    top_10_percent_growth: int
    
    # Efficiency stats
    avg_questions_first_survey: float
    avg_questions_warmstart_survey: float
    questions_saved_percentage: float
    
    # Time stats
    avg_days_to_second_survey: float
    avg_days_between_surveys: float


class EfficiencyMetrics(BaseModel):
    """Learning efficiency metrics."""
    
    # Per-user metrics
    user_id: str
    surveys_taken: int
    
    # Vocabulary efficiency
    words_learned_per_day: float
    words_learned_per_verified: float
    
    # Survey efficiency
    avg_questions_needed: float
    confidence_trend: str  # "improving", "stable", "declining"
    
    # Retention
    retention_rate: Optional[float]  # If we track verification failures
    
    # Benchmark comparison
    percentile_vs_platform: float
    efficiency_rating: str  # "exceptional", "above_average", "average", "needs_improvement"


# --- Endpoints ---

@router.get("/user/{user_id}", response_model=UserProgressStory)
async def get_user_progress_story(
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get a user's complete progress story for testimonials.
    
    Returns vocabulary growth, survey efficiency, and a generated testimonial.
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    # Get survey history
    result = db.execute(
        text("""
            SELECT 
                ss.start_time,
                sr.volume,
                sr.reach,
                sr.density,
                sm.questions_asked,
                sm.questions_saved_by_prior,
                sm.efficiency_score,
                ROW_NUMBER() OVER (ORDER BY ss.start_time) as survey_number
            FROM survey_sessions ss
            JOIN survey_results sr ON sr.session_id = ss.id
            LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
            WHERE ss.user_id = :user_id
            AND ss.status = 'completed'
            ORDER BY ss.start_time
        """),
        {"user_id": user_uuid}
    )
    
    rows = result.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No survey history found for this user")
    
    # Build milestones
    milestones = []
    starting_volume = rows[0][1]
    
    for i, row in enumerate(rows):
        date, volume, reach, density, questions, saved, efficiency, num = row
        improvement = volume - rows[i-1][1] if i > 0 else 0
        
        milestones.append(SurveyMilestone(
            date=date,
            survey_number=int(num),
            volume=volume,
            reach=reach,
            questions_asked=questions,
            improvement_from_previous=improvement if i > 0 else None,
            cumulative_growth=volume - starting_volume,
        ))
    
    # Calculate stats
    total_surveys = len(rows)
    first_date = rows[0][0]
    latest_date = rows[-1][0]
    days_on_platform = (latest_date - first_date).days if first_date and latest_date else 0
    
    current_volume = rows[-1][1]
    total_growth = current_volume - starting_volume
    growth_pct = (total_growth / starting_volume * 100) if starting_volume > 0 else 0
    
    starting_reach = rows[0][2]
    current_reach = rows[-1][2]
    
    # Questions stats
    questions_list = [r[4] for r in rows if r[4] is not None]
    avg_questions = sum(questions_list) / len(questions_list) if questions_list else None
    questions_saved = sum(r[5] or 0 for r in rows)
    
    # Efficiency stats
    efficiency_list = [r[6] for r in rows if r[6] is not None]
    avg_efficiency = sum(efficiency_list) / len(efficiency_list) if efficiency_list else None
    
    # Get total verified words
    verified_result = db.execute(
        text("""
            SELECT COUNT(*) FROM learning_progress
            WHERE user_id = :user_id AND status = 'verified'
        """),
        {"user_id": user_uuid}
    )
    total_verified = verified_result.scalar() or 0
    
    # Generate testimonial text
    headline, story = _generate_testimonial_text(
        total_surveys=total_surveys,
        total_growth=total_growth,
        growth_pct=growth_pct,
        days_on_platform=days_on_platform,
        questions_saved=questions_saved,
        avg_efficiency=avg_efficiency,
    )
    
    return UserProgressStory(
        user_id=user_id,
        total_surveys=total_surveys,
        first_survey_date=first_date,
        latest_survey_date=latest_date,
        days_on_platform=days_on_platform,
        starting_volume=starting_volume,
        current_volume=current_volume,
        total_growth=total_growth,
        growth_percentage=round(growth_pct, 1),
        starting_reach=starting_reach,
        current_reach=current_reach,
        reach_growth=current_reach - starting_reach,
        avg_questions_per_survey=round(avg_questions, 1) if avg_questions else None,
        questions_saved_by_warmstart=questions_saved,
        avg_efficiency_score=round(avg_efficiency, 2) if avg_efficiency else None,
        total_verified_words=total_verified,
        milestones=milestones,
        headline=headline,
        story=story,
    )


@router.get("/platform", response_model=PlatformStats)
async def get_platform_stats(
    db: Session = Depends(get_db_session)
):
    """
    Get aggregate platform statistics for testimonials.
    
    Shows overall effectiveness of the platform and PSM.
    """
    # User and survey counts
    user_stats = db.execute(
        text("""
            SELECT 
                COUNT(DISTINCT ss.user_id) as total_users,
                COUNT(*) as total_surveys
            FROM survey_sessions ss
            JOIN survey_results sr ON sr.session_id = ss.id
            WHERE ss.status = 'completed'
        """)
    ).fetchone()
    
    total_users = user_stats[0] or 0
    total_surveys = user_stats[1] or 0
    
    # Users with multiple surveys
    multi_survey = db.execute(
        text("""
            SELECT COUNT(*) FROM (
                SELECT ss.user_id, COUNT(*) as cnt
                FROM survey_sessions ss
                JOIN survey_results sr ON sr.session_id = ss.id
                WHERE ss.status = 'completed'
                GROUP BY ss.user_id
                HAVING COUNT(*) >= 2
            ) sub
        """)
    ).scalar() or 0
    
    # Growth stats (for users with 2+ surveys)
    growth_stats = db.execute(
        text("""
            WITH user_growth AS (
                SELECT 
                    ss.user_id,
                    MIN(sr.volume) as first_volume,
                    MAX(sr.volume) as latest_volume,
                    MAX(sr.volume) - MIN(sr.volume) as growth
                FROM survey_sessions ss
                JOIN survey_results sr ON sr.session_id = ss.id
                WHERE ss.status = 'completed'
                GROUP BY ss.user_id
                HAVING COUNT(*) >= 2
            )
            SELECT 
                AVG(growth) as avg_growth,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY growth) as median_growth,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY growth) as top_10_growth
            FROM user_growth
            WHERE growth > 0
        """)
    ).fetchone()
    
    avg_growth = float(growth_stats[0]) if growth_stats[0] else 0
    median_growth = int(growth_stats[1]) if growth_stats[1] else 0
    top_10_growth = int(growth_stats[2]) if growth_stats[2] else 0
    
    # Questions stats by survey mode
    question_stats = db.execute(
        text("""
            SELECT 
                COALESCE(ss.survey_mode, 'cold_start') as mode,
                AVG(sm.questions_asked) as avg_questions
            FROM survey_sessions ss
            LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
            WHERE ss.status = 'completed'
            AND sm.questions_asked IS NOT NULL
            GROUP BY COALESCE(ss.survey_mode, 'cold_start')
        """)
    ).fetchall()
    
    cold_start_avg = 25.0  # Default
    warm_start_avg = 15.0  # Default
    for mode, avg_q in question_stats:
        if mode == 'cold_start':
            cold_start_avg = float(avg_q) if avg_q else cold_start_avg
        elif mode in ('warm_start', 'quick_validation'):
            warm_start_avg = float(avg_q) if avg_q else warm_start_avg
    
    questions_saved_pct = ((cold_start_avg - warm_start_avg) / cold_start_avg * 100) if cold_start_avg > 0 else 0
    
    # Time between surveys
    time_stats = db.execute(
        text("""
            WITH survey_gaps AS (
                SELECT 
                    ss.user_id,
                    ss.start_time,
                    LAG(ss.start_time) OVER (PARTITION BY ss.user_id ORDER BY ss.start_time) as prev_time,
                    ROW_NUMBER() OVER (PARTITION BY ss.user_id ORDER BY ss.start_time) as rn
                FROM survey_sessions ss
                WHERE ss.status = 'completed'
            )
            SELECT 
                AVG(CASE WHEN rn = 2 THEN EXTRACT(DAY FROM start_time - prev_time) END) as avg_to_second,
                AVG(CASE WHEN rn > 1 THEN EXTRACT(DAY FROM start_time - prev_time) END) as avg_between
            FROM survey_gaps
            WHERE prev_time IS NOT NULL
        """)
    ).fetchone()
    
    avg_to_second = float(time_stats[0]) if time_stats[0] else 0
    avg_between = float(time_stats[1]) if time_stats[1] else 0
    
    return PlatformStats(
        total_users_with_surveys=total_users,
        users_with_multiple_surveys=multi_survey,
        total_surveys=total_surveys,
        avg_surveys_per_user=round(total_surveys / total_users, 1) if total_users > 0 else 0,
        avg_vocabulary_growth=round(avg_growth, 0),
        median_vocabulary_growth=median_growth,
        top_10_percent_growth=top_10_growth,
        avg_questions_first_survey=round(cold_start_avg, 1),
        avg_questions_warmstart_survey=round(warm_start_avg, 1),
        questions_saved_percentage=round(questions_saved_pct, 1),
        avg_days_to_second_survey=round(avg_to_second, 1),
        avg_days_between_surveys=round(avg_between, 1),
    )


@router.get("/efficiency/{user_id}", response_model=EfficiencyMetrics)
async def get_user_efficiency(
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get detailed learning efficiency metrics for a user.
    
    Compares user's efficiency to platform averages.
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    # Get user's survey stats
    user_stats = db.execute(
        text("""
            SELECT 
                COUNT(*) as survey_count,
                MIN(sr.volume) as first_volume,
                MAX(sr.volume) as latest_volume,
                MIN(ss.start_time) as first_date,
                MAX(ss.start_time) as latest_date,
                AVG(sm.questions_asked) as avg_questions,
                AVG(sm.efficiency_score) as avg_efficiency
            FROM survey_sessions ss
            JOIN survey_results sr ON sr.session_id = ss.id
            LEFT JOIN survey_metadata sm ON sm.session_id = ss.id
            WHERE ss.user_id = :user_id
            AND ss.status = 'completed'
        """),
        {"user_id": user_uuid}
    ).fetchone()
    
    if not user_stats or not user_stats[0]:
        raise HTTPException(status_code=404, detail="No survey data found")
    
    survey_count, first_vol, latest_vol, first_date, latest_date, avg_questions, avg_efficiency = user_stats
    
    # Calculate metrics
    total_growth = latest_vol - first_vol
    total_days = (latest_date - first_date).days if first_date and latest_date else 1
    
    # Get verified words count
    verified_count = db.execute(
        text("SELECT COUNT(*) FROM learning_progress WHERE user_id = :user_id AND status = 'verified'"),
        {"user_id": user_uuid}
    ).scalar() or 0
    
    words_per_day = total_growth / max(total_days, 1)
    words_per_verified = total_growth / max(verified_count, 1)
    
    # Get platform percentile
    percentile_result = db.execute(
        text("""
            WITH user_growth AS (
                SELECT 
                    ss.user_id,
                    MAX(sr.volume) - MIN(sr.volume) as growth
                FROM survey_sessions ss
                JOIN survey_results sr ON sr.session_id = ss.id
                WHERE ss.status = 'completed'
                GROUP BY ss.user_id
                HAVING COUNT(*) >= 2
            )
            SELECT 
                PERCENT_RANK() OVER (ORDER BY growth) * 100 as percentile
            FROM user_growth
            WHERE user_id = :user_id
        """),
        {"user_id": user_uuid}
    ).fetchone()
    
    percentile = float(percentile_result[0]) if percentile_result and percentile_result[0] else 50.0
    
    # Determine confidence trend (simplified)
    if avg_efficiency and avg_efficiency > 1.2:
        confidence_trend = "improving"
    elif avg_efficiency and avg_efficiency < 0.8:
        confidence_trend = "declining"
    else:
        confidence_trend = "stable"
    
    # Determine rating
    if percentile >= 90:
        rating = "exceptional"
    elif percentile >= 70:
        rating = "above_average"
    elif percentile >= 30:
        rating = "average"
    else:
        rating = "needs_improvement"
    
    return EfficiencyMetrics(
        user_id=user_id,
        surveys_taken=survey_count,
        words_learned_per_day=round(words_per_day, 2),
        words_learned_per_verified=round(words_per_verified, 2),
        avg_questions_needed=round(float(avg_questions), 1) if avg_questions else 0,
        confidence_trend=confidence_trend,
        retention_rate=None,  # Would need verification failure tracking
        percentile_vs_platform=round(percentile, 1),
        efficiency_rating=rating,
    )


# --- Helper Functions ---

def _generate_testimonial_text(
    total_surveys: int,
    total_growth: int,
    growth_pct: float,
    days_on_platform: int,
    questions_saved: int,
    avg_efficiency: Optional[float],
) -> tuple[str, str]:
    """
    Generate testimonial headline and story based on user stats.
    
    Returns (headline, story)
    """
    # Generate headline
    if total_growth >= 2000:
        headline = f"詞彙量增長 {total_growth:,} 個字！"
    elif growth_pct >= 50:
        headline = f"詞彙量提升 {growth_pct:.0f}%！"
    elif questions_saved >= 20:
        headline = f"測驗效率提升，節省 {questions_saved} 道題目！"
    elif total_surveys >= 3:
        headline = f"持續學習 {total_surveys} 次測驗，穩步成長！"
    else:
        headline = "開始我的字塊探索之旅"
    
    # Generate story
    story_parts = []
    
    if days_on_platform > 0:
        months = days_on_platform // 30
        if months >= 1:
            story_parts.append(f"在 LexiCraft 學習 {months} 個月以來")
        else:
            story_parts.append(f"在 LexiCraft 學習 {days_on_platform} 天以來")
    
    if total_growth > 0:
        story_parts.append(f"我的詞彙量從基礎測驗到現在增長了 {total_growth:,} 個字")
    
    if growth_pct >= 20:
        story_parts.append(f"成長幅度達到 {growth_pct:.0f}%")
    
    if questions_saved >= 10:
        story_parts.append(f"系統透過學習記錄讓我的測驗時間大幅縮短，共節省了 {questions_saved} 道題目")
    
    if avg_efficiency and avg_efficiency >= 1.0:
        story_parts.append("學習效率持續提升，系統越來越了解我的程度")
    
    if not story_parts:
        story_parts.append("開始使用 LexiCraft 探索我的英語詞彙")
    
    story = "，".join(story_parts) + "。"
    
    return headline, story

