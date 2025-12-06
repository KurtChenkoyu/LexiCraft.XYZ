"""
Pipeline Step 7: The Factory (Orchestrator)
The Master Production Loop for V6.1.

Responsibility:
1. Iterate through words by Unified Priority.
2. Execute Pipeline Steps:
   - Step 1: Structure Mining (WordNet skeletons)
   - Step 2: Content Generation Level 1 (Gemini) - WITH RETRY LOGIC
   - Step 3: Relationship Mining (WordNet relationships)

Usage:
    python3 -m src.main_factory --limit 50
"""

import time
import random
import argparse
from tqdm import tqdm
from src.database.neo4j_connection import Neo4jConnection
from src.structure_miner import get_skeletons
from src.agent import get_enrichment, update_graph
from src.adversary_miner import get_semantic_targets

# Configuration
GEMINI_SLEEP_BASE = 2.0  # Seconds between calls to avoid 429
MAX_RETRIES = 3

def run_miner_stage(session, word):
    """Pipeline Step 1: Structure Mining"""
    # Check if skeletons exist
    result = session.run("""
        MATCH (w:Word {name: $word})-[:HAS_SENSE]->()
        RETURN count(*) as count
    """, word=word)
    if result.single()["count"] > 0:
        return False  # Already mined

    skeletons = get_skeletons(word)
    if not skeletons:
        return False

    # Write Skeletons
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
    session.run(query, word=word, skeletons=skeletons)
    return True

def run_agent_stage(session, word, mock=False):
    """Pipeline Step 2: Content Generation Level 1"""
    # Fetch raw skeletons INCLUDING PHRASES
    result = session.run("""
        MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
        WHERE s.enriched IS NULL
        RETURN collect({
            id: s.id, 
            def: s.definition, 
            phrases: s.skeleton_phrases
        }) as skeletons
    """, word=word)
    
    record = result.single()
    if not record or not record["skeletons"]:
        return False # Nothing to enrich

    skeletons = record["skeletons"]
    
    # Retry Loop for API
    for attempt in range(MAX_RETRIES):
        try:
            enriched_data = get_enrichment(word, skeletons, mock=mock)
            if enriched_data:
                update_graph(Neo4jConnection(), enriched_data) # Pass new connection if needed or reuse
                return True
            else:
                return False
        except Exception as e:
            if "429" in str(e):
                wait = GEMINI_SLEEP_BASE * (2 ** attempt) + random.uniform(0, 1)
                print(f"  ⚠️ 429 Rate Limit. Sleeping {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"  ❌ Agent Error: {e}")
                return False
    return False

def run_adversary_stage(session, word):
    """Pipeline Step 3: Relationship Mining"""
    # Fetch senses
    result = session.run("""
        MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
        RETURN collect(s.id) as sense_ids
    """, word=word)
    
    sense_ids = result.single()["sense_ids"]
    count = 0
    
    for sid in sense_ids:
        targets = get_semantic_targets(sid)
        
        # Antonyms
        for target in targets["antonyms"]:
            if target == word: continue
            res = session.run("""
                MATCH (a:Word {name: $word}), (b:Word {name: $target})
                MERGE (a)-[r:OPPOSITE_TO]->(b)
                RETURN count(r)
            """, word=word, target=target)
            if res.peek(): count += 1
            
        # Synonyms
        for target in targets["synonyms"]:
            if target == word: continue
            res = session.run("""
                MATCH (a:Word {name: $word}), (b:Word {name: $target})
                MERGE (a)-[r:RELATED_TO]->(b)
                RETURN count(r)
            """, word=word, target=target)
            if res.peek(): count += 1
            
    return count > 0

def run_factory(conn: Neo4jConnection, limit: int = 100, mock: bool = False):
    print("🏭 Starting V6.1 Factory...")
    
    with conn.get_session() as session:
        # 1. Get Words by Priority
        # Filter: Words that are NOT fully enriched yet
        print("Fetching priority queue...")
        result = session.run("""
            MATCH (w:Word)
            WHERE NOT EXISTS {
                MATCH (w)-[:HAS_SENSE]->(s:Sense)
                WHERE s.enriched = true
            }
            RETURN w.name as word, w.frequency_rank as rank
            ORDER BY w.frequency_rank ASC
            LIMIT $limit
        """, limit=limit)
        
        queue = list(result)
        print(f"Queue size: {len(queue)}")
        
        pbar = tqdm(queue)
        for record in pbar:
            word = record["word"]
            pbar.set_description(f"Processing '{word}'")
            
            # Step 1: Miner
            mined = run_miner_stage(session, word)
            
            # Step 2: Agent (Pass connection specifically for update_graph)
            # Note: run_agent_stage calls update_graph which needs a connection object, not session
            # We'll pass the connection to run_agent_stage
            enriched = run_agent_stage_with_conn(session, conn, word, mock=mock)
            
            # Step 3: Adversary
            linked = run_adversary_stage(session, word)
            
            # Rate Limit Sleep (if we used the API)
            if enriched and not mock:
                time.sleep(GEMINI_SLEEP_BASE)

    print("✅ Factory Run Complete.")

def run_agent_stage_with_conn(session, conn, word, mock=False):
    """Wrapper to pass connection object"""
    # Fetch raw skeletons INCLUDING PHRASES
    result = session.run("""
        MATCH (w:Word {name: $word})-[:HAS_SENSE]->(s:Sense)
        WHERE s.enriched IS NULL
        RETURN collect({
            id: s.id, 
            def: s.definition, 
            phrases: s.skeleton_phrases
        }) as skeletons
    """, word=word)
    
    record = result.single()
    if not record or not record["skeletons"]:
        return False # Nothing to enrich

    skeletons = record["skeletons"]
    
    # Retry Loop for API
    for attempt in range(MAX_RETRIES):
        try:
            enriched_data = get_enrichment(word, skeletons, mock=mock)
            if enriched_data:
                update_graph(conn, enriched_data)
                return True
            else:
                return False
        except Exception as e:
            if "429" in str(e):
                wait = GEMINI_SLEEP_BASE * (2 ** attempt) + random.uniform(0, 1)
                tqdm.write(f"  ⚠️ 429 Rate Limit. Sleeping {wait:.1f}s...")
                time.sleep(wait)
            else:
                tqdm.write(f"  ❌ Agent Error: {e}")
                return False
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Number of words to process")
    parser.add_argument("--mock", action="store_true", help="Use mock agent")
    parser.add_argument("--batched", action="store_true", help="Use batched Level 1 content generation (faster, processes multiple words per API call)")
    parser.add_argument("--batch-size", type=int, default=5, help="Words per batch (only if --batched)")
    args = parser.parse_args()
    
    # If batched mode, use the batched agent instead
    if args.batched:
        from src.agent_batched import run_batched_agent
        conn = Neo4jConnection()
        try:
            if conn.verify_connectivity():
                print("🚀 Using BATCHED mode for faster processing...")
                run_batched_agent(conn, batch_size=args.batch_size, limit=args.limit, mock=args.mock)
        finally:
            conn.close()
    else:
        conn = Neo4jConnection()
        try:
            if conn.verify_connectivity():
                run_factory(conn, limit=args.limit, mock=args.mock)
        finally:
            conn.close()
