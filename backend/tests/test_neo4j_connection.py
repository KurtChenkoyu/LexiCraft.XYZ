"""
Test Neo4j Connection

Tests basic connectivity and schema initialization.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import Neo4jConnection
from src.database.neo4j_schema import initialize_schema


def test_connection():
    """Test basic Neo4j connection."""
    print("Testing Neo4j connection...")
    
    try:
        conn = Neo4jConnection()
        
        if conn.verify_connectivity():
            print("✓ Connection successful!")
            return True
        else:
            print("✗ Connection verification failed")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def test_schema_initialization():
    """Test schema initialization (constraints and indexes)."""
    print("\nTesting schema initialization...")
    
    try:
        conn = Neo4jConnection()
        
        if not conn.verify_connectivity():
            print("✗ Cannot initialize schema: connection failed")
            return False
        
        results = initialize_schema(conn)
        
        print("\nSchema initialization results:")
        print(f"  Constraints: {results['constraints']}")
        print(f"  Indexes: {results['indexes']}")
        
        # Check if all constraints were created successfully
        constraints_ok = all(
            "error" not in str(v).lower() 
            for v in results['constraints'].values()
        )
        
        indexes_ok = all(
            "error" not in str(v).lower() 
            for v in results['indexes'].values()
        )
        
        if constraints_ok and indexes_ok:
            print("✓ Schema initialization successful!")
            return True
        else:
            print("✗ Some schema elements failed to initialize")
            return False
            
    except Exception as e:
        print(f"✗ Schema initialization error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Neo4j Connection and Schema Tests")
    print("=" * 50)
    
    connection_ok = test_connection()
    schema_ok = test_schema_initialization() if connection_ok else False
    
    print("\n" + "=" * 50)
    if connection_ok and schema_ok:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)

