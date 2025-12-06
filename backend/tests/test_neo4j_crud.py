"""
Test Neo4j CRUD Operations

Tests Create, Read, Update, Delete operations for LearningPoints.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import Neo4jConnection
from src.database.neo4j_crud import (
    create_learning_point,
    get_learning_point,
    get_learning_point_by_word,
    update_learning_point,
    delete_learning_point,
    list_learning_points,
)
from src.models.learning_point import LearningPoint


def test_create_and_read():
    """Test creating and reading a learning point."""
    print("Testing CREATE and READ operations...")
    
    conn = Neo4jConnection()
    
    try:
        # Create a test learning point
        test_lp = LearningPoint(
            id="test_word_1",
            word="test word",
            type="word",
            tier=1,
            definition="A test word definition",
            example="This is a test example.",
            frequency_rank=1000,
            difficulty="A1",
            register="both",
            contexts=["test"],
            metadata={"test": True}
        )
        
        # Create
        created = create_learning_point(conn, test_lp)
        if not created:
            print("✗ Failed to create learning point")
            return False
        print("✓ Learning point created")
        
        # Read by ID
        retrieved = get_learning_point(conn, "test_word_1")
        if not retrieved:
            print("✗ Failed to retrieve learning point by ID")
            return False
        if retrieved["id"] != "test_word_1":
            print("✗ Retrieved learning point has wrong ID")
            return False
        print("✓ Learning point retrieved by ID")
        
        # Read by word
        retrieved_by_word = get_learning_point_by_word(conn, "test word")
        if not retrieved_by_word:
            print("✗ Failed to retrieve learning point by word")
            return False
        if retrieved_by_word["word"] != "test word":
            print("✗ Retrieved learning point has wrong word")
            return False
        print("✓ Learning point retrieved by word")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in CREATE/READ test: {e}")
        return False
    finally:
        conn.close()


def test_update():
    """Test updating a learning point."""
    print("\nTesting UPDATE operation...")
    
    conn = Neo4jConnection()
    
    try:
        # Update the test learning point
        updates = {
            "definition": "Updated definition",
            "tier": 2
        }
        
        updated = update_learning_point(conn, "test_word_1", updates)
        if not updated:
            print("✗ Failed to update learning point")
            return False
        print("✓ Learning point updated")
        
        # Verify update
        retrieved = get_learning_point(conn, "test_word_1")
        if retrieved["definition"] != "Updated definition":
            print("✗ Update did not persist")
            return False
        if retrieved["tier"] != 2:
            print("✗ Tier update did not persist")
            return False
        print("✓ Update verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in UPDATE test: {e}")
        return False
    finally:
        conn.close()


def test_list():
    """Test listing learning points."""
    print("\nTesting LIST operation...")
    
    conn = Neo4jConnection()
    
    try:
        # List all learning points
        all_points = list_learning_points(conn, limit=10)
        print(f"✓ Found {len(all_points)} learning points")
        
        # List by tier
        tier_points = list_learning_points(conn, limit=10, tier=1)
        print(f"✓ Found {len(tier_points)} tier 1 learning points")
        
        # List by difficulty
        difficulty_points = list_learning_points(conn, limit=10, difficulty="A1")
        print(f"✓ Found {len(difficulty_points)} A1 difficulty learning points")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in LIST test: {e}")
        return False
    finally:
        conn.close()


def test_delete():
    """Test deleting a learning point."""
    print("\nTesting DELETE operation...")
    
    conn = Neo4jConnection()
    
    try:
        # Delete the test learning point
        deleted = delete_learning_point(conn, "test_word_1")
        if not deleted:
            print("✗ Failed to delete learning point")
            return False
        print("✓ Learning point deleted")
        
        # Verify deletion
        retrieved = get_learning_point(conn, "test_word_1")
        if retrieved is not None:
            print("✗ Learning point still exists after deletion")
            return False
        print("✓ Deletion verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in DELETE test: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Neo4j CRUD Operations Tests")
    print("=" * 50)
    
    results = []
    
    results.append(("CREATE/READ", test_create_and_read()))
    results.append(("UPDATE", test_update()))
    results.append(("LIST", test_list()))
    results.append(("DELETE", test_delete()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✓ All CRUD tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some CRUD tests failed")
        sys.exit(1)

