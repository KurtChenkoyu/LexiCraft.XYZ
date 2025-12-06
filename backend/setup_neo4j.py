#!/usr/bin/env python3
"""
Neo4j Setup Script

This script helps set up and verify the Neo4j connection and schema.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.neo4j_connection import Neo4jConnection
from src.database.neo4j_schema import initialize_schema


def main():
    """Main setup function."""
    print("=" * 60)
    print("Neo4j Setup for LexiCraft MVP")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("Checking environment variables...")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, user, password]):
        print("✗ Missing environment variables!")
        print()
        print("Please set the following environment variables:")
        print("  - NEO4J_URI (e.g., neo4j+s://xxxxx.databases.neo4j.io)")
        print("  - NEO4J_USER (usually 'neo4j')")
        print("  - NEO4J_PASSWORD (your Neo4j password)")
        print()
        print("Or create a .env file in the backend/ directory with:")
        print("  NEO4J_URI=your_uri_here")
        print("  NEO4J_USER=neo4j")
        print("  NEO4J_PASSWORD=your_password_here")
        print()
        return 1
    
    print("✓ Environment variables found")
    print()
    
    # Test connection
    print("Testing connection to Neo4j...")
    try:
        conn = Neo4jConnection()
        
        if conn.verify_connectivity():
            print("✓ Connection successful!")
            print()
        else:
            print("✗ Connection verification failed")
            print("  Please check your connection details.")
            conn.close()
            return 1
        
        # Initialize schema
        print("Initializing schema (constraints and indexes)...")
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
        print()
        print("Next steps:")
        print("  1. Run tests: python tests/test_neo4j_connection.py")
        print("  2. Run CRUD tests: python tests/test_neo4j_crud.py")
        print("  3. Run relationship tests: python tests/test_neo4j_relationships.py")
        print()
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"✗ Error during setup: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Verify your Neo4j URI is correct")
        print("  2. Check that your Neo4j instance is running")
        print("  3. Ensure your IP is whitelisted (for Aura)")
        print("  4. Verify your username and password are correct")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

