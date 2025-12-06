import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.neo4j_connection import Neo4jConnection

def reset_schema(conn: Neo4jConnection):
    """Drop all constraints and indexes."""
    print("Resetting schema...")
    with conn.get_session() as session:
        # Get all constraints
        result = session.run("SHOW CONSTRAINTS")
        constraints = [record["name"] for record in result]
        for name in constraints:
            print(f"Dropping constraint: {name}")
            session.run(f"DROP CONSTRAINT {name} IF EXISTS")
            
        # Get all indexes
        result = session.run("SHOW INDEXES")
        indexes = [record["name"] for record in result if record["type"] != "LOOKUP"]
        for name in indexes:
            print(f"Dropping index: {name}")
            session.run(f"DROP INDEX {name} IF EXISTS")
            
        # Delete all data
        print("Deleting all data...")
        session.run("MATCH (n) DETACH DELETE n")
        
    print("Schema reset complete.")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            reset_schema(conn)
        else:
            print("Connection failed.")
    finally:
        conn.close()

