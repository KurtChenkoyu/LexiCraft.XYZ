"""
Neo4j Relationship Operations

Create and query relationships between LearningPoints.
"""
from typing import List, Dict, Any, Optional
from ..neo4j_connection import Neo4jConnection
from ...models.learning_point import RelationshipType


def create_relationship(
    conn: Neo4jConnection,
    source_id: str,
    target_id: str,
    relationship_type: str,
    properties: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Create a relationship between two LearningPoints.
    
    Args:
        conn: Neo4jConnection instance
        source_id: Source learning point ID
        target_id: Target learning point ID
        relationship_type: Type of relationship (e.g., PREREQUISITE_OF)
        properties: Optional relationship properties
        
    Returns:
        True if successful, False otherwise
    """
    if properties is None:
        properties = {}
    
    # Build property string
    prop_string = ", ".join([f"{k}: ${k}" for k in properties.keys()])
    if prop_string:
        prop_string = " {" + prop_string + "}"
    
    query = f"""
    MATCH (source:LearningPoint {{id: $source_id}})
    MATCH (target:LearningPoint {{id: $target_id}})
    CREATE (source)-[r:{relationship_type}{prop_string}]->(target)
    RETURN type(r) as relationship_type
    """
    
    with conn.get_session() as session:
        try:
            params = {"source_id": source_id, "target_id": target_id, **properties}
            result = session.run(query, **params)
            record = result.single()
            return record is not None
        except Exception as e:
            print(f"Error creating relationship: {e}")
            return False


def delete_relationship(
    conn: Neo4jConnection,
    source_id: str,
    target_id: str,
    relationship_type: str
) -> bool:
    """
    Delete a relationship between two LearningPoints.
    
    Args:
        conn: Neo4jConnection instance
        source_id: Source learning point ID
        target_id: Target learning point ID
        relationship_type: Type of relationship to delete
        
    Returns:
        True if successful, False otherwise
    """
    query = f"""
    MATCH (source:LearningPoint {{id: $source_id}})-[r:{relationship_type}]->(target:LearningPoint {{id: $target_id}})
    DELETE r
    RETURN count(r) as deleted_count
    """
    
    with conn.get_session() as session:
        try:
            result = session.run(query, source_id=source_id, target_id=target_id)
            record = result.single()
            return record["deleted_count"] > 0
        except Exception as e:
            print(f"Error deleting relationship: {e}")
            return False


def get_prerequisites(conn: Neo4jConnection, learning_point_id: str) -> List[Dict[str, Any]]:
    """
    Get all prerequisites for a learning point.
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the learning point
        
    Returns:
        List of prerequisite learning points
    """
    query = """
    MATCH (prereq:LearningPoint)-[:PREREQUISITE_OF]->(target:LearningPoint {id: $id})
    RETURN prereq
    ORDER BY prereq.frequency_rank
    """
    
    with conn.get_session() as session:
        result = session.run(query, id=learning_point_id)
        return [dict(record["prereq"]) for record in result]


def get_collocations(conn: Neo4jConnection, learning_point_id: str) -> List[Dict[str, Any]]:
    """
    Get all collocations for a learning point.
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the learning point
        
    Returns:
        List of collocation learning points
    """
    query = """
    MATCH (word:LearningPoint {id: $id})-[:COLLOCATES_WITH]-(colloc:LearningPoint)
    RETURN colloc
    ORDER BY colloc.frequency_rank
    """
    
    with conn.get_session() as session:
        result = session.run(query, id=learning_point_id)
        return [dict(record["colloc"]) for record in result]


def get_related_points(conn: Neo4jConnection, learning_point_id: str) -> List[Dict[str, Any]]:
    """
    Get all related learning points.
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the learning point
        
    Returns:
        List of related learning points
    """
    query = """
    MATCH (source:LearningPoint {id: $id})-[:RELATED_TO]-(related:LearningPoint)
    RETURN related
    ORDER BY related.frequency_rank
    """
    
    with conn.get_session() as session:
        result = session.run(query, id=learning_point_id)
        return [dict(record["related"]) for record in result]


def get_components_within_degrees(
    conn: Neo4jConnection,
    learning_point_id: str,
    max_degrees: int = 3
) -> List[Dict[str, Any]]:
    """
    Find all components related to a learning point within N degrees.
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the target learning point
        max_degrees: Maximum degrees of separation (default: 3)
        
    Returns:
        List of components with their degrees of separation
    """
    query = f"""
    MATCH path = (target:LearningPoint {{id: $id}})-[*1..{max_degrees}]-(component:LearningPoint)
    RETURN DISTINCT component, length(path) as degrees
    ORDER BY degrees, component.frequency_rank
    """
    
    with conn.get_session() as session:
        result = session.run(query, id=learning_point_id)
        return [
            {
                "component": dict(record["component"]),
                "degrees": record["degrees"]
            }
            for record in result
        ]


def discover_relationships(
    conn: Neo4jConnection,
    source_id: str,
    known_component_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Discover relationships between a source learning point and known components.
    Used for relationship discovery bonuses.
    
    Args:
        conn: Neo4jConnection instance
        source_id: ID of the newly learned point
        known_component_ids: List of IDs that the user already knows
        
    Returns:
        List of discovered relationships with target IDs and relationship types
    """
    query = """
    MATCH (source:LearningPoint {id: $source_id})-[r]-(target:LearningPoint)
    WHERE target.id IN $known_components
    RETURN target.id as target_id, type(r) as relationship_type, target
    """
    
    with conn.get_session() as session:
        result = session.run(
            query,
            source_id=source_id,
            known_components=known_component_ids
        )
        return [
            {
                "target_id": record["target_id"],
                "relationship_type": record["relationship_type"],
                "target": dict(record["target"])
            }
            for record in result
        ]


def get_morphological_relationships(
    conn: Neo4jConnection,
    prefix_or_suffix_id: str,
    morph_type: str = "prefix"
) -> List[Dict[str, Any]]:
    """
    Get all words that have a specific prefix or suffix.
    
    Args:
        conn: Neo4jConnection instance
        prefix_or_suffix_id: ID of the prefix/suffix learning point
        morph_type: "prefix" or "suffix"
        
    Returns:
        List of words with the prefix/suffix
    """
    query = f"""
    MATCH (word:LearningPoint)-[:MORPHOLOGICAL {{type: $morph_type}}]->(morph:LearningPoint {{id: $id}})
    RETURN word
    ORDER BY word.frequency_rank
    """
    
    with conn.get_session() as session:
        result = session.run(query, id=prefix_or_suffix_id, morph_type=morph_type)
        return [dict(record["word"]) for record in result]


def get_all_relationships(conn: Neo4jConnection, learning_point_id: str) -> List[Dict[str, Any]]:
    """
    Get all relationships for a learning point (both incoming and outgoing).
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the learning point
        
    Returns:
        List of relationships with direction and type
    """
    query = """
    MATCH (lp:LearningPoint {id: $id})-[r]-(related:LearningPoint)
    RETURN 
        related,
        type(r) as relationship_type,
        startNode(r).id = $id as is_outgoing
    ORDER BY related.frequency_rank
    """
    
    with conn.get_session() as session:
        result = session.run(query, id=learning_point_id)
        return [
            {
                "related": dict(record["related"]),
                "relationship_type": record["relationship_type"],
                "is_outgoing": record["is_outgoing"]
            }
            for record in result
        ]

