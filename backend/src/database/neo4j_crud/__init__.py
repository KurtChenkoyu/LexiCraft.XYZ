"""
Neo4j CRUD operations package.
"""
from .learning_points import (
    create_learning_point,
    get_learning_point,
    get_learning_point_by_word,
    update_learning_point,
    delete_learning_point,
    list_learning_points,
)
from .relationships import (
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
    # Learning Points
    'create_learning_point',
    'get_learning_point',
    'get_learning_point_by_word',
    'update_learning_point',
    'delete_learning_point',
    'list_learning_points',
    # Relationships
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

