"""
Morphological Relationship Miner - Finds word families and prefix/suffix relationships.

Uses WordNet's derivationally_related_forms() to find:
- Word families (happy → happiness, happily, unhappy)
- Prefix relationships (direct → indirect, redirect)
- Suffix relationships (care → careful, careless, carefully)

Schema:
(:Word)-[:DERIVED_FROM]->(:Word)  // Word families
(:Word)-[:HAS_PREFIX {prefix: "un-"}]->(:Word)  // Prefix relationships
(:Word)-[:HAS_SUFFIX {suffix: "-ness"}]->(:Word)  // Suffix relationships
"""

import nltk
import time
import re
from nltk.corpus import wordnet as wn
from src.database.neo4j_connection import Neo4jConnection
from typing import Dict, List, Optional, Set, Tuple

# Ensure WordNet is downloaded
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading WordNet...")
    nltk.download('wordnet')
    nltk.download('omw-1.4')

# Common prefixes and suffixes for detection
COMMON_PREFIXES = {
    'un', 'in', 'im', 'il', 'ir', 'dis', 'mis', 're', 'pre', 'post',
    'anti', 'de', 'en', 'em', 'non', 'over', 'out', 'sub', 'super',
    'trans', 'under', 'up', 'co', 'ex', 'pro', 'auto', 'inter', 'intra'
}

COMMON_SUFFIXES = {
    'ness', 'ly', 'tion', 'sion', 'ing', 'ed', 'er', 'est', 'ful', 'less',
    'able', 'ible', 'al', 'ic', 'ical', 'ous', 'ious', 'ive', 'ment',
    'ity', 'ty', 'ism', 'ist', 'ize', 'ise', 'fy', 'en', 'ify'
}


def detect_prefix(word1: str, word2: str) -> Optional[str]:
    """Detect if word2 has a prefix from word1."""
    word1_lower = word1.lower()
    word2_lower = word2.lower()
    
    # Check if word2 starts with word1 + prefix
    for prefix in COMMON_PREFIXES:
        if word2_lower.startswith(prefix) and word2_lower[len(prefix):] == word1_lower:
            return prefix
        # Also check if word1 + prefix = word2
        if word1_lower + prefix == word2_lower:
            return prefix
    
    return None


def detect_suffix(word1: str, word2: str) -> Optional[str]:
    """Detect if word2 has a suffix added to word1."""
    word1_lower = word1.lower()
    word2_lower = word2.lower()
    
    # Check if word2 = word1 + suffix
    for suffix in COMMON_SUFFIXES:
        if word2_lower == word1_lower + suffix:
            return suffix
        # Also check if word2 ends with suffix and starts with word1
        if word2_lower.endswith(suffix) and word2_lower[:-len(suffix)] == word1_lower:
            return suffix
    
    return None


def get_morphological_relationships(word: str) -> Dict[str, List[Dict]]:
    """
    Get morphological relationships for a word using WordNet.
    
    Returns:
        {
            "derived_from": [{"target_word": "...", "relationship": "..."}],
            "prefixes": [{"target_word": "...", "prefix": "un-"}],
            "suffixes": [{"target_word": "...", "suffix": "-ness"}]
        }
    """
    relationships = {
        "derived_from": [],
        "prefixes": [],
        "suffixes": []
    }
    
    seen_targets = set()
    
    # Get all synsets for the word
    synsets = wn.synsets(word)
    if not synsets:
        return relationships
    
    # Check all lemmas in all synsets
    for syn in synsets:
        for lemma in syn.lemmas():
            # Get derivationally related forms
            derived_forms = lemma.derivationally_related_forms()
            
            for derived_lemma in derived_forms:
                target_word = derived_lemma.name().lower().replace('_', ' ')
                
                # Skip self
                if target_word == word.lower():
                    continue
                
                # Skip if already processed
                if target_word in seen_targets:
                    continue
                seen_targets.add(target_word)
                
                # Detect prefix relationship
                prefix = detect_prefix(word, target_word)
                if prefix:
                    relationships["prefixes"].append({
                        "target_word": target_word,
                        "prefix": prefix
                    })
                    continue
                
                # Detect suffix relationship
                suffix = detect_suffix(word, target_word)
                if suffix:
                    relationships["suffixes"].append({
                        "target_word": target_word,
                        "suffix": suffix
                    })
                    continue
                
                # Otherwise, it's a general derivation (word family)
                relationships["derived_from"].append({
                    "target_word": target_word,
                    "relationship": "derivationally_related"
                })
    
    return relationships


def run_morphological_miner(
    conn: Neo4jConnection,
    batch_size: int = 50,
    rate_limit_delay: float = 2.5,
    limit: Optional[int] = None
):
    """
    Create morphological relationships between words.
    
    Optimized for Neo4j Aura Free tier (25 requests/minute):
    - Batches operations to reduce query count
    - Adds rate limiting delays
    
    Creates:
    - (:Word)-[:DERIVED_FROM]->(:Word) for word families
    - (:Word)-[:HAS_PREFIX {prefix: "un-"}]->(:Word) for prefixes
    - (:Word)-[:HAS_SUFFIX {suffix: "-ness"}]->(:Word) for suffixes
    
    Args:
        conn: Neo4j connection
        batch_size: Number of relationships to batch per query
        rate_limit_delay: Seconds to wait between batches (default 2.5s for ~24 req/min)
        limit: Optional limit on number of words to process (for testing)
    """
    print("🔤 Starting Morphological Relationship Mining...")
    print(f"   Batch size: {batch_size}")
    print(f"   Rate limit delay: {rate_limit_delay}s (respecting 25 req/min limit)")
    print(f"   Using new session per batch (prevents timeout)")
    
    # Fetch all Words (single query, then close session)
    print("   Fetching words...")
    with conn.get_session() as session:
        query = """
            MATCH (w:Word)
            RETURN w.name as word
            ORDER BY w.frequency_rank
        """
        if limit:
            query += f" LIMIT {limit}"
        
        result = session.run(query)
        words = [record["word"] for record in result]
    
    print(f"   Processing {len(words)} words...")
    
    rel_counts = {
        "DERIVED_FROM": 0,
        "HAS_PREFIX": 0,
        "HAS_SUFFIX": 0
    }
    
    # Collect all relationships first (in-memory, no DB queries)
    all_relationships = []
    processed = 0
    
    for word in words:
        # Get morphological relationships (WordNet only, no DB)
        morph_rels = get_morphological_relationships(word)
        
        # Add derived_from relationships
        for rel in morph_rels["derived_from"]:
            all_relationships.append({
                "source_word": word,
                "target_word": rel["target_word"],
                "rel_type": "DERIVED_FROM",
                "properties": {}
            })
        
        # Add prefix relationships
        for rel in morph_rels["prefixes"]:
            all_relationships.append({
                "source_word": word,
                "target_word": rel["target_word"],
                "rel_type": "HAS_PREFIX",
                "properties": {"prefix": rel["prefix"]}
            })
        
        # Add suffix relationships
        for rel in morph_rels["suffixes"]:
            all_relationships.append({
                "source_word": word,
                "target_word": rel["target_word"],
                "rel_type": "HAS_SUFFIX",
                "properties": {"suffix": rel["suffix"]}
            })
        
        processed += 1
        if processed % 500 == 0:
            print(f"   Analyzed {processed}/{len(words)} words, found {len(all_relationships)} relationships so far...")
    
    print(f"\n   Found {len(all_relationships)} potential relationships")
    print("   Validating and creating relationships in batches...")
    
    # Batch validate and create relationships (new session per batch)
    batch = []
    batch_num = 0
    
    for rel in all_relationships:
        batch.append(rel)
        
        if len(batch) >= batch_size:
            batch_num += 1
            # Create new session for each batch (prevents timeout)
            try:
                with conn.get_session() as batch_session:
                    created = _process_morphological_batch(batch_session, batch, rel_counts)
                print(f"   Batch {batch_num}: Created {created} relationships (total: {sum(rel_counts.values())})")
            except Exception as e:
                print(f"   Batch {batch_num}: Error - {e}, retrying...")
                time.sleep(5)  # Wait before retry
                try:
                    with conn.get_session() as batch_session:
                        created = _process_morphological_batch(batch_session, batch, rel_counts)
                    print(f"   Batch {batch_num}: Retry successful - Created {created} relationships (total: {sum(rel_counts.values())})")
                except Exception as e2:
                    print(f"   Batch {batch_num}: Retry failed - {e2}, skipping batch")
            
            batch = []
            
            # Rate limiting: wait between batches
            if batch_num % 10 == 0:  # Every 10 batches, longer pause
                time.sleep(rate_limit_delay * 2)
            else:
                time.sleep(rate_limit_delay)
    
    # Process remaining batch
    if batch:
        batch_num += 1
        try:
            with conn.get_session() as batch_session:
                created = _process_morphological_batch(batch_session, batch, rel_counts)
            print(f"   Batch {batch_num}: Created {created} relationships (total: {sum(rel_counts.values())})")
        except Exception as e:
            print(f"   Batch {batch_num}: Error - {e}, retrying...")
            time.sleep(5)
            try:
                with conn.get_session() as batch_session:
                    created = _process_morphological_batch(batch_session, batch, rel_counts)
                print(f"   Batch {batch_num}: Retry successful - Created {created} relationships (total: {sum(rel_counts.values())})")
            except Exception as e2:
                print(f"   Batch {batch_num}: Retry failed - {e2}, skipping batch")
        
        print(f"\n✅ Morphological Mining Complete.")
        print(f"   Created {rel_counts['DERIVED_FROM']} DERIVED_FROM relationships")
        print(f"   Created {rel_counts['HAS_PREFIX']} HAS_PREFIX relationships")
        print(f"   Created {rel_counts['HAS_SUFFIX']} HAS_SUFFIX relationships")
        print(f"   Total: {sum(rel_counts.values())} relationships")


def _process_morphological_batch(session, batch: List[Dict], rel_counts: Dict[str, int]) -> int:
    """
    Process a batch of morphological relationships: validate they exist, then create them.
    Returns number of relationships created.
    """
    if not batch:
        return 0
    
    # Build batch data for validation query
    batch_data = [
        {
            "source_word": rel["source_word"],
            "target_word": rel["target_word"],
            "rel_type": rel["rel_type"],
            "properties": rel["properties"]
        }
        for rel in batch
    ]
    
    # Validate all relationships exist in one query
    validation_result = session.run("""
        UNWIND $batch as rel
        MATCH (source:Word)
        WHERE toLower(source.name) = toLower(rel.source_word)
        MATCH (target:Word)
        WHERE toLower(target.name) = toLower(rel.target_word)
        WITH rel, source, target
        WHERE source <> target
        RETURN rel.source_word as source_word,
               rel.target_word as target_word,
               rel.rel_type as rel_type,
               rel.properties as properties
    """, batch=batch_data)
    
    valid_rels = list(validation_result)
    if not valid_rels:
        return 0
    
    # Group by relationship type for batch creation
    by_type = {}
    for rel in valid_rels:
        rel_type = rel["rel_type"]
        if rel_type not in by_type:
            by_type[rel_type] = []
        by_type[rel_type].append(rel)
    
    created = 0
    
    # Create relationships by type (one query per type)
    for rel_type, rels in by_type.items():
        # Build data for batch creation
        rels_with_props = []
        for rel in rels:
            props = rel["properties"] or {}
            rels_with_props.append({
                "source_word": rel["source_word"],
                "target_word": rel["target_word"],
                **props
            })
        
        # Build query based on relationship type
        if rel_type == "HAS_PREFIX":
            # HAS_PREFIX with prefix property
            create_query = f"""
                UNWIND $rels as rel
                MATCH (source:Word)
                WHERE toLower(source.name) = toLower(rel.source_word)
                MATCH (target:Word)
                WHERE toLower(target.name) = toLower(rel.target_word)
                MERGE (source)-[r:{rel_type}]->(target)
                SET r.prefix = rel.prefix,
                    r.source = "wordnet",
                    r.created_at = timestamp()
                RETURN count(r) as created
            """
        elif rel_type == "HAS_SUFFIX":
            # HAS_SUFFIX with suffix property
            create_query = f"""
                UNWIND $rels as rel
                MATCH (source:Word)
                WHERE toLower(source.name) = toLower(rel.source_word)
                MATCH (target:Word)
                WHERE toLower(target.name) = toLower(rel.target_word)
                MERGE (source)-[r:{rel_type}]->(target)
                SET r.suffix = rel.suffix,
                    r.source = "wordnet",
                    r.created_at = timestamp()
                RETURN count(r) as created
            """
        else:
            # DERIVED_FROM (no extra properties)
            create_query = f"""
                UNWIND $rels as rel
                MATCH (source:Word)
                WHERE toLower(source.name) = toLower(rel.source_word)
                MATCH (target:Word)
                WHERE toLower(target.name) = toLower(rel.target_word)
                MERGE (source)-[r:{rel_type}]->(target)
                SET r.source = "wordnet",
                    r.created_at = timestamp()
                RETURN count(r) as created
            """
        
        create_result = session.run(create_query, rels=rels_with_props)
        created_count = create_result.single()["created"]
        created += created_count
        rel_counts[rel_type] += created_count
    
    return created


if __name__ == "__main__":
    import sys
    
    limit = None
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            print(f"Invalid limit: {sys.argv[1]}, processing all words")
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            if limit:
                print(f"⚠️ TEST MODE: Processing only {limit} words")
            run_morphological_miner(conn, limit=limit)
    finally:
        conn.close()

