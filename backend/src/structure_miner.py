"""
Phase 1: Structure Extraction (The Skeleton)
Mines WordNet for the "Semantic Skeleton" of each word.

1. Connects to Neo4j to get target words.
2. Queries WordNet for synsets.
3. Filtering Logic:
   - Keeps top N synsets (default 3-5) based on Lemma count (frequency).
   - Ignores rare/archaic meanings to prevent hallucinations.
4. Returns 'Sense Skeletons' (ID + Raw Definition + Phrases) for the Agent to enrich later.
"""

import nltk
from nltk.corpus import wordnet as wn
from src.database.neo4j_connection import Neo4jConnection
import sys

# Ensure WordNet is downloaded
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading WordNet...")
    nltk.download('wordnet')
    nltk.download('omw-1.4')

def get_skeletons(word_text: str, limit: int = 3) -> list:
    """
    Fetches and filters synsets for a word.
    Returns a list of dicts: {sense_id, definition, pos, lemma_names, skeleton_phrases}
    """
    synsets = wn.synsets(word_text)
    
    if not synsets:
        return []

    # Sorting Strategy:
    # WordNet synsets are already roughly ordered by frequency, 
    # but we can be more explicit by counting lemma occurrences if needed.
    # For MVP V6.1, we trust WordNet's default order (Semcor frequency).
    
    skeletons = []
    for syn in synsets[:limit]:
        # Generate a unique ID for the sense (e.g., "bank.n.01")
        sense_id = syn.name()
        
        # Extract lemmas
        lemmas = [l.name().replace('_', ' ') for l in syn.lemmas()]
        
        # Identify phrases (multi-word lemmas)
        # These serve as "Skeleton Phrases" for the Agent to map
        skeleton_phrases = [lemma for lemma in lemmas if ' ' in lemma and word_text.lower() in lemma.lower()]
        
        skeletons.append({
            "id": sense_id,
            "definition": syn.definition(),
            "pos": syn.pos(),
            "lemmas": lemmas,
            "skeleton_phrases": skeleton_phrases
        })
        
    return skeletons

def run_mining_operation(conn: Neo4jConnection):
    print("⛏️ Starting Structure Mining...")
    
    with conn.get_session() as session:
        # 1. Fetch all Words that don't have senses yet
        # (Incremental processing)
        result = session.run("""
            MATCH (w:Word)
            WHERE NOT (w)-[:HAS_SENSE]->()
            RETURN w.name AS word
        """)
        
        words_to_mine = [record["word"] for record in result]
        print(f"Found {len(words_to_mine)} words needing skeletons.")
        
        count = 0
        for word_text in words_to_mine:
            skeletons = get_skeletons(word_text)
            
            if not skeletons:
                # Log skipped words (no WordNet data)
                # print(f"⚠️ No senses found for: {word_text}")
                continue

            # 2. Inject Skeletons into Graph immediately (Phase 1 Loader)
            # We do this here to keep the miner stateful
            query = """
            MATCH (w:Word {name: $word})
            WITH w
            UNWIND $skeletons AS skel
            MERGE (s:Sense {id: skel.id})
            SET s.definition = skel.definition,
                s.pos = skel.pos,
                s.skeleton_phrases = skel.skeleton_phrases
            MERGE (w)-[:HAS_SENSE]->(s)
            """
            
            session.run(query, word=word_text, skeletons=skeletons)
            count += 1
            
            if count % 100 == 0:
                print(f"Mined {count} words...")

    print(f"✅ Mining Complete. Processed {count} words.")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            run_mining_operation(conn)
    finally:
        conn.close()
