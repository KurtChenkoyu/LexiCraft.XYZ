"""
PostgreSQL CRUD operations package.
"""
from .users import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    update_user,
    delete_user,
    add_user_role,
    remove_user_role,
    get_user_roles,
    user_has_role,
    create_user_relationship,
    get_user_children,
    get_user_parents,
    is_parent_of,
    get_user_relationships,
    delete_user_relationship,
    create_parent_child_relationship,
    delete_parent_child_relationship,
    create_child_account,
)
from .progress import (
    create_learning_progress,
    get_learning_progress_by_id,
    get_learning_progress_by_user,
    get_learning_progress_by_learning_point,
    update_learning_progress_status,
    get_user_known_components,
    delete_learning_progress,
)
from .verification import (
    create_verification_schedule,
    get_verification_schedule_by_id,
    get_verification_schedules_by_user,
    get_upcoming_verifications,
    complete_verification,
    delete_verification_schedule,
)
from .points import (
    create_points_account,
    get_points_account_by_user,
    get_or_create_points_account,
    update_points_account,
    create_points_transaction,
    get_points_transaction_by_id,
    get_points_transactions_by_user,
    get_points_transactions_by_learning_progress,
)
from .withdrawals import (
    create_withdrawal_request,
    get_withdrawal_request_by_id,
    get_withdrawal_requests_by_user,
    get_withdrawal_requests_by_parent,
    update_withdrawal_request_status,
    delete_withdrawal_request,
)
from .relationships import (
    create_relationship_discovery,
    get_relationship_discovery_by_id,
    get_relationship_discoveries_by_user,
    get_relationship_discoveries_by_source,
    check_relationship_exists,
    mark_bonus_awarded,
    delete_relationship_discovery,
)

__all__ = [
    # Users
    'create_user',
    'get_user_by_id',
    'get_user_by_email',
    'update_user',
    'delete_user',
    # User Roles
    'add_user_role',
    'remove_user_role',
    'get_user_roles',
    'user_has_role',
    # User Relationships
    'create_user_relationship',
    'get_user_children',
    'get_user_parents',
    'is_parent_of',
    'get_user_relationships',
    'delete_user_relationship',
    'create_parent_child_relationship',
    'delete_parent_child_relationship',
    'create_child_account',
    # Learning Progress
    'create_learning_progress',
    'get_learning_progress_by_id',
    'get_learning_progress_by_user',
    'get_learning_progress_by_learning_point',
    'update_learning_progress_status',
    'get_user_known_components',
    'delete_learning_progress',
    # Verification
    'create_verification_schedule',
    'get_verification_schedule_by_id',
    'get_verification_schedules_by_user',
    'get_upcoming_verifications',
    'complete_verification',
    'delete_verification_schedule',
    # Points
    'create_points_account',
    'get_points_account_by_user',
    'get_or_create_points_account',
    'update_points_account',
    'create_points_transaction',
    'get_points_transaction_by_id',
    'get_points_transactions_by_user',
    'get_points_transactions_by_learning_progress',
    # Withdrawals
    'create_withdrawal_request',
    'get_withdrawal_request_by_id',
    'get_withdrawal_requests_by_user',
    'get_withdrawal_requests_by_parent',
    'update_withdrawal_request_status',
    'delete_withdrawal_request',
    # Relationships
    'create_relationship_discovery',
    'get_relationship_discovery_by_id',
    'get_relationship_discoveries_by_user',
    'get_relationship_discoveries_by_source',
    'check_relationship_exists',
    'mark_bonus_awarded',
    'delete_relationship_discovery',
]

