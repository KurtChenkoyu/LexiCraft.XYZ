#!/usr/bin/env python3
"""
Populate Relationships between Learning Points

Creates relationships (synonyms, antonyms) between learning points using WordNet.

Usage:
    python populate_relationships.py [--limit N] [--type synonyms|antonyms|all]
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import nltk
from nltk.corpus import wordnet as wn
from src.database.neo4j_connection import Neo4jConnection
from src.database.neo4j_crud.learning_points import list_learning_points, get_learning_point
from src.database.neo4j_crud.relationships import create_relationship
from src.models.learning_point import RelationshipType

# Download NLTK data if needed
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading WordNet data...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)


def get_synonyms_from_synset(synset):
    """Get all synonyms (lemmas) from a synset."""
    return [lemma.name().replace('_', ' ') for lemma in synset.lemmas()]


def get_antonyms_from_synset(synset):
    """Get all antonyms from a synset."""
    antonyms = []
    for lemma in synset.lemmas():
        for antonym in lemma.antonyms():
            antonyms.append(antonym.name().replace('_', ' '))
    return antonyms


def find_learning_point_ids_for_word(conn, word):
    """Find all learning point IDs for a given word."""
    # Use a more efficient query - get all learning points with this word
    # Note: We'll need to query all and filter, or we could add a query function
    learning_points = list_learning_points(conn, limit=10000)
    return [lp['id'] for lp in learning_points if lp.get('word', '').lower() == word.lower()]


def create_synonym_relationships(conn, learning_point, limit=None):
    """
    Create RELATED_TO relationships for synonyms.
    
    Args:
        conn: Neo4j connection
        learning_point: Learning point dictionary
        limit: Limit number of relationships to create (None for all)
        
    Returns:
        Number of relationships created
    """
    word = learning_point['word']
    lp_id = learning_point['id']
    
    # Get synset from metadata
    import json
    metadata = learning_point.get('metadata', {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}
    
    synset_id = metadata.get('synset_id')
    if not synset_id:
        return 0
    
    try:
        synset = wn.synset(synset_id)
    except Exception as e:
        return 0
    
    # Get synonyms
    synonyms = get_synonyms_from_synset(synset)
    
    # Remove the word itself
    synonyms = [s for s in synonyms if s.lower() != word.lower()]
    
    if not synonyms:
        return 0
    
    if limit:
        synonyms = synonyms[:limit]
    
    relationships_created = 0
    
    for synonym_word in synonyms:
        # Find learning points for this synonym
        synonym_ids = find_learning_point_ids_for_word(conn, synonym_word)
        
        if not synonym_ids:
            # Synonym word not in our database, skip
            continue
        
        for synonym_id in synonym_ids:
            # Skip self-relationships
            if synonym_id == lp_id:
                continue
            
            # Create RELATED_TO relationship (skip if already exists)
            try:
                if create_relationship(
                    conn,
                    lp_id,
                    synonym_id,
                    RelationshipType.RELATED_TO,
                    properties={"source": "wordnet", "type": "synonym"}
                ):
                    relationships_created += 1
            except Exception as e:
                # Relationship might already exist, skip silently
                # Only log if it's not a duplicate error
                error_str = str(e).lower()
                if "already exists" not in error_str and "duplicate" not in error_str:
                    pass  # Could log here if needed
    
    return relationships_created


def create_antonym_relationships(conn, learning_point, limit=None):
    """
    Create OPPOSITE_OF relationships for antonyms.
    
    Args:
        conn: Neo4j connection
        learning_point: Learning point dictionary
        limit: Limit number of relationships to create (None for all)
        
    Returns:
        Number of relationships created
    """
    word = learning_point['word']
    lp_id = learning_point['id']
    
    # Get synset from metadata
    import json
    metadata = learning_point.get('metadata', {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except:
            metadata = {}
    
    synset_id = metadata.get('synset_id')
    if not synset_id:
        return 0
    
    try:
        synset = wn.synset(synset_id)
    except Exception as e:
        return 0
    
    # Get antonyms
    antonyms = get_antonyms_from_synset(synset)
    
    if not antonyms:
        return 0
    
    if limit:
        antonyms = antonyms[:limit]
    
    relationships_created = 0
    
    for antonym_word in antonyms:
        # Find learning points for this antonym
        antonym_ids = find_learning_point_ids_for_word(conn, antonym_word)
        
        if not antonym_ids:
            # Antonym word not in our database, skip
            continue
        
        for antonym_id in antonym_ids:
            # Skip self-relationships
            if antonym_id == lp_id:
                continue
            
            # Create OPPOSITE_OF relationship (skip if already exists)
            try:
                if create_relationship(
                    conn,
                    lp_id,
                    antonym_id,
                    RelationshipType.OPPOSITE_OF,
                    properties={"source": "wordnet", "type": "antonym"}
                ):
                    relationships_created += 1
            except Exception as e:
                # Relationship might already exist, skip silently
                error_str = str(e).lower()
                if "already exists" not in error_str and "duplicate" not in error_str:
                    pass  # Could log here if needed
    
    return relationships_created


def populate_relationships(conn, relationship_type="all", limit=None, word_limit=None):
    """
    Populate relationships for all learning points.
    
    Args:
        conn: Neo4j connection
        relationship_type: "synonyms", "antonyms", or "all"
        limit: Limit relationships per learning point (None for all)
        word_limit: Limit number of learning points to process (None for all)
        
    Returns:
        Dictionary with counts
    """
    # Get all learning points
    print("Loading learning points...")
    learning_points = list_learning_points(conn, limit=10000)
    
    if word_limit:
        learning_points = learning_points[:word_limit]
    
    print(f"Processing {len(learning_points)} learning points...")
    print()
    
    total_synonyms = 0
    total_antonyms = 0
    processed = 0
    
    for i, lp in enumerate(learning_points, start=1):
        try:
            synonyms_created = 0
            antonyms_created = 0
            
            if relationship_type in ["synonyms", "all"]:
                synonyms_created = create_synonym_relationships(conn, lp, limit)
                total_synonyms += synonyms_created
            
            if relationship_type in ["antonyms", "all"]:
                antonyms_created = create_antonym_relationships(conn, lp, limit)
                total_antonyms += antonyms_created
            
            if synonyms_created > 0 or antonyms_created > 0:
                print(f"[{i}/{len(learning_points)}] {lp['word']}: "
                      f"synonyms={synonyms_created}, antonyms={antonyms_created}")
            
            processed += 1
            
            # Progress update every 100 learning points
            if i % 100 == 0:
                print(f"\nProgress: {i}/{len(learning_points)} processed")
                print(f"  Total synonyms: {total_synonyms}, Total antonyms: {total_antonyms}\n")
                
        except Exception as e:
            print(f"[{i}/{len(learning_points)}] {lp.get('word', 'unknown')}: ERROR - {e}")
            continue
    
    return {
        "processed": processed,
        "synonyms": total_synonyms,
        "antonyms": total_antonyms
    }


def main():
    parser = argparse.ArgumentParser(description='Populate relationships between learning points')
    parser.add_argument(
        '--type',
        type=str,
        choices=['synonyms', 'antonyms', 'all'],
        default='all',
        help='Type of relationships to create (default: all)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of relationships per learning point (default: all)'
    )
    parser.add_argument(
        '--word-limit',
        type=int,
        default=None,
        help='Limit number of learning points to process (for testing)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("RELATIONSHIP POPULATION")
    print("="*60)
    print(f"Relationship type: {args.type}")
    if args.limit:
        print(f"Relationships per LP limit: {args.limit}")
    if args.word_limit:
        print(f"Learning points limit: {args.word_limit}")
    print()
    
    # Connect to Neo4j
    try:
        conn = Neo4jConnection()
        if not conn.verify_connectivity():
            print("Error: Failed to connect to Neo4j")
            sys.exit(1)
        print("Connected to Neo4j")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        sys.exit(1)
    
    # Populate relationships
    results = populate_relationships(
        conn,
        relationship_type=args.type,
        limit=args.limit,
        word_limit=args.word_limit
    )
    
    # Final summary
    print("\n" + "="*60)
    print("RELATIONSHIP POPULATION COMPLETE")
    print("="*60)
    print(f"Learning points processed: {results['processed']}")
    print(f"Synonym relationships created: {results['synonyms']}")
    print(f"Antonym relationships created: {results['antonyms']}")
    print(f"Total relationships: {results['synonyms'] + results['antonyms']}")
    print("="*60)
    
    conn.close()


if __name__ == "__main__":
    main()

