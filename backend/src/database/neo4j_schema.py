"""
Neo4j Schema Initialization

Creates constraints and indexes for the Learning Point Cloud.
"""
from .neo4j_connection import Neo4jConnection


def create_constraints(conn: Neo4jConnection) -> dict:
    """
    Create all constraints for LearningPoint nodes.
    
    Args:
        conn: Neo4jConnection instance
        
    Returns:
        Dictionary with constraint creation results
    """
    results = {}
    
    constraints = [
        {
            "name": "learning_point_id",
            "query": """
            CREATE CONSTRAINT learning_point_id IF NOT EXISTS
            FOR (lp:LearningPoint) REQUIRE lp.id IS UNIQUE
            """
        }
        # Note: word is NOT unique - multiple learning points can share the same word
        # (different meanings, POS, tiers)
    ]
    
    with conn.get_session() as session:
        for constraint in constraints:
            try:
                result = session.run(constraint["query"])
                result.consume()  # Consume the result to execute the query
                results[constraint["name"]] = "created or already exists"
            except Exception as e:
                results[constraint["name"]] = f"error: {str(e)}"
    
    return results


def create_indexes(conn: Neo4jConnection) -> dict:
    """
    Create indexes for better query performance.
    
    Args:
        conn: Neo4jConnection instance
        
    Returns:
        Dictionary with index creation results
    """
    results = {}
    
    indexes = [
        {
            "name": "learning_point_word",
            "query": """
            CREATE INDEX learning_point_word IF NOT EXISTS
            FOR (lp:LearningPoint) ON (lp.word)
            """
        },
        {
            "name": "learning_point_tier",
            "query": """
            CREATE INDEX learning_point_tier IF NOT EXISTS
            FOR (lp:LearningPoint) ON (lp.tier)
            """
        },
        {
            "name": "learning_point_difficulty",
            "query": """
            CREATE INDEX learning_point_difficulty IF NOT EXISTS
            FOR (lp:LearningPoint) ON (lp.difficulty)
            """
        },
        {
            "name": "learning_point_type",
            "query": """
            CREATE INDEX learning_point_type IF NOT EXISTS
            FOR (lp:LearningPoint) ON (lp.type)
            """
        }
    ]
    
    with conn.get_session() as session:
        for index in indexes:
            try:
                result = session.run(index["query"])
                result.consume()
                results[index["name"]] = "created or already exists"
            except Exception as e:
                results[index["name"]] = f"error: {str(e)}"
    
    return results


def initialize_schema(conn: Neo4jConnection) -> dict:
    """
    Initialize the complete Neo4j schema (constraints + indexes).
    
    Args:
        conn: Neo4jConnection instance
        
    Returns:
        Dictionary with all initialization results
    """
    print("Creating constraints...")
    constraints_result = create_constraints(conn)
    
    print("Creating indexes...")
    indexes_result = create_indexes(conn)
    
    return {
        "constraints": constraints_result,
        "indexes": indexes_result
    }


if __name__ == "__main__":
    # Test schema initialization
    from .neo4j_connection import Neo4jConnection
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            print("✓ Connection verified")
            results = initialize_schema(conn)
            print("\nSchema initialization results:")
            print(f"Constraints: {results['constraints']}")
            print(f"Indexes: {results['indexes']}")
        else:
            print("✗ Connection verification failed")
    finally:
        conn.close()

