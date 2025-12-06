"""
Improved Relationship Miner - Makes semantic relationships more meaningful.

Key improvements:
1. Sense-specific relationships (not word-level)
2. Relationship types (SYNONYM_OF, RELATED_TO, etc.)
3. Quality scoring (semantic similarity, frequency matching)
4. Relationship properties (strength, source_sense, target_sense)

Schema:
(:Sense)-[:SYNONYM_OF {strength: 0.95, source: "wordnet"}]->(:Sense)
(:Sense)-[:RELATED_TO {strength: 0.75, source: "wordnet"}]->(:Sense)
(:Word)-[:HAS_RELATIONSHIP]->(:Word)  // Aggregated view for queries
"""

import nltk
import time
from nltk.corpus import wordnet as wn
from src.database.neo4j_connection import Neo4jConnection
from typing import Dict, List, Optional, Tuple

# Ensure WordNet is downloaded
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading WordNet...")
    nltk.download('wordnet')
    nltk.download('omw-1.4')


def classify_relationship(source_syn: wn.synset, target_syn: wn.synset) -> Optional[Tuple[str, float]]:
    """
    Classify the type and strength of relationship between two synsets.
    
    Returns:
        (relationship_type, strength) or None if too weak
        relationship_type: "SYNONYM_OF", "CLOSE_SYNONYM", "RELATED_TO"
        strength: 0.0-1.0 (semantic similarity score)
    """
    # Same synset = true synonyms
    if source_syn == target_syn:
        return ("SYNONYM_OF", 1.0)
    
    # Check if synsets share lemmas (strong indicator of relationship)
    source_lemmas = {l.name().lower() for l in source_syn.lemmas()}
    target_lemmas = {l.name().lower() for l in target_syn.lemmas()}
    shared_lemmas = source_lemmas & target_lemmas
    
    # Calculate path similarity (WordNet's built-in metric)
    path_sim = source_syn.path_similarity(target_syn)
    
    # If synsets share lemmas, they're related even if path similarity is low
    # (e.g., happy.a.01 and felicitous.s.01 both have "happy" lemma)
    if shared_lemmas:
        # Shared lemmas = close relationship
        if path_sim and path_sim >= 0.8:
            return ("CLOSE_SYNONYM", path_sim)
        elif path_sim and path_sim >= 0.6:
            return ("RELATED_TO", path_sim)
        else:
            # Shared lemmas but low path sim (different POS) = still related
            # Use a moderate strength based on shared lemma count
            strength = min(0.75, 0.5 + (len(shared_lemmas) * 0.1))
            return ("RELATED_TO", strength)
    
    # No shared lemmas - rely on path similarity only
    if path_sim is None:
        return None
    
    # Classify by similarity threshold
    if path_sim >= 0.8:
        return ("CLOSE_SYNONYM", path_sim)
    elif path_sim >= 0.6:
        return ("RELATED_TO", path_sim)
    else:
        # Too weak, don't create relationship
        return None


def get_all_word_ranks(conn: Neo4jConnection) -> Dict[str, float]:
    """Get frequency ranks for all words from Neo4j in one query."""
    with conn.get_session() as session:
        result = session.run("""
            MATCH (w:Word)
            RETURN w.name as word, w.frequency_rank as rank
        """)
        return {record["word"]: record["rank"] for record in result if record["rank"] is not None}


def score_relationship_quality(
    source_word: str,
    source_sense_id: str,
    target_word: str,
    target_sense_id: str,
    word_ranks: Optional[Dict[str, float]] = None
) -> float:
    """
    Score relationship quality (0.0-1.0) based on multiple factors.
    
    Factors:
    - Semantic similarity (WordNet path similarity)
    - Shared lemmas (strong indicator of relationship)
    - Same synset
    - Part of speech matching
    - Frequency rank similarity (pedagogical appropriateness)
    """
    try:
        source_syn = wn.synset(source_sense_id)
        target_syn = wn.synset(target_sense_id)
    except:
        return 0.0
    
    scores = []
    weights = []
    
    # Check for shared lemmas (strong relationship indicator)
    source_lemmas = {l.name().lower() for l in source_syn.lemmas()}
    target_lemmas = {l.name().lower() for l in target_syn.lemmas()}
    shared_lemmas = source_lemmas & target_lemmas
    shared_lemma_bonus = min(1.0, 0.5 + len(shared_lemmas) * 0.2) if shared_lemmas else 0.0
    
    # 1. Path similarity (30% weight, or 20% if shared lemmas)
    path_sim = source_syn.path_similarity(target_syn) or 0.0
    scores.append(path_sim)
    weights.append(0.2 if shared_lemmas else 0.3)
    
    # 2. Shared lemmas bonus (20% weight if shared, otherwise 0%)
    scores.append(shared_lemma_bonus)
    weights.append(0.2 if shared_lemmas else 0.0)
    
    # 3. Same synset? (25% weight)
    same_synset = 1.0 if source_syn == target_syn else 0.0
    scores.append(same_synset)
    weights.append(0.25)
    
    # 4. Part of speech match (15% weight, or 10% if shared lemmas)
    pos_match = 1.0 if source_syn.pos() == target_syn.pos() else 0.0
    scores.append(pos_match)
    weights.append(0.1 if shared_lemmas else 0.15)
    
    # 5. Frequency rank similarity (10% weight) - if available
    if word_ranks:
        source_rank = word_ranks.get(source_word)
        target_rank = word_ranks.get(target_word)
        if source_rank and target_rank:
            rank_diff = abs(source_rank - target_rank) / max(source_rank, target_rank)
            rank_sim = max(0.0, 1.0 - rank_diff)  # Closer ranks = higher score
            scores.append(rank_sim)
            weights.append(0.1)
        else:
            # If ranks unavailable, don't penalize
            scores.append(1.0)
            weights.append(0.1)
    else:
        # No word ranks, skip this factor
        pass
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]
    
    # Weighted average
    quality_score = sum(score * weight for score, weight in zip(scores, weights))
    return quality_score


def get_hierarchical_relationships(
    source_sense_id: str,
    source_word: str,
    word_ranks: Optional[Dict[str, float]] = None,
    min_quality: float = 0.3  # Lower threshold for hierarchical (they're structural, not semantic similarity)
) -> List[Dict]:
    """
    Get hypernym/hyponym, meronym/holonym, and entailment relationships.
    These are hierarchical/structural relationships, so lower quality threshold.
    
    Returns:
        List of relationship dicts with types: HYPERNYM_OF, HYPONYM_OF, HAS_PART, PART_OF, ENTAILS
    """
    try:
        source_syn = wn.synset(source_sense_id)
    except Exception as e:
        return []
    
    relationships = []
    seen_target_senses = set()
    
    # Get hypernyms (more general concepts)
    for hypernym in source_syn.hypernyms():
        target_sense_id = hypernym.name()
        if target_sense_id in seen_target_senses or target_sense_id == source_sense_id:
            continue
        
        # Get representative word from hypernym
        target_lemmas = hypernym.lemmas()
        if not target_lemmas:
            continue
        target_word = target_lemmas[0].name().lower().replace('_', ' ')
        
        # Score quality (hierarchical relationships are structural, so use simpler scoring)
        # For hierarchical, we care more about existence than semantic similarity
        try:
            source_syn_check = wn.synset(source_sense_id)
            target_syn_check = wn.synset(target_sense_id)
            # Basic quality: POS match gets higher score, but hierarchical relationships are valid even with different POS
            pos_match = 1.0 if source_syn_check.pos() == target_syn_check.pos() else 0.5
            quality = 0.6 + (pos_match * 0.2)  # Base 0.6, up to 0.8 if POS matches
        except:
            quality = 0.6  # Default quality for hierarchical relationships
        
        if quality >= min_quality:
            seen_target_senses.add(target_sense_id)
            relationships.append({
                "target_word": target_word,
                "target_sense_id": target_sense_id,
                "relationship_type": "HYPERNYM_OF",
                "strength": 0.8,  # Hierarchical relationships are strong
                "quality_score": quality
            })
    
    # Get hyponyms (more specific concepts)
    for hyponym in source_syn.hyponyms():
        target_sense_id = hyponym.name()
        if target_sense_id in seen_target_senses or target_sense_id == source_sense_id:
            continue
        
        target_lemmas = hyponym.lemmas()
        if not target_lemmas:
            continue
        target_word = target_lemmas[0].name().lower().replace('_', ' ')
        
        quality = score_relationship_quality(
            source_word, source_sense_id,
            target_word, target_sense_id,
            word_ranks
        )
        
        if quality >= min_quality:
            seen_target_senses.add(target_sense_id)
            relationships.append({
                "target_word": target_word,
                "target_sense_id": target_sense_id,
                "relationship_type": "HYPONYM_OF",
                "strength": 0.8,
                "quality_score": quality
            })
    
    # Get meronyms (parts)
    for meronym in source_syn.part_meronyms() + source_syn.member_meronyms() + source_syn.substance_meronyms():
        target_sense_id = meronym.name()
        if target_sense_id in seen_target_senses or target_sense_id == source_sense_id:
            continue
        
        target_lemmas = meronym.lemmas()
        if not target_lemmas:
            continue
        target_word = target_lemmas[0].name().lower().replace('_', ' ')
        
        quality = score_relationship_quality(
            source_word, source_sense_id,
            target_word, target_sense_id,
            word_ranks
        )
        
        if quality >= min_quality:
            seen_target_senses.add(target_sense_id)
            relationships.append({
                "target_word": target_word,
                "target_sense_id": target_sense_id,
                "relationship_type": "HAS_PART",
                "strength": 0.75,
                "quality_score": quality
            })
    
    # Get holonyms (wholes) - reverse of meronyms
    for holonym in source_syn.part_holonyms() + source_syn.member_holonyms() + source_syn.substance_holonyms():
        target_sense_id = holonym.name()
        if target_sense_id in seen_target_senses or target_sense_id == source_sense_id:
            continue
        
        target_lemmas = holonym.lemmas()
        if not target_lemmas:
            continue
        target_word = target_lemmas[0].name().lower().replace('_', ' ')
        
        quality = score_relationship_quality(
            source_word, source_sense_id,
            target_word, target_sense_id,
            word_ranks
        )
        
        if quality >= min_quality:
            seen_target_senses.add(target_sense_id)
            relationships.append({
                "target_word": target_word,
                "target_sense_id": target_sense_id,
                "relationship_type": "PART_OF",
                "strength": 0.75,
                "quality_score": quality
            })
    
    # Get entailments (verb relationships)
    for entailment in source_syn.entailments():
        target_sense_id = entailment.name()
        if target_sense_id in seen_target_senses or target_sense_id == source_sense_id:
            continue
        
        target_lemmas = entailment.lemmas()
        if not target_lemmas:
            continue
        target_word = target_lemmas[0].name().lower().replace('_', ' ')
        
        quality = score_relationship_quality(
            source_word, source_sense_id,
            target_word, target_sense_id,
            word_ranks
        )
        
        if quality >= min_quality:
            seen_target_senses.add(target_sense_id)
            relationships.append({
                "target_word": target_word,
                "target_sense_id": target_sense_id,
                "relationship_type": "ENTAILS",
                "strength": 0.7,
                "quality_score": quality
            })
    
    return relationships


def get_sense_relationships(
    source_sense_id: str,
    source_word: str,
    word_ranks: Optional[Dict[str, float]] = None,
    min_quality: float = 0.6,
    include_hierarchical: bool = True
) -> List[Dict]:
    """
    Get high-quality relationships for a specific sense.
    
    Returns:
        List of {
            "target_word": str,
            "target_sense_id": str,
            "relationship_type": str,
            "strength": float,
            "quality_score": float
        }
    """
    try:
        # Skip if not a valid WordNet synset ID format
        if not source_sense_id or '.' not in source_sense_id:
            return []
        parts = source_sense_id.rsplit('.', 2)
        if len(parts) != 3 or parts[2] not in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']:
            # Check if it's a number
            try:
                int(parts[2])
            except:
                return []
        
        source_syn = wn.synset(source_sense_id)
    except Exception as e:
        # Skip invalid synsets (e.g., manual senses)
        return []
    
    relationships = []
    seen_target_senses = set()  # Avoid duplicates
    
    # Get all lemma words from source synset
    source_lemma_words = {lemma.name().lower().replace('_', ' ') for lemma in source_syn.lemmas()}
    
    # Strategy: Check all synsets that share lemmas with source synset
    # This finds synonyms and related senses (e.g., happy.a.01 -> felicitous.s.01 via shared "happy" lemma)
    for lemma in source_syn.lemmas():
        lemma_word = lemma.name().lower().replace('_', ' ')
        
        # Get all synsets that contain this lemma word
        # This includes synsets of the lemma word itself, plus any synset that has this word as a lemma
        target_synsets = wn.synsets(lemma_word)
        if not target_synsets:
            continue
        
        # Check all synsets containing this lemma
        for target_syn in target_synsets:
            target_sense_id = target_syn.name()
            
            # Skip self-relationship (same sense)
            if target_sense_id == source_sense_id:
                continue
            
            # Get a representative word from target synset (prefer non-source words)
            target_lemmas = target_syn.lemmas()
            target_word = None
            for t_lemma in target_lemmas:
                t_word = t_lemma.name().lower().replace('_', ' ')
                if t_word not in source_lemma_words:
                    target_word = t_word
                    break
            # If all lemmas are in source, use first lemma
            if not target_word:
                target_word = target_lemmas[0].name().lower().replace('_', ' ')
            
            # Classify relationship
            rel_info = classify_relationship(source_syn, target_syn)
            if not rel_info:
                continue
            
            rel_type, strength = rel_info
            
            # Score quality
            quality = score_relationship_quality(
                source_word, source_sense_id,
                target_word, target_sense_id,
                word_ranks
            )
            
            # Check if synsets share lemmas (strong relationship indicator)
            source_lemmas_check = {l.name().lower() for l in source_syn.lemmas()}
            target_lemmas_check = {l.name().lower() for l in target_syn.lemmas()}
            shared_lemmas_check = source_lemmas_check & target_lemmas_check
            
            # Lower threshold for shared-lemma relationships (they're strongly related)
            effective_threshold = min_quality * 0.75 if shared_lemmas_check else min_quality
            
            # Only include if quality is above threshold and not duplicate
            if (quality >= effective_threshold and 
                target_sense_id not in seen_target_senses):
                seen_target_senses.add(target_sense_id)
                relationships.append({
                    "target_word": target_word,
                    "target_sense_id": target_sense_id,
                    "relationship_type": rel_type,
                    "strength": strength,
                    "quality_score": quality
                })
    
    # Add hierarchical relationships (hypernyms, hyponyms, meronyms, entailments)
    if include_hierarchical:
        hierarchical_rels = get_hierarchical_relationships(
            source_sense_id,
            source_word,
            word_ranks,
            min_quality=min_quality * 0.83  # Slightly lower threshold for hierarchical
        )
        for rel in hierarchical_rels:
            if rel["target_sense_id"] not in seen_target_senses:
                seen_target_senses.add(rel["target_sense_id"])
                relationships.append(rel)
    
    # Sort by quality score (best first)
    relationships.sort(key=lambda x: x["quality_score"], reverse=True)
    
    return relationships


def run_relationship_miner(conn: Neo4jConnection, min_quality: float = 0.6, batch_size: int = 50, rate_limit_delay: float = 2.5, limit: Optional[int] = None):
    """
    Create sense-specific relationships with quality scoring.
    
    Optimized for Neo4j Aura Free tier (25 requests/minute):
    - Batches operations to reduce query count
    - Adds rate limiting delays
    - Pre-fetches word ranks in bulk
    
    Creates:
    - (:Sense)-[:SYNONYM_OF]->(:Sense) for true synonyms
    - (:Sense)-[:CLOSE_SYNONYM]->(:Sense) for very similar (similarity >= 0.8)
    - (:Sense)-[:RELATED_TO]->(:Sense) for related concepts (similarity 0.6-0.8)
    
    Also creates aggregated Word-level relationships for backward compatibility.
    
    Args:
        conn: Neo4j connection
        min_quality: Minimum quality score threshold (0.0-1.0)
        batch_size: Number of relationships to batch per query
        rate_limit_delay: Seconds to wait between batches (default 2.5s for ~24 req/min)
        limit: Optional limit on number of word-sense pairs to process (for testing)
    """
    print("🔗 Starting Improved Relationship Mining...")
    print(f"   Minimum quality threshold: {min_quality}")
    print(f"   Batch size: {batch_size}")
    print(f"   Rate limit delay: {rate_limit_delay}s (respecting 25 req/min limit)")
    print(f"   Using new session per batch (prevents timeout)")
    print(f"   Including hierarchical relationships (hypernyms, meronyms, entailments)")
    
    # Fetch word ranks and senses (single queries, then close session)
    with conn.get_session() as session:
        # 1. Pre-fetch all word ranks in one query
        print("   Pre-fetching word ranks...")
        word_ranks = get_all_word_ranks(conn)
        print(f"   Loaded {len(word_ranks)} word ranks")
        
        # 2. Fetch all Words with their Senses (only valid WordNet synsets)
        print("   Fetching word-sense pairs...")
        query = """
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            WHERE s.id =~ '.*\\.[anrv]\\.[0-9]+$'  // Valid WordNet format: word.pos.number
            RETURN w.name as word, w.frequency_rank as rank, s.id as sense_id
            ORDER BY w.frequency_rank
        """
        if limit:
            query += f" LIMIT {limit}"
        
        result = session.run(query)
        records = list(result)
        print(f"   Processing {len(records)} word-sense pairs...")
        
        rel_counts = {
            "SYNONYM_OF": 0,
            "CLOSE_SYNONYM": 0,
            "RELATED_TO": 0,
            "HYPERNYM_OF": 0,
            "HYPONYM_OF": 0,
            "HAS_PART": 0,
            "PART_OF": 0,
            "ENTAILS": 0
        }
        
        # Collect all relationships first (in-memory, no DB queries)
        all_relationships = []
        processed = 0
        
        for record in records:
            source_word = record["word"]
            source_sense_id = record["sense_id"]
            
            # Get high-quality relationships for this sense (WordNet only, no DB)
            # Include hierarchical relationships (hypernyms, meronyms, entailments)
            relationships = get_sense_relationships(
                source_sense_id,
                source_word,
                word_ranks,
                min_quality=min_quality,
                include_hierarchical=True
            )
            
            for rel in relationships:
                all_relationships.append({
                    "source_sense_id": source_sense_id,
                    "target_word": rel["target_word"],
                    "target_sense_id": rel["target_sense_id"],
                    "rel_type": rel["relationship_type"],
                    "strength": rel["strength"],
                    "quality": rel["quality_score"]
                })
            
            processed += 1
            if processed % 500 == 0:
                print(f"   Analyzed {processed}/{len(records)} senses, found {len(all_relationships)} relationships so far...")
        
        print(f"\n   Found {len(all_relationships)} potential relationships")
        print("   Validating and creating relationships in batches...")
        
        # 3. Batch validate and create relationships (new session per batch to prevent timeout)
        batch = []
        batch_num = 0
        
        for rel in all_relationships:
            batch.append(rel)
                
            if len(batch) >= batch_size:
                batch_num += 1
                debug = (batch_num == 1)  # Debug first batch only
                # Create new session for each batch (prevents timeout)
                try:
                    with conn.get_session() as batch_session:
                        created = _process_relationship_batch(batch_session, batch, rel_counts, debug=debug)
                    print(f"   Batch {batch_num}: Created {created} relationships (total: {sum(rel_counts.values())})")
                except Exception as e:
                    print(f"   Batch {batch_num}: Error - {e}, retrying...")
                    time.sleep(5)
                    try:
                        with conn.get_session() as batch_session:
                            created = _process_relationship_batch(batch_session, batch, rel_counts, debug=False)
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
                    created = _process_relationship_batch(batch_session, batch, rel_counts, debug=False)
                print(f"   Batch {batch_num}: Created {created} relationships (total: {sum(rel_counts.values())})")
            except Exception as e:
                print(f"   Batch {batch_num}: Error - {e}, retrying...")
                time.sleep(5)
                try:
                    with conn.get_session() as batch_session:
                        created = _process_relationship_batch(batch_session, batch, rel_counts, debug=False)
                    print(f"   Batch {batch_num}: Retry successful - Created {created} relationships (total: {sum(rel_counts.values())})")
                except Exception as e2:
                    print(f"   Batch {batch_num}: Retry failed - {e2}, skipping batch")
        
        print(f"\n✅ Relationship Mining Complete.")
        print(f"   Created {rel_counts['SYNONYM_OF']} SYNONYM_OF relationships")
        print(f"   Created {rel_counts['CLOSE_SYNONYM']} CLOSE_SYNONYM relationships")
        print(f"   Created {rel_counts['RELATED_TO']} RELATED_TO relationships")
        print(f"   Created {rel_counts['HYPERNYM_OF']} HYPERNYM_OF relationships")
        print(f"   Created {rel_counts['HYPONYM_OF']} HYPONYM_OF relationships")
        print(f"   Created {rel_counts['HAS_PART']} HAS_PART relationships")
        print(f"   Created {rel_counts['PART_OF']} PART_OF relationships")
        print(f"   Created {rel_counts['ENTAILS']} ENTAILS relationships")
        print(f"   Total: {sum(rel_counts.values())} relationships")
        
        # Create aggregated Word-level relationships for backward compatibility
        print("\n   Creating aggregated Word-level relationships...")
        session.run("""
            MATCH (s1:Sense)-[r:SYNONYM_OF|CLOSE_SYNONYM|RELATED_TO|HYPERNYM_OF|HYPONYM_OF|HAS_PART|PART_OF|ENTAILS]->(s2:Sense)
            MATCH (w1:Word)-[:HAS_SENSE]->(s1)
            MATCH (w2:Word)-[:HAS_SENSE]->(s2)
            WHERE w1 <> w2
            WITH w1, w2, collect(r) as rels, avg(r.quality_score) as avg_quality
            MERGE (w1)-[wr:RELATED_TO]->(w2)
            SET wr.avg_quality = avg_quality,
                wr.relationship_count = size(rels),
                wr.types = [r IN rels | type(r)]
        """)
        print("   ✅ Aggregated relationships created")


def _process_relationship_batch(session, batch: List[Dict], rel_counts: Dict[str, int], debug: bool = False) -> int:
    """
    Process a batch of relationships: validate they exist, then create them.
    Returns number of relationships created.
    """
    if not batch:
        return 0
    
    # Build batch data for validation query
    batch_data = [
        {
            "source_sense_id": rel["source_sense_id"],
            "target_word": rel["target_word"],
            "target_sense_id": rel["target_sense_id"],
            "rel_type": rel["rel_type"],
            "strength": rel["strength"],
            "quality": rel["quality"]
        }
        for rel in batch
    ]
    
    if debug and len(batch) > 0:
        print(f"      Debug: Sample relationship: {batch[0]['source_sense_id']} -> {batch[0]['target_sense_id']} ({batch[0]['target_word']})")
    
    # Validate all relationships exist in one query
    # Use toLower for case-insensitive word matching
    validation_result = session.run("""
        UNWIND $batch as rel
        MATCH (target:Word)
        WHERE toLower(target.name) = toLower(rel.target_word)
        MATCH (target)-[:HAS_SENSE]->(target_sense:Sense {id: rel.target_sense_id})
        MATCH (source_sense:Sense {id: rel.source_sense_id})
        WHERE source_sense <> target_sense
        RETURN rel.source_sense_id as source_sense_id,
               rel.target_sense_id as target_sense_id,
               rel.rel_type as rel_type,
               rel.strength as strength,
               rel.quality as quality
    """, batch=batch_data)
    
    valid_rels = list(validation_result)
    if debug:
        print(f"      Debug: Validated {len(valid_rels)}/{len(batch)} relationships exist in graph")
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
        create_result = session.run(f"""
            UNWIND $rels as rel
            MATCH (source_sense:Sense {{id: rel.source_sense_id}})
            MATCH (target_sense:Sense {{id: rel.target_sense_id}})
            MERGE (source_sense)-[r:{rel_type}]->(target_sense)
            SET r.strength = rel.strength,
                r.quality_score = rel.quality,
                r.source = "wordnet",
                r.created_at = timestamp()
            RETURN count(r) as created
        """, rels=[dict(rel) for rel in rels])
        
        created_count = create_result.single()["created"]
        created += created_count
        rel_counts[rel_type] += created_count
    
    return created


if __name__ == "__main__":
    import sys
    
    min_quality = 0.6
    limit = None
    
    if len(sys.argv) > 1:
        try:
            min_quality = float(sys.argv[1])
        except:
            print(f"Invalid quality threshold: {sys.argv[1]}, using default 0.6")
    
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except:
            print(f"Invalid limit: {sys.argv[2]}, processing all records")
    
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            if limit:
                print(f"⚠️ TEST MODE: Processing only {limit} word-sense pairs")
            run_relationship_miner(conn, min_quality=min_quality, limit=limit)
    finally:
        conn.close()

