"""
Phase 3: The Adversary (Miner Edition)
Mines WordNet for Semantic Relationships to build the "Adversarial Layer".

Adapts V6.1 Schema:
(:Word)-[:OPPOSITE_TO]->(:Word)
(:Word)-[:RELATED_TO]->(:Word)

1. Iterates through all Word nodes.
2. Uses attached Sense Skeletons to find Antonyms and Synonyms in WordNet.
3. Checks if the target word exists in our Graph.
4. Creates relationships if both words exist.
"""

import nltk
from nltk.corpus import wordnet as wn
from src.database.neo4j_connection import Neo4jConnection

def get_semantic_targets(sense_id: str):
    """
    Returns dict of {relationship_type: [word_list]}
    """
    try:
        syn = wn.synset(sense_id)
    except:
        return {"antonyms": [], "synonyms": []}
        
    antonyms = set()
    synonyms = set()
    
    for lemma in syn.lemmas():
        # Synonyms (Lemmas)
        synonyms.add(lemma.name().lower().replace('_', ' '))
        
        # Antonyms
        for ant in lemma.antonyms():
            antonyms.add(ant.name().lower().replace('_', ' '))
            
    return {
        "antonyms": list(antonyms),
        "synonyms": list(synonyms)
    }

def run_adversary_miner(conn: Neo4jConnection):
    print("😈 Starting Adversary Mining (WordNet Edition)...")
    
    with conn.get_session() as session:
        # 1. Fetch all Words and their Sense IDs
        result = session.run("""
            MATCH (w:Word)-[:HAS_SENSE]->(s:Sense)
            RETURN w.name as word, collect(s.id) as sense_ids
        """)
        
        records = list(result)
        print(f"Scanning {len(records)} words for relationships...")
        
        rel_counts = {"OPPOSITE_TO": 0, "RELATED_TO": 0}
        
        for rec in records:
            source_word = rec["word"]
            sense_ids = rec["sense_ids"]
            
            for sid in sense_ids:
                targets = get_semantic_targets(sid)
                
                # 1. Antonyms (OPPOSITE_TO)
                for target_word in targets["antonyms"]:
                    if target_word == source_word: continue
                    
                    # Cypher: Only create if target word exists in our graph
                    res = session.run("""
                        MATCH (source:Word {name: $source})
                        MATCH (target:Word {name: $target})
                        MERGE (source)-[r:OPPOSITE_TO]->(target)
                        RETURN count(r) as created
                    """, source=source_word, target=target_word)
                    
                    if res.peek():
                        rel_counts["OPPOSITE_TO"] += 1

                # 2. Synonyms (RELATED_TO)
                for target_word in targets["synonyms"]:
                    if target_word == source_word: continue
                    
                    res = session.run("""
                        MATCH (source:Word {name: $source})
                        MATCH (target:Word {name: $target})
                        MERGE (source)-[r:RELATED_TO]->(target)
                        RETURN count(r) as created
                    """, source=source_word, target=target_word)
                    
                    if res.peek():
                        rel_counts["RELATED_TO"] += 1
                        
        print(f"✅ Adversary Mining Complete.")
        print(f"  Created {rel_counts['OPPOSITE_TO']} Antonym links.")
        print(f"  Created {rel_counts['RELATED_TO']} Synonym links.")

if __name__ == "__main__":
    conn = Neo4jConnection()
    try:
        if conn.verify_connectivity():
            run_adversary_miner(conn)
    finally:
        conn.close()

