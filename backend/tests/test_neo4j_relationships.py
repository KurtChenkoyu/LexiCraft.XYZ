"""
Test Neo4j Relationship Queries

Tests relationship creation and querying operations.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import Neo4jConnection
from src.database.neo4j_crud import (
    create_learning_point,
    delete_learning_point,
    create_relationship,
    get_prerequisites,
    get_collocations,
    get_related_points,
    get_components_within_degrees,
    discover_relationships,
    get_all_relationships,
)
from src.models.learning_point import LearningPoint, RelationshipType


def setup_test_data(conn: Neo4jConnection):
    """Create test learning points for relationship testing."""
    test_points = [
        LearningPoint(
            id="base_word",
            word="base",
            type="word",
            tier=1,
            definition="Foundation or starting point",
            example="The base of the mountain",
            frequency_rank=500,
            difficulty="A1",
            register="both",
            contexts=["general"]
        ),
        LearningPoint(
            id="basic_word",
            word="basic",
            type="word",
            tier=1,
            definition="Simple or fundamental",
            example="Basic knowledge",
            frequency_rank=600,
            difficulty="A1",
            register="both",
            contexts=["general"]
        ),
        LearningPoint(
            id="advanced_word",
            word="advanced",
            type="word",
            tier=3,
            definition="Complex or sophisticated",
            example="Advanced techniques",
            frequency_rank=800,
            difficulty="B2",
            register="both",
            contexts=["academic"]
        ),
        LearningPoint(
            id="fundamental_word",
            word="fundamental",
            type="word",
            tier=2,
            definition="Essential or basic",
            example="Fundamental principles",
            frequency_rank=700,
            difficulty="B1",
            register="formal",
            contexts=["academic"]
        )
    ]
    
    for lp in test_points:
        create_learning_point(conn, lp)


def cleanup_test_data(conn: Neo4jConnection):
    """Clean up test learning points."""
    test_ids = ["base_word", "basic_word", "advanced_word", "fundamental_word"]
    for test_id in test_ids:
        delete_learning_point(conn, test_id)


def test_create_relationships():
    """Test creating relationships between learning points."""
    print("Testing relationship creation...")
    
    conn = Neo4jConnection()
    
    try:
        setup_test_data(conn)
        
        # Create PREREQUISITE_OF relationship
        created = create_relationship(
            conn,
            "base_word",
            "advanced_word",
            RelationshipType.PREREQUISITE_OF
        )
        if not created:
            print("✗ Failed to create PREREQUISITE_OF relationship")
            return False
        print("✓ PREREQUISITE_OF relationship created")
        
        # Create COLLOCATES_WITH relationship
        created = create_relationship(
            conn,
            "base_word",
            "basic_word",
            RelationshipType.COLLOCATES_WITH
        )
        if not created:
            print("✗ Failed to create COLLOCATES_WITH relationship")
            return False
        print("✓ COLLOCATES_WITH relationship created")
        
        # Create RELATED_TO relationship
        created = create_relationship(
            conn,
            "basic_word",
            "fundamental_word",
            RelationshipType.RELATED_TO
        )
        if not created:
            print("✗ Failed to create RELATED_TO relationship")
            return False
        print("✓ RELATED_TO relationship created")
        
        # Create MORPHOLOGICAL relationship with properties
        created = create_relationship(
            conn,
            "base_word",
            "basic_word",
            RelationshipType.MORPHOLOGICAL,
            properties={"type": "root"}
        )
        if not created:
            print("✗ Failed to create MORPHOLOGICAL relationship")
            return False
        print("✓ MORPHOLOGICAL relationship created")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in relationship creation test: {e}")
        return False
    finally:
        cleanup_test_data(conn)
        conn.close()


def test_prerequisites_query():
    """Test querying prerequisites."""
    print("\nTesting prerequisites query...")
    
    conn = Neo4jConnection()
    
    try:
        setup_test_data(conn)
        create_relationship(
            conn,
            "base_word",
            "advanced_word",
            RelationshipType.PREREQUISITE_OF
        )
        
        prerequisites = get_prerequisites(conn, "advanced_word")
        if len(prerequisites) == 0:
            print("✗ No prerequisites found")
            return False
        if prerequisites[0]["id"] != "base_word":
            print("✗ Wrong prerequisite returned")
            return False
        print(f"✓ Found {len(prerequisites)} prerequisite(s)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in prerequisites query test: {e}")
        return False
    finally:
        cleanup_test_data(conn)
        conn.close()


def test_collocations_query():
    """Test querying collocations."""
    print("\nTesting collocations query...")
    
    conn = Neo4jConnection()
    
    try:
        setup_test_data(conn)
        create_relationship(
            conn,
            "base_word",
            "basic_word",
            RelationshipType.COLLOCATES_WITH
        )
        
        collocations = get_collocations(conn, "base_word")
        if len(collocations) == 0:
            print("✗ No collocations found")
            return False
        print(f"✓ Found {len(collocations)} collocation(s)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in collocations query test: {e}")
        return False
    finally:
        cleanup_test_data(conn)
        conn.close()


def test_related_points_query():
    """Test querying related points."""
    print("\nTesting related points query...")
    
    conn = Neo4jConnection()
    
    try:
        setup_test_data(conn)
        create_relationship(
            conn,
            "basic_word",
            "fundamental_word",
            RelationshipType.RELATED_TO
        )
        
        related = get_related_points(conn, "basic_word")
        if len(related) == 0:
            print("✗ No related points found")
            return False
        print(f"✓ Found {len(related)} related point(s)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in related points query test: {e}")
        return False
    finally:
        cleanup_test_data(conn)
        conn.close()


def test_components_within_degrees():
    """Test finding components within N degrees."""
    print("\nTesting components within degrees query...")
    
    conn = Neo4jConnection()
    
    try:
        setup_test_data(conn)
        # Create a chain: base -> basic -> fundamental
        create_relationship(
            conn,
            "base_word",
            "basic_word",
            RelationshipType.RELATED_TO
        )
        create_relationship(
            conn,
            "basic_word",
            "fundamental_word",
            RelationshipType.RELATED_TO
        )
        
        components = get_components_within_degrees(conn, "base_word", max_degrees=2)
        if len(components) == 0:
            print("✗ No components found within degrees")
            return False
        print(f"✓ Found {len(components)} component(s) within 2 degrees")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in components within degrees test: {e}")
        return False
    finally:
        cleanup_test_data(conn)
        conn.close()


def test_discover_relationships():
    """Test relationship discovery query."""
    print("\nTesting relationship discovery query...")
    
    conn = Neo4jConnection()
    
    try:
        setup_test_data(conn)
        create_relationship(
            conn,
            "base_word",
            "basic_word",
            RelationshipType.RELATED_TO
        )
        
        # Simulate user knows "basic_word" and learns "base_word"
        discoveries = discover_relationships(
            conn,
            "base_word",
            ["basic_word"]
        )
        if len(discoveries) == 0:
            print("✗ No relationships discovered")
            return False
        print(f"✓ Discovered {len(discoveries)} relationship(s)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in relationship discovery test: {e}")
        return False
    finally:
        cleanup_test_data(conn)
        conn.close()


def test_get_all_relationships():
    """Test getting all relationships for a learning point."""
    print("\nTesting get all relationships query...")
    
    conn = Neo4jConnection()
    
    try:
        setup_test_data(conn)
        create_relationship(
            conn,
            "base_word",
            "basic_word",
            RelationshipType.RELATED_TO
        )
        create_relationship(
            conn,
            "advanced_word",
            "base_word",
            RelationshipType.PREREQUISITE_OF
        )
        
        all_rels = get_all_relationships(conn, "base_word")
        if len(all_rels) == 0:
            print("✗ No relationships found")
            return False
        print(f"✓ Found {len(all_rels)} relationship(s)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in get all relationships test: {e}")
        return False
    finally:
        cleanup_test_data(conn)
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Neo4j Relationship Query Tests")
    print("=" * 50)
    
    results = []
    
    results.append(("CREATE RELATIONSHIPS", test_create_relationships()))
    results.append(("PREREQUISITES", test_prerequisites_query()))
    results.append(("COLLOCATIONS", test_collocations_query()))
    results.append(("RELATED POINTS", test_related_points_query()))
    results.append(("COMPONENTS WITHIN DEGREES", test_components_within_degrees()))
    results.append(("DISCOVER RELATIONSHIPS", test_discover_relationships()))
    results.append(("GET ALL RELATIONSHIPS", test_get_all_relationships()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✓ All relationship tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some relationship tests failed")
        sys.exit(1)

