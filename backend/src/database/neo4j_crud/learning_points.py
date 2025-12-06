"""
Neo4j CRUD Operations for Learning Points

Create, Read, Update, Delete operations for LearningPoint nodes.
"""
import json
from typing import List, Optional, Dict, Any
from ..neo4j_connection import Neo4jConnection
from ...models.learning_point import LearningPoint


def create_learning_point(conn: Neo4jConnection, learning_point: LearningPoint) -> bool:
    """
    Create a new LearningPoint node.
    
    Args:
        conn: Neo4jConnection instance
        learning_point: LearningPoint model instance
        
    Returns:
        True if successful, False otherwise
    """
    query = """
    CREATE (lp:LearningPoint {
        id: $id,
        word: $word,
        type: $type,
        tier: $tier,
        definition: $definition,
        example: $example,
        frequency_rank: $frequency_rank,
        difficulty: $difficulty,
        register: $register,
        contexts: $contexts,
        metadata: $metadata
    })
    RETURN lp.id as id
    """
    
    with conn.get_session() as session:
        try:
            # Convert metadata dict to JSON string for Neo4j storage
            metadata_json = json.dumps(learning_point.metadata) if learning_point.metadata else "{}"
            
            result = session.run(
                query,
                id=learning_point.id,
                word=learning_point.word,
                type=learning_point.type,
                tier=learning_point.tier,
                definition=learning_point.definition,
                example=learning_point.example,
                frequency_rank=learning_point.frequency_rank,
                difficulty=learning_point.difficulty,
                register=learning_point.register,
                contexts=learning_point.contexts,
                metadata=metadata_json
            )
            record = result.single()
            return record is not None
        except Exception as e:
            print(f"Error creating learning point: {e}")
            return False


def get_learning_point(conn: Neo4jConnection, learning_point_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a LearningPoint by ID.
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the learning point
        
    Returns:
        Dictionary with learning point data or None if not found
    """
    query = """
    MATCH (lp:LearningPoint {id: $id})
    RETURN lp
    """
    
    with conn.get_session() as session:
        result = session.run(query, id=learning_point_id)
        record = result.single()
        
        if record:
            lp = record["lp"]
            lp_dict = dict(lp)
            # Parse metadata JSON string back to dict
            if 'metadata' in lp_dict and isinstance(lp_dict['metadata'], str):
                try:
                    lp_dict['metadata'] = json.loads(lp_dict['metadata'])
                except (json.JSONDecodeError, TypeError):
                    lp_dict['metadata'] = {}
            return lp_dict
        return None


def get_learning_point_by_word(conn: Neo4jConnection, word: str) -> Optional[Dict[str, Any]]:
    """
    Get a LearningPoint by word.
    
    Args:
        conn: Neo4jConnection instance
        word: The word/phrase
        
    Returns:
        Dictionary with learning point data or None if not found
    """
    query = """
    MATCH (lp:LearningPoint {word: $word})
    RETURN lp
    """
    
    with conn.get_session() as session:
        result = session.run(query, word=word)
        record = result.single()
        
        if record:
            lp = record["lp"]
            lp_dict = dict(lp)
            # Parse metadata JSON string back to dict
            if 'metadata' in lp_dict and isinstance(lp_dict['metadata'], str):
                try:
                    lp_dict['metadata'] = json.loads(lp_dict['metadata'])
                except (json.JSONDecodeError, TypeError):
                    lp_dict['metadata'] = {}
            return lp_dict
        return None


def update_learning_point(conn: Neo4jConnection, learning_point_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update a LearningPoint node.
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the learning point to update
        updates: Dictionary of fields to update
        
    Returns:
        True if successful, False otherwise
    """
    # Build SET clause dynamically
    set_clauses = []
    for key in updates.keys():
        set_clauses.append(f"lp.{key} = ${key}")
    
    query = f"""
    MATCH (lp:LearningPoint {{id: $id}})
    SET {', '.join(set_clauses)}
    RETURN lp.id as id
    """
    
    with conn.get_session() as session:
        try:
            # Convert metadata dict to JSON string if present
            params = {"id": learning_point_id}
            for key, value in updates.items():
                if key == 'metadata' and isinstance(value, dict):
                    params[key] = json.dumps(value)
                else:
                    params[key] = value
            
            result = session.run(query, **params)
            record = result.single()
            return record is not None
        except Exception as e:
            print(f"Error updating learning point: {e}")
            return False


def delete_learning_point(conn: Neo4jConnection, learning_point_id: str) -> bool:
    """
    Delete a LearningPoint node and all its relationships.
    
    Args:
        conn: Neo4jConnection instance
        learning_point_id: ID of the learning point to delete
        
    Returns:
        True if successful, False otherwise
    """
    query = """
    MATCH (lp:LearningPoint {id: $id})
    DETACH DELETE lp
    RETURN count(lp) as deleted_count
    """
    
    with conn.get_session() as session:
        try:
            result = session.run(query, id=learning_point_id)
            record = result.single()
            return record["deleted_count"] > 0
        except Exception as e:
            print(f"Error deleting learning point: {e}")
            return False


def list_learning_points(
    conn: Neo4jConnection,
    limit: int = 100,
    offset: int = 0,
    tier: Optional[int] = None,
    difficulty: Optional[str] = None,
    type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List LearningPoints with optional filters.
    
    Args:
        conn: Neo4jConnection instance
        limit: Maximum number of results
        offset: Number of results to skip
        tier: Filter by tier (optional)
        difficulty: Filter by difficulty (optional)
        type: Filter by type (optional)
        
    Returns:
        List of learning point dictionaries
    """
    # Build WHERE clause
    where_clauses = []
    if tier:
        where_clauses.append("lp.tier = $tier")
    if difficulty:
        where_clauses.append("lp.difficulty = $difficulty")
    if type:
        where_clauses.append("lp.type = $type")
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"""
    MATCH (lp:LearningPoint)
    {where_clause}
    RETURN lp
    ORDER BY lp.frequency_rank
    SKIP $offset
    LIMIT $limit
    """
    
    with conn.get_session() as session:
        params = {"limit": limit, "offset": offset}
        if tier:
            params["tier"] = tier
        if difficulty:
            params["difficulty"] = difficulty
        if type:
            params["type"] = type
        
        result = session.run(query, **params)
        learning_points = []
        for record in result:
            lp_dict = dict(record["lp"])
            # Parse metadata JSON string back to dict
            if 'metadata' in lp_dict and isinstance(lp_dict['metadata'], str):
                try:
                    lp_dict['metadata'] = json.loads(lp_dict['metadata'])
                except (json.JSONDecodeError, TypeError):
                    lp_dict['metadata'] = {}
            learning_points.append(lp_dict)
        return learning_points

