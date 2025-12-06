#!/usr/bin/env python3
"""Quick Neo4j setup test that avoids PostgreSQL imports."""
import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Import directly from file path to avoid package __init__
import importlib.util

# Load neo4j_connection module directly
spec = importlib.util.spec_from_file_location(
    "neo4j_connection",
    os.path.join(src_path, "database", "neo4j_connection.py")
)
neo4j_connection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neo4j_connection)
Neo4jConnection = neo4j_connection.Neo4jConnection

# Load neo4j_schema module directly
spec = importlib.util.spec_from_file_location(
    "neo4j_schema",
    os.path.join(src_path, "database", "neo4j_schema.py")
)
neo4j_schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neo4j_schema)
initialize_schema = neo4j_schema.initialize_schema

def main():
    print("=" * 60)
    print("Neo4j Setup Test")
    print("=" * 60)
    print()
    
    print("Testing connection...")
    conn = Neo4jConnection()
    
    if conn.verify_connectivity():
        print("✓ Connection successful!")
        print()
        
        print("Initializing schema...")
        results = initialize_schema(conn)
        
        print()
        print("Schema initialization results:")
        print("  Constraints:")
        for name, result in results['constraints'].items():
            status = "✓" if "error" not in str(result).lower() else "✗"
            print(f"    {status} {name}: {result}")
        
        print("  Indexes:")
        for name, result in results['indexes'].items():
            status = "✓" if "error" not in str(result).lower() else "✗"
            print(f"    {status} {name}: {result}")
        
        print()
        print("=" * 60)
        print("✓ Setup complete!")
        print("=" * 60)
        conn.close()
        return 0
    else:
        print("✗ Connection verification failed")
        print("  Please check your .env file and Neo4j credentials")
        conn.close()
        return 1

if __name__ == "__main__":
    sys.exit(main())

