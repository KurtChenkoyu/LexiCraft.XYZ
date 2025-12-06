"""
Database package initialization.
"""
# Import Neo4j connection (always available)
from .neo4j_connection import Neo4jConnection

# Make PostgreSQL imports optional to allow Neo4j-only usage
try:
    from .postgres_connection import PostgresConnection
    from .models import (
        Base,
        User,
        Child,
        LearningProgress,
        VerificationSchedule,
        PointsAccount,
        PointsTransaction,
        WithdrawalRequest,
        RelationshipDiscovery
    )
    _POSTGRES_AVAILABLE = True
except ImportError:
    _POSTGRES_AVAILABLE = False
    PostgresConnection = None
    Base = None
    User = None
    Child = None
    LearningProgress = None
    VerificationSchedule = None
    PointsAccount = None
    PointsTransaction = None
    WithdrawalRequest = None
    RelationshipDiscovery = None

# Import CRUD operations (PostgreSQL only if available)
if _POSTGRES_AVAILABLE:
    from .postgres_crud import (
        # Users
        create_user,
        get_user_by_id,
        get_user_by_email,
        update_user,
        delete_user,
        # Children
        create_child,
        get_child_by_id,
        get_children_by_parent,
        update_child,
        delete_child,
        # Learning Progress
        create_learning_progress,
        get_learning_progress_by_id,
        get_learning_progress_by_child,
        get_learning_progress_by_learning_point,
        update_learning_progress_status,
        get_user_known_components,
        delete_learning_progress,
        # Verification
        create_verification_schedule,
        get_verification_schedule_by_id,
        get_verification_schedules_by_child,
        get_upcoming_verifications,
        complete_verification,
        delete_verification_schedule,
        # Points
        create_points_account,
        get_points_account_by_child,
        get_or_create_points_account,
        update_points_account,
        create_points_transaction,
        get_points_transaction_by_id,
        get_points_transactions_by_child,
        get_points_transactions_by_learning_progress,
        # Withdrawals
        create_withdrawal_request,
        get_withdrawal_request_by_id,
        get_withdrawal_requests_by_child,
        get_withdrawal_requests_by_parent,
        update_withdrawal_request_status,
        delete_withdrawal_request,
        # Relationships
        create_relationship_discovery,
        get_relationship_discovery_by_id,
        get_relationship_discoveries_by_child,
        get_relationship_discoveries_by_source,
        check_relationship_exists,
        mark_bonus_awarded,
        delete_relationship_discovery,
    )

# Neo4j CRUD - always available
from .neo4j_crud import (
    # Learning Points
    create_learning_point,
    get_learning_point,
    get_learning_point_by_word,
    update_learning_point,
    delete_learning_point,
    list_learning_points,
    # Relationships
    create_relationship,
    delete_relationship,
    get_prerequisites,
    get_collocations,
    get_related_points,
    get_components_within_degrees,
    discover_relationships,
    get_morphological_relationships,
    get_all_relationships,
)

__all__ = [
    # Connections
    'Neo4jConnection',
    # Neo4j CRUD - Learning Points
    'create_learning_point',
    'get_learning_point',
    'get_learning_point_by_word',
    'update_learning_point',
    'delete_learning_point',
    'list_learning_points',
    # Neo4j CRUD - Relationships
    'create_relationship',
    'delete_relationship',
    'get_prerequisites',
    'get_collocations',
    'get_related_points',
    'get_components_within_degrees',
    'discover_relationships',
    'get_morphological_relationships',
    'get_all_relationships',
]

# Add PostgreSQL items only if available
if _POSTGRES_AVAILABLE:
    __all__.extend([
        'PostgresConnection',
        # Models
        'Base',
        'User',
        'Child',
        'LearningProgress',
        'VerificationSchedule',
        'PointsAccount',
        'PointsTransaction',
        'WithdrawalRequest',
        'RelationshipDiscovery',
        # PostgreSQL CRUD - Users
        'create_user',
        'get_user_by_id',
        'get_user_by_email',
        'update_user',
        'delete_user',
        # PostgreSQL CRUD - Children
        'create_child',
        'get_child_by_id',
        'get_children_by_parent',
        'update_child',
        'delete_child',
        # PostgreSQL CRUD - Learning Progress
        'create_learning_progress',
        'get_learning_progress_by_id',
        'get_learning_progress_by_child',
        'get_learning_progress_by_learning_point',
        'update_learning_progress_status',
        'get_user_known_components',
        'delete_learning_progress',
        # PostgreSQL CRUD - Verification
        'create_verification_schedule',
        'get_verification_schedule_by_id',
        'get_verification_schedules_by_child',
        'get_upcoming_verifications',
        'complete_verification',
        'delete_verification_schedule',
        # PostgreSQL CRUD - Points
        'create_points_account',
        'get_points_account_by_child',
        'get_or_create_points_account',
        'update_points_account',
        'create_points_transaction',
        'get_points_transaction_by_id',
        'get_points_transactions_by_child',
        'get_points_transactions_by_learning_progress',
        # PostgreSQL CRUD - Withdrawals
        'create_withdrawal_request',
        'get_withdrawal_request_by_id',
        'get_withdrawal_requests_by_child',
        'get_withdrawal_requests_by_parent',
        'update_withdrawal_request_status',
        'delete_withdrawal_request',
        # PostgreSQL CRUD - Relationships
        'create_relationship_discovery',
        'get_relationship_discovery_by_id',
        'get_relationship_discoveries_by_child',
        'get_relationship_discoveries_by_source',
        'check_relationship_exists',
        'mark_bonus_awarded',
        'delete_relationship_discovery',
    ])
