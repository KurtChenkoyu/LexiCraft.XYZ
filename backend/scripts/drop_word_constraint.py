#!/usr/bin/env python3
"""
Drop the unique constraint on word field.

This allows multiple learning points to share the same word
(different meanings, POS, tiers).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection


def drop_word_constraint(conn: Neo4jConnection) -> bool:
    """Drop the unique constraint on word field."""
    query = """
    DROP CONSTRAINT learning_point_word IF EXISTS
    """
    
    with conn.get_session() as session:
        try:
            result = session.run(query)
            result.consume()
            return True
        except Exception as e:
            print(f"Error dropping constraint: {e}")
            return False


if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            print("Dropping unique constraint on word field...")
            if drop_word_constraint(conn):
                print("✓ Constraint dropped successfully")
            else:
                print("✗ Failed to drop constraint")
        else:
            print("✗ Connection verification failed")
    finally:
        conn.close()


