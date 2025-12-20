"""
SQLAlchemy Models for PostgreSQL Database

All table models for the LexiCraft MVP user data.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, Float,
    DECIMAL, ForeignKey, UniqueConstraint, JSON, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


class BaseModel:
    """Base model with common fields."""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class User(Base, BaseModel):
    """Unified user accounts (parent, child, or learner)."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=True)  # Optional for Supabase Auth
    name = Column(Text)
    phone = Column(Text)
    country = Column(Text, default='TW')
    age = Column(Integer)  # Required during onboarding
    # Birthday fields (optional - for birthday celebrations)
    birth_month = Column(Integer, nullable=True)  # 1-12
    birth_day = Column(Integer, nullable=True)  # 1-31
    birthday_edit_count = Column(Integer, default=0, nullable=False)  # Max 3 edits allowed
    email_confirmed = Column(Boolean, default=False, nullable=False)
    email_confirmed_at = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    relationships_from = relationship("UserRelationship", foreign_keys="UserRelationship.from_user_id", back_populates="from_user")
    relationships_to = relationship("UserRelationship", foreign_keys="UserRelationship.to_user_id", back_populates="to_user")
    learning_progress = relationship("LearningProgress", back_populates="user", cascade="all, delete-orphan")
    verification_schedules = relationship("VerificationSchedule", back_populates="user", cascade="all, delete-orphan")
    points_account = relationship("PointsAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    points_transactions = relationship("PointsTransaction", back_populates="user", cascade="all, delete-orphan")
    withdrawal_requests_as_learner = relationship("WithdrawalRequest", foreign_keys="WithdrawalRequest.user_id", back_populates="learner")
    withdrawal_requests_as_parent = relationship("WithdrawalRequest", foreign_keys="WithdrawalRequest.parent_id", back_populates="parent")
    relationship_discoveries = relationship("RelationshipDiscovery", back_populates="user", cascade="all, delete-orphan")


class UserRole(Base):
    """User roles for RBAC."""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Text, nullable=False)  # 'parent', 'learner', 'admin'
    created_at = Column(DateTime, default=func.now(), nullable=False)
    # Note: updated_at not included - user_roles table doesn't have this column
    
    # Relationships
    user = relationship("User", back_populates="roles")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'role', name='uq_user_role'),
    )


class UserRelationship(Base, BaseModel):
    """Generic user relationships (parent_child, coach_student, sibling, friend, etc.)."""
    __tablename__ = "user_relationships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(Text, nullable=False)  # 'parent_child', 'coach_student', 'sibling', 'friend', 'classmate', 'tutor_student'
    status = Column(Text, default='active')  # 'active', 'pending_approval', 'blocked', 'suspended'
    
    # Permissions (what from_user can do for to_user)
    permissions = Column(JSONB)  # JSONB for better querying
    
    # Metadata (context-specific) - using 'name' parameter to avoid SQLAlchemy reserved word conflict
    relationship_metadata = Column('metadata', JSONB)  # e.g., {"class_name": "English 101", "group_id": "..."}
    
    # Approval tracking
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Relationships
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="relationships_from")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="relationships_to")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    __table_args__ = (
        UniqueConstraint('from_user_id', 'to_user_id', 'relationship_type', name='uq_user_relationship'),
        CheckConstraint('from_user_id != to_user_id', name='check_not_self_relationship'),
    )


class LearningProgress(Base, BaseModel):
    """Track learning progress for each user and learning point."""
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed from child_id
    learner_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # References public.learners.id
    learning_point_id = Column(Text, nullable=False)  # References Neo4j learning_point.id
    learned_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    rank = Column(Integer, nullable=False)  # Renamed from tier to rank (word complexity 1-7)
    status = Column(Text, default='learning', nullable=False, index=True)  # 'learning', 'pending', 'verified', 'failed'
    
    # Relationships
    user = relationship("User", back_populates="learning_progress")
    verification_schedules = relationship("VerificationSchedule", back_populates="learning_progress", cascade="all, delete-orphan")
    points_transactions = relationship("PointsTransaction", back_populates="learning_progress")
    
    __table_args__ = (
        # Note: Unique constraints are now handled via partial unique indexes in the database
        # to support both learner_id-based (new) and user_id-based (legacy) progress tracking.
        # See migration 016_fix_learning_progress_unique_constraint.sql
    )


class VerificationSchedule(Base, BaseModel):
    """Spaced repetition verification schedule."""
    __tablename__ = "verification_schedule"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed from child_id
    learning_progress_id = Column(Integer, ForeignKey("learning_progress.id", ondelete="CASCADE"), nullable=False)
    
    # Algorithm support
    algorithm_type = Column(String, default='sm2_plus', nullable=False, index=True)  # 'sm2_plus' or 'fsrs'
    
    # SM-2+ specific
    test_day = Column(Integer, nullable=True)  # 1, 3, or 7 (nullable for FSRS)
    ease_factor = Column(Float, default=2.5, nullable=True)
    consecutive_correct = Column(Integer, default=0, nullable=True)
    
    # FSRS specific
    stability = Column(Float, nullable=True)  # Memory stability
    difficulty = Column(Float, default=0.5, nullable=True)  # Word difficulty (0-1)
    retention_probability = Column(Float, nullable=True)  # Predicted retention
    fsrs_state = Column(JSON, nullable=True)  # Full FSRS state object
    last_review_date = Column(Date, nullable=True)
    
    # Common fields
    current_interval = Column(Integer, default=1, nullable=False)  # Days until next review
    scheduled_date = Column(Date, nullable=False, index=True)
    completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(DateTime)
    passed = Column(Boolean)
    score = Column(DECIMAL(5, 2))
    questions = Column(JSON)
    answers = Column(JSON)
    
    # Mastery tracking
    mastery_level = Column(String, default='learning', nullable=False, index=True)
    is_leech = Column(Boolean, default=False, nullable=False, index=True)
    total_reviews = Column(Integer, default=0, nullable=False)
    total_correct = Column(Integer, default=0, nullable=False)
    avg_response_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="verification_schedules")
    learning_progress = relationship("LearningProgress", back_populates="verification_schedules")


class PointsAccount(Base, BaseModel):
    """Points account for each user."""
    __tablename__ = "points_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)  # Changed from child_id
    total_earned = Column(Integer, default=0, nullable=False)
    available_points = Column(Integer, default=0, nullable=False)
    locked_points = Column(Integer, default=0, nullable=False)
    withdrawn_points = Column(Integer, default=0, nullable=False)
    deficit_points = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="points_account")


class PointsTransaction(Base, BaseModel):
    """Points transaction history."""
    __tablename__ = "points_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed from child_id
    learning_progress_id = Column(Integer, ForeignKey("learning_progress.id"))
    transaction_type = Column(Text, nullable=False, index=True)  # 'earned', 'unlocked', 'withdrawn', 'deficit', 'bonus'
    bonus_type = Column(Text)  # 'relationship_discovery', 'pattern_recognition', etc.
    points = Column(Integer, nullable=False)
    rank = Column(Integer)  # Renamed from tier to rank (word complexity 1-7)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="points_transactions")
    learning_progress = relationship("LearningProgress", back_populates="points_transactions")


class WithdrawalRequest(Base, BaseModel):
    """Withdrawal requests from parents."""
    __tablename__ = "withdrawal_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed from child_id (the learner)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # The parent requesting
    amount_ntd = Column(DECIMAL(10, 2), nullable=False)
    points_amount = Column(Integer, nullable=False)
    status = Column(Text, default='pending', nullable=False, index=True)  # 'pending', 'processing', 'completed', 'failed'
    bank_account = Column(Text)
    transaction_id = Column(Text)
    completed_at = Column(DateTime)
    
    # Relationships
    learner = relationship("User", foreign_keys=[user_id], back_populates="withdrawal_requests_as_learner")
    parent = relationship("User", foreign_keys=[parent_id], back_populates="withdrawal_requests_as_parent")


class RelationshipDiscovery(Base, BaseModel):
    """Track relationship discoveries for bonus points."""
    __tablename__ = "relationship_discoveries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Changed from child_id
    source_learning_point_id = Column(Text, nullable=False, index=True)  # Neo4j ID
    target_learning_point_id = Column(Text, nullable=False)  # Neo4j ID
    relationship_type = Column(Text, nullable=False)
    discovered_at = Column(DateTime, default=func.now(), nullable=False)
    bonus_awarded = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="relationship_discoveries")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'source_learning_point_id', 'target_learning_point_id', 'relationship_type', 
                        name='uq_relationship_discovery'),
    )


# ============================================
# MCQ Statistics & Adaptive Selection Models
# ============================================

class MCQPool(Base, BaseModel):
    """Stores generated MCQs for verification testing."""
    __tablename__ = "mcq_pool"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sense_id = Column(String(255), nullable=False, index=True)  # References Neo4j sense.id
    word = Column(String(255), nullable=False, index=True)
    mcq_type = Column(String(50), nullable=False, index=True)  # 'meaning', 'usage', 'discrimination'
    
    # Question content
    question = Column(Text, nullable=False)
    context = Column(Text)  # Example sentence providing context
    options = Column(JSONB, nullable=False)  # [{text, is_correct, source, source_word}]
    correct_index = Column(Integer, nullable=False)
    explanation = Column(Text)  # Shown after answering
    mcq_metadata = Column('metadata', JSONB, default={})  # Additional data
    
    # Quality tracking (updated from statistics)
    difficulty_index = Column(DECIMAL(5, 4))  # % who get it right (0.0-1.0)
    discrimination_index = Column(DECIMAL(5, 4))  # How well it distinguishes ability levels
    quality_score = Column(DECIMAL(5, 4))  # Overall quality (0.0-1.0)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)  # Can be shown to users
    needs_review = Column(Boolean, default=False)  # Flagged for manual review
    review_reason = Column(Text)
    
    # Relationships
    statistics = relationship("MCQStatistics", back_populates="mcq", uselist=False, cascade="all, delete-orphan")
    attempts = relationship("MCQAttempt", back_populates="mcq", cascade="all, delete-orphan")


class MCQStatistics(Base, BaseModel):
    """Aggregated statistics for each MCQ."""
    __tablename__ = "mcq_statistics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mcq_id = Column(UUID(as_uuid=True), ForeignKey("mcq_pool.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Basic counts
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    
    # Timing
    total_response_time_ms = Column(Integer, default=0)  # Sum for calculating average
    avg_response_time_ms = Column(Integer)
    min_response_time_ms = Column(Integer)
    max_response_time_ms = Column(Integer)
    
    # Distractor effectiveness
    distractor_selections = Column(JSONB, default={})  # {"confused": 15, "opposite": 8, "similar": 3}
    
    # Quality metrics (recalculated periodically)
    difficulty_index = Column(DECIMAL(5, 4))  # correct_attempts / total_attempts
    discrimination_index = Column(DECIMAL(5, 4))  # Point-biserial correlation
    quality_score = Column(DECIMAL(5, 4))  # Weighted combination
    
    # User ability distribution (for discrimination calculation)
    ability_sum_correct = Column(DECIMAL(10, 4), default=0)
    ability_sum_wrong = Column(DECIMAL(10, 4), default=0)
    ability_count_correct = Column(Integer, default=0)
    ability_count_wrong = Column(Integer, default=0)
    
    # Flags
    needs_recalculation = Column(Boolean, default=False, index=True)
    last_calculated_at = Column(DateTime)
    
    # Relationships
    mcq = relationship("MCQPool", back_populates="statistics")


class MCQAttempt(Base):
    """Detailed record of each MCQ attempt by users."""
    __tablename__ = "mcq_attempts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mcq_id = Column(UUID(as_uuid=True), ForeignKey("mcq_pool.id", ondelete="CASCADE"), nullable=False, index=True)
    sense_id = Column(String(255), nullable=False, index=True)
    
    # Link to verification schedule (optional - for spaced rep integration)
    verification_schedule_id = Column(Integer, ForeignKey("verification_schedule.id", ondelete="SET NULL"))
    
    # Attempt details
    is_correct = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer)
    selected_option_index = Column(Integer)
    selected_option_source = Column(String(50))  # 'target', 'confused', 'opposite', 'similar'
    
    # User state at time of attempt (for discrimination calculation)
    user_ability_estimate = Column(DECIMAL(5, 4))  # Estimated ability when attempting
    
    # Context
    attempt_context = Column(String(50), default='verification')  # 'verification', 'practice', 'survey'
    
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    mcq = relationship("MCQPool", back_populates="attempts")
    verification_schedule = relationship("VerificationSchedule")

